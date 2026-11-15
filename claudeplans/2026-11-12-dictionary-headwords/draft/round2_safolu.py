#!/usr/bin/env python3
"""Round 2 data for the Safolu headword page (editors' version 4cb82539d, round 1 rulings applied).

Usage: python3 -I round2_safolu.py <WORK>
Reads  draft/section_rulings_4cb8.json (apply_section_rulings.py), src/4cb8/docs/s, src/e7c6976/docs/s (examples check)
Writes draft/round2_safolu_cards.json, draft/borrow_labels.tsv, draft/pos_labels.tsv, draft/embedded_examples.tsv

Round 1 rulings applied before anything is listed (decision log 2026-11-15):
  sections: drop senses traced to section 23; drop section-24 senses of headwords printed in 01-22
  s-version editors; s-xref drop; s-nochinese drop; s-affix omit; s-nosense omit
"""
import collections, csv, json, pathlib, re, sys
import xml.etree.ElementTree as ET

W = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(W / "draft"))
from safolu_headwords import clean, classify, SPECIAL  # noqa: E402

EB = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (W / "src/4cb8/docs/s").glob("*.json") if p.name not in SPECIAL}
RUL = json.load(open(W / "draft/section_rulings_4cb8.json", encoding="utf-8"))
AFFIX = lambda t: t.startswith("-") or t.endswith("-") or "…" in t
EMB = re.compile(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([㐀-鿿].*)$")
HEAD = re.compile(r"[：:]\s*$")
LEAD = re.compile(r"^[（(]([^（）()]{1,14})[）)]\s*[。.]?\s*")
LOAN = re.compile(r"[（(〔〈\[［]([^（）()〔〕〈〉\[\]［］]*借[詞語][^（）()〔〕〈〉\[\]［］]*)[）)〕〉\]］]")
# Labels I propose to treat as parts of speech (the maintainer checks this list on the page).
POS = {"前綴", "後綴", "前後綴", "中綴", "詞綴", "感嘆詞", "感歎詞", "語氣助詞", "語氣詞", "助詞", "指示代詞", "代詞", "代名詞",
       "人稱代詞", "疑問代詞", "疑問詞", "連接詞", "連詞", "量詞", "介詞", "副詞", "數詞", "名詞", "動詞", "形容詞", "擬聲詞",
       "格位標記", "否定詞", "語助詞", "動詞詞綴"}


def senses_after_rulings(stem):
    """[(h, d, cleaned text, action)] for the editors' version; action from the section ledger or 'keep'."""
    e = EB[stem]; acts = RUL.get(stem)
    out = []
    for i, h in enumerate(e["h"]):
        for j, d in enumerate(h.get("d", [])):
            a = acts[i][j] if acts else "keep"
            out.append((i, j, clean(d.get("f", "")), a))
    return out


def kept(rows):
    return [r for r in rows if r[3] == "keep" and classify(r[2]) not in ("empty", "xref", "nochinese", "label")]


def tidy(x):
    """text after a label is moved out: collapse spaces, doubled 。, trailing commas"""
    x = re.sub(r"\s+", " ", x).strip()
    x = re.sub(r"\s+([。，、；])", r"\1", x)
    x = re.sub(r"。+", "。", x)
    return x.strip(" ，,、；;") or "(nothing left)"


cards = []
ledger = list(csv.DictReader(open(W / "draft/section_rulings_4cb8.tsv", encoding="utf-8"), delimiter="\t"))
by_hw = collections.defaultdict(list)
for x in ledger:
    by_hw[x["headword"]].append(x)
stem_of = {e["t"]: s for s, e in EB.items()}

# ---- merged: printed in 01-22 and in 23/24, every surviving sense traced to 23/24
merged = [w for w, v in by_hw.items() if all(x["action"] != "keep" for x in v) and "main" in v[0]["printed_in"]]
only23 = [w for w, v in by_hw.items() if all(x["action"] != "keep" for x in v) and v[0]["printed_in"] == "23"]


def row_lines(rows, show_drop):
    L = []
    for i, j, t, a in rows:
        if classify(t) in ("empty", "xref", "nochinese"):
            continue
        if a == "keep":
            L.append(["TRANSL zho", t])
        elif show_drop:
            L.append(["—", f"dropped ({a[-2:]}): {t}"])
    return L or [["—", "headword not published"]]


items = []
for w in sorted(merged):
    rows = senses_after_rulings(stem_of[w])
    items.append({"key": w, "source": [f"{x['text']}  [traced to section {x['matched_section']}, score {x['score']}]" for x in by_hw[w]],
                  "cells": {"keep": [["FORM", w]] + [["TRANSL zho" if k == 0 else "TRANSL zho alt", r[2]] for k, r in enumerate(rows) if classify(r[2]) not in ("empty", "xref", "nochinese")],
                            "drop": [["—", "headword not published"]]}})
cards.append({"id": "r2-merged", "corpus": "Safolu", "flag": False,
              "title": "Words printed in sections 1-22 whose only upstream sense is the section 23/24 wording",
              "count": f"{len(merged)} headwords ({sum(1 for w in merged if '23' in by_hw[w][0]['printed_in'])} with section 23, {sum(1 for w in merged if '24' in by_hw[w][0]['printed_in'])} with section 24)",
              "question": "Upstream has already merged the two printed versions of these words into one sense, and its text is closer to the section 23/24 wording. Publish the headword with that sense, or leave the headword out?",
              "body": ["Your ruling: \"Do not record headwords from section 23 of Safolu. For section 24, include only headwords that do not appear in sections 1-22.\" These words are printed in sections 1-22 too, so the ruling keeps the headword; but the only sense upstream still has was matched (by text similarity to the converter's database) to the section 23/24 version. Example: hako is printed in section 06 as 箱子，盒子。(日語借詞)。 and in section 24 as 箱子〈日語借詞〉。; upstream now has one sense, 箱子，盒子〈日語借詞〉。",
                       "How the section of each sense was found: the converter's own database (miaoski/amis-safolu, db/amis-sqlite3-db.sqlite3) records the entries in file order (section 23 = database rows 40942-41609, section 24 = rows flagged loanword). Each upstream sense was matched to the database sense with the most similar text."],
              "options": [{"key": "keep", "label": "Publish the headword with this sense", "rec": True, "desc": "The word is in sections 1-22, so it is published; its text is upstream's merged sense."},
                          {"key": "drop", "label": "Leave the headword out", "desc": f"{len(merged)} headwords that are printed in sections 1-22 are not published."}],
              "items": items})


def sec_card(cid, which, title, extra_body):
    hws = sorted(w for w, v in by_hw.items() if any(x["action"] == f"drop-{which}" for x in v) and w not in merged)
    nsen = sum(1 for w in hws for x in by_hw[w] if x["action"] == f"drop-{which}")
    rev = sum(1 for w in hws for x in by_hw[w] if x["action"] == f"drop-{which}" and x["review"])
    gone = [w for w in hws if all(x["action"] != "keep" for x in by_hw[w])]
    its = []
    for w in hws:
        rows = senses_after_rulings(stem_of[w])
        src = [("⚑ " if x["review"] else "") + f"{x['text']}  [section {x['matched_section']}, score {x['score']}]" for x in by_hw[w]]
        its.append({"key": w, "source": src, "cells": {"apply": row_lines(rows, True),
                                                      "leave": [["TRANSL zho", r[2]] for r in rows if classify(r[2]) not in ("empty", "xref", "nochinese")]}})
    cards.append({"id": cid, "corpus": "Safolu", "flag": True, "title": title,
                  "count": f"{nsen} senses dropped in {len(hws)} headwords; {len(gone)} headwords are left out entirely; {rev} senses marked ⚑ were matched with a text-similarity score under 0.75",
                  "question": "Is this what you meant? Flag any row that is wrong.",
                  "body": extra_body + ["Score = how similar the upstream sense is to the database sense it was matched to (1.00 = identical). ⚑ marks a weak match: check those rows first."],
                  "options": [{"key": "apply", "label": "Apply as listed", "rec": True, "desc": "These senses are not published (flagged rows aside)."},
                              {"key": "leave", "label": "Leave as is", "desc": "Nothing is dropped; say in the note what you want instead."}],
                  "items": its})
    return len(hws), nsen, len(gone)


n23 = sec_card("r2-sec23", "23", "Section 23: the senses your ruling removes",
               [f"Your ruling: \"Do not record headwords from section 23 of Safolu.\" Applied to the editors' version: every upstream sense matched to a section-23 entry is dropped. The {len(only23)} headwords printed only in section 23 are left out; the other headwords keep their sections 1-22 senses."])
n24 = sec_card("r2-sec24", "24", "Section 24: the senses your ruling removes from words also in sections 1-22",
               ["Your ruling: \"For section 24, include only headwords that do not appear in sections 1-22.\" The 480 or so loanwords printed only in section 24 are published as usual. Where a section-24 headword is also printed in sections 1-22, its section-24 senses are dropped. This includes 13 words that are spelled alike but mean something else, e.g. mita (section 14: 我們 'we'; section 24: 電錶 'meter'), kita (木屐 'geta', 吉他 'guitar'), sato (砂糖 'sugar'), kasa (傘 'umbrella'), iki (車站 'station'), tofa (豆花 'tofu pudding'): the loanword sense is not published."])

# ---- part-of-speech labels
lab = collections.Counter(); lab_ex = {}
pos_rows = []  # (headword, kind, label, sense)
for s, e in sorted(EB.items()):
    t = e["t"]
    if AFFIX(t):
        continue
    rows = kept(senses_after_rulings(s))
    for i, j, x, a in rows:
        m = LEAD.match(x)
        if not m:
            continue
        L = m.group(1).strip()
        lab[L] += 1; lab_ex.setdefault(L, f"{t}: {x}")
        if L in POS:
            pos_rows.append((t, "only" if not x[m.end():].strip(" 。.") else "lead", L, x))
with open(W / "draft/pos_labels.tsv", "w", encoding="utf-8", newline="") as f:
    wr = csv.writer(f, delimiter="\t"); wr.writerow(["label", "senses", "treated_as_part_of_speech", "example"])
    for L, n in lab.most_common():
        wr.writerow([L, n, "yes" if L in POS else "no", lab_ex[L]])
pos_items = []
for t in sorted({r[0] for r in pos_rows}):
    rows = kept(senses_after_rulings(stem_of[t]))
    notes_cells, cur = [], {}
    # labels apply to the senses after them in the same h, until the next label; a leading label applies to its own sense
    out = []
    for i, j, x, a in rows:
        m = LEAD.match(x); L = m.group(1).strip() if m else None
        if L in POS and not x[m.end():].strip(" 。."):
            cur[i] = L; continue
        if L in POS:
            out.append((x[m.end():].strip(), L)); cur[i] = cur.get(i)
            continue
        out.append((x, cur.get(i)))
    ncell = [["FORM", t]] + [["TRANSL zho" + (" alt" if k else ""), x + (f"   [notes: {L}]" if L else "")] for k, (x, L) in enumerate(out)]
    lcell = [["FORM", t]] + [["TRANSL zho" + (" alt" if k else ""), r[2]] for k, r in enumerate(rows)]
    pos_items.append({"key": t, "source": [r[2] for r in rows], "cells": {"notes": ncell, "leave": lcell}})
n_only = sum(1 for r in pos_rows if r[1] == "only"); n_lead = sum(1 for r in pos_rows if r[1] == "lead")
cards.append({"id": "r2-pos", "corpus": "Safolu", "flag": True, "title": "Part-of-speech labels at the start of a sense",
              "count": f"{n_only + n_lead} senses in {len(pos_items)} headwords: {n_only} are only a label such as （語氣助詞）。, {n_lead} start with one, e.g. （感嘆詞）表示驚嘆：啊呀",
              "question": "Move the part-of-speech label to the notes of the translation(s) it applies to, as ILRDF does, or leave it in the text as printed?",
              "body": ["Your question (on the heading card): \"Many of these senses include part-of-speech information: （前後綴）（語氣助詞）（後綴） How have we been capturing that more generally in this corpus?\"",
                       "Answer, checked in the published XML: one corpus records parts of speech, ILRDF_Dicts, on each sense's translation note, e.g. <TRANSL xml:lang=\"zho\" notes=\"動詞\"> (38,756 動詞 'verb' and 10,553 名詞 'noun' notes). Its README: \"A sense's part of speech rides on that sense's TRANSL/@notes.\" No other corpus records parts of speech; the schema's class attribute exists only on W and M and no corpus uses it. Safolu prints the label inside the definition.",
                       "Upstream often keeps a label as a sense of its own: 'i has （語氣助詞）。 followed by 表示疑問。 and 呢。, then （連接詞）。 followed by its senses. Under 'Move', a label that stands alone applies to the senses after it in the same entry, up to the next label; a label at the start of a sense applies to that sense.",
                       "Which labels count as parts of speech is on the next card (my proposal; please check it)."],
              "options": [{"key": "notes", "label": "Move it to TRANSL notes (as ILRDF)", "rec": True, "desc": "TRANSL text without the label; notes=\"語氣助詞\". A label standing alone is not published as a translation."},
                          {"key": "leave", "label": "Leave it in the text", "desc": "As printed, including senses that are only （語氣助詞）。"}],
              "items": pos_items})
lab_items = [{"key": L, "source": [lab_ex[L]], "cells": {"ok": [["count", str(n)], ["part of speech?", "yes" if L in POS else "no"]]}}
             for L, n in sorted(lab.items(), key=lambda kv: (kv[0] not in POS, -kv[1], kv[0]))]
cards.append({"id": "r2-poslabels", "corpus": "Safolu", "flag": True, "title": "Which bracketed labels count as parts of speech",
              "count": f"{len(lab)} different labels open a sense ({sum(lab.values())} senses); I propose {sum(1 for L in lab if L in POS)} of them as parts of speech",
              "question": "Is my yes/no right for each label? Flag any row where it is wrong. (File: pos_labels.tsv.)",
              "body": ["Only labels marked yes are affected by the previous card. The others stay in the text: most restrict the meaning, e.g. （東西）'of things', （動物）'of animals', （水）'of water', or describe a use, e.g. （表促使、命令）'causative/imperative', （短語）'phrase'."],
              "options": [{"key": "ok", "label": "The yes/no column is right", "rec": True, "desc": "Flagged rows aside."},
                          {"key": "other", "label": "Change it (see note)", "desc": "Say in the note what to change."}],
              "items": lab_items})

# ---- headings ending in a colon (affix headwords already omitted)
heads = []
for s, e in sorted(EB.items()):
    t = e["t"]
    if AFFIX(t):
        continue
    rows = kept(senses_after_rulings(s))
    if any(HEAD.search(r[2]) for r in rows):
        heads.append({"key": t, "source": [r[2] for r in rows],
                      "cells": {"drop": [["FORM", t]] + [["TRANSL zho" + (" alt" if k else ""), r[2]] for k, r in enumerate([r for r in rows if not HEAD.search(r[2])])],
                                "keep": [["FORM", t]] + [["TRANSL zho" + (" alt" if k else ""), r[2]] for k, r in enumerate(rows)]}})
cards.append({"id": "r2-heading", "corpus": "Safolu", "flag": False, "title": "Senses that are a heading ending in a colon (asked again)",
              "count": f"{len(heads)} headwords once affixes (left out, your ruling) are removed",
              "question": "主要表示： 'mainly indicates:' and the like introduce the senses after them. Leave them out, or publish them as translations?",
              "body": ["You asked how parts of speech are captured instead of choosing here; that answer and the question about the labels are on the part-of-speech card. This card is only about the heading text itself."],
              "options": [{"key": "drop", "label": "Leave them out", "rec": True, "desc": "The senses after them are published as usual."},
                          {"key": "keep", "label": "Keep them", "desc": "Published as their own ver=\"alt\" TRANSL."}],
              "items": heads})

# ---- borrowing labels
bl = collections.Counter(); bl_ex = {}; n_loan_senses = 0; loan_only = []
for s, e in sorted(EB.items()):
    t = e["t"]
    if AFFIX(t):
        continue
    for i, j, x, a in kept(senses_after_rulings(s)):
        ms = list(LOAN.finditer(x))
        if not ms:
            continue
        n_loan_senses += 1
        rest = LOAN.sub("", x).strip(" 。.，,")
        if not rest:
            loan_only.append((t, x))
        for m in ms:
            bl[m.group(0)] += 1
            bl_ex.setdefault(m.group(0), (t, x, tidy(LOAN.sub("", x)), m.group(1).strip()))
with open(W / "draft/borrow_labels.tsv", "w", encoding="utf-8", newline="") as f:
    wr = csv.writer(f, delimiter="\t"); wr.writerow(["label_as_printed", "senses", "note_text", "example_headword", "example_before", "example_after"])
    for L, n in bl.most_common():
        t, x, after, note = bl_ex[L]; wr.writerow([L, n, note, t, x, after])
bitems = [{"key": L, "source": [f"{bl_ex[L][0]}: {bl_ex[L][1]}"], "cells": {"ok": [["senses", str(n)], ["TRANSL", bl_ex[L][2]], ["notes", bl_ex[L][3]]]}} for L, n in bl.most_common()]
cards.append({"id": "r2-borrow", "corpus": "Safolu", "flag": True, "title": "The list of borrowing labels (moved to TRANSL notes)",
              "count": f"{len(bl)} different labels in {n_loan_senses} senses; {len(loan_only)} senses are only a label",
              "question": "Your note: \"Have a list of these in a tsv, rather than listing them within the code. That way I can check the list. Also show me the list to check!\" Here it is (file: borrow_labels.tsv). Flag any label that is not a borrowing label, or whose note text is wrong.",
              "body": ["Each row: the label exactly as printed, how many senses carry it, the example sense after the label is moved out, and the note text. The round 1 sample matched only 〈…借詞〉 and 〔…借詞〕; this list also takes round brackets, square brackets and 借語.",
                       f"{len(loan_only)} senses are only a label, e.g. " + "; ".join(f"{t}: {x}" for t, x in loan_only[:4]) + ". These go to the notes of the other senses of the same entry, like a part-of-speech label standing alone."],
              "options": [{"key": "ok", "label": "The list is right", "rec": True, "desc": "Flagged rows aside."},
                          {"key": "other", "label": "Change it (see note)", "desc": "Say in the note what to change."}],
              "items": bitems})

lo_items = []
for t, x in loan_only:
    rows = kept(senses_after_rulings(stem_of[t]))
    other = [r[2] for r in rows if r[2] != x]
    note = "; ".join(m.group(1).strip() for m in LOAN.finditer(x))
    lo_items.append({"key": t, "source": [r[2] for r in rows],
                     "cells": {"form": [["FORM", f"{t}   [notes: {note}]"]] + [["TRANSL zho" + (" alt" if k else ""), tidy(LOAN.sub("", o))] for k, o in enumerate(other)] if other else [["—", "headword not published (no other sense)"]],
                               "transl": [["FORM", t]] + [["TRANSL zho" + (" alt" if k else ""), tidy(LOAN.sub("", o)) + f"   [notes: {note}]"] for k, o in enumerate(other)] if other else [["—", "headword not published (no other sense)"]]}})
cards.append({"id": "r2-loanonly", "corpus": "Safolu", "flag": False, "title": "Senses that are only a borrowing label in round or angle brackets",
              "count": f"{len(loan_only)} senses, e.g. akong （閩南語借詞）。",
              "question": "Where does a borrowing label go when it is the whole sense?",
              "body": ["Your label ruling (\"Put it in FORM notes\") already covers a sense that is only a label in 〔 〕 or [ ], e.g. 'epang 〔日語借詞〕; I apply it to those. These are the same thing in （ ） or 〈 〉 brackets, which that card did not cover."],
              "options": [{"key": "form", "label": "FORM notes, like the 〔 〕 ones", "rec": True, "desc": "Same place as your label ruling puts 〔日語借詞〕 standing alone."},
                          {"key": "transl", "label": "Notes of the entry's other translations", "desc": "Like a borrowing label inside a sense (your s-borrow ruling)."}],
              "items": lo_items})

# ---- embedded example sentences -> examples file
pub = set()
try:
    ex_xml = W / "main-ro/Corpora/Safolu-Amis-Dictionary/XML/Amis/Safolu/amis_safolu_examples.xml"
    for s_ in ET.parse(ex_xml).getroot().iter("S"):
        for f_ in s_.findall("FORM"):
            pub.add(re.sub(r"\s+", " ", (f_.text or "")).strip().rstrip(".!?"))
except Exception:
    pass
emb = []
for s, e in sorted(EB.items()):
    t = e["t"]
    if AFFIX(t):
        continue
    for i, j, x, a in senses_after_rulings(s):
        if a != "keep":
            continue
        m = EMB.match(x)
        if m and len(m.group(1).split()) >= 3:
            amis = m.group(1).strip(); zho = m.group(2).strip()
            emb.append((t, x, amis, zho, amis.rstrip(".!?") in pub))
with open(W / "draft/embedded_examples.tsv", "w", encoding="utf-8", newline="") as f:
    wr = csv.writer(f, delimiter="\t"); wr.writerow(["headword", "definition_field_as_printed", "new_example_FORM", "new_example_TRANSL_zho", "already_published"])
    wr.writerows(emb)
eitems = [{"key": f"{t} #{k}", "source": [x], "cells": {"ok": [["FORM", amis], ["TRANSL zho", zho]] + ([["—", "already in the examples file"]] if p else [])}} for k, (t, x, amis, zho, p) in enumerate(emb, 1)]
cards.append({"id": "r2-embedded", "corpus": "Safolu", "flag": True, "title": "Example sentences moved from the definition field: the check round",
              "count": f"{len(emb)} sentences ({sum(1 for r in emb if r[4])} already in the examples file, so not added again)",
              "question": "Your choice was \"Move to the examples file\" (\"after a check round\"). Flag any row that is not a real sentence, is cut short, or is split wrongly.",
              "body": ["Each becomes a new S in amis_safolu_examples.xml (FORM = the Amis part, TRANSL zho = the Chinese part), then goes through the same pipeline as the other examples. The sense itself is not published as a headword translation. File: embedded_examples.tsv."],
              "options": [{"key": "ok", "label": "Add them (flagged rows aside)", "rec": True, "desc": "Flagged rows are left out."},
                          {"key": "other", "label": "Something else (see note)", "desc": ""}],
              "items": eitems})
json.dump(cards, open(W / "draft/round2_safolu_cards.json", "w", encoding="utf-8"), ensure_ascii=False)
for c in cards:
    print(f"{c['id']:14s} items={len(c['items']):5d}  {c['count']}")
print("merged:", len(merged), "| only in 23:", len(only23))
