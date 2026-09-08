#!/usr/bin/env python3
"""Enforce the merged SEALS33 reconstruction-title HARD exception exactly."""

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


EXPECTED = Counter({(name, tier): 1 for name in (
    "saisiyat_seals.xml", "seediq_SEALS.xml"
) for tier in ("original", "standard")})


def check(report_dir: Path) -> None:
    found = Counter()
    for name in ("xml.csv", "text.csv"):
        with (report_dir / name).open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["severity"] != "HARD":
                    continue
                tier = re.search(r"kindOf='(original|standard)'", row["message"])
                if (name != "text.csv" or row["rule_id"] != "V129"
                        or row["location"] != "S=25" or tier is None):
                    raise ValueError(f"Unreviewed HARD finding: {row}")
                found[(Path(row["file"]).name, tier.group(1))] += int(row["count"])
    if found != EXPECTED:
        raise ValueError(f"Expected four scoped reconstruction-title findings, got {found}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report_dir", type=Path)
    args = parser.parse_args()
    check(args.report_dir)
    print("Four scoped V129 exceptions verified; review SOFT and warning reports separately.")


if __name__ == "__main__":
    main()
