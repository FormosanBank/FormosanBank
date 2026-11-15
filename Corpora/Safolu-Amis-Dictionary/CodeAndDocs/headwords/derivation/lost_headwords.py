#!/usr/bin/env python3
"""r7-missed-lost (RULED "Publish them from the converter's input (show me first)"): build the entries of missed
headwords that upstream lost, from the converter's input (missed_headwords.tsv source_text).

Usage: python3 -I lost_headwords.py <WORK>  -> draft/lost_headwords.tsv (headword, stem, parent, senses ‖-joined) and
       appends their example sentences to draft/examples_manual.tsv (no translation removed)
Each source sentence (split after 。！？): Amis text followed by Chinese = example sentence; Chinese only = definition;
a cross-reference (同 X / 參見 X) is left out (s-xref RULED).
"""
import csv, pathlib, re, sys
W = pathlib.Path(sys.argv[1]); D = W / "draft"
M = [r for r in csv.DictReader(open(D / "missed_headwords.tsv", encoding="utf-8"), delimiter="\t") if r["status"].startswith(("lost", "same"))]
EX = re.compile(r"^([A-Za-z'^][A-Za-z'^ ,.!?\-]*?)[.!?]?\s*([㐀-鿿].*)$")
rows, exs = [], []
for r in M:
    text = re.sub(r"\s*¶\s*", "", r["source_text"])
    parts = [p.strip() for p in re.split(r"(?<=[。！？])", text) if p.strip()]
    senses = []
    for p in parts:
        p = re.sub(r"(同|參見)\s*[A-Za-z'^ ,、\-]+。?$", "", p).strip()
        if not p:
            continue
        m = EX.match(p)
        if m and len(m.group(1).split()) >= 2:
            exs.append([r["headword"], m.group(1).strip() + ".", m.group(2).strip(), "", "converter input (r7-missed-lost RULED)"])
        elif re.search(r"[㐀-鿿]", p) and not re.match(r"^[A-Za-z]", p):
            senses.append(p)
    rows.append([r["headword"], r["stem"], r["filed_under"], " ‖ ".join(senses)])
with open(D / "lost_headwords.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["headword", "stem", "after_headword", "senses"]); w.writerows(rows)
old = [x for x in csv.reader(open(D / "examples_manual.tsv", encoding="utf-8"), delimiter="\t")]
keep = [x for x in old if not x[-1].startswith("converter input (r7")]
with open(D / "examples_manual.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerows(keep + exs)
for x in rows: print("  entry  :", x)
for x in exs: print("  example:", x[:3])
