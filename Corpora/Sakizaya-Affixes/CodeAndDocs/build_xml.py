#!/usr/bin/env python3
"""Build FormosanBank XML from Akiw 2012 numbered examples."""

from __future__ import annotations

import csv
import difflib
import json
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from xml_tiers import (
    add_form_pair,
    add_translation,
    add_word_tiers,
    gloss_tokens,
    word_tokens,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCAN = ROOT / "Private/source/akiw_2012_sakizaya_affixes_scan.pdf"
SOURCE_OCR = ROOT / "Private/source/akiw_2012_sakizaya_affixes_acrobat_ocr.pdf"
CACHE_DIR = ROOT / "Private/cache"
SCAN_TEXT = CACHE_DIR / "scan_text_layer.txt"
OCR_TEXT = CACHE_DIR / "acrobat_ocr_text_layer.txt"
VISION_OCR_DIR = CACHE_DIR / "vision_ocr_350"
REPORT_CSV = ROOT / "CodeAndDocs/extraction_report.csv"
XML_PATH = ROOT / "XML/szy/akiw_2012_sakizaya_affixes_examples.xml"
SOURCE_DATA_DIR = ROOT / "CodeAndDocs/source_data"

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


@dataclass
class Candidate:
    page: int
    example: int
    subexample: str
    form: str
    raw_form: str
    word_form: str = ""
    source_judgement: str = ""
    retained_xml_id: str = ""
    status: str = "include"
    note: str = ""
    translation_zho: str = ""
    raw_ocr_gloss: str = ""
    source_gloss: str = ""
    aligned_gloss_tokens: list[str] = field(default_factory=list)
    ocr_match_score: float = 0.0
    ocr_note: str = ""

    @property
    def source_label(self) -> str:
        label = f"{self.example:03d}{self.subexample}" if self.subexample else f"{self.example:03d}"
        return f"example {label}; extracted text page {self.page}"

    @property
    def xml_id(self) -> str:
        label = f"{self.example:03d}{self.subexample.upper()}" if self.subexample else f"{self.example:03d}"
        return f"AKIW_SZY_2012_EX_{label}"

    @property
    def tier_word_form(self) -> str:
        return self.word_form or self.form


@dataclass
class OcrLine:
    page: int
    left: float
    top: float
    right: float
    bottom: float
    text: str


@dataclass(frozen=True)
class SourceDecision:
    example: int
    subexample: str
    page: int | None
    seed_form: str
    corrected_form: str
    translation_zho: str
    aligned_gloss_tokens: tuple[str, ...]
    candidate_status: str
    source_judgement: str
    analysis_action: str
    note: str
    ocr_note: str


def load_source_decisions() -> dict[tuple[int, str], SourceDecision]:
    path = SOURCE_DATA_DIR / "numbered_source_decisions.csv"
    decisions: dict[tuple[int, str], SourceDecision] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (int(row["example"]), row["subexample"])
            if key in decisions:
                raise RuntimeError(f"Duplicate numbered source decision: {key}")
            glosses = tuple(json.loads(row["aligned_gloss_tokens_zho"])) if row["aligned_gloss_tokens_zho"] else ()
            decisions[key] = SourceDecision(
                example=key[0],
                subexample=key[1],
                page=int(row["page"]) if row["page"] else None,
                seed_form=row["seed_form"],
                corrected_form=row["corrected_form"],
                translation_zho=row["translation_zho"],
                aligned_gloss_tokens=glosses,
                candidate_status=row["candidate_status"],
                source_judgement=row["source_judgement"],
                analysis_action=row["analysis_action"],
                note=row["note"],
                ocr_note=row["ocr_note"],
            )
    return decisions


def load_gloss_cell_replacements() -> dict[str, str]:
    path = SOURCE_DATA_DIR / "gloss_cell_replacements.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    replacements = {row["ocr_text"]: row["source_text"] for row in rows}
    if len(replacements) != len(rows):
        raise RuntimeError("Duplicate OCR text in gloss_cell_replacements.csv")
    return replacements


SOURCE_DECISIONS = load_source_decisions()
GLOSS_CELL_REPLACEMENTS = load_gloss_cell_replacements()


def seed_candidates() -> list[Candidate]:
    candidates: list[Candidate] = []
    for decision in SOURCE_DECISIONS.values():
        if not decision.seed_form:
            continue
        if decision.page is None:
            raise RuntimeError(f"Seeded source example lacks a page: {decision.example}")
        candidates.append(
            Candidate(
                decision.page,
                decision.example,
                decision.subexample,
                decision.seed_form,
                decision.seed_form,
            )
        )
    return candidates


def correct_gloss_cell(text: str) -> str:
    corrected = text.lstrip("•：:")
    for bad, source_value in GLOSS_CELL_REPLACEMENTS.items():
        corrected = corrected.replace(bad, source_value)
    return corrected


def run_pdftotext(pdf_path: Path, txt_path: Path) -> None:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required on PATH")
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
        check=True,
        cwd=ROOT,
    )


