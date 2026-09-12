#!/usr/bin/env python3
"""Test-driven audit of the NTU *Grammar* subcorpus XML.

Twelve tests over the published XML, each reported as pass/fail with the unit
being counted (record, sentence, word or morpheme). Run against any XML tree so
different pipeline versions can be compared on the same measurements.

    python grammar_xml_tests.py --xml <XMLdir> --json <grammar JSON dir> [--label NAME]

Tests
  0  every JSON record has a corresponding S block          unit: JSON record
  1  S FORM is non-empty                                    unit: S
  2  W has a non-empty FORM and at least one non-empty TRANSL   unit: W
  3  number of W accounts for every word in the S FORM      unit: S
  4  W FORM contains no Han characters                      unit: W
  5  W FORMs, markers stripped, reconstitute the S FORM     unit: S
  6  every morpheme implied by the W FORM has an M          unit: W
  7  M with a FORM has a non-empty Mandarin gloss           unit: M
  8  M FORMs recombine to the W FORM, infixes re-embedded  unit: W
  9  M FORM contains no Han characters                      unit: M
 10  M Mandarin gloss carries Han                           unit: M
 11  Mandarin free translation is non-empty                 unit: S
 12  M has a FORM (a form-less M marks a surplus gloss piece)   unit: M
 13  S has a W tier                                         unit: S
 14  S FORM contains no Han characters                      unit: S
 15  a TRANSL labelled zho carries Han                      unit: TRANSL
 16  total S blocks (a count, not a rate)                   unit: S
 17  M with a FORM has a non-empty English gloss            unit: M
 18  M English gloss is free of Han                         unit: M
 19  W has a non-empty Mandarin gloss                       unit: W
 20  W has a non-empty English gloss                        unit: W
 21  the Mandarin gloss has one piece per morpheme          unit: W
 22  the English gloss has one piece per morpheme           unit: W

The gloss tests come in Mandarin/English pairs at both tiers: 19/20 for words,
7/17 for morphemes, plus 10/18 asking whether each gloss is actually in the
language its xml:lang claims. The sentence sources carry two glosses per row --
Mandarin and English -- so every W and M there should have both TRANSLs.

The GRAMMAR sources carry one gloss per row, in Mandarin (with the odd Latin
letter where no character fits); their third column is a "_" placeholder. There
is no English gloss to test, so pass --no-english for grammar and tests 17, 18
and 20 report n/a rather than a misleading 0%.

Tests 21/22 are the per-language form of the alignment question that tests 6
and 12 can only ask once. They have to be separate because the two glosses do
not agree on where a boundary falls: the Mandarin gloss often writes "." where
the English writes "-" for the same morpheme break (zho "主焦.去" against eng
"AF-go" for the two-piece form "m-usa\'"), so one gloss can align with the form
while the other does not. In the sentence sources that is 158 rows; in stories
the glosses agree with each other but not the form in 5647 more.

Tests 8 (the morphemes rebuild the word) and 9 (the morpheme form has no Han)
remain single: they read the FORM only and have no gloss to vary by language.
A "_" is the sources' placeholder for an absent gloss and counts as empty
throughout.

Test 3 lets a clitic be written either way -- the sentence tier may print a
clitic as its own token where the word tier attaches it ('nipu’a kee' vs
'ni-pu’a=kee'), or attach it on both tiers ('’acecu' vs '’ace=cu'). Each clitic
is resolved individually against the sentence text rather than by allowing a
range of counts, so a sentence containing clitics does not thereby admit
unrelated missing or extra words.

Test 15 catches a mislabelled gloss column. The sources do not agree on which
column is Chinese -- some write Chinese first, some English, and one language
mixes the two within itself -- so assigning columns positionally tags Chinese
as English and vice versa. Test 10 cannot see that (it asks only whether SOME
gloss carries Han), which left the realignment step unmeasurable.

Test 13 is a tracker, not a target. Some sentences legitimately carry no word
tier -- A2 vocabulary entries, and sentences the source never glossed -- so a
figure below 100% is expected; it is here so the number stays visible and any
sudden movement in it gets noticed.

Test 12 exists because a gloss that splits into more pieces than its word form
leaves the surplus with nothing to attach to. Parking it in a form-less M keeps
it in the data and makes it countable; without this test those pieces are simply
dropped and nothing fails.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
INFIX_GLOSS = re.compile(r"<[^>]+>")
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
MARKERS = re.compile(r"[-=<>∅]")
# Sentence punctuation only. The straight apostrophe is the glottal-stop
# LETTER in these orthographies (POL-018) and is never stripped.
PUNCT = re.compile(r"[.,;:!?()\[\]\"\u3002\uff0c\u3001\uff1f\uff01\u201c\u201d]")



def substantive(text) -> bool:
    """True when the cell carries actual content, not a placeholder.

    A FORM of '-', '=', '_', '.', '@@' or a TRANSL of '_' satisfies a bare
    non-empty test while saying nothing. Requiring a letter (any script, so the
    Formosan Latin extensions and a null morpheme's O-stroke both count) or a
    digit is what "has content" was always meant to mean.
    """
    # U+2205 EMPTY SET and U+00D8 O-STROKE are the null morpheme: real
    # content, but U+2205 is category Sm, so a category test alone rejects it.
    return any(unicodedata.category(c)[0] in ("L", "N") or c in "\u2205\u00d8"
               for c in str(text or ""))

def has_han(text: str | None) -> bool:
    return bool(HAN.search(text or ""))


def squash(text: str | None) -> str:
    """Comparable form: markers, punctuation, whitespace, case and accents gone.

    Case is folded because the sentence FORM capitalises sentence-initially while
    the word tier does not ('Laqi na' vs 'laqi=na'). Accents are folded because
    the sentence tier marks stress where the word tier does not ('páriku' vs
    'pariku', 'iávatu' vs 'iavatu') -- a difference in notation, not in the word.
    Both are the same string for the purposes of tests 5 and 8.

    Note ʉ (U+0289) is a LETTER, not an accented u, and survives folding.
    """
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = unicodedata.normalize("NFC", text)
    return "".join(PUNCT.sub("", MARKERS.sub("", text)).split()).lower()


def form_text(el) -> str:
    """FORM text including tails around child elements such as <UNCLEAR/>."""
    node = el.find("FORM[@kindOf='original']")
    return "".join(node.itertext()) if node is not None else ""


PLACEHOLDER = {"", "_"}


def transls(el) -> dict:
    """{lang: text}, with the sources' "_" placeholder treated as absent."""
    out = {}
    for t in el.findall("TRANSL"):
        text = (t.text or "").strip()
        out[t.get(XML_LANG)] = "" if text in PLACEHOLDER else text
    return out


def clitic_alignment(s_form: str, forms: list) -> bool:
    """Whether the word tier accounts for exactly the sentence's tokens.

    The two tiers need not agree on where words divide, in either direction:

      one W, several sentence tokens   'nipu’a kee'  vs  'ni-pu’a=kee'
      several W, one sentence token    'itiza'       vs  'i' + 't-iza'

    So the walk consumes a group of word forms against a group of sentence
    tokens whenever their text agrees exactly. Grouping requires an exact
    match -- no guessing on morpheme boundaries. The one inexact allowance is
    a single word carrying a clitic ('='), which may be spelled slightly
    differently across tiers; there the span is accepted only if its text
    length is within one character. Anything else advances one-to-one, so a
    genuine extra or missing word desynchronises the walk and fails.
    """
    tokens = [squash(t) for t in s_form.split()]
    words = [squash(f) for f in forms]
    raw = list(forms)
    MAX = 4
    i = j = 0
    while i < len(words) and j < len(tokens):
        if words[i] == tokens[j]:
            i, j = i + 1, j + 1
            continue
        # Try grouping on either side, smallest total group first.
        found = None
        for total in range(3, 2 * MAX + 1):
            for a in range(1, min(MAX, len(words) - i) + 1):
                b = total - a
                if not 1 <= b <= min(MAX, len(tokens) - j):
                    continue
                if "".join(words[i:i + a]) == "".join(tokens[j:j + b]):
                    found = (a, b)
                    break
            if found:
                break
        if found:
            i, j = i + found[0], j + found[1]
            continue
        # A clitic-bearing word may be spelled differently across tiers, so its
        # span cannot be read off the text; take the span whose length fits best.
        if "=" in raw[i]:
            pieces = [p for p in raw[i].split("=") if p]
            best = None
            for k in range(1, min(len(pieces), len(tokens) - j) + 1):
                delta = abs(len("".join(tokens[j:j + k])) - len(words[i]))
                if best is None or delta < best[0]:
                    best = (delta, k)
            if best and best[0] <= 1 and best[1] > 1:
                i, j = i + 1, j + best[1]
                continue
        # Otherwise assume one word to one token. This test counts words, so a
        # spelling difference between the tiers is test 5's business -- but the
        # two must still be recognisably the same word. Without that guard a
        # walk that has slipped by one keeps marching, comparing word N with
        # token N+1, and still balances at the end, so a misaligned sentence
        # passes. Below the threshold we call it desynchronised and fail.
        if SequenceMatcher(None, words[i], tokens[j]).ratio() < 0.5:
            return False
        i, j = i + 1, j + 1
    return i == len(words) and j == len(tokens)


def recombine_morphemes(forms: list) -> str:
    """Rebuild a word from its morpheme forms, re-embedding any infixes.

    An infix is not a prefix: its morpheme sits beside the base in document
    order, but belongs *inside* it, at the '-' the base carries as its
    embedding point. Joining the forms left to right would give 'um' + 'ta'
    for 't<um>a'; inserting gives 't' + 'um' + 'a'. Without this, any pipeline
    that expands infixes is penalised for doing so.
    """
    pending, out = [], []
    for form in forms:
        text = (form or "").strip()
        # Two conventions for an infix morpheme are in use: angle brackets
        # ('<um>', what expand_infixes emits) and hyphen-flanked ('-n-', what
        # the published XML carries). Both mean the same thing here.
        if re.fullmatch(r"<[^>]*>", text):
            pending.append(text.strip("<>"))
            continue
        if re.fullmatch(r"-[^-]+-", text):
            pending.append(text.strip("-"))
            continue
        if pending and "-" in text:
            pieces = text.split("-")
            rebuilt = pieces[0]
            for piece in pieces[1:]:
                rebuilt += (pending.pop(0) if pending else "") + piece
            text = rebuilt
        elif pending:
            # A word-initial or word-final infix leaves no embedding point:
            # expand_infixes strips the hyphen in those positions ('<n>apa' ->
            # base 'apa'), so the position cannot be read off the base. Prepend,
            # which is the word-initial case; the caller compares both.
            text = "".join(pending) + text
            pending = []
        out.append(text)
    return squash("".join(out) + "".join(pending))


def morphemes_match_word(forms: list, w_form: str) -> bool:
    """Whether the morpheme forms rebuild the word, either infix placement."""
    target = squash(w_form)
    if recombine_morphemes(forms) == target:
        return True
    # Try the word-final placement for a bare (hyphenless) infix host.
    swapped, pending = [], []
    for form in forms:
        text = (form or "").strip()
        if re.fullmatch(r"<[^>]*>", text) or re.fullmatch(r"-[^-]+-", text):
            pending.append(text.strip("<>-"))
        else:
            swapped.append(text + "".join(pending))
            pending = []
    return squash("".join(swapped) + "".join(pending)) == target


def morpheme_count(form: str) -> int:
    """Morphemes implied by a W FORM's own markers.

    'kʉnʉ-ʉn' -> 2; 'h<m>uwa' -> 2 (infix + root); a bare word -> 1.
    """
    stripped = form.strip()
    if not stripped:
        return 0
    infixes = len(re.findall(r"<[^>]+>", stripped))
    rest = re.sub(r"<[^>]+>", "", stripped)
    # A piece carrying no letter, digit or null symbol is punctuation that
    # rode along on the form, not a morpheme.
    pieces = [p for p in re.split(r"[-=]", rest) if p and substantive(p)]
    return max(1, len(pieces)) + infixes


def load_json_records(json_dir: Path) -> dict:
    """{(file stem, record id): record} for every grammar JSON entry."""
    out = {}
    for path in sorted(json_dir.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        recs = data if isinstance(data, list) else (list(data.values())[0] if data else [])
        if not isinstance(recs, list):
            continue
        for rec in recs:
            if isinstance(rec, list) and len(rec) > 1 and isinstance(rec[1], dict):
                out[(path.stem, str(rec[0]))] = rec[1]
    return out


def run(xml_dir: Path, json_dir: Path) -> tuple[Counter, Counter, Counter]:
    ok, bad, skipped = Counter(), Counter(), Counter()

    def check(test: str, condition: bool) -> None:
        (ok if condition else bad)[test] += 1

    sentence_ids = set()
    for path in sorted(xml_dir.rglob("*.xml")):
        try:
            root = etree.parse(str(path)).getroot()
        except Exception:
            continue
        for s in root.iter("S"):
            sid = s.get("id") or ""
            sentence_ids.add(sid)
            s_form = form_text(s)
            words = s.findall("W")

            check("1 S FORM non-empty", bool(s_form.strip()))
            check("13 S has a W tier", bool(words))
            for el in s.iter():
                if el.tag != "TRANSL" or el.get(XML_LANG) != "zho":
                    continue
                text = (el.text or "").strip()
                if text:
                    check("15 zho TRANSL carries Han", has_han(text))
            check("14 S FORM has no Han", not has_han(s_form))
            # A sentence with no W tier is a failure to analyse, not a case the
            # W-scoped tests sit out. Scoring it "skipped" let the prune post a
            # perfect 3/5 by deleting exactly the sentences that failed them.
            if not words:
                check("3 #W accounts for S FORM words", False)
                check("5 W FORMs reconstitute S FORM", False)
            else:
                check("3 #W accounts for S FORM words",
                      clitic_alignment(s_form, [form_text(w) for w in words]))
                joined = "".join(squash(form_text(w)) for w in words)
                check("5 W FORMs reconstitute S FORM", joined == squash(s_form))

            free = {t.get(XML_LANG): (t.text or "").strip() for t in s.findall("TRANSL")}
            check("11 Mandarin free translation non-empty",
                  bool(free.get("zho", "").strip()))

            for w in words:
                w_form = form_text(w)
                w_tr = transls(w)
                check("2 W FORM and TRANSL non-empty",
                      bool(w_form.strip()) and any(v for v in w_tr.values()))
                check("19 W has a Mandarin gloss", bool(w_tr.get("zho")))
                check("20 W has an English gloss", bool(w_tr.get("eng")))
                check("4 W FORM has no Han", not has_han(w_form))

                for lang, name in (("zho", "21 Mandarin gloss aligns with form"),
                                   ("eng", "22 English gloss aligns with form")):
                    gloss = w_tr.get(lang, "")
                    if gloss and MARKERS.search(w_form):
                        # An infix gloss is its own morpheme, exactly as the
                        # infix is on the form side. Splitting the gloss on
                        # [-=] alone counts '<um>' in the form but not
                        # '<主事焦點>' in the gloss, so every infixed word failed
                        # a test it should pass (273 of grammar's 328 failures).
                        pieces = (len([p for p in re.split(r"[-=]", gloss) if p])
                                  + len(INFIX_GLOSS.findall(gloss)))
                        check(name, pieces == morpheme_count(w_form))

                ms = w.findall("M")
                if MARKERS.search(w_form):
                    # Count only M that carry a form: a form-less M marks a
                    # surplus gloss piece (test 12), not an implied morpheme.
                    formed = [m for m in ms if form_text(m).strip()]
                    check("6 every implied morpheme has an M",
                          len(formed) == morpheme_count(w_form))
                else:
                    skipped["W FORM has no segmentation markers"] += 1
                if ms:
                    check("8 M FORMs recombine to W FORM",
                          morphemes_match_word([form_text(m) for m in ms], w_form))
                else:
                    skipped["W with no M children"] += 1

                for m in ms:
                    m_form = form_text(m)
                    m_tr = transls(m)
                    check("12 M has a FORM", substantive(m_form))
                    if not m_form.strip():
                        # A surplus-gloss marker: tests about the form do not apply.
                        skipped["M is a surplus-gloss marker"] += 1
                        continue
                    check("7 M has a Mandarin gloss", substantive(m_tr.get("zho")))
                    check("17 M has an English gloss", bool(m_tr.get("eng")))
                    check("9 M FORM has no Han", not has_han(m_form))
                    if m_tr.get("zho"):
                        check("10 M Mandarin gloss carries Han",
                              has_han(m_tr["zho"]))
                    if m_tr.get("eng"):
                        check("18 M English gloss is free of Han",
                              not has_han(m_tr["eng"]))

    for (stem, rid) in load_json_records(json_dir):
        check("0 JSON record has an S block",
              any(sid.endswith(f"_S_{rid}") or sid == f"{stem}_S_{rid}"
                  for sid in sentence_ids))
    return ok, bad, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml", required=True, type=Path)
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--label", default="")
    ap.add_argument("--no-english", action="store_true",
                    help="the sources carry no English gloss (grammar), so the "
                         "English tests (17, 18, 20, 22) report n/a "
                         "rather than 0%%")
    ap.add_argument("--na", default="",
                    help="comma-separated test numbers this tree cannot be scored "
                         "on, e.g. a pipeline that never emits the element under "
                         "test would otherwise score 100%% by omission")
    args = ap.parse_args()

    na = {t.strip() for t in args.na.split(",") if t.strip()}
    if args.no_english:
        na |= {"17", "18", "20", "22"}
    ok, bad, skipped = run(args.xml, args.json)
    print(f"\n=== {args.label or args.xml}")
    print(f"  {'test':44}{'pass':>9}{'fail':>9}{'% pass':>9}")
    for test in sorted(set(ok) | set(bad)):
        p, f = ok[test], bad[test]
        if test.split()[0] in na:
            print(f"  {test:44}{'-':>9}{'-':>9}{'n/a':>9}")
            continue
        pct = 100.0 * p / (p + f) if (p + f) else 0.0
        print(f"  {test:44}{p:>9}{f:>9}{pct:>8.1f}%")
    total_s = ok.get("1 S FORM non-empty", 0) + bad.get("1 S FORM non-empty", 0)
    print(f"  {'16 total S blocks':44}{total_s:>9}{'-':>9}{total_s:>9}")
    if skipped:
        print("  not applicable:")
        for k in sorted(skipped):
            print(f"    {k:42}{skipped[k]:>9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
