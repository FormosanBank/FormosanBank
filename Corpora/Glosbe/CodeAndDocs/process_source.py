#!/usr/bin/env python3
"""Author original tiers from frozen Glosbe records and reviewed source IDs."""

import argparse
import csv
import hashlib
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
with (HERE / "withdrawn_ids.csv").open(encoding="utf-8", newline="") as stream:
    WITHDRAWN = {row["withdrawn_id"]: row for row in csv.DictReader(stream)}
with (HERE / "keep_published_ids.csv").open(encoding="utf-8", newline="") as stream:
    KEEP_ROWS = list(csv.DictReader(stream))
    KEEP_PUBLISHED = {row["id"] for row in KEEP_ROWS}
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


# Maintainer, 2026-10-18 ([licence]): "Yes, delete this: `note = {{Collected
# by FormosanBank for private research review; redistribution subject to
# Glosbe terms and third-party source rights}}`".
PRIVATE_NOTE = (", note = {{Collected by FormosanBank for private research review; "
                "redistribution subject to Glosbe terms and third-party source rights}}")


def render(records, metadata):
    root = etree.Element("TEXT", attrib=metadata)
    root.set("copyright", "CC BY-NC-SA 4.0")
    bibtex = root.get("BibTeX_citation", "")
    if bibtex.count(PRIVATE_NOTE) == 1:
        root.set("BibTeX_citation", bibtex.replace(PRIVATE_NOTE, ""))
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
    deleted = {sid for sid, row in WITHDRAWN.items() if row["action"] == "deleted"}
    seen = set()
    with (HERE / "source_records.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row["sid"] in deleted:  # withdrawn by ruling; see withdrawn_ids.csv
                seen.add(row["sid"])
                continue
            files[row["file"]].append(row)
    if seen != deleted:
        raise ValueError(f"Withdrawn ids not in the frozen source: {sorted(deleted - seen)}")
    witness_path = HERE / "work/reference_glosbe/amis_glosbe_traditional.xml"
    witness = {s.get("id"): s for s in etree.parse(witness_path).findall("S")}
    for keep in KEEP_ROWS:  # published ids kept pending a ruling (keep_published_ids.csv)
        rows = files[keep["file"]]
        if any(r["sid"] == keep["id"] for r in rows):
            continue
        sentence = witness[keep["witness_id"]]
        record = {"file": keep["file"], "sid": keep["id"], "record": keep["record"],
                  "kind": "reviewed_chinese", "source_key": keep["witness_id"],
                  "source": " ".join(sentence.findtext("FORM[@kindOf='original']").split()),
                  "target": " ".join(sentence.findtext("TRANSL").split()), "url": keep["url"],
                  "locator": f"work/reference_glosbe/amis_glosbe_traditional.xml#{keep['witness_id']}",
                  "sha256": hashlib.sha256(witness_path.read_bytes()).hexdigest(), "asterisks": ""}
        position = sum(1 for r in rows if r["sid"] < keep["id"])
        rows.insert(position, record)
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
            if old in KEEP_PUBLISHED:  # kept as published pending a ruling
                continue
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


# Editorial material in the Amis original FORM and the English TRANSL of the
# two Amis translation-memory files moves to notes= (maintainer, 2026-10-18,
# [editorial citations]: "Move to notes= (both files)"; "Consistency is good.
# Putting in notes is fine."). Chinese TRANSL text is not touched.
_REF = r"(?:[1-3] )?[A-Z][A-Za-z'.]*(?: [A-Za-z][A-Za-z'.]*)*\.? \d"
EDITORIAL = [
    # scripture or reading references inside parentheses, anywhere
    ("citation", re.compile(r"\s*\([^()]*\d+:\d+[^()]*\)")),
    # paragraph/picture/box cross-references: Amis "Nengnengen ko ...", English "See ..."
    ("cross-reference", re.compile(r"\s*\(\s*(?:Nen?gnengen|See|Look under)\b[^()]*\)")),
    # box and footnote captions: "(of the Watchtower)", "(of the Awake!)"
    ("caption", re.compile(r"\s*\(no (?:Kowaping|Padaka|padaka)\)")),
    # a trailing reference after a dash: " -Luka 12:15.", " -'Osien ko Isaya 40:26."
    ("citation", re.compile(r"\s+-\s?(?:'Osien ko |Read |Compare |Nengnengen ko )?" + _REF + r"[^-]{0,70}$")),
]
LEADING = [
    # the end of a reference whose start lies outside this Glosbe segment: "33:12-17) "
    ("citation", re.compile(r"^\d+:\d[\d:,; \-]*\)\s+")),
    # paragraph, page and list labels: "9 ", "6, 7. ", "(1) ", "(b) ", "b. ", "2. "
    ("label", re.compile(r"^(?:\d{1,2}(?:\s*,\s*\d{1,2})*\.?|\((?:\d{1,2}|[a-z])\)|[a-z]\.)\s+(?=[A-Z\"(]|'[A-Z])")),
]
# A list label that starts a second question inside the same segment: "? (3) O"
INNER_LABEL = re.compile(r"(?<=[?.!\"]) \((?:\d{1,2}|[a-z])\)(?= [A-Z])")


def move_editorial(element):
    """Move editorial pieces of one FORM/TRANSL into its notes. Returns them."""
    text = "".join(element.itertext())
    pieces = []
    changed = True
    while changed:
        changed = False
        for kind, pattern in LEADING + EDITORIAL:
            match = pattern.search(text)
            if not match:
                continue
            rest = (text[:match.start()] + " " + text[match.end():]).strip()
            if not re.search(r"[^\W\d_]", rest):
                continue  # the whole segment is the reference; keep it
            pieces.append((match.start(), kind, match.group(0).strip()))
            text = " ".join(rest.split())
            changed = True
            break
    for match in list(INNER_LABEL.finditer(text))[::-1]:
        pieces.append((match.start(), "label", match.group(0).strip()))
        text = text[:match.start()] + text[match.end():]
    if pieces:
        element.text = text
        notes = [element.get("notes")] if element.get("notes") else []
        element.set("notes", " | ".join(notes + [p for _, _, p in pieces]))
    return [(k, p) for _, k, p in pieces]


def apply_label_notes(sentences, records):
    """source_labels.csv labels, already removed at render, become notes."""
    sid_of = {r["record"]: r["sid"] for r in records}
    count = 0
    for record, label in LABELS.items():
        sentence = sentences.get(sid_of[record])
        if sentence is None:
            continue
        for element, value in ([(sentence.find("FORM[@kindOf='original']"), label["source_label"])]
                               + [(t, label["target_label"]) for t in sentence.findall("TRANSL")]):
            note = value.strip()
            if element.get("notes") and note in element.get("notes").split(" | "):
                continue
            notes = [element.get("notes")] if element.get("notes") else []
            element.set("notes", " | ".join([note] + notes))
            count += 1
    return count


def apply_rulings(bank):
    """Before the alias replay: source labels and editorial material to notes."""
    trees = {p: etree.parse(p) for p in sorted((HERE.parent / "XML").rglob("*.xml"))}
    sentences = {s.get("id"): s for t in trees.values() for s in t.getroot().findall("S")}
    with (HERE / "source_records.jsonl").open(encoding="utf-8") as stream:
        records = [json.loads(line) for line in stream]
    labels = apply_label_notes(sentences, records)
    moved = defaultdict(int)
    for path, tree in trees.items():
        if not path.name.endswith("_tmem.xml") or not path.name.startswith("Glosbe_ami_"):
            continue
        for sentence in tree.getroot().findall("S"):
            targets = [sentence.find("FORM[@kindOf='original']")]
            targets += [t for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "eng"]
            for element in targets:
                for kind, _ in move_editorial(element):
                    moved[kind] += 1
    for path, tree in trees.items():
        tree.write(str(path), encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"Recorded {labels} source-label notes; moved to notes: {dict(sorted(moved.items()))}")


def apply_typography(bank):
    """After the alias replay: main's typography (main_typography.csv)."""
    trees = {p: etree.parse(p) for p in sorted((HERE.parent / "XML").rglob("*.xml"))}
    sentences = {s.get("id"): s for t in trees.values() for s in t.getroot().findall("S")}
    typography = apply_main_typography(sentences)
    joined = 0
    with (HERE / "joined_translations.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):  # English alternatives main kept as one TRANSL
            sentence = sentences[row["sid"]]
            english = [t for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "eng"]
            if " || ".join("".join(t.itertext()) for t in english) != row["before"]:
                raise ValueError(f"Joined-translation row no longer matches: {row['sid']}")
            english[0].text = row["after"]
            english[0].attrib.pop("ver", None)
            for extra in english[1:]:
                sentence.remove(extra)
            joined += 1
    for path, tree in trees.items():
        tree.write(str(path), encoding="utf-8", xml_declaration=True, pretty_print=True)
    print(f"Kept main's typography in {typography} fields; rejoined {joined} English translations")


LEDGER_FIELDS = ["withdrawn_id", "kept_id", "action", "reason", "ruling"]
DUPLICATE_RULING = ('2026-10-18, [highlight spaces main already published]: "Yes, remove them '
                    '(and join the 79)"; [U000669/U000801 duplicate]: "Withdraw U000801 (-> U000669)"')


def _write_ledger(rows):
    with (HERE / "withdrawn_ids.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=LEDGER_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _published_ids():
    return {s.get("id") for f in sorted((HERE / "pre_correction_snapshot").rglob("*.xml"))
            for s in etree.parse(f).findall("S")}


def remove_duplicates(bank, write_ledger=False):
    """The shared within-file duplicate removal on the original tier, except
    for ids kept as published pending a ruling (keep_published_ids.csv). A
    published id it removes must be listed in withdrawn_ids.csv ("duplicate")."""
    sys.path.insert(0, str(bank))
    from QC.cleaning.remove_duplicate_sentences import apply_removals, plan_removals

    plan = [p for p in plan_removals(str(HERE.parent / "XML"), scope="file", tier="original")
            if p[1] not in KEEP_PUBLISHED]
    published = _published_ids()
    removed = {p[1]: p[3] for p in plan if p[1] in published}
    listed = {k for k, v in WITHDRAWN.items() if v["action"] == "duplicate"}
    if write_ledger:
        rows = [v for v in WITHDRAWN.values() if v["action"] != "duplicate"]
        rows += [{"withdrawn_id": old, "kept_id": keep, "action": "duplicate",
                  "reason": "Same Amis FORM and the same translation as the kept S (copies of "
                            "one Glosbe sentence that differed only by search-highlight spaces).",
                  "ruling": DUPLICATE_RULING} for old, keep in sorted(removed.items())]
        _write_ledger(rows)
    elif set(removed) != listed:
        raise ValueError(f"Duplicate removal differs from withdrawn_ids.csv: "
                         f"new {sorted(set(removed) - listed)[:5]}, gone {sorted(listed - set(removed))[:5]}")
    merged = apply_removals(plan) if plan else 0
    print(f"Removed {len(plan)} duplicate S ({len(removed)} published ids); "
          f"merged {merged} distinct translations")


ENG_TMEM = HERE.parent / "XML" / "Amis" / "Glosbe_ami_eng_tmem.xml"
ZHO_TMEM = HERE.parent / "XML" / "Amis" / "Glosbe_ami_zho_tmem.xml"


def _form_key(sentence):
    return " ".join("".join(sentence.find("FORM[@kindOf='original']").itertext()).split())


# Maintainer, 2026-10-18 (round 2, near-matches): "If the two versions differ in
# the addition or subtraction of an Amis word, then they are different records
# and should not be merged. ... commas and periods and dashes can be ignored
# ... Differences in ' vs \" vs curly versions of either must be discussed."
IGNORABLE = re.compile(r"[\s,.\-]")


def _loose_key(text):
    return IGNORABLE.sub("", text)


def plan_merge():
    """Amis-Chinese S joining one Amis-English S: identical original FORM, or
    (if none) a FORM that differs only in spaces, commas, periods and dashes.
    Returns {zho id: (eng id, "exact" | "loose", zho text)} and the ambiguous."""
    english = etree.parse(ENG_TMEM).getroot().findall("S")
    chinese = etree.parse(ZHO_TMEM).getroot().findall("S")
    exact, loose = defaultdict(list), defaultdict(list)
    for sentence in english:
        exact[_form_key(sentence)].append(sentence.get("id"))
        loose[_loose_key(_form_key(sentence))].append(sentence.get("id"))
    merges, ambiguous = {}, {}
    for sentence in chinese:
        sid, text = sentence.get("id"), _form_key(sentence)
        if sid in KEEP_PUBLISHED:
            continue
        kind, matches = "exact", exact.get(text, [])
        if not matches:
            kind, matches = "loose", loose.get(_loose_key(text), [])
        if len(matches) == 1:
            merges[sid] = (matches[0], kind, text)
        elif matches:
            ambiguous[sid] = matches
    return merges, ambiguous


def drop_enumerators(sentences):
    """List enumerators deleted outright, not kept as notes (drop_enumerators.csv)."""
    dropped = 0
    with (HERE / "drop_enumerators.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):  # list enumerators deleted, not kept as notes
            sentence = sentences[row["sid"]]
            element = (sentence.find("FORM[@kindOf='original']") if row["element"] == "FORM" else
                       next(t for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "eng"))
            notes = element.get("notes", "").split(" | ")
            for piece in row["pieces"].split(" | "):
                if piece not in notes:
                    raise ValueError(f"Enumerator {piece} not in notes of {row['sid']}")
                notes.remove(piece)
                dropped += 1
            if notes:
                element.set("notes", " | ".join(notes))
            else:
                del element.attrib["notes"]
    return dropped


def merge_translation_files(bank, write_ledger=False):
    """One Amis translation-memory file (maintainer, 2026-10-18: "For Glosbe,
    I think we can have just one file. Some Ss have translations in English,
    some in Mandarin, and some in both."). A Chinese-file S whose Amis FORM is
    identical to an English-file S joins it (its id is withdrawn -> the English
    id); every other Chinese-file S moves over with its own id. The English
    file keeps its path and TEXT id; the Chinese file is removed."""
    plan, ambiguous = plan_merge()
    merges = {old: keep for old, (keep, _, _) in plan.items()}
    ledger = {k: v for k, v in WITHDRAWN.items() if v["action"] == "merged"}
    if write_ledger:
        rows = [v for v in WITHDRAWN.values() if v["action"] != "merged"]
        for old, (keep, kind, text) in sorted(plan.items()):
            if kind == "exact":
                reason = ("Same Amis sentence (identical original FORM) as the kept "
                          "Amis-English S; its Chinese translation moved there.")
                ruling = MERGE_RULING
            else:
                reason = ("Same Amis sentence as the kept Amis-English S except for spaces, "
                          "commas, periods or dashes; the kept S keeps its Amis-English FORM. "
                          f"Amis-Chinese FORM was: {text}")
                ruling = NEAR_RULING
            rows.append({"withdrawn_id": old, "kept_id": keep, "action": "merged",
                         "reason": reason, "ruling": ruling})
        target = {r["withdrawn_id"]: r["kept_id"] for r in rows}
        for row in rows:  # a duplicate whose survivor later joins points at the final id
            while row["kept_id"] in target and row["kept_id"] != row["withdrawn_id"]:
                row["kept_id"] = target[row["kept_id"]]
        _write_ledger(rows)
        ledger = {old: {"kept_id": keep} for old, keep in merges.items()}
    planned = {old: row["kept_id"] for old, row in ledger.items()}
    if planned != merges:
        raise ValueError(f"Merge plan differs from withdrawn_ids.csv: "
                         f"new {sorted(set(merges.items()) - set(planned.items()))[:5]}, "
                         f"gone {sorted(set(planned.items()) - set(merges.items()))[:5]}")
    english_tree, chinese_tree = etree.parse(ENG_TMEM), etree.parse(ZHO_TMEM)
    english = {s.get("id"): s for s in english_tree.getroot().findall("S")}
    root = english_tree.getroot()
    zho_root = chinese_tree.getroot()
    moved = joined = 0
    for sentence in zho_root.findall("S"):
        sid = sentence.get("id")
        if sid not in merges:
            root.append(sentence)
            moved += 1
            continue
        target = english[merges[sid]]
        form, other = target.find("FORM[@kindOf='original']"), sentence.find("FORM[@kindOf='original']")
        pieces = (form.get("notes") or "").split(" | ") if form.get("notes") else []
        for piece in ((other.get("notes") or "").split(" | ") if other.get("notes") else []):
            if piece not in pieces:
                pieces.append(piece)
        if pieces:
            form.set("notes", " | ".join(pieces))
        have = {(t.get(XML_LANG), " ".join("".join(t.itertext()).split())) for t in target.findall("TRANSL")}
        for transl in sentence.findall("TRANSL"):
            key = (transl.get(XML_LANG), " ".join("".join(transl.itertext()).split()))
            if key in have:
                continue
            transl.attrib.pop("ver", None)
            if any(t.get(XML_LANG) == key[0] for t in target.findall("TRANSL")):
                transl.set("ver", "alt")
            last = target.findall("TRANSL")[-1]
            last.addnext(transl)
            have.add(key)
        joined += 1
    dropped = drop_enumerators(english)
    zho_source = zho_root.get("source")
    root.set("source", f"{root.get('source')} Chinese translations: {zho_source}")
    english_tree.write(str(ENG_TMEM), encoding="utf-8", xml_declaration=True, pretty_print=True)
    ZHO_TMEM.unlink()
    final = {s.get("id") for f in (HERE.parent / "XML").rglob("*.xml") for s in etree.parse(f).findall("S")}
    with (HERE / "withdrawn_ids.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["action"].startswith("text"):
                continue
            if row["withdrawn_id"] in final or row["kept_id"] not in final:
                raise ValueError(f"withdrawn_ids.csv does not describe the output: {row['withdrawn_id']}")
    print(f"Deleted {dropped} list enumerators")
    exact_n = sum(1 for _, kind, _ in plan.values() if kind == "exact")
    print(f"Joined {joined} Amis-Chinese S to Amis-English S ({exact_n} identical, {joined - exact_n} "
          f"differing only in spaces/commas/periods/dashes); moved {moved} with their own ids; "
          f"{len(ambiguous)} match more than one Amis-English S and were moved unmerged")


NEAR_RULING = ('2026-10-18 (round 2, near-matches): "Join spacing/punctuation/quote-only ones"; '
               '"commas and periods and dashes can be ignored; merge in whatever way seems more '
               'appropriate (but do so consistently, using code)."')
MERGE_RULING = ("2026-10-18: \"If we have Mandarin and English translations for the same Amis, is it "
                "one S or two? It should be one, with both English and Mandarin translations.\"; "
                "\"Merge inside #180\"; \"For Glosbe, I think we can have just one file.\"")


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
    parser.add_argument("--apply-typography", type=Path)
    parser.add_argument("--remove-duplicates", type=Path)
    parser.add_argument("--merge-translations", type=Path)
    parser.add_argument("--write-ledger", dest="write_merge_ledger", action="store_true",
                        help="Rewrite the merged rows of withdrawn_ids.csv; review the diff")
    parser.add_argument("--record-provenance", type=Path)
    args = parser.parse_args()
    if args.record_provenance:
        record_provenance(args.record_provenance.resolve())
    elif args.apply_aliases:
        apply_reviewed_aliases(args.apply_aliases.resolve())
    elif args.apply_rulings:
        apply_rulings(args.apply_rulings.resolve())
    elif args.apply_typography:
        apply_typography(args.apply_typography.resolve())
    elif args.remove_duplicates:
        remove_duplicates(args.remove_duplicates.resolve(), args.write_merge_ledger)
    elif args.merge_translations:
        merge_translation_files(args.merge_translations.resolve(), args.write_merge_ledger)
    else:
        if not args.formosanbank_root:
            parser.error("use generate_xml.sh or supply --formosanbank-root")
        main(args.formosanbank_root.resolve())
