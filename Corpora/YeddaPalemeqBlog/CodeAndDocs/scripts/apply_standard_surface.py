#!/usr/bin/env python3
"""Record the one reviewed standard-tier segmentation decision.

The corpus runs ``standardize.py --remove_accents``, whose C012 hyphen step
already removes the source segmentation from the standard FORM of
``S652653654_2`` — the only sentence in the corpus that carries it. This
script no longer performs that edit; it asserts the surface C012 produced and
attaches the note that says why the two tiers differ.

Fails closed: if either tier stops matching, the decision has to be reviewed
again rather than silently re-applied.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
XML = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"

SENTENCE_ID = "S652653654_2"
EXPECTED_ORIGINAL = "pai, maya manu seman-neka-aravac tua zuma."
EXPECTED_STANDARD = "pai, maya manu semannekaaravac tua zuma."
NOTE = "Source segmentation is removed only in the standard tier."


def main() -> None:
    tree = ET.parse(XML)
    root = tree.getroot()
    sentence = root.find(f"S[@id='{SENTENCE_ID}']")
    if sentence is None:
        raise SystemExit(f"Missing {SENTENCE_ID}")
    original = sentence.find("FORM[@kindOf='original']")
    standard = sentence.find("FORM[@kindOf='standard']")
    if original is None or standard is None:
        raise SystemExit(f"Missing {SENTENCE_ID} FORM tiers")
    if original.text != EXPECTED_ORIGINAL:
        raise SystemExit(f"Unexpected {SENTENCE_ID} source surface")
    if standard.text != EXPECTED_STANDARD:
        raise SystemExit(
            f"Unexpected {SENTENCE_ID} standard surface: C012 produced "
            f"{standard.text!r}, expected {EXPECTED_STANDARD!r}"
        )
    standard.set("notes", NOTE)
    ET.indent(tree, space="  ")
    tree.write(XML, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
