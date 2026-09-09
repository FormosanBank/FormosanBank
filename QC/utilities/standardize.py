import copy
import os
import xml.etree.ElementTree as ET
import argparse
import re
import csv
import sys
import unicodedata
from pathlib import Path

from lxml import etree

# Make the QC package importable so we can reuse the shared dialect inventory
# (the same single-vs-multi-dialect source used by fix_dialects.py and V036).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.utilities._accents import (  # noqa: E402
    standard_orthography_accents,
    strip_accents,
)
from QC.utilities._case_variants import (  # noqa: E402
    derive_case_variants,
    load_profile_graphemes,
    resolve_source_profile,
)
from QC.validation._dialect_inventory import (  # noqa: E402
    ISO_TO_LANGUAGE,
    is_multi_dialect_language,
)
from QC.cleaning.clean_xml import CleanerWarnings  # noqa: E402
from QC.corpus_counts import LANG_CODE_TO_NAME as _ISO_TO_LANG_NAME  # noqa: E402  (languages.csv, POL-039)



_HYPHEN_IS_LETTER_CACHE: dict = {}


def _resolve_ortho_path(ortho_path: str | None) -> Path:
    """Return the canonical orthography directory.

    If ortho_path is None, default to <repo>/Orthographies/Ortho113/
    relative to clean_xml.py's location.
    """
    if ortho_path is not None:
        return Path(ortho_path)
    return Path(__file__).resolve().parents[2] / "Orthographies" / "Ortho113"


def _hyphen_is_letter(lang_code: str, ortho_path: str | None = None) -> bool:
    """Return True if '-' appears as a letter row in the canonical orthography.

    Looks up <ortho_path>/<Language>.tsv (where Language is the human-readable
    name resolved from the ISO 639-3 code via _ISO_TO_LANG_NAME). Cached after
    first lookup per (lang_code, ortho_path) pair.

    Empirically verified 2026-05-29: only Bunun (bnn) and Thao (ssf) return True.
    """
    cache_key = (lang_code, ortho_path)
    if cache_key in _HYPHEN_IS_LETTER_CACHE:
        return _HYPHEN_IS_LETTER_CACHE[cache_key]

    lang_name = _ISO_TO_LANG_NAME.get(lang_code)
    if lang_name is None:
        _HYPHEN_IS_LETTER_CACHE[cache_key] = False
        return False

    tsv_path = _resolve_ortho_path(ortho_path) / f"{lang_name}.tsv"
    if not tsv_path.exists():
        _HYPHEN_IS_LETTER_CACHE[cache_key] = False
        return False

    found = False
    try:
        with open(tsv_path, encoding="utf-8") as f:
            for line in f:
                # Each row's first column is a letter. We treat any row whose
                # first column is exactly '-' as evidence that hyphen is a
                # letter in this orthography.
                cols = line.split("\t")
                if cols and cols[0].strip() == "-":
                    found = True
                    break
    except OSError:
        found = False

    _HYPHEN_IS_LETTER_CACHE[cache_key] = found
    return found


_SEG_HYPHEN = re.compile(r"-")


def _strip_seg_hyphens(text: str) -> str:
    """Strip segmentation hyphens, with two exceptions:

    - a '-' flanked by digits on both sides survives (dates, number/verse
      ranges, e.g. 2020-07-31, 3:2-5, 8-11);
    - a '-' adjacent to the null-morpheme marker '∅' survives — it is part
      of the null unit ('∅-' / '-∅'), which remove_null_units() strips as a
      whole. In the normal call order nulls are already gone by the time
      C012 runs, but stripping the bridging hyphen here would fuse the
      marker into the word ('∅dhuq') if that order ever changed.
    """
    def _replace(match: "re.Match[str]") -> str:
        i = match.start()
        prev = match.string[i - 1] if i > 0 else ""
        nxt = match.string[i + 1] if i + 1 < len(match.string) else ""
        if prev == "∅" or nxt == "∅":
            return "-"
        if prev.isdigit() and nxt.isdigit():
            return "-"
        return ""

    return _SEG_HYPHEN.sub(_replace, text)


