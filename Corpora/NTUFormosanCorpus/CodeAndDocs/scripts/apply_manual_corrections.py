#!/usr/bin/env python3
"""apply_manual_corrections.py

Apply a small table of hand-verified one-off corrections to the
published XML. Each entry names the file, the S id, the element to fix,
and an exact old->new text substitution; an entry that no longer
matches anything is reported (so silent drift is impossible) but does
not fail the run.

Current corrections
-------------------
1. Sentences/Bunun 59_S_12, zho TRANSL: the source has a stray ``<``
   where an opening parenthesis was meant
   (``... < 敬禮請原諒), ...`` -> ``... (敬禮請原諒), ...``).
   The parenthetical content itself is left in place, consistent with
   how parentheticals in TRANSL are handled corpus-wide. (This typo is
   also why validate_text.py's V132 counts were imbalanced: 1129 ``<``
   vs 1128 ``>``.)

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent: applied
corrections simply stop matching.

Usage
-----
    python apply_manual_corrections.py            # corpus XML/ by default
    python apply_manual_corrections.py --dry-run
"""

import argparse
import os
from pathlib import Path

import lxml.etree as etree

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"

# (relative file, S id, element tag, xml:lang or None, old substring, new substring)
CORRECTIONS = [
    ("Sentences/Bunun/Bunun.xml", "59_S_12", "TRANSL", "zho",
     "< 敬禮請原諒)", "(敬禮請原諒)"),
]


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    by_file = {}
    for entry in CORRECTIONS:
        by_file.setdefault(entry[0], []).append(entry)

    applied = stale = 0
    for rel, entries in by_file.items():
        path = os.path.join(args.xml_dir, rel)
        if not os.path.exists(path):
            print(f"  MISSING FILE: {rel}")
            stale += len(entries)
            continue
        original = open(path, "rb").read()
        tree = etree.parse(path)
        if serialize(tree) != original:
            print(f"  SKIP (round-trip guard): {rel}")
            continue
        root = tree.getroot()
        sindex = {s.get("id"): s for s in root.iter("S")}
        modified = False
        for _, sid, tag, lang, old, new in entries:
            s = sindex.get(sid)
            target = None
            if s is not None:
                for el in s.iter(tag):
                    el_lang = el.get(_XLANG) or el.get("lang")
                    if lang is not None and el_lang != lang:
                        continue
                    if old in (el.text or ""):
                        target = el
                        break
            if target is None:
                stale += 1
                print(f"  no match (already applied or drifted): "
                      f"{rel} {sid} {tag} {old!r}")
                continue
            target.text = target.text.replace(old, new)
            applied += 1
            modified = True
            print(f"  applied: {rel} {sid} {tag}: {old!r} -> {new!r}")
        if modified and not args.dry_run:
            with open(path, "wb") as f:
                f.write(serialize(tree))
    verb = "would be " if args.dry_run else ""
    print(f"\ncorrections {verb}applied: {applied} (no-match: {stale})")


if __name__ == "__main__":
    main()
