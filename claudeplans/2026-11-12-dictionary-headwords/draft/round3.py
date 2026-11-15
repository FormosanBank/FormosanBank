#!/usr/bin/env python3
"""Round 3 page: carried-over open cards + new cards; template fix so 'Show all' stays open.

Usage: python3 -I round3.py <WORK>   -> draft/dictionary-headwords-round3.html
Inputs: round2_safolu_cards.json, round2_extra_cards.json (round 2 cards), embedded_rebuild.tsv, out_r2 draft XML,
        dictionary-headwords-round2.html (its round 1 log rows are carried over), page_template_r2.html.
"""
import csv, html, json, pathlib, re, sys
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1]) / "draft"
XL = "{http://www.w3.org/XML/1998/namespace}lang"
S2 = {c["id"]: c for c in json.load(open(W / "round2_safolu_cards.json", encoding="utf-8"))}
X2 = {c["id"]: c for c in json.load(open(W / "round2_extra_cards.json", encoding="utf-8"))}
XML = W / "out_r2/XML/Amis/Safolu/amis_safolu_headwords.xml"
SS = list(ET.parse(XML).getroot().iter("S"))
cards = []

# carried over unchanged (unanswered, or still being checked)
cards.append(X2["r2-sections"])
pl = S2["r2-poslabels"]
pl["body"] = pl["body"] + ["Your rows flagged so far (刀 水 做 牲口 動物 東西 關於 植物 穀物 狗 人 用手) are kept as you said: 'can be left alone'. 'Show all' now stays open while you flag."]
pl["cols"] = [{"key": "ok", "head": "My proposal"}]; pl["keyhead"] = "Label"; pl["srchead"] = "Example"
cards.append(pl)
cards.append(S2["r2-heading"])

# lost characters: answer the grammar question
cl = X2["r2-cut-lost"]
GRAM = {"hacaen": ("yes: 要求再來，重復一下 'ask to come again; repeat it once more'", "no: 重一下 is not a word here"),
        "tili'ien": ("yes: …，對…討厭 'dislike …'", "no: without 對 the gloss reads '… is annoying' and loses its object"),
        "mipasikiwan": ("yes, though 對…有偏見 would be more usual", "no: ；…偏見 is a fragment"),
        "tona": ("yes: 系toni與a的連讀 'the contraction of toni and a' (the 2015 text has spaces: 系 toni 與 a 的連讀)", "no: the halves run together into 'tonia', which is not a word"),
        "papitoay": ("yes: 指所具有的七個（人或動物） 'the seven (people or animals) one has'", "no: 所 needs a verb after it")}
for it in cl["items"]:
    w = it["key"].split(" (")[0]
    g = GRAM.get(w)
    if g:
        it["source"] = it["source"] + [f"Restored grammatical? {g[0]}", f"Pasted only grammatical? {g[1]}"]
cl["body"] = ["Your question: \"Which versions result in grammatical Chinese?\" My reading (I am not a native speaker; please check): the restored version is grammatical in all 5; the pasted-only version is not grammatical in any of them. Each row says why."] + cl["body"]
cards.append(cl)
cards.append(X2["r2-cut-unchecked"])
cards.append(X2["r2-homs-notreview"])

# rebuilt example sentences
R = [r for r in csv.DictReader(open(W / "embedded_rebuild.tsv", encoding="utf-8"), delimiter="\t") if r["status"].startswith("rebuilt")]
flags_r2 = set(json.load(open(W.parent / "answers_r2/answers/r2-embedded.json", encoding="utf-8")).get("flags", []))
MARK = {"mingohahay #49": "⚑ my reading: 我Alik約會了 looks like it lost 和 or 跟 (我和Alik約會了)",
        "mingihngihay #48": "⚑ my reading: 他在小姐調情 looks like it lost 跟 (他在跟小姐調情)",
        "mirikap #72": "⚑ the source repeats ko across the break: Mirikap ko ¶ ko mato'asay",
        "sapipatawyiwaw #99": "⚑ the source Chinese has a stray 同: 加一點同醬油",
        "koko' no riyar #17": "⚑ two sentences joined; the second (Makutay…) has no translation",
        "ciem #8": "⚑ the Chinese 我的親家 'my in-law' looks shorter than the Amis"}