def _process_standard_hyphens(
    text: str,
    xml_file: str,
    s_id: "str | None",
    lang_code: "str | None",
    warnings: "CleanerWarnings | None",
    hard_remove_segmentation: bool,
    ortho_path: "str | None",
) -> str:
    """Per C012: handle hyphens in S-level standard FORM by orthography.

    If '-' is NOT a letter in the canonical orthography (the common case),
    strip hyphens AND clitic '=' markers silently. If '-' IS a letter
    (Bunun, Thao), preserve hyphens and emit a c012 warning per occurrence
    (unless --hard-remove-segmentation is set, in which case strip anyway
    and DO NOT warn).

    The '=' clitic marker is always stripped (it's never a letter).

    Null morphemes are NOT deleted here (they were prior to the 2026-08-09
    null-morpheme spec): remove_null_units() strips them from S-level
    standard FORMs before C012 runs, and clean_xml normalizes the marker
    glyph to '∅' (U+2205). C012 only guarantees it never destroys a null
    unit — hyphens adjacent to '∅' are skipped when stripping (see
    _strip_seg_hyphens) and skipped by the hyphen-is-letter warning (they
    are annotation, not letters).
    """
    if lang_code and _hyphen_is_letter(lang_code, ortho_path):
        if hard_remove_segmentation:
            return _strip_seg_hyphens(text).replace("=", "")
        # Preserve hyphens, warn per occurrence — but skip null-adjacent
        # hyphens (annotation, not letters).
        if warnings is not None:
            for i, ch in enumerate(text):
                if ch != "-":
                    continue
                if (i > 0 and text[i - 1] == "∅") or (
                    i + 1 < len(text) and text[i + 1] == "∅"
                ):
                    continue
                warnings.add("c012", xml_file, s_id, ch, i)
        return text.replace("=", "")  # clitic stripped even when preserving '-'
    # Hyphen is not a letter → strip both
    return _strip_seg_hyphens(text).replace("=", "")


def _apply_standard_hyphens(element, lang_code, ortho_path, hard_remove,
                            warnings, file_path, segmented_without_m=False):
    """Apply C012 to an S element's standard FORM. No-op for W/M (they keep
    segmentation) and for elements without a standard FORM.

    The M tier is C012's proxy for "this sentence is morpheme-segmented", and
    for almost every corpus it is the right one. It is a proxy, though, not the
    property itself: a corpus can print segmentation hyphens in its FORMs and
    publish no M analysis at all (MontgomeryTexts, Nowbucyang-Truku-Thesis),
    and there C012 declines to fire on a sentence that plainly is segmented.

    `segmented_without_m` (CLI `--segmented-without-m-tier`) is the opt-in for
    exactly that shape. It is off by default and must stay off by default: an
    S-level standard FORM can carry a hyphen for reasons that are not
    segmentation -- hyphenated proper nouns in Wikipedias, the morpheme and
    orthographic hyphens Siraya_Gospels deliberately keeps -- and 15,855
    sentences across 12 corpora would be caught by a blanket widening of the
    guard (measured 2026-09-07). Whether a corpus's hyphens are segmentation is
    a per-corpus judgement, so it is a per-corpus flag.

    After C012, emits c022 for any '*' character found in the resulting
    standard FORM text.
    """
    if element.tag != "S":
        return
    if element.find(".//M") is None and not segmented_without_m:
        return  # C012 only on morpheme-segmented sentences (has an <M> tier)
    # Every standard-tier FORM: the tier's base and each ver="alt" variant
    # (POL-028). findall returns one element for data without variants, so
    # this is a no-op change for a corpus that has none.
    for form in element.findall("FORM[@kindOf='standard']"):
        if not form.text:
            continue
        new_text = _process_standard_hyphens(
            form.text, file_path, element.get("id"), lang_code,
            warnings, hard_remove, ortho_path,
        )
        if new_text != form.text:
            form.text = new_text
        if warnings is not None and form.text and "*" in form.text:
            for i, ch in enumerate(form.text):
                if ch == "*":
                    warnings.add("c022", file_path, element.get("id"), ch, i)


