#!/usr/bin/env python3
"""Sort Safolu headwords with 2+ upstream entries (h) into plausible homophones vs. not.

Usage: python3 -I homophone_triage.py <WORK>   -> draft/homophone_triage.json, prints counts

Population: pinned JSON 4cb82539d, files with 2+ h.
1. Entries whose senses are all dropped by the section 23/24 ruling are removed.
2. Ruled 2026-11-15: a capitalised entry with a place-name meaning beside a lowercase non-place entry is a homophone
   (own S). Such capitalised entries are set aside.
3. The lowercase entries left are compared pairwise on their Chinese meaning words (CJK characters, minus a list of
   grammatical characters such as 指 要 的 了 被 把, and minus （東西）-type parentheticals):
     identical text                         -> repeat
     one entry is only a label/cross-reference/no-Chinese/heading/example -> fragment (not a separate word)
     overlap (Jaccard >= 0.4, or 80% of the smaller entry's characters in the larger) -> same word
     no shared meaning character            -> different words
     anything in between                    -> unclear
   A headword whose entries all join into one word = not a homophone; 2+ words joined by no unclear pair = plausibly
   homophones; otherwise unclear.
"""
import collections, itertools, json, pathlib, re, sys
W = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(W / "draft"))
from safolu_headwords import clean, classify, SPECIAL  # noqa: E402
D = W / "src/4cb8/docs/s"
R = json.load(open(W / "draft/section_rulings_4cb8.json", encoding="utf-8"))
if "--no-sections" in sys.argv:  # the section 23/24 ruling is on hold (2026-11-15)
    R = {}
PLACE = re.compile(r"部落|地名|地區|村|鄉|鎮|縣|市|社區|山名|河名|溪名")
EMB = re.compile(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([㐀-鿿].*)$")
STOP = set("指要的了是被把將即使讓去吧在有一種個者之所於與和或等也很不為地方時候情況處人做用使得著過可能會就再又還都對其此該這那某各每及以而並且又")
PAREN = re.compile(r"[（(][^）)]*[）)]|〔[^〕]*〕|\[[^\]]*\]")


def senses(e, i, h):
    acts = R.get(e["_stem"])
    out = []
    for j, d in enumerate(h.get("d", [])):
        if acts and acts[i][j] != "keep":
            continue
        out.append(clean(d.get("f", "")))
    return out


def is_fragment(ss):
    for s in ss:
        if classify(s) in ("empty", "xref", "label", "nochinese"):
            continue
        m = EMB.match(s)
        if m and len(m.group(1).split()) >= 3:
            continue
        if re.search(r"[：:]\s*$", s):
            continue
        return False
    return True


def chars(ss):
    return {c for s in ss for c in PAREN.sub("", re.sub(r"(同|參見|參閱|見)\s*[A-Za-z'^ ,、\-]+。?", "", s)) if "㐀" <= c <= "鿿" and c not in STOP}


def rel(a, b):
    ta, tb = "".join(a), "".join(b)
    if ta == tb:
        return "repeat"
    ca, cb = chars(a), chars(b)
    if not ca or not cb:
        return "unclear"
    inter = len(ca & cb)
    if inter == 0:
        return "different"
    if inter / len(ca | cb) >= 0.4 or inter / min(len(ca), len(cb)) >= 0.8:
        return "same"
    return "unclear"


res = []
C = collections.Counter()
for p in sorted(D.glob("*.json")):
    if p.name in SPECIAL:
        continue
    e = json.loads(p.read_text(encoding="utf-8")); e["_stem"] = p.stem
    H = e["h"]
    if len(H) < 2:
        continue
    C["headwords with 2+ h in the pinned JSON"] += 1
    ents = []
    for i, h in enumerate(H):
        ss = senses(e, i, h)
        if not ss:
            continue  # removed by the section ruling
        ents.append({"i": i, "name": h.get("name") or "", "senses": ss})
    if len(ents) < 2:
        C["left with one entry after the section 23/24 ruling"] += 1
        res.append({"t": e["t"], "verdict": "one entry after section ruling", "h": len(H)}); continue
    cap = [x for x in ents if x["name"][:1].isupper() or (x["name"][:1] == "'" and x["name"][1:2].isupper())]
    low = [x for x in ents if x not in cap]
    capplace = [x for x in cap if PLACE.search(" ".join(x["senses"]))]
    ruled = bool(capplace) and any(not PLACE.search(" ".join(x["senses"])) for x in low)
    rest_cap = [x for x in cap if x not in capplace]
    frag = [x for x in low if is_fragment(x["senses"])]
    words = [x for x in low if x not in frag]
    verdict = None
    pairs = {}
    if len(words) <= 1:
        verdict = "not homophones: repeats or fragments only" if len(low) >= 2 else "no second lowercase entry"
    else:
        rels = {(a, b): rel(words[a]["senses"], words[b]["senses"]) for a, b in itertools.combinations(range(len(words)), 2)}
        pairs = {f"{a}-{b}": r for (a, b), r in rels.items()}
        par = list(range(len(words)))
        def f(x):
            while par[x] != x:
                x = par[x]
            return x
        for (a, b), r in rels.items():
            if r in ("repeat", "same"):
                par[f(a)] = f(b)
        comps = {f(x) for x in range(len(words))}
        if len(comps) == 1:
            kinds = set(rels.values())
            verdict = "not homophones: identical repeat" if kinds == {"repeat"} else "not homophones: overlapping meanings"
        elif any(r == "unclear" and f(a) != f(b) for (a, b), r in rels.items()):
            verdict = "unclear"
        else:
            verdict = "plausibly homophones: no shared meaning"
    if ruled:
        C["has a capitalised place-name entry (ruled homophone)"] += 1
    if rest_cap:
        C["has a capitalised non-place entry (not covered by the ruling)"] += 1
    C[verdict] += 1
    res.append({"t": e["t"], "verdict": verdict, "h": len(H), "capplace_ruled": ruled, "cap_nonplace": [x["name"] for x in rest_cap],
                "fragments": [x["senses"] for x in frag], "words": [x["senses"] for x in words], "pairs": pairs,
                "removed_by_section": len(H) - len(ents)})
json.dump(res, open(W / "draft/homophone_triage.json", "w", encoding="utf-8"), ensure_ascii=False)
for k, v in C.most_common():
    print(f"{v:6d}  {k}")
