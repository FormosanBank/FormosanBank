#!/usr/bin/env python3
"""Regenerate the Siraya standard-FORM tier from the original tier.

Policy (from the source dev repo's ``fix_linebreak_hyphens.py``): the
``standard`` tier is a copy of the ``original`` tier with **OCR line-break
hyphens** removed, while **morpheme / orthographic hyphens are kept**.

The set of line-break hyphens was determined once, on the pre-QC original
text, by a conservative frequency rule (a rare hyphenated form whose
de-hyphenated version is much more common) and recorded in the sibling
``hyphen_removals.csv`` (158 distinct forms / 199 occurrences). We apply that
fixed, documented set here rather than re-deriving it, because later QC edits
to the original tier shift token frequencies and would change the derived set.

This script rebuilds every ``FORM[@kindOf="standard"]`` as its sibling
``FORM[@kindOf="original"]`` with exactly those recorded merges applied, so the
standard tier stays in sync with the (QC-cleaned) original tier — inheriting
its punctuation (editorial ``(...)``, single ``-``) while keeping every
morpheme hyphen. Only the standard FORM text is rewritten; nothing else in the
files is touched. Idempotent.

    python CodeAndDocs/regenerate_standard_tier.py   # run from the corpus root
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

from lxml import etree

CORPUS_ROOT = Path(__file__).resolve().parents[1]          # Corpora/Siraya_Gospels
XML_DIRS = [CORPUS_ROOT / "XML" / "Siraya" / "John",
            CORPUS_ROOT / "XML" / "Siraya" / "Matthew"]
CSV_PATH = Path(__file__).resolve().parent / "hyphen_removals.csv"

_LETTER = r"A-Za-zÀ-ɏ"                            # Latin + Latin-1/Ext-A/B
_WORD = re.compile(rf"[{_LETTER}][{_LETTER}'\-]*")


def load_replacements() -> dict[str, str]:
    with CSV_PATH.open(encoding="utf-8") as fh:
        return {row["hyphenated_form"].lower(): row["merged_form"]
                for row in csv.DictReader(fh)}


def apply_merges(text: str, repl: dict[str, str]) -> str:
    def _repl(m: re.Match) -> str:
        w = m.group(0)
        merged = repl.get(w.lower())
        if merged is None:
            return w
        # Don't merge a hyphen adjacent to an editorial bracket ( word-( / )-word ).
        if w.endswith("-") and m.end() < len(text) and text[m.end()] in "([":
            return w
        if m.start() >= 2 and text[m.start() - 2:m.start()] in (")-", "]-"):
            return w
        return (merged[0].upper() + merged[1:]) if w[0].isupper() else merged
    return _WORD.sub(_repl, text)


def iter_files():
    for d in XML_DIRS:
        yield from sorted(d.glob("chapter*.xml"),
                          key=lambda p: int(p.stem.replace("chapter", "")))


def main() -> None:
    repl = load_replacements()
    updated = 0
    for f in iter_files():
        raw = f.read_bytes()
        trailing_nl = raw.endswith(b"\n")
        tree = etree.parse(str(f))
        changed = False
        for s in tree.getroot().iter("S"):
            original = standard = None
            for form in s.findall("FORM"):
                if form.get("kindOf") == "original":
                    original = form
                elif form.get("kindOf") == "standard":
                    standard = form
            if original is None or standard is None or not original.text:
                continue
            new_text = apply_merges(original.text, repl)
            if standard.text != new_text:
                standard.text = new_text
                changed = True
                updated += 1
        if changed:
            out = etree.tostring(tree, encoding="UTF-8", xml_declaration=True)
            # Preserve the file's original XML declaration verbatim (lxml
            # normalizes e.g. 'utf-8' -> 'UTF-8'); keep the diff to FORM text only.
            orig_decl = raw.split(b"?>", 1)[0] + b"?>"
            out_head, out_tail = out.split(b"?>", 1)
            if out_head + b"?>" != orig_decl:
                out = orig_decl + out_tail
            if trailing_nl and not out.endswith(b"\n"):
                out += b"\n"
            f.write_bytes(out)
    print(f"standard FORMs rewritten: {updated}")


if __name__ == "__main__":
    main()
