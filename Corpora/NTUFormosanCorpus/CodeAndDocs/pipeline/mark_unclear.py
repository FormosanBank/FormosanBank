#!/usr/bin/env python3
"""Write NTU's unknown-content markers as <UNCLEAR/> (maintainer's rulings, 2026-10-17
and 2026-10-18).

NTU writes a word it could not transcribe as X (README: "An untranscribed word is
written `X`"; in practice X, XX, XXX or XXXX), glosses such a word X, and marks
a gloss it does not know as ?, ?? or ???. FormosanBank's schema has an element for
exactly this: <UNCLEAR/>, "we tried and failed". This step replaces the markers.

What it does, per sentence (S):

1. Untranscribed words. Ruling: "A. All tiers: sentence FORM, word FORM, word
   gloss, PHON; drop the M under it (no analysis exists, POL-057)".
   * every S-level FORM (both tiers, every variant): each whitespace token that is
     X+ with optional surrounding punctuation has its X+ replaced by <UNCLEAR/>;
     the punctuation stays (``piala haca, <UNCLEAR/>, aku ...``);
   * every S-level PHON: the matching ``x+`` tokens (add_phonology's reading of
     X+) become <UNCLEAR/>; their number must equal the FORM's X tokens, or the
     build stops;
   * every W whose FORMs are all X+ and whose glosses are X+ or absent: FORM and
     PHON become <UNCLEAR/>, each X+ gloss becomes <TRANSL ...><UNCLEAR/></TRANSL>
     (attributes kept), and its M are removed. The word FORM is a bare <UNCLEAR/>,
     without the punctuation NTU attached to the X (ruling 2026-10-18, option
     "Bare <UNCLEAR/>": "Punctuation shouldn't be in W FORMs or M FORMs anyway.
     Delete everywhere in NTU."; the rest of that ruling is
     strip_word_punctuation.py, the step after this one).
   * A W whose FORM is X+ but whose gloss is something else (FS, PART, father,
     ?? ...; 13 words). Ruling 2026-10-18: "FORM -> <UNCLEAR/>, keep the real
     gloss (and its morphemes)". Every FORM of the word becomes a bare
     <UNCLEAR/>; its PHON, glosses (including a ?? gloss) and M are left as NTU
     wrote them. Each one is listed in the report.
   * X as part of a word. Ruling 2026-10-18: "Convert the X part only
     (mi-<UNCLEAR/>)". In every FORM of any other W (mi-XX, -> mi-<UNCLEAR/>,),
     and in every S-level FORM (我的XX在XX那邊 -> 我的<UNCLEAR/>在<UNCLEAR/>那邊), a
     run of X with no Latin letter on either side becomes <UNCLEAR/>. Nothing
     else of these words changes (PHON, glosses, M, the fused sentence token
     miXX,).
2. Unknown glosses. Ruling: "B. A, plus ? used as a placeholder inside a gloss",
   A = "Convert glosses that are exactly ? or ??". A W or M TRANSL whose whole text
   is ?, ?? or ??? (half- or full-width) becomes <TRANSL ...><UNCLEAR/></TRANSL>.
3. Unknown sentence translations. Ruling: "B. Glosses UNCLEAR; sentence
   translations omitted". An S-level TRANSL whose whole text is ?, ??, ??? or X+
   is removed.
4. Ruling: "if the S FORM is simply <UNCLEAR/>, no Ws. If the W FORM is
   <UNCLEAR />, no Ms under it." An S whose original FORM holds nothing but
   <UNCLEAR/> markers (no letter or digit left) loses its W tier.
6. A gloss label NTU typed into a form cell. Ruling 2026-10-18: "these are
   candidates for reversed items. But if there's no evidence of a reversal (no
   actual text to flip with the gloss), then obviously this should be deleted. If
   that's a problem for the whole sentence, the whole sentence goes. If it is just
   for that word, then the FORM should carry <UNCLEAR/>". One case, listed in
   GLOSS_LABEL_IN_FORM: Sentences 3.json record 456, form cell
   'AV.kara-peen=kasu', glosses '主焦.喝-多少=2SG.主格' / 'AV.drink-how.many=2SG.NOM',
   no sentence text (ori '.'). The gloss cells hold glosses, not a form, so there
   is no reversal; the other word (pai'ici?) and the translation are sound, so it
   is a problem for this word only. The label is deleted and <UNCLEAR/> takes its
   place -- the form NTU wrote for that position is unknown -- in the W and M
   FORMs and PHONs and in the sentence FORM and PHON, both tiers:
   <UNCLEAR/>kara-peen=kasu, M <UNCLEAR/>kara, S <UNCLEAR/>karapeenkasu pai'ici?.
5. Placeholders: a ? standing as a whole gloss piece (bounded by -, =, ., space or
   the ends of the gloss) is replaced by <UNCLEAR/> only in glosses listed in
   ../unclear_gloss_placeholders.tsv (columns gloss, lang). The maintainer decides
   these row by row; the table ships empty.

Runs last in each subcorpus build, after the shared standardize/add_phonology
steps: those read FORM.text, so a FORM holding <UNCLEAR/> earlier in the build
would be transliterated only up to the marker.

A file is rewritten only if something in it changed. Idempotent: a second run
finds no markers left. ``--report`` writes one TSV row per change.

usage: mark_unclear.py --xml_dir <dir> [--placeholders <tsv>] [--report <tsv>]
"""
import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Punctuation that may stick to an X token in a FORM.
_PUNCT = r"[.,!?;:\"“”()\[\]…、。，！？；：「」]"
X_TOKEN = re.compile(rf"(?<!\S)({_PUNCT}*)(X+)({_PUNCT}*)(?!\S)")
X_WHOLE = re.compile(rf"^\s*{_PUNCT}*X+{_PUNCT}*\s*$")
X_GLOSS = re.compile(r"^\s*X+\s*$")
# add_phonology's reading of an X+ token: x+ under Ortho94; *+ under Ortho113
# (Kanakanavu's original PHON), which has no letter x.
PHON_X = re.compile(r"(?<!\S)(?:x+|\*+)(?!\S)")
# The X part of a word (ruling 3, 2026-10-18): an X run with no Latin letter on
# either side. Whole-token X has been converted by then, and in a token such as
# miXX, the X touches a letter, so this finds mi-XX, and 我的XX在XX那邊 only.
PART_X = re.compile(r"(?<![A-Za-z])X+(?![A-Za-z])")
UNKNOWN_GLOSS = re.compile(r"^\s*[?？]{1,3}\s*$")
UNKNOWN_S_TRANSL = re.compile(r"^\s*(?:[?？]{1,3}|X+)\s*$")
# A ? piece inside a longer gloss: bounded by - = . whitespace or the ends.
PLACEHOLDER_PIECE = re.compile(r"(?:^|(?<=[-=.\s]))[?？]{1,3}(?=$|[-=.\s])")


