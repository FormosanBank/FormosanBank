#!/usr/bin/env python3
"""Split single-M morphemes that bundle an infix/reduplicant with a root via '='.

In this corpus the glosser left actor-focus/perfective infixes (and partial
reduplication) un-segmented, packed into one <M> as INFIX=ROOT / gloss=gloss,
using the CITATION form of the root (e.g. 'keman' -> <M>em=kan / af=eat</M>,
where the surface shows k<em>an). This script splits each such single-M word
into two <M> elements:

    M0  the infix/reduplicant, FORM '-em-'   (gloss e.g. 'af' / 'red')
    M1  the root,              FORM 'k-an'   ('-' marks the infix position)

The infix position (and hence the root's '-') is found by splicing the infix
into the citation root and matching the surface W FORM, allowing one root-vowel
syncope (qetsi -> q<em>tsi). Cases that don't splice cleanly -- consonant
mutation, stacked '=' (reduplication+infix+root), or an extra unglossed prefix
(sipatsatsay) -- are NOT touched and are listed for manual handling.

Per project decision, the two new <M> keep ONLY FORM(kindOf=original) and
TRANSL; PHON and the standard-tier FORM are dropped and regenerated later by
standardize.py / add_phonology.py.

Only single-M words are handled (the M's surface == the whole W FORM, so the
splice is well-defined). Multi-M words containing '=' are reported but left
alone (the '=' morpheme maps to an unknown substring of the word).

Edits are done as targeted text replacement (each M located by its unique id)
so the diff touches only the split blocks; every file is re-parsed afterward to
confirm it still parses and the new M structure is exactly as intended.

Usage:
    python split_infix_morphemes.py --dry-run     # preview, no writes
    python split_infix_morphemes.py               # apply + write flagged CSV
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import regex
from lxml import etree

XMLDIR_DEFAULT = Path(__file__).resolve().parent.parent / "XML"
VOWELS = set("aeiouə")


def letters(s: str) -> str:
    return "".join(regex.findall(r"\p{L}", s or "")).lower()


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def orig_form(node) -> str:
    for f in node.findall("FORM"):
        if f.get("kindOf") in (None, "original"):
            return f.text or ""
    return ""


def transl(node) -> str:
    t = node.findall("TRANSL")
    return (t[0].text or "") if t else ""


def splice(surface: str, infix: str, root: str):
    """Return (root_before, root_after) substrings of the (possibly syncopated)
    citation root, such that root_before + infix + root_after == surface
    (letters only). Try plain insertion, then one-root-vowel syncope. Else None.
    """
    s = letters(surface)
    I = infix.lower()
    R, Rl = root, root.lower()
    for k in range(len(R) + 1):
        if Rl[:k] + I + Rl[k:] == s:
            return R[:k], R[k:]
    for j in range(len(R)):
        if Rl[j] in VOWELS:
            R2, R2l = R[:j] + R[j + 1:], Rl[:j] + Rl[j + 1:]
            for k in range(len(R2) + 1):
                if R2l[:k] + I + R2l[k:] == s:
                    return R2[:k], R2[k:]
    return None


def plan_file(path: Path):
    """Return (splits, flags, n_multi_eq) for one file.
    splits: list of dicts with the data needed to rewrite each M.
    flags : list of (wid, mid, wform, mform, gloss, reason).
    """
    root = etree.parse(str(path)).getroot()
    splits, flags, multi_rows = [], [], []
    for w in root.iter("W"):
        ms = w.findall("M")
        eq_ms = [m for m in ms if "=" in orig_form(m)]
        if not eq_ms:
            continue
        if len(ms) != 1:
            for m in eq_ms:
                multi_rows.append((
                    w.get("id"), m.get("id"), orig_form(w),
                    " | ".join(orig_form(x) for x in ms),
                    orig_form(m), transl(m), len(ms),
                ))
            continue
        m = ms[0]
        mform, gloss = orig_form(m), transl(m)
        wform = orig_form(w)
        if mform.count("=") != 1 or gloss.count("=") != 1:
            flags.append((w.get("id"), m.get("id"), wform, mform, gloss,
                          "stacked/uneven '=' (FORM or gloss)"))
            continue
        infix, rootcit = mform.split("=")
        ig, rg = gloss.split("=")
        sp = splice(wform, infix, rootcit)
        if sp is None:
            flags.append((w.get("id"), m.get("id"), wform, mform, gloss,
                          "no clean splice (mutation / extra prefix)"))
            continue
        rb, ra = sp
        wid = w.get("id")
        splits.append({
            "mid": m.get("id"),
            "mid0": f"{wid}M0",
            "mid1": f"{wid}M1",
            "infix_form": f"-{infix}-",
            "infix_gloss": ig,
            "root_form": f"{rb}-{ra}",
            "root_gloss": rg,
            "wform": wform, "mform": mform,
        })
    return splits, flags, multi_rows


def apply_splits(path: Path, splits, dry_run: bool) -> None:
    text = path.read_text(encoding="utf-8")
    for sp in splits:
        pat = re.compile(
            r'(?P<ind>[ \t]*)<M id="' + re.escape(sp["mid"]) + r'"[^>]*>.*?</M>\n',
            re.DOTALL)
        mobj = pat.search(text)
        if mobj is None:
            raise AssertionError(f"{path}: could not locate M block {sp['mid']}")
        ind = mobj.group("ind")
        c = ind + "    "
        block = (
            f'{ind}<M id="{sp["mid0"]}">\n'
            f'{c}<FORM kindOf="original">{esc(sp["infix_form"])}</FORM>\n'
            f'{c}<TRANSL xml:lang="eng">{esc(sp["infix_gloss"])}</TRANSL>\n'
            f'{ind}</M>\n'
            f'{ind}<M id="{sp["mid1"]}">\n'
            f'{c}<FORM kindOf="original">{esc(sp["root_form"])}</FORM>\n'
            f'{c}<TRANSL xml:lang="eng">{esc(sp["root_gloss"])}</TRANSL>\n'
            f'{ind}</M>\n'
        )
        text, n = pat.subn(lambda _m: block, text, count=1)
        if n != 1:
            raise AssertionError(f"{path}: failed to replace {sp['mid']}")

    # verify
    root = etree.fromstring(text.encode("utf-8"))
    by_id = {m.get("id"): m for m in root.iter("M")}
    for sp in splits:
        for mid, ff, gg in ((sp["mid0"], sp["infix_form"], sp["infix_gloss"]),
                            (sp["mid1"], sp["root_form"], sp["root_gloss"])):
            m = by_id.get(mid)
            if m is None or orig_form(m) != ff or transl(m) != gg:
                raise AssertionError(f"{path}: verification failed for {mid}")
        if sp["mid"] not in (sp["mid0"], sp["mid1"]) and sp["mid"] in by_id:
            raise AssertionError(f"{path}: old M {sp['mid']} still present")
    if not dry_run:
        path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", type=Path, default=XMLDIR_DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--csv", type=Path,
                    default=Path(__file__).resolve().parent / "flagged_infix_splits.csv")
    ap.add_argument("--multi-csv", type=Path,
                    default=Path(__file__).resolve().parent / "multi_M_eq_morphemes.csv")
    args = ap.parse_args()

    files = sorted(args.xml_dir.glob("*.xml"))
    if not files:
        print(f"No .xml in {args.xml_dir}", file=sys.stderr)
        return 1

    all_flags, all_multi, total_splits = [], [], 0
    sample = []
    for path in files:
        splits, flags, multi_rows = plan_file(path)
        all_flags += [(path.name, *f) for f in flags]
        all_multi += [(path.name, *r) for r in multi_rows]
        if splits:
            apply_splits(path, splits, args.dry_run)
            total_splits += len(splits)
            for sp in splits[:0 if len(sample) >= 14 else 14]:
                sample.append((path.name, sp))

    print(f"single-M '=' words split into two Ms : {total_splits}")
    print(f"single-M '=' words FLAGGED (untouched): {len(all_flags)}")
    print(f"'=' morphemes inside MULTI-M words (out of scope, untouched): {len(all_multi)}\n")

    print("sample splits (W surface | old M | -> M0 / M1):")
    for name, sp in sample[:14]:
        print(f"  {sp['wform']!r:18} {sp['mform']!r:16} -> "
              f"{sp['infix_form']!r}/{sp['infix_gloss']!r}  +  "
              f"{sp['root_form']!r}/{sp['root_gloss']!r}")

    print(f"\nflagged single-M '=' cases ({len(all_flags)}):")
    for name, wid, mid, wf, mf, g, reason in all_flags:
        print(f"  {name} {mid:14} {wf!r:18} {mf!r:18} {g!r:14} [{reason}]")

    if not args.dry_run:
        with open(args.csv, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["file", "W_id", "M_id", "W_form", "M_form", "gloss", "reason"])
            wr.writerows(all_flags)
        with open(args.multi_csv, "w", newline="", encoding="utf-8") as fh:
            wr = csv.writer(fh)
            wr.writerow(["file", "W_id", "M_id", "W_form", "W_all_M_forms",
                         "this_M_form", "this_M_gloss", "n_M_in_W"])
            wr.writerows(all_multi)
        print(f"\nwrote flagged CSV     : {args.csv}  ({len(all_flags)} rows)")
        print(f"wrote multi-M '=' CSV : {args.multi_csv}  ({len(all_multi)} rows)")
    else:
        print("\n(dry run: no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
