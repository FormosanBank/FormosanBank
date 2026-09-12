#!/usr/bin/env python3
"""Is each tier in the language it claims to be? Run over any built XML tree.

The same test validate_entries.py applies to the JSON, applied to the XML so
two builds can be compared on the one thing a reader cares about: whether a
Thao FORM is Thao and an English TRANSL is English. Both lexicons are external
to Blust's book - English from wordfreq's top 1,000, Thao from FormosanBank's
ILRDF_Dicts - so neither can be evidence for the other.

A field is judged only when it has at least four tokens; a capitalised token is
a proper name and belongs to both languages, so it is not evidence for either.
"""

from __future__ import annotations

import argparse
import collections
import re
import sys
import unicodedata
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_entries import load_lexicons  # noqa: E402

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
NON_THAO_LETTERS = re.compile(r"[vxVX]")
MIN_TOKENS = 4
MAJORITY = 0.5


def tokens(text: str) -> list[str]:
    text = " ".join(w for w in (text or "").split() if not w[:1].isupper())
    text = unicodedata.normalize("NFC", text).replace("–", "-")
    return [
        t for t in (
            piece.strip(".,;:?!`'\"()[]").replace("-", "").lower()
            for piece in text.split()
        ) if t
    ]


def score(text: str, english: set, thao: set) -> tuple[float, float, int]:
    toks = tokens(text)
    if not toks:
        return 0.0, 0.0, 0
    e = sum(1 for t in toks if t in english)
    h = sum(1 for t in toks if t in thao)
    return e / len(toks), h / len(toks), len(toks)


def check(path: Path, english: set, thao: set) -> tuple[collections.Counter, list]:
    counts = collections.Counter()
    hits = []
    for xml in sorted(path.glob("*.xml")):
        for sentence in etree.parse(str(xml)).getroot().findall("S"):
            form = sentence.find('FORM[@kindOf="original"]')
            value = (form.text or "") if form is not None else ""
            counts["S"] += 1
            if NON_THAO_LETTERS.search(value):
                counts["L1 FORM uses a letter Thao lacks"] += 1
                hits.append(("L1", sentence.get("id"), value[:60]))
            e, h, n = score(value, english, thao)
            if n >= MIN_TOKENS and e >= MAJORITY:
                counts["L2 FORM reads as English"] += 1
                hits.append(("L2", sentence.get("id"), value[:60]))
            for translation in sentence.findall("TRANSL"):
                counts["TRANSL"] += 1
                e, h, n = score(translation.text or "", english, thao)
                if n >= MIN_TOKENS and h >= MAJORITY:
                    counts["L3 TRANSL reads as Thao"] += 1
                    hits.append(("L3", sentence.get("id"), (translation.text or "")[:60]))
                if translation.get(XML_LANG) != "eng":
                    counts["L4 TRANSL not tagged eng"] += 1
    return counts, hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trees", nargs="+", type=Path)
    parser.add_argument("--show", type=int, default=6)
    args = parser.parse_args()
    english, thao = load_lexicons()
    for tree in args.trees:
        counts, hits = check(tree, english, thao)
        print(f"\n=== {tree} ===")
        print(f"  {counts['S']:,} S, {counts['TRANSL']:,} TRANSL")
        flagged = 0
        for rule in sorted(k for k in counts if k.startswith("L")):
            print(f"  {rule:34} {counts[rule]:5}   "
                  f"{counts[rule] / max(counts['S'], 1):.4%} of S")
            flagged += counts[rule]
        print(f"  {'total wrong-language findings':34} {flagged:5}")
        for rule, identifier, value in hits[: args.show]:
            print(f"      {rule} {identifier:28} {value!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