# Ruling 6 (2026-10-18): (xml:lang, W id) -> (the label in its FORMs, the label's
# reading at the start of its PHONs). The build stops if the data no longer matches.
GLOSS_LABEL_IN_FORM = {("xnb", "3_S_456_W0"): ("AV.", "av")}


def text_of(el):
    return "".join(el.itertext())


def has_children(el):
    return len(el) > 0


def set_mixed(el, pieces):
    """Replace el's content with pieces: str for text, None for <UNCLEAR/>."""
    for child in list(el):
        el.remove(child)
    el.text = None
    last = None
    for piece in pieces:
        if piece is None:
            last = etree.SubElement(el, "UNCLEAR")
        elif last is None:
            el.text = (el.text or "") + piece
        else:
            last.tail = (last.tail or "") + piece
    if el.text == "":
        el.text = None
    if last is not None and last.tail == "":
        last.tail = None


def replace_matches(el, pattern, group):
    """Replace each match's `group` in el.text by <UNCLEAR/>; return the count."""
    if has_children(el) and all(c.tag == "UNCLEAR" for c in el):
        return 0     # already marked (a second run)
    if has_children(el):
        raise SystemExit(f"mark_unclear: {el.tag} already has child elements: "
                         f"{etree.tostring(el, encoding='unicode')!r}")
    text = el.text or ""
    pieces, pos, n = [], 0, 0
    for m in pattern.finditer(text):
        start, end = m.span(group)
        pieces += [text[pos:start], None]
        pos = end
        n += 1
    if n:
        pieces.append(text[pos:])
        set_mixed(el, [p for p in pieces if p != ""])
    return n


