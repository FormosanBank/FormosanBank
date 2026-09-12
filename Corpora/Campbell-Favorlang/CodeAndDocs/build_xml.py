#!/usr/bin/env python3
"""Build logically segmented FormosanBank XML from Campbell 1896.

The Internet Archive DjVu XML supplies word coordinates. Campbell's layout has
parallel Dutch/Favorlang columns and same-page English translations, followed
by five source-only, two-column sermons. This builder follows the printed
section and item boundaries instead of treating physical pages as sentences.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace
from functools import cache
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_XML = (
    ROOT
    / "Private/source/archive-org/"
    "campbell_1896_articles_favorlang_formosan_djvu.xml"
)
XML_PATH = (
    ROOT
    / "XML/Babuza-Favorlang/"
    "campbell_1896_favorlang_christian_instruction.xml"
)
ACCEPTED_TSV = ROOT / "CodeAndDocs/extracted_records.tsv"
REJECTED_TSV = ROOT / "CodeAndDocs/rejected_sections.tsv"
SOURCE_CORRECTIONS_TSV = ROOT / "CodeAndDocs/source_corrections.tsv"
REVIEWER_CORRECTIONS_TSV = ROOT / "CodeAndDocs/reviewer_corrections.tsv"
SERMON_REVIEW_TSV = ROOT / "CodeAndDocs/sermon_review.tsv"
RECORD_SPLITS_TSV = ROOT / "CodeAndDocs/record_splits.tsv"
DIPLOMATIC_DIACRITICS_TSV = ROOT / "CodeAndDocs/diplomatic_diacritics.tsv"
SUMMARY_MD = ROOT / "CodeAndDocs/extraction_summary.md"
STANDARD_JOIN_TOKENS = ROOT / "CodeAndDocs/standard_join_tokens.txt"
STANDARD_BOUNDARY_OVERRIDES = (
    ROOT / "CodeAndDocs/standard_boundary_overrides.tsv"
)
TOKEN_RE = re.compile(r"[^\W_]+(?:[-'][^\W_]+)*", re.UNICODE)
DASH_TRANSLATION = str.maketrans({char: "-" for char in "‐‑‒–—―−﹘﹣－"})

TEXT_ID = "campbell_1896_favorlang_christian_instruction"
SOURCE_DESC = (
    "Basecamp card 8307423372; Internet Archive item cu31924026424675; "
    "Campbell 1896 Favorlang-Formosan Christian Instruction"
)
COPYRIGHT = "public domain"
CITATION = (
    "Campbell, W. (ed.). (1896). The Articles of Christian Instruction in "
    "Favorlang-Formosan. London: Kegan Paul, Trench, Trubner & Co."
)
BIBTEX = (
    "@book{campbell1896FavorlangChristianInstruction,"
    "editor={Campbell, W.},"
    "title={The Articles of Christian Instruction in Favorlang-Formosan},"
    "publisher={Kegan Paul, Trench, Trubner & Co.},"
    "address={London},"
    "year={1896}}"
)
EXPECTED_STANDARD_CHANGES = 244
EXPECTED_REVIEWER_CORRECTIONS = Counter(
    {"original": 170, "standard": 169, "translation": 20}
)
EXPECTED_REVIEW_SOURCE_SHA256 = (
    "01e284bb3d696b53798c473f981787db2d70ceb1b901db68f3a6a80ab6214098"
)
EXPECTED_SERMON_REVIEW_SOURCE_SHA256 = (
    "a8447242a20117486a0c7406a1184cc81c1991570ab39779659097ce2ced7196"
)
EXPECTED_FINAL_PART_COUNTS = Counter(
    {
        "primary_section": 8,
        "section_title": 14,
        "section_preamble": 1,
        "numbered_item": 160,
        "dialogue_turn": 160,
        "qa_turn": 22,
        "sermon_sentence": 687,
    }
)
EXPECTED_REVIEWED_FINAL_PART_COUNTS = EXPECTED_FINAL_PART_COUNTS.copy()
EXPECTED_REVIEWED_FINAL_PART_COUNTS["sermon_sentence"] = 684
EXPECTED_SERMON_SENTENCES = {
    "section_15_first_sermon": 133,
    "section_16_second_sermon": 211,
    "section_17_third_sermon": 129,
    "section_18_fourth_sermon": 145,
    "section_19_fifth_sermon": 69,
}

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


@cache
def load_standard_surface_review() -> tuple[frozenset[str], dict[str, str]]:
    """Load the exhaustive reviewed inventory of source hyphen tokens."""
    join_tokens = frozenset(
        line
        for line in STANDARD_JOIN_TOKENS.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith("#")
    )
    with STANDARD_BOUNDARY_OVERRIDES.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    overrides = {
        row["source_token"]: row["standard_surface"] for row in rows
    }
    if len(overrides) != len(rows):
        raise ValueError("Duplicate standard boundary override token")
    overlap = join_tokens.intersection(overrides)
    if overlap:
        raise ValueError(f"Standard review tokens have two decisions: {overlap}")
    if any("-" not in token for token in join_tokens | overrides.keys()):
        raise ValueError("Every standard review token must contain a hyphen")
    return join_tokens, overrides


def standard_surface(text: str) -> str:
    """Apply the exact, source-reviewed surface decision for every hyphen token."""
    join_tokens, overrides = load_standard_surface_review()
    phrase_overrides = {
        source: surface
        for source, surface in overrides.items()
        if TOKEN_RE.fullmatch(source) is None
    }
    token_overrides = {
        source: surface
        for source, surface in overrides.items()
        if TOKEN_RE.fullmatch(source) is not None
    }
    for source in sorted(phrase_overrides, key=len, reverse=True):
        text = text.replace(source, phrase_overrides[source])

    def transform(match: re.Match[str]) -> str:
        token = match.group(0)
        if "-" not in token:
            return token
        if token in token_overrides:
            return token_overrides[token]
        if token in join_tokens:
            return token.replace("-", "")
        raise ValueError(f"Unreviewed source hyphen token: {token!r}")

    return TOKEN_RE.sub(transform, text)


def canonicalize_dashes(text: str) -> str:
    """Apply FormosanBank's POL-011 dash normalization."""
    return re.sub(r"--+", "-", text.translate(DASH_TRANSLATION))


def canonicalize_policy_text(text: str) -> str:
    return unicodedata.normalize("NFC", canonicalize_dashes(text))

