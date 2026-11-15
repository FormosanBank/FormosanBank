#!/usr/bin/env python3
"""Round 5 page: round 4's open cards + checks of how round 4 was applied.

Usage: python3 -I round5.py <WORK>   -> draft/dictionary-headwords-round5.html
Inputs: dictionary-headwords-round4.html (cards, log), out_r5 draft XML, log_r5.json, amis_tails_rebuild.tsv,
        example_pieces_removed.tsv, page_template_r2.html.
"""
import csv, html, json, pathlib, re, sys
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1]) / "draft"
old = (W / "dictionary-headwords-round4.html").read_text(encoding="utf-8")
C4 = {c["id"]: c for c in json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', old, re.S).group(1).replace("<\\/", "</"))}
SS = list(ET.parse(W / "out_r5/XML/Amis/Safolu/amis_safolu_headwords.xml").getroot().iter("S"))
BY = {s.find("FORM").text: s for s in SS}
LOG = json.load(open(W / "log_r5.json", encoding="utf-8"))
cards = [C4["r2-sections"]]

# heading card recomputed on the current draft
heads = []
for s in SS:
    T = [t.text or "" for t in s.findall("TRANSL")]
    if any(re.search(r"[：:]\s*$", x) for x in T):
        f = s.find("FORM").text
        heads.append({"key": f, "source": T, "cells": {"drop": [["FORM", f]] + [["TRANSL zho" + (" alt" if i else ""), x] for i, x in enumerate([x for x in T if not re.search(r"[：:]\s*$", x)])],
                                                       "keep": [["FORM", f]] + [["TRANSL zho" + (" alt" if i else ""), x] for i, x in enumerate(T)]}})
hd = C4["r2-heading"]; hd["items"] = heads
hd["count"] = f"{len(heads)} headwords left once your affix and letter rulings are applied (the prefixes that had 主要表示： are gone)"
hd["body"] = ["Your question: \"Please give me a list of the forms specifically. What is the phrase followed by a colon?\" It is almost always 主要表示： 'mainly indicates:'; 'a' has 用法如下： 'used as follows:'. With your affix ruling applied, these are the headwords still carrying one. Each row shows every translation; the heading is the one ending in ：."]
cards.append(hd)
cards.append(C4["r2-homs-notreview"])

# affix senses for approval
STRONG = re.compile(r"^(用法如下：)?(（\d）)?\s*[(（〔\[]?\s*(複合|復合)?(前綴|後綴|前後綴)(詞)?\s*[)）〕\]]?\s*[。，,:：]?")
aff = []
for s in SS:
    w = s.find("FORM").text
    for t in s.findall("TRANSL"):
        x = t.text or ""; n = t.get("notes") or ""
        m = STRONG.match(x)
        if (m and m.group(4)) or "詞綴" in n:
            why = "its notes say 詞綴 'affix' (moved there from (詞綴) by your part-of-speech ruling); your affix rule names only 前綴 and 後綴" if "詞綴" in n else f"the text itself starts with {m.group(0).strip()} without brackets, so it never became a note"
            aff.append({"key": f"{w} · {x[:20]}", "source": [why], "cells": {"drop": [["—", f"left out: {x}"]], "keep": [["TRANSL zho", x]]}})
cards.append({"id": "r5-affix-approval", "corpus": "Safolu", "flag": True,
              "title": "Senses I believe are affix meanings, for your approval",
              "count": f"{len(aff)} senses",
              "question": "Your affix rule: \"Senses that are marked explicitly as affixes (後綴 or 前綴 in parentheses or brackets, now listed as a note attribute) should be left out. Others can be assumed to be non-affix senses unless you have a strong reason to believe they are affix meanings (in which case, please explain and list for my approval).\" Leave these out too? Flag any row to keep.",
              "body": ["Applied already: 33 senses marked 前綴 / 後綴 in brackets (including (複合前綴) 'compound prefix'), and the 9 headwords that had nothing else (haki, halo, hari, hasa, hasaka, hasapa, kana, maha, sapi).",
                       "My strong reason for each row below is in the second column: in almost every case the sense text itself begins with 前綴 'prefix', 複合前綴 'compound prefix' or 後綴 'suffix', written without brackets (e.g. pi 前綴。; la 前綴。主要表示：變成，演變成。). The exceptions: sato (its note says 詞綴 'affix', a word your rule did not name) and a ((1)前綴詞 'prefix', inside its numbered list of uses)."],
              "options": [{"key": "drop", "label": "Leave these out too (flagged rows aside)", "rec": True, "desc": "A headword left with no sense is not published."},
                          {"key": "keep", "label": "Keep them", "desc": "Only the bracketed ones stay out."}],
              "cols": [{"key": "drop", "head": "If left out"}], "keyhead": "Headword · sense", "srchead": "Why I believe it is an affix meaning",
              "items": aff})

# letters: show the split
lsplit = [x for x in LOG if x[0] == "letter-split"]
litems = [{"key": x[1], "source": ["left out: " + " ‖ ".join(x[2])], "cells": {"ok": [["TRANSL zho" + (" alt" if i else ""), y] for i, y in enumerate(x[3])] or [["—", "headword not published"]]}} for x in lsplit]
cards.append({"id": "r5-letters-split", "corpus": "Safolu", "flag": True,
              "title": "Letter entries: the split you asked to see",
              "count": f"{len(litems)} letter entries; {sum(1 for x in lsplit if not x[3])} are left out entirely, {sum(1 for x in lsplit if x[3])} (a, i, o) keep word senses",
              "question": "Your choice was 'Leave out the sound descriptions, keep word senses'. Is this split right? Flag any row that is wrong.",
              "body": ["A sense counts as a sound description when it talks about the sound (音值, 元音, 輔音, 詞尾, 送氣, 鼻音, 舌面 and similar). The affix rule also applies: i's 主要表示：存在，所在 is gone because it was marked （前綴）."],
              "options": [{"key": "ok", "label": "The split is right", "rec": True, "desc": "Flagged rows aside."},
                          {"key": "other", "label": "Change it (see note)", "desc": ""}],
              "cols": [{"key": "ok", "head": "Published"}], "keyhead": "Letter", "srchead": "Left out",
              "items": litems})

# example pieces removed (consequence of the rebuild ruling)
P = list(csv.DictReader(open(W / "example_pieces_removed.tsv", encoding="utf-8"), delimiter="\t"))
pitems = [{"key": f"{r['headword']} · {r['translation_removed']}", "source": [r["rebuilt_example"]],
           "cells": {"ok": [["—", f"removed: {r['translation_removed']}"]] + ([["—", "malingses has no other sense, so it is not published"]] if r["headword"] == "malingses" else [])}} for r in P]
cards.append({"id": "r5-pieces", "corpus": "Safolu", "flag": True,
              "title": "Pieces of the rebuilt example sentences that were still published as translations",
              "count": f"{len(P)} translations in {len({r['headword'] for r in P})} headwords; 1 headword (malingses) is left with no sense",
              "question": "When I rebuilt the 70 example sentences, I did not take their other pieces out of the headword. Each row is a translation that is only a piece of a sentence you approved as an example (e.g. mi'efeng 圾丟到垃圾桶。). I have removed them. Is that right? Flag any row that is a real translation.",
              "body": ["malingses had only two such pieces (感到噁心。 and 到噁心。), both from its example 'Tada malingses kako to pinangan ningra / 對他的行為感到噁心。'; with no definition left it is not published (your 'headwords with no definition' ruling)."],
              "options": [{"key": "ok", "label": "Right to remove them", "rec": True, "desc": "Flagged rows go back."},
                          {"key": "back", "label": "Put them all back", "desc": ""}],
              "cols": [{"key": "ok", "head": "Done"}], "keyhead": "Headword · translation", "srchead": "The example sentence it belongs to",
              "items": pitems})

# Amis-text translations: rebuild results
A = list(csv.DictReader(open(W / "amis_tails_rebuild.tsv", encoding="utf-8"), delimiter="\t"))
aitems = []
for r in A:
    mark = ""
    if r["result"] == "rebuilt" and re.match(r"^[a-z]", r["example_FORM"]):
        mark = "⚑ starts with a small letter: the sentence start may be further back"
    if r["headword"] == "ona":
        mark = "⚑ my reading: a definition ('the contraction of oni a'), not an example"
    if r["result"] == "rebuilt":
        cell = [["FORM", r["example_FORM"]], ["TRANSL zho", r["example_TRANSL_zho"]], ["—", f"taken out of the headword: {r['translation_now']}"]]
    elif r["result"] == "leave as translation":
        cell = [["TRANSL zho", r["translation_now"]], ["—", f"stays ({r['how']})"]]
    else:
        cell = [["TRANSL zho", r["translation_now"]], ["—", f"could not rebuild: {r['how']}" + (f" ({r['example_FORM'][:50]})" if r["example_FORM"] else "")]]
    aitems.append({"key": f"{r['headword']} ({r['S']})", "source": [r["translation_now"]] + ([mark] if mark else []), "cells": {"res": cell}})
n = {k: sum(1 for r in A if r["result"] == k) for k in ("rebuilt", "could not rebuild", "leave as translation")}
cards.append({"id": "r5-tails", "corpus": "Safolu", "flag": True,
              "title": "Translations that start with Amis text: the rebuild you asked for",
              "count": f"{len(A)} translations: {n['rebuilt']} rebuilt into example sentences, {n['could not rebuild']} could not be rebuilt, {n['leave as translation']} stay as translations under your rule; {sum(1 for i in aitems if any('⚑' in x for x in i['source']))} marked ⚑",
              "question": "Your choice: rebuild them, with the note \"Where the definition starts with a single word in latin characters following by mandarin with no intervening punctuation, leave as translation. Attempt rebuilding the others.\" Add the rebuilt sentences to the examples file (and take the piece out of the headword)? Flag any row that is wrong.",
              "body": ["Rebuilt from the converter's own input: the start of the Amis sentence is the end of the paragraph before (after its last 。！？), e.g. mitapayan 'ko tamako. 煙葉烘乾了。' → Mitapayan ko tamako / 煙葉烘乾了。",
                       "Rows that could not be rebuilt stay as translations unless you say otherwise in the note; most are definitions that mention an Amis word (taowanan 'tao 的賓格形態', ngarohngohay 'ngiha：指人的嗓音')."],
              "options": [{"key": "add", "label": "Add the rebuilt sentences (flagged rows aside)", "rec": True, "desc": "The others stay as translations."},
                          {"key": "leave", "label": "Leave all as translations", "desc": ""}],
              "cols": [{"key": "res", "head": "Result"}], "keyhead": "Headword", "srchead": "Translation now",
              "items": aitems})

# ---- page
t = (W / "page_template_r2.html").read_text(encoding="utf-8")
def rep(a, b):
    global t
    assert a in t, a[:70]
    t = t.replace(a, b)
rep("<title>Dictionary Headwords Round 2</title>", "<title>Dictionary Headwords Round 5</title>")
rep("FormosanBank · decisions round 2", "FormosanBank · decisions round 5")
t = t.replace("meta/round2", "meta/round5")
rep("const answers = {}; let db = null; let doneFlag = false;", "const answers = {}; let db = null; let doneFlag = false; const EXPANDED = new Set();")
rep("if (i >= LIMIT) tr.hidden = true;", "if (i >= LIMIT && !EXPANDED.has(card.id)) tr.hidden = true;")
rep("if (card.items.length > LIMIT){\n          const more", "if (card.items.length > LIMIT && !EXPANDED.has(card.id)){\n          const more")
rep("more.addEventListener('click', () => { for (const r of tb.rows) r.hidden = false; more.remove(); });",
    "more.addEventListener('click', () => { EXPANDED.add(card.id); for (const r of tb.rows) r.hidden = false; more.remove(); });")
q = html.escape
R4 = [("r2-cut-lost", "Restore from the 2015 text", "Applied: hacaen 重復一下, tili'ien 對…討厭, mipasikiwan 對…偏見, tona 系toni與a的連讀, papitoay 指所具有的七個."),
      ("r3-embedded-rebuilt", "Add the rebuilt sentences (flagged rows aside)", "Applied: 70 rebuilt + 33 whole = 103 new example sentences at the build. Also removed 29 leftover pieces of them from the headwords (check card below)."),
      ("r3-tags", "One 'Tag: [疊 N]' note each. Note: \"But where are you getting the stem from? \"", "Applied (20). The stem is the author's: the source prints it in brackets after the headword, e.g. 01-A.txt line 664 'acaen('aca); the converter (parsing-terms.rb) splits the headword line at the bracket, stores 'aca as the stem, and the JSON export writes it as \"stem\": \"'aca\"."),
      ("r3-label-pos", "Notes on the translations (as your part-of-speech ruling)", "Applied: hales, hani, haw (語氣助詞), orasaka (連接詞), hay awid, hayken makenaay (短語)."),
      ("r3-amis-tails", "Rebuild them as example sentences (next round); flags afa, a, f, k. Note: \"Where the definition starts with a single word in latin characters following by mandarin with no intervening punctuation, leave as translation. Attempt rebuilding the others. \"", "Rebuilt: results on a card below; nothing added yet."),
      ("r4-affixes", "No choice. Note: \"Senses that are marked explicitly as affixes (後綴 or 前綴 in parentheses or brackets, now listed as a note attribute) should be left out. Others can be assumed to be non-affix senses unless you have a strong reason to believe they are affix meanings (in which case, please explain and list for my approval). \"", "Applied: 33 bracketed affix senses left out; 9 headwords had nothing else. The ones I have a strong reason for are listed for approval below."),
      ("r4-letters", "Leave out the sound descriptions, keep word senses", "Applied: 18 letter entries left out; a, i, o keep word senses (split shown below)."),
      ("Unanswered", "r2-sections, r2-heading, r2-homs-notreview", "Carried over.")]
rows4 = "".join(f"<tr><td class='mono'>{q(a)}</td><td>{q(b)}</td><td>{q(c)}</td></tr>" for a, b, c in R4)
prev = re.search(r'(<section class="panel"><h2>Round 3: what you decided.*?</section>)', old, re.S).group(1)
prev = prev.replace('<section class="panel"><h2>Round 3: what you decided and what I applied</h2>', '<details><summary>Round 3 (log)</summary>').replace("</section>", "</details>")
prev = re.sub(r"<p><b>Draft now</b>.*?</p>", "", prev, flags=re.S)
LOGH = f"""<section class="panel"><h2>Round 4: what you decided and what I applied</h2>
<div class="scroll"><table class="log"><thead><tr><th>Card</th><th>Your answer</th><th>What I did (observed in the draft build)</th></tr></thead><tbody>{rows4}</tbody></table></div>
<p><b>Draft now</b>: Safolu 42,290 headword S, 56,031 TRANSL (sections 23/24 treated like any other entry while your ruling is on hold); Fey 4,696 headword S. Nothing is committed to the corpora yet.</p>
{prev}</section>"""
intro = ("Round 5: the three cards still unanswered, two checks you asked for (the letter split; the Amis-text rebuild), the affix senses I listed for your approval, "
         "and one check of my own (29 pieces of rebuilt example sentences I had left in the headwords).")
t = t.replace("__INTRO__", intro).replace("__LOG__", LOGH).replace("__DATA__", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/"))
(W / "dictionary-headwords-round5.html").write_text(t, encoding="utf-8")
print(len(cards), "cards:", [(c["id"], len(c["items"])) for c in cards], f"{len(t)/1e6:.2f} MB")
