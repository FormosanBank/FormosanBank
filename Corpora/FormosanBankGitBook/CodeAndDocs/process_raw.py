#!/usr/bin/env python3
"""Generate source-owned Paiwan GitBook XML tiers from the reviewed text ledger."""

from __future__ import annotations

import argparse
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

SOURCE_URLS = {
    "Welcome": "https://ai4commsci.gitbook.io/formosanbank",
    "FormosanBank": "https://ai4commsci.gitbook.io/formosanbank/background/formosanbank",
    "Formosan_Languages": "https://ai4commsci.gitbook.io/formosanbank/background/quickstart",
    "Contributors": "https://ai4commsci.gitbook.io/formosanbank/background/contributors",
    "Terms_of_Use": "https://ai4commsci.gitbook.io/formosanbank/additional-resources/terms-of-use",
    "Contributing_to_FormosanBank": (
        "https://ai4commsci.gitbook.io/formosanbank/additional-resources/"
        "contributing-to-formosanbank"
    ),
}
SOURCE_FILES = tuple(f"{stem}.txt" for stem in SOURCE_URLS)


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
            "source": SOURCE_URLS[stem],
            "copyright": "CC-BY-NC",
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "dialect": DIALECT,
        },
    )
    for index, record in enumerate(records):
        sentence = ET.SubElement(root, "S", {"id": str(index)})
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
    code_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-dir", type=Path, default=code_dir / "raw_data" / "Paiwan"
    )
    parser.add_argument(
        "--output", type=Path, default=code_dir / "Final_XML" / "Paiwan"
    )
    args = parser.parse_args()

    files, records = generate(args.source_dir.resolve(), args.output.resolve())
    print(f"Generated {files} XML files with {records} source records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