def replace_in_mixed(el, pattern):
    """Like replace_matches, in el.text and in the tail of each <UNCLEAR/> child."""
    if any(c.tag != "UNCLEAR" for c in el):
        raise SystemExit(f"mark_unclear: {el.tag} has a child other than UNCLEAR: "
                         f"{etree.tostring(el, encoding='unicode')!r}")
    pieces, n = [], 0
    for seg_i, seg in enumerate([el.text or ""] + [c.tail or "" for c in el]):
        if seg_i:
            pieces.append(None)          # the existing <UNCLEAR/> child
        pos = 0
        for m in pattern.finditer(seg):
            pieces += [seg[pos:m.start()], None]
            pos = m.end()
            n += 1
        pieces.append(seg[pos:])
    if n:
        set_mixed(el, [p for p in pieces if p != ""])
    return n


def is_bare_unclear(el):
    return len(el) == 1 and el[0].tag == "UNCLEAR" and not (el.text or "").strip() \
        and not (el[0].tail or "").strip()


def remove_keep_layout(el):
    """Remove el; hand its tail to whatever preceded it, so indentation survives."""
    parent = el.getparent()
    prev = el.getprevious()
    if prev is not None:
        prev.tail = el.tail
    else:
        parent.text = el.tail
    parent.remove(el)


def write_like(path, root):
    """Rewrite path keeping its own bytes before and after the root element.

    The build's files carry two declaration styles (add_phonology's and lxml's);
    keeping each file's own avoids churning lines this step did not change.
    """
    raw = path.read_text(encoding="utf-8")
    start = raw.index("<" + root.tag)
    end = raw.rindex("</" + root.tag + ">") + len(root.tag) + 3
    body = etree.tostring(root, encoding="unicode", with_tail=False)
    path.write_text(raw[:start] + body + raw[end:], encoding="utf-8")


def load_placeholders(path):
    if path is None or not path.exists():
        return set()
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines()
             if ln.strip() and not ln.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE))
    for r in rows:
        if set(r) != {"gloss", "lang"}:
            raise SystemExit(f"mark_unclear: {path}: expected columns gloss, lang; got {sorted(r)}")
        if not PLACEHOLDER_PIECE.search(r["gloss"]):
            raise SystemExit(f"mark_unclear: {path}: listed gloss {r['gloss']!r} has no ? piece")
    return {(r["gloss"], r["lang"]) for r in rows}


def is_x_word(w):
    forms = w.findall("FORM")
    return bool(forms) and all(not has_children(f) and X_WHOLE.match(f.text or "") for f in forms)


def x_word_held(w):
    """An X word whose gloss is real (not X+, not absent): left untouched."""
    return any(not X_GLOSS.match(text_of(t)) for t in w.findall("TRANSL"))


def form_is_only_unclear(form):
    if form.find("UNCLEAR") is None:
        return False
    rest = (form.text or "") + "".join(c.tail or "" for c in form)
    return not any(ch.isalnum() for ch in rest)


def replace_label(el, label, where):
    """Replace a leading label in el's text (or in the first token of a sentence) with <UNCLEAR/>."""
    if has_children(el):
        if el[0].tag == "UNCLEAR" and not (el.text or "").strip():
            return False         # a second run
        raise SystemExit(f"mark_unclear: {where}: unexpected children in {etree.tostring(el, encoding='unicode')!r}")
    text = el.text or ""
    if not text.startswith(label):
        raise SystemExit(f"mark_unclear: {where}: {el.tag} {text!r} does not start with {label!r}")
    set_mixed(el, [None, text[len(label):]])
    return True


