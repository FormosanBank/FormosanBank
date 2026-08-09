#!/usr/bin/env python3
"""Preserve reviewed Huteson segmentation in Rukai standard sentence forms."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML_DIR = ROOT / "XML" / "Rukai"
DEFAULT_MAPPING = ROOT / "CodeAndDocs" / "huteson_source_to_ortho113.tsv"


def read_replacements(path: Path, dialect: str) -> list[tuple[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if not rows or dialect not in rows[0]:
        raise ValueError(f"No {dialect!r} column in {path}")
    return [(row["original"], row[dialect]) for row in rows if row["original"]]


def expected_standard_form(form: str, replacements: list[tuple[str, str]]) -> str:
    for original, replacement in replacements:
        form = form.replace(original, replacement)
    return re.sub(r"\s+", " ", form).strip()


def preserve_file(path: Path, mapping_path: Path) -> tuple[int, int]:
    tree = etree.parse(str(path))
    root = tree.getroot()
    dialect = root.get("dialect") or ""
    replacements = read_replacements(mapping_path, dialect)
    changed = 0
    restored_hyphens = 0
    for sentence in root.findall("./S"):
        original = sentence.find("./FORM[@kindOf='original']")
        standard = sentence.find("./FORM[@kindOf='standard']")
        if original is None or not original.text or standard is None:
            raise ValueError(f"Missing sentence FORM tier in {path}: {sentence.get('id')}")
        expected = expected_standard_form(original.text, replacements)
        current = standard.text or ""
        if current != expected:
            restored_hyphens += max(0, expected.count("-") - current.count("-"))
            standard.text = expected
            changed += 1
    if changed:
        tree.write(str(path), xml_declaration=True, pretty_print=True, encoding="utf-8")
    return changed, restored_hyphens


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml-dir", type=Path, default=DEFAULT_XML_DIR)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    args = parser.parse_args()

    changed = 0
    restored = 0
    for path in sorted(args.xml_dir.glob("*.xml")):
        file_changed, file_restored = preserve_file(path, args.mapping)
        changed += file_changed
        restored += file_restored
    print(f"Updated {changed} sentence standard forms; restored {restored} hyphens.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
