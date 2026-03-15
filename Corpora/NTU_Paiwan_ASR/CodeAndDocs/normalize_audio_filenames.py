"""
normalize_audio_filenames.py

Replaces spaces with underscores in the `audio` attribute of every <TEXT>
element across all XML files under Final_XML, updating each file in place.

Usage
-----
    python normalize_audio_filenames.py [--xml_root Final_XML]
"""

import argparse
import sys
from pathlib import Path

from lxml import etree


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--xml_root",
        default="Final_XML",
        help="Root directory containing XML files (default: Final_XML)",
    )
    args = parser.parse_args()

    xml_root = Path(args.xml_root).resolve()
    xml_files = sorted(xml_root.rglob("*.xml"))

    if not xml_files:
        print(f"No XML files found under {xml_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(xml_files)} XML file(s) under {xml_root}")
    changed = 0

    for xml_file in xml_files:
        tree = etree.parse(str(xml_file))
        root = tree.getroot()

        text_elem = root if root.tag == "TEXT" else root.find(".//TEXT")
        if text_elem is None:
            continue

        audio_val = text_elem.get("audio", "")
        new_val = audio_val.replace(" ", "_")

        if new_val == audio_val:
            continue

        text_elem.set("audio", new_val)
        tree.write(
            str(xml_file),
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=True,
        )
        print(f"  {xml_file.name}: '{audio_val}' → '{new_val}'")
        changed += 1

    print(f"\nUpdated {changed} file(s).")


if __name__ == "__main__":
    main()
