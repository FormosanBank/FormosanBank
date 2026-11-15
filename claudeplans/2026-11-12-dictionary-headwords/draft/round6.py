#!/usr/bin/env python3
"""Round 6 page: the held-back Amis-text rows, the headword lines the converter missed, and the homophone review.

Usage: python3 -I round6.py <WORK>   -> draft/dictionary-headwords-round6.html
Inputs: dictionary-headwords-round5.html (log), out_r6 draft XML, amis_tails_rebuild.tsv, homophone_triage.json,
        the converter db, the 2015 text, page_template_r2.html.
"""
import ast, collections, csv, glob, html, json, pathlib, re, sqlite3, sys
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1]); D = W / "draft"
SS = list(ET.parse(D / "out_r6/XML/Amis/Safolu/amis_safolu_headwords.xml").getroot().iter("S"))
BY = collections.defaultdict(list)
for s in SS:
    BY[s.find("FORM").text.lower()].append(s)
db = sqlite3.connect(f"file:{W}/src/printed/amis-safolu/db/amis-sqlite3-db.sqlite3?mode=ro", uri=True)
cards = []

# 1. held-back Amis-text rows
A = {r["headword"]: r for r in csv.DictReader(open(D / "amis_tails_rebuild.tsv", encoding="utf-8"), delimiter="\t")}
held = [
    ("ona", "rebuilt as FORM 'oni a' / TRANSL '的連讀形態。'", "my reading: this is a definition ('the contraction of oni a'), not an example sentence",
     {"keep": [["TRANSL zho", "oni a 的連讀形態。"]], "example": [["FORM (example)", "oni a"], ["TRANSL zho", "的連讀形態。"]]}),
    ("paonol", "rebuilt as FORM 'paonol to demak' / TRANSL '放任他去做。'", "starts with a small letter; in the source the sentence starts 'paonol to demak' right after the definition, so this may be the whole sentence",
     {"keep": [["TRANSL zho", A["paonol"]["translation_now"]]], "example": [["FORM (example)", "Paonol to demak"], ["TRANSL zho", "放任他去做。"]]}),
    ("mimingay", "converter input: ①fali anini.今天風小了。  2015 text: ① 小了，很小了。 / Mimingay ko fali anini. / 今天風小了。",
     "your note: \"Looks like it works fine if you get rid of the numerical marker ①.\" The converter input has lost text here: the sense 小了，很小了 and the sentence start 'Mimingay ko'. The 2015 text has both.",
     {"keep": [["TRANSL zho", A["mimingay"]["translation_now"]]],
      "example": [["FORM (example)", "Mimingay ko fali anini"], ["TRANSL zho", "今天風小了。"], ["TRANSL zho (headword, restored)", "小了，很小了。"]]}),
]
cards.append({"id": "r6-tails-held", "corpus": "Safolu", "flag": False,
              "title": "Three Amis-text rows I held back",
              "count": "3 rows (the other 56 rebuilt sentences are applied, as I read your 'Otherwise, can consume')",
              "question": "Make each of these an example sentence (as shown), or leave it as a translation?",
              "body": ["co^eco is now rebuilt (Co^eco saan a mararamod / (未經父母同意)結婚、同居。) after your note; the bug was my split pattern, which wanted the Chinese to start with a Chinese character. It also fixed pikilim.",
                       "For mimingay the example option uses the 2015 text: the sentence and the lost sense 小了，很小了 are restored, as you chose for lost characters."],
              "options": [{"key": "example", "label": "Example sentence as shown", "rec": True, "desc": "ona: my recommendation is the other option for that row; say so in the note."},
                          {"key": "keep", "label": "Leave as translations", "desc": ""}],
              "keyhead": "Headword", "srchead": "What the source has · why held",
              "items": [{"key": k, "source": [a, b], "cells": c} for k, a, b, c in held]})

# 2. headword lines the converter missed
H = re.compile(r"^\s*([A-Za-z'^][A-Za-z'^\-]*)\s*[（(]\s*([A-Za-z'^][A-Za-z'^\- ]*)\s*[)）]\s*$")
mitems = []
for key, val in db.execute("select key, value from raw_contents order by id"):
    paras = ast.literal_eval(val)
    for i, p in enumerate(paras):
        m = H.match(p)
        if not m:
            continue
        parent = re.split(r"[（(]", key)[0].strip()
        after = []
        for q in paras[i + 1:]:
            if H.match(q):
                break
            after.append(q)
        pub = [t.text for s in BY.get(parent.lower(), []) for t in s.findall("TRANSL")]
        mitems.append({"key": f"{m.group(1)} (under {parent})", "source": [" ¶ ".join(after)[:200]],
                       "cells": {"split": [["S (new headword)", m.group(1) + f"   [notes: Stem: {m.group(2)}]"], ["—", "its definitions (the text after it, up to the next headword) move here from " + parent]],
                                 "leave": [["—", f"{parent} now publishes: " + " ‖ ".join(x[:24] for x in pub[:6])]]}})
