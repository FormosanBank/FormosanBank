#!/usr/bin/env python3
"""Among identical entries, keep the one that carries the etymology.

Blust lists every derived form twice: once as a numbered sub-entry under its
root, once as an alphabetical index entry in its own place. The two are
identical in FORM and gloss, so QC/cleaning/remove_duplicate_sentences.py will
remove one - but it keeps the first by (file, S id), and because the dictionary
is alphabetical an index entry may be printed before or after its root.

That choice is free except in one respect: the root's entry carries the
etymology (`Etymology: (PAN *aCay 'die; death')`) and the index entry does not.
38 pairs in the book differ that way. This runs before the remover and deletes,
within each group of identical FORM+gloss, any S whose FORM/@notes lacks an
etymology that a sibling has - leaving the remover a set of interchangeable
copies, so its own keep-rule cannot lose anything (maintainer, 2026-09-11).

Corpus-local on purpose: "prefer the one with an etymology" is a fact about this
book's layout, not a general rule about duplicates.
"""
from __future__ import annotations

import argparse
import collections
from pathlib import Path
from xml.etree import ElementTree as ET

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _key(sentence: ET.Element) -> tuple:
    form = sentence.find('FORM[@kindOf="standard"]')
    if form is None or not (form.text or "").strip():
        form = sentence.find('FORM[@kindOf="original"]')
    text = " ".join((form.text or "").split()) if form is not None else ""
    glosses = tuple(sorted(
        ((t.get(XML_LANG) or "").strip().lower(), " ".join((t.text or "").split()))
        for t in sentence.findall("TRANSL")
    ))
    return (text, glosses)


def _has_etymology(sentence: ET.Element) -> bool:
    return any(
        "Etymology:" in (f.get("notes") or "")
        for f in sentence.findall("FORM")
    )


def prune(directory: Path) -> int:
    trees = {path: ET.parse(path) for path in sorted(directory.glob("*.xml"))}
    groups: dict[tuple, list] = collections.defaultdict(list)
    for path, tree in trees.items():
        root = tree.getroot()
        for sentence in root.findall("S"):
            groups[_key(sentence)].append((path, root, sentence))

    doomed: dict[Path, list] = collections.defaultdict(list)
    for members in groups.values():
        if len(members) < 2:
            continue
        if not any(_has_etymology(s) for _p, _r, s in members):
            continue
        for path, root, sentence in members:
            if not _has_etymology(sentence):
                doomed[path].append((root, sentence))

    removed = 0
    for path, victims in doomed.items():
        for root, sentence in victims:
            root.remove(sentence)
            removed += 1
        trees[path].write(path, encoding="utf-8", xml_declaration=True)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    removed = prune(args.path)
    print(f"prefer_the_etymology: removed {removed} entries that lacked one")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
