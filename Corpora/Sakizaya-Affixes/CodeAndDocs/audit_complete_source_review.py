#!/usr/bin/env python3
"""Account for every source unit against original-scan evidence and final XML."""

from __future__ import annotations

import csv
from functools import cache
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from review_policy import EXPERT_REVIEW_STATUS, effective_status


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "CodeAndDocs"
PRIVATE = ROOT / "Private"
XML_ROOT = ROOT / "XML/szy"
SOURCE_PDF = PRIVATE / "source/akiw_2012_sakizaya_affixes_scan.pdf"
SCAN_TEXT = PRIVATE / "cache/scan_text_layer.txt"
REPORT_CSV = CODE / "complete_source_review.csv"
SOURCE_SHA256 = "fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

REPORTS = (
    ("numbered", CODE / "extraction_report.csv"),
    ("inventory", CODE / "table_extraction_report.csv"),
    ("late", CODE / "summary_table_extraction_report.csv"),
)
EXPECTED_SOURCE_COUNTS = {"numbered": 261, "inventory": 434, "late": 113}
EXPECTED_INCLUDED_COUNTS = {"numbered": 238, "inventory": 432, "late": 0}
MANUAL_EDITS = CODE / "manual_edits.xml"

# These six long examples wrap across independent OCR regions. Their source
# forms and interlinear alignment were adjudicated directly from the page image.
IMAGE_REVIEWED_LATIN_EXCEPTIONS = {
    "numbered:19b": "Page image 39 reviewed; the sentence wraps before ca-cudad-an.",
    "numbered:31b": "Page image 64 reviewed; the sentence wraps before maku a tudem.",
    "numbered:92b": "Page image 124 reviewed; the sentence wraps before pa-pelu.",
    "numbered:106c": "Page image 136 reviewed; the sentence wraps before lima-ay.",
    "numbered:107a": "Page image 137 reviewed; the sentence wraps before ni-ka-tanektek.",
    "numbered:114b": "Page image 142 reviewed; the sentence wraps before pa-saluimeng-en.",
}

CORRUPTED_AUTHORITATIVE_TEXT = re.compile(
    r"靥格|麕格|麡格|闓格|齏格|𪊽格|蟨格|麠格|檕詞|刹格|科格|"
    r"肩牓|長痚瘡|文且|文亘|交旦|寫主|流哦|探收|桑甚|補不到|艹|"
    r"lbun|生產[\"']"
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def normalized_latin(text: str) -> str:
    normalized = text.lower().replace("’", "'").replace("‘", "'").replace("`", "'")
    return re.sub(r"[^a-z']", "", normalized)


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u3400-\u9fff]", text))


def numbered_label(row: dict[str, str]) -> str:
    return f"{int(row['example'])}{row['subexample']}"


def numbered_xml_id(row: dict[str, str]) -> str:
    suffix = f"{int(row['example']):03d}{row['subexample'].upper()}"
    return f"AKIW_SZY_2012_EX_{suffix}"


def source_unit(kind: str, row: dict[str, str]) -> str:
    if kind == "numbered":
        return f"numbered:{numbered_label(row)}"
    return f"{kind}:{int(row['seq'])}"


def expected_xml_id(kind: str, row: dict[str, str]) -> str:
    if kind == "numbered":
        return numbered_xml_id(row)
    prefix = "TABLE" if kind == "inventory" else "SUMMARY"
    return f"AKIW_SZY_2012_{prefix}_ROW_{int(row['seq']):03d}"


def expected_locator(kind: str, row: dict[str, str]) -> str:
    page = int(row["page"])
    if kind == "numbered":
        return f"PDF page {page}; example {numbered_label(row)}"
    if kind == "inventory":
        return f"PDF page {page}; affix inventory row {int(row['seq'])}"
    return f"PDF page {page}; {row['source_table']} row {int(row['seq'])}"


def authoritative_chinese(kind: str, row: dict[str, str]) -> list[str]:
    if kind == "numbered":
        if row["source_judgement"]:
            return []
        glosses = json.loads(row["aligned_gloss_tokens_zho"])
        return [row["translation_zho"], row["source_gloss"], *glosses]
    return [row["meaning_zho"], row["base_meaning_zho"], row["affix_function_zho"]]


def chinese_review_basis(kind: str, row: dict[str, str]) -> str:
    if kind == "numbered" and row["source_judgement"]:
        return "Page-image reviewed source-starred judgment; the source prints no translation or gloss."
    if kind == "numbered":
        return "Original-scan text and Vision evidence; OCR repairs and aligned Mandarin gloss cells are explicit in the extraction ledger."
    if kind == "inventory":
        return "Original-page Vision/Tesseract evidence; row fields are retained in the ledger and every OCR repair is explicit and page-image adjudicated."
    return "All late-table pages were visually reviewed; the source meaning is transcribed per row and retained independently from earlier repeats."


