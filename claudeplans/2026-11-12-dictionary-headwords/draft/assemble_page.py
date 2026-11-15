#!/usr/bin/env python3
"""Rebuild dictionary-headwords-round1.html (round 1 decision page, v2, 18 cards).

Usage: python3 -I assemble_page.py <WORK>    (WORK = the directory holding draft/)

Written 2026-11-12 from the inline commands that built the published v2 page;
it does the same steps in the same order:
  1. homophone_cards.json: the Fey card's "review" option gets its cell text
     (homophone_cards.py leaves it empty; this patch was applied by hand).
  2. Card order: s-homophones, the Safolu cards from page_cards.json,
     f-homophones, the Fey cards.
  3. The corpus summary table (the <tbody> rows) is copied from the existing
     dictionary-headwords-round1.html, because it was written by hand.
  4. __SUMMARY__ and __DATA__ in page_template.html are filled in.
"""
import json
import pathlib
import re
import sys

W = pathlib.Path(sys.argv[1]) / "draft"
hc = json.load(open(W / "homophone_cards.json", encoding="utf-8"))
for it in hc[1]["items"]:
    it["cells"]["review"] = [["—", "decided per headword on a review page before publishing"]]
cards = json.load(open(W / "page_cards.json", encoding="utf-8"))
allc = [hc[0]] + [c for c in cards if c["corpus"] == "Safolu"] + [hc[1]] + [c for c in cards if c["corpus"] == "Fey"]
page = W / "dictionary-headwords-round1.html"
summary = re.search(r"<tbody>(.*?)</tbody>", page.read_text(encoding="utf-8"), re.S).group(1)
t = (W / "page_template.html").read_text(encoding="utf-8")
t = t.replace("__SUMMARY__", summary).replace("__DATA__", json.dumps(allc, ensure_ascii=False).replace("</", "<\\/"))
page.write_text(t, encoding="utf-8")
d = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', t, re.S).group(1))
print(len(d), "cards:", [c["id"] for c in d])