from QC.utilities._prettify import prettify  # noqa: E402,F401  (shared, mixed-content-safe, idempotent)


def get_files(path, language):
    to_check = []
    if language:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".xml") and re.findall(language, os.path.join(root)): # and 'Final_XML' in os.path.join(root, file)
                    to_check.append(os.path.join(root, file))
        return to_check
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"): # and 'Final_XML' in os.path.join(root, file)
                to_check.append(os.path.join(root, file))

    return to_check


def get_exploration_targets(corpora_path, corpus=None):
    if corpus:
        return [os.path.join(corpora_path, corpus)]
    if os.path.isfile(corpora_path) and corpora_path.endswith('.xml'):
        return [corpora_path]
    return [os.path.join(corpora_path, x) for x in os.listdir(corpora_path)]

def _attested_accents(lang_code, dialect=None):
    """Accented letters this language's designated standard orthography lists.

    Thin wrapper over _accents.standard_orthography_accents, resolving the
    ISO code to a language name first. ``dialect`` is accepted and ignored:
    an orthography table's ``letter`` column is shared across its dialect
    value columns, so the letter inventory does not vary by dialect.
    """
    language = _ISO_TO_LANG_NAME.get((lang_code or "").strip())
    return standard_orthography_accents(language) if language else frozenset()


# Conversion rules are staged through Private Use Area placeholders so that no
# rule can rewrite another rule's output. The range is far larger than any
# table (6,400 code points against fewer than a hundred rules) and no Formosan
# orthography uses it.
_PUA_FIRST = 0xE000
_PUA_LAST = 0xF8FF


def _marker(index):
    codepoint = _PUA_FIRST + index
    if codepoint > _PUA_LAST:
        raise ValueError(
            f"conversion table needs {index + 1} placeholders; only "
            f"{_PUA_LAST - _PUA_FIRST + 1} are available"
        )
    return chr(codepoint)


def apply_standard(s_element, standard, keep=frozenset()):
    """Transliterate every standard-tier FORM on this node.

    Covers the tier's base and each ver="alt" variant (POL-028): a variant is
    a reading of the standard tier and is transliterated like one, so the pair
    stays in the same orthography. Before variants existed this was a single
    FORM, and findall still returns exactly one for data without them.

    Within each FORM, every rule is staged through a placeholder, longest
    source first, so a rule's *output* is never matched by another rule.
    Without that, a table written in the usual digraph-first idiom silently
    misconverts: with ``ll -> ll`` guarding ``l -> lr``, sequential replacement
    turns ``ll`` into ``lrlr``. Longest-first is what makes the idiom hold even
    when the table lists the short rule first.

    Diacritic-bearing sources are staged in a first pass, before the general
    stress-mark cleanup, so a table can distinguish a real orthographic letter
    such as ä from an otherwise unlisted stressed á. Everything else is staged
    after that cleanup, because a rule source is bare by definition and must
    see the text the cleanup produced.
    """
    for form in s_element.findall("FORM[@kindOf='standard']"):
        if not form.text:
            continue
        if any(_PUA_FIRST <= ord(char) <= _PUA_LAST for char in form.text):
            raise ValueError(
                f"{s_element.get('id')}: standard FORM contains a Private Use "
                f"Area character, which collides with conversion placeholders"
            )

        staged = []
        deferred = []
        for original, replacement in standard:
            decomposed = unicodedata.normalize("NFD", original)
            if any(unicodedata.category(char).startswith("M") for char in decomposed):
                marker = _marker(len(staged))
                form.text = form.text.replace(original, marker)
                staged.append((marker, replacement))
            else:
                deferred.append((original, replacement))

        # The original tier is never touched here. Unprotected diacritics are
        # treated as source stress/prosody and removed from the standard tier.
        form.text = strip_accents(form.text, keep=keep)

        for original, replacement in sorted(deferred, key=lambda rule: -len(rule[0])):
            if original and original in form.text:
                marker = _marker(len(staged))
                form.text = form.text.replace(original, marker)
                staged.append((marker, replacement))

        for marker, replacement in staged:
            form.text = form.text.replace(marker, replacement)


