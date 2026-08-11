#!/usr/bin/env python3
"""Flatten segmentation markers from the sentence-level standard tier.

standardize.py rebuilds the standard tier from the original, which re-introduces
the source segmentation notation ('-', '=', '<', '>'). For this corpus those
markers are only morpheme boundaries (see README: the glottal stop is 'ʔ', never
'-'), so they are removed from the sentence-level FORM[@kindOf="standard"] while
the W/M standard tiers keep them for the morphological analysis.

Run after standardize.py and before add_phonology.py. Usage:

    python3 scripts/flatten_standard_segmentation.py <XML-dir-or-file>
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MARKERS = re.compile(r"[-=<>]")


def flatten_file(path: Path) -> None:
    tree = ET.parse(path)
    root = tree.getroot()
    for sentence in root.iter("S"):
        # Direct FORM children of S only — never the W/M descendants.
        for form in sentence.findall("FORM"):
            if form.get("kindOf") == "standard" and form.text:
                form.text = MARKERS.sub("", form.text)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: flatten_standard_segmentation.py <XML-dir-or-file>")
    target = Path(sys.argv[1])
    files = [target] if target.is_file() else sorted(target.rglob("*.xml"))
    for path in files:
        flatten_file(path)
        print(f"flattened sentence-level standard segmentation: {path}")


if __name__ == "__main__":
    main()
