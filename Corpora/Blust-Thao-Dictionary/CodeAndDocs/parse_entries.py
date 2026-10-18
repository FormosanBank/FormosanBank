#!/usr/bin/env python3
"""Parse the dictionary into one JSON record per entry, against a declared schema.

This is the other half of extract_source.py. That script streams the pages and
accumulates example sentences, never asking whether what it read was a
well-formed entry; every failure it had was therefore silent. This one parses
against a shape, so an entry that does not fit says so.

Two formats, one JSON shape (maintainer, 2026-09-10):

    A   the headword is a free word. It carries its own definition, printed
        unnumbered right after the etymology - that definition IS sense 1 -
        and its derived forms follow as senses 2, 3, 4 ...

            fatu (PAN *batu `stone; testicle')
            stone; testicle
            nak a fatu  my testicles
            2 fatu a shapa  scrotum

    B   the headword is a BOUND ROOT, which is what the bars and the trailing
        colon mark. It has no definition of its own, so numbering starts at 2
        with the first derived form.

            |ailhi| (PAN *wiRi `left side'):
            2 tana-ailhi  left side
              ihu i-sahay nak a tana-ailhi mi-lhugqu  You are sitting ...

`format` is the only structural difference; everything else is a validation
profile. See validate_entries.py.

This covers the dictionary only. The five interlinear texts are a different
structure and are extract_source.py's business.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract_source import (  # noqa: E402
    DICTIONARY_PAGES,
    SOURCE_FONTS,
    SOURCE_PATH,
    normalized_rows,
)
from pdf_text import (  # noqa: E402
    append_wrapped,
    join_spans,
    learn_hyphenation_from,
)
from extract_source import Row, Span  # noqa: E402

COLUMN_SPLIT = 300.0
BODY_GAP = 1.2
ROW_TOLERANCE = 3.1
#: How far below a line's own baseline Blust sets its subscripts, bars,
#: colons, sense numbers and bracketed labels. See Parser._column_lines.
LINE_TOLERANCE = 7.5

HEADWORD_FONT = "T8"
# Inside an example the word being exemplified is set bold-italic and the rest
# italic. An example with no bold portion is not illustrating anything, which is
# a red flag on the parse rather than on the book (maintainer, 2026-09-10).
EXEMPLIFIED_FONT = "T5"
SUBENTRY_FONT = "T9"
LABEL_FONT = "T11"
DEFINITION_FONTS = {"T7", "T2"}
TRANSLATION_FONT = "T4"
ITALIC_FONT = "T10"
XREF_FONTS = {"Century", "PMingLiU"}
# A numbered sub-entry puts the NUMBER at the column margin and indents its
# form about nine points past it. An index entry puts the form itself at the
# margin. Two points of slack separates them.
SUBENTRY_MARGIN = 2.0
# An example opens a little past the column margin; a wrapped body line is
# indented further still. The two distances are NOT the same on every page -
# printed p. 291, the one page set in Book Antiqua, opens at +6.0 and wraps at
# +9.0 where the rest of the book uses +2.2 and +5.4 - so the dividing line is
# measured per page rather than fixed. A fixed 3.5 swallowed p.291's examples
# into the previous translation.
BODY_INDENT = 3.5          # fallback, for a page whose rows give no clear pair

BAR = "|"
# A free-standing acute, drawn over the vowel it belongs to.
# A standalone accent glyph drawn over the letter that follows it in join
# order: 0x13 is TeX's acute, `~` its tilde (0x7E in OT1).
ACCENT_OVERLAY = "\x13"
ACCENT_OVERLAYS = ("\x13", "~")
ARROW = "→"
# The re-typeset p. 291 draws the bar in Century as an em dash and the arrow in
# PMingLiU, so both glyphs have to be recognised by shape, not only by face.
BAR_GLYPHS = {"|", "—", "\u2013"}
SENSE_AT_MARGIN = re.compile(r"^(\d+)([a-z])?$")
# The etymology opens the entry and is set in the definition face. PyMuPDF
# splits "(PAN" across spans, so it is recognised on the rendered text rather
# than span by span.
# One bracket of nesting, because an etymology's glosses can carry their own:
# p.925 prints "(PAN *CekeS `a slender bamboo: Sinobambusa kunishii (Nakai)')".
# Stopping at the first ")" cut the etymology after `(Nakai)` and left the
# definition beginning "') the slenderest bamboo".
ETYMOLOGY = re.compile(
    r"^\((?:P(?:AN|MP|Ph|WMP|CEMP|EF)|Proto-)\b(?:[^()]|\([^()]*\))*\)\s*:?\s*"
)
LABEL = re.compile(r"^\[.*\]$")
# A grammatical label that reached the definition instead of the label slot.
# Blust sets the label in its own face, but a compound one - `[AFc; PFc]`,
# `[F; atemporal]`, `[C/IT/ PF]` - can arrive in the definition face instead,
# and on printed p.291, the page set in a different font family, even the simple
# ones do. It then reads as the opening of the gloss, and `clean_xml` turns the
# square brackets into round ones, so the published TRANSL began `(PF) by
# oneself` - "That's grammatical category, not a definition" (maintainer,
# 2026-09-11). 24 definitions in the book.
#
# Anchored, and required to open with a capital, so that `[= /qut/] fish bone`
# - an equivalence note, not a label - is left alone.
LEADING_LABEL = re.compile(r"^\[([A-Z][A-Za-z0-9;,/ ]*)\]\s*")

#: A definition has to say something. See Sense.render.
NOT_ONLY_PUNCTUATION = re.compile(r"[^\W_]")

#: A finished cross-reference names a sense: `ara1:3`, `|kulhmuz|:2`.
COMPLETE_XREF = re.compile(r":\s*\d+[a-e]?$")
NOTE_MARKER = re.compile(r"^NOTE\b", re.IGNORECASE)
# A sense number may carry a letter: afu has 1a, 1b, 1c before 2 and 3.
SENSE_NUMBER = re.compile(r"^(\d+)([a-z])?$")


def merge_accent_overlays(spans):
    """Fold a free-standing acute into the span it belongs to.

    Blust marks stress with an acute and PyMuPDF reports it as its own span,
    positioned just LEFT of the vowel it sits on. join_spans already handles
    that correctly by sorting the overlay 0.5pt earlier, so the reassembled
    line reads `maní`. The parser never gets that far: it routes spans to
    fields one at a time, and a lone overlay - whose x-range overlaps its
    neighbour's - defeats the adjacency test that continues a headword. The
    headword closed early and the accent landed in the definition. 139 fields
    lost it and 59 headwords were truncated at it.

    So the overlay is merged here, before any routing, by prepending it to the
    span join_spans would place it before. That is the same rule, applied one
    step earlier, and it reproduces join_spans exactly:

        Alis  |13| an        -> Alis  |13|an     -> Alisán
        Matans un   |13|     -> Matans |13|un    -> Matansún
        man   |13| dotless-i -> man   |13|(i)    -> maní

    An earlier version inserted the overlay INSIDE the covering span at the
    character its x0 landed on. That put 75 accents one letter to the left
    (`máni` for the printed `maní`) - caught only by diffing against the
    example sentences Hunter's build produces, where join_spans had it right
    all along.
    """
    if not any(s.text in ACCENT_OVERLAYS for s in spans):
        return spans
    order = sorted(
        range(len(spans)),
        key=lambda i: spans[i].x0 - 0.5
        if spans[i].text in ACCENT_OVERLAYS
        else spans[i].x0,
    )
    text = {i: spans[i].text for i in range(len(spans))}
    dropped = set()
    for position, index in enumerate(order):
        if spans[index].text not in ACCENT_OVERLAYS:
            continue
        following = next(
            (order[k] for k in range(position + 1, len(order))
             if order[k] not in dropped and spans[order[k]].text.strip()),
            None,
        )
        if following is None:
            continue
        text[following] = spans[index].text + text[following]
        dropped.add(index)
    return [
        spans[i] if text[i] == spans[i].text
        else Span(x0=spans[i].x0, x1=spans[i].x1, y0=spans[i].y0,
                  text=text[i], font=spans[i].font)
        for i in range(len(spans))
        if i not in dropped
    ]


# The Linnean authority in a botanical name - "Musa sapientum (Linn.)",
# "Imperata cylindrica (L.) Beauv." - is a classification credit, not a note
# about the Thao. It goes, and does not become a @note (maintainer,
# 2026-09-10). Two definitions in the book carry one.
LINNEAN = re.compile(r"\s*\((?:Linn\.|L\.)\)")


def _render(spans) -> str:
    """Join spans that may span several printed lines, in reading order."""
    if not spans:
        return ""
    lines: list[list] = []
    for span in spans:
        # LINE_TOLERANCE, not ROW_TOLERANCE: a subscript is part of the line it
        # hangs off, so `ara` + `1` + `:` + `2` must render `ara1:2`, not
        # `ara 1:2` with the subscript treated as a wrapped line of its own.
        if lines and abs(lines[-1][0].y0 - span.y0) <= LINE_TOLERANCE:
            lines[-1].append(span)
        else:
            lines.append([span])
    text = ""
    for line in lines:
        text = append_wrapped(text, join_spans(line, gap=BODY_GAP))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:?!)])", r"\1", text)
    return re.sub(r"\(\s+", "(", text)


#: How many consecutive unnumbered sub-entries can be read as the book leaving
#: a number off. Beyond this, a run of unnumbered senses is not a printing slip
#: but a missed entry boundary - klhiw absorbed 148 of them - and inferring
#: numbers there would bury the defect instead of showing it (S09).
MAX_INFERRED_RUN = 3


def _number_the_gaps(senses: list) -> None:
    """Give a sub-entry the number the book left off.

    Blust numbers derived forms 2, 3, 4 ... and occasionally omits one:
    ana-faw and ana-i print no number where 4 and 5 belong. The number is
    recoverable from position, so the record carries it - marked `inferred`,
    because it is our reading and not the page's.
    """
    printed = {s["number"] for s in senses if s["number"] is not None}
    last = None
    run = []
    for sense in senses:
        if sense["number"] is not None:
            last = sense["number"]
            run = []
            continue
        if last is None or sense["form"] is None:
            continue
        run.append(sense)
        if len(run) > MAX_INFERRED_RUN:
            for member in run:
                member["number"] = None
                member["number_inferred"] = False
            continue
        # Never invent a number the page already prints somewhere in this
        # entry: that would be two senses called 3, which is a worse record
        # than one sense with no number.
        if last + 1 in printed:
            run = []
            continue
        last += 1
        printed.add(last)
        sense["number"] = last
        sense["number_inferred"] = True


#: Blust sometimes answers a question inside a parenthetical and sets the
#: question in Thao with its gloss beside it:
#:
#:   I just sowed the rice (answer to Shi-ntua ihu? Where did you go?)
#:
#: That is a Thao sentence with a translation, sitting inside a note. The Thao
#: is recognisable because it arrives in the Thao font, so the pair is recorded
#: at parse time rather than guessed from the rendered string. A single cited
#: term - falhán, lina - is not a sentence and is left alone.
#: Blust occasionally prints an English remark about the wording INSIDE the
#: Thao run, where it is not Thao at all. extract_source.py lifts the same ones
#: out of the example sentences it publishes (the maintainer sanctioned keeping
#: Hunter's three, 2026-09-11); this does it for the entry apparatus. The list
#: is explicit rather than inferred, and language_check.py is what will catch a
#: future one - the `v` of "alternatively" is a letter Thao does not have.
_NO_MATCH = re.compile(r"(?!x)x").match("") or re.match(r"()", "")

SOURCE_NOTES = re.compile(
    r"""\s*\(
        (?: alternatively\ /\w+/\ may\ precede\ the\ rest
          | itia\ may\ also\ precede\ [^)]*
        )
    \)\s*$""",
    re.IGNORECASE | re.VERBOSE,
)


ANSWER = re.compile(r"\(\s*(?:answer|reply)\b[^()]*\)", re.IGNORECASE)


#: An English remark about the wording, opened in the Thao and closed in the
#: English, so neither side holds a whole parenthetical:
#:
#:   itia shau-na-nay yakin (itia    | may also precede p-in-a-kacu) I have ...
#:
#: extract_source.py patches this one by name; recognising the SHAPE catches it
#: and anything like it (maintainer, 2026-09-11).
STRADDLE = re.compile(r"\s*\([^()]*$")


def _straddling(thao: str, english: str) -> tuple[str, str, str | None]:
    """Lift a parenthetical that opens in the Thao and closes in the English."""
    note = SOURCE_NOTES.search(thao)
    if note:
        return SOURCE_NOTES.sub("", thao).strip(), english, note.group(0).strip().strip("()")
    opened = STRADDLE.search(thao)
    if opened and ")" in english:
        head, _, tail = english.partition(")")
        return (
            thao[: opened.start()].strip(),
            tail.strip(),
            f"{opened.group(0).strip().lstrip('(')} {head}".strip(),
        )
    return thao, english, None


def _quoted_sentences(english: str, cited: list) -> list[dict]:
    """The Thao question inside an "answer to ..." parenthetical, with its gloss.

    Keyed on the parenthetical rather than on where the spans sit: the Thao
    often wraps across a printed line - `Shi-ntua` ends one and `ihu?` opens the
    next - so splitting the recorded spans geometrically cut the question into
    two one-word fragments and neither reached the two-word minimum.
    """
    if not cited or not english:
        return []
    out = []
    for match in ANSWER.finditer(english):
        inner = match.group()
        # The longest contiguous run of recorded spans whose joined text sits
        # inside this parenthetical. Span-by-span matching fails as soon as the
        # Thao is hyphenated across a line: p.876 records `i-` and `hu?`, and
        # neither appears in the rendered English, which reads `ihu?`.
        thao = ""
        for start in range(len(cited)):
            for stop in range(start + 1, len(cited) + 1):
                candidate = _render(cited[start:stop])
                # No early exit: an intermediate join can end on the printed
                # line-break hyphen (`shi-ntua i-`) and so fail to match, while
                # the next span completes it (`shi-ntua ihu?`) and does.
                if candidate and candidate in inner and len(candidate) > len(thao):
                    thao = candidate
        if len(thao.split()) < 2:
            continue
        tail = inner[inner.index(thao) + len(thao):].strip(" )")
        if tail:
            out.append({"thao": thao, "english": tail})
    return out


# "cf." introduces a comparison with another entry, which is the editor
# speaking, not part of the gloss. Blust writes it both ways - bracketed,
# `about, approximately (cf. /kaiza/)`, and appended after a comma,
# `left (side), cf. /tana/`. 8 definitions in the book carry one (maintainer,
# 2026-09-11: "In general, `cf.` introduces something that should be in a note").
CF_BRACKETED = re.compile(r"\s*\((cf\.\s[^()]*(?:\([^()]*\)[^()]*)*)\)")
CF_TRAILING = re.compile(r",\s*(cf\.\s.*)$")


def _lift_comparisons(definition: str) -> tuple[str, list[str]]:
    """Take any `cf. ...` out of a definition and hand it back as notes."""
    lifted: list[str] = []

    def take(match):
        lifted.append(match.group(1).strip())
        return ""

    text = CF_BRACKETED.sub(take, definition)
    text = CF_TRAILING.sub(take, text)
    return re.sub(r"\s+", " ", text).strip().rstrip(","), lifted


def _is_citation(example: dict) -> bool:
    """A Thao word standing in an English definition, not an example of use.

    An example sentence is never one word (maintainer, 2026-09-10): "The wood of
    the lina tree does not rot quickly" cites `lina` mid-definition, and the
    citation has no translation of its own because it is inside one.
    """
    return not example["english"] and len(example["thao"].split()) <= 1


@dataclass
class Sense:
    number: int | None = None
    subsense: str | None = None
    form: list = field(default_factory=list)
    label: str | None = None
    definition: list = field(default_factory=list)
    examples: list = field(default_factory=list)
    printed_page: int = 0
    notes: list = field(default_factory=list)
    cross_references: list = field(default_factory=list)

    def render(self, headword: str) -> dict:
        rendered = [
            {
                "thao": _straddling(_render(t), _render(e))[0],
                "source_note": _straddling(_render(t), _render(e))[2],
                "english": _straddling(_render(t), _render(e))[1],
                "exemplifies": _render([s for s in t if s.font == EXEMPLIFIED_FONT]),
                "quoted": _quoted_sentences(_render(e), cited),
                # The page this example is PRINTED on, which is not the page
                # its entry opened on: a long entry runs over several, and
                # 2,389 of 8,214 examples were inheriting the wrong one.
                "printed_page": page,
            }
            for t, e, cited, page in self.examples
            if _render(t) or _render(e)
        ]
        definition, comparisons = _lift_comparisons(
            LINNEAN.sub("", _render(self.definition))
        )
        label = self.label
        leading = LEADING_LABEL.match(definition)
        if leading:
            # A label at the head of the definition is the one printed
            # immediately after the form, so it wins over anything already in
            # the label slot. That happens once: p.375 sense 8 prints
            # `f-in-ariw [AFc; PFc] bought ...` with the label split across two
            # spans, and a stray `[PF]` from elsewhere on the page had taken the
            # slot.
            label = f"[{leading.group(1)}]"
            definition = definition[leading.end():]
        if definition and not NOT_ONLY_PUNCTUATION.search(definition):
            # "A definition will never consist of just a colon" (maintainer,
            # 2026-09-11, on p.1038 `undadan`). 9 senses reached the build with
            # a definition of `:` or `=` - all of them the tail of a cross-
            # reference or an equivalence the sense never had a gloss for.
            definition = ""
        return {
            "number": self.number,
            "number_inferred": False,
            "subsense": self.subsense,
            "printed_page": self.printed_page,
            "form": _render(self.form) or headword,
            "label": label,
            "definition": definition,
            "examples": [x for x in rendered if not _is_citation(x)],
            "citations": [x["thao"] for x in rendered if _is_citation(x)],
            "notes": comparisons + [n for n in (_render(s) for s in self.notes) if n],
            "cross_references": self.cross_references,
        }

    def empty(self) -> bool:
        return not (self.form or self.definition or self.examples or self.notes)


@dataclass
class Entry:
    fmt: str
    printed_page: int
    homograph: int | None = None
    headword: list = field(default_factory=list)
    etymology: list = field(default_factory=list)
    senses: list = field(default_factory=list)

    def render(self) -> dict:
        # An entry opened by a form at the margin has no bold headword of its
        # own; the form IS the headword.
        head = _render(self.headword)
        if not head and self.senses:
            head = _render(self.senses[0].form)
        senses = [s.render(head) for s in self.senses if not s.empty()]
        _number_the_gaps(senses)
        etymology = _render(self.etymology) or None
        if senses and etymology is None:
            match = ETYMOLOGY.match(senses[0]["definition"])
            if match:
                etymology = match.group().strip().strip(":").strip()
                senses[0]["definition"] = senses[0]["definition"][
                    match.end() :
                ].strip()
        # A bound root is not a word, so it carries no sense of its own. What
        # the printed colon leaves behind - once the etymology is lifted out -
        # is a sense whose definition is punctuation and nothing else. That goes.
        # A first sense with real content is a finding, not a sense.
        #
        # The bars are decoration, not the marker. Blust writes a bound root
        # three ways - |acay| (PAN *aCay):, kuza (PAN *kuja `how?'): and a bare
        # antua: - and the one thing all three share is a header that ends in a
        # colon and defines nothing. So the root test is that empty first sense,
        # whatever the header looked like (maintainer's question, 2026-09-10).
        # Nor is "numbering starts at 2" the marker: Matansun: runs 1a, 1b.
        fmt = self.fmt
        marker = "bars" if fmt == "B" else None
        bare = (
            senses
            and senses[0]["number"] is None
            and not re.search(r"\w", senses[0]["definition"])
        )
        # Roothood is decided the same way it always was - a first sense that
        # is empty but for the printed colon. Only an entry whose header was
        # ALREADY marked with bars may keep that sense when it carries an
        # example, because there the bars say it is a root and the example is
        # the book illustrating the root. Letting any definitionless first
        # sense make a colon-root promoted 8 format A entries by mistake.
        if bare and (fmt == "B" or not (senses[0]["examples"] or senses[0]["notes"])):
            # The colon defines nothing, so it goes - but the sense may still
            # carry the example the book prints directly under the header:
            #
            #     |puqnur|:
            #       cicu a punuq itia tusha wa puqnur  He has two bumps ...
            #     2 lhum-puqnur  swelling or bump ...
            #
            # Requiring the whole sense to be empty left that colon standing as
            # the definition, so the entry read as a bound root with a sense of
            # its own; and 10 example sentences in 8 entries were dropped from
            # the XML with it (maintainer, 2026-09-11).
            if senses[0]["examples"] or senses[0]["notes"]:
                senses[0]["definition"] = ""
            else:
                senses = senses[1:]
            if fmt != "B":
                fmt, marker = "B", "colon"
        return {
            "format": fmt,
            "root_marker": marker,
            "headword": head,
            "homograph": self.homograph,
            "printed_page": self.printed_page,
            "etymology": etymology,
            "senses": senses,
        }


class Parser:
    """One pass over the dictionary, emitting entries."""

    def __init__(self):
        self.entries: list[Entry] = []
        self.entry: Entry | None = None
        self.sense: Sense | None = None
        self.mode = "definition"      # definition | example | note
        self.awaiting_headword = False
        self.translation_on_this_row = False
        self.in_headword = False
        self.row_has_xref = False
        self.row_has_arrow = False
        self.xref_spans: list = []
        self.consumed = 0
        self.entries_opened_at_margin = 0
        self.body_indent = BODY_INDENT
        self.skipped: dict[str, int] = {}

    # -- helpers -------------------------------------------------------
    def _new_sense(self, number=None, subsense=None):
        self.sense = Sense(number=number, subsense=subsense)
        self.sense.printed_page = self.page
        if self.entry:
            self.entry.senses.append(self.sense)
        self.mode = "definition"

    def _form_broke_across_the_line(self):
        """True when the open sense's form ended the previous line hyphenated."""
        if self.sense is None or not self.sense.form:
            return False
        return self.sense.form[-1].text.rstrip().endswith(("-", "\u2013", "\u2014"))

    def _flush_xref(self, force: bool = False) -> bool:
        """One cross-reference per printed line, assembled whole.

        Returns True when the reference is hyphenated across the line break and
        must stay open for the next line.

        "-> |punuq|:2" arrives as an arrow, two bars, the target split across
        spans, a colon and a digit. Collected as they come and joined here, so
        the sense records `punuq:2` rather than three fragments - and the colon
        and digit stop landing on the end of the previous definition.
        """
        if not self.xref_spans:
            return False
        text = _render(self.xref_spans).strip()
        text = re.sub(r"^[\u2192|—\s]+|[\s]+$", "", text)
        # A cross-reference is `target:N`, so one that does not end in a sense
        # number is not finished and the rest is on the next line. Blust breaks
        # two of them: p.412 sets `->kahi-` then `wan:2`, and p.565 sets
        # `->|sia-` then `siaq|:2` - note that the closing bar lands on the
        # second line too, which is why holding the reference open matters for
        # more than the text (maintainer, 2026-09-11: "on the first line, we had
        # a cross reference to a bound form, but the closing `|` was not there.
        # Instead, it appeared on the 2nd line. Recommend writing a guard to
        # look for other such cases"). Exactly two in the book.
        if text and not force and not COMPLETE_XREF.search(text):
            return True
        if text:
            if self.sense is not None:
                self.sense.cross_references.append(text)
            else:
                # There is no sense to hang it on. That used to end here in
                # silence, and it is how 527 etymologies left the book without
                # a trace: `consumed` counts what feed() ACCEPTED, not what
                # survived into a record, so the 100% consumption figure could
                # not see it. Anything landing here is a defect - log it.
                self._skip("cross-reference with no sense", text)
        self.xref_spans = []
        return False

    def _close_entry(self):
        self._flush_xref(force=True)
        if self.entry and (self.entry.headword or self.entry.senses):
            self.entries.append(self.entry)
        self.entry = None
        self.sense = None
        self.awaiting_headword = False

    def _skip(self, reason, text):
        self.skipped[reason] = self.skipped.get(reason, 0) + len(text)

    # -- the pass ------------------------------------------------------
    def feed(self, span, text, first_in_row, margin):
        font = span.font
        stripped = text.strip()
        if not stripped:
            return

        if (font == ITALIC_FONT and stripped == BAR) or (
            font in XREF_FONTS and stripped in BAR_GLYPHS
        ):
            # The bar that CLOSES the headword we are building is mid-row too,
            # and this test has to come first. Reading it as a cross-reference
            # bar threw away everything after it on the header row - which is
            # where Blust puts the etymology, so every one of the 527 barred
            # roots lost it: `|kashkash| (PAN *kaSkaS ...` kept the headword and
            # dropped `(PAN *kaSkaS` entirely (maintainer, 2026-09-10).
            if (
                self.in_headword
                and self.entry is not None
                and self.entry.headword
                and not self.entry.senses
            ):
                self.in_headword = False
                self._new_sense(number=None)
                self.entry.senses.clear()
                self.sense = None
                self.consumed += len(text)
                return
            # A headword is never mid-line. Mid-row this bar belongs to a
            # cross-reference - "-> |faw|:2" - and what follows it is the
            # target, not a new entry (maintainer, 2026-09-10).
            #
            # But only if an arrow has opened one. Blust also puts bars round a
            # sub-entry's OWN form when that form is a bound root: p.370 sets
            # `4 |pia-dutkhun| [C] lower the head`, and with no arrow in sight
            # the bar swept the form, the label and the definition into a
            # cross-reference, leaving sense 4 with `pia-dutkhun [C] lower the`
            # as its target. One line in the book; the only other mid-row
            # opening bar is p.565's, and that one does follow an arrow.
            if not first_in_row and self.entry is not None and self.row_has_arrow:
                self.row_has_xref = True
                self.consumed += len(text)
                return
            if first_in_row:
                self._close_entry()
                self.entry = Entry(fmt="B", printed_page=self.page)
                self.awaiting_headword = True
                self._new_sense(number=None)
                self.entry.senses.clear()
                self.sense = None
            self.consumed += len(text)
            return

        if font == HEADWORD_FONT:
            # PyMuPDF splits a headword across spans (|aca|+|y| for acay), so a
            # bold run adjacent to the one being built continues it.
            # Adjacent bold spans on the same line continue the headword.
            # Adjacent means touching: the gaps measure -0.8 to 0.0 points,
            # because the spans overlap slightly. (This used to also require
            # the entry to have no senses, which is never true - a sense is
            # opened the moment the entry is, so the join never fired and
            # lhalhum came out as lhalh, muzin as m.)
            building = (
                self.in_headword
                and self.entry is not None
                and self.entry.headword
                and abs(self.entry.headword[-1].x1 - span.x0) <= 2.5
                and abs(self.entry.headword[-1].y0 - span.y0) <= ROW_TOLERANCE
            )
            if building:
                self.entry.headword.append(span)
                self.consumed += len(text)
                return
            if self.awaiting_headword and self.entry is not None:
                self.entry.headword.append(span)
                self.awaiting_headword = False
                self.in_headword = True
                self.consumed += len(text)
                return
            if span.x0 <= margin + 4.0:
                self._close_entry()
                self.entry = Entry(fmt="A", printed_page=self.page)
                self.entry.headword.append(span)
                self._new_sense(number=None)
                self.in_headword = True
                self.consumed += len(text)
                return
            if self.entry is None:
                self._skip("before the first entry", text)
                return
            # A bold run away from the margin is a headword cited inside a
            # definition, not a new entry.
            (self.sense.definition if self.sense else self.entry.etymology).append(span)
            self.consumed += len(text)
            return

        self.in_headword = False

        # Anything that is not a bold span ends the headword - and cancels the
        # expectation of one. A root header puts its headword immediately after
        # the opening bar, so if the next span is not bold, that bar was never a
        # root header: it is a cross-reference bar that wrapped to the start of
        # a line ("... -> |anak|:2"). Left standing, the expectation survived
        # rows of text and then swallowed the next real headword - `bahi` and
        # `baruku` became headwords of the entry above them, and their own
        # definitions were lost (maintainer, 2026-09-10).
        self.in_headword = False
        self.awaiting_headword = False

        if self.row_has_xref:
            # Everything after the arrow on this line is the reference.
            self.xref_spans.append(span)
            self.consumed += len(text)
            return


        if self.entry is None:
            self._skip("before the first entry", text)
            return

        if (
            font == TRANSLATION_FONT
            and first_in_row
            and SENSE_AT_MARGIN.match(stripped)
            and span.x0 <= margin + self.body_indent
            and not self.row_has_xref
        ):
            # Printed p. 291 sets its sense numbers in the plain face, which
            # aliases to the translation font, so without this they were read as
            # translation text - "…where it fell 3".
            #
            # A sense number opens its line AT the margin. Allowing ten points
            # of slack let a wrapped translation line that happens to begin
            # with a numeral open a sense instead: p.887 wraps `tata wa shaba
            # ‘100’; tusha wa shaba` / `200`, and the 200 became a sense
            # number, so shaba read "sense numbering starts at 200".
            m = SENSE_AT_MARGIN.match(stripped)
            self._new_sense(int(m.group(1)), m.group(2))
            self.consumed += len(text)
            return

        if font == LABEL_FONT:
            match = SENSE_NUMBER.match(stripped)
            # A digit set below the baseline right after the headword is a
            # homograph index, not a sense number: the dictionary has two `a`
            # entries, a(1) "future marker" and a(2) the linking particle.
            if (
                match
                and self.entry is not None
                and self.entry.headword
                and self.entry.homograph is None
                # Nothing but the colon may have arrived. A root's subscript is
                # set so far below the baseline that row clustering puts it on
                # its OWN row, after the colon - `|kazash|` then `:` then, 4.2pt
                # lower, `2`. Requiring no sense at all meant the digit landed
                # in the definition, so the root read `: 2` and every one of
                # these looked like "a bound root with its own sense"
                # (maintainer, 2026-09-11).
                and not any(
                    re.search(r"\w", _render(s.definition) or "")
                    or s.examples or s.notes or s.form
                    for s in self.entry.senses
                )
                and abs(self.entry.headword[-1].x1 - span.x0) <= 4.0
                and span.y0 > self.entry.headword[-1].y0 + 1.0
            ):
                self.entry.homograph = int(match.group(1))
                self.consumed += len(text)
                return
            if match and span.x0 <= margin + 10.0:
                self._new_sense(int(match.group(1)), match.group(2))
            elif LABEL.match(stripped) and self.sense is not None:
                self.sense.label = stripped
            elif NOTE_MARKER.match(stripped):
                if self.sense is None:
                    self._new_sense()
                self.sense.notes.append([])
                self.mode = "note"
            elif self.mode == "note" and self.sense is not None and self.sense.notes:
                # A note cites a homograph by its subscript - "Said to be
                # distinct from /rizit/(1)." - and the subscript is set in this
                # face. Sent to the definition it read `... used for houseposts
                # 1` and the note lost the only thing that told the two rizit
                # entries apart. 3 notes in the book carry one.
                self.sense.notes[-1].append(span)
            else:
                # Blust queries a gloss he could not settle by printing
                # `GLOSS?` in this face where the definition goes, and one of
                # the four sits right after a root header, where there is no
                # sense yet. Requiring one dropped it in silence - and
                # `consumed` counts what feed() accepted, so the 100% figure
                # could not see it.
                if self.sense is None:
                    self._new_sense()
                self.sense.definition.append(span)
            self.consumed += len(text)
            return

        if font == SUBENTRY_FONT:
            # Three things open a block at the column margin, not two. A bold
            # headword (T8) opens a main entry; a sense number opens a
            # sub-entry of the entry above it; and - 4,372 times - the derived
            # form itself, set in this face and sitting AT the margin with no
            # number in front of it, opens an entry of its own. It is an index
            # line pointing at the entry that treats the form: "an-sun-in [PF]
            # be gathered in a place -> sun:2". Reading those as sub-entries is
            # what absorbed 148 forms into klhiw and 137 into manu
            # (maintainer, 2026-09-10).
            #
            # A form broken across a printed line resumes at the margin too, so
            # a run that ended in a hyphen continues rather than opens.
            if (
                first_in_row
                and not self.row_has_xref
                and span.x0 <= margin + SUBENTRY_MARGIN
                and not self._form_broke_across_the_line()
            ):
                self._close_entry()
                self.entry = Entry(fmt="A", printed_page=self.page)
                self.entries_opened_at_margin += 1
                self._new_sense()
                self.sense.form.append(span)
                self.consumed += len(text)
                return
            # A Thao form cited mid-definition, with the definition running on
            # after it: p.896 prints `legendary Thao character, the wife of
            # Shnawluman; name for a female buffalo` with `Shnawluman` in this
            # face. Read as a sub-entry it cut the definition in two and left
            # `the wife of` dangling. A real sub-entry opens its line, so a run
            # arriving mid-line while a definition is already under way is a
            # citation. Two lines in the book cite a form this way, and the
            # other is the bracketed `(short for haya wa caw)` below.
            if (
                self.sense is not None
                and not first_in_row
                and not self.row_has_xref
                and re.search(r"\w", _render(self.sense.definition) or "")
            ):
                self.sense.definition.append(span)
                self.consumed += len(text)
                return
            if self.sense is not None and self._definition_bracket_open():
                # A Thao form cited inside a parenthetical in the definition is
                # set in this face too: p.398 prints `that person/those people
                # (short for haya wa caw)`. Read as a sub-entry it opened a
                # sense whose form was `haya wa caw` and whose entire definition
                # was the closing bracket. This mirrors the rule one branch up
                # that keeps a bold run inside a definition out of the headword.
                # 5 definitions in the book cite a form this way.
                self.sense.definition.append(span)
                self.consumed += len(text)
                return
            if self.sense is None or self.sense.definition or self.sense.examples:
                self._new_sense()
            self.sense.form.append(span)
            self.consumed += len(text)
            return

        if font in XREF_FONTS or (font == ITALIC_FONT and stripped == ARROW):
            if stripped == ARROW:
                self.row_has_arrow = True
            self.row_has_xref = True
            self.consumed += len(text)
            return

        if self.sense is None:
            self._new_sense()

        if font in SOURCE_FONTS:
            # A Thao run that appears after English has already started on this
            # printed line is a term cited inside the translation - "The wood of
            # the lina tree does not rot quickly" sets `lina` in italic - not a
            # new example. extract_source.py has the same rule; without it the
            # translation is cut in half and the fragment left behind
            # illustrates nothing, which is what the bold-word check reports.
            # A Thao run that OPENS a printed line while a translation is
            # already open is a wrapped body line, not a new example - the
            # sentence or the term cited inside its English simply ran on.
            # Position separates the two: an example opens at about margin+2,
            # a wrapped body line is indented to about margin+5.
            #
            #   p.372   pa-shzup-i uan ihu sa falhán sa nak   x0 = margin+2.2
            #           a maca Please put a poultice of       x0 = margin+5.4
            #           falhán on my eyes                     x0 = margin+5.4
            #
            # Without it the third line opened a new example, leaving `falhán`
            # translated "on my eyes" and the real sentence cut in half. 49 of
            # them; Hunter's extractor has had this test (`continuation_x`) all
            # along, which is how the diff found it.
            if (
                first_in_row
                and span.x0 > margin + self.body_indent
                and self.mode == "example"
                and self.sense.examples
                and self.sense.examples[-1][1]
            ):
                self.sense.examples[-1][1].append(span)
                self.sense.examples[-1][2].append(span)
                # The rest of the run follows it: `falhán` arrives as `falh`
                # plus the accented tail, and only the first span opens the row.
                self.translation_on_this_row = True
                self.consumed += len(text)
                return
            if self.translation_on_this_row and self.sense.examples:
                target = (
                    self.sense.notes[-1]
                    if self.mode == "note" and self.sense.notes
                    else self.sense.examples[-1][1]
                )
                target.append(span)
                if target is self.sense.examples[-1][1]:
                    self.sense.examples[-1][2].append(span)
                self.consumed += len(text)
                return
            if self.mode != "example" or (
                self.sense.examples and self.sense.examples[-1][1]
            ):
                self.sense.examples.append(([], [], [], self.page))
            self.mode = "example"
            self.sense.examples[-1][0].append(span)
            self.consumed += len(text)
            return

        if (
            stripped == "/"
            and self.sense is not None
            and self.sense.form
            and not self.sense.definition
            and not self.sense.examples
        ):
            # An alternation slash between two spellings of one form is set in
            # the Thao face nearly everywhere - `pasa-rima/pasay rima`. Printed
            # p.832 sets this one in the translation face instead, so it landed
            # in the definition and the second spelling opened a sense of its
            # own whose whole definition was `/`. One in the book.
            self.sense.form.append(span)
            self.consumed += len(text)
            return

        if font == TRANSLATION_FONT:
            if self.mode == "note" and self.sense.notes:
                self.sense.notes[-1].append(span)
            elif self.mode == "example" and self.sense.examples:
                self.sense.examples[-1][1].append(span)
                self.translation_on_this_row = True
            else:
                self.sense.definition.append(span)
            self.consumed += len(text)
            return

        if font in DEFINITION_FONTS or font == ITALIC_FONT:
            # The book occasionally sets an example's translation in the
            # definition face. p.835 prints
            #     ani yaku ma-min-riqaz atu        (T5/T6, margin+2.2)
            #     I never see the dog              (T7,    margin+5.4)
            # and the second line went to the sense definition, leaving the
            # example with no English at all - the first defect the maintainer
            # reported. A definition never follows an example directly
            # (maintainer's ruling), so an indented body line arriving while an
            # example is open and still untranslated IS its translation.
            if (
                first_in_row
                and span.x0 > margin + self.body_indent
                and self.mode == "example"
                and self.sense.examples
                and not self.sense.examples[-1][1]
                and self.sense.examples[-1][0]
            ):
                self.sense.examples[-1][1].append(span)
                self.translation_on_this_row = True
                self.consumed += len(text)
                return
            # ... and the rest of that row follows it. Only the first span
            # opens a row, so without this the p.835 translation was the single
            # word "I".
            if (
                self.translation_on_this_row
                and self.mode == "example"
                and self.sense.examples
            ):
                self.sense.examples[-1][1].append(span)
                self.consumed += len(text)
                return
            if self.mode == "note" and self.sense.notes:
                self.sense.notes[-1].append(span)
            elif (
                not self.entry.etymology
                and not self.sense.definition
                and ETYMOLOGY.match(stripped)
            ):
                self.entry.etymology.append(span)
                self.mode = "definition"
            else:
                self.sense.definition.append(span)
                self.mode = "definition"
            self.consumed += len(text)
            return

        self._skip(f"font {font}", text)

    def _definition_bracket_open(self) -> bool:
        """True when the definition so far has an unclosed `(`."""
        text = _render(self.sense.definition)
        return text.count("(") > text.count(")")

    def _column_lines(self, rows, column):
        """Group one column's spans into the printed lines they were set in.

        normalized_rows clusters at 3.1pt. That is tight enough to strand the
        parts of a line that are set below its baseline, and Blust sets four
        such parts: the bars and colon of a root header, a homograph subscript,
        a sense number, and a bracketed grammatical label.

            p.317   y = 464.02   T9 pash-balis   T7 nail it!
                    y = 467.34   T11 3           T11 [I]

        The parser saw a form with no number and then a bare `3 [I]`, so
        `pash-balis` came out unnumbered and the label was lost. The same split
        hits `|dumdum|:`, `|bariz|(2):`, `qali(1) day; sky; weather`, and the
        subscript in a cross-reference - `->ara(1):3` - 800 lines in all.

        There is no need to special-case any of them, because the two
        populations do not overlap. Measured over every column of every
        dictionary page, the gap between one clustered row and the next falls
        either in 3.1-6.8pt (804 gaps, every one of them a split line) or at
        11.0pt and above (the real line spacing, 14.9 being the mode). Nothing
        whatever lies between 6.9 and 8.3. Re-clustering the column at 7.5pt,
        measured from the line's own first row so a group cannot creep, closes
        every split and cannot join two printed lines.

        Columns are grouped separately: the two columns' baselines do not
        agree, so clustering them together would chain one column's line into
        the other's. Doing it per column also means a split row that carries
        the OTHER column's text keeps it - moving whole rows lost 817
        characters (maintainer, 2026-09-11).
        """
        low, high = (0.0, COLUMN_SPLIT) if column == 0 else (COLUMN_SPLIT, 1e9)
        lines: list[tuple[float, list]] = []
        for row in sorted(rows, key=lambda r: r.y0):
            spans = [s for s in row.spans if low <= s.x0 < high]
            if not spans:
                continue
            if lines and row.y0 - lines[-1][0] <= LINE_TOLERANCE:
                lines[-1][1].extend(spans)
            else:
                lines.append((row.y0, list(spans)))
        return [sorted(spans, key=lambda s: s.x0) for _y0, spans in lines]

    def _body_indent(self, lines, margins):
        """The offset above which a row is a wrapped body line, for this page.

        Rows open at three distances from the column margin: 0 for anything
        structural (a headword, a sense number), a small one for an example,
        and a larger one for a continuation. The dividing line is the midpoint
        of the two non-zero distances the page actually uses.
        """
        offsets = collections.Counter()
        for column, margin in margins.items():
            for spans in lines[column]:
                offsets[round(min(s.x0 for s in spans) - margin, 1)] += 1
        # Most rows on a dictionary page are continuations, so the wrapped
        # indent is by far the commonest non-zero offset; the example opener is
        # the largest offset below it. Taking the "two most commonest" instead
        # is fragile - p.372 has 60 rows at +5.4, 2 at +2.2 and 2 at a stray
        # +39.2, which put the dividing line at 22.
        non_zero = [(value, n) for value, n in offsets.items() if value > 0.5]
        if not non_zero:
            return BODY_INDENT
        wrapped = max(non_zero, key=lambda pair: pair[1])[0]
        below = [value for value, n in non_zero if value < wrapped and n >= 2]
        if not below:
            return BODY_INDENT
        opener = max(below)
        if wrapped - opener > 8.0:
            return BODY_INDENT
        return (opener + wrapped) / 2.0

    def run(self, document) -> list[dict]:
        for pdf_page in DICTIONARY_PAGES:
            self.page = pdf_page - 10
            rows = [
                r for r in normalized_rows(document, pdf_page) if 95.0 < r.y0 < 680.0
            ]
            spans = [s for r in rows for s in r.spans]
            if not spans:
                continue
            margins = {
                c: min(s.x0 for s in spans if (s.x0 < COLUMN_SPLIT) == (c == 0))
                for c in (0, 1)
                if any((s.x0 < COLUMN_SPLIT) == (c == 0) for s in spans)
            }
            lines = {c: self._column_lines(rows, c) for c in margins}
            self.body_indent = self._body_indent(lines, margins)
            for col in (0, 1):
                if col not in margins:
                    continue
                for ordered in lines[col]:
                    ordered = merge_accent_overlays(ordered)
                    carried = self._flush_xref()
                    self.translation_on_this_row = False
                    self.row_has_xref = carried
                    self.row_has_arrow = carried
                    for index, span in enumerate(ordered):
                        self.feed(
                            span,
                            join_spans([span]),
                            index == 0,
                            margins[col],
                        )
        self._close_entry()
        return [e.render() for e in self.entries]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path,
                        default=Path(__file__).resolve().parent / "entry-records.json")
    parser.add_argument("--show", help="print the entry with this headword")
    args = parser.parse_args()

    document = fitz.open(SOURCE_PATH)
    learn_hyphenation_from(document, DICTIONARY_PAGES)
    engine = Parser()
    records = engine.run(document)

    if args.show:
        for record in records:
            if record["headword"] == args.show:
                print(json.dumps(record, ensure_ascii=False, indent=2))
        return 0

    payload = {
        "statistics": {
            "entries": len(records),
            "format_A": sum(1 for r in records if r["format"] == "A"),
            "format_B": sum(1 for r in records if r["format"] == "B"),
            "senses": sum(len(r["senses"]) for r in records),
            "examples": sum(len(s["examples"]) for r in records for s in r["senses"]),
            "notes": sum(len(s["notes"]) for r in records for s in r["senses"]),
            "characters_consumed": engine.consumed,
            "characters_skipped": engine.skipped,
        },
        "entries": records,
    }
    args.out.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"wrote {args.out}")
    print(json.dumps(payload["statistics"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