ritems = []
for r in R:
    src = [f"shown on round 2: {r['definition_field']}", f"2015 text matches: {r['matches_2015_text']}" + ("  · you flagged this row on round 2" if r["row"] in flags_r2 else "")]
    if r["row"] in MARK:
        src.append(MARK[r["row"]])
    ritems.append({"key": r["row"], "source": src, "cells": {"add": [["FORM", r["example_FORM"]], ["TRANSL zho", r["example_TRANSL_zho"]]]}})
cards.append({"id": "r3-embedded-rebuilt", "corpus": "Safolu", "flag": True,
              "title": "Example sentences from the definition field, rebuilt across the source's paragraph breaks",
              "count": f"{len(R)} of the 103 sentences ({sum(1 for r in R if r['row'] in flags_r2)} are the rows you flagged; the other {sum(1 for r in R if r['row'] not in flags_r2)} looked whole on the page but are broken too); {sum(1 for r in R if r['matches_2015_text'] == 'yes')} match the 2015 text; {len(MARK)} marked ⚑",
              "question": "Add these rebuilt sentences to the examples file? Flag any that are still wrong.",
              "body": ["Your round 2 note: \"Some of these were clearly sentence fragments. I think I flagged them all. I don't know if they are part of your identified broken lines.\" They were not in my 152 (those were checked after the example sentences had been taken out of the definitions). Checked now: all 13 you flagged, and 57 more, are pieces of a sentence that the source document broke across paragraphs: its start (often the first Amis word) ends the paragraph before, and its last Chinese characters start the next. E.g. cikang was shown as 'Awa ko cikang no mako a tayra' with only part of the Chinese.",
                       "Rebuilt by taking the end of the previous paragraph (after its last 。！？) and the start of the next one (up to its first 。！？) from the converter's own input. The other 33 of the 103 are whole in the source and stay as you ruled ('Add them (flagged rows aside)')."],
              "options": [{"key": "add", "label": "Add the rebuilt sentences (flagged rows aside)", "rec": True, "desc": "Each becomes an S in amis_safolu_examples.xml."},
                          {"key": "drop", "label": "Leave all 70 out", "desc": "Only the 33 whole ones are added."}],
              "cols": [{"key": "add", "head": "New example S"}], "keyhead": "Row", "srchead": "What round 2 showed · checks",
              "items": ritems})

# 疊 tags
titems = []
for s in SS:
    f = s.find("FORM"); n = f.get("notes") or ""
    parts = [p.strip() for p in n.split(" | ")] if n else []
    tg = [p for p in parts if re.match(r"^[〔\[]\s*疊\s*\d?\s*[〕\]][。.]?$", p)]
    if not tg:
        continue
    has_tag = any(p.startswith("Tag:") for p in parts)
    num = re.search(r"\d", tg[0])
    new = [p for p in parts if p not in tg]
    if not has_tag:
        new.insert(0, f"Tag: [疊 {num.group(0)}]" if num else "Tag: [疊]")
    titems.append({"key": f"{f.text} ({s.get('id')})", "source": [" / ".join(t.text for t in s.findall("TRANSL"))[:80]],
                   "cells": {"norm": [["FORM notes", " | ".join(new)]], "leave": [["FORM notes", n]]}})
cards.append({"id": "r3-tags", "corpus": "Safolu", "flag": False,
              "title": "The reduplication tag 〔疊 2〕 left behind as a 'definition'",
              "count": f"{len(titems)} headwords: 10 with 〔疊 2〕 (all in section 23 entries), 10 with a bare 〔疊〕 (no number)",
              "question": "Write these as the same 'Tag: [疊 N]' note the other 3,866 tagged headwords get, once?",
              "body": ["〔疊 N〕 marks a reduplicated form ([疊 1] 513 headwords, [疊 2] 3,308, [疊 3] 40, [疊 4] 6). The converter lifts it out of the definition only when it is written exactly 〔疊N〕 (parsing-content.rb: /〔疊\\d〕/); written with a space (97 of 98 such source paragraphs are in section 23) or without a number, it stayed behind as a sense. Your label ruling put those senses in FORM notes, so 8 headwords now carry the tag twice (Tag: [疊 2] … | 〔疊 2〕).",
                       "What the numbers mean is not documented in the repo; from examples it classifies the reduplication pattern (all 疊 3 samples repeat two syllables, e.g. mikelikeling ← keling), but I cannot state the rule."],
              "options": [{"key": "norm", "label": "One 'Tag: [疊 N]' note each", "rec": True, "desc": "The duplicate goes; a bare 〔疊〕 becomes Tag: [疊] (number unknown)."},
                          {"key": "leave", "label": "Leave as now", "desc": "As your label ruling has it."}],
              "items": titems})

