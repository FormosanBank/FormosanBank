#!/usr/bin/env python3
"""What shapes does a dictionary entry actually take?

The extractor in extract_source.py has no notion of an entry format. It is a
streaming heuristic: walk the rows, classify each span by its font, accumulate
into whatever record is open, and close that record when a row looks
structural. Nothing ever asserts that what it just read was a well-formed
entry, which is why every failure found so far was silent - a page in a
different font family, a translation set in the definition face, a column
margin fifteen points to the right.

This script asks the other question. It reads the same spans, types each one,
and reports the *sequence* of types each entry takes. If a handful of sequences
cover almost everything, then those are the formats the book is set in, and
every entry that does not match one is a defect worth looking at by name.

Element types, by font (FONT_ALIASES already applied, so printed p. 291 reads
like every other page):

    HEAD   T8 at the column's left margin      the headword
    ETY    T7 opening "(PAN" or "(PMP"         the etymology
    DEF    T7 / T2                             definition prose
    NUM    T11, a bare digit                   sense number
    LBL    T11, "[...]"                        grammatical label
    SUB    T9                                  sub-entry headword
    EX     T5 / T6                             a Thao example
    TR     T4                                  its English translation
    NOTE   T11 "NOTE:"                         a printed note
    XREF   Century / PMingLiU                  a cross-reference arrow or dash
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_source import (  # noqa: E402
    DICTIONARY_PAGES,
    SOURCE_FONTS,
    SUBENTRY_FONT,
    TRANSLATION_FONT,
    SOURCE_PATH,
    normalized_rows,
)
from pdf_text import join_spans  # noqa: E402

COLUMN_SPLIT = 300.0
BAR = "|"
ETYMOLOGY = re.compile(r"^\(P(AN|MP|Ph|WMP|CEMP|EF)\b")
LABEL = re.compile(r"^\[.*\]$")


def _type(span, text, margin):
    if span.font == "T8":
        return "HEAD" if span.x0 <= margin + 4.0 else "SUB"
    if span.font == SUBENTRY_FONT:
        return "SUB"
    if span.font in SOURCE_FONTS:
        return "EX"
    if span.font == TRANSLATION_FONT:
        return "TR"
    if span.font in {"T7", "T2"}:
        return "ETY" if ETYMOLOGY.match(text) else "DEF"
    if span.font == "T11":
        value = text.strip()
        if value.isdigit():
            return "NUM"
        if LABEL.match(value):
            return "LBL"
        if value.upper().startswith("NOTE"):
            return "NOTE"
        return "DEF"
    if span.font in {"Century", "PMingLiU"}:
        return "XREF"
    if span.font == "T10":
        # The bar brackets a headword; the arrow opens a cross-reference.
        if text.strip() == BAR:
            return "BAR"
        if text.strip() == "\u2192":
            return "XREF"
        return "DEF"          # italic inside a definition: a binomial, a citation
    return None


def entries(document):
    """Yield (headword, printed_page, [element types]) per main entry."""
    current = None
    for pdf_page in DICTIONARY_PAGES:
        rows = [r for r in normalized_rows(document, pdf_page) if 95.0 < r.y0 < 680.0]
        spans = [s for r in rows for s in r.spans]
        if not spans:
            continue
        margins = {
            col: min(s.x0 for s in spans if (s.x0 < COLUMN_SPLIT) == (col == 0))
            for col in (0, 1)
            if any((s.x0 < COLUMN_SPLIT) == (col == 0) for s in spans)
        }
        for col in (0, 1):
            if col not in margins:
                continue
            for row in rows:
                ordered = sorted(
                    (s for s in row.spans if (s.x0 < COLUMN_SPLIT) == (col == 0)),
                    key=lambda s: s.x0,
                )
                for span in ordered:
                    text = join_spans([span])
                    if not text.strip():
                        continue
                    kind = _type(span, text, margins[col])
                    if kind is None:
                        continue
                    if kind == "BAR":
                        # |WORD| at the head of a row opens a format-B entry;
                        # mid-row it is a cross-reference inside a definition.
                        if span is ordered[0]:
                            if current:
                                yield current
                            current = ["", pdf_page - 10, ["HEAD", "BAR"]]
                        elif current:
                            if current[2][-1] != "XREF":
                                current[2].append("XREF")
                        continue
                    if kind == "HEAD":
                        if current is not None and current[2][-2:] == ["HEAD", "BAR"]:
                            current[0] = text          # the bracketed headword
                            continue
                        if current:
                            yield current
                        current = [text, pdf_page - 10, ["HEAD"]]
                        continue
                    if current is None:
                        continue
                    if current[2][-1] != kind:
                        current[2].append(kind)
                    elif kind == "HEAD":
                        current[0] += text
    if current:
        yield current


# The grammar the book is set in, as far as these types can express it:
#
#     ENTRY  = HEAD [ETY] SENSE+
#     SENSE  = [NUM] [SUB] [LBL] DEF [BODY] [NOTE] (XREF NUM?)*
#     BODY   = (EX TR)+
#
# reduce() applies exactly that, bottom up, and returns what is left. An entry
# that reduces to "HEAD SENSE" or "HEAD SENSE+" is well formed; anything else
# is the residue worth looking at by name.


def _reduce_body(kinds):
    out, i = [], 0
    while i < len(kinds):
        if i + 1 < len(kinds) and kinds[i] == "EX" and kinds[i + 1] == "TR":
            while i + 1 < len(kinds) and kinds[i] == "EX" and kinds[i + 1] == "TR":
                i += 2
            out.append("BODY")
            continue
        out.append(kinds[i])
        i += 1
    return out


def _reduce_cite(kinds):
    """`|word|` inside a definition is a cross-reference, not a sub-entry.

    It reaches here as XREF SUB XREF (the bars either side of a bold headword)
    or as a bare XREF, and either way it belongs to the definition it sits in.
    """
    out, i = [], 0
    while i < len(kinds):
        if kinds[i] == "XREF":
            j = i + 1
            if j < len(kinds) and kinds[j] == "SUB":
                j += 1
                if j < len(kinds) and kinds[j] == "XREF":
                    j += 1
            out.append("DEF")
            i = j
            continue
        out.append(kinds[i])
        i += 1
    return out


def _reduce_note(kinds):
    """A printed NOTE line sets its body in the translation face."""
    out, i = [], 0
    while i < len(kinds):
        if kinds[i] == "NOTE":
            i += 1
            while i < len(kinds) and kinds[i] in {"TR", "DEF", "EX", "BODY"}:
                i += 1
            out.append("NOTE")
            continue
        out.append(kinds[i])
        i += 1
    return out


SENSE_ORDER = ["NUM", "SUB", "LBL", "DEF", "BODY", "NOTE"]
HEADS = {"HEAD", "HEADBAR"}


def _reduce_sense(kinds):
    out, i = [], 0
    while i < len(kinds):
        start, slot = i, 0
        seen_def = False
        while i < len(kinds) and slot < len(SENSE_ORDER):
            if kinds[i] == SENSE_ORDER[slot]:
                seen_def = seen_def or kinds[i] == "DEF"
                i += 1
                slot += 1
                continue
            slot += 1
        # A cross-reference names a sense of its target ("-> - ana -:2"), so a
        # sense number trailing one belongs to it, not to a sense here.
        while i < len(kinds) and kinds[i] in {"XREF", "NUM"}:
            if kinds[i] == "NUM" and (
                i == 0 or kinds[i - 1] not in {"XREF", "NUM"}
            ):
                break
            i += 1
        if seen_def and i > start:
            out.append("SENSE")
            continue
        out.append(kinds[start])
        i = start + 1
    return out


def _collapse(kinds):
    out = []
    for kind in kinds:
        if out and out[-1].rstrip("+") == kind:
            out[-1] = kind + "+"
        else:
            out.append(kind)
    return out


def reduce_entry(kinds: list[str]) -> list[str]:
    # A bracketed headword is the format-B opener; the bar carries no content
    # of its own once it has done that job.
    if kinds[:2] == ["HEAD", "BAR"]:
        kinds = ["HEADBAR"] + kinds[2:]
    kinds = [k for k in kinds if k != "BAR"]
    return _collapse(
        _reduce_sense(_reduce_note(_reduce_body(_reduce_cite(kinds))))
    )


def signature(kinds: list[str]) -> str:
    return " ".join(reduce_entry(kinds))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--top", type=int, default=25)
    parser.add_argument("--show", help="print the entries matching this signature")
    parser.add_argument("--json", type=Path, help="write every entry's signature")
    args = parser.parse_args()

    document = fitz.open(SOURCE_PATH)
    found = list(entries(document))
    counts = collections.Counter(signature(kinds) for _h, _p, kinds in found)
    total = sum(counts.values())

    if args.show:
        for head, page, kinds in found:
            if signature(kinds) == args.show:
                print(f"  {head!r} (printed p.{page}): {' '.join(kinds)}")
        return 0
    if args.json:
        args.json.write_text(
            json.dumps(
                [
                    {"headword": h, "printed_page": p, "elements": k,
                     "signature": signature(k)}
                    for h, p, k in found
                ],
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.json}")
        return 0

    print(f"{len(found)} main entries, {len(counts)} distinct signatures\n")
    running = 0
    for sig, n in counts.most_common(args.top):
        running += n
        print(f"  {n:5d}  {running / total * 100:5.1f}%  {sig}")
    tail = total - running
    print(f"\n  {tail:5d}  the remaining {len(counts) - args.top} signatures")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
