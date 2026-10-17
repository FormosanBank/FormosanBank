#!/usr/bin/env python3
"""Publish each Bunun sentence once where 63.json repeats it (rulings 2026-10-16).

63.json is NTU's revised copy of the Bunun sentence collection; bunun63_pairs.tsv
(make_bunun63_pairs.py) says which of its records repeats which record of another
file. This step runs at the END of the Sentences build, so the two copies are
compared as published -- after every cleaning step (maintainer: "you are trying to
combine BEFORE cleaning ... do that cleaning first, then retry combination").

For each pair, on the cleaned sentences (a record split into several sentences --
'a'/'b', '-opt' -- is compared member by member):

  identical                    -> the 63.json copy is deleted ("del63")
  notes differ only            -> the 63.json copy is deleted; the kept sentence
                                  takes "the more recent/complete note"
  translations differ (+notes) -> the 63.json copy is deleted; its differing
                                  translations are added to the kept sentence as
                                  alternative translations (ver="alt")
  same text, analysis differs  -> the OTHER copy is deleted: 63.json's revised
                                  analysis is kept ("rev"), with the other copy's
                                  differing translations added as alternatives
  text differs, punctuation or
  word division only           -> the OTHER copy is deleted (63.json kept, "rev")
  text differs in letters      -> the 63.json copy is deleted (other kept, "other")

A translation written as two renderings 'A / B' counts as two translations, and
in a kept sentence becomes A plus an alternative B (ruling, card d~tr).

usage: dedupe_bunun63.py --xml_dir <Sentences work dir> [--report <tsv>]
"""
from __future__ import annotations

import argparse
import collections
import csv
import re
import sys
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
XL = "{http://www.w3.org/XML/1998/namespace}lang"
_ID = re.compile(r"^(.+)_S_(\d+)([a-z]?)((?:-opt\d?)?)$")


def load_pairs(path=HERE / "bunun63_pairs.tsv"):
    lines = [l for l in Path(path).read_text(encoding="utf-8").splitlines() if l and not l.startswith("#")]
    return [(r["record_63"], r["other_file"], r["other_record"]) for r in csv.DictReader(lines, delimiter="\t")]


def _orig(el):
    f = el.find("FORM[@kindOf='original']")
    return f


def _parts(text: str, lang: str):
    out = []
    for p in (text or "").split(" / "):
        p = p.strip().rstrip("。.!?？！ ").strip()
        if lang == "zho":
            p = re.sub(r"\s+", "", p)
        else:
            p = " ".join(p.split())
        if p:
            out.append(p)
    return out


def translations(s) -> dict:
    """{lang: {comparison key: the rendering as written}}; 'A / B' is two renderings."""
    out = collections.defaultdict(dict)
    for t in s.findall("TRANSL"):
        lang = t.get(XL)
        for raw in (t.text or "").split(" / "):
            for key in _parts(raw, lang):
                out[lang].setdefault(key, raw.strip())
    return out


def _keys(tr: dict) -> dict:
    return {lang: set(v) for lang, v in tr.items()}


def summary(s) -> dict:
    f = _orig(s)
    return dict(text="".join(f.itertext()) if f is not None else "",
                notes=re.sub(r"\s+", "", (f.get("notes") or "") if f is not None else ""),
                words=tuple("".join(w.find("FORM[@kindOf='original']").itertext()) for w in s.findall("W")),
                glosses=tuple(tuple(t.text or "" for t in w.findall("TRANSL")) for w in s.findall("W")),
                tr=_keys(translations(s)))


def choose_note(keep, drop_note: str | None, recent_is_keep: bool):
    """'the more recent/complete note': the copy whose note contains the other's
    characters is the more complete; when neither contains the other, the more
    recent (63.json, NTU's revision) wins."""
    f = _orig(keep)
    kn, dn = (f.get("notes") or ""), (drop_note or "")
    if kn.strip() == dn.strip():
        return "same"
    ck, cd = collections.Counter(re.sub(r"\s", "", kn)), collections.Counter(re.sub(r"\s", "", dn))
    if not (cd - ck):
        return "kept note is complete"
    if not (ck - cd) or not recent_is_keep:
        if dn:
            f.set("notes", dn)
        elif "notes" in f.attrib:
            del f.attrib["notes"]
        return "took the other copy's note"
    return "kept the more recent note"