# Null-morpheme units in an S-level standard FORM: the canonical marker
# '∅' (U+2205) plus one bridging segmentation hyphen. Removed as a unit
# so no dangling hyphen is left (matters where '-' is a letter: Bunun,
# Thao). Must run BEFORE any hyphen stripping elsewhere in the pipeline,
# while units are still recognizable.
#
# A '∅' introduced by an asterisk is a *reconstruction label*, not a null
# morpheme: in '*-∅' the asterisk marks a Neogrammarian reconstruction and
# the '∅' names the reconstructed segment — it is the content of the label,
# not the absence of a morpheme. Stripping it leaves a bare '*' that means
# nothing (SEALS33 S25, 'tgbukuy *-ʔ, *-h, ma *-∅', where the third label
# became 'ma *'). The reconstruction alternative is listed first so an
# asterisked label is consumed whole and kept, before the plain null-unit
# alternatives can match its '∅'.
#
# This is the only reading of '*' that survives into a published FORM:
# POL-016 excludes source-ungrammatical examples at intake, so a '*' left
# in the bank is notation, not a grammaticality judgement.
_NULL_UNIT_RE = re.compile(r"\*-?∅|∅-|-∅|∅")


def _drop_unless_reconstruction(match):
    """Keep an asterisked reconstruction label; drop a real null unit."""
    return match.group(0) if match.group(0).startswith("*") else ""


def remove_null_units(element):
    """Remove null-morpheme units from an element's standard FORM.

    Called for S elements only (never W/M — the morpheme tier is where a
    null is meaningful) and never in --copy mode (pure duplication).
    Asterisked reconstruction labels ('*-∅') are left intact.
    """
    for form in element.findall("FORM[@kindOf='standard']"):
        if not form.text:
            continue
        stripped = _NULL_UNIT_RE.sub(_drop_unless_reconstruction, form.text)
        if stripped != form.text:
            form.text = re.sub(r" {2,}", " ", stripped).strip()


def _copy_mixed_content(src, dst):
    """Replace dst's text and children with a deep copy of src's.

    Used by create_standard so that mixed-content children — currently
    just <UNCLEAR/> — are preserved when duplicating original → standard.
    A plain `dst.text = src.text` drops UNCLEAR (an element child, not
    text), which would silently strip the "audio is unintelligible"
    marker from the standard tier and trigger V017 (empty FORM) under
    the 2026-06-08 schema.
    """
    for child in list(dst):
        dst.remove(child)
    dst.text = src.text
    for child in src:
        dst.append(copy.deepcopy(child))


def create_standard(element, file_path=None):
    # Bases lack ver; _sync_standard_variants handles the variant FORMs.
    original_form = next(
        (f for f in element.findall("FORM[@kindOf='original']") if f.get("ver") is None),
        None,
    )
    standard_form = next(
        (f for f in element.findall("FORM[@kindOf='standard']") if f.get("ver") is None),
        None,
    )

    if original_form is None:
        s_id = element.get('id', '<unknown>')
        location = f" in {file_path}" if file_path else ""
        print(
            f"Error: S id={s_id!r}{location} has no original base (kindOf='original' without ver). "
            f"Cannot create standard tier.",
            file=sys.stderr,
        )
        sys.exit(1)

    if standard_form is not None:
        # Standard form exists, replace its content with original's
        _copy_mixed_content(original_form, standard_form)
    else:
        # No standard form exists, create one
        original_form.set("kindOf", "original")

        new_form = ET.Element("FORM")
        new_form.set("kindOf", "standard")
        _copy_mixed_content(original_form, new_form)
        # Directly after the last original-tier FORM, so the tiers stay
        # grouped once variants exist (POL-028). For a node with a single
        # original FORM — every node in every corpus that has not migrated —
        # that index is 1, exactly where this always inserted.
        last_original = element.findall("FORM[@kindOf='original']")[-1]
        element.insert(list(element).index(last_original) + 1, new_form)

    _sync_standard_variants(element)


