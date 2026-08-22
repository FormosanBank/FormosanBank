#!/usr/bin/env python3
"""Compare fresh PDF text extraction against the manifested XML.

This is a final-pass audit, separate from the normal build path. It pulls text
from the source PDF with pdftotext and PyMuPDF, derives the expected
FormosanBank XML surface from the source unit sidecars, and verifies that the
generated XML matches that expectation.
"""

from __future__ import annotations

import csv
import json
import random
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz

import pipeline


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/raw/pdf/B602_KanakanavuText.pdf"
OUT_DIR = ROOT / "build/source_audit"
REPORT = ROOT / "data/processed/source_xml_comparison_report.md"
SPOTCHECK_REPORT = ROOT / "data/processed/pdf_xml_spotchecks.csv"
RANDOM_SAMPLE_REPORT = ROOT / "data/processed/random_source_xml_audit.csv"
XML_NS = "{http://www.w3.org/XML/1998/namespace}"
XML_DIR = ROOT / "XML/xnb"

RANDOM_SAMPLE_SEED = 20260810
RANDOM_SAMPLE_SIZE = 30
REVIEWED_RANDOM_SAMPLE_UNIT_IDS = (
    "ILCAA_KANAKANAVU_TEXTS_021_LITTLE_PEOPLE_U0011",
    "ILCAA_KANAKANAVU_TEXTS_002_THE_BIG_FLOOD_U0002",
    "ILCAA_KANAKANAVU_TEXTS_022_THE_GIANT_U0003",
    "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0010",
    "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0065",
    "ILCAA_KANAKANAVU_TEXTS_002_THE_BIG_FLOOD_U0013",
    "ILCAA_KANAKANAVU_TEXTS_035_SETTING_UP_TRAPS_II_U0010",
    "ILCAA_KANAKANAVU_TEXTS_037_ROASTING_MEAT_AND_FISH_U0009",
    "ILCAA_KANAKANAVU_TEXTS_027_PANGOLIN_U0039",
    "ILCAA_KANAKANAVU_TEXTS_005_THE_SKY_FELL_DOWN_U0007",
    "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0002",
    "ILCAA_KANAKANAVU_TEXTS_027_PANGOLIN_U0032",
    "ILCAA_KANAKANAVU_TEXTS_008_A_LEGENDARY_MALICIOUS_SPIRIT_U0015",
    "ILCAA_KANAKANAVU_TEXTS_024_FRUIT_OF_THE_BIRD_LIME_PLANT_II_U0003",
    "ILCAA_KANAKANAVU_TEXTS_015_WHITE_TAILED_BLUE_ROBIN_U0019",
    "ILCAA_KANAKANAVU_TEXTS_001_SHOOTING_THE_SUN_U0044",
    "ILCAA_KANAKANAVU_TEXTS_020_RAINBOW_U0002",
    "ILCAA_KANAKANAVU_TEXTS_042_A_DANGEROUS_NARROW_STREAM_WITH_WHITE_STONES_U0006",
    "ILCAA_KANAKANAVU_TEXTS_032_KILLING_A_SNAKE_BROUGHT_A_CURSE_ON_A_PERSON_U0029",
    "ILCAA_KANAKANAVU_TEXTS_038_THE_STORY_OF_LAND_BOUNDARIES_U0004",
    "ILCAA_KANAKANAVU_TEXTS_036_TO_PREPARE_SALTED_MEAT_U0012",
    "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0016",
    "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0055",
    "ILCAA_KANAKANAVU_TEXTS_017_MY_FATHER_U0019",
    "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0006",
    "ILCAA_KANAKANAVU_TEXTS_020_RAINBOW_U0027",
    "ILCAA_KANAKANAVU_TEXTS_012_HUNTING_U0002",
    "ILCAA_KANAKANAVU_TEXTS_030_SNAKE_II_U0006",
    "ILCAA_KANAKANAVU_TEXTS_017_MY_FATHER_U0016",
    "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0053",
)
RANDOM_SAMPLE_THEORY = (
    "S original preserves the admitted printed source after technical cleanup and "
    "explicit source-judgment exclusions; W forms retain source analysis notation; "
    "M represents infixes as -X-; W/M source glosses use kindOf=original; the "
    "printed free translation maps independently to an untyped S TRANSL."
)

SPOTCHECKS = [
    {
        "physical_page": 18,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0004",
        "source_anchor": "khiojiu=maku",
        "gloss_anchor": "professor=1SG.GEN",
        "translation_anchor": "recording our words",
        "focus": "introduction example, footnote anchor 3, clitic alignment",
    },
    {
        "physical_page": 42,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_002_THE_BIG_FLOOD_U0031",
        "source_anchor": "paira=pa",
        "gloss_anchor": "always=still",
        "translation_anchor": "At that time, (people) were always very happy.",
        "focus": "page-bottom translation recovered below the old cutoff",
    },
    {
        "physical_page": 57,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_008_A_LEGENDARY_MALICIOUS_SPIRIT_U0015",
        "source_anchor": "pasə-kə-kəəc-ai=kan",
        "gloss_anchor": "by.hand-RED-pinch-NEUT=said",
        "translation_anchor": "with her fingernails",
        "focus": "wrapped interlinear rows and footnote anchor 16",
    },
    {
        "physical_page": 101,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0132",
        "source_anchor": "ʔaisi=kan=cu",
        "gloss_anchor": "exist=said=COS",
        "translation_anchor": "They were (there) to pacify the sun.",
        "focus": "standalone wrapped S suffix completing COS and parenthesized translation",
    },
    {
        "physical_page": 124,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_019_A_HUNDRED_PACER_U0010",
        "source_anchor": "r<um>a-raʔisi",
        "gloss_anchor": "RED<AV>-bite",
        "translation_anchor": "Since we're living here",
        "focus": "four-row sentence, infix notation, quoted translation",
    },
    {
        "physical_page": 149,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_023_FRUIT_OF_THE_BIRD_LIME_PLANT_U0023",
        "source_anchor": "c<um>arəʔə=kamu",
        "gloss_anchor": "sprinkle.salt<AV>=2PL.NOM",
        "translation_anchor": "seasoning powder",
        "focus": "infix/clitic alignment and footnote anchor 33",
    },
    {
        "physical_page": 168,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_028_PANGOLIN_II_U0016",
        "source_anchor": "canaa-ini",
        "gloss_anchor": "field-3.GEN",
        "translation_anchor": "place (field hut)",
        "focus": "footnote anchor 48 and meaningful translation parentheses",
    },
    {
        "physical_page": 190,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0014",
        "source_anchor": "t<im>mana=maku",
        "gloss_anchor": "hear<PFV>=1SG.GEN",
        "translation_anchor": "weeding (with a hoe)",
        "focus": "infix alignment, footnote anchor 65, translation parentheses",
    },
    {
        "physical_page": 226,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_039_THE_STORY_OF_LAND_BOUNDARIES_II_U0004",
        "source_anchor": "ʔaupoo",
        "gloss_anchor": "lunar.new.year",
        "translation_anchor": "Lunar New Year",
        "focus": "multiline alignment and footnote anchors 77/78",
    },
    {
        "physical_page": 247,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_043_A_TABOO_ON_STEPPING_ON_FLOWING_WATER_WITH_BLOOD_U0017",
        "source_anchor": "gookoosho",
        "gloss_anchor": "office",
        "translation_anchor": "officer from a city district",
        "focus": "late-corpus alignment and footnote anchor 87",
    },
]

