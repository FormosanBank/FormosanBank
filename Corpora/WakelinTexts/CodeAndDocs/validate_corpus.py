#!/usr/bin/env python3
"""Validate the public Wakelin reconstruction against its checked ledgers."""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

from build_corpus import OverrideKey, load_id_overrides, resolve_node_id
from expand_alternatives import load_expanded_ledger

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
PUBLICATION_NOTICE = "All rights reserved; FormosanBank has permission to publish."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml-root", type=Path, required=True)
    parser.add_argument("--source-ledger", type=Path, required=True)
    parser.add_argument("--alternative-decisions", type=Path, required=True)
    parser.add_argument("--id-ledger", type=Path, required=True)
    parser.add_argument("--source-checks", type=Path, required=True)
    return parser.parse_args()


def tier_text(element: ET.Element, tag: str, kind: str | None = None) -> str:
    for child in element.findall(tag):
        if kind is None or child.get("kindOf") == kind:
            return child.text or ""
    raise ValueError(f"Missing {tag} {kind or ''} in {element.get('id')}")


def translation_values(element: ET.Element) -> list[dict[str, str]]:
    return [
        {
            "text": translation.text or "",
            "lang": translation.get(XML_LANG, ""),
            **({"ver": translation.get("ver", "")} if translation.get("ver") else {}),
        }
        for translation in element.findall("TRANSL")
    ]


def validate_node(
    element: ET.Element,
    source_record: dict[str, Any],
    expected_id: str,
    relative: str,
    sentence_id: str,
    overrides: dict[OverrideKey, str],
    used_overrides: set[OverrideKey],
    word_number: int | None = None,
) -> Counter[str]:
    if element.get("id") != expected_id:
        raise ValueError(
            f"Non-stable ID in {relative}: expected {expected_id}, "
            f"found {element.get('id')}"
        )

    source_forms = source_record["forms"]
    original_forms = [
        form.text or "" for form in element.findall("FORM[@kindOf='original']")
    ]
    expected_original = [
        form["text"] for form in source_forms if form["kind"] == "original"
    ]
    if original_forms != expected_original:
        raise ValueError(f"Source FORM mismatch in {relative} {expected_id}")
    standard_forms = [
        form.text or "" for form in element.findall("FORM[@kindOf='standard']")
    ]
    if standard_forms != expected_original:
        raise ValueError(
            f"Standard FORM must copy original in {relative} {expected_id}"
        )
    if element.findall("FORM[@kindOf='alternate']"):
        raise ValueError(f"Unexpanded alternate FORM in {relative} {expected_id}")
    if translation_values(element) != source_record.get("translations", []):
        raise ValueError(f"TRANSL mismatch in {relative} {expected_id}")

    totals = Counter({element.tag: 1})
    if element.tag == "S":
        children = element.findall("W")
        child_records = source_record.get("words", [])
        for number, (child, child_record) in enumerate(
            zip(children, child_records, strict=True), start=1
        ):
            child_id, key = resolve_node_id(
                overrides, relative, sentence_id, "W", number, None
            )
            if key in overrides:
                used_overrides.add(key)
            totals.update(
                validate_node(
                    child,
                    child_record,
                    child_id,
                    relative,
                    sentence_id,
                    overrides,
                    used_overrides,
                    word_number=number,
                )
            )
    elif element.tag == "W":
        if word_number is None:
            raise ValueError(f"Missing word position for {relative} {expected_id}")
        children = element.findall("M")
        child_records = source_record.get("morphemes", [])
        for number, (child, child_record) in enumerate(
            zip(children, child_records, strict=True), start=1
        ):
            child_id, key = resolve_node_id(
                overrides, relative, sentence_id, "M", word_number, number
            )
            if key in overrides:
                used_overrides.add(key)
            totals.update(
                validate_node(
                    child,
                    child_record,
                    child_id,
                    relative,
                    sentence_id,
                    overrides,
                    used_overrides,
                )
            )
    else:
        children = []
        child_records = []

    if len(children) != len(child_records):
        raise ValueError(f"Child count mismatch in {relative} {expected_id}")
    return totals


def main() -> int:
    args = parse_args()
    ledger = load_expanded_ledger(args.source_ledger, args.alternative_decisions)
    overrides = load_id_overrides(args.id_ledger)
    used_overrides: set[OverrideKey] = set()
    paths = sorted(args.xml_root.rglob("*.xml"))
    if len(paths) != 6:
        raise ValueError(f"Expected 6 XML files, found {len(paths)}")
    roots = {
        str(path.relative_to(args.xml_root)): ET.parse(path).getroot()
        for path in paths
    }
    source_by_path = {text["path"]: text for text in ledger["texts"]}
    if set(roots) != set(source_by_path):
        raise ValueError("XML paths differ from source ledger")

    totals = Counter()
    for relative, root in roots.items():
        source_text = source_by_path[relative]
        expected_metadata = {
            "id": source_text["text_id"],
            XML_LANG: source_text["language"],
            "dialect": source_text["dialect"],
            "source": source_text["source"],
            "copyright": PUBLICATION_NOTICE,
            "citation": source_text["citation"],
            "BibTeX_citation": source_text["bibtex"],
        }
        for attribute, expected in expected_metadata.items():
            if root.get(attribute) != expected:
                raise ValueError(
                    f"TEXT metadata mismatch in {relative}: {attribute}"
                )
        if list(root.iter("PHON")):
            raise ValueError(f"Unapproved PHON tier in {relative}")
        sentences = root.findall("S")
        if len(sentences) != len(source_text["sentences"]):
            raise ValueError(f"Sentence count mismatch in {relative}")
        for sentence, source_record in zip(
            sentences, source_text["sentences"], strict=True
        ):
            sentence_id = source_record["id"]
            totals.update(
                validate_node(
                    sentence,
                    source_record,
                    sentence_id,
                    relative,
                    sentence_id,
                    overrides,
                    used_overrides,
                )
            )

    unused_overrides = set(overrides) - used_overrides
    if unused_overrides:
        raise ValueError(f"Unused public ID overrides: {sorted(unused_overrides)}")

    with args.source_checks.open(newline="", encoding="utf-8") as source:
        checks = list(csv.DictReader(source))
    if len(checks) != 9:
        raise ValueError(f"Expected 9 direct source fixtures, found {len(checks)}")
    for row in checks:
        root = roots[row["path"]]
        sentence = root.find(f"S[@id='{row['sentence_id']}']")
        if sentence is None:
            raise ValueError(f"Missing fixture {row['path']} {row['sentence_id']}")
        if tier_text(sentence, "FORM", "original") != row["expected_form"]:
            raise ValueError(f"FORM fixture mismatch: {row['path']} {row['sentence_id']}")
        if tier_text(sentence, "TRANSL") != row["expected_translation"]:
            raise ValueError(
                f"TRANSL fixture mismatch: {row['path']} {row['sentence_id']}"
            )

    if totals != Counter({"M": 1183, "W": 926, "S": 190}):
        raise ValueError(f"Unexpected corpus totals: {totals}")
    print(
        "PASS: 190 S, 926 W, 1,183 M, 9 direct source fixtures, "
        "stable public IDs, copied standard FORM, and no PHON validated."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
