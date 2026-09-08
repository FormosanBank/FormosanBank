#!/usr/bin/env python3
"""Author original tiers from frozen Glosbe records and reviewed source IDs."""

import argparse
import csv
import json
import os
import re
import subprocess
import unicodedata
from collections import defaultdict
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
with (HERE / "source_labels.csv").open(encoding="utf-8", newline="") as stream:
    LABELS = {row["record"]: row for row in csv.DictReader(stream)}
with (HERE / "source_notes.csv").open(encoding="utf-8", newline="") as stream:
    NOTES = {row["record"]: row for row in csv.DictReader(stream)}


def text_key(text):
    """Compare typographic variants without joining words or folding case."""
    text = unicodedata.normalize("NFC", text)
    text = text.translate(str.maketrans({"ˈ": "'", "ʼ": "'", "’": "'", "‘": "'"}))
    return re.sub(r"\s+([,.;:!?])", r"\1", " ".join(text.split()))


def source_text(record, field):
    text = record[field]
    role = record["asterisks"]
    if "*" in text:
        if role == "footnote":
            text = text.replace("*", "")
        elif role == "highlight":
            text = text.replace("**", "")
            if "*" in text:
                raise ValueError(f"Unpaired highlight: {record['record']}")
        else:
            raise ValueError(f"Unreviewed asterisk: {record['record']}")
    return " ".join(text.split())


def content_fields(record):
    source, target = (source_text(record, field) for field in ("source", "target"))
    # The English JW fragments repeat article/page/outline labels in both
    # columns. These are locators, not spoken numerals. The frozen input
    # retains them; years, dates, unpaired numbers and Chinese stay intact.
    if record["record"] in LABELS:
        label = LABELS[record["record"]]
        if record["sha256"] != label["sha256"]:
            raise ValueError(f"Label review belongs to another capture: {record['record']}")
        if not source.startswith(label["source_label"]) or not target.startswith(label["target_label"]):
            raise ValueError(f"Label changed: {record['record']}")
        source, target = source[len(label["source_label"]):], target[len(label["target_label"]):]
    if record["record"] in NOTES:
        note = NOTES[record["record"]]
        if record["sha256"] != note["sha256"]:
            raise ValueError(f"Citation review belongs to another capture: {record['record']}")
        if not source.endswith(note["source_suffix"]) or not target.endswith(note["target_suffix"]):
            raise ValueError(f"Citation changed: {record['record']}")
        source = source[:-len(note["source_suffix"])].rstrip()
        target = target[:-len(note["target_suffix"])].rstrip()
    return source, target


def render(records, metadata):
    root = etree.Element("TEXT", attrib=metadata)
    root.set("copyright", "CC BY-NC-SA 4.0")
    grouped = defaultdict(list)
    for row in records:
        grouped[row["sid"]].append(row)
    for sid, rows in grouped.items():
        source = content_fields(rows[0])[0]
        for row in rows[1:]:
            other = content_fields(row)[0]
            same = text_key(source) == text_key(other)
            # Joseph's two versions of this title differ only in capitals.
            if sid == "GLOSBE_ami_zho_TMEM_U000375":
                same = text_key(source).casefold() == text_key(other).casefold()
            if not same:
                raise ValueError(f"Different source forms share {sid}")
        sentence = etree.SubElement(root, "S", id=sid)
        form = etree.SubElement(sentence, "FORM", kindOf="original")
        form.text = source
        if rows[0]["record"] in NOTES:
            form.set("notes", NOTES[rows[0]["record"]]["note"])
        seen = set()
        for row in rows:
            target = content_fields(row)[1]
            key = text_key(target)
            if key in seen:
                continue
            attributes = {XML_LANG: "zho" if row["kind"] == "reviewed_chinese" else "eng"}
            if row["record"] in NOTES:
                attributes["notes"] = NOTES[row["record"]]["note"]
            if seen:
                attributes["ver"] = "alt"
            etree.SubElement(sentence, "TRANSL", attrib=attributes).text = target
            seen.add(key)
    return root


def main():
    files = defaultdict(list)
    with (HERE / "source_records.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            files[row["file"]].append(row)
    for relative, rows in files.items():
        baseline = HERE / "pre_correction_snapshot" / relative
        metadata = dict(etree.parse(baseline).getroot().attrib)
        output = HERE.parent / "XML" / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        etree.ElementTree(render(rows, metadata)).write(
            output, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"Generated {len(files)} Glosbe source files")


def record_provenance(bank):
    revision = os.environ.get("FORMOSANBANK_COMMIT", "")
    if (bank / ".git").exists():
        revision = subprocess.run(["git", "-C", str(bank), "rev-parse", "HEAD"],
                                  check=True, capture_output=True, text=True).stdout.strip()
    if not revision:
        print("No checkout/export revision supplied; reviewed provenance was not updated.")
        return
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Expected a full FormosanBank checkout/export commit")
    value = {"_note": "Tools used for this build. Informational; no executable tools pin.",
             "formosanbank_commit": revision}
    (HERE / "provenance.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record-provenance", type=Path)
    args = parser.parse_args()
    if args.record_provenance:
        record_provenance(args.record_provenance.resolve())
    else:
        main()
