#!/usr/bin/env python3
"""Rebuild example sentences that sit in the definition field (s-embedded) when the source broke them across paragraphs.

Usage: python3 -I embedded_rebuild.py <WORK>   -> draft/embedded_rebuild.tsv, prints counts
For each row of round2 card r2-embedded: find the definition-field text in the converter input (db raw_contents, the
source paragraphs); if the paragraph before ends without 。！？ (an Amis sentence start) or the Chinese part has no
final 。！？, take the tail of the previous paragraph (after its last 。！？) and the head of the next paragraph (up to
its first 。！？) and join them. Check the joined sentence against the 2015 text (whitespace removed).
"""
import ast, collections, csv, glob, json, pathlib, re, sqlite3, sys
W = pathlib.Path(sys.argv[1])
db = sqlite3.connect(f"file:{W}/src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3?mode=ro", uri=True)
nos = lambda t: re.sub(r"\s+", "", t or "")
pr = collections.defaultdict(list)
for f in sorted(glob.glob(str(W / "src/printed/amis-safolu/dict/*.txt"))):
    for b in re.split(r"\n\s*\n", open(f, encoding="utf-8", errors="replace").read().replace("\r", "")):
        L = [l for l in b.split("\n") if l.strip()]
        if L and not L[0].startswith((" ", "\t")):
            pr[re.split(r"[（(]", L[0].strip())[0].strip().lower()].append(nos("".join(L)))
cards = json.load(open(W / "draft/round2_safolu_cards.json", encoding="utf-8"))
emb = [c for c in cards if c["id"] == "r2-embedded"][0]["items"]
END = re.compile(r"[。！？!?]\s*$")
rows = []; C = collections.Counter()
for it in emb:
    key = it["key"]; hw = key.split(" #")[0]; field = it["source"][0].strip()
    paras = [p for (v,) in db.execute("select r.value from raw_contents r join terms t on t.id = r.term_id where t.lower_name = ? order by r.id", (hw.lower(),)) for p in ast.literal_eval(v)]
    k = next((i for i, p in enumerate(paras) if nos(field) in nos(p)), None)
    amis, zho = it["cells"]["ok"][0][1], it["cells"]["ok"][1][1]
    status, full_a, full_z = "not in converter input", amis, zho
    if k is not None:
        p = paras[k].strip()
        prev = paras[k - 1].strip() if k > 0 else ""
        nxt = paras[k + 1].strip() if k + 1 < len(paras) else ""
        starts_here = nos(p).startswith(nos(field)[:8])
        head_cont = starts_here and prev and not END.search(prev)
        tail_cont = (not END.search(zho)) and nxt
        if not head_cont and not tail_cont:
            status = "complete in the source"
        else:
            pre = ""
            if head_cont:
                pre = re.split(r"[。！？]", prev)[-1].strip()
                kk = k - 1
                while pre and re.match(r"^[a-z]", pre) and kk > 0 and not END.search(paras[kk - 1].strip()):
                    kk -= 1
                    pre = (re.split(r"[。！？]", paras[kk])[-1].strip() + " " + pre).strip()
            lab = re.match(r"^\s*([〔\[（(][^〕\]）)]*[〕\]）)])\s*", pre)
            label = lab.group(1) if lab else ""
            if lab:
                pre = pre[lab.end():]
            post = re.match(r"^[^。！？]*[。！？]?", nxt).group(0).strip() if tail_cont else ""
            full = (pre + " " + field if pre else field) + post
            m = re.match(r"^([A-Za-z'^ ,.!?\-]+?(?:[（(][A-Za-z'^ ,\-]*[）)][A-Za-z'^ ,.!?\-]*?)*)[.!?]?\s*([（(〔\[]?[㐀-鿿].*)$", full)
            if m and re.sub(r"[\s.,!?。，！？]", "", m.group(1) + m.group(2)) != re.sub(r"[\s.,!?。，！？]", "", field):
                full_a, full_z = m.group(1).strip(), m.group(2).strip()
                status = "rebuilt across paragraph breaks" + (f" (label {label} before the sentence)" if label else "")
            else:
                status = "complete in the source"
    in2015 = any(nos(full_a + full_z)[:40] in b or (nos(full_a) in b and nos(full_z) in b) for b in pr.get(hw.lower(), []))
    C[(status, "2015 matches" if in2015 else ("headword not in 2015" if not pr.get(hw.lower()) else "2015 differs"))] += 1
    rows.append([key, field, status, full_a, full_z, "yes" if in2015 else "no"])
with open(W / "draft/embedded_rebuild.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["row", "definition_field", "status", "example_FORM", "example_TRANSL_zho", "matches_2015_text"]); w.writerows(rows)
for k, v in sorted(C.items(), key=lambda kv: -kv[1]):
    print(f"{v:4d}  {k[0]:34s} {k[1]}")
