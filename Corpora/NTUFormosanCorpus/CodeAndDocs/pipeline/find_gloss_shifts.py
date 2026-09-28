#!/usr/bin/env python3
"""Find gloss shifts in the source JSONs and propose the repairs that undo them.

For every sentence (an ``s_end`` group of intonation-unit records, or a single
record where the source has no groups) this tries each repair in
``gloss_shift.OPS`` over every window whose preconditions hold, scores the
result against the rest of the language (leave-one-out), and keeps the ones that
pass ``gloss_shift.improves``: more (word, gloss) pairs attested elsewhere, and
no loss in morpheme-count agreement, plain-text reconstruction, glossed words,
or uncontradicted glosses. Up to three repairs are chained per sentence, best
first, so two independent shifts in one sentence are both found.

A window normally stays inside one record -- in the source each record is one
intonation unit, and the shifts found so far never cross one. A window that
would cross a record boundary is tried too, and reported separately
(``cross_record``) only when it beats every in-record candidate: that is the
case where content may have slid from one unit into the next.

Nothing is applied. The output is a proposals TSV in the exact schema of
``gloss_shift_repairs.tsv`` (status ``proposed``, plus score columns) and a
Markdown report showing each sentence before and after. A human decides.

    python find_gloss_shifts.py --codedocs .. --language Atayal --out-dir <dir>
    python find_gloss_shifts.py --codedocs .. --out-dir <dir>        # every language
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gloss_shift import (TABLE_FIELDS, TIERS, Op, RepairError, apply_op,  # noqa: E402
                         blank, build_lexicon, check_moved_not_edited, improves,
                         is_word, record_digest, records_of, score, source_files,
                         suggest)

MAX_WINDOW = 12
MAX_CHAIN = 3
METRICS = ("attested", "contradicted", "morph_match", "morph_eng", "morph_zho", "unglossed",
           "reconstruct", "paired", "support")


def groups(records: list, per_record: bool = False) -> list:
    """Records grouped into sentences the way the builder groups them.

    The Stories builder merges each s_end group (pipeline_stories.merge_groups);
    the Grammar and Sentences builders publish one sentence per record, so for
    them (*per_record*) every record is its own sentence -- grouping them by
    s_end would name the wrong sentence and let a window cross from one
    example into the next.
    """
    if per_record:
        return [[rec] for rec in records]
    out, cur = [], []
    for rec in records:
        cur.append(rec)
        if rec[1].get("s_end", True):
            out.append(cur)
            cur = []
    if cur:
        out.append(cur)
    return out


def _blank_on(row: list, cols: tuple) -> bool:
    return all(blank(row[c] if c < len(row) else "") for c in cols)


def _glossless(row: list) -> bool:
    return _blank_on(row, TIERS["gloss"])


def candidates(rows: list, bounds: list):
    """Every op whose preconditions could hold, as (Op, cross_record).

    Tried on both gloss columns together and on each alone: the English and
    Chinese columns are usually displaced together, but not always, and moving
    both when only one slipped repairs one and breaks the other.
    """
    words = [k for k, r in enumerate(rows) if r and is_word(r[0])]
    rec_of = {}
    for n, (lo, hi) in enumerate(bounds):
        for k in range(lo, hi):
            rec_of[k] = n
    for tier in ("gloss", "col1", "col2"):
        cols = TIERS[tier]
        for a, i in enumerate(words):
            for j in words[a + 1:a + MAX_WINDOW]:
                cross = rec_of[i] != rec_of[j]
                if _blank_on(rows[j], cols):
                    yield Op(tier, "shift_right", i, j), cross
                    if all("=" in (rows[i][c] if c < len(rows[i]) else "") for c in cols):
                        yield Op(tier, "split", i, j, sep="="), cross
                if _blank_on(rows[i], cols) and not _blank_on(rows[j], cols):
                    yield Op(tier, "shift_left", i, j), cross
                nxt = words[a + 1]
                seam = [(rows[i][c] if c < len(rows[i]) else "",
                         rows[nxt][c] if c < len(rows[nxt]) else "") for c in cols]
                for sep in ("=", "-"):
                    if all(x and y and (x.endswith(sep) or y.startswith(sep)) for x, y in seam):
                        yield Op(tier, "merge", i, j, sep=sep), cross


def repairable(rows: list) -> bool:
    """Whether any op's precondition can hold: a word with a blank gloss cell,
    or a marker at the seam between two words' glosses."""
    words = [r for r in rows if r and is_word(r[0])]
    if any(blank(r[c] if c < len(r) else "") for r in words for c in (1, 2)):
        return True
    return any(((a[c] if c < len(a) else "").endswith(("=", "-")) or
                (b[c] if c < len(b) else "").startswith(("=", "-")))
               for a, b in zip(words, words[1:]) for c in (1, 2))


