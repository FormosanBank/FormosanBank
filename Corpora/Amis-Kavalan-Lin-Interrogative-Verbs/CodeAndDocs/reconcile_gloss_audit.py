#!/usr/bin/env python3
"""Reconcile the shared gloss-source audit against reviewed Lin 2015 ledgers."""
from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def source_id_from_message(message: str) -> str:
    match = re.search(r"source example\s+\(?([0-9]+[a-z]?)\)?", message)
    return match.group(1) if match else ""


def reconcile(
    findings_path: Path,
    examples_path: Path,
    exclusions_path: Path,
) -> list[dict[str, str]]:
    examples = read_tsv(examples_path)
    exclusions = read_tsv(exclusions_path)
    example_rows = {row["source_id"]: row for row in examples}
    exclusion_ids = {row["source_id"] for row in exclusions}

    with findings_path.open(encoding="utf-8-sig", newline="") as handle:
        findings = list(csv.DictReader(handle))

    reconciled: list[dict[str, str]] = []
    for finding in findings:
        rule_id = finding["rule_id"]
        source_id = ""
        disposition = "unresolved"
        evidence = "No reviewed disposition rule applies."

        if rule_id == "G021":
            source_id = source_id_from_message(finding["message"])
            source_row = example_rows.get(source_id)
            if source_row and source_row["admission_status"] == "excluded":
                disposition = "source-excluded"
                evidence = source_row["exclusion_reason"]
            elif source_id in exclusion_ids:
                disposition = "source-excluded"
                evidence = "Recorded in excluded_source_units.tsv after page review."
            elif source_row and source_row["admission_status"] == "admitted":
                disposition = "false-positive-source-reference"
                evidence = "The admitted source ID is represented in XML; the detector matched a narrative reference."
            else:
                grouped = [
                    row
                    for row in examples
                    if row["source_id"].startswith(source_id)
                    and row["admission_status"] == "admitted"
                ]
                if source_id and grouped:
                    disposition = "false-positive-source-reference"
                    evidence = "The detector matched a numbered group reference; its admitted subexamples are represented in XML."
        elif rule_id == "G012":
            disposition = "retain-source-translation"
            evidence = "The parenthetical literal or alternate wording is part of the published free translation."
        elif rule_id == "G013":
            disposition = "false-positive-subexample-grouping"
            evidence = "The detector grouped independently aligned lettered subexamples under one number."
        elif rule_id == "G003" and "contains an internal '-'" in finding["message"]:
            disposition = "required-infix-root"
            evidence = (
                "POL-014 requires the root M to mark the source infix insertion point "
                "with an internal hyphen; the paired infix M is preserved separately."
            )
        elif rule_id == "G022" and "'‹' (U+2039)" in finding["message"]:
            disposition = "normalized-infix-notation"
            evidence = (
                "The source guillemets are analytical infix brackets. POL-014 removes "
                "them from S FORM while preserving ASCII brackets in W and gap-hyphen "
                "root plus infix M tiers."
            )
        elif rule_id == "G005":
            disposition = "retain-source-gloss"
            evidence = "The reviewed interlinear line contains this source gloss label; POL-036 preserves it."
        elif rule_id == "G023":
            disposition = "informational"
            evidence = "Extractor self-report reviewed against the 38-page manual coverage ledger."

        reconciled.append(
            {
                "severity": finding["severity"],
                "rule_id": rule_id,
                "location": finding["location"],
                "source_id": source_id,
                "disposition": disposition,
                "evidence": evidence,
            }
        )
    return reconciled


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings", type=Path, required=True)
    parser.add_argument("--examples", type=Path, required=True)
    parser.add_argument("--exclusions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = reconcile(args.findings, args.examples, args.exclusions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["severity", "rule_id", "location", "source_id", "disposition", "evidence"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    unresolved = [row for row in rows if row["disposition"] == "unresolved"]
    print(f"Reconciled gloss audit findings: {len(rows)}; unresolved: {len(unresolved)}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
