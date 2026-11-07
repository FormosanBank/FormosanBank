#!/usr/bin/env python3
"""Apply recorded standard-tier spelling corrections.

The original FORM keeps what the official PDF prints. Each row of
data/standard_corrections.tsv replaces one printed word in the standard base
FORM of one section. Runs after standardize.py --copy (which would overwrite
the standard tier) and before add_phonology.py, so the standard PHON is built
from the corrected spelling.
"""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]


def load_corrections(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))


def apply_corrections(xml_dir: Path, rows: list[dict[str, str]]) -> int:
    """Apply every row; raise ValueError unless each printed word occurs once."""
    by_language: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_language.setdefault(row["language"], []).append(row)
    applied = 0
    for language, language_rows in sorted(by_language.items()):
        path = xml_dir / language / f"{language}.xml"
        tree = ET.parse(path)
        root = tree.getroot()
        for row in language_rows:
            sentence = root.find(f'S[@id="{row["section_id"]}"]')
            if sentence is None:
                raise ValueError(f"{path}: no S id={row['section_id']}")
            original = next(f for f in sentence.findall('FORM[@kindOf="original"]') if f.get("ver") is None)
            standard = next(f for f in sentence.findall('FORM[@kindOf="standard"]') if f.get("ver") is None)
            printed = row["printed"]
            # The original must still show the printed word: this corrects the
            # standard tier only.
            if original.text.count(printed) != 1 or standard.text.count(printed) != 1:
                raise ValueError(
                    f"{language} S{row['section_id']}: expected {printed!r} once in each tier"
                )
            standard.text = standard.text.replace(printed, row["standard"])
            applied += 1
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return applied


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, required=True)
    parser.add_argument(
        "--table",
        type=Path,
        default=CODE_ROOT / "data" / "standard_corrections.tsv",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        applied = apply_corrections(args.xml_dir, load_corrections(args.table))
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"applied {applied} standard-tier corrections")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
