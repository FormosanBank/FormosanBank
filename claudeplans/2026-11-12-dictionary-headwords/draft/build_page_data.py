"""Build the decision-page data (cards, items, per-option renderings) from the drafts' inputs."""
import csv, json, pathlib, re, sys, collections
SP = pathlib.Path(sys.argv[1])
sys.path.insert(0, str(SP / "draft"))
from safolu_headwords import clean, classify, SPECIAL  # noqa: E402

A = SP / "src/e7c6976/docs/s"
B = SP / "src/4cb8/docs/s"
CJK = re.compile(r"[㐀-鿿]")
P = re.compile(r"[（(][^）)]*[）)]")


def load(d):
    return {p.name: json.loads(p.read_text(encoding="utf-8")) for p in d.glob("*.json") if p.name not in SPECIAL}


EA, EB = load(A), load(B)


def senses(e):
    return [clean(df.get("f", "")) for h in e.get("h", []) for df in h.get("d", [])]


def S(form, zho=(), eng=(), fnotes=None, tnotes=None):
    """Render one published S as lines."""
    lines = [("FORM", form + (f"   [notes: {fnotes}]" if fnotes else ""))]
    tnotes = tnotes or {}
    for lang, items in (("eng", eng), ("zho", zho)):
        for i, t in enumerate(items):
            n = tnotes.get((lang, i))
            lines.append((f"TRANSL {lang}" + (" alt" if i else ""), t + (f"   [notes: {n}]" if n else "")))
    return lines


NOT = [("—", "not published")]


def uniq(xs):
    out = []
    for x in xs:
        if x and x not in out:
            out.append(x)
    return out


