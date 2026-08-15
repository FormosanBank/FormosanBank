#!/usr/bin/env python3
"""Write a page-level coverage report for the Sakizaya affixes source."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOTAL_PAGES = 174
IMAGE_DIR = ROOT / "Private/cache/page_images_350"
VISION_DIR = ROOT / "Private/cache/vision_ocr_350"
EXAMPLE_REPORT = ROOT / "CodeAndDocs/extraction_report.csv"
TABLE_REPORT = ROOT / "CodeAndDocs/table_extraction_report.csv"
SUMMARY_REPORT = ROOT / "CodeAndDocs/summary_table_extraction_report.csv"
COVERAGE_CSV = ROOT / "CodeAndDocs/page_coverage.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def count_by_page(rows: list[dict[str, str]]) -> dict[int, Counter[str]]:
    counts: dict[int, Counter[str]] = defaultdict(Counter)
    for row in rows:
        page = int(row["page"])
        counts[page]["total"] += 1
        counts[page][row["status"]] += 1
    return counts


def cache_path(directory: Path, page: int, suffix: str) -> Path:
    if suffix == "vision.tsv":
        return directory / f"page-{page:03d}.vision.tsv"
    return directory / f"scan_page-{page:03d}.{suffix}"


def row_for_page(
    page: int,
    examples: dict[int, Counter[str]],
    tables: dict[int, Counter[str]],
    summaries: dict[int, Counter[str]],
) -> dict[str, str]:
    example_counts = examples.get(page, Counter())
    table_counts = tables.get(page, Counter())
    summary_counts = summaries.get(page, Counter())
    source_rows = example_counts["total"] + table_counts["total"] + summary_counts["total"]
    expected_xml_rows = example_counts["include"] + table_counts["include"] + summary_counts["include"]
    excluded_rows = source_rows - expected_xml_rows
    image_present = cache_path(IMAGE_DIR, page, "png").exists()
    vision_present = cache_path(VISION_DIR, page, "vision.tsv").exists()
    note = "report rows represented" if source_rows else "OCR cached; no reportable XML row in current extraction scope"
    return {
        "pdf_page": str(page),
        "image_cache": "true" if image_present else "false",
        "vision_ocr_cache": "true" if vision_present else "false",
        "numbered_rows": str(example_counts["total"]),
        "numbered_included": str(example_counts["include"]),
        "numbered_excluded": str(example_counts["total"] - example_counts["include"]),
        "table_rows": str(table_counts["total"]),
        "table_included": str(table_counts["include"]),
        "table_excluded": str(table_counts["total"] - table_counts["include"]),
        "summary_rows": str(summary_counts["total"]),
        "summary_included": str(summary_counts["include"]),
        "summary_excluded": str(summary_counts["total"] - summary_counts["include"]),
        "source_report_rows": str(source_rows),
        "expected_xml_rows": str(expected_xml_rows),
        "excluded_report_rows": str(excluded_rows),
        "note": note,
    }


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "pdf_page",
        "image_cache",
        "vision_ocr_cache",
        "numbered_rows",
        "numbered_included",
        "numbered_excluded",
        "table_rows",
        "table_included",
        "table_excluded",
        "summary_rows",
        "summary_included",
        "summary_excluded",
        "source_report_rows",
        "expected_xml_rows",
        "excluded_report_rows",
        "note",
    ]
    with COVERAGE_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    example_rows = read_rows(EXAMPLE_REPORT)
    table_rows = read_rows(TABLE_REPORT)
    summary_rows = read_rows(SUMMARY_REPORT)
    examples = count_by_page(example_rows)
    tables = count_by_page(table_rows)
    summaries = count_by_page(summary_rows)
    rows = [row_for_page(page, examples, tables, summaries) for page in range(1, TOTAL_PAGES + 1)]
    write_csv(rows)

    missing_critical = [
        row["pdf_page"]
        for row in rows
        if row["image_cache"] != "true" or row["vision_ocr_cache"] != "true"
    ]
    expected_table_sequences = {str(seq) for seq in range(1, 435)}
    actual_table_sequences = {row["seq"] for row in table_rows}
    missing_table_sequences = sorted(expected_table_sequences - actual_table_sequences, key=int)
    expected_summary_sequences = {str(seq) for seq in range(435, 548)}
    actual_summary_sequences = {row["seq"] for row in summary_rows}
    missing_summary_sequences = sorted(
        expected_summary_sequences - actual_summary_sequences,
        key=int,
    )

    represented = len(example_rows) + len(table_rows) + len(summary_rows)
    included = sum(row["status"] == "include" for row in [*example_rows, *table_rows, *summary_rows])

    print(f"page coverage rows: {len(rows)}")
    print(f"pages with source report rows: {sum(1 for row in rows if int(row['source_report_rows']) > 0)}")
    print(f"critical OCR cache pages missing: {len(missing_critical)}")
    print(f"missing table sequences: {len(missing_table_sequences)}")
    print(f"missing late-table sequences: {len(missing_summary_sequences)}")
    if represented != 808 or included != 681:
        raise SystemExit(
            f"Expected 808 source units and 681 XML rows; found {represented} and {included}"
        )
    if missing_critical or missing_table_sequences or missing_summary_sequences:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
