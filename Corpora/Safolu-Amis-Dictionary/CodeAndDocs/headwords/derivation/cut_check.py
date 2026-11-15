#!/usr/bin/env python3
"""Check suspected converter cuts in the Safolu headword draft against the pre-parser text.

Usage: python3 -I cut_check.py <WORK> <draft headwords xml>   -> draft/cut_check.tsv, prints counts

Suspect: a TRANSL with unbalanced brackets, or with no sentence-final punctuation.
Candidate joins: the suspect + the next TRANSL of the same S, and the previous TRANSL + the suspect.
A suspect counts as a confirmed cut if either join is contiguous in the converter input.
Witness 1 (converter input): miaoski/amis-safolu db raw_contents.value for every term with that lower_name:
  the list of paragraphs of the source .docx (via html), before parsing-content.rb split anything.
Witness 2 (independent): the 2015 conversion of the printed manuscript, dict/*.txt blocks for that headword.
Text is compared with whitespace removed and （）/() unified.
Verdicts (witness 1):
  joined-in-one-paragraph     the two pieces are one continuous run of text inside one source paragraph
  joined-across-paragraph     contiguous only if the paragraph break between them is removed
  separate-in-source          both pieces are in the source but not next to each other (a sense mark or other text
                              between them): not a cut
  not-found                   a piece is not in the converter input (upstream edited it, or the headword is not in the db)
"""
import ast, collections, csv, glob, pathlib, re, sqlite3, sys
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1]); XML = pathlib.Path(sys.argv[2])
db = sqlite3.connect(f"file:{W}/src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3?mode=ro", uri=True)
END = re.compile(r"[。！？!?．.」』)）〕〉…”]\s*$")
PAIRS = ["（）", "()", "〔〕", "〈〉", "「」", "“”"]


def unbalanced(t):
    return any(t.count(a) != t.count(b) for a, b in PAIRS)


def norm(t):
    t = re.sub(r"\s+", "", t or "").replace("`", "").replace("~", "")
    return t.replace("（", "(").replace("）", ")")


raw = collections.defaultdict(list)
for lower, val in db.execute("select t.lower_name, r.value from raw_contents r join terms t on t.id = r.term_id order by r.id"):
    try:
        paras = ast.literal_eval(val)
    except Exception:
        paras = [val]
    raw[lower].append([norm(p) for p in paras])
pr = collections.defaultdict(list)
for f in sorted(glob.glob(str(W / "src/printed/amis-safolu/dict/*.txt"))):
    for b in re.split(r"\n\s*\n", open(f, encoding="utf-8", errors="replace").read().replace("\r", "")):
        L = [l for l in b.split("\n") if l.strip()]
        if L and not L[0].startswith((" ", "\t")):
            hw = re.split(r"[（(]", L[0].strip())[0].strip().lower()
            pr[hw].append(norm("".join(L[1:])))


def verdict(a, b, lower):
    A, B = norm(a), norm(b)
    J = A + B
    rows = raw.get(lower, [])
    if any(J in p for paras in rows for p in paras):
        return "joined-in-one-paragraph"
    if any(J in "".join(paras) for paras in rows):
        return "joined-across-paragraph"
    inA = any(A in p for paras in rows for p in paras); inB = any(B in p for paras in rows for p in paras)
    if inA and inB:
        return "separate-in-source"
    return "not-found"


def pverdict(a, b, lower):
    A, B = norm(a), norm(b)
    blocks = pr.get(lower, [])
    if not blocks:
        return "headword-not-in-2015-text"
    if any(A + B in x for x in blocks):
        return "joined"
    if any(A in x and B in x for x in blocks):
        return "separate"
    return "not-found"


out = []; C = collections.Counter(); seen = set()
for s in ET.parse(XML).getroot().iter("S"):
    form = s.find("FORM").text; low = form.lower()
    T = [t.text or "" for t in s.findall("TRANSL") if t.get("{http://www.w3.org/XML/1998/namespace}lang") == "zho"]
    for i, t in enumerate(T):
        why = []
        if unbalanced(t):
            why.append("unbalanced brackets")
        if not END.search(t):
            why.append("no final punctuation")
        if not why:
            continue
        cands = []
        if i + 1 < len(T):
            cands.append((i, i + 1))
        if i > 0:
            cands.append((i - 1, i))
        if not cands:
            C[("last translation, nothing to join", "")] += 1
            out.append([s.get("id"), form, "+".join(why), i, t, "", "", "nothing-to-join", ""]); continue
        for a, b in cands:
            if (s.get("id"), a, b) in seen:
                continue
            seen.add((s.get("id"), a, b))
            v = verdict(T[a], T[b], low); pv = pverdict(T[a], T[b], low)
            C[(v, pv)] += 1
            out.append([s.get("id"), form, "+".join(why), f"{a}+{b}", T[a], T[b], T[a] + T[b], v, pv])
with open(W / "draft/cut_check.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t")
    w.writerow(["S", "FORM", "why_suspect", "translations", "piece_1", "piece_2", "joined", "converter_input", "text_2015"])
    w.writerows(out)
tot = collections.Counter()
for (v, pv), n in C.items():
    tot[v] += n
print("by converter-input verdict:", dict(tot))
for (v, pv), n in sorted(C.items(), key=lambda kv: -kv[1]):
    print(f"{n:5d}  converter input: {v:28s} 2015 text: {pv}")