def best_repair(rows, bounds, lex, ori, base):
    """Best in-record and cross-record repair, plus every improving candidate."""
    best = {False: None, True: None}
    alts = {False: [], True: []}
    for op, cross in candidates(rows, bounds):
        try:
            after = apply_op(rows, op)
            check_moved_not_edited(rows, after, op)
        except RepairError:
            continue
        s = score(after, lex, ori)
        if not improves(base, s):
            continue
        key = (s["attested"] - base["attested"], s["support"], -(op.j - op.i))
        alts[cross].append((key, op, s))
        cur = best[cross]
        if cur is None or key > cur[0]:
            best[cross] = (key, after, op, s)
    return best, alts


def locate(op: Op, bounds: list, group: list):
    """Table coordinates for *op*: the record ids it spans and i/j within them."""
    first = next(n for n, (lo, hi) in enumerate(bounds) if lo <= op.i < hi)
    last = next(n for n, (lo, hi) in enumerate(bounds) if lo <= op.j < hi)
    spanned = group[first:last + 1]
    off = bounds[first][0]
    return spanned, op.i - off, op.j - off


def fmt_rows(rows: list, lo: int, hi: int) -> list:
    return [f"| {k} | `{r[0]}` | {r[1] if len(r) > 1 else ''} | {r[2] if len(r) > 2 else ''} |"
            for k, r in enumerate(rows) if lo <= k <= hi]


