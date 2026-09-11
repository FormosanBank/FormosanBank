#!/usr/bin/env python3
"""Generate final FormosanBank XML from the reviewed sentence table."""

from __future__ import annotations

import csv
import os
import tempfile
import xml.etree.ElementTree as ET
from collections import defaultdict

from corpus_config import (
    BIBTEX,
    CITATION,
    COPYRIGHT,
    FINAL_DIR,
    REVIEWED_CSV,
    SOURCE_ATTRIBUTE,
    TEXTS,
    final_path,
    sentence_id,
    source_locator,
)


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def load_reviewed_rows() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with REVIEWED_CSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["review_status"] != "reviewed":
                raise ValueError(
                    f"Unreviewed row: {row['text_key']} sequence {row['sequence']}"
                )
            if row["text_key"] not in TEXTS:
                raise ValueError(f"Unknown text_key: {row['text_key']}")
            grouped[row["text_key"]].append(row)

    for text_key, rows in grouped.items():
        rows.sort(key=lambda row: int(row["sequence"]))
        expected_sequence = list(range(1, len(rows) + 1))
        actual_sequence = [int(row["sequence"]) for row in rows]
        if actual_sequence != expected_sequence:
            raise ValueError(f"Non-contiguous sequence for {text_key}: {actual_sequence}")
        expected_count = int(TEXTS[text_key]["expected_count"])
        if len(rows) != expected_count:
            raise ValueError(
                f"Row count for {text_key} is {len(rows)}; expected {expected_count}"
            )
    return grouped


def build_tree(text_key: str, rows: list[dict[str, str]]) -> ET.ElementTree:
    config = TEXTS[text_key]
    root = ET.Element(
        "TEXT",
        {
            "id": config["text_id"],
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "copyright": COPYRIGHT,
            XML_LANG: "pzh",
            "source": SOURCE_ATTRIBUTE,
            "glottocode": "paze1234",
            "dialect": "unknown",
        },
    )

    for row in rows:
        sequence = int(row["sequence"])
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": sentence_id(text_key, sequence),
                "source": source_locator(row),
            },
        )
        form = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        form.text = row["form_original"]
        if row["translation_jpn"]:
            translation = ET.SubElement(sentence, "TRANSL", {XML_LANG: "jpn"})
            translation.text = row["translation_jpn"]

    ET.indent(root, space="  ")
    return ET.ElementTree(root)


def write_tree(tree: ET.ElementTree, destination) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", dir=destination.parent
    )
    os.close(file_descriptor)
    try:
        tree.write(
            temporary_name,
            encoding="UTF-8",
            xml_declaration=True,
            short_empty_elements=True,
        )
        with open(temporary_name, "ab") as handle:
            handle.write(b"\n")
        os.replace(temporary_name, destination)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def main() -> int:
    grouped = load_reviewed_rows()
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    expected_paths = {final_path(text_key) for text_key in TEXTS}
    for stale_path in FINAL_DIR.glob("*.xml"):
        if stale_path not in expected_paths:
            raise RuntimeError(f"Refusing to leave stale XML in XML/: {stale_path}")

    total = 0
    for text_key in TEXTS:
        rows = grouped[text_key]
        destination = final_path(text_key)
        write_tree(build_tree(text_key, rows), destination)
        total += len(rows)
        print(f"generated={destination} sentences={len(rows)}")
    print(f"total_sentences={total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
