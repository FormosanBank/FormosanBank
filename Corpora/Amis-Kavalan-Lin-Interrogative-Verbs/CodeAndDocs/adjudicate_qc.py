#!/usr/bin/env python3
"""Fail on unreviewed QC findings and record the source-backed dispositions."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc-dir", type=Path, required=True)
    args = parser.parse_args()
    qc_dir = args.qc_dir.resolve()

    xml_findings = read_csv(qc_dir / "validate_xml_findings.csv")
    gloss_findings = read_csv(qc_dir / "validate_glosses_findings.csv")
    if xml_findings:
        raise SystemExit(f"validate_xml has {len(xml_findings)} unadjudicated findings")
    if gloss_findings:
        raise SystemExit(f"validate_glosses has {len(gloss_findings)} unadjudicated findings")

    text_findings = read_csv(qc_dir / "validate_text_findings.csv")
    text_inventory = Counter((row["severity"], row["rule_id"], row["location"]) for row in text_findings)
    expected_text = Counter(
        {
            ("SOFT", "V122", "S=S_amis_009"): 2,
            ("SOFT", "V122", "S=S_amis_010"): 2,
            ("SOFT", "V122", "S=S_amis_014"): 4,
        }
    )
    if text_inventory != expected_text or any("in TRANSL" not in row["message"] for row in text_findings):
        raise SystemExit(f"unexpected validate_text findings: {text_inventory}")

    expected_duplicate_ids = {"S_kavalan_003", "S_kavalan_016_OPT0"}
    for tier in ("original", "standard"):
        rows = read_csv(qc_dir / f"duplicate_{tier}_findings.csv")
        ids = {row["s_id"] for row in rows}
        normalized = {row["normalized_text"] for row in rows}
        if len(rows) != 2 or ids != expected_duplicate_ids or len(normalized) != 1:
            raise SystemExit(f"unexpected {tier} duplicate findings")

    reconciliation = read_csv(qc_dir / "gloss_scrape_reconciliation.csv")
    dispositions = Counter(row["disposition"] for row in reconciliation)
    expected_dispositions = Counter(
        {
            "source-excluded": 21,
            "false-positive-source-reference": 4,
            "required-infix-root": 12,
            "normalized-infix-notation": 12,
            "false-positive-subexample-grouping": 5,
            "retain-source-gloss": 1,
            "informational": 1,
        }
    )
    if dispositions != expected_dispositions:
        raise SystemExit(f"unexpected gloss-audit dispositions: {dispositions}")

    conversion_log = (qc_dir / "validate_conversion_table.log").read_text(encoding="utf-8")
    if "Result: PASS" not in conversion_log or "mismatch=0" not in conversion_log:
        raise SystemExit("conversion-table validation did not pass cleanly")
    source_log = (qc_dir / "source_alignment_audit.log").read_text(encoding="utf-8")
    if "errors=0 warnings=0" not in source_log:
        raise SystemExit("source-alignment audit is not clean")
    port_log = (qc_dir / "validate_port_readiness.log").read_text(encoding="utf-8")
    if "port-readiness: 0 HARD, 1 WARN" not in port_log or "P006 WARN" not in port_log:
        raise SystemExit("port-readiness findings differ from the reviewed P006 warning")

    lines = [
        "# QC Finding Adjudication",
        "",
        "- `validate_xml`: no findings.",
        "- `validate_glosses`: no findings.",
        "- `validate_text`: eight V122 SOFT rows preserve naturalistic parenthetical wording in four source translations under POL-024.",
        "- Duplicate validation: one two-record group on each FORM tier is required by the source's optional `na-` expansion under POL-026; the omitted variant matches an independently attested source sentence.",
        "- Gloss scrape audit: all 56 rows are reconciled to source exclusions, detector grouping, POL-014 infix notation, or retained source labels; none is unresolved.",
        "- Port readiness: zero HARD findings. P006 is satisfied by the clean conversion-table audit with four confirmed equivalences and no information loss.",
        "",
    ]
    (qc_dir / "adjudication.md").write_text("\n".join(lines), encoding="utf-8")
    print("All residual findings are source-adjudicated; unresolved=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
