#!/usr/bin/env python3
"""Apply the reviewed Virginia Fey source decisions to the POL-035 baseline."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from lxml import etree


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def fail(message: str) -> None:
    raise SystemExit(f"ERROR: {message}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize(text: str | None) -> str:
    value = unicodedata.normalize("NFC", text or "")
    value = value.translate(
        str.maketrans(
            {
                "’": "'",
                "‘": "'",
                "ʼ": "'",
                "ʻ": "'",
                "`": "'",
                "“": '"',
                "”": '"',
                "「": '"',
                "」": '"',
                "＂": '"',
                "‐": "-",
                "‑": "-",
                "‒": "-",
                "–": "-",
                "—": "-",
                "―": "-",
            }
        )
    )
    return re.sub(r"\s+", " ", value).strip()


def load_sheet(path: Path) -> tuple[list[str], dict[int, list[str]]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.reader(source)
        try:
            header = next(reader)
        except StopIteration:
            fail(f"empty source sheet: {path}")
        rows = {index: row for index, row in enumerate(reader, start=1)}
    return header, rows


def original_form(sentence: etree._Element) -> etree._Element:
    forms = sentence.xpath('./FORM[@kindOf="original"]')
    if len(forms) != 1:
        fail(f"{sentence.get('id')}: expected one original FORM, found {len(forms)}")
    return forms[0]


def drop_derived_tiers(sentence: etree._Element) -> None:
    for child in list(sentence):
        if child.tag == "PHON" or (
            child.tag == "FORM" and child.get("kindOf") == "standard"
        ):
            sentence.remove(child)


def translation_nodes(sentence: etree._Element, lang: str) -> list[etree._Element]:
    return [node for node in sentence.findall("TRANSL") if node.get(XML_LANG) == lang]


def validate_inputs(code_docs: Path, decisions: dict) -> dict[int, list[str]]:
    baseline_path = code_docs / decisions["baseline"]["path"]
    expected = decisions["baseline"]["sha256"]
    if sha256(baseline_path) != expected:
        fail(f"POL-035 baseline hash drifted: {baseline_path}")

    sheet_path = code_docs / decisions["sheet"]["path"]
    if sha256(sheet_path) != decisions["sheet"]["sha256"]:
        fail(f"source sheet hash drifted: {sheet_path}")
    header, rows = load_sheet(sheet_path)
    expected_header = [
        "詞條",
        "英文解釋",
        "中文解釋",
        "阿美語例句",
        "英文例句",
        "中文例句",
        "參見",
    ]
    if header != expected_header:
        fail(f"unexpected source sheet header: {header!r}")
    if len(rows) != decisions["sheet"]["data_rows"]:
        fail(
            f"source sheet row count is {len(rows)}, expected {decisions['sheet']['data_rows']}"
        )
    complete = {
        index: row
        for index, row in rows.items()
        if len(row) >= 6 and all(row[column].strip() for column in (3, 4, 5))
    }
    if len(complete) != decisions["sheet"]["complete_example_rows"]:
        fail(
            f"complete example count is {len(complete)}, expected "
            f"{decisions['sheet']['complete_example_rows']}"
        )

    for relative, expected_hash in decisions["upstream"]["files"].items():
        path = code_docs / relative
        if sha256(path) != expected_hash:
            fail(f"upstream evidence hash drifted: {path}")
    return complete


def apply_form_decisions(
    root: etree._Element,
    decisions: dict,
    rows: dict[int, list[str]],
) -> dict[str, int]:
    by_id = {sentence.get("id"): sentence for sentence in root.iter("S")}
    row_by_id = {f"S{row}": row for row in rows}

    for decision in decisions["form_variants"]:
        row_number = decision["source_row"]
        variants = decision["variants"]
        if not variants or variants[0]["id"] != f"S{row_number}":
            fail(f"row {row_number}: first variant must retain S{row_number}")
        sheet_form = normalize(rows[row_number][3])
        if "sheet_defect" not in decision and sheet_form != normalize(
            decision["source_form"]
        ):
            fail(f"row {row_number}: source_decisions form does not match pinned sheet")

        base = by_id.get(f"S{row_number}")
        if base is None:
            fail(f"row {row_number}: baseline sentence S{row_number} is missing")
        insertion_parent = base.getparent()
        insertion_index = insertion_parent.index(base) + 1

        for position, variant in enumerate(variants):
            sentence_id = variant["id"]
            sentence = by_id.get(sentence_id)
            if sentence is None:
                sentence = copy.deepcopy(base)
                sentence.set("id", sentence_id)
                insertion_parent.insert(insertion_index, sentence)
                insertion_index += 1
                by_id[sentence_id] = sentence
            drop_derived_tiers(sentence)
            form = original_form(sentence)
            form.text = variant["form"]
            form.set("notes", decision["source_form"])
            row_by_id[sentence_id] = row_number

    for decision in decisions["single_form_decisions"]:
        row_number = decision["source_row"]
        if normalize(rows[row_number][3]) != normalize(decision["source_form"]):
            fail(
                f"row {row_number}: single-form source text does not match pinned sheet"
            )
        sentence = by_id.get(f"S{row_number}")
        if sentence is None:
            fail(f"row {row_number}: baseline sentence is missing")
        drop_derived_tiers(sentence)
        form = original_form(sentence)
        form.text = decision["form"]
        form.set("notes", decision["source_form"])

    all_ids = [sentence.get("id") for sentence in root.iter("S")]
    if len(all_ids) != len(set(all_ids)):
        fail("form reconciliation produced duplicate S ids")
    if set(all_ids) != set(row_by_id):
        missing = sorted(set(all_ids) - set(row_by_id))
        extra = sorted(set(row_by_id) - set(all_ids))
        fail(f"source-row map mismatch; unmapped={missing}, absent={extra}")
    return row_by_id


def apply_translation_repairs(root: etree._Element, decisions: dict) -> int:
    by_id = {sentence.get("id"): sentence for sentence in root.iter("S")}
    repaired = 0
    for repair in decisions["translation_repairs"]:
        sentence = by_id.get(repair["id"])
        if sentence is None:
            fail(f"translation repair target is missing: {repair['id']}")
        matches = [
            node
            for node in translation_nodes(sentence, repair["lang"])
            if normalize(node.text) == normalize(repair["old"])
        ]
        occurrence = repair.get("occurrence", 1)
        if len(matches) < occurrence:
            fail(
                f"{repair['id']} {repair['lang']}: expected occurrence {occurrence} "
                f"of {repair['old']!r}, found {len(matches)}"
            )
        matches[occurrence - 1].text = repair["new"]
        repaired += 1

    removed = 0
    for sentence in root.iter("S"):
        seen: set[tuple[str, str]] = set()
        for node in list(sentence.findall("TRANSL")):
            key = (node.get(XML_LANG, ""), normalize("".join(node.itertext())))
            if key in seen:
                sentence.remove(node)
                removed += 1
            else:
                seen.add(key)
        by_language: dict[str, list[etree._Element]] = defaultdict(list)
        for node in sentence.findall("TRANSL"):
            by_language[node.get(XML_LANG, "")].append(node)
        for nodes in by_language.values():
            if len(nodes) > 1:
                nodes[0].attrib.pop("ver", None)
                for node in nodes[1:]:
                    node.set("ver", "alt")

    expected_removed = decisions["expected_duplicate_translations_removed"]
    if removed != expected_removed:
        fail(f"removed {removed} duplicate translations, expected {expected_removed}")
    return repaired


def apply_structural_repairs(root: etree._Element, decisions: dict) -> int:
    by_id = {sentence.get("id"): sentence for sentence in root.iter("S")}
    repaired = 0
    for repair in decisions["structural_repairs"]:
        sentence = by_id.get(repair["id"])
        if sentence is None:
            fail(f"structural repair target is missing: {repair['id']}")
        matches = [
            child
            for child in sentence
            if normalize(child.tail) == normalize(repair["tail_text"])
        ]
        if len(matches) != 1:
            fail(
                f"{repair['id']}: expected one tail {repair['tail_text']!r}, "
                f"found {len(matches)}"
            )
        matches[0].tail = "\n        "
        repaired += 1
    return repaired


def preserve_source_translations(
    root: etree._Element,
    rows: dict[int, list[str]],
    row_by_id: dict[str, int],
) -> int:
    annotated = 0
    for sentence in root.iter("S"):
        row_number = row_by_id[sentence.get("id")]
        row = rows[row_number]
        for lang, column in (("eng", 4), ("zho", 5)):
            nodes = translation_nodes(sentence, lang)
            if not nodes:
                fail(f"{sentence.get('id')}: missing {lang} translation")
            source_text = row[column].strip()
            output = [normalize("".join(node.itertext())) for node in nodes]
            if output != [normalize(source_text)]:
                nodes[0].set("notes", source_text)
                annotated += 1
    return annotated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, help="XML file to reconcile")
    parser.add_argument(
        "--decisions",
        default=str(Path(__file__).with_name("source_decisions.json")),
        help="source decision JSON (default: sibling source_decisions.json)",
    )
    args = parser.parse_args()

    xml_path = Path(args.path).resolve()
    decisions_path = Path(args.decisions).resolve()
    code_docs = decisions_path.parent
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    rows = validate_inputs(code_docs, decisions)

    if sha256(xml_path) != decisions["baseline"]["sha256"]:
        fail("reconciliation input is not the pinned POL-035 baseline")
    tree = etree.parse(str(xml_path))
    root = tree.getroot()
    if len(list(root.iter("S"))) != decisions["baseline"]["sentence_count"]:
        fail("reconciliation input sentence count does not match the baseline")

    for attribute, value in decisions["header_updates"].items():
        root.set(attribute, value)
    row_by_id = apply_form_decisions(root, decisions, rows)
    structural = apply_structural_repairs(root, decisions)
    repaired = apply_translation_repairs(root, decisions)
    annotated = preserve_source_translations(root, rows, row_by_id)

    tree.write(
        str(xml_path),
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
    print(
        f"Reconciled {len(row_by_id)} S records from {len(rows)} source rows; "
        f"applied {structural} structural and {repaired} translation repairs, "
        f"and preserved "
        f"{annotated} transformed source translation fields in notes."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
