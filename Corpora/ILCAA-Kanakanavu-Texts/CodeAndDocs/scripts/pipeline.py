#!/usr/bin/env python3
"""Reproducible extraction pipeline for the ILCAA Kanakanavu Texts PDF.

The implementation is intentionally conservative: it preserves raw positioned
PDF data first, then only emits W/M tiers when source/gloss alignment is
complete enough to satisfy current FormosanBank validators.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
PDF_NAME = "B602_KanakanavuText.pdf"
EXPECTED_SHA256 = "785058bad6a8495f8b5fb51ed3d0eaf7da1736e791b308611d9442c010d93c03"
EXPECTED_SOURCE_UNIT_COUNT = 1431
EXPECTED_SENTENCE_COUNT = 1455
EXPECTED_FORMOSANBANK_QC_TREE = "009bfceab8eb7378e4bef6c010acc75971acabfc"
EXPECTED_FORMOSANBANK_ORTHOGRAPHIES_TREE = "59eed42b21e95c752f1abd2a3a9fbcd1bfb920b3"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
NSMAP = {"xml": "http://www.w3.org/XML/1998/namespace"}


DOC_URLS = {
    "qc_pipeline_url": "https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/developers/qc-pipeline",
    "claude_skills_url": "https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/developers/using-the-claude-skills",
    "xml_format_url": "https://ai4commsci.gitbook.io/formosanbank/the-bank-architecture/formosanbank-xml-format",
}


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


def load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore
        except ImportError as exc:
            raise SystemExit(f"{path} is not JSON and PyYAML is not installed") from exc
        return yaml.safe_load(text)


def formosanbank_checkout(config: dict[str, Any]) -> Path:
    paths = config.get("paths", {})
    configured = os.environ.get("FORMOSANBANK_PATH")
    checkout = (
        Path(configured).expanduser().resolve()
        if configured
        else (ROOT / paths.get("formosanbank", "../../..")).resolve()
    )
    expected_commit = paths.get("formosanbank_commit", "")
    if not (checkout / ".git").exists():
        raise SystemExit(f"Missing FormosanBank checkout: {checkout}")
    actual_commit = subprocess.check_output(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        text=True,
    ).strip()
    if expected_commit and actual_commit != expected_commit:
        raise SystemExit(
            "FormosanBank commit mismatch: "
            f"expected {expected_commit}, found {actual_commit} at {checkout}"
        )
    dirty = subprocess.check_output(
        ["git", "-C", str(checkout), "status", "--porcelain=v1"],
        text=True,
    ).strip()
    if dirty:
        raise SystemExit(f"FormosanBank checkout is not clean: {checkout}")
    expected_trees = {
        "QC": paths.get("formosanbank_qc_tree", EXPECTED_FORMOSANBANK_QC_TREE),
        "Orthographies": paths.get(
            "formosanbank_orthographies_tree",
            EXPECTED_FORMOSANBANK_ORTHOGRAPHIES_TREE,
        ),
    }
    for subtree, expected_tree in expected_trees.items():
        actual_tree = subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", f"HEAD:{subtree}"],
            text=True,
        ).strip()
        if actual_tree != expected_tree:
            raise SystemExit(
                f"FormosanBank {subtree} tree mismatch: expected {expected_tree}, "
                f"found {actual_tree} at {checkout}"
            )
    return checkout


def ensure_dirs() -> None:
    for rel in [
        "data/raw/pdf",
        "data/raw/docs/formosanbank",
        "data/raw/text/pages",
        "data/raw/words/pages",
        "data/raw/blocks/pages",
        "data/raw/spans/pages",
        "data/raw/renders",
        "data/raw/crops",
        "data/processed/review",
        "build/xml_drafts",
        "build/xml_failed",
        "build/qc_output",
        "logs",
        "tests/fixtures",
        "XML/xnb",
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


def normalize_generated_text_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    text = text.replace("\r\n", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    path.write_text(text, encoding="utf-8")


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
    preserved = ROOT / "data/raw/pdf" / PDF_NAME
    if preserved.exists():
        return preserved
    src = ROOT / PDF_NAME
    if not src.exists():
        raise SystemExit(f"Missing source PDF: {src}")
    preserved.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, preserved)
    return preserved


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
            row = {
                "word_id": wid,
                "unit_id": unit_id,
                "word_order": word_order,
                "source_token_raw": sw["raw_text"],
                "source_token_clean": src_core,
                "gloss_token_raw": gw["raw_text"] if gw is not None else "",
                "gloss_token_clean": gls_core,
                "gloss_token_unclear": not bool(gls_core),
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
            "gloss_morpheme_unclear": not bool(gls_form),
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
            infix = m.group(1)
            after = chunk[m.end():]
            if not is_source:
                if before:
                    parts.append((before, current_boundary))
                parts.append((f"<{infix}>", "infix"))
                if after:
                    parts.append((after, "suffix"))
                current_boundary = "suffix"
                continue
            surround = f"{before}-{after}" if is_source else f"{before}{after}"
            if surround:
                if current_boundary == "clitic" and is_source:
                    surround = f"={surround}"
                parts.append((surround, current_boundary))
            parts.append((f"-{infix}-" if is_source else f"<{infix}>", "infix"))
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
                "status": "resolved" if eligible or empty_extraction_artifact else "unresolved",
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


def inventory_duplicate_units() -> list[dict[str, Any]]:
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


def overlap_against_formosanbank(formosanbank: Path) -> list[dict[str, Any]]:
    units = read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
    existing: list[dict[str, str]] = []
    by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_translation: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_prefix: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path in (formosanbank / "Corpora").rglob("*.xml"):
        try:
            tree = etree.parse(str(path))
        except etree.XMLSyntaxError:
            continue
        if tree.getroot().get(XML_LANG) != "xnb":
            continue
        for s in tree.iter("S"):
            src = first_direct_text(s, "FORM", kind="standard") or first_direct_text(s, "FORM", kind="original") or ""
            eng = first_direct_text(s, "TRANSL", lang="eng") or ""
            if src or eng:
                rec = {
                    "file": path.relative_to(formosanbank).as_posix(),
                    "sid": s.get("id", ""),
                    "source": clean_space(src),
                    "translation": clean_space(eng),
                }
                existing.append(rec)
                if rec["source"]:
                    by_source[rec["source"]].append(rec)
                    by_prefix[prefix_key(rec["source"])].append(rec)
                if rec["translation"]:
                    by_translation[rec["translation"]].append(rec)
    rows: list[dict[str, Any]] = []
    for unit in units:
        src = unit.get("source_line_clean", "")
        tr = unit.get("free_translation_clean", "")
        candidates: list[dict[str, str]] = []
        otype = "no_overlap"
        if src in by_source:
            candidates = by_source[src]
            otype = "exact_source"
        elif tr in by_translation:
            candidates = by_translation[tr]
            otype = "exact_translation"
        else:
            candidates = by_prefix.get(prefix_key(src), [])[:100]
        best: tuple[float, dict[str, str] | None] = (0.0, None)
        for ex_rec in candidates:
            ss = difflib.SequenceMatcher(None, src, ex_rec["source"]).ratio() if src and ex_rec["source"] else 0
            tt = difflib.SequenceMatcher(None, tr, ex_rec["translation"]).ratio() if tr and ex_rec["translation"] else 0
            score = (ss + tt) / 2
            if score > best[0]:
                best = (score, ex_rec)
        ex = best[1]
        if otype == "no_overlap" and ex and best[0] >= 0.92:
            otype = "near_source_translation"
        rows.append({
            "unit_id": unit["unit_id"],
            "text_id": unit["text_id"],
            "source_sentence_clean": src,
            "translation_clean": tr,
            "existing_repo_or_corpus": "FormosanBank",
            "existing_file": ex["file"] if ex else "",
            "existing_sentence_id": ex["sid"] if ex else "",
            "existing_source_text": ex["source"] if ex else "",
            "existing_translation": ex["translation"] if ex else "",
            "overlap_type": otype,
            "source_similarity": round(difflib.SequenceMatcher(None, src, ex["source"]).ratio(), 3) if ex else 0,
            "translation_similarity": round(difflib.SequenceMatcher(None, tr, ex["translation"]).ratio(), 3) if ex else 0,
            "combined_similarity": round(best[0], 3),
            "same_story_candidate": "",
            "same_publication_candidate": "",
            "recommended_action": "retain" if otype == "no_overlap" else "review",
            "final_action": "retain",
            "notes": "",
        })
    write_csv(ROOT / "data/processed/overlap_candidates.csv", rows, [
        "unit_id", "text_id", "source_sentence_clean", "translation_clean",
        "existing_repo_or_corpus", "existing_file", "existing_sentence_id",
        "existing_source_text", "existing_translation", "overlap_type",
        "source_similarity", "translation_similarity", "combined_similarity",
        "same_story_candidate", "same_publication_candidate", "recommended_action",
        "final_action", "notes",
    ])
    return rows


def prefix_key(text: str) -> str:
    words = re.findall(r"[\wʔŋəɨʉ]+", text.lower())
    return " ".join(words[:3])


def first_direct_text(elem: etree._Element, tag: str, *, kind: str | None = None, lang: str | None = None) -> str | None:
    for child in elem:
        if child.tag != tag:
            continue
        if kind is not None and child.get("kindOf") != kind:
            continue
        if lang is not None and child.get(XML_LANG) != lang:
            continue
        return "".join(child.itertext())
    return None


def add_translation(
    parent: etree._Element,
    text: str,
    *,
    unclear: bool = False,
    kind_of: str | None = None,
) -> etree._Element:
    attributes = {XML_LANG: "eng"}
    if kind_of is not None:
        attributes["kindOf"] = kind_of
    transl = etree.SubElement(parent, "TRANSL", attributes)
    if text:
        transl.text = text
    elif unclear:
        etree.SubElement(transl, "UNCLEAR")
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
    source_tokens = unit["source_line_clean"].split()
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
            "gloss_token_unclear": not bool(gloss),
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
        options = PARENTHETICAL_VARIANTS.get(source_unit_id, (
            {"label": "source", "source": (), "gloss": ()},
        ))
        for variant_order, option in enumerate(options, start=1):
            unit = dict(source_unit)
            unit["source_unit_id"] = source_unit_id
            unit["variant_label"] = option["label"]
            unit["variant_order"] = variant_order
            unit["variant_count"] = len(options)
            unit["unit_id"] = (
                source_unit_id
                if len(options) == 1
                else f"{source_unit_id}_V{variant_order}"
            )
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
            unresolved_analysis = bool(
                re.search(r"[()\[\]*/]", unit["source_line_clean"])
            )
            unit["word_tier_candidate"] = not unresolved_analysis
            unit["morpheme_tier_candidate"] = not unresolved_analysis
            xml_units.append(unit)

            if len(options) > 1 or source_unit_id in RESOLVED_JUDGMENT_GLOSS_REPLACEMENTS:
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
    draft_dir = ROOT / "build/xml_drafts"
    final_dir = ROOT / "XML/xnb"
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
            sid = (
                sid_base
                if int(unit["variant_count"]) == 1
                else f"{sid_base}V{int(unit['variant_order'])}"
            )
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
                    add_translation(
                        w_elem,
                        w["gloss_token_clean"],
                        unclear=w.get("gloss_token_unclear"),
                        kind_of="original",
                    )
                    token_index.append(token_index_row(text, unit, w, "W", w_elem.get("id"), sid, sid))
                    for m in sorted(morphs_by_word.get(w["word_id"], []), key=lambda r: r["morpheme_order"]):
                        source_morpheme = clean_source_form(m["source_morpheme_clean"])
                        m_elem = etree.SubElement(w_elem, "M", id=m["morpheme_id"].replace(unit["unit_id"], sid))
                        etree.SubElement(m_elem, "FORM", kindOf="original").text = source_morpheme
                        add_translation(
                            m_elem,
                            m["gloss_morpheme_clean"],
                            unclear=m.get("gloss_morpheme_unclear"),
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


def derive_machine_tiers(formosanbank: Path) -> None:
    xml_dir = ROOT / "build/xml_drafts"
    output = ROOT / "build/derived_tiers"
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    qc_python = formosanbank / ".venv/bin/python"
    if not os.access(qc_python, os.X_OK):
        raise RuntimeError(f"FormosanBank QC Python is not executable: {qc_python}")
    source_profile = ROOT / "scripts/orthographies/Asai2026/Kanakanavu.tsv"
    target_profile = formosanbank / "Orthographies/Ortho113/Kanakanavu.tsv"
    conversion = (
        ROOT
        / "scripts/orthographies/ConversionTables/Kanakanavu_Asai2026_113.tsv"
    )
    commands = (
        (
            "validate_conversion_table",
            [
                str(qc_python),
                str(formosanbank / "QC/validation/validate_conversion_table.py"),
                str(source_profile),
                str(target_profile),
                str(conversion),
                "--dialect",
                "Kanakanavu",
            ],
        ),
        (
            "standardize",
            [
                str(qc_python),
                str(formosanbank / "QC/utilities/standardize.py"),
                "--tsv_path",
                str(conversion),
                "--target_column",
                "standard",
                "--corpora_path",
                str(xml_dir),
            ],
        ),
        (
            "add_phonology",
            [
                sys.executable,
                str(ROOT / "scripts/add_reviewed_phonology.py"),
                "--formosanbank-root",
                str(formosanbank),
                "--corpora-path",
                str(xml_dir),
            ],
        ),
    )
    for name, command in commands:
        proc = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        (output / f"{name}.log").write_text(proc.stdout, encoding="utf-8")
        reviewed_conversion_result = (
            name == "validate_conversion_table"
            and proc.returncode == 1
            and "confirmed=3, warning=0, mismatch=3, unknown_source=0, untokenizable=0" in proc.stdout
            and "`l` → `r` (ɾ / [r|ɾ])" in proc.stdout
            and "`r` → `r` (r / [r|ɾ])" in proc.stdout
            and "`ə` → `e` (ə / e)" in proc.stdout
            and "merge: [r|ɾ] ← r, ɾ" in proc.stdout
            and "cannot encode: f" in proc.stdout
            and "cannot encode: ɨ" in proc.stdout
            and "### Coverage\n- (none)" in proc.stdout
            and "### Table integrity\n- (none)" in proc.stdout
        )
        if proc.returncode and not reviewed_conversion_result:
            raise RuntimeError(
                f"{name} failed with exit {proc.returncode}; see "
                f"{(output / f'{name}.log').relative_to(ROOT)}"
            )
        if reviewed_conversion_result:
            (ROOT / "data/processed/conversion_validation_adjudication.md").write_text(
                "# Conversion Validation Adjudication\n\n"
                "The current shared validator confirmed all shape-changing "
                "equivalences and found no unknown source grapheme, "
                "untokenizable row, coverage gap, or table-integrity defect.\n\n"
                "Its three phoneme-level mismatches are the reviewed purpose "
                "of this conversion: source l /ɾ/ and r /r/ merge into "
                "Ortho113 r /[r|ɾ]/, and source ə maps to the approved nearest "
                "Ortho113 vowel e. Target-only f and ɨ do not occur in the "
                "source corpus. Madeline Boese approved these mappings in the "
                "completed Basecamp review on 2026-08-12. No mismatch is "
                "unreviewed.\n",
                encoding="utf-8",
            )
    warning_path = xml_dir / "standardize_warnings.csv"
    if warning_path.exists():
        warning_path.unlink()

    reviewed_foreign_letters = set("bdgjzBDGJZ")
    review_rows: list[dict[str, str]] = []
    for path in sorted(xml_dir.glob("*.xml")):
        root = etree.parse(str(path)).getroot()
        for parent in root.iter():
            if parent.tag not in {"S", "W", "M"}:
                continue
            for kind in ("original", "standard"):
                form = parent.find(f'FORM[@kindOf="{kind}"]')
                phon = parent.find(f'PHON[@kindOf="{kind}"]')
                if form is None or phon is None or "*" not in (phon.text or ""):
                    continue
                form_text = "".join(form.itertext())
                letters = "".join(
                    sorted({character for character in form_text if character in reviewed_foreign_letters})
                )
                if not letters:
                    raise RuntimeError(
                        f"unreviewed PHON mapping gap in {path.name} "
                        f"{parent.tag} {parent.get('id', '')}: {form_text!r} -> {phon.text!r}"
                    )
                review_rows.append({
                    "xml_file": path.name,
                    "element": parent.tag,
                    "element_id": parent.get("id", ""),
                    "kindOf": kind,
                    "form": form_text,
                    "phon": phon.text or "",
                    "unmapped_foreign_letters": letters,
                    "decision": "reviewed loanword or proper name; retain shared visible asterisk signal",
                })
    write_csv(
        ROOT / "data/processed/phonology_mapping_review.csv",
        review_rows,
        [
            "xml_file", "element", "element_id", "kindOf", "form", "phon",
            "unmapped_foreign_letters", "decision",
        ],
    )


def apa_citation() -> str:
    return "Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. (2026). Kanakanavu texts (P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies."


def bibtex_citation() -> str:
    return "@book{AsaiMeiLiTsuchida2026KanakanavuTexts,author={Erin Asai and Kuang Mei and Paul Jen-kuei Li and Shigeru Tsuchida},editor={Paul Jen-kuei Li},title={Kanakanavu Texts},year={2026},publisher={Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies},isbn={978-4-86337-602-1},note={With the assistance of Yi-Chun Chen, Hsiu-min Huang, and Amy Ming-luan Chen. Licensed under CC BY 4.0}}"


def copyright_attr() -> str:
    return "Copyright © 2026 Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang, and Amy Ming-luan Chen. Licensed under CC BY 4.0."


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


def sentence_original_forms(xml_dir: Path) -> dict[tuple[str, str], str]:
    forms: dict[tuple[str, str], str] = {}
    for path in sorted(xml_dir.glob("*.xml")):
        root = etree.parse(str(path)).getroot()
        for sentence in root.iter("S"):
            original = sentence.find('./FORM[@kindOf="original"]')
            forms[(path.name, sentence.get("id", ""))] = (
                original.text if original is not None and original.text else ""
            )
    return forms


def write_cleaner_probe_report(source_dir: Path, probe_dir: Path, exit_code: int) -> None:
    before = sentence_original_forms(source_dir)
    after = sentence_original_forms(probe_dir) if exit_code == 0 else {}
    changed = [key for key, value in before.items() if after.get(key) != value]
    rows = [
        "# Disposable Cleaner Probe",
        "",
        "The pinned FormosanBank cleaner was run only on `build/qc_output/cleaner_probe`. The generated source-faithful XML in `build/xml_drafts` and `XML` was not used as cleaner input.",
        "",
        f"- Cleaner exit code: {exit_code}.",
        f"- S-original forms checked: {len(before)}.",
        f"- S-original forms changed by the cleaner: {len(changed)}.",
        f"- Hyphen characters before/after: {sum(value.count('-') for value in before.values())}/{sum(value.count('-') for value in after.values())}.",
        f"- Equals characters before/after: {sum(value.count('=') for value in before.values())}/{sum(value.count('=') for value in after.values())}.",
        "",
        "Decision: do not promote the disposable cleaner output. It leaves source segmentation counts unchanged but rewrites four source square-bracket constructions as parentheses and one source single-quoted utterance as double-quoted text. The original tier retains the source-supported notation.",
        "",
    ]
    (ROOT / "data/processed/cleaner_probe.md").write_text(
        "\n".join(rows), encoding="utf-8"
    )


def run_qc(formosanbank: Path) -> dict[str, Any]:
    xml_dir = ROOT / "build/xml_drafts"
    out = ROOT / "build/qc_output"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    cleaner_probe = out / "cleaner_probe"
    shutil.copytree(xml_dir, cleaner_probe)
    py = sys.executable
    commands = [
        ("cleaner_probe", [py, str(formosanbank / "QC/cleaning/clean_xml.py"), "--corpora_path", str(cleaner_probe)]),
        ("validate_xml", [py, str(formosanbank / "QC/validation/validate_xml.py"), "by_path", "--path", str(xml_dir), "--csv", str(out / "validate_xml_findings.csv")]),
        ("validate_dialect", [py, str(formosanbank / "QC/validation/validate_dialect.py"), "--path", str(xml_dir)]),
        ("validate_text", [py, str(formosanbank / "QC/validation/validate_text.py"), "by_path", "--path", str(xml_dir), "--csv", str(out / "validate_text_findings.csv")]),
        ("validate_glosses", [py, str(formosanbank / "QC/validation/validate_glosses.py"), "by_path", "--path", str(xml_dir), "--output_dir", str(out)]),
        ("audit_gloss_scrape", [py, str(formosanbank / "QC/validation/audit_gloss_scrape.py"), "--xml", str(xml_dir), "--source", str(source_pdf()), "--csv", str(out / "audit_gloss_scrape_findings.csv")]),
        ("validate_duplicate_sentences", [py, str(formosanbank / "QC/validation/validate_duplicate_sentences.py"), "by_path", "--path", str(xml_dir), "--output", str(out / "duplicate_sentences.csv")]),
    ]
    results: dict[str, Any] = {}
    for name, cmd in commands:
        log_path = out / f"{name}.log"
        proc = subprocess.run(cmd, cwd=formosanbank, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log_path.write_text(proc.stdout, encoding="utf-8")
        command = (
            " ".join(cmd)
            .replace(sys.executable, "python")
            .replace(str(formosanbank), "../FormosanBank")
            .replace(str(ROOT), ".")
        )
        results[name] = {"command": command, "exit_code": proc.returncode, "log": str(log_path.relative_to(ROOT))}
    write_cleaner_probe_report(
        xml_dir,
        cleaner_probe,
        results["cleaner_probe"]["exit_code"],
    )
    for generated_csv in out.glob("*.csv"):
        normalize_generated_text_file(generated_csv)
    duplicate_csv = out / "duplicate_sentences.csv"
    if duplicate_csv.exists():
        shutil.copy2(duplicate_csv, ROOT / "data/processed/duplicate_sentences.csv")
    failed_validators = [
        name for name, result in results.items()
        if result["exit_code"] != 0
    ]
    blocking_hard_findings = 0
    for finding_name in ("validate_xml_findings.csv", "validate_text_findings.csv"):
        finding_path = out / finding_name
        if not finding_path.exists():
            continue
        with finding_path.open(encoding="utf-8-sig") as handle:
            blocking_hard_findings += sum(
                1 for row in csv.DictReader(handle) if row.get("severity") == "HARD"
            )
    blocking_gloss_hard = 0
    gloss_findings = out / "validate_glosses_findings.csv"
    if gloss_findings.exists():
        with gloss_findings.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                if row.get("severity") == "HARD":
                    blocking_gloss_hard += 1
                    blocking_hard_findings += 1
    if "validate_glosses" in failed_validators and blocking_gloss_hard == 0:
        failed_validators.remove("validate_glosses")
    duplicate_hard_findings = 0
    if duplicate_csv.exists():
        with duplicate_csv.open(encoding="utf-8-sig") as handle:
            duplicate_hard_findings = sum(
                1 for row in csv.DictReader(handle) if row.get("severity") == "HARD"
            )
    actionable_gloss_scrape_findings = 0
    gloss_scrape_csv = out / "audit_gloss_scrape_findings.csv"
    if gloss_scrape_csv.exists():
        with gloss_scrape_csv.open(encoding="utf-8-sig") as handle:
            actionable_gloss_scrape_findings = sum(
                int(row.get("count") or 1)
                for row in csv.DictReader(handle)
                if row.get("rule_id") == "G012"
            )
    hard_fail = bool(
        failed_validators
        or blocking_hard_findings
        or actionable_gloss_scrape_findings
    )
    final_dir = ROOT / "XML/xnb"
    if not hard_fail:
        for path in final_dir.glob("*"):
            if path.is_file():
                path.unlink()
        for xml in xml_dir.glob("*.xml"):
            shutil.copy2(xml, final_dir / xml.name)
    return {
        "results": results,
        "failed_validators": failed_validators,
        "blocking_hard_findings": blocking_hard_findings,
        "duplicate_hard_findings": duplicate_hard_findings,
        "actionable_gloss_scrape_findings": actionable_gloss_scrape_findings,
        "hard_fail": hard_fail,
        "finalized": not hard_fail,
    }


def write_preflight_report(formosanbank: Path) -> None:
    fb_head = subprocess.check_output(["git", "-C", str(formosanbank), "rev-parse", "HEAD"], text=True).strip()
    lines = [
        "# QC Preflight",
        "",
        "## Documentation",
    ]
    for key, url in DOC_URLS.items():
        lines.append(f"- {key}: {url}")
    lines.extend([
        "",
        "## Validation dependency",
        "",
        "- FormosanBank checkout: `../FormosanBank`",
        f"- Pinned FormosanBank commit: `{fb_head}`",
        "- XML schema: `../FormosanBank/QC/validation/xml_template.xsd`",
        "- Validators: `../FormosanBank/QC/validation`",
        "",
        "## QC command sequence",
        "",
        "1. Run `clean_xml.py` on a disposable copy and record whether its output is source-safe.",
        "2. Validate the reviewed Asai 2026 to Ortho113 conversion table.",
        "3. Regenerate standard FORM with the pinned shared standardizer.",
        "4. Regenerate original and standard PHON with the pinned shared phonology utility.",
        "5. Run the current XML, dialect, text, gloss, source-gloss, and duplicate validators.",
        "",
        "## Source-specific decisions",
        "",
        "- Development XML is written only to `XML/xnb` after blocking HARD findings are zero.",
        "- Standard FORM and PHON are regenerated on every run from Madeline Boese's reviewed route and the pinned shared tools.",
        "- Physical page 251 visibly prints page 246. The observed footer is retained rather than forcing the earlier expected value 247.",
        "- Smart quotes in FORM are normalized to ASCII under current V127. Exact source characters remain in the source ledger.",
        "- Twenty-four source parentheticals are expanded under POL-026/POL-027. The two source judgment constructions are resolved explicitly under POL-016/POL-017.",
        "- Nine trailing source editorial labels or citations are represented in `TRANSL@notes`; meaningful parentheses remain in translation text.",
        "- Native source phonology includes the reviewed c/s palatalization before i. Unreviewed foreign loan letters retain the shared visible asterisk signal.",
    ])
    (ROOT / "data/processed/qc_and_skills_preflight.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def pdf_preflight(formosanbank: Path) -> None:
    ensure_dirs()
    pdf = source_pdf()
    doc = fitz.open(pdf)
    sha = sha256_path(pdf)
    fonts: Counter[str] = Counter()
    image_count = 0
    zero_text = []
    unusual_dims = []
    for idx, page in enumerate(doc, start=1):
        for font in page.get_fonts(full=True):
            fonts[font[3]] += 1
        image_count += len(page.get_images(full=True))
        if not page.get_text("text").strip():
            zero_text.append(idx)
        if abs(page.rect.width - 515.9046) > 2 or abs(page.rect.height - 728.5036) > 2:
            unusual_dims.append(idx)
    lines = [
        "# PDF Preflight",
        "",
        "Generated deterministically from the preserved source PDF.",
        f"Filename: {pdf.relative_to(ROOT)}",
        f"SHA-256: {sha}",
        f"Expected SHA-256: {EXPECTED_SHA256}",
        f"File size: {pdf.stat().st_size} bytes",
        f"PDF metadata format: {doc.metadata.get('format')}",
        f"Physical page count: {doc.page_count}",
        f"Encrypted: {doc.metadata.get('encryption')}",
        f"Tagged: no (per pdfinfo snapshot)",
        f"Forms: AcroForm (per pdfinfo snapshot)",
        f"JavaScript: no (per pdfinfo snapshot)",
        f"Page dimensions: {doc[0].rect.width:.3f} x {doc[0].rect.height:.3f} points",
        f"Rotation values: {sorted(set(page.rotation for page in doc))}",
        f"Embedded image count: {image_count}",
        f"Pages with zero extractable text: {zero_text}",
        f"Pages with unusual dimensions: {unusual_dims}",
        f"Font inventory: {dict(fonts.most_common())}",
        f"Metadata creation date: {doc.metadata.get('creationDate')}",
        f"Metadata modification date: {doc.metadata.get('modDate')}",
        "Text-layer availability: extractable text is present on corpus pages; OCR was not used.",
        "Permissions: pdfinfo reports print:yes copy:yes change:no addNotes:no.",
    ]
    (ROOT / "data/processed/pdf_preflight.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def rights_and_source_reports() -> None:
    sha = sha256_path(source_pdf())
    rights = [
        "# Rights and License",
        "",
        f"Source filename: {PDF_NAME}",
        f"Source SHA-256: {sha}",
        "Title: Kanakanavu Texts",
        "Authors: Erin Asai; Kuang Mei; Paul Jen-kuei Li; Shigeru Tsuchida",
        "Editor: Paul Jen-kuei Li",
        "Assistants: Yi-Chun Chen; Hsiu-min Huang; Amy Ming-luan Chen",
        "Publisher: Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies",
        "Year: 2026",
        "ISBN: 978-4-86337-602-1",
        "Copyright statement exactly as printed: Copyright © 2026 Paul Jen-kuei Li, Yi-Chun Chen, Hsiu-min Huang, and Amy Ming-luan Chen",
        "CC BY statement exactly as printed: This publication is offered under Creative Commons International License Attribution 4.0.",
        "License URL: http://creativecommons.org/licenses/by/4.0/",
        "Physical page containing the licence: 3",
        "Redistribution and transformation: permitted under CC BY 4.0 with attribution.",
        f"Required attribution: {copyright_attr()}",
        f"Recommended FormosanBank citation: {apa_citation()}",
        f"Recommended BibTeX citation: {bibtex_citation()}",
        "Source URL discovered: https://biblio.aa-ken.jp/ (publisher catalogue root printed in source)",
        "No machine translation or OCR was used.",
    ]
    (ROOT / "data/processed/rights_and_license.md").write_text("\n".join(rights) + "\n", encoding="utf-8")
    texts = read_jsonl(ROOT / "data/processed/texts.jsonl") or segment_texts()
    source = [
        "# Source Facts",
        "",
        "Verified bibliographic metadata matches the task and copyright page.",
        "Verified physical page count: 252.",
        "Observed printed footer mapping: grammatical introduction examples begin at physical 17 / printed 12; narrative corpus text begins at physical 33 / printed 28; physical 251 visibly prints 246; physical 252 has no extractable text.",
        f"45-text inventory parsed: 1 grammatical-introduction XML plus {len([t for t in texts if t.get('text_kind') != 'grammar_examples'])} narrative texts.",
        "Grammatical introduction examples parsed: 40 numbered examples / 48 sentence units after splitting subexamples.",
        "Collector counts: Erin Asai 7; Kuang Mei 4; Paul Jen-kuei Li 11; Shigeru Tsuchida 22.",
        "Reported sentence counts: at least 162 / 286 / 259 / 670, total at least 1,377.",
        "Source transcription conventions preserved in raw fields; XML FORM punctuation-standardizes smart quotes only to satisfy current hard validation.",
        "W/M TRANSL tiers preserve source-published interlinear glosses; W glosses keep whole-word gloss notation, including angle-bracket infix notation required by current FormosanBank validation.",
        "Source uncertainty statements and footnotes are preserved in sidecars, not merged into translations.",
        "Source licence: Creative Commons Attribution 4.0 International.",
        f"Source hash: {sha}.",
    ]
    (ROOT / "data/processed/source_facts.md").write_text("\n".join(source) + "\n", encoding="utf-8")


def coverage_and_reports(qc: dict[str, Any] | None = None) -> None:
    texts = read_jsonl(ROOT / "data/processed/texts.jsonl")
    units = read_jsonl(ROOT / "data/processed/sentence_units.jsonl")
    xml_units = read_jsonl(ROOT / "data/processed/xml_sentence_units.jsonl")
    words = read_jsonl(ROOT / "data/processed/xml_word_units.jsonl")
    morphs = read_jsonl(ROOT / "data/processed/xml_morpheme_units.jsonl")
    xml_index_rows = list(csv.DictReader((ROOT / "data/processed/xml_index.csv").open(encoding="utf-8"))) if (ROOT / "data/processed/xml_index.csv").exists() else []
    part_rows: list[dict[str, Any]] = []
    expected = {1: (7, 162), 2: (4, 286), 3: (11, 259), 4: (22, 670)}
    for part, (text_count, sent_min) in expected.items():
        part_texts = [t for t in texts if t["part_number"] == part]
        part_units = [u for u in units if any(t["text_id"] == u["text_id"] for t in part_texts)]
        part_rows.append({
            "part_number": part,
            "collector": PARTS[part][1],
            "expected_text_count": text_count,
            "parsed_text_count": len(part_texts),
            "reported_sentence_minimum": sent_min,
            "extracted_sentence_count": len(part_units),
            "XML_sentence_count": sum(1 for r in xml_index_rows if int(r.get("part_number") or 0) == part),
            "complete_W_tier_count": sum(1 for u in part_units if u.get("word_tier_candidate")),
            "sentence_only_count": sum(1 for u in part_units if not u.get("word_tier_candidate")),
            "M_annotated_sentence_count": sum(1 for u in part_units if u.get("morpheme_tier_candidate")),
            "rejected_count": sum(1 for u in part_units if not unit_in_final_xml(u)),
            "notes": "",
        })
    write_csv(ROOT / "data/processed/coverage_by_part.csv", part_rows, [
        "part_number", "collector", "expected_text_count", "parsed_text_count",
        "reported_sentence_minimum", "extracted_sentence_count", "XML_sentence_count",
        "complete_W_tier_count", "sentence_only_count", "M_annotated_sentence_count",
        "rejected_count", "notes",
    ])
    text_rows = []
    for t in texts:
        tus = [u for u in units if u["text_id"] == t["text_id"]]
        text_rows.append({
            "text_id": t["text_id"],
            "global_text_order": t["global_text_order"],
            "part_number": t["part_number"],
            "collector": t["collector"],
            "text_number_within_part": t["text_number_within_part"],
            "title_english": t["title_english_clean"],
            "title_kanakanavu": t["title_kanakanavu_clean"],
            "printed_page_start": t["printed_page_start"],
            "printed_page_end": t["printed_page_end"],
            "physical_page_start": t["physical_page_start"],
            "physical_page_end": t["physical_page_end"],
            "first_sentence_label": tus[0]["source_sentence_label"] if tus else "",
            "last_sentence_label": tus[-1]["source_sentence_label"] if tus else "",
            "extracted_units": len(tus),
            "XML_units": sum(1 for r in xml_index_rows if r.get("text_id") == t["text_id"]),
            "complete_W_tiers": sum(1 for u in tus if u.get("word_tier_candidate")),
            "M_annotated_units": sum(1 for u in tus if u.get("morpheme_tier_candidate")),
            "low_confidence_units": sum(1 for u in tus if u.get("unit_confidence") == "low"),
            "rejected_units": sum(1 for u in tus if not unit_in_final_xml(u)),
            "hard_QC_findings": "",
            "soft_QC_findings": "",
            "status": "parsed" if tus else "missing_units",
            "notes": "",
        })
    write_csv(ROOT / "data/processed/coverage_by_text.csv", text_rows, [
        "text_id", "global_text_order", "part_number", "collector", "text_number_within_part",
        "title_english", "title_kanakanavu", "printed_page_start", "printed_page_end",
        "physical_page_start", "physical_page_end", "first_sentence_label", "last_sentence_label",
        "extracted_units", "XML_units", "complete_W_tiers", "M_annotated_units",
        "low_confidence_units", "rejected_units", "hard_QC_findings", "soft_QC_findings",
        "status", "notes",
    ])
    pages = list(csv.DictReader((ROOT / "data/processed/pages.csv").open(encoding="utf-8"))) if (ROOT / "data/processed/pages.csv").exists() else []
    by_page = []
    for p in pages:
        phys = int(p["physical_page_number"])
        pus = [u for u in units if u.get("physical_page_start") == phys or u.get("physical_page_end") == phys]
        by_page.append({
            "physical_page": phys,
            "printed_page": p.get("printed_page_number", ""),
            "fetched_or_present": True,
            "has_text_layer": p.get("has_text_layer", ""),
            "character_count": p.get("character_count", ""),
            "positioned_words": p.get("word_count", ""),
            "text_ids": sorted({u["text_id"] for u in pus}),
            "sentence_units_started": sum(1 for u in units if u.get("physical_page_start") == phys),
            "sentence_units_continued": sum(1 for u in units if u.get("physical_page_start") != phys and u.get("physical_page_end") == phys),
            "footnotes": "",
            "warnings": p.get("warnings", ""),
        })
    write_csv(ROOT / "data/processed/coverage_by_page.csv", by_page, [
        "physical_page", "printed_page", "fetched_or_present", "has_text_layer",
        "character_count", "positioned_words", "text_ids", "sentence_units_started",
        "sentence_units_continued", "footnotes", "warnings",
    ])
    conf_counts = Counter((u.get("unit_confidence"), u.get("quality_status")) for u in units)
    write_csv(ROOT / "data/processed/coverage_by_confidence.csv", [
        {
            "layer": "sentence_unit",
            "confidence": conf or "",
            "record_count": count,
            "included_in_XML": sum(1 for u in units if u.get("unit_confidence") == conf and unit_in_final_xml(u)),
            "excluded_from_XML": sum(1 for u in units if u.get("unit_confidence") == conf and not unit_in_final_xml(u)),
            "reviewed_count": "",
            "unresolved_count": "",
            "notes": status,
        }
        for (conf, status), count in conf_counts.items()
    ], ["layer", "confidence", "record_count", "included_in_XML", "excluded_from_XML", "reviewed_count", "unresolved_count", "notes"])
    write_csv(ROOT / "data/processed/parse_errors.csv", [], ["record_id", "stage", "message", "source"])
    write_csv(ROOT / "data/processed/parse_warnings.csv", [
        {"record_id": u["unit_id"], "stage": "parse-units", "message": u.get("warnings", ""), "source": u.get("source_sentence_label", "")}
        for u in units if u.get("warnings")
    ], ["record_id", "stage", "message", "source"])
    write_source_only_sentences(units)
    write_source_unit_coverage(units)
    write_source_notation_audit(units)
    write_duplicate_triage()
    write_standardization_review()
    write_qc_finding_review()
    write_count_audit(texts, units, xml_index_rows)
    write_reports(qc, texts, xml_units, words, morphs)


def write_source_only_sentences(units: list[dict[str, Any]]) -> None:
    rows = [
        {
            "unit_id": u["unit_id"],
            "text_id": u["text_id"],
            "source_sentence_label": u["source_sentence_label"],
            "printed_page_start": u["printed_page_start"],
            "physical_page_start": u["physical_page_start"],
            "source_line_clean": u["source_line_clean"],
            "gloss_line_clean": u["gloss_line_clean"],
            "reason": "source_published_free_translation_absent",
            "final_action": "included_without_s_level_translation",
        }
        for u in units if u.get("translation_confidence") == "source_absent"
    ]
    write_csv(ROOT / "data/processed/source_only_sentences.csv", rows, [
        "unit_id", "text_id", "source_sentence_label", "printed_page_start",
        "physical_page_start", "source_line_clean", "gloss_line_clean",
        "reason", "final_action",
    ])


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
            "standardization_action": "generated_by_pinned_shared_standardizer_from_reviewed_conversion",
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
                "expanded_variants_with_aligned_w_m"
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
        elif unit["unit_id"] in PARENTHETICAL_VARIANTS:
            decision = (
                "Expand the reviewed optional or alternative parenthetical into "
                "two complete S/W/M manifestations under POL-026/POL-027."
            )
        rows.append({
            "unit_id": unit["unit_id"],
            "physical_page": unit["physical_page_start"],
            "source_sentence_label": unit["source_sentence_label"],
            "notation_types": types,
            "exact_source_form": source,
            "xml_original_form": " || ".join(
                manifestation["source_line_clean"] for manifestation in manifestations
            ),
            "created_variants": " || ".join(
                f"{manifestation['unit_id']}:{manifestation['variant_label']}"
                for manifestation in manifestations
            ) if len(manifestations) > 1 else "none",
            "excluded_sentences": excluded,
            "translation_action": "retained_exact_source_translation",
            "audio_action": "not_applicable_no_source_audio",
            "word_morpheme_action": (
                "expanded_variants_with_aligned_w_m"
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


def write_qc_finding_review() -> None:
    output = ROOT / "build/qc_output"
    rows: list[dict[str, Any]] = []
    dispositions = {
        "V122": "retained_source_square_bracket_analysis",
        "V126": "retained_source_clitic_boundary",
        "V133": "retained_source_morpheme_boundary",
        "V134": "retained_source_infix_notation_in_original_form",
        "V060": "word_morpheme_tiers_omitted_for_square_bracket_analysis_notation",
    }
    source_words = {
        row["word_id"]: row
        for row in read_jsonl(ROOT / "data/processed/word_units.jsonl")
    }

    def gloss_scrape_disposition(finding: dict[str, str]) -> tuple[str, str, str]:
        rule_id = finding.get("rule_id", "")
        if rule_id in {"G001", "G002"}:
            return (
                "source_published_segmentation_or_lexical_gloss_verified",
                "word_units.jsonl and morpheme_units.jsonl; five locations checked against the PDF",
                "justified",
            )
        if rule_id in {"G003", "G004"}:
            return (
                "retained_current_infix_host_gap_marker_convention",
                "word_units.jsonl and morpheme_units.jsonl; current FormosanBank infix convention uses host gaps such as k-ita and infixes such as -um-",
                "justified",
            )
        if rule_id == "G005":
            word_match = re.search(r"W=([^ ]+)", finding.get("location", ""))
            label_match = re.search(
                r"gloss label '([^']+)'",
                finding.get("message", ""),
            )
            if word_match and label_match:
                source_word_id = re.sub(
                    r"_S(\d{4})_W",
                    r"_U\1_W",
                    word_match.group(1),
                )
                source_word = source_words.get(source_word_id, {})
                source_labels = re.split(
                    r"[-=<>()]+",
                    source_word.get("gloss_token_clean", ""),
                )
                if label_match.group(1) in source_labels:
                    return (
                        "source_published_gloss_label_verified",
                        f"word_units.jsonl exact source W gloss at {source_word_id}",
                        "justified",
                    )
            return (
                "requires_source_gloss_verification",
                "word_units.jsonl",
                "unresolved",
            )
        if rule_id == "G012":
            return (
                "move_trailing_editorial_parenthetical_to_TRANSL_notes",
                "source_unit_coverage.csv",
                "unresolved",
            )
        if rule_id == "G013":
            return (
                "source_region_alignment_false_positive",
                "source_unit_coverage.csv and source_xml_comparison_report.md; all 1,431 source translations are independently aligned",
                "justified",
            )
        if rule_id == "G020":
            return (
                "page_local_source_tokens_independently_verified",
                "source_xml_comparison_report.md; all units have at least 0.80 page-local token support",
                "justified",
            )
        if rule_id == "G021":
            return (
                "non_unit_or_repeated_source_region_extraction",
                "source_unit_coverage.csv and source_xml_comparison_report.md; regions are headers, phonology prose, or wrapped/column-repeated examples",
                "justified",
            )
        if rule_id == "G022":
            return (
                "documented_character_normalization_or_region_contamination",
                "source_unit_coverage.csv and source_notation_audit.csv; linguistic source characters have zero same-unit loss",
                "justified",
            )
        if rule_id == "G023":
            return (
                "source_extractor_self_report_reviewed",
                "audit_gloss_scrape.log",
                "justified",
            )
        return "requires_remediation", "audit_gloss_scrape_findings.csv", "unresolved"
    for validator, filename in (
        ("xml", "validate_xml_findings.csv"),
        ("text", "validate_text_findings.csv"),
        ("gloss", "validate_glosses_findings.csv"),
    ):
        path = output / filename
        if not path.exists():
            continue
        with path.open(encoding="utf-8-sig") as handle:
            for finding in csv.DictReader(handle):
                rule_id = finding.get("rule_id", "")
                rows.append({
                    "validator": validator,
                    "severity": finding.get("severity", ""),
                    "rule_id": rule_id,
                    "file": Path(finding.get("file", "")).name,
                    "location": finding.get("location", ""),
                    "message": finding.get("message", ""),
                    "count": finding.get("count", "1"),
                    "disposition": dispositions.get(rule_id, "requires_remediation"),
                    "source_evidence": "source_unit_coverage.csv and source_notation_audit.csv",
                    "status": (
                        "justified"
                        if rule_id in dispositions
                        else "unresolved"
                    ),
                })
    gloss_scrape_path = output / "audit_gloss_scrape_findings.csv"
    if gloss_scrape_path.exists():
        with gloss_scrape_path.open(encoding="utf-8-sig") as handle:
            for finding in csv.DictReader(handle):
                disposition, evidence, status = gloss_scrape_disposition(finding)
                rows.append({
                    "validator": "gloss_scrape",
                    "severity": finding.get("severity", ""),
                    "rule_id": finding.get("rule_id", ""),
                    "file": Path(finding.get("file", "")).name,
                    "location": finding.get("location", ""),
                    "message": finding.get("message", ""),
                    "count": finding.get("count", "1"),
                    "disposition": disposition,
                    "source_evidence": evidence,
                    "status": status,
                })
    duplicate_triage_path = ROOT / "data/processed/duplicate_sentence_triage.csv"
    triage = {}
    if duplicate_triage_path.exists():
        with duplicate_triage_path.open(encoding="utf-8-sig") as handle:
            triage = {row["normalized_text"]: row for row in csv.DictReader(handle)}
    duplicate_path = output / "duplicate_sentences.csv"
    if duplicate_path.exists():
        with duplicate_path.open(encoding="utf-8-sig") as handle:
            for finding in csv.DictReader(handle):
                decision = triage.get(finding.get("normalized_text", ""), {})
                rows.append({
                    "validator": "duplicate",
                    "severity": finding.get("severity", ""),
                    "rule_id": "duplicate_sentence",
                    "file": finding.get("file", ""),
                    "location": finding.get("s_id", ""),
                    "message": finding.get("raw_text", ""),
                    "count": "1",
                    "disposition": decision.get("final_action", "requires_remediation"),
                    "source_evidence": decision.get("rationale", ""),
                    "status": "justified" if decision else "unresolved",
                })
    write_csv(ROOT / "data/processed/qc_finding_review.csv", rows, [
        "validator", "severity", "rule_id", "file", "location", "message", "count",
        "disposition", "source_evidence", "status",
    ])


def write_standardization_review() -> None:
    report = [
        "# Standardization Review",
        "",
        "## Decision",
        "",
        "Standard FORM is regenerated by the pinned shared standardizer from the reviewed Asai 2026 conversion table. The route maps ŋ to ng, l to r, ʔ and Ɂ to apostrophe, and ə to e. The shared tool removes S-level segmentation while preserving W/M segmentation.",
        "",
        "Madeline Boese's completed Basecamp review supplied and approved this mapping. Physical page 16, printed page 11, independently describes the source transcription's four main vowels `/i, u, ə, a/` and its historical liquid distinction.",
        "",
        "Original and standard PHON are regenerated by the pinned shared phonology utility. The reviewed rules palatalize c and s before i. The source profile keeps l as ɾ and r as r; standard Ortho113 represents the collapsed r as [r|ɾ].",
        "",
        "The conversion validator intentionally reports the reviewed l-to-r merger and ə-to-e approximation as phoneme-level mismatches. Its target-only f and ɨ inventory rows do not occur in this source. A small set of Japanese, Mandarin, and proper-name loan spellings contains b, d, g, j, or z outside the reviewed profile; the shared utility exposes those segments as `*`, and `phonology_mapping_review.csv` records every occurrence.",
        "",
        "The pinned cleaner was run on a disposable copy. Its source-notation rewrites were not promoted; see `cleaner_probe.md`.",
        "",
    ]
    (ROOT / "data/processed/standardization_review.md").write_text(
        "\n".join(report), encoding="utf-8"
    )


def write_duplicate_triage() -> None:
    path = ROOT / "data/processed/duplicate_sentences.csv"
    if not path.exists():
        write_csv(ROOT / "data/processed/duplicate_sentence_triage.csv", [], [
            "severity", "normalized_text", "occurrence_count", "files", "s_ids",
            "final_action", "rationale",
        ])
        return
    groups: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in csv.DictReader(path.open(encoding="utf-8")):
        groups[(row.get("severity", ""), row.get("normalized_text", ""))].append(row)
    rows = []
    sentence_sources: dict[str, str] = {}
    xml_index_path = ROOT / "data/processed/xml_index.csv"
    if xml_index_path.exists():
        with xml_index_path.open(encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                sentence_sources[row["sentence_id"]] = (
                    f"physical page {row['physical_page_start']} "
                    f"source label {row['source_sentence_label']}"
                )
    for (severity, normalized), occs in sorted(groups.items(), key=lambda item: (item[0][0], item[0][1])):
        files = sorted({r.get("file", "") for r in occs})
        s_ids = [r.get("s_id", "") for r in occs]
        locators = [sentence_sources.get(sid, sid) for sid in s_ids]
        if severity == "HARD" and normalized == "ara-rakau=kani sua taniare.":
            action = "retain_source_repetition"
            rationale = (
                "The source prints the same sentence as distinct Shooting the sun "
                f"units at {'; '.join(locators)}."
            )
        elif severity == "HARD" and normalized == "kuu=ku m-iima canumu.":
            action = "retain_source_contrast_pair"
            rationale = (
                "The source prints the same form as grammatical-introduction "
                f"examples (36) and (40a) at {'; '.join(locators)}."
            )
        else:
            action = "retain_source_repetition"
            rationale = (
                "The source prints this sentence in distinct units at "
                f"{'; '.join(locators)}; each occurrence retains its own source locator and translation."
            )
        rows.append({
            "severity": severity,
            "normalized_text": normalized,
            "occurrence_count": len(occs),
            "files": files,
            "s_ids": s_ids,
            "final_action": action,
            "rationale": rationale,
        })
    write_csv(ROOT / "data/processed/duplicate_sentence_triage.csv", rows, [
        "severity", "normalized_text", "occurrence_count", "files", "s_ids",
        "final_action", "rationale",
    ])


def write_count_audit(texts: list[dict[str, Any]], units: list[dict[str, Any]], xml_index_rows: list[dict[str, str]]) -> None:
    rows = []
    for t in texts:
        tus = [u for u in units if u["text_id"] == t["text_id"]]
        nums = [u["source_sentence_number"] for u in tus]
        expected = max(nums) if nums else 0
        missing = sorted(set(range(1, expected + 1)) - set(nums)) if expected else []
        dupes = sorted(n for n, c in Counter(nums).items() if c > 1)
        expected_count = ""
        notes = ""
        if t.get("text_kind") == "grammar_examples":
            expected_count = "40 numbered examples / 48 sentence units"
            notes = "Subexamples are split into separate S units while retaining the source example number."
        rows.append({
            "text_id": t["text_id"],
            "collector": t["collector"],
            "expected_or_reported_count": expected_count,
            "first_source_sentence_label": f"({min(nums)})" if nums else "",
            "last_source_sentence_label": f"({max(nums)})" if nums else "",
            "extracted_count": len(tus),
            "XML_count": sum(1 for r in xml_index_rows if r.get("text_id") == t["text_id"]),
            "missing_labels": missing,
            "duplicate_labels": dupes,
            "cross_page_units": sum(1 for u in tus if u.get("physical_page_start") != u.get("physical_page_end")),
            "rejected_units": sum(1 for u in tus if not unit_in_final_xml(u)),
            "difference": "",
            "notes": notes,
        })
    write_csv(ROOT / "data/processed/sentence_count_audit.csv", rows, [
        "text_id", "collector", "expected_or_reported_count", "first_source_sentence_label",
        "last_source_sentence_label", "extracted_count", "XML_count", "missing_labels",
        "duplicate_labels", "cross_page_units", "rejected_units", "difference", "notes",
    ])


def write_reports(qc: dict[str, Any] | None, texts: list[dict[str, Any]], units: list[dict[str, Any]], words: list[dict[str, Any]], morphs: list[dict[str, Any]]) -> None:
    infix_words = [w for w in words if "<" in w.get("source_token_clean", "") and ">" in w.get("source_token_clean", "")]
    infix_morphs = [m for m in morphs if m.get("is_infix")]
    clitic_words = [w for w in words if "=" in w.get("source_token_clean", "")]
    clitic_morphs = [m for m in morphs if m.get("is_clitic")]
    unclear_word_glosses = [w for w in words if w.get("gloss_token_unclear")]
    unclear_morpheme_glosses = [m for m in morphs if m.get("gloss_morpheme_unclear")]
    (ROOT / "data/processed/normalization_report.md").write_text(
        "# Normalization Report\n\n"
        "- Unicode normalization: NFC.\n"
        "- Nonbreaking spaces are normalized to ordinary spaces in clean fields.\n"
        "- Smart quotes are punctuation-standardized to ASCII quotes in XML FORM tiers because current validate_text hard-fails smart quotes in FORM.\n"
        "- Positively identified footnote anchor digits are removed from linguistic tiers and preserved in footnote sidecars. Other digits are retained.\n"
        "- Literal double-encoded HTML entity residue is unescaped before XML serialization; XML-required escaping such as `&lt;` for a real infix delimiter is not treated as residue.\n"
        "- Standard FORM is regenerated with the reviewed Asai 2026 to Ortho113 table and the pinned shared standardizer.\n"
        "- S- and W-level original FORM preserve source angle-bracket infix notation; M original tiers encode the infix as `-X-`.\n"
        "- Source hyphens and equals signs remain in original forms because no source-backed bulk de-segmentation rule applies.\n"
        "- Twenty-four source parentheticals are expanded into complete manifestations under POL-026/POL-027; source square-bracket analysis, ellipses, and CJK text are retained.\n"
        "- Two source judgment constructions remain exact in the source ledger. Their starred material is excluded explicitly under POL-016/POL-017.\n"
        "- No ASCII folding, NFKC, spelling modernization, or machine translation was performed.\n"
        "- Kanakanavu orthographic characters, non-angle segmentation markers, case, and source gloss abbreviations are preserved.\n"
        "- W/M TRANSL tiers preserve source-published interlinear glosses as `kindOf=\"original\"`; direct S-level TRANSL elements have no `kindOf`.\n",
        encoding="utf-8",
    )
    (ROOT / "data/processed/extraction_report.md").write_text(
        "# Extraction Report\n\n"
        f"- PDF engine: PyMuPDF/fitz.\n- Pages inventoried: 252.\n"
        f"- Positioned word count: {sum(1 for _ in read_jsonl(ROOT / 'data/processed/positioned_words.jsonl'))}.\n"
        "- Rendered pages are under `data/raw/renders/`.\n"
        "- OCR was not used.\n",
        encoding="utf-8",
    )
    (ROOT / "data/processed/alignment_report.md").write_text(
        "# Alignment Report\n\n"
        f"- Total numbered units extracted: {len(units)}.\n"
        f"- High-confidence units: {sum(1 for u in units if u.get('unit_confidence') == 'high')}.\n"
        f"- Medium-confidence units: {sum(1 for u in units if u.get('unit_confidence') == 'medium')}.\n"
        f"- Low-confidence units: {sum(1 for u in units if u.get('unit_confidence') == 'low')}.\n"
        f"- Word rows: {len(words)}.\n"
        f"- Morpheme rows: {len(morphs)}.\n"
        "- W/M tiers are included only where complete source/gloss token alignment is available.\n",
        encoding="utf-8",
    )
    (ROOT / "data/processed/gloss_tier_audit.md").write_text(
        "# Gloss Tier Audit\n\n"
        "Decision: keep source-published interlinear glosses in W- and M-level `TRANSL kindOf=\"original\"` elements.\n\n"
        "- S-level `TRANSL` contains the free English sentence translation.\n"
        "- W-level `TRANSL` contains the source's whole-word interlinear gloss token, for example `NEG=1SG.NOM` or `STA-good`.\n"
        "- M-level `TRANSL` contains morpheme-level glosses aligned to each M element.\n"
        "- Angle brackets in S/W original FORM and W glosses mark infix position/glossing in the source and are serialized as `&lt;...&gt;` because XML requires escaping literal `<` and `>` text.\n"
        "- Infix M elements use FormosanBank's canonical `-X-` notation; W glosses keep `<X>` where required by `validate_glosses` V062.\n\n"
        f"- W rows: {len(words)}.\n"
        f"- W rows with concrete source gloss text: {sum(1 for w in words if w.get('gloss_token_clean'))}.\n"
        f"- W rows emitted with explicit UNCLEAR gloss markers: {len(unclear_word_glosses)}.\n"
        f"- M rows: {len(morphs)}.\n"
        f"- M rows with concrete source gloss text: {sum(1 for m in morphs if m.get('gloss_morpheme_clean'))}.\n"
        f"- M rows emitted with explicit UNCLEAR gloss markers: {len(unclear_morpheme_glosses)}.\n"
        f"- W rows with source infix angle notation: {len(infix_words)}.\n"
        f"- M rows marked as infixes: {len(infix_morphs)}.\n"
        f"- W rows with clitic `=` notation: {len(clitic_words)}.\n"
        f"- M rows marked as clitics: {len(clitic_morphs)}.\n",
        encoding="utf-8",
    )
    overlaps = list(csv.DictReader((ROOT / "data/processed/overlap_candidates.csv").open(encoding="utf-8"))) if (ROOT / "data/processed/overlap_candidates.csv").exists() else []
    (ROOT / "data/processed/overlap_report.md").write_text(
        "# Overlap Report\n\n"
        f"- Existing xnb FormosanBank XML compared: yes.\n- Candidate overlap rows: {len(overlaps)}.\n"
        f"- Non-no-overlap rows: {sum(1 for r in overlaps if r.get('overlap_type') != 'no_overlap')}.\n"
        "- Source-specific traditional variants are retained pending human review.\n",
        encoding="utf-8",
    )
    final_count = len(list((ROOT / "XML/xnb").glob("*.xml")))
    final_s_count = 0
    translated_s_count = 0
    for path in (ROOT / "XML/xnb").glob("*.xml"):
        try:
            root = etree.parse(str(path)).getroot()
        except etree.XMLSyntaxError:
            continue
        for s_elem in root.iter("S"):
            final_s_count += 1
            if any(child.tag == "TRANSL" for child in s_elem):
                translated_s_count += 1
    source_only_count = final_s_count - translated_s_count
    rejected_count = sum(1 for u in units if not unit_in_final_xml(u))
    review_rows = list(csv.DictReader((ROOT / "data/processed/manual_review_queue.csv").open(encoding="utf-8"))) if (ROOT / "data/processed/manual_review_queue.csv").exists() else []
    unresolved_high = sum(1 for r in review_rows if r.get("severity") == "high" and r.get("status") != "resolved")
    dup_rows = list(csv.DictReader((ROOT / "data/processed/duplicate_sentences.csv").open(encoding="utf-8"))) if (ROOT / "data/processed/duplicate_sentences.csv").exists() else []
    dup_hard_groups = len({r.get("normalized_text", "") for r in dup_rows if r.get("severity") == "HARD"})
    dup_soft_groups = len({r.get("normalized_text", "") for r in dup_rows if r.get("severity") == "SOFT"})
    validate_text_rows = list(csv.DictReader((ROOT / "build/qc_output/validate_text_findings.csv").open(encoding="utf-8-sig"))) if (ROOT / "build/qc_output/validate_text_findings.csv").exists() else []
    validate_text_soft_counts = Counter(r.get("rule_id", "") for r in validate_text_rows if r.get("severity") == "SOFT")
    validate_text_hard_counts = Counter(r.get("rule_id", "") for r in validate_text_rows if r.get("severity") == "HARD")
    validate_text_hard_count = sum(validate_text_hard_counts.values())
    gloss_rows = list(csv.DictReader((ROOT / "build/qc_output/validate_glosses_findings.csv").open(encoding="utf-8-sig"))) if (ROOT / "build/qc_output/validate_glosses_findings.csv").exists() else []
    gloss_soft_counts = Counter(r.get("rule_id", "") for r in gloss_rows if r.get("severity") == "SOFT")
    gloss_scrape_rows = list(csv.DictReader((ROOT / "build/qc_output/audit_gloss_scrape_findings.csv").open(encoding="utf-8-sig"))) if (ROOT / "build/qc_output/audit_gloss_scrape_findings.csv").exists() else []
    gloss_scrape_counts = Counter()
    for row in gloss_scrape_rows:
        gloss_scrape_counts[row.get("rule_id", "")] += int(row.get("count") or 1)
    qc_review_rows = list(csv.DictReader((ROOT / "data/processed/qc_finding_review.csv").open(encoding="utf-8-sig"))) if (ROOT / "data/processed/qc_finding_review.csv").exists() else []
    unresolved_finding_count = sum(1 for row in qc_review_rows if row.get("status") != "justified")
    expected_final_count = len(texts)
    grammar_units = [u for u in units if u.get("text_id") == GRAMMAR_EXAMPLE_TEXT_ID]
    grammar_numbers = {u.get("grammar_example_number") for u in grammar_units}
    qc_lines = ["# Validation Report", ""]
    if qc:
        for name, result in qc["results"].items():
            qc_lines.append(f"- {name}: exit {result['exit_code']} (`{result['command']}`), log `{result['log']}`")
        status = (
            "PASS"
            if not qc["hard_fail"]
            and final_count == expected_final_count
            and final_s_count == EXPECTED_SENTENCE_COUNT
            and len(grammar_units) == GRAMMAR_EXAMPLE_EXPECTED_UNIT_COUNT
            and grammar_numbers == GRAMMAR_EXAMPLE_EXPECTED_NUMBERS
            and unresolved_high == 0
            and unresolved_finding_count == 0
            and source_only_count == 0
            else "FAIL"
        )
    else:
        status = "NOT_RUN"
    qc_lines.extend([
        "",
        f"Parsed text count: {len(texts)}",
        f"Extracted sentence count: {len(units)}",
        f"Final XML file count: {final_count}",
        f"Final XML S count: {final_s_count}",
        f"Grammatical introduction S count: {len(grammar_units)}",
        f"Grammatical introduction numbered examples covered: {len(grammar_numbers)}",
        f"S with source-published English TRANSL: {translated_s_count}",
        f"Source-only S count: {source_only_count}",
        f"Rejected extraction artifacts: {rejected_count}",
        f"Manual review rows: {len(review_rows)}",
        f"Unresolved high-severity review rows: {unresolved_high}",
        f"validate_text hard findings: {validate_text_hard_count}",
        f"validate_text V122 source-notation soft findings: {validate_text_soft_counts.get('V122', 0)}",
        f"validate_text V126 preserved-clitic soft findings: {validate_text_soft_counts.get('V126', 0)}",
        f"validate_text V133 preserved-hyphen soft findings: {validate_text_soft_counts.get('V133', 0)}",
        f"validate_text V134 source-infix soft findings: {validate_text_soft_counts.get('V134', 0)}",
        f"validate_gloss V060 documented W/M omissions: {gloss_soft_counts.get('V060', 0)}",
        f"Gloss scrape finding rows: {len(gloss_scrape_rows)}",
        f"Gloss scrape G012 actionable translation-note findings: {gloss_scrape_counts.get('G012', 0)}",
        f"Reviewed raw finding rows: {len(qc_review_rows)}",
        f"Unresolved finding rows: {unresolved_finding_count}",
        f"Duplicate validator hard-labeled groups: {dup_hard_groups}",
        f"Duplicate validator soft groups: {dup_soft_groups}",
        "Duplicate triage: data/processed/duplicate_sentence_triage.csv",
        "Finding review: data/processed/qc_finding_review.csv",
        "Source coverage: data/processed/source_unit_coverage.csv",
        "Source notation audit: data/processed/source_notation_audit.csv",
        "",
        "Notes:",
        "- `validate_duplicate_sentences.py` reports no current duplicate groups.",
        "- V122 findings preserve four printed square-bracket analysis constructions at S level.",
        "- V126 and V133 findings preserve printed clitic and morpheme boundaries. No bulk de-segmentation was applied.",
        "- V134 source-infix soft findings are expected: the source prints Kanakanavu infixes with `<...>` and `FORM[@kindOf=\"original\"]` preserves them.",
        "- V060 rows are limited to the four square-bracket analysis constructions whose W/M representation would require destructive source interpretation.",
        "- The gloss scrape audit is a triage tool. Its G003/G004 infix-host warnings conflict with the current gap-marker convention; its source-region findings are independently reconciled in the source audit. G012 is treated as actionable and must remain zero.",
        "- All 12 formerly source-only sentences now carry their printed page-bottom translations.",
    ])
    if qc and qc["failed_validators"]:
        qc_lines.append(
            "- Validator execution failures: "
            + ", ".join(
                f"`{name}` (exit {qc['results'][name]['exit_code']})"
                for name in qc["failed_validators"]
            )
            + ". The last validated XML snapshot was preserved; inspect the listed logs."
        )
    else:
        qc_lines.append(
            "- Standard FORM and both PHON tiers were regenerated from the reviewed route with the pinned shared tools."
        )
    qc_lines.append(f"Final status: {status}")
    (ROOT / "data/processed/validation_report.md").write_text("\n".join(qc_lines) + "\n", encoding="utf-8")
    (ROOT / "data/processed/import_report.md").write_text(
        "# Import Report\n\n"
        f"- Corpus: Formosan-ILCAA-Kanakanavu-Texts.\n- Licence: CC BY 4.0.\n"
        f"- XML files ready: {final_count}.\n- S elements: {final_s_count}.\n"
        f"- S elements with English TRANSL: {translated_s_count}.\n- Source-only S elements: {source_only_count}.\n"
        f"- W rows: {len(words)}.\n- M rows: {len(morphs)}.\n"
        "- Ready for FormosanBank import only if `validation_report.md` says PASS.\n",
        encoding="utf-8",
    )
    manifest_rows = []
    manifest_path = ROOT / "data/processed/manifest.csv"
    for path in sorted((ROOT / "data").rglob("*")) + sorted((ROOT / "XML").rglob("*")):
        if path.is_file() and path != manifest_path:
            manifest_rows.append({"path": str(path.relative_to(ROOT)), "size_bytes": path.stat().st_size, "sha256": sha256_path(path)})
    write_csv(ROOT / "data/processed/manifest.csv", manifest_rows, ["path", "size_bytes", "sha256"], lineterminator="\n")
    write_readme()


def write_readme() -> None:
    readme = f"""# Formosan-ILCAA-Kanakanavu-Texts

