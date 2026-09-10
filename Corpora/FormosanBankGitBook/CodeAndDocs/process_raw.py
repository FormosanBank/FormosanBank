#!/usr/bin/env python3
"""Generate source-owned Paiwan GitBook XML tiers from the reviewed text ledger."""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
LANGUAGE = "Paiwan"
LANGUAGE_CODE = "pwn"
DIALECT = "Eastern"
CITATION = "Ruan, X. (2025). Paiwan translation of FormosanBank manual."
BIBTEX = (
    "@misc{gitbook_paiwan_transl, author={Ruan, X.}, "
    "title={Paiwan Translation of FormosanBank Manual}, year={2025}, "
    "note={Translation}}"
)

CODE = Path(__file__).resolve().parent


def read_table(name: str) -> list[dict[str, str]]:
    with (CODE / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


SECTIONS = {row["section"]: row for row in read_table("source_sections.tsv")}
SOURCE_FILES = tuple(f"{stem}.txt" for stem in SECTIONS)


def record_keys(stem: str, count: int) -> list[dict[str, str]]:
    rows = [row for row in read_table("source_records.tsv") if row["section"] == stem]
    if [int(row["record"]) for row in rows] != list(range(count)):
        raise ValueError(f"{stem}: source records do not match the stable ID table")
    if len({row["s_id"] for row in rows}) != count:
        raise ValueError(f"{stem}: duplicate source IDs")
    return rows


@dataclass(frozen=True)
class SourceRecord:
    english: str
    chinese: str
    paiwan: str


def parse_source(path: Path) -> list[SourceRecord]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError(f"empty source file: {path}")

    records: list[SourceRecord] = []
    for index, block in enumerate(text.split("\n\n")):
        fields = block.splitlines()
        if len(fields) != 3 or any(not field.strip() for field in fields):
            raise ValueError(
                f"{path}: block {index} must contain exactly three non-empty lines"
            )
        records.append(SourceRecord(*(field.strip() for field in fields)))
    return records


def source_inventory(source_dir: Path) -> dict[str, list[SourceRecord]]:
    actual = {path.name for path in source_dir.glob("*.txt")}
    expected = set(SOURCE_FILES)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        raise ValueError(f"source inventory mismatch: missing={missing}, unexpected={unexpected}")
    return {Path(name).stem: parse_source(source_dir / name) for name in SOURCE_FILES}


def build_tree(stem: str, records: list[SourceRecord]) -> ET.ElementTree:
    root = ET.Element(
        "TEXT",
        {
            "id": f"gitbook_{LANGUAGE}_{stem}",
            XML_LANG: LANGUAGE_CODE,
            "source": "translation of FormosanBank gitbook in Paiwan",
            "copyright": "CC BY-NC 4.0",
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "dialect": DIALECT,
        },
    )
    for key, record in zip(record_keys(stem, len(records)), records, strict=True):
        sentence = ET.SubElement(root, "S", {"id": key["s_id"]})
        ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = record.paiwan
        ET.SubElement(sentence, "TRANSL", {XML_LANG: "zho"}).text = record.chinese
        ET.SubElement(sentence, "TRANSL", {XML_LANG: "eng"}).text = record.english
    ET.indent(root, space="  ")
    return ET.ElementTree(root)


def write_tree(tree: ET.ElementTree, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_path, encoding="utf-8", xml_declaration=True, short_empty_elements=True)
    with output_path.open("ab") as handle:
        handle.write(b"\n")


def generate(source_dir: Path, output_dir: Path) -> tuple[int, int]:
    inventory = source_inventory(source_dir)
    expected_outputs = {f"{stem}.xml" for stem in inventory}
    unexpected_outputs = {
        path.name for path in output_dir.glob("*.xml") if path.name not in expected_outputs
    }
    if unexpected_outputs:
        raise ValueError(f"unexpected XML outputs: {sorted(unexpected_outputs)}")

    total = 0
    for stem, records in inventory.items():
        write_tree(build_tree(stem, records), output_dir / f"{stem}.xml")
        total += len(records)
    return len(inventory), total


def main() -> int:
    repo = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, default=repo / "raw_data" / "Paiwan")
    parser.add_argument("--output", type=Path, default=repo.parent / "XML" / "Paiwan")
    args = parser.parse_args()

    files, records = generate(args.source_dir.resolve(), args.output.resolve())
    print(f"Generated {files} XML files with {records} source records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
