#!/usr/bin/env python3
"""Which printed section each upstream Safolu entry (h) comes from.

Usage: python3 -I section_map.py <WORK> <docs/s dir to check against> <out.json>

Source of truth: miaoski/amis-safolu db/amis-sqlite3-db.sqlite3 (f512d5b), the converter's own database.
- raw_contents are created file by file in FILE_LIST order (parsing.rb), so raw id ranges are sections:
    main (sections 01-22): id <= 40941   ('yoyang', last entry of 22-WXY)
    section 23:            40942..41609  (starts with the key "'"; the letter entry)
    section 24:            loanword = 1   (41610..42234)
    later:                 id > 42234     (added to the db after the first parse)
- parsing-content.rb walks raw_contents in id order and creates one definition per content paragraph,
  so a term's definitions (by id) belong to its raws (by id) in sequence.
- generate-json-from-sqlite.rb: h = for each term with that lower_name, ordered by stem_id DESC,
  repetition DESC, its definitions in order.
The reconstructed h list is compared with the upstream JSON; only headwords whose h texts match are
mapped automatically.
"""
import ast
import collections
import json
import pathlib
import re
import sqlite3
import sys

W = pathlib.Path(sys.argv[1]); DOCS = pathlib.Path(sys.argv[2]); OUT = pathlib.Path(sys.argv[3])
DB = W / "src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3"
c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


def section(rid, loan):
    if loan:
        return "24"
    if rid <= 40941:
        return "main"
    if rid <= 41609:
        return "23"
    return "later"


raws = collections.defaultdict(list)
for rid, tid, val, loan in c.execute("select id, term_id, value, loanword from raw_contents order by id"):
    try:
        n = len(ast.literal_eval(val))
    except Exception:
        n = len(json.loads(val))
    raws[tid].append((rid, n, section(rid, loan)))
descs = collections.defaultdict(list)
for did, content in c.execute("select definition_id, content from descriptions order by id"):
    descs[did].append(content or "")
defs = collections.defaultdict(list)
for did, tid in c.execute("select id, term_id from definitions order by id"):
    defs[tid].append(did)
bad_terms = 0
def_sec = {}
for tid, dl in defs.items():
    rl = raws.get(tid, [])
    if sum(n for _, n, _ in rl) != len(dl):
        bad_terms += 1
        secs = {s for _, _, s in rl}
        for d in dl:
            def_sec[d] = secs.pop() if len(secs) == 1 else "?"
        continue
    i = 0
    for _, n, s in rl:
        for d in dl[i:i + n]:
            def_sec[d] = s
        i += n
terms = collections.defaultdict(list)
for tid, lower, stem, rep in c.execute("select id, lower_name, stem_id, repetition from terms"):
    terms[lower].append((tid, stem, rep))


def norm(s):
    return re.sub(r"[`~\s￹-￻]", "", s or "")


def order_key(t):  # stem_id DESC, repetition DESC; SQLite puts NULL lowest, so NULL last in DESC; ties by id
    tid, stem, rep = t
    return (stem is None, -(stem or 0), rep is None, -(rep or 0), tid)


SPECIAL = {"=.json", "ch-mapping.json", "index.json", "lenToRegex.json", "precomputed.json", "stem-words.json"}
out = {}
C = collections.Counter()
for p in sorted(DOCS.glob("*.json")):
    if p.name in SPECIAL:
        continue
    e = json.loads(p.read_text(encoding="utf-8"))
    name = e.get("t", p.stem)
    H = e.get("h", [])
    rec = [(def_sec[d], [norm(x) for x in descs[d]]) for t in sorted(terms.get(name.lower(), []), key=order_key) for d in defs[t[0]]]
    jt = [[norm(x.get("f", "")) for x in h.get("d", [])] for h in H]
    if not rec:
        C["not in db (added upstream later)"] += 1
        out[p.stem] = ["upstream-only"] * len(H)
    elif len(rec) == len(H) and all(a == b for (_, a), b in zip(rec, jt)):
        C["h texts match db exactly"] += 1
        out[p.stem] = [s for s, _ in rec]
    else:
        # match each h to an unused reconstructed definition with the same text; else by position if counts agree
        used = set(); m = []
        for b in jt:
            k = next((i for i, (_, a) in enumerate(rec) if i not in used and a == b), None)
            if k is None:
                m.append(None)
            else:
                used.add(k); m.append(rec[k][0])
        if None not in m:
            C["matched by text, order differs"] += 1
        elif len(rec) == len(H):
            m = [x if x is not None else rec[i][0] for i, x in enumerate(m)]
            C["same count, some text edited (position used)"] += 1
        else:
            C["count differs, partly matched"] += 1
            m = [x if x is not None else "?" for x in m]
        out[p.stem] = m
print("terms whose definition count != raw paragraph count:", bad_terms)
for k, v in C.most_common():
    print(f"{v:6d}  {k}")
secs = collections.Counter(s for v in out.values() for s in v)
print("h by section:", dict(secs))
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
