"""Replay the five scoped August 12 decisions with the current shared merger."""

import argparse
import csv
import sys
from pathlib import Path

from lxml import etree


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formosanbank", type=Path, required=True)
    parser.add_argument("--xml", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.formosanbank.resolve()))
    from QC.cleaning.remove_duplicate_sentences import apply_removals, normalize_for_comparison
    from QC.xml_forms import find_base_form

    root = etree.parse(str(args.xml)).getroot()
    sentences = {s.get("id"): s for s in root.findall("S")}
    path = str(args.xml.resolve())
    removals = []
    with Path(__file__).with_name("reviewed_merges.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            removed, kept = row["removed_id"], row["kept_id"]
            before = find_base_form(sentences[removed], "original")
            after = find_base_form(sentences[kept], "original")
            if before is None or after is None or not before.text or not after.text:
                raise ValueError(f"Missing source FORM for reviewed merge: {removed}, {kept}")
            if normalize_for_comparison(before.text) != normalize_for_comparison(after.text):
                raise ValueError(f"Source FORM changed since the reviewed merge: {removed}, {kept}")
            removals.append((path, removed, path, kept))
    apply_removals(removals)


if __name__ == "__main__":
    main()
