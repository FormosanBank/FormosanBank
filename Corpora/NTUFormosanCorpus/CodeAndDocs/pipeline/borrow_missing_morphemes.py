#!/usr/bin/env python3
"""Give a word with NO morphemes the analysis a duplicate of it already carries.

The corpus's own borrow_segmentation.py repairs words that hold *empty-form* <M>
shells -- the residue repair_empty_morphemes.py leaves behind. This build never
creates those shells, so that script finds nothing. The condition this build
actually has is a word with no <M> at all: either the source never segmented it,
or the withdrawal step just took its morpheme tier away.

Run AFTER the withdrawal and BEFORE mirroring. The withdrawal is what creates
most of the candidates, and a borrowed analysis is real data, so it should win
over the flat one-M-per-word mirror that would otherwise stand in.

A donor must agree exactly: same word form, exactly one distinct segmentation
across the whole corpus, every donor morpheme glossed, and the donor morphemes
must recombine to the word. Anything less is skipped, never guessed.

    python borrow_missing_morphemes.py --xml_dir <dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import re
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

MARKERS = re.compile(r"[-=<>]")


def form_text(el) -> str:
    node = el.find("FORM[@kindOf='original']")
    if node is None:
        node = el.find("FORM")
    return "".join(node.itertext()).strip() if node is not None else ""


def glossed(m) -> bool:
    return any((t.text or "").strip() for t in m.findall("TRANSL"))


def bare(text: str) -> str:
    return MARKERS.sub("", text or "").strip()


def collect_donors(paths: list) -> dict:
    """form -> {segmentation tuple: representative <M> list}, over the corpus."""
    donors: dict = defaultdict(dict)
    for path in paths:
        for w in etree.parse(str(path)).getroot().iter("W"):
            ms = w.findall("M")
            if not ms:
                continue
            form = form_text(w)
            if not form:
                continue
            key = tuple(form_text(m) for m in ms)
            if not all(key) or not all(glossed(m) for m in ms):
                continue                      # an incomplete donor is no donor
            donors[form].setdefault(key, [copy.deepcopy(m) for m in ms])
    return donors


def borrow(w, donors: dict, stats: Counter) -> bool:
    if w.findall("M"):
        return False
    form = form_text(w)
    if not form:
        return False
    if not MARKERS.search(form):
        stats["skip: monomorphemic (mirror is correct)"] += 1
        return False
    cands = donors.get(form)
    if not cands:
        stats["skip: no donor anywhere in the corpus"] += 1
        return False
    if len(cands) > 1:
        stats["skip: donor ambiguous (>1 segmentation)"] += 1
        return False
    key, template = next(iter(cands.items()))
    if bare("".join(key)) != bare(form):
        stats["skip: donor morphemes do not recombine to the word"] += 1
        return False
    for j, m in enumerate(template):
        clone = copy.deepcopy(m)
        clone.set("id", f"{w.get('id')}M{j}")
        w.append(clone)
    stats["words given a borrowed analysis"] += 1
    stats["  morphemes added"] += len(template)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    paths = sorted(args.xml_dir.rglob("*.xml"))
    donors = collect_donors(paths)
    stats, files = Counter(), 0
    for path in paths:
        tree = etree.parse(str(path))
        changed = False
        for w in tree.getroot().iter("W"):
            changed |= borrow(w, donors, stats)
        if changed and not args.dry_run:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
            files += 1
    print(f"files modified: {files}   (donor forms: {len(donors)})")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
