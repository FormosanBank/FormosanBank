#!/usr/bin/env python3
"""List headword translations that are only a piece of a rebuilt example sentence (r3-embedded-rebuilt, RULED).

Usage: python3 -I example_pieces.py <WORK> <draft xml built without --pieces or with the previous list>
       -> draft/example_pieces_removed.tsv
A translation counts as a piece when its text (whitespace removed) occurs inside a rebuilt example sentence of the same
headword and is not the definition-field text the example came from.
"""
import csv, pathlib, re, sys
import xml.etree.ElementTree as ET
W = pathlib.Path(sys.argv[1]); X = pathlib.Path(sys.argv[2])
import collections
b = collections.defaultdict(list)  # every S of a headword (split headwords have several)
for s_ in ET.parse(X).getroot().iter("S"):
    b[s_.find("FORM").text.lower()].append(s_)
nos = lambda t: re.sub(r"\s+", "", t or "")
rows = []
for r in csv.DictReader(open(W / "draft/embedded_rebuild.tsv", encoding="utf-8"), delimiter="\t"):
    if not r["status"].startswith("rebuilt"):
        continue
    SL = b.get(r["row"].split(" #")[0].lower(), [])
    full = nos(r["example_FORM"] + r["example_TRANSL_zho"])
    for t in [t for s in SL for t in s.findall("TRANSL")]:
        x = nos(t.text)
        if x and x != nos(r["definition_field"]) and x in full:
            rows.append([SL[0].find("FORM").text, t.text, r["row"], r["example_FORM"] + " / " + r["example_TRANSL_zho"]])
HELD = {"ona"}  # r6-tails-held (RULED): ona stays a translation; paonol, mimingay are examples
for r in csv.DictReader(open(W / "draft/amis_tails_rebuild.tsv", encoding="utf-8"), delimiter="\t"):
    if r["result"] != "rebuilt" or r["headword"] in HELD:
        continue
    SL = b.get(r["headword"].lower(), [])
    if not SL:
        continue
    nop = lambda t: re.sub(r"[\s.,!?。，！？]", "", t or "")
    full = nop(r["example_FORM"] + r["example_TRANSL_zho"])
    for t in [t for s in SL for t in s.findall("TRANSL")]:
        x = nop(t.text)
        # only the rebuilt translation itself: a real definition can occur inside the example's Chinese (kandaw 綠色 in 樹葉是綠色的)
        if x and t.text == r["translation_now"] and [r["headword"], t.text] not in [q[:2] for q in rows]:
            rows.append([SL[0].find("FORM").text, t.text, f"amis-tail {r['S']}", r["example_FORM"] + " / " + r["example_TRANSL_zho"]])
for r in csv.DictReader(open(W / "draft/examples_manual.tsv", encoding="utf-8"), delimiter="\t"):
    if not r["translation_removed"]:
        continue
    rows.append([r["headword"], r["translation_removed"], "manual (2015 text)", r["example_FORM"] + " / " + r["example_TRANSL_zho"]])
with open(W / "draft/example_pieces_removed.tsv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t"); w.writerow(["headword", "translation_removed", "example_row", "rebuilt_example"]); w.writerows(rows)
print("pieces:", len(rows))
