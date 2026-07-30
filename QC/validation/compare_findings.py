#!/usr/bin/env python3
"""Fail when a validator CSV contains findings absent from its baseline."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


FINGERPRINT_FIELDS = ("rule_id", "location", "language", "character")


def _read_fingerprints(path: Path | None, severity: str) -> Counter[tuple[str, ...]]:
    if path is None:
        return Counter()

    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = csv.DictReader(handle)
        return Counter(
            tuple(row.get(field, "") for field in FINGERPRINT_FIELDS)
            for row in rows
            if row.get("severity") == severity
        )


def new_findings(
    baseline: Path | None,
    candidate: Path,
    severity: str = "HARD",
) -> Counter[tuple[str, ...]]:
    """Return candidate finding fingerprints not present in the baseline."""
    return _read_fingerprints(candidate, severity) - _read_fingerprints(
        baseline, severity
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare finding CSVs and fail on newly introduced findings."
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Baseline findings CSV. Omit for a newly added source file.",
    )
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument(
        "--severity",
        choices=("HARD", "SOFT", "WARN"),
        default="HARD",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    introduced = new_findings(args.baseline, args.candidate, args.severity)
    if not introduced:
        print(f"No new {args.severity} findings.")
        return 0

    print(f"New {args.severity} findings: {sum(introduced.values())}")
    for fingerprint, count in sorted(introduced.items()):
        details = ", ".join(
            f"{field}={value!r}"
            for field, value in zip(FINGERPRINT_FIELDS, fingerprint, strict=True)
            if value
        )
        print(f"  {count} x {details}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
