from __future__ import annotations

import argparse
import csv
import os
import re
import string
import sys
import unicodedata
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.validation._dialect_inventory import (  # noqa: E402
    ISO_TO_LANGUAGE,
    STANDARD_ORTHOGRAPHY_MAP,
    is_multi_dialect_language,
    standard_orthography,
)


ORTHOGRAPHIES_PATH = _REPO_ROOT / "Orthographies"

NULL_MARKER = "∅"
# A null unit is the marker plus one bridging segmentation hyphen, removed
# as a unit so no dangling hyphen is left where '-' is a mapped letter
# (Bunun, Thao). Only the canonical U+2205 counts: 'ø'/'Ø' normalization is
# clean_xml's job, so foreign letters are never swallowed here.
_NULL_UNIT_RE = re.compile(r"∅-|-∅|∅")


@dataclass(frozen=True)
class PhonologyRule:
    pattern: re.Pattern[str]
    replacement: str
    description: str


@dataclass(frozen=True)
class PhonologyProfile:
    mappings: tuple[tuple[str, str], ...]
    ipa_characters: frozenset[str]
    rules: tuple[PhonologyRule, ...]


from QC.utilities._prettify import prettify  # noqa: E402,F401  (shared, mixed-content-safe, idempotent)


def get_files(path: str, language: str | None) -> list[str]:
    files = []
    for root, _dirs, filenames in os.walk(path):
        for filename in filenames:
            candidate = os.path.join(root, filename)
            if filename.endswith(".xml") and (
                not language or re.search(language, candidate)
            ):
                files.append(candidate)
    return sorted(files)


def get_exploration_targets(corpora_path: str) -> list[str]:
    if os.path.isfile(corpora_path) and corpora_path.endswith(".xml"):
        return [corpora_path]
    return [
        os.path.join(corpora_path, name)
        for name in sorted(os.listdir(corpora_path))
    ]


def _select_target_column(
    fieldnames: list[str],
    language: str,
    dialect: str,
    *,
    explicit: str | None = None,
) -> str:
    if "letter" not in fieldnames:
        raise ValueError("orthography TSV has no 'letter' column")
    value_columns = [column for column in fieldnames if column != "letter"]
    if explicit:
        if explicit not in value_columns:
            raise ValueError(
                f"target column {explicit!r} is not present; columns are {fieldnames}"
            )
        return explicit

    if is_multi_dialect_language(language):
        if dialect not in {"default", "unknown"} and dialect in value_columns:
            return dialect
        if "default" in value_columns:
            if dialect not in {"default", "unknown"}:
                print(
                    f"Warning: Dialect {dialect!r} is not in the {language} "
                    "orthography; using 'default'"
                )
            return "default"
        if "IPA" in value_columns:
            return "IPA"
        if len(value_columns) == 1:
            return value_columns[0]
        raise ValueError(
            f"dialect {dialect!r} is not present and there is no default "
            f"column for multi-dialect {language}: {fieldnames}"
        )

    if len(value_columns) == 1:
        return value_columns[0]
    if dialect in value_columns:
        return dialect
    if "IPA" in value_columns:
        return "IPA"
    if "default" in value_columns:
        return "default"
    raise ValueError(
        f"no unambiguous value column for single-dialect {language}: {fieldnames}"
    )


