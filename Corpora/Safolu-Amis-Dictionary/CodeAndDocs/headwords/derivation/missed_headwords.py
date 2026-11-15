#!/usr/bin/env python3
"""Headword lines the converter missed (r6-missed-headwords, RULED "split them out, show me first").

Usage: python3 -I missed_headwords.py <WORK>   -> draft/missed_headwords.tsv (one row per missed headword, with the
       upstream entries (h indices) of its parent that belong to it)
A missed headword is a source paragraph that is only "word (stem)" inside another headword's converter input
(db raw_contents). Its own paragraphs run from that line to the next such line or the end of that raw entry.
An upstream sense (h[i].d[j]) of the parent belongs to it when its text (whitespace removed) occurs in those paragraphs and
- if upstream kept the headword line itself as an h - only when it comes after that line's h.
Status: split (h's found) / same text as the parent (cannot be told apart) / already its own headword upstream /
lost upstream (in the converter input only).
"""
import ast, csv, json, pathlib, re, sqlite3, sys
W = pathlib.Path(sys.argv[1]); D = W / "src/4cb8/docs/s"
c = sqlite3.connect(f"file:{W}/src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3?mode=ro", uri=True)
H = re.compile(r"^\s*([A-Za-z'^][A-Za-z'^\-]*)\s*[（(]\s*([A-Za-z'^][A-Za-z'^\- ]*)\s*[)）]\s*$")
nos = lambda t: re.sub(r"[\s`~]", "", t or "").replace("（", "(").replace("）", ")")
rows = []
for key, val in c.execute("select key, value from raw_contents order by id"):
    paras = ast.literal_eval(val)
    lines = [i for i, p in enumerate(paras) if H.match(p)]
    if not lines:
        continue
    parent = re.split(r"[（(]", key)[0].strip()
    e = json.load(open(D / (parent.lower() + ".json"), encoding="utf-8"))
    units = [(hi, di, nos(d.get("f", ""))) for hi, h in enumerate(e["h"]) for di, d in enumerate(h.get("d", []))]  # sense level
    htxt = [u[2] for u in units]
    own_parent = nos("".join(paras[:lines[0]]))
    for n, i in enumerate(lines):
        m = H.match(paras[i]); sub, stem = m.group(1), m.group(2)
        end = lines[n + 1] if n + 1 < len(lines) else len(paras)
        mine = nos("".join(paras[i + 1:end]))
        bidx = next((k for k, t in enumerate(htxt) if t == nos(paras[i])), None)
        nxt = next((k for k, t in enumerate(htxt) if n + 1 < len(lines) and t == nos(paras[lines[n + 1]])), None)
        hits = [k for k, t in enumerate(htxt) if t and t in mine and (bidx is None or k > bidx) and (nxt is None or k < nxt)
                and not (bidx is None and t in own_parent)]
        same = [k for k, t in enumerate(htxt) if t and t in mine and bidx is None and t in own_parent]
        has_own = (D / (sub.lower() + ".json")).exists()
        if hits:
            status = "split"
        elif same:
            status = "same text as the parent's definition"
        elif has_own:
            status = "already its own headword upstream"
        else:
            status = "lost upstream (in the converter input only)"
        rows.append([sub, stem, parent, status, ",".join(f"{units[k][0]}.{units[k][1]}" for k in hits), " ¶ ".join(p.strip() for p in paras[i + 1:end]), "yes" if has_own else "no"])
with open(W / "draft/missed_headwords.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["headword", "stem", "filed_under", "status", "parent_senses_h.d", "source_text", "own_file_upstream"]); w.writerows(rows)
import collections
print(collections.Counter(r[3] for r in rows))
for r in rows:
    print(f"  {r[0]:18s} <- {r[2]:16s} {r[3]:42s} h={r[4]:6s} own={r[6]}")
