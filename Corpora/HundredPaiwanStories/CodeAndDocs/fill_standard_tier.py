#!/usr/bin/env python3
"""Add a standard FORM to <M> elements that have an original FORM but no standard.

The morphemes created by split_infix_morphemes.py (and other hand-repaired Ms)
carry only FORM kindOf="original" and TRANSL. This fills their standard FORM by
applying the Paiwan_Ferrell_113.tsv orthography mappings directly to each new
morpheme's original FORM.

Why not just run QC/utilities/standardize.py? On the *published* corpus that is
unsafe: standardize.py re-derives EVERY standard form and its TSV maps '?' -> ''',
which reconflates sentence-final question-mark punctuation with the glottal stop.
In the dev-repo build that is undone afterward by fix_ferrell.py, but that script
is hardcoded to the dev path and does not run here. Applying the TSV to only the
new morphemes avoids the problem entirely — morpheme FORMs never carry question-
mark punctuation, so '?' in an M is always a glottal stop and '? -> '' is correct.

Targeted text insertion (additions only); each file is re-parsed to confirm the
filled Ms now have a standard FORM and the file still parses.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lxml import etree

# Paiwan_Ferrell_113.tsv (original -> standard)
TSV = [("ts", "c"), ("Ts", "C"), ("?", "'"),
       ("ḍ", "dr"), ("Ḍ", "dr"), ("ɫ", "lj"), ("Ɫ", "Lj")]


def stdize(s: str) -> str:
    for a, b in TSV:
        s = s.replace(a, b)
    return s


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def process(path: Path, dry_run: bool) -> int:
    root = etree.parse(str(path)).getroot()
    targets = []
    for m in root.iter("M"):
        forms = m.findall("FORM")
        of = next((f for f in forms if f.get("kindOf") in (None, "original")), None)
        if of is not None and not any(f.get("kindOf") == "standard" for f in forms):
            targets.append((m.get("id"), of.text or ""))
    if not targets:
        return 0
    if dry_run:
        return len(targets)
    text = path.read_text(encoding="utf-8")
    for mid, otext in targets:
        pat = re.compile(
            r'(<M id="' + re.escape(mid) + r'"[^>]*>.*?\n)([ \t]*)'
            r'(<FORM kindOf="original">' + re.escape(esc(otext)) + r'</FORM>\n)',
            re.DOTALL)
        def repl(mm):
            ind = mm.group(2)
            return (mm.group(1) + ind + mm.group(3)
                    + f'{ind}<FORM kindOf="standard">{esc(stdize(otext))}</FORM>\n')
        text, n = pat.subn(repl, text, count=1)
        if n != 1:
            raise AssertionError(f"{path}: could not insert standard for {mid}")
    chk = etree.fromstring(text.encode("utf-8"))
    byid = {m.get("id"): m for m in chk.iter("M")}
    for mid, _ in targets:
        if not any(f.get("kindOf") == "standard" for f in byid[mid].findall("FORM")):
            raise AssertionError(f"{path}: {mid} still missing standard FORM")
    path.write_text(text, encoding="utf-8")
    return len(targets)


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
    verb = "would fill" if args.dry_run else "filled"
    print(f"{verb} standard FORM for {total} Ms across {changed} of {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
