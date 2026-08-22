#!/usr/bin/env python3
"""Compare every reviewed Latham source cell with the report and final XML."""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

from build_lexical_xml import LexicalEntry, included_entries, load_ledger


ROOT = Path(__file__).resolve().parents[1]
EXTRACTION_REPORT = ROOT / "CodeAndDocs" / "extraction_report.csv"
AUDIT_CSV = ROOT / "CodeAndDocs" / "source_coverage_audit.csv"
AUDIT_MD = ROOT / "CodeAndDocs" / "source_coverage_audit.md"
XML_ROOT = ROOT / "XML"
EXPECTED_XML_PATHS = {
    "bzg": "Babuza-Favorlang/latham_1862_favorlang.xml",
    "fos": "Siraya/latham_1862_sideia_sida.xml",
}
PAGE_SCOPE = [
    (
        "314",
        "No target Formosan rows; Philippine, Dumagat, and Bashi data excluded.",
    ),
    (
        "315",
        "Sideia comparison table: all 16 Formosan cells included.",
    ),
    (
        "316",
        "Gabelentz table: 15 Formosan cells included; Sida Forehead dash omitted.",
    ),
    (
        "317",
        "Gabelentz table: 15 Formosan cells included; Sida Beard dash omitted.",
    ),
    (
        "318",
        "Gabelentz table: all 16 Formosan cells included.",
    ),
    (
        "319",
        "Only non-Formosan continuation rows; excluded from target scope.",
    ),
]


def read_report() -> dict[str, dict[str, str]]:
    with EXTRACTION_REPORT.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    report = {row["s_id"]: row for row in rows}
    if len(report) != len(rows):
        raise ValueError("Extraction report contains duplicate S IDs")
    return report


def read_xml() -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for path in sorted(XML_ROOT.rglob("*.xml")):
        relative_path = str(path.relative_to(XML_ROOT))
        root = etree.parse(path).getroot()
        for sentence in root.findall("S"):
            record_id = sentence.get("id", "")
            originals = sentence.findall("FORM[@kindOf='original']")
            standards = sentence.findall("FORM[@kindOf='standard']")
            alternates = sentence.findall("FORM[@kindOf='alternate']")
            translations = sentence.findall("TRANSL")
            if (
                not record_id
                or record_id in records
                or len(originals) != 1
                or len(standards) != 1
                or len(translations) != 1
            ):
                raise ValueError(f"Ambiguous XML record: {record_id}")
            records[record_id] = {
                "xml_path": relative_path,
                "original": originals[0].text or "",
                "standard": standards[0].text or "",
                "alternates": tuple(form.text or "" for form in alternates),
                "translation": translations[0].text or "",
                "translation_language": translations[0].get(
                    "{http://www.w3.org/XML/1998/namespace}lang",
                    "",
                ),
                "source": sentence.get("source", ""),
                "has_inferred_tiers": any(
                    sentence.find(tag) is not None for tag in ("PHON", "W", "M")
                ),
            }
    return records


def audit_included(
    entry: LexicalEntry,
    report: dict[str, dict[str, str]],
    xml: dict[str, dict[str, object]],
) -> dict[str, str]:
    issues: list[str] = []
    report_row = report.get(entry.s_id)
    xml_row = xml.get(entry.s_id)
    if report_row is None:
        issues.append("missing extraction report row")
    else:
        expected_report = {
            "language_code": entry.language_code,
            "language_label": entry.language_label,
            "dialect": entry.dialect,
            "source_variety": entry.source_variety,
            "english": entry.english,
            "form": entry.form,
            "alternate_forms": " | ".join(entry.alternate_forms),
            "printed_page": entry.printed_page,
            "pdf_page": entry.pdf_page,
            "table": entry.table,
            "review_note": entry.note,
        }
        for field, expected in expected_report.items():
            if report_row.get(field) != expected:
                issues.append(
                    f"report {field} mismatch: {report_row.get(field)!r}"
                )
    if xml_row is None:
        issues.append("missing XML S")
    else:
        expected_xml = {
            "xml_path": EXPECTED_XML_PATHS[entry.language_code],
            "original": entry.form,
            "standard": entry.form,
            "alternates": entry.alternate_forms,
            "translation": entry.english.lower(),
            "translation_language": "eng",
            "source": entry.source_attr,
            "has_inferred_tiers": False,
        }
        for field, expected in expected_xml.items():
            if xml_row.get(field) != expected:
                issues.append(
                    f"XML {field} mismatch: {xml_row.get(field)!r}"
                )
    return {
        "printed_page": entry.printed_page,
        "pdf_page": entry.pdf_page,
        "table": entry.table,
        "source_variety": entry.source_variety,
        "english": entry.english,
        "expected_form": entry.form,
        "expected_alternate_forms": " | ".join(entry.alternate_forms),
        "xml_s_id": entry.s_id,
        "xml_form": str(xml_row.get("original", "")) if xml_row else "",
        "xml_alternate_forms": (
            " | ".join(xml_row.get("alternates", ())) if xml_row else ""
        ),
        "status": "PASS" if not issues else "FAIL",
        "note": "; ".join(issues),
    }