def plausible_continuation(line: str) -> bool:
    text = line.strip()
    if not text or re.search(r"[\u4e00-\u9fff]", text):
        return False
    if re.match(r"^(\d+|[IVX]+|[A-Z]{2,}|[A-Z]+-|[-A-Z\s.]+)$", text):
        return False
    blocked = (
        "Shen",
        "Ferrell",
        "Ross",
        "Blust",
        "Tsukida",
        "Sakizaya",
        "Malay",
        "Austronesian",
        "Role",
        "agent",
        "patient",
        "instrument",
        "focus",
        "semantic",
        "inclusive",
        "exclusive",
        "common noun",
    )
    if text.startswith(blocked):
        return False
    return sum(ch.isalpha() and ord(ch) < 128 for ch in text) >= 3


def collect_continuations(lines: list[str], start: int) -> list[str]:
    out: list[str] = []
    blank_seen = 0
    for offset, raw in enumerate(lines[start : start + 10]):
        text = raw.strip()
        if re.match(r"^(\d{1,3}\s+)?[a-e]\.\s+", text):
            break
        if re.match(r"^\d{1,3}\s+[a-e]\.\s+", text):
            break
        if re.match(r"^\d{1,3}\s*$", text):
            break
        if not text:
            blank_seen += 1
            continue
        if plausible_continuation(text) and re.match(
            r"^(i|tu|nu|ni|ku|ci|sa|a|atu|han|kiyu|niza|maku|mita|kaku|kisu|"
            r"[a-zø*][A-Za-zø’'\-]+)\b",
            text,
        ):
            out.append(text)
            continue
        if blank_seen > 1 or offset > 4:
            break
    return out