def safolu_render(title, ss, *, xref="drop", label="notes", noch="notes", emb="drop", head="drop"):
    keep, notes = [], []
    for s in ss:
        k = classify(s)
        if k == "empty":
            continue
        if k == "xref":
            if xref == "translation": keep.append(s)
            elif xref == "notes": notes.append(s)
            continue
        if k == "label":
            if label == "translation": keep.append(s)
            elif label == "notes": notes.append(s)
            continue
        if k == "nochinese":
            if noch == "translation": keep.append(s)
            elif noch == "notes": notes.append(s)
            continue
        m = re.match(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([㐀-鿿].*)$", s)
        if m and len(m.group(1).split()) >= 3 and emb != "keep":
            continue
        if re.search(r"[：:]\s*$", s) and head == "drop":
            continue
        keep.append(s)
    keep = uniq(keep)
    if not keep:
        return NOT
    return S(title, keep, fnotes=" | ".join(notes) or None)


cards = []

# ---------- Safolu: version ----------
items = []
same_after_rules = 0
for n in sorted(set(EA) & set(EB)):
    a, b = senses(EA[n]), senses(EB[n])
    if a == b:
        continue
    t = EA[n]["t"]
    cells = {"base": safolu_render(t, a), "editors": safolu_render(t, b), "both": safolu_render(t, uniq(b + a))}
    if cells["base"] == cells["editors"] == cells["both"]:
        same_after_rules += 1
        continue
    items.append({"key": t, "cells": cells})
added = [{"key": EB[n]["t"], "senses": [s for s in senses(EB[n]) if s]} for n in sorted(set(EB) - set(EA))]
cards.append({
    "id": "s-version", "corpus": "Safolu", "title": "Which version of the definitions",
    "count": f"383 headwords whose definitions differ between the two versions; {len(items)} of them still differ once the other cards' recommended choices are applied (the other {same_after_rules} differ only in cross-references, labels or markup, and are not listed); 72 headwords exist only in the later one",
    "question": "The examples already follow the editors' revision at g0v/amis-moedict 4cb82539d (2026-10-16), under your rules for each kind of edit. For the definitions, which version should be published?",
    "body": [
        "Base snapshot = g0v/amis-moedict e7c6976 (2026-05-08), the version the examples were built from. Editors' version = 4cb82539d (2026-10-16), the pin the examples use for the editors' edits and added examples (your ruling r13-pin: \"Keep 4cb82539d (recommended)\").",
        "What the editors changed in these 383 headwords (measured): 213 lost one or more senses, 54 gained senses, 106 have the same number of senses with edited text, 10 differ only in a parenthetical. Of the senses they removed, 216 appear nowhere in the later dictionary. Some of those are real changes of meaning, e.g. kalatawan was 發生山林火災的時間或地方 and is now only 被施巫術或魔法. Others are clean-ups (duplicates, cross-references, a borrowing label moved into the sense).",
        "The 72 headwords added by the editors are published under every option below (your ruling r13-provenance treats the editors' additions as part of Safolu). They are listed at the bottom of this card.",
        "Every other card on this page shows its counts at the editors' version; at the base snapshot they differ by a few (e.g. 36 rather than 34 cross-reference senses).",
    ],
    "options": [
        {"key": "base", "label": "Base snapshot (e7c6976)", "desc": "Definitions as in the examples' base snapshot, plus the 72 added headwords."},
        {"key": "editors", "label": "Editors' version (4cb82539d)", "desc": "Definitions as the editors have them now. Their removed senses are not published."},
        {"key": "both", "label": "Keep both", "rec": True, "desc": "Every sense either version has, each once (editors' senses first, base-only senses after as further ver=\"alt\" TRANSLs). Nothing either version says is lost; near-duplicates such as 花〈日語借詞〉。 beside 花。〔日語借詞〕。 remain. Recommended because it loses nothing, as your 25% rule for examples keeps ours and theirs."},
    ],
    "items": items, "extra": {"title": "The 72 headwords only the editors' version has (published under every option)", "rows": added},
})


def cat_items(kind, renderer_opts, pick):
    out = []
    for n in sorted(EB):
        e = EB[n]; t = e["t"]; ss = senses(e)
        if not pick(ss, t):
            continue
        out.append({"key": t, "source": [s for s in ss if s], "cells": {k: safolu_render(t, ss, **v) for k, v in renderer_opts.items()}})
    return out


def has(kind):
    return lambda ss, t: any(classify(s) == kind for s in ss)


cards.append({
    "id": "s-xref", "corpus": "Safolu", "title": "Definitions that are only a cross-reference",
    "count": "34 senses (in 34 headwords; every one of these headwords keeps other senses)",
    "question": "A sense whose whole text is 同 X or 參見 X (\"same as X\", \"see X\"). Where should it go?",
    "body": ["For the examples you ruled (round 3) that cross-references come out of translations, e.g. S48080 → drop 同 tata'ian。. No headword is lost under any option."],
    "options": [
        {"key": "drop", "label": "Leave it out", "rec": True, "desc": "Not published. Same treatment as the examples' cross-references."},
        {"key": "notes", "label": "Put it in FORM notes", "desc": "Kept as a note on the headword, not as a translation."},
        {"key": "translation", "label": "Publish as a translation", "desc": "Kept as a Chinese TRANSL, as the source has it."},
    ],
    "items": cat_items("xref", {"drop": {"xref": "drop"}, "notes": {"xref": "notes"}, "translation": {"xref": "translation"}}, has("xref")),
})
cards.append({
    "id": "s-label", "corpus": "Safolu", "title": "Definitions that are only a label",
    "count": "165 senses in 164 headwords, almost all 〔疊 2〕 (\"reduplication, type 2\")",
    "question": "A sense whose whole text is a bracketed label, with no meaning given. Where should it go?",
    "body": ["The label describes the word's form (here, its reduplication pattern), not what it means."],
    "options": [
        {"key": "notes", "label": "Put it in FORM notes", "rec": True, "desc": "The label is kept as information about the headword, not as a translation."},
        {"key": "drop", "label": "Leave it out", "desc": "Not published."},
        {"key": "translation", "label": "Publish as a translation", "desc": "A Chinese TRANSL reading only 〔疊 2〕."},
    ],
    "items": cat_items("label", {"notes": {"label": "notes"}, "drop": {"label": "drop"}, "translation": {"label": "translation"}}, has("label")),
})
cards.append({
    "id": "s-nochinese", "corpus": "Safolu", "title": "Definitions with no Chinese in them",
    "count": "148 senses in 136 headwords; for some headwords this is all there is (see the card on headwords with no definition)",
    "question": "A 'definition' that contains only Amis (mostly a related or variant word such as ka'apak, makerah). Where should it go?",
    "body": ["Published as a Chinese TRANSL it would be a Chinese translation with no Chinese in it."],
    "options": [
        {"key": "notes", "label": "Put it in FORM notes", "rec": True, "desc": "Kept as a note on the headword."},
        {"key": "drop", "label": "Leave it out", "desc": "Not published."},
        {"key": "translation", "label": "Publish as a translation", "desc": "Kept as a Chinese TRANSL."},
    ],
    "items": cat_items("nochinese", {"notes": {"noch": "notes"}, "drop": {"noch": "drop"}, "translation": {"noch": "translation"}}, has("nochinese")),
})


def emb_pick(ss, t):
    return any(re.match(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([㐀-鿿].*)$", s) and len(re.match(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*", s).group(1).split()) >= 3 for s in ss if s)


