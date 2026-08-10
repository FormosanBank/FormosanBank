#!/usr/bin/env python3
"""Remove source analysis notation from S-level standard forms only."""

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def normalize(text: str) -> str:
    value = value_without_notation(text)
    return re.sub(r"\s+", " ", value).strip()


def value_without_notation(text: str) -> str:
    return text.translate(str.maketrans("", "", "-=()[]"))


def process(path: Path) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    changed = 0
    sentences = root.findall("S")
    for sentence in sentences:
        form = sentence.find("FORM[@kindOf='standard']")
        if form is None or form.text is None:
            raise ValueError(f"Missing S-level standard FORM at {sentence.get('id')}")
        normalized = normalize(form.text)
        if normalized != form.text:
            form.text = normalized
            changed += 1
    if changed:
        ET.indent(root, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
    return len(sentences), changed


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    paths = [args.path] if args.path.is_file() else sorted(args.path.rglob("*.xml"))
    if not paths:
        raise SystemExit("No XML files found")
    sentence_count = changed_count = 0
    for path in paths:
        sentences, changed = process(path)
        sentence_count += sentences
        changed_count += changed
    print(
        f"Normalized source notation in {changed_count} of {sentence_count} "
        "S-level standard forms."
    )


if __name__ == "__main__":
    main()
