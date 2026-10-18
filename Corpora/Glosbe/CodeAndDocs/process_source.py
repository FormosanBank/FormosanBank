#!/usr/bin/env python3
"""Author original tiers from frozen Glosbe records and reviewed source IDs."""

import argparse
import csv
import json
import os
import re
import subprocess
import sys
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
with (HERE / "highlight_space_keep.csv").open(encoding="utf-8", newline="") as stream:
    HIGHLIGHT_KEEP = defaultdict(list)
    for row in csv.DictReader(stream):
        HIGHLIGHT_KEEP[row["record"]].append(row["text"])


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


def strip_highlight_spaces(text, keep=()):
    """Remove the spaces Glosbe's search-word highlighting left in a scrape.

    Joseph Lin's witness was scraped from Glosbe result pages, which pad the
    searched word with spaces (`i ,` on the page for "i", `" o wacay` on the
    page for "o"). Collapsed whitespace hides the padding between words; what
    remains is a space before , ; : ! ? or a lone period, inside parentheses,
    or just inside a double quotation (maintainer, 2026-10-18: "Fix the whole
    highlight-space class (426 S) before merge" and "No space after \"").
    A spaced ellipsis ". . ." is the source's own spelling and is not touched.
    Single quotes are left alone: ' is also the Amis glottal letter.
    `keep` lists exact source snippets whose space is not this PR's artifact
    (highlight_space_keep.csv): main published it, or the English-paired
    capture prints it too. Changing those is a separate, unruled question.
    """
    for snippet in keep:
        if text.count(snippet) != 1:
            raise ValueError(f"Kept highlight snippet not found once: {snippet!r}")
        text = text.replace(snippet, snippet.replace(" ", "\0"))
    text = re.sub(r"(?<!\. \.)\s+([,;:!?])", r"\1", text)
    text = re.sub(r"(?<![.\s])\s+\.(?!\s*\.)", ".", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    if text.count('"') % 2 == 0:
        parts = text.split('"')
        for i in range(1, len(parts), 2):  # the text inside each quotation
            parts[i] = parts[i].strip()
        text = '"'.join(parts)
    return text.replace("\0", " ")


def content_fields(record):
    source, target = (source_text(record, field) for field in ("source", "target"))
    if record["kind"] == "reviewed_chinese":
        source = strip_highlight_spaces(source, HIGHLIGHT_KEEP.get(record["record"], ()))
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


def main(bank):
    sys.path.insert(0, str(bank))
    from QC.corpus_counts import resolve_language

    files = defaultdict(list)
    with (HERE / "source_records.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            files[row["file"]].append(row)
    outputs = []
    for relative, rows in files.items():
        baseline = HERE / "pre_correction_snapshot" / relative
        metadata = dict(etree.parse(baseline).getroot().attrib)
        language = resolve_language(metadata.get(XML_LANG), metadata.get("dialect"))
        if language is None:
            raise ValueError(f"Unregistered source language: {relative}")
        output = HERE.parent / "XML" / language / Path(relative).name
        outputs.append((output, rows, metadata))
    unexpected = set((HERE.parent / "XML").rglob("*.xml")) - {p for p, _, _ in outputs}
    if unexpected:
        raise ValueError(f"Unexpected final XML; review its layout before rebuilding: {sorted(unexpected)}")
    for output, rows, metadata in outputs:
        output.parent.mkdir(parents=True, exist_ok=True)
        etree.ElementTree(render(rows, metadata)).write(
            output, encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"Generated {len(files)} Glosbe source files")


def apply_reviewed_aliases(bank):
    """Replay reviewed source associations, never infer them from spelling alone."""
    sys.path.insert(0, str(bank))
    from QC.cleaning.remove_duplicate_sentences import apply_removals, normalize_for_comparison
    from QC.xml_forms import find_base_form

    entries = {s.get("id"): (str(p), s)
               for p in (HERE.parent / "XML").rglob("*.xml")
               for s in etree.parse(p).findall("S")}
    plan = []
    with (HERE / "source_aliases.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            old, keep = row["omitted_id"], row["retained_id"]
            if old not in entries:  # Already absent from the baseline or manual edits.
                continue
            old_path, old_s = entries[old]
            keep_path, keep_s = entries[keep]
            forms = [normalize_for_comparison(find_base_form(s, "original").text or "")
                     for s in (old_s, keep_s)]
            if old_path != keep_path or forms[0] != forms[1]:
                raise ValueError(f"Reviewed alias no longer matches: {old} -> {keep}")
            plan.append((old_path, old, keep_path, keep))
    merged = apply_removals(plan)
    print(f"Replayed {len(plan)} reviewed aliases; retained {merged} alternate translations")


def _element(sentence, element, text):
    """The one FORM original, or the one TRANSL whose text is `text`."""
    if element == "FORM":
        found = sentence.findall("FORM[@kindOf='original']")
    else:
        found = [t for t in sentence.findall("TRANSL") if "".join(t.itertext()) == text]
    if len(found) != 1:
        raise ValueError(f"Expected one {element} in {sentence.get('id')}")
    return found[0]


def apply_main_typography(sentences):
    """Keep main's dashes, dates, symbols and ellipses where the maintainer
    rejected the PR's source spelling (2026-10-18: [dashes, dates, symbols]
    "Reject"; [ellipsis] "Reject"). Each row replaces one whole field and
    refuses to apply if the field no longer reads as reviewed."""
    count = 0
    with (HERE / "main_typography.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            target = _element(sentences[row["sid"]], row["element"], row["before"])
            if "".join(target.itertext()) != row["before"]:
                raise ValueError(f"Typography row no longer matches: {row['sid']}")
            target.text = row["after"]
            count += 1
    return count


def apply_rulings(bank):
    """Post-cleaning, table-driven maintainer rulings (see README)."""
    trees = {p: etree.parse(p) for p in sorted((HERE.parent / "XML").rglob("*.xml"))}
    sentences = {s.get("id"): s for t in trees.values() for s in t.getroot().findall("S")}
    typography = apply_main_typography(sentences)
    for path, tree in trees.items():
        tree.write(str(path), encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"Kept main's typography in {typography} fields")


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
    parser.add_argument("--formosanbank-root", type=Path)
    parser.add_argument("--apply-aliases", type=Path)
    parser.add_argument("--apply-rulings", type=Path)
    parser.add_argument("--record-provenance", type=Path)
    args = parser.parse_args()
    if args.record_provenance:
        record_provenance(args.record_provenance.resolve())
    elif args.apply_aliases:
        apply_reviewed_aliases(args.apply_aliases.resolve())
    elif args.apply_rulings:
        apply_rulings(args.apply_rulings.resolve())
    else:
        if not args.formosanbank_root:
            parser.error("use generate_xml.sh or supply --formosanbank-root")
        main(args.formosanbank_root.resolve())
