#!/usr/bin/env python3
"""Extra round 2 cards (2026-11-15, after the chat about converter cuts and repeated headwords).

Usage: python3 -I round2_extra.py <WORK>   -> draft/round2_extra_cards.json
Reads draft/cut_confirmed.tsv (cut_check.py + 2015 comparison) and draft/homophone_triage.json (homophone_triage.py).
"""
import csv, json, pathlib, re, sys, glob, collections

W = pathlib.Path(sys.argv[1]) / "draft"
R = list(csv.DictReader(open(W / "cut_confirmed.tsv", encoding="utf-8"), delimiter="\t"))
where = {"joined-across-paragraph": "a paragraph break in the source document", "joined-in-one-paragraph": "the converter's split after 。"}
cards = []


def item(r, extra_src=None):
    src = [f"piece 1: {r['piece_1']}", f"piece 2: {r['piece_2']}", f"broken at: {where.get(r['where_in_source'], r['where_in_source'])}"]
    if extra_src:
        src.append(extra_src)
    return src


paste = [r for r in R if r["check_2015"] == "pasting reproduces 2015"]
cards.append({"id": "r2-cut-paste", "corpus": "Safolu", "flag": True,
              "title": "Translations broken in two: the halves match the 2015 text when pasted together",
              "count": f"{len(paste)} breaks",
              "question": "Paste each pair back into one translation? Flag any row where the result is wrong.",
              "body": ["Each row is one translation the converter broke into two TRANSLs. Checked two ways: the two pieces are one continuous run of text in the converter's own input (its database, before it split anything), and the pasted text is word for word what the 2015 conversion of the printed manuscript has.",
                       "Most breaks come from a paragraph break in the middle of a sentence in the source document (each paragraph became its own entry); a few come from the converter splitting after a 。 inside brackets, e.g. nimaay (人稱疑問代詞。所有格形態)."],
              "options": [{"key": "paste", "label": "Paste them back together", "rec": True, "desc": "Two TRANSLs become one, as shown."},
                          {"key": "leave", "label": "Leave them broken", "desc": "Published as two TRANSLs, as now."}],
              "cols": [{"key": "paste", "head": "Published if pasted"}], "keyhead": "Headword", "srchead": "What the draft has now",
              "items": [{"key": f"{r['FORM']} ({r['S']})", "source": item(r), "cells": {"paste": [["TRANSL zho", r["joined"]]]}} for r in paste]})

# lost characters: 2015 text has something between the halves
pr = collections.defaultdict(list)
norm = lambda t: re.sub(r"\s+", "", t or "")
for f in sorted(glob.glob(str(W.parent / "src/printed/amis-safolu/dict/*.txt"))):
    for b in re.split(r"\n\s*\n", open(f, encoding="utf-8", errors="replace").read().replace("\r", "")):
        L = [l for l in b.split("\n") if l.strip()]
        if L and not L[0].startswith((" ", "\t")):
            pr[re.split(r"[（(]", L[0].strip())[0].strip().lower()].append(" / ".join(l.strip() for l in L[1:]))
lost = [r for r in R if r["check_2015"] == "characters lost at the break"]
litems = []
for r in lost:
    p2015 = next((x for x in pr.get(r["FORM"].lower(), []) if r["lost_chars"] in x), "")
    restored = r["piece_1"] + r["lost_chars"] + r["piece_2"]
    litems.append({"key": f"{r['FORM']} ({r['S']})", "source": item(r, f"2015 text: {p2015[:120]}"),
                   "cells": {"restore": [["TRANSL zho", restored], ["", f"(restored from the 2015 text: {r['lost_chars']})"]],
                             "paste": [["TRANSL zho", r["joined"]]],
                             "leave": [["TRANSL zho", r["piece_1"]], ["TRANSL zho alt", r["piece_2"]]]}})
