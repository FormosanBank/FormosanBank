#!/usr/bin/env python3
"""Take the literal '/' out of W and M FORMs (V121 HARD), per POL-027/028.

The source writes a word's competing readings separated by '/'. Left in place
they violate V121 ("parens or '/' in a W- or M-level FORM is forbidden") and
they poison the morpheme tier, which splits them into nonsense like 'lrigi/ma'.

Two outcomes, decided by POL-028's own test rather than by guessing:

* the readings are **spelling variants** of one another (they overlap highly and
  neither is more than twice the other's length) -- the first becomes the FORM
  and each other becomes a sibling FORM[@kindOf='alternate'], which is exactly
  what POL-028 defines an alternate to be.
* the readings are **competing lexemes** ('ma-lrigi/ma-elre-elrenge/ma-adraw')
  -- POL-027 makes those separate S blocks, which is a larger change than this
  script should make on its own. The first reading is kept so the FORM is legal,
  and the discarded readings are recorded in @notes so nothing is lost and the
  POL-027 pass has a worklist.

In both cases the word's morphemes are regenerated from the surviving form,
because the ones built from the slashed string describe nothing.

    python resolve_slash_alternatives.py --xml_dir <dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apply_prune_and_mirror import segment_from_form  # noqa: E402

MARK = re.compile(r"[-=<>]")
OVERLAP_MIN = 0.6          # POL-028: an alternate looks like its sibling
LENGTH_RATIO = 2           # POL-028: neither form may be twice the other


def _bare(text: str) -> str:
    return MARK.sub("", text or "")


def is_spelling_variant(parts: list) -> bool:
    if len(parts) < 2:
        return False
    longest, shortest = max(map(len, parts)), min(map(len, parts))
    if longest > LENGTH_RATIO * max(shortest, 1):
        return False
    first = _bare(parts[0])
    return all(difflib.SequenceMatcher(None, first, _bare(p)).ratio() >= OVERLAP_MIN
               for p in parts[1:])



def _readings(raw: str) -> list:
    """The full word readings a slashed form encodes.

    The slash scope is the MORPHEME, not the word. 'pua/mua/mu-lebe' means the
    first morpheme alternates three ways while '-lebe' is shared, so the
    readings are 'pua-lebe', 'mua-lebe', 'mu-lebe' -- not the naive string split
    'pua', 'mua', 'mu-lebe', which drops '-lebe' from two of the three.

    So whatever follows the first segmentation marker in the LAST alternative is
    a shared tail, and is appended to the earlier alternatives.
    """
    parts = [p.strip() for p in (raw or "").split("/") if p.strip()]
    if len(parts) < 2:
        return parts
    tail_match = re.search(r"[-=]", parts[-1])
    if not tail_match:
        return parts
    tail = parts[-1][tail_match.start():]
    return [p + tail if not re.search(r"[-=]", p) else p for p in parts[:-1]] + [parts[-1]]


def _forms(el):
    return [f for f in el.findall("FORM")]


def _pick_base(parts: list, sentence_form: str) -> int:
    """Index of the reading the sentence itself uses, else 0.

    Taking the first reading blindly picked 'ngu' out of 'ngu/mu-a-ta-tulru'
    while the sentence form read 'muatatulru' -- the word tier then described a
    sentence it did not belong to. The sentence form is the arbiter.
    """
    haystack = _bare(sentence_form).replace(" ", "").lower()
    for i, part in enumerate(parts):
        needle = _bare(part).replace(" ", "").lower()
        if needle and needle in haystack:
            return i
    return 0


def resolve_word(w, stats: Counter, sentence_form: str = "") -> str | None:
    """Resolve a slashed W FORM. Returns the surviving base form, or None."""
    form = w.find("FORM[@kindOf='original']")
    if form is None:
        form = w.find("FORM")
    if form is None or "/" not in (form.text or ""):
        return None
    raw = form.text
    parts = _readings(raw)
    if not parts:
        return None
    if len(parts) == 1:
        form.text = parts[0]
        stats["trailing slash removed"] += 1
        return parts[0]

    keep = _pick_base(parts, sentence_form)
    if keep:
        stats["base chosen to match the sentence form, not the first reading"] += 1
    parts = [parts[keep]] + [p for i, p in enumerate(parts) if i != keep]
    form.text = parts[0]
    if is_spelling_variant(parts):
        for extra in parts[1:]:
            alt = etree.SubElement(w, "FORM")
            alt.set("kindOf", "alternate")
            alt.text = extra
        stats["spelling variants -> FORM[@kindOf='alternate']"] += 1
    else:
        note = "competing readings (POL-027, pending split): " + " / ".join(parts[1:])
        form.set("notes", ((form.get("notes") or "") + " " + note).strip())
        stats["competing lexemes -> first reading kept, rest in @notes"] += 1

    # The morphemes were built from the slashed string; rebuild them.
    for m in w.findall("M"):
        w.remove(m)
    pieces = segment_from_form(parts[0])
    if len(pieces) > 1:
        for i, piece in enumerate(pieces):
            m = etree.SubElement(w, "M")
            m.set("id", f"{w.get('id')}M{i}")
            mf = etree.SubElement(m, "FORM")
            mf.set("kindOf", "original")
            mf.text = piece
        stats["  morpheme tiers rebuilt from the surviving form"] += 1
    return parts[0]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats, files = Counter(), 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = False
        for s in tree.getroot().iter("S"):
            for w in s.findall("W"):
                sf = s.find("FORM[@kindOf='original']")
                if sf is None:
                    sf = s.find("FORM")
                base = resolve_word(w, stats, (sf.text or "") if sf is not None else "")
                if base is None:
                    continue
                changed = True
                # Keep the sentence form in step with the word tier.
                for sf in _forms(s):
                    if sf.text and "/" in sf.text:
                        sf.text = " ".join(
                            (tok.split("/")[0] if "/" in tok else tok)
                            for tok in sf.text.split())
                        stats["sentence forms de-slashed"] += 1
        if changed and not args.dry_run:
            tree.write(str(path), encoding="utf-8", xml_declaration=True)
            files += 1
    print(f"files modified: {files}")
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