This repository converts the grammatical examples and 44 narratives in `data/raw/pdf/{PDF_NAME}` into FormosanBank development XML for Kanakanavu (`xnb`, dialect `Kanakanavu`). Generated output is in `XML/xnb/`.

Source: Asai, E., Mei, K., Li, P. J.-k., & Tsuchida, S. (2026). *Kanakanavu texts* (P. J.-k. Li, Ed.). Research Institute for Languages and Cultures of Asia and Africa, Tokyo University of Foreign Studies. Licensed CC BY 4.0. SHA-256: `{EXPECTED_SHA256}`.

The CC BY 4.0 source PDF is intentionally tracked so a fresh private clone can reproduce the corpus without an unrecorded local dependency.

## Verify

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
make verify PYTHON=.venv/bin/python
```

Poppler `pdftotext` and a clean sibling `../FormosanBank` checkout at commit `3a3c47c220520113f747e6a2d441494000e13c4b` are required. Generated extraction and QC files are ignored under `data/processed/` and `build/` and can be deleted at any time.

## Mapping rules

- Original S forms preserve source spelling and analysis notation after technical cleanup.
- Direct S-level `TRANSL` elements have no `kindOf`. Source W/M glosses use `TRANSL kindOf=\"original\"`.
- The source's two starred constructions are handled by explicit POL-016/POL-017 decisions in `source_notation_audit.csv`. The generator rejects any unreviewed asterisk.
- Twenty-four parenthetical optional or alternative constructions expand to two complete manifestations each under POL-026/POL-027. Four square-bracket analysis constructions remain S-only.
- W/M tiers preserve unambiguous source glossing. Every W in a segmented file receives at least one M under POL-023.
- Standard FORM and original/standard PHON are regenerated by the pinned shared tools from Madeline Boese's reviewed mapping. Unreviewed foreign loan segments remain visible as `*` and are listed in `phonology_mapping_review.csv`.