cards.append({"id": "r2-cut-lost", "corpus": "Safolu", "flag": True,
              "title": "Broken translations where characters are missing at the break",
              "count": f"{len(lost)} breaks, checked against the 2015 text",
              "question": "Restore the missing characters from the 2015 text, paste the halves as they are, or leave them broken?",
              "body": ["At these breaks the converter's own input has already lost one or two characters that the 2015 text has, e.g. hacaen: 2015 要求再來，重復一下 / converter input 要求再來，重 ¶ 一下 (復 lost). Pasting alone would publish 要求再來，重一下.",
                       "Observed only for these rows; why the characters went missing is my inference (the break and the loss are at the same spot, which suggests the source document's conversion dropped a character and broke the paragraph there)."],
              "options": [{"key": "restore", "label": "Restore from the 2015 text", "rec": True, "desc": "Pasted, with the missing characters put back."},
                          {"key": "paste", "label": "Paste only", "desc": "Pasted, characters still missing."},
                          {"key": "leave", "label": "Leave them broken", "desc": "Two TRANSLs, as now."}],
              "keyhead": "Headword", "srchead": "What the draft has now",
              "items": litems})

# breaks the 2015 text cannot check
unc = [r for r in R if r["check_2015"] in ("not locatable in 2015 text", "headword not in 2015 text")]
READ = {"mado^etay": "my reading: perhaps a character lost (令人納悶的?)"}
uitems = []
for r in unc:
    mark = ""
    if re.search(r"[（(]$", r["piece_1"]) and r["piece_2"].startswith("象"):
        mark = "⚑ looks like 對 of （對象） lost"
    mark = mark or READ.get(r["FORM"], "")
    uitems.append({"key": f"{r['FORM']} ({r['S']})", "source": item(r, ("2015: " + ("headword not in the 2015 text" if r["check_2015"].startswith("headword") else "this sense not found in the 2015 text")) + (f" · {mark}" if mark else "")),
                   "cells": {"paste": [["TRANSL zho", r["joined"]]] + ([["—", mark]] if mark else []), "leave": [["TRANSL zho", r["piece_1"]], ["TRANSL zho alt", r["piece_2"]]]}})
cards.append({"id": "r2-cut-unchecked", "corpus": "Safolu", "flag": True,
              "title": "Broken translations the 2015 text cannot check",
              "count": f"{len(unc)} breaks ({sum(1 for r in unc if r['check_2015'].startswith('headword'))} headwords absent from the 2015 text; {sum(1 for r in unc if r['check_2015'].startswith('not'))} senses it does not have, mostly ② senses); {sum(1 for i in uitems if '⚑' in ' '.join(i['source']))} marked ⚑",
              "question": "Paste these back together as they are? Flag any row that should not be pasted, or that looks like it lost a character.",
              "body": ["Confirmed as breaks by the converter's input (the halves are one continuous run of text there), but there is no second copy to check the wording against. Rows marked ⚑ look by reading like they lost a character, e.g. dadasa'en 要奉祀、祭奠的（ ‖ 象）。 for （對象）; those would be pasted with the character missing unless you say otherwise in the note."],
              "options": [{"key": "paste", "label": "Paste them back together", "rec": True, "desc": "Two TRANSLs become one; flagged rows left broken."},
                          {"key": "leave", "label": "Leave them broken", "desc": "Two TRANSLs, as now."}],
              "keyhead": "Headword", "srchead": "What the draft has now",
              "items": uitems})

# repeated headwords that are not homophones
T = json.load(open(W / "homophone_triage.json", encoding="utf-8"))
nh = [r for r in T if r["verdict"] in ("not homophones: overlapping meanings", "not homophones: repeats or fragments only")]
hitems = [{"key": r["t"], "source": [" / ".join(w) for w in r["words"]] + ([("fragment: " + " / ".join(f)) for f in r["fragments"]]),
           "cells": {"one": [["S", r["t"] + " (one S, all senses)"]]}} for r in nh]