def read_page_evidence() -> dict[int, str]:
    embedded_pages = SCAN_TEXT.read_text(encoding="utf-8", errors="replace").split("\f")
    return {
        page: normalized_latin(embedded_pages[page - 1])
        for page in range(1, 175)
    }


def read_xml() -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for path in sorted(XML_ROOT.glob("*.xml")):
        for sentence in ET.parse(path).getroot().findall("S"):
            sid = sentence.attrib["id"]
            if sid in rows:
                raise RuntimeError(f"Duplicate XML ID: {sid}")
            original = sentence.find('./FORM[@kindOf="original"]')
            translations = [
                {
                    "text": transl.text or "",
                    "ver": transl.attrib.get("ver", ""),
                    "notes": transl.attrib.get("notes", ""),
                }
                for transl in sentence.findall("TRANSL")
                if transl.attrib.get(XML_LANG) == "zho"
                and not transl.attrib.get("kindOf", "")
            ]
            rows[sid] = {
                "original": original.text if original is not None else "",
                "original_notes": original.attrib.get("notes", "") if original is not None else "",
                "source": sentence.attrib.get("source", ""),
                "translations": translations,
                "word_glosses": [
                    next(
                        (
                            transl.text or ""
                            for transl in word.findall("TRANSL")
                            if transl.attrib.get(XML_LANG) == "zho"
                        ),
                        "",
                    )
                    for word in sentence.findall("W")
                ],
            }
    return rows


@cache
def manually_reviewed_ids() -> set[str]:
    return {
        sentence.attrib["id"]
        for sentence in ET.parse(MANUAL_EDITS).getroot().findall(".//S")
        if sentence.attrib.get("action") != "delete"
    }