cards.append({"id": "r6-missed-headwords", "corpus": "Safolu", "flag": True,
              "title": "Headword lines the converter missed",
              "count": f"{len(mitems)} headword lines inside another headword's text",
              "question": "Found while fixing sacaniis: in the source, a paragraph that is only 'word (stem)' starts a new headword, but the converter did not recognise it, so that word's definitions and examples were filed under the headword before it (e.g. 'saca'owa'owaw (ca'owaw) / 顛簸，上下搖晃' sits inside sacaniis; micekos's 7 entries include micekosan and micekosay). Split them out as their own headwords?",
              "body": ["Each row: the missed headword, the headword it is filed under, and the text that follows it in the source (¶ = paragraph break). Under 'Split them out' I show you the result on the next page before it goes in."],
              "options": [{"key": "split", "label": "Split them out as their own headwords (show me first)", "rec": True, "desc": "Flagged rows stay as they are."},
                          {"key": "leave", "label": "Leave them under the headword before", "desc": ""}],
              "keyhead": "Missed headword", "srchead": "Text after it in the source",
              "items": mitems})

# 3. homophone review
T = json.load(open(D / "homophone_triage.json", encoding="utf-8"))
def hitems(verdict):
    out = []
    for r in T:
        if r["verdict"] != verdict:
            continue
        ents = r["words"]
        out.append({"key": r["t"], "source": [" ‖ ".join(" / ".join(x) for x in ents)],
                    "cells": {"split": [[f"S {i + 1}", " / ".join(x)[:80]] for i, x in enumerate(ents)], "one": [["S", " / ".join(" / ".join(x) for x in ents)[:120]]]}})
    return out
p_items = hitems("plausibly homophones: no shared meaning")
u_items = hitems("unclear")
cards.append({"id": "r6-homs-plausible", "corpus": "Safolu", "flag": True,
              "title": "Repeated headwords whose entries share no meaning: separate entries?",
              "count": f"{len(p_items)} headwords (from my sample, about 12 in 20 are real homophones)",
              "question": "Your choice for repeated headwords was 'Follow the book's entries, check the rest'. For these, the default is one S per printed entry (homophones). Flag each headword that is really ONE word; flagged rows get one S.",
              "body": ["‖ separates the printed entries; / separates senses within an entry. Examples of real homophones: piya' 張開 'open' ‖ 蚶，蛤 'clam'; falah 木炭 'charcoal' ‖ 拋棄 'throw away'. Examples of one word: rana 山腳 'foot of a mountain' ‖ 根基、底部 'base'.",
                       "Already settled and not listed: capitalised entries (own S), word-for-word identical entries (kept once), and the 468 not-homophone repeats (one S)."],
              "options": [{"key": "split", "label": "Separate S per entry (flagged rows one S)", "rec": True, "desc": ""},
                          {"key": "one", "label": "One S for all of them", "desc": ""}],
              "keyhead": "Headword", "srchead": "Its printed entries",
              "items": p_items})
cards.append({"id": "r6-homs-unclear", "corpus": "Safolu", "flag": True,
              "title": "Repeated headwords whose entries partly share meaning: one entry?",
              "count": f"{len(u_items)} headwords (from my sample, about 3 in 20 are real homophones)",
              "question": "For these, the default is one S (one word with several senses). Flag each headword that is really TWO OR MORE words; flagged rows get one S per printed entry.",
              "body": ["Example of a homophone here: lono' 化膿 'pus' ‖ 土石流 'mudslide'. Example of one word: tingeroh 樓層 'storey' ‖ 上面 'above'."],
              "options": [{"key": "one", "label": "One S each (flagged rows separate)", "rec": True, "desc": ""},
                          {"key": "split", "label": "Separate S per entry for all of them", "desc": ""}],
              "keyhead": "Headword", "srchead": "Its printed entries",
              "items": u_items})

# ---- page
t = (D / "page_template_r2.html").read_text(encoding="utf-8")
def rep(a, b):
    global t
    assert a in t, a[:70]
    t = t.replace(a, b)