def add_alternatives(keep, other_tr: dict) -> int:
    """Split 'A / B' in the kept sentence, then add every translation the other
    copy has that the kept one lacks, as ver="alt" after its language's last TRANSL."""
    added = 0
    for t in list(keep.findall("TRANSL")):
        if " / " in (t.text or "") and not t.get("ver"):
            first, *rest = [p.strip() for p in t.text.split(" / ") if p.strip()]
            t.text = first
            anchor = t
            for r in rest:
                n = etree.Element("TRANSL"); n.set(XL, t.get(XL)); n.set("ver", "alt"); n.text = r
                anchor.addnext(n); anchor = n; added += 1
    have = _keys(translations(keep))
    for lang, parts in other_tr.items():
        for key in sorted(set(parts) - have.get(lang, set())):
            same = keep.findall(f"TRANSL[@{XL}='{lang}']") or keep.findall("TRANSL")
            n = etree.Element("TRANSL"); n.set(XL, lang); n.set("ver", "alt"); n.text = parts[key]
            (same[-1].addnext(n) if same else keep.insert(0, n)); added += 1
    return added


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args(argv)
    files = sorted((args.xml_dir / "Bunun").glob("*.xml")) if (args.xml_dir / "Bunun").is_dir() else []
    if not files:
        print("dedupe_bunun63: no Bunun sentence file; nothing to do")
        return 0
    stats, report = collections.Counter(), []
    for path in files:
        tree = etree.parse(str(path)); root = tree.getroot()
        groups = collections.defaultdict(list)
        for s in root.iter("S"):
            m = _ID.match(s.get("id") or "")
            if m:
                groups[(m.group(1), m.group(2))].append(s)
        changed = False
        for r63, ofile, orec in load_pairs():
            g63, go = groups.get(("63", r63), []), groups.get((ofile, orec), [])
            if any(s.getparent() is None for s in g63 + go):
                # The other file's record is the pair of two 63.json records (63.json
                # repeats it internally); the first pair already resolved it.
                stats["pair skipped: one copy already resolved by an earlier pair"] += 1
                report.append((r63, ofile, orec, "already resolved", ""))
                continue
            if not g63 or not go or len(g63) != len(go):
                stats["pair skipped: copies not both published, or split differently"] += 1
                report.append((r63, ofile, orec, "skipped", ""))
                continue
            S63, SO = [summary(s) for s in g63], [summary(s) for s in go]
            same = lambda k: all(a[k] == b[k] for a, b in zip(S63, SO))
            if not same("text"):
                # Round 2 (rulings 2026-10-16): punctuation-only and word-division-only
                # differences keep the revision ("rev"); different letters keep the
                # other file's copy ("other"), whose spellings other Bunun corpora
                # mostly use (saia 1,254 vs saiia 49).
                letters = lambda s: re.sub(r"[^\w']", "", s.replace("\u2019", "'")).lower()
                words_np = lambda s: re.sub(r"[^\w\s']", "", s).split()
                if any(letters(a["text"]) != letters(b["text"]) for a, b in zip(S63, SO)):
                    kind = "text differs: letters"
                elif all(words_np(a["text"]) == words_np(b["text"]) for a, b in zip(S63, SO)):
                    kind = "text differs: punctuation only"
                else:
                    kind = "text differs: word division only"
            elif not (same("words") and same("glosses")):
                kind = "same text, analysis differs"
            elif not same("tr"):
                kind = "translations differ" + ("" if same("notes") else " + notes")
            elif not same("notes"):
                kind = "notes differ"
            else:
                kind = "identical"
            stats[kind] += 1
            keep_revision = kind in ("same text, analysis differs", "text differs: punctuation only",
                                     "text differs: word division only")
            keep, drop = (g63, go) if keep_revision else (go, g63)
            notes_how = []
            for k, d in zip(keep, drop):
                notes_how.append(choose_note(k, (_orig(d).get("notes") if _orig(d) is not None else None),
                                             recent_is_keep=(keep is g63)))
                stats["  alternative translations added"] += add_alternatives(k, translations(d))
                d.getparent().remove(d)
                stats["  sentences deleted"] += 1
            report.append((r63, ofile, orec, kind, f"kept {keep[0].get('id')}, deleted {drop[0].get('id')}; notes: {'; '.join(notes_how)}"))
            changed = True
        if changed:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(["record_63", "other_file", "other_record", "kind", "action"]); w.writerows(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
