#!/usr/bin/env python3
"""Apply the one reviewed standard-tier segmentation decision."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
XML = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"


def main() -> None:
    tree = ET.parse(XML)
    root = tree.getroot()
    sentence = root.find("S[@id='S652653654_2']")
    if sentence is None:
        raise SystemExit("Missing S652653654_2")
    original = sentence.find("FORM[@kindOf='original']")
    standard = sentence.find("FORM[@kindOf='standard']")
    if original is None or standard is None:
        raise SystemExit("Missing S652653654_2 FORM tiers")
    expected = "pai, maya manu seman-neka-aravac tua zuma."
    if original.text != expected or standard.text != expected:
        raise SystemExit("Unexpected S652653654_2 source surface")
    standard.text = "pai, maya manu semannekaaravac tua zuma."
    standard.set("notes", "Source segmentation is removed only in the standard tier.")
    ET.indent(tree, space="  ")
    tree.write(XML, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