def _sync_standard_variants(element):
    """Mirror the original tier's ver="alt" variants into the standard tier.

    POL-028 (revised 2026-09-09): a variant reading is a FORM whose ``kindOf``
    names its tier plus ``ver="alt"``, and variants exist for both tiers. The
    standard tier is derived (POL-002), so its variants are derived too — one
    standard variant per original variant, in the original's order, seeded
    with the original's text for the caller's transliteration pass to rewrite.

    Surplus standard variants are deleted rather than left: a variant the
    original no longer has is a variant of nothing, and leaving it would make
    the standard tier something other than a function of the original.

    A corpus with no ``ver`` FORMs has no original variants and no standard
    ones, so both loops are empty and the element is untouched — which is why
    this is a no-op for every corpus that has not migrated yet.
    """
    originals = [
        f for f in element.findall("FORM[@kindOf='original']")
        if f.get("ver") is not None
    ]
    standards = [
        f for f in element.findall("FORM[@kindOf='standard']")
        if f.get("ver") is not None
    ]

    for surplus in standards[len(originals):]:
        element.remove(surplus)

    for index, source in enumerate(originals):
        if index < len(standards):
            target = standards[index]
            target.set("ver", source.get("ver"))
            _copy_mixed_content(source, target)
            continue
        target = ET.Element("FORM")
        target.set("kindOf", "standard")
        target.set("ver", source.get("ver"))
        _copy_mixed_content(source, target)
        # After the last standard-tier FORM, so the tier stays contiguous.
        anchor = element.findall("FORM[@kindOf='standard']")[-1]
        element.insert(list(element).index(anchor) + 1, target)

