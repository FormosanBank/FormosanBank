#!/usr/bin/env python3
"""Restore source-located S records before applying the complete expert transcription."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

CODE = Path(__file__).resolve().parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")


def build(code: Path = CODE, output: Path | None = None) -> None:
    output = output or code.parent / "XML"
    metadata = json.loads((code / "source_data/text_metadata.json").read_text())
    manual = ET.parse(code / "manual_edits.xml").getroot()
    reviewed = {
        group.get("path"): [sentence.get("id") for sentence in group.findall("S")]
        for group in manual.findall("FILE")
    }
    trees = []
    for kind, info in metadata.items():
        path = info["file"]
        inventory = "extraction_report.csv" if kind == "examples" else "table_extraction_report.csv"
        with (code / inventory).open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        root = ET.Element("TEXT", info["text_attributes"])
        for row in rows:
            if row["status"] != "include":
                continue
            if kind == "examples":
                label = f"{int(row['example']):03d}{row['subexample'].upper()}"
                sid = f"AKIW_SZY_2012_EX_{label}"
                locator = f"example {int(row['example'])}{row['subexample']}"
                translation = row["translation_zho"]
            else:
                sid = f"AKIW_SZY_2012_TABLE_ROW_{int(row['seq']):03d}"
                locator = f"affix inventory row {int(row['seq'])}"
                translation = row["meaning_zho"]
            sentence = ET.SubElement(root, "S", {
                "id": sid, "source": f"PDF page {int(row['page'])}; {locator}",
            })
            ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = row["form"]
            ET.SubElement(sentence, "TRANSL", {XML_LANG: "zho"}).text = translation
        ids = [sentence.get("id") for sentence in root.findall("S")]
        if len(ids) != len(set(ids)) or ids != reviewed.get(path):
            raise ValueError(f"Source inventory and expert transcription disagree: {path}")
        trees.append((output / path, root))
    if set(reviewed) != {info["file"] for info in metadata.values()}:
        raise ValueError("Unaccounted expert transcription file")
    for path, root in trees:
        path.parent.mkdir(parents=True, exist_ok=True)
        ET.indent(root, space="    ")
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def expand_optional_23c() -> None:
    """Expand the parenthesized object on scan p. 55 after expert transcription."""
    metadata = json.loads((CODE / "source_data/text_metadata.json").read_text())
    path = CODE.parent / "XML" / metadata["examples"]["file"]
    tree = ET.parse(path)
    root = tree.getroot()
    sid = "AKIW_SZY_2012_EX_023C"
    sentence = root.find(f"S[@id='{sid}']")
    if sentence is None or root.find(f"S[@id='{sid}-opt']") is not None:
        raise ValueError("Expand 23c only from the fresh expert transcription")
    words = sentence.findall("W")
    if ([word.findtext("FORM[@kindOf='original']") for word in words]
            != ["ha-min", "han", "mu-kan", "kiya", "hemay"]
            or sentence.findtext("TRANSL") != "（飯）全部都吃掉。"):
        raise ValueError("Example 23c no longer matches its reviewed optional span")
    short = copy.deepcopy(sentence)
    for word in short.findall("W")[3:]:
        short.remove(word)
    for node in short.iter():
        if node.get("id"):
            node.set("id", node.get("id").replace(sid, sid + "-opt", 1))
    short.set("source", "PDF page 55; example 23c, without optional kiya hemay")
    short.find("FORM[@kindOf='original']").text = "ha-min han mu-kan."
    short.find("TRANSL").text = "全部都吃掉。"
    sentence.find("TRANSL").text = "飯全部都吃掉。"
    root.insert(list(root).index(sentence) + 1, short)
    ET.indent(root, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def add_supplemental_examples() -> None:
    """Recover scan-located footnote/prose examples after the expert transcription."""
    metadata = json.loads((CODE / "source_data/text_metadata.json").read_text())
    path = CODE.parent / "XML" / metadata["examples"]["file"]
    tree = ET.parse(path)
    root = tree.getroot()
    data = json.loads((CODE / "source_data/supplemental_examples.json").read_text())
    for row in data["sentences"]:
        if root.find(f"S[@id='{row['id']}']") is not None:
            raise ValueError(f"Supplement must run on fresh transcription: {row['id']}")
        anchor = root.find(f"S[@id='{row['after']}']")
        if anchor is None:
            raise ValueError(f"Missing source-order anchor: {row['after']}")
        sentence = ET.Element("S", {"id": row["id"], "source": row["source"]})
        ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = row["form"]
        ET.SubElement(sentence, "TRANSL", {XML_LANG: "zho"}).text = row["translation"]
        for wi, (form, gloss, morphs) in enumerate(row.get("words", []), 1):
            word = ET.SubElement(sentence, "W", {"id": f"{row['id']}W{wi}"})
            ET.SubElement(word, "FORM", {"kindOf": "original"}).text = form
            ET.SubElement(word, "TRANSL", {XML_LANG: "zho"}).text = gloss
            for mi, (mform, mgloss) in enumerate(morphs, 1):
                morph = ET.SubElement(word, "M", {"id": f"{row['id']}W{wi}M{mi}"})
                ET.SubElement(morph, "FORM", {"kindOf": "original"}).text = mform
                ET.SubElement(morph, "TRANSL", {XML_LANG: "zho"}).text = mgloss
        root.insert(list(root).index(anchor) + 1, sentence)
    for row in data["alternative_translations"]:
        sentence = root.find(f"S[@id='{row['id']}']")
        if sentence is None or sentence.findtext("FORM[@kindOf='original']") != row["form"]:
            raise ValueError(f"Alternative no longer matches its source sentence: {row['id']}")
        ET.SubElement(sentence, "TRANSL", {
            XML_LANG: "zho", "ver": "alt", "notes": row["source"],
        }).text = row["translation"]
    ET.indent(root, space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def record_provenance(formosanbank: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(formosanbank), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        print("No Git metadata: retain provenance.json and verify the export's tools revision separately.", file=sys.stderr)
        return
    record = {
        "_note": "Actual FormosanBank build tools; informational, never a build pin.",
        "formosanbank_commit": result.stdout.strip(),
    }
    (CODE / "provenance.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--record-provenance", type=Path)
    action.add_argument("--complete-transcription", action="store_true")
    args = parser.parse_args()
    if args.record_provenance:
        record_provenance(args.record_provenance)
    elif args.complete_transcription:
        expand_optional_23c()
        add_supplemental_examples()
    else:
        build()