def clean_form(text: str) -> str:
    replacements = {
        "’": "'",
        "‘": "'",
        "`": "'",
        "＇": "'",
        "…": "...",
    }
    cleaned = re.sub(r"\s+", " ", text).strip()
    for src, dst in replacements.items():
        cleaned = cleaned.replace(src, dst)
    cleaned = re.sub(r"\s+([.!?,;:])", r"\1", cleaned)
    cleaned = re.sub(r"\s+(\d{1,3})$", "", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def apply_manual_form_fixes(candidates: list[Candidate]) -> None:
    by_key = {(candidate.example, candidate.subexample): candidate for candidate in candidates}
    fixes = {
        key: decision
        for key, decision in SOURCE_DECISIONS.items()
        if decision.corrected_form
    }
    missing = sorted(set(fixes) - set(by_key))
    if missing:
        raise RuntimeError(f"Manual FORM fix targets were not extracted: {missing}")
    for key, decision in fixes.items():
        candidate = by_key[key]
        candidate.form = decision.corrected_form
        candidate.note = decision.note


def apply_source_form_decisions(candidates: list[Candidate]) -> None:
    """Apply source judgements and canonicalize the printed null marker."""

    by_key = {(candidate.example, candidate.subexample): candidate for candidate in candidates}
    for key, decision in SOURCE_DECISIONS.items():
        if decision.analysis_action != "canonical_null_prefix":
            continue
        zero = by_key.get(key)
        if zero is None or not zero.form.startswith(("ø-", "Ø-", "∅-")):
            raise RuntimeError(f"Source example no longer carries its null prefix: {key}")
        zero.form = re.sub(r"^[øØ∅]-", "∅-", zero.form, count=1)
        zero.word_form = zero.form
        zero.note = decision.note

    for candidate in candidates:
        key = (candidate.example, candidate.subexample)
        decision = SOURCE_DECISIONS.get(key)
        if decision and decision.candidate_status == "excluded_ungrammatical":
            if not candidate.form.startswith("*"):
                raise RuntimeError(f"Source-starred decision no longer has a star: {key}")
            candidate.source_judgement = decision.source_judgement
            candidate.form = re.sub(r"^\*\s*", "", candidate.form, count=1)
            candidate.word_form = candidate.form
            candidate.status = decision.candidate_status
            candidate.note = decision.note
        elif not candidate.word_form:
            candidate.word_form = candidate.form


def apply_manual_ocr_fixes(candidates: list[Candidate]) -> None:
    by_key = {(candidate.example, candidate.subexample): candidate for candidate in candidates}
    expected_keys = {
        key
        for key, decision in SOURCE_DECISIONS.items()
        if decision.translation_zho or decision.aligned_gloss_tokens
    }
    missing = sorted(expected_keys - set(by_key))
    if missing:
        raise RuntimeError(f"Manual OCR fix targets were not extracted: {missing}")

    for key in expected_keys:
        decision = SOURCE_DECISIONS[key]
        if decision.translation_zho:
            candidate = by_key[key]
            candidate.translation_zho = decision.translation_zho
            candidate.ocr_note = decision.ocr_note

    for candidate in candidates:
        key = (candidate.example, candidate.subexample)
        decision = SOURCE_DECISIONS.get(key)
        words = word_tokens(candidate.tier_word_form)
        if decision and decision.aligned_gloss_tokens:
            candidate.aligned_gloss_tokens = list(decision.aligned_gloss_tokens)
            if len(candidate.aligned_gloss_tokens) != len(words):
                raise RuntimeError(
                    f"Manual gloss alignment for {candidate.source_label} has "
                    f"{len(candidate.aligned_gloss_tokens)} cells for {len(words)} words"
                )
            note = "PDF page-image verified interlinear column alignment."
            candidate.ocr_note = f"{candidate.ocr_note} {note}".strip()
        else:
            candidate.aligned_gloss_tokens = (
                gloss_tokens(candidate.source_gloss, len(words))
                if candidate.source_gloss
                else []
            )
        candidate.aligned_gloss_tokens = [
            correct_gloss_cell(token) for token in candidate.aligned_gloss_tokens
        ]
        if candidate.aligned_gloss_tokens:
            candidate.source_gloss = " ".join(candidate.aligned_gloss_tokens)


def roman_key(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace("`", "'")
    text = text.replace("－", "-").replace("–", "-").replace("—", "-")
    return re.sub(r"[^a-zA-Z'\-]+", "", text).lower()


def clean_zho_translation(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.replace("_", "")
    cleaned = cleaned.replace("「", "").replace("」", "")
    cleaned = cleaned.replace("『", "").replace("』", "")
    cleaned = cleaned.replace("＂", "").replace('"', "")
    cleaned = cleaned.replace("“", "").replace("”", "")
    cleaned = cleaned.strip("' ")
    cleaned = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", cleaned)
    cleaned = re.sub(r"\s+([。！？!?，,；;：:])", r"\1", cleaned)
    cleaned = re.sub(r"([。！？!?])\s*[‘'`\"A-Za-z].*$", r"\1", cleaned)
    cleaned = re.sub(r"(?<=[。！？!?])\s*\d{1,3}$", "", cleaned)
    cleaned = re.sub(r"([「『])\s+", r"\1", cleaned)
    cleaned = re.sub(r"\s+([」』])", r"\1", cleaned)
    return cleaned.strip()


def clean_gloss_line(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.replace("－", "-").replace("–", "-").replace("—", "-")
    return cleaned.strip(" 。")


def ensure_vision_ocr_cache() -> None:
    required = VISION_OCR_DIR / "page-174.vision.tsv"
    if required.exists() and required.stat().st_size > 0:
        return
    script = ROOT / "CodeAndDocs/ocr_pages.py"
    subprocess.run([sys.executable, str(script), "--skip-tesseract"], check=True, cwd=ROOT)


def load_vision_lines(page: int) -> list[OcrLine]:
    path = VISION_OCR_DIR / f"page-{page:03d}.vision.tsv"
    if not path.exists():
        return []
    items: list[OcrLine] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            text = (row.get("text") or "").strip()
            if not text:
                continue
            items.append(
                OcrLine(
                    page=page,
                    left=float(row["left"]),
                    top=float(row["top"]),
                    right=float(row["right"]),
                    bottom=float(row["bottom"]),
                    text=text,
                )
            )
    if not items:
        return []

    lines: list[list[OcrLine]] = []
    for item in sorted(items, key=lambda item: (item.top, item.left)):
        if not lines:
            lines.append([item])
            continue
        current = lines[-1]
        current_top = min(piece.top for piece in current)
        current_bottom = max(piece.bottom for piece in current)
        overlap = min(current_bottom, item.bottom) - max(current_top, item.top)
        if abs(item.top - current_top) <= 28 or overlap > 20:
            current.append(item)
        else:
            lines.append([item])

    out: list[OcrLine] = []
    for pieces in lines:
        pieces = sorted(pieces, key=lambda item: item.left)
        text = " ".join(piece.text for piece in pieces)
        text = re.sub(r"\s+", " ", text).strip()
        out.append(
            OcrLine(
                page=page,
                left=min(piece.left for piece in pieces),
                top=min(piece.top for piece in pieces),
                right=max(piece.right for piece in pieces),
                bottom=max(piece.bottom for piece in pieces),
                text=text,
            )
        )
    return sorted(out, key=lambda line: (line.top, line.left))


def score_form_match(form: str, text: str) -> float:
    target = roman_key(form)
    observed = roman_key(text)
    if not target or not observed:
        return 0.0
    ratio = difflib.SequenceMatcher(None, target, observed).ratio()
    if target in observed or observed in target:
        ratio = max(ratio, min(len(target), len(observed)) / max(len(target), len(observed)))
    return ratio


def find_form_line(candidate: Candidate, lines: list[OcrLine]) -> tuple[int, int, float] | None:
    best: tuple[int, int, float] | None = None
    for start in range(len(lines)):
        for span in range(1, 4):
            end = start + span - 1
            if end >= len(lines):
                break
            combined = " ".join(line.text for line in lines[start : end + 1])
            # A form line can include OCR artifacts, but it should not be mostly Chinese.
            if len(re.findall(r"[\u4e00-\u9fff]", combined)) > len(combined) / 3:
                continue
            score = score_form_match(candidate.form, combined)
            if best is None or score > best[2]:
                best = (start, end, score)
    if best and best[2] >= 0.62:
        return best
    return None


def is_next_example_or_prose(line: str) -> bool:
    text = line.strip()
    if re.match(r"^([a-eA-EcC]\.|[（(]\s*\d{1,3}\s*[）)])", text):
        return True
    return text.startswith(("在例", "例句", "表", "前綴", "後綴", "而", "因此", "由於"))


def looks_like_translation(text: str, *, first_after_form: bool) -> bool:
    raw = text.strip()
    cleaned = clean_zho_translation(raw)
    if not cleaned or not re.search(r"[\u4e00-\u9fff]", cleaned):
        return False
    has_open_quote = "「" in raw or "『" in raw
    has_close_quote = "」" in raw or "』" in raw
    if has_open_quote:
        return True
    if has_close_quote and ("-" in raw or "主格" in raw or "屬格" in raw or "斜格" in raw):
        return False
    if has_close_quote:
        return True
    if first_after_form:
        return False
    if is_next_example_or_prose(raw):
        return False
    if len(cleaned) > 90:
        return False
    if re.search(r"[A-Za-z]{3,}", cleaned) and len(re.findall(r"[\u4e00-\u9fff]", cleaned)) < 6:
        return False
    return bool(re.search(r"[。！？!?]$", cleaned))


def enrich_candidates_from_ocr(candidates: list[Candidate]) -> None:
    ensure_vision_ocr_cache()
    lines_by_page: dict[int, list[OcrLine]] = {}
    for candidate in candidates:
        if candidate.page not in lines_by_page:
            lines_by_page[candidate.page] = load_vision_lines(candidate.page)

    for candidate in candidates:
        if candidate.source_judgement:
            candidate.ocr_note = (
                "Source provides no aligned translation or gloss for this judged example; "
                "nearby prose is intentionally not attached."
            )
            continue
        lines = lines_by_page.get(candidate.page, [])
        match = find_form_line(candidate, lines)
        if not match:
            candidate.ocr_note = "No OCR form-line match."
            continue
        _, form_end, score = match
        candidate.ocr_match_score = score
        following = lines[form_end + 1 : min(len(lines), form_end + 8)]
        translation_index: int | None = None
        for offset, line in enumerate(following):
            if offset > 0 and is_next_example_or_prose(line.text):
                break
            if looks_like_translation(line.text, first_after_form=(offset == 0)):
                candidate.translation_zho = clean_zho_translation(line.text)
                translation_index = offset
                break
        gloss_candidates = following[:translation_index] if translation_index is not None else following[:2]
        gloss_parts = []
        for line in gloss_candidates:
            text = clean_gloss_line(line.text)
            if not text or "「" in text or "」" in text:
                continue
            if re.search(r"[\u4e00-\u9fff]", text) or "-" in text:
                gloss_parts.append(text)
        candidate.raw_ocr_gloss = " / ".join(gloss_parts)
        candidate.source_gloss = candidate.raw_ocr_gloss
        if not candidate.translation_zho:
            candidate.ocr_note = "No OCR Mandarin translation found after form line."


def extract_candidates(scan_text: str) -> list[Candidate]:
    pages = scan_text.split("\f")
    candidates = seed_candidates()
    current_example: int | None = None
    current_page: int | None = None

    for page_no, page in enumerate(pages, 1):
        if page_no < 38 or page_no > 155:
            continue
        lines = page.splitlines()
        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            numbered = re.match(r"^(\d{1,3})\s+([a-e])\.\s+(.+)$", line)
            if numbered and 17 <= int(numbered.group(1)) <= 126:
                example = int(numbered.group(1))
                subexample = numbered.group(2)
                raw_form = " ".join([numbered.group(3).strip()] + collect_continuations(lines, index + 1))
                candidates.append(
                    Candidate(page_no, example, subexample, clean_form(raw_form), raw_form)
                )
                current_example = example
                current_page = page_no
                continue

            subonly = re.match(r"^([a-e])\.\s+(.+)$", line)
            if (
                subonly
                and current_example is not None
                and current_page is not None
                and page_no <= current_page + 1
            ):
                raw_form = " ".join([subonly.group(2).strip()] + collect_continuations(lines, index + 1))
                candidates.append(
                    Candidate(page_no, current_example, subonly.group(1), clean_form(raw_form), raw_form)
                )

    return candidates


def classify_candidates(candidates: list[Candidate]) -> list[Candidate]:
    seen_forms: dict[str, Candidate] = {}
    for candidate in candidates:
        if candidate.status != "include":
            continue
        if len(candidate.form.split()) < 2:
            raise RuntimeError(f"Unexpected non-sentence source row: {candidate.source_label}")
        first = seen_forms.get(candidate.form)
        if first is not None:
            candidate.status = "excluded_exact_repeat"
            candidate.retained_xml_id = first.xml_id
            duplicate_note = (
                f"Exact source-form repeat of {first.source_label}; represented by "
                f"{first.xml_id}. This row's source translation and gloss remain in the ledger."
            )
            candidate.note = f"{candidate.note} {duplicate_note}".strip()
        else:
            seen_forms[candidate.form] = candidate

    # These source forms differ in the printed analytical boundary. Preserve
    # both originals even though shared standardization correctly converges.
    by_key = {(candidate.example, candidate.subexample): candidate for candidate in candidates}
    standard_collision = by_key[(82, "a")]
    retained = by_key[(69, "a")]
    if standard_collision.form != "mulusu' ku tanang nay zais." or retained.form != "mu-lusu' ku tanang nay zais.":
        raise RuntimeError("Reviewed examples 69a/82a standard-tier collision changed")
    standard_collision.note = (
        "PDF page-image verified source-distinct unsegmented occurrence; retained under "
        "its own source ID. Its derived standard S tier intentionally matches segmented "
        "example 69a."
    )
    return candidates


def add_source_morpheme_decisions(sentence: ET.Element, candidate: Candidate) -> None:
    decision = SOURCE_DECISIONS.get((candidate.example, candidate.subexample))
    if decision is None or decision.analysis_action != "canonical_null_prefix":
        return
    null_words = [
        word
        for word in sentence.findall("W")
        if (form := word.find('./FORM[@kindOf="original"]')) is not None
        and (form.text or "").startswith("∅-")
    ]
    if len(null_words) != 1:
        raise RuntimeError(
            f"Expected one null-prefixed W for {candidate.source_label}; found {len(null_words)}"
        )
    word = null_words[0]
    if word.findall("M"):
        raise RuntimeError(f"Null-prefixed W already has an M analysis: {candidate.source_label}")
    word_form = word.find('./FORM[@kindOf="original"]')
    assert word_form is not None and word_form.text is not None
    root_form = word_form.text.removeprefix("∅-")
    word_index = sentence.findall("W").index(word)
    root_gloss = (
        candidate.aligned_gloss_tokens[word_index]
        if word_index < len(candidate.aligned_gloss_tokens)
        else ""
    )

    null_m = ET.SubElement(word, "M", {"id": f"{word.attrib['id']}M1"})
    add_form_pair(null_m, "∅")
    root_m = ET.SubElement(word, "M", {"id": f"{word.attrib['id']}M2"})
    add_form_pair(root_m, root_form)
    if root_gloss:
        add_translation(root_m, root_gloss, kind_of="original")


def write_report(candidates: list[Candidate]) -> None:
    REPORT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "status",
                "example",
                "subexample",
                "page",
                "form",
                "word_form",
                "raw_form",
                "source_judgement",
                "retained_xml_id",
                "translation_zho",
                "raw_ocr_gloss",
                "source_gloss",
                "aligned_gloss_tokens_zho",
                "ocr_match_score",
                "ocr_note",
                "note",
            ],
        )
        writer.writeheader()
        for candidate in candidates:
            writer.writerow(
                {
                    "status": candidate.status,
                    "example": candidate.example,
                    "subexample": candidate.subexample,
                    "page": candidate.page,
                    "form": candidate.form,
                    "word_form": candidate.tier_word_form,
                    "raw_form": candidate.raw_form,
                    "source_judgement": candidate.source_judgement,
                    "retained_xml_id": candidate.retained_xml_id,
                    "translation_zho": candidate.translation_zho,
                    "raw_ocr_gloss": candidate.raw_ocr_gloss,
                    "source_gloss": candidate.source_gloss,
                    "aligned_gloss_tokens_zho": json.dumps(
                        candidate.aligned_gloss_tokens,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "ocr_match_score": f"{candidate.ocr_match_score:.3f}" if candidate.ocr_match_score else "",
                    "ocr_note": candidate.ocr_note,
                    "note": candidate.note,
                }
            )


def write_xml(candidates: list[Candidate]) -> None:
    XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element(
        "TEXT",
        {
            "id": "AKIW_SZY_2012_SAKIZAYA_AFFIXES_EXAMPLES",
            "citation": (
                "Akiw, Chung-Wen Hsu. 2012. The Study of Affixes in Sakizaya. "
                "Master's thesis, National Dong Hwa University."
            ),
            "BibTeX_citation": (
                "@mastersthesis{Akiw_2012_Sakizaya_Affixes, "
                "author = {Akiw, Chung-Wen Hsu}, "
                "title = {The Study of Affixes in Sakizaya}, "
                "school = {National Dong Hwa University}, "
                "year = {2012}}"
            ),
            "copyright": (
                "Author permission recorded on Basecamp card 8176965975; "
                "private development corpus pending maintainer port-in approval."
            ),
            f"{{{XML_NS}}}lang": "szy",
            "source": (
                "akiw_2012_sakizaya_affixes_scan.pdf; numbered Sakizaya examples; "
                "SHA-256 fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee"
            ),
            "glottocode": "saki1247",
            "dialect": "Sakizaya",
        },
    )
    for candidate in candidates:
        if candidate.status != "include":
            continue
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": candidate.xml_id,
                "source": f"PDF page {candidate.page}; example {candidate.example}{candidate.subexample}",
            },
        )
        add_form_pair(
            sentence,
            candidate.form,
            original_notes=candidate.source_judgement,
        )
        if candidate.translation_zho:
            add_translation(sentence, candidate.translation_zho)
        add_word_tiers(
            sentence,
            candidate.xml_id,
            candidate.tier_word_form,
            candidate.source_gloss,
            candidate.aligned_gloss_tokens,
        )
        add_source_morpheme_decisions(sentence, candidate)

    ET.indent(root, space="    ")
    tree = ET.ElementTree(root)
    tree.write(XML_PATH, encoding="utf-8", xml_declaration=True)


def main() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    run_pdftotext(SOURCE_SCAN, SCAN_TEXT)
    if SOURCE_OCR.exists():
        run_pdftotext(SOURCE_OCR, OCR_TEXT)
    candidates = extract_candidates(SCAN_TEXT.read_text(encoding="utf-8", errors="ignore"))
    apply_manual_form_fixes(candidates)
    apply_source_form_decisions(candidates)
    candidates = classify_candidates(candidates)
    enrich_candidates_from_ocr(candidates)
    apply_manual_ocr_fixes(candidates)
    write_report(candidates)
    write_xml(candidates)
    print(f"Wrote {XML_PATH}")
    print(f"Wrote {REPORT_CSV}")
    print(f"Included {sum(1 for item in candidates if item.status == 'include')} XML sentences")


if __name__ == "__main__":
    main()
