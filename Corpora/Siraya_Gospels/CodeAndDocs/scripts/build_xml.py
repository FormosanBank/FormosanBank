#!/usr/bin/env python3
"""Build reviewed Siraya Gospel XML from the public structured source data."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "verses.jsonl"
FINAL = ROOT.parent / "XML" / "Siraya"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


def published_text_id(path: str) -> str:
    book, chapter = Path(path).parts
    chapter_number = Path(chapter).stem.removeprefix("chapter")
    return f"Siraya_Dutch_{book}_Chapter{chapter_number}"


def main() -> None:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    with INTERMEDIATE.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            grouped[row["path"]].append(row)

    if FINAL.exists():
        shutil.rmtree(FINAL)
    for relative, rows in sorted(grouped.items()):
        attrs = dict(rows[0]["root_attributes"])
        attrs["id"] = published_text_id(relative)
        root = ET.Element("TEXT", attrs)
        for row in rows:
            sentence = ET.SubElement(root, "S", {"id": row["sentence_id"]})
            for field in row["fields"]:
                child_attrs: dict[str, str] = {}
                if field["kindOf"]:
                    child_attrs["kindOf"] = field["kindOf"]
                if field["xml_lang"]:
                    child_attrs[f"{{{XML_NS}}}lang"] = field["xml_lang"]
                child = ET.SubElement(sentence, field["tag"], child_attrs)
                child.text = field["text"]
        output = FINAL / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(root, space="    ")
        ET.ElementTree(root).write(output, encoding="UTF-8", xml_declaration=True)
    print(f"Built {len(grouped)} XML files in XML/Siraya")


if __name__ == "__main__":
    main()
