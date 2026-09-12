#!/usr/bin/env python3
"""Reproducible extraction pipeline for the ILCAA Kanakanavu Texts PDF.

The implementation is intentionally conservative: it preserves raw positioned
PDF data first, then only emits W/M tiers when source/gloss alignment is
supported by the positioned source. Source extraction does not establish QC readiness.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from lxml import etree


CODEDOCS = Path(__file__).resolve().parents[1]
ROOT = CODEDOCS / ".build"
PDF_NAME = "B602_KanakanavuText.pdf"
EXPECTED_SHA256 = "785058bad6a8495f8b5fb51ed3d0eaf7da1736e791b308611d9442c010d93c03"
EXPECTED_SOURCE_UNIT_COUNT = 1431
EXPECTED_SENTENCE_COUNT = 1449
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
NSMAP = {"xml": "http://www.w3.org/XML/1998/namespace"}

with (CODEDOCS / "notation_decisions.tsv").open(encoding="utf-8") as notation_evidence:
    NOTATION_DECISIONS = {
        row["unit_id"]: row["representation"]
        for row in csv.DictReader(notation_evidence, delimiter="\t")
    }
FORM_VARIANT_UNITS = {key for key, value in NOTATION_DECISIONS.items() if value == "form_variants"}
CLAUSE_BRACKET_UNITS = {key for key, value in NOTATION_DECISIONS.items() if value == "clause_brackets"}


PARTS = {
    1: ("PART ONE: TEXTS BY ERIN ASAI", "Erin Asai", "Texts by Erin Asai"),
    2: ("PART TWO: TEXTS BY KUANG MEI", "Kuang Mei", "Texts by Kuang Mei"),
    3: ("PART THREE: TEXTS BY PAUL JEN-KUEI LI", "Paul Jen-kuei Li", "Texts by Paul Jen-kuei Li"),
    4: ("PART FOUR: TEXTS BY SHIGERU TSUCHIDA", "Shigeru Tsuchida", "Texts by Shigeru Tsuchida"),
}


TEXT_INVENTORY: list[dict[str, Any]] = [
    {"part": 1, "num": 1, "title": "Shooting the sun", "page": 28},
    {"part": 1, "num": 2, "title": "The big flood", "page": 34},
    {"part": 1, "num": 3, "title": "The big flood II", "page": 42},
    {"part": 1, "num": 4, "title": "I want to take a wife", "page": 44},
    {"part": 1, "num": 5, "title": "The sky fell down", "page": 47},
    {"part": 1, "num": 6, "title": "Transforming into a monkey", "page": 48},
    {"part": 1, "num": 7, "title": "To bear a child without a husband", "page": 49},
    {"part": 2, "num": 1, "title": "A legendary malicious spirit", "page": 50},
    {"part": 2, "num": 2, "title": "The story of a head", "page": 55},
    {"part": 2, "num": 3, "title": "Story of a Kanakanavu girl who was married to a snake", "page": 64},
    {"part": 2, "num": 4, "title": "Naparamaci", "page": 73},
    {"part": 3, "num": 1, "title": "Hunting", "page": 99},
    {"part": 3, "num": 2, "title": "Fishing", "page": 100},
    {"part": 3, "num": 3, "title": "Orphan 'Usu", "page": 102},
    {"part": 3, "num": 4, "title": "White-tailed blue robin", "page": 105},
    {"part": 3, "num": 5, "title": "The frog", "page": 109},
    {"part": 3, "num": 6, "title": "My father", "page": 111},
    {"part": 3, "num": 7, "title": "Prince Calabash", "page": 115},
    {"part": 3, "num": 8, "title": "A hundred pacer", "page": 117},
    {"part": 3, "num": 9, "title": "Rainbow", "page": 120},
    {"part": 3, "num": 10, "title": "Little people", "page": 124},
    {"part": 3, "num": 11, "title": "The giant", "page": 136},
    {"part": 4, "num": 1, "title": "Fruit of the bird lime plant", "page": 141},
    {"part": 4, "num": 2, "title": "Fruit of the bird lime plant II", "page": 146},
    {"part": 4, "num": 3, "title": "Not eating eels", "page": 148},
    {"part": 4, "num": 4, "title": "Not eating eels II", "page": 152},
    {"part": 4, "num": 5, "title": "Pangolin", "page": 154},
    {"part": 4, "num": 6, "title": "Pangolin II", "page": 161},
    {"part": 4, "num": 7, "title": "Snake", "page": 168},
    {"part": 4, "num": 8, "title": "Snake II", "page": 180},
    {"part": 4, "num": 9, "title": "A reckless mother", "page": 183},
    {"part": 4, "num": 10, "title": "Killing a snake brought a curse on a person", "page": 192},
    {"part": 4, "num": 11, "title": "Worshiping a snake", "page": 198},
    {"part": 4, "num": 12, "title": "Setting up traps", "page": 201},
    {"part": 4, "num": 13, "title": "Setting up traps II", "page": 208},
    {"part": 4, "num": 14, "title": "To prepare salted meat", "page": 211},
    {"part": 4, "num": 15, "title": "Roasting meat and fish", "page": 214},
    {"part": 4, "num": 16, "title": "The story of land boundaries", "page": 216},
    {"part": 4, "num": 17, "title": "The story of land boundaries II", "page": 221},
    {"part": 4, "num": 18, "title": "A ghost story", "page": 225},
    {"part": 4, "num": 19, "title": "An Event at Napalanga", "page": 228},
    {"part": 4, "num": 20, "title": "A dangerous narrow stream with white stones", "page": 234},
    {"part": 4, "num": 21, "title": "A taboo on stepping on flowing water with blood", "page": 240},
    {"part": 4, "num": 22, "title": "The story of my marriage", "page": 244},
]


GRAMMAR_EXAMPLE_TITLE = "Grammatical introduction examples"
GRAMMAR_EXAMPLE_PHYSICAL_PAGES = range(17, 28)
GRAMMAR_EXAMPLE_PRINTED_START = 12
GRAMMAR_EXAMPLE_PRINTED_END = 22
GRAMMAR_EXAMPLE_EXPECTED_NUMBERS = set(range(1, 41))
GRAMMAR_EXAMPLE_EXPECTED_UNIT_COUNT = 48
GRAMMAR_EXAMPLE_SUBNUMBERED = {10, 23, 24, 25, 26, 40}


# Each option is a complete admitted manifestation of one source unit. Exact
# replacements make the source decision auditable and cause a hard build error
# if a future scrape changes the source string without a fresh review.
PARENTHETICAL_VARIANTS: dict[str, tuple[dict[str, Any], dict[str, Any]]] = {
    "ILCAA_KANAKANAVU_TEXTS_006_TRANSFORMING_INTO_A_MONKEY_U0004": (
        {"label": "omitted", "source": (("makaasu(a)", "makaasu"),), "gloss": ()},
        {"label": "included", "source": (("makaasu(a)", "makaasua"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_008_A_LEGENDARY_MALICIOUS_SPIRIT_U0001": (
        {"label": "tee", "source": (("tee(= tia)=ku", "tee=ku"),), "gloss": ()},
        {"label": "tia", "source": (("tee(= tia)=ku", "tia=ku"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_008_A_LEGENDARY_MALICIOUS_SPIRIT_U0002": (
        {"label": "usa", "source": (("mu-usa (=mu-a-kusa)", "mu-usa"),), "gloss": (("AV-go (=AV-IRR-go.toward)", "AV-go"),)},
        {"label": "akusa", "source": (("mu-usa (=mu-a-kusa)", "mu-a-kusa"),), "gloss": (("AV-go (=AV-IRR-go.toward)", "AV-IRR-go.toward"),)},
    ),
    "ILCAA_KANAKANAVU_TEXTS_009_THE_STORY_OF_A_HEAD_U0031": (
        {"label": "ha", "source": (("ha (= sua)", "ha"),), "gloss": ()},
        {"label": "sua", "source": (("ha (= sua)", "sua"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_009_THE_STORY_OF_A_HEAD_U0042": (
        {"label": "usa", "source": (("mu-usa (= mu-kusa)", "mu-usa"),), "gloss": ()},
        {"label": "kusa", "source": (("mu-usa (= mu-kusa)", "mu-kusa"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_010_STORY_OF_A_KANAKANAVU_GIRL_WHO_WAS_MARRIED_TO_A_SNAKE_U0014": (
        {"label": "short", "source": (("cəpəŋ-in(i)", "cəpəŋ-in"),), "gloss": ()},
        {"label": "long", "source": (("cəpəŋ-in(i)", "cəpəŋ-ini"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_010_STORY_OF_A_KANAKANAVU_GIRL_WHO_WAS_MARRIED_TO_A_SNAKE_U0029": (
        {"label": "omitted", "source": (("(ʔaisi na)", ""),), "gloss": (("who exist LOC LOC-sit-LOC", "who LOC-sit-LOC"),)},
        {"label": "included", "source": (("(ʔaisi na)", "ʔaisi na"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0088": (
        {"label": "short", "source": (("ma-ʔanivi-(i)ni", "ma-ʔanivi-ni"),), "gloss": ()},
        {"label": "long", "source": (("ma-ʔanivi-(i)ni", "ma-ʔanivi-ini"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0102": (
        {"label": "short", "source": (("(a)va=ʔai", "va=ʔai"),), "gloss": ()},
        {"label": "long", "source": (("(a)va=ʔai", "ava=ʔai"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_027_PANGOLIN_U0017": (
        {"label": "omitted", "source": (("(kusa) ", ""),), "gloss": (("perhaps toward where", "perhaps where"),)},
        {"label": "included", "source": (("(kusa)", "kusa"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_028_PANGOLIN_II_U0001": (
        {"label": "omitted", "source": (("(sua) ", ""),), "gloss": (("NOM 1SG", "1SG"),)},
        {"label": "included", "source": (("(sua)", "sua"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_028_PANGOLIN_II_U0031": (
        {"label": "omitted", "source": ((" (sua) t<um>ani-ulaʔə", " t<um>ani-ulaʔə"),), "gloss": (("tradition NOM TANI<AV>-abuse", "tradition TANI<AV>-abuse"),)},
        {"label": "included", "source": (("(sua)", "sua"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0005": (
        {"label": "omitted", "source": (("(nuu) ", ""),), "gloss": (("TOP if FUT", "TOP FUT"),)},
        {"label": "included", "source": (("(nuu)", "nuu"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0013": (
        {"label": "ha", "source": (("ha (=sua)", "ha"),), "gloss": ()},
        {"label": "sua", "source": (("ha (=sua)", "sua"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0019": (
        {"label": "misai", "source": (("misai (= misa=kani)", "misai"),), "gloss": (("say say=said", "say"),)},
        {"label": "misa", "source": (("misai (= misa=kani)", "misa=kani"),), "gloss": (("say say=said", "say=said"),)},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0021": (
        {"label": "omitted", "source": ((" (misa=kan).", ""),), "gloss": ((" say=said IRR", " IRR"),)},
        {"label": "included", "source": (("(misa=kan)", "misa=kan"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0023": (
        {"label": "omitted", "source": ((" (misa=kani).", "."),), "gloss": ((" say=said", ""),)},
        {"label": "included", "source": (("(misa=kani)", "misa=kani"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0030": (
        {"label": "omitted", "source": (("mu-caan (=kan)", "mu-caan"),), "gloss": (("AV-go (=said)", "AV-go"),)},
        {"label": "included", "source": (("mu-caan (=kan)", "mu-caan=kan"),), "gloss": (("AV-go (=said)", "AV-go=said"),)},
    ),
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0037": (
        {"label": "omitted", "source": ((" (ʔinia) saruanai", " saruanai"),), "gloss": (("said 3.OBL man", "said man"),)},
        {"label": "included", "source": (("(ʔinia)", "ʔinia"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_032_KILLING_A_SNAKE_BROUGHT_A_CURSE_ON_A_PERSON_U0029": (
        {"label": "omitted", "source": (("naanu=(musu)", "naanu"),), "gloss": (("what=2SG.AGT", "what"),)},
        {"label": "included", "source": (("naanu=(musu)", "naanu=musu"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_032_KILLING_A_SNAKE_BROUGHT_A_CURSE_ON_A_PERSON_U0033": (
        {"label": "omitted", "source": (("tu-pau=(kani)", "tu-pau"),), "gloss": (("LOC-hole=said", "LOC-hole"),)},
        {"label": "included", "source": (("tu-pau=(kani)", "tu-pau=kani"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_032_KILLING_A_SNAKE_BROUGHT_A_CURSE_ON_A_PERSON_U0035": (
        {"label": "ha_iihaa", "source": (("ha (= sua)", "ha"), ("iihaa (= iisua)", "iihaa")), "gloss": ()},
        {"label": "sua_iisua", "source": (("ha (= sua)", "sua"), ("iihaa (= iisua)", "iisua")), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_034_SETTING_UP_TRAPS_U0011": (
        {"label": "omitted", "source": ((" (c<um>əʔəra)", ""),), "gloss": ((" see<AV>", ""),)},
        {"label": "included", "source": (("(c<um>əʔəra)", "c<um>əʔəra"),), "gloss": ()},
    ),
    "ILCAA_KANAKANAVU_TEXTS_040_A_GHOST_STORY_U0009": (
        {"label": "short", "source": (("(h)aan=ci", "aan=ci"),), "gloss": ()},
        {"label": "long", "source": (("(h)aan=ci", "haan=ci"),), "gloss": ()},
    ),
}


RESOLVED_JUDGMENT_GLOSS_REPLACEMENTS: dict[str, tuple[tuple[str, str], ...]] = {
    "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0025": (
        ("eat-NMLZ.UV=2SG.GEN", "eat-NMLZ.UV"),
    ),
    "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0032": (
        ("IRR-CAUS-eat-AV.IMP OBL child", "IRR-CAUS-eat-AV.IMP child"),
    ),
}


def ensure_dirs() -> None:
    for rel in [
        "data/raw/text/pages",
        "data/raw/words/pages",
        "data/raw/blocks/pages",
        "data/raw/spans/pages",
        "data/raw/renders",
        "data/raw/crops",
        "data/processed/review",
        "build/xml_drafts/Kanakanavu",
    ]:
        (ROOT / rel).mkdir(parents=True, exist_ok=True)


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str], *, lineterminator: str = "\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", lineterminator=lineterminator)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_value(row.get(k, "")) for k in fieldnames})


def _csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").lower()
    return text or "untitled"


def text_id(order: int, title: str) -> str:
    return f"ILCAA_KANAKANAVU_TEXTS_{order:03d}_{slugify(title).upper()}"


def xml_filename(order: int, title: str) -> str:
    return f"ILCAA_KanakanavuTexts_{order:03d}_{slugify(title)}.xml"


GRAMMAR_EXAMPLE_TEXT_ID = text_id(0, GRAMMAR_EXAMPLE_TITLE)


def source_pdf() -> Path:
    source = CODEDOCS / "data/raw/pdf" / PDF_NAME
    if not source.is_file() or sha256_path(source) != EXPECTED_SHA256:
        raise SystemExit("Missing or changed committed Kanakanavu source PDF")
    return source


def clean_space(text: str) -> str:
    text = html.unescape(text)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_source_chars(text: str) -> str:
    """Normalize source-text codepoint confusables verified against the PDF."""
    return unicodedata.normalize("NFC", text).replace("ә", "ə")


def strip_form_footnote_anchors(text: str) -> str:
    """Retain digits after positively identified anchors were handled upstream."""
    return text


def remove_source_metalinguistic_annotations(text: str) -> str:
    """Retain source-published metalinguistic notation in original forms."""
    return text


def clean_source_form(text: str) -> str:
    text = remove_source_metalinguistic_annotations(text)
    text = normalize_source_chars(text)
    text = re.sub(r"\s*([=-])\s*", r"\1", text)
    text = strip_form_footnote_anchors(text)
    return normalize_inline_spacing(text)


def normalize_inline_spacing(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,;:])([^\s\"'\)\]\}])", r"\1 \2", text)
    return text.strip()


def matching_paren_end(text: str, start: int) -> int:
    depth = 0
    for index in range(start, len(text)):
        if text[index] == "(":
            depth += 1
        elif text[index] == ")":
            depth -= 1
            if depth == 0:
                return index
    return -1


def translation_note_parenthetical(inner: str) -> bool:
    lowered = inner.strip().lower()
    if lowered.startswith(("lit", "i.e.", "cf.")):
        return True
    if lowered in {
        "pseudo-cleft",
        "av indicative",
        "uv indicative",
        "he replied.",
    }:
        return True
    if re.fullmatch(r"(liu|tsuchida)\s+\d{4}(?::\s*\d+)?", lowered):
        return True
    return False


def normalize_translation_ascii(text: str) -> str:
    """Normalize layout whitespace without changing published characters."""
    return normalize_inline_spacing(text)


def clean_sentence_translation(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = normalize_translation_ascii(text)
    return text.strip()


def sentence_translation_and_note(text: str) -> tuple[str, str]:
    """Separate a known trailing editorial parenthetical from translation prose."""
    translation = clean_sentence_translation(text)
    if not translation.endswith(")"):
        return translation, ""
    start = translation.rfind("(")
    if start == -1 or matching_paren_end(translation, start) != len(translation) - 1:
        return translation, ""
    note = translation[start + 1:-1].strip()
    if not translation_note_parenthetical(note):
        return translation, ""
    return translation[:start].rstrip(), note


SOURCE_JUDGMENT_EDITS = {
    "naini sua [kaən-a/*kaən-ən=musu]": "naini sua [kaən-a]",
    "a-pa-kaən-a (*sua) maanu uuru.": "a-pa-kaən-a maanu uuru.",
}


def sentence_original_form(text: str) -> str:
    text = clean_source_form(text)
    text = SOURCE_JUDGMENT_EDITS.get(text, text)
    if "*" in text:
        raise ValueError(
            "Unreviewed source judgment marker. Add an explicit "
            "SOURCE_JUDGMENT_EDITS decision before generating XML: "
            f"{text!r}"
        )
    return normalize_inline_spacing(text)


def clean_gloss_form(text: str) -> str:
    text = normalize_inline_spacing(text)
    text = re.sub(r"(?<=[A-Za-z.])-\s+(?=[A-Za-z])", "-", text)
    text = re.sub(r"(?<=\S)\s*=\s*(?=\S)", "=", text)
    text = re.sub(r"(?<=\()=\s*", "=", text)
    return normalize_inline_spacing(text)


SMART_QUOTE_MAP = str.maketrans({
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u201f": '"',
    "\u2018": "'",
    "\u2019": "'",
    "\u02bc": "'",
})


def xml_clean_text(text: str) -> str:
    return clean_space(text.translate(SMART_QUOTE_MAP))


def strip_outer_punct(token: str) -> tuple[str, str, str]:
    token = token.strip()
    m1 = re.match(r"^([\"'“”‘’(\[]+)(.*)$", token)
    leading = m1.group(1) if m1 else ""
    core = m1.group(2) if m1 else token
    m2 = re.match(r"^(.*?)([\"'“”‘’,.;:!?、。)\]]+)$", core)
    trailing = m2.group(2) if m2 else ""
    core = m2.group(1) if m2 else core
    return leading, core, trailing


def remove_footnote_anchors(text: str, known_numbers: set[str] | None = None) -> tuple[str, list[str]]:
    refs: list[str] = []

    def repl(match: re.Match[str]) -> str:
        head = match.group("head")
        punct = match.group("punct") or ""
        num = match.group("num")
        tail = match.group("tail") or ""
        if known_numbers and num not in known_numbers:
            return match.group(0)
        refs.append(num)
        return f"{head}{punct}{tail}"

    pattern = re.compile(
        r"(?P<head>[A-Za-zʔŋəɨʉƏáéíóúÁÉÍÓÚ]+)"
        r"(?P<punct>[,.;:!?]?)"
        r"(?P<num>\d{1,3})(?P<tail>(?=[=(),.;:!?]|\s|$))"
    )
    return pattern.sub(repl, text), refs


@dataclass
class Line:
    line_id: str
    physical_page: int
    printed_page: int | None
    block: int
    line: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    words: list[dict[str, Any]] = field(default_factory=list)

    @property
    def marker(self) -> int | None:
        if self.words and re.fullmatch(r"\(\d+\)", self.words[0]["text"]):
            return int(self.words[0]["text"].strip("()"))
        m = re.match(r"^\((\d+)\)\s*$", self.text.strip())
        return int(m.group(1)) if m else None

    def content_without_marker(self) -> str:
        if self.words and re.fullmatch(r"\(\d+\)", self.words[0]["text"]):
            return " ".join(w["text"] for w in self.words[1:]).strip()
        return re.sub(r"^\(\d+\)\s*", "", self.text).strip()


def detect_printed_page(words: list[tuple[Any, ...]], phys: int) -> tuple[int | None, str, str]:
    candidates: list[tuple[float, int]] = []
    for w in words:
        x0, y0, x1, y1, text = w[:5]
        if re.fullmatch(r"0?\d{1,3}", str(text)) and 230 <= x0 <= 285 and 630 <= y0 <= 690:
            try:
                candidates.append((float(y0), int(str(text))))
            except ValueError:
                pass
    if not candidates:
        return None, "none", ""
    candidates.sort()
    if phys >= 104:
        # Later pages have a spurious upper number one greater than the visual footer.
        chosen = candidates[-1][1]
        method = "lower_footer"
    else:
        chosen = Counter(n for _, n in candidates).most_common(1)[0][0]
        method = "footer"
    warnings = "" if len(set(n for _, n in candidates)) <= 1 else f"duplicate_footer_numbers={candidates}"
    return chosen, method, warnings


def page_lines_from_words(words: list[tuple[Any, ...]], physical_page: int, printed_page: int | None) -> list[Line]:
    grouped_rows: list[list[tuple[Any, ...]]] = []
    for w in sorted(words, key=lambda item: (float(item[1]), float(item[0]))):
        if not grouped_rows:
            grouped_rows.append([w])
            continue
        current_y = sum(float(item[1]) for item in grouped_rows[-1]) / len(grouped_rows[-1])
        if abs(float(w[1]) - current_y) <= 3.2:
            grouped_rows[-1].append(w)
        else:
            grouped_rows.append([w])
    lines: list[Line] = []
    for line_no, items in enumerate(grouped_rows):
        items = sorted(items, key=lambda w: (float(w[0]), int(w[7])))
        text = " ".join(str(w[4]) for w in items)
        x0 = min(float(w[0]) for w in items)
        y0 = min(float(w[1]) for w in items)
        x1 = max(float(w[2]) for w in items)
        y1 = max(float(w[3]) for w in items)
        block = int(items[0][5]) if items else 0
        line_id = f"p{physical_page:04d}_v{line_no:03d}"
        lines.append(Line(
            line_id=line_id,
            physical_page=physical_page,
            printed_page=printed_page,
            block=block,
            line=line_no,
            x0=x0,
            y0=y0,
            x1=x1,
            y1=y1,
            text=text,
            words=[
                {
                    "text": str(w[4]),
                    "x0": float(w[0]),
                    "y0": float(w[1]),
                    "x1": float(w[2]),
                    "y1": float(w[3]),
                    "word_index": int(w[7]),
                }
                for w in items
            ],
        ))
    return sorted(lines, key=lambda ln: (ln.y0, ln.x0))


def extract_all_pages(render: bool = True) -> tuple[list[dict[str, Any]], dict[int, list[Line]]]:
    ensure_dirs()
    pdf = source_pdf()
    doc = fitz.open(pdf)
    page_rows: list[dict[str, Any]] = []
    all_positioned: list[dict[str, Any]] = []
    lines_by_page: dict[int, list[Line]] = {}
    for idx, page in enumerate(doc, start=1):
        words = page.get_text("words")
        printed, method, warnings = detect_printed_page(words, idx)
        raw_text = page.get_text("text")
        (ROOT / f"data/raw/text/pages/page_{idx:04d}.txt").write_text(raw_text, encoding="utf-8")

        word_rows: list[dict[str, Any]] = []
        for word_no, w in enumerate(words):
            x0, y0, x1, y1, text, block, line_no, word_index = w[:8]
            zone = "unknown"
            if y0 > 640 and re.fullmatch(r"\d{1,3}", str(text)):
                zone = "page_footer"
            elif y0 > 580:
                zone = "footnote"
            elif re.fullmatch(r"\(\d+\)", str(text)):
                zone = "sentence_number"
            row = {
                "word_id": f"p{idx:04d}_w{word_no:05d}",
                "physical_page_number": idx,
                "printed_page_number": printed,
                "block_index": int(block),
                "line_index": int(line_no),
                "span_index": "",
                "word_index": int(word_index),
                "raw_text": str(text),
                "clean_text": unicodedata.normalize("NFC", str(text)),
                "x0": float(x0),
                "y0": float(y0),
                "x1": float(x1),
                "y1": float(y1),
                "font_name": "",
                "font_size": "",
                "font_flags": "",
                "is_bold": False,
                "is_italic": False,
                "reading_order": word_no,
                "likely_zone": zone,
                "likely_tier": "unknown",
                "parse_confidence": "raw",
                "warnings": "",
            }
            word_rows.append(row)
            all_positioned.append(row)
        write_jsonl(ROOT / f"data/raw/words/pages/page_{idx:04d}.words.jsonl", word_rows)

        blocks = page.get_text("blocks")
        block_rows = [
            {
                "physical_page_number": idx,
                "printed_page_number": printed,
                "block_index": int(b[5]) if len(b) > 5 else n,
                "x0": b[0],
                "y0": b[1],
                "x1": b[2],
                "y1": b[3],
                "text": b[4],
            }
            for n, b in enumerate(blocks)
        ]
        write_jsonl(ROOT / f"data/raw/blocks/pages/page_{idx:04d}.blocks.jsonl", block_rows)

        spans: list[dict[str, Any]] = []
        for bno, block in enumerate(page.get_text("dict").get("blocks", [])):
            for lno, line in enumerate(block.get("lines", [])):
                for sno, span in enumerate(line.get("spans", [])):
                    bbox = span.get("bbox", [0, 0, 0, 0])
                    font = span.get("font", "")
                    flags = int(span.get("flags", 0))
                    spans.append({
                        "physical_page_number": idx,
                        "printed_page_number": printed,
                        "block_index": bno,
                        "line_index": lno,
                        "span_index": sno,
                        "text": span.get("text", ""),
                        "x0": bbox[0],
                        "y0": bbox[1],
                        "x1": bbox[2],
                        "y1": bbox[3],
                        "font_name": font,
                        "font_size": span.get("size", ""),
                        "font_flags": flags,
                        "is_bold": "bold" in font.lower() or bool(flags & 16),
                        "is_italic": "italic" in font.lower() or bool(flags & 2),
                    })
        write_jsonl(ROOT / f"data/raw/spans/pages/page_{idx:04d}.spans.jsonl", spans)

        render_path = ROOT / f"data/raw/renders/page_{idx:04d}.png"
        if render and not render_path.exists():
            pix = page.get_pixmap(matrix=fitz.Matrix(180 / 72, 180 / 72), alpha=False)
            pix.save(render_path)

        lines = page_lines_from_words(words, idx, printed)
        lines_by_page[idx] = lines
        write_jsonl(ROOT / f"data/raw/blocks/pages/page_{idx:04d}.lines.jsonl", [
            {
                "line_id": ln.line_id,
                "physical_page": ln.physical_page,
                "printed_page": ln.printed_page,
                "block": ln.block,
                "line": ln.line,
                "x0": ln.x0,
                "y0": ln.y0,
                "x1": ln.x1,
                "y1": ln.y1,
                "text": ln.text,
                "words": ln.words,
            }
            for ln in lines
        ])

        page_rows.append({
            "physical_page_number": idx,
            "printed_page_number": printed,
            "printed_page_detection_method": method,
            "section": classify_page_section(printed),
            "part_number": part_for_printed_page(printed),
            "text_ids_present": "",
            "page_width_points": round(page.rect.width, 3),
            "page_height_points": round(page.rect.height, 3),
            "rotation": page.rotation,
            "has_text_layer": bool(raw_text.strip()),
            "character_count": len(raw_text),
            "word_count": len(words),
            "block_count": len(blocks),
            "image_count": len(page.get_images(full=True)),
            "raw_text_path": f"data/raw/text/pages/page_{idx:04d}.txt",
            "positioned_words_path": f"data/raw/words/pages/page_{idx:04d}.words.jsonl",
            "positioned_blocks_path": f"data/raw/blocks/pages/page_{idx:04d}.blocks.jsonl",
            "render_path": f"data/raw/renders/page_{idx:04d}.png" if render_path.exists() else "",
            "extraction_status": "ok",
            "parse_status": "pending",
            "warnings": warnings,
        })
    write_jsonl(ROOT / "data/processed/positioned_words.jsonl", all_positioned)
    write_csv(ROOT / "data/processed/pages.csv", page_rows, [
        "physical_page_number", "printed_page_number", "printed_page_detection_method",
        "section", "part_number", "text_ids_present", "page_width_points", "page_height_points",
        "rotation", "has_text_layer", "character_count", "word_count", "block_count",
        "image_count", "raw_text_path", "positioned_words_path", "positioned_blocks_path",
        "render_path", "extraction_status", "parse_status", "warnings",
    ])
    return page_rows, lines_by_page


def load_lines_by_page() -> dict[int, list[Line]]:
    lines_by_page: dict[int, list[Line]] = {}
    for path in sorted((ROOT / "data/raw/blocks/pages").glob("page_*.lines.jsonl")):
        rows = read_jsonl(path)
        if not rows:
            continue
        phys = int(rows[0]["physical_page"])
        lines_by_page[phys] = [
            Line(
                line_id=r["line_id"],
                physical_page=r["physical_page"],
                printed_page=r.get("printed_page"),
                block=r["block"],
                line=r["line"],
                x0=r["x0"],
                y0=r["y0"],
                x1=r["x1"],
                y1=r["y1"],
                text=r["text"],
                words=r["words"],
            )
            for r in rows
        ]
    if not lines_by_page:
        _, lines_by_page = extract_all_pages(render=False)
    return lines_by_page


def classify_page_section(printed: int | None) -> str:
    if printed is None:
        return "unknown_or_cover"
    if printed < 28:
        return "front_matter_or_introduction"
    if printed <= 247:
        return "corpus_texts"
    return "back_matter"


def part_for_printed_page(printed: int | None) -> str:
    if printed is None:
        return ""
    current = ""
    for row in TEXT_INVENTORY:
        if printed >= row["page"]:
            current = str(row["part"])
    return current


def physical_from_printed(printed: int) -> int:
    return printed + 5


def build_text_inventory(lines_by_page: dict[int, list[Line]] | None = None) -> list[dict[str, Any]]:
    if lines_by_page is None:
        lines_by_page = load_lines_by_page()
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(TEXT_INVENTORY, start=1):
        next_page = TEXT_INVENTORY[idx]["page"] if idx < len(TEXT_INVENTORY) else 247
        end_page = max(item["page"], next_page - 1)
        part_title, collector, part_short = PARTS[item["part"]]
        tid = text_id(idx, item["title"])
        start_phys = physical_from_printed(item["page"])
        end_phys = physical_from_printed(end_page)
        heading = detect_heading(lines_by_page.get(start_phys, []), item["num"], item["title"])
        rows.append({
            "text_id": tid,
            "global_text_order": idx,
            "part_number": item["part"],
            "part_title": part_short,
            "collector": collector,
            "text_number_within_part": item["num"],
            "title_english_raw": heading.get("title_english_raw") or item["title"],
            "title_english_clean": item["title"],
            "title_kanakanavu_raw": heading.get("title_kanakanavu_raw", ""),
            "title_kanakanavu_clean": heading.get("title_kanakanavu_clean", ""),
            "informant_raw": heading.get("informant_raw", ""),
            "informant_name": heading.get("informant_name", ""),
            "informant_gender": heading.get("informant_gender", ""),
            "informant_age": heading.get("informant_age", ""),
            "checked_with_raw": heading.get("checked_with_raw", ""),
            "checked_with_name": heading.get("checked_with_name", ""),
            "recording_or_check_date_raw": heading.get("date_raw", ""),
            "date_start_iso": heading.get("date_start_iso", ""),
            "date_end_iso": heading.get("date_end_iso", ""),
            "original_collection_year": source_year_for_part(item["part"]),
            "printed_page_start": item["page"],
            "printed_page_end": end_page,
            "physical_page_start": start_phys,
            "physical_page_end": end_phys,
            "source_page_numbers": list(range(item["page"], end_page + 1)),
            "source_pdf_path": f"data/raw/pdf/{PDF_NAME}",
            "source_pdf_sha256": EXPECTED_SHA256,
            "story_intro_raw": "",
            "story_closing_note_raw": "",
            "field_notebook_reference": "",
            "Japanese_translation_reference": "",
            "original_publication_reference": "",
            "license": "CC BY 4.0",
            "parse_confidence": "medium" if heading.get("header_detected") else "low",
            "warnings": heading.get("warnings", ""),
            "xml_file": xml_filename(idx, item["title"]),
        })
    return rows


def grammar_example_text_inventory() -> dict[str, Any]:
    return {
        "text_id": GRAMMAR_EXAMPLE_TEXT_ID,
        "global_text_order": 0,
        "part_number": 0,
        "part_title": "Grammatical introduction",
        "collector": "Kanakanavu Texts introduction",
        "text_number_within_part": 0,
        "title_english_raw": GRAMMAR_EXAMPLE_TITLE,
        "title_english_clean": GRAMMAR_EXAMPLE_TITLE,
        "title_kanakanavu_raw": "",
        "title_kanakanavu_clean": "",
        "informant_raw": "",
        "informant_name": "",
        "informant_gender": "",
        "informant_age": "",
        "checked_with_raw": "",
        "checked_with_name": "",
        "recording_or_check_date_raw": "",
        "date_start_iso": "",
        "date_end_iso": "",
        "original_collection_year": "source grammatical introduction",
        "printed_page_start": GRAMMAR_EXAMPLE_PRINTED_START,
        "printed_page_end": GRAMMAR_EXAMPLE_PRINTED_END,
        "physical_page_start": min(GRAMMAR_EXAMPLE_PHYSICAL_PAGES),
        "physical_page_end": max(GRAMMAR_EXAMPLE_PHYSICAL_PAGES),
        "source_page_numbers": list(range(GRAMMAR_EXAMPLE_PRINTED_START, GRAMMAR_EXAMPLE_PRINTED_END + 1)),
        "source_pdf_path": f"data/raw/pdf/{PDF_NAME}",
        "source_pdf_sha256": EXPECTED_SHA256,
        "story_intro_raw": "",
        "story_closing_note_raw": "",
        "field_notebook_reference": "",
        "Japanese_translation_reference": "",
        "original_publication_reference": "",
        "license": "CC BY 4.0",
        "parse_confidence": "high",
        "warnings": "grammatical_introduction_examples_not_in_toc",
        "xml_file": xml_filename(0, GRAMMAR_EXAMPLE_TITLE),
        "text_kind": "grammar_examples",
    }


def source_year_for_part(part: int) -> str:
    return {1: "1931", 2: "1978", 3: "1999-2000; 2025", 4: "2008-2013"}[part]


def detect_heading(lines: list[Line], text_num: int, expected_title: str) -> dict[str, str]:
    result: dict[str, str] = {"header_detected": "", "warnings": ""}
    heading_idx = None
    for i, ln in enumerate(lines):
        if re.search(rf"\bText\s+{text_num}\.\s+", ln.text):
            if clean_title(ln.text).lower().startswith(expected_title.lower()[:12].lower()) or "Text" in ln.text:
                heading_idx = i
                break
    if heading_idx is None:
        result["warnings"] = "heading_not_detected_on_expected_physical_page"
        return result
    result["header_detected"] = "yes"
    heading_text = lines[heading_idx].text
    m = re.search(r"Text\s+\d+\.\s*(.+)$", heading_text)
    if m:
        result["title_english_raw"] = m.group(1)
    result["title_english_clean"] = clean_title(result.get("title_english_raw", expected_title))
    for ln in lines[heading_idx + 1: heading_idx + 8]:
        text = ln.text.strip()
        if not text:
            continue
        if text.startswith(("Informant:", "Checked with:", "Date:")) or re.match(r"^\(\d+\)", text):
            break
        if not result.get("title_kanakanavu_raw") and not text.startswith("Text "):
            result["title_kanakanavu_raw"] = text
            result["title_kanakanavu_clean"] = clean_title(text)
            break
    for ln in lines[heading_idx + 1: heading_idx + 12]:
        text = ln.text.strip()
        if text.startswith("Informant:"):
            result["informant_raw"] = text
            parse_person_metadata(text, "informant", result)
        elif text.startswith("Checked with:"):
            result["checked_with_raw"] = text
            parse_person_metadata(text, "checked_with", result)
        elif text.startswith("Date:"):
            result["date_raw"] = text.replace("Date:", "").strip()
            parse_dates(result["date_raw"], result)
    return result


def clean_title(text: str) -> str:
    cleaned, _ = remove_footnote_anchors(clean_space(text), None)
    return cleaned.strip()


def parse_person_metadata(text: str, prefix: str, result: dict[str, str]) -> None:
    body = re.sub(r"^(Informant|Checked with):\s*", "", text).strip()
    parts = [p.strip() for p in body.split(",")]
    name = parts[0] if parts else body
    if prefix == "informant":
        result["informant_name"] = name
    else:
        result["checked_with_name"] = name
    for part in parts[1:]:
        if part in {"male", "female"}:
            result[f"{prefix}_gender"] = part
        m = re.search(r"Age\s+(\d+)", part)
        if m:
            result[f"{prefix}_age"] = m.group(1)


def parse_dates(raw: str, result: dict[str, str]) -> None:
    dates = re.findall(r"\d{4}\.\d{2}\.\d{2}|\d{4}", raw)
    if dates:
        result["date_start_iso"] = dates[0].replace(".", "-")
        result["date_end_iso"] = dates[-1].replace(".", "-")


def parse_toc() -> None:
    lines_by_page = load_lines_by_page()
    texts = build_text_inventory(lines_by_page)
    rows: list[dict[str, Any]] = []
    for text in texts:
        rows.append({
            "global_text_order": text["global_text_order"],
            "part_number": text["part_number"],
            "part_title": text["part_title"],
            "collector": text["collector"],
            "text_number_within_part": text["text_number_within_part"],
            "title_english_raw": text["title_english_raw"],
            "title_english_clean": text["title_english_clean"],
            "title_kanakanavu_raw": text["title_kanakanavu_raw"],
            "title_kanakanavu_clean": text["title_kanakanavu_clean"],
            "printed_page_start": text["printed_page_start"],
            "printed_page_end": text["printed_page_end"],
            "physical_page_start": text["physical_page_start"],
            "physical_page_end": text["physical_page_end"],
            "expected_from_toc": True,
            "header_detected": text["parse_confidence"] != "low",
            "parse_confidence": text["parse_confidence"],
            "warnings": text["warnings"],
        })
    write_csv(ROOT / "data/processed/toc_entries.csv", rows, [
        "global_text_order", "part_number", "part_title", "collector",
        "text_number_within_part", "title_english_raw", "title_english_clean",
        "title_kanakanavu_raw", "title_kanakanavu_clean", "printed_page_start",
        "printed_page_end", "physical_page_start", "physical_page_end",
        "expected_from_toc", "header_detected", "parse_confidence", "warnings",
    ])


def segment_texts() -> list[dict[str, Any]]:
    lines_by_page = load_lines_by_page()
    texts = [grammar_example_text_inventory()] + build_text_inventory(lines_by_page)
    write_jsonl(ROOT / "data/processed/texts.jsonl", texts)
    return texts


def text_bounds_by_page(texts: list[dict[str, Any]], lines_by_page: dict[int, list[Line]]) -> dict[str, dict[int, tuple[float, float]]]:
    bounds: dict[str, dict[int, tuple[float, float]]] = {}
    for i, text in enumerate(texts):
        tid = text["text_id"]
        bounds[tid] = {}
        next_text = texts[i + 1] if i + 1 < len(texts) else None
        for phys in range(text["physical_page_start"], text["physical_page_end"] + 1):
            start_y = 45.0
            end_y = 640.0
            lines = lines_by_page.get(phys, [])
            if phys == text["physical_page_start"]:
                first_marker = first_sentence_y_after_heading(lines, text["text_number_within_part"])
                if first_marker is not None:
                    start_y = max(45.0, first_marker - 2)
            if next_text and phys == next_text["physical_page_start"]:
                heading_y = heading_y_for_text(lines, next_text["text_number_within_part"])
                if heading_y is not None:
                    end_y = min(end_y, heading_y - 2)
            bounds[tid][phys] = (start_y, end_y)
    return bounds


def first_sentence_y_after_heading(lines: list[Line], text_num: int) -> float | None:
    hy = heading_y_for_text(lines, text_num)
    for ln in lines:
        if hy is not None and ln.y0 <= hy:
            continue
        if ln.marker is not None:
            return ln.y0
    return None


def heading_y_for_text(lines: list[Line], text_num: int) -> float | None:
    for ln in lines:
        if re.search(rf"\bText\s+{text_num}\.\s+", ln.text):
            return ln.y0
    return None


def is_sentence_line(ln: Line, start_y: float, end_y: float) -> bool:
    if not (start_y <= ln.y0 <= end_y):
        return False
    if ln.y0 > 585 and re.match(r"^\d+\s+", ln.text):
        return False
    if ln.marker is None and ln.x0 < 90:
        return False
    if ln.x0 < 60 or ln.x0 > 455:
        return False
    if re.fullmatch(r"\d{1,3}", ln.text.strip()) and ln.x0 > 220:
        return False
    if ln.text.startswith(("Part ", "Text ")):
        return False
    return True


def is_page_bottom_translation_continuation(
    ln: Line,
    current_lines: list[Line],
    end_y: float,
) -> bool:
    """Recover a final translation line below the narrative body cutoff.

    The source places 12 final free translations between y=640 and y=650.
    Footnotes in that band start farther left, at about x=77, and page numbers
    occur below y=660. This rule applies only to a source/gloss group that still
    lacks a translation, so it cannot absorb a footer into a completed unit.
    """
    if end_y < 639.0 or ln.marker is not None:
        return False
    if not (640.0 < ln.y0 <= 650.0 and 94.0 <= ln.x0 <= 455.0):
        return False
    if re.match(r"^\d{1,3}\s+", ln.text.strip()):
        return False
    source, gloss, translation, _confidence = classify_unit_lines(current_lines)
    return bool(
        source
        and gloss
        and not translation
        and looks_like_translation(ln.content_without_marker())
    )


def grammar_example_start_from_line(ln: Line, last_number: int | None) -> tuple[int, str, int] | None:
    text = ln.text.strip()
    numbered = re.match(r"^\((\d+)\)\s*(.+)$", text)
    if numbered:
        number = int(numbered.group(1))
        if number not in GRAMMAR_EXAMPLE_EXPECTED_NUMBERS:
            return None
        label = ""
        skip_words = 1
        body = numbered.group(2)
        if number in GRAMMAR_EXAMPLE_SUBNUMBERED:
            labeled = re.match(r"^([a-d])\.?\s+(.+)$", body)
            if labeled:
                label = labeled.group(1)
                skip_words = 2
        return number, label, skip_words
    subexample = re.match(r"^([a-d])\.?\s+(.+)$", text)
    if (
        subexample
        and last_number in GRAMMAR_EXAMPLE_SUBNUMBERED
        and 95 <= ln.x0 <= 125
    ):
        return last_number, subexample.group(1), 1
    return None


def clone_grammar_start_line(ln: Line, number: int, skip_words: int) -> Line:
    body_words = [dict(w) for w in ln.words[skip_words:]]
    if ln.words:
        marker = dict(ln.words[0])
    else:
        marker = {"x0": ln.x0, "y0": ln.y0, "x1": ln.x0, "y1": ln.y1, "word_index": 0}
    marker["text"] = f"({number})"
    words = [marker] + body_words
    for idx, word in enumerate(words):
        word["word_index"] = idx
    body = " ".join(str(w.get("text", "")) for w in body_words).strip()
    return Line(
        line_id=ln.line_id,
        physical_page=ln.physical_page,
        printed_page=ln.printed_page,
        block=ln.block,
        line=ln.line,
        x0=ln.x0,
        y0=ln.y0,
        x1=ln.x1,
        y1=ln.y1,
        text=f"({number}) {body}".strip(),
        words=words,
    )


def grammar_group_complete(lines: list[Line]) -> bool:
    source, gloss, translation, _confidence = classify_unit_lines(lines)
    return bool(source and gloss and translation) or (
        len(lines) >= 3 and looks_like_translation(lines[-1].content_without_marker())
    )


def grammar_prose_boundary(ln: Line, current_lines: list[Line]) -> bool:
    if not grammar_group_complete(current_lines):
        return False
    if ln.x0 < 90:
        return True
    prose_starters = (
        "If we treat",
        "Notice that",
        "The prefix",
        "Future aspect",
        "Progressive is",
        "Similarly,",
        "In addition,",
        "The norm",
        "Compare the",
        "One primary",
        "There is",
        "There are",
        "According to",
        "For Actor",
        "Table ",
        "A free",
        "As stated",
    )
    return ln.x0 < 105 and ln.text.strip().startswith(prose_starters)


def parse_grammar_example_units(
    text: dict[str, Any],
    lines_by_page: dict[int, list[Line]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    last_number: int | None = None
    for phys in GRAMMAR_EXAMPLE_PHYSICAL_PAGES:
        for ln in lines_by_page.get(phys, []):
            if not (45 <= ln.y0 <= 658):
                continue
            start = grammar_example_start_from_line(ln, last_number)
            if start:
                number, label, skip_words = start
                if current:
                    groups.append(current)
                current = {
                    "number": number,
                    "label": label,
                    "lines": [clone_grammar_start_line(ln, number, skip_words)],
                }
                last_number = number
                continue
            if current is None:
                continue
            if grammar_prose_boundary(ln, current["lines"]):
                groups.append(current)
                current = None
                continue
            if ln.x0 >= 90 or not grammar_group_complete(current["lines"]):
                current["lines"].append(ln)
    if current:
        groups.append(current)

    found_numbers = {group["number"] for group in groups}
    if found_numbers != GRAMMAR_EXAMPLE_EXPECTED_NUMBERS or len(groups) != GRAMMAR_EXAMPLE_EXPECTED_UNIT_COUNT:
        missing = sorted(GRAMMAR_EXAMPLE_EXPECTED_NUMBERS - found_numbers)
        extra = sorted(found_numbers - GRAMMAR_EXAMPLE_EXPECTED_NUMBERS)
        raise SystemExit(
            "Introduction example extraction mismatch: "
            f"units={len(groups)} expected={GRAMMAR_EXAMPLE_EXPECTED_UNIT_COUNT} "
            f"missing={missing} extra={extra}"
        )

    units: list[dict[str, Any]] = []
    word_rows: list[dict[str, Any]] = []
    morph_rows: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []
    for unit_order, group in enumerate(groups, start=1):
        unit, words, morphs, rej = build_unit(text, group["number"], unit_order, group["lines"])
        label = f"({group['number']}{group['label']})" if group["label"] else f"({group['number']})"
        unit["source_sentence_label"] = label
        unit["grammar_example_number"] = group["number"]
        unit["grammar_example_sublabel"] = group["label"]
        unit["parse_method"] = "grammar_introduction_example_line_pairing"
        for row in rej:
            row["source_sentence_label"] = label
        units.append(unit)
        word_rows.extend(words)
        morph_rows.extend(morphs)
        rejects.extend(rej)
    return units, word_rows, morph_rows, rejects


def unit_lines_have_content(lines: list[Line]) -> bool:
    return any(ln.content_without_marker() for ln in lines)


def parse_sentence_units() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    texts = segment_texts()
    lines_by_page = load_lines_by_page()
    narrative_texts = [t for t in texts if t.get("text_kind") != "grammar_examples"]
    bounds = text_bounds_by_page(narrative_texts, lines_by_page)
    units: list[dict[str, Any]] = []
    word_rows: list[dict[str, Any]] = []
    morph_rows: list[dict[str, Any]] = []
    rejects: list[dict[str, Any]] = []
    for text in texts:
        if text.get("text_kind") == "grammar_examples":
            g_units, g_words, g_morphs, g_rejects = parse_grammar_example_units(text, lines_by_page)
            units.extend(g_units)
            word_rows.extend(g_words)
            morph_rows.extend(g_morphs)
            rejects.extend(g_rejects)
            continue
        current_lines: list[Line] = []
        current_num: int | None = None
        unit_order = 0
        for phys in range(text["physical_page_start"], text["physical_page_end"] + 1):
            start_y, end_y = bounds[text["text_id"]][phys]
            for ln in lines_by_page.get(phys, []):
                if not is_sentence_line(ln, start_y, end_y):
                    if current_lines and is_page_bottom_translation_continuation(
                        ln, current_lines, end_y
                    ):
                        current_lines.append(ln)
                    continue
                marker = ln.marker
                if marker is not None:
                    if current_lines and current_num is not None and unit_lines_have_content(current_lines):
                        unit_order += 1
                        unit, words, morphs, rej = build_unit(text, current_num, unit_order, current_lines)
                        units.append(unit)
                        word_rows.extend(words)
                        morph_rows.extend(morphs)
                        rejects.extend(rej)
                    current_lines = [ln]
                    current_num = marker
                elif current_lines:
                    current_lines.append(ln)
        if current_lines and current_num is not None and unit_lines_have_content(current_lines):
            unit_order += 1
            unit, words, morphs, rej = build_unit(text, current_num, unit_order, current_lines)
            units.append(unit)
            word_rows.extend(words)
            morph_rows.extend(morphs)
            rejects.extend(rej)

    write_jsonl(ROOT / "data/processed/sentence_units.jsonl", units)
    write_jsonl(ROOT / "data/processed/word_units.jsonl", word_rows)
    write_jsonl(ROOT / "data/processed/morpheme_units.jsonl", morph_rows)
    write_csv(ROOT / "data/processed/rejected_records.csv", rejects, [
        "record_id", "text_id", "unit_id", "physical_page", "printed_page",
        "source_sentence_label", "rejection_level", "rejection_reason",
        "source_raw", "gloss_raw", "translation_raw", "source_line_ids", "notes",
    ])
    return units, word_rows, morph_rows, rejects


def line_pair_score(source: Line, gloss: Line) -> float:
    sw = source.words[1:] if source.marker is not None else source.words
    gw = gloss.words
    if not sw or not gw:
        return 0.0
    matches = 0
    used: set[int] = set()
    for s in sw:
        sx = float(s["x0"])
        best_i, best = None, 999.0
        for i, g in enumerate(gw):
            if i in used:
                continue
            dist = abs(float(g["x0"]) - sx)
            if dist < best:
                best_i, best = i, dist
        if best_i is not None and best <= 18:
            used.add(best_i)
            matches += 1
    return min(matches / len(sw), matches / len(gw))


def looks_like_translation(text: str) -> bool:
    if not text:
        return False
    words = text.split()
    if not words:
        return False
    upperish = sum(1 for w in words if looks_like_gloss_marker_token(w))
    has_source_chars = bool(re.search(r"[ʔŋəɨʉƏ]", text))
    common = sum(1 for w in words if w.lower().strip(".,;:!?\"'()") in {
        "the", "a", "an", "and", "or", "when", "if", "in", "on", "to", "of", "with",
        "he", "she", "it", "they", "we", "i", "you", "was", "were", "is", "are",
        "that", "this", "there", "as", "at", "for", "from", "by", "because", "while",
        "would", "could", "should", "will", "be", "been", "being", "not", "no", "his",
        "her", "their", "them", "him", "my", "your", "our", "who", "what", "where",
        "whenever", "although", "only", "one", "already", "still",
        "some", "all", "nothing", "none", "yes", "so", "then", "therefore", "just",
        "people", "person", "man", "woman", "mother", "father", "child", "friend",
        "home", "water", "food", "sun", "rock", "came", "come", "went", "go",
        "grew", "found", "talked", "said", "asked", "answered", "called", "returned",
        "stay", "healthy", "thank", "thanks",
    })
    if common >= 2 and upperish == 0 and not re.search(r"[=<>]", text):
        return True
    starts_like_english = bool(re.match(r'^[("“‘\[]?[A-Z]', text.strip()))
    ends_like_sentence = bool(re.search(r'[.!?”’)]$', text.strip()))
    no_interlinear_markers = upperish == 0 and not has_source_chars and not re.search(r"[=<>]", text)
    return no_interlinear_markers and starts_like_english and ends_like_sentence and len(words) >= 2


def looks_like_gloss_marker_token(token: str) -> bool:
    core = token.strip(".,;:!?\"'()[]“”‘’")
    return bool(
        re.search(r"[A-Z]{2,}|[=<>-]", core)
        or re.search(r"[A-Za-z0-9]\.[A-Za-z0-9]", core)
    )


def line_pair_y_compatible(source: Line, gloss: Line) -> bool:
    ydiff = gloss.y0 - source.y0
    if source.physical_page == gloss.physical_page:
        return 8 <= ydiff <= 24
    return (
        gloss.physical_page == source.physical_page + 1
        and source.y0 > 580
        and gloss.y0 < 135
    )


def is_source_gloss_pair(source: Line, gloss: Line) -> bool:
    return (
        line_pair_y_compatible(source, gloss)
        and line_pair_score(source, gloss) >= 0.45
        and not looks_like_translation(source.content_without_marker())
        and not looks_like_translation(gloss.content_without_marker())
    )


def short_gloss_continuation(previous: Line, candidate: Line) -> bool:
    text = candidate.content_without_marker().strip()
    if not text or len(text.split()) > 2:
        return False
    if re.search(r"[ʔŋəɨʉƏ]", text):
        return False
    if candidate.physical_page != previous.physical_page:
        return False
    if not (8 <= candidate.y0 - previous.y0 <= 24):
        return False
    if any(looks_like_gloss_marker_token(token) for token in text.split()):
        return True
    if not re.fullmatch(r"[A-Z]", text) or len(candidate.words) != 1:
        return False
    suffix_x = float(candidate.words[0].get("x0", candidate.x0))
    return any(
        re.search(r"[A-Z]$", str(word.get("text", "")))
        and abs(float(word.get("x0", 0)) - suffix_x) <= 12
        for word in previous.words
    )


def merge_line_text(first: Line, second: Line) -> Line:
    first_words = [dict(word) for word in first.words]
    second_words = [dict(word) for word in second.words]
    extra_words: list[dict[str, Any]] = []
    merged_indexes: set[int] = set()
    for second_word in second_words:
        second_text = str(second_word.get("text", ""))
        candidates = [
            (abs(float(word.get("x0", 0)) - float(second_word.get("x0", 0))), idx)
            for idx, word in enumerate(first_words)
            if idx not in merged_indexes
            and (
                str(word.get("text", "")).endswith("-")
                or (
                    re.fullmatch(r"[A-Z]", second_text)
                    and re.search(r"[A-Z]$", str(word.get("text", "")))
                )
            )
        ]
        if candidates:
            distance, idx = min(candidates)
            max_distance = 12 if re.fullmatch(r"[A-Z]", second_text) else 45
            if distance <= max_distance:
                merged = dict(first_words[idx])
                merged["text"] = f"{first_words[idx]['text']}{second_text}"
                merged["x1"] = max(float(merged.get("x1", 0)), float(second_word.get("x1", 0)))
                first_words[idx] = merged
                merged_indexes.add(idx)
                continue
        extra_words.append(second_word)
    words = first_words + extra_words
    for idx, word in enumerate(words):
        word["word_index"] = idx
    text = normalize_inline_spacing(" ".join(str(word["text"]) for word in words))
    return Line(
        line_id=f"{first.line_id}+{second.line_id}",
        physical_page=first.physical_page,
        printed_page=first.printed_page,
        block=first.block,
        line=first.line,
        x0=min(first.x0, second.x0),
        y0=min(first.y0, second.y0),
        x1=max(first.x1, second.x1),
        y1=max(first.y1, second.y1),
        text=text,
        words=words,
    )


def classify_unit_lines(lines: list[Line]) -> tuple[list[Line], list[Line], list[Line], str]:
    repaired = classify_known_line_pair_artifact(lines)
    if repaired is not None:
        return repaired
    content = [ln for ln in lines if ln.content_without_marker()]
    source: list[Line] = []
    gloss: list[Line] = []
    translation: list[Line] = []
    i = 0
    while i + 1 < len(content):
        a, b = content[i], content[i + 1]
        if is_source_gloss_pair(a, b):
            source.append(a)
            gloss.append(b)
            i += 2
            while (
                i < len(content)
                and short_gloss_continuation(gloss[-1], content[i])
                and not (i + 1 < len(content) and is_source_gloss_pair(content[i], content[i + 1]))
            ):
                gloss[-1] = merge_line_text(gloss[-1], content[i])
                i += 1
            continue
        break
    translation = content[i:]
    confidence = "high" if source and gloss and translation else "low"
    if source and gloss and translation and any(line_pair_score(s, g) < 0.7 for s, g in zip(source, gloss)):
        confidence = "medium"
    return source, gloss, translation, confidence


def classify_known_line_pair_artifact(lines: list[Line]) -> tuple[list[Line], list[Line], list[Line], str] | None:
    by_id = {ln.line_id: ln for ln in lines}
    needed = {
        "p0099_v029", "p0099_v030", "p0099_v031", "p0099_v032",
        "p0099_v033", "p0099_v034", "p0100_v000", "p0100_v001", "p0100_v002",
    }
    if not needed.issubset(by_id):
        return None
    source = [by_id["p0099_v029"], by_id["p0099_v032"], by_id["p0099_v034"]]
    gloss = [
        repaired_naparamaci_121_gloss_line(by_id["p0099_v030"], by_id["p0099_v031"]),
        by_id["p0099_v033"],
        by_id["p0100_v000"],
    ]
    translation = [by_id["p0100_v001"], by_id["p0100_v002"]]
    return source, gloss, translation, "medium"


def repaired_naparamaci_121_gloss_line(av_line: Line, leave_line: Line) -> Line:
    av_words = [dict(w) for w in av_line.words]
    leave_words = [dict(w) for w in leave_line.words]
    if len(av_words) < 4 or len(leave_words) < 2:
        return av_line
    first = dict(av_words[0])
    first["text"] = f"{av_words[0]['text']}{leave_words[0]['text']}"
    first["x1"] = leave_words[0]["x1"]
    words = [first, av_words[1], av_words[2], leave_words[1], av_words[3]]
    for idx, word in enumerate(words):
        word["word_index"] = idx
    text = " ".join(str(word["text"]) for word in words)
    return Line(
        line_id=f"{av_line.line_id}_repaired",
        physical_page=av_line.physical_page,
        printed_page=av_line.printed_page,
        block=av_line.block,
        line=av_line.line,
        x0=min(float(word["x0"]) for word in words),
        y0=av_line.y0,
        x1=max(float(word["x1"]) for word in words),
        y1=max(av_line.y1, leave_line.y1),
        text=text,
        words=words,
    )


def build_unit(
    text: dict[str, Any],
    sentence_num: int,
    unit_order: int,
    lines: list[Line],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_lines, gloss_lines, trans_lines, confidence = classify_unit_lines(lines)
    known_footnotes = footnote_numbers_on_pages({ln.physical_page for ln in lines})
    source_raw = " ".join(ln.content_without_marker() for ln in source_lines)
    gloss_raw = " ".join(ln.content_without_marker() for ln in gloss_lines)
    trans_raw = " ".join(ln.content_without_marker() for ln in trans_lines)
    source_clean, source_refs = remove_footnote_anchors(source_raw, known_footnotes)
    gloss_clean, gloss_refs = remove_footnote_anchors(gloss_raw, known_footnotes)
    trans_clean, trans_refs = remove_footnote_anchors(trans_raw, known_footnotes)
    source_clean = xml_clean_text(source_clean)
    gloss_clean = xml_clean_text(gloss_clean)
    trans_clean = xml_clean_text(trans_clean)
    unit_id = f"{text['text_id']}_U{unit_order:04d}"
    phys_pages = sorted({ln.physical_page for ln in lines})
    printed_pages = sorted({ln.printed_page for ln in lines if ln.printed_page is not None})
    words, morphs, tier_warnings = build_word_and_morph_rows(unit_id, text, unit_order, source_lines, gloss_lines, known_footnotes)
    unit_w_tier = bool(words) and all(w["alignment_confidence"] in {"high", "medium"} for w in words)
    if any("unresolved_parenthetical" in w.get("warnings", "") for w in words):
        unit_w_tier = False
    source_gloss_complete = bool(
        source_clean
        and gloss_clean
        and source_lines
        and gloss_lines
        and len(source_lines) == len(gloss_lines)
    )
    wm_has_source_analysis_notation = bool(re.search(r"[()\[\]/*]", source_clean))
    if wm_has_source_analysis_notation:
        unit_w_tier = False
        tier_warnings.append("wm_omitted_source_analysis_notation")
    if source_clean and trans_clean and confidence in {"high", "medium"}:
        unit_quality = "xml_eligible"
        unit_confidence = confidence
        translation_confidence = "high"
    elif source_gloss_complete and not trans_clean:
        unit_quality = "xml_eligible_source_only"
        unit_confidence = "medium"
        translation_confidence = "source_absent"
    else:
        unit_quality = "rejected"
        unit_confidence = confidence if source_clean and trans_clean else "low"
        translation_confidence = "high" if trans_clean else "low"
    unit = {
        "unit_id": unit_id,
        "text_id": text["text_id"],
        "global_text_order": text["global_text_order"],
        "source_sentence_label": f"({sentence_num})",
        "source_sentence_number": sentence_num,
        "unit_order": unit_order,
        "physical_page_start": min(phys_pages) if phys_pages else "",
        "physical_page_end": max(phys_pages) if phys_pages else "",
        "printed_page_start": min(printed_pages) if printed_pages else "",
        "printed_page_end": max(printed_pages) if printed_pages else "",
        "source_line_raw": source_raw,
        "source_line_clean": source_clean,
        "gloss_line_raw": gloss_raw,
        "gloss_line_clean": gloss_clean,
        "free_translation_raw": trans_raw,
        "free_translation_clean": trans_clean,
        "source_line_ids": [ln.line_id for ln in source_lines],
        "gloss_line_ids": [ln.line_id for ln in gloss_lines],
        "translation_line_ids": [ln.line_id for ln in trans_lines],
        "source_word_ids": [w["word_id"] for w in words],
        "gloss_word_ids": [w["word_id"] for w in words],
        "footnote_refs": sorted(set(source_refs + gloss_refs + trans_refs)),
        "bold_spans": [],
        "italic_spans": [],
        "editorially_supplied_spans": [],
        "coordinates": {
            "lines": [
                {"line_id": ln.line_id, "page": ln.physical_page, "x0": ln.x0, "y0": ln.y0, "x1": ln.x1, "y1": ln.y1}
                for ln in lines
            ]
        },
        "parse_method": "coordinate_line_pairing",
        "source_confidence": confidence,
        "gloss_confidence": confidence if gloss_clean else "low",
        "translation_confidence": translation_confidence,
        "unit_confidence": unit_confidence,
        "word_tier_candidate": unit_w_tier,
        "morpheme_tier_candidate": bool(morphs),
        "quality_status": unit_quality,
        "warnings": "; ".join(tier_warnings),
    }
    rejects: list[dict[str, Any]] = []
    if unit_quality not in {"xml_eligible", "xml_eligible_source_only"}:
        rejects.append({
            "record_id": f"REJ_{unit_id}",
            "text_id": text["text_id"],
            "unit_id": unit_id,
            "physical_page": unit["physical_page_start"],
            "printed_page": unit["printed_page_start"],
            "source_sentence_label": unit["source_sentence_label"],
            "rejection_level": "S",
            "rejection_reason": "missing_source_or_translation_or_low_sentence_confidence",
            "source_raw": source_raw,
            "gloss_raw": gloss_raw,
            "translation_raw": trans_raw,
            "source_line_ids": [ln.line_id for ln in source_lines],
            "notes": confidence,
        })
    return unit, words if unit_w_tier else [], morphs if unit_w_tier else [], rejects


def footnote_numbers_on_pages(pages: set[int]) -> set[str]:
    nums: set[str] = set()
    for page in pages:
        for row in read_jsonl(ROOT / f"data/raw/blocks/pages/page_{page:04d}.lines.jsonl"):
            text = row.get("text", "")
            if row.get("y0", 0) > 585:
                m = re.match(r"^(\d{1,3})\s+", text)
                if m:
                    nums.add(m.group(1))
    return nums


def build_word_and_morph_rows(
    unit_id: str,
    text: dict[str, Any],
    unit_order: int,
    source_lines: list[Line],
    gloss_lines: list[Line],
    known_footnotes: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    warnings: list[str] = []
    word_rows: list[dict[str, Any]] = []
    morph_rows: list[dict[str, Any]] = []
    word_order = 0
    for sline, gline in zip(source_lines, gloss_lines):
        s_tokens = line_token_entries(sline, known_footnotes, source=True)
        g_tokens = line_token_entries(gline, known_footnotes, source=False)
        aligned_g_tokens: list[dict[str, Any] | None]
        if len(s_tokens) != len(g_tokens):
            aligned_g_tokens = align_gloss_entries_by_source_position(s_tokens, g_tokens)
            if len(aligned_g_tokens) != len(s_tokens):
                warnings.append(f"word_count_mismatch:{sline.line_id}")
        else:
            aligned_g_tokens = g_tokens
        for i, sw in enumerate(s_tokens):
            gw = aligned_g_tokens[i] if i < len(aligned_g_tokens) else None
            src_tok = sw["text"]
            src_refs = sw["refs"]
            gls_tok = gw["text"] if gw is not None else ""
            gls_refs = gw["refs"] if gw is not None else []
            if not src_tok:
                continue
            if re.search(r"[/]", src_tok):
                warnings.append("unresolved_parenthetical_or_slash")
                return [], [], warnings
            word_order += 1
            wid = f"{unit_id}_W{word_order:03d}"
            _, src_core, outer_right = strip_outer_punct(src_tok)
            _, gls_core, _ = strip_outer_punct(gls_tok)
            if source_analysis_token(src_tok):
                src_core = src_tok
            if source_analysis_token(gls_tok):
                gls_core = gls_tok
            if not src_core:
                continue
            if gw is None:
                warnings.append(f"source_gloss_absent:{sline.line_id}:W{word_order}")
            row = {
                "word_id": wid,
                "unit_id": unit_id,
                "word_order": word_order,
                "source_token_raw": sw["raw_text"],
                "source_token_clean": src_core,
                "gloss_token_raw": gw["raw_text"] if gw is not None else "",
                "gloss_token_clean": gls_core,
                "gloss_token_absent": not bool(gls_core),
                "source_bbox": sw["bbox"],
                "gloss_bbox": gw["bbox"] if gw is not None else "",
                "source_page": sline.physical_page,
                "gloss_page": gline.physical_page if gw is not None else "",
                "alignment_method": "line_pair_sequence_coordinate" if gw is not None else "source_token_only",
                "alignment_score": round(line_pair_score(sline, gline), 3),
                "alignment_confidence": (
                    "high" if gw is not None and abs(float(sw["bbox"][0]) - float(gw["bbox"][0])) <= 18 else "medium"
                ),
                "segmentation_markers": "".join(ch for ch in src_core if ch in "-=<>"),
                "outer_punctuation": outer_right,
                "footnote_refs": sorted(set(src_refs + gls_refs)),
                "warnings": "",
            }
            word_rows.append(row)
            morphs = parse_morphemes_for_word(row)
            morph_rows.extend(morphs)
    return word_rows, morph_rows, warnings


def align_gloss_entries_by_source_position(
    source_entries: list[dict[str, Any]],
    gloss_entries: list[dict[str, Any]],
) -> list[dict[str, Any] | None]:
    if not source_entries:
        return []
    source_centers = [bbox_center(entry["bbox"]) for entry in source_entries]
    boundaries = [
        (source_centers[i] + source_centers[i + 1]) / 2
        for i in range(len(source_centers) - 1)
    ]
    groups: list[list[dict[str, Any]]] = [[] for _ in source_entries]
    for gloss in gloss_entries:
        gx = bbox_center(gloss["bbox"])
        index = 0
        while index < len(boundaries) and gx >= boundaries[index]:
            index += 1
        groups[index].append(gloss)
    # A long gloss can cross the next column's centre. Recover a clearly
    # aligned empty column without splitting multiword glosses (PDF pp. 72, 90).
    for index, group in enumerate(groups):
        if group:
            continue
        source_left = source_entries[index]["bbox"][0]
        matches = [
            other for other in (index - 1, index + 1)
            if 0 <= other < len(groups) and len(groups[other]) == 1
            and abs(groups[other][0]["bbox"][0] - source_left) <= 1
        ]
        if len(matches) == 1:
            groups[index], groups[matches[0]] = groups[matches[0]], []
    return [
        merge_token_entries(group, source_entries[index]["text"]) if group else None
        for index, group in enumerate(groups)
    ]


def bbox_center(bbox: Any) -> float:
    if isinstance(bbox, str):
        return 0.0
    return (float(bbox[0]) + float(bbox[2])) / 2


def line_token_entries(line: Line, known_footnotes: set[str], *, source: bool) -> list[dict[str, Any]]:
    raw_words = line.words[1:] if source and line.marker is not None else line.words
    entries: list[dict[str, Any]] = []
    for raw_group in group_analysis_words(raw_words):
        raw_text = " ".join(str(word["text"]) for word in raw_group)
        text, refs = remove_footnote_anchors(raw_text, known_footnotes or None)
        text = xml_clean_text(text)
        text = clean_source_form(text) if source else clean_gloss_form(text)
        bbox = [
            min(float(word["x0"]) for word in raw_group),
            min(float(word["y0"]) for word in raw_group),
            max(float(word["x1"]) for word in raw_group),
            max(float(word["y1"]) for word in raw_group),
        ]
        for token in text.split():
            entries.append({
                "text": token,
                "raw_text": raw_text,
                "bbox": bbox,
                "refs": refs,
            })
    return entries


def group_analysis_words(raw_words: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    groups: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for word in raw_words:
        raw = str(word.get("text", ""))
        if current:
            current.append(word)
            if ")" in raw:
                groups.append(current)
                current = []
            continue
        if "(=" in raw and ")" not in raw:
            current = [word]
        else:
            groups.append([word])
    if current:
        groups.append(current)
    return groups


def source_analysis_token(token: str) -> bool:
    return (
        token.startswith(("(=", "(*", "["))
        or token.endswith("]")
        or "/" in token
    )


def merge_token_entries(entries: list[dict[str, Any]], source_token: str) -> dict[str, Any]:
    if not entries:
        return {"text": "", "raw_text": "", "bbox": "", "refs": []}
    joiner = "=" if "=" in source_token else "-" if "-" in source_token else " "
    text = joiner.join(entry["text"] for entry in entries if entry["text"])
    raw_text = " ".join(entry["raw_text"] for entry in entries if entry["raw_text"])
    refs = sorted({ref for entry in entries for ref in entry.get("refs", [])})
    bbox = entries[0]["bbox"]
    return {"text": text, "raw_text": raw_text, "bbox": bbox, "refs": refs}


def clean_word_token(token: str, known_footnotes: set[str], *, source: bool) -> tuple[str, list[str]]:
    token, refs = remove_footnote_anchors(token, known_footnotes or None)
    token = xml_clean_text(token)
    if source:
        token = clean_source_form(token)
    else:
        token = clean_gloss_form(token)
    return token, refs


def parse_morphemes_for_word(word: dict[str, Any]) -> list[dict[str, Any]]:
    source = word["source_token_clean"]
    gloss = word["gloss_token_clean"]
    if re.search(r"[()\[\]*/]", source):
        return []
    segmented = any(ch in source for ch in "-=<>")
    src_parts = (
        split_morphemes(source, is_source=True)
        if segmented
        else [(source, "root")]
    )
    gls_parts = (
        split_morphemes(gloss, is_source=False)
        if segmented
        else [(gloss, "root")]
    )
    if len(gls_parts) > len(src_parts) and src_parts:
        head = gls_parts[:len(src_parts) - 1]
        tail = "-".join(part for part, _boundary in gls_parts[len(src_parts) - 1:] if part)
        gls_parts = head + [(tail, src_parts[-1][1])]
    rows: list[dict[str, Any]] = []
    for idx, (src_form, boundary) in enumerate(src_parts, start=1):
        gls_form = gls_parts[idx - 1][0] if idx - 1 < len(gls_parts) else ""
        if not src_form:
            return []
        mid = f"{word['word_id']}_M{idx:02d}"
        rows.append({
            "morpheme_id": mid,
            "word_id": word["word_id"],
            "unit_id": word["unit_id"],
            "morpheme_order": idx,
            "source_word_raw": word["source_token_raw"],
            "gloss_word_raw": word["gloss_token_raw"],
            "source_morpheme_raw": src_form,
            "source_morpheme_clean": src_form,
            "gloss_morpheme_raw": gls_form,
            "gloss_morpheme_clean": gls_form,
            "gloss_morpheme_absent": not bool(gls_form),
            "boundary_type": boundary,
            "is_prefix": boundary == "prefix",
            "is_suffix": boundary == "suffix",
            "is_infix": boundary == "infix",
            "is_clitic": boundary == "clitic",
            "source_span": "",
            "gloss_span": "",
            "alignment_method": (
                "segmentation_marker_parse"
                if segmented
                else "source_monomorphemic_analysis"
            ),
            "alignment_confidence": "high",
            "warnings": "",
        })
    return rows


def split_morphemes(token: str, *, is_source: bool) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    chunks = split_top_level_markers(token)
    current_boundary = "root"
    for chunk in chunks:
        if chunk == "-":
            current_boundary = "suffix" if parts else "prefix"
            continue
        if chunk == "=":
            current_boundary = "clitic"
            continue
        if not chunk:
            continue
        m = re.search(r"<([^>]+)>", chunk)
        if m:
            before = chunk[:m.start()]
            infixes = m.group(1).split("-")
            after = chunk[m.end():]
            if not is_source:
                if before:
                    parts.append((before, current_boundary))
                parts.extend((f"<{infix}>", "infix") for infix in infixes)
                if after:
                    parts.append((after, "suffix"))
                current_boundary = "suffix"
                continue
            surround = f"{before}-{after}" if is_source else f"{before}{after}"
            if surround:
                if current_boundary == "clitic" and is_source:
                    surround = f"={surround}"
                parts.append((surround, current_boundary))
            parts.extend((f"-{infix}-", "infix") for infix in infixes)
        else:
            form = f"={chunk}" if current_boundary == "clitic" and is_source else chunk
            parts.append((form, current_boundary))
        current_boundary = "suffix"
    return parts


def split_top_level_markers(token: str) -> list[str]:
    chunks: list[str] = []
    buf: list[str] = []
    depth = 0
    for ch in token:
        if ch == "<":
            depth += 1
            buf.append(ch)
            continue
        if ch == ">":
            depth = max(0, depth - 1)
            buf.append(ch)
            continue
        if ch in "-=" and depth == 0:
            if buf:
                chunks.append("".join(buf))
                buf = []
            chunks.append(ch)
            continue
        buf.append(ch)
    if buf:
        chunks.append("".join(buf))
    return chunks


def extract_footnotes() -> list[dict[str, Any]]:
    lines_by_page = load_lines_by_page()
    texts = segment_texts()
    text_by_page = text_for_printed_lookup(texts)
    rows: list[dict[str, Any]] = []
    for phys, lines in lines_by_page.items():
        current: dict[str, Any] | None = None
        for ln in lines:
            if ln.y0 < 585 or ln.y0 > 660:
                continue
            m = re.match(r"^(\d{1,3})\s+(.*)$", ln.text.strip())
            if m:
                if current:
                    rows.append(current)
                printed = ln.printed_page
                t = text_by_page.get(printed or -1, {})
                current = {
                    "footnote_id": f"FN_p{phys:04d}_{m.group(1)}",
                    "footnote_number": m.group(1),
                    "physical_page": phys,
                    "printed_page": printed,
                    "text_id": t.get("text_id", ""),
                    "unit_id_if_applicable": "",
                    "anchor_text": "",
                    "footnote_raw": m.group(2),
                    "footnote_clean": xml_clean_text(m.group(2)),
                    "footnote_type": classify_footnote(m.group(2)),
                    "action": "preserve_sidecar_only",
                    "parse_confidence": "medium",
                    "warnings": "",
                }
            elif current:
                current["footnote_raw"] += " " + ln.text.strip()
                current["footnote_clean"] = xml_clean_text(current["footnote_raw"])
        if current:
            rows.append(current)
    write_jsonl(ROOT / "data/processed/footnotes.jsonl", rows)
    return rows


def classify_footnote(text: str) -> str:
    low = text.lower()
    if "loanword" in low:
        return "loanword_note"
    if "field notebook" in low:
        return "field_notebook_reference"
    if "japanese translation" in low:
        return "Japanese_translation_reference"
    if "form" in low or "variation" in low:
        return "form_explanation"
    if "recorded" in low or "informant" in low or "age" in low:
        return "source_collection_note"
    return "unknown"


def text_for_printed_lookup(texts: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    lookup: dict[int, dict[str, Any]] = {}
    for t in texts:
        for p in range(t["printed_page_start"], t["printed_page_end"] + 1):
            lookup[p] = t
    return lookup


def extract_style_spans() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    texts = segment_texts()
    text_by_page = text_for_printed_lookup(texts)
    for path in sorted((ROOT / "data/raw/spans/pages").glob("page_*.spans.jsonl")):
        for span in read_jsonl(path):
            if not (span.get("is_bold") or span.get("is_italic")):
                continue
            printed = span.get("printed_page_number")
            t = text_by_page.get(printed or -1, {})
            rows.append({
                "style_span_id": f"STYLE_{len(rows)+1:05d}",
                "text_id": t.get("text_id", ""),
                "unit_id": "",
                "tier": "unknown",
                "raw_text": span.get("text", ""),
                "physical_page": span.get("physical_page_number"),
                "printed_page": printed,
                "x0": span.get("x0"),
                "y0": span.get("y0"),
                "x1": span.get("x1"),
                "y1": span.get("y1"),
                "font": span.get("font_name"),
                "is_bold": span.get("is_bold"),
                "is_italic": span.get("is_italic"),
                "likely_meaning": "bold_editorial_or_discussion_marker" if span.get("is_bold") else "italic_source_style",
                "warnings": "",
            })
    write_jsonl(ROOT / "data/processed/style_spans.jsonl", rows)
    return rows


def filter_units() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    units = read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
    rows: list[dict[str, Any]] = []
    review: list[dict[str, Any]] = []
    for unit in units:
        eligible = unit_in_final_xml(unit) and unit.get("unit_confidence") in {"high", "medium"}
        rows.append({
            **unit,
            "included_in_xml": eligible,
            "quality_filter_reason": "" if eligible else "not_xml_eligible",
        })
        if not eligible or unit.get("warnings") or unit.get("footnote_refs") or unit.get("translation_confidence") == "source_absent":
            empty_extraction_artifact = not (
                unit.get("source_line_raw") or unit.get("gloss_line_raw") or unit.get("free_translation_raw")
            )
            review.append({
                "issue_id": f"MR_{len(review)+1:05d}",
                "severity": "medium" if eligible or empty_extraction_artifact else "high",
                "text_id": unit["text_id"],
                "unit_id": unit["unit_id"],
                "physical_page": unit["physical_page_start"],
                "printed_page": unit["printed_page_start"],
                "source_sentence_label": unit["source_sentence_label"],
                "issue_type": "quality_filter_or_warning",
                "source_raw": unit["source_line_raw"],
                "gloss_raw": unit["gloss_line_raw"],
                "translation_raw": unit["free_translation_raw"],
                "suspected_parse": (
                    unit.get("warnings", "")
                    or ("source_published_free_translation_absent" if unit.get("translation_confidence") == "source_absent" else "")
                    or ("empty_marker_extraction_artifact" if empty_extraction_artifact else "")
                ),
                "recommended_action": "review against rendered source page",
                "page_crop_path": "",
                "status": "needs_review",
                "resolution": (
                    "included_without_s_level_translation_source_has_no_free_translation_line"
                    if unit.get("translation_confidence") == "source_absent"
                    else (
                        "excluded_empty_marker_extraction_artifact"
                        if empty_extraction_artifact
                        else ("included_with_documented_warning" if eligible else "")
                    )
                ),
                "notes": unit.get("unit_confidence", ""),
            })
    write_jsonl(ROOT / "data/processed/quality_filtered_units.jsonl", rows)
    write_csv(ROOT / "data/processed/manual_review_queue.csv", review, [
        "issue_id", "severity", "text_id", "unit_id", "physical_page", "printed_page",
        "source_sentence_label", "issue_type", "source_raw", "gloss_raw", "translation_raw",
        "suspected_parse", "recommended_action", "page_crop_path", "status", "resolution", "notes",
    ])
    return rows, review


def dedupe_units() -> list[dict[str, Any]]:
    units = read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
    seen_pair: dict[str, str] = {}
    rows: list[dict[str, Any]] = []
    for unit in units:
        src = clean_space(unit.get("source_line_clean", ""))
        tr = clean_space(unit.get("free_translation_clean", ""))
        pair_hash = hashlib.sha256(f"{src}\n{tr}".encode("utf-8")).hexdigest()
        classification = "distinct"
        other = ""
        if pair_hash in seen_pair:
            classification = "exact_source_and_translation_duplicate"
            other = seen_pair[pair_hash]
        else:
            seen_pair[pair_hash] = unit["unit_id"]
        rows.append({
            "unit_id": unit["unit_id"],
            "text_id": unit["text_id"],
            "raw_unit_hash": hashlib.sha256(json.dumps(unit, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest(),
            "clean_kanakanavu_hash": hashlib.sha256(src.encode("utf-8")).hexdigest(),
            "clean_english_translation_hash": hashlib.sha256(tr.encode("utf-8")).hexdigest(),
            "source_translation_pair_hash": pair_hash,
            "normalized_whitespace_pair_hash": pair_hash,
            "same_text_and_sentence_label": "",
            "duplicate_of": other,
            "classification": classification,
            "final_action": "retain" if classification == "distinct" else "review",
            "notes": "",
        })
    write_csv(ROOT / "data/processed/duplicates.csv", rows, [
        "unit_id", "text_id", "raw_unit_hash", "clean_kanakanavu_hash",
        "clean_english_translation_hash", "source_translation_pair_hash",
        "normalized_whitespace_pair_hash", "same_text_and_sentence_label",
        "duplicate_of", "classification", "final_action", "notes",
    ])
    return rows


def add_translation(
    parent: etree._Element,
    text: str,
    *,
    kind_of: str | None = None,
) -> etree._Element | None:
    if not text:
        return None
    attributes = {XML_LANG: "eng"}
    if kind_of is not None:
        attributes["kindOf"] = kind_of
    transl = etree.SubElement(parent, "TRANSL", attributes)
    transl.text = text
    return transl


def unit_in_final_xml(unit: dict[str, Any]) -> bool:
    return unit.get("quality_status") in {"xml_eligible", "xml_eligible_source_only"}


def replace_exact(
    text: str,
    replacements: tuple[tuple[str, str], ...],
    *,
    context: str,
) -> str:
    for old, new in replacements:
        count = text.count(old)
        if count != 1:
            raise RuntimeError(
                f"{context}: expected exactly one {old!r}, found {count} in {text!r}"
            )
        text = text.replace(old, new, 1)
    return clean_space(text)


def synthetic_word_and_morph_rows(
    unit: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_tokens = unit.get("word_source_line", unit["source_line_clean"]).split()
    gloss_tokens = unit["gloss_line_clean"].split()
    if len(source_tokens) != len(gloss_tokens):
        raise RuntimeError(
            f"{unit['unit_id']}: admitted variant has {len(source_tokens)} source "
            f"tokens but {len(gloss_tokens)} gloss tokens\n"
            f"source={unit['source_line_clean']!r}\n"
            f"gloss={unit['gloss_line_clean']!r}"
        )
    words: list[dict[str, Any]] = []
    morphs: list[dict[str, Any]] = []
    for order, (source_raw, gloss_raw) in enumerate(
        zip(source_tokens, gloss_tokens), start=1
    ):
        _, source, outer_right = strip_outer_punct(source_raw)
        _, gloss, _ = strip_outer_punct(gloss_raw)
        if not source or re.search(r"[()\[\]*/]", source):
            raise RuntimeError(
                f"{unit['unit_id']}: unresolved source notation in admitted "
                f"synthetic W token {source_raw!r}"
            )
        word_id = f"{unit['unit_id']}_W{order:03d}"
        row = {
            "word_id": word_id,
            "unit_id": unit["unit_id"],
            "word_order": order,
            "source_token_raw": source_raw,
            "source_token_clean": source,
            "gloss_token_raw": gloss_raw,
            "gloss_token_clean": gloss,
            "gloss_token_absent": not bool(gloss),
            "source_bbox": "",
            "gloss_bbox": "",
            "source_page": unit["physical_page_start"],
            "gloss_page": unit["physical_page_start"],
            "alignment_method": "reviewed_parenthetical_variant",
            "alignment_score": 1.0,
            "alignment_confidence": "high",
            "segmentation_markers": "".join(ch for ch in source if ch in "-=<>"),
            "outer_punctuation": outer_right,
            "footnote_refs": unit.get("footnote_refs", []),
            "warnings": "",
        }
        word_morphs = parse_morphemes_for_word(row)
        if not word_morphs:
            raise RuntimeError(f"{unit['unit_id']}: no M rows for {source!r}")
        words.append(row)
        morphs.extend(word_morphs)
    return words, morphs


def merge_form_readings(
    units: list[dict], words: list[dict], morphs: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """Keep reviewed pronunciation readings on their aligned W/M nodes."""
    if len(units) != 2:
        raise RuntimeError("A reviewed FORM pair must have exactly two readings")
    base, alternate = units
    if base["free_translation_clean"] != alternate["free_translation_clean"]:
        raise RuntimeError(f"{base['source_unit_id']}: FORM readings have different translations")
    merged_rows = []
    for rows, form_key, gloss_key in (
        (words, "source_token_clean", "gloss_token_clean"),
        (morphs, "source_morpheme_clean", "gloss_morpheme_clean"),
    ):
        primary = [row for row in rows if row["unit_id"] == base["unit_id"]]
        secondary = [row for row in rows if row["unit_id"] == alternate["unit_id"]]
        if len(primary) != len(secondary):
            raise RuntimeError(f"{base['source_unit_id']}: FORM readings change tier inventory")
        for first, second in zip(primary, secondary):
            first_word = first["word_id"].removeprefix(base["unit_id"])
            second_word = second["word_id"].removeprefix(alternate["unit_id"])
            if (
                first_word != second_word
                or first.get("morpheme_order") != second.get("morpheme_order")
                or first[gloss_key] != second[gloss_key]
            ):
                raise RuntimeError(f"{base['source_unit_id']}: FORM readings change gloss alignment")
            if first[form_key] != second[form_key]:
                first["form_alternatives"] = [second[form_key]]
        merged_rows.append(primary)
    base["alternative_source_lines"] = [alternate["source_line_clean"]]
    base["variant_count"] = 1
    return [base], merged_rows[0], merged_rows[1]


def reading_suffix(order: int) -> str:
    return "" if order == 1 else "-opt" if order == 2 else f"-opt{order}"


def expand_xml_units() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    source_units = [
        unit
        for unit in read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
        if unit_in_final_xml(unit)
    ]
    source_words = read_jsonl(ROOT / "data/processed/word_units.jsonl")
    source_morphs = read_jsonl(ROOT / "data/processed/morpheme_units.jsonl")
    words_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    morphs_by_word: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for word in source_words:
        words_by_unit[word["unit_id"]].append(word)
    for morph in source_morphs:
        morphs_by_word[morph["word_id"]].append(morph)

    xml_units: list[dict[str, Any]] = []
    xml_words: list[dict[str, Any]] = []
    xml_morphs: list[dict[str, Any]] = []
    for source_unit in source_units:
        source_unit_id = source_unit["unit_id"]
        unit_start, word_start, morph_start = len(xml_units), len(xml_words), len(xml_morphs)
        options = PARENTHETICAL_VARIANTS.get(source_unit_id, (
            {"label": "source", "source": (), "gloss": ()},
        ))
        for variant_order, option in enumerate(options, start=1):
            unit = dict(source_unit)
            unit["source_unit_id"] = source_unit_id
            unit["variant_label"] = option["label"]
            unit["variant_order"] = variant_order
            unit["variant_count"] = len(options)
            unit["unit_id"] = source_unit_id + reading_suffix(variant_order)
            transformed_source = replace_exact(
                source_unit["source_line_clean"],
                option["source"],
                context=f"{source_unit_id} {option['label']} source",
            )
            unit["source_line_clean"] = sentence_original_form(transformed_source)
            gloss_replacements = (
                tuple(option["gloss"])
                + RESOLVED_JUDGMENT_GLOSS_REPLACEMENTS.get(source_unit_id, ())
            )
            unit["gloss_line_clean"] = replace_exact(
                source_unit["gloss_line_clean"],
                gloss_replacements,
                context=f"{source_unit_id} {option['label']} gloss",
            )
            word_source_line = unit["source_line_clean"]
            if source_unit_id in CLAUSE_BRACKET_UNITS:
                if word_source_line.count("[") != 1 or word_source_line.count("]") != 1:
                    raise RuntimeError(f"{source_unit_id}: reviewed clause brackets changed")
                word_source_line = word_source_line.replace("[", "").replace("]", "")
                unit["word_source_line"] = word_source_line
                unit["warnings"] = "; ".join(
                    warning for warning in unit["warnings"].split("; ")
                    if warning != "wm_omitted_source_analysis_notation"
                )
            unresolved_analysis = bool(re.search(r"[()\[\]*/]", word_source_line))
            unit["word_tier_candidate"] = not unresolved_analysis
            unit["morpheme_tier_candidate"] = not unresolved_analysis
            xml_units.append(unit)

            if (len(options) > 1 or source_unit_id in RESOLVED_JUDGMENT_GLOSS_REPLACEMENTS
                    or source_unit_id in CLAUSE_BRACKET_UNITS):
                if unresolved_analysis:
                    continue
                variant_words, variant_morphs = synthetic_word_and_morph_rows(unit)
                xml_words.extend(variant_words)
                xml_morphs.extend(variant_morphs)
                continue

            for source_word in words_by_unit.get(source_unit_id, []):
                word = dict(source_word)
                xml_words.append(word)
                xml_morphs.extend(
                    dict(morph)
                    for morph in morphs_by_word.get(source_word["word_id"], [])
                )

        if source_unit_id in FORM_VARIANT_UNITS:
            merged = merge_form_readings(
                xml_units[unit_start:], xml_words[word_start:], xml_morphs[morph_start:]
            )
            xml_units[unit_start:], xml_words[word_start:], xml_morphs[morph_start:] = merged

    if len(source_units) != EXPECTED_SOURCE_UNIT_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_SOURCE_UNIT_COUNT} source units, found {len(source_units)}"
        )
    if len(xml_units) != EXPECTED_SENTENCE_COUNT:
        raise RuntimeError(
            f"expected {EXPECTED_SENTENCE_COUNT} XML manifestations, found {len(xml_units)}"
        )
    write_jsonl(ROOT / "data/processed/xml_sentence_units.jsonl", xml_units)
    write_jsonl(ROOT / "data/processed/xml_word_units.jsonl", xml_words)
    write_jsonl(ROOT / "data/processed/xml_morpheme_units.jsonl", xml_morphs)
    return xml_units, xml_words, xml_morphs


def build_xml() -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    texts = segment_texts()
    units, words, morphs = expand_xml_units()
    words_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    morphs_by_word: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for w in words:
        words_by_unit[w["unit_id"]].append(w)
    for m in morphs:
        morphs_by_word[m["word_id"]].append(m)
    units_by_text: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for unit in units:
        units_by_text[unit["text_id"]].append(unit)
    draft_dir = ROOT / "build/xml_drafts/Kanakanavu"
    for path in draft_dir.glob("*.xml"):
        path.unlink()
    xml_index: list[dict[str, Any]] = []
    token_index: list[dict[str, Any]] = []
    paths: list[Path] = []
    for text in texts:
        root = etree.Element("TEXT", nsmap=NSMAP)
        root.set("id", text["text_id"])
        root.set(XML_LANG, "xnb")
        root.set("dialect", "Kanakanavu")
        root.set("citation", apa_citation())
        root.set("BibTeX_citation", bibtex_citation())
        root.set("copyright", copyright_attr())
        root.set("source", source_attr(text))
        for unit in sorted(units_by_text[text["text_id"]], key=lambda u: u["unit_order"]):
            sid_base = f"{text['text_id']}_S{int(unit['unit_order']):04d}"
            sid = sid_base + reading_suffix(int(unit["variant_order"]))
            source_line = unit["source_line_clean"]
            translation, translation_note = sentence_translation_and_note(
                unit["free_translation_clean"]
            )
            s_elem = etree.SubElement(root, "S", id=sid)
            original_form = etree.SubElement(s_elem, "FORM", kindOf="original")
            original_form.text = source_line
            if int(unit["variant_count"]) > 1:
                original_form.set(
                    "notes",
                    "Source parenthetical expanded under POL-026/POL-027; exact source and decision are in source_notation_audit.csv.",
                )
            elif unit["source_unit_id"] in RESOLVED_JUDGMENT_GLOSS_REPLACEMENTS:
                original_form.set(
                    "notes",
                    "Source judgment resolved under POL-016/POL-017; exact source and exclusion are in source_notation_audit.csv.",
                )
            if translation:
                translation_elem = etree.SubElement(
                    s_elem,
                    "TRANSL",
                    {XML_LANG: "eng"},
                )
                translation_elem.text = translation
                if translation_note:
                    translation_elem.set("notes", translation_note)
            include_words = unit.get("word_tier_candidate") and unit["unit_id"] in words_by_unit
            if include_words:
                for w in sorted(words_by_unit[unit["unit_id"]], key=lambda r: r["word_order"]):
                    source_token = clean_source_form(w["source_token_clean"])
                    w_elem = etree.SubElement(s_elem, "W", id=w["word_id"].replace(unit["unit_id"], sid))
                    etree.SubElement(w_elem, "FORM", kindOf="original").text = source_token
                    for alternative in w.get("form_alternatives", []):
                        etree.SubElement(w_elem, "FORM", kindOf="original", ver="alt").text = clean_source_form(alternative)
                    add_translation(
                        w_elem,
                        w["gloss_token_clean"],
                        kind_of="original",
                    )
                    token_index.append(token_index_row(text, unit, w, "W", w_elem.get("id"), sid, sid))
                    for m in sorted(morphs_by_word.get(w["word_id"], []), key=lambda r: r["morpheme_order"]):
                        source_morpheme = clean_source_form(m["source_morpheme_clean"])
                        m_elem = etree.SubElement(w_elem, "M", id=m["morpheme_id"].replace(unit["unit_id"], sid))
                        etree.SubElement(m_elem, "FORM", kindOf="original").text = source_morpheme
                        for alternative in m.get("form_alternatives", []):
                            etree.SubElement(m_elem, "FORM", kindOf="original", ver="alt").text = clean_source_form(alternative)
                        add_translation(
                            m_elem,
                            m["gloss_morpheme_clean"],
                            kind_of="original",
                        )
                        token_index.append(token_index_row(text, unit, {**w, **m}, "M", m_elem.get("id"), w_elem.get("id"), sid))
            xml_file = xml_filename(text["global_text_order"], text["title_english_clean"])
            unit_has_morphs = any(morphs_by_word.get(w["word_id"]) for w in words_by_unit.get(unit["unit_id"], []))
            xml_index.append(xml_index_row(text, unit, sid, xml_file, include_words, unit_has_morphs))
        out = draft_dir / xml_filename(text["global_text_order"], text["title_english_clean"])
        etree.ElementTree(root).write(str(out), encoding="UTF-8", xml_declaration=True, pretty_print=True)
        paths.append(out)
    write_csv(ROOT / "data/processed/xml_index.csv", xml_index, [
        "xml_file", "text_id", "sentence_id", "unit_id", "source_unit_id",
        "variant_label", "variant_order", "variant_count", "global_text_order",
        "part_number", "collector", "text_number_within_part", "title_english",
        "title_kanakanavu", "source_sentence_label", "source_sentence_number",
        "physical_page_start", "physical_page_end", "printed_page_start", "printed_page_end",
        "source_line_ids", "gloss_line_ids", "translation_line_ids", "source_pdf_path",
        "source_pdf_sha256", "source_text_sha256", "gloss_text_sha256",
        "translation_text_sha256", "translation_note", "pair_sha256",
        "source_confidence", "gloss_confidence",
        "translation_confidence", "unit_confidence", "word_tier_included",
        "morpheme_tier_included", "footnote_refs", "overlap_status", "quality_status", "warnings",
    ])
    write_csv(ROOT / "data/processed/xml_token_index.csv", token_index, [
        "xml_file", "sentence_id", "element_type", "element_id", "parent_id",
        "word_id", "morpheme_id", "source_token_raw", "source_token_clean",
        "gloss_token_raw", "gloss_token_clean", "physical_page", "printed_page",
        "source_bbox", "gloss_bbox", "alignment_confidence", "warnings",
    ])
    return paths, xml_index, token_index


def apa_citation() -> str:
    return "Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. (2026). Kanakanavu texts (P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies."


def bibtex_citation() -> str:
    return "@book{AsaiMeiLiTsuchida2026KanakanavuTexts,author={Erin Asai and Kuang Mei and Paul Jen-kuei Li and Shigeru Tsuchida},editor={Paul Jen-kuei Li},title={Kanakanavu Texts},year={2026},publisher={Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies},isbn={978-4-86337-602-1},note={With the assistance of Yi-Chun Chen, Hsiu-min Huang, and Amy Ming-luan Chen. Licensed under CC BY 4.0}}"


def copyright_attr() -> str:
    return "CC BY 4.0"


def source_attr(text: dict[str, Any]) -> str:
    if text.get("text_kind") == "grammar_examples":
        return (
            "Kanakanavu Texts (2026), grammatical introduction examples "
            f"(examples 1-40), printed pages {text['printed_page_start']}-"
            f"{text['printed_page_end']}, source PDF {PDF_NAME}"
        )
    return (
        f"Kanakanavu Texts (2026), Part {text['part_number']}, "
        f"Text {text['text_number_within_part']}, {text['collector']}, "
        f"printed pages {text['printed_page_start']}-{text['printed_page_end']}, "
        f"source PDF {PDF_NAME}"
    )


def xml_index_row(text: dict[str, Any], unit: dict[str, Any], sid: str, xml_file: str, include_words: bool, include_morphs: bool) -> dict[str, Any]:
    src = sentence_original_form(unit["source_line_clean"])
    gls = unit["gloss_line_clean"]
    tr, translation_note = sentence_translation_and_note(
        unit["free_translation_clean"]
    )
    return {
        "xml_file": xml_file,
        "text_id": text["text_id"],
        "sentence_id": sid,
        "unit_id": unit["unit_id"],
        "source_unit_id": unit["source_unit_id"],
        "variant_label": unit["variant_label"],
        "variant_order": unit["variant_order"],
        "variant_count": unit["variant_count"],
        "global_text_order": text["global_text_order"],
        "part_number": text["part_number"],
        "collector": text["collector"],
        "text_number_within_part": text["text_number_within_part"],
        "title_english": text["title_english_clean"],
        "title_kanakanavu": text["title_kanakanavu_clean"],
        "source_sentence_label": unit["source_sentence_label"],
        "source_sentence_number": unit["source_sentence_number"],
        "physical_page_start": unit["physical_page_start"],
        "physical_page_end": unit["physical_page_end"],
        "printed_page_start": unit["printed_page_start"],
        "printed_page_end": unit["printed_page_end"],
        "source_line_ids": unit["source_line_ids"],
        "gloss_line_ids": unit["gloss_line_ids"],
        "translation_line_ids": unit["translation_line_ids"],
        "source_pdf_path": f"data/raw/pdf/{PDF_NAME}",
        "source_pdf_sha256": EXPECTED_SHA256,
        "source_text_sha256": hashlib.sha256(src.encode("utf-8")).hexdigest(),
        "gloss_text_sha256": hashlib.sha256(gls.encode("utf-8")).hexdigest(),
        "translation_text_sha256": hashlib.sha256(tr.encode("utf-8")).hexdigest(),
        "translation_note": translation_note,
        "pair_sha256": hashlib.sha256(f"{src}\n{tr}".encode("utf-8")).hexdigest(),
        "source_confidence": unit["source_confidence"],
        "gloss_confidence": unit["gloss_confidence"],
        "translation_confidence": unit["translation_confidence"],
        "unit_confidence": unit["unit_confidence"],
        "word_tier_included": include_words,
        "morpheme_tier_included": include_morphs,
        "footnote_refs": unit["footnote_refs"],
        "overlap_status": "",
        "quality_status": unit["quality_status"],
        "warnings": unit["warnings"],
    }


def token_index_row(text: dict[str, Any], unit: dict[str, Any], row: dict[str, Any], element_type: str, element_id: str | None, parent_id: str | None, sentence_id: str) -> dict[str, Any]:
    source_clean = clean_source_form(row.get("source_token_clean") or row.get("source_morpheme_clean", ""))
    return {
        "xml_file": xml_filename(text["global_text_order"], text["title_english_clean"]),
        "sentence_id": sentence_id,
        "element_type": element_type,
        "element_id": element_id or "",
        "parent_id": parent_id or "",
        "word_id": row.get("word_id", ""),
        "morpheme_id": row.get("morpheme_id", ""),
        "source_token_raw": row.get("source_token_raw") or row.get("source_morpheme_raw", ""),
        "source_token_clean": source_clean,
        "gloss_token_raw": row.get("gloss_token_raw") or row.get("gloss_morpheme_raw", ""),
        "gloss_token_clean": row.get("gloss_token_clean") or row.get("gloss_morpheme_clean", ""),
        "physical_page": row.get("source_page", ""),
        "printed_page": unit.get("printed_page_start", ""),
        "source_bbox": row.get("source_bbox", ""),
        "gloss_bbox": row.get("gloss_bbox", ""),
        "alignment_confidence": row.get("alignment_confidence", ""),
        "warnings": row.get("warnings", ""),
    }


def write_source_unit_coverage(units: list[dict[str, Any]]) -> None:
    xml_units_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for xml_unit in read_jsonl(ROOT / "data/processed/xml_sentence_units.jsonl"):
        xml_units_by_source[xml_unit["source_unit_id"]].append(xml_unit)
    rows = []
    for unit in units:
        exact_source = unit["source_line_clean"]
        manifestations = xml_units_by_source[unit["unit_id"]]
        xml_translation, translation_note = sentence_translation_and_note(
            unit["free_translation_clean"]
        )
        rows.append({
            "unit_id": unit["unit_id"],
            "text_id": unit["text_id"],
            "source_sentence_label": unit["source_sentence_label"],
            "physical_pages": f"{unit['physical_page_start']}-{unit['physical_page_end']}",
            "printed_pages": f"{unit['printed_page_start']}-{unit['printed_page_end']}",
            "source_line_ids": unit["source_line_ids"],
            "gloss_line_ids": unit["gloss_line_ids"],
            "translation_line_ids": unit["translation_line_ids"],
            "exact_source_form": exact_source,
            "xml_original_form": " || ".join(
                manifestation["source_line_clean"] for manifestation in manifestations
            ),
            "standardization_action": "not_run_by_source_parser",
            "source_gloss": unit["gloss_line_clean"],
            "source_translation": unit["free_translation_clean"],
            "xml_translation": xml_translation,
            "translation_note": translation_note,
            "footnote_refs": unit["footnote_refs"],
            "xml_action": "included",
            "translation_action": (
                "included_translation_with_source_editorial_note_attribute"
                if translation_note
                else "included_exact_source_translation"
            ),
            "word_morpheme_action": (
                "clause_brackets_at_s_aligned_w_m"
                if unit["unit_id"] in CLAUSE_BRACKET_UNITS
                else "same_tier_form_variants"
                if unit["unit_id"] in FORM_VARIANT_UNITS
                else "expanded_variants_with_aligned_w_m"
                if unit["unit_id"] in PARENTHETICAL_VARIANTS
                else (
                    "omitted_source_square_bracket_analysis_notation"
                    if any("[" in item["source_line_clean"] for item in manifestations)
                    else "included"
                )
            ),
            "source_judgment_action": (
                "exact_source_retained_here_and_starred_material_excluded_from_xml"
                if "*" in exact_source
                else "not_applicable"
            ),
            "quality_status": unit["quality_status"],
            "warnings": unit["warnings"],
        })
    write_csv(ROOT / "data/processed/source_unit_coverage.csv", rows, [
        "unit_id", "text_id", "source_sentence_label", "physical_pages",
        "printed_pages", "source_line_ids", "gloss_line_ids",
        "translation_line_ids", "exact_source_form", "xml_original_form",
        "standardization_action", "source_gloss", "source_translation",
        "xml_translation", "translation_note", "footnote_refs", "xml_action",
        "translation_action",
        "word_morpheme_action", "source_judgment_action", "quality_status",
        "warnings",
    ])


def write_source_notation_audit(units: list[dict[str, Any]]) -> None:
    xml_units_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for xml_unit in read_jsonl(ROOT / "data/processed/xml_sentence_units.jsonl"):
        xml_units_by_source[xml_unit["source_unit_id"]].append(xml_unit)
    rows = []
    notation_chars = {
        "square_brackets": "[]",
        "parentheses": "()",
        "slash": "/",
        "asterisk": "*",
    }
    for unit in units:
        source = unit["source_line_clean"]
        types = [
            name for name, chars in notation_chars.items()
            if any(char in source for char in chars)
        ]
        if not types:
            continue
        manifestations = xml_units_by_source[unit["unit_id"]]
        excluded = "none"
        decision = "Preserve square-bracket source analysis notation at S level."
        if source == "naini sua [kaən-a/*kaən-ən=musu]":
            excluded = "starred alternative: kaən-ən=musu"
            decision = (
                "Retain the grammatical kaən-a alternative and exclude the "
                "starred kaən-ən=musu alternative under POL-016/POL-027."
            )
        elif source == "a-pa-kaən-a (*sua) maanu uuru.":
            excluded = "forbidden optional material: sua"
            decision = (
                "Drop forbidden (*sua) under POL-017 and retain the admitted "
                "sentence without sua."
            )
        elif unit["unit_id"] in FORM_VARIANT_UNITS:
            decision = "Keep both source readings on aligned original W/M FORM nodes (POL-028); see CodeAndDocs/notation_decisions.tsv."
        elif unit["unit_id"] in PARENTHETICAL_VARIANTS:
            decision = (
                "Keep the two aligned source readings in base/-opt S blocks. "
                "Unresolved source classifications are listed in CodeAndDocs/source-decisions.md."
            )
        if unit["unit_id"] in CLAUSE_BRACKET_UNITS:
            decision += " Preserve clause brackets at S and recover the aligned source W/M tiers without bracket punctuation."
        rows.append({
            "unit_id": unit["unit_id"],
            "physical_page": unit["physical_page_start"],
            "source_sentence_label": unit["source_sentence_label"],
            "notation_types": types,
            "exact_source_form": source,
            "xml_original_form": " || ".join(
                manifestation["source_line_clean"] for manifestation in manifestations
            ),
            "created_variants": "FORM: " + " || ".join(
                manifestations[0].get("alternative_source_lines", [])
            ) if unit["unit_id"] in FORM_VARIANT_UNITS else " || ".join(
                f"{manifestation['unit_id']}:{manifestation['variant_label']}"
                for manifestation in manifestations
            ) if len(manifestations) > 1 else "none",
            "excluded_sentences": excluded,
            "translation_action": "retained_exact_source_translation",
            "audio_action": "not_applicable_no_source_audio",
            "word_morpheme_action": (
                "clause_brackets_at_s_aligned_w_m"
                if unit["unit_id"] in CLAUSE_BRACKET_UNITS
                else "same_tier_form_variants"
                if unit["unit_id"] in FORM_VARIANT_UNITS
                else "expanded_variants_with_aligned_w_m"
                if len(manifestations) > 1
                else (
                    "omitted_to_avoid_destructive_square_bracket_cleanup"
                    if "[" in manifestations[0]["source_line_clean"]
                    else "included_after_source_judgment_resolution"
                )
            ),
            "decision": decision,
        })
    write_csv(ROOT / "data/processed/source_notation_audit.csv", rows, [
        "unit_id", "physical_page", "source_sentence_label", "notation_types",
        "exact_source_form", "xml_original_form", "created_variants",
        "excluded_sentences", "translation_action", "audio_action",
        "word_morpheme_action", "decision",
    ])


def main() -> int:
    global ROOT
    parser = argparse.ArgumentParser(description="Extract the committed source into isolated working files; no final QC verdict.")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--render", action="store_true", help="Also render source pages for manual review")
    args = parser.parse_args()
    ROOT = args.workspace.resolve()
    source_pdf()
    extract_all_pages(render=args.render)
    parse_toc()
    segment_texts()
    units, _, _, _ = parse_sentence_units()
    extract_footnotes()
    extract_style_spans()
    filter_units()
    dedupe_units()
    paths, _, _ = build_xml()
    write_source_unit_coverage(units)
    write_source_notation_audit(units)
    print(f"Extracted {len(units)} source units into {len(paths)} source-only XML files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
