#!/usr/bin/env python3
"""Split a free translation written as two renderings, 'A / B', into a translation
and an alternative translation (ruling 2026-10-16, Bunun 63.json duplicates round 2,
"split all 48 the same way").

NTU sometimes writes two English or Chinese renderings of a sentence on one line,
separated by ' / ' ("I have three younger brothers. / There are my three younger
brothers."). The first stays the sentence's translation; each further rendering
becomes a sibling TRANSL with ver="alt", the form NTU's other alternative
translations take. Only sentence-level translations that are not already
alternatives are split, and only on ' / ' with spaces on both sides, so a slash
inside a phrase ('fun/happiness') is left alone.

usage: split_two_renderings.py --xml_dir <dir>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lxml import etree

XL = "{http://www.w3.org/XML/1998/namespace}lang"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    args = ap.parse_args(argv)
    split = 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = False
        for t in list(tree.getroot().iter("TRANSL")):
            if t.getparent().tag != "S" or t.get("ver") or " / " not in (t.text or ""):
                continue
            first, *rest = [p.strip() for p in t.text.split(" / ") if p.strip()]
            if not rest:
                continue
            t.text = first
            anchor = t
            for r in rest:
                n = etree.Element("TRANSL")
                n.set(XL, t.get(XL))
                n.set("ver", "alt")
                n.text = r
                n.tail = t.tail
                anchor.addnext(n)
                anchor = n
            split += 1
            changed = True
        if changed:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
    print(f"translations split into two renderings: {split}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
