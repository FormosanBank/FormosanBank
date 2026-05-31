import csv
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from lxml import etree
import html
import argparse
import unicodedata
from pathlib import Path

XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"

_CHINESE_LANGS = frozenset({
    "zho", "zh", "cmn", "yue", "wuu", "hak", "nan",
})


def _get_xml_lang(element) -> str | None:
    """Return the effective xml:lang for element.

    Walk up from element through its ancestors, returning the first
    xml:lang value found. Falls back to None if no ancestor (including
    element itself) carries xml:lang.

    Used by language-aware cleaning rules to decide whether an element
    carries Chinese text.
    """
    node = element
    while node is not None:
        lang = node.get(XML_LANG_ATTR)
        if lang is not None:
            return lang
        node = node.getparent()
    return None


def _is_chinese(lang: str | None) -> bool:
    """Return True when lang matches a known Chinese variant."""
    if lang is None:
        return False
    return lang.lower() in _CHINESE_LANGS or lang.lower().startswith("zh")


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
    """
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


def _find_bopomofo(text: str) -> list[tuple[str, int]]:
    """Return [(char, position)] for every Bopomofo character in text.

    Covers Bopomofo (U+3100-U+312F) and Bopomofo Extended (U+31A0-U+31BF).
    All 75 named codepoints in those ranges have unicodedata.name
    starting with "BOPOMOFO" (verified 2026-05-30).
    """
    out = []
    for i, ch in enumerate(text):
        try:
            if unicodedata.name(ch).startswith("BOPOMOFO"):
                out.append((ch, i))
        except ValueError:
            continue
    return out


@dataclass
class CleanerWarnings:
    """Accumulates per-occurrence warning rows and writes a CSV at end of run.

    CSV columns: rule_id, file, s_id, character, position.

    write_csv() is a no-op when no rows have been added (avoids creating
    empty files on clean corpora).
    """
    csv_path: Path
    _rows: list = field(default_factory=list, repr=False)

    def add(
        self,
        rule_id: str,
        file_path: str,
        s_id: str | None,
        character: str,
        position: int,
    ) -> None:
        self._rows.append({
            "rule_id": rule_id,
            "file": file_path,
            "s_id": s_id or "",
            "character": character,
            "position": position,
        })

    def write_csv(self) -> None:
        if not self._rows:
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["rule_id", "file", "s_id", "character", "position"],
            )
            if f.tell() == 0:
                writer.writeheader()
            writer.writerows(self._rows)


@dataclass
class TransformCounter:
    """Tallies every (input_char → output_char) substitution.

    record() may be called with count > 1 when the transformation was
    applied to a string containing multiple occurrences.

    summary() returns a list of dicts sorted by count descending,
    suitable for printing as a human-readable table.
    """
    _counts: dict = field(default_factory=lambda: defaultdict(int), repr=False)

    def record(self, input_char: str, output_char: str, count: int = 1) -> None:
        self._counts[(input_char, output_char)] += count

    def record_string_delta(self, before: str, after: str) -> None:
        """Infer individual-character changes by comparing before/after strings.

        Lightweight heuristic: counts characters in before that are absent
        in after as deletions (output=""). Use for full-string deltas where
        a transformation produced a diff but the caller did not record
        each individual swap.
        """
        for ch in set(before):
            if ch not in after:
                self._counts[(ch, "")] += before.count(ch)

    def summary(self) -> list[dict]:
        return sorted(
            [
                {"input": inp, "output": out, "count": cnt}
                for (inp, out), cnt in self._counts.items()
            ],
            key=lambda r: r["count"],
            reverse=True,
        )

    def print_summary(self) -> None:
        rows = self.summary()
        if not rows:
            return
        print("\nTransformation summary (input → output : count):")
        for r in rows:
            out = r["output"] if r["output"] else "<deleted>"
            print(f"  {r['input']!r} → {out!r} : {r['count']}")


'''
def fix_parentheses(text):
    """
    Fixes imbalanced parentheses by removing unmatched ones.
    """
    stack = []
    indices_to_remove = set()
    for i, char in enumerate(text):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                indices_to_remove.add(i)
    indices_to_remove.update(stack)
    return ''.join(
        [char for i, char in enumerate(text) if i not in indices_to_remove]
    )
'''

_CARET_VARIANTS_TO_ASCII = {
    "⌃": "^",  # UP ARROWHEAD (U+2303)
    "‸": "^",  # CARET (U+2038)
    "ˆ": "^",  # MODIFIER LETTER CIRCUMFLEX ACCENT (U+02C6)
    "＾": "^",  # FULLWIDTH CIRCUMFLEX ACCENT (U+FF3E)
}


def normalize_caret_variants(text: str) -> str:
    """Normalize caret-like Unicode characters to ASCII '^'.

    Per FormosanBank convention, a caret-like glyph in this corpus
    always represents a glottal stop. We canonicalize the visual
    variants to a single character so downstream processing sees
    one form regardless of source. Applied to both FORM and TRANSL
    regardless of xml:lang.
    """
    for variant, ascii_caret in _CARET_VARIANTS_TO_ASCII.items():
        text = text.replace(variant, ascii_caret)
    return text


_U201D = "”"  # RIGHT DOUBLE QUOTATION MARK — canonical Chinese closing quote
CHINESE_DOUBLE_QUOTE_COLLAPSE = {
    "“": _U201D,  # LEFT DOUBLE QUOTATION MARK
    "「": _U201D,  # LEFT CORNER BRACKET 「
    "」": _U201D,  # RIGHT CORNER BRACKET 」
    "『": _U201D,  # LEFT WHITE CORNER BRACKET 『
    "』": _U201D,  # RIGHT WHITE CORNER BRACKET 』
    "《": _U201D,  # LEFT DOUBLE ANGLE BRACKET 《
    "》": _U201D,  # RIGHT DOUBLE ANGLE BRACKET 》
    "〈": _U201D,  # LEFT ANGLE BRACKET 〈
    "〉": _U201D,  # RIGHT ANGLE BRACKET 〉
}

CHINESE_WARN_SINGLE_QUOTES = frozenset({
    "‘",  # LEFT SINGLE QUOTATION MARK '
    "’",  # RIGHT SINGLE QUOTATION MARK '
    "ʼ",       # MODIFIER LETTER APOSTROPHE (U+02BC)
    "ʻ",       # MODIFIER LETTER TURNED COMMA (U+02BB)
    "`",       # GRAVE ACCENT / backtick
})


def _clean_trans_chinese(
    text: str,
    xml_file: str,
    s_id: "str | None",
    warnings: "CleanerWarnings | None",
) -> str:
    """C002 Branch B: canonicalise Chinese double quotes; warn on singles.

    Double-quote variants (curly doubles, CJK brackets used as quotes)
    are all collapsed to U+201D RIGHT DOUBLE QUOTATION MARK — the
    conventional canonical form in Chinese text. Single-quote variants
    and ASCII apostrophes emit a c002 warning row and are left unchanged:
    these are typically IME artefacts worth flagging to the corpus author.
    """
    for ch, replacement in CHINESE_DOUBLE_QUOTE_COLLAPSE.items():
        text = text.replace(ch, replacement)
    for i, ch in enumerate(text):
        if ch in CHINESE_WARN_SINGLE_QUOTES or ch == "'":
            if warnings:
                warnings.add("c002", xml_file, s_id, ch, i)
    return text


def swap_punctuation(text):
    """
    Replaces specific non-ASCII punctuation with their ASCII equivalents.
    """
    # Define the mapping of full-width punctuation to regular punctuation
    # Also convert square brackets to parentheses
    fullwidth_to_regular = {
        '（': '(',
        '）': ')',
        '：': ':',
        '，': ',',
        '？': '?',
        '！': '!',
        '。': '.',
        '》': '"',
        '《': '"',
        '」': '"',
        '「': '"',
        '、': ',',
        '】': ')',
        '【': '(',
        ']': ')',
        '[': '(',
        '〔': '(',
        '〕': ')',
        '“': '"',  # LEFT DOUBLE QUOTATION MARK "
        '”': '"',  # RIGHT DOUBLE QUOTATION MARK "
        '‘': "'",  # LEFT SINGLE QUOTATION MARK '
        '’': "'",  # RIGHT SINGLE QUOTATION MARK '
        'ˈ': "'",
        '`': "'",
        'ʼ': "'",  # Modifier Letter Apostrophe (U+02BC)
        'ʻ': "'",
        '『': '"',
        '』': '"',
    }
    
    # Create a regular expression pattern to match any of the full-width punctuation characters
    pattern = re.compile('|'.join(map(re.escape, fullwidth_to_regular.keys())))
    
    # Define a function to replace each match with the corresponding regular punctuation
    def replace(match):
        return fullwidth_to_regular[match.group(0)]
    
    # Use re.sub to replace all full-width punctuation with regular punctuation
    return pattern.sub(replace, text)


'''
def process_punctuation(text):
    """
    Cleans and standardizes punctuation in the text.
    """
    text = re.sub(r''([^']*)'', r'"\1"', text)  # Paired single quotes
    text = text.replace("'", "'").replace("'", "'")  # Single quotes
    text = re.sub(r'"([^"]*)"', r'"\1"', text)  # Paired double quotes
    text = text.replace('"', '"').replace('"', '"')  # Double quotes
    text = text.replace("ˈ", "'")  # Specific mark replacements
    return text
'''

def normalize_whitespace(text):
    """
    Standardizes whitespace in the text.
    """
    text = re.sub(r' {2,}', ' ', text)  # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

def trim_repeated_punctuation(text):
    """
    Replaces repeated punctuation with single marks.
    """
    text = re.sub(r'([?!])\1+', r'\1', text)  # !! -> !
    text = re.sub(r'--+', '-', text)  # --- -> -
    return text

def clean_text(
    text,
    lang,
    xml_file: str = "",
    s_id: "str | None" = None,
    warnings: "CleanerWarnings | None" = None,
    counter: "TransformCounter | None" = None,
):
    """Apply cleaning functions to a FORM-tier text node.

    Pipeline (always language-agnostic for FORM):
      1. normalize_caret_variants — four caret-like Unicode chars → ASCII '^'
         regardless of xml:lang. In FormosanBank a caret always represents
         a glottal stop.
      2. swap_punctuation — full-width and typographic punctuation → ASCII.
         Emits a c002b warning row for each U+02C8 (IPA PRIMARY STRESS MARK)
         found before the swap, because stress marks are unexpected in Formosan
         corpus data and worth surfacing to the corpus author.
      3. normalize_whitespace — collapse runs of whitespace.
      4. trim_repeated_punctuation — !! → !, ??? → ?, --- → -.
    """
    text = normalize_caret_variants(text)
    # Emit c002b warning for U+02C8 before it gets swapped to apostrophe.
    if warnings is not None:
        for pos, ch in enumerate(text):
            if ch == "ˈ":
                warnings.add("c002b", xml_file, s_id, ch, pos)
    text = swap_punctuation(text)
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    return text


def clean_trans(
    text,
    lang,
    xml_file: str = "",
    s_id: "str | None" = None,
    warnings: "CleanerWarnings | None" = None,
    counter: "TransformCounter | None" = None,
):
    """Apply cleaning functions to a TRANSL-tier text node.

    Pipeline:
      1. normalize_caret_variants — language-agnostic; four caret-like Unicode
         chars → ASCII '^' in EVERY TRANSL regardless of xml:lang. In
         FormosanBank a caret always represents a glottal stop, so the
         normalization is unconditional and deliberately does NOT branch on
         _is_chinese(lang).
      2. Language-aware quote/apostrophe handling:
         - Non-Chinese (C001/C002 Branch A): call swap_punctuation, which
           collapses full-width punctuation and typographic quotes/apostrophes
           to their ASCII equivalents — same as FORM. A c002b warning row is
           emitted for each U+02C8 (IPA PRIMARY STRESS MARK) found before swap.
         - Chinese (C002 Branch B): call _clean_trans_chinese, which collapses
           double-quote variants to U+201D and emits c002 warning rows for
           single-quote variants and ASCII apostrophes (left unchanged).
      3. normalize_whitespace — collapse runs of whitespace.
      4. trim_repeated_punctuation — !! → !, ??? → ?, --- → -.
    """
    text = normalize_caret_variants(text)
    if _is_chinese(lang):
        text = _clean_trans_chinese(text, xml_file, s_id, warnings)
    else:
        # Emit c002b warning for U+02C8 before swap.
        if warnings is not None:
            for pos, ch in enumerate(text):
                if ch == "ˈ":
                    warnings.add("c002b", xml_file, s_id, ch, pos)
        text = swap_punctuation(text)
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    return text

def analyze_and_modify_xml_file(
    xml_dir,
    corpora_dir,
    warnings: CleanerWarnings | None = None,
    counter: TransformCounter | None = None,
    hard_remove_segmentation: bool = False,
    ortho_path: str | None = None,
):
    """
    Analyzes and modifies an XML file by cleaning text and handling specific cases in <FORM>.
    """
    for droot, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                print(f"Processing file: {file}")

                xml_file = os.path.join(droot, file)
                # Read the content of the XML file
                with open(xml_file, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Replace all non-breaking spaces with regular spaces
                content = re.sub('\u00A0', ' ', content)

                # Write the modified content back to the XML file
                with open(xml_file, 'w', encoding='utf-8') as file:
                    file.write(content)

                # Silling to re-open the file, but such are the times we live in.
                tree = etree.parse(xml_file)
                root = tree.getroot()
                modified = False

                for sentence in root.findall('.//S'):
                    form_elements = sentence.findall('.//FORM')
                    for form_element in form_elements:
                        if form_element is not None:
                            form_text = form_element.text
                            if form_text is None or form_text == "":
                                continue
                            if warnings is not None:
                                for ch, pos in _find_bopomofo(form_text):
                                    warnings.add("c007", xml_file, sentence.get("id"), ch, pos)
                            if form_text != unicodedata.normalize("NFC", form_text):
                                form_element.text = unicodedata.normalize("NFC", form_text)
                                modified = True

                            # Handle specific <FORM> cases
                            if "456otca" in form_text:  # Remove <S> if text contains 456otca
                                root.remove(sentence)
                                modified = True
                            else:
                                if html.unescape(form_text) != form_text:  # Replace HTML entities
                                    print('HTML entities found')
                                    # log the change
                                    with open(os.path.join(corpora_dir,"html_entities.log"), "a") as f:
                                        f.write(f"{xml_file}:\n")
                                        f.write(f"Original: {form_text}\n")
                                        f.write(f"Modified: {html.unescape(form_text)}\n\n")
                                    form_element.text = html.unescape(form_text)
                                    modified = True
                                cleaned_form_text = clean_text(
                                    form_text,
                                    lang="na",
                                    xml_file=xml_file,
                                    s_id=sentence.get("id"),
                                    warnings=warnings,
                                    counter=counter,
                                )
                                if cleaned_form_text != form_text:
                                    form_element.text = cleaned_form_text
                                    modified = True

                    # C012: handle hyphens in S-level FORM[@kindOf="standard"] only.
                    # Must run AFTER clean_text so any clean_text output is included.
                    # W/M FORMs keep their segmentation (they are NOT matched here
                    # because findall("FORM[...]") returns only direct children of S).
                    lang_code = _get_xml_lang(sentence) or ""
                    for s_form in sentence.findall("FORM[@kindOf='standard']"):
                        if s_form.text:
                            new_text = _process_standard_hyphens(
                                s_form.text,
                                xml_file,
                                sentence.get("id"),
                                lang_code,
                                warnings,
                                hard_remove_segmentation,
                                ortho_path,
                            )
                            if new_text != s_form.text:
                                s_form.text = new_text
                                modified = True

                    # Clean <TRANSL> elements
                    for transl in sentence.findall('TRANSL'):
                        transl_lang = _get_xml_lang(transl)
                        transl_text = transl.text
                        if transl_text:
                            cleaned_transl_text = clean_trans(
                                transl_text,
                                lang=transl_lang,
                                xml_file=xml_file,
                                s_id=sentence.get("id"),
                                warnings=warnings,
                                counter=counter,
                            )
                            if cleaned_transl_text != transl_text:
                                transl.text = cleaned_transl_text
                                modified = True

                if modified:
                    tree.write(xml_file, xml_declaration=True, pretty_print=True, encoding="utf-8")
                    print(f"File cleaned: {xml_file}")

def main(args):
    print(f"Processing XML files in directory: {args.corpora_path}")
    warnings_path = Path(args.corpora_path) / "cleaner_warnings.csv"
    warnings = CleanerWarnings(warnings_path)
    counter = TransformCounter()
    analyze_and_modify_xml_file(
        args.corpora_path,
        args.corpora_path,
        warnings=warnings,
        counter=counter,
        hard_remove_segmentation=getattr(args, "hard_remove_segmentation", False),
        ortho_path=getattr(args, "ortho_path", None),
    )
    warnings.write_csv()
    counter.print_summary()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extract orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora_path', help='the path to the corpus')
    parser.add_argument(
        "--hard-remove-segmentation",
        action="store_true",
        default=False,
        help=(
            "Force stripping of hyphens from S/FORM[@kindOf='standard'] even "
            "when the language's canonical orthography includes '-' as a letter. "
            "Overrides the default preserve-and-warn behavior for Bunun and Thao."
        ),
    )
    parser.add_argument(
        "--ortho-path",
        default=None,
        help=(
            "Path to the canonical orthography directory (default: "
            "Orthographies/Ortho113/ relative to the repo root). "
            "Each <Language>.tsv under this directory is consulted by C012."
        ),
    )
    args = parser.parse_args()

    if not args.corpora_path:
        parser.error("--corpora_path is required.")    
    if not os.path.exists(os.path.join(args.corpora_path)):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist")

    main(args)
