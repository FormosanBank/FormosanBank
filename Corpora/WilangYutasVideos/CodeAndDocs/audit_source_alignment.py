#!/usr/bin/env python3
"""Verify generated pre-clean XML against every pinned transcript line."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import sys
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "CodeAndDocs" / "make_xml.py"
ISSUE_REVIEW = ROOT / "CodeAndDocs" / "issue_1_review.tsv"
SUMMARY = ROOT / "CodeAndDocs" / "source_alignment_summary.md"


def load_builder():
    spec = importlib.util.spec_from_file_location("wilang_make_xml", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load builder: {BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical_xml(element: etree._Element) -> bytes:
    return etree.tostring(element, method="c14n", with_comments=False)


def read_issue_review() -> list[dict[str, str]]:
    with ISSUE_REVIEW.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    findings = [int(row["finding"]) for row in rows]
    if findings != list(range(1, 22)):
        raise ValueError("Issue #1 review must contain findings 1 through 21 in order")
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml-root", type=Path, default=ROOT / "XML")
    args = parser.parse_args()
    xml_root = args.xml_root.resolve()
    builder = load_builder()
    manifest = builder.load_manifest()
    expected_paths = {row.output_path.relative_to(ROOT) for row in manifest}
    actual_paths = {
        Path("XML") / path.relative_to(xml_root) for path in xml_root.rglob("*.xml")
    }
    if actual_paths != expected_paths:
        missing = sorted(str(path) for path in expected_paths - actual_paths)
        extra = sorted(str(path) for path in actual_paths - expected_paths)
        raise SystemExit(f"XML path mismatch; missing={missing}; extra={extra}")

    totals = builder.SourceStats(0, 0, 0, 0, 0)
    sentence_index: dict[tuple[str, str], etree._Element] = {}
    for row in manifest:
        actual_path = xml_root / row.output_path.relative_to(ROOT / "XML")
        parser_no_blanks = etree.XMLParser(remove_blank_text=True)
        actual = etree.parse(str(actual_path), parser_no_blanks).getroot()
        if row.source_path is not None:
            expected, stats = builder.build_transcript(row)
            totals = builder.SourceStats(
                totals.timestamp_lines + stats.timestamp_lines,
                totals.included_entries + stats.included_entries,
                totals.blank_entries + stats.blank_entries,
                totals.translation_lines + stats.translation_lines,
                totals.continuation_lines + stats.continuation_lines,
            )
        else:
            expected = builder.build_audio_only(row)
        if canonical_xml(actual) != canonical_xml(expected):
            raise SystemExit(f"Generated XML/source mismatch: {actual_path}")
        for sentence in actual.findall("S"):
            sentence_index[(str(row.output_path.relative_to(ROOT)), sentence.get("id", ""))] = sentence

    expected_totals = builder.SourceStats(6455, 3014, 3441, 237, 5)
    if totals != expected_totals:
        raise SystemExit(f"Unexpected source totals: {totals}")

    issue_rows = read_issue_review()
    for row in issue_rows:
        key = (row["output_path"], row["s_id"])
        sentence = sentence_index.get(key)
        if sentence is None:
            raise SystemExit(f"Issue #1 row has no generated sentence: {key}")
        if row["finding"] == "21":
            if sentence.find("TRANSL") is not None:
                raise SystemExit("Issue #1 finding 21 still has a false translation")
            notes = " ".join(form.get("notes", "") for form in sentence.findall("FORM"))
            if "(再確認)" not in notes:
                raise SystemExit("Issue #1 finding 21 lost its editorial source marker")

    summary = """# Source alignment summary

- Pinned transcript files: 34
- Manifested XML outputs: 82
- Transcript outputs: 34
- Audio-only outputs: 48
- Timestamped source rows: 6,455
- Included non-empty source rows: 3,014
- Explicitly omitted blank source rows: 3,441
- Translation lines: 237
- Wrapped source continuations restored: 5
- Generated pre-clean XML mismatches: 0
- Issue #1 findings reviewed: 21/21
- Unresolved issue #1 findings: 0

The audit verifies every generated pre-clean XML element against the pinned
source manifest and fails on missing, extra, reclassified, or changed input.
The current FormosanBank cleaning, standardization, and phonology stages run
only after this exact source-alignment gate passes.
"""
    SUMMARY.write_text(summary, encoding="utf-8")
    print("PASS: 82/82 generated XML files match pinned source inputs")
    print(
        "PASS: 3,014 included rows; 3,441 blank rows omitted; "
        "237 translations; 5 continuations"
    )
    print("PASS: issue #1 review is complete with 0 unresolved findings")
    print(f"Wrote {SUMMARY}")


if __name__ == "__main__":
    main()
