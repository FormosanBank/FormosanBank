#!/usr/bin/env python3
"""remove_null_symbols.py

Remove null-morpheme symbols from the *standard* tier at S and W level.

The Kanakanavu sentence subcorpus writes a null-morpheme placeholder
inside words (e.g. ``cinimʉ'ʉraku niarisinatʉ∅kee.``). This is
linguist's annotation, not pronounceable orthography, so it is kept in
the ``original`` tier but removed from the ``standard`` tier (the
project's cleaned common-orthography tier).

Scope and safety:
- Only ``FORM``/``PHON`` elements with ``kindOf="standard"`` that are
  direct children of S or W are touched. M-level null symbols are left
  alone deliberately: there the symbol constitutes a whole morpheme slot
  (e.g. ``ø-sitangah`` -> M1 ``ø`` + M2 ``sitangah``), and stripping it
  would create exactly the empty-FORM morphemes that
  ``repair_empty_morphemes.py`` exists to eliminate.
- An element is never emptied: if stripping the symbol would leave no
  text, the element is skipped and reported.
- By default only ``∅`` (U+2205) is removed. ``--chars`` can extend
  this (e.g. ``--chars "∅ø"``) once the status of other null symbols is
  settled.
- A file is rewritten only if its unmodified tree first re-serializes
  byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python remove_null_symbols.py            # corpus XML/ by default
    python remove_null_symbols.py --dry-run
"""

import argparse
import collections
import os
from pathlib import Path

import lxml.etree as etree


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, chars, dry_run=False):
    original = open(path, "rb").read()
    if not any(c.encode("utf-8") in original for c in chars):
        return 0, 0
    tree = etree.parse(path)
    if serialize(tree) != original:
        print(f"  SKIP (round-trip guard): {path}")
        return 0, 0
    root = tree.getroot()
    changed = skipped = 0
    for level in ("S", "W"):
        for el in root.iter(level):
            for child in el:
                if child.tag not in ("FORM", "PHON"):
                    continue
                if child.get("kindOf") != "standard":
                    continue
                text = child.text or ""
                if not any(c in text for c in chars):
                    continue
                new = text
                for c in chars:
                    new = new.replace(c, "")
                if not new.strip():
                    skipped += 1
                    print(f"  NOT emptied (kept as-is): {level} "
                          f"id={el.get('id')!r} {child.tag} text={text!r}")
                    continue
                child.text = new
                changed += 1
    if changed and not dry_run:
        with open(path, "wb") as f:
            f.write(serialize(tree))
    return changed, skipped


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--chars", default="∅",
                    help="Null symbols to remove from standard S/W tiers (default: ∅).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    total = collections.Counter()
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            ch, sk = process_file(os.path.join(dirpath, fn), list(args.chars),
                                  dry_run=args.dry_run)
            if ch or sk:
                print(f"  {fn}: {ch} element(s) cleaned, {sk} skipped")
            total["changed"] += ch
            total["skipped"] += sk
    verb = "would be " if args.dry_run else ""
    print(f"\nstandard-tier elements {verb}cleaned: {total['changed']}"
          f" (skipped to avoid emptying: {total['skipped']})")


if __name__ == "__main__":
    main()
