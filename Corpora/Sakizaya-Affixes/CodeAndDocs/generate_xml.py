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


def expand_optional_23c(xml_root: Path) -> None:
    """Expand the parenthesized object on scan p. 55 after expert transcription."""
    metadata = json.loads((CODE / "source_data/text_metadata.json").read_text())
    path = xml_root / metadata["examples"]["file"]
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


def add_supplemental_examples(xml_root: Path) -> None:
    """Recover scan-located footnote/prose examples after the expert transcription."""
    metadata = json.loads((CODE / "source_data/text_metadata.json").read_text())
    path = xml_root / metadata["examples"]["file"]
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


def _xml_paths(xml_root: Path) -> dict[str, Path]:
    metadata = json.loads((CODE / "source_data/text_metadata.json").read_text())
    return {kind: xml_root / info["file"] for kind, info in metadata.items()}


def _write(tree: ET.ElementTree, path: Path) -> None:
    ET.indent(tree.getroot(), space="    ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def _transl(parent: ET.Element, readings: list[str]) -> None:
    """A primary translation plus ver="alt" readings, the expert transcription's shape."""
    for index, text in enumerate(readings):
        attributes = {XML_LANG: "zho"} if index == 0 else {XML_LANG: "zho", "ver": "alt"}
        ET.SubElement(parent, "TRANSL", attributes).text = text


def add_ruled_records(xml_root: Path) -> None:
    """Add the records the maintainer ruled in (source_data/ruled_additions.json).

    Each example must still be in extraction_report.csv with the same form and status
    include_ruled; each table row must still be in late_table_rows.csv with the same form
    and meaning. Anything else stops the build rather than adding a stale record.
    """
    data = json.loads((CODE / "source_data/ruled_additions.json").read_text(encoding="utf-8"))
    paths = _xml_paths(xml_root)
    with (CODE / "extraction_report.csv").open(encoding="utf-8-sig", newline="") as handle:
        inventory = {f"AKIW_SZY_2012_EX_{int(r['example']):03d}{r['subexample'].upper()}": r
                     for r in csv.DictReader(handle)}
    tree = ET.parse(paths["examples"])
    root = tree.getroot()
    for row in data["examples"]:
        source = inventory.get(row["id"])
        if source is None or source["form"] != row["form"] or source["status"] != "include_ruled":
            raise ValueError(f"Ruled example no longer matches extraction_report.csv: {row['id']}")
        if root.find(f"S[@id='{row['id']}']") is not None:
            raise ValueError(f"Ruled example already present: {row['id']}")
        anchor = root.find(f"S[@id='{row['after']}']")
        if anchor is None:
            raise ValueError(f"Missing source-order anchor: {row['after']}")
        sentence = ET.Element("S", {"id": row["id"], "source": row["source"]})
        ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = row["form"]
        _transl(sentence, [row["translation"]])
        for wi, (form, gloss, morphs) in enumerate(row["words"], 1):
            word = ET.SubElement(sentence, "W", {"id": f"{row['id']}W{wi}"})
            ET.SubElement(word, "FORM", {"kindOf": "original"}).text = form
            _transl(word, [gloss])
            for mi, (mform, mgloss) in enumerate(morphs, 1):
                morph = ET.SubElement(word, "M", {"id": f"{row['id']}W{wi}M{mi}"})
                ET.SubElement(morph, "FORM", {"kindOf": "original"}).text = mform
                _transl(morph, [mgloss])
        root.insert(list(root).index(anchor) + 1, sentence)
    _write(tree, paths["examples"])

    with (CODE / "source_data/late_table_rows.csv").open(encoding="utf-8-sig", newline="") as handle:
        late = {r["seq"]: r for r in csv.DictReader(handle)}
    tree = ET.parse(paths["table_rows"])
    root = tree.getroot()
    for row in data["table_rows"]:
        source = late.get(str(row["seq"]))
        if source is None or source["form"] != row["form"] or source["meaning_zho"].split("、") != row["meaning"]:
            raise ValueError(f"Ruled table row no longer matches late_table_rows.csv: {row['seq']}")
        if root.find(f"S[@id='{row['id']}']") is not None:
            raise ValueError(f"Ruled table row already present: {row['id']}")
        sentence = ET.SubElement(root, "S", {
            "id": row["id"],
            "source": f"PDF page {row['page']}; affix inventory row {row['seq']} ({row['source_table']}, late summary table)",
        })
        ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = row["form"]
        _transl(sentence, row["meaning"])
        word = ET.SubElement(sentence, "W", {"id": f"{row['id']}W1"})
        ET.SubElement(word, "FORM", {"kindOf": "original"}).text = row["form"]
        _transl(word, row["meaning"])
        for mi, (mform, readings) in enumerate(((row["affix"], [row["affix_function"]]),
                                                 (row["base"], row["base_meaning"])), 1):
            morph = ET.SubElement(word, "M", {"id": f"{row['id']}W1M{mi}"})
            ET.SubElement(morph, "FORM", {"kindOf": "original"}).text = mform
            _transl(morph, readings)
    _write(tree, paths["table_rows"])


def apply_ruled_corrections(xml_root: Path) -> None:
    """Apply source_data/ruled_corrections.tsv; every row names the value it expects."""
    with (CODE / "source_data/ruled_corrections.tsv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    trees = {kind: ET.parse(path) for kind, path in _xml_paths(xml_root).items()}
    nodes = {node.get("id"): node for tree in trees.values() for node in tree.getroot().iter() if node.get("id")}
    for row in rows:
        node, op, expected, value = nodes.get(row["target_id"]), row["op"], row["expected"], row["value"]
        where = f"{row['target_id']} ({op})"
        if node is None:
            raise ValueError(f"Ruled correction target missing: {where}")
        primary = next((t for t in node.findall("TRANSL") if t.get("ver") is None), None)
        original = node.find("FORM[@kindOf='original']")
        if op in ("transl", "transl_notes"):
            if primary is None or primary.text != expected:
                raise ValueError(f"Ruled correction no longer matches: {where}")
            if op == "transl":
                primary.text = value
            else:
                primary.set("notes", value)
        elif op == "delete_alt":
            matches = [t for t in node.findall("TRANSL") if t.get("ver") == "alt" and t.text == expected]
            if len(matches) != 1:
                raise ValueError(f"Ruled correction no longer matches: {where}")
            node.remove(matches[0])
        elif op in ("form", "form_notes"):
            if original is None or original.text != expected:
                raise ValueError(f"Ruled correction no longer matches: {where}")
            if op == "form":
                original.text = value
            else:
                original.set("notes", value)
        elif op == "unclear":
            if original is None or original.text != expected or node.findall("TRANSL"):
                raise ValueError(f"Ruled correction no longer matches: {where}")
            transl = ET.Element("TRANSL", {XML_LANG: "zho"})
            ET.SubElement(transl, "UNCLEAR")
            node.insert(list(node).index(original) + 1, transl)
        else:
            raise ValueError(f"Unknown ruled correction: {where}")
    for kind, path in _xml_paths(xml_root).items():
        _write(trees[kind], path)


def normalise_table_morphemes(xml_root: Path) -> None:
    """Morphemes of the affix-inventory rows in word order, hyphens only as notation.

    The tables list the affix column before the root column. A suffix therefore follows
    its root here; a prefix and a circumfix (whose first part opens the word) stay first.
    Hyphens are dropped from every morpheme except a circumfix's single hyphen at the
    root's place, and a circumfix printed with ... (ka-...-an) is written ka-an.
    """
    path = _xml_paths(xml_root)["table_rows"]
    tree = ET.parse(path)
    for sentence in tree.getroot().findall("S"):
        word = sentence.find("W")
        morphs = word.findall("M")
        if len(morphs) != 2:
            raise ValueError(f"Table row without exactly two morphemes: {sentence.get('id')}")
        affix_form = morphs[0].find("FORM[@kindOf='original']")
        root_form = morphs[1].find("FORM[@kindOf='original']")
        text = affix_form.text
        if "..." in text:
            before, after = text.split("...")
            affix_form.text = before.rstrip("-").replace("-", "") + "-" + after.lstrip("-").replace("-", "")
            ordered = morphs
        elif text.endswith("-") and not text.startswith("-"):
            affix_form.text = text.replace("-", "")
            ordered = morphs
        elif text.startswith("-") and not text.endswith("-"):
            affix_form.text = text.replace("-", "")
            ordered = [morphs[1], morphs[0]]
        else:
            raise ValueError(f"Unexpected affix shape {text!r}: {sentence.get('id')}")
        root_form.text = root_form.text.replace("-", "")
        for morph in morphs:
            word.remove(morph)
        for index, morph in enumerate(ordered, 1):
            morph.set("id", f"{word.get('id')}M{index}")
            word.append(morph)
    _write(tree, path)


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
    parser.add_argument("--xml-root", type=Path, default=CODE.parent / "XML",
                        help="XML tree to build or complete (generate_xml.sh passes its staging directory)")
    args = parser.parse_args()
    if args.record_provenance:
        record_provenance(args.record_provenance)
    elif args.complete_transcription:
        expand_optional_23c(args.xml_root)
        add_supplemental_examples(args.xml_root)
        add_ruled_records(args.xml_root)
        apply_ruled_corrections(args.xml_root)
        normalise_table_morphemes(args.xml_root)
    else:
        build(output=args.xml_root)
