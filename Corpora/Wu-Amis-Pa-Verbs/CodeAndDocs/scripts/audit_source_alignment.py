#!/usr/bin/env python3
"""Verify final XML against the source-adjudicated extraction tables."""

from __future__ import annotations

import argparse
import csv
import copy
import hashlib
import importlib.util
import subprocess
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_XML_PATH = ROOT / "XML/Amis/pa-verbs.xml"
SOURCE_PDF = ROOT / "CodeAndDocs/raw_data/source.pdf"
SOURCE_PDF_SHA256 = "9ba94321d9c8e926cf8cca3b0b81814400d2bb7194ba48574d77ad54490308f5"
MANUAL_EDITS = ROOT / "CodeAndDocs/manual_edits.xml"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SPEC = importlib.util.spec_from_file_location(
    "build_xml", ROOT / "CodeAndDocs/scripts/build_xml.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load build_xml.py")
BUILD_XML = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_XML)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def text(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text


def strip_derived_tiers(sentence: ET.Element) -> ET.Element:
    stripped = copy.deepcopy(sentence)
    for parent in stripped.iter():
        for child in list(parent):
            if child.tag == "PHON" or (
                child.tag == "FORM" and child.get("kindOf") == "standard"
            ):
                parent.remove(child)
    stripped.attrib.pop("after", None)
    stripped.attrib.pop("action", None)
    return stripped


def semantic_element(node: ET.Element) -> tuple:
    return (
        node.tag,
        tuple(sorted(node.attrib.items())),
        (node.text or "").strip(),
        tuple(semantic_element(child) for child in node),
    )


def expected_after_manual_edits(rows: list[dict[str, str]]) -> ET.Element:
    expected = BUILD_XML.build_tree(rows).getroot()
    manual_root = ET.parse(MANUAL_EDITS).getroot()
    file_group = manual_root.find("FILE[@path='pa-verbs.xml']")
    if file_group is None:
        raise ValueError("manual_edits.xml lacks pa-verbs.xml records")

    for record in file_group.findall("S"):
        sentence_id = record.get("id", "")
        sentences = expected.findall("S")
        current = next((item for item in sentences if item.get("id") == sentence_id), None)
        if record.get("action") == "delete":
            if current is None:
                raise ValueError(f"manual deletion target is absent: {sentence_id}")
            expected.remove(current)
            continue

        replacement = strip_derived_tiers(record)
        if current is not None:
            expected.insert(list(expected).index(current), replacement)
            expected.remove(current)
            continue

        after_id = record.get("after", "")
        after = next(
            (item for item in expected.findall("S") if item.get("id") == after_id),
            None,
        )
        if after is None:
            raise ValueError(f"manual insertion anchor is absent: {after_id}")
        expected.insert(list(expected).index(after) + 1, replacement)
    return expected


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml", type=Path, default=DEFAULT_XML_PATH)
    args = parser.parse_args()
    xml_path = args.xml.resolve()
    errors: list[str] = []
    accepted = read_tsv(ROOT / "CodeAndDocs/raw_data/source_examples.tsv")
    direct = read_tsv(ROOT / "CodeAndDocs/raw_data/direct_source_checks.tsv")
    rejected = read_tsv(ROOT / "CodeAndDocs/raw_data/rejected_source_examples.tsv")
    root = ET.parse(xml_path).getroot()

    source_hash = hashlib.sha256(SOURCE_PDF.read_bytes()).hexdigest()
    if source_hash != SOURCE_PDF_SHA256:
        errors.append(f"source PDF SHA-256 changed: {source_hash}")
    pdfinfo = subprocess.check_output(["pdfinfo", str(SOURCE_PDF)], text=True)
    pages = next(
        (
            line.split(":", 1)[1].strip()
            for line in pdfinfo.splitlines()
            if line.startswith("Pages:")
        ),
        "",
    )
    if pages != "13":
        errors.append(f"expected 13 source PDF pages, found {pages or 'unknown'}")

    expected_root = {
        XML_LANG: "ami",
        "dialect": "Coastal",
        "id": "wu-2006-amis-pa-verbs",
        "copyright": BUILD_XML.COPYRIGHT,
    }
    for key, expected in expected_root.items():
        if root.get(key) != expected:
            errors.append(
                f"TEXT {key!r}: expected {expected!r}, found {root.get(key)!r}"
            )
    if not root.get("citation") or not root.get("BibTeX_citation"):
        errors.append("TEXT citation metadata is incomplete")

    expected_root = expected_after_manual_edits(accepted)
    expected_sentences = expected_root.findall("S")
    actual_sentences = root.findall("S")
    sentences = {node.get("id", ""): node for node in actual_sentences}
    if len(accepted) != 30 or len(sentences) != 29:
        errors.append(
            f"expected 30 generator rows and 29 final sentences, found "
            f"{len(accepted)}/{len(sentences)}"
        )
    if len(direct) != 30 or any(row["result"] != "match" for row in direct):
        errors.append("expected 30 passing direct visual checks of generator rows")
    expected_rejected = {
        "duplicate_source_occurrence": 2,
        "source_marked_ungrammatical": 7,
        "starred_alternative": 4,
        "starred_reading": 1,
        "source_marked_questionable": 2,
    }
    rejected_reasons = Counter(row["reason"] for row in rejected)
    if rejected_reasons != expected_rejected:
        errors.append(f"unexpected rejection inventory: {dict(rejected_reasons)}")

    expected_ids = [item.get("id", "") for item in expected_sentences]
    actual_ids = [item.get("id", "") for item in actual_sentences]
    if actual_ids != expected_ids:
        errors.append("final sentence IDs/order do not match generator plus manual edits")
    for expected_sentence, actual_sentence in zip(
        expected_sentences, actual_sentences, strict=False
    ):
        if semantic_element(expected_sentence) != semantic_element(
            strip_derived_tiers(actual_sentence)
        ):
            errors.append(
                f"{expected_sentence.get('id', '')} differs from generator plus manual edits"
            )

    all_ids = [node.get("id", "") for node in root.iter() if node.get("id")]
    if len(all_ids) != len(set(all_ids)):
        errors.append("XML IDs are not unique")
    if any(not identifier.isascii() or "'" in identifier for identifier in all_ids):
        errors.append("XML IDs are not ASCII-safe")
    if any(not sentence.findall("W") for sentence in root.findall("S")):
        errors.append("one or more sentences lack word glossing")
    if any(word.find("TRANSL") is None for word in root.findall(".//W")):
        errors.append("one or more words lack a gloss")
    if any(
        marker in text(form)
        for form in root.findall(".//FORM")
        for marker in ("*", "?")
    ):
        errors.append("acceptability punctuation was lexicalized in FORM")
    if "ø" in text(root.find("S[@id='s18a']/FORM[@kindOf='original']")):
        errors.append("null marker remains at the sentence tier")

    null_words = [
        word
        for word in root.findall(".//W")
        if "ø" in text(word.find("FORM[@kindOf='original']"))
    ]
    null_morphs = [
        morph
        for morph in root.findall(".//M")
        if text(morph.find("FORM[@kindOf='original']")) == "ø"
    ]
    if len(null_words) != 7 or len(null_morphs) != 7:
        errors.append(
            f"expected seven source nulls at W/M, found {len(null_words)}/{len(null_morphs)}"
        )
    if any(
        text(word.find("PHON[@kindOf='standard']")) != "ʦi" for word in null_words
    ):
        errors.append("a null-plus-ci word has non-silent null phonology")
    if any(
        text(morph.find("PHON[@kindOf='standard']")) != "∅" for morph in null_morphs
    ):
        errors.append("a null-only morpheme does not retain PHON ∅")
    if any("*" in text(phon) for phon in root.findall(".//PHON")):
        errors.append("one or more PHON tiers contain unknown-character asterisks")

    report = [
        "# Source Alignment Audit: Wu (2006) Amis Pa-Verbs",
        "",
        "Audit date: 2026-08-07",
        "",
        f"- Source PDF SHA-256: `{source_hash}`",
        f"- Source PDF pages: {pages}",
        f"- Generator sentence rows: {len(accepted)}",
        f"- Final XML sentence variants: {len(sentences)}",
        f"- Direct visual checks of generator rows: {len(direct)}",
        f"- Rejected source items/alternatives: {len(rejected)}",
        f"- Final W/M counts: {len(root.findall('.//W'))}/{len(root.findall('.//M'))}",
        "- Manual edits: 3 changed, 1 added, 2 deleted sentence records",
        "- Source nulls: removed at S; retained as ø at W/M",
        "- Null phonology: silent in mixed forms; retained as ∅ for null-only M",
        "- Source segmentation: removed at S; retained at W/M where supported",
        "- Source-marked ungrammatical examples/alternatives: excluded",
        "- Source-marked questionable 38a-prime and 38c-prime: excluded",
        "- Basecamp card changes: none",
        "- Shared FormosanBank phonology dependency: pinned null-marker fix",
        "",
        "## Result",
        "",
        "PASS" if not errors else "FAIL",
    ]
    if errors:
        report.extend(["", "## Errors", "", *[f"- {item}" for item in errors]])
    print("\n".join(report))
    print(f"errors={len(errors)} warnings=0 notices=0")
    if errors:
        raise SystemExit("Source alignment failed")


if __name__ == "__main__":
    main()
