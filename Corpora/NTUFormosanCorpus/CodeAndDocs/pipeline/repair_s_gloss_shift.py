#!/usr/bin/env python3
"""Re-home glosses that sit one word too high (the S-tier analogue of _repair_w).

repair_empty_morphemes._repair_w fixes a word whose morpheme glosses have
slipped: an M is left unglossed and a surplus gloss sits on a form-less shell.
The same slip happens one tier up. In 59_S_12 the source pairs a bare comma with
the gloss 'then', and every gloss from there on belongs to the *next* word:

    ','                then                 <- form-less, but glossed
    'at'               give-LF=1SG.NOM      <- 'at' means 'then'
    'saiv-an=ik'       3SG.GEN              <- means give-LF=1SG.NOM
    'saicia'           OBL                  <- means 3SG.GEN
    'mas'              money                <- means OBL
    'sui.'             (none)               <- means money

Shifting the glosses down from the form-less word to the unglossed one restores
every pairing and leaves the punctuation unglossed, which is correct.

A word is "form-less" when its FORM carries no letter or digit -- a comma, '@@',
'_'. Testing for an empty string misses every one of those.

The shift is applied only when it fills EVERY gap in the sentence and raises the
number of words whose form and gloss agree in morpheme count, so a coincidental
pairing cannot trigger it.

    python repair_s_gloss_shift.py --xml_dir <dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from collections import Counter
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SPLIT = re.compile(r"[-=]")


def form_text(el) -> str:
    node = el.find("FORM[@kindOf='original']")
    if node is None:
        node = el.find("FORM")
    return "".join(node.itertext()) if node is not None else ""


def formless(text: str) -> bool:
    text = (text or "").strip()
    return (text in ("", "_")
            or not any(unicodedata.category(c)[0] in ("L", "N") for c in text))


def glosses(w) -> dict:
    return {t.get(XML_LANG): (t.text or "") for t in w.findall("TRANSL")}


def unglossed(g: dict) -> bool:
    return not any(v.strip() and v.strip() != "_" for v in g.values())


def pieces(text: str) -> int:
    return len([p for p in SPLIT.split(text or "") if p.strip()])


def agreement(forms: list, gs: list) -> int:
    return sum(1 for f, g in zip(forms, gs)
               if not formless(f) and not unglossed(g)
               and pieces(f) == pieces(next(iter(g.values()), "")))


def repair(sentence, stats: Counter) -> bool:
    words = sentence.findall("W")
    if len(words) < 2:
        return False
    forms = [form_text(w) for w in words]
    gs = [glosses(w) for w in words]
    gaps = [i for i, (f, g) in enumerate(zip(forms, gs))
            if not formless(f) and unglossed(g)]
    spares = [i for i, (f, g) in enumerate(zip(forms, gs))
              if formless(f) and not unglossed(g)]
    if not (gaps and spares):
        return False

    base = agreement(forms, gs)
    best = None
    for s in spares:
        for g in gaps:
            if g <= s:
                continue                      # a gloss only ever slips upward
            shifted = gs[:s] + [{}] + gs[s:g] + gs[g + 1:]
            if any(not formless(forms[i]) and unglossed(shifted[i])
                   for i in range(len(forms))):
                continue                      # would leave a word unglossed
            score = agreement(forms, shifted)
            if score > base and (best is None or score > best[1]):
                best = (shifted, score)
    if best is None:
        stats["sentences with a gap and a spare, not shiftable"] += 1
        return False

    for w, g in zip(words, best[0]):
        for t in w.findall("TRANSL"):
            w.remove(t)
        for lang, text in g.items():
            if lang is None:
                continue
            t = etree.SubElement(w, "TRANSL")
            t.set(XML_LANG, lang)
            t.text = text
    stats["sentences whose word glosses were shifted"] += 1
    stats["  words re-homed"] += len(best[0])

    # A donor that has handed its gloss on is left with a punctuation-only form
    # and no gloss: not a word, and add_phonology has nothing to say about it,
    # which then trips V073 (PHON must be non-empty). Drop it. The sentence form
    # keeps its punctuation; only the spurious W goes.
    for w in list(words):
        if formless(form_text(w)) and unglossed(glosses(w)):
            sentence.remove(w)
            stats["  form-less donor words removed"] += 1
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats, files = Counter(), 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = False
        for sentence in tree.getroot().iter("S"):
            changed |= repair(sentence, stats)
        if changed and not args.dry_run:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
            files += 1
    print(f"files modified: {files}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