def audit_row(
    kind: str,
    row: dict[str, str],
    page_evidence: dict[int, str],
    xml_rows: dict[str, dict[str, object]],
) -> dict[str, str]:
    unit = source_unit(kind, row)
    page = int(row["page"])
    form = row["form"]
    status = effective_status(kind, row)
    xml_id = (
        expected_xml_id(kind, row)
        if status == "include"
        else row["retained_xml_id"] if status == "excluded_exact_repeat" else ""
    )
    xml = xml_rows.get(xml_id)
    reviewed_ids = manually_reviewed_ids()
    checks: list[str] = []
    notes: list[str] = []

    latin_form = normalized_latin(form)
    exact_latin = bool(latin_form) and latin_form in page_evidence.get(page, "")
    if exact_latin:
        latin_score = "1.000"
    elif unit in IMAGE_REVIEWED_LATIN_EXCEPTIONS:
        score = float(row.get("ocr_match_score", "0") or 0)
        latin_score = f"{score:.3f}"
        if score < 0.85:
            checks.append("manual_latin_review_score_below_threshold")
        notes.append(IMAGE_REVIEWED_LATIN_EXCEPTIONS[unit])
    else:
        latin_score = "0.000"
        checks.append("form_not_found_in_original_page_evidence")

    if status not in {
        "include",
        "excluded_exact_repeat",
        "excluded_ungrammatical",
        EXPERT_REVIEW_STATUS,
    }:
        checks.append("unsupported_disposition")
    if not (1 <= page <= 174):
        checks.append("page_out_of_range")
    if not latin_form:
        checks.append("source_form_has_no_latin_text")

    chinese_fields = authoritative_chinese(kind, row)
    if kind == "numbered" and row["source_judgement"]:
        if row["translation_zho"] or row["source_gloss"] or json.loads(
            row["aligned_gloss_tokens_zho"]
        ):
            checks.append("source_judgment_has_invented_translation_or_gloss")
    else:
        if not all(chinese_fields) or not has_cjk(" ".join(chinese_fields)):
            checks.append("missing_authoritative_chinese_field")
        if any(CORRUPTED_AUTHORITATIVE_TEXT.search(text) for text in chinese_fields):
            checks.append("known_ocr_corruption_in_authoritative_field")

    if kind == "numbered" and not row["source_judgement"]:
        aligned = json.loads(row["aligned_gloss_tokens_zho"])
        if len(aligned) != len(row["word_form"].split()):
            checks.append("word_gloss_alignment_count_mismatch")

    if status in {"excluded_ungrammatical", EXPERT_REVIEW_STATUS}:
        if xml_id:
            checks.append("excluded_row_has_retained_xml_link")
        if expected_xml_id(kind, row) in xml_rows:
            checks.append("excluded_row_present_in_xml")
    elif xml is None:
        checks.append("xml_target_missing")
    else:
        if xml["original"] != form and xml_id not in reviewed_ids:
            checks.append("xml_original_mismatch")
        if status == "include":
            if xml["source"] != expected_locator(kind, row):
                checks.append("xml_source_locator_mismatch")
            primary = next(
                (
                    item["text"]
                    for item in xml["translations"]
                    if not item["ver"]
                ),
                "",
            )
            expected_translation = (
                row["translation_zho"] if kind == "numbered" else row["meaning_zho"]
            )
            if primary != expected_translation and xml_id not in reviewed_ids:
                checks.append("xml_primary_translation_mismatch")
            if kind == "numbered" and not row["source_judgement"]:
                expected_glosses = json.loads(row["aligned_gloss_tokens_zho"])
                if (
                    xml["word_glosses"] != expected_glosses
                    and xml_id not in reviewed_ids
                ):
                    checks.append("xml_word_gloss_mismatch")
            if kind == "numbered":
                if xml["original_notes"] != row["source_judgement"]:
                    checks.append("xml_source_judgment_mismatch")
        elif kind != "numbered":
            retained_translations = [item["text"] for item in xml["translations"]]
            if row["meaning_zho"] not in retained_translations:
                checks.append("repeated_source_meaning_not_retained")

    if row.get("note"):
        notes.append(row["note"])
    if status == "include":
        disposition = "included"
    elif status == "excluded_exact_repeat":
        disposition = f"excluded exact repeat; retained as {xml_id}"
    elif status == "excluded_ungrammatical":
        disposition = "excluded source-starred ungrammatical example under POL-016"
    else:
        disposition = "excluded after expert review; not admitted to release XML"
    return {
        "source_kind": kind,
        "source_unit": unit,
        "pdf_page": str(page),
        "source_form": form,
        "latin_match_score": latin_score,
        "chinese_review_basis": chinese_review_basis(kind, row),
        "xml_disposition": disposition,
        "xml_id": xml_id,
        "result": "pass" if not checks else "fail",
        "notes": "; ".join([*checks, *notes]),
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    global_errors: list[str] = []
    actual_hash = hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest()
    if actual_hash != SOURCE_SHA256:
        global_errors.append(f"Source SHA-256 mismatch: {actual_hash}")

    page_evidence = read_page_evidence()
    xml_rows = read_xml()
    rows: list[dict[str, str]] = []
    expected_xml_ids: set[str] = set()
    used_units: set[str] = set()
    for kind, path in REPORTS:
        report_rows = read_csv(path)
        if len(report_rows) != EXPECTED_SOURCE_COUNTS[kind]:
            global_errors.append(
                f"{kind} source count is {len(report_rows)}, expected {EXPECTED_SOURCE_COUNTS[kind]}"
            )
        include_count = sum(effective_status(kind, row) == "include" for row in report_rows)
        if include_count != EXPECTED_INCLUDED_COUNTS[kind]:
            global_errors.append(
                f"{kind} include count is {include_count}, expected {EXPECTED_INCLUDED_COUNTS[kind]}"
            )
        for row in report_rows:
            unit = source_unit(kind, row)
            if unit in used_units:
                global_errors.append(f"Duplicate source unit: {unit}")
            used_units.add(unit)
            if effective_status(kind, row) == "include":
                expected_xml_ids.add(expected_xml_id(kind, row))
            rows.append(audit_row(kind, row, page_evidence, xml_rows))

    if {int(row["source_unit"].split(":")[1]) for row in rows if row["source_kind"] == "inventory"} != set(range(1, 435)):
        global_errors.append("Inventory row sequence is not exactly 1-434")
    if {int(row["source_unit"].split(":")[1]) for row in rows if row["source_kind"] == "late"} != set(range(435, 548)):
        global_errors.append("Late-table row sequence is not exactly 435-547")
    if len(rows) != 808:
        global_errors.append(f"Source unit total is {len(rows)}, expected 808")
    if len(expected_xml_ids) != 670:
        global_errors.append(f"Expected XML ID total is {len(expected_xml_ids)}, expected 670")
    if set(xml_rows) != expected_xml_ids:
        missing = sorted(expected_xml_ids - set(xml_rows))
        extra = sorted(set(xml_rows) - expected_xml_ids)
        global_errors.append(f"XML/report ID mismatch; missing={missing}; extra={extra}")
    sources = [str(row["source"]) for row in xml_rows.values()]
    if any(not source for source in sources) or len(sources) != len(set(sources)):
        global_errors.append("XML source locators are missing or non-unique")
    used_exceptions = {
        row["source_unit"]
        for row in rows
        if row["source_unit"] in IMAGE_REVIEWED_LATIN_EXCEPTIONS
        and row["latin_match_score"] != "1.000"
    }
    if used_exceptions != set(IMAGE_REVIEWED_LATIN_EXCEPTIONS):
        global_errors.append("The explicit Latin page-image exception set is stale")

    write_csv(rows)
    failures = sum(row["result"] != "pass" for row in rows)
    print(f"complete source review rows: {len(rows)}")
    print(f"complete source review failures: {failures + len(global_errors)}")
    if failures or global_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
