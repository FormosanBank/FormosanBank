#!/usr/bin/env python3
"""Test-driven audit of the NTU *Sentences* subcorpus XML.

A different suite from grammar_xml_tests.py, because the sources differ: a
sentence record carries TWO glosses per row, Mandarin and English, so every W
and M should hold two TRANSLs with the right xml:lang. Grammar carries one
gloss, in Mandarin, and no English tier exists there to test.

    python sentence_xml_tests.py --xml <XMLdir> --json <sentence JSON dir> [--label NAME]

Tests
  0  every JSON record has a corresponding S block          unit: JSON record
  1  S FORM is non-empty                                    unit: S
  2  W FORM and both TRANSLs are non-empty                  unit: W
  3  number of W accounts for every word in the S FORM      unit: S
  4  W FORM contains no Han                                 unit: W
  5  W FORMs, markers stripped, reconstitute the S FORM     unit: S
  6  morpheme count of W FORM and both TRANSLs match        unit: W
  7  W English TRANSL contains no Han                       unit: W
  8  W Mandarin TRANSL contains no lower-case Latin           unit: W
  9  Mandarin free translation is non-empty                 unit: S
 10  English free translation is non-empty                  unit: S
 11  Mandarin free translation contains no English          unit: S
 12  English free translation contains no Han               unit: S
 13  every M with a FORM has content in both TRANSLs        unit: M
 14  every M has content in its FORM                        unit: M
 15  S has a W tier                                         unit: S
 16  total S blocks (a count, not a rate)                   unit: S
 17  every morpheme implied by the W FORM has an M          unit: W

Test 17 asks whether the morpheme tier is actually there. A word whose only
internal structure is an infix carries no "-" or "=", so a splitter that keys on
those alone gives it no morphemes at all -- 162 words in this subcorpus. Only M
that carry a form are counted: a form-less M marks a surplus gloss piece, not a
morpheme.

Test 8 is stated as "contains only Han". Leipzig-style abbreviations (3PL, AF,
PFV) are legitimate inside an otherwise-Chinese gloss, and they are upper case,
so the test forbids only LOWER-case Latin -- which is what an untranslated
English word looks like.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
LATIN = re.compile(r"[A-Za-z]")
LOWER_LATIN = re.compile(r"[a-z]")
MARKERS = re.compile(r"[-=<>∅]")
PUNCT = re.compile(r"[.,;:!?()\[\]\"。，、？！“”]")
PLACEHOLDER = {"", "_"}



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

def has_han(text): return bool(HAN.search(text or ""))
def has_latin(text): return bool(LATIN.search(text or ""))
def has_lower_latin(text): return bool(LOWER_LATIN.search(text or ""))


def squash(text):
    """Comparable form: markers, punctuation, whitespace, case and accents gone."""
    text = unicodedata.normalize("NFD", text or "")
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = unicodedata.normalize("NFC", text)
    return "".join(PUNCT.sub("", MARKERS.sub("", text)).split()).lower()


def form_text(el):
    node = el.find("FORM[@kindOf='original']")
    return "".join(node.itertext()) if node is not None else ""


def transls(el):
    """{lang: text}, with the sources' "_" placeholder treated as absent."""
    out = {}
    for t in el.findall("TRANSL"):
        text = (t.text or "").strip()
        out[t.get(XML_LANG)] = "" if text in PLACEHOLDER else text
    return out


def morpheme_count(form):
    """Morphemes implied by a form's own markers: 'kʉnʉ-ʉn' -> 2, 'h<m>uwa' -> 2."""
    stripped = (form or "").strip()
    if not stripped:
        return 0
    infixes = len(re.findall(r"<[^>]+>", stripped))
    rest = re.sub(r"<[^>]+>", "", stripped)
    # A piece carrying no letter, digit or null symbol is punctuation that rode
    # along on the form ('m-qa-,' splits to 'm', 'qa', ','), not a morpheme.
    pieces = [p for p in re.split(r"[-=]", rest) if p and substantive(p)]
    return max(1, len(pieces)) + infixes


def gloss_pieces(gloss):
    """Morphemes a gloss accounts for.

    A piece carrying an infix marker glosses TWO morphemes, the infix and its
    host, because the sources attach the infix gloss to the host rather than
    separating it: '<PFV>plant' is one piece but two morphemes, matching the
    form 'p<en>aluma'. Counting pieces alone reported 2,375 story words as
    misaligned whose two glosses in fact agreed with each other and with the
    form.
    """
    total = 0
    for part in re.split(r"[-=]", gloss or ""):
        if not part:
            continue
        infixes = len(re.findall(r"<[^>]+>", part))
        total += infixes + (1 if re.sub(r"<[^>]+>", "", part).strip() else 0)
    return total


