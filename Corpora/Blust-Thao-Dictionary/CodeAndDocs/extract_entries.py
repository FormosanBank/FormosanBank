#!/usr/bin/env python3
"""Extract the dictionary's headwords, sub-entries and definitions.

Separate from extract_source.py on purpose. That script reads the material the
Academia Sinica authorization names -- the interlinear texts and the example
sentences -- and treats a headword row only as a record boundary. This one reads
the entry apparatus around those examples: the headword, its homograph index,
the numbered senses, the grammatical labels, the English definition and the
etymology. Whether that apparatus is inside the authorized scope is a separate
question from whether it can be recovered; this script answers only the second.

Font roles in the dictionary body, established by inspection:

    T8   main headword (bold), set at the column's left margin
    T9   sub-entry headword (bold), indented
    T10  italic: the delimiter glyphs around a headword, and Latin binomials
    T11  sense numbers and bracketed grammatical labels, e.g. [IT]
    T7   definition prose and etymologies
    T5/T6  Thao example sentences   -- extract_source.py's business
    T4   English translations       -- extract_source.py's business
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

import fitz

try:
    from CodeAndDocs.pdf_text import (Span, append_wrapped, join_spans,
                                      learn_hyphenation_from, page_rows)
except ModuleNotFoundError:
    from pdf_text import (Span, append_wrapped, join_spans,
                          learn_hyphenation_from, page_rows)


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "CodeAndDocs" / "source-lock.json"
OUTPUT_PATH = ROOT / "CodeAndDocs" / "entry-records.json"
SOURCE_PATH = ROOT / "Private" / json.loads(
    LOCK_PATH.read_text(encoding="utf-8")
)["pdf_filename"]

DICTIONARY_PAGES = range(290, 1079)
COLUMN_SPLIT = 300.0
# A main headword sits at the column's left margin; anything further right that
# is still bold is a run-on inside a definition, not a new entry.
LEFT_MARGIN = {0: 112.0, 1: 308.0}
HEADWORD_FONT = "T8"
SUBENTRY_FONT = "T9"
LABEL_FONT = "T11"
DEFINITION_FONTS = {"T7", "T2"}
ITALIC_FONT = "T10"
EXAMPLE_FONTS = {"T5", "T6", "T4"}
# The italic Type 3 face returns two glyphs with no usable ToUnicode mapping.
# They bracket a headword and are typography, not content.
UNMAPPED_ITALIC = {"j", "!"}


def _column_spans(row, column: int) -> list[Span]:
    return sorted(
        (s for s in row.spans if (s.x0 < COLUMN_SPLIT) == (column == 0)),
        key=lambda s: s.x0,
    )


# The dictionary body sets words with tight inter-glyph spacing; the default
# 2.2pt gap splits them ("v ariet y"). extract_source.py uses 1.2 here too.
BODY_GAP = 1.2


def _join(spans: list[Span]) -> str:
    """Join spans that may span several printed lines.

    join_spans sorts by x, which is right within one line and destroys reading
    order across lines, so lines are joined separately and then folded with
    append_wrapped -- which is also what removes line-break hyphenation.
    """
    if not spans:
        return ""
    lines: list[list[Span]] = []
    for span in spans:
        if lines and abs(lines[-1][0].y0 - span.y0) <= 3.1:
            lines[-1].append(span)
        else:
            lines.append([span])
    text = ""
    for line in lines:
        text = append_wrapped(text, join_spans(line, gap=BODY_GAP))
    return _clean(text)


def _clean(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.;:?!)])", r"\1", text)


def _new_sense(number: int | None = None) -> dict[str, Any]:
    return {"number": number, "headword": None, "label": None, "_head": [],
            "_def": []}


def _flush(entry: dict[str, Any] | None, out: list[dict[str, Any]]) -> None:
    if entry is None:
        return
    entry["headword"] = _join(entry.pop("_head"))
    senses = []
    for sense in entry["senses"]:
        sense["headword"] = _join(sense.pop("_head")) or None
        sense["definition"] = _join(sense.pop("_def"))
        if sense["definition"] or sense["headword"]:
            senses.append(sense)
    entry["senses"] = senses
    if entry["headword"]:
        out.append(entry)


def extract_entries(document: fitz.Document) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    entry: dict[str, Any] | None = None
    sense: dict[str, Any] | None = None

    for pdf_page in DICTIONARY_PAGES:
        rows = [r for r in page_rows(document[pdf_page - 1]) if 95.0 < r.y0 < 680.0]
        for column in (0, 1):
            for row in rows:
                spans = _column_spans(row, column)
                if not spans:
                    continue
                index = 0
                while index < len(spans):
                    span = spans[index]
                    index += 1
                    if span.font in EXAMPLE_FONTS:
                        continue
                    if span.font == ITALIC_FONT and join_spans([span]) in UNMAPPED_ITALIC:
                        continue

                    if span.font == HEADWORD_FONT and span.x0 <= LEFT_MARGIN[column]:
                        _flush(entry, entries)
                        sense = _new_sense()
                        entry = {
                            "_head": [span],
                            "printed_page": pdf_page - 10,
                            "pdf_page": pdf_page,
                            "senses": [sense],
                        }
                        continue
                    if entry is None:
                        continue

                    if span.font == HEADWORD_FONT:
                        # Bold continuation of the headword itself.
                        (entry["_head"] if not entry["senses"][0]["_def"]
                         else sense["_def"]).append(span)
                        continue

                    if span.font == SUBENTRY_FONT:
                        # A sub-entry headword runs over several spans and can
                        # wrap a line; only start a new sense when the previous
                        # one has already taken definition text.
                        if sense is None or sense["_def"]:
                            sense = _new_sense(sense["number"] if sense else None)
                            entry["senses"].append(sense)
                        sense["_head"].append(span)
                        continue

                    if span.font == LABEL_FONT:
                        value = join_spans([span]).strip()
                        if value.isdigit():
                            sense = _new_sense(int(value))
                            entry["senses"].append(sense)
                        elif value.startswith("[") and sense is not None:
                            sense["label"] = value
                        continue

                    if span.font in DEFINITION_FONTS or span.font == ITALIC_FONT:
                        if sense is None:
                            sense = _new_sense()
                            entry["senses"].append(sense)
                        sense["_def"].append(span)
    _flush(entry, entries)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    document = fitz.open(SOURCE_PATH)
    learn_hyphenation_from(document, DICTIONARY_PAGES)
    entries = extract_entries(document)
    payload = {
        "source_pdf_sha256": json.loads(LOCK_PATH.read_text(encoding="utf-8"))[
            "pdf_sha256"
        ],
        "statistics": {
            "entries": len(entries),
            "senses": sum(len(e["senses"]) for e in entries),
            "sub_entries": sum(
                1 for e in entries for s in e["senses"] if s["headword"]
            ),
        },
        "entries": entries,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.summary:
        print(json.dumps(payload["statistics"], indent=2))
        for entry in entries[:6]:
            print(f"\n{entry['headword']!r}  (printed p.{entry['printed_page']})")
            for s in entry["senses"]:
                print(f"   {s['number']} {s['headword']!r} {s['label']!r}: {s['definition'][:90]!r}")
        return 0
    if args.check:
        if not OUTPUT_PATH.exists() or OUTPUT_PATH.read_text(encoding="utf-8") != text:
            print("Entry extraction differs from entry-records.json", file=sys.stderr)
            return 1
        print("Entry extraction matches entry-records.json")
        return 0
    OUTPUT_PATH.write_text(text, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    print(json.dumps(payload["statistics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
