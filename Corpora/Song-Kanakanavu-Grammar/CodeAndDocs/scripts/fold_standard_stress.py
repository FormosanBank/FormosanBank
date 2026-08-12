#!/usr/bin/env python3
"""Fold source stress accents in standard and alternate FORM tiers."""

from __future__ import annotations

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML_PATH = ROOT.parent / "XML"
ACCENT_CHARACTERS = frozenset("áéíóúÁÉÍÓÚ")
ACCENT_MAP = str.maketrans(
    {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
    }
)
STANDARD_KINDS = {"standard", "alternate"}


def fold_stress(text: str) -> str:
    return text.translate(ACCENT_MAP)


def xml_files(path: Path) -> list[Path]:
    return [path] if path.is_file() else sorted(path.rglob("*.xml"))


def process_file(path: Path) -> int:
    tree = ET.parse(path)
    root = tree.getroot()
    changed = 0
    for form in root.findall(".//FORM"):
        if form.get("kindOf") not in STANDARD_KINDS or not form.text:
            continue
        folded = fold_stress(form.text)
        if folded != form.text:
            form.text = folded
            changed += 1
    if changed:
        ET.indent(root, space="  ")
        tree.write(path, encoding="UTF-8", xml_declaration=True)
    return changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora_path", type=Path, default=DEFAULT_XML_PATH)
    args = parser.parse_args()
    files = xml_files(args.corpora_path)
    total = 0
    for path in files:
        count = process_file(path)
        total += count
        print(f"Folded source stress in {count} standard FORM tiers in {path}")
    print(f"Folded source stress in {total} standard FORM tiers across {len(files)} files")


if __name__ == "__main__":
    main()
