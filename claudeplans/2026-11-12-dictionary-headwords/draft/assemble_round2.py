#!/usr/bin/env python3
"""Assemble dictionary-headwords-round2.html from page_template_r2.html + round2_*_cards.json.
Usage: python3 -I assemble_round2.py <WORK>"""
import html, json, pathlib, re, sys
W = pathlib.Path(sys.argv[1]) / "draft"
S = json.load(open(W / "round2_safolu_cards.json", encoding="utf-8"))
F = json.load(open(W / "round2_fey_cards.json", encoding="utf-8"))
for c in S + F:
    if c["id"] in ("r2-sec23", "r2-sec24"):
        c["cols"] = [{"key": "apply", "head": "Published if applied (dropped senses shown in red)"}]
    if c["id"] == "r2-poslabels":
        c["cols"] = [{"key": "ok", "head": "My proposal"}]; c["keyhead"] = "Label"; c["srchead"] = "Example"
    if c["id"] == "r2-borrow":
        c["cols"] = [{"key": "ok", "head": "Senses · example after the move · note text"}]; c["keyhead"] = "Label as printed"; c["srchead"] = "Example as printed"
    if c["id"] == "r2-embedded":
        c["cols"] = [{"key": "ok", "head": "New example S"}]; c["keyhead"] = "Headword"; c["srchead"] = "Definition field as printed"
cards = S + F
q = lambda s: html.escape(s)
LOG = [
 ("Sections 23 / 24 (chat)", "Do not record headwords from section 23 of Safolu. For section 24, include only headwords that do not appear in sections 1-22.", "Applied per sense from the converter's database: 370 section-23 senses and 77 section-24 senses dropped; 29 headwords printed only in section 23 left out. Shown in full on two cards below, plus a card for 41 words where the ruling and upstream's merging collide."),
 ("s-homophones", "Follow the book's entries, check the rest. Note: \"My decision here does NOT apply to section 23 or section 24. \"", "Not applied yet: needs its own review page for the main-section headwords printed as more than one entry (next round)."),
 ("s-version", "Editors' version (4cb82539d)", "Applied: the draft reads 4cb82539d."),
 ("s-xref", "Leave it out", "Applied."),
 ("s-label", "Put it in FORM notes", "Applied (this includes a sense that is only 〔日語借詞〕)."),
 ("s-nochinese", "Leave it out", "Applied."),
 ("s-embedded", "Move to the examples file", "Applied to the headwords (99 senses taken out). Adding them to the examples file waits for the check card below."),
 ("s-heading", "No choice; note: \"Many of these senses include part-of-speech information: （前後綴）（語氣助詞）（後綴） How have we been capturing that more generally in this corpus?\"", "Answered on the part-of-speech card; asked again below."),
 ("s-affix", "Leave them out", "Applied: 41 headwords (18 hyphenated, 23 circumfixes with …)."),
 ("s-nosense", "Leave them out", "Applied."),
 ("s-stemtag", "Put them in FORM notes", "Applied."),
 ("s-synrel", "Don't publish them", "Applied."),
 ("s-borrow", "Move it to TRANSL notes. Note: \"Have a list of these in a tsv, rather than listing them within the code. That way I can check the list. Also show me the list to check!\"", "List written to borrow_labels.tsv and shown below for checking; applied after you check it."),
 ("f-homophones", "One S per headword. Note: Notes & Caveats should say: \"Original source does not distinguish polysemy from homophony. Thus in the wordlist, any homophones are listed under a single headword, with the different homophones' meanings given as different senses.\"", "Applied (one S per headword); the README sentence goes in at the build, word for word."),
 ("f-split", "Keep each sense whole", "Applied."),
 ("f-xref", "Leave them out", "Applied: 144 headwords."),
 ("f-see", "Put them in FORM notes", "Applied: notes=\"See also: …\"."),
 ("f-fixme", "Drop those Chinese senses. Note: \"Add in note that a Chinese sense was marked \"fixme\" and as been dropped.\"", "Applied to all 6 cells; the English TRANSL of that sense carries the note. Two cells are only partly marked: one card below."),
 ("f-affix", "No answer saved", "Asked again below."),
]
rows = "".join(f"<tr><td class='mono'>{q(a)}</td><td>{q(b)}</td><td>{q(c)}</td></tr>" for a, b, c in LOG)
log = f"""<section class="panel"><h2>Round 1: what you decided and what I applied</h2>
<p class="muted">Read from this page's answer store on 2026-11-15 (17 of 18 cards answered) plus your chat message. Your words are quoted as saved.</p>
<div class="scroll"><table class="log"><thead><tr><th>Card</th><th>Your answer</th><th>What I did (observed in the draft build)</th></tr></thead><tbody>{rows}</tbody></table></div>
<p><b>Draft result with everything above applied</b> (Safolu, editors' version): 42,289 headword S if the 41 merged words are kept, 42,248 if not. Fey: 4,704 headword S. Nothing is committed to the corpora yet.</p></section>"""
intro = ("Round 2 holds only what is still open: how your section 23/24 ruling plays out (shown in full so you can check it), "
         "the part-of-speech labels (with the answer to your question), the heading card again, the borrowing-label list you asked to see, "
         "the check round for example sentences moving to the examples file, and two Fey cards. Cards that are lists have a <b>flag</b> button on each row: "
         "flag anything wrong. The review of main-section headwords printed as more than one entry (your 'follow the book' choice) comes on its own page next.")
t = open(W / "page_template_r2.html", encoding="utf-8").read()
t = t.replace("__INTRO__", intro).replace("__LOG__", log).replace("__DATA__", json.dumps(cards, ensure_ascii=False).replace("</", "<\\/"))
(W / "dictionary-headwords-round2.html").write_text(t, encoding="utf-8")
d = json.loads(re.search(r'<script id="data" type="application/json">(.*?)</script>', t, re.S).group(1).replace("<\\/", "</"))
print(len(d), "cards:", [c["id"] for c in d], f"{len(t)/1e6:.2f} MB")
