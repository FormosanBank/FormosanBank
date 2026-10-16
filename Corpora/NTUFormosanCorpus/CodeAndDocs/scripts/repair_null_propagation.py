#!/usr/bin/env python3
"""Repair the source-backed NTU null markers left after XML generation.

The canonical null is U+2205 ``∅``.  It remains on original S tiers and on
both W/M tiers, while standard S tiers omit the non-surface unit.  Seven
source-located NTU examples need a post-parser repair:

* four Sakizaya grammar examples carry source ``ø-`` analyses whose null was
  generated on W/M but not propagated to the original sentence FORM;
* one Kanakanavu grammar example has a source ``ø中心語`` W but no M child and
  no original sentence null;
* one Kanakanavu sentence and its POL-026 clone retain source U+00D8 ``Ø`` on
  S/W while their M tier already uses canonical ``∅``.

The raw JSON remains unchanged as the primary source witness.  This repair is
deterministic and idempotent, and the next make step regenerates PHON.
"""

from __future__ import annotations

import argparse
import collections
import os
import re
from pathlib import Path

import lxml.etree as etree


SAKIZAYA_PREFIX_NULL = {
    "06_S_1",
    "06_S_2",
    "13_S_29",
    "13_S_30",
}

KANAKANAVU_CANONICALIZE = {
    "3_S_375",
    "3_S_375-opt",
}


def _tier(parent, kind):
    return next(
        (form for form in parent.findall("FORM")
         if form.get("kindOf") == kind),
        None,
    )


def _append_note(form, note):
    existing = (form.get("notes") or "").strip()
    if note in existing:
        return
    form.set("notes", f"{existing}; {note}" if existing else note)


def _remove_phon(sentence):
    for phon in list(sentence.xpath(".//PHON")):
        phon.getparent().remove(phon)


def _prefix_null(sentence):
    original = _tier(sentence, "original")
    if original is None or "∅" in (original.text or ""):
        return False
    original.text = "∅" + (original.text or "")
    _append_note(
        original,
        "canonical source-backed null propagated from the first W/M analysis; "
        "standard S omits the null unit",
    )
    _remove_phon(sentence)
    return True


def _append_sentence_null(sentence):
    original = _tier(sentence, "original")
    if original is None or "∅" in (original.text or ""):
        return False
    text = original.text or ""
    match = re.search(r"([.!?。！？])$", text)
    if match:
        original.text = text[:match.start()] + " ∅" + match.group(1)
    else:
        original.text = text.rstrip() + " ∅"
    _append_note(
        original,
        "source grammar record 14-8 lists a null head after the overt words; "
        "canonical ∅ propagated to original S and a child M",
    )

    word = next(
        (candidate for candidate in sentence.findall("W")
         if candidate.get("id") == "14_S_8_W10"),
        None,
    )
    if word is None:
        raise AssertionError("14_S_8_W10 is missing")
    if not any("∅" in ((_tier(morph, "original").text or ""))
               for morph in word.findall("M")
               if _tier(morph, "original") is not None):
        morph = etree.Element("M", id="14_S_8_W10M1")
        etree.SubElement(morph, "FORM", kindOf="original").text = "∅"
        etree.SubElement(morph, "FORM", kindOf="standard").text = "∅"
        morph.tail = word[-1].tail if len(word) else None
        word.append(morph)
    _remove_phon(sentence)
    return True


def _canonicalize_kanakanavu(sentence):
    changed = False
    for form in sentence.xpath(".//FORM"):
        value = form.text or ""
        canonical = value.replace("Ø", "∅").replace("ø", "∅")
        if canonical != value:
            form.text = canonical
            changed = True
    standard = _tier(sentence, "standard")
    if standard is not None and "∅" in (standard.text or ""):
        standard.text = (standard.text or "").replace("∅", "")
        changed = True
    if changed:
        original = _tier(sentence, "original")
        _append_note(
            original,
            "source U+00D8 null canonicalized to U+2205 ∅; standard S omits "
            "the null unit while W/M retain it",
        )
        _remove_phon(sentence)
    return changed


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, dry_run, stats):
    original_bytes = Path(path).read_bytes()
    tree = etree.parse(path)
    if serialize(tree) != original_bytes:
        stats["file skipped: round-trip guard"] += 1
        return False
    modified = False
    normalized_path = str(path).replace("\\", "/")
    for sentence in tree.getroot().iter("S"):
        sid = sentence.get("id")
        if (normalized_path.endswith("Grammar/Sakizaya/Sakizaya.xml")
                and sid in SAKIZAYA_PREFIX_NULL
                and _prefix_null(sentence)):
            stats["Sakizaya source nulls propagated"] += 1
            modified = True
        elif (normalized_path.endswith("Grammar/Kanakanavu/Kanakanavu.xml")
              and sid == "14_S_8"
              and _append_sentence_null(sentence)):
            stats["Kanakanavu null head repaired"] += 1
            modified = True
        elif (normalized_path.endswith("Sentences/Kanakanavu/Kanakanavu.xml")
              and sid in KANAKANAVU_CANONICALIZE
              and _canonicalize_kanakanavu(sentence)):
            stats["Kanakanavu U+00D8 nulls canonicalized"] += 1
            modified = True

    for form in tree.xpath(".//FORM"):
        if form.text and ("Ø" in form.text or "ø" in form.text):
            raise AssertionError(
                f"noncanonical null remains in {path}: {form.text!r}"
            )

    if modified and not dry_run:
        Path(path).write_bytes(serialize(tree))
    return modified


def main():
    corpus = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml_dir", default=str(corpus / "XML"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    stats = collections.Counter()
    files = 0
    for directory, _, filenames in os.walk(args.xml_dir):
        for filename in sorted(filenames):
            if not filename.endswith(".xml"):
                continue
            path = os.path.join(directory, filename)
            if process_file(path, args.dry_run, stats):
                files += 1
                print(f"  modified: {Path(path).relative_to(args.xml_dir)}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for label, count in stats.most_common():
        print(f"  {count:5d}  {label}")


if __name__ == "__main__":
    main()
