#!/usr/bin/env python3
"""Audit table extraction reports against generated FormosanBank XML."""

from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLE_REPORT = ROOT / "CodeAndDocs/table_extraction_report.csv"
TABLE_XML = ROOT / "XML/szy/akiw_2012_sakizaya_affixes_table_rows.xml"
SUMMARY_REPORT = ROOT / "CodeAndDocs/summary_table_extraction_report.csv"
SUMMARY_XML = ROOT / "XML/szy/akiw_2012_sakizaya_affixes_summary_rows.xml"
AUDIT_CSV = ROOT / "CodeAndDocs/table_output_audit.csv"


def read_report(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_xml(path: Path) -> dict[str, dict[str, str]]:
    root = ET.parse(path).getroot()
    rows: dict[str, dict[str, str]] = {}
    for sentence in root.findall("S"):
        forms = {
            form.attrib.get("kindOf", ""): form.text or ""
            for form in sentence.findall("FORM")
        }
        translations = []
        for transl in sentence.findall("TRANSL"):
            translations.append(
                {
                    "lang": transl.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", ""),
                    "kindOf": transl.attrib.get("kindOf", ""),
                    "ver": transl.attrib.get("ver", ""),
                    "text": transl.text or "",
                }
            )
        rows[sentence.attrib["id"]] = {
            "s_attrs": ",".join(sorted(sentence.attrib)),
            "source": sentence.attrib.get("source", ""),
            "original": forms.get("original", ""),
            "standard": forms.get("standard", ""),
            "phon_count": str(len(sentence.findall("PHON"))),
            "w_count": str(len(sentence.findall("W"))),
            "zho_translation": next(
                (
                    item["text"]
                    for item in translations
                    if item["lang"] == "zho" and not item["kindOf"] and not item["ver"]
                ),
                "",
            ),
            "zho_alternates": [
                item["text"]
                for item in translations
                if item["lang"] == "zho" and item["ver"] == "alt"
            ],
            "source_sidecar_count": str(
                sum(1 for item in translations if item["kindOf"].startswith("source_"))
            ),
            "w_original": "",
            "w_translation": "",
            "s_original_notes": "",
            "w_original_notes": "",
            "m_count": "0",
            "affix_m_original": "",
            "affix_m_translation": "",
            "root_m_original": "",
            "root_m_translation": "",
        }
        s_original = sentence.find('./FORM[@kindOf="original"]')
        if s_original is not None:
            rows[sentence.attrib["id"]]["s_original_notes"] = s_original.attrib.get(
                "notes", ""
            )
        word = sentence.find("W")
        if word is not None:
            w_forms = {
                form.attrib.get("kindOf", ""): form.text or ""
                for form in word.findall("FORM")
            }
            rows[sentence.attrib["id"]]["w_original"] = w_forms.get("original", "")
            rows[sentence.attrib["id"]]["w_translation"] = next(
                (
                    transl.text or ""
                    for transl in word.findall("TRANSL")
                    if transl.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "") == "zho"
                ),
                "",
            )
            w_original = word.find('./FORM[@kindOf="original"]')
            if w_original is not None:
                rows[sentence.attrib["id"]]["w_original_notes"] = w_original.attrib.get(
                    "notes", ""
                )
            morphemes = word.findall("M")
            rows[sentence.attrib["id"]]["m_count"] = str(len(morphemes))
            for label, morpheme in zip(("affix", "root"), morphemes):
                m_original = morpheme.find('./FORM[@kindOf="original"]')
                m_translation = next(
                    (
                        transl.text or ""
                        for transl in morpheme.findall("TRANSL")
                        if transl.attrib.get("{http://www.w3.org/XML/1998/namespace}lang", "")
                        == "zho"
                    ),
                    "",
                )
                rows[sentence.attrib["id"]][f"{label}_m_original"] = (
                    (m_original.text or "") if m_original is not None else ""
                )
                rows[sentence.attrib["id"]][f"{label}_m_translation"] = m_translation
    return rows