emb = []
for n in sorted(EB):
    e = EB[n]; t = e["t"]; ss = senses(e)
    for s in ss:
        m = re.match(r"^([A-Za-z'^ ,.!?\-]+?)[.!?]?\s*([㐀-鿿].*)$", s or "")
        if m and len(m.group(1).split()) >= 3:
            emb.append({"key": t, "source": [x for x in ss if x], "cells": {
                "examples": safolu_render(t, ss, emb="drop") + [("+ new example S", f"FORM {m.group(1).strip()}"), ("", f"TRANSL zho {m.group(2).strip()}")],
                "drop": safolu_render(t, ss, emb="drop"),
                "keep": safolu_render(t, ss, emb="keep")}})
cards.append({
    "id": "s-embedded", "corpus": "Safolu", "title": "Example sentences sitting in the definition field",
    "count": "104 senses; 103 of these sentences are not published anywhere in the corpus now",
    "question": "The source put an Amis sentence plus its Chinese translation in the definition field instead of the example field. What should happen to it?",
    "body": ["Some look cut short in the source (caay kanca': kanca' ka tayni cingra.他一定). If you choose 'examples', those would each get a card before anything is published."],
    "options": [
        {"key": "examples", "label": "Move to the examples file", "rec": True, "desc": "Not a headword translation; added to amis_safolu_examples.xml as a new example sentence (about 103 new S), after a check round."},
        {"key": "drop", "label": "Leave it out", "desc": "Not published anywhere."},
        {"key": "keep", "label": "Keep as a translation", "desc": "Published as a Chinese TRANSL of the headword, Amis and all."},
    ],
    "items": emb,
})
cards.append({
    "id": "s-heading", "corpus": "Safolu", "title": "Senses that are a heading ending in a colon",
    "count": "23 senses (主要表示： \"mainly indicates:\", 用法如下： \"used as follows:\")",
    "question": "These introduce the senses that follow; they mean nothing on their own. Keep them?",
    "body": [],
    "options": [
        {"key": "drop", "label": "Leave them out", "rec": True, "desc": "The senses after them are published as usual."},
        {"key": "keep", "label": "Keep them", "desc": "Published as their own ver=\"alt\" TRANSL."},
    ],
    "items": cat_items("heading", {"drop": {"head": "drop"}, "keep": {"head": "keep"}}, lambda ss, t: any(re.search(r"[：:]\s*$", s or "") for s in ss)),
})
aff = []
for n in sorted(EB):
    e = EB[n]; t = e["t"]
    if t.startswith("-") or t.endswith("-") or "…" in t:
        aff.append({"key": t, "source": [s for s in senses(e) if s], "cells": {"publish": safolu_render(t, senses(e)), "omit": NOT}})
cards.append({
    "id": "s-affix", "corpus": "Safolu", "title": "Affix and circumfix entries",
    "count": "41 headwords: 18 written with a hyphen (-ay, ki-, mapa-) and 23 circumfixes written with … (pa…an, nai…tala…)",
    "question": "These are not words but parts of words, and their 'definitions' describe grammar (前後綴。 \"circumfix.\", 表示人名詞、親屬稱謂詞受格形態。). Publish them as headwords?",
    "body": ["For Blust's Thao dictionary you ruled that a bound root is not a dictionary entry; that ruling was about Blust and does not decide this one."],
    "options": [
        {"key": "omit", "label": "Leave them out", "rec": True, "desc": "Not published. Recommended because no translation of these forms exists to publish: the text describes what the affix does."},
        {"key": "publish", "label": "Publish them", "desc": "Published like any other headword (with the other cards' choices applied)."},
    ],
    "items": aff,
})
nos = []
for n in sorted(EB):
    e = EB[n]; t = e["t"]; ss = senses(e)
    if safolu_render(t, ss, noch="drop", label="drop") == NOT and not (t.startswith("-") or t.endswith("-") or "…" in t):
        raw = [df.get("f") for h in e["h"] for df in h.get("d", [])]
        nos.append({"key": t, "source": [repr(x) for x in raw], "cells": {"omit": NOT, "bare": S(t, [], fnotes=" | ".join(s for s in ss if s) or None)}})
