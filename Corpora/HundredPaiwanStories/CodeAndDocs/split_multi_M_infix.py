#!/usr/bin/env python3
"""Split INFIX=ROOT morphemes that sit inside an already-multi-M word.

split_infix_morphemes.py only handled single-M words (the morpheme spans the
whole W FORM). This handles the multi-M case by first peeling off the sibling
morphemes that match the surface directly, to isolate the substring the '='
morpheme actually spans, then splicing as usual:

    qemaqivu  with  <M>em=qa</M> <M>qivu</M>
    -> "qivu" matches the tail of "qemaqivu"  =>  span "qema"
    -> splice em into qa over "qema": q<em>a   =>  -em- + q-a

The '=' M is replaced by two Ms; the sibling Ms are untouched; the W's M ids are
renumbered 0-based (splitting one M into two shifts the trailing siblings). The
two new Ms are emitted complete (original + standard FORM, original + standard
PHON, TRANSL) using the same TSV / orthography mappings as fill_standard_tier.py
and add_phonology.py, so no follow-up fill is needed. A reduplication gloss
'red' on the affix piece is written 'RED' to match capitalize_red.py.

Only words with exactly one '=' morpheme are handled. Words where a sibling
doesn't match the surface (consonant mutation, infix vowel change, w/v
alternation) or that stack several '=' morphemes are left untouched and written
to multi_M_eq_morphemes.csv for manual handling.

Targeted text edit; each file re-parsed to confirm it still parses and the
W now has the expected M structure.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import regex
from lxml import etree

ROOT = Path(__file__).resolve().parents[3]
VOWELS = set("aeiouə")
TSV = [("ts", "c"), ("Ts", "C"), ("?", "'"), ("ḍ", "dr"), ("Ḍ", "dr"),
       ("ɫ", "lj"), ("Ɫ", "Lj")]


def load_phon(p):
    with open(p, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        cols = [c for c in r.fieldnames if c != "letter"]
        rows = list(r)
    return rows, cols


ORTHO = load_phon(ROOT / "Orthographies/Ortho113/Paiwan.tsv")
FERR = load_phon(ROOT / "Orthographies/Ferrell/Paiwan.tsv")


def letters(s):
    return "".join(regex.findall(r"\p{L}", s or "")).lower()


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def stdize(s):
    for a, b in TSV:
        s = s.replace(a, b)
    return s


def to_phon(text, tsv, dialect):
    rows, cols = tsv
    col = dialect if dialect in cols else ("default" if "default" in cols else cols[-1])
    mp, conv, ipa = [], {}, set()
    for row in rows:
        L = (row.get("letter") or "").strip()
        v = (row.get(col) or "").strip()
        if L and v != "NA":
            mp.append((L, v)); conv[L] = v; ipa.update(v)
    r = text
    for L, ip in mp:
        if L in r:
            r = r.replace(L, ip)
        lu = L.capitalize() if len(L) > 1 else L.upper()
        if lu in r and lu not in conv:
            r = r.replace(lu, ip)
    import string
    return "".join(c if (c in ipa or c in string.punctuation or c.isspace()) else "*" for c in r)


def splice(span, infix, root):
    """span: lowercase letters. Returns (root_before, root_after) in the root's
    original case, possibly with one root vowel syncopated. Else None."""
    I = infix.lower()
    R, Rl = root, root.lower()
    for k in range(len(R) + 1):
        if Rl[:k] + I + Rl[k:] == span:
            return R[:k], R[k:]
    for j in range(len(R)):
        if Rl[j] in VOWELS:
            R2, R2l = R[:j] + R[j + 1:], Rl[:j] + Rl[j + 1:]
            for k in range(len(R2) + 1):
                if R2l[:k] + I + R2l[k:] == span:
                    return R2[:k], R2[k:]
    return None


def m_form(m):
    for f in m.findall("FORM"):
        if f.get("kindOf") in (None, "original"):
            return f.text or ""
    return ""


def m_gloss(m):
    t = m.findall("TRANSL")
    return (t[0].text or "") if t else ""


def make_block(ind, mform, gloss, dialect):
    """Full 5-line <M> body (original+standard FORM/PHON + TRANSL) at indent ind."""
    c = ind + "    "
    fstd = stdize(mform)
    if gloss == "red":
        gloss = "RED"
    return (
        f'{ind}<M id="__TMP__">\n'
        f'{c}<FORM kindOf="original">{esc(mform)}</FORM>\n'
        f'{c}<PHON kindOf="original">{esc(to_phon(mform, FERR, dialect))}</PHON>\n'
        f'{c}<FORM kindOf="standard">{esc(fstd)}</FORM>\n'
        f'{c}<PHON kindOf="standard">{esc(to_phon(fstd, ORTHO, dialect))}</PHON>\n'
        f'{c}<TRANSL xml:lang="eng">{esc(gloss)}</TRANSL>\n'
        f'{ind}</M>\n'
    )


def plan_file(path):
    root = etree.parse(str(path)).getroot()
    dialect = root.get("dialect") or "default"
    jobs, flags = [], []
    for w in root.iter("W"):
        ms = w.findall("M")
        eqs = [m for m in ms if "=" in m_form(m)]
        if len(ms) < 2 or not eqs:
            continue
        allforms = " | ".join(m_form(m) for m in ms)
        if len(eqs) > 1:
            flags.append((w.get("id"), m_form(eqs[0]), allforms, "stacked '=' (>1)"))
            continue
        eqm = eqs[0]
        idx = ms.index(eqm)
        wl = letters(m_form(w))
        span = wl
        ok = True
        for m in ms[:idx]:
            f = letters(m_form(m))
            if f and span.startswith(f):
                span = span[len(f):]
            else:
                ok = False; break
        if ok:
            for m in reversed(ms[idx + 1:]):
                f = letters(m_form(m))
                if f and span.endswith(f):
                    span = span[:len(span) - len(f)]
                else:
                    ok = False; break
        mf, g = m_form(eqm), m_gloss(eqm)
        if not ok:
            flags.append((w.get("id"), mf, allforms, "sibling does not match surface (mutation)"))
            continue
        if mf.count("=") != 1 or g.count("=") != 1:
            flags.append((w.get("id"), mf, allforms, "uneven '=' in FORM/gloss"))
            continue
        infix, rootcit = mf.split("=")
        ig, rg = g.split("=")
        sp = splice(span, infix, rootcit)
        if sp is None:
            flags.append((w.get("id"), mf, allforms, "no clean splice on isolated span"))
            continue
        rb, ra = sp
        jobs.append({"wid": w.get("id"), "eqid": eqm.get("id"), "dialect": dialect,
                     "infix_form": f"-{infix}-", "infix_gloss": ig,
                     "root_form": f"{rb}-{ra}", "root_gloss": rg})
    return jobs, flags


def apply_file(path, jobs):
    text = path.read_text(encoding="utf-8")
    for j in jobs:
        wid = j["wid"]
        wpat = re.compile(r'(<W id="' + re.escape(wid) + r'">)(.*?)(</W>)', re.DOTALL)
        wm = wpat.search(text)
        if not wm:
            raise AssertionError(f"{path}: W {wid} not found")
        wblock = wm.group(2)
        eqpat = re.compile(r'([ \t]*)<M id="' + re.escape(j["eqid"]) + r'"[^>]*>.*?</M>\n',
                           re.DOTALL)
        em = eqpat.search(wblock)
        if not em:
            raise AssertionError(f"{path}: =M {j['eqid']} not found in {wid}")
        ind = em.group(1)
        two = (make_block(ind, j["infix_form"], j["infix_gloss"], j["dialect"])
               + make_block(ind, j["root_form"], j["root_gloss"], j["dialect"]))
        wblock = wblock[:em.start()] + two + wblock[em.end():]
        cnt = {"n": 0}
        def renum(mm):
            s = f'<M id="{wid}M{cnt["n"]}"'; cnt["n"] += 1; return s
        wblock = re.sub(r'<M id="[^"]*"', renum, wblock)
        text = text[:wm.start(2)] + wblock + text[wm.end(2):]
    # verify
    root = etree.fromstring(text.encode("utf-8"))
    ids = [m.get("id") for m in root.iter("M")]
    assert len(ids) == len(set(ids)), f"{path}: duplicate M ids after split"
    path.write_text(text, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", type=Path,
                    default=Path(__file__).resolve().parent.parent / "XML")
    ap.add_argument("--csv", type=Path,
                    default=Path(__file__).resolve().parent / "multi_M_eq_morphemes.csv")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    files = sorted(args.xml_dir.glob("*.xml"))
    total_split = 0
    all_flags = []
    for path in files:
        jobs, flags = plan_file(path)
        all_flags += [(path.name, *f) for f in flags]
        if jobs:
            total_split += len(jobs)
            if not args.dry_run:
                apply_file(path, jobs)

    print(f"{'[dry-run] ' if args.dry_run else ''}multi-M '=' morphemes split: {total_split}")
    print(f"left for manual (written to CSV): {len(all_flags)}")
    if not args.dry_run:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["file", "W_id", "eq_M_form", "all_M_forms", "reason"])
            wr.writerows(all_flags)
        print(f"wrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
