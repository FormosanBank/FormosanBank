#!/usr/bin/env python3
"""Fail-closed source coverage audit for the Virginia Fey corpus."""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

from lxml import etree

from reconcile_source import XML_LANG, normalize, validate_inputs


def english_tokens(text: str | None) -> set[str]:
    return set(
        re.findall(
            r"[A-Za-z]+(?:['’-][A-Za-z]+)*",
            unicodedata.normalize("NFC", text or "").lower(),
        )
    )


def han_characters(text: str | None) -> set[str]:
    return {
        character
        for character in unicodedata.normalize("NFC", text or "")
        if "\u3400" <= character <= "\u9fff"
    }


def tier_text(node: etree._Element) -> str:
    return "".join(node.itertext())


def original_form(sentence: etree._Element) -> etree._Element:
    forms = sentence.xpath('./FORM[@kindOf="original"]')
    if len(forms) != 1:
        raise ValueError(
            f"{sentence.get('id')}: expected one original FORM, found {len(forms)}"
        )
    return forms[0]


def build_expected(
    decisions: dict, rows: dict[int, list[str]]
) -> tuple[dict[str, int], dict[str, str], dict[str, str]]:
    row_by_id = {f"S{row}": row for row in rows}
    form_by_id = {f"S{row}": rows[row][3].strip() for row in rows}
    form_note_by_id: dict[str, str] = {}

    for decision in decisions["form_variants"]:
        row = decision["source_row"]
        for variant in decision["variants"]:
            sentence_id = variant["id"]
            if sentence_id in row_by_id and sentence_id != f"S{row}":
                raise ValueError(
                    f"variant id collides with a source row: {sentence_id}"
                )
            row_by_id[sentence_id] = row
            form_by_id[sentence_id] = variant["form"]
            form_note_by_id[sentence_id] = decision["source_form"]

    for decision in decisions["single_form_decisions"]:
        sentence_id = f"S{decision['source_row']}"
        form_by_id[sentence_id] = decision["form"]
        form_note_by_id[sentence_id] = decision["source_form"]
    return row_by_id, form_by_id, form_note_by_id


def translation_exceptions(decisions: dict) -> dict[tuple[int, str], set[str]]:
    result: dict[tuple[int, str], set[str]] = defaultdict(set)
    for item in decisions["translation_token_exceptions"]:
        result[(item["source_row"], item["lang"])].update(item["tokens"])
    return result


