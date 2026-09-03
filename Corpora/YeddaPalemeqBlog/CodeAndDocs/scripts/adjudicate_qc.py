#!/usr/bin/env python3
"""Fail closed unless current Yedda QC matches reviewed source evidence."""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


# V116 counts the 30 source diacritics and code-switched characters the blog
# prints; 9 of them sit in the standard tier of two quoted Mandarin kin terms
# that standardize.py --remove_accents flattens, so only 21 remain.
EXPECTED_TEXT = Counter({"V116": 21, "V122": 2389})
# V064 is one finding per morpheme without a gloss. fix_m_tier.py removes the
# 1,165 mirror morphemes of the unparsed sentences, so the inventory falls from
# 7,657 to 6,492 without any gloss being invented or lost.
EXPECTED_GLOSS = Counter({"V060": 18, "V062": 274, "V064": 6492, "V065": 731})
EXPECTED_DUPLICATES = {
    (
        "aicu a sapui katua zaljum mamaw a kinamasanpazangalan tua tja nasi.",
        frozenset({"S511_1", "S194_1"}),
    ),
    ("inika nanguaq a mikemudan itjen.", frozenset({"S531_1", "S463_1"})),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def duplicate_groups(rows: list[dict[str, str]]) -> set[tuple[str, frozenset[str]]]:
    grouped: dict[str, set[str]] = {}
    for row in rows:
        if row["severity"] != "SOFT" or row["scope"] != "within-file":
            raise SystemExit(f"Unexpected duplicate finding: {row}")
        grouped.setdefault(row["normalized_text"], set()).add(row["s_id"])
    return {(text, frozenset(ids)) for text, ids in grouped.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--xml-root", type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    xml_root = args.xml_root.resolve()

    xml_paths = sorted(xml_root.rglob("*.xml"))
    if len(xml_paths) != 1:
        raise SystemExit(f"Expected one canonical XML file, got {len(xml_paths)}")
    root = ET.parse(xml_paths[0]).getroot()
    if len(root.findall("S")) != 671:
        raise SystemExit("Canonical sentence count changed")

    xml_rows = read_csv(run_dir / "validate_xml_findings.csv")
    if xml_rows:
        raise SystemExit(f"Structural XML findings are unresolved: {len(xml_rows)}")

    text_rows = read_csv(run_dir / "validate_text_findings.csv")
    text_counts = Counter(row["rule_id"] for row in text_rows)
    if text_counts != EXPECTED_TEXT or any(
        row["severity"] != "SOFT" for row in text_rows
    ):
        raise SystemExit(f"Text finding inventory changed: {text_counts}")

    gloss_rows = read_csv(run_dir / "validate_glosses_findings.csv")
    gloss_counts = Counter(row["rule_id"] for row in gloss_rows)
    if gloss_counts != EXPECTED_GLOSS or any(
        row["severity"] != "SOFT" for row in gloss_rows
    ):
        raise SystemExit(f"Gloss finding inventory changed: {gloss_counts}")

    duplicate_rows = []
    for name in ("duplicate_original_findings.csv", "duplicate_standard_findings.csv"):
        rows = read_csv(run_dir / name)
        if duplicate_groups(rows) != EXPECTED_DUPLICATES:
            raise SystemExit(f"Duplicate inventory changed: {name}")
        duplicate_rows.extend(rows)

    port_log = (run_dir / "11_port_readiness.log").read_text(encoding="utf-8")
    if "port-readiness: 0 HARD" not in port_log:
        raise SystemExit("Port readiness did not retain the expected 0-HARD verdict")
    warning_lines = [line for line in port_log.splitlines() if " WARN:" in line]
    if any(
        line != "P001 WARN: not a git checkout; Private/ tracking not checkable here"
        for line in warning_lines
    ):
        raise SystemExit(f"Unexpected port-readiness warning: {warning_lines}")

    total = len(text_rows) + len(gloss_rows) + len(duplicate_rows)
    print(f"Reviewed {total} finding occurrences: {total} accepted, 0 unresolved")


if __name__ == "__main__":
    main()