def audit_dataset(
    dataset: str,
    report_rows: list[dict[str, str]],
    xml_rows: dict[str, dict[str, str]],
    id_prefix: str,
) -> list[dict[str, str]]:
    audit: list[dict[str, str]] = []
    report_ids: set[str] = set()

    for row in report_rows:
        xml_id = f"{id_prefix}{int(row['seq']):03d}"
        report_ids.add(xml_id)
        xml = xml_rows.get(xml_id)
        expected_present = row["status"] == "include"
        actual_present = xml is not None
        checks: list[str] = []

        if expected_present != actual_present:
            checks.append("presence_mismatch")
        if expected_present and xml:
            expected_source = (
                f"PDF page {int(row['page'])}; affix inventory row {int(row['seq'])}"
                if dataset == "table"
                else f"PDF page {int(row['page'])}; {row['source_table']} row {int(row['seq'])}"
            )
            if xml["original"] != row["form"]:
                checks.append("original_mismatch")
            if not xml["standard"]:
                checks.append("standard_missing")
            if xml["zho_translation"] != row["meaning_zho"]:
                checks.append("translation_mismatch")
            if xml["s_attrs"] != "id,source":
                checks.append("nonstandard_s_attributes")
            if xml["source"] != expected_source:
                checks.append("source_locator_mismatch")
            if xml["source_sidecar_count"] != "0":
                checks.append("source_sidecar_on_s")
            if xml["w_count"] != "1":
                checks.append("w_count_mismatch")
            if xml["w_original"] != row["form"]:
                checks.append("w_original_mismatch")
            if xml["w_translation"] != row["meaning_zho"]:
                checks.append("w_translation_mismatch")
            if xml["phon_count"] != "2":
                checks.append("phon_count_mismatch")
            if dataset in {"table", "summary"}:
                if xml["s_original_notes"] or xml["w_original_notes"]:
                    checks.append("linguistic_data_in_form_notes")
                if xml["m_count"] != "2":
                    checks.append("m_count_mismatch")
                if xml["affix_m_original"] != row["affix_form"]:
                    checks.append("affix_m_form_mismatch")
                if xml["affix_m_translation"] != row["affix_function_zho"]:
                    checks.append("affix_m_translation_mismatch")
                if xml["root_m_original"] != row["base_form"]:
                    checks.append("root_m_form_mismatch")
                if xml["root_m_translation"] != row["base_meaning_zho"]:
                    checks.append("root_m_translation_mismatch")

        audit.append(
            {
                "dataset": dataset,
                "xml_id": xml_id,
                "source_status": row["status"],
                "xml_present": "true" if actual_present else "false",
                "original_matches_report": (
                    "true" if expected_present and xml and xml["original"] == row["form"] else ""
                ),
                "standard_present": "true" if expected_present and xml and bool(xml["standard"]) else "",
                "translation_matches_report": (
                    "true" if expected_present and xml and xml["zho_translation"] == row["meaning_zho"] else ""
                ),
                "s_attrs": xml["s_attrs"] if xml else "",
                "source": xml["source"] if xml else "",
                "w_count": xml["w_count"] if xml else "0",
                "w_original_matches_report": (
                    "true" if expected_present and xml and xml["w_original"] == row["form"] else ""
                ),
                "w_translation_matches_report": (
                    "true" if expected_present and xml and xml["w_translation"] == row["meaning_zho"] else ""
                ),
                "source_sidecar_count": xml["source_sidecar_count"] if xml else "0",
                "phon_count": xml["phon_count"] if xml else "0",
                "m_count": xml["m_count"] if xml else "0",
                "affix_m_matches_report": (
                    "true"
                    if dataset in {"table", "summary"}
                    and expected_present
                    and xml
                    and xml["affix_m_original"] == row["affix_form"]
                    and xml["affix_m_translation"] == row["affix_function_zho"]
                    else ""
                ),
                "root_m_matches_report": (
                    "true"
                    if dataset in {"table", "summary"}
                    and expected_present
                    and xml
                    and xml["root_m_original"] == row["base_form"]
                    and xml["root_m_translation"] == row["base_meaning_zho"]
                    else ""
                ),
                "audit_status": "pass" if not checks else "fail",
                "notes": "; ".join(checks) if checks else row.get("note", ""),
            }
        )

    for xml_id in sorted(set(xml_rows) - report_ids):
        audit.append(
            {
                "dataset": dataset,
                "xml_id": xml_id,
                "source_status": "missing_report_row",
                "xml_present": "true",
                "original_matches_report": "",
                "standard_present": "",
                "translation_matches_report": "",
                "s_attrs": "",
                "source": xml_rows[xml_id]["source"],
                "w_count": "",
                "w_original_matches_report": "",
                "w_translation_matches_report": "",
                "source_sidecar_count": "",
                "phon_count": xml_rows[xml_id]["phon_count"],
                "m_count": xml_rows[xml_id]["m_count"],
                "affix_m_matches_report": "",
                "root_m_matches_report": "",
                "audit_status": "fail",
                "notes": "xml_row_missing_from_report",
            }
        )

    return audit


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "dataset",
        "xml_id",
        "source_status",
        "xml_present",
        "original_matches_report",
        "standard_present",
        "translation_matches_report",
        "s_attrs",
        "source",
        "w_count",
        "w_original_matches_report",
        "w_translation_matches_report",
        "source_sidecar_count",
        "phon_count",
        "m_count",
        "affix_m_matches_report",
        "root_m_matches_report",
        "audit_status",
        "notes",
    ]
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    table_report = read_report(TABLE_REPORT)
    summary_report = read_report(SUMMARY_REPORT)
    rows = []
    rows.extend(
        audit_dataset(
            "table",
            table_report,
            read_xml(TABLE_XML),
            "AKIW_SZY_2012_TABLE_ROW_",
        )
    )
    all_xml_rows: dict[str, dict[str, str]] = {}
    for xml_path in sorted((ROOT / "XML/szy").glob("*.xml")):
        all_xml_rows.update(read_xml(xml_path))
    for dataset, report in (("table", table_report), ("summary", summary_report)):
        for report_row in report:
            if report_row["status"] != "excluded_exact_repeat":
                continue
            retained = all_xml_rows.get(report_row["retained_xml_id"])
            if retained is None or retained["original"] != report_row["form"]:
                raise SystemExit(
                    f"{dataset} row {report_row['seq']} does not link to its exact retained FORM"
                )
            if (
                report_row["meaning_zho"] != retained["zho_translation"]
                and report_row["meaning_zho"] not in retained["zho_alternates"]
            ):
                raise SystemExit(
                    f"{dataset} row {report_row['seq']} distinct meaning is missing as an alternate translation"
                )
    rows.extend(
        audit_dataset(
            "summary",
            summary_report,
            read_xml(SUMMARY_XML),
            "AKIW_SZY_2012_SUMMARY_ROW_",
        )
    )
    write_csv(rows)
    failures = sum(1 for row in rows if row["audit_status"] != "pass")
    print(f"table output audit rows: {len(rows)}")
    print(f"table output audit failures: {failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