bins = collections.Counter(r["verdict"] for r in T)
cards.append({"id": "r2-homs-notreview", "corpus": "Safolu", "flag": True,
              "title": "Repeated headwords that are not homophones: publish as one S without a review",
              "count": f"{len(nh)} headwords ({bins['not homophones: overlapping meanings']} whose entries share meaning, {bins['not homophones: repeats or fragments only']} whose extra entries are only repeats, cross-references or fragments)",
              "question": "Publish these as one S each (all senses under one headword) without reviewing them one by one? Flag any that is really two words.",
              "body": ["Your choice for repeated headwords was 'Follow the book's entries, check the rest'. In the pinned JSON 1,234 headwords have 2+ entries. Counted here with sections 23 and 24 treated like any other entry (your section ruling is on hold). Settled already: capitalised entries get their own S (your rulings; 28 headwords); word-for-word identical entries are kept once (your ruling; " + str(bins["not homophones: identical repeat"]) + " headwords).",
                       "Of the rest, I compared each pair of entries on the Chinese characters that carry meaning (leaving out 指 要 的 了 被 把 and similar, and bracketed labels). Bins: " + "; ".join(f"{k}: {v}" for k, v in bins.most_common()) + ".",
                       "I read a random sample from each bin (drawn with the section ruling applied, before it was put on hold): 'overlapping meanings' 15 of 15 one word; 'repeats or fragments only' 8 of 8 one word; 'no shared meaning' about 12 of 20 real homophones; 'unclear' about 3 of 20. Many of the 'not homophone' cases are the converter breaking one printed entry into pieces (see the broken-translation cards).",
                       "The " + str(bins["plausibly homophones: no shared meaning"]) + " 'no shared meaning' and " + str(bins["unclear"]) + " 'unclear' headwords go on their own review page next, with each headword's entries side by side; Lidaw (a village and a cliff under one capitalised S) and ceroh (an uncapitalised copy of the place Ceroh) go there too."],
              "options": [{"key": "one", "label": "One S each, flagged rows to the review", "rec": True, "desc": f"{len(nh)} headwords published with all their senses in one S."},
                          {"key": "review", "label": "Review all of them too", "desc": f"They join the review page ({len(nh)} more headwords)."}],
              "cols": [{"key": "one", "head": "Published"}], "keyhead": "Headword", "srchead": "Its entries (‖ separates entries)",
              "items": [dict(i, source=[" ‖ ".join(i["source"])]) for i in hitems]})
# ---- sections 23 / 24 (ruling on hold): what each option publishes
L = list(csv.DictReader(open(W / "section_rulings_4cb8.tsv", encoding="utf-8"), delimiter="\t"))
byw = collections.defaultdict(list)
for x in L:
    byw[x["headword"]].append(x)
RUL = json.load(open(W / "section_rulings_4cb8.json", encoding="utf-8"))
SPECIAL = {"=.json", "ch-mapping.json", "index.json", "lenToRegex.json", "precomputed.json", "stem-words.json"}
import json as _j
EB = {p.stem: _j.loads(p.read_text(encoding="utf-8")) for p in (W.parent / "src/4cb8/docs/s").glob("*.json") if p.name not in SPECIAL}
stem_of = {e["t"]: k for k, e in EB.items()}
only_because = [e["t"] for k, e in EB.items() if len(e["h"]) >= 2 and k in RUL and sum(1 for h in RUL[k] if any(a == "keep" for a in h)) <= 1]
tv = {r["t"]: r["verdict"] for r in T}
ob = collections.Counter(tv.get(w, "?") for w in only_because)
lab = {"main": "1-22", "23": "23", "24": "24", "later": "1-22", "none": "?"}
def uniq(xs):
    o = []
    for x in xs:
        if x not in o:
            o.append(x)
    return o
