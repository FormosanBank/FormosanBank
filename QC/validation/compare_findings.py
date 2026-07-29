#!/usr/bin/env python3
"""Fail when a validation CSV contains HARD findings absent from a baseline."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


KEY_FIELDS = ("rule_id", "title", "location", "language", "character", "message")


def hard_findings(path: Path) -> Counter[tuple[str, ...]]:
    if not path.is_file() or path.stat().st_size == 0:
        return Counter()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return Counter(
            tuple(row.get(field, "") for field in KEY_FIELDS)
            for row in csv.DictReader(handle)
            if row.get("severity") == "HARD"
        )


def new_findings(current: Path, baseline: Path) -> Counter[tuple[str, ...]]:
    return hard_findings(current) - hard_findings(baseline)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("current", type=Path)
    parser.add_argument("baseline", type=Path)
    args = parser.parse_args()

    added = new_findings(args.current, args.baseline)
    for finding, count in sorted(added.items()):
        values = dict(zip(KEY_FIELDS, finding))
        print(
            f"NEW HARD x{count}: {values['rule_id']} "
            f"{values['location']} — {values['message']}"
        )
    return 1 if added else 0


if __name__ == "__main__":
    raise SystemExit(main())
