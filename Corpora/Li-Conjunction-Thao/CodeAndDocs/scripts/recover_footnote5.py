#!/usr/bin/env python3
"""Recover the omitted inline example from the official PDF, outside builds."""

import argparse
import csv
import re
from pathlib import Path

from audit_source_fidelity import _source_text
from build_xml import RECORDS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    text = _source_text(args.source)
    match = re.search(r"e\.g\.,\s*(tu sa suma wa anyamin)\s*‘(.*?)’\.", text, re.DOTALL)
    if match is None:
        raise SystemExit("Footnote 5 example not found in the verified source")
    with RECORDS.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames
        rows = [row for row in reader if row["id"] != "li2014_thao_fn5_1"]
    if len(rows) != 27 or rows[7]["id"] != "li2014_thao_S008":
        raise SystemExit("Unexpected baseline; review the source inventory")
    rows.insert(8, dict(zip(fields, (
        "li2014_thao_fn5_1", "PDF p. 396; printed p. 403; footnote 5, inline example",
        "396", "403", "fn5-1", "", "yes", match[1], "",
        " ".join(match[2].split()).replace("’", "'"),
        "Translated inline example in footnote 5; no printed gloss line or segmentation. Existing IDs remain unchanged.",
    ), strict=True)))
    with RECORDS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
