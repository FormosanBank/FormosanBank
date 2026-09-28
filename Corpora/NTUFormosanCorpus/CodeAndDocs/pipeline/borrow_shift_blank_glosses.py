#!/usr/bin/env python3
"""Borrow a gloss for a word that a gloss-shift repair left bare.

Maintainer ruling, 2026-09-28: "if we have a sentence with one word without a
gloss BECAUSE WE SHIFTED THE GLOSSES, try borrowing a gloss following similar
functionality for what is done in (5)" -- i.e. same language only, from the
corpus's own evidence, and never a guess.

Which words: the build applies the repair rows in force (see gloss_shift.py) to
the source records when it loads them. This step replays those rows and takes
exactly the cells a row blanked -- a word that had a gloss in the source and has
none after the shift. Words that were already bare in the source are not
touched: that is an omission, not something we did.

The borrowed gloss: among the other W elements of the SAME language (never the
sentence itself) whose form is the same word, the most frequent gloss in that
gloss language. It is borrowed only when the evidence is one-sided: at least
``--min-count`` occurrences, and that gloss on at least ``--min-share`` of them.
Placeholder glosses (XX, ??, FIL, FS, ...) are not evidence. Each gloss language
is decided separately. The TRANSL written carries a ``notes`` attribute naming
its provenance and the counts, so a reader can tell it from a gloss NTU wrote. A
word whose single M mirrors it gets the same gloss on the M.

Anything not borrowed -- no occurrences, evidence split, or the word could not
be located unambiguously -- is written to ``--report`` for review.

    python borrow_shift_blank_glosses.py --xml_dir <dir> --codedocs <CodeAndDocs> \\
        [--report out.tsv] [--min-count 5] [--min-share 0.9]
"""
from __future__ import annotations

import argparse
import copy
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gloss_shift import (PLACEHOLDER_GLOSSES, REPAIRS_TSV,  # noqa: E402
                         apply_to_records, blank, is_word, load_table, norm_form,
                         records_of)

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")


def form_text(el) -> str:
    node = el.find("FORM[@kindOf='original']")
    return "".join(node.itertext()).strip() if node is not None else ""


def gloss(el, lang: str) -> str:
    for t in el.findall("TRANSL"):
        if t.get(XML_LANG) == lang and t.get("ver") is None:
            return (t.text or "").strip()
    return ""


def evidence_gloss(g: str) -> bool:
    return bool(g) and g != "_" and g.rstrip("=").upper() not in PLACEHOLDER_GLOSSES


def created_blanks(codedocs: Path, rows: list) -> list:
    """(language dir, S id, source form, gloss lang) for every cell a row blanked.

    The rows are applied exactly as the builders apply them (``apply_to_records``:
    every row for a file, in table order, each pinned to the source), so chained
    rows over the same or overlapping records compose the same way here.
    """
    out = []
    by_file = defaultdict(list)
    for row in rows:
        by_file[row["source_file"]].append(row)
    for src, frows in by_file.items():
        path = codedocs / src
        recs = records_of(path)
        fixed = apply_to_records(recs, src, frows, {})
        per_record = src.startswith(("grammar/", "sentence/"))
        first_of, start = {}, None
        for r in recs:
            if start is None or per_record:
                start = r[0]
            first_of[str(r[0])] = start
            if r[1].get("s_end", True):
                start = None
        targeted = {rid for row in frows for rid in row["record_ids"].split("+")}
        language = path.parent.name.split("_")[0]
        for before, after in zip(recs, fixed):
            rid = str(before[0])
            if rid not in targeted:
                continue
            for b, a in zip(before[1].get("gloss") or [], after[1].get("gloss") or []):
                if not is_word(b[0]):
                    continue
                for c in (1, 2):
                    old = b[c] if c < len(b) else ""
                    new = a[c] if c < len(a) else ""
                    if not blank(old) and blank(new):
                        lang = "zho" if HAN.search(old) else "eng"
                        out.append((language, f"{path.stem}_S_{first_of[rid]}", b[0], lang))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--codedocs", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--report", type=Path)
    ap.add_argument("--table", type=Path, default=REPAIRS_TSV,
                    help="repairs table (default: the build's, honouring NTU_GLOSS_SHIFT_TABLE)")
    ap.add_argument("--min-count", type=int, default=5)
    ap.add_argument("--min-share", type=float, default=0.9)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    rows = load_table(args.table)
    blanks = created_blanks(args.codedocs, rows)
    stats, report = Counter(), []
    if not blanks:
        print("no gloss-shift repair in force left a word bare")
        return 0
    # Index the build: per language dir, every S and every W's glosses.
    trees, sents, lex = {}, {}, defaultdict(Counter)
    for path in sorted(args.xml_dir.rglob("*.xml")):
        lang_dir = path.parent.name
        tree = etree.parse(str(path))
        trees[path] = tree
        for s in tree.getroot().iter("S"):
            sents[(lang_dir, s.get("id"))] = (path, s)
            for w in s.findall("W"):
                for gl in ("eng", "zho"):
                    g = gloss(w, gl)
                    if evidence_gloss(g):
                        lex[(lang_dir, norm_form(form_text(w)), gl)][g] += 1
    changed_files = set()
    for language, sid, src_form, gl in blanks:
        base = {"language": language, "sentence": sid, "word": src_form, "gloss_lang": gl}
        hit = sents.get((language, sid))
        if hit is None:
            report.append({**base, "outcome": "sentence not in this build"})
            continue
        path, s = hit
        key = norm_form(src_form)
        cands = [w for w in s.findall("W") if norm_form(form_text(w)) == key and not gloss(w, gl)]
        if len(cands) != 1:
            report.append({**base, "outcome": f"{len(cands)} bare W with this form; not located"})
            stats["not located"] += 1
            continue
        w = cands[0]
        own = Counter(gloss(x, gl) for x in s.findall("W")
                      if norm_form(form_text(x)) == key and evidence_gloss(gloss(x, gl)))
        counts = lex[(language, key, gl)] - own
        n = sum(counts.values())
        top, k = (counts.most_common(1)[0] if counts else ("", 0))
        dist = ", ".join(f"{g} {c}" for g, c in counts.most_common(4)) or "none"
        if n < args.min_count or k / max(n, 1) < args.min_share:
            report.append({**base, "outcome": f"not borrowed: {dist} (n={n})"})
            stats["not borrowed (evidence too thin or split)"] += 1
            continue
        note = (f"gloss borrowed: '{src_form}' is glossed this way in {k} of its {n} other "
                f"occurrences in this language; the source gloss was displaced (gloss-shift repair)")
        t = etree.SubElement(w, "TRANSL")
        t.set(XML_LANG, gl)
        t.set("notes", note)
        t.text = top
        ms = w.findall("M")
        if len(ms) == 1 and norm_form(form_text(ms[0])) == key and not gloss(ms[0], gl):
            ms[0].append(copy.deepcopy(t))
        report.append({**base, "outcome": f"borrowed '{top}' ({k}/{n})"})
        stats["borrowed"] += 1
        changed_files.add(path)
    if not args.dry_run:
        for path in changed_files:
            trees[path].write(str(path), encoding="utf-8", xml_declaration=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8", newline="") as fh:
            wr = csv.DictWriter(fh, fieldnames=["language", "sentence", "word", "gloss_lang", "outcome"],
                                delimiter="\t")
            wr.writeheader()
            wr.writerows(report)
    print(f"words left bare by a shift: {len(blanks)} cells; files modified: {len(changed_files)}")
    for key in sorted(stats):
        print(f"  {key}: {stats[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
