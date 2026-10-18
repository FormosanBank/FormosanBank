#!/usr/bin/env python3
"""Extract the authorized texts and dictionary examples from the locked PDF."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import fitz

try:
    from CodeAndDocs.pdf_text import (
        Row,
        Span,
        append_wrapped,
        join_spans,
        learn_hyphenation_from,
        page_rows,
    )
except ModuleNotFoundError:
    from pdf_text import (Row, Span, append_wrapped, join_spans,
                          learn_hyphenation_from, page_rows)


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "CodeAndDocs" / "source-lock.json"
# The published filename lives in the lock, so renaming the source is a one-line
# change there rather than an edit in every script (it was hardcoded here).
SOURCE_PATH = ROOT / "Private" / json.loads(
    LOCK_PATH.read_text(encoding="utf-8")
)["pdf_filename"]
OUTPUT_PATH = ROOT / "CodeAndDocs" / "extracted-records.json"


@dataclass(frozen=True)
class TextSpec:
    number: int
    title: str
    source_pages: tuple[int, ...]
    translation_pages: tuple[int, ...]


TEXT_SPECS = (
    TextSpec(1, "The Festival of the Swings", (256,), (257,)),
    TextSpec(
        2,
        "The Monkeys Who Were Sawing Wood",
        tuple(range(258, 263)),
        (262, 263, 264),
    ),
    TextSpec(3, "The Thao New Year Celebration", (265,), (265,)),
    TextSpec(4, "The Little People and the Lake", (266, 267), (267, 268)),
    TextSpec(5, "The White Deer", tuple(range(269, 281)), tuple(range(280, 285))),
)
DICTIONARY_PAGES = range(290, 1079)
SOURCE_FONTS = {"T5", "T6"}
TRANSLATION_FONT = "T4"
SUBENTRY_FONT = "T9"
# Every font the dictionary body uses in a role this extractor reads.
KNOWN_FONTS = SOURCE_FONTS | {TRANSLATION_FONT, SUBENTRY_FONT, "T2", "T7", "T8",
                              "T10", "T11", "T12"}
# How far past a column's left margin a run has to start before it reads as a
# separately indented note rather than a continuation. Was two hardcoded
# absolute thresholds (130.0 and 323.0).
NOTE_INDENT = 18.0
# Slack on the body indent, absorbing the sub-point of jitter between rows.
BODY_TOLERANCE = 2.0

# Type3 extraction drops the printed A immediately after an opening quotation
# mark at these three positions. The aligned gloss and rendered page both show
# the missing source word as A. Indices are zero-based within the sentence.
TEXT_WORD_REPAIRS = {
    (5, 66, 4): ("`", "`FUT", "`A"),
    (5, 69, 3): ("`", "`FUT", "`A"),
    (5, 95, 15): ("`", "`A", "`A"),
}


# Printed p. 291 (PDF p. 301) is the one page of the dictionary typeset in a
# different family - Book Antiqua with Courier hyphens, not the Type 3 faces the
# rest of the book uses. Every classification here is by font name, so without
# this map the page is invisible: no example on it is extracted, and the record
# open when the page begins survives across it and absorbs the first translation
# on the page after. The roles line up one for one.
#
#   bold italic  headword repeated inside an example  -> T5
#   italic       the Thao example                     -> T6
#   plain        English, and definitions             -> T4
#   bold         sub-entry headword                   -> T9
#
# Courier appears only as the hyphen glyph. Its spans become the en dash the
# rest of the book prints for a morpheme boundary, so append_wrapped does not
# mistake a line-final morpheme hyphen for print hyphenation.
FONT_ALIASES = {
    "BookAntiqua-BoldItalic": "T5",
    "CourierNewPS-BoldItalicM": "T5",
    "BookAntiqua-Italic": "T6",
    "CourierNewPS-ItalicMT": "T6",
    "BookAntiqua": TRANSLATION_FONT,
    "BookAntiqua-Bold": SUBENTRY_FONT,
    "CourierNewPS-BoldMT": SUBENTRY_FONT,
}
COURIER_HYPHEN = "\u2013"


def normalized_rows(document: fitz.Document, pdf_page: int) -> list[Row]:
    """Page rows with any aliased font mapped onto the role it plays."""
    rows = page_rows(document[pdf_page - 1])
    if not any(span.font in FONT_ALIASES for row in rows for span in row.spans):
        return rows
    return [
        Row(
            y0=row.y0,
            spans=tuple(
                Span(
                    x0=span.x0,
                    x1=span.x1,
                    y0=span.y0,
                    text=(
                        COURIER_HYPHEN
                        if span.font.startswith("CourierNew")
                        and span.text.strip() == "-"
                        else span.text
                    ),
                    font=FONT_ALIASES[span.font],
                )
                if span.font in FONT_ALIASES
                else span
                for span in row.spans
            ),
        )
        for row in rows
    ]


def source_sha256() -> str:
    digest = hashlib.sha256()
    with SOURCE_PATH.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_source(document: fitz.Document) -> dict[str, Any]:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if SOURCE_PATH.stat().st_size != lock["pdf_bytes"]:
        raise ValueError("source byte count differs from source-lock.json")
    if source_sha256() != lock["pdf_sha256"]:
        raise ValueError("source SHA-256 differs from source-lock.json")
    if document.page_count != lock["pdf_pages"]:
        raise ValueError("source page count differs from source-lock.json")
    return lock


def _row_text(row: Row, fonts: set[str] | None = None) -> str:
    spans = [span for span in row.spans if fonts is None or span.font in fonts]
    return join_spans(spans)


def _translation_heading(row: Row, title: str) -> bool:
    normalized = re.sub(r"[^A-Z ]", "", _row_text(row).upper())
    expected = re.sub(r"[^A-Z ]", "", title.upper())
    return normalized.strip() == expected.strip()


def _body_rows(document: fitz.Document, pdf_page: int) -> list[Row]:
    return [
        row
        for row in page_rows(document[pdf_page - 1])
        if 100.0 < row.y0 < 685.0
    ]


def _numeric_markers(row: Row) -> list[Span]:
    return [
        span
        for span in row.spans
        if span.font == "T12" and span.text.strip().isdigit()
    ]


def _tokenize_source_row(row: Row) -> tuple[list[dict[str, Any]], list[Span]]:
    markers = _numeric_markers(row)
    content = [span for span in row.spans if span.font == "T11"]
    groups: list[list[Span]] = []
    for span in sorted(content, key=lambda item: item.x0):
        if groups and span.x0 - max(item.x1 for item in groups[-1]) <= 2.2:
            groups[-1].append(span)
        else:
            groups.append([span])
    tokens = [
        {
            "x0": min(span.x0 for span in group),
            "x1": max(span.x1 for span in group),
            "form": join_spans(group),
        }
        for group in groups
    ]
    return tokens, markers


GLOSS_FONTS = {"T3", "T11", "T10"}
FOOTNOTE_MARKER_FONT = "T9"


def _footnote_markers(gloss_row: Row) -> list[Span]:
    """Superscript digits in the gloss line: raised, bare-numeric, marker font."""
    if not gloss_row.spans:
        return []
    baseline = max(
        (span.y0 for span in gloss_row.spans if span.font in GLOSS_FONTS),
        default=None,
    )
    if baseline is None:
        return []
    return [
        span
        for span in gloss_row.spans
        if span.font == FOOTNOTE_MARKER_FONT
        and span.text.strip().isdigit()
        and span.y0 < baseline - 1.0
    ]


def _aligned_glosses(
    gloss_row: Row, tokens: list[dict[str, Any]]
) -> list[str]:
    """Assign complete printed gloss groups to aligned source words.

    T10 is the italic face Blust uses in a gloss line for a Thao word he leaves
    untranslated (`funfun`) and for Latin binomials. Excluding it used to drop
    the gloss and leave the stranded punctuation behind as the word's gloss.
    T9 in this row is the raised footnote marker, and is deliberately not a
    gloss - see _footnote_markers.
    """
    spans = sorted(
        (span for span in gloss_row.spans if span.font in GLOSS_FONTS),
        key=lambda item: item.x0,
    )
    groups: list[list[Span]] = []
    for span in spans:
        if groups and span.x0 - max(item.x1 for item in groups[-1]) <= 2.2:
            groups[-1].append(span)
        else:
            groups.append([span])

    assigned: list[list[list[Span]]] = [[] for _ in tokens]
    for group in groups:
        group_x0 = min(span.x0 for span in group)
        token_index = min(
            range(len(tokens)),
            key=lambda index: abs(tokens[index]["x0"] - group_x0),
        )
        assigned[token_index].append(group)
    return [
        " ".join(join_spans(group) for group in token_groups)
        for token_groups in assigned
    ]


def extract_text_source(
    document: fitz.Document, spec: TextSpec
) -> dict[int, dict[str, Any]]:
    sentences: dict[int, dict[str, Any]] = {}
    current_number: int | None = None
    started = False

    for pdf_page in spec.source_pages:
        rows = _body_rows(document, pdf_page)
        stop = next(
            (
                index
                for index, row in enumerate(rows)
                if _translation_heading(row, spec.title)
            ),
            len(rows),
        )
        rows = rows[:stop]
        if not started:
            start = next(
                index for index, row in enumerate(rows) if _numeric_markers(row)
            )
            rows = rows[start:]
            started = True
        rows = [
            row
            for row in rows
            if any(span.font in {"T3", "T11", "T12"} for span in row.spans)
        ]
        if len(rows) % 2:
            raise ValueError(
                f"text {spec.number}, PDF page {pdf_page}: "
                f"odd interlinear row count {len(rows)}"
            )
        for row_index in range(0, len(rows), 2):
            source_row, gloss_row = rows[row_index : row_index + 2]
            tokens, markers = _tokenize_source_row(source_row)
            glosses = _aligned_glosses(gloss_row, tokens)
            notes = _footnote_markers(gloss_row)
            marker_index = 0
            for token_index, token in enumerate(tokens):
                while (
                    marker_index < len(markers)
                    and markers[marker_index].x0 < token["x0"]
                ):
                    current_number = int(markers[marker_index].text)
                    sentences.setdefault(
                        current_number,
                        {
                            "number": current_number,
                            "source_pdf_pages": [],
                            "words": [],
                        },
                    )
                    marker_index += 1
                if current_number is None:
                    raise ValueError(
                        f"text {spec.number}, PDF page {pdf_page}: "
                        "word precedes first sentence number"
                    )
                record = sentences[current_number]
                if pdf_page not in record["source_pdf_pages"]:
                    record["source_pdf_pages"].append(pdf_page)
                word = {
                    "form": token["form"],
                    "gloss": glosses[token_index] or None,
                }
                # A marker sits immediately to the RIGHT of the gloss it
                # marks, so it belongs to the last token that starts at or
                # before it - not to the nearest one, which is the next word.
                for note in notes:
                    owners = [
                        index
                        for index, item in enumerate(tokens)
                        if item["x0"] <= note.x0
                    ]
                    if owners and owners[-1] == token_index:
                        word["footnote"] = int(note.text.strip())
                record["words"].append(word)
    return sentences


def _page_footnotes(document: fitz.Document, pdf_page: int) -> dict[int, str]:
    """Numbered footnotes printed under the interlinear body of a text page.

    The marker is raised far enough that row clustering sometimes puts it in a
    row of its own (text 4, PDF p. 266), so a lone marker takes the following
    row as its body.
    """
    rows = [
        row
        for row in page_rows(document[pdf_page - 1])
        if 100.0 < row.y0 < 685.0
        and row.spans
        and {span.font for span in row.spans} <= {"T8", "T9", "T10"}
    ]
    result: dict[int, str] = {}
    for index, row in enumerate(rows):
        ordered = sorted(row.spans, key=lambda span: span.x0)
        first = ordered[0]
        if first.font != FOOTNOTE_MARKER_FONT or not first.text.strip().isdigit():
            continue
        body = join_spans(ordered[1:])
        if not body and index + 1 < len(rows):
            body = join_spans(rows[index + 1].spans)
        if body:
            result[int(first.text.strip())] = body
    return result


def _translation_rows(
    document: fitz.Document, spec: TextSpec
) -> list[tuple[int, Row]]:
    result: list[tuple[int, Row]] = []
    active = False
    for pdf_page in spec.translation_pages:
        rows = _body_rows(document, pdf_page)
        heading = next(
            (
                index
                for index, row in enumerate(rows)
                if _translation_heading(row, spec.title)
            ),
            None,
        )
        if heading is not None:
            active = True
            rows = rows[heading + 1 :]
        elif not active:
            active = True
        result.extend((pdf_page, row) for row in rows)
    return result


def extract_text_translations(
    document: fitz.Document, spec: TextSpec
) -> dict[int, dict[str, Any]]:
    translations: dict[int, dict[str, Any]] = {}
    current_number: int | None = None
    for pdf_page, row in _translation_rows(document, spec):
        spans = [span for span in row.spans if span.font in {"T11", "T12"}]
        if not spans:
            continue
        pieces: list[tuple[str, str]] = []
        current_spans: list[Span] = []
        for span in sorted(spans, key=lambda item: item.x0):
            if span.font == "T12" and span.text.strip().isdigit():
                if current_spans:
                    pieces.append(("text", join_spans(current_spans)))
                    current_spans = []
                pieces.append(("number", span.text.strip()))
            else:
                current_spans.append(span)
        if current_spans:
            pieces.append(("text", join_spans(current_spans)))

        for kind, value in pieces:
            if kind == "number":
                current_number = int(value)
                translations.setdefault(
                    current_number,
                    {"translation": "", "translation_pdf_pages": []},
                )
                continue
            if current_number is None:
                continue
            record = translations[current_number]
            record["translation"] = append_wrapped(record["translation"], value)
            if pdf_page not in record["translation_pdf_pages"]:
                record["translation_pdf_pages"].append(pdf_page)
    return translations


def extract_text(document: fitz.Document, spec: TextSpec) -> dict[str, Any]:
    source = extract_text_source(document, spec)
    footnotes: dict[int, dict[int, str]] = {
        page: _page_footnotes(document, page) for page in spec.source_pages
    }
    translations = extract_text_translations(document, spec)
    if set(source) != set(translations):
        raise ValueError(
            f"text {spec.number}: source numbers {sorted(source)} differ from "
            f"translation numbers {sorted(translations)}"
        )
    numbers = sorted(source)
    if numbers != list(range(1, numbers[-1] + 1)):
        raise ValueError(f"text {spec.number}: non-contiguous sentence numbers")
    sentences = []
    for number in numbers:
        record = source[number]
        record.update(translations[number])
        for (text_number, sentence_number, word_index), (
            expected_form,
            expected_gloss,
            replacement,
        ) in TEXT_WORD_REPAIRS.items():
            if text_number != spec.number or sentence_number != number:
                continue
            word = record["words"][word_index]
            if word != {"form": expected_form, "gloss": expected_gloss}:
                raise ValueError(
                    f"unexpected input for text repair {(text_number, number, word_index)}: "
                    f"{word!r}"
                )
            word["form"] = replacement
        for word in record["words"]:
            marker = word.pop("footnote", None)
            if marker is None:
                continue
            for page in record["source_pdf_pages"]:
                body = footnotes.get(page, {}).get(marker)
                if body:
                    word["note"] = body
                    break
            else:
                raise ValueError(
                    f"text {spec.number}: footnote {marker} has no body on "
                    f"pages {record['source_pdf_pages']}"
                )
        record["form"] = " ".join(word["form"] for word in record["words"])
        sentences.append(record)
    return {
        "number": spec.number,
        "title": spec.title,
        "source_pdf_pages": list(spec.source_pages),
        "translation_pdf_pages": list(spec.translation_pages),
        "sentences": sentences,
    }


def _dictionary_runs(row: Row, column: int) -> list[tuple[str, str, float]]:
    if column == 0:
        spans = [span for span in row.spans if span.x0 < 300]
    else:
        spans = [span for span in row.spans if span.x0 >= 300]
    categorized: list[tuple[str, Span]] = []
    has_translation = any(span.font == TRANSLATION_FONT for span in spans)
    has_entry_fields = any(span.font in {"T9", "T11"} for span in spans)
    # A row set entirely in the definition face, with no example-translation
    # face, no Thao, and no entry apparatus of any kind. Printed p. 835 sets a
    # whole example translation that way ("I never see the dog"), and it is the
    # only row in the dictionary that does; a definition continuation has the
    # same shape but is only ever reached after finish() has closed the entry,
    # so no example is open to absorb it.
    definition_face_only = not (
        has_translation
        or has_entry_fields
        or any(
            span.font in SOURCE_FONTS | {"T2", "T8", "T10", "T12"} for span in spans
        )
    )
    for span in spans:
        if span.font in SOURCE_FONTS:
            categorized.append(("source", span))
        elif span.font in {TRANSLATION_FONT, "T2"}:
            categorized.append(("translation", span))
        elif span.font == "T7" and has_translation and not has_entry_fields:
            # One printed example (p. 280) changes font after the first word
            # of its translation. Entry definitions also use T7, so admit it
            # only when no entry-number or headword fields share the column.
            categorized.append(("translation", span))
        elif span.font == "T7" and definition_face_only:
            # Tagged, not classified: whether this is an example's translation
            # or a definition continuing over a line depends on whether an
            # example is waiting for its translation, which only the caller
            # knows. See extract_dictionary.
            categorized.append(("definition", span))
    runs: list[tuple[str, str, float]] = []
    current_kind: str | None = None
    current_spans: list[Span] = []
    for kind, span in categorized:
        if current_kind is not None and kind != current_kind:
            runs.append(
                (
                    current_kind,
                    join_spans(current_spans, gap=1.2),
                    min(item.x0 for item in current_spans),
                )
            )
            current_spans = []
        current_kind = kind
        current_spans.append(span)
    if current_kind is not None:
        runs.append(
            (
                current_kind,
                join_spans(current_spans, gap=1.2),
                min(item.x0 for item in current_spans),
            )
        )
    runs = [(kind, value, x0) for kind, value, x0 in runs if value]

    # Thao plant and cultural terms are occasionally set in italics inside an
    # English translation. A source-font run bracketed by translation-font
    # runs on the same visual row is part of that translation, not a new
    # example sentence.
    normalized: list[tuple[str, str, float]] = []
    translation_started = False
    for kind, value, x0 in runs:
        if (
            kind == "source"
            and translation_started
        ):
            kind = "translation"
        if kind == "translation":
            translation_started = True
        if normalized and normalized[-1][0] == kind:
            normalized[-1] = (
                kind,
                append_wrapped(normalized[-1][1], value),
                normalized[-1][2],
            )
        else:
            normalized.append((kind, value, x0))
    return normalized


def extract_dictionary(document: fitz.Document) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    active: dict[str, Any] | None = None
    per_page_counts: defaultdict[int, int] = defaultdict(int)

    discards: list[dict[str, Any]] = []

    def finish() -> None:
        nonlocal active
        if active and active["source"] and not active["translation"]:
            # A printed Thao run with no English beside it. Usually a headword
            # continuation or a fragment of an entry definition, but it is the
            # one place an example can leave the corpus without a trace, so it
            # is logged rather than dropped silently.
            discards.append(
                {
                    "reason": "source without translation",
                    "source_printed_page": active["source_printed_page"],
                    "source_pdf_page": active["source_pdf_page"],
                    "text": active["source"],
                }
            )
        if active and active["source"] and active["translation"]:
            if active["source"].endswith(" (itia") and active[
                "translation"
            ].startswith("may also precede p–in–a–kacu) "):
                active["source"] = active["source"][: -len(" (itia")]
                active["source_note"] = (
                    "(itia may also precede p–in–a–kacu)"
                )
                active["translation"] = active["translation"][
                    len("may also precede p–in–a–kacu) ") :
                ]
            source_note = re.search(
                r"\s+(\(alternatively /tilha/ may precede the rest\))$",
                active["source"],
            )
            if source_note:
                active["source"] = active["source"][: source_note.start()]
                active["source_note"] = source_note.group(1)
            active["translation"] = re.sub(
                r"\s*—\s*", "—", active["translation"]
            )
            # A printed "(recorded ...)" parenthetical is Blust's note about
            # how the Thao was transcribed, not part of the English. It leaves
            # the translation and is kept beside the form, like the two
            # placement notes above.
            trimmed = re.split(
                r"\s+(\(recorded\b.*)$",
                active["translation"],
                maxsplit=1,
                flags=re.IGNORECASE,
            )
            if len(trimmed) > 1:
                note = trimmed[1].strip()
                active["source_note"] = (
                    f"{active['source_note']} {note}"
                    if active.get("source_note")
                    else note
                )
            active["translation"] = trimmed[0]
            page = active["source_printed_page"]
            per_page_counts[page] += 1
            active["id"] = (
                f"blust-dict-p{page:04d}-e{per_page_counts[page]:03d}"
            )
            records.append(active)
        active = None

    for pdf_page in DICTIONARY_PAGES:
        rows = [
            row
            for row in normalized_rows(document, pdf_page)
            if 95.0 < row.y0 < 680.0
        ]
        # A dictionary page the font map cannot read is not an empty page, it
        # is a page nothing on it can be extracted from - and the record open
        # when it starts will cross it and pick up text from the page after.
        # Printed p. 291 was exactly that for as long as it went unnoticed.
        spans = [span for row in rows for span in row.spans]
        margins = {
            col: min(
                (
                    span.x0
                    for span in spans
                    if (span.x0 < 300) == (col == 0)
                ),
                default=112.0 if col == 0 else 306.0,
            )
            for col in (0, 1)
        }
        # Where the body text of each column starts, as opposed to the hanging
        # sense numbers to its left. A Thao run at that indent begins a new
        # example; one further right continues the translation above it.
        body = {
            col: min(
                (
                    span.x0
                    for span in spans
                    if (span.x0 < 300) == (col == 0)
                    and span.font in SOURCE_FONTS
                ),
                default=margins[col] + 2.0,
            )
            for col in (0, 1)
        }
        if spans and not any(span.font in KNOWN_FONTS for span in spans):
            raise ValueError(
                f"PDF page {pdf_page} (printed {pdf_page - 10}) carries text in "
                f"{sorted({span.font for span in spans})} and no font this "
                "extractor recognizes; see FONT_ALIASES"
            )
        for column in (0, 1):
            for row in rows:
                column_spans = [
                    span
                    for span in row.spans
                    if (span.x0 < 300) == (column == 0)
                ]
                structural_row = (
                    any(span.font in {"T8", "T9"} for span in column_spans)
                    and not any(span.font in SOURCE_FONTS for span in column_spans)
                ) or any(
                    span.font == "T11" and span.text.strip().upper() == "NOTE:"
                    for span in column_spans
                )
                if structural_row:
                    finish()
                    continue
                runs = _dictionary_runs(row, column)
                if not runs:
                    continue
                has_source = any(kind == "source" for kind, _, _ in runs)
                for kind, value, x0 in runs:
                    if kind == "source":
                        if active and active["translation"]:
                            # Measured per page for the same reason as
                            # NOTE_INDENT: printed p. 291 sets its columns
                            # ~15pt right of every other page, so a fixed
                            # threshold read every new example on it as more of
                            # the previous translation.
                            continuation_x = body[column] + BODY_TOLERANCE
                            if x0 > continuation_x:
                                active["translation"] = append_wrapped(
                                    active["translation"], value
                                )
                                continue
                            finish()
                        if active is None:
                            active = {
                                "source_pdf_page": pdf_page,
                                "source_printed_page": pdf_page - 10,
                                "source": "",
                                "translation": "",
                            }
                        active["source"] = append_wrapped(active["source"], value)
                    elif kind == "definition":
                        # A definition-face row counts as an example's
                        # translation only when an example is open and still
                        # has none: printed p. 835 sets one that way. Once a
                        # translation has started, the same shape is a
                        # definition continuing over a line and is not ours.
                        if active is not None and not active["translation"]:
                            active["translation"] = append_wrapped(
                                active["translation"], value
                            )
                    elif active is not None:
                        # A run indented past the column's own left margin is a
                        # separately indented note, not a continuation. The
                        # margin is measured per page rather than hardcoded:
                        # printed p. 291 sets its columns ~15pt to the right of
                        # every other page, which put its whole right column
                        # past a fixed threshold and cut every translation on it
                        # short.
                        note_x = margins[column] + NOTE_INDENT
                        if not has_source and x0 > note_x:
                            finish()
                            continue
                        active["translation"] = append_wrapped(
                            active["translation"], value
                        )
    finish()
    return records, discards


def payload() -> dict[str, Any]:
    document = fitz.open(SOURCE_PATH)
    lock = validate_source(document)
    learn_hyphenation_from(document, DICTIONARY_PAGES)
    texts = [extract_text(document, spec) for spec in TEXT_SPECS]
    examples, discards = extract_dictionary(document)
    text_sentence_count = sum(len(text["sentences"]) for text in texts)
    word_count = sum(
        len(sentence["words"])
        for text in texts
        for sentence in text["sentences"]
    )
    return {
        "source_pdf_sha256": lock["pdf_sha256"],
        "extractor": f"PyMuPDF {fitz.VersionBind}",
        "decoding": {
            "0x0b": "ff ligature",
            "0x0c": "fi ligature",
            "0x0f": "ffl ligature",
            "0x10": "dotless i under accent",
            "0x12": "theta",
            "0x13": "acute accent applied to following vowel",
            "left_brace": "source en dash",
            "vertical_bar": "source em dash",
            "backslash": "opening double quotation mark",
            "double_quote": "closing double quotation mark",
        },
        "scope": lock["scope"],
        "discards": discards,
        "texts": texts,
        "dictionary_examples": examples,
        "statistics": {
            "texts": len(texts),
            "text_sentences": text_sentence_count,
            "interlinear_words": word_count,
            "dictionary_examples": len(examples),
            "discarded_runs": len(discards),
            "total_sentences": text_sentence_count + len(examples),
        },
    }


def serialized(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="compare extraction with committed data"
    )
    args = parser.parse_args()
    current = serialized(payload())
    if args.check:
        if not OUTPUT_PATH.exists():
            print(f"Missing extraction: {OUTPUT_PATH}", file=sys.stderr)
            return 1
        if OUTPUT_PATH.read_text(encoding="utf-8") != current:
            print("Extraction differs from extracted-records.json", file=sys.stderr)
            return 1
        print("Extraction matches extracted-records.json")
        return 0
    OUTPUT_PATH.write_text(current, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")
    print(json.dumps(json.loads(current)["statistics"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
