#!/usr/bin/env python3
"""Make the M tier per-sentence consistent (POL-023, per-sentence reading).

The blog parses *some* sentences morphologically and simply does not parse
others. The parser, however, always emits one M per W: for an unparsed
sentence that M is a bare mirror of its W FORM, which adds no information
and — worse — asserts an analysis Yedda never made.

Maintainer's ruling (2026-08-12), applied here per sentence rather than per
file:

* a sentence that carries **some** morphological parsing must give **every**
  one of its W elements at least one M (a single M there reads
  "analyzed as monomorphemic");
* a sentence with **no** morphological parsing carries **no** M at all.

Criterion for "carries some morphological parsing" (both clauses; either
one is enough):

1. some W in the sentence has two or more M children, or
2. some M's FORM differs from its parent W's FORM (an infix split such as
   ``l<em>angeda`` -> ``l-angeda`` / ``-em-`` would satisfy this even if it
   somehow produced a single M).

Anything else is an all-single-M mirror tier, i.e. no analysis.

Run after apply_manual_edits.py (so the split sentences are covered too) and
before standardize/add_phonology. Idempotent: a second run reports 0/0.

Usage:
    fix_m_tier.py --corpora_path <dir> [--formosanbank_root <dir>]
"""
from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def form_text(elem) -> str:
    form = elem.find("FORM")
    return (form.text or "") if form is not None else ""


def has_parsing(sentence) -> bool:
    for w in sentence.findall("W"):
        ms = w.findall("M")
        if len(ms) >= 2:
            return True
        if any(form_text(m) != form_text(w) for m in ms):
            return True
    return False


def fix_file(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    added = removed = 0
    gained = stripped = conforming = 0
    for s in root.iter("S"):
        ws = s.findall("W")
        if not ws:
            continue
        if has_parsing(s):
            missing = [w for w in ws if not w.findall("M")]
            for w in missing:
                m = ET.SubElement(w, "M")
                m.set("id", f"{w.get('id')}M1")
                form = ET.SubElement(m, "FORM")
                form.set("kindOf", "original")
                form.text = form_text(w)
                added += 1
            gained += bool(missing)
            conforming += not missing
        else:
            dropped = 0
            for w in ws:
                for m in w.findall("M"):
                    w.remove(m)
                    dropped += 1
            removed += dropped
            stripped += bool(dropped)
            conforming += not dropped
    return tree, root, added, removed, gained, stripped, conforming


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora_path", required=True,
                    help="directory holding the XML to fix (searched recursively)")
    ap.add_argument("--formosanbank_root",
                    help="FormosanBank checkout to take the shared pretty-printer from "
                         "(default: inferred from this script's location)")
    args = ap.parse_args()

    root_dir = Path(args.formosanbank_root) if args.formosanbank_root \
        else Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(root_dir))
    from QC.utilities._prettify import prettify  # noqa: E402

    totals = [0, 0, 0, 0, 0]
    for path in sorted(Path(args.corpora_path).rglob("*.xml")):
        tree, root, added, removed, gained, stripped, conforming = fix_file(path)
        if added or removed:
            path.write_text(prettify(root), encoding="utf-8")
        totals = [a + b for a, b in
                  zip(totals, (added, removed, gained, stripped, conforming))]
        print(f"{path.name}: +{added} M added, -{removed} M removed "
              f"({gained} sentences gained an M tier, {stripped} had theirs removed, "
              f"{conforming} already conforming)")
    added, removed, gained, stripped, conforming = totals
    print(f"M tier: +{added} / -{removed}; sentences: {gained} gained, "
          f"{stripped} stripped, {conforming} already conforming")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