def main(args):
    # Handle copy mode vs normal standardization mode
    if args.copy:
        available_columns = None
        print("Running in copy mode - copying original text to standard form")
    elif args.remove_accents:
        available_columns = None
        print("Running in remove_accents mode - copying original to standard, then deleting accents")
    else:
        # Load the TSV file to get available columns
        with open(args.tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            available_columns = reader.fieldnames

        # Resolve the source-orthography profile from the table's filename
        # so capital-letter variants of lowercase rules can be derived —
        # except for capitals the profile declares as distinct graphemes.
        profile_graphemes = None
        profile_path = resolve_source_profile(args.tsv_path)
        if profile_path is None:
            print(
                f"Warning: {os.path.basename(args.tsv_path)} does not follow the "
                "Orthographies/ConversionTables/<Language>_<Scheme>_113.tsv "
                "convention; capital-letter variants will NOT be derived."
            )
        elif not profile_path.exists():
            print(
                f"Warning: source orthography profile not found at {profile_path}; "
                "capital-letter variants will NOT be derived."
            )
        else:
            try:
                profile_graphemes = load_profile_graphemes(profile_path)
            except ValueError as e:
                print(f"Warning: {e}; capital-letter variants will NOT be derived.")

    warnings = CleanerWarnings(Path(args.corpora_path) / "standardize_warnings.csv")

    to_explore = get_exploration_targets(args.corpora_path, args.corpus)

    for corpus in to_explore:
        print(f"Processing corpus: {corpus}")
        if ".DS_Store" in corpus:
            continue
        
        # Check if corpus is a file or directory
        if os.path.isfile(corpus) and corpus.endswith('.xml'):
            files = [corpus]
        else:
            files = get_files(corpus, args.language)
            
        if files:
            for file in files:
                try:
                    # Parse the XML file
                    tree = ET.parse(file)
                    root = tree.getroot()
                    lang_code = (
                        root.get("{http://www.w3.org/XML/1998/namespace}lang")
                        or root.get("xml:lang")
                        or root.get("lang")
                    )
                    # Accented letters this language's reference orthography
                    # attests are real letters, not source prosody, so they
                    # survive the standard-tier accent cleanup.
                    keep_accents = _attested_accents(lang_code, root.get("dialect"))

                    if args.copy:
                        # In copy mode, just copy original to standard.
                        # --copy is a PURE duplication (2026-08-09 ruling):
                        # no C012 hyphen handling, no null-unit removal. The
                        # standard tier keeps segmentation and null units;
                        # V120/V133 flag them SOFT as "re-standardize when a
                        # conversion table exists" signals.
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                    elif args.remove_accents:
                        # Copy original to standard, then delete accents only.
                        # apply_standard with an empty mapping strips accents and
                        # applies no letter conversion.
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            if element.tag == "S":
                                remove_null_units(element)
                            apply_standard(element, [], keep=keep_accents)
                            _apply_standard_hyphens(
                                element, lang_code, args.ortho_path,
                                args.hard_remove_segmentation, warnings, file,
                                args.segmented_without_m_tier)
                    else:
                        # Normal standardization mode
                        assert available_columns is not None  # loaded in non-copy branch above
                        # Determine target column, driven by whether the language
                        # actually has multiple dialects (per dialects.csv). Single-dialect
                        # languages follow the convention dialect == the language name
                        # (e.g. dialect="Yami"), so the dialect attribute is NOT a column
                        # selector — we use the sole value column ('standard' or whatever
                        # it is named). Multi-dialect languages select by dialect, falling
                        # back to 'standard'.
                        target_column = args.target_column
                        if not target_column:
                            dialect = root.get('dialect')
                            xlang = (
                                root.get('{http://www.w3.org/XML/1998/namespace}lang')
                                or root.get('xml:lang')
                                or root.get('lang')
                                or ''
                            ).strip()
                            language = ISO_TO_LANGUAGE.get(xlang, xlang)
                            value_columns = [c for c in available_columns if c != 'original']
                            if language and is_multi_dialect_language(language):
                                # Multi-dialect: the dialect attribute selects the column.
                                if dialect and dialect in value_columns:
                                    target_column = dialect
                                    print(f"Using dialect-specific column: {dialect}")
                                elif 'standard' in value_columns:
                                    if dialect and dialect not in ('standard', 'unknown'):
                                        print(f"Warning: Dialect '{dialect}' in file '{file}' not in TSV columns {available_columns}; falling back to 'standard' column")
                                    target_column = 'standard'
                                else:
                                    print(
                                        f"Error: Dialect '{dialect}' from file '{file}' is not in TSV columns "
                                        f"{available_columns}, and no 'standard' column exists to fall back to. "
                                        f"Pass --target_column to pick one explicitly.",
                                        file=sys.stderr,
                                    )
                                    sys.exit(1)
                            else:
                                # Single-dialect language (or unresolved xml:lang): use the
                                # sole value column. A dialect attribute that happens to
                                # match a column is still honored.
                                if dialect and dialect in value_columns:
                                    target_column = dialect
                                    print(f"Using dialect-specific column: {dialect}")
                                elif len(value_columns) == 1:
                                    target_column = value_columns[0]
                                elif 'standard' in value_columns:
                                    target_column = 'standard'
                                else:
                                    print(
                                        f"Error: File '{file}' (language '{language or xlang}') has no unique value "
                                        f"column and no 'standard' column in TSV {args.tsv_path}. Available columns: "
                                        f"{available_columns}. Pass --target_column to pick one explicitly.",
                                        file=sys.stderr,
                                    )
                                    sys.exit(1)
                        
                        # Load standardization mappings for this target column
                        standard = []
                        with open(args.tsv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f, delimiter='\t')
                            for row in reader:
                                if target_column in row:
                                    original_value = row.get('original', '').strip()
                                    standard_value = row.get(target_column, '').strip()
                                    # 'NA' means the letter does not occur in this dialect,
                                    # so the row is not a rule at all — the same reading
                                    # validate_conversion_table.py uses. An *empty* cell is
                                    # a rule: it deletes the matched string (Bunun 'w',
                                    # Sakizaya 'x', Wakelin '?').
                                    if original_value and standard_value != 'NA':
                                        standard.append((original_value, standard_value))

                        if profile_graphemes is not None:
                            standard = derive_case_variants(standard, profile_graphemes)

                        # Iterate over all <S> elements
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            if element.tag == "S":
                                remove_null_units(element)
                            apply_standard(element, standard, keep=keep_accents)
                            _apply_standard_hyphens(
                                element, lang_code, args.ortho_path,
                                args.hard_remove_segmentation, warnings, file,
                                args.segmented_without_m_tier)
                        
                    try:
                        xml_string = prettify(root)
                        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
                    except Exception as e:
                        xml_string = ""
                        print(f"Failed to format file: {file}, Error: {e}")

                    with open(file, "w", encoding="utf-8") as xmlfile:
                        xmlfile.write(xml_string)
                        print(f"file: {file} standardized successfully")
                            
                except ET.ParseError:
                    print(f"Error parsing file: {file}")
                except Exception as e:
                    print(f"Unexpected error with file {file}: {e}")

    warnings.write_csv()

if __name__ == "__main__":
    langs = sorted(set(ISO_TO_LANGUAGE.values()) | {'Truku'})
    
    parser = argparse.ArgumentParser(description="Standardize the orthography")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--copy', action='store_true', help='copy original text to standard form without any transformations')
    parser.add_argument('--remove_accents', action='store_true', help='copy original to standard and delete accents (no TSV, no dialectal letter conversion)')
    parser.add_argument('--tsv_path', help='path to TSV file with original and standard columns (not required when using --copy or --remove_accents)')
    parser.add_argument('--target_column', help='column name to use as target for standardization (default: auto-detect from dialect or use "standard")')
    parser.add_argument('--corpora_path', help='path of the corpora')
    parser.add_argument('--corpus', help='if standardization is desired to be applied to a specific corpus -- optional')
    parser.add_argument('--language', help='if standardization is desired to be applied to a specific language -- optional')
    parser.add_argument("--hard-remove-segmentation", dest="hard_remove_segmentation",
                        action="store_true", default=False,
                        help="strip '-' from standard even where it is a letter (Bunun/Thao)")
    parser.add_argument("--segmented-without-m-tier", dest="segmented_without_m_tier",
                        action="store_true", default=False,
                        help="apply C012 hyphen handling to S-level standard FORMs in a "
                             "corpus that is segmented but publishes no M tier "
                             "(MontgomeryTexts, Nowbucyang-Truku-Thesis)")
    parser.add_argument("--ortho-path", dest="ortho_path", default=None,
                        help="orthography dir for the hyphen-is-letter check (default Ortho113)")
    args = parser.parse_args()

    # Validate required arguments
    if sum([bool(args.copy), bool(args.remove_accents), bool(args.tsv_path)]) != 1:
        parser.error("Exactly one of --copy, --remove_accents, or --tsv_path is required.")
    if args.tsv_path and not os.path.exists(args.tsv_path):
        parser.error(f"The TSV file doesn't exist: {args.tsv_path}")
    if not args.corpora_path:
        parser.error("--corpora_path is required.")
    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered corpora path doesn't exists: {args.corpora_path}")
    if args.corpus:
        if os.path.isfile(args.corpora_path):
            parser.error("--corpus cannot be used when --corpora_path is a file.")
        if not os.path.exists(os.path.join(args.corpora_path, args.corpus)):
            parser.error(f"The entered corpus doesn't exist: {os.path.join(args.corpora_path, args.corpus)}")
    if args.language and args.language not in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args)
