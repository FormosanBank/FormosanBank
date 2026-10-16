#!/usr/bin/env python3
"""Expand source-marked optional and slash alternatives deterministically."""

from __future__ import annotations

import argparse
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import os
import re
import sys
from typing import Any


# QC/utilities/parentheticals.py decides what a parenthesis is; see POL-024 and
# the maintainer's rule of 2026-09-10 that equal counts on the two sides mean
# the parentheses are about the same thing.
_FB = os.environ.get("FORMOSANBANK_PATH")
if _FB:
    sys.path.insert(0, _FB)
else:
    for _parent in Path(__file__).resolve().parents:
        if (_parent / "QC" / "utilities" / "parentheticals.py").is_file():
            sys.path.insert(0, str(_parent))
            break
from QC.utilities.parentheticals import split_in_step  # noqa: E402
from build_xml import THAO_PARTICLES  # noqa: E402
from QC.utilities.slash_alternatives import resolve_scope  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "CodeAndDocs" / "extracted-records.json"
SLASH_PATH = ROOT / "CodeAndDocs" / "slash-alternatives.json"
SLASH_TRANSLATION_PATH = ROOT / "CodeAndDocs" / "slash-translations.json"
OUTPUT_PATH = ROOT / "CodeAndDocs" / "expanded-records.json"

#: A bracket with whitespace (or the string edge) on BOTH sides: the material
#: is a separate token, so the sentence is really two and POL-026 expands it.
OPTION_RE = re.compile(r"(?:(?<=\s)|(?<=^))\(([^()]*)\)(?=\s|$)")

#: A bracket attached to a word - `mashta(y)`, `ihu-(n)`, `(ma)-mamuri`,
#: `shi-a-ucuc(-an)` - is not optional material at all. It is one lexeme spelt
#: two ways, and the two spellings belong in one sentence as a FORM and its
#: `ver="alt"` variant (POL-028), not in two sentences (maintainer,
#: 2026-09-11). 21 records in the book, and none mixes the two shapes.
WORD_INTERNAL_RE = re.compile(r"\(([^()]*)\)")


def word_internal_variants(value: str) -> tuple[str, str | None]:
    """``(base, variant)`` for a bracket attached to a word, else ``(value, None)``.

    The base is the reading WITHOUT the bracketed material, which is what the
    variants vary from: `(ma)-mamuri` is `mamuri` plus an optional `ma-`,
    `ihu-(n)` is `ihu` plus an optional oblique `-n`.
    """
    if OPTION_RE.search(value) or not WORD_INTERNAL_RE.search(value):
        return value, None
    without = _normalize_form(WORD_INTERNAL_RE.sub("", value))
    with_it = _normalize_form(value.replace("(", "").replace(")", ""))
    if without == with_it:
        return value, None
    return without, with_it


def _normalize_form(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"(^|\s)–", r"\1", value)
    value = re.sub(r"–(?=$|[\s,.;:?!)])", "", value)
    value = re.sub(r"\s+([,.;:?!])", r"\1", value)
    return value


def expand_optional(value: str) -> list[tuple[str, tuple[str, ...]]]:
    """Return all source-marked optional variants in stable out/in order."""
    states: list[tuple[str, tuple[str, ...]]] = [(value, ())]
    option_number = 0
    while any(OPTION_RE.search(text) for text, _labels in states):
        option_number += 1
        next_states: list[tuple[str, tuple[str, ...]]] = []
        for text, labels in states:
            match = OPTION_RE.search(text)
            if match is None:
                next_states.append((text, labels))
                continue
            prefix = text[: match.start()]
            suffix = text[match.end() :]
            next_states.append(
                (
                    _normalize_form(prefix + suffix),
                    labels + (f"opt{option_number:02d}out",),
                )
            )
            next_states.append(
                (
                    _normalize_form(prefix + match.group(1) + suffix),
                    labels + (f"opt{option_number:02d}in",),
                )
            )
        states = next_states

    unique: list[tuple[str, tuple[str, ...]]] = []
    seen: set[str] = set()
    for text, labels in states:
        text = _normalize_form(text)
        if text not in seen:
            unique.append((text, labels))
            seen.add(text)
    return unique


