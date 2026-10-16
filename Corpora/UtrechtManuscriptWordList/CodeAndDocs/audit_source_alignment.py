#!/usr/bin/env python3
"""Fail closed unless the canonical XML accounts for every pinned source row.

This is a check, not a build step: POL-047 keeps validators out of
`generate_xml.sh`, so it runs from `validate.sh`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from lxml import etree

from generate_xml import (
    XML_LANG,
    build_tree,
    form_decisions_by_row,
    load_inputs,
)


def audit_xml(path: Path, decisions: dict[str, Any], source: dict[str, Any],
              reconciliation: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.parse(str(path), parser).getroot()

    for name, expected in decisions["xml"]["attributes"].items():
        key = XML_LANG if name == "xml:lang" else name
        if root.get(key) != expected:
            findings.append(f"TEXT {name} differs from source_decisions.json")
    if len(root.attrib) != len(decisions["xml"]["attributes"]):
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
    if list(root.iter("PHON")):
        findings.append("canonical XML must not contain PHON tiers")
    if root.xpath('.//FORM[@kindOf="standard"]'):
        findings.append("canonical XML must not contain standard FORM tiers")

    # Every element the generator can emit must be reproducible from the inputs.
    expected_tree = build_tree(decisions, source, reconciliation)
    if etree.tostring(expected_tree.getroot()) != etree.tostring(root):
        findings.append("the published XML is not what the decisions produce")

    parsed = {row for row, item in form_decisions_by_row(decisions, source).items()
              if item.get("parse") is not None}
    with_word = {sentence.get("id") for sentence in sentences if sentence.findall("W")}
    reconciled = {record["source_row"]: record["output_id"]
                  for record in reconciliation["records"]}
    if with_word != {reconciled[row] for row in parsed}:
        findings.append("the W tier does not match the parsed form decisions")

    # No translation may repeat the form it translates -- the symptom of a
    # column landing in the wrong place, which happened at rows 223-233.
    for sentence in sentences:
        form = sentence.findtext('./FORM[@kindOf="original"]') or ""
        for node in sentence.findall("TRANSL"):
            if (node.text or "").strip() and (node.text or "").strip() == form.strip():
                findings.append(
                    f"{sentence.get('id')}: {node.get(XML_LANG)} translation repeats the form"
                )

    for sentence in sentences:
        for node in sentence.iter("FORM", "TRANSL"):
            if "[" in (node.text or "") or "]" in (node.text or ""):
                findings.append(f"{sentence.get('id')}: square brackets survive in published text")
    return findings


def parse_args() -> argparse.Namespace:
    code_docs = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-docs", type=Path, default=code_docs)
    parser.add_argument("--xml", type=Path,
                        default=code_docs.parent / "XML" / "Siraya" / "Utrecht_Manuscript.xml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions, source, reconciliation = load_inputs(args.code_docs)
    findings = audit_xml(args.xml, decisions, source, reconciliation)
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Source audit passed: {len(source['rows'])} rows accounted for.")


if __name__ == "__main__":
    main()
