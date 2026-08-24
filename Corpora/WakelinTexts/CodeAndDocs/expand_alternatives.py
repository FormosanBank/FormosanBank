#!/usr/bin/env python3
"""Expand checked source alternatives into independently aligned sentences."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ledger", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def original_form(record: dict[str, Any]) -> str:
    forms = [form["text"] for form in record["forms"] if form["kind"] == "original"]
    if len(forms) != 1:
        raise ValueError("Expected exactly one original FORM")
    return forms[0]


def replace_form(record: dict[str, Any], text: str) -> None:
    record["forms"] = [{"text": text, "kind": "original"}]


def word_from_morpheme(
    source_words: list[dict[str, Any]], spec: dict[str, int]
) -> dict[str, Any]:
    source_word = source_words[spec["source_word"] - 1]
    source_morph = source_word["morphemes"][spec["source_morpheme"] - 1]
    return {
        "forms": copy.deepcopy(source_morph["forms"]),
        "translations": copy.deepcopy(source_morph.get("translations", [])),
    }


def select_words(
    source_words: list[dict[str, Any]], specs: list[int | dict[str, int]]
) -> list[dict[str, Any]]:
    selected = []
    for spec in specs:
        if isinstance(spec, int):
            selected.append(copy.deepcopy(source_words[spec - 1]))
        else:
            selected.append(word_from_morpheme(source_words, spec))
    return selected


def apply_word_edit(word: dict[str, Any], edit: dict[str, Any]) -> None:
    if "form" in edit:
        replace_form(word, edit["form"])
    if "translations" in edit:
        word["translations"] = copy.deepcopy(edit["translations"])

    if "morpheme_indices" in edit:
        source_morphemes = word.get("morphemes", [])
        indices = edit["morpheme_indices"]
        if indices:
            word["morphemes"] = [
                copy.deepcopy(source_morphemes[index - 1]) for index in indices
            ]
        else:
            word.pop("morphemes", None)

    morphemes = word.get("morphemes", [])
    for raw_index, text in edit.get("morpheme_forms", {}).items():
        replace_form(morphemes[int(raw_index) - 1], text)
    for raw_index, translations in edit.get("morpheme_translations", {}).items():
        morphemes[int(raw_index) - 1]["translations"] = copy.deepcopy(translations)


def build_variant(source_record: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(source_record)
    variant["id"] = spec["id"]
    variant["source_variant"] = spec["source_variant"]
    replace_form(variant, spec["form"])
    if "translations" in spec:
        variant["translations"] = copy.deepcopy(spec["translations"])

    source_words = source_record.get("words", [])
    word_specs = spec.get("word_specs", list(range(1, len(source_words) + 1)))
    variant["words"] = select_words(source_words, word_specs)
    for raw_index, edit in spec.get("word_edits", {}).items():
        apply_word_edit(variant["words"][int(raw_index) - 1], edit)
    return variant


def has_alternate_form(record: dict[str, Any]) -> bool:
    if any(form["kind"] == "alternate" for form in record.get("forms", [])):
        return True
    return any(
        has_alternate_form(child)
        for key in ("words", "morphemes")
        for child in record.get(key, []) or []
    )


def expand_ledger(
    source_ledger: dict[str, Any], decision_data: dict[str, Any]
) -> dict[str, Any]:
    if source_ledger.get("schema_version") != 1:
        raise ValueError("Unsupported source ledger schema")
    if decision_data.get("schema_version") != 1:
        raise ValueError("Unsupported alternative-decision schema")

    decisions = decision_data["expansions"]
    decision_by_key = {
        (decision["path"], decision["source_id"]): decision for decision in decisions
    }
    if len(decision_by_key) != len(decisions):
        raise ValueError("Duplicate alternative-expansion decision")

    source_slash_keys = {
        (text["path"], record["id"])
        for text in source_ledger["texts"]
        for record in text["sentences"]
        if "/" in original_form(record)
    }
    if source_slash_keys != set(decision_by_key):
        missing = sorted(source_slash_keys - set(decision_by_key))
        extra = sorted(set(decision_by_key) - source_slash_keys)
        raise ValueError(f"Alternative decisions differ from source: missing={missing}, extra={extra}")

    expanded = copy.deepcopy(source_ledger)
    for text in expanded["texts"]:
        emitted = []
        for source_record in text["sentences"]:
            key = (text["path"], source_record["id"])
            decision = decision_by_key.get(key)
            if decision is None:
                emitted.append(source_record)
                continue
            if original_form(source_record) != decision["source_form"]:
                raise ValueError(f"Source FORM drift for {key}")
            variants = decision["variants"]
            if len(variants) < 2 or variants[0]["id"] != source_record["id"]:
                raise ValueError(f"Invalid stable-ID variants for {key}")
            emitted.extend(build_variant(source_record, variant) for variant in variants)
        text["sentences"] = emitted

        ids = [record["id"] for record in emitted]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate emitted sentence ID in {text['path']}")

    all_records = [
        record for text in expanded["texts"] for record in text["sentences"]
    ]
    if len(decisions) != 18 or len(all_records) != 190:
        raise ValueError(
            f"Expected 18 decisions and 190 emitted sentences, found "
            f"{len(decisions)} and {len(all_records)}"
        )
    for record in all_records:
        if "/" in original_form(record):
            raise ValueError(f"Unexpanded sentence alternative: {record['id']}")
        if has_alternate_form(record):
            raise ValueError(f"Alternate FORM remains inside expanded sentence: {record['id']}")
    return expanded


def load_expanded_ledger(source_path: Path, decisions_path: Path) -> dict[str, Any]:
    source = json.loads(source_path.read_text(encoding="utf-8"))
    decisions = json.loads(decisions_path.read_text(encoding="utf-8"))
    return expand_ledger(source, decisions)


def main() -> int:
    args = parse_args()
    expanded = load_expanded_ledger(args.source_ledger, args.decisions)
    args.output.write_text(
        json.dumps(expanded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Expanded 171 source records into 190 aligned sentence variants: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