def _variant_id(
    source_id: str,
    slash_number: int | None,
    optional_labels: tuple[str, ...],
) -> str:
    suffixes: list[str] = []
    if slash_number is not None:
        suffixes.append(f"alt{slash_number:02d}")
    suffixes.extend(optional_labels)
    return source_id if not suffixes else source_id + "-" + "-".join(suffixes)


def _split_translation(
    translation_key: str, translation: str, options: int
) -> list[str] | None:
    """One English reading per slash option, or None to keep sharing one."""
    if options < 2 or SLASH_TRANSLATIONS is None:
        return None
    curated = SLASH_TRANSLATIONS.get(translation_key)
    if curated is not None:
        if len(curated) != options:
            raise ValueError(f"curated translation count for {translation_key!r}")
        return curated
    if "/" not in translation:
        return None
    scope = resolve_scope(translation)
    if scope.confidence == "low" or len(scope.options) != options:
        return None
    return scope.options


def expand_dictionary(
    records: list[dict[str, Any]],
    slash_map: dict[str, list[str]],
) -> list[dict[str, Any]]:
    source_slash_ids = {record["id"] for record in records if "/" in record["source"]}
    if source_slash_ids != set(slash_map):
        missing = sorted(source_slash_ids - set(slash_map))
        extra = sorted(set(slash_map) - source_slash_ids)
        raise ValueError(f"slash inventory mismatch: missing={missing}, extra={extra}")

    expanded: list[dict[str, Any]] = []
    for record in records:
        source_id = record["id"]
        slash_options = slash_map.get(source_id, [record["source"]])
        if len(slash_options) != len(set(slash_options)):
            raise ValueError(f"duplicate slash option for {source_id}")
        for slash_index, slash_form in enumerate(slash_options, start=1):
            if "/" in slash_form:
                raise ValueError(f"unexpanded slash in curated option for {source_id}")
            slash_number = slash_index if source_id in slash_map else None
            # When the Thao and the English carry the same number of
            # parentheticals they are about the same thing, so the translation
            # is expanded in step rather than copied to both readings: the
            # reading without `sa pagka` must not still say "a chair".
            in_step = split_in_step(
                slash_form, str(record["translation"]),
                never_pairs=THAO_PARTICLES,
            )
            # When the English carries a slash too, the two sides are about the
            # same thing and the readings must not share one translation that
            # still says both: `yakin/yamin` glosses `me/us`, so reading 1 is
            # "Why do you hate me?" and reading 2 "Why do you hate us?"
            # (maintainer, 2026-09-11). The scope is resolved by the shared
            # utility, which is token-based and serves either language; the one
            # record it cannot settle is curated.
            english = _split_translation(
                str(record["source"]), str(record["translation"]), len(slash_options)
            )
            for index, (form, optional_labels) in enumerate(
                expand_optional(slash_form)
            ):
                variant = deepcopy(record)
                variant["id"] = _variant_id(
                    source_id,
                    slash_number,
                    optional_labels,
                )
                variant["source_record_id"] = source_id
                variant["source_raw"] = record["source"]
                # A bracket attached to a word is one lexeme spelt two ways,
                # not two sentences: the readings go in one S as a FORM and its
                # ver="alt" variant.
                base, alternate = word_internal_variants(form)
                variant["source"] = base
                if alternate is not None:
                    variant["alternate"] = alternate
                if english is not None and slash_number is not None:
                    variant["translation"] = english[slash_number - 1]
                if in_step is not None and index < len(in_step):
                    paired_form, paired_translation = in_step[index]
                    if paired_form == form:
                        variant["translation"] = paired_translation
                variant["expansion"] = {
                    "slash_option": slash_number,
                    "optional_choices": list(optional_labels),
                }
                expanded.append(variant)

    ids = [record["id"] for record in expanded]
    if len(ids) != len(set(ids)):
        raise ValueError("expanded dictionary IDs are not unique")
    for record in expanded:
        if any(character in record["source"] for character in "()/"):
            raise ValueError(
                f"unexpanded notation in {record['id']}: {record['source']!r}"
            )
    return expanded