def _load_rules(tsv_path: Path, dialect: str) -> tuple[PhonologyRule, ...]:
    """Load the ordered rule sidecar, keeping only the rules that apply to
    ``dialect``.

    The optional ``dialect`` column scopes a rule to one or more dialects
    (comma-separated). Its semantics mirror the mapping columns' dialect/default
    resolution, matched against the raw ``dialect`` attribute from the XML:

    * a blank cell (or no ``dialect`` column at all) — the rule is universal and
      applies to every dialect;
    * a named dialect that matches — the rule applies;
    * the literal token ``default`` — the rule is the fallback, applied only to
      dialects that no rule names explicitly (so a named dialect uses its own
      rules instead of the fallback).
    """
    rules_path = tsv_path.with_suffix(".rules.tsv")
    if not rules_path.exists():
        return ()

    parsed = []
    with rules_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        required = {"pattern", "replacement", "description"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(
                f"{rules_path} must contain columns {sorted(required)}"
            )
        for line_number, row in enumerate(reader, start=2):
            pattern = row["pattern"]
            if not pattern:
                raise ValueError(f"{rules_path}:{line_number}: empty pattern")
            replacement = row["replacement"]
            if "\\" in replacement:
                raise ValueError(
                    f"{rules_path}:{line_number}: replacements must be literal; "
                    "use lookarounds instead of capture references"
                )
            try:
                compiled = re.compile(pattern)
            except re.error as error:
                raise ValueError(
                    f"{rules_path}:{line_number}: invalid regex: {error}"
                ) from error
            dialects = frozenset(
                token.strip()
                for token in (row.get("dialect") or "").split(",")
                if token.strip()
            )
            parsed.append(
                (PhonologyRule(compiled, replacement, row["description"].strip()),
                 dialects)
            )

    # A dialect is "named" if any rule scopes itself to it (the reserved
    # ``default`` token is not a dialect name). The fallback rules apply only
    # when the requested dialect is not named anywhere.
    named = {name for _, dialects in parsed for name in dialects} - {"default"}
    fallback_active = dialect not in named

    applicable = []
    for rule, dialects in parsed:
        if (
            not dialects
            or dialect in dialects
            or ("default" in dialects and fallback_active)
        ):
            applicable.append(rule)
    return tuple(applicable)


def load_profile(
    scheme: str,
    language: str,
    dialect: str,
    *,
    target_column: str | None = None,
) -> PhonologyProfile | None:
    """Load one language profile and its optional ordered rule sidecar."""
    path = ORTHOGRAPHIES_PATH / scheme / f"{language}.tsv"
    if not path.exists():
        return None

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        selected = _select_target_column(
            fieldnames,
            language,
            dialect,
            explicit=target_column,
        )
        mappings = []
        ipa_characters = set()
        for row in reader:
            letter = (row.get("letter") or "").strip()
            value = (row.get(selected) or "").strip()
            if not letter or value == "NA":
                continue
            mappings.append((letter, value))
            ipa_characters.update(value)

    rules = _load_rules(path, dialect)
    for rule in rules:
        ipa_characters.update(rule.replacement)
    return PhonologyProfile(
        mappings=tuple(mappings),
        ipa_characters=frozenset(ipa_characters),
        rules=rules,
    )


def apply_phonology_mappings(
    text: str,
    phonology_mappings: tuple[tuple[str, str], ...]
    | list[tuple[str, str]],
) -> str:
    """Apply longest grapheme mappings without remapping generated IPA."""
    result = text.replace("=", "").replace("<", "").replace(">", "")
    mapped_letters = {letter for letter, _replacement in phonology_mappings}
    if "-" not in mapped_letters:
        result = result.replace("-", "")

    ordered = sorted(
        enumerate(phonology_mappings),
        key=lambda item: (-len(item[1][0]), item[0]),
    )
    output = []
    index = 0
    while index < len(result):
        exact = next(
            (
                (letter, replacement)
                for _position, (letter, replacement) in ordered
                if result.startswith(letter, index)
            ),
            None,
        )
        match = exact
        if match is None:
            match = next(
                (
                    (letter, replacement)
                    for _position, (letter, replacement) in ordered
                    if result[index : index + len(letter)].casefold()
                    == letter.casefold()
                ),
                None,
            )
        if match is None:
            output.append(result[index])
            index += 1
            continue
        letter, replacement = match
        output.append(replacement)
        index += len(letter)
    return "".join(output)


def phonologize(text: str, profile: PhonologyProfile) -> str:
    """Convert FORM text with a TSV profile and its ordered contextual rules."""
    # A form that IS a null morpheme has no sound; keep a visible marker so
    # the PHON tier is never empty (the M-level '∅' case).
    if text.strip() == NULL_MARKER:
        return NULL_MARKER
    # Null morphemes inside a larger form are silent: drop the unit before
    # mapping so PHON is clean IPA.
    stripped = _NULL_UNIT_RE.sub("", text)
    if stripped != text:
        text = re.sub(r" {2,}", " ", stripped).strip()
    result = apply_phonology_mappings(
        text,
        profile.mappings,
    )
    for rule in profile.rules:
        result = rule.pattern.sub(rule.replacement, result)

    output = []
    for character in result:
        category = unicodedata.category(character)
        if (
            character in profile.ipa_characters
            or character == "*"
            or character.isspace()
            or category.startswith("M")
        ):
            output.append(character)
        elif character in string.punctuation or category.startswith("P"):
            # Unmapped punctuation is not sound: drop it from PHON. Mapped
            # punctuation (e.g. an orthographic apostrophe) was consumed by
            # the tokenizer above and is unaffected.
            continue
        else:
            output.append("*")
    return "".join(output)


def _form_text(form: ET.Element) -> str:
    return "".join(form.itertext())


def _write_phonology(
    root: ET.Element,
    profile: PhonologyProfile,
    *,
    form_kind: str,
    preserve_existing: bool = False,
) -> int:
    parent_map = {child: parent for parent in root.iter() for child in parent}
    changed = 0
    for form in root.findall(f'.//FORM[@kindOf="{form_kind}"]'):
        parent = parent_map.get(form)
        if parent is None:
            continue
        phon = parent.find(f'PHON[@kindOf="{form_kind}"]')
        if phon is not None and preserve_existing:
            continue
        if phon is None:
            phon = ET.Element("PHON", {"kindOf": form_kind})
            parent.insert(list(parent).index(form) + 1, phon)
        phon.text = phonologize(_form_text(form), profile)
        changed += 1
    return changed


def process_file(path: str, args: argparse.Namespace) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    text_element = root if root.tag == "TEXT" else root.find(".//TEXT")
    if text_element is None:
        print(f"Warning: No <TEXT> element found in file: {path}")
        return

    language_code = (
        text_element.get("xml:lang", "")
        or text_element.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        or text_element.get("lang", "")
    ).strip()
    language = ISO_TO_LANGUAGE.get(language_code, language_code)
    dialect = text_element.get("dialect", "").strip() or "default"
    if not language:
        raise ValueError(f"Language is blank in file: {path}")

    print(f"Processing file: {path} (Language: {language}, Dialect: {dialect})")
    # The standard-tier scheme is declared per language in standards.csv, not
    # hardcoded. None means the language has no designated standard yet.
    scheme = standard_orthography(language) if language in STANDARD_ORTHOGRAPHY_MAP else None
    standard = (
        load_profile(scheme, language, dialect, target_column=args.target_column)
        if scheme
        else None
    )
    original = (
        load_profile(args.orthography, language, dialect)
        if args.orthography
        else None
    )

    if scheme is None:
        print(
            f"Warning: no designated standard orthography for {language}; "
            "skipping standard PHON"
        )
    elif standard is None:
        print(
            f"Warning: Standard orthography TSV not found for {language}: "
            f"{ORTHOGRAPHIES_PATH / scheme / f'{language}.tsv'}"
        )
    if args.orthography and original is None:
        print(
            f"Warning: Custom orthography TSV not found for {language}: "
            f"{ORTHOGRAPHIES_PATH / args.orthography / f'{language}.tsv'}"
        )
    if standard is None and original is None:
        return

    changed = 0
    if standard is not None:
        changed += _write_phonology(root, standard, form_kind="standard")
    if original is not None:
        changed += _write_phonology(
            root,
            original,
            form_kind="original",
            preserve_existing=args.preserve_existing_original,
        )
    if not changed:
        print(f"File: {path} had no matching FORM tiers")
        return

    xml_string = prettify(root)
    xml_string = "\n".join(
        line for line in xml_string.split("\n") if line.strip()
    )
    Path(path).write_text(xml_string, encoding="utf-8")
    print(f"File: {path} processed successfully")


def main(args: argparse.Namespace) -> int:
    failures = 0
    for corpus in get_exploration_targets(args.corpora_path):
        if ".DS_Store" in corpus:
            continue
        print(f"Processing corpus: {corpus}")
        files = (
            [corpus]
            if os.path.isfile(corpus) and corpus.endswith(".xml")
            else get_files(corpus, args.language)
        )
        for path in files:
            try:
                process_file(path, args)
            except (ET.ParseError, OSError, ValueError) as error:
                failures += 1
                print(f"Error processing {path}: {error}", file=sys.stderr)
    return 1 if failures else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate FormosanBank PHON tiers")
    parser.add_argument(
        "--orthography",
        help=(
            "orthography folder used to generate original PHON; standard PHON "
            "continues to use Ortho113 when that language table exists"
        ),
    )
    parser.add_argument(
        "--target_column",
        help="explicit Ortho113 IPA column (default: resolve from dialect)",
    )
    parser.add_argument("--corpora_path", required=True, help="corpus or XML path")
    parser.add_argument("--language", help="optional language-name path filter")
    parser.add_argument(
        "--preserve-existing-original",
        "--preserve_existing_original",
        action="store_true",
        help="keep source-supplied original PHON instead of regenerating it",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    if args.orthography:
        orthography_path = ORTHOGRAPHIES_PATH / args.orthography
        if not orthography_path.exists():
            parser.error(f"The orthography doesn't exist: {orthography_path}")
    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered corpora path doesn't exist: {args.corpora_path}")
    valid_languages = set(ISO_TO_LANGUAGE.values()) | {"Truku"}
    if args.language and args.language not in valid_languages:
        parser.error(
            f"Enter a valid Formosan language from the list: {sorted(valid_languages)}"
        )
    raise SystemExit(main(args))
