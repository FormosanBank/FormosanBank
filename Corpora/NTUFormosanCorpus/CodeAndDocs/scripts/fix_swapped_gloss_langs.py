#!/usr/bin/env python3
"""fix_swapped_gloss_langs.py

Swap eng/zho W- and M-level glosses in sentence stems whose source
files are zh-first.

Two Bunun sentence-subcorpus source files (``sentence/Bunun_Isbukun/
63.json`` and ``64.json``) order their gloss columns [wordform, zho,
eng] while the parser assumes [wordform, eng, zho] for non-Kanakanavu
languages; the published XML carried the two gloss languages inverted
for every W and M element in those stems (~16,400 glosses:
``eng="蜂蜜"``, ``zho="honey"``). Beyond those, ~300 isolated rows
across the corpus have the same per-row inversion. S-level free
translations were never affected (they come from the language-tagged
#e/#c source lines).

With ``--all`` the script sweeps every file and every stem; the strict
per-element gate makes this safe corpus-wide.

The swap is gated per element: the texts are exchanged only when the
eng-slot text contains CJK and the zho-slot text does not. This makes
the script idempotent (after the swap the condition no longer holds)
and leaves identical-text pairs (DM, TOP, PN...) and single-tier
elements untouched.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8).

Usage
-----
    python fix_swapped_gloss_langs.py            # Sentences/Bunun stems 63,64
    python fix_swapped_gloss_langs.py --dry-run
    python fix_swapped_gloss_langs.py --file <rel-path> --stems 63,64
"""

import argparse
import collections
import os
import re
from pathlib import Path

import lxml.etree as etree

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"
_CJK = re.compile(r"[一-鿿]")


def cjk(text):
    return bool(_CJK.search(text or ""))


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--file", default="Sentences/Bunun/Bunun.xml")
    ap.add_argument("--stems", default="63,64")
    ap.add_argument("--all", action="store_true",
                    help="Sweep every XML file and stem (per-element gate).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = collections.Counter()

    def process(path, stems):
        original = open(path, "rb").read()
        tree = etree.parse(path)
        if serialize(tree) != original:
            stats["file skipped: round-trip guard"] += 1
            return
        root = tree.getroot()
        swapped_here = 0
        for el in list(root.iter("W")) + list(root.iter("M")):
            eid = el.get("id") or ""
            if stems is not None and eid.split("_S_")[0] not in stems:
                continue
            eng = next((t for t in el.findall("TRANSL") if t.get(_XLANG) == "eng"), None)
            zho = next((t for t in el.findall("TRANSL") if t.get(_XLANG) == "zho"), None)
            if eng is None or zho is None:
                stats["single-tier element (left)"] += 1
                continue
            if cjk(eng.text) and not cjk(zho.text):
                eng.text, zho.text = zho.text, eng.text
                stats[f"swapped ({el.tag})"] += 1
                swapped_here += 1
            elif (eng.text or "") == (zho.text or ""):
                stats["identical pair (left)"] += 1
        if swapped_here and not args.dry_run:
            with open(path, "wb") as f:
                f.write(serialize(tree))
        if swapped_here:
            print(f"  {'would swap' if args.dry_run else 'swapped'} "
                  f"{swapped_here} in {os.path.basename(path)}")

    if args.all:
        for dirpath, _, filenames in os.walk(args.xml_dir):
            for fn in sorted(filenames):
                if fn.endswith(".xml"):
                    process(os.path.join(dirpath, fn), None)
    else:
        process(os.path.join(args.xml_dir, args.file),
                set(args.stems.split(",")))
    for k, v in stats.most_common():
        print(f"  {v:6d}  {k}")


if __name__ == "__main__":
    main()
