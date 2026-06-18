#!/usr/bin/env python3
"""Capitalize the reduplication gloss 'red' -> 'RED' (a glossing abbreviation).

In this corpus an M-level TRANSL of exactly 'red' is always the REDUPLICATION
marker, not the colour word: an analysis of all 1170 such glosses found every
one to be a reduplicant (its FORM copies a sister morpheme), with no colour
'red'. The source .docx capitalizes glossing abbreviations; the XML lost that.
This restores it for reduplication.

Safety: only M-level TRANSL whose text is exactly 'red' are changed. If any
'red' TRANSL is found at W or S level (a possible colour translation), it is
reported and left untouched, and nothing is written for that file.

Edit is targeted text replacement (minimal diff); each file is re-parsed to
confirm the count of M-level 'red' dropped to zero and 'RED' rose by the same.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lxml import etree


def red_transls(root):
    """(n_m_level, non_m_locations) for TRANSL elements whose text == 'red'."""
    n_m, non_m = 0, []
    for t in root.iter("TRANSL"):
        if (t.text or "").strip() == "red":
            parent = t.getparent()
            if parent is not None and parent.tag == "M":
                n_m += 1
            else:
                non_m.append(parent.tag if parent is not None else "?")
    return n_m, non_m


def process(path: Path, dry_run: bool):
    text = path.read_text(encoding="utf-8")
    root = etree.fromstring(text.encode("utf-8"))
    n_m, non_m = red_transls(root)
    if non_m:
        print(f"  SKIP {path.name}: 'red' TRANSL at non-M level {non_m} -- left untouched")
        return 0
    if n_m == 0:
        return 0
    new = text.replace('<TRANSL xml:lang="eng">red</TRANSL>',
                        '<TRANSL xml:lang="eng">RED</TRANSL>')
    after = etree.fromstring(new.encode("utf-8"))
    n_m_after, _ = red_transls(after)
    n_red_caps = sum(1 for t in after.iter("TRANSL")
                     if (t.text or "").strip() == "RED"
                     and t.getparent() is not None and t.getparent().tag == "M")
    if n_m_after != 0:
        raise AssertionError(f"{path}: {n_m_after} M-level 'red' remain after edit")
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    return n_m


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", type=Path,
                    default=Path(__file__).resolve().parent.parent / "XML")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(args.xml_dir.glob("*.xml"))
    total = changed = 0
    for path in files:
        n = process(path, args.dry_run)
        if n:
            changed += 1
            total += n
    verb = "would capitalize" if args.dry_run else "capitalized"
    print(f"\n{verb} {total} M-level 'red' -> 'RED' across {changed} of {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
