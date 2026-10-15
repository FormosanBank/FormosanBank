#!/usr/bin/env python3
"""Freeze the reviewed 2026 crawl and Joseph Lin witness, without fetching."""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote, urlparse

from lxml import etree, html

HERE = Path(__file__).resolve().parent
# Reviewed editorial references, not grammaticality judgments (POL-016).
with (HERE / "source_markers.csv").open(encoding="utf-8", newline="") as stream:
    MARKERS = {row["source_key"]: row["role"] for row in csv.DictReader(stream)}


def csv_rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def layout(text):
    return " ".join(text.split())


def capture(dev):
    """Keep assigned IDs as data; corrected text never determines identity."""
    index = csv_rows(dev / "data/processed/xml_index.csv")
    restoration = {
        row["record_id"]: row
        for row in csv_rows(dev / "data/processed/amis_chinese_restoration_audit.csv")
    }
    witness = HERE / "work/reference_glosbe/amis_glosbe_traditional.xml"
    reviewed = {s.get("id"): s for s in etree.parse(witness).findall("S")}
    witness_sha = hashlib.sha256(witness.read_bytes()).hexdigest()
    candidates = {}
    for name, kind in [("quality_filtered_examples.jsonl", "tmem"),
                       ("dictionary_entries_deduped.jsonl", "lexical")]:
        with (dev / "data/processed" / name).open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                candidates[row["record_id"]] = (kind, row)

    # These two cached entries are definitions, not cross-reference/empty rows.
    for record, lang in [
        ("GLOSBE_DICT_c8eb4078bc44582c", "tay"),
        ("GLOSBE_DICT_a004589dd6fb0864", "xsy"),
    ]:
        source_id = candidates[record][1]["translation_id"]
        sid = f"GLOSBE_{lang}_eng_LEXICAL_T{source_id}"
        index.append({"record_id": record, "sentence_id": sid,
                      "xml_file": f"XML/{lang}/Glosbe_{lang}_eng_lexical.xml"})

    pages = {}
    output = []
    for entry in index:
        record = entry["record_id"]
        if record in restoration:
            legacy = restoration[record]["legacy_source_id"]
            sentence = reviewed[legacy]
            form = sentence.find("FORM[@kindOf='original']")
            if form is None:
                form = sentence.find("FORM")
            source = layout("".join(form.itertext()))
            target = layout("".join(sentence.find("TRANSL").itertext()))
            locator = "work/reference_glosbe/amis_glosbe_traditional.xml#" + legacy
            source_key = legacy
            sha = witness_sha
            url = restoration[record]["source_url"]
            kind = "reviewed_chinese"
        else:
            kind, row = candidates[record]
            cache = row["raw_html_path"]
            if cache not in pages:
                content = (dev / cache).read_bytes()
                pages[cache] = (html.fromstring(content.decode("utf-8")),
                                hashlib.sha256(content).hexdigest())
            page, sha = pages[cache]
            if sha != row["raw_html_sha256"]:
                raise ValueError(f"Changed capture: {cache}")
            source_key = row["tmBunchId"] if kind == "tmem" else row["translation_id"]
            nodes = page.xpath('//*[@data-translationid=$key]', key=source_key)
            if len(nodes) != 1:
                raise ValueError(f"Ambiguous source ID: {record}")
            if kind == "tmem":
                cells = nodes[0].getparent().getparent().xpath(
                    './/div[contains(concat(" ", normalize-space(@class), " "), " w-1/2 ")]')
                if len(cells) != 2:
                    raise ValueError(f"Expected two translation cells: {record}")
                source, target = (layout(cell.text_content()) for cell in cells)
            else:
                source = unquote(urlparse(row["source_url"]).path.rsplit("/", 1)[-1])
                targets = nodes[0].xpath('.//*[contains(@class,"translation__item__pharse")]')
                if len(targets) != 1:
                    raise ValueError(f"Expected one definition: {record}")
                target = layout(targets[0].text_content())
            url = row["source_url"]
            locator = cache + "#" + source_key
        asterisks = ""
        if "*" in source or "*" in target:
            asterisks = MARKERS.get(source_key, "")
            if asterisks not in {"footnote", "highlight"}:
                raise ValueError(f"Unreviewed asterisk in {record}")
        output.append({
            "file": entry["xml_file"].removeprefix("XML/"),
            "sid": entry["sentence_id"], "record": record, "kind": kind,
            "source_key": source_key, "source": source, "target": target,
            "url": url, "locator": locator, "sha256": sha, "asterisks": asterisks,
        })
    return output


