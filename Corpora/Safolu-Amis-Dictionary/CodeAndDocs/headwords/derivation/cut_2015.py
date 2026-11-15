#!/usr/bin/env python3
"""Second step of the converter-cut check: keep the confirmed cuts from cut_check.tsv and compare each with the
2015 conversion of the printed manuscript (dict/*.txt).

Usage: python3 -I cut_2015.py <WORK>   (after cut_check.py)   -> draft/cut_confirmed.tsv
Confirmed cut = the joined pieces are contiguous in the converter input AND the first piece does not end a sentence
(or leaves a bracket open); a join whose first piece ends in 。！？ is the converter's normal sentence split.
2015 check: the last 4/3/2 characters of piece 1 and the first 4/3/2 of piece 2 are looked up in the headword's 2015
blocks; the text between them (at most 4 characters) is reported: empty = pasting reproduces 2015.
"""
import collections, csv, glob, pathlib, re, sys
W = pathlib.Path(sys.argv[1])
SENT = re.compile(r"[。！？!?]\s*$")
P = ["（）", "()", "〔〕", "〈〉", "「」", "“”"]
openb = lambda t: any(t.count(a) > t.count(b) for a, b in P)
norm = lambda t: re.sub(r"\s+", "", t or "").replace("`", "").replace("~", "").replace("（", "(").replace("）", ")")
pr = collections.defaultdict(list)
for f in sorted(glob.glob(str(W / "src/printed/amis-safolu/dict/*.txt"))):
    for b in re.split(r"\n\s*\n", open(f, encoding="utf-8", errors="replace").read().replace("\r", "")):
        L = [l for l in b.split("\n") if l.strip()]
        if L and not L[0].startswith((" ", "\t")):
            pr[re.split(r"[（(]", L[0].strip())[0].strip().lower()].append(norm("".join(L[1:])))


def gap(A, B, blocks):
    for n in (4, 3, 2):
        a, b = A[-n:], B[:n]
        best = None
        for x in blocks:
            for m in re.finditer(re.escape(a), x):
                k = x.find(b, m.end())
                if k != -1 and k - m.end() <= 4:
                    g = x[m.end():k]
                    if best is None or len(g) < len(best):
                        best = g
        if best is not None:
            return best
    return None


rows = []; C = collections.Counter()
for r in csv.DictReader(open(W / "draft/cut_check.tsv", encoding="utf-8"), delimiter="\t"):
    if r["converter_input"] not in ("joined-in-one-paragraph", "joined-across-paragraph"):
        continue
    if SENT.search(r["piece_1"]) and not openb(r["piece_1"]):
        continue
    bl = pr.get(r["FORM"].lower(), [])
    if not bl:
        res, g = "headword not in 2015 text", None
    else:
        g = gap(norm(r["piece_1"]), norm(r["piece_2"]), bl)
        res = "not locatable in 2015 text" if g is None else ("pasting reproduces 2015" if g == "" else "characters lost at the break")
    C[res] += 1
    rows.append({"S": r["S"], "FORM": r["FORM"], "translations": r["translations"], "piece_1": r["piece_1"], "piece_2": r["piece_2"],
                 "joined": r["joined"], "where_in_source": r["converter_input"], "text_2015": r["text_2015"], "check_2015": res, "lost_chars": g or ""})
with open(W / "draft/cut_confirmed.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter="\t"); w.writeheader(); w.writerows(rows)
print("confirmed cuts:", len(rows), dict(C))