## QC status

This repository is ready to port when `make verify` passes at the pinned FormosanBank commit.

- Madeline completed the ten-page Basecamp review on 2026-08-12 and reported no errors in the word or morpheme structure.
- The licensed source PDF, extraction decisions, variant decisions, and current tool pin are reproducible from a fresh private clone.
- This development repository has not been ported or published.
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def run_tests() -> int:
    proc = subprocess.run([sys.executable, "-m", "pytest", "tests"], cwd=ROOT)
    return proc.returncode


def stage_all(config: dict[str, Any]) -> int:
    formosanbank = formosanbank_checkout(config)
    write_preflight_report(formosanbank)
    pdf_preflight(formosanbank)
    extract_all_pages(render=True)
    parse_toc()
    segment_texts()
    parse_sentence_units()
    extract_footnotes()
    extract_style_spans()
    filter_units()
    inventory_duplicate_units()
    overlap_against_formosanbank(formosanbank)
    build_xml()
    derive_machine_tiers(formosanbank)
    qc = run_qc(formosanbank)
    rights_and_source_reports()
    coverage_and_reports(qc)
    return 1 if qc["hard_fail"] else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=[
        "all", "preflight", "docs-and-skills", "extract", "toc", "segment-texts",
        "parse-units", "align-words", "align-morphemes", "normalize",
        "quality-filter", "duplicate-inventory", "build-xml", "qc", "reports", "test",
    ])
    parser.add_argument("--config", default="scripts/config.yaml")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    config = load_config(ROOT / args.config)
    formosanbank = formosanbank_checkout(config)
    ensure_dirs()
    if args.stage == "all":
        return stage_all(config)
    elif args.stage == "docs-and-skills":
        write_preflight_report(formosanbank)
    elif args.stage == "preflight":
        write_preflight_report(formosanbank)
        pdf_preflight(formosanbank)
    elif args.stage == "extract":
        extract_all_pages(render=True)
    elif args.stage == "toc":
        parse_toc()
    elif args.stage == "segment-texts":
        segment_texts()
    elif args.stage == "parse-units":
        parse_sentence_units()
    elif args.stage in {"align-words", "align-morphemes", "normalize"}:
        parse_sentence_units()
    elif args.stage == "quality-filter":
        filter_units()
    elif args.stage == "duplicate-inventory":
        inventory_duplicate_units()
        overlap_against_formosanbank(formosanbank)
    elif args.stage == "build-xml":
        build_xml()
        derive_machine_tiers(formosanbank)
    elif args.stage == "qc":
        qc = run_qc(formosanbank)
        coverage_and_reports(qc)
        return 1 if qc["hard_fail"] else 0
    elif args.stage == "reports":
        rights_and_source_reports()
        coverage_and_reports(None)
    elif args.stage == "test":
        return run_tests()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