cards.append({
    "id": "s-nosense", "corpus": "Safolu", "title": "Headwords with no definition at all",
    "count": f"{len(nos)} headwords",
    "question": "The source gives these headwords no usable definition (empty, or only an Amis word). Publish the bare headword?",
    "body": [],
    "options": [
        {"key": "omit", "label": "Leave them out", "rec": True, "desc": "Not published. ILRDF's headword files follow the same rule (\"a headword left with no sense is not published\")."},
        {"key": "bare", "label": "Publish with no translation", "desc": "A FORM with no TRANSL (and any Amis text as a note)."},
    ],
    "items": nos,
})
st = []
for n in sorted(EB)[:4000:250]:
    e = EB[n]; t = e["t"]
    if not (e.get("stem") or e.get("tag")):
        continue
    note = " | ".join(x for x in ([f"Tag: {e['tag']}"] if e.get("tag") else []) + ([f"Stem: {e['stem']}"] if e.get("stem") else []))
    st.append({"key": t, "cells": {"none": safolu_render(t, senses(e))[:1], "notes": [("FORM", f"{t}   [notes: {note}]")]}})
cards.append({
    "id": "s-stemtag", "corpus": "Safolu", "title": "The source's stem and reduplication tag",
    "count": "34,774 headwords have a stem (e.g. 'a'acaen → 'aca) and/or a tag such as [疊 2]",
    "question": "Each upstream entry records the headword's stem and, for reduplicated forms, a tag. Publish them as a note on the headword?",
    "body": ["Sample below: every 250th headword that has one (16 shown of 34,774)."],
    "options": [
        {"key": "notes", "label": "Put them in FORM notes", "rec": True, "desc": "e.g. notes=\"Tag: [疊 2] | Stem: 'aca\". Translations unchanged."},
        {"key": "none", "label": "Don't publish them", "desc": "The FORM carries no note."},
    ],
    "items": st,
})
syn = []
for n in sorted(EB)[:6000:300]:
    e = EB[n]; t = e["t"]
    s_ = uniq([clean(w) for h in e["h"] for df in h.get("d", []) for w in (df.get("s") or [])])
    r_ = uniq([clean(w) for h in e["h"] for df in h.get("d", []) for w in (df.get("r") or [])])
    if not (s_ or r_):
        continue
    note = " | ".join([f"Synonym: {w}" for w in s_] + [f"Related: {w}" for w in r_])
    syn.append({"key": t, "cells": {"none": safolu_render(t, senses(e))[:1], "notes": [("FORM", f"{t}   [notes: {note}]")]}})
cards.append({
    "id": "s-synrel", "corpus": "Safolu", "title": "Synonym and related-word links",
    "count": "8,013 senses list synonyms, 4,390 list related (derived) words; 10,841 headwords have one or both",
    "question": "Upstream links each sense to synonyms and related words, which are themselves headwords in the file. Publish the links as notes?",
    "body": ["Sample below (every 300th headword that has links, among the first 6,000)."],
    "options": [
        {"key": "none", "label": "Don't publish them", "rec": True, "desc": "The linked words are headwords in the same file already. (Blust's README: cross-references are not published.)"},
        {"key": "notes", "label": "Put them in FORM notes", "desc": "e.g. notes=\"Synonym: 'a'alacamen | Related: miki'a'am\"."},
    ],
    "items": syn,
})
bor = []
for n in sorted(EB):
    e = EB[n]; t = e["t"]
    for s in senses(e):
        m = re.search(r"[〔〈][^〕〉]*借詞[〕〉]", s or "")
        if m and len(bor) < 20:
            rest = (s.replace(m.group(0), "")).strip() or s
            bor.append({"key": t, "cells": {"inline": [("TRANSL zho", s)], "notes": [("TRANSL zho", rest + f"   [notes: {m.group(0)}]")]}})