def capture_labels(records):
    """Candidate paired editorial labels. Review this file with the snapshot."""
    left_pattern = re.compile(r"^(?:[1-3]?\d(?:\s*[-,]\s*[1-3]?\d)*\.?\s+|\([1-3]?\d\)\s*)")
    right_pattern = re.compile(r"^(?:[1-3]?\d(?:\s*[-,]\s*[1-3]?\d)*\.?\s+|\([a-z]\)\s*)")
    labels = []
    for row in records:
        if row["kind"] != "tmem" or row["file"] != "ami/Glosbe_ami_eng_tmem.xml":
            continue
        source, target = row["source"], row["target"]
        while True:
            left, right = left_pattern.match(source), right_pattern.match(target)
            if not left or not right:
                break
            a, b = (match[0].strip("(). ") for match in (left, right))
            if not (a == b or (a.isdigit() and b.isalpha() and int(a) == ord(b) - 96)):
                break
            source, target = source[left.end():], target[right.end():]
        if source != row["source"]:
            labels.append({"record": row["record"], "sha256": row["sha256"],
                           "source_label": row["source"][:len(row["source"]) - len(source)],
                           "target_label": row["target"][:len(row["target"]) - len(target)]})
    with (HERE / "source_labels.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["record", "sha256", "source_label", "target_label"],
                                quoting=csv.QUOTE_ALL, lineterminator="\n")
        writer.writeheader()
        writer.writerows(labels)
    print(f"Captured {len(labels)} paired-label candidates for source review")


def capture_chinese_coverage(dev, records):
    """Recover historical group membership only; never author text with its cleanup."""
    sentences = etree.parse(HERE / "work/reference_glosbe/amis_glosbe_traditional.xml").findall("S")
    witness = {s.get("id"): s for s in sentences}

    def old_key(text):
        text = " ".join(unicodedata.normalize("NFC", text).replace("*", "").split())
        text = re.sub(r"\s+([,.;:!?])", r"\1", text)
        return re.sub(r"([A-Za-z])\s+'", r"\1'", text).casefold()

    def pair(sentence):
        return (old_key(sentence.findtext("FORM[@kindOf='original']")),
                old_key(sentence.findtext("TRANSL")))

    def layout_key(text):
        text = text.translate(str.maketrans({"ˈ": "'", "ʼ": "'", "’": "'", "‘": "'",
                                           "“": '"', "”": '"'})).replace("*", "")
        return "".join(unicodedata.normalize("NFC", text).casefold().split())

    historical = {}
    for row in csv_rows(dev / "data/processed/amis_chinese_restoration_audit.csv"):
        key = pair(witness[row["legacy_source_id"]])
        if key in historical:
            raise ValueError("Historical Chinese group is ambiguous")
        historical[key] = row
    indexed = {row["record"]: row for row in records}
    variants = defaultdict(set)
    for row in records:
        if row["kind"] == "reviewed_chinese":
            variants[(layout_key(row["source"]), layout_key(row["target"]))].add(row["sid"])
    coverage = []
    for sentence in sentences:
        previous = historical[pair(sentence)]
        record = previous["record_id"]
        if record in indexed:
            sid = indexed[record]["sid"]
        else:
            source, target = sentence.findtext("FORM[@kindOf='original']"), sentence.findtext("TRANSL")
            matches = variants[(layout_key(source), layout_key(target))]
            if len(matches) != 1:
                raise ValueError(f"Unresolved historical duplicate: {sentence.get('id')}")
            sid = next(iter(matches))
        coverage.append({"source_id": sentence.get("id"), "record": record, "sentence_id": sid})
    with (HERE / "chinese_source_coverage.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["source_id", "record", "sentence_id"],
                                lineterminator="\n")
        writer.writeheader()
        writer.writerows(coverage)
    print(f"Accounted for all {len(coverage)} Chinese witness records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", type=Path, required=True,
                        help="Preserved development crawl and its reviewed index")
    parser.add_argument("--refresh-labels", action="store_true",
                        help="Replace the label decision table; requires source review")
    args = parser.parse_args()
    records = capture(args.dev.resolve())
    destination = HERE / "source_records.jsonl"
    destination.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                           encoding="utf-8")
    if args.refresh_labels:
        capture_labels(records)
    capture_chinese_coverage(args.dev.resolve(), records)
    print(f"Captured {len(records)} indexed translations in {destination.name}")
