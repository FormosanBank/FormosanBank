#!/usr/bin/env python3
"""Build the reviewed public Wakelin corpus from its checked ledgers."""

from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from expand_alternatives import load_expanded_ledger

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ledger", type=Path, required=True)
    parser.add_argument("--alternative-decisions", type=Path, required=True)
    parser.add_argument("--id-ledger", type=Path, required=True)
    parser.add_argument("--xml-dir", type=Path, required=True)
    return parser.parse_args()


OverrideKey = tuple[str, str, str, int, int | None]


def load_id_overrides(path: Path) -> dict[OverrideKey, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("collection") != "wakelin":
        raise ValueError("Unsupported public ID ledger")

    overrides: dict[OverrideKey, str] = {}
    public_ids: set[tuple[str, str]] = set()
    for item in data.get("node_id_overrides", []):
        node = item["node"]
        morpheme_number = item.get("morpheme_number")
        if node not in {"W", "M"} or (node == "W" and morpheme_number is not None):
            raise ValueError(f"Invalid public ID override: {item}")
        if node == "M" and morpheme_number is None:
            raise ValueError(f"Missing morpheme number in public ID override: {item}")
        key = (
            item["path"],
            item["sentence_id"],
            node,
            item["word_number"],
            morpheme_number,
        )
        if key in overrides:
            raise ValueError(f"Duplicate public ID override key: {key}")
        path_and_id = (item["path"], item["public_id"])
        if path_and_id in public_ids:
            raise ValueError(f"Duplicate overridden public ID: {path_and_id}")
        overrides[key] = item["public_id"]
        public_ids.add(path_and_id)
    return overrides


def resolve_node_id(
    overrides: dict[OverrideKey, str],
    relative: str,
    sentence_id: str,
    node: str,
    word_number: int,
    morpheme_number: int | None,
) -> tuple[str, OverrideKey]:
    key = (relative, sentence_id, node, word_number, morpheme_number)
    if node == "W":
        default = f"{sentence_id}W{word_number}"
    else:
        default = f"{sentence_id}W{word_number}M{morpheme_number}"
    return overrides.get(key, default), key


def add_tiers(parent: ET.Element, record: dict[str, Any]) -> None:
    forms = record.get("forms", [])
    if not forms or forms[0].get("kind") != "original":
        raise ValueError("Every source node must begin with original FORM")
    for form in forms:
        ET.SubElement(parent, "FORM", {"kindOf": form["kind"]}).text = form["text"]
    for transl in record.get("translations", []):
        attributes = {XML_LANG: transl["lang"]}
        if transl.get("ver"):
            attributes["ver"] = transl["ver"]
        ET.SubElement(parent, "TRANSL", attributes).text = transl["text"]


def add_children(
    parent: ET.Element,
    record: dict[str, Any],
    sentence_id: str,
    relative: str,
    overrides: dict[OverrideKey, str],
    used_overrides: set[OverrideKey],
) -> None:
    for word_number, word_record in enumerate(record.get("words", []), start=1):
        word_id, word_key = resolve_node_id(
            overrides, relative, sentence_id, "W", word_number, None
        )
        if word_key in overrides:
            used_overrides.add(word_key)
        word = ET.SubElement(parent, "W", {"id": word_id})
        add_tiers(word, word_record)
        for morph_number, morph_record in enumerate(
            word_record.get("morphemes", []), start=1
        ):
            morph_id, morph_key = resolve_node_id(
                overrides,
                relative,
                sentence_id,
                "M",
                word_number,
                morph_number,
            )
            if morph_key in overrides:
                used_overrides.add(morph_key)
            morph = ET.SubElement(word, "M", {"id": morph_id})
            add_tiers(morph, morph_record)


def build_text(
    text: dict[str, Any],
    overrides: dict[OverrideKey, str],
    used_overrides: set[OverrideKey],
) -> ET.Element:
    attributes = {
        "id": text["text_id"],
        XML_LANG: text["language"],
        "source": text["source"],
        "copyright": text["copyright"],
        "citation": text["citation"],
        "BibTeX_citation": text["bibtex"],
        "dialect": text["dialect"],
    }
    root = ET.Element("TEXT", attributes)
    for record in text["sentences"]:
        sentence_id = record["id"]
        sentence = ET.SubElement(root, "S", {"id": sentence_id})
        add_tiers(sentence, record)
        add_children(
            sentence,
            record,
            sentence_id,
            text["path"],
            overrides,
            used_overrides,
        )
    return root


def main() -> int:
    args = parse_args()
    data = load_expanded_ledger(args.source_ledger, args.alternative_decisions)
    overrides = load_id_overrides(args.id_ledger)
    used_overrides: set[OverrideKey] = set()
    target = args.xml_dir.resolve()
    if target.name != "XML":
        raise ValueError(f"Refusing to replace non-XML directory: {target}")
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    sentence_total = 0
    for text in data["texts"]:
        output = target / text["path"]
        output.parent.mkdir(parents=True, exist_ok=True)
        root = build_text(text, overrides, used_overrides)
        ET.indent(root, space="    ")
        ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
        sentence_total += len(text["sentences"])
    unused_overrides = set(overrides) - used_overrides
    if unused_overrides:
        raise ValueError(f"Unused public ID overrides: {sorted(unused_overrides)}")
    if sentence_total != 190:
        raise ValueError(f"Expected 190 sentence variants, found {sentence_total}")
    print(
        f"Built {len(data['texts'])} files and {sentence_total} aligned sentence "
        f"variants from 171 source records in {target}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
