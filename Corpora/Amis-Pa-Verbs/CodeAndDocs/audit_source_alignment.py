#!/usr/bin/env python3
"""Verify final XML against the reviewed Wu source inventory."""

from __future__ import annotations

import copy
import csv
import importlib.util
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "XML/Amis/pa-verbs.xml"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SPEC = importlib.util.spec_from_file_location(
    "build_xml", ROOT / "CodeAndDocs/build_xml.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load build_xml.py")
BUILD_XML = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_XML)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def node_text(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text


def strip_machine_tiers(sentence: ET.Element) -> ET.Element:
    stripped = copy.deepcopy(sentence)
    for parent in stripped.iter():
        for child in list(parent):
            if child.tag == "PHON" or (
                child.tag == "FORM" and child.get("kindOf") == "standard"
            ):
                parent.remove(child)
    return stripped


def semantic_element(node: ET.Element) -> tuple:
    return (
        node.tag,
        tuple(sorted(node.attrib.items())),
        (node.text or "").strip(),
        tuple(semantic_element(child) for child in node),
    )


def tier_is_complete(node: ET.Element) -> bool:
    for kind_of in ("original", "standard"):
        forms = node.findall(f"FORM[@kindOf='{kind_of}']")
        phons = node.findall(f"PHON[@kindOf='{kind_of}']")
        if len(forms) != 1 or len(phons) != 1:
            return False
    return True


def main() -> None:
    root = ET.parse(XML_PATH).getroot()
    accepted = read_tsv(ROOT / "CodeAndDocs/source_examples.tsv")
    expected = BUILD_XML.build_tree(accepted).getroot()
    errors = []
    if semantic_element(strip_machine_tiers(root)) != semantic_element(expected):
        errors.append("source tiers differ from the committed transcription")
    ids = [node.get("id") for node in root.iter() if node.get("id")]
    if len(ids) != len(set(ids)):
        errors.append("duplicate IDs")
    if any(not tier_is_complete(node) for node in root.iter() if node.tag in {"S", "W", "M"}):
        errors.append("missing original/standard FORM or PHON")
    coverage = read_tsv(ROOT / "CodeAndDocs/source_coverage.tsv")
    if [row["pdf_page"] for row in coverage] != [str(n) for n in range(1, 14)]:
        errors.append("source page inventory is incomplete")
    rejected = read_tsv(ROOT / "CodeAndDocs/rejected_source_examples.tsv")
    if Counter(row["reason"] for row in rejected) != {
        "duplicate_source_occurrence": 2, "source_marked_ungrammatical": 7,
        "starred_alternative": 3, "starred_reading": 1,
        "source_marked_questionable": 2,
    }:
        errors.append("source exclusion inventory changed")
    if errors:
        raise SystemExit("; ".join(errors))
    print("Source tiers match the committed transcription; 29 S and all 13 pages accounted for.")
    print("This consistency check does not establish source accuracy or a QC verdict.")


if __name__ == "__main__":
    main()