sitems = []
for w in sorted(byw, key=lambda w: (byw[w][0]["printed_in"], w)):
    v = byw[w]; pin = v[0]["printed_in"]
    if pin == "24":
        continue  # loanwords printed only in section 24: published under every option
    keepA = [x["text"] for x in v if x["action"] == "keep"]
    if not keepA and "main" in pin:  # upstream merged the two versions; the earlier ruling's option kept the headword
        keepA = uniq([x["text"] for x in v]) + ["(kept: printed in 1-22; upstream merged its versions into this sense)"]
    keepC = [x["text"] for x in v if x["action"] != "drop-23"]
    allB = uniq([x["text"] for x in v])
    cell = lambda xs: [(["—", t] if t.startswith("(kept") else ["TRANSL zho" + (" alt" if i else ""), t]) for i, t in enumerate(xs)] or [["—", "headword not published"]]
    sitems.append({"key": w, "source": [" ‖ ".join(f"[{lab.get(x['matched_section'], x['matched_section'])}] {x['text']}" for x in v) + f"   (printed in: {pin.replace('main', '1-22')})"],
                   "cells": {"none": cell(allB), "drop23": cell(keepC), "ruling": cell(keepA)}})
n_only23 = sum(1 for w in byw if byw[w][0]["printed_in"] == "23")
n_only24 = sum(1 for w in byw if byw[w][0]["printed_in"] == "24")
LOGS = {k: open(W / f"log_opt{k}.txt", encoding="utf-8").read() for k in "ABC"}
num = lambda k, pat: re.search(r"(\d+) " + pat, LOGS[k]).group(1)
cards.insert(0, {"id": "r2-sections", "corpus": "Safolu", "flag": False,
              "title": "Sections 23 and 24: your ruling is on hold, so the question is open again",
              "count": f"{len(sitems)} headwords printed both in sections 1-22 and in section 23 or 24, or only in section 23 ({n_only23}); the {n_only24} loanwords printed only in section 24 are published under every option",
              "question": "What should happen to the entries that come from section 23 (the ' chapter, an older version of the 'a/'e words) and section 24 (the loanword list)?",
              "body": ["You asked: \"can you please undo that for now? And then update the card.\" Done: the drafts and every other card on this page are now computed with sections 23 and 24 treated like any other entry.",
                       "What the sections are (from the manuscript and the converter's database): section 23 is the chapter for the letter ' and holds only 'a... and 'e... words; most are also printed under A or E in a different, usually older wording (e.g. 'adideman: section 01 有桑樹的地方 'place with mulberry trees', section 23 桑樹的種類 'a kind of mulberry'). Section 24 is a list of loanwords, each labelled 〈日語借詞〉 etc.; most of its words appear nowhere else, but some are also printed in sections 1-22, sometimes as a different word (mita: section 14 我們 'we', section 24 電錶 'meter').",
                       f"In the pinned JSON, {len(only_because)} headwords are repeated only because of a section 23/24 entry. Treated like any other entry, they fall into these bins: " + "; ".join(f"{k}: {n}" for k, n in ob.most_common()) + ".",
                       "Each row: every upstream sense of the headword, tagged with the section it was traced to (from the converter's database, matched by text), and what each option publishes. Under 'treat like any other entry' a word-for-word repeated sense is kept once (your ruling); the repeated-headword review then applies as for any headword.",
                       "This is about the headword file only. The published examples file (amis_safolu_examples.xml) already contains examples from section 23/24 entries (303 and 38 sentences); no option here changes it."],
              "options": [{"key": "none", "label": "Treat them like any other entry", "desc": f"Draft: {num('B', 'S written')} S, {num('B', 'TRANSL written')} TRANSL. Repeats handled by the identical-entry ruling and the repeated-headword review."},
                          {"key": "drop23", "label": "Leave out section 23 only", "desc": f"Draft: {num('C', 'S written')} S, {num('C', 'TRANSL written')} TRANSL. Section 24 treated like any other entry."},
                          {"key": "ruling", "label": "Your earlier ruling", "desc": f"Leave out section 23; for section 24 only headwords not in sections 1-22. Draft: {num('A', 'S written')} S, {num('A', 'TRANSL written')} TRANSL (the 41 words upstream merged are kept)."}],
              "keyhead": "Headword", "srchead": "Its upstream senses, with the section each comes from",
              "items": sitems})
json.dump(cards, open(W / "round2_extra_cards.json", "w", encoding="utf-8"), ensure_ascii=False)
for c in cards:
    print(f"{c['id']:20s} items={len(c['items']):4d}  {c['count']}")
