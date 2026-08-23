#!/usr/bin/env python3
"""Fail closed unless the canonical XML accounts for every pinned source row."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lxml import etree

from generate_xml import (
    XML_LANG,
    expected_translation_nodes,
    form_decisions_by_row,
    load_inputs,
    translation_decisions_by_key,
)


def audit_xml(
    path: Path,
    decisions: dict[str, Any],
    source: dict[str, Any],
    reconciliation: dict[str, Any],
) -> list[str]:
    findings: list[str] = []
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    tree = etree.parse(str(path), parser)
    root = tree.getroot()

    for name, expected in decisions["xml"]["attributes"].items():
        key = XML_LANG if name == "xml:lang" else name
        if root.get(key) != expected:
            findings.append(f"TEXT {name} differs from source_decisions.json")
    expected_attribute_count = len(decisions["xml"]["attributes"])
    if len(root.attrib) != expected_attribute_count:
        findings.append("TEXT has unreviewed metadata attributes")

    sentences = root.findall("S")
    expected_ids = [record["output_id"] for record in reconciliation["records"]]
    actual_ids = [sentence.get("id") for sentence in sentences]
    if actual_ids != expected_ids:
        findings.append("S inventory or order differs from source reconciliation")
    if len(actual_ids) != len(set(actual_ids)):
        findings.append("duplicate S ids remain")
    if root.findall("W") or root.findall("M"):
        findings.append("TEXT contains direct W or M records")
    if list(root.iter("W")) or list(root.iter("M")):
        findings.append("canonical XML must not contain W or M tiers")
    if list(root.iter("PHON")):
        findings.append("canonical XML must not contain PHON tiers")
    if root.xpath('.//FORM[@kindOf="standard"]'):
        findings.append("canonical XML must not contain standard FORM tiers")

    decisions_by_row = form_decisions_by_row(decisions, source)
    translation_decisions = translation_decisions_by_key(decisions, source)
    actual_repeats: dict[str, list[int]] = {}
    rows_by_form: dict[str, list[int]] = {}
    for row, sentence in zip(source["rows"], sentences):
        source_row = row["source_row"]
        forms = sentence.xpath('./FORM[@kindOf="original"]')
        if len(forms) != 1:
            findings.append(
                f"source row {source_row}: expected one original FORM, found {len(forms)}"
            )
            continue
        form = forms[0]
        form_decision = decisions_by_row.get(source_row)
        expected_form = (
            form_decision["output_form"]
            if form_decision is not None
            else row["um_formosana"]
        )
        expected_notes = form_decision["notes"] if form_decision is not None else None
        if "".join(form.itertext()) != expected_form:
            findings.append(f"source row {source_row}: original FORM differs")
        if form.get("notes") != expected_notes:
            findings.append(f"source row {source_row}: FORM notes differ")
        if len(sentence.findall("FORM")) != 1:
            findings.append(f"source row {source_row}: unexpected additional FORM")
        rows_by_form.setdefault(expected_form, []).append(source_row)

        expected_translations = [
            (
                item["xml_lang"],
                item["text"],
                item.get("notes"),
                item.get("ver"),
            )
            for item in expected_translation_nodes(
                row, decisions, translation_decisions
            )
        ]
        actual_translations = [
            (
                node.get(XML_LANG),
                "".join(node.itertext()),
                node.get("notes"),
                node.get("ver"),
            )
            for node in sentence.findall("TRANSL")
        ]
        if actual_translations != expected_translations:
            findings.append(f"source row {source_row}: translation fields differ")
        allowed_children = {"FORM", "TRANSL"}
        unexpected = [child.tag for child in sentence if child.tag not in allowed_children]
        if unexpected:
            findings.append(
                f"source row {source_row}: unexpected child tiers {unexpected}"
            )

    actual_repeats = {
        form: row_numbers
        for form, row_numbers in rows_by_form.items()
        if len(row_numbers) > 1
    }
    expected_repeats = {
        item["form"]: item["source_rows"]
        for item in decisions["repeat_policy"]["retained_form_groups"]
    }
    if actual_repeats != expected_repeats:
        findings.append("repeated FORM inventory differs from the POL-022 decision")

    if len(sentences) != len(source["rows"]):
        findings.append(
            f"expected {len(source['rows'])} S records, found {len(sentences)}"
        )
    return findings


def parse_args() -> argparse.Namespace:
    code_docs = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-docs", type=Path, default=code_docs)
    parser.add_argument(
        "--path",
        type=Path,
        default=code_docs.parent / "XML" / "Siraya" / "Utrecht_Manuscript.xml",
    )
    parser.add_argument("--json", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    decisions, source, reconciliation = load_inputs(args.code_docs)
    findings = audit_xml(args.path, decisions, source, reconciliation)
    summary = {
        "source_rows": len(source["rows"]),
        "sentences": len(etree.parse(str(args.path)).findall("S")),
        "retained_predecessor_entries": reconciliation["counts"][
            "retained_predecessor_entries"
        ],
        "retired_predecessor_entries": reconciliation["counts"][
            "retired_predecessor_entries"
        ],
        "new_source_rows": reconciliation["counts"]["new_source"],
        "findings": findings,
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        print(f"Source alignment failed with {len(findings)} finding(s).")
        return 1
    print(
        "Source alignment passed: "
        f"{summary['source_rows']} source rows, {summary['sentences']} S records, "
        f"{summary['retired_predecessor_entries']} retired predecessor artifacts."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
