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
from QC.utilities._accents import strip_accents  # noqa: E402
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


_ISO_TO_LANG_NAME = {
    "ami": "Amis",
    "tay": "Atayal",
    "bnn": "Bunun",
    "xnb": "Kanakanavu",
    "ckv": "Kavalan",
    "pwn": "Paiwan",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "sxr": "Saaroa",
    "xsy": "Saisiyat",
    "szy": "Sakizaya",
    "trv": "Seediq",
    "ssf": "Thao",
    "tsu": "Tsou",
    "tao": "Yami",
}

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

    The null-morpheme marker 'Ø' (U+00D8) is likewise stripped unconditionally
    — together with its bridging segmentation hyphen ('Ø-' / '-Ø') — because it
    is an annotation, never an orthographic letter in any Formosan language.
    Removing it as a unit avoids leaving a dangling hyphen even where '-' is a
    letter (Bunun, Thao).
    """
    text = re.sub(r"Ø-|-Ø|Ø", "", text)
    if lang_code and _hyphen_is_letter(lang_code, ortho_path):
        if hard_remove_segmentation:
            return text.replace("-", "").replace("=", "")
        # Preserve hyphens, warn per occurrence
        if warnings is not None:
            for i, ch in enumerate(text):
                if ch == "-":
                    warnings.add("c012", xml_file, s_id, ch, i)
        return text.replace("=", "")  # clitic stripped even when preserving '-'
    # Hyphen is not a letter → strip both
    return text.replace("-", "").replace("=", "")


def _apply_standard_hyphens(element, lang_code, ortho_path, hard_remove,
                            warnings, file_path):
    """Apply C012 to an S element's standard FORM. No-op for W/M (they keep
    segmentation) and for elements without a standard FORM.

    After C012, emits c022 for any '*' character found in the resulting
    standard FORM text.
    """
    if element.tag != "S":
        return
    form = element.find("FORM[@kindOf='standard']")
    if form is None or not form.text:
        return
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


def prettify(elem):
    """Pretty-print XML without adding whitespace inside mixed content."""
    rough_string = ET.tostring(elem, encoding="utf-8")
    reparsed = etree.fromstring(rough_string, etree.XMLParser(remove_blank_text=True))
    body = etree.tostring(reparsed, encoding="unicode", pretty_print=True)
    body = "\n".join(
        re.sub(r"^( +)", lambda match: match.group(1) * 2, line)
        for line in body.splitlines()
    )
    return f'<?xml version="1.0" ?>\n{body}\n'


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

def apply_standard(s_element, standard):
    form = s_element.find("FORM[@kindOf='standard']")
    if form.text:
        # Protect explicitly mapped diacritic-bearing letters before the
        # general stress-mark cleanup. This lets a table distinguish a true
        # orthographic letter such as ä from an otherwise unlisted stressed á.
        protected = []
        remaining = []
        for original, replacement in standard:
            decomposed = unicodedata.normalize("NFD", original)
            if any(unicodedata.category(char).startswith("M") for char in decomposed):
                marker = chr(0xE000 + len(protected))
                form.text = form.text.replace(original, marker)
                protected.append((marker, replacement))
            else:
                remaining.append((original, replacement))

        # The original tier is never touched here. Unprotected diacritics are
        # treated as source stress/prosody and removed from the standard tier.
        form.text = strip_accents(form.text)
        for original, replacement in remaining:
            form.text = form.text.replace(original, replacement)
        for marker, replacement in protected:
            form.text = form.text.replace(marker, replacement)

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
    # Find the <FORM> child within each <S> element
    original_form = element.find("FORM[@kindOf='original']")
    standard_form = element.find("FORM[@kindOf='standard']")

    if original_form is None:
        s_id = element.get('id', '<unknown>')
        location = f" in {file_path}" if file_path else ""
        print(
            f"Error: S id={s_id!r}{location} has no original tier (kindOf='original'). "
            f"Cannot create standard tier.",
            file=sys.stderr,
        )
        sys.exit(1)

    if standard_form is not None:
        # Standard form exists, replace its content with original's
        _copy_mixed_content(original_form, standard_form)
        return

    # No standard form exists, create one
    original_form.set("kindOf", "original")

    new_form = ET.Element("FORM")
    new_form.set("kindOf", "standard")
    _copy_mixed_content(original_form, new_form)
    element.insert(1, new_form)

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

                    if args.copy:
                        # In copy mode, just copy original to standard
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            _apply_standard_hyphens(
                                element, lang_code, args.ortho_path,
                                args.hard_remove_segmentation, warnings, file)
                    elif args.remove_accents:
                        # Copy original to standard, then delete accents only.
                        # apply_standard with an empty mapping strips accents and
                        # applies no letter conversion.
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            apply_standard(element, [])
                            _apply_standard_hyphens(
                                element, lang_code, args.ortho_path,
                                args.hard_remove_segmentation, warnings, file)
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
                                    # Only include mappings where the original value exists
                                    # Empty standard value means "remove the original character"
                                    if original_value:  # Only process if there's something to replace
                                        standard.append((original_value, standard_value))

                        if profile_graphemes is not None:
                            standard = derive_case_variants(standard, profile_graphemes)

                        # Iterate over all <S> elements
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            apply_standard(element, standard)
                            _apply_standard_hyphens(
                                element, lang_code, args.ortho_path,
                                args.hard_remove_segmentation, warnings, file)
                        
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
