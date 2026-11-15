#!/usr/bin/env python3
"""r3-amis-tails (RULED 2026-11-15): rebuild translations that start with Amis text into example sentences.

Usage: python3 -I amis_tails_rebuild.py <WORK> <draft xml>   -> draft/amis_tails_rebuild.tsv
Maintainer's rule: "Where the definition starts with a single word in latin characters following by mandarin with no
intervening punctuation, leave as translation. Attempt rebuilding the others." Rows flagged on the page (afa, a, f, k)
also stay as translations. Rebuild: in the converter input (db raw_contents), find the paragraph holding the tail;
prepend the previous paragraph's text after its last 。！？ (the start of the Amis sentence), append the next
paragraph's head up to its first 。！？ if the Chinese has no final 。！？.
"""
import ast, csv, json, pathlib, re, sqlite3, sys
import xml.etree.ElementTree as ET
W = pathlib.Path(sys.argv[1]); X = pathlib.Path(sys.argv[2])
db = sqlite3.connect(f"file:{W}/src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3?mode=ro", uri=True)
FLAGGED = {"afa", "a", "f", "k"}
LEAVE = re.compile(r"^[A-Za-z'^]+[㐀-鿿]")
END = re.compile(r"[。！？!?]\s*$")
nos = lambda t: re.sub(r"\s+", "", t or "")
rows = []
for s in ET.parse(X).getroot().iter("S"):
    form = s.find("FORM").text
    for t in s.findall("TRANSL"):
        x = t.text or ""
        if not re.match(r"^[A-Za-z'^]", x):
            continue
        if form in FLAGGED or LEAVE.match(x):
            rows.append([form, s.get("id"), x, "leave as translation", "", "", "flagged on the page" if form in FLAGGED else "single Latin word followed directly by Mandarin"]); continue
        paras = [p for (v,) in db.execute("select r.value from raw_contents r join terms t on t.id = r.term_id where t.lower_name = ? order by r.id", (form.lower(),)) for p in ast.literal_eval(v)]
        k = next((i for i, p in enumerate(paras) if nos(x)[:10] in nos(p)), None)
        if k is None:
            rows.append([form, s.get("id"), x, "could not rebuild", "", "", "not found in the converter input"]); continue
        p = paras[k]; j = nos(p).find(nos(x)[:10])
        prev = paras[k - 1] if k > 0 else ""
        pre = ""
        if j == 0 and prev and not END.search(prev.strip()):
            pre = re.split(r"[。！？]", prev)[-1].strip()
            kk = k - 1
            while pre and re.match(r"^[a-z]", pre) and kk > 0 and not END.search(paras[kk - 1].strip()):
                kk -= 1
                pre = (re.split(r"[。！？]", paras[kk])[-1].strip() + " " + pre).strip()
        elif j > 0:
            # the start is earlier in the same paragraph: take its text after the last 。！？ before the tail
            raw_before = p[:p.find(x[:6])] if x[:6] in p else ""
            pre = re.split(r"[。！？]", raw_before)[-1].strip()
        nxt = paras[k + 1] if k + 1 < len(paras) else ""
        post = re.match(r"^[^。！？]*[。！？]?", nxt).group(0).strip() if (not END.search(x) and nxt) else ""
        lab = re.match(r"^\s*([〔\[（(][^〕\]）)]*[〕\]）)])\s*", pre)
        if lab:
            pre = pre[lab.end():]
        full = (pre + " " + x if pre else x) + post
        m = re.match(r"^([A-Za-z'^ ,.!?\-]+?(?:[（(][A-Za-z'^ ,\-]*[）)][A-Za-z'^ ,.!?\-]*?)*)[.!?]?\s*([（(〔\[]?[㐀-鿿].*)$", full)
        if not pre:
            rows.append([form, s.get("id"), x, "could not rebuild", "", "", "no Amis sentence start found before it"]); continue
        if not m:
            rows.append([form, s.get("id"), x, "could not rebuild", full, "", "rebuilt text does not split into Amis + Chinese"]); continue
        rows.append([form, s.get("id"), x, "rebuilt", m.group(1).strip(), m.group(2).strip(), "start from the previous paragraph" if j == 0 else "start from earlier in the same paragraph"])
with open(W / "draft/amis_tails_rebuild.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["headword", "S", "translation_now", "result", "example_FORM", "example_TRANSL_zho", "how"]); w.writerows(rows)
import collections
print(collections.Counter(r[3] for r in rows))
for r in rows: print(f"  {r[3]:22s} {r[0]:18s} | {r[2][:34]:36s} -> {r[4][:40]} | {r[5][:24]}  [{r[6]}]")