cards.append({
    "id": "s-borrow", "corpus": "Safolu", "title": "Borrowing labels inside definitions",
    "count": "731 senses carry a label such as 〈日語借詞〉 (Japanese loan) or 〔閩南語借詞〕 (Hokkien loan)",
    "question": "Keep the label inside the Chinese translation, as printed, or move it to the translation's notes?",
    "body": ["The examples keep such a label with the translation (README: \"a leading loanword note such as (閩南語借詞) stays with the translation\"). Sample: the first 20."],
    "options": [
        {"key": "inline", "label": "Keep it in the translation", "rec": True, "desc": "As the source prints it, and as the examples do."},
        {"key": "notes", "label": "Move it to TRANSL notes", "desc": "The translation reads without it."},
    ],
    "items": bor,
})

# ---------- Fey ----------
rows = list(csv.DictReader(open(SP / "main-ro/Corpora/Virginia_Fey_Dictionary/CodeAndDocs/source/virginia_fey_source.csv", encoding="utf-8")))
ents = []
for line, r in enumerate(rows, 2):
    h = r["詞條"].strip()
    if h:
        ents.append({"hw": h, "line": line, "senses": [], "see": []})
    if not ents:
        continue
    e_, z_ = r["英文解釋"].strip(), r["中文解釋"].strip()
    if e_ or z_:
        ents[-1]["senses"].append((e_, z_))
    if r["參見"].strip():
        ents[-1]["see"].append(r["參見"].strip())
XE = re.compile(r"^(refer to|see)\s+\S+\.?$", re.I)
XZ = re.compile(r"^(詳見|參見|參看|參閱|見)\s*[A-Za-z'^ ,\-]+[。.]?$")


def fey_render(x, split="split", xref="drop", fix="notes", see="none"):
    eng, zho, tn = [], [], {}
    for e_, z_ in x["senses"]:
        if XE.match(e_) or XZ.match(z_):
            if xref == "drop":
                continue
            if xref == "notes":
                continue
        fixnote = None
        if "FIXME" in z_:
            if fix == "notes":
                z_ = re.sub(r"\s*\(FIXME\)", "", z_); fixnote = "source marks this translation (FIXME)"
            elif fix == "drop":
                z_ = ""
        for lang, txt, sep, acc in (("eng", e_, r"\*", eng), ("zho", z_, r"[，、,]", zho)):
            if not txt:
                continue
            parts = [p.strip() for p in re.split(sep, txt)] if split == "split" else [txt]
            parts = [p for p in parts if p]
            first = len(acc)
            for p in parts:
                if p not in acc:
                    acc.append(p)
            if split == "split" and len(parts) > 1 and first < len(acc):
                tn[(lang, first)] = txt
            if fixnote and lang == "zho" and first < len(acc):
                tn[(lang, first)] = (tn.get((lang, first), "") + " | " if tn.get((lang, first)) else "") + fixnote
    fn = None
    if xref == "notes":
        xs = [e_ or z_ for e_, z_ in x["senses"] if XE.match(e_) or XZ.match(z_)]
        fn = " | ".join(xs) or None
    if see == "notes" and x["see"]:
        fn = ((fn + " | ") if fn else "") + "See also: " + ", ".join(x["see"])
    if not (eng or zho):
        return NOT if not (xref == "notes" and fn) else S(x["hw"], fnotes=fn)
    return S(x["hw"], zho, eng, fnotes=fn, tnotes=tn)


split_items = []
for x in ents:
    if any("*" in e_ or re.search("[，、]", z_) for e_, z_ in x["senses"]) and len(split_items) < 400:
        if ents.index(x) % 7 == 0 or any(w in x["hw"] for w in ("'adidem", "'a'iloc")) or any("as of" in e_ for e_, _ in x["senses"]):
            split_items.append({"key": x["hw"], "source": [f"{e_} / {z_}" for e_, z_ in x["senses"]], "cells": {"split": fey_render(x, split="split"), "keep": fey_render(x, split="keep")}})
