#!/usr/bin/env python3
"""Build the three source-owned Paiwan story XML files and source ledger."""

from __future__ import annotations

import csv
import shutil
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "CodeAndDocs" / "data"
RECORDS = DATA_ROOT / "reviewed_records.tsv"
EXCLUSIONS = DATA_ROOT / "source_exclusions.tsv"
LEDGER = DATA_ROOT / "source_ledger.csv"
XML_ROOT = ROOT / "XML"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)

CITATION = (
    "Juan, T. F., and X. Ruan. 2024. Corpus of Paiwan Stories. "
    "Electronic resource."
)
BIBTEX = (
    "@electronic{ruan2024paiwan,author={Juan, T. F. and Ruan, X.},"
    "year={2024},title={Corpus of {Paiwan} Stories},"
    "type={Electronic Resource}}"
)
COPYRIGHT = "CC BY-NC"

STORIES = {
    "dingding": {
        "filename": "DingDing.xml",
        "text_id": "PaiwanStories_PS_dingding",
        "audio": "DingDing.wav",
        "source": (
            "Gesi Giling (2020), Dingding; complete Paiwan text on PDF pages "
            "2-30 and Chinese translation on PDF page 32; all 32 pages reviewed."
        ),
    },
    "kavatjes": {
        "filename": "kavatjes_ni_vuvu.xml",
        "text_id": "PaiwanStories_PS_kavatjes",
        "audio": "kavatjes_ni_vuvu.wav",
        "source": (
            "Gesi Giling (2020), Kavatjes ni vuvu; complete Paiwan text on "
            "PDF pages 2-30 and Chinese translation on PDF page 32; all 32 "
            "pages reviewed."
        ),
    },
    "maljialjian": {
        "filename": "maljialjian_a_qaciljay.xml",
        "text_id": "PaiwanStories_PS_maljialjian",
        "audio": "maljialjian_a_qaciljay.wav",
        "source": (
            "Complete bilingual Maljialjian a qaciljay Word source; both "
            "pages and all 16 table rows reviewed."
        ),
    },
}


def read_table(path: Path, delimiter: str = "\t") -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def rows() -> list[dict[str, str]]:
    records = read_table(RECORDS)
    expected_counts = {"dingding": 15, "kavatjes": 15, "maljialjian": 16}
    if Counter(row["story"] for row in records) != expected_counts:
        raise ValueError("reviewed-record story count drift")
    if len(records) != 46:
        raise ValueError("reviewed-record count drift")
    for story, count in expected_counts.items():
        members = [row for row in records if row["story"] == story]
        if [int(row["sequence"]) for row in members] != list(range(1, count + 1)):
            raise ValueError(f"non-contiguous sequence for {story}")
        if [row["s_id"] for row in members] != [f"S{i}" for i in range(1, count + 1)]:
            raise ValueError(f"sentence ID drift for {story}")
    if any(row["review_status"] != "visual_source_verified" for row in records):
        raise ValueError("nonterminal review row")
    if any(not row["original"] or not row["translation"] for row in records):
        raise ValueError("blank source tier")
    return records


def build(records: list[dict[str, str]]) -> dict[Path, ET.ElementTree]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in records:
        grouped[row["story"]].append(row)

    trees: dict[Path, ET.ElementTree] = {}
    for story, metadata in STORIES.items():
        root = ET.Element(
            "TEXT",
            {
                "id": metadata["text_id"],
                f"{{{XML_NS}}}lang": "pwn",
                "dialect": "Eastern",
                "citation": CITATION,
                "BibTeX_citation": BIBTEX,
                "copyright": COPYRIGHT,
                "source": metadata["source"],
                "audio": metadata["audio"],
            },
        )
        for row in grouped[story]:
            locator = (
                f"{row['source_filename']}: {row['original_locator']} "
                f"(Paiwan); {row['translation_locator']} (Chinese)"
            )
            sentence = ET.SubElement(root, "S", {"id": row["s_id"], "source": locator})
            form_attributes = {"kindOf": "original"}
            if not row["notes"].startswith("Paiwan and Chinese"):
                form_attributes["notes"] = row["notes"]
            ET.SubElement(sentence, "FORM", form_attributes).text = row["original"]
            ET.SubElement(
                sentence,
                "TRANSL",
                {f"{{{XML_NS}}}lang": "zho", "kindOf": "original"},
            ).text = row["translation"]

        path = XML_ROOT / "Paiwan" / metadata["filename"]
        trees[path] = ET.ElementTree(root)
    return trees


def write_trees(trees: dict[Path, ET.ElementTree]) -> None:
    if XML_ROOT.exists():
        shutil.rmtree(XML_ROOT)
    for path, tree in trees.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(tree.getroot(), space="  ")
        tree.write(path, encoding="UTF-8", xml_declaration=True)
        with path.open("ab") as handle:
            handle.write(b"\n")


def write_ledger(records: list[dict[str, str]]) -> None:
    fields = [
        "source_locator",
        "source_item",
        "target_text",
        "translation_or_gloss",
        "included_in_xml",
        "exclusion_reason",
        "final_xml_path",
        "final_s_id",
    ]
    ledger_rows = []
    for row in records:
        filename = STORIES[row["story"]]["filename"]
        ledger_rows.append(
            {
                "source_locator": (
                    f"{row['source_filename']}: {row['original_locator']} (Paiwan); "
                    f"{row['translation_locator']} (Chinese)"
                ),
                "source_item": f"{row['story']} row {row['sequence']}",
                "target_text": row["original"],
                "translation_or_gloss": row["translation"],
                "included_in_xml": "yes",
                "exclusion_reason": "",
                "final_xml_path": f"XML/Paiwan/{filename}",
                "final_s_id": row["s_id"],
            }
        )
    for row in read_table(EXCLUSIONS):
        ledger_rows.append(
            {
                "source_locator": f"{row['source_filename']}: {row['locator']}",
                "source_item": "source exclusion",
                "target_text": "",
                "translation_or_gloss": "",
                "included_in_xml": "no",
                "exclusion_reason": row["reason"],
                "final_xml_path": "",
                "final_s_id": "",
            }
        )
    with LEDGER.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(ledger_rows)


def main() -> None:
    records = rows()
    write_trees(build(records))
    write_ledger(records)
    print("Built 3 XML files: 46 records and 4 explicit source exclusions")


if __name__ == "__main__":
    main()