ENGLISH_WORDS = {
    "a",
    "all",
    "and",
    "are",
    "as",
    "be",
    "because",
    "belief",
    "by",
    "christ",
    "christian",
    "commandments",
    "do",
    "earth",
    "father",
    "for",
    "from",
    "god",
    "has",
    "have",
    "he",
    "heaven",
    "his",
    "how",
    "i",
    "in",
    "is",
    "it",
    "jesus",
    "lord",
    "may",
    "not",
    "of",
    "on",
    "our",
    "shall",
    "son",
    "that",
    "the",
    "thee",
    "their",
    "them",
    "this",
    "thou",
    "thy",
    "to",
    "unto",
    "us",
    "was",
    "we",
    "what",
    "when",
    "where",
    "who",
    "will",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class Line:
    y: float
    all_text: str
    left_text: str
    right_text: str


@dataclass(frozen=True)
class LocatedLine:
    printed_page: int
    pdf_object_page: int
    y: float
    text: str


@dataclass(frozen=True)
class SectionSpec:
    number: int
    slug: str
    title: str
    source_start: tuple[int, int]
    source_stop: tuple[int, int]
    translation_start: tuple[int, int] | None
    translation_stop: tuple[int, int] | None
    mode: str
    expected_items: int = 0


@dataclass(frozen=True)
class Record:
    record_id: str
    section: int
    section_title: str
    part: str
    label: str
    printed_page_start: int
    printed_page_end: int
    pdf_object_page_start: int
    pdf_object_page_end: int
    form: str
    translation: str
    notes: str
    standard: str = ""

    @property
    def source_attr(self) -> str:
        page_range = _range_text(
            "printed_page",
            self.printed_page_start,
            self.printed_page_end,
        )
        object_range = _range_text(
            "pdf_object_page",
            self.pdf_object_page_start,
            self.pdf_object_page_end,
        )
        parts = [
            page_range,
            object_range,
            f"section_{self.section:02d}",
            self.record_id,
            self.part,
        ]
        if self.label:
            parts.append(f"label_{self.label}")
        return ";".join(parts)


@dataclass(frozen=True)
class SourceCorrection:
    record_id: str
    old: str
    new: str
    reason: str


@dataclass(frozen=True)
class AppliedCorrection:
    record_id: str
    printed_page_start: int
    printed_page_end: int
    old: str
    new: str
    reason: str
    tier: str = "original"


@dataclass(frozen=True)
class DiplomaticCorrection:
    record_id: str
    token_index: int
    old_token: str
    new_token: str
    printed_page: int
    verification: str


@dataclass(frozen=True)
class ReviewerCorrection:
    record_id: str
    tier: str
    old_text: str
    new_text: str
    reviewer: str
    review_date: str
    review_source_sha256: str


@dataclass(frozen=True)
class RecordSplit:
    parent_id: str
    child_id: str
    split_kind: str
    ordinal: int


@dataclass(frozen=True)
class SermonReview:
    decision: str
    reviewed_id: str
    baseline_ids: tuple[str, ...]
    baseline_sha256: str
    form: str
    reason: str
    reviewer: str
    review_date: str
    review_source_sha256: str


# Coordinates are stable locations in the committed IA DjVu XML. Starts point
# to the first source or translation line after the printed section heading.
# Stops point to the next heading or a printed end marker.
SECTIONS = (
    SectionSpec(
        1,
        "lords_prayer",
        "The Prayer of Our Lord Jesus Christ",
        (1, 835),
        (2, 269),
        (1, 1912),
        (2, 1822),
        "single",
    ),
    SectionSpec(
        2,
        "christian_belief",
        "The Christian Belief",
        (2, 400),
        (3, 480),
        (2, 1822),
        (3, 1819),
        "single",
    ),
    SectionSpec(
        3,
        "ten_commandments",
        "The Ten Commandments of the Lord",
        (3, 630),
        (5, 945),
        (3, 1819),
        (5, 1930),
        "numbered_with_preamble",
        10,
    ),
    SectionSpec(
        4,
        "morning_prayer",
        "The Morning Prayer",
        (5, 1050),
        (6, 1700),
        (5, 1930),
        (7, 1792),
        "single",
    ),
    SectionSpec(
        5,
        "evening_prayer",
        "The Evening Prayer",
        (7, 430),
        (8, 1195),
        (7, 1792),
        (8, 1990),
        "single",
    ),
    SectionSpec(
        6,
        "prayer_before_meals",
        "Prayer Before Meals",
        (8, 1290),
        (9, 1194),
        (8, 1990),
        (9, 1985),
        "single",
    ),
    SectionSpec(
        7,
        "prayer_after_meals",
        "Prayer To Be Used After Meals",
        (9, 1310),
        (11, 240),
        (9, 1985),
        (11, 1673),
        "single",
    ),
    SectionSpec(
        8,
        "prayer_before_instruction",
        "Prayer Before Religious Instruction",
        (11, 430),
        (11, 1060),
        (11, 1673),
        (11, 1962),
        "single",
    ),
    SectionSpec(
        9,
        "prayer_after_instruction",
        "Prayer After Religious Instruction",
        (11, 1200),
        (12, 887),
        (11, 1962),
        (12, 1886),
        "single",
    ),
    SectionSpec(
        10,
        "favorlanger_dutchman_dialogue",
        "Dialogue Between a Favorlanger and a Dutch Stranger",
        (12, 1050),
        (32, 1603),
        (12, 1886),
        (33, 1714),
        "numbered",
        80,
    ),
    SectionSpec(
        11,
        "christian_maxims",
        "Christian Maxims",
        (33, 430),
        (38, 886),
        (33, 1714),
        (38, 1929),
        "numbered_first_unmarked",
        20,
    ),
    SectionSpec(
        12,
        "questions_lords_prayer",
        "Questions on the Prayer of the Lord",
        (38, 1260),
        (40, 1532),
        (38, 1929),
        (41, 1680),
        "qa_pairs",
        11,
    ),
    SectionSpec(
        13,
        "questions_christian_belief",
        "Questions on the Christian Belief",
        (41, 520),
        (67, 1475),
        (41, 1680),
        (68, 1683),
        "numbered",
        90,
    ),
    SectionSpec(
        14,
        "baptism_catechism",
        "A Short Catechism Before Receiving Christian Baptism",
        (68, 540),
        (75, 550),
        (68, 1683),
        (75, 800),
        "numbered",
        40,
    ),
    SectionSpec(
        15,
        "first_sermon",
        "First Sermon: Isaiah lvi. 7",
        (75, 1017),
        (79, 338),
        None,
        None,
        "sermon",
    ),
    SectionSpec(
        16,
        "second_sermon",
        "Second Sermon: 1 Timothy ii. 5",
        (79, 410),
        (86, 1292),
        None,
        None,
        "sermon",
    ),
    SectionSpec(
        17,
        "third_sermon",
        "Third Sermon: Hebrews xi. 6",
        (86, 1360),
        (91, 1060),
        None,
        None,
        "sermon",
    ),
    SectionSpec(
        18,
        "fourth_sermon",
        "Fourth Sermon: John xvii. 3",
        (91, 1150),
        (98, 1670),
        None,
        None,
        "sermon",
    ),
    SectionSpec(
        19,
        "fifth_sermon",
        "Fifth Sermon: John xvi. 23",
        (98, 1760),
        (102, 220),
        None,
        None,
        "sermon",
    ),
)

# Printed Favorlang headings aligned to Campbell's English headings. Sections
# XV-XIX have editorial sermon headings but do not consistently provide an
# aligned Favorlang title plus English translation, so they are not promoted to
# title records.
SOURCE_TITLES = {
    1: "Ai-ach'o ma-acháchimit ja Torro ta Jesus Christus.",
    2: "Autat o Christan.",
    3: "Tschiet o Áttillono ta Jehova.",
    4: "Ai-ach'o Patsjisimma.",
    5: "Ai-ach'o Marpesa.",
    6: "Ai-ach'o tinnaam Man.",
    7: "Ai-ach'o a-i-jor a Man.",
    8: "Ai-acha katinnaam Atil.",
    9: "Ai-acha a-i-jor a Atil.",
    10: "Karri-atite tuppach o sjam Ternern, so-o ta Holland-azjies.",
    11: "Atite o Atil o Christan.",
    12: "Chachod o Ai-Ach'o Christan.",
    13: "Chachod o Autat o Christan.",
    14: "Ma-ápapp'a Atil ino Arácho Christan a Sasikir i to.",
}


# These corrections are verified against rendered source pages. Section 1 is
# replaced as a complete short text because it is a compact, independently
# reviewed transcription and supplies exact regression coverage for historical
# diacritics that the IA coordinate OCR omits.
EXACT_FORM_OVERRIDES = {
    "section_01_lords_prayer": (
        "Namoa tamau tamasea paḡa de boesum, ipá-dassa joa naan. "
        "Ipáṣaija joa chachimit o ai. "
        "Ipá-i-jorr'o oa airab maibas de boesum, masini de ta channumma. "
        "Epé-e namono piadai torro uppo ma-atsikap. "
        "Ṣo-o abó-e namo tataap o kakossi namoa, maibas channumma namo "
        "mabo tamasea parapies i namo. "
        "Hai pásabas i namo, ṣo-o barraṣ'i namo innai rapies ai. "
        "Inau joa micho chachimit o ai, ṣo-o barr'o ai, ṣo-o adas ai, "
        "taulaulan, Amen."
    ),
    "section_02_christian_belief": (
        "Ka na-a poetautat inni Deos o Tamau, Airien o boesum, a ta "
        "kamabarr'ija tapos o ai; "
        "Ṣo-o inni ta Jesus Christus choa sjiem nattaṣar o binoḡa "
        "ma-acháchimit ja torro, tamasea karinab innaide Auchar o Deos "
        "o ma-áchimit, ta Spirito Santo, kabinodd'o patómammali ta Maria. "
        "Minachoté o ai de rapo ma-achachált ta Pontius Pilatus, "
        "tsiniltillan i ṣaṣakimotto, minachá, chinap o ta, ṣinoss'i "
        "chauch o chau, michoṣar a pattite, gehenna. "
        "Ka natorroa da zijsja minaṣéas a macha. "
        "Tsinnummaḡach i boesum, airoossen i kallamas o choa Tamau "
        "kamabarr'ija tapos o ai; "
        "Innaide icho ṣaṣai pacheoach, alla mierien o chachalt o cho "
        "morich-a ṣo-o macháda ai. "
        "Kana-a poetautat inni ta Auchar o Deos o ma-áchimit, ta Spirito "
        "Santo. "
        "Na-a pittau o aiḡarrórro-no cho Christan o ma-achímit, o ai "
        "pinaḡa ani-aicho, paḡa pia ṣo-o kapapoetautachṣar. "
        "Rorróno-ad'o chono ma-achimit ai. "
        "Ábono tataap o kakossi ai. "
        "Aṣéas o bo'ai. "
        "Ṣo-o morícho o ma-áchonṣar ai. "
        "Amen."
    ),
}

SOURCE_CORRECTIONS = (
    SourceCorrection(
        "section_03_preamble",
        "'\"pA Deos ma-cho",
        "Ta Deos ma-cho",
        "Printed page 3: ornate initial T is misread as pA.",
    ),
    SourceCorrection(
        "section_03_item_04",
        "o Jehova oa t)eos-ech",
        "o Jehova oa Deos-ech",
        "Printed page 4: ornate initial D is split and misread.",
    ),
    SourceCorrection(
        "section_04_morning_prayer",
        "Mi A-abo a Tamaii",
        "A-abo a Tamau",
        "Printed page 5: ornate opening and Tamau are misread by OCR.",
    ),
    SourceCorrection(
        "section_04_morning_prayer",
        "sasa-6d o tagg'o",
        "ṣaṣa-ód o tagg'o",
        "Printed page 6: OCR loses both underdots and reads ó as 6.",
    ),
    SourceCorrection(
        "section_05_evening_prayer",
        "p Eos o ma-abo",
        "Deos o ma-abo",
        "Printed page 7: ornate initial D is misread as p.",
    ),
    SourceCorrection(
        "section_06_prayer_before_meals",
        "TV fAcha o tapos",
        "Macha o tapos",
        "Printed page 8: ornate initial M is split into OCR noise.",
    ),
    SourceCorrection(
        "section_06_prayer_before_meals",
        "tummassin -A ijo",
        "tummassin ijo",
        "Printed page 8: OCR adds a false hyphen and initial.",
    ),
    SourceCorrection(
        "section_07_prayer_after_meals",
        "XT A ochal",
        "Ka ochal",
        "Printed page 9: ornate initial Ka is OCR noise.",
    ),
    SourceCorrection(
        "section_07_prayer_after_meals",
        "mamaddabi -ijonoe",
        "mamaddabi ijonoe",
        "Printed page 9: OCR adds a false hyphen before ijonoe.",
    ),
    SourceCorrection(
        "section_09_prayer_after_instruction",
        "T7 Aposisi",
        "Kaposisi",
        "Printed page 11: ornate initial K is split from Aposisi.",
    ),
    SourceCorrection(
        "section_12_qa_10",
        "gagilna, s6-o allecho",
        "gagilna, so-o allecho",
        "Printed page 40: OCR reads the first o in so-o as 6.",
    ),
    SourceCorrection(
        "section_08_prayer_before_instruction",
        "A Ssanman-a",
        "A Ṣśánman-a",
        "Printed page 11: the opening diacritics are omitted by OCR.",
    ),
    SourceCorrection(
        "section_08_prayer_before_instruction",
        "Deos--sar",
        "Deos-sar",
        "Printed page 11: a line-break hyphen was duplicated by extraction.",
    ),
    SourceCorrection(
        "section_15_first_sermon",
        "--Don o ai-acha",
        "Don o ai-acha",
        "Printed page 75: ornamental indentation is OCR punctuation.",
    ),
    SourceCorrection(
        "section_15_first_sermon",
        "lummaPi namo",
        "lummal'i namo",
        "Printed page 76: OCR misreads l'i as Pi.",
    ),
    SourceCorrection(
        "section_16_second_sermon",
        "choa ri-6, makkesjap",
        "choa ri-ó, makkesjap",
        "Printed page 83: OCR reads accented ó as 6.",
    ),
    SourceCorrection(
        "section_16_second_sermon",
        "choa ri-6, cho'al-al",
        "choa ri-ó, cho'al-al",
        "Printed page 83: OCR reads accented ó as 6.",
    ),
    SourceCorrection(
        "section_17_third_sermon",
        "A1H talan ta Deos",
        "Alli talan ta Deos",
        "Printed page 91: OCR splits lli as H.",
    ),
    SourceCorrection(
        "section_18_fourth_sermon",
        "Agil o aba",
        "Gagil o aba",
        "Printed page 91: ornate initial G is omitted before Gagil.",
    ),
    SourceCorrection(
        "section_19_fifth_sermon",
        "-\" Maibas o sisjiem",
        "Maibas o sisjiem",
        "Printed page 98: ornamental indentation is OCR punctuation.",
    ),
    SourceCorrection(
        "section_19_fifth_sermon",
        "Macha o Deos mialFo autat ai inni ai-acha",
        "Macha o Deos mial'o autat ai inni ai-acha",
        "Printed page 101: OCR misreads apostrophe-l as F.",
    ),
)

# These rendered-source corrections are applied after the token-indexed
# diacritic ledger so that structural fixes cannot invalidate ledger indices.
POST_SOURCE_CORRECTIONS = (
    SourceCorrection(
        "section_04_morning_prayer",
        "0-0",
        "Ṣo-o",
        "Printed page 6: OCR reads the initial underdotted S as zero.",
    ),
    SourceCorrection(
        "section_05_evening_prayer",
        "rnicho",
        "micho",
        "Printed page 7: OCR reads printed micho as rnicho.",
    ),
    SourceCorrection(
        "section_05_evening_prayer",
        " j hena",
        "; hena",
        "Printed page 7: OCR reads the printed semicolon as j.",
    ),
    SourceCorrection(
        "section_10_item_03",
        "3. Ter. 7 r. ",
        "3. Ter. ",
        "Printed pages 12-13: repeated carry-over speaker label removed.",
    ),
    SourceCorrection(
        "section_10_item_03",
        "ijonoe?",
        "ijonoë?",
        "Printed page 13: the final e carries a diaeresis.",
    ),
    SourceCorrection(
        "section_10_item_03",
        "maso rnaso milip rinlip a geroan a baas",
        "maso milip a geroan a baas",
        "Printed page 13: duplicated OCR fragments removed.",
    ),
    SourceCorrection(
        "section_10_item_04",
        "4. 7 r. ",
        "4. Ter. ",
        "Printed page 13: italic Ter. is misread as 7 r.",
    ),
    SourceCorrection(
        "section_10_item_17",
        "17. 7?r. ",
        "17. Ter. ",
        "Printed page 15: italic Ter. is misread as 7?r.",
    ),
    SourceCorrection(
        "section_10_item_18",
        "18. 7 r. ",
        "18. Ter. ",
        "Printed page 15: italic Ter. is misread as 7 r.",
    ),
    SourceCorrection(
        "section_10_item_41",
        "41. 7 r. ",
        "41. Ter. ",
        "Printed page 20: italic Ter. is misread as 7 r.",
    ),
    SourceCorrection(
        "section_10_item_42",
        "42. 7 r. ",
        "42. Ter. ",
        "Printed page 20: italic Ter. is misread as 7 r.",
    ),
    SourceCorrection(
        "section_10_item_49",
        "49. 71?r.Numrna,jarapiesta haibos?",
        "49. Ter. Numma, ja rapies ta haibos?",
        "Printed page 21: the full numbered speaker line was visually transcribed.",
    ),
    SourceCorrection(
        "section_10_item_65",
        "65. Ter. 7 r. ",
        "65. Ter. ",
        "Printed pages 26-27: repeated carry-over speaker label removed.",
    ),
    SourceCorrection(
        "section_10_item_77",
        "77. Ter. 7 r. ",
        "77. Ter. ",
        "Printed pages 29-30: repeated carry-over speaker label removed.",
    ),
    SourceCorrection(
        "section_10_item_22",
        "Jzj. Azj.",
        "Azj.",
        "Printed page 15: duplicated answer label removed.",
    ),
    SourceCorrection(
        "section_10_item_30",
        "Azj. Jzj.",
        "Azj.",
        "Printed page 17: duplicated answer label removed.",
    ),
    SourceCorrection(
        "section_10_item_33",
        "Jzj. z.",
        "Azj.",
        "Printed page 18: damaged OCR answer label restored.",
    ),
    SourceCorrection(
        "section_13_item_23",
        "Torro Torro",
        "Torro",
        "Printed page 46: duplicated OCR word removed.",
    ),
    SourceCorrection(
        "section_13_item_62",
        "tapos 6 ai",
        "tapos o ai",
        "Printed page 57: OCR reads source o as 6.",
    ),
    SourceCorrection(
        "section_13_item_71",
        "tum-; malattal'i",
        "tummalattal'i",
        "Printed page 61: a line-break and semicolon OCR artifact are removed.",
    ),
    SourceCorrection(
        "section_15_first_sermon",
        "arorroai-a 1 e-illa-na",
        "arorroai-a e-illa-na",
        "Printed page 75: OCR inserts a false numeral at a page continuation.",
    ),
    SourceCorrection(
        "section_18_fourth_sermon",
        "0-0",
        "Ṣo-o",
        "Printed page 94: OCR reads the initial underdotted S as zero.",
    ),
    SourceCorrection(
        "section_03_item_02",
        "tamasea tamasea",
        "tamasea",
        "Printed pages 3-4: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_03_item_04",
        "tataap j ṣo-o",
        "tataap; ṣo-o",
        "Printed page 4: OCR reads the printed semicolon as j.",
    ),
    SourceCorrection(
        "section_07_prayer_after_meals",
        "Jehova, Jehova,",
        "Jehova,",
        "Printed pages 9-10: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_09_prayer_after_instruction",
        "naan, naan,",
        "naan,",
        "Printed pages 11-12: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_10_item_08",
        "haibos J a babosa",
        "haibos ja babosa",
        "Printed page 13: split lowercase ja restored.",
    ),
    SourceCorrection(
        "section_10_item_08",
        "Na'esurro alia",
        "Na'esurro, alia",
        "Printed page 13: source comma restored.",
    ),
    SourceCorrection(
        "section_10_item_06",
        "boesum aioe.",
        "boesum ai-oë.",
        "Printed page 13: source hyphen and diaeresis restored.",
    ),
    SourceCorrection(
        "section_10_item_09",
        "9. Ter. Nacha.",
        "9. Ter. Nachá.",
        "Printed page 13: source acute accent restored.",
    ),
    SourceCorrection(
        "section_10_item_40",
        " 41. Ter.",
        "",
        "Printed page 20: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_10_item_49",
        "anibaas, anibaas,",
        "anibaas,",
        "Printed pages 21-22: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_10_item_58",
        "Deos Deos",
        "Deos",
        "Printed pages 24-25: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "aukat aukat",
        "aukat",
        "Printed pages 25-26: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_10_item_71",
        " 72. Ter.",
        "",
        "Printed page 27: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_10_item_79",
        "haibos, haibos,",
        "haibos,",
        "Printed pages 30-31: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "boesum boesum",
        "boesum",
        "Printed pages 31-32: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_10_item_13",
        "nattada ga ja boa",
        "nattada ḡa ja boa",
        "Printed page 14: source g carries a macron.",
    ),
    SourceCorrection(
        "section_10_item_14",
        "pait'ijonoe",
        "pait'ijonoë",
        "Printed page 14: source e carries a diaeresis.",
    ),
    SourceCorrection(
        "section_10_item_15",
        "ailoe?",
        "ail-oë?",
        "Printed page 14: source hyphen and diaeresis restored.",
    ),
    SourceCorrection(
        "section_10_item_16",
        "pait'o choa barro,",
        "pait'o choa barr'o,",
        "Printed page 14: source apostrophe restored.",
    ),
    SourceCorrection(
        "section_10_item_16",
        "j '. Inni choa maunis",
        "Inni choa maunis",
        "Printed page 15: stray OCR characters before the answer removed.",
    ),
    SourceCorrection(
        "section_10_item_17",
        "maabarra",
        "ma-abarra",
        "Printed page 15: source hyphen restored.",
    ),
    SourceCorrection(
        "section_10_item_19",
        "Pagana.",
        "Pagána.",
        "Printed page 15: source acute accent restored.",
    ),
    SourceCorrection(
        "section_10_item_20",
        "Na-a paita masini j ja",
        "Na-a paita masini; ja",
        "Printed page 15: OCR reads the printed semicolon as j.",
    ),
    SourceCorrection(
        "section_10_item_22",
        "choa! baan",
        "choa baan",
        "Printed page 16: false OCR exclamation removed.",
    ),
    SourceCorrection(
        "section_10_item_23",
        "boesum aioe?",
        "boesum aioë?",
        "Printed page 16: source e carries a diaeresis.",
    ),
    SourceCorrection(
        "section_10_item_24",
        "Pagaga chaddai",
        "Pagaga chaddai!",
        "Printed page 16: source exclamation restored.",
    ),
    SourceCorrection(
        "section_10_item_29",
        "ja baziep,",
        "ja baziep.",
        "Printed page 17: source sentence-ending period restored.",
    ),
    SourceCorrection(
        "section_10_item_31",
        "maal-al",
        "ma-al-ál",
        "Printed page 18: source hyphenation and acute accent restored.",
    ),
    SourceCorrection(
        "section_10_item_41",
        "choa micho ga ja boa.",
        "choa micho ḡa ja boa.",
        "Printed page 20: source g carries a macron.",
    ),
    SourceCorrection(
        "section_10_item_44",
        "chono baak decho-",
        "chono baak decho-noë.",
        "Printed page 20: line-end continuation and diaeresis restored.",
    ),
    SourceCorrection(
        "section_10_item_46",
        "y. Pa:",
        "Pa:",
        "Printed page 21: stray OCR characters before the answer removed.",
    ),
    SourceCorrection(
        "section_10_item_46",
        "pagatomma tapos o; tataap",
        "pagatomma tapos o tataap",
        "Printed page 21: false OCR semicolon removed.",
    ),
    SourceCorrection(
        "section_10_item_48",
        "so-o cho'arapies.",
        "ṣo-o cho'arapies.",
        "Printed page 21: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_52",
        "so-o pabo'o",
        "ṣo-o pabo'o",
        "Printed page 22: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_53",
        "Mauchus poelakies imoa maibas",
        "Mauchus poelakies imoa; maibas",
        "Printed page 23: source semicolon restored.",
    ),
    SourceCorrection(
        "section_10_item_57",
        "Ja alii pinab'o",
        "Ja alli pinab'o",
        "Printed page 24: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "maabarra",
        "ma-abarra",
        "Printed page 25: source hyphen restored.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "Alii man",
        "Alli man",
        "Printed page 25: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "alii pausjiem",
        "alli pausjiem",
        "Printed page 25: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "alii mach'ija",
        "alli mach'ija",
        "Printed page 25: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "kutnmossi",
        "kummossi",
        "Printed page 26: OCR misreads the repeated m.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "machonsar rapies",
        "machonṣar rapies",
        "Printed page 26: source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_62",
        "Ja alii machi'o",
        "Ja alli machi'o",
        "Printed page 26: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_65",
        "kakoemen! ja",
        "kakoemen ja",
        "Printed page 27: false OCR exclamation removed.",
    ),
    SourceCorrection(
        "section_10_item_67",
        "ṣo-o choa arada",
        "ṣo-o choa arada!",
        "Printed page 27: source exclamation restored.",
    ),
    SourceCorrection(
        "section_10_item_68",
        "Talla alii maborr'i",
        "Talla alli maborr'i",
        "Printed page 27: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_68",
        "Deos dechonoe?",
        "Deos dechonoë?",
        "Printed page 27: source e carries a diaeresis.",
    ),
    SourceCorrection(
        "section_10_item_71",
        "babosa channumma dechonoe?",
        "babosa channumma dechonoë?",
        "Printed page 27: source e carries a diaeresis.",
    ),
    SourceCorrection(
        "section_10_item_73",
        "maabisse a tsjes",
        "ma-abisse a tsjes",
        "Printed page 28: source hyphen restored.",
    ),
    SourceCorrection(
        "section_10_item_73",
        "atillóno Deos",
        "atillono Deos",
        "Printed page 28: OCR adds a false acute accent.",
    ),
    SourceCorrection(
        "section_10_item_73",
        "aborra tuppach pach o Deos",
        "aborra tuppach o Deos",
        "Printed pages 28-29: duplicated page-continuation fragment removed.",
    ),
    SourceCorrection(
        "section_10_item_74",
        "klnummossi",
        "kinummossi",
        "Printed page 29: OCR reads i as l.",
    ),
    SourceCorrection(
        "section_10_item_76",
        "so-o ausjimen",
        "ṣo-o ausjimen",
        "Printed page 29: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_77",
        "lummal'i arapies?;",
        "lummal'i arapies?",
        "Printed page 30: false OCR semicolon removed.",
    ),
    SourceCorrection(
        "section_10_item_77",
        "mikkil o baak alia",
        "mikkil o baak; alia",
        "Printed page 30: source semicolon restored.",
    ),
    SourceCorrection(
        "section_10_item_78",
        "cho'arapies imonoe.",
        "cho'arapies imonoë.",
        "Printed page 30: source e carries a diaeresis.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "Ja alii maso",
        "Ja alli maso",
        "Printed page 31: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "Alii mabarra",
        "Alli mabarra",
        "Printed page 31: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "sja alii pauss'icho",
        "sja alli pauss'icho",
        "Printed page 31: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "tuppono mini:",
        "tuppono mini:—",
        "Printed page 31: source em dash restored.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "choa rara ummior",
        "choa rará ummior",
        "Printed page 32: source acute accent restored.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "pinoetat dechonoë",
        "pinoetatt dechonoë",
        "Printed page 32: final source t restored.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "pinaga maaijaab",
        "pinaga ma-aijaab",
        "Printed page 32: source hyphen restored.",
    ),
    SourceCorrection(
        "section_10_title",
        "so-o ta Holland-azjies",
        "ṣo-o ta Holland-azjies",
        "Printed page 12: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_02",
        "ja alii orachan",
        "ja alli orachan",
        "Printed page 12: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_16",
        "so-o aba matoto",
        "ṣo-o aba matoto",
        "Printed page 14: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_20",
        "so-o abas",
        "ṣo-o abas",
        "Printed page 15: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_21",
        "Matalam alii inerien",
        "Matalam alli inerien",
        "Printed page 15: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_28",
        "boesum alii poelakies",
        "boesum alli poelakies",
        "Printed page 17: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_30",
        "Gagilna: so-o innai",
        "Gagilna: ṣo-o innai",
        "Printed page 18: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_32",
        "sja alii moetas, alii tummoach",
        "sja alli moetas, alli tummoach",
        "Printed page 18: OCR reads two printed l characters as i.",
    ),
    SourceCorrection(
        "section_10_item_33",
        "sja alii maunis",
        "sja alli maunis",
        "Printed page 19: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_46",
        "Ja torro alii madarram",
        "Ja torro alli madarram",
        "Printed page 20: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_46",
        "sja alii pinachip",
        "sja alli pinachip",
        "Printed page 21: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_46",
        "anibaas alii pinattas",
        "anibaas alli pinattas",
        "Printed page 21: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_49",
        "channumma alii makarrichi",
        "channumma alli makarrichi",
        "Printed page 22: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_49",
        "haibos, alii poddodo",
        "haibos, alli poddodo",
        "Printed page 22: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_49",
        "madig, alii pattonan",
        "madig, alli pattonan",
        "Printed page 22: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_10_item_54",
        "anibaas, so-o choa sjiem",
        "anibaas, ṣo-o choa sjiem",
        "Printed page 23: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_61",
        "madas i ta Deos, so-o ummior",
        "madas i ta Deos, ṣo-o ummior",
        "Printed page 26: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_73",
        "babisse, so-o ummior",
        "babisse, ṣo-o ummior",
        "Printed page 28: initial source s carries an underdot.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "a abas alii pinaga",
        "a abas alli pinaga",
        "Printed page 31: OCR reads the second l as i.",
    ),
    SourceCorrection(
        "section_11_item_04",
        "Ta Ta Christus",
        "Ta Christus",
        "Printed page 34: duplicated line-start word removed.",
    ),
    SourceCorrection(
        "section_11_item_08",
        "Ta Ta Christus",
        "Ta Christus",
        "Printed page 34: duplicated line-start word removed.",
    ),
    SourceCorrection(
        "section_11_item_15",
        "Ta Ta Christus",
        "Ta Christus",
        "Printed page 37: duplicated line-start word removed.",
    ),
    SourceCorrection(
        "section_12_qa_06",
        "Ka Ka",
        "Ka",
        "Printed pages 39-40: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_03",
        " 4. Numma",
        "",
        "Printed page 41: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_13_item_06",
        "Inau Inau",
        "Inau",
        "Printed pages 42-43: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_14",
        " 15. Mai",
        "",
        "Printed page 45: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_13_item_26",
        "Maini Maini:",
        "Maini:",
        "Printed pages 47-48: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_37",
        "boa boa",
        "boa",
        "Printed pages 49-50: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_46",
        "Hena Hena:",
        "Hena:",
        "Printed pages 51-52: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_55",
        "kakossi kakossi",
        "kakossi",
        "Printed pages 54-55: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_57",
        "Maini: Maini:",
        "Maini:",
        "Printed pages 55-56: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_13_item_60",
        " 61. Inonumma",
        "",
        "Printed page 56: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_13_item_68",
        " 69. Numma",
        "",
        "Printed page 60: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_13_item_76",
        " 77-Ja",
        "",
        "Printed page 62: next-item carry-over marker removed.",
    ),
    SourceCorrection(
        "section_13_item_79",
        "Mapan Mapan",
        "Mapan",
        "Printed pages 64-65: duplicated page-continuation word removed.",
    ),
    SourceCorrection(
        "section_14_item_06",
        "Kamaunionis Kamaunionis",
        "Kamaunionis",
        "Printed page 68: duplicated line-start word removed.",
    ),
    SourceCorrection(
        "section_04_morning_prayer",
        "masini:-Namoa",
        "masini:—Namoa",
        "Printed page 6: OCR reads the source em dash as a hyphen.",
    ),
    SourceCorrection(
        "section_05_evening_prayer",
        "masini:-Namoa",
        "masini:—Namoa",
        "Printed page 8: OCR reads the source em dash as a hyphen.",
    ),
    SourceCorrection(
        "section_09_prayer_after_instruction",
        "masini:-Namoa",
        "masini:—Namoa",
        "Printed page 12: OCR reads the source em dash as a hyphen.",
    ),
    SourceCorrection(
        "section_13_item_89",
        "a-i-joramorichomini",
        "a-i-jor a morich o mini",
        (
            "Printed page 67: OCR fuses the four visibly separated source "
            "words."
        ),
    ),
    SourceCorrection(
        "section_13_item_77",
        "Aigar-; rórro",
        "Aigarrórro",
        (
            "Printed page 63: remove extraction punctuation from the "
            "line-wrapped word."
        ),
    ),
    SourceCorrection(
        "section_13_item_90",
        " Amen. Ma-",
        " Amen.",
        "Printed page 67: remove the next-section carry-over fragment.",
    ),
    SourceCorrection(
        "section_16_second_sermon",
        "machalloch-; allo",
        "machallochallo",
        (
            "Printed page 80: remove extraction punctuation from the "
            "line-wrapped dictionary-attested word machallochallo."
        ),
    ),
    SourceCorrection(
        "section_18_fourth_sermon",
        "ma-abisse-; bissé",
        "ma-abisse-bissé",
        (
            "Printed page 94: remove an extraction semicolon inserted into "
            "the line-wrapped source word."
        ),
    ),
)

TRANSLATION_CORRECTIONS = (
    SourceCorrection(
        "section_10_item_24",
        "Perhaps",
        "Perhaps!",
        "Printed page 16: English exclamation restored.",
    ),
    SourceCorrection(
        "section_10_item_26",
        "fruits of the field,",
        "fruits of the field.",
        "Printed page 16: English sentence-ending period restored.",
    ),
    SourceCorrection(
        "section_10_item_54",
        "and a. deception",
        "and a deception",
        "Printed page 23: false OCR period removed from the English text.",
    ),
    SourceCorrection(
        "section_10_item_55",
        "He lies. ' The birds",
        "He lies. The birds",
        "Printed page 24: stray OCR apostrophe removed from the English text.",
    ),
    SourceCorrection(
        "section_10_item_60",
        "By what means do you know him?.,-,..",
        "By what means do you know him?",
        "Printed page 25: stray OCR punctuation removed from the English text.",
    ),
    SourceCorrection(
        "section_10_item_73",
        "an enemy, a. murderer",
        "an enemy, a murderer",
        "Printed page 28: false OCR period removed from the English text.",
    ),
    SourceCorrection(
        "section_10_item_73",
        "steps oftiis disobedience",
        "steps of his disobedience",
        "Printed page 29: fused OCR words restored in the English text.",
    ),
    SourceCorrection(
        "section_10_item_74",
        "Well,. has man",
        "Well, has man",
        "Printed page 29: false OCR period removed from the English text.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "punishment of hell -fire",
        "punishment of hell-fire",
        "Printed page 31: false OCR space removed from the English text.",
    ),
    SourceCorrection(
        "section_10_item_80",
        "remember these three things:",
        "remember these three things:--",
        "Printed page 31: English em dash restored.",
    ),
)

POST_REVIEW_TRANSLATION_CORRECTIONS = (
    SourceCorrection(
        "section_03_item_10",
        "neighbour s wife",
        "neighbour's wife",
        "Printed page 5: possessive apostrophe restored in the English text.",
    ),
    SourceCorrection(
        "section_13_item_50",
        "on the, cross",
        "on the cross",
        "Printed page 53: false OCR comma removed from the English text.",
    ),
    SourceCorrection(
        "section_13_item_50",
        "man s sin",
        "man's sin",
        "Printed page 53: possessive apostrophe restored in the English text.",
    ),
    SourceCorrection(
        "section_13_item_50",
        "covering- on account",
        "covering--on account",
        "Printed page 53: English em dash restored.",
    ),
)


def _range_text(prefix: str, start: int, end: int) -> str:
    return f"{prefix}_{start}" if start == end else f"{prefix}s_{start}-{end}"


def parse_word_coords(coords: str) -> tuple[int, float]:
    left, y1, _right, y0, y2 = [int(part) for part in coords.split(",")]
    y_mid = (min(y0, y1, y2) + max(y0, y1, y2)) / 2
    return left, y_mid


def read_pages() -> list[ET.Element]:
    if not SOURCE_XML.exists():
        raise FileNotFoundError(SOURCE_XML)
    return ET.parse(SOURCE_XML).getroot().findall(".//OBJECT")


def page_lines(page: ET.Element) -> list[Line]:
    words: list[tuple[float, int, str]] = []
    for word in page.findall(".//WORD"):
        if not word.text or not word.get("coords"):
            continue
        try:
            x_left, y_mid = parse_word_coords(word.get("coords", ""))
        except ValueError:
            continue
        words.append((y_mid, x_left, word.text))

    clusters: list[dict[str, object]] = []
    for y_mid, x_left, text in sorted(words):
        for cluster in clusters:
            if abs(float(cluster["y"]) - y_mid) < 18:
                items = cluster["items"]
                assert isinstance(items, list)
                count = len(items)
                cluster["y"] = (float(cluster["y"]) * count + y_mid) / (
                    count + 1
                )
                items.append((x_left, text))
                break
        else:
            clusters.append({"y": y_mid, "items": [(x_left, text)]})

    lines: list[Line] = []
    for cluster in sorted(clusters, key=lambda item: float(item["y"])):
        items = sorted(cluster["items"])  # type: ignore[arg-type]
        all_text = " ".join(text for _x, text in items)
        left_text = " ".join(text for x, text in items if x < 850)
        right_text = " ".join(text for x, text in items if x >= 850)
        lines.append(Line(float(cluster["y"]), all_text, left_text, right_text))
    return lines


def english_score(text: str) -> int:
    tokens = re.findall(r"[A-Za-z']+", text.lower())
    return sum(token in ENGLISH_WORDS for token in tokens)


def looks_like_english_block_start(text: str) -> bool:
    normalized = clean_translation(text)
    if re.match(r"^[IVXLCDM]+\.\s+[A-Z]", normalized):
        return True
    if english_score(normalized) >= 4:
        return True
    return bool(
        re.match(r"^(?:\d+\s*[.;:]?\s*)?(?:Fav|Str|Sir)\.?\b", normalized)
        or re.match(
            r"^\d+\s*[.;:]?\s+"
            r"(?:Thou|What|Who|Where|When|Whence|How|Does|Do|Did|Is|"
            r"Are|Will|Must|Can|Has|Have|No|Yes|Thus)\b",
            normalized,
        )
        or re.match(r"^(?:Question|Answer|Q|A)\.\s+", normalized)
    )


def detect_english_start(
    lines: list[Line],
    min_y: int,
    max_y: int | None = None,
) -> int | None:
    candidates: list[int] = []
    for index, line in enumerate(lines):
        if line.y <= min_y:
            continue
        if max_y is not None and line.y >= max_y:
            continue
        if looks_like_english_block_start(line.all_text):
            candidates.append(index)
    for index in candidates:
        if index == 0 or lines[index].y - lines[index - 1].y >= 55:
            return index
    return candidates[0] if candidates else None


def normalize_typography(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    replacements = {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2013": "-",
        "\u2014": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def clean_source(text: str) -> str:
    text = normalize_typography(text)
    allowed_punctuation = set("'\".,;:?!-()")
    text = "".join(
        char
        if (
            char.isspace()
            or unicodedata.category(char)[0] in {"L", "M", "N"}
            or char in allowed_punctuation
        )
        else " "
        for char in text
    )
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    text = re.sub(r"\s*-\s*", "-", text)
    return normalize_source_marker(text)


def clean_translation(text: str) -> str:
    text = normalize_typography(text)
    text = re.sub(r"[^\x20-\x7E]", " ", text)
    text = re.sub(r"[\^><~*_`=+\[\]{}|\\@#$%]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    return text


def normalize_source_marker(text: str) -> str:
    text = re.sub(r"^io\.\s+Ter\.", "10. Ter.", text, flags=re.I)
    text = re.sub(r"^ii\.\s+Ter\.", "11. Ter.", text, flags=re.I)
    text = re.sub(r"^1\s+7\.\s+", "17. ", text)
    text = re.sub(r"^1\s+6\.\s+", "16. ", text)
    text = re.sub(r"^1\s+3\.\s+", "13. ", text)
    text = re.sub(r"^8\s+1\.\s+", "81. ", text)
    text = re.sub(r"^35\s+Ter\.", "35. Ter.", text)
    return text


def normalize_translation_marker(text: str) -> str:
    text = re.sub(r"^(\d+)-\s+", r"\1. ", text)
    text = re.sub(r"^IS-\s+Fav\.", "15. Fav.", text)
    text = re.sub(r"^l\s+J\.\s+Fav\.", "17. Fav.", text)
    text = re.sub(r"^53\s+Fav\.", "53. Fav.", text)
    text = re.sub(r"^3\s+4\.\s+", "34. ", text)
    text = re.sub(r"^3\s+5\.\s+", "35. ", text)
    text = re.sub(r"^2\s+2\.\s+", "22. ", text)
    text = re.sub(
        r"^[\"',.]+\s*Do all men receive the forgiveness",
        "22. Do all men receive the forgiveness",
        text,
    )
    return text


def drop_source_line(text: str) -> bool:
    if not text or len(re.findall(r"[^\W\d_]", text, re.UNICODE)) < 2:
        return True
    stripped = text.strip(" .;:-").lower()
    if stripped in {
        "autat",
        "aseas",
        "christian",
        "de",
        "het",
        "instruction",
    }:
        return True
    if re.fullmatch(r"[IVXLCDMivxlcdm0-9]+[.;:]?", text):
        return True
    if "SERMON" in text.upper():
        return True
    if re.search(
        r"\b(?:Isaiah|Timothy|Matthew|Matthei|Genesis|Corinthians|Hebrews|John)\b",
        text,
        re.I,
    ):
        return True
    return False


def drop_translation_line(text: str) -> bool:
    stripped = text.strip()
    return bool(
        not stripped
        or re.fullmatch(r"[A-Z]", stripped)
        or re.match(r"^[IVXLCDM]+\.\s+", stripped)
        or re.match(r"^END OF (?:THE )?", stripped)
    )


def dehyphenate(lines: list[LocatedLine]) -> str:
    chunks: list[str] = []
    for line in lines:
        text = line.text.strip()
        if not text:
            continue
        if chunks and chunks[-1].endswith("-"):
            chunks[-1] = chunks[-1][:-1] + text
        else:
            chunks.append(text)
    return " ".join(chunks)


def in_span(
    printed_page: int,
    y: float,
    start: tuple[int, int],
    stop: tuple[int, int],
) -> bool:
    position = (printed_page, y)
    return (start[0], float(start[1])) <= position < (
        stop[0],
        float(stop[1]),
    )


def collect_short_source_lines(
    pages: list[ET.Element],
    spec: SectionSpec,
) -> list[LocatedLine]:
    output: list[LocatedLine] = []
    for printed_page in range(spec.source_start[0], spec.source_stop[0] + 1):
        pdf_object_page = printed_page + 32
        lines = page_lines(pages[pdf_object_page - 1])
        english_start = detect_english_start(
            lines,
            550 if printed_page == 75 else 1450,
            800 if printed_page == 75 else None,
        )
        if english_start is None:
            raise RuntimeError(
                f"No English block detected on printed page {printed_page}"
            )
        source_limit_y = lines[english_start].y - 25
        for line in lines:
            if line.y < 200 or line.y >= source_limit_y:
                continue
            if not in_span(
                printed_page,
                line.y,
                spec.source_start,
                spec.source_stop,
            ):
                continue
            text = clean_source(line.right_text)
            if not drop_source_line(text):
                output.append(
                    LocatedLine(
                        printed_page,
                        pdf_object_page,
                        line.y,
                        text,
                    )
                )
    if not output:
        raise RuntimeError(f"No source lines found for section {spec.number}")
    return output


def collect_translation_lines(
    pages: list[ET.Element],
    spec: SectionSpec,
) -> list[LocatedLine]:
    if spec.translation_start is None or spec.translation_stop is None:
        return []
    output: list[LocatedLine] = []
    for printed_page in range(
        spec.translation_start[0],
        spec.translation_stop[0] + 1,
    ):
        pdf_object_page = printed_page + 32
        lines = page_lines(pages[pdf_object_page - 1])
        english_start = detect_english_start(
            lines,
            550 if printed_page == 75 else 1450,
            800 if printed_page == 75 else None,
        )
        if english_start is None:
            raise RuntimeError(
                f"No English block detected on printed page {printed_page}"
            )
        for line in lines[english_start:]:
            if not in_span(
                printed_page,
                line.y,
                spec.translation_start,
                spec.translation_stop,
            ):
                continue
            text = normalize_translation_marker(clean_translation(line.all_text))
            if not drop_translation_line(text):
                output.append(
                    LocatedLine(
                        printed_page,
                        pdf_object_page,
                        line.y,
                        text,
                    )
                )
    if not output:
        raise RuntimeError(
            f"No translation lines found for section {spec.number}"
        )
    return output


def collect_sermon_source_lines(
    pages: list[ET.Element],
    spec: SectionSpec,
) -> list[LocatedLine]:
    output: list[LocatedLine] = []
    for printed_page in range(spec.source_start[0], spec.source_stop[0] + 1):
        pdf_object_page = printed_page + 32
        lines = page_lines(pages[pdf_object_page - 1])
        for side in ("left_text", "right_text"):
            for line in lines:
                if line.y < 200:
                    continue
                if not in_span(
                    printed_page,
                    line.y,
                    spec.source_start,
                    spec.source_stop,
                ):
                    continue
                text = clean_source(getattr(line, side))
                if not drop_source_line(text):
                    output.append(
                        LocatedLine(
                            printed_page,
                            pdf_object_page,
                            line.y,
                            text,
                        )
                    )
    if not output:
        raise RuntimeError(f"No sermon lines found for section {spec.number}")
    return output


def numbered_segments(
    lines: list[LocatedLine],
    expected: int,
    *,
    first_unmarked: bool = False,
    allow_preamble: bool = False,
) -> tuple[list[LocatedLine], dict[int, list[LocatedLine]]]:
    preamble: list[LocatedLine] = []
    segments: dict[int, list[LocatedLine]] = {}
    current: int | None = 1 if first_unmarked else None
    if first_unmarked:
        segments[1] = []

    for line in lines:
        match = re.match(r"^(\d+)\.\s*(.*)$", line.text)
        if match:
            number = int(match.group(1))
            remainder = match.group(2)
            if number < 1 or number > expected:
                raise RuntimeError(
                    f"Unexpected item {number}; expected 1-{expected}"
                )
            next_number = 1 if current is None else current + 1
            if number not in {current, next_number}:
                if current is None:
                    preamble.append(line)
                else:
                    segments[current].append(line)
                continue
            if number == current:
                if remainder:
                    existing = dehyphenate(segments[number])
                    existing_body = re.sub(
                        rf"^{number}\.\s*",
                        "",
                        existing,
                    )
                    if remainder.startswith(existing_body):
                        segments[number] = [
                            replace(line, text=f"{number}. {remainder}")
                        ]
                    elif not existing_body.startswith(remainder):
                        segments[number].append(
                            replace(line, text=remainder)
                        )
                continue
            current = number
            segments.setdefault(number, [])
            segments[number].append(line)
            continue
        if current is None:
            preamble.append(line)
        else:
            segments[current].append(line)

    if first_unmarked and not segments[1]:
        raise RuntimeError("Expected unmarked first item has no source text")
    if preamble and not allow_preamble:
        raise RuntimeError(
            f"Unexpected preamble before numbered items: {dehyphenate(preamble)[:80]}"
        )
    expected_numbers = set(range(1, expected + 1))
    if set(segments) != expected_numbers:
        missing = sorted(expected_numbers - set(segments))
        extras = sorted(set(segments) - expected_numbers)
        raise RuntimeError(
            f"Numbered segment mismatch: missing={missing} extras={extras}"
        )
    return preamble, segments


def qa_segments(
    lines: list[LocatedLine],
    *,
    source: bool,
) -> dict[int, list[LocatedLine]]:
    pattern = (
        re.compile(r"^(?:Chachod|Cha)\.\s*", re.I)
        if source
        else re.compile(r"^(?:Question|Q)\.\s*", re.I)
    )
    segments: dict[int, list[LocatedLine]] = {}
    current = 0
    for line in lines:
        if pattern.match(line.text):
            current += 1
            segments[current] = [line]
        elif current:
            segments[current].append(line)
        else:
            raise RuntimeError(
                f"Text before first Q/A marker: {line.text[:80]}"
            )
    return segments


def record_from_lines(
    spec: SectionSpec,
    record_id: str,
    part: str,
    label: str,
    source_lines: list[LocatedLine],
    translation_lines: list[LocatedLine],
    notes: str,
) -> Record:
    if not source_lines:
        raise RuntimeError(f"Empty FORM for {record_id}")
    return Record(
        record_id=record_id,
        section=spec.number,
        section_title=spec.title,
        part=part,
        label=label,
        printed_page_start=min(line.printed_page for line in source_lines),
        printed_page_end=max(line.printed_page for line in source_lines),
        pdf_object_page_start=min(
            line.pdf_object_page for line in source_lines
        ),
        pdf_object_page_end=max(line.pdf_object_page for line in source_lines),
        form=dehyphenate(source_lines),
        translation=dehyphenate(translation_lines),
        notes=notes,
    )


def title_record(spec: SectionSpec) -> Record | None:
    source_title = SOURCE_TITLES.get(spec.number)
    if source_title is None:
        return None
    printed_page = spec.source_start[0]
    return Record(
        record_id=f"section_{spec.number:02d}_title",
        section=spec.number,
        section_title=spec.title,
        part="section_title",
        label="title",
        printed_page_start=printed_page,
        printed_page_end=printed_page,
        pdf_object_page_start=printed_page + 32,
        pdf_object_page_end=printed_page + 32,
        form=source_title,
        translation=f"{spec.title}.",
        notes=(
            "Printed Favorlang section heading aligned to Campbell's "
            "English heading"
        ),
    )


def prepend_title(spec: SectionSpec, records: list[Record]) -> list[Record]:
    title = title_record(spec)
    return records if title is None else [title, *records]


def records_for_section(
    pages: list[ET.Element],
    spec: SectionSpec,
) -> list[Record]:
    if spec.mode == "sermon":
        source_lines = collect_sermon_source_lines(pages, spec)
        return prepend_title(
            spec,
            [
                record_from_lines(
                    spec,
                    f"section_{spec.number:02d}_{spec.slug}",
                    "sermon",
                    "",
                    source_lines,
                    [],
                    "Source-only sermon joined across physical page boundaries",
                )
            ],
        )

    source_lines = collect_short_source_lines(pages, spec)
    translation_lines = collect_translation_lines(pages, spec)
    if spec.mode == "single":
        return prepend_title(
            spec,
            [
                record_from_lines(
                    spec,
                    f"section_{spec.number:02d}_{spec.slug}",
                    "primary_section",
                    "",
                    source_lines,
                    translation_lines,
                    "Printed primary section joined across page boundaries",
                )
            ],
        )

    if spec.mode == "qa_pairs":
        source_segments = qa_segments(source_lines, source=True)
        translation_segments = qa_segments(
            translation_lines,
            source=False,
        )
        expected = set(range(1, spec.expected_items + 1))
        if set(source_segments) != expected or set(translation_segments) != expected:
            raise RuntimeError(
                f"Section {spec.number} Q/A mismatch: "
                f"source={sorted(source_segments)} "
                f"translation={sorted(translation_segments)}"
            )
        return prepend_title(
            spec,
            [
                record_from_lines(
                    spec,
                    f"section_{spec.number:02d}_qa_{number:02d}",
                    "qa_pair",
                    f"qa_{number:02d}",
                    source_segments[number],
                    translation_segments[number],
                    "Question and answer pair segmented by printed speaker labels",
                )
                for number in sorted(expected)
            ],
        )

    source_preamble, source_segments = numbered_segments(
        source_lines,
        spec.expected_items,
        first_unmarked=spec.mode == "numbered_first_unmarked",
        allow_preamble=spec.mode == "numbered_with_preamble",
    )
    translation_preamble, translation_segments = numbered_segments(
        translation_lines,
        spec.expected_items,
        allow_preamble=spec.mode == "numbered_with_preamble",
    )
    records: list[Record] = []
    if spec.mode == "numbered_with_preamble":
        if not source_preamble or not translation_preamble:
            raise RuntimeError(
                f"Section {spec.number} should have source and translation preambles"
            )
        records.append(
            record_from_lines(
                spec,
                f"section_{spec.number:02d}_preamble",
                "section_preamble",
                "preamble",
                source_preamble,
                translation_preamble,
                "Introductory text before the numbered items",
            )
        )
    for number in range(1, spec.expected_items + 1):
        records.append(
            record_from_lines(
                spec,
                f"section_{spec.number:02d}_item_{number:02d}",
                "numbered_item",
                f"item_{number:02d}",
                source_segments[number],
                translation_segments[number],
                "Numbered source item aligned to the corresponding English item",
            )
        )
    return prepend_title(spec, records)


def collect_records() -> list[Record]:
    pages = read_pages()
    records = [
        record
        for spec in SECTIONS
        for record in records_for_section(pages, spec)
    ]
    expected_count = 279
    if len(records) != expected_count:
        raise RuntimeError(
            f"Expected {expected_count} logical records, found {len(records)}"
        )
    ids = [record.record_id for record in records]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Generated record IDs are not unique")
    return records


def apply_source_corrections(
    records: list[Record],
) -> tuple[list[Record], list[AppliedCorrection]]:
    corrected: list[Record] = []
    applied: list[AppliedCorrection] = []
    correction_ids = {item.record_id for item in SOURCE_CORRECTIONS}
    record_ids = {record.record_id for record in records}
    unknown_ids = sorted(correction_ids - record_ids)
    if unknown_ids:
        raise RuntimeError(
            f"Source corrections reference unknown records: {unknown_ids}"
        )

    for record in records:
        form = record.form
        if record.record_id in EXACT_FORM_OVERRIDES:
            new_form = EXACT_FORM_OVERRIDES[record.record_id]
            applied.append(
                AppliedCorrection(
                    record.record_id,
                    record.printed_page_start,
                    record.printed_page_end,
                    form,
                    new_form,
                    (
                        "Complete rendered-page transcription preserving "
                        "the printed short-text diacritics."
                    ),
                )
            )
            form = new_form
        for correction in (
            item
            for item in SOURCE_CORRECTIONS
            if item.record_id == record.record_id
        ):
            if correction.old not in form:
                raise RuntimeError(
                    f"Expected correction text missing in {record.record_id}: "
                    f"{correction.old!r}"
                )
            form = form.replace(correction.old, correction.new, 1)
            applied.append(
                AppliedCorrection(
                    record.record_id,
                    record.printed_page_start,
                    record.printed_page_end,
                    correction.old,
                    correction.new,
                    correction.reason,
                )
            )
        corrected.append(replace(record, form=form))
    return corrected, applied


def fold_diacritics(text: str) -> str:
    return "".join(
        char.casefold()
        for char in unicodedata.normalize("NFD", text)
        if unicodedata.category(char) != "Mn"
    )


def read_diplomatic_corrections() -> list[DiplomaticCorrection]:
    if not DIPLOMATIC_DIACRITICS_TSV.exists():
        raise FileNotFoundError(DIPLOMATIC_DIACRITICS_TSV)
    with DIPLOMATIC_DIACRITICS_TSV.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {
        "record_id",
        "token_index",
        "old_token",
        "new_token",
        "printed_page",
        "verification",
    }
    if not rows or set(rows[0]) != required:
        raise RuntimeError("Diplomatic diacritic ledger schema changed")
    corrections = [
        DiplomaticCorrection(
            record_id=row["record_id"],
            token_index=int(row["token_index"]),
            old_token=row["old_token"],
            new_token=row["new_token"],
            printed_page=int(row["printed_page"]),
            verification=row["verification"],
        )
        for row in rows
    ]
    keys = [
        (correction.record_id, correction.token_index)
        for correction in corrections
    ]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Diplomatic diacritic ledger keys are not unique")
    for correction in corrections:
        if fold_diacritics(correction.old_token) != fold_diacritics(
            correction.new_token
        ):
            raise RuntimeError(
                "Diplomatic correction changes base letters: "
                f"{correction.record_id} token {correction.token_index}"
            )
        if "ṭ" in correction.new_token.casefold():
            raise RuntimeError(
                "No source-verified t-underdot is accepted in this edition"
            )
    return corrections


def apply_diplomatic_corrections(
    records: list[Record],
) -> tuple[list[Record], int]:
    corrections = read_diplomatic_corrections()
    by_record: dict[str, list[DiplomaticCorrection]] = {}
    for correction in corrections:
        by_record.setdefault(correction.record_id, []).append(correction)
    record_ids = {record.record_id for record in records}
    unknown = sorted(set(by_record) - record_ids)
    if unknown:
        raise RuntimeError(
            f"Diplomatic corrections reference unknown records: {unknown}"
        )

    corrected: list[Record] = []
    applied = 0
    for record in records:
        form = record.form
        token_matches = list(TOKEN_RE.finditer(form))
        replacements: dict[int, str] = {}
        for correction in by_record.get(record.record_id, []):
            if not (
                record.printed_page_start
                <= correction.printed_page
                <= record.printed_page_end
            ):
                raise RuntimeError(
                    "Diplomatic correction page is outside record provenance: "
                    f"{record.record_id} token {correction.token_index}"
                )
            if correction.token_index >= len(token_matches):
                raise RuntimeError(
                    "Diplomatic correction token index is out of range: "
                    f"{record.record_id} token {correction.token_index}"
                )
            actual = token_matches[correction.token_index].group(0)
            if actual != correction.old_token:
                raise RuntimeError(
                    "Diplomatic correction source token changed: "
                    f"{record.record_id} token {correction.token_index}; "
                    f"expected {correction.old_token!r}, found {actual!r}"
                )
            replacements[correction.token_index] = correction.new_token
        if replacements:
            chunks: list[str] = []
            cursor = 0
            for index, match in enumerate(token_matches):
                if index not in replacements:
                    continue
                chunks.append(form[cursor : match.start()])
                chunks.append(replacements[index])
                cursor = match.end()
            chunks.append(form[cursor:])
            form = "".join(chunks)
            applied += len(replacements)
        corrected.append(replace(record, form=form))
    if applied != len(corrections):
        raise RuntimeError(
            f"Applied {applied} of {len(corrections)} diplomatic corrections"
        )
    return corrected, applied


def apply_post_source_corrections(
    records: list[Record],
) -> tuple[list[Record], list[AppliedCorrection]]:
    corrected: list[Record] = []
    applied: list[AppliedCorrection] = []
    record_ids = {record.record_id for record in records}
    unknown = sorted(
        {correction.record_id for correction in POST_SOURCE_CORRECTIONS}
        - record_ids
    )
    if unknown:
        raise RuntimeError(
            f"Post-ledger corrections reference unknown records: {unknown}"
        )
    for record in records:
        form = record.form
        for correction in (
            item
            for item in POST_SOURCE_CORRECTIONS
            if item.record_id == record.record_id
        ):
            if correction.old not in form:
                raise RuntimeError(
                    f"Expected post-ledger text missing in {record.record_id}: "
                    f"{correction.old!r}"
                )
            form = form.replace(correction.old, correction.new, 1)
            applied.append(
                AppliedCorrection(
                    record.record_id,
                    record.printed_page_start,
                    record.printed_page_end,
                    correction.old,
                    correction.new,
                    correction.reason,
                )
            )
        if record.section == 10:
            form = re.sub(r"\bJzj\.", "Azj.", form)
            form = re.sub(r"\bA j[,.]", "Azj.", form)
            form = re.sub(r"(?:Azj\.\s*){2,}", "Azj. ", form)
        form = re.sub(r"([,;:?!])(?=[^\W_])", r"\1 ", form)
        form = re.sub(r"(?<=[a-zëḡṣáéíóú])\.(?=[A-Z])", ". ", form)
        form = re.sub(r"\s+", " ", form).strip()
        corrected.append(replace(record, form=form))
    return corrected, applied


def apply_translation_corrections(
    records: list[Record],
    correction_inventory: tuple[SourceCorrection, ...] = TRANSLATION_CORRECTIONS,
) -> tuple[list[Record], list[AppliedCorrection]]:
    corrected: list[Record] = []
    applied: list[AppliedCorrection] = []
    record_ids = {record.record_id for record in records}
    unknown = sorted(
        {correction.record_id for correction in correction_inventory}
        - record_ids
    )
    if unknown:
        raise RuntimeError(
            f"Translation corrections reference unknown records: {unknown}"
        )
    for record in records:
        translation = record.translation
        for correction in (
            item
            for item in correction_inventory
            if item.record_id == record.record_id
        ):
            if correction.old not in translation:
                raise RuntimeError(
                    "Expected translation correction text missing in "
                    f"{record.record_id}: {correction.old!r}"
                )
            translation = translation.replace(
                correction.old,
                correction.new,
                1,
            )
            applied.append(
                AppliedCorrection(
                    record.record_id,
                    record.printed_page_start,
                    record.printed_page_end,
                    correction.old,
                    correction.new,
                    correction.reason,
                    tier="translation",
                )
            )
        corrected.append(replace(record, translation=translation))
    return corrected, applied


def strip_boundary_number(text: str) -> str:
    return re.sub(r"^\d+\.\s*", "", text, count=1).strip()


def split_dialogue_text(
    text: str,
    *,
    opening_label: re.Pattern[str],
    response_label: re.Pattern[str],
) -> tuple[str, str]:
    opening = opening_label.match(text)
    if opening is None:
        raise RuntimeError(f"Dialogue opening label missing: {text[:100]!r}")
    body = text[opening.end() :]
    response = response_label.search(body)
    if response is None:
        raise RuntimeError(f"Dialogue response label missing: {text[:100]!r}")
    first = body[: response.start()].strip()
    second = body[response.end() :].strip()
    if not first or not second:
        raise RuntimeError(f"Empty dialogue turn: {text[:100]!r}")
    return first, second


def restructure_records(records: list[Record]) -> list[Record]:
    source_opening = re.compile(r"^\d+\.\s*(?:Ternern|Ter)\.\s*")
    source_response = re.compile(r"\b(?:Azjies|Azj|Axj)\.\s*")
    english_opening = re.compile(
        r"^\d+\.\s*(?:Favorlanger|Fav|Fan)\.\s*"
    )
    english_response = re.compile(r"\b(?:Stranger|Str|Sir)\.\s*")

    restructured: list[Record] = []
    for record in records:
        if record.section == 10 and record.part == "numbered_item":
            favorlanger_form, stranger_form = split_dialogue_text(
                record.form,
                opening_label=source_opening,
                response_label=source_response,
            )
            favorlanger_translation, stranger_translation = split_dialogue_text(
                record.translation,
                opening_label=english_opening,
                response_label=english_response,
            )
            restructured.extend(
                [
                    replace(
                        record,
                        record_id=f"{record.record_id}_favorlanger",
                        part="dialogue_turn",
                        label=f"{record.label}_favorlanger",
                        form=favorlanger_form,
                        translation=favorlanger_translation,
                        notes=(
                            "Favorlanger turn split at printed speaker labels; "
                            "boundary number and label omitted"
                        ),
                    ),
                    replace(
                        record,
                        record_id=f"{record.record_id}_stranger",
                        part="dialogue_turn",
                        label=f"{record.label}_stranger",
                        form=stranger_form,
                        translation=stranger_translation,
                        notes=(
                            "Dutch stranger turn split at printed speaker labels; "
                            "boundary number and label omitted"
                        ),
                    ),
                ]
            )
            continue
        if record.part == "numbered_item":
            record = replace(
                record,
                form=strip_boundary_number(record.form),
                translation=strip_boundary_number(record.translation),
                notes=(
                    "Printed numbered item aligned to the corresponding English "
                    "item; boundary number omitted"
                ),
            )
        restructured.append(record)
    return restructured


def assign_standard_surfaces(records: list[Record]) -> list[Record]:
    standardized = [
        replace(record, standard=standard_surface(record.form))
        for record in records
    ]
    changed = sum(record.standard != record.form for record in standardized)
    if changed != EXPECTED_STANDARD_CHANGES:
        raise ValueError(
            "Baseline standard surface inventory changed: expected "
            f"{EXPECTED_STANDARD_CHANGES}, found {changed}"
        )
    if any("-" in record.standard for record in standardized):
        raise ValueError("ASCII hyphen remains in a baseline standard surface")
    return standardized


def read_reviewer_corrections() -> list[ReviewerCorrection]:
    if not REVIEWER_CORRECTIONS_TSV.exists():
        raise FileNotFoundError(REVIEWER_CORRECTIONS_TSV)
    with REVIEWER_CORRECTIONS_TSV.open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {
        "record_id",
        "tier",
        "old_text",
        "new_text",
        "reviewer",
        "review_date",
        "review_source_sha256",
    }
    if not rows or set(rows[0]) != required:
        raise RuntimeError("Reviewer correction ledger schema changed")
    corrections = [ReviewerCorrection(**row) for row in rows]
    keys = [(item.record_id, item.tier) for item in corrections]
    if len(keys) != len(set(keys)):
        raise RuntimeError("Reviewer correction ledger keys are not unique")
    tier_counts = Counter(item.tier for item in corrections)
    if tier_counts != EXPECTED_REVIEWER_CORRECTIONS:
        raise RuntimeError(
            "Reviewer correction inventory changed: expected "
            f"{EXPECTED_REVIEWER_CORRECTIONS}, found {tier_counts}"
        )
    if any(
        item.review_source_sha256 != EXPECTED_REVIEW_SOURCE_SHA256
        for item in corrections
    ):
        raise RuntimeError("Reviewer correction source hash changed")
    if any(item.reviewer != "Madeline Boese" for item in corrections):
        raise RuntimeError("Reviewer correction attribution changed")
    if any(item.review_date != "2026-08-06" for item in corrections):
        raise RuntimeError("Reviewer correction date changed")
    return corrections


def apply_reviewer_corrections(
    records: list[Record],
) -> tuple[list[Record], list[ReviewerCorrection]]:
    corrections = read_reviewer_corrections()
    by_record: dict[str, list[ReviewerCorrection]] = {}
    for correction in corrections:
        by_record.setdefault(correction.record_id, []).append(correction)
    record_ids = {record.record_id for record in records}
    unknown = sorted(set(by_record) - record_ids)
    if unknown:
        raise RuntimeError(
            f"Reviewer corrections reference unknown records: {unknown}"
        )

    corrected: list[Record] = []
    tier_fields = {
        "original": "form",
        "standard": "standard",
        "translation": "translation",
    }
    for record in records:
        values = {
            "form": record.form,
            "standard": record.standard,
            "translation": record.translation,
        }
        for correction in by_record.get(record.record_id, []):
            field = tier_fields.get(correction.tier)
            if field is None:
                raise RuntimeError(
                    f"Unsupported reviewer tier: {correction.tier!r}"
                )
            if values[field] != correction.old_text:
                raise RuntimeError(
                    "Reviewer correction baseline changed for "
                    f"{record.record_id} {correction.tier}"
                )
            values[field] = correction.new_text
        corrected.append(
            replace(
                record,
                form=values["form"],
                standard=values["standard"],
                translation=values["translation"],
            )
        )
    return corrected, corrections


def split_qa_record(record: Record) -> tuple[Record, Record]:
    source_question = re.compile(r"^(?:Chachod|Cha)\.\s*(?:C\.\s*)?", re.I)
    source_answer = re.compile(r"\b(?:Tattaam|Tatt)\.\s*", re.I)
    english_question = re.compile(r"^(?:Question|Q)\.\s*", re.I)
    english_answer = re.compile(r"\b(?:Answer|A)\.\s*", re.I)
    question_form, answer_form = split_dialogue_text(
        record.form,
        opening_label=source_question,
        response_label=source_answer,
    )
    question_standard, answer_standard = split_dialogue_text(
        record.standard,
        opening_label=source_question,
        response_label=source_answer,
    )
    question_translation, answer_translation = split_dialogue_text(
        record.translation,
        opening_label=english_question,
        response_label=english_answer,
    )
    return (
        replace(
            record,
            record_id=f"{record.record_id}_question",
            part="qa_turn",
            label=f"{record.label}_question",
            form=question_form,
            standard=question_standard,
            translation=question_translation,
            notes="Question turn split at printed Q/A labels; labels omitted",
        ),
        replace(
            record,
            record_id=f"{record.record_id}_answer",
            part="qa_turn",
            label=f"{record.label}_answer",
            form=answer_form,
            standard=answer_standard,
            translation=answer_translation,
            notes="Answer turn split at printed Q/A labels; labels omitted",
        ),
    )


def sentence_units(text: str) -> list[str]:
    units = re.split(r"(?<=[.!?])\s+", text.strip())
    joined: list[str] = []
    index = 0
    while index < len(units):
        unit = units[index]
        if unit == "Jac." and index + 1 < len(units):
            unit = f"{unit} {units[index + 1]}"
            index += 1
        joined.append(unit)
        index += 1
    if not joined or any(not unit for unit in joined):
        raise RuntimeError("Sermon sentence splitter emitted an empty unit")
    if " ".join(joined) != text.strip():
        raise RuntimeError("Sermon sentence splitter changed source text")
    return joined


def restructure_reviewed_units(
    records: list[Record],
) -> tuple[list[Record], list[RecordSplit]]:
    restructured: list[Record] = []
    splits: list[RecordSplit] = []
    for record in records:
        if record.part == "qa_pair":
            children = split_qa_record(record)
            for ordinal, child in enumerate(children, start=1):
                restructured.append(child)
                splits.append(
                    RecordSplit(
                        record.record_id,
                        child.record_id,
                        "qa_turn",
                        ordinal,
                    )
                )
            continue
        if record.part == "sermon":
            original_units = sentence_units(record.form)
            standard_units = sentence_units(record.standard)
            expected = EXPECTED_SERMON_SENTENCES.get(record.record_id)
            if expected is None or len(original_units) != expected:
                raise RuntimeError(
                    f"Unexpected sermon sentence count for {record.record_id}: "
                    f"{len(original_units)}"
                )
            if len(standard_units) != len(original_units):
                raise RuntimeError(
                    f"Sermon FORM tier boundary mismatch for {record.record_id}"
                )
            for ordinal, (form, standard) in enumerate(
                zip(original_units, standard_units, strict=True),
                start=1,
            ):
                child = replace(
                    record,
                    record_id=(
                        f"{record.record_id}_sentence_{ordinal:03d}"
                    ),
                    part="sermon_sentence",
                    label=f"sentence_{ordinal:03d}",
                    form=form,
                    standard=standard,
                    notes=(
                        "Source-only sermon sentence split at printed "
                        "sentence-final punctuation"
                    ),
                )
                restructured.append(child)
                splits.append(
                    RecordSplit(
                        record.record_id,
                        child.record_id,
                        "sermon_sentence",
                        ordinal,
                    )
                )
            continue
        restructured.append(record)

    part_counts = Counter(record.part for record in restructured)
    if part_counts != EXPECTED_FINAL_PART_COUNTS:
        raise RuntimeError(
            "Final record inventory changed: expected "
            f"{EXPECTED_FINAL_PART_COUNTS}, found {part_counts}"
        )
    ids = [record.record_id for record in restructured]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Restructured record IDs are not unique")
    if any(
        re.search(r"[^\W\d_]-[^\W\d_]", record.standard, re.UNICODE)
        for record in restructured
    ):
        raise RuntimeError("Alphabetic hyphen remains in a reviewed standard FORM")
    return restructured, splits


def read_sermon_review() -> list[SermonReview]:
    with SERMON_REVIEW_TSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    required = {
        "decision", "reviewed_id", "baseline_ids", "baseline_sha256", "form",
        "reason", "reviewer", "review_date", "review_source_sha256",
    }
    if not rows or set(rows[0]) != required:
        raise RuntimeError("Sermon review ledger schema changed")
    reviews = [
        SermonReview(
            row["decision"],
            row["reviewed_id"],
            tuple(row["baseline_ids"].split(",")),
            row["baseline_sha256"],
            row["form"],
            row["reason"],
            row["reviewer"],
            row["review_date"],
            row["review_source_sha256"],
        )
        for row in rows
    ]
    if Counter(item.decision for item in reviews) != Counter(
        {"accepted": 684, "excluded": 1}
    ):
        raise RuntimeError("Sermon review decision inventory changed")
    reviewed_ids = [item.reviewed_id for item in reviews if item.reviewed_id]
    baseline_ids = [item for review in reviews for item in review.baseline_ids]
    if len(reviewed_ids) != 684 or len(set(reviewed_ids)) != 684:
        raise RuntimeError("Sermon review IDs are missing or duplicated")
    if len(baseline_ids) != 687 or len(set(baseline_ids)) != 687:
        raise RuntimeError("Sermon review baseline coverage changed")
    if any(
        item.reviewer != "Madeline Boese"
        or item.review_date != "2026-08-12"
        or item.review_source_sha256 != EXPECTED_SERMON_REVIEW_SOURCE_SHA256
        for item in reviews
    ):
        raise RuntimeError("Sermon review provenance changed")
    if any(item.decision == "accepted" and not item.form for item in reviews):
        raise RuntimeError("Accepted sermon review row lacks source text")
    if any(
        item.decision == "excluded" and (item.reviewed_id or item.form)
        for item in reviews
    ):
        raise RuntimeError("Excluded sermon review row emits corpus content")
    return reviews


def apply_sermon_review(
    records: list[Record], splits: list[RecordSplit]
) -> tuple[list[Record], list[RecordSplit], list[SermonReview]]:
    reviews = read_sermon_review()
    sermon_by_id = {
        record.record_id: record
        for record in records
        if record.part == "sermon_sentence"
    }
    reviewed_by_baseline: dict[str, SermonReview] = {}
    for review in reviews:
        try:
            baseline_records = [sermon_by_id[item] for item in review.baseline_ids]
        except KeyError as error:
            raise RuntimeError(
                f"Sermon review references unknown baseline {error.args[0]}"
            ) from error
        baseline_text = "\n".join(item.form for item in baseline_records)
        if hashlib.sha256(baseline_text.encode("utf-8")).hexdigest() != (
            review.baseline_sha256
        ):
            raise RuntimeError(
                f"Sermon review baseline changed for {review.baseline_ids}"
            )
        if len({item.section for item in baseline_records}) != 1:
            raise RuntimeError("A sermon review row crosses section boundaries")
        reviewed_by_baseline.update(
            {baseline_id: review for baseline_id in review.baseline_ids}
        )
    if set(reviewed_by_baseline) != set(sermon_by_id):
        raise RuntimeError("Sermon review does not cover every baseline sentence")

    reviewed_records: list[Record] = []
    for record in records:
        if record.part != "sermon_sentence":
            reviewed_records.append(record)
            continue
        review = reviewed_by_baseline[record.record_id]
        if record.record_id != review.baseline_ids[0] or review.decision == "excluded":
            continue
        merged = [sermon_by_id[item] for item in review.baseline_ids]
        reviewed_records.append(
            replace(
                merged[0],
                record_id=review.reviewed_id,
                label=review.reviewed_id.split("_sermon_", 1)[-1],
                printed_page_start=min(item.printed_page_start for item in merged),
                printed_page_end=max(item.printed_page_end for item in merged),
                pdf_object_page_start=min(
                    item.pdf_object_page_start for item in merged
                ),
                pdf_object_page_end=max(item.pdf_object_page_end for item in merged),
                form=review.form,
                standard="",
                notes=review.reason,
            )
        )

    reviewed_splits = [item for item in splits if item.split_kind != "sermon_sentence"]
    ordinals: Counter[str] = Counter()
    for review in reviews:
        if review.decision != "accepted":
            continue
        match = re.fullmatch(r"(.+)_sentence_\d{3}", review.baseline_ids[0])
        if match is None:
            raise RuntimeError(f"Unexpected sermon baseline ID: {review.baseline_ids[0]}")
        parent_id = match.group(1)
        ordinals[parent_id] += 1
        reviewed_splits.append(
            RecordSplit(
                parent_id,
                review.reviewed_id,
                "sermon_sentence",
                ordinals[parent_id],
            )
        )

    if Counter(record.part for record in reviewed_records) != (
        EXPECTED_REVIEWED_FINAL_PART_COUNTS
    ):
        raise RuntimeError("Reviewed record inventory changed")
    ids = [record.record_id for record in reviewed_records]
    if len(ids) != len(set(ids)):
        raise RuntimeError("Reviewed record IDs are not unique")
    return reviewed_records, reviewed_splits, reviews


def apply_policy_normalization(records: list[Record]) -> list[Record]:
    return [
        replace(
            record,
            form=canonicalize_policy_text(record.form),
            standard=canonicalize_policy_text(record.standard),
            translation=canonicalize_policy_text(record.translation),
        )
        for record in records
    ]


def write_accepted(records: list[Record]) -> None:
    ACCEPTED_TSV.parent.mkdir(parents=True, exist_ok=True)
    with ACCEPTED_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "record_id",
                "section",
                "section_title",
                "part",
                "label",
                "printed_page_start",
                "printed_page_end",
                "pdf_object_page_start",
                "pdf_object_page_end",
                "has_translation",
                "form_chars",
                "standard_chars",
                "translation_chars",
                "notes",
                "translation",
                "form",
                "standard",
            ]
        )
        for record in records:
            writer.writerow(
                [
                    record.record_id,
                    record.section,
                    record.section_title,
                    record.part,
                    record.label,
                    record.printed_page_start,
                    record.printed_page_end,
                    record.pdf_object_page_start,
                    record.pdf_object_page_end,
                    bool(record.translation),
                    len(record.form),
                    len(record.standard),
                    len(record.translation),
                    record.notes,
                    record.translation,
                    record.form,
                    record.standard,
                ]
            )


def load_accepted(path: Path = ACCEPTED_TSV) -> list[Record]:
    """Load the reviewed extraction ledger for source-free reproduction."""
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    records = [
        Record(
            record_id=row["record_id"],
            section=int(row["section"]),
            section_title=row["section_title"],
            part=row["part"],
            label=row["label"],
            printed_page_start=int(row["printed_page_start"]),
            printed_page_end=int(row["printed_page_end"]),
            pdf_object_page_start=int(row["pdf_object_page_start"]),
            pdf_object_page_end=int(row["pdf_object_page_end"]),
            form=row["form"],
            translation=row["translation"],
            notes=row["notes"],
            standard=row["standard"],
        )
        for row in rows
    ]
    if len(records) != 1049 or len({record.record_id for record in records}) != 1049:
        raise ValueError("reviewed extraction ledger inventory changed")
    for row, record in zip(rows, records, strict=True):
        if row["has_translation"] != str(bool(record.translation)):
            raise ValueError(f"{record.record_id}: translation flag changed")
        if int(row["form_chars"]) != len(record.form):
            raise ValueError(f"{record.record_id}: form length changed")
        if int(row["translation_chars"]) != len(record.translation):
            raise ValueError(f"{record.record_id}: translation length changed")
    return records


def write_record_splits(splits: list[RecordSplit]) -> None:
    with RECORD_SPLITS_TSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["parent_id", "child_id", "split_kind", "ordinal"])
        for split in splits:
            writer.writerow(
                [
                    split.parent_id,
                    split.child_id,
                    split.split_kind,
                    split.ordinal,
                ]
            )


def write_source_corrections(
    corrections: list[AppliedCorrection],
) -> None:
    with SOURCE_CORRECTIONS_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(
            [
                "record_id",
                "printed_page_start",
                "printed_page_end",
                "tier",
                "old_text",
                "new_text",
                "reason",
            ]
        )
        for correction in corrections:
            writer.writerow(
                [
                    correction.record_id,
                    correction.printed_page_start,
                    correction.printed_page_end,
                    correction.tier,
                    correction.old,
                    correction.new,
                    correction.reason,
                ]
            )


def write_rejected() -> None:
    rows = [
        (
            "front_matter",
            "PDF title page through table of contents",
            "not corpus text",
        ),
        (
            "sek_hoan_specimen",
            "printed page 102",
            "separate specimen, not the Favorlang Christian Instruction corpus",
        ),
        (
            "psalmanazar_dialogue",
            "printed pages 103-121",
            (
                "separate dialogue attributed to Psalmanazar, not treated as "
                "Favorlang Christian Instruction"
            ),
        ),
        (
            "happart_vocabulary",
            "printed pages 122-199",
            "lexical vocabulary rather than sentence/chunk text",
        ),
        (
            "appendices_and_indexes",
            "material after vocabulary",
            "not target text for this extraction",
        ),
    ]
    with REJECTED_TSV.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["section_id", "source_range", "reason"])
        writer.writerows(rows)