split_items = split_items[:30]
cards.append({
    "id": "f-split", "corpus": "Fey", "title": "Senses that list several glosses",
    "count": "3,014 of 4,848 headwords: English glosses joined with * (2,075 senses), Chinese with ，/、 (2,624 senses)",
    "question": "Fey writes one sense as a list, e.g. 'the back of the head * neck' / 脖子，頸，頸項. Split each list into separate ver=\"alt\" translations?",
    "body": ["The published Fey examples were split this way by hand: all 75 English translations with * and 349 Chinese ones with ，/、 are split, each with the unsplit text kept in the first piece's notes. Splitting also cuts some glosses that are not alternatives, e.g. 'sour * as of unripe fruit' gives a standalone 'as of unripe fruit'. Totals: keep = 5,971 English + 5,969 Chinese TRANSL; split = 8,412 + 9,868. Sample of 30 below."],
    "options": [
        {"key": "split", "label": "Split, keep the original in notes", "rec": True, "desc": "Same convention as the published Fey examples."},
        {"key": "keep", "label": "Keep each sense whole", "desc": "One English and one Chinese TRANSL per sense, as printed."},
    ],
    "items": split_items,
})
cards.append({
    "id": "f-xref", "corpus": "Fey", "title": "Headwords whose only sense is a cross-reference",
    "count": "144 headwords; 'Refer to X' / 詳見 X is their only sense",
    "question": "Publish these headwords?",
    "body": ["Unlike Safolu, here the choice decides whether the headword exists in the XML at all."],
    "options": [
        {"key": "drop", "label": "Leave them out", "rec": True, "desc": "Not published (no translation to give)."},
        {"key": "notes", "label": "Publish, cross-reference in notes", "desc": "FORM only, notes=\"Refer to X\"; no TRANSL."},
        {"key": "translation", "label": "Publish the cross-reference as the translation", "desc": "TRANSL eng 'Refer to X', TRANSL zho 詳見 X."},
    ],
    "items": [{"key": x["hw"], "source": [f"{e_} / {z_}" for e_, z_ in x["senses"]], "cells": {k: fey_render(x, xref=k) for k in ("drop", "notes", "translation")}} for x in ents if all(XE.match(e_) or XZ.match(z_) for e_, z_ in x["senses"])],
})
cards.append({
    "id": "f-fixme", "corpus": "Fey", "title": "Chinese senses marked (FIXME)",
    "count": "6 headwords (the published examples have 1 more: so'elin)",
    "question": "The digitiser left (FIXME) on 6 Chinese translations; some are plainly wrong (so'ol 'to melt as a candle melts' = 鐵生鏽 'iron rusts'). What should be published?",
    "body": [],
    "options": [
        {"key": "notes", "label": "Remove the marker, say so in notes", "rec": True, "desc": "Chinese kept; TRANSL notes record that the source flags it."},
        {"key": "drop", "label": "Drop those Chinese senses", "desc": "English kept; the flagged Chinese is not published."},
        {"key": "keep", "label": "Keep (FIXME) in the text", "desc": "As the sheet has it."},
    ],
    "items": [{"key": x["hw"], "source": [f"{e_} / {z_}" for e_, z_ in x["senses"]], "cells": {k: fey_render(x, fix=k) for k in ("notes", "drop", "keep")}} for x in ents if any("FIXME" in z_ for _, z_ in x["senses"])],
})
cards.append({
    "id": "f-affix", "corpus": "Fey", "title": "Prefix entries",
    "count": "8 headwords (ala-, haki-, hali-, hina-, kara-, kina-, mako-, tada-)",
    "question": "Publish prefixes as headwords?",
    "body": [],
    "options": [
        {"key": "omit", "label": "Leave them out", "rec": True, "desc": "Not published."},
        {"key": "publish", "label": "Publish them", "desc": "Like any other headword."},
    ],
    "items": [{"key": x["hw"], "source": [f"{e_} / {z_}" for e_, z_ in x["senses"]], "cells": {"omit": NOT, "publish": fey_render(x)}} for x in ents if x["hw"].endswith("-") or x["hw"].startswith("-")],
})
cards.append({
    "id": "f-see", "corpus": "Fey", "title": "The see-also column (參見)",
    "count": "2,404 headwords list related words in the 參見 column",
    "question": "Publish the see-also words as a note on the headword?",
    "body": ["Sample: the first 15."],
    "options": [
        {"key": "none", "label": "Don't publish them", "rec": True, "desc": "Same recommendation as for Safolu's links."},
        {"key": "notes", "label": "Put them in FORM notes", "desc": "notes=\"See also: miki'a'am\"."},
    ],
    "items": [{"key": x["hw"], "cells": {"none": fey_render(x)[:1], "notes": fey_render(x, see="notes")[:1]}} for x in ents if x["see"]][:15],
})
json.dump(cards, open(SP / "draft/page_cards.json", "w"), ensure_ascii=False)
for c in cards:
    print(c["id"], len(c["items"]))
print("bytes", (SP / "draft/page_cards.json").stat().st_size)
