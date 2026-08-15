#!/usr/bin/env python3
"""Audit extraction rows against generated FormosanBank XML."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_CSV = ROOT / "CodeAndDocs/extraction_report.csv"
XML_PATH = ROOT / "XML/szy/akiw_2012_sakizaya_affixes_examples.xml"
AUDIT_CSV = ROOT / "CodeAndDocs/source_alignment_audit.csv"


def example_id(example: str, subexample: str) -> str:
    label = f"{int(example):03d}{subexample.upper()}" if subexample else f"{int(example):03d}"
    return f"AKIW_SZY_2012_EX_{label}"


def read_report_rows() -> list[dict[str, str]]:
    with REPORT_CSV.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_xml_rows() -> dict[str, dict[str, str]]:
    root = ET.parse(XML_PATH).getroot()
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
                    "text": transl.text or "",
                }
            )
        rows[sentence.attrib["id"]] = {
            "s_attrs": ",".join(sorted(sentence.attrib)),
            "source": sentence.attrib.get("source", ""),
            "original": forms.get("original", ""),
            "standard": forms.get("standard", ""),
            "original_notes": sentence.find('./FORM[@kindOf="original"]').attrib.get("notes", "")
            if sentence.find('./FORM[@kindOf="original"]') is not None
            else "",
            "phon_count": str(len(sentence.findall("PHON"))),
            "w_count": str(len(sentence.findall("W"))),
            "m_count": str(len(sentence.findall(".//M"))),
            "source_sidecar_count": str(
                sum(1 for item in translations if item["kindOf"].startswith("source_"))
            ),
            "zho_translation": next(
                (item["text"] for item in translations if item["lang"] == "zho" and not item["kindOf"]),
                "",
            ),
            "w_translations": json.dumps(
                [
                    translation
                    for word in sentence.findall("W")
                    if (
                        translation := next(
                        (
                            transl.text or ""
                            for transl in word.findall("TRANSL")
                            if transl.attrib.get(
                                "{http://www.w3.org/XML/1998/namespace}lang", ""
                            )
                            == "zho"
                        ),
                        "",
                    )
                    )
                ],
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        }
    return rows


def audit_rows(report_rows: list[dict[str, str]], xml_rows: dict[str, dict[str, str]]) -> list[dict[str, str]]:
    audit: list[dict[str, str]] = []
    for row in report_rows:
        sid = example_id(row["example"], row["subexample"])
        xml = xml_rows.get(sid)
        expected_present = row["status"] == "include"
        actual_present = xml is not None
        checks: list[str] = []
        if expected_present != actual_present:
            checks.append("presence_mismatch")
        if expected_present and xml:
            expected_source = (
                f"PDF page {int(row['page'])}; example "
                f"{int(row['example'])}{row['subexample']}"
            )
            if xml["original"] != row["form"]:
                checks.append("original_mismatch")
            if xml["phon_count"] != "2":
                checks.append("phon_count_mismatch")
            if xml["s_attrs"] != "id,source":
                checks.append("nonstandard_s_attributes")
            if xml["source"] != expected_source:
                checks.append("source_locator_mismatch")
            if xml["source_sidecar_count"] != "0":
                checks.append("source_sidecar_on_s")
            if xml["w_count"] != str(len(row["word_form"].split())):
                checks.append("w_count_mismatch")
            if xml["original_notes"] != row.get("source_judgement", ""):
                checks.append("source_judgement_note_mismatch")
            if row.get("translation_zho") and xml.get("zho_translation") != row["translation_zho"]:
                checks.append("translation_mismatch")
            if xml["w_translations"] != row.get("aligned_gloss_tokens_zho", "[]"):
                checks.append("word_gloss_alignment_mismatch")
        audit.append(
            {
                "example_id": sid,
                "source_status": row["status"],
                "xml_present": "true" if actual_present else "false",
                "original_matches_report": "true" if expected_present and xml and xml["original"] == row["form"] else "",
                "standard_present": "true" if expected_present and xml and bool(xml["standard"]) else "",
                "translation_matches_report": "true" if expected_present and xml and row.get("translation_zho") and xml.get("zho_translation") == row["translation_zho"] else "",
                "word_glosses_match_report": "true" if expected_present and xml and xml["w_translations"] == row.get("aligned_gloss_tokens_zho", "[]") else "",
                "s_attrs": xml["s_attrs"] if xml else "",
                "source": xml["source"] if xml else "",
                "w_count": xml["w_count"] if xml else "0",
                "m_count": xml["m_count"] if xml else "0",
                "source_sidecar_count": xml["source_sidecar_count"] if xml else "0",
                "phon_count": xml["phon_count"] if xml else "0",
                "audit_status": "pass" if not checks else "fail",
                "notes": "; ".join(checks) if checks else row.get("note", ""),
            }
        )
    return audit


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "example_id",
        "source_status",
        "xml_present",
        "original_matches_report",
        "standard_present",
        "translation_matches_report",
        "word_glosses_match_report",
        "s_attrs",
        "source",
        "w_count",
        "m_count",
        "source_sidecar_count",
        "phon_count",
        "audit_status",
        "notes",
    ]
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    report_rows = read_report_rows()
    xml_rows = read_xml_rows()
    for row in report_rows:
        if row["status"] == "include":
            continue
        if row["status"] == "excluded_ungrammatical":
            if example_id(row["example"], row["subexample"]) in xml_rows:
                raise SystemExit(
                    f"Source-starred row {row['example']}{row['subexample']} was not excluded"
                )
            continue
        retained = xml_rows.get(row.get("retained_xml_id", ""))
        if retained is None:
            raise SystemExit(
                f"Excluded source row {row['example']}{row['subexample']} lacks retained XML"
            )
        if row["status"] == "excluded_exact_repeat" and retained["original"] != row["form"]:
            raise SystemExit(
                f"Exact-repeat source row {row['example']}{row['subexample']} is not linked to the same FORM"
            )
    audit = audit_rows(report_rows, xml_rows)
    write_csv(audit)
    failures = sum(1 for row in audit if row["audit_status"] != "pass")
    print(f"source alignment audit rows: {len(audit)}")
    print(f"source alignment audit failures: {failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