def write_xml(records: list[Record]) -> None:
    XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element(
        "TEXT",
        {
            "id": TEXT_ID,
            f"{{{XML_NS}}}lang": "bzg",
            "source": SOURCE_DESC,
            "dialect": "Favorlang",
            "copyright": COPYRIGHT,
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
        },
    )
    for record in records:
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": record.record_id,
                "source": record.source_attr,
            },
        )
        form = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        form.text = record.form
        if record.translation:
            translation = ET.SubElement(
                sentence,
                "TRANSL",
                {f"{{{XML_NS}}}lang": "eng"},
            )
            translation.text = record.translation

    tree = ET.ElementTree(root)
    ET.indent(tree, space="    ")
    tree.write(XML_PATH, encoding="UTF-8", xml_declaration=True)


def write_summary(
    records: list[Record],
    corrections: list[AppliedCorrection],
    diplomatic_corrections: int,
    reviewer_corrections: list[ReviewerCorrection],
    sermon_reviews: list[SermonReview],
    splits: list[RecordSplit],
) -> None:
    part_counts = Counter(record.part for record in records)
    translated = sum(bool(record.translation) for record in records)
    source_only = len(records) - translated
    total_form_chars = sum(len(record.form) for record in records)
    total_translation_chars = sum(len(record.translation) for record in records)
    lines = [
        "# Extraction Summary",
        "",
        f"Accepted logical XML records: {len(records)}",
        f"Records with English translation: {translated}",
        f"Source-only sermon records: {source_only}",
        f"Total extracted Favorlang characters: {total_form_chars}",
        f"Total extracted English translation characters: {total_translation_chars}",
        f"Source-backed corrections applied: {len(corrections)}",
        f"Diplomatic diacritic restorations applied: {diplomatic_corrections}",
        f"Reviewer tier corrections applied: {len(reviewer_corrections)}",
        f"Sermon review decisions applied: {len(sermon_reviews)}",
        f"Split child records emitted: {len(splits)}",
        "",
        "## Logical Record Counts",
        "",
        "| Record type | Count |",
        "| --- | ---: |",
    ]
    for part, count in sorted(part_counts.items()):
        lines.append(f"| {part} | {count} |")
    lines.extend(
        [
            "",
            "## Source Range",
            "",
            "- Printed sections I-XIV: Favorlang text with Campbell's English translation.",
            "- Printed sections XV-XIX: five source-only Favorlang sermons.",
            "- Physical page continuations are joined before XML is emitted.",
            "- Long sections use printed item numbers or question labels as secondary boundaries.",
            "- Section XII question/answer pairs are emitted as separate turns.",
            "- Sections XV-XIX are split at sentence-final punctuation.",
            "",
            "## Excluded Sections",
            "",
            "- Front matter and table of contents.",
            "- Printed page 102 Sek-hoan specimen.",
            "- Printed pages 103-121 Psalmanazar dialogue.",
            "- Printed pages 122-199 Happart Favorlang vocabulary.",
            "- Later appendices/index material.",
            "",
            "## Outputs",
            "",
            f"- XML: `{XML_PATH.relative_to(ROOT)}`",
            f"- Accepted audit TSV: `{ACCEPTED_TSV.relative_to(ROOT)}`",
            f"- Rejected section TSV: `{REJECTED_TSV.relative_to(ROOT)}`",
            f"- Source correction TSV: `{SOURCE_CORRECTIONS_TSV.relative_to(ROOT)}`",
            f"- Diplomatic diacritic TSV: `{DIPLOMATIC_DIACRITICS_TSV.relative_to(ROOT)}`",
            f"- Reviewer correction TSV: `{REVIEWER_CORRECTIONS_TSV.relative_to(ROOT)}`",
            f"- Sermon review TSV: `{SERMON_REVIEW_TSV.relative_to(ROOT)}`",
            f"- Record split TSV: `{RECORD_SPLITS_TSV.relative_to(ROOT)}`",
        ]
    )
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_baseline_records() -> tuple[
    list[Record],
    list[AppliedCorrection],
    int,
]:
    records, corrections = apply_source_corrections(collect_records())
    records, diplomatic_corrections = apply_diplomatic_corrections(records)
    records, post_corrections = apply_post_source_corrections(records)
    corrections.extend(post_corrections)
    records, translation_corrections = apply_translation_corrections(records)
    corrections.extend(translation_corrections)
    records = restructure_records(records)
    records = assign_standard_surfaces(records)
    return records, corrections, diplomatic_corrections


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-ledger",
        action="store_true",
        help="render XML from tracked reviewed records without private sources",
    )
    args = parser.parse_args()
    if args.from_ledger:
        records = load_accepted()
        write_xml(records)
        print(f"Wrote {len(records)} reviewed records to {XML_PATH}")
        return

    records, corrections, diplomatic_corrections = build_baseline_records()
    records, reviewer_corrections = apply_reviewer_corrections(records)
    records, post_review_corrections = apply_translation_corrections(
        records, POST_REVIEW_TRANSLATION_CORRECTIONS
    )
    corrections.extend(post_review_corrections)
    records, splits = restructure_reviewed_units(records)
    records, splits, sermon_reviews = apply_sermon_review(records, splits)
    records = apply_policy_normalization(records)
    write_accepted(records)
    write_record_splits(splits)
    write_source_corrections(corrections)
    write_rejected()
    write_xml(records)
    write_summary(
        records,
        corrections,
        diplomatic_corrections,
        reviewer_corrections,
        sermon_reviews,
        splits,
    )
    print(f"Wrote {len(records)} logical records to {XML_PATH}")
    print(
        "Wrote audit tables to "
        f"{ACCEPTED_TSV}, {SOURCE_CORRECTIONS_TSV}, and {REJECTED_TSV}"
    )
    print(
        f"Applied {diplomatic_corrections} source-backed diplomatic "
        "diacritic restorations"
    )


if __name__ == "__main__":
    main()