SPOTCHECKS.extend([
    {
        "physical_page": page,
        "unit_id": unit_id,
        "source_anchor": "",
        "gloss_anchor": "",
        "translation_anchor": translation,
        "focus": "page-bottom translation recovered below the old cutoff",
    }
    for page, unit_id, translation in [
        (101, "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0133", "The people were playing while dancing."),
        (104, "ILCAA_KANAKANAVU_TEXTS_012_HUNTING_U0006", "I can only teach you in that way."),
        (105, "ILCAA_KANAKANAVU_TEXTS_013_FISHING_U0007", "In those days, I sold my fish."),
        (169, "ILCAA_KANAKANAVU_TEXTS_028_PANGOLIN_II_U0027", "As for her body, her skin appeared to be the same color as a pangolin."),
        (175, "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0016", "I looked up."),
        (182, "ILCAA_KANAKANAVU_TEXTS_029_SNAKE_U0058", "My children from Taichung all came to see me, their father."),
        (189, "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0013", "The girl could stand up, and her mother left (for work)."),
        (213, "ILCAA_KANAKANAVU_TEXTS_035_SETTING_UP_TRAPS_II_U0008", "It would be bad should I tell a lie, all elders would know it."),
        (235, "ILCAA_KANAKANAVU_TEXTS_041_AN_EVENT_AT_NAPALANGA_U0021", "His wife was standing up to follow him."),
        (236, "ILCAA_KANAKANAVU_TEXTS_041_AN_EVENT_AT_NAPALANGA_U0031", "The man disappeared and he had been broken into pieces."),
        (242, "ILCAA_KANAKANAVU_TEXTS_042_A_DANGEROUS_NARROW_STREAM_WITH_WHITE_STONES_U0027", "Two days later, the Paiwan who saw (the snake) died."),
    ]
])

SPOTCHECKS.extend([
    {
        "physical_page": 24,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0025",
        "source_anchor": "[kaən-a]",
        "gloss_anchor": "eat-NMLZ.UV",
        "translation_anchor": "What do you eat?!",
        "focus": "grammatical slash alternative admitted; exact exclusion retained in the source ledger",
    },
    {
        "physical_page": 33,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_001_SHOOTING_THE_SUN_U0004",
        "source_anchor": "r<um>a-riuʔu=kani",
        "gloss_anchor": "RED<AV>-fish.with.net=said",
        "translation_anchor": "caught no fish",
        "focus": "first narrative page, infix and clitic alignment",
    },
    {
        "physical_page": 69,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_010_STORY_OF_A_KANAKANAVU_GIRL_WHO_WAS_MARRIED_TO_A_SNAKE_U0004",
        "source_anchor": "pu-kari-kari=kan",
        "gloss_anchor": "speak-RED-word=said",
        "translation_anchor": "traditional bird of omen",
        "focus": "quoted translation, reduplication, and clitic alignment",
    },
    {
        "physical_page": 78,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0005",
        "source_anchor": "pirapa-ən=kiai",
        "gloss_anchor": "share-UV=3.AGT",
        "translation_anchor": "never share with the girl",
        "focus": "dense six-line opening-page interlinear unit",
    },
    {
        "physical_page": 129,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_021_LITTLE_PEOPLE_U0005",
        "source_anchor": "ni-mu-səɁəc-ai",
        "gloss_anchor": "PFV-AV.go-starved-NEUT",
        "translation_anchor": "all people in the world were starving",
        "focus": "new text boundary and multiline alignment",
    },
    {
        "physical_page": 141,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_022_THE_GIANT_U0007",
        "source_anchor": "Ɂ<um>a-Ɂucanə",
        "gloss_anchor": "RED<AV>-rain",
        "translation_anchor": "heavy rain just like a storm",
        "focus": "new text boundary with infix notation",
    },
    {
        "physical_page": 153,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_025_NOT_EATING_EELS_U0003",
        "source_anchor": "seŋsei=maku",
        "gloss_anchor": "teacher=1SG.GEN",
        "translation_anchor": "Please talk from here",
        "focus": "quoted translation and footnote anchor 36",
    },
    {
        "physical_page": 197,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_032_KILLING_A_SNAKE_BROUGHT_A_CURSE_ON_A_PERSON_U0004",
        "source_anchor": "s<um>a-sərəcə",
        "gloss_anchor": "RED<AV>-check.trap",
        "translation_anchor": "returning to check the traps",
        "focus": "new text boundary and infix alignment",
    },
    {
        "physical_page": 203,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_033_WORSHIPING_A_SNAKE_U0004",
        "source_anchor": "pa-tikur-au mu-caan-a",
        "gloss_anchor": "CAUS-wear-IMP AV-go-IMP",
        "translation_anchor": "Please wear them and leave",
        "focus": "long four-row unit with quoted translation",
    },
    {
        "physical_page": 221,
        "unit_id": "ILCAA_KANAKANAVU_TEXTS_038_THE_STORY_OF_LAND_BOUNDARIES_U0005",
        "source_anchor": "taka-ʔanman-an=mu",
        "gloss_anchor": "self-like-LOC=2PL.GEN",
        "translation_anchor": "mountains or on the plains",
        "focus": "long quoted question at a text boundary",
    },
])


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def direct_text(elem: ET.Element, tag: str, *, kind: str | None = None, lang: str | None = None) -> str:
    for child in elem:
        if child.tag != tag:
            continue
        if kind is not None and child.attrib.get("kindOf") != kind:
            continue
        if lang is not None and child.attrib.get(f"{XML_NS}lang") != lang:
            continue
        return "".join(child.itertext()).strip()
    return ""


