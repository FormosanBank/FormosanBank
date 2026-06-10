#!/usr/bin/env python3
"""Add PHON (IPA) to <M> elements that have a FORM but no sister PHON.

Mirrors fill_standard_tier.py, but for the phonological tier. For each <M> that
has an original/standard FORM but lacks the matching PHON, this generates the
PHON by applying the same orthography->IPA character mappings add_phonology.py
uses: original FORM via Orthographies/Ferrell/Paiwan.tsv, standard FORM via
Orthographies/Ortho113/Paiwan.tsv, choosing the dialect column from the TEXT's
`dialect` attribute. Unknown characters become '*' (same as add_phonology.py).

Why not run add_phonology.py over the published XML/? Same reason as
fill_standard_tier.py: it re-derives every form and reformats every file, and
carries the question-mark/glottal-stop hazard. Applying the mapping to only the
morphemes that lack PHON is additions-only and leaves existing PHON untouched.

The replication was checked by reproducing existing PHON for 32832/32833 M
(100%). Targeted text insertion; each file is re-parsed to confirm it parses
and the filled Ms now carry the expected PHON.
"""
from __future__ import annotations

import argparse
import csv
import re
import string
from pathlib import Path

from lxml import etree

REPO = Path(__file__).resolve().parents[3]


def load_tsv(p):
    with open(p, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        cols = [c for c in r.fieldnames if c != "letter"]
        return list(r), cols


ORTHO = load_tsv(REPO / "Orthographies/Ortho113/Paiwan.tsv")   # standard -> IPA
FERR = load_tsv(REPO / "Orthographies/Ferrell/Paiwan.tsv")     # original -> IPA


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def to_phon(text, tsv, dialect):
    rows, cols = tsv
    col = dialect if dialect in cols else ("default" if "default" in cols else cols[-1])
    mp, conv, ipa = [], {}, set()
    for row in rows:
        L = (row.get("letter") or "").strip()
        v = (row.get(col) or "").strip()
        if L and v != "NA":
            mp.append((L, v)); conv[L] = v; ipa.update(v)
    r = text or ""
    for L, ip in mp:
        if L in r:
            r = r.replace(L, ip)
        lu = L.capitalize() if len(L) > 1 else L.upper()
        if lu in r and lu not in conv:
            r = r.replace(lu, ip)
    return "".join(c if (c in ipa or c in string.punctuation or c.isspace()) else "*"
                   for c in r)


def process(path: Path, dry_run: bool) -> int:
    root = etree.parse(str(path)).getroot()
    dialect = root.get("dialect") or "default"
    jobs = []  # (m_id, kind, form_text, phon_text)
    for m in root.iter("M"):
        forms = {f.get("kindOf"): (f.text or "") for f in m.findall("FORM")}
        phons = {p.get("kindOf") for p in m.findall("PHON")}
        if "original" in forms and "original" not in phons:
            jobs.append((m.get("id"), "original", forms["original"],
                         to_phon(forms["original"], FERR, dialect)))
        if "standard" in forms and "standard" not in phons:
            jobs.append((m.get("id"), "standard", forms["standard"],
                         to_phon(forms["standard"], ORTHO, dialect)))
    if not jobs:
        return 0
    if dry_run:
        return len(jobs)
    text = path.read_text(encoding="utf-8")
    for mid, kind, ftext, ptext in jobs:
        pat = re.compile(
            r'(<M id="' + re.escape(mid) + r'"[^>]*>.*?\n)([ \t]*)'
            r'(<FORM kindOf="' + kind + r'">' + re.escape(esc(ftext)) + r'</FORM>\n)',
            re.DOTALL)
        def repl(mm):
            ind = mm.group(2)
            return (mm.group(1) + ind + mm.group(3)
                    + f'{ind}<PHON kindOf="{kind}">{esc(ptext)}</PHON>\n')
        text, n = pat.subn(repl, text, count=1)
        if n != 1:
            raise AssertionError(f"{path}: could not insert {kind} PHON for {mid}")
    chk = etree.fromstring(text.encode("utf-8"))
    byid = {m.get("id"): m for m in chk.iter("M")}
    for mid, kind, _, _ in jobs:
        if not any(p.get("kindOf") == kind for p in byid[mid].findall("PHON")):
            raise AssertionError(f"{path}: {mid}/{kind} PHON still missing")
    path.write_text(text, encoding="utf-8")
    return len(jobs)


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
    verb = "would add" if args.dry_run else "added"
    print(f"{verb} {total} PHON elements across {changed} of {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
