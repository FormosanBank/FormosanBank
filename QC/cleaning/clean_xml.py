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

import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.corpus_counts import resolve_language, XML_LANG
from QC.utilities.classify_quotes import QUOTE, apply_quote_corrections

_DEFAULT_REFERENCE_DIR = _REPO_ROOT / "QC" / "validation" / "reference"

XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"

_CHINESE_LANGS = frozenset({
    "zho", "zh", "cmn", "yue", "wuu", "hak", "nan",
})
_TRANSL_LANG_ALIASES = {
    "en": "eng",
    "zh": "zho",
}
_ENGLISH_GLOSS_CORPUS_PATHS = frozenset({
    "Formosan-100_Paiwan_Texts",
    "HundredPaiwanStories",
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


def normalize_translation_language_metadata(
    root,
    xml_file: str,
) -> dict[str, int]:
    """Canonicalize known TRANSL language metadata without guessing broadly.

    ISO 639-1 aliases ``en`` and ``zh`` are normalized to the repository's
    ISO 639-3 convention. The Hundred Paiwan Stories source is the only
    corpus where missing TRANSL languages are inferred: its bare morpheme
    glosses are documented as English in the corpus migration script.
    """
    counts: defaultdict[str, int] = defaultdict(int)
    infer_english = any(
        part in _ENGLISH_GLOSS_CORPUS_PATHS
        for part in Path(xml_file).parts
    )
    for transl in root.iter("TRANSL"):
        raw = (transl.get(XML_LANG_ATTR) or "").strip()
        canonical = _TRANSL_LANG_ALIASES.get(raw.lower())
        if canonical and canonical != raw:
            transl.set(XML_LANG_ATTR, canonical)
            counts[f"normalize_translation_language_{raw.lower()}_to_{canonical}"] += 1
        elif not raw and infer_english:
            transl.set(XML_LANG_ATTR, "eng")
            counts["infer_hundred_paiwan_gloss_language_eng"] += 1
    return dict(counts)


# Null-morpheme markers attested in source data: 'ø' (U+00F8, NTU Grammar
# Sakizaya/Kanakanavu), 'Ø' (U+00D8, legacy), and the canonical '∅'
# (U+2205 EMPTY SET). A glyph counts as a null morpheme ONLY in morpheme
# position — both neighbors are a string edge, whitespace, or the ASCII
# segmentation hyphen — so the same letters inside foreign proper nouns
# (Danish 'Grønland', 'Børn' in the Wikipedia corpora) are never touched.
_NULL_MORPHEME_RE = re.compile(r"(^|[\s\-])[øØ∅](?=[\s\-]|$)")


def normalize_null_morphemes(text: str) -> str:
    """Canonicalize null-morpheme marker glyphs to '∅' (U+2205).

    Applies to every FORM tier clean_xml cleans (original S/W/M; the
    standard tier is owned by standardize.py): the marker glyph is
    annotation, not source spelling, so canonicalizing it keeps the
    original tier faithful. Removal of null units is standardize.py's
    job (S-level standard FORMs only) — this function only renames.
    """
    return _NULL_MORPHEME_RE.sub(lambda m: m.group(1) + "∅", text)


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

    Two modes (POL-033 vs POL-035):
    - default (``append=False``): an ephemeral per-run report — rewritten
      each run, removed when a run finds nothing (cleaner_warnings.csv).
    - ``append=True``: a durable, committed log (quote_corrections.csv) —
      rows accumulate across runs and an empty run leaves the file alone,
      so the record of past original-tier rewrites survives reruns.
    """
    csv_path: Path
    append: bool = False
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
        """Write this run's rows (see class docstring for the two modes).

        Default mode replaces any previous run's CSV (POL-033: per-run
        report; a run with no rows removes a stale CSV). Append mode adds
        this run's rows to the existing log and never deletes it.
        """
        if not self._rows:
            if self.append:
                return  # durable log: an empty run changes nothing
            try:
                self.csv_path.unlink()
            except OSError:
                # Missing file, or csv_path's parent is itself a file
                # (single-XML corpora_path) — either way nothing stale
                # exists to remove.
                pass
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if self.append:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["rule_id", "file", "s_id", "character",
                                "position"],
                )
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerows(self._rows)
            return
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["rule_id", "file", "s_id", "character", "position"],
            )
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


# Zero-width / BOM codepoints that are never meaningful in FormosanBank
# FORM or TRANSL text: ZERO WIDTH SPACE, ZERO WIDTH NON-JOINER, ZERO WIDTH
# JOINER, and ZERO WIDTH NO-BREAK SPACE (a.k.a. BOM). They are invisible
# source residue. The validator side flags them HARD (V131 / TR16); the
# cleaner strips them silently here so HARD findings stay near zero in
# practice. Like NFC normalization (C010), this is unconditional and emits
# no CleanerWarnings row.
_ZERO_WIDTH_CHARS = "​‌‍﻿"
_ZERO_WIDTH_RE = re.compile(f"[{_ZERO_WIDTH_CHARS}]")


def _strip_zero_width(text: str) -> str:
    """Remove zero-width / BOM characters (U+200B/200C/200D/FEFF).

    Applied to both FORM and TRANSL regardless of xml:lang. Silent
    mechanical fix — no warning row, idempotent.
    """
    return _ZERO_WIDTH_RE.sub("", text)


_FW_DQUOTE = "＂"  # U+FF02 FULLWIDTH QUOTATION MARK — canonical Chinese double quote
# Only genuine double-quotation marks are collapsed. The angle brackets
# 《 》 (whole-work title mark, 書名號) and 〈 〉 (part-work/篇名號) are Chinese
# TITLE marks, not quotes — they carry real semantic information and are
# deliberately left untouched.
CHINESE_DOUBLE_QUOTE_COLLAPSE = {
    "“": _FW_DQUOTE,  # U+201C LEFT DOUBLE QUOTATION MARK
    "”": _FW_DQUOTE,  # U+201D RIGHT DOUBLE QUOTATION MARK
    "「": _FW_DQUOTE,  # LEFT CORNER BRACKET 「
    "」": _FW_DQUOTE,  # RIGHT CORNER BRACKET 」
    "『": _FW_DQUOTE,  # LEFT WHITE CORNER BRACKET 『
    "』": _FW_DQUOTE,  # RIGHT WHITE CORNER BRACKET 』
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

    Double-quote variants (curly doubles, and the corner brackets 「」『』
    used as quotes) are all collapsed to U+FF02 FULLWIDTH QUOTATION MARK —
    the full-width straight double quote, the conventional canonical form
    in Chinese text. The angle brackets 《》/〈〉 are Chinese TITLE marks
    (書名號/篇名號), not quotes, and are deliberately left untouched.
    Single-quote variants and ASCII apostrophes emit a c002 warning row
    and are left unchanged: these are typically IME artefacts worth
    flagging to the corpus author.
    """
    for ch, replacement in CHINESE_DOUBLE_QUOTE_COLLAPSE.items():
        text = text.replace(ch, replacement)
    for i, ch in enumerate(text):
        if ch in CHINESE_WARN_SINGLE_QUOTES or ch == "'":
            if warnings:
                warnings.add("c002", xml_file, s_id, ch, i)
    return text


# C028: entity residue after XML parse. A parsed text containing literal
# '&lt;' means the source file held '&amp;lt;' — html.escape applied to
# already-escaped text (NTU Bunun shipped 1,109 TRANSLs this way). Decode
# to FIXED POINT, not one level: a single-level decode would leave residue
# for the next cleaning run to decode, making the cleaner non-idempotent.
# Only the five XML-named entities and numeric character references are
# matched — a bare '&' ("salt & pepper", "AT&T") is never touched.
# V132 is the validator twin: it flags any residue that sneaks back in.
_ENTITY_RESIDUE_RE = re.compile(
    r"&(amp|apos|lt|gt|quot|#\d{1,7}|#x[0-9A-Fa-f]{1,6});"
)
_NAMED_ENTITIES = {"amp": "&", "apos": "'", "lt": "<", "gt": ">", "quot": '"'}


def _decode_entity_match(match: "re.Match") -> str:
    body = match.group(1)
    if body in _NAMED_ENTITIES:
        return _NAMED_ENTITIES[body]
    try:
        code = int(body[2:], 16) if body.startswith("#x") else int(body[1:])
        return chr(code)
    except (ValueError, OverflowError):
        return match.group(0)


def decode_entity_residue(
    text,
    xml_file: str = "",
    s_id: "str | None" = None,
    warnings: "CleanerWarnings | None" = None,
):
    """C028: decode double-encoded entity residue to fixed point.

    Emits one c028 warning row per residue occurrence in the incoming
    text (first level only — deeper wrapping decodes without re-warning).
    Bounded at 8 iterations as a runaway guard; real data is 1–2 deep.
    """
    if warnings is not None:
        for match in _ENTITY_RESIDUE_RE.finditer(text):
            warnings.add("c028", xml_file, s_id, match.group(0), match.start())
    for _ in range(8):
        decoded = _ENTITY_RESIDUE_RE.sub(_decode_entity_match, text)
        if decoded == text:
            break
        text = decoded
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
        # All dash/hyphen look-alikes canonicalize to ASCII '-': much of the
        # corpus text is OCRed, so a source's hyphen-vs-dash choice cannot be
        # trusted as principled. We standardize to one character and let
        # context decide downstream — standardize.py's C012 strips '-' from
        # S-level standard FORMs only in morpheme-segmented sentences and
        # keeps digit-flanked '-' (dates, verse ranges) everywhere.
        # Tilde look-alikes → ASCII '~' (POL-013 codepoint ruling,
        # 2026-08-10): LaTeX-typeset PDFs emit the math TILDE OPERATOR
        # where the reduplication convention wants a plain tilde; the CJK
        # wave dash is the same visual twin from CJK-typeset sources.
        # (Chinese TRANSL is unaffected — that branch never calls
        # swap_punctuation, so a wave dash in Chinese text survives.)
        '∼': '~',  # U+223C TILDE OPERATOR
        '〜': '~',  # U+301C WAVE DASH
        '‐': '-',  # U+2010 HYPHEN
        '‑': '-',  # U+2011 NON-BREAKING HYPHEN
        '‒': '-',  # U+2012 FIGURE DASH
        '–': '-',  # U+2013 EN DASH
        '—': '-',  # U+2014 EM DASH
        '―': '-',  # U+2015 HORIZONTAL BAR
        '−': '-',  # U+2212 MINUS SIGN
        '﹘': '-',  # U+FE58 SMALL EM DASH
        '﹣': '-',  # U+FE63 SMALL HYPHEN-MINUS
        '－': '-',  # U+FF0D FULLWIDTH HYPHEN-MINUS
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

    Collapses !! → !, ?? → ?, and --- → -.
    """
    text = re.sub(r'([?!])\1+', r'\1', text)  # !! -> ! and ?? -> ?
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
      2b. normalize_null_morphemes — ø/Ø/∅ in morpheme position → canonical
          '∅' (U+2205). Letter-adjacent glyphs (foreign loanwords) untouched.
      3. normalize_whitespace — collapse runs of whitespace.
      4. trim_repeated_punctuation — !! → !, ??? → ?, --- → -.

    Zero-width / BOM characters (U+200B/200C/200D/FEFF) are stripped first,
    unconditionally — invisible source residue the validator flags HARD
    (V131 / TR16).
    """
    text = _strip_zero_width(text)
    # C028 runs before everything else so decoded characters (e.g. an
    # em-dash from '&#8212;') flow through the rest of the pipeline.
    text = decode_entity_residue(text, xml_file, s_id, warnings)
    text = normalize_caret_variants(text)
    # Emit c002b warning for U+02C8 before it gets swapped to apostrophe.
    if warnings is not None:
        for pos, ch in enumerate(text):
            if ch == "ˈ":
                warnings.add("c002b", xml_file, s_id, ch, pos)
    text = swap_punctuation(text)
    text = normalize_null_morphemes(text)
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
           double-quote variants to U+FF02 (full-width straight double quote)
           and emits c002 warning rows for single-quote variants and ASCII
           apostrophes (left unchanged).
      3. normalize_whitespace — collapse runs of whitespace.
      4. trim_repeated_punctuation — !! → !, ??? → ?, --- → -.

    Zero-width / BOM characters (U+200B/200C/200D/FEFF) are stripped first,
    unconditionally — invisible source residue the validator flags HARD
    (V131 / TR16).
    """
    text = _strip_zero_width(text)
    # C028: entity-residue decode is language-agnostic and runs before
    # the language branch so decoded characters flow through it.
    text = decode_entity_residue(text, xml_file, s_id, warnings)
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

def _load_attestation(language, reference_dir, cache):
    """Return the casefolded attestation set for `language`, or None if absent.

    `cache` is a dict reused across files in one run. A missing file caches
    None so we do not stat it repeatedly.
    """
    if language in cache:
        return cache[language]
    result = None
    if language:
        path = Path(reference_dir) / language / "attestation.txt"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                result = {w.strip().casefold() for w in fh if w.strip()}
    cache[language] = result
    return result


def analyze_and_modify_xml_file(
    xml_dir,
    corpora_dir,
    warnings: CleanerWarnings | None = None,
    counter: TransformCounter | None = None,
    metadata_counter: dict[str, int] | None = None,
    reference_dir=None,
    _attestation_cache: dict | None = None,
    corrections: "CleanerWarnings | None" = None,
):
    """
    Analyzes and modifies an XML file by cleaning text and handling specific cases in <FORM>.

    `corrections` is the durable quote-correction log (append-mode
    CleanerWarnings writing quote_corrections.csv; POL-035): actual
    original-tier rewrites (c031 corrected, c032 stranded-repair) go
    there, while ambiguous audit flags (c030) go to the ephemeral
    `warnings` report.
    """
    if reference_dir is None:
        reference_dir = _DEFAULT_REFERENCE_DIR
    if _attestation_cache is None:
        _attestation_cache = {}
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
                language = resolve_language(root.get(XML_LANG), root.get("dialect"))
                dictionary = _load_attestation(language, reference_dir, _attestation_cache)
                is_wikipedia = "Wikipedias" in Path(xml_file).parts
                modified = False
                metadata_repairs = normalize_translation_language_metadata(
                    root,
                    xml_file,
                )
                if metadata_repairs:
                    modified = True
                    if metadata_counter is not None:
                        for rule, count in metadata_repairs.items():
                            metadata_counter[rule] = (
                                metadata_counter.get(rule, 0) + count
                            )

                for sentence in root.findall('.//S'):
                    # Intentionally includes descendant W/M FORM tiers; they
                    # receive the same punctuation/Unicode cleanup as S FORM.
                    # S/FORM[@kindOf="standard"] is excluded: standardize.py
                    # owns all cleaning of the standard tier (C012 et al.).
                    form_elements = [
                        f for f in sentence.findall('.//FORM')
                        if f.get("kindOf") != "standard"
                    ]
                    for form_element in form_elements:
                        if form_element is not None:
                            form_text = form_element.text
                            if form_text is None or form_text == "":
                                continue
                            if warnings is not None:
                                for ch, pos in _find_bopomofo(form_text):
                                    warnings.add("c007", xml_file, sentence.get("id"), ch, pos)
                            working_text = unicodedata.normalize("NFC", form_text)
                            if form_text != working_text:
                                form_element.text = working_text
                                modified = True

                            unescaped_text = html.unescape(working_text)
                            if unescaped_text != working_text:  # Replace HTML entities
                                print('HTML entities found')
                                # log the change
                                with open(os.path.join(corpora_dir,"html_entities.log"), "a") as f:
                                    f.write(f"{xml_file}:\n")
                                    f.write(f"Original: {working_text}\n")
                                    f.write(f"Modified: {unescaped_text}\n\n")
                                working_text = unescaped_text
                                form_element.text = working_text
                                modified = True
                            cleaned_form_text = clean_text(
                                working_text,
                                lang="na",
                                xml_file=xml_file,
                                s_id=sentence.get("id"),
                                warnings=warnings,
                                counter=counter,
                            )
                            if cleaned_form_text != working_text:
                                form_element.text = cleaned_form_text
                                modified = True

                            # C022: warn on each '*' in any FORM (any position).
                            # FORM text is preserved (no removal).
                            if warnings is not None and "*" in cleaned_form_text:
                                for i, ch in enumerate(cleaned_form_text):
                                    if ch == "*":
                                        warnings.add("c022", xml_file, sentence.get("id"), ch, i)

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

                    # Quote/glottal correction: sentence-level ORIGINAL FORM only.
                    # W/M FORMs and the standard tier are intentionally excluded.
                    if dictionary is not None:
                        transl_texts = [
                            "".join(t.itertext())
                            for t in sentence.findall('TRANSL')
                            if "".join(t.itertext()).strip()
                        ]
                        for form_element in sentence.findall('FORM'):
                            if form_element.get("kindOf") != "original":
                                continue
                            ft = form_element.text
                            if not ft or QUOTE not in ft:
                                continue
                            new_text, corrected, stranded, ambiguous = \
                                apply_quote_corrections(ft, transl_texts, dictionary)
                            if corrected or stranded:
                                form_element.text = new_text
                                modified = True
                            if corrections is not None:
                                for pos in corrected:
                                    corrections.add("c031", xml_file,
                                                    sentence.get("id"), "'", pos)
                                for pos in stranded:
                                    corrections.add("c032", xml_file,
                                                    sentence.get("id"), "'", pos)
                            if warnings is not None and not is_wikipedia:
                                for pos in ambiguous:
                                    warnings.add("c030", xml_file,
                                                 sentence.get("id"), "'", pos)
                            if counter is not None and corrected:
                                counter.record("'", '"', len(corrected))

                if modified:
                    tree.write(xml_file, xml_declaration=True, pretty_print=True, encoding="utf-8")
                    print(f"File cleaned: {xml_file}")

def main(args):
    print(f"Processing XML files in directory: {args.corpora_path}")
    warnings_path = Path(args.corpora_path) / "cleaner_warnings.csv"
    warnings = CleanerWarnings(warnings_path)
    # Durable quote-correction log (POL-035): append-mode, committed.
    corrections = CleanerWarnings(
        Path(args.corpora_path) / "quote_corrections.csv", append=True)
    counter = TransformCounter()
    metadata_counter: dict[str, int] = {}
    analyze_and_modify_xml_file(
        args.corpora_path,
        args.corpora_path,
        warnings=warnings,
        counter=counter,
        metadata_counter=metadata_counter,
        reference_dir=getattr(args, "reference_dir", None),
        _attestation_cache={},
        corrections=corrections,
    )
    warnings.write_csv()
    corrections.write_csv()
    counter.print_summary()
    if metadata_counter:
        print("\nMetadata repair summary (rule : count):")
        for rule, count in sorted(metadata_counter.items()):
            print(f"  {rule} : {count}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extract orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora_path', help='the path to the corpus')
    parser.add_argument('--reference_dir', default=None,
                        help='dir holding <Language>/attestation.txt '
                             '(default: QC/validation/reference)')
    args = parser.parse_args()

    if not args.corpora_path:
        parser.error("--corpora_path is required.")    
    if not os.path.exists(os.path.join(args.corpora_path)):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist")

    main(args)