def scan(codedocs: Path, language: str, stats: Counter):
    paths = source_files(codedocs, language)
    lex = build_lexicon(paths)
    for path in paths:
        rel = path.relative_to(codedocs).as_posix()
        per_record = rel.startswith(("grammar/", "sentence/"))
        for group in groups(records_of(path), per_record):
            bounds, rows, ori = [], [], []
            for rec in group:
                g = [list(r) for r in (rec[1].get("gloss") or [])]
                bounds.append((len(rows), len(rows) + len(g)))
                rows.extend(g)
                ori.extend(rec[1].get("ori") or [])
            if not rows:
                continue
            stats["sentences scanned"] += 1
            if any(r and is_word(r[0]) and _glossless(r) for r in rows):
                stats["sentences with an unglossed word"] += 1
            if not repairable(rows):
                continue
            own = lex.without(rows)
            current, chain = rows, []
            for _ in range(MAX_CHAIN):
                before = score(current, own, ori)
                best, alts = best_repair(current, bounds, own, ori, before)
                inrec, cross = best[False], best[True]
                pick = inrec
                is_cross = False
                if cross and (inrec is None or cross[0] > inrec[0]):
                    pick, is_cross = cross, True
                if pick is None:
                    break
                _, after, op, s = pick
                bare = [(k, after[k][0], suggest(after[k][0], own))
                        for k in range(op.i, op.j + 1)
                        if is_word(after[k][0]) and _glossless(after[k])]
                chain.append((op, is_cross, alts[is_cross], current, after, before, s, bare))
                current = after
            if not chain:
                continue
            stats["sentences with a proposed repair"] += 1
            yield rel, group, bounds, chain


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--codedocs", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--language", action="append",
                    help="source language directory prefix (repeatable); default all")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    langs = args.language or sorted({p.parent.name.split("_")[0]
                                     for p in source_files(args.codedocs)})
    args.out_dir.mkdir(parents=True, exist_ok=True)
    tsv = args.out_dir / "gloss_shift_proposals.tsv"
    md = args.out_dir / "gloss_shift_proposals.md"
    fields = list(TABLE_FIELDS) + ["language", "sentence", "cross_record", "alternatives",
                                   "left_bare"] + \
        [f"{m}_{w}" for m in METRICS for w in ("before", "after")]
    report = ["# Gloss-shift proposals", "",
              "Generated by `find_gloss_shifts.py`. Nothing here is applied: a row takes",
              "effect only once it is copied into `gloss_shift_repairs.tsv` with status",
              "`accepted`. Row indices count every source row, apparatus included.", ""]
    totals = {}
    with tsv.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, delimiter="\t")
        w.writeheader()
        for lang in langs:
            stats = Counter()
            for rel, group, bounds, chain in scan(args.codedocs, lang, stats):
                sid = f"{Path(rel).stem}_S_{group[0][0]}"
                report += [f"## {lang} `{sid}`", "", f"`{rel}`", ""]
                free = [f for f in group[-1][1].get("free") or [] if f.startswith("#e")]
                if free:
                    report += [f"> {free[0][3:]}", ""]
                for op, cross, n_alt, before, after, b, s, bare in chain:
                    stats["repairs proposed"] += 1
                    spanned, i, j = locate(op, bounds, group)
                    row = {"source_file": rel,
                           "record_ids": "+".join(str(r[0]) for r in spanned),
                           "record_sha256": record_digest(spanned),
                           "tier": op.tier, "op": op.op, "i": i, "j": j,
                           "sep": op.sep if op.op in ("split", "merge") else "",
                           "value": "", "status": "proposed", "reviewer": "",
                           "rationale": "", "language": lang, "sentence": sid,
                           "cross_record": int(cross), "alternatives": len(n_alt),
                           "left_bare": "; ".join(f"{f} -> {g}" for _, f, g in bare)}
                    for m in METRICS:
                        row[f"{m}_before"], row[f"{m}_after"] = b[m], s[m]
                    w.writerow(row)
                    delta = ", ".join(f"{m} {b[m]}→{s[m]}" for m in METRICS if b[m] != s[m])
                    report += [f"**{op.label()}** on records {row['record_ids']} "
                               f"(rows {i}..{j} there){' — CROSSES A RECORD BOUNDARY' if cross else ''}; "
                               f"{delta}", "",
                               "| row | form | before col1 | before col2 |", "|---|---|---|---|",
                               *fmt_rows(before, op.i, op.j), "",
                               "| row | form | after col1 | after col2 |", "|---|---|---|---|",
                               *fmt_rows(after, op.i, op.j), ""]
                    if bare:
                        report += ["Left bare by this repair, with how the same word is "
                                   "glossed elsewhere in this language (a suggestion only):", ""]
                        report += [f"- `{f}`: {g}" for _, f, g in bare]
                        report.append("")
                    runners = sorted(n_alt, key=lambda t: t[0], reverse=True)[1:4]
                    if runners:
                        report += [f"Other improving candidates ({len(n_alt) - 1} in all; top 3):", ""]
                        report += [f"- {o.label()}: attested {b['attested']}→{sc['attested']}, "
                                   f"support {b['support']}→{sc['support']}" for _, o, sc in runners]
                        report.append("")
            totals[lang] = stats
    report += ["## Totals", "", "| language | sentences | with an unglossed word | "
               "with a proposal | repairs proposed |", "|---|---|---|---|---|"]
    for lang, st in totals.items():
        report.append(f"| {lang} | {st['sentences scanned']} | {st['sentences with an unglossed word']} | "
                      f"{st['sentences with a proposed repair']} | {st['repairs proposed']} |")
    md.write_text("\n".join(report) + "\n", encoding="utf-8")
    for lang, st in totals.items():
        print(f"{lang:<12} " + "  ".join(f"{k}: {v}" for k, v in sorted(st.items())))
    print(f"wrote {tsv}\nwrote {md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
