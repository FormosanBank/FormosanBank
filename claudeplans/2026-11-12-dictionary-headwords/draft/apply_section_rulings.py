#!/usr/bin/env python3
"""Apply the 2026-11-15 rulings on Safolu sections 23/24, sense by sense, to the editors' snapshot.

  "Do not record headwords from section 23 of Safolu. For section 24, include only headwords that
   do not appear in sections 1-22."  (maintainer, 2026-11-15)

Only headwords with a printed entry in section 23 or 24 are touched (per the converter's db,
miaoski/amis-safolu db/amis-sqlite3-db.sqlite3: raw id <= 40941 main, 40942..41609 section 23,
loanword=1 section 24). Upstream has merged and edited many entries since the db was made, so
each upstream sense (h[i].d[j].f) is matched one-to-one to a db sense (descriptions.content) by
text similarity (best pairs first; on equal scores the main-section sense is taken first).
  sense matched to section 23                         -> drop-23
  sense matched to section 24, headword has a 01-22 entry -> drop-24
  otherwise                                           -> keep
  match score < 0.75, or no db sense left             -> also marked REVIEW
Usage: python3 -I apply_section_rulings.py <WORK>
Writes draft/section_rulings_4cb8.json {stem: [[action per d] per h]} and draft/section_rulings_4cb8.tsv
"""
import ast, collections, csv, difflib, json, pathlib, re, sqlite3, sys
W = pathlib.Path(sys.argv[1])
c = sqlite3.connect(f"file:{W}/src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3?mode=ro", uri=True)
sec = lambda rid, loan: "24" if loan else "main" if rid <= 40941 else "23" if rid <= 41609 else "later"
norm = lambda s: re.sub(r"[`~\s￹-￻]", "", s or "")
LABEL = re.compile(r"^[〔\[]疊 ?\d[〕\]]$")
PRI = {"main": 0, "later": 1, "24": 2, "23": 3}
dbs = collections.defaultdict(list)  # lower -> [(section, text)]
rawsecs = collections.defaultdict(set)
for lower, tid in c.execute("select lower_name, id from terms").fetchall():
    raws = sorted(c.execute("select id, value, loanword from raw_contents where term_id=?", (tid,)).fetchall())
    for rid, _, loan in raws:
        rawsecs[lower].add(sec(rid, loan))
    defs = [d for (d,) in c.execute("select id from definitions where term_id=? order by id", (tid,))]
    secs = [sec(rid, loan) for rid, v, loan in raws for _ in range(len(ast.literal_eval(v)))]
    if len(secs) != len(defs):
        secs = [sorted({sec(r, l) for r, _, l in raws}, key=PRI.get)[0]] * len(defs)
    for d, s in zip(defs, secs):
        for (x,) in c.execute("select content from descriptions where definition_id=? order by id", (d,)):
            if x and not LABEL.match(x.strip()):
                dbs[lower].append((s, norm(x)))
D = W / "src/4cb8/docs/s"
SPECIAL = {"=.json", "ch-mapping.json", "index.json", "lenToRegex.json", "precomputed.json", "stem-words.json"}
res, rows, C = {}, [], collections.Counter()
for p in sorted(D.glob("*.json")):
    if p.name in SPECIAL:
        continue
    e = json.loads(p.read_text(encoding="utf-8")); name = e.get("t", p.stem); low = name.lower()
    S = rawsecs.get(low, set())
    if not ({"23", "24"} & S):
        continue
    ups = [(i, j, d.get("f", "")) for i, h in enumerate(e["h"]) for j, d in enumerate(h.get("d", []))]
    cand = dbs.get(low, [])
    pairs = sorted(((difflib.SequenceMatcher(None, norm(t), dt).ratio(), -PRI[s], k, u)
                    for u, (_, _, t) in enumerate(ups) for k, (s, dt) in enumerate(cand)), reverse=True)
    got, usedk = {}, set()
    for r, negp, k, u in pairs:
        if u in got or k in usedk:
            continue
        got[u] = (cand[k][0], r); usedk.add(k)
    acts = [[None] * len(h.get("d", [])) for h in e["h"]]
    for u, (i, j, t) in enumerate(ups):
        s, r = got.get(u, ("none", 0.0))
        act = "drop-23" if s == "23" else "drop-24" if (s == "24" and "main" in S) else "keep"
        review = r < 0.75
        acts[i][j] = act
        C[act + (" REVIEW" if review else "")] += 1
        rows.append([name, i, j, s, f"{r:.2f}", act, "REVIEW" if review else "", t, "+".join(sorted(S, key=PRI.get))])
    res[p.stem] = acts
print("senses in headwords with a section 23/24 entry:", sum(C.values()))
for k, v in sorted(C.items()):
    print(f"{v:6d}  {k}")
whole = [k for k, v in res.items() if all(a != "keep" for h in v for a in h)]
print("headwords left with no sense (dropped entirely):", len(whole))
json.dump(res, open(W / "draft/section_rulings_4cb8.json", "w", encoding="utf-8"), ensure_ascii=False)
with open(W / "draft/section_rulings_4cb8.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["headword", "h", "d", "matched_section", "score", "action", "review", "text", "printed_in"]); w.writerows(rows)
