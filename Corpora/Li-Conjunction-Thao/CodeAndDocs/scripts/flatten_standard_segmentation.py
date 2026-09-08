#!/usr/bin/env python3
"""Retain the merged Li-only finalization of S standard infix brackets.

Current standardize.py owns hyphen/clitic cleanup. The merged corpus ruling
also removes S-level infix brackets before phonology; W/M retain the analysis.
This is an explicit POL-047 deviation until shared standardization owns it.
"""

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


def flatten_file(path: Path) -> None:
    tree = ET.parse(path)
    for form in tree.findall("./S/FORM[@kindOf='standard']"):
        if form.text:
            form.text = form.text.replace("<", "").replace(">", "")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml_dir", type=Path)
    args = parser.parse_args()
    for path in sorted(args.xml_dir.rglob("*.xml")):
        flatten_file(path)


if __name__ == "__main__":
    main()
