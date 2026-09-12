#!/usr/bin/env python3
"""Generate source tiers from the reviewed bilingual transcription."""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")


def read_table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def rows(path: Path = HERE / "data/reviewed_records.tsv") -> list[dict[str, str]]:
    records = read_table(path)
    seen = set()
    for row in records:
        key = row["story"], row["s_id"]
        if key in seen:
            raise ValueError(f"duplicate source ID: {key}")
        seen.add(key)
        if row["legacy_id"] and row["legacy_id"] != row["s_id"]:
            raise ValueError(f"published ID changed: {key}")
        if not row["original"].strip() or not row["translation"].strip():
            raise ValueError(f"empty bilingual source unit: {key}")
    if not records:
        raise ValueError("empty source transcription")
    return records


def build(records: list[dict[str, str]]) -> dict[str, ET.ElementTree]:
    metadata = read_table(HERE / "data/texts.tsv")
    if {row["story"] for row in records} != {row["story"] for row in metadata}:
        raise ValueError("story metadata does not match the transcription")
    trees = {}
    for text in metadata:
        root = ET.Element("TEXT", {
            "id": text["text_id"], XML_LANG: text["language"],
            "dialect": text["dialect"], "citation": text["citation"],
            "BibTeX_citation": text["BibTeX_citation"],
            "copyright": text["copyright"], "source": text["source"],
            "audio": text["audio"],
        })
        members = sorted(
            (row for row in records if row["story"] == text["story"]),
            key=lambda row: int(row["sequence"]),
        )
        if len({row["sequence"] for row in members}) != len(members):
            raise ValueError(f"duplicate source order: {text['story']}")
        for row in members:
            locator = (
                f"{row['source_filename']}: {row['original_locator']} (Paiwan); "
                f"{row['translation_locator']} (Chinese)"
            )
            sentence = ET.SubElement(root, "S", {"id": row["s_id"], "source": locator})
            ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = row["original"]
            ET.SubElement(sentence, "TRANSL", {XML_LANG: "zho"}).text = row["translation"]
        trees[text["filename"]] = ET.ElementTree(root)
    return trees


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    destination = args.output_dir / "Paiwan"
    destination.mkdir(parents=True, exist_ok=True)
    records = rows()
    for filename, tree in build(records).items():
        ET.indent(tree, space="  ")
        path = destination / filename
        tree.write(path, encoding="UTF-8", xml_declaration=True)
        with path.open("ab") as handle:
            handle.write(b"\n")
    print(f"Generated {len(records)} bilingual source units.")


if __name__ == "__main__":
    main()