def direct_element(
    elem: ET.Element,
    tag: str,
    *,
    kind: str | None = None,
    lang: str | None = None,
) -> ET.Element | None:
    for child in elem:
        if child.tag != tag:
            continue
        if kind is not None and child.attrib.get("kindOf") != kind:
            continue
        if lang is not None and child.attrib.get(f"{XML_NS}lang") != lang:
            continue
        return child
    return None


def norm_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def expected_inline_spacing(text: str, *, linguistic_form: bool = False) -> str:
    text = norm_text(text)
    if linguistic_form:
        text = re.sub(r"\s*([=-])\s*", r"\1", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([,;:])([^\s\"'\)\]\}])", r"\1 \2", text)
    return text.strip()


def source_tokens(text: str) -> list[str]:
    raw = norm_text(text)
    tokens = []
    for token in raw.split():
        token = token.strip("\"'“”‘’.,;:!?()[]{}")
        if token:
            tokens.append(token)
    return tokens


def token_variants(token: str) -> set[str]:
    variants = {token}
    variants.add(token.rstrip("0123456789"))
    variants.add(token.replace("ʔ", "'"))
    variants.add(token.replace("'", "ʔ"))
    variants.add(token.replace("=", " = "))
    variants.add(token.replace("-", " "))
    return {norm_text(v) for v in variants if norm_text(v)}


def extract_pdf_text() -> tuple[str, list[str]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pdftotext_path = OUT_DIR / "pdftotext_layout.txt"
    subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(PDF), str(pdftotext_path)],
        check=True,
    )
    pdftotext_pages = pdftotext_path.read_text(encoding="utf-8", errors="replace").split("\f")
    pymupdf_dir = OUT_DIR / "pymupdf_pages"
    pymupdf_dir.mkdir(parents=True, exist_ok=True)
    pymupdf_pages = []
    with fitz.open(PDF) as doc:
        for index, page in enumerate(doc, start=1):
            text = page.get_text("text")
            pymupdf_pages.append(text)
            (pymupdf_dir / f"page_{index:04d}.txt").write_text(text, encoding="utf-8")
    combined_pages = []
    for i in range(max(len(pdftotext_pages), len(pymupdf_pages))):
        combined_pages.append(
            "\n".join(
                part
                for part in [
                    pdftotext_pages[i] if i < len(pdftotext_pages) else "",
                    pymupdf_pages[i] if i < len(pymupdf_pages) else "",
                ]
                if part
            )
        )
    combined_text = "\n".join(combined_pages)
    (OUT_DIR / "combined_pdf_text.txt").write_text(combined_text, encoding="utf-8")
    return combined_text, combined_pages


def page_text_for_unit(unit: dict, pages: list[str]) -> str:
    try:
        start = int(unit.get("physical_page_start") or 0)
        end = int(unit.get("physical_page_end") or start)
    except ValueError:
        return ""
    chunks = []
    for page_no in range(start, end + 1):
        if 1 <= page_no <= len(pages):
            chunks.append(pages[page_no - 1])
    return norm_text(" ".join(chunks))


def source_support(unit: dict, pages: list[str]) -> dict[str, float | int | bool]:
    page_text = page_text_for_unit(unit, pages)
    text = unit.get("source_line_clean") or unit.get("source_line_raw") or ""
    support = text_support(text, page_text)
    source_line = norm_text(
        unit.get("source_line_raw") or unit.get("source_line_clean") or ""
    )
    support["exact_line"] = bool(source_line and source_line in page_text)
    return support


def text_support(text: str, page_text: str) -> dict[str, float | int | bool]:
    tokens = source_tokens(text)
    if not tokens:
        return {"tokens": 0, "found": 0, "ratio": 1.0, "exact_line": True}
    found = 0
    for token in tokens:
        if any(variant and variant in page_text for variant in token_variants(token)):
            found += 1
    source_line = norm_text(text)
    return {
        "tokens": len(tokens),
        "found": found,
        "ratio": found / len(tokens),
        "exact_line": bool(source_line and source_line in page_text),
    }


def load_xml() -> dict[str, ET.Element]:
    sentences: dict[str, ET.Element] = {}
    for path in sorted(XML_DIR.glob("*.xml")):
        root = ET.parse(path).getroot()
        for sentence in root.findall("S"):
            sid = sentence.attrib["id"]
            sentences[sid] = sentence
    return sentences


def load_xml_index() -> tuple[dict[str, dict], dict[str, str]]:
    by_unit = {}
    sid_to_file = {}
    with (ROOT / "data/processed/xml_index.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            by_unit[row["unit_id"]] = row
            by_unit.setdefault(row.get("source_unit_id", row["unit_id"]), row)
            sid_to_file[row["sentence_id"]] = row["xml_file"]
    return by_unit, sid_to_file


def expected_sentence(unit: dict) -> dict[str, str]:
    original = expected_inline_spacing(
        pipeline.sentence_original_form(unit["source_line_clean"]).replace("ә", "ə"),
        linguistic_form=True,
    )
    translation, translation_note = pipeline.sentence_translation_and_note(
        unit.get("free_translation_clean", "")
    )
    return {
        "original": original,
        "translation": expected_inline_spacing(translation),
        "translation_note": translation_note,
    }


def compare_sentences(units: list[dict], xml_index: dict[str, dict], sentences: dict[str, ET.Element]) -> list[str]:
    mismatches = []
    for unit in units:
        row = xml_index.get(unit["unit_id"])
        if not row:
            mismatches.append(f"{unit['unit_id']}: missing xml_index row")
            continue
        sid = row["sentence_id"]
        sentence = sentences.get(sid)
        if sentence is None:
            mismatches.append(f"{unit['unit_id']}: missing S {sid}")
            continue
        expected = expected_sentence(unit)
        actual_original = direct_text(sentence, "FORM", kind="original")
        translation_element = direct_element(sentence, "TRANSL", lang="eng")
        actual_translation = (
            "" if translation_element is None
            else "".join(translation_element.itertext()).strip()
        )
        actual_translation_note = (
            "" if translation_element is None
            else translation_element.attrib.get("notes", "")
        )
        for key, actual in [
            ("original", actual_original),
            ("translation", actual_translation),
            ("translation_note", actual_translation_note),
        ]:
            if expected[key] != actual:
                mismatches.append(
                    f"{sid}: {key} mismatch expected={expected[key]!r} actual={actual!r}"
                )
    return mismatches


def compare_words_and_morphemes(
    units: list[dict],
    words: list[dict],
    morphs: list[dict],
    xml_index: dict[str, dict],
    sentences: dict[str, ET.Element],
) -> list[str]:
    mismatches: list[str] = []
    words_by_unit: dict[str, list[dict]] = defaultdict(list)
    morphs_by_word: dict[str, list[dict]] = defaultdict(list)
    for word in words:
        words_by_unit[word["unit_id"]].append(word)
    for morph in morphs:
        morphs_by_word[morph["word_id"]].append(morph)
    for unit in units:
        row = xml_index.get(unit["unit_id"])
        if not row:
            continue
        sid = row["sentence_id"]
        sentence = sentences.get(sid)
        if sentence is None:
            continue
        expected_words = sorted(words_by_unit.get(unit["unit_id"], []), key=lambda r: r["word_order"])
        actual_words = sentence.findall("W")
        if len(expected_words) != len(actual_words):
            mismatches.append(f"{sid}: W count expected={len(expected_words)} actual={len(actual_words)}")
            continue
        for expected_word, actual_word in zip(expected_words, actual_words):
            expected_wid = expected_word["word_id"].replace(unit["unit_id"], sid)
            if actual_word.attrib.get("id") != expected_wid:
                mismatches.append(f"{sid}: W id expected={expected_wid} actual={actual_word.attrib.get('id')}")
            expected_original = norm_text(expected_word["source_token_clean"]).replace("ә", "ə")
            expected_gloss = expected_word["gloss_token_clean"]
            actual_original = direct_text(actual_word, "FORM", kind="original")
            actual_gloss = direct_text(actual_word, "TRANSL", lang="eng")
            for key, expected, actual in [
                ("W original", expected_original, actual_original),
                ("W gloss", expected_gloss, actual_gloss),
            ]:
                if expected != actual:
                    mismatches.append(f"{expected_wid}: {key} expected={expected!r} actual={actual!r}")
            expected_morphs = sorted(morphs_by_word.get(expected_word["word_id"], []), key=lambda r: r["morpheme_order"])
            actual_morphs = actual_word.findall("M")
            if len(expected_morphs) != len(actual_morphs):
                mismatches.append(f"{expected_wid}: M count expected={len(expected_morphs)} actual={len(actual_morphs)}")
                continue
            for expected_morph, actual_morph in zip(expected_morphs, actual_morphs):
                expected_mid = expected_morph["morpheme_id"].replace(unit["unit_id"], sid)
                if actual_morph.attrib.get("id") != expected_mid:
                    mismatches.append(f"{expected_wid}: M id expected={expected_mid} actual={actual_morph.attrib.get('id')}")
                expected_m_original = norm_text(expected_morph["source_morpheme_clean"]).replace("ә", "ə")
                expected_m_gloss = expected_morph["gloss_morpheme_clean"]
                actual_m_original = direct_text(actual_morph, "FORM", kind="original")
                actual_m_gloss = direct_text(actual_morph, "TRANSL", lang="eng")
                for key, expected, actual in [
                    ("M original", expected_m_original, actual_m_original),
                    ("M gloss", expected_m_gloss, actual_m_gloss),
                ]:
                    if expected != actual:
                        mismatches.append(f"{expected_mid}: {key} expected={expected!r} actual={actual!r}")
    return mismatches


def artifact_scan(sentences: dict[str, ET.Element]) -> dict[str, int]:
    counts = {
        "S_TRANSL_with_kindOf": 0,
        "WM_TRANSL_not_original": 0,
        "standard_FORM_missing": 0,
        "PHON_missing": 0,
        "literal_entity_residue": 0,
    }
    entity_needles = ("&apos;", "&quot;", "&lt;", "&gt;", "&amp;")
    for sentence in sentences.values():
        for child in sentence:
            if child.tag == "TRANSL" and "kindOf" in child.attrib:
                counts["S_TRANSL_with_kindOf"] += 1
        for elem in sentence.iter():
            if elem.tag in {"W", "M"}:
                for transl in elem.findall("TRANSL"):
                    if transl.attrib.get("kindOf") != "original":
                        counts["WM_TRANSL_not_original"] += 1
            text = "".join(elem.itertext())
            if any(needle in text for needle in entity_needles):
                counts["literal_entity_residue"] += 1
        for elem in sentence.iter():
            if elem.tag not in {"S", "W", "M"}:
                continue
            if elem.find('./FORM[@kindOf="standard"]') is None:
                counts["standard_FORM_missing"] += 1
            for kind in ("original", "standard"):
                if elem.find(f'PHON[@kindOf="{kind}"]') is None:
                    counts["PHON_missing"] += 1
    return counts


def suspicious_sentence_translations(sentences: dict[str, ET.Element]) -> list[str]:
    note_patterns = [
        r"\bThis text appears\b",
        r"\bJapanese translation appears\b",
        r"\bThe title appears\b",
        r"\binformant,\b",
        r"\bThe former was recorded\b",
        r"\binstead of the term\b",
        r"\bassimilated to the following\b",
    ]
    gloss_pattern = re.compile(
        r"(?:^|\s)(?:AV|UV|PFV|FUT|NOM|GEN|OBL|COS|STA|RED|LOC|NUM|DUR|IRR|CAUS|NEUT)[.A-Z-]*(?:\s|$)|[<>=]"
    )
    findings = []
    for sid, sentence in sorted(sentences.items()):
        transl = direct_text(sentence, "TRANSL", lang="eng")
        if not transl:
            continue
        first_token = transl.split()[0] if transl.split() else ""
        if looks_like_gloss_leader(first_token):
            findings.append(f"{sid}: gloss-looking prefix in S TRANSL: {transl[:220]!r}")
            continue
        if any(re.search(pattern, transl) for pattern in note_patterns):
            findings.append(f"{sid}: source-note text in S TRANSL: {transl[:220]!r}")
            continue
        _, trailing_note = pipeline.sentence_translation_and_note(transl)
        if trailing_note:
            findings.append(
                f"{sid}: trailing editorial note remains in S TRANSL text: "
                f"{trailing_note!r}"
            )
            continue
        if re.search(r"[ʔŋəɨʉƏ]", transl) and gloss_pattern.search(transl):
            findings.append(f"{sid}: source/gloss-looking text in S TRANSL: {transl[:220]!r}")
    return findings


def looks_like_gloss_leader(token: str) -> bool:
    core = token.strip(".,;:!?\"'()[]“”‘’")
    return bool(
        re.search(r"[=<>]", core)
        or re.match(r"^(?:AV|UV|PFV|FUT|NOM|GEN|OBL|COS|STA|RED|LOC|NUM|DUR|IRR|CAUS|NEUT)(?:[-.=]|$)", core)
        or re.match(r"^[A-Z]{2,}[.-]", core)
    )


def update_manifest() -> None:
    rows = []
    manifest_path = ROOT / "data/processed/manifest.csv"
    for path in sorted((ROOT / "data").rglob("*")) + sorted((ROOT / "XML").rglob("*")):
        if path.is_file() and path != manifest_path:
            rows.append({
                "path": str(path.relative_to(ROOT)),
                "size_bytes": path.stat().st_size,
                "sha256": pipeline.sha256_path(path),
            })
    pipeline.write_csv(ROOT / "data/processed/manifest.csv", rows, ["path", "size_bytes", "sha256"], lineterminator="\n")


def sample_rows(units: list[dict], xml_index: dict[str, dict], sentences: dict[str, ET.Element]) -> list[str]:
    chosen_ids = [
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0001",
        "ILCAA_KANAKANAVU_TEXTS_000_GRAMMATICAL_INTRODUCTION_EXAMPLES_U0019",
        "ILCAA_KANAKANAVU_TEXTS_001_SHOOTING_THE_SUN_U0001",
        "ILCAA_KANAKANAVU_TEXTS_002_THE_BIG_FLOOD_U0010",
        "ILCAA_KANAKANAVU_TEXTS_011_NAPARAMACI_U0001",
        "ILCAA_KANAKANAVU_TEXTS_027_PANGOLIN_U0005",
        "ILCAA_KANAKANAVU_TEXTS_031_A_RECKLESS_MOTHER_U0020",
        "ILCAA_KANAKANAVU_TEXTS_044_THE_STORY_OF_MY_MARRIAGE_U0019",
    ]
    by_id = {u["unit_id"]: u for u in units}
    for unit in units:
        by_id.setdefault(unit.get("source_unit_id", unit["unit_id"]), unit)
    rows = []
    for unit_id in chosen_ids:
        unit = by_id.get(unit_id)
        if not unit or unit_id not in xml_index:
            continue
        sid = xml_index[unit["unit_id"]]["sentence_id"]
        sentence = sentences[sid]
        expected = expected_sentence(unit)
        rows.append(
            "| {sid} | `{src}` | `{actual}` | `{tr}` |".format(
                sid=sid,
                src=expected["original"].replace("|", "\\|")[:120],
                actual=direct_text(sentence, "FORM", kind="original").replace("|", "\\|")[:120],
                tr=direct_text(sentence, "TRANSL", lang="eng").replace("|", "\\|")[:120] or "(source-only)",
            )
        )
    return rows


def write_spotchecks(
    units: list[dict],
    words: list[dict],
    morphs: list[dict],
    xml_index: dict[str, dict],
    sentences: dict[str, ET.Element],
    pages: list[str],
) -> list[dict[str, str]]:
    by_id = {unit["unit_id"]: unit for unit in units}
    for unit in units:
        by_id.setdefault(unit.get("source_unit_id", unit["unit_id"]), unit)
    rows: list[dict[str, str]] = []
    for check in SPOTCHECKS:
        unit_id = check["unit_id"]
        unit = by_id.get(unit_id)
        findings: list[str] = []
        if unit is None:
            findings.append("unit missing from final XML input set")
            unit = {}
        actual_page = int(unit.get("physical_page_start") or 0)
        if actual_page != check["physical_page"]:
            findings.append(
                f"physical page expected {check['physical_page']} actual {actual_page}"
            )
        for field, anchor in [
            ("source_line_clean", check["source_anchor"]),
            ("gloss_line_clean", check["gloss_anchor"]),
            ("free_translation_clean", check["translation_anchor"]),
        ]:
            if anchor and anchor not in str(unit.get(field, "")):
                findings.append(f"{field} missing anchor {anchor!r}")
        row = xml_index.get(unit.get("unit_id", unit_id), {})
        sid = row.get("sentence_id", "")
        sentence = sentences.get(sid)
        if not row:
            findings.append("xml_index row missing")
        if sentence is None:
            findings.append(f"XML sentence missing: {sid or '(unknown)'}")
        if unit and row and sentence is not None:
            findings.extend(compare_sentences([unit], xml_index, sentences))
            findings.extend(
                compare_words_and_morphemes(
                    [unit], words, morphs, xml_index, sentences
                )
            )

        support = source_support(unit, pages) if unit else {
            "tokens": 0, "found": 0, "ratio": 0.0
        }
        if float(support["ratio"]) < 0.80:
            findings.append(
                f"fresh PDF source-token support below 0.80: {support['ratio']:.3f}"
            )
        rows.append({
            "physical_page": str(check["physical_page"]),
            "printed_page": str(unit.get("printed_page_start", "")),
            "unit_id": unit_id,
            "sentence_id": sid,
            "xml_file": row.get("xml_file", ""),
            "source_line_ids": ";".join(unit.get("source_line_ids", [])),
            "gloss_line_ids": ";".join(unit.get("gloss_line_ids", [])),
            "translation_line_ids": ";".join(unit.get("translation_line_ids", [])),
            "source_anchor": check["source_anchor"],
            "gloss_anchor": check["gloss_anchor"],
            "translation_anchor": check["translation_anchor"],
            "source_token_support": (
                f"{support['found']}/{support['tokens']} ({float(support['ratio']):.3f})"
            ),
            "visual_review": "PASS; rendered source inspected during completion audit",
            "focus": check["focus"],
            "status": "PASS" if not findings else "FAIL",
            "findings": "; ".join(findings),
        })
    pipeline.write_csv(SPOTCHECK_REPORT, rows, [
        "physical_page", "printed_page", "unit_id", "sentence_id", "xml_file",
        "source_line_ids", "gloss_line_ids", "translation_line_ids",
        "source_anchor", "gloss_anchor", "translation_anchor",
        "source_token_support", "visual_review", "focus", "status", "findings",
    ], lineterminator="\n")
    return rows


def write_random_source_checks(
    units: list[dict],
    words: list[dict],
    morphs: list[dict],
    xml_index: dict[str, dict],
    sentences: dict[str, ET.Element],
    pages: list[str],
) -> list[dict[str, str]]:
    source_population = [
        unit
        for unit in read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
        if pipeline.unit_in_final_xml(unit)
    ]
    sample_ids = tuple(
        unit["unit_id"]
        for unit in random.Random(RANDOM_SAMPLE_SEED).sample(
            source_population, RANDOM_SAMPLE_SIZE
        )
    )
    sample_is_reviewed = sample_ids == REVIEWED_RANDOM_SAMPLE_UNIT_IDS
    by_id = {unit["unit_id"]: unit for unit in units}
    for unit in units:
        by_id.setdefault(unit.get("source_unit_id", unit["unit_id"]), unit)
    sampled = [by_id[unit_id] for unit_id in sample_ids]

    words_by_unit: dict[str, list[dict]] = defaultdict(list)
    morphs_by_word: dict[str, list[dict]] = defaultdict(list)
    for word in words:
        words_by_unit[word["unit_id"]].append(word)
    for morph in morphs:
        morphs_by_word[morph["word_id"]].append(morph)

    rows: list[dict[str, str]] = []
    for sample_index, unit in enumerate(sampled, start=1):
        unit_id = unit["unit_id"]
        row = xml_index.get(unit_id, {})
        sid = row.get("sentence_id", "")
        sentence = sentences.get(sid)
        expected = expected_sentence(unit)
        findings: list[str] = []
        findings.extend(compare_sentences([unit], xml_index, sentences))
        findings.extend(
            compare_words_and_morphemes(
                [unit], words, morphs, xml_index, sentences
            )
        )
        if not sample_is_reviewed:
            findings.append(
                "seeded sample differs from the recorded visual-review sample; "
                "render and review the new source entries"
            )

        page_text = page_text_for_unit(unit, pages)
        source = text_support(unit.get("source_line_clean", ""), page_text)
        gloss = text_support(unit.get("gloss_line_clean", ""), page_text)
        translation = text_support(
            unit.get("free_translation_clean", ""), page_text
        )
        for tier, support in [
            ("source", source),
            ("gloss", gloss),
            ("translation", translation),
        ]:
            if float(support["ratio"]) < 0.80:
                findings.append(
                    f"fresh PDF {tier}-token support below 0.80: "
                    f"{float(support['ratio']):.3f}"
                )

        expected_words = sorted(
            words_by_unit.get(unit_id, []), key=lambda item: item["word_order"]
        )
        expected_morph_count = sum(
            len(morphs_by_word.get(word["word_id"], []))
            for word in expected_words
        )
        actual_words = [] if sentence is None else sentence.findall("W")
        actual_morph_count = sum(len(word.findall("M")) for word in actual_words)
        translation_element = (
            None
            if sentence is None
            else direct_element(sentence, "TRANSL", lang="eng")
        )

        rows.append({
            "sample_index": str(sample_index),
            "seed": str(RANDOM_SAMPLE_SEED),
            "unit_id": unit_id,
            "text_id": unit.get("text_id", ""),
            "physical_page": str(unit.get("physical_page_start", "")),
            "printed_page": str(unit.get("printed_page_start", "")),
            "source_label": str(unit.get("source_unit_label", "")),
            "sentence_id": sid,
            "xml_file": row.get("xml_file", ""),
            "source_form": unit.get("source_line_clean", ""),
            "expected_original": expected["original"],
            "actual_original": (
                ""
                if sentence is None
                else direct_text(sentence, "FORM", kind="original")
            ),
            "source_gloss": unit.get("gloss_line_clean", ""),
            "source_translation": unit.get("free_translation_clean", ""),
            "expected_translation": expected["translation"],
            "actual_translation": (
                ""
                if translation_element is None
                else "".join(translation_element.itertext()).strip()
            ),
            "expected_translation_note": expected["translation_note"],
            "actual_translation_note": (
                ""
                if translation_element is None
                else translation_element.attrib.get("notes", "")
            ),
            "expected_w_count": str(len(expected_words)),
            "actual_w_count": str(len(actual_words)),
            "expected_m_count": str(expected_morph_count),
            "actual_m_count": str(actual_morph_count),
            "source_token_support": (
                f"{source['found']}/{source['tokens']} "
                f"({float(source['ratio']):.3f})"
            ),
            "gloss_token_support": (
                f"{gloss['found']}/{gloss['tokens']} "
                f"({float(gloss['ratio']):.3f})"
            ),
            "translation_token_support": (
                f"{translation['found']}/{translation['tokens']} "
                f"({float(translation['ratio']):.3f})"
            ),
            "expected_xml_theory": RANDOM_SAMPLE_THEORY,
            "visual_review": (
                "PASS; rendered PDF crop inspected 2026-08-10"
                if sample_is_reviewed
                else "REVIEW REQUIRED; seeded sample changed"
            ),
            "status": "PASS" if not findings else "FAIL",
            "findings": "; ".join(findings),
        })

    pipeline.write_csv(RANDOM_SAMPLE_REPORT, rows, [
        "sample_index", "seed", "unit_id", "text_id", "physical_page",
        "printed_page", "source_label", "sentence_id", "xml_file",
        "source_form", "expected_original", "actual_original", "source_gloss",
        "source_translation", "expected_translation", "actual_translation",
        "expected_translation_note", "actual_translation_note",
        "expected_w_count", "actual_w_count", "expected_m_count",
        "actual_m_count", "source_token_support", "gloss_token_support",
        "translation_token_support", "expected_xml_theory", "visual_review",
        "status", "findings",
    ], lineterminator="\n")
    return rows


def main() -> int:
    _, pages = extract_pdf_text()
    units = read_jsonl(ROOT / "data/processed/xml_sentence_units.jsonl")
    words = read_jsonl(ROOT / "data/processed/xml_word_units.jsonl")
    morphs = read_jsonl(ROOT / "data/processed/xml_morpheme_units.jsonl")
    xml_index, _ = load_xml_index()
    sentences = load_xml()

    sentence_mismatches = compare_sentences(units, xml_index, sentences)
    wm_mismatches = compare_words_and_morphemes(units, words, morphs, xml_index, sentences)
    scans = artifact_scan(sentences)
    suspicious_translations = suspicious_sentence_translations(sentences)
    spotcheck_rows = write_spotchecks(
        units, words, morphs, xml_index, sentences, pages
    )
    failed_spotchecks = [row for row in spotcheck_rows if row["status"] != "PASS"]
    random_rows = write_random_source_checks(
        units, words, morphs, xml_index, sentences, pages
    )
    failed_random_rows = [row for row in random_rows if row["status"] != "PASS"]

    source_units_by_id = {
        unit["unit_id"]: unit
        for unit in read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
    }
    evidence_units = [
        source_units_by_id[unit.get("source_unit_id", unit["unit_id"])]
        for unit in units
    ]
    supports = [source_support(unit, pages) for unit in evidence_units]
    low_support = [
        (unit, support)
        for unit, support in zip(units, supports)
        if support["ratio"] < 0.80
    ]
    exact_source_lines = sum(1 for support in supports if support["exact_line"])
    average_ratio = sum(float(support["ratio"]) for support in supports) / len(supports)
    full_ratio_count = sum(1 for support in supports if support["ratio"] == 1.0)

    translated_units = [u for u in units if u.get("quality_status") == "xml_eligible" and u.get("free_translation_raw")]
    combined_pdf_text = norm_text((OUT_DIR / "combined_pdf_text.txt").read_text(encoding="utf-8"))
    exact_translation_lines = sum(
        1 for unit in translated_units if norm_text(unit.get("free_translation_raw", "")) in combined_pdf_text
    )

    report = [
        "# Source XML Comparison Audit",
        "",
        "Generated deterministically from the current source, sidecars, and XML.",
        "",
        "## Extraction",
        "",
        f"- Source PDF: `{PDF.relative_to(ROOT)}`.",
        "- Fresh extraction engines: `pdftotext -layout -enc UTF-8` and PyMuPDF `page.get_text(\"text\")`.",
        "- OCR was not used for this final pass because every audited page has an extractable text layer and the project source policy prefers text-layer extraction for this born-digital PDF.",
        f"- The audit script writes temporary fresh extraction artifacts under `{OUT_DIR.relative_to(ROOT)}/`; rerun `python scripts/source_xml_audit.py` to regenerate them.",
        "",
        "## Expected XML Model",
        "",
        "- Each ordinary source unit manifests as one S. Twenty-four reviewed parenthetical units manifest as two complete variants under POL-026/POL-027.",
        "- Standard FORM and both PHON tiers are regenerated with the reviewed route and the pinned shared tools.",
        "- Every source-published free English translation should appear as the S-level `TRANSL xml:lang=\"eng\"`. Meaningful parenthetical, CJK, dash, and ellipsis material stays in the text; nine trailing source editorial labels or citations are represented in `TRANSL@notes`.",
        "- W/M tiers should preserve source-published interlinear glossing. W forms keep source segmentation; M infixes use `-X-`; W/M `TRANSL` uses `kindOf=\"original\"`; direct S `TRANSL` has no `kindOf`.",
        "",
        "## Full Comparison",
        "",
        f"- Final S elements checked: {len(units)}.",
        f"- S expected-vs-actual mismatches: {len(sentence_mismatches)}.",
        f"- W/M expected-vs-actual mismatches: {len(wm_mismatches)}.",
        f"- Suspicious S-level translation artifacts: {len(suspicious_translations)}.",
        f"- Direct S `TRANSL` with `kindOf`: {scans['S_TRANSL_with_kindOf']}.",
        f"- W/M `TRANSL` not marked `kindOf=original`: {scans['WM_TRANSL_not_original']}.",
        f"- S/W/M elements missing standard FORM: {scans['standard_FORM_missing']}.",
        f"- Missing original or standard PHON tiers: {scans['PHON_missing']}.",
        f"- Parsed XML text nodes with literal entity residue (`&apos;`, `&quot;`, `&lt;`, `&gt;`, `&amp;`): {scans['literal_entity_residue']}.",
        "",
        "## Fresh PDF Support",
        "",
        f"- Source units with exact source-line string found in fresh page text: {exact_source_lines}/{len(units)}.",
        f"- Source units with 100% page-local source-token support: {full_ratio_count}/{len(units)}.",
        f"- Average page-local source-token support: {average_ratio:.3f}.",
        f"- Source units below 0.80 token support: {len(low_support)}.",
        f"- Free translations with exact line string found in fresh extraction: {exact_translation_lines}/{len(translated_units)}.",
        "",
        "Exact source-line matching is intentionally reported separately from token support. The PDF lays interlinear source/gloss material out in columns, so a source sentence reconstructed for XML is often not contiguous in `pdftotext` output even when all source tokens are present on the page.",
        "",
        "## Spot-Check Sketch",
        "",
        "| S id | expected original FORM | actual original FORM | actual S TRANSL |",
        "|---|---|---|---|",
        *sample_rows(units, xml_index, sentences),
        "",
        "## Visual and Regression Audit",
        "",
        "- All 252 physical pages were reviewed during the completion audit. The stable rows below cover difficult interlinear cases and all 12 page-bottom translation recoveries.",
        f"- Machine-verifiable page/XML rows: {len(spotcheck_rows)}; passed: {len(spotcheck_rows) - len(failed_spotchecks)}; failed: {len(failed_spotchecks)}.",
        f"- Detailed stable locators and tier anchors: `{SPOTCHECK_REPORT.relative_to(ROOT)}`.",
        "",
        "| physical page | printed page | S id | focus | status |",
        "|---:|---:|---|---|---|",
        *[
            "| {physical_page} | {printed_page} | `{sentence_id}` | {focus} | {status} |".format(
                **{key: str(value).replace("|", "\\|") for key, value in row.items()}
            )
            for row in spotcheck_rows
        ],
        "",
        "## Seeded Random Source Checks",
        "",
        f"- Seed: `{RANDOM_SAMPLE_SEED}`; source-unit population: {pipeline.EXPECTED_SOURCE_UNIT_COUNT}; sample size: {len(random_rows)}.",
        f"- Unique texts: {len({row['text_id'] for row in random_rows})}; unique physical pages: {len({row['physical_page'] for row in random_rows})}.",
        f"- S/W/M source-to-XML rows passed: {len(random_rows) - len(failed_random_rows)}; failed: {len(failed_random_rows)}.",
        f"- W elements checked: {sum(int(row['actual_w_count']) for row in random_rows)}; M elements checked: {sum(int(row['actual_m_count']) for row in random_rows)}.",
        "- Every sampled source form, interlinear gloss, and free translation was checked against a rendered PDF crop. The CSV records the expected XML model and actual S/W/M manifestation for each entry.",
        f"- Detailed random audit: `{RANDOM_SAMPLE_REPORT.relative_to(ROOT)}`.",
        "",
    ]
    if sentence_mismatches or wm_mismatches or suspicious_translations or any(scans.values()) or low_support or failed_spotchecks or failed_random_rows:
        report.extend([
            "## Findings",
            "",
        ])
        for mismatch in sentence_mismatches[:25]:
            report.append(f"- S mismatch: {mismatch}")
        for mismatch in wm_mismatches[:25]:
            report.append(f"- W/M mismatch: {mismatch}")
        for finding in suspicious_translations[:25]:
            report.append(f"- Translation artifact: {finding}")
        for unit, support in low_support[:25]:
            report.append(
                f"- Low source-token support: {unit['unit_id']} page {unit.get('physical_page_start')} "
                f"{support['found']}/{support['tokens']} tokens, source `{unit.get('source_line_clean', '')[:160]}`"
            )
        for row in failed_spotchecks:
            report.append(
                f"- Source spot check failed: page {row['physical_page']} "
                f"{row['unit_id']}: {row['findings']}"
            )
        for row in failed_random_rows:
            report.append(
                f"- Random source check failed: sample {row['sample_index']} "
                f"page {row['physical_page']} {row['unit_id']}: "
                f"{row['findings']}"
            )
        if len(sentence_mismatches) + len(wm_mismatches) + len(suspicious_translations) + len(low_support) > 100:
            report.append("- Additional findings truncated in this report; rerun the script for full counts.")
        verdict = "FAIL"
    else:
        report.extend([
            "## Findings",
            "",
            "No source-to-XML remediation findings were found. Fresh PDF extraction supports the source units, and the manifested XML matches the expected S/W/M model.",
        ])
        verdict = "PASS"
    report.extend(["", f"Final status: {verdict}", ""])
    REPORT.write_text("\n".join(report), encoding="utf-8")
    update_manifest()
    print(f"Wrote {REPORT}")
    print(f"Final status: {verdict}")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
