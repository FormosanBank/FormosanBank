#!/usr/bin/env python3
"""List entries that wildjcrt's pourrias-poinsot.txt glued onto the entry before them.

In the printed book (2020 proofreading DB), many entries starting with the glottal letter ’ begin their own
printed line, e.g. p.566 l.17 "tkip - {S}：陷機" / l.18 "’tkiw - {FT} ＝ atkiw：辣椒". pourrias-poinsot.txt
joins such lines onto the previous entry ("tkip - {S}：陷機 'tkiw - {F}{T} = atkiw：辣椒"). This script finds
every printed line that (a) lies inside another entry's span, (b) starts with ’ or ' plus a word and has an
entry's shape (a colon), and (c) sorts alphabetically between its host entry and the next entry. It writes
CodeAndDocs/data/line_splits.tsv: decision "split" when all three hold, "not-a-split" otherwise (with reason).
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_amis_chinese_xml as B  # noqa: E402

ENTRY_START = re.compile(r"^\s*([’'][A-Za-z][A-Za-z'’]*)(?=\s*[-=＝{(：]|\s+[A-Za-z'’]+\s*[-=＝{：(])")


def alpha(word: str) -> str:
    return re.sub(r"[^a-z]", "", word.lower())


def head_word(line: str) -> str:
    return re.split(r"[\s：=＝\-{(<]", line.strip(), 1)[0]


def fingerprint(printed_line: str) -> str:
    return B.keyed(printed_line)[0][:14]


def main() -> None:
    raw = B.load_source(B.SOURCE_TXT)
    locs_raw = B.printed_locations(raw, B.SOURCE_DB)
    lines, members = B.apply_wraps(B.apply_corrections(raw))   # splits are applied after printed-line joins
    locs = {n: (locs_raw[m[0]][0], locs_raw[m[-1]][1]) if all(locs_raw[x] for x in m) else None
            for n, m in members.items()}
    con = sqlite3.connect(B.SOURCE_DB)
    printed = {(p, l): a for p, l, a in con.execute("select p, line, ans from toufu") if a}
    order = sorted(lines)
    nxt = dict(zip(order, order[1:]))
    rows = ["line	fingerprint	decision	evidence"]
    for n in order:
        loc = locs[n]
        if not loc:
            continue
        (p0, l0), (p1, l1) = loc
        last = len(B.split_head_body(lines[n])[0])
        host = alpha(head_word(lines[n]))
        after_word = alpha(head_word(lines[nxt[n]])) if n in nxt else "zzzz"
        for key in sorted(k for k in printed if (p0, l0) < k <= (p1, l1)):
            text = printed[key]
            m = ENTRY_START.match(text)
            if not m or "：" not in text:
                continue
            word, fp = m.group(1), fingerprint(text)
            ev = f"printed p.{key[0]:03d} l.{key[1]:02d} begins \"{text[:40]}\""
            off = B.locate(lines[n], fp, last)
            if off is None:
                rows.append(f"{n}\t{fp}\tnot-a-split\t{ev}; not found in the host line")
            elif not (host <= alpha(word) <= after_word):
                rows.append(f"{n}\t{fp}\tnot-a-split\t{ev}; '{alpha(word)}' out of alphabetical order (host '{host}', next '{after_word}')")
            else:
                rows.append(f"{n}\t{fp}\tsplit\t{ev}; '{alpha(word)}' sorts between host '{host}' and next '{after_word}'")
                last = off
    # splits confirmed by eye on the scan, where the alphabetical check cannot decide (split_confirmations.tsv)
    confirmed = {(int(r["line"]), r["fingerprint"]): r["evidence"] for r in B.read_tsv(B.DATA / "split_confirmations.tsv")}
    for i, row in enumerate(rows[1:], start=1):
        n, fp, decision, ev = row.split("\t", 3)
        if (int(n), fp) in confirmed:
            rows[i] = f"{n}\t{fp}\tsplit\t{confirmed.pop((int(n), fp))}"
    for (n, fp), ev in confirmed.items():   # a confirmation whose fingerprint the scan-matching did not produce
        rows.append(f"{n}\t{fp}\tsplit\t{ev}")
    out = B.DATA / "line_splits.tsv"
    out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    split = sum(1 for r in rows[1:] if "\tsplit\t" in r)
    print(f"{len(rows) - 1} candidates: {split} split, {len(rows) - 1 - split} not-a-split -> {out}")


if __name__ == "__main__":
    main()