def audit_rows() -> tuple[list[dict[str, str]], Counter[str]]:
    ledger = load_ledger()
    included = included_entries(ledger)
    report = read_report()
    xml = read_xml()
    rows: list[dict[str, str]] = []
    counts: Counter[str] = Counter()

    for entry in included:
        row = audit_included(entry, report, xml)
        counts[row["status"]] += 1
        rows.append(row)

    for entry in ledger:
        if entry.status != "omitted_blank_or_dash":
            continue
        omitted_id = entry.s_id
        issues = []
        if omitted_id in report:
            issues.append("omitted source cell appears in extraction report")
        if omitted_id in xml:
            issues.append("omitted source cell appears in XML")
        status = "OMITTED_BLANK_OR_DASH" if not issues else "FAIL"
        counts[status] += 1
        rows.append(
            {
                "printed_page": entry.printed_page,
                "pdf_page": entry.pdf_page,
                "table": entry.table,
                "source_variety": entry.source_variety,
                "english": entry.english,
                "expected_form": "",
                "expected_alternate_forms": "",
                "xml_s_id": "",
                "xml_form": "",
                "xml_alternate_forms": "",
                "status": status,
                "note": "; ".join(issues) or entry.note,
            }
        )

    expected_ids = {entry.s_id for entry in included}
    for record_id in sorted(set(report) - expected_ids):
        counts["EXTRA_REPORT_ROW"] += 1
        rows.append(
            {
                "printed_page": "",
                "pdf_page": "",
                "table": "",
                "source_variety": "",
                "english": "",
                "expected_form": "",
                "expected_alternate_forms": "",
                "xml_s_id": record_id,
                "xml_form": "",
                "xml_alternate_forms": "",
                "status": "EXTRA_REPORT_ROW",
                "note": "Report row is absent from the source ledger.",
            }
        )
    for record_id in sorted(set(xml) - expected_ids):
        counts["EXTRA_XML_S"] += 1
        rows.append(
            {
                "printed_page": "",
                "pdf_page": "",
                "table": "",
                "source_variety": "",
                "english": "",
                "expected_form": "",
                "expected_alternate_forms": "",
                "xml_s_id": record_id,
                "xml_form": str(xml[record_id]["original"]),
                "xml_alternate_forms": " | ".join(
                    xml[record_id]["alternates"]
                ),
                "status": "EXTRA_XML_S",
                "note": "XML record is absent from the source ledger.",
            }
        )
    return rows, counts


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "printed_page",
        "pdf_page",
        "table",
        "source_variety",
        "english",
        "expected_form",
        "expected_alternate_forms",
        "xml_s_id",
        "xml_form",
        "xml_alternate_forms",
        "status",
        "note",
    ]
    with AUDIT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(counts: Counter[str]) -> None:
    unresolved = sum(
        count
        for status, count in counts.items()
        if status not in {"PASS", "OMITTED_BLANK_OR_DASH"}
    )
    page_rows = ["| Page | Coverage decision |", "| --- | --- |"]
    page_rows.extend(f"| {page} | {note} |" for page, note in PAGE_SCOPE)
    lines = [
        "# Source Coverage Audit",
        "",
        "All target cells on printed pages 315–318 were manually transcribed",
        "from the page images into `source_ledger.tsv`. Pages 314 and 319 were",
        "visually checked and contain no target Formosan rows.",
        "",
        "## Result",
        "",
        f"- Expected included Formosan cells: 62",
        f"- Included cells matching ledger, report, and XML: {counts['PASS']}",
        "- Blank/dash Formosan cells intentionally omitted: "
        f"{counts['OMITTED_BLANK_OR_DASH']}",
        f"- Unresolved mismatches or extras: {unresolved}",
        f"- Exact independent spot checks: 12 in `source_checks.tsv`",
        f"- CSV detail: `{AUDIT_CSV.relative_to(ROOT)}`",
        "",
        "## Page Decisions",
        "",
        *page_rows,
        "",
        "## Review Notes",
        "",
        "- The PDF is a six-page image-only excerpt; rendered pages 1–6 were",
        "  visually reviewed.",
        "- Historical diacritics are preserved exactly in original and standard",
        "  FORM tiers.",
        "- Comma-separated variants are separate original/alternate FORM tiers.",
        "- The layout hyphen in `arribórri-` / `bon` is removed when the source",
        "  word is reconstructed as `arribórribon`.",
        "- Sida Forehead and Beard are dash cells and are not emitted.",
        "- No PHON or W/M structure is inferred from the lexical table.",
    ]
    AUDIT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    rows, counts = audit_rows()
    write_csv(rows)
    write_markdown(counts)
    unresolved = sum(
        count
        for status, count in counts.items()
        if status not in {"PASS", "OMITTED_BLANK_OR_DASH"}
    )
    print(f"PASS source cells: {counts['PASS']}/62")
    print(f"OMITTED blank/dash cells: {counts['OMITTED_BLANK_OR_DASH']}")
    print(f"Unresolved mismatches/extras: {unresolved}")
    print(f"Wrote {AUDIT_CSV.relative_to(ROOT)}")
    print(f"Wrote {AUDIT_MD.relative_to(ROOT)}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    sys.exit(main())