def clitic_alignment(s_form, forms):
    """Whether the word tier accounts for exactly the sentence's tokens.

    The tiers need not agree on where words divide, in either direction: one W
    may span several sentence tokens ('nipu’a kee' / 'ni-pu’a=kee'), or several
    W one token ('itiza' / 'i' + 't-iza'). Groups are matched only on an exact
    text match; a clitic-bearing word may be resolved by closest length; and
    anything else advances one to one, but only when the two are recognisably
    the same word, so a walk that has slipped desynchronises and fails.
    """
    from difflib import SequenceMatcher
    tokens = [squash(t) for t in s_form.split()]
    words = [squash(f) for f in forms]
    raw, MAX = list(forms), 4
    i = j = 0
    while i < len(words) and j < len(tokens):
        if words[i] == tokens[j]:
            i, j = i + 1, j + 1
            continue
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
        if SequenceMatcher(None, words[i], tokens[j]).ratio() < 0.5:
            return False
        i, j = i + 1, j + 1
    return i == len(words) and j == len(tokens)


def load_json_records(json_dir):
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


def run(xml_dir, json_dir):
    ok, bad, skipped = Counter(), Counter(), Counter()

    def check(test, condition):
        (ok if condition else bad)[test] += 1

    sentence_ids, total_s = set(), 0
    for path in sorted(xml_dir.rglob("*.xml")):
        try:
            root = etree.parse(str(path)).getroot()
        except Exception:
            continue
        for s in root.iter("S"):
            total_s += 1
            sentence_ids.add(s.get("id") or "")
            s_form = form_text(s)
            words = s.findall("W")
            free = transls(s)

            check("1 S FORM non-empty", bool(s_form.strip()))
            check("15 S has a W tier", bool(words))
            check("9 Mandarin free translation non-empty", bool(free.get("zho")))
            check("10 English free translation non-empty", bool(free.get("eng")))
            if free.get("zho"):
                check("11 Mandarin free translation has no English",
                      not has_latin(free["zho"]))
            if free.get("eng"):
                check("12 English free translation has no Han",
                      not has_han(free["eng"]))

            # A sentence with no W tier is a failure to analyse, not a case the
            # W-scoped tests sit out. Scoring it "skipped" let the prune post a
            # perfect 3/5 by deleting exactly the sentences that failed them.
            if not words:
                check("3 #W accounts for S FORM words", False)
                check("5 W FORMs reconstitute S FORM", False)
            else:
                check("3 #W accounts for S FORM words",
                      clitic_alignment(s_form, [form_text(w) for w in words]))
                check("5 W FORMs reconstitute S FORM",
                      "".join(squash(form_text(w)) for w in words) == squash(s_form))

            for w in words:
                w_form, w_tr = form_text(w), transls(w)
                check("2 W FORM and both TRANSLs non-empty",
                      bool(w_form.strip()) and bool(w_tr.get("zho"))
                      and bool(w_tr.get("eng")))
                check("4 W FORM has no Han", not has_han(w_form))
                if w_tr.get("eng"):
                    check("7 W English gloss has no Han", not has_han(w_tr["eng"]))
                if w_tr.get("zho"):
                    check("8 W Mandarin gloss has no lower-case Latin",
                          not has_lower_latin(w_tr["zho"]))
                if w_tr.get("zho") and w_tr.get("eng"):
                    n = morpheme_count(w_form)
                    check("6 morpheme count matches both glosses",
                          gloss_pieces(w_tr["zho"]) == n
                          and gloss_pieces(w_tr["eng"]) == n)
                else:
                    skipped["W without both glosses"] += 1

                if MARKERS.search(w_form):
                    formed = [m for m in w.findall("M") if form_text(m).strip()]
                    check("17 every implied morpheme has an M",
                          len(formed) == morpheme_count(w_form))
                else:
                    skipped["W FORM has no segmentation markers"] += 1

                for m in w.findall("M"):
                    m_form, m_tr = form_text(m), transls(m)
                    check("14 M has content in its FORM", substantive(m_form))
                    if substantive(m_form):
                        check("13 M with a FORM has both glosses",
                              substantive(m_tr.get("zho"))
                              and substantive(m_tr.get("eng")))

    for (stem, rid) in load_json_records(json_dir):
        check("0 JSON record has an S block",
              any(sid.endswith(f"_S_{rid}") or sid.startswith(f"{stem}_S_{rid}")
                  for sid in sentence_ids))
    return ok, bad, skipped, total_s


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml", required=True, type=Path)
    ap.add_argument("--json", required=True, type=Path)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    ok, bad, skipped, total_s = run(args.xml, args.json)
    print(f"\n=== {args.label or args.xml}")
    print(f"  {'test':44}{'pass':>9}{'fail':>9}{'% pass':>9}")
    for test in sorted(set(ok) | set(bad), key=lambda t: int(t.split()[0])):
        p, f = ok[test], bad[test]
        pct = 100.0 * p / (p + f) if (p + f) else 0.0
        print(f"  {test:44}{p:>9}{f:>9}{pct:>8.1f}%")
    print(f"  {'16 total S blocks':44}{total_s:>9}{'-':>9}{total_s:>9}")
    if skipped:
        print("  not applicable:")
        for k in sorted(skipped):
            print(f"    {k:42}{skipped[k]:>9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
