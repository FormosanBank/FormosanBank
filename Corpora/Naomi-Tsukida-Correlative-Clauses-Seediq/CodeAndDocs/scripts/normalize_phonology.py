#!/usr/bin/env python3
"""Apply the reviewed Seediq PHON punctuation and glottal-stop policy."""

from __future__ import annotations

import argparse
import re
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path


def normalize(text: str) -> str:
    value = text.replace("'", "ʔ")
    value = "".join(
        character
        for character in value
        if not unicodedata.category(character).startswith("P")
    )
    return re.sub(r"\s+", " ", value).strip()


def process(path: Path) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    phonology = root.findall(".//PHON")
    changed = 0
    for phon in phonology:
        if phon.text is None:
            raise ValueError(f"Empty PHON in {path}")
        normalized = normalize(phon.text)
        if not normalized:
            raise ValueError(f"PHON normalization removed all content in {path}")
        if normalized != phon.text:
            phon.text = normalized
            changed += 1
    if changed:
        ET.indent(root, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return len(phonology), changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.path] if args.path.is_file() else sorted(args.path.rglob("*.xml"))
    if not paths:
        raise SystemExit("No XML files found")
    total = changed = 0
    for path in paths:
        path_total, path_changed = process(path)
        total += path_total
        changed += path_changed
    print(f"Normalized {changed} of {total} PHON tiers.")


if __name__ == "__main__":
    main()