def _expand_text_sentence(sentence: dict[str, Any]) -> list[dict[str, Any]]:
    word_options: list[list[tuple[dict[str, Any] | None, str]]] = []
    has_optional = False
    for word in sentence["words"]:
        variants = expand_optional(word["form"])
        if len(variants) == 1:
            word_options.append([(deepcopy(word), "")])
            continue
        has_optional = True
        gloss = word["gloss"]
        gloss_variants = expand_optional(gloss) if gloss is not None else []
        plain_gloss = gloss is not None and len(gloss_variants) == 1
        if (
            gloss is not None
            and not plain_gloss
            and len(gloss_variants) != len(variants)
        ):
            raise ValueError(
                f"optional form/gloss mismatch in sentence {sentence['number']}: "
                f"{word!r}"
            )
        choices: list[tuple[dict[str, Any] | None, str]] = []
        for index, (form, labels) in enumerate(variants):
            label = "-".join(labels)
            if labels[-1].endswith("out") and not form:
                choices.append((None, label))
                continue
            variant_word = deepcopy(word)
            variant_word["form"] = form
            if gloss is not None:
                variant_word["gloss"] = (
                    gloss_variants[0][0]
                    if plain_gloss
                    else gloss_variants[index][0]
                )
            choices.append((variant_word, label))
        word_options.append(choices)

    if not has_optional:
        return [deepcopy(sentence)]

    result: list[dict[str, Any]] = []
    for combination in product(*word_options):
        variant = deepcopy(sentence)
        variant["words"] = [word for word, _label in combination if word is not None]
        variant["form"] = " ".join(word["form"] for word in variant["words"])
        labels = [label for _word, label in combination if label]
        variant["variant_suffix"] = "-".join(labels)
        variant["source_form_raw"] = sentence["form"]
        result.append(variant)
    return result


def expand_texts(texts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = deepcopy(texts)
    for text in result:
        expanded_sentences: list[dict[str, Any]] = []
        for sentence in text["sentences"]:
            expanded_sentences.extend(_expand_text_sentence(sentence))
        text["sentences"] = expanded_sentences
    return result


SLASH_TRANSLATIONS = json.loads(
    SLASH_TRANSLATION_PATH.read_text(encoding="utf-8")
) if SLASH_TRANSLATION_PATH.exists() else {}


def payload() -> dict[str, Any]:
    source = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    slash_map = json.loads(SLASH_PATH.read_text(encoding="utf-8"))
    texts = expand_texts(source["texts"])
    dictionary = expand_dictionary(source["dictionary_examples"], slash_map)
    text_sentences = sum(len(text["sentences"]) for text in texts)
    word_count = sum(
        len(sentence["words"])
        for text in texts
        for sentence in text["sentences"]
    )
    return {
        "source_pdf_sha256": source["source_pdf_sha256"],
        "source_extraction": str(INPUT_PATH.relative_to(ROOT)),
        "slash_inventory": str(SLASH_PATH.relative_to(ROOT)),
        "policy": {
            "optional_material": "POL-026",
            "slash_alternatives": "POL-027",
        },
        "texts": texts,
        "dictionary_examples": dictionary,
        "statistics": {
            "raw_dictionary_examples": len(source["dictionary_examples"]),
            "raw_text_sentences": source["statistics"]["text_sentences"],
            "slash_source_records": len(slash_map),
            "optional_dictionary_source_records": sum(
                "(" in record["source"]
                for record in source["dictionary_examples"]
            ),
            "expanded_dictionary_sentences": len(dictionary),
            "expanded_text_sentences": text_sentences,
            "expanded_interlinear_words": word_count,
            "total_sentences": len(dictionary) + text_sentences,
        },
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="compare expansions with committed data"
    )
    args = parser.parse_args()
    current = serialized(payload())
    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"Missing expansion: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        if OUTPUT_PATH.read_text(encoding="utf-8") != current:
            print("Expansion differs from expanded-records.json", file=sys.stderr)
            return 1
        print("Expansion matches expanded-records.json")
        return 0
    OUTPUT_PATH.write_text(current, encoding="utf-8")
    statistics = json.loads(current)["statistics"]
    print(f"Wrote {OUTPUT_PATH}")
    print(json.dumps(statistics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
