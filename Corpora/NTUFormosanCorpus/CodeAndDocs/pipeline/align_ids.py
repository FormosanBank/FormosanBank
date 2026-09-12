#!/usr/bin/env python3
"""Bring generated ids back into line with the published corpus. Runs LAST.

POL-037 wants an id to survive a rebuild, so a reference to a sentence keeps
resolving. Where this build names something differently from the published
corpus for no substantive reason, the published spelling wins.

Currently one rule:

* ``-opt1`` -> ``-opt``. ``resolve_inline_parentheticals`` numbers the readings
  it materialises, but with a single optional group there is only ever one
  extra reading, and the corpus publishes it as ``-opt`` (as
  ``split_optional_parentheticals`` already does). The rename is applied only
  when no ``-opt`` sibling already exists, so it can never collide, and only
  when no ``-opt2`` exists, so a genuinely numbered series is left alone.

Descendant ids embed the sentence id (``<sid>_W3``, ``<sid>_W3M0``), so they are
rewritten with it.

It runs last on purpose: renaming ids earlier would break every repair script
keyed on the id it was given.

    python align_ids.py --xml_dir <dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from lxml import etree

_OPT_N = re.compile(r"-opt(\d+)$")


def align(tree, stats: Counter) -> bool:
    root = tree.getroot()
    existing = {s.get("id") for s in root.iter("S")}
    changed = False
    for s in root.iter("S"):
        sid = s.get("id") or ""
        m = _OPT_N.search(sid)
        if not m or m.group(1) != "1":
            continue
        target = sid[: m.start()] + "-opt"
        if target in existing or f"{sid[: m.start()]}-opt2" in existing:
            stats["left alone (would collide, or a numbered series)"] += 1
            continue
        s.set("id", target)
        existing.discard(sid)
        existing.add(target)
        for el in s.iter():
            if el is s:
                continue
            eid = el.get("id")
            if eid and eid.startswith(sid):
                el.set("id", target + eid[len(sid):])
        stats["sentences renamed -opt1 -> -opt"] += 1
        changed = True
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    stats, files = Counter(), 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        if align(tree, stats) and not args.dry_run:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
            files += 1
    print(f"files modified: {files}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
