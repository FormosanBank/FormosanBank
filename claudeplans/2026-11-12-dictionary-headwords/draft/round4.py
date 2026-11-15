#!/usr/bin/env python3
"""Round 4 page: round 3's open cards (two recomputed on the current draft) + affix and letter-entry cards.

Usage: python3 -I round4.py <WORK>   -> draft/dictionary-headwords-round4.html
Inputs: dictionary-headwords-round3.html (its cards and log), out_r3 draft XML, pos_labels.tsv, page_template_r2.html.
"""
import csv, html, json, pathlib, re, sys
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1]) / "draft"
old = (W / "dictionary-headwords-round3.html").read_text(encoding="utf-8")
C3 = {c["id"]: c for c in json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', old, re.S).group(1).replace("<\\/", "</"))}
SS = list(ET.parse(W / "out_r3/XML/Amis/Safolu/amis_safolu_headwords.xml").getroot().iter("S"))
POS = {r["label"] for r in csv.DictReader(open(W / "pos_labels.tsv", encoding="utf-8"), delimiter="\t") if r["treated_as_part_of_speech"] == "yes"}
cards = []
cards.append(C3["r2-sections"])

hd = C3["r2-heading"]
hd["body"] = ["Your question: \"Please give me a list of the forms specifically. What is the phrase followed by a colon?\" The phrase is almost always 主要表示： 'mainly indicates:' (9 of 11); a has 用法如下： 'used as follows:'; mi has (前綴)。自主性的施動動詞，其後有及物動詞的主要形態標誌，主要表示：; tano has 前綴，主要表示：. Each row shows the headword's senses; the colon heading is the one that ends in ：.",
              "Most of these 11 headwords are prefixes written without a hyphen (mi, pi, piki, pisa, pasa, tano, hasaka, hasapa, taha). Your affix ruling covered hyphenated forms only; the new affix card below asks about all 81 such headwords. If they are left out there, this card only matters for 'i and a."]
cards.append(hd)
for k in ("r2-cut-lost", "r2-homs-notreview", "r3-embedded-rebuilt", "r3-tags"):
    cards.append(C3[k])

# r3-label-pos recomputed (短語 is now a part of speech)
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
lp = C3["r3-label-pos"]; lp["items"] = pitems
lp["count"] = f"{len(pitems)} headwords (〔語氣助詞〕 ×3, 〔連接詞〕 ×1, and 〔短語〕 ×2 now that you count 短語 as a part of speech)"
cards.append(lp)

# r3-amis-tails recomputed on the current draft (after the 57 pastes)
aitems = []
for s in SS:
    for t in s.findall("TRANSL"):
        x = t.text or ""
        if re.match(r"^[A-Za-z'^]", x):
            aitems.append({"key": f"{s.find('FORM').text} ({s.get('id')})", "source": [" ‖ ".join(tt.text for tt in s.findall("TRANSL"))[:140]], "cells": {"cur": [["TRANSL zho", x]]}})
at = C3["r3-amis-tails"]; at["items"] = aitems; at["count"] = f"{len(aitems)} translations"
cards.append(at)

# affix headwords written without a hyphen
AFF = re.compile(r"前綴|後綴|詞綴|前後綴|中綴")
NOTAFF = {"ciciping", "cicipingay", "kaciciping", "kacicipingan", "paciping", "pacipingay", "pacipingen", "sakaciciping", "sakacicipingaw"}
LETTER = re.compile(r"阿美語[族的]?[元輔母]音之一|阿美語的?輔音之一")
fitems = []; kinds = {"only": 0, "mixed": 0, "not": 0}
for s in SS:
    f = s.find("FORM"); T = s.findall("TRANSL")
    if not any(AFF.search((t.get("notes") or "") + " " + (t.text or "")[:12]) for t in T):
        continue
    w = f.text
    if w in NOTAFF:
        read = "my reading: a word whose meaning mentions an affix (詞綴), not an affix entry"; kinds["not"] += 1
    elif any(LETTER.search(t.text or "") for t in T):
        read = "my reading: a letter entry with affix senses (see the letter card)"; kinds["mixed"] += 1
    else:
        read = "my reading: affix entry; check for word senses mixed in"; kinds["only"] += 1
    fitems.append({"key": f"{w} ({s.get('id')})", "source": [read],
                   "cells": {"cur": [["TRANSL zho" + (" alt" if i else ""), (t.text or "") + (f"   [notes: {t.get('notes')}]" if t.get("notes") else "")] for i, t in enumerate(T)]}})
cards.append({"id": "r4-affixes", "corpus": "Safolu", "flag": True,
              "title": "Affix entries written without a hyphen",
              "count": f"{len(fitems)} published headwords have a sense that calls them a prefix or suffix (前綴, 後綴, 詞綴); {kinds['not']} of them are, by my reading, ordinary words whose meaning mentions an affix",
              "question": "Your affix ruling ('Leave them out') covered headwords written with a hyphen or … (41). These are the same kind written without one, e.g. pi 前綴。主要表示：命令、請求對方從事某種行為。 Some also have ordinary word senses under the same spelling, e.g. kali: prefix 均分，等分 and noun 水溝，小水渠 'ditch'; pala: prefix and 曠野 'wilderness'. What should happen?",
              "body": ["Every row shows everything the draft publishes for that headword now. Flag rows where my reading (in the second column) is wrong.",
                       "Under 'Leave out the affix senses', I show you each headword's split (which senses are the affix, which are a word) on the next page before anything changes; the upstream entries do not mark where an affix's list of meanings ends."],
              "options": [{"key": "split", "label": "Leave out the affix senses, keep word senses (show me the split first)", "rec": True, "desc": "Like your affix ruling; a headword with only affix senses is left out."},
                          {"key": "all", "label": "Leave out every headword listed (flagged rows aside)", "desc": "Word senses under the same spelling go too."},
                          {"key": "keep", "label": "Publish them as now", "desc": ""}],
              "cols": [{"key": "cur", "head": "Published now"}], "keyhead": "Headword", "srchead": "My reading",
              "items": fitems})

# letter entries
litems = []
for s in SS:
    T = s.findall("TRANSL")
    if any(LETTER.search(t.text or "") for t in T):
        litems.append({"key": f"{s.find('FORM').text} ({s.get('id')})", "source": [f"{len(T)} senses"],
                       "cells": {"cur": [["TRANSL zho" + (" alt" if i else ""), t.text or ""] for i, t in enumerate(T)]}})
cards.append({"id": "r4-letters", "corpus": "Safolu", "flag": False,
              "title": "Entries for the letters of the alphabet",
              "count": f"{len(litems)} headwords (' a c d e f h i k l m n ng o p r s t w x y): each section of the dictionary opens with an entry for its letter",
              "question": "These describe a sound (e.g. k: 阿美語輔音之一。屬舌面後清塞音，不送氣…), not a word. a, i and o also have word senses (a: prefix, conjunction; i: 在（某處） 'at'; o: demonstrative, 至於 'as for'). What should happen?",
              "body": ["Each row shows everything the draft publishes now. The sound descriptions run over several senses because the converter split them at each 。."],
              "options": [{"key": "drop-desc", "label": "Leave out the sound descriptions, keep word senses", "rec": True, "desc": "18 letters are left out; a, i, o keep their word senses (shown next page)."},
                          {"key": "keep", "label": "Publish them as now", "desc": ""},
                          {"key": "drop-all", "label": "Leave out all 21 headwords", "desc": "a, i, o's word senses go too."}],
              "cols": [{"key": "cur", "head": "Published now"}], "keyhead": "Headword", "srchead": "",
              "items": litems})

# ---- page
t = (W / "page_template_r2.html").read_text(encoding="utf-8")
def rep(a, b):
    global t
    assert a in t, a[:70]
    t = t.replace(a, b)
rep("<title>Dictionary Headwords Round 2</title>", "<title>Dictionary Headwords Round 4</title>")
rep("FormosanBank · decisions round 2", "FormosanBank · decisions round 4")
t = t.replace("meta/round2", "meta/round4")
rep("const answers = {}; let db = null; let doneFlag = false;", "const answers = {}; let db = null; let doneFlag = false; const EXPANDED = new Set();")
rep("if (i >= LIMIT) tr.hidden = true;", "if (i >= LIMIT && !EXPANDED.has(card.id)) tr.hidden = true;")
rep("if (card.items.length > LIMIT){\n          const more", "if (card.items.length > LIMIT && !EXPANDED.has(card.id)){\n          const more")
rep("more.addEventListener('click', () => { for (const r of tb.rows) r.hidden = false; more.remove(); });",
    "more.addEventListener('click', () => { EXPANDED.add(card.id); for (const r of tb.rows) r.hidden = false; more.remove(); });")
q = html.escape
R3 = [("r2-cut-unchecked", "Paste them back together. Note: \"For notes and caveats: 57 items appeared to Claude to have had single definitions split into two. These have been repaired, but not all have been checked by a human. See a list at [INSERT LINK HERE]. ----- Note that I intend for you to link to the TSV and replace the `[INSERT LINK HERE]`. That same tsv should be noted in the processing pipeline section of the doc.\"", "Applied: 57 rejoined (147 in all). List written to repaired_breaks_unchecked.tsv; the caveat, with the link, and the pipeline-section mention go into the README at the build. Rows I had marked ⚑ are pasted as they are, e.g. dadasa'en 要奉祀、祭奠的（象）。"),
      ("r2-poslabels", "The yes/no column is right; flag 短語. Note: \"\"短語\" can be treated as a part of speech. Otherwise parantheticals that you marked as not part of speech can be left in the definitons.\"", "Applied: 短語 marked yes in pos_labels.tsv; 205 part-of-speech labels now in TRANSL notes. All other bracketed labels stay in the text."),
      ("r2-heading", "No choice. Note: \"Please give me a list of the forms specifically. What is the phrase followed by a colon?\"", "Answered on the card (carried over). Most of these headwords are prefixes written without a hyphen: new card.")]
rows3 = "".join(f"<tr><td class='mono'>{q(a)}</td><td>{q(b)}</td><td>{q(c)}</td></tr>" for a, b, c in R3)
prev = re.search(r'(<section class="panel"><h2>Round 2: what you decided.*?</section>)', old, re.S).group(1)
prev = prev.replace('<section class="panel"><h2>Round 2: what you decided and what I applied</h2>', '<details><summary>Round 2 (log)</summary>').replace("</section>", "</details>")
prev = re.sub(r"<p><b>Draft now</b>.*?</p>", "", prev, flags=re.S)
LOG = f"""<section class="panel"><h2>Round 3: what you decided and what I applied</h2>
<div class="scroll"><table class="log"><thead><tr><th>Card</th><th>Your answer</th><th>What I did (observed in the draft build)</th></tr></thead><tbody>{rows3}</tbody></table></div>
<p><b>Draft now</b>: Safolu 42,318 headword S, 56,145 TRANSL (sections 23/24 treated like any other entry while your ruling is on hold); Fey 4,696 headword S. Nothing is committed to the corpora yet.</p>
{prev}</section>"""
intro = ("Round 4: round 3's open cards (the heading card now lists the phrases you asked for), and two new ones the heading list led to: "
         "affix entries written without a hyphen (81), and the entries for the letters of the alphabet (21). 'Show all' stays open while you flag rows.")
t = t.replace("__INTRO__", intro).replace("__LOG__", LOG).replace("__DATA__", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/"))
(W / "dictionary-headwords-round4.html").write_text(t, encoding="utf-8")
print(len(cards), "cards:", [(c["id"], len(c["items"])) for c in cards], f"{len(t)/1e6:.2f} MB")