def validate_translation_shape(
    sentence: etree._Element,
    source_rows: list[int],
    rows: dict[int, list[str]],
    exceptions: dict[tuple[int, str], set[str]],
    findings: list[str],
) -> None:
    sentence_id = sentence.get("id")
    by_language: dict[str, list[etree._Element]] = defaultdict(list)
    for translation in sentence.findall("TRANSL"):
        language = translation.get(XML_LANG, "")
        by_language[language].append(translation)
        text = tier_text(translation)
        if text.count("(") != text.count(")") or text.count("（") != text.count("）"):
            findings.append(
                f"{sentence_id}: unbalanced translation parentheses: {text!r}"
            )

    if set(by_language) != {"eng", "zho"}:
        findings.append(
            f"{sentence_id}: expected eng and zho translations, found {sorted(by_language)}"
        )
        return

    for language, nodes in by_language.items():
        keys = [normalize(tier_text(node)) for node in nodes]
        if len(keys) != len(set(keys)):
            findings.append(f"{sentence_id}: duplicate {language} translation text")
        if len(nodes) > 1:
            if nodes[0].get("ver") is not None:
                findings.append(f"{sentence_id}: first {language} translation has ver")
            for node in nodes[1:]:
                if node.get("ver") != "alt":
                    findings.append(
                        f"{sentence_id}: later {language} translation lacks ver=alt"
                    )

        column = 4 if language == "eng" else 5
        source_texts = [rows[row][column].strip() for row in source_rows]
        output_norms = {normalize(tier_text(node)) for node in nodes}
        note_norms = {
            normalize(node.get("notes")) for node in nodes if node.get("notes")
        }
        for source_text in source_texts:
            source_norm = normalize(source_text)
            if source_norm not in output_norms and source_norm not in note_norms:
                findings.append(
                    f"{sentence_id}: {language} source row text is neither an output nor a note: "
                    f"{source_text!r}"
                )

        output_text = " ".join(tier_text(node) for node in nodes)
        source_text = " ".join(source_texts)
        allowed = set().union(
            *(exceptions.get((row, language), set()) for row in source_rows)
        )
        if language == "eng":
            unexpected = (
                english_tokens(output_text)
                - english_tokens(source_text)
                - {token.lower() for token in allowed}
            )
        else:
            unexpected = (
                han_characters(output_text) - han_characters(source_text) - allowed
            )
        if unexpected:
            findings.append(
                f"{sentence_id}: unreviewed {language} output additions: {sorted(unexpected)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", required=True, help="XML file to audit")
    parser.add_argument("--stage", choices=("pre-dedup", "canonical"), required=True)
    parser.add_argument(
        "--decisions",
        default=str(Path(__file__).with_name("source_decisions.json")),
    )
    parser.add_argument("--json", help="optional JSON summary output")
    args = parser.parse_args()

    decisions_path = Path(args.decisions).resolve()
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    rows = validate_inputs(decisions_path.parent, decisions)
    row_by_id, form_by_id, form_note_by_id = build_expected(decisions, rows)
    exceptions = translation_exceptions(decisions)

    tree = etree.parse(str(Path(args.path).resolve()))
    root = tree.getroot()
    findings: list[str] = []
    if root.get("{http://www.w3.org/XML/1998/namespace}lang") != "ami":
        findings.append("TEXT xml:lang is not ami")
    if root.get("dialect") != decisions["dialect"]["xml_value"]:
        findings.append("TEXT dialect does not match the confirmed decision")
    for attribute, expected in decisions["header_updates"].items():
        if root.get(attribute) != expected:
            findings.append(f"TEXT {attribute} does not match source_decisions.json")

    sentences = list(root.iter("S"))
    by_id = {sentence.get("id"): sentence for sentence in sentences}
    if len(by_id) != len(sentences):
        findings.append("duplicate S ids remain")

    expected_ids = set(row_by_id)
    dedup_map = {
        item["removed"]: item["survivor"]
        for item in decisions["expected_deduplications"]
    }
    if args.stage == "pre-dedup":
        wanted_ids = expected_ids
    else:
        wanted_ids = expected_ids - set(dedup_map)
    if set(by_id) != wanted_ids:
        findings.append(
            "S inventory mismatch: "
            f"missing={sorted(wanted_ids - set(by_id))}, "
            f"extra={sorted(set(by_id) - wanted_ids)}"
        )

    for removed, survivor in dedup_map.items():
        if args.stage == "pre-dedup":
            if removed not in by_id or survivor not in by_id:
                findings.append(
                    f"dedup pair absent before dedup: {removed} -> {survivor}"
                )
            elif normalize(
                by_id[removed].findtext('./FORM[@kindOf="standard"]')
            ) != normalize(by_id[survivor].findtext('./FORM[@kindOf="standard"]')):
                findings.append(f"declared dedup forms differ: {removed} -> {survivor}")
        elif removed in by_id or survivor not in by_id:
            findings.append(f"canonical dedup state is wrong: {removed} -> {survivor}")

    rows_by_actual_id: dict[str, list[int]] = defaultdict(list)
    for sentence_id, row in row_by_id.items():
        actual_id = (
            dedup_map.get(sentence_id, sentence_id)
            if args.stage == "canonical"
            else sentence_id
        )
        rows_by_actual_id[actual_id].append(row)

    for sentence_id, sentence in by_id.items():
        source_rows = sorted(set(rows_by_actual_id[sentence_id]))
        if sentence.text and sentence.text.strip():
            findings.append(
                f"{sentence_id}: stray S character content {sentence.text!r}"
            )
        for child in sentence:
            if child.tail and child.tail.strip():
                findings.append(
                    f"{sentence_id}: stray character content after {child.tag}: "
                    f"{child.tail.strip()!r}"
                )
        try:
            form = original_form(sentence)
        except ValueError as error:
            findings.append(str(error))
            continue
        if args.stage == "pre-dedup":
            expected_form = form_by_id[sentence_id]
            if normalize(tier_text(form)) != normalize(expected_form):
                findings.append(
                    f"{sentence_id}: original FORM differs: "
                    f"{tier_text(form)!r} != {expected_form!r}"
                )
            expected_note = form_note_by_id.get(sentence_id)
            if expected_note is not None and form.get("notes") != expected_note:
                findings.append(
                    f"{sentence_id}: source FORM note is missing or changed"
                )
        if "/" in tier_text(form):
            findings.append(f"{sentence_id}: unresolved slash remains in original FORM")
        validate_translation_shape(sentence, source_rows, rows, exceptions, findings)

    standard_forms = [
        normalize(sentence.findtext('./FORM[@kindOf="standard"]'))
        for sentence in sentences
    ]
    if args.stage == "canonical" and len(standard_forms) != len(set(standard_forms)):
        findings.append(
            "canonical reference resource still has duplicate standard FORMs"
        )

    summary = {
        "stage": args.stage,
        "source_rows": len(rows),
        "expected_source_units": len(expected_ids),
        "sentences": len(sentences),
        "deduplications": len(dedup_map) if args.stage == "canonical" else 0,
        "findings": findings,
    }
    if args.json:
        Path(args.json).write_text(
            json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if findings:
        for finding in findings:
            print(f"FAIL: {finding}")
        print(f"Source alignment failed with {len(findings)} finding(s).")
        return 1
    print(
        f"Source alignment passed ({args.stage}): {len(rows)} source rows, "
        f"{len(expected_ids)} source units, {len(sentences)} S records."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