# part-of-speech labels in 〔 〕 standing alone
POS = {r["label"] for r in csv.DictReader(open(W / "pos_labels.tsv", encoding="utf-8"), delimiter="\t") if r["treated_as_part_of_speech"] == "yes"}
pitems = []
for s in SS:
    f = s.find("FORM"); n = f.get("notes") or ""
    for p in n.split(" | "):
        m = re.match(r"^[〔\[]\s*([^〕\]]+?)\s*[〕\]][。.]?$", p.strip())
        if m and m.group(1) in POS:
            T = [t.text for t in s.findall("TRANSL")]
            pitems.append({"key": f"{f.text} ({s.get('id')})", "source": [p.strip()],
                           "cells": {"transl": [["TRANSL zho" + (" alt" if i else ""), t + f"   [notes: {m.group(1)}]"] for i, t in enumerate(T)],
                                     "form": [["FORM notes", n]] + [["TRANSL zho" + (" alt" if i else ""), t] for i, t in enumerate(T)]}})
cards.append({"id": "r3-label-pos", "corpus": "Safolu", "flag": False,
              "title": "A part-of-speech label standing alone in 〔 〕",
              "count": f"{len(pitems)} headwords (〔語氣助詞〕 'modal particle' ×3, 〔連接詞〕 'conjunction' ×1)",
              "question": "Treat these like your part-of-speech ruling (notes on the translations), or like your label ruling (FORM notes, as now)?",
              "body": ["Your part-of-speech ruling covered labels in （ ）; these four are in 〔 〕, which the round 1 label card covered (that card described its 165 senses as 'almost all 〔疊 2〕', which was wrong: about 140 are borrowing labels, 20 are 疊 tags, and these 4 are parts of speech). Standalone borrowing labels in any bracket go to FORM notes, consistent with your round 2 loan-label choice."],
              "options": [{"key": "transl", "label": "Notes on the translations (as your part-of-speech ruling)", "rec": True, "desc": "Same as （語氣助詞） elsewhere."},
                          {"key": "form", "label": "FORM notes (as now)", "desc": "As your label ruling has it."}],
              "items": pitems})

# translations that start with Amis text
aitems = []
for s in SS:
    for t in s.findall("TRANSL"):
        x = t.text or ""
        if re.match(r"^[A-Za-z'^]", x):
            aitems.append({"key": f"{s.find('FORM').text} ({s.get('id')})", "source": [" ‖ ".join(tt.text for tt in s.findall("TRANSL"))[:140]],
                           "cells": {"cur": [["TRANSL zho", x]]}})
cards.append({"id": "r3-amis-tails", "corpus": "Safolu", "flag": True,
              "title": "Translations that start with Amis text",
              "count": f"{len(aitems)} translations",
              "question": "Most of these are the tail of an example sentence broken off at a source paragraph break (e.g. mitapayan 'ko tamako. 煙葉烘乾了。'). Rebuild them into example sentences like the card above (shown to you before anything is added), leave them as translations, or leave them out? Flag any row that is a real translation (e.g. lintoking 'X光').",
              "body": ["Not caught by the example-sentence test (fewer than three Amis words before the Chinese) or by the broken-translation test (they end with 。)."],
              "options": [{"key": "rebuild", "label": "Rebuild them as example sentences (next round)", "rec": True, "desc": "Flagged rows stay as translations."},
                          {"key": "leave", "label": "Leave them as translations", "desc": "As now."},
                          {"key": "drop", "label": "Leave them out", "desc": "Flagged rows stay as translations."}],
              "cols": [{"key": "cur", "head": "Published now"}], "keyhead": "Headword", "srchead": "All translations of that S",
              "items": aitems})

# ---- page
t = (W / "page_template_r2.html").read_text(encoding="utf-8")
def rep(a, b):
    global t
    assert a in t, a[:70]
    t = t.replace(a, b)