rep("<title>Dictionary Headwords Round 2</title>", "<title>Dictionary Headwords Round 6</title>")
rep("FormosanBank · decisions round 2", "FormosanBank · decisions round 6")
t = t.replace("meta/round2", "meta/round6")
rep("const answers = {}; let db = null; let doneFlag = false;", "const answers = {}; let db = null; let doneFlag = false; const EXPANDED = new Set();")
rep("if (i >= LIMIT) tr.hidden = true;", "if (i >= LIMIT && !EXPANDED.has(card.id)) tr.hidden = true;")
rep("if (card.items.length > LIMIT){\n          const more", "if (card.items.length > LIMIT && !EXPANDED.has(card.id)){\n          const more")
rep("more.addEventListener('click', () => { for (const r of tb.rows) r.hidden = false; more.remove(); });",
    "more.addEventListener('click', () => { EXPANDED.add(card.id); for (const r of tb.rows) r.hidden = false; more.remove(); });")
q = html.escape
R5 = [("chat: ciem", "\"The H02336 translated as \"O\" can be rebuilt… That is a paranthetical at the beginning saying there's a loanword. Put that in a note and you've got a good example sentence. (I assume example sentences are going into the sentence XML, not our dictionary headword XML file.)\"", "Applied: example O Kalingko ko ciem ako. / 我的親家母住花蓮。 (the 2015 text agrees; my earlier rebuild had missed both ends). 〔閩南語借詞〕 is on the translation 親家母，嬸子 (the 2015 text prints it under the headword). Yes: example sentences go into amis_safolu_examples.xml."),
      ("chat: co^eco", "\"…you say can't be split into Amis + Chinese, but it looks like it can be??\"", "You were right; my split pattern wanted the Chinese to start with a Chinese character. Fixed; it also fixed pikilim."),
      ("chat: mimingay", "\"Looks like it works fine if you get rid of the numerical marker ①.\"", "The converter input lost text there; the 2015 text has the full sentence. Card below."),
      ("r2-sections", "Treat them like any other entry", "Applied (the earlier 23/24 ruling is replaced)."),
      ("r2-heading", "Leave them out", "Applied: 7 headings."),
      ("r2-homs-notreview", "One S each", "Applied: 468."),
      ("r5-affix-approval", "Leave these out too", "Applied: all 48 (6 headwords had nothing else: hina, mo, nipa, nipi, nisa, sa-an)."),
      ("r5-letters-split", "The split is right", "Applied."),
      ("r5-pieces", "Right to remove them", "Applied (31 now, with ciem's O and 母住花蓮。)."),
      ("r5-tails", "No choice; flags co^eco, mimingay (and your chat notes)", "Applied as 'Add the rebuilt sentences' for 56; 3 held back (card below). While doing this, my piece removal briefly also removed six real definitions that appear inside an example's translation (e.g. kandaw 綠色 in 樹葉是綠色的); caught and fixed before publishing: only the rebuilt translation itself is removed.")]
rows5 = "".join(f"<tr><td class='mono'>{q(a)}</td><td>{q(b)}</td><td>{q(c)}</td></tr>" for a, b, c in R5)
old = (D / "dictionary-headwords-round5.html").read_text(encoding="utf-8")
prev = re.search(r'(<section class="panel"><h2>Round 4: what you decided.*?</section>)', old, re.S).group(1)
prev = prev.replace('<section class="panel"><h2>Round 4: what you decided and what I applied</h2>', '<details><summary>Round 4 (log)</summary>').replace("</section>", "</details>")
prev = re.sub(r"<p><b>Draft now</b>.*?</p>", "", prev, flags=re.S)
LOG = f"""<section class="panel"><h2>Round 5: what you decided and what I applied</h2>
<div class="scroll"><table class="log"><thead><tr><th>Card</th><th>Your answer</th><th>What I did (observed in the draft build)</th></tr></thead><tbody>{rows5}</tbody></table></div>
<p><b>Draft now</b>: Safolu 42,284 headword S, 55,919 TRANSL; 159 new example sentences for amis_safolu_examples.xml (103 from definition fields, 56 rebuilt tails); Fey 4,696 headword S. Nothing is committed to the corpora yet.</p>
{prev}</section>"""
intro = ("Round 6: three held-back example rows, 29 headword lines the converter missed, and the homophone review you chose ('Follow the book's entries, check the rest'): "
         f"{len(p_items)} headwords whose entries share no meaning (default: separate) and {len(u_items)} whose entries partly share meaning (default: one). Flag the exceptions.")
t = t.replace("__INTRO__", intro).replace("__LOG__", LOG).replace("__DATA__", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/"))
(D / "dictionary-headwords-round6.html").write_text(t, encoding="utf-8")
print(len(cards), "cards:", [(c["id"], len(c["items"])) for c in cards], f"{len(t)/1e6:.2f} MB")