def fix_gloss_label_in_form(s, lang, counts, log):
    """Ruling 6: the gloss label in a word's FORM becomes <UNCLEAR/>, in every tier."""
    for w in s.findall("W"):
        entry = GLOSS_LABEL_IN_FORM.get((lang, w.get("id")))
        if entry is None:
            continue
        label, reading = entry
        morph = w.find("M")
        targets = ([(f, label) for f in w.findall("FORM")] + [(p, reading) for p in w.findall("PHON")]
                   + [(f, label) for f in morph.findall("FORM")] + [(p, reading) for p in morph.findall("PHON")])
        if w is s.find("W"):     # the sentence's first token carries the label too
            targets += [(f, label) for f in s.findall("FORM")] + [(p, reading) for p in s.findall("PHON")]
        else:
            raise SystemExit(f"mark_unclear: {w.get('id')}: the label is expected on the first word")
        for el, lab in targets:
            before = etree.tostring(el, encoding="unicode", with_tail=False)
            if replace_label(el, lab, w.get("id")):
                counts["gloss label in FORM -> UNCLEAR (ruling 6)"] += 1
                log("gloss label in FORM (ruling 6)", w.get("id"), before,
                    etree.tostring(el, encoding="unicode", with_tail=False))


def process_sentence(s, placeholders, counts, report, rel, lang=None):
    sid = s.get("id")

    def log(kind, where, before, after):
        report.append((rel, sid, where, kind, before, after))

    fix_gloss_label_in_form(s, lang, counts, log)

    # 1. S-level FORM and PHON. The PHON is located through its FORM: PHON holds
    # one token per FORM token that has a letter or digit, in order, so the
    # k-th such FORM token being X+ means the k-th PHON token is its reading.
    x_positions = {}
    for form in s.findall("FORM"):
        before = form.text
        if form.get("ver") is None and not has_children(form):
            words = [t for t in (form.text or "").split() if any(c.isalnum() for c in t)]
            x_positions[form.get("kindOf")] = (len(words), [i for i, t in enumerate(words) if X_WHOLE.match(t)])
        n = replace_matches(form, X_TOKEN, 2)
        if n:
            counts["S FORM X tokens -> UNCLEAR"] += n
            counts["S FORM elements changed"] += 1
            log("S FORM", sid, before, etree.tostring(form, encoding="unicode", with_tail=False))
        before = "".join(form.itertext())
        n = replace_in_mixed(form, PART_X)
        if n:
            counts["S FORM X part of a token -> UNCLEAR (ruling 3)"] += n
            log("S FORM X part (ruling 3)", sid, before, etree.tostring(form, encoding="unicode", with_tail=False))
    for phon in s.findall("PHON"):
        n_words, positions = x_positions.get(phon.get("kindOf"), (0, []))
        if not positions:
            continue
        before = phon.text or ""
        spans = [m.span() for m in re.finditer(r"\S+", before)] if not has_children(phon) else []
        if len(spans) != n_words or any(not PHON_X.fullmatch(before[a:b]) for a, b in (spans[i] for i in positions)):
            raise SystemExit(f"mark_unclear: {sid}: PHON kindOf={phon.get('kindOf')} {before!r} does not "
                             f"line up with its FORM's {n_words} word tokens (X at {positions})")
        pieces, pos = [], 0
        for a, b in (spans[i] for i in positions):
            pieces += [before[pos:a], None]
            pos = b
        pieces.append(before[pos:])
        set_mixed(phon, [p for p in pieces if p != ""])
        counts["S PHON tokens -> UNCLEAR"] += len(positions)
        log("S PHON", sid, before, etree.tostring(phon, encoding="unicode", with_tail=False))

    # 3. Sentence translations that are only an unknown marker.
    for tr in s.findall("TRANSL"):
        if not has_children(tr) and UNKNOWN_S_TRANSL.match(tr.text or ""):
            counts["S TRANSL omitted"] += 1
            log("S TRANSL omitted", f"{sid} TRANSL xml:lang={tr.get(XML_LANG)}", tr.text, "")
            remove_keep_layout(tr)

    # 4. An S that is nothing but <UNCLEAR/> has no word tier.
    base = next((f for f in s.findall("FORM[@kindOf='original']") if f.get("ver") is None), None)
    if base is not None and form_is_only_unclear(base) and s.findall("W"):
        for w in s.findall("W"):
            counts["W removed (S is only UNCLEAR)"] += 1
            counts["M removed"] += len(w.findall("M"))
            log("W removed: S is only UNCLEAR", w.get("id"), etree.tostring(w, encoding="unicode", with_tail=False), "")
            remove_keep_layout(w)

    for w in s.findall("W"):
        wid = w.get("id")
        if is_x_word(w):
            if x_word_held(w):
                # Ruling 2 (2026-10-18): FORM only; PHON, glosses and M stay.
                counts["X word with real gloss: FORM -> UNCLEAR (ruling 2)"] += 1
                glosses = " | ".join(f"{t.get(XML_LANG)}={text_of(t)}" for t in w.findall("TRANSL"))
                log("X word with real gloss: FORM -> UNCLEAR", wid,
                    " | ".join(f.text for f in w.findall("FORM")), glosses)
                for form in w.findall("FORM"):
                    set_mixed(form, [None])
                continue
            counts["W X words -> UNCLEAR"] += 1
            for form in w.findall("FORM"):
                set_mixed(form, [None])     # bare: the punctuation goes (ruling 2026-10-18)
            for phon in w.findall("PHON"):
                if has_children(phon) or not PHON_X.fullmatch((phon.text or "").strip()):
                    raise SystemExit(f"mark_unclear: {wid}: PHON {phon.text!r} is not x+ or *+")
                set_mixed(phon, [None])
            for tr in w.findall("TRANSL"):
                counts["W gloss X -> UNCLEAR"] += 1
                set_mixed(tr, [None])
            ms = w.findall("M")
            counts["M removed"] += len(ms)
            for m in ms:
                remove_keep_layout(m)
            log("W X word -> UNCLEAR", wid, "", etree.tostring(w, encoding="unicode", with_tail=False))
            continue

        # A word whose FORMs are all a bare <UNCLEAR/> was handled above (a second
        # run): its glosses stay as they are, a ruling-2 word's ?? included.
        if all(is_bare_unclear(f) for f in w.findall("FORM")) and w.findall("FORM"):
            continue

        # Ruling 3: the X part of a word.
        for form in w.findall("FORM"):
            before = "".join(form.itertext())
            n = replace_in_mixed(form, PART_X)
            if n:
                counts["W FORM X part -> UNCLEAR (ruling 3)"] += n
                log("W FORM X part (ruling 3)", f"{wid} kindOf={form.get('kindOf')}", before,
                    etree.tostring(form, encoding="unicode", with_tail=False))

        # 2 and 5 on this word's glosses and its morphemes' glosses.
        for node, level in [(w, "W")] + [(m, "M") for m in w.findall("M")]:
            for tr in node.findall("TRANSL"):
                if has_children(tr):
                    continue
                before = tr.text or ""
                if UNKNOWN_GLOSS.match(before):
                    set_mixed(tr, [None])
                    counts[f"{level} gloss ?/??/??? -> UNCLEAR"] += 1
                    log(f"{level} gloss unknown", f"{node.get('id')} xml:lang={tr.get(XML_LANG)}", before, "<UNCLEAR/>")
                elif (before, tr.get(XML_LANG)) in placeholders:
                    n = replace_matches(tr, PLACEHOLDER_PIECE, 0)
                    counts[f"{level} gloss placeholder ? -> UNCLEAR"] += n
                    log(f"{level} gloss placeholder", f"{node.get('id')} xml:lang={tr.get(XML_LANG)}", before,
                        etree.tostring(tr, encoding="unicode", with_tail=False))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--placeholders", type=Path,
                    default=Path(__file__).resolve().parent.parent / "unclear_gloss_placeholders.tsv")
    ap.add_argument("--report", type=Path)
    args = ap.parse_args(argv)
    placeholders = load_placeholders(args.placeholders)
    counts, report, files = Counter(), [], 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        before = len(report)
        rel = str(path.relative_to(args.xml_dir))
        lang = tree.getroot().get(XML_LANG)
        for s in tree.getroot().iter("S"):
            process_sentence(s, placeholders, counts, report, rel, lang)
        if report[before:]:
            write_like(path, tree.getroot())
            files += 1
    print(f"placeholder table rows: {len(placeholders)}")
    for key in sorted(counts):
        print(f"  {key}: {counts[key]}")
    print(f"files rewritten: {files}")
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8", newline="") as fh:
            out = csv.writer(fh, delimiter="\t", lineterminator="\n")
            out.writerow(["file", "s_id", "where", "change", "before", "after"])
            out.writerows(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