rep("<title>Dictionary Headwords Round 2</title>", "<title>Dictionary Headwords Round 3</title>")
rep("FormosanBank · decisions round 2", "FormosanBank · decisions round 3")
t = t.replace("meta/round2", "meta/round3")
rep("const answers = {}; let db = null; let doneFlag = false;", "const answers = {}; let db = null; let doneFlag = false; const EXPANDED = new Set();")
rep("if (i >= LIMIT) tr.hidden = true;", "if (i >= LIMIT && !EXPANDED.has(card.id)) tr.hidden = true;")
rep("if (card.items.length > LIMIT){\n          const more", "if (card.items.length > LIMIT && !EXPANDED.has(card.id)){\n          const more")
rep("more.addEventListener('click', () => { for (const r of tb.rows) r.hidden = false; more.remove(); });",
    "more.addEventListener('click', () => { EXPANDED.add(card.id); for (const r of tb.rows) r.hidden = false; more.remove(); });")
old = (W / "dictionary-headwords-round2.html").read_text(encoding="utf-8")
log1 = re.search(r'<table class="log">.*?<tbody>(.*?)</tbody>', old, re.S).group(1)
q = html.escape
R2 = [("r2-borrow", "The list is right", "Applied: 797 borrowing labels moved to TRANSL notes (borrow_labels.tsv)."),
      ("r2-loanonly", "FORM notes, like the 〔 〕 ones", "Applied: 21 senses."),
      ("r2-pos", "Move it to TRANSL notes (as ILRDF). Note: \"Please do this using a tsv of parts of speech for better transparency. The TSV should be linked to in the appropriate part of the doc's description of the processing pipeline.\"", "Applied from pos_labels.tsv (98 senses); the TSV goes into CodeAndDocs/ and the README's pipeline section links to it at the build."),
      ("r2-poslabels", "Change it (see note); 12 flags. Note: \"The ones I have flagged so far can be left alone. Right now, to expand so I can see the additional rows, every time I flag something it collapses again. Can you prevent that?\"", "Flagged labels stay in the text. Fixed: 'Show all' stays open. Card carried over for the rest."),
      ("r2-cut-paste", "Paste them back together", "Applied: 90 rejoined."),
      ("r2-cut-lost", "No choice. Note: \"Which versions result in grammatical Chinese? \"", "Answered on the card (carried over)."),
      ("r2-embedded", "Add them (flagged rows aside); 13 flags. Note: \"Some of these were clearly sentence fragments. I think I flagged them all. I don't know if they are part of your identified broken lines. \"", "Checked: 70 of the 103 are broken across source paragraphs, including all 13 you flagged; rebuilt versions on a new card. The 33 whole ones are added as ruled (at the build)."),
      ("r2-f-affix", "Leave them out", "Applied: 8 Fey prefixes."),
      ("r2-f-fixme", "Drop only the marked part", "Applied: sinawar and sorar keep their unmarked Chinese; the English note names the dropped part."),
      ("Unanswered", "r2-sections, r2-heading, r2-cut-unchecked, r2-homs-notreview", "Carried over."),
      ("〔疊 2〕 (chat)", "\"This is a weird definition that appears more than a few times, What's going on with it? 〔疊 2〕\"", "Explained on the new tag card.")]
rows2 = "".join(f"<tr><td class='mono'>{q(a)}</td><td>{q(b)}</td><td>{q(c)}</td></tr>" for a, b, c in R2)
LOG = f"""<section class="panel"><h2>Round 2: what you decided and what I applied</h2>
<div class="scroll"><table class="log"><thead><tr><th>Card</th><th>Your answer</th><th>What I did (observed in the draft build)</th></tr></thead><tbody>{rows2}</tbody></table></div>
<p><b>Draft now</b>: Safolu 42,318 headword S, 56,271 TRANSL (sections 23/24 treated like any other entry while your ruling is on hold); Fey 4,696 headword S. Nothing is committed to the corpora yet.</p>
<details><summary>Round 1 and chat rulings (log)</summary><div class="scroll"><table class="log"><thead><tr><th>Card</th><th>Your answer</th><th>What I did</th></tr></thead><tbody>{log1}</tbody></table></div></details></section>"""
intro = ("Round 3: the four round 2 cards you have not answered yet, the part-of-speech label list (still being checked), your grammar question on the lost-character card, "
         "and four new cards: the 70 example sentences rebuilt across the source's paragraph breaks, the 疊 tag, four part-of-speech labels in 〔 〕, and 82 translations that start with Amis text. "
         "'Show all' now stays open while you flag rows.")
t = t.replace("__INTRO__", intro).replace("__LOG__", LOG).replace("__DATA__", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/"))
(W / "dictionary-headwords-round3.html").write_text(t, encoding="utf-8")
print(len(cards), "cards:", [(c["id"], len(c["items"])) for c in cards], f"{len(t)/1e6:.2f} MB")
