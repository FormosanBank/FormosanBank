#!/usr/bin/env python3
"""Build the reviewed public Montgomery corpus from its source ledger."""

from __future__ import annotations

import argparse
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ledger", type=Path, required=True)
    parser.add_argument("--xml-dir", type=Path, required=True)
    return parser.parse_args()


def add_tiers(parent: ET.Element, record: dict[str, Any]) -> None:
    forms = record.get("forms", [])
    if not forms or forms[0].get("kind") != "original":
        raise ValueError("Every source node must begin with original FORM")
    for form in forms:
        ET.SubElement(parent, "FORM", {"kindOf": form["kind"]}).text = form["text"]
    for translation in record.get("translations", []):
        attributes = {XML_LANG: translation["lang"]}
        if translation.get("ver"):
            attributes["ver"] = translation["ver"]
        ET.SubElement(parent, "TRANSL", attributes).text = translation["text"]


def add_words(parent: ET.Element, record: dict[str, Any], sentence_id: str) -> None:
    for number, word_record in enumerate(record.get("words", []), start=1):
        word_id = f"{sentence_id}W{number}"
        word = ET.SubElement(parent, "W", {"id": word_id})
        add_tiers(word, word_record)
        for morph_number, morph_record in enumerate(
            word_record.get("morphemes", []), start=1
        ):
            morph = ET.SubElement(word, "M", {"id": f"{word_id}M{morph_number}"})
            add_tiers(morph, morph_record)


def build_text(text: dict[str, Any]) -> ET.Element:
    root = ET.Element(
        "TEXT",
        {
            "id": text["text_id"],
            XML_LANG: text["language"],
            "source": text["source"],
            "copyright": text["copyright"],
            "citation": text["citation"],
            "BibTeX_citation": text["bibtex"],
            "dialect": text["dialect"],
        },
    )
    offset = text["public_sentence_id_offset"]
    for source_number, record in enumerate(text["sentences"], start=1):
        source_id = f"S{source_number}"
        if record["id"] != source_id or record["source_number"] != source_number:
            raise ValueError(f"Non-contiguous source record in {text['path']}")
        sentence_id = f"S{source_number + offset}"
        sentence = ET.SubElement(root, "S", {"id": sentence_id})
        add_tiers(sentence, record)
        add_words(sentence, record, sentence_id)
    return root


def main() -> int:
    args = parse_args()
    data = json.loads(args.source_ledger.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported source ledger schema")

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
        root = build_text(text)
        ET.indent(root, space="    ")
        ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)
        sentence_total += len(text["sentences"])

    file_total = len(data["texts"])
    if file_total != data["expected_file_count"]:
        raise ValueError(f"Expected {data['expected_file_count']} files, found {file_total}")
    if sentence_total != data["expected_sentence_count"]:
        raise ValueError(
            f"Expected {data['expected_sentence_count']} sentences, found {sentence_total}"
        )
    print(f"Built {file_total} files and {sentence_total} sentences in {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
