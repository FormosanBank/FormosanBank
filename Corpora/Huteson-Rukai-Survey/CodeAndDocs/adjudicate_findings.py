#!/usr/bin/env python3
"""Fail QC unless validator findings match the reviewed Huteson evidence."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


EXPECTED_TEXT_FINDINGS = Counter(
    {
        ("S=S_maga_009", "("): 1,
        ("S=S_maga_009", ")"): 1,
        ("W=S_maga_009_W_001", "/"): 1,
        ("M=S_maga_009_W_001_M_01", "/"): 1,
        ("S=S_maga_013", "("): 1,
        ("S=S_maga_013", ")"): 1,
        ("S=S_tona_008", "("): 1,
        ("S=S_tona_008", ")"): 1,
    }
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def require_empty(path: Path) -> None:
    findings = rows(path)
    if findings:
        counts = Counter((row["severity"], row["rule_id"]) for row in findings)
        raise ValueError(f"Unexpected findings in {path.name}: {dict(counts)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc-dir", type=Path, required=True)
    args = parser.parse_args()

    for name in (
        "validate_xml.csv",
        "validate_glosses.csv",
        "audit_gloss_scrape.csv",
    ):
        require_empty(args.qc_dir / name)

    text_findings = rows(args.qc_dir / "validate_text.csv")
    if any(
        row["severity"] != "SOFT" or row["rule_id"] != "V122"
        for row in text_findings
    ):
        raise ValueError("validate_text.csv contains an unreviewed rule or severity")
    actual = Counter(
        (row["location"], row["character"]) for row in text_findings
    )
    if actual != EXPECTED_TEXT_FINDINGS:
        raise ValueError(
            f"V122 finding set changed: expected {EXPECTED_TEXT_FINDINGS}, got {actual}"
        )

    require_empty(args.qc_dir / "duplicate_original.csv")
    require_empty(args.qc_dir / "duplicate_standard.csv")

    report = args.qc_dir / "adjudication.md"
    report.write_text(
        "\n".join(
            [
                "# QC finding adjudication",
                "",
                "- XML findings: 0",
                "- Gloss findings: 0",
                "- Generic gloss-audit findings: 0",
                "- Duplicate findings: 0",
                "- Text findings: 8 SOFT V122, all reviewed",
                "",
                "The sentence parentheticals `(how to)` and `(his)` are printed ",
                "source translations retained under POL-024. `ACT/REAL` is a printed ",
                "source gloss retained as an original-tier gloss under POL-036. The ",
                "actionable `S/he` and `ran/is running` shorthands were expanded into ",
                "same-S alternate translations under POL-025.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"Reviewed findings match the expected evidence; wrote {report}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
