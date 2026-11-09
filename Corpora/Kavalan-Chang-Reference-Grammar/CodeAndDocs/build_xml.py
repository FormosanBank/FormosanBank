#!/usr/bin/env python3
"""Build the Kavalan reference-grammar corpus from reviewed source ledgers."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE_UNITS = ROOT / "CodeAndDocs" / "source_units.tsv"
SOURCE_COVERAGE = ROOT / "CodeAndDocs" / "source_coverage.tsv"
SOURCE_VARIANTS = ROOT / "CodeAndDocs" / "source_variant_decisions.tsv"
REVIEW_CORRECTIONS = ROOT / "CodeAndDocs" / "review_corrections.tsv"
REVIEW_LOG = ROOT / "CodeAndDocs" / "review_log.tsv"
REVIEW_ADJUDICATION = ROOT / "CodeAndDocs" / "review_adjudication.tsv"
SOURCE_ADDITIONS = ROOT / "CodeAndDocs" / "source_units_additions.tsv"
OUT_XML = ROOT / "XML" / "Kavalan" / "chang-2000-kavalan-reference-grammar.xml"
# Record-level decisions, one TSV per kind (POL-039; maintainer, audit round 1, 2026-11-09: "Move them into TSV
# files"). Each row names its example or word and carries the ruling it applies, in the maintainer's words, or says
# that none exists. A row that changes nothing stops the build (see build_tree).
DECISIONS = {kind: ROOT / "CodeAndDocs" / f"decisions_{kind}.tsv"
             for kind in ("word_glosses", "morphemes", "spellings", "clitics", "notes", "song_lines")}


def read_decisions(kind: str, actions: frozenset[str] | None = None) -> list[dict[str, str]]:
    """The rows of decisions_<kind>.tsv: tab-separated, no quoting; every row needs a ruling and, where the file
    has an action column, a known action."""
    with DECISIONS[kind].open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))
    for row in rows:
        if not (row.get("ruling") or "").strip():
            raise ValueError(f"decisions_{kind}.tsv: a row without its ruling: {row}")
        if actions is not None and row["action"] not in actions:
            raise ValueError(f"decisions_{kind}.tsv: unknown action {row['action']!r}")
    return rows


def _unique(kind: str, keys: list) -> list:
    if len(keys) != len(set(keys)):
        raise ValueError(f"decisions_{kind}.tsv: the same example or word is listed twice")
    return keys


_MORPHEME_ROWS = read_decisions("morphemes", frozenset({"morphemes", "no_morphemes", "circumfix",
                                                        "unglossed_last_piece"}))
_SPELLING_ROWS = read_decisions("spellings", frozenset({"respell", "words_from_printing"}))
_NOTE_ROWS = read_decisions("notes", frozenset({"book_note", "handwriting_note", "drop_form_note",
                                                "drop_translation_note"}))
# Each action fills exactly the columns it uses.
for _row in _MORPHEME_ROWS:
    if bool(_row["morphemes"]) != (_row["action"] == "morphemes"):
        raise ValueError(f"decisions_morphemes.tsv: morphemes given or missing for {_row['action']}: {_row}")
for _row in _SPELLING_ROWS:
    if (bool(_row["was"] and _row["now"]), bool(_row["printing"])) != (
            (True, False) if _row["action"] == "respell" else (False, True)):
        raise ValueError(f"decisions_spellings.tsv: wrong columns for {_row['action']}: {_row}")
for _row in _NOTE_ROWS:
    if not _row["note"] or bool(_row["replacement"]) != (_row["action"] == "handwriting_note"):
        raise ValueError(f"decisions_notes.tsv: wrong columns for {_row['action']}: {_row}")


def _word_keys(action: str) -> frozenset[tuple[str, int]]:
    return frozenset(_unique("morphemes", [(row["unit_id"], int(row["word"]))
                                           for row in _MORPHEME_ROWS if row["action"] == action]))


def _notes(action: str) -> dict[str, dict[str, str]]:
    rows = [row for row in _NOTE_ROWS if row["action"] == action]
    _unique("notes", [row["unit_id"] for row in rows])
    return {row["unit_id"]: row for row in rows}

# The student review (2026-10-30), as ruled by the maintainer on 2026-11-06; see README "Student review".
REVIEW_NOTE_PREFIX = "Review (2026-10)"
ADJUDICATION_ACTIONS = frozenset({
    "keep_transcription",          # do not apply the student's correction to this field
    "replace",                     # apply `value` (a JSON array for words/glosses) instead of hers
    "drop_alternate_translation",  # do not publish this printed alternative translation
    "remove_note_text",            # leave this text out of the unit's published review note
    "add_word_gloss_note",         # field `word_gloss_note:<n>`: a note on word n's gloss
})
# A unit whose source prints no free translation says exactly this in translation_notes.
NO_PRINTED_TRANSLATION = "No translation is printed for this example."
# Stands for <UNCLEAR/> inside gloss strings until serialization (POL-061).
UNCLEAR = "\ue000"
# Glosses that say "unknown" are written <UNCLEAR/> too (POL-061, amended 2026-10-17).
UNKNOWN_GLOSSES = frozenset({"?", "??"})
# Morpheme FORMs carry no punctuation; words and sentences keep theirs (ruled 2026-11-06).
MORPHEME_PUNCTUATION = "[]【】,.;:?!\"，。？！；：、「」『』"
# Sentences and their translations end in the script's own period (ruled 2026-11-06: "sentences and their
# translations should end in periods appropriate to the script being used"). A Kavalan line ends as its Chinese
# translation ends, in ? or ! for a question or an exclamation (round-3 decision page, 2026-11-07: "End the
# Kavalan as the Chinese ends: ? or !").
LATIN_SENTENCE_END = ".?!"
CHINESE_SENTENCE_END = "。？！"
KAVALAN_END_OF = {"？": "?", "！": "!", "，": ","}
# Final marks that 。 must not follow: mid-sentence marks, and Latin end marks in a Chinese translation.
MID_SENTENCE_END = "，,；;：:、.?!…"
# Six song lines whose printed translation ends in a comma because the song goes on keep the comma, and their Kavalan
# line ends in one too (round-6 decision page, 2026-11-08: "I was wrong about the song lines. Those can end in commas.
# They should match across the FORM and the translation (with the script-appropriate variant)."). Each listed unit
# must still end in a comma; any other translation ending in a mid-sentence mark stops the build.
SONG_LINE_COMMA_UNITS = frozenset(_unique("song_lines", [row["unit_id"] for row in read_decisions("song_lines")]))
# Notes that say what the book prints are not written (his ruling on the Chang Seediq grammar, 2026-10-14: "I would
# NOT put in the notes 'what the book prints' since you don't actually know!"). Asked again for this corpus, where a
# scan reader checked each place, he answered "No (as now)" (round-3 decision page, 2026-11-07). The switch would turn
# both kinds below on; it stays off.
PRINT_NOTES = False
# Brackets and subscripts in the Kavalan line are deleted from the original tier (ruled 2026-11-06: "the brackets
# in the Formosan text line (S FORM) can be deleted, along with any subscripts"). With PRINT_NOTES, a note says what
# the book bracketed.
BRACKET_PAIRS = (("【", "】", "bold brackets 【 】"), ("[", "]", "square brackets [ ]"))
CONSTITUENT_LABEL = re.compile(r"\[\s*[sₛ]\s+")   # the transcription writes the subscript s of [ₛ as "[s "
SUBSCRIPTS = "ₛᵢⱼₖ"
# The transcription's notes on the bracketed examples: six say the brackets are preserved, which is no longer true,
# and are removed. 6b's says only that the book prints them; it is true and kept, unless PRINT_NOTES writes the
# fuller note that says which words the book bracketed.
OLD_BRACKET_NOTES = ("Square brackets are printed analytical notation and are preserved.",)
SUPERSEDED_BRACKET_NOTES = ("Brackets are printed constituent notation.",)
# Three transcription notes say the handwriting is excluded, but the corpus now follows it there (ruled
# 2026-11-06: "Use the handwriting as corrections to the book" ... "In all of these cases, follow what the student
# did"). The untrue note is removed; with PRINT_NOTES it is replaced by what the book prints (the first also
# misquoted the print, pun=ta for pun-ta).
HANDWRITING_NOTE_REPLACEMENTS = {unit: (row["note"], row["replacement"])
                                 for unit, row in _notes("handwriting_note").items()}
# The transcription's note on example 20 (p. 112) says its gloss keeps the printed trailing hyphen, which the
# trailing-hyphen ruling (below) removes; the note, untrue now, goes with it.
TRAILING_HYPHEN_NOTES = ("Gloss transcribed exactly as printed, including the trailing hyphen.",)
# Notes giving what the book prints about an example, chosen on the round-3 decision page (2026-11-07): footnote 30
# on 20a ("Only a note on 20a"), and example 1's printed pronunciation (the option "Add the 9 new ones; leave out
# the 4 already in the corpus" gives example 1 its pronunciation note too). The nine examples added from the
# phonology chapter carry theirs in source_units_additions.tsv.
BOOK_NOTES = {unit: row["note"] for unit, row in _notes("book_note").items()}
# Five ta-/sa-...-an words whose -an slot the book leaves unglossed take one morpheme for the circumfix, written
# with - where the root goes, as an infixed root is (POL-014: "Circumfixes are analogous, unless the source glosses
# them as prefix + suffix"; round-3 decision page, 2026-11-07: "One morpheme for the circumfix (POL-014)"). Keyed
# (unit, word number). The other ta-/sa-...-an words keep two morphemes, ta and an: those whose -an the book glosses
# (POL-014's exception), and 18a (p049l-e001), whose -an the book leaves unglossed but whose transcription gloss
# (處所格-豐濱-處所格) the corpus keeps, as the student recommended; the circumfix answer did not name it.
# The two sa-kasaw-an (p101r-e004, p102r-e005) are not circumfix words: the grammar says sa- takes no -an (p. 79), so
# their -an is a piece the book leaves unglossed: sa 終點 · kasaw 長濱 · an <UNCLEAR/>, word gloss 終點-長濱-<UNCLEAR/>
# (round-6 decision page, 2026-11-08: "sa 終點 · kasaw 長濱 · an <UNCLEAR/>").
CIRCUMFIX_WORDS = _word_keys("circumfix")
CIRCUMFIX_PREFIXES = frozenset({"ta"})
UNGLOSSED_LAST_PIECE = _word_keys("unglossed_last_piece")
# A ruled circumfix word's gloss drops the empty slot the book prints under -an, the frame's second half:
# ta=paw-an-su's 處所格-家--你 is published 處所格-家-你 (round-6 decision page, 2026-11-08: "處所格-家-你").
# Words written as the maintainer ruled, in every printing of the example (keyed by sentence): ta=paw-an-su as
# ta-paw-an-su (round 6, on V066: "Write the word with a hyphen: ta-paw-an-su"), and quni=pa=isu as quni-pa=isu
# (round 6: "use her version, but segment as quni-pa=isu (matching the gloss)").
RULED_FORM_EDITS: dict[str, tuple[tuple[str, str], ...]] = {}
for _row in _SPELLING_ROWS:
    if _row["action"] == "respell":
        RULED_FORM_EDITS.setdefault(_row["sentence"].removeprefix("S-"), ())
        RULED_FORM_EDITS[_row["sentence"].removeprefix("S-")] += ((_row["was"], _row["now"]),)
# Two examples printed twice take their words from the printing the student corrected (round 6: "S-p039r-e002: use
# her version"; "S-p069r-e003: use her version"). Sentence id -> unit.
WORDS_FROM_PRINTING = dict(zip(
    _unique("spellings", [row["sentence"] for row in _SPELLING_ROWS if row["action"] == "words_from_printing"]),
    [row["printing"] for row in _SPELLING_ROWS if row["action"] == "words_from_printing"]))
# A clitic written before its word keeps the = (POL-015) on itself, qa= · patay (round 6: "Put = on the clitic:
# qa= · patay (11 words)"). Word ids.
PROCLITIC_WORDS = frozenset(_unique("clitics", [row["word_id"] for row in read_decisions("clitics")]))
# A word the book leaves unglossed keeps one <UNCLEAR/> morpheme, except paqenanum (p050l-e001), the handwritten
# replacement of the printed word (round 6: "All of them except paqenanum keep a morpheme, glossed as <UNCLEAR/>.
# paqenanum does not have an M.").
NO_MORPHEME_WORDS = _word_keys("no_morphemes")
# Footnote 19 (p. 74): the transcription's two notes on why its first example was held back are dropped; the example
# is published (round 6: "Publish ia. as its own sentence, and drop the transcription's two notes").
DROPPED_TRANSCRIPTION_NOTES = {unit: (row["note"], _notes("drop_translation_note")[unit]["note"])
                               for unit, row in _notes("drop_form_note").items()}
if set(DROPPED_TRANSCRIPTION_NOTES) != set(_notes("drop_translation_note")):
    raise ValueError("decisions_notes.tsv: drop_form_note and drop_translation_note must list the same examples")
_USED: dict[str, set] = {}
# Parentheses: full-width in the Chinese, ASCII in the Kavalan. He asked for normalization (2026-11-06: "does this
# get normalized during processing? If not, it should be."). The direction is the one he approved for the Chang
# Seediq grammar (2026-10-14: "OK."); applying it here is our reading of his request to do this review "in the same
# way we did for the other Chang reference grammar", shown to him in round 3.
TO_FULL_WIDTH = str.maketrans("()", "（）")
TO_ASCII = str.maketrans("（）", "()")

XML_NS = "http://www.w3.org/XML/1998/namespace"
XML_LANG = f"{{{XML_NS}}}lang"
ET.register_namespace("xml", XML_NS)

TEXT_ATTRIBUTES = {
    "id": "chang-2000-kavalan-reference-grammar",
    XML_LANG: "ckv",
    "dialect": "Kavalan",
    "source": "Chang Yung-li 2000 Kavalan reference grammar, Basecamp scan 12.pdf, reviewed source-unit ledger",
    "copyright": "CC BY-NC 4.0",
    "citation": "Chang, Y. (2000). Gamalanyu cankao yufa. Yuan liu chuban shiye gufen.",
    "BibTeX_citation": "@book{chang2000kavalan,title={Gamalanyu cankao yufa},author={Chang, Yung-li},year={2000},publisher={Yuan liu chuban shiye gufen}}",
}

# A gloss line, one gloss per word, where the transcription's does not line up with the words (decisions_word_glosses.tsv).
_GLOSS_ROWS = read_decisions("word_glosses")
WORD_GLOSS_OVERRIDES = dict(zip(_unique("word_glosses", [row["unit_id"] for row in _GLOSS_ROWS]),
                                [tuple(json.loads(row["glosses"])) for row in _GLOSS_ROWS]))

# A word's morphemes written out (decisions_morphemes.tsv, action "morphemes"): the two locative pronouns of p. 96,
# split as p. 80 glosses ti-maisu-an; the two t-ayta words.
_word_keys("morphemes")   # each word listed once
MORPHEME_OVERRIDES = {(row["unit_id"], int(row["word"])): tuple(tuple(part) for part in json.loads(row["morphemes"]))
                      for row in _MORPHEME_ROWS if row["action"] == "morphemes"}

INLINE_INFIXES = frozenset({"em", "um", "n"})
# A word FORM writes an infix in angle brackets, p<um>ukun, and so does the sentence line (maintainer, audit round 1,
# 2026-11-09: "the sentence line should change hyphens to <> for infixes"; see sentence_line). POL-014:
# "W-tier FORMs mark an infix with ASCII angle brackets (k<um>a'en); S-level original FORMs may keep the source's
# typography". Maintainer, round 5 (2026-11-08), on the 82 infixed words: "Write them as POL-014 says: p<um>ukun".
# A one-word alternative the book prints with a slash under one gloss is a second FORM (ver="alt") on that word, not a
# sentence of its own. Maintainer, round 4 (2026-11-07), on the alternative sentences: "If a/ya is shows as a slash
# alternative (or a parantheses alternative), that should be handled using ver="alt" on the word, not by making a
# whole additional S block. Same for S-p097r-e003-alt01. Same for Ranaw/Rakana". POL-028 makes "a whole short word
# alternating a/u" a variant FORM (ya/a), and an optional morpheme the glossing does not distinguish too (timayku/an,
# both 我); whether Ranaw/Rakana are one word or two it leaves to the maintainer, and his rule decides it. The rows
# he named are marked word_variant in source_variant_decisions.tsv.
WORD_VARIANT = "word_variant"
# ALTERNATIVE_WORD_GLOSSES: an alternative sentence (an included row of source_variant_decisions.tsv) gets a word
# tier, built like any other sentence's, from the gloss line in that row's `glosses` column. Maintainer, round 5
# (2026-11-08): 'nay/wi'u, "A sentence of its own, with words"; saraq/tengen, the same, and "I assume you mean this
# also has Ms as appropriate. These are two S-blocks, one for each variant."; zau/'nay, "Two S blocks, each glossed
# and translated according to its variant."; (u) and (ya), "There should be two S-blocks, one with the optional
# piece (and it's gloss) and one without." The glosses are the example's printed gloss line: a slash under one gloss
# gives both readings that gloss ('nay/wi'u 那, saraq/tengen 髒兮兮); zau/'nay prints 這/那, so 'nay is 那; the
# reading without an optional piece leaves out that piece and its gloss ((u)-turu 類別詞-三 -> turu 三; (ya) 主格).
# 28's =b. and =c. (p059l-e002) have none yet: their own gloss lines are not in the transcription, and the
# maintainer has not ruled on them.


@dataclass(frozen=True)
class SourceUnit:
    unit_id: str
    xml_unit_id: str
    pdf_page: str
    side: str
    book_page: str
    source_order: int
    printed_label: str
    unit_type: str
    decision: str
    review_status: str
    form: str
    alternate_forms: str
    gloss: str
    gloss_alignment: str
    translation_zho: str
    alternate_translations_zho: str
    translation_eng: str
    form_notes: str
    translation_notes: str
    decision_reason: str
    # Set only by a student review correction (see load_review_corrections); it
    # then replaces the ledger gloss and WORD_GLOSS_OVERRIDES for this unit.
    reviewed_glosses: tuple[str, ...] | None = None
    # True for a printed example the transcription missed, added from the scan
    # after review (source_units_additions.tsv).
    added: bool = False
    # The form as transcribed, kept when a review correction replaces `form`.
    transcribed_form: str = ""
    # The fields a review correction changed ("words", "glosses", "translation").
    review_fields: tuple[str, ...] = ()

    @classmethod
    def from_row(cls, row: dict[str, str], added: bool = False) -> "SourceUnit":
        return cls(
            added=added,
            unit_id=row["unit_id"],
            xml_unit_id=row["xml_unit_id"],
            pdf_page=row["pdf_page"],
            side=row["side"],
            book_page=row["book_page"],
            source_order=int(row["source_order"]),
            printed_label=row["printed_label"],
            unit_type=row["unit_type"],
            decision=row["decision"],
            review_status=row["review_status"],
            form=row["form"],
            transcribed_form=row["form"],
            alternate_forms=row["alternate_forms"],
            gloss=row["gloss"],
            gloss_alignment=row["gloss_alignment"],
            translation_zho=row["translation_zho"],
            alternate_translations_zho=row["alternate_translations_zho"],
            translation_eng=row["translation_eng"],
            form_notes=row["form_notes"],
            translation_notes=row["translation_notes"],
            decision_reason=row["decision_reason"],
        )


@dataclass(frozen=True)
class VariantDecision:
    unit_id: str
    alternate_form: str
    decision: str
    translation_zho: str
    reason: str
    # An included alternative sentence's gloss line, one gloss per word, read from the example's printed gloss line
    # (ALTERNATIVE_WORD_GLOSSES); empty for an alternative that has no word tier yet.
    glosses: str
    # The note published on an included alternative sentence's FORM (empty: none). `reason` documents the decision
    # and is not published. None carries one: 28's =b. and =c. (round 6, 2026-11-08: "notes="The source marks this
    # as an equivalent accepted form." is unnecessary."), footnote 19's ia., and the other eight (round 7: "Drop all
    # eight").
    note: str
    # An included alternative sentence's id is its example's id plus "-" and this: "opt" for a second reading
    # (POL-028), the printed label for a separate printed example (28's b and c, footnote 19's ia) (round 6:
    # "Rename as POL-028 says").
    id_suffix: str

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "VariantDecision":
        return cls(**{field: row[field] for field in cls.__dataclass_fields__})


def split_alternates(value: str) -> list[str]:
    return [part.strip() for part in value.split("|") if part.strip()]


def review_words(unit: SourceUnit) -> list[str]:
    """The words a reviewer is shown: as printed, unless the printed notation
    splits differently from the aligned words (only `[s` constituent brackets
    do), in which case the aligned words."""
    printed = unit.form.split()
    aligned = normalize_surface_form(unit).split()
    return printed if len(printed) == len(aligned) else aligned


def review_glosses(unit: SourceUnit) -> list[str]:
    """The glosses a reviewer is shown: exactly what word_alignment publishes."""
    return [gloss for _, gloss in word_alignment(unit)]


def load_review_corrections(path: Path = REVIEW_CORRECTIONS) -> dict[str, dict[str, tuple[str, str]]]:
    """Student review corrections: unit id -> field -> (was, now).

    Written by apply_review.py. `words` and `glosses` are JSON arrays (a gloss
    may legitimately be empty where the book prints none); `translation` is the
    Chinese free translation. They sit in their own file rather than being
    folded into source_units.tsv, so "what the transcription read" and "what
    review corrected" stay two separate, legible things.
    """
    if not path.exists():
        return {}
    out: dict[str, dict[str, tuple[str, str]]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["field"] not in {"words", "glosses", "translation"}:
                raise ValueError(f"{row['unit_id']}: unknown review field {row['field']!r}")
            out.setdefault(row["unit_id"], {})[row["field"]] = (row["was"], row["now"])
    return out


def load_review_adjudication(path: Path = REVIEW_ADJUDICATION) -> list[dict[str, str]]:
    """The maintainer's rulings where the published result departs from the
    student's literal edit (or adds to it). One row per ruling; `ruling` quotes
    him, `reason` says what the row does and why; for keep_transcription and
    replace, `student_value` is the value she typed that the ruling was made about."""
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    for row in rows:
        if row["action"] not in ADJUDICATION_ACTIONS:
            raise ValueError(f"{row['unit_id']}: unknown adjudication action {row['action']!r}")
        if not row["ruling"].strip():
            raise ValueError(f"{row['unit_id']}: adjudication row without the ruling it applies")
        if row["action"] in {"keep_transcription", "replace"} and not row.get("student_value", "").strip():
            raise ValueError(f"{row['unit_id']}: {row['action']} row without the student's value it rules on")
    return rows


def _same_value(field: str, left: str, right: str) -> bool:
    if field in {"words", "glosses"}:
        return json.loads(left) == json.loads(right)
    return left == right


def adjudicate_corrections(
    corrections: dict[str, dict[str, tuple[str, str]]], adjudication: list[dict[str, str]]
) -> dict[str, dict[str, tuple[str, str]]]:
    """Apply keep_transcription / replace rows to the student's corrections. A
    row applies only to the edit it was ruled on: if her value differs from the
    row's student_value (say, a later return of her file), the build stops."""
    out = {unit_id: dict(fields) for unit_id, fields in corrections.items()}
    for row in adjudication:
        if row["action"] not in {"keep_transcription", "replace"}:
            continue
        fields = out.get(row["unit_id"], {})
        if row["field"] not in fields:
            raise ValueError(f"{row['unit_id']}: adjudication {row['action']} for {row['field']}, "
                             "but the student did not change that field")
        if not _same_value(row["field"], fields[row["field"]][1], row["student_value"]):
            raise ValueError(f"{row['unit_id']}: adjudication {row['action']} for {row['field']} was ruled on "
                             f"{row['student_value']!r}, but her edit is now {fields[row['field']][1]!r}")
        if row["action"] == "keep_transcription":
            del fields[row["field"]]
            if not fields:
                out.pop(row["unit_id"])
        else:
            was, _ = fields[row["field"]]
            value = row["value"]
            if row["field"] in {"words", "glosses"}:
                value = json.dumps(json.loads(value), ensure_ascii=False)
            fields[row["field"]] = (was, value)
    return out


def load_review_notes(
    path: Path = REVIEW_LOG, adjudication: list[dict[str, str]] | None = None
) -> dict[str, str]:
    """Every note the student wrote, verbatim (ruled 2026-11-06: "Every note, in
    her words"), with whitespace collapsed and any remove_note_text applied."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as handle:
        notes = {row["unit_id"]: row["note"] for row in csv.DictReader(handle, delimiter="\t")
                 if row["note"].strip()}
    for row in adjudication if adjudication is not None else load_review_adjudication():
        if row["action"] != "remove_note_text":
            continue
        if row["value"] not in notes.get(row["unit_id"], ""):
            raise ValueError(f"{row['unit_id']}: note text to remove is not in the note")
        notes[row["unit_id"]] = notes[row["unit_id"]].replace(row["value"], " ")
    return {unit_id: " ".join(note.split()) for unit_id, note in notes.items()}


def apply_review_corrections(
    units: list[SourceUnit], corrections: dict[str, dict[str, tuple[str, str]]]
) -> list[SourceUnit]:
    by_id = {unit.unit_id: unit for unit in units}
    orphans = sorted(uid for uid in corrections
                     if uid not in by_id or by_id[uid].decision != "include")
    if orphans:
        raise ValueError(f"review corrections for units that are not included: {orphans[:5]}")
    out = []
    for unit in units:
        fields = corrections.get(unit.unit_id)
        if not fields:
            out.append(unit)
            continue
        current = {
            "words": json.dumps(review_words(unit), ensure_ascii=False),
            "glosses": json.dumps(review_glosses(unit), ensure_ascii=False),
            "translation": unit.translation_zho,
        }
        for field, (was, _) in fields.items():
            if was != current[field]:
                raise ValueError(
                    f"{unit.unit_id}: stale review correction for {field}: reviewed against "
                    f"{was!r}, the ledger now gives {current[field]!r}. Re-export and re-review."
                )
        words = json.loads(fields["words"][1]) if "words" in fields else review_words(unit)
        glosses = json.loads(fields["glosses"][1]) if "glosses" in fields else review_glosses(unit)
        if any(not word or any(ch.isspace() for ch in word) for word in words):
            raise ValueError(f"{unit.unit_id}: a reviewed word is empty or contains a space")
        if len(words) != len(glosses):
            raise ValueError(f"{unit.unit_id}: review leaves {len(words)} words but "
                             f"{len(glosses)} glosses")
        if "glosses" in fields and unit.gloss_alignment == "unavailable":
            raise ValueError(f"{unit.unit_id}: the source prints no glosses for this unit")
        pinned = [index for (uid, index) in MORPHEME_OVERRIDES if uid == unit.unit_id]
        original = list(zip(review_words(unit), review_glosses(unit)))
        if pinned and (len(words) != len(original) or any(
                (words[i - 1], glosses[i - 1]) != original[i - 1] for i in pinned)):
            raise ValueError(f"{unit.unit_id}: review changed a word whose morphemes are "
                             "written out in MORPHEME_OVERRIDES; edit that table by hand")
        out.append(replace(
            unit,
            form=" ".join(words),
            gloss=" ".join(glosses),
            translation_zho=fields["translation"][1] if "translation" in fields
            else unit.translation_zho,
            reviewed_glosses=tuple(glosses) if "glosses" in fields or "words" in fields
            else None,
            review_fields=tuple(sorted(fields)),
        ))
    return out


def load_source_units(
    path: Path = SOURCE_UNITS,
    corrections: dict[str, dict[str, tuple[str, str]]] | None = None,
    additions: Path | None = SOURCE_ADDITIONS,
) -> list[SourceUnit]:
    """Load the ledger with student review corrections applied, as adjudicated,
    plus the examples added after review; pass corrections={} and additions=None
    for the transcription alone."""
    with path.open(encoding="utf-8", newline="") as handle:
        units = [SourceUnit.from_row(row) for row in csv.DictReader(handle, delimiter="\t")]
    if additions is not None and additions.exists():
        with additions.open(encoding="utf-8", newline="") as handle:
            units += [SourceUnit.from_row(row, added=True)
                      for row in csv.DictReader(handle, delimiter="\t")]
    if corrections is None:
        corrections = adjudicate_corrections(load_review_corrections(), load_review_adjudication())
    if corrections:
        units = apply_review_corrections(units, corrections)

    ids = [unit.unit_id for unit in units]
    if len(ids) != len(set(ids)):
        raise ValueError("source_units.tsv contains duplicate unit_id values")
    orders = [unit.source_order for unit in units]
    if len(orders) != len(set(orders)):
        raise ValueError("source_units.tsv contains duplicate source_order values")

    for unit in units:
        if unit.review_status != "verified_against_scan":
            raise ValueError(f"{unit.unit_id}: source unit is not scan-verified")
        if unit.decision == "include" and (not unit.form or (
                not unit.translation_zho and unit.translation_notes != NO_PRINTED_TRANSLATION)):
            raise ValueError(f"{unit.unit_id}: included unit lacks a form or Chinese translation")
        if unit.decision == "include" and not unit.xml_unit_id:
            raise ValueError(f"{unit.unit_id}: included unit lacks xml_unit_id")
        if unit.decision == "exclude" and unit.xml_unit_id:
            raise ValueError(f"{unit.unit_id}: excluded unit has xml_unit_id")
        if unit.decision not in {"include", "exclude"}:
            raise ValueError(f"{unit.unit_id}: unknown decision {unit.decision!r}")
        if unit.decision == "include" and unit.gloss_alignment not in {
            "aligned_morpheme",
            "aligned_word",
            "unavailable",
        }:
            raise ValueError(
                f"{unit.unit_id}: unsupported gloss alignment {unit.gloss_alignment!r}"
            )

    edited = []
    for index, unit in enumerate(units):
        for was, now in RULED_FORM_EDITS.get(unit.xml_unit_id, ()):
            if unit.decision == "include" and was in unit.form:
                if unit.form.count(was) != 1:
                    raise ValueError(f"{unit.unit_id}: {was!r} is not in its form exactly once")
                units[index] = unit = replace(unit, form=unit.form.replace(was, now))
                edited.append(unit.xml_unit_id)
    if set(RULED_FORM_EDITS) - set(edited):
        raise ValueError(f"ruled form edits that changed nothing: {sorted(set(RULED_FORM_EDITS) - set(edited))}")

    units.sort(key=lambda unit: (unit.source_order, unit.unit_id))
    included_ids = {unit.unit_id for unit in units if unit.decision == "include"}
    for unit in units:
        if unit.decision == "include" and unit.xml_unit_id not in included_ids:
            raise ValueError(f"{unit.unit_id}: xml_unit_id is not an included source unit")
    group_source_units(units)
    return units


def group_source_units(units: list[SourceUnit]) -> list[list[SourceUnit]]:
    groups: dict[str, list[SourceUnit]] = {}
    for unit in units:
        if unit.decision == "include":
            groups.setdefault(unit.xml_unit_id, []).append(unit)
    for anchor, group in groups.items():
        if group[0].unit_id != anchor:
            raise ValueError(f"{anchor}: XML group anchor is not its first source occurrence")
        equivalent_forms = {
            sentence_equivalence_key(normalize_surface_form(unit)) for unit in group
        }
        if len(equivalent_forms) != 1:
            raise ValueError(
                f"{anchor}: XML group contains non-equivalent surface forms"
            )
    return list(groups.values())


def load_variant_decisions(
    units: list[SourceUnit], path: Path = SOURCE_VARIANTS
) -> dict[tuple[str, str], VariantDecision]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = [
            VariantDecision.from_row(row)
            for row in csv.DictReader(handle, delimiter="\t")
        ]
    decisions = {(row.unit_id, row.alternate_form): row for row in rows}
    if len(decisions) != len(rows):
        raise ValueError("source_variant_decisions.tsv contains duplicate decisions")
    allowed = {
        "include",
        WORD_VARIANT,
        "exclude_analysis_notation",
        "exclude_unacceptable",
        "block_pending_judgment",
    }
    if any(row.decision not in allowed for row in rows):
        raise ValueError("source_variant_decisions.tsv contains an unknown decision")
    expected = {
        (unit.unit_id, normalize_surface_form(unit, alternate))
        for unit in units
        if unit.decision == "include"
        for alternate in split_alternates(unit.alternate_forms)
    }
    if set(decisions) != expected:
        missing = sorted(expected - set(decisions))
        extra = sorted(set(decisions) - expected)
        raise ValueError(f"variant decision coverage mismatch; missing={missing}, extra={extra}")
    for row in rows:
        if row.decision != "include" and (row.note or row.id_suffix):
            raise ValueError(f"{row.unit_id}: note or id_suffix given for a {row.decision} alternative")
        if row.decision == "include" and not re.fullmatch(r"opt|[a-z]+", row.id_suffix):
            raise ValueError(f"{row.unit_id}: alternative {row.alternate_form!r} has id_suffix {row.id_suffix!r}")
        if row.glosses and row.decision != "include":
            raise ValueError(f"{row.unit_id}: glosses given for a {row.decision} alternative {row.alternate_form!r}")
        if row.glosses and len(row.glosses.split()) != len(row.alternate_form.split()):
            raise ValueError(f"{row.unit_id}: alternative {row.alternate_form!r} has "
                             f"{len(row.alternate_form.split())} words but glosses {row.glosses!r}")
    return decisions


def validate_coverage(units: list[SourceUnit], path: Path = SOURCE_COVERAGE) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if [row["pdf_page"] for row in rows] != [f"{page:03d}" for page in range(1, 123)]:
        raise ValueError("source_coverage.tsv must contain exactly PDF pages 001 through 122")
    if any(row["coverage_status"] != "verified_against_rendered_scan" for row in rows):
        raise ValueError("source_coverage.tsv contains an unverified page")

    included_count = sum(
        int(row["included_left"]) + int(row["included_right"]) for row in rows
    )
    vocabulary_count = sum(
        int(row["vocabulary_left"]) + int(row["vocabulary_right"]) for row in rows
    )
    # Every record's id names its PDF page and half, and its book page follows from them
    # (book page = 2 x PDF page - 20, +1 on the right half): true of all 755 transcribed rows.
    for unit in units:
        match = re.fullmatch(r"p(\d{3})([lr])-[ev]\d{3}", unit.unit_id)
        side = {"l": "left", "r": "right"}.get(match.group(2)) if match else None
        if (match is None or match.group(1) != unit.pdf_page or side != unit.side
                or unit.book_page != str(2 * int(unit.pdf_page) - 20 + (unit.side == "right"))):
            raise ValueError(f"{unit.unit_id}: id, PDF page {unit.pdf_page} {unit.side} and book page "
                             f"{unit.book_page} disagree")
    # The coverage file records what the transcription read; examples added after
    # review (source_units_additions.tsv) are counted separately, not here.
    added = [unit for unit in units if unit.added]
    units = [unit for unit in units if not unit.added]
    if any(unit.decision != "include" or unit.unit_type == "vocabulary_entry" for unit in added):
        raise ValueError("an added record must be an included example, not a vocabulary entry")
    if included_count != sum(unit.decision == "include" for unit in units):
        raise ValueError("source coverage and included source-unit counts disagree")
    if vocabulary_count != sum(unit.unit_type == "vocabulary_entry" for unit in units):
        raise ValueError("source coverage and vocabulary source-unit counts disagree")


def set_text(element: ET.Element, text: str) -> None:
    """Element text, with each UNCLEAR placeholder written as an <UNCLEAR/> child."""
    parts = text.split(UNCLEAR)
    element.text = parts[0] or None
    for part in parts[1:]:
        ET.SubElement(element, "UNCLEAR").tail = part or None


def as_note(text: str) -> str:
    """Attributes hold plain text: an UNCLEAR placeholder is written as `<UNCLEAR/>`."""
    return text.replace(UNCLEAR, "<UNCLEAR/>")


def end_sentence(text: str, translation: str = "") -> str:
    """A Kavalan sentence that does not already end in . ? or ! ends as its
    (finished) Chinese translation does: ? after ？, ! after ！, else a period."""
    if not text or text[-1] in LATIN_SENTENCE_END:
        return text
    return text + KAVALAN_END_OF.get(translation[-1:], ".")


def end_translation(text: str, song_line: bool = False) -> str:
    """A Chinese translation ends in 。 unless it already ends in 。？！. On a song
    line (SONG_LINE_COMMA_UNITS) a final ， becomes 。."""
    text = text.translate(TO_FULL_WIDTH)
    if song_line and text.endswith("，"):
        return text
    if text and text[-1] in MID_SENTENCE_END:
        # Adding 。 would publish "，。"; a translation ending in a comma or another mid-sentence mark needs a
        # ruling first (the six song lines had one).
        raise ValueError(f"translation {text!r} ends in {text[-1]!r}, which no ruling covers")
    return text if not text or text[-1] in CHINESE_SENTENCE_END else text + "。"


def add_form(parent: ET.Element, kind: str, text: str, notes: str = "") -> ET.Element:
    attributes = {"kindOf": kind}
    if notes:
        attributes["notes"] = notes
    element = ET.SubElement(parent, "FORM", attributes)
    set_text(element, text.translate(TO_ASCII))
    return element


def add_translation(
    parent: ET.Element,
    text: str,
    *,
    language: str = "zho",
    alternate: bool = False,
    notes: str = "",
) -> ET.Element:
    attributes = {XML_LANG: language}
    if parent.tag in {"W", "M"}:
        attributes["kindOf"] = "original"
    if alternate:
        attributes["ver"] = "alt"
    if notes:
        attributes["notes"] = notes
    element = ET.SubElement(parent, "TRANSL", attributes)
    set_text(element, text.translate(TO_FULL_WIDTH) if language == "zho" else text)
    return element


def normalize_surface_form(unit: SourceUnit, text: str | None = None) -> str:
    """Remove source analysis notation that is not part of the utterance."""
    normalized = unit.form if text is None else text
    if "Parentheses are printed optional material" in unit.form_notes:
        normalized = re.sub(r"\(([^()]*)\)", r"\1", normalized)
    normalized = CONSTITUENT_LABEL.sub("[", normalized)
    for mark in "[]【】" + SUBSCRIPTS:
        normalized = normalized.replace(mark, "")
    return " ".join(normalized.split())


def bracket_note(unit: SourceUnit) -> str:
    """What the book prints in brackets in this example; the brackets themselves
    are deleted from the FORM. Read from the reviewed form when it still has the
    brackets (the student restored 【 】 in p094l-e002/e003), else from the
    transcription (p045r-e002's reviewed words never showed them)."""
    text = unit.form if any(mark in unit.form for mark in "[]【】") else unit.transcribed_form
    published = normalize_surface_form(unit)
    notes = []
    for opening, closing, kind in BRACKET_PAIRS:
        label = r"(\s*[sₛ]\s+)?" if opening == "[" else "()"
        pattern = re.escape(opening) + label + "([^" + re.escape(opening + closing) + "]*)" + re.escape(closing)
        for subscript, span in re.findall(pattern, text):
            span = " ".join(span.split())
            # The note quotes the bracketed words; they must be the words published (a review
            # correction inside the brackets would otherwise be misquoted).
            if span not in published:
                raise ValueError(f"{unit.unit_id}: bracketed {span!r} is not in the published FORM {published!r}")
            span_kind = "square brackets with a subscript s, [ₛ ]" if subscript else kind
            notes.append(f"The book prints {span} in {span_kind}.")
    return " ".join(notes)


def without_old_bracket_notes(notes: str) -> str:
    for old in OLD_BRACKET_NOTES + (SUPERSEDED_BRACKET_NOTES if PRINT_NOTES else ()):
        notes = notes.replace(old, "")
    return " ".join(notes.split())


def sentence_equivalence_key(form: str) -> str:
    """Return a grouping key without source analysis separators."""
    return form.replace("-", "").replace("=", "")


def word_alignment(unit: SourceUnit) -> list[tuple[str, str]]:
    forms = normalize_surface_form(unit).split()
    if unit.reviewed_glosses is not None:
        glosses = list(unit.reviewed_glosses)
    elif unit.gloss_alignment == "unavailable":
        glosses = [""] * len(forms)
    elif unit.unit_id in WORD_GLOSS_OVERRIDES:
        glosses = list(WORD_GLOSS_OVERRIDES[unit.unit_id])
        _USED.setdefault("word_glosses", set()).add(unit.unit_id)
    else:
        glosses = unit.gloss.split()
    if len(forms) != len(glosses):
        raise ValueError(
            f"{unit.unit_id}: reviewed word alignment has {len(forms)} forms "
            f"but {len(glosses)} glosses"
        )
    return list(zip(forms, glosses, strict=True))


def split_segments(text: str) -> tuple[list[str], list[str]]:
    """Split `-` and `=` outside parenthetical gloss annotations."""
    parts: list[str] = []
    separators: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char in "(（":
            depth += 1
        elif char in ")）" and depth:
            depth -= 1
        if char in "-=" and depth == 0:
            parts.append("".join(current))
            separators.append(char)
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return parts, separators


def looks_like_grammatical_label(text: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Z0-9.]*", text))


def strip_morpheme_punctuation(text: str) -> str:
    return text.strip(MORPHEME_PUNCTUATION)


def is_infixed(form_parts: list[str], form_separators: list[str]) -> bool:
    """p-um-ukun: the infix -um- inside the root p-ukun."""
    return len(form_parts) >= 3 and form_separators[:2] == ["-", "-"] and form_parts[1] in INLINE_INFIXES


def has_inline_infix(form_parts: list[str], form_separators: list[str], gloss_count: int) -> bool:
    return len(form_parts) == gloss_count + 1 and is_infixed(form_parts, form_separators)


def word_tier_form(form_word: str) -> str:
    """The word FORM of a printed word: an infix in angle brackets (POL-014, see INLINE_INFIXES), p-um-ukun ->
    p<um>ukun, q-em-an=ti=iku -> q<em>an=ti=iku; any other word as printed."""
    parts, separators = split_segments(strip_morpheme_punctuation(form_word))
    parts = [strip_morpheme_punctuation(part) for part in parts]
    if not is_infixed(parts, separators):
        return form_word
    lead = len(form_word) - len(form_word.lstrip(MORPHEME_PUNCTUATION))
    printed = f"{parts[0]}-{parts[1]}-"
    if not form_word[lead:].startswith(printed):
        raise ValueError(f"infixed word {form_word!r} does not start with {printed!r}")
    return form_word[:lead] + f"{parts[0]}<{parts[1]}>" + form_word[lead + len(printed):]


def sentence_line(text: str) -> str:
    """A Kavalan sentence line with each infix in angle brackets, as its word FORM writes it: p-um-ukun ti-utay
    ti-tuyaw -> p<um>ukun ti-utay ti-tuyaw (maintainer, audit round 1, 2026-11-09: "the sentence line should change
    hyphens to <> for infixes")."""
    return " ".join(word_tier_form(word) for word in text.split())


def word_morpheme_count(unit_id: str, word_index: int, form_word: str) -> int:
    """The morphemes in a word's segmentation: its pieces, less one where two
    pieces are one morpheme, as for an infixed root (p-um-ukun: p-ukun and -um-)
    or a ruled circumfix (ta-miaoriq-an: ta-an and miaoriq)."""
    parts, separators = split_segments(strip_morpheme_punctuation(form_word))
    parts = [strip_morpheme_punctuation(part) for part in parts]
    if is_infixed(parts, separators) or (unit_id, word_index) in CIRCUMFIX_WORDS:
        return len(parts) - 1
    return len(parts)


def without_redundant_trailing_hyphen(unit_id: str, word_index: int, form_word: str, gloss_word: str) -> str:
    """A trailing hyphen on a gloss is deleted when, without it, the gloss has as
    many pieces as the word has morphemes (ruled 2026-11-07: "There are a number
    of trailing hyphens on glosses. These can be delete if the result is the
    number of morphemes matches the segmentation of the word."): 打-AF- under
    p-um-ukun becomes 打-AF, 處所格-苗栗- under ta-miaoriq-an becomes 處所格-苗栗.
    Any other trailing hyphen stays as printed."""
    if len(gloss_word) > 1 and gloss_word.endswith("-") and not gloss_word.endswith("--"):
        parts, _ = split_segments(gloss_word[:-1])
        if all(parts) and len(parts) == word_morpheme_count(unit_id, word_index, form_word):
            return gloss_word[:-1]
    return gloss_word


def circumfix_morphemes(
    unit_id: str, form_parts: list[str], form_separators: list[str], gloss_parts: list[str]
) -> list[tuple[str, str]]:
    """A ruled circumfix word (CIRCUMFIX_WORDS): ta-miaoriq-an under 處所格-苗栗 is
    ta-an 處所格 and miaoriq 苗栗; ta=paw-an-su under 處所格-家--你 is ta-an 處所格,
    paw 家 and su 你, as the circumfix option showed. The gloss has one piece for the
    circumfix; an empty slot left under -an is its second half for the morphemes.
    The word gloss is circumfix_word_gloss's."""
    if not (len(form_parts) >= 3 and form_parts[0] in CIRCUMFIX_PREFIXES and form_parts[2] == "an"
            and form_separators[1] == "-"):
        raise ValueError(f"{unit_id}: {form_parts} is listed in CIRCUMFIX_WORDS but is not ta/sa-root-an")
    glosses = list(gloss_parts)
    if len(glosses) == len(form_parts) and glosses[2] == "":
        del glosses[2]
    if len(glosses) != len(form_parts) - 1:
        raise ValueError(f"{unit_id}: circumfix word {form_parts} has glosses {gloss_parts}")
    glosses = [UNCLEAR if not part or part in UNKNOWN_GLOSSES else part for part in glosses]
    morphemes = [(f"{form_parts[0]}-an", glosses[0]), (form_parts[1], glosses[1])]
    for index in range(3, len(form_parts)):
        marker = "=" if form_separators[index - 1] == "=" else ""
        morphemes.append((marker + form_parts[index], glosses[index - 1]))
    return morphemes


def circumfix_word_gloss(gloss: str) -> str:
    """A ruled circumfix word's gloss without the empty slot the book prints under -an (see UNGLOSSED_LAST_PIECE's
    neighbour comment): 處所格-家--你 -> 處所格-家-你. A gloss with no such slot is returned as it is."""
    parts, separators = split_segments(gloss)
    if len(parts) < 4 or parts[2] != "":
        return gloss
    kept = parts[:2] + parts[3:]
    seps = separators[:1] + separators[2:]
    return kept[0] + "".join(sep + part for sep, part in zip(seps, kept[1:]))


def mark_unglossed(gloss: str) -> str:
    """Write <UNCLEAR/> into each leading or inner empty piece of a segmented
    gloss (POL-061): `-持續貌-說` becomes `<UNCLEAR/>-持續貌-說`. A trailing
    hyphen stays as printed (see split_morphemes)."""
    parts, separators = split_segments(gloss)
    if len(parts) == 1:
        return gloss
    def piece(part: str, last: bool) -> str:
        if part in UNKNOWN_GLOSSES:
            return UNCLEAR
        return part or ("" if last else UNCLEAR)
    out = piece(parts[0], False)
    for index, (separator, part) in enumerate(zip(separators, parts[1:]), start=1):
        out += separator + piece(part, index == len(parts) - 1)
    return out


def split_morphemes(
    unit: SourceUnit,
    word_index: int,
    form_word: str,
    gloss_word: str,
) -> list[tuple[str, str]]:
    override = MORPHEME_OVERRIDES.get((unit.unit_id, word_index))
    if override is not None:
        _USED.setdefault("morphemes", set()).add((unit.unit_id, word_index))
        return list(override)
    if not gloss_word:
        return []

    form_parts, form_separators = split_segments(strip_morpheme_punctuation(form_word))
    form_parts = [strip_morpheme_punctuation(part) for part in form_parts]
    gloss_parts, _ = split_segments(gloss_word)
    if any(not part for part in form_parts):
        return []
    if (unit.unit_id, word_index) in CIRCUMFIX_WORDS:
        return circumfix_morphemes(unit.unit_id, form_parts, form_separators, gloss_parts)
    if (len(gloss_parts) >= 3 and gloss_parts[2] == ""
            and has_inline_infix(form_parts, form_separators, len(gloss_parts) - 1)):
        # The book leaves the gloss slot after an infix's gloss empty: 打-AF- under p-um-ukun,
        # or 蓋-完成貌--PF-他 under s-n-angi-an-na. That slot is the rest of the infixed root,
        # not a morpheme of its own.
        del gloss_parts[2]
    elif len(gloss_parts) > 1 and gloss_parts[-1] == "":
        if has_inline_infix(form_parts, form_separators, len(gloss_parts) - 1):
            # A trailing empty slot on a longer infixed word (打-AF=我- under p-um-ukun=iku)
            # is the rest of the root too.
            gloss_parts = gloss_parts[:-1]
        else:
            # A trailing empty slot that is neither the rest of an infixed root nor the second
            # half of a ruled circumfix (CIRCUMFIX_WORDS): no ruling covers it, so no morphemes.
            # (None in today's data: the four ta-/sa-...-an words that had one are circumfixes.)
            return []
    # A leading or inner empty piece is a morpheme the book leaves unglossed (POL-061).
    gloss_parts = [UNCLEAR if not part or part in UNKNOWN_GLOSSES else part for part in gloss_parts]

    if len(form_parts) == len(gloss_parts):
        morphemes: list[tuple[str, str]] = []
        for index, (form_part, gloss_part) in enumerate(
            zip(form_parts, gloss_parts, strict=True)
        ):
            marker = "=" if index and form_separators[index - 1] == "=" else ""
            morphemes.append((f"{marker}{form_part}", gloss_part))
        return morphemes

    if not has_inline_infix(form_parts, form_separators, len(gloss_parts)):
        return []

    aligned_glosses = list(gloss_parts)
    if (
        len(aligned_glosses) >= 2
        and looks_like_grammatical_label(aligned_glosses[0])
        and not looks_like_grammatical_label(aligned_glosses[1])
    ):
        aligned_glosses[0], aligned_glosses[1] = (
            aligned_glosses[1],
            aligned_glosses[0],
        )

    morphemes = [
        (f"{form_parts[0]}-{form_parts[2]}", aligned_glosses[0]),
        (f"-{form_parts[1]}-", aligned_glosses[1]),
    ]
    for form_index, form_part in enumerate(form_parts[3:], start=3):
        separator = form_separators[form_index - 1]
        marker = "=" if separator == "=" else ""
        morphemes.append((f"{marker}{form_part}", aligned_glosses[form_index - 1]))
    return morphemes


def canonical_word_gloss(
    source_gloss: str, morphemes: list[tuple[str, str]]
) -> str:
    infix_index = next(
        (
            index
            for index, (form, _) in enumerate(morphemes)
            if re.fullmatch(r"-[^-]+-", form)
        ),
        None,
    )
    if infix_index != 1:
        return mark_unglossed(source_gloss)
    rendered = f"{morphemes[0][1]}<{morphemes[1][1]}>"
    for form, gloss in morphemes[2:]:
        rendered += ("=" if form.startswith("=") else "-") + gloss
    # A trailing mark the gloss still has is kept. A trailing hyphen whose deletion leaves as many pieces as the
    # word has morphemes never gets here: without_redundant_trailing_hyphen removes it first (ruled 2026-11-07).
    if source_gloss[-1:] in {"-", "="}:
        rendered += source_gloss[-1]
    return rendered


def unglossed_word_morphemes(form_word: str) -> list[tuple[str, str]]:
    """A word the book leaves unglossed inside a glossed sentence. Its gloss is
    <UNCLEAR/> (POL-061). Its morphemes are its printed pieces, each glossed
    <UNCLEAR/>: an unsegmented word gets one M, as every unsegmented word in the
    analysed line does (ruled 2026-10-17 for all corpora, on single Ms from the
    analysed line: "keep", with "This is obvious, right? That's the source saying
    it's monomorphemic."). His round-3 note (2026-11-07) is read as keeping this for
    a word the book or the student leaves unglossed; that reading is put to him in
    round 4."""
    parts, separators = split_segments(strip_morpheme_punctuation(form_word))
    return [
        (("=" if index and separators[index - 1] == "=" else "") + strip_morpheme_punctuation(part), UNCLEAR)
        for index, part in enumerate(parts)
        if strip_morpheme_punctuation(part)
    ]


def alternative_glosses_note(alternatives: list[tuple[str, bool]]) -> str:
    """The note listing other printings' glosses. Each gloss is (text, from_review):
    a gloss the student corrected lives in review_corrections.tsv, not in
    source_units.tsv, and the note says so."""
    def listing(glosses: list[str]) -> str:
        return " | ".join(as_note(gloss.translate(TO_FULL_WIDTH)) for gloss in glosses)
    ledger = [gloss for gloss, from_review in alternatives if not from_review]
    reviewed = [gloss for gloss, from_review in alternatives if from_review]
    parts = []
    if ledger:
        parts.append("Alternative printed glosses retained in source_units.tsv: " + listing(ledger))
    if reviewed:
        parts.append("Alternative printed glosses as corrected in the 2026-10 review (review_corrections.tsv): "
                     + listing(reviewed))
    return ". ".join(parts)


def word_gloss_notes(adjudication: list[dict[str, str]]) -> dict[tuple[str, int], str]:
    notes = {}
    for row in adjudication:
        if row["action"] == "add_word_gloss_note":
            kind, _, index = row["field"].partition(":")
            if kind != "word_gloss_note" or not index.isdigit():
                raise ValueError(f"{row['unit_id']}: add_word_gloss_note needs field word_gloss_note:<n>")
            notes[(row["unit_id"], int(index))] = row["value"]
    return notes


def add_word_tier(
    sentence: ET.Element,
    sentence_id: str,
    source_units: list[SourceUnit],
    gloss_notes: dict[tuple[str, int], str] | None = None,
) -> set[tuple[str, int]]:
    """Returns the (unit, word) keys whose gloss note was written."""
    status_order = {"aligned_morpheme": 0, "aligned_word": 1, "unavailable": 2}
    aligned_units = sorted(
        source_units, key=lambda item: (status_order[item.gloss_alignment], item.source_order)
    )
    unit = aligned_units[0]
    if sentence_id in WORDS_FROM_PRINTING:
        unit = next((item for item in source_units if item.unit_id == WORDS_FROM_PRINTING[sentence_id]), None)
        if unit is None:
            raise ValueError(f"{sentence_id}: {WORDS_FROM_PRINTING[sentence_id]} is not one of its printings")
        _USED.setdefault("printing", set()).add(sentence_id)
    aligned_words = word_alignment(unit)
    gloss_notes = gloss_notes or {}
    used_notes: set[tuple[str, int]] = set()

    for word_index, (form_word, gloss_word) in enumerate(aligned_words, start=1):
        word_id = f"{sentence_id}W{word_index}"
        word = ET.SubElement(sentence, "W", {"id": word_id})
        add_form(word, "original", word_tier_form(form_word))
        if (not gloss_word or gloss_word in UNKNOWN_GLOSSES) and unit.gloss_alignment != "unavailable":
            primary_morphemes = unglossed_word_morphemes(form_word)
            if (unit.unit_id, word_index) in NO_MORPHEME_WORDS:
                primary_morphemes = []
                _USED.setdefault("no_m", set()).add((unit.unit_id, word_index))
            rendered_gloss = UNCLEAR
        else:
            if (unit.unit_id, word_index) in UNGLOSSED_LAST_PIECE:
                if not gloss_word.endswith("-"):
                    raise ValueError(f"{unit.unit_id} word {word_index}: {gloss_word!r} has no empty last piece")
                gloss_word += UNCLEAR
                _USED.setdefault("last_piece", set()).add((unit.unit_id, word_index))
            gloss_word = without_redundant_trailing_hyphen(unit.unit_id, word_index, form_word, gloss_word)
            primary_morphemes = split_morphemes(unit, word_index, form_word, gloss_word)
            word_gloss = (circumfix_word_gloss(gloss_word) if (unit.unit_id, word_index) in CIRCUMFIX_WORDS
                          else gloss_word)
            rendered_gloss = canonical_word_gloss(word_gloss, primary_morphemes)
        word_translation = None
        if rendered_gloss:
            word_translation = add_translation(word, rendered_gloss)
            note = gloss_notes.get((unit.unit_id, word_index))
            if note:
                word_translation.set("notes", note)
                used_notes.add((unit.unit_id, word_index))
        alternate_word_glosses: list[tuple[str, bool]] = []
        for alternate_unit in source_units:
            if alternate_unit.unit_id == unit.unit_id:
                continue
            alternate_words = word_alignment(alternate_unit)
            alternate_form, alternate_gloss = alternate_words[word_index - 1]
            alternate_gloss = without_redundant_trailing_hyphen(
                alternate_unit.unit_id, word_index, alternate_form, alternate_gloss
            )
            alternate_morphemes = split_morphemes(
                alternate_unit, word_index, alternate_form, alternate_gloss
            )
            rendered_alternate = canonical_word_gloss(
                alternate_gloss, alternate_morphemes
            )
            # Compared as published (full-width parentheses), so a width difference is not an alternative.
            if (
                rendered_alternate
                and rendered_alternate.translate(TO_FULL_WIDTH) != rendered_gloss.translate(TO_FULL_WIDTH)
                and rendered_alternate.translate(TO_FULL_WIDTH)
                not in [gloss.translate(TO_FULL_WIDTH) for gloss, _ in alternate_word_glosses]
            ):
                alternate_word_glosses.append((rendered_alternate, "glosses" in alternate_unit.review_fields))
        if word_translation is not None and alternate_word_glosses:
            existing = word_translation.get("notes")
            word_translation.set(
                "notes",
                ((existing + " ") if existing else "") + alternative_glosses_note(alternate_word_glosses),
            )
        written_forms = [form for form, _ in primary_morphemes]
        if word_id in PROCLITIC_WORDS:
            if len(written_forms) < 2 or not written_forms[1].startswith("=") or written_forms[0].startswith("="):
                raise ValueError(f"{word_id}: {written_forms} is not a clitic before its word")
            written_forms[0], written_forms[1] = written_forms[0] + "=", written_forms[1][1:]
            _USED.setdefault("proclitic", set()).add(word_id)
        for morph_index, (form_part, gloss_part) in enumerate(
            primary_morphemes, start=1
        ):
            morph = ET.SubElement(word, "M", {"id": f"{word_id}M{morph_index}"})
            add_form(morph, "original", written_forms[morph_index - 1])
            morph_translation = add_translation(morph, gloss_part)
            alternate_morph_glosses: list[tuple[str, bool]] = []
            for alternate_unit in source_units:
                if alternate_unit.unit_id == unit.unit_id:
                    continue
                alternate_form, alternate_word = word_alignment(alternate_unit)[
                    word_index - 1
                ]
                alternate_word = without_redundant_trailing_hyphen(
                    alternate_unit.unit_id, word_index, alternate_form, alternate_word
                )
                alternate_parts = split_morphemes(
                    alternate_unit, word_index, alternate_form, alternate_word
                )
                if len(alternate_parts) != len(primary_morphemes):
                    continue
                if [part[0] for part in alternate_parts] != [
                    part[0] for part in primary_morphemes
                ]:
                    continue
                alternate_gloss = alternate_parts[morph_index - 1][1]
                if (
                    alternate_gloss.translate(TO_FULL_WIDTH) != gloss_part.translate(TO_FULL_WIDTH)
                    and alternate_gloss.translate(TO_FULL_WIDTH)
                    not in [gloss.translate(TO_FULL_WIDTH) for gloss, _ in alternate_morph_glosses]
                ):
                    alternate_morph_glosses.append((alternate_gloss, "glosses" in alternate_unit.review_fields))
            if alternate_morph_glosses:
                morph_translation.set("notes", alternative_glosses_note(alternate_morph_glosses))
    return used_notes


def sentence_id(unit: SourceUnit) -> str:
    return f"S-{unit.xml_unit_id}"


def unique_values(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def source_reference(unit: SourceUnit) -> str:
    return (
        f"PDF page {unit.pdf_page} {unit.side}, book page {unit.book_page}, "
        f"printed label {unit.printed_label}, source unit {unit.unit_id}"
    )


def add_word_variants(
    sentence: ET.Element,
    source_group: list[SourceUnit],
    decisions: dict[tuple[str, str], VariantDecision],
) -> set[tuple[str, str]]:
    """Each word_variant alternative of the group differs from the published words in exactly one word; that
    word gets one FORM kindOf="original" ver="alt" with the alternative's spelling, right after its base FORM. It
    carries no note: ver="alt" says what the decision's reason said (maintainer, round 5, 2026-11-08, on "The source
    prints ya and a as accepted alternatives.": "That's literally what ver="alt" means. why would you add that
    note?"). An alternative printed with more than one printing of the example is written once (as
    accepted_variants merges alternative sentences); one printing may not make an alternative a word variant while
    another makes it a sentence. Returns the decision keys used."""
    words = sentence.findall("W")
    published = [word.findtext("FORM") or "" for word in words]
    kinds: dict[str, set[str]] = {}
    planned: set[tuple[int, str]] = set()
    used: set[tuple[str, str]] = set()
    for item in source_group:
        for alternate in split_alternates(item.alternate_forms):
            normalized = normalize_surface_form(item, alternate)
            decision = decisions[(item.unit_id, normalized)]
            kinds.setdefault(normalized, set()).add(decision.decision)
            if decision.decision != WORD_VARIANT:
                continue
            spelled = [word_tier_form(word.translate(TO_ASCII)) for word in normalized.split()]
            differ = [index for index, (a, b) in enumerate(zip(published, spelled)) if a != b]
            if len(spelled) != len(published) or len(differ) != 1:
                raise ValueError(f"{item.unit_id}: word variant {normalized!r} is not one word of {published}")
            planned.add((differ[0], spelled[differ[0]]))
            used.add((item.unit_id, normalized))
    mixed = sorted(alternative for alternative, found in kinds.items() if WORD_VARIANT in found and len(found) > 1)
    if mixed:
        raise ValueError(f"{sentence.get('id')}: a word variant on one printing and not on another: {mixed}")
    for index, text in sorted(planned):
        word = words[index]
        base = word.find("FORM")
        variant = ET.Element("FORM", {"kindOf": "original", "ver": "alt"})
        set_text(variant, text)
        word.insert(list(word).index(base) + 1, variant)
    return used


def accepted_variants(
    source_group: list[SourceUnit],
    decisions: dict[tuple[str, str], VariantDecision],
) -> list[tuple[str, str, list[VariantDecision]]]:
    variants: dict[tuple[str, str], list[VariantDecision]] = {}
    for unit in source_group:
        for alternate in split_alternates(unit.alternate_forms):
            normalized = normalize_surface_form(unit, alternate)
            decision = decisions[(unit.unit_id, normalized)]
            if decision.decision == "include":
                variants.setdefault(
                    (decision.alternate_form, decision.translation_zho), []
                ).append(decision)
    return [(form, translation, rows) for (form, translation), rows in variants.items()]


def paired_variant_translations(
    unit: SourceUnit,
    decisions: dict[tuple[str, str], VariantDecision],
) -> set[str]:
    return {
        decisions[(unit.unit_id, normalize_surface_form(unit, alternate))].translation_zho
        for alternate in split_alternates(unit.alternate_forms)
        if decisions[(unit.unit_id, normalize_surface_form(unit, alternate))].decision == "include"
    }


def form_notes_of(unit: SourceUnit, used_replacements: set[str], removed_notes: set[str] | None = None) -> str:
    """The transcription's notes on a printing, less the kinds now untrue: the old
    bracket notes, the note on a printed trailing hyphen the build now deletes, and
    (where the handwriting is now followed) the notes saying it is excluded."""
    notes = without_old_bracket_notes(unit.form_notes)
    if unit.unit_id in DROPPED_TRANSCRIPTION_NOTES:
        dropped_note = DROPPED_TRANSCRIPTION_NOTES[unit.unit_id][0]
        if dropped_note not in notes:
            raise ValueError(f"{unit.unit_id}: the note to drop is not in its form_notes")
        notes = " ".join(notes.replace(dropped_note, "").split())
        _USED.setdefault("dropped_form_note", set()).add(unit.unit_id)
    for old in TRAILING_HYPHEN_NOTES:
        if old in notes:
            notes = " ".join(notes.replace(old, "").split())
            if removed_notes is not None:
                removed_notes.add(old)
    replacement = HANDWRITING_NOTE_REPLACEMENTS.get(unit.unit_id)
    if replacement is not None and unit.form != unit.transcribed_form:
        old, new = replacement
        if old not in notes:
            raise ValueError(f"{unit.unit_id}: the handwriting note to replace is not in its form_notes")
        notes = " ".join(notes.replace(old, new if PRINT_NOTES else "").split())
        used_replacements.add(unit.unit_id)
    return notes


def build_tree(
    units: list[SourceUnit] | None = None,
    variant_decisions: dict[tuple[str, str], VariantDecision] | None = None,
    review: bool = True,
) -> ET.ElementTree:
    """review=False builds the transcription alone, without the student review's
    data: no corrections, added examples, student notes or adjudication rows (pass
    units loaded with corrections={} and additions=None). The build rules the
    maintainer ruled (final punctuation, circumfixes, trailing hyphens, BOOK_NOTES)
    apply to it too."""
    source_units = units if units is not None else load_source_units()
    decisions = variant_decisions or load_variant_decisions(source_units)
    validate_coverage(source_units)
    adjudication = load_review_adjudication() if review else []
    review_notes = load_review_notes(adjudication=adjudication) if review else {}
    gloss_notes = word_gloss_notes(adjudication)
    dropped = {(row["unit_id"], row["value"]) for row in adjudication
               if row["action"] == "drop_alternate_translation"}
    used_drops: set[tuple[str, str]] = set()
    used_gloss_notes: set[tuple[str, int]] = set()
    used_replacements: set[str] = set()
    removed_notes: set[str] = set()
    used_book_notes: set[str] = set()
    song_lines_seen: set[str] = set()
    used_word_variants: set[tuple[str, str]] = set()
    _USED.clear()
    root = ET.Element("TEXT", TEXT_ATTRIBUTES)

    for source_group in group_source_units(source_units):
        unit = source_group[0]
        sid = sentence_id(unit)
        source = "; ".join(source_reference(item) for item in source_group)
        sentence = ET.SubElement(root, "S", {"id": sid, "source": source})
        # The base translation is the first printing's that has one; a sentence has
        # none only if no printing has one and each says so.
        translated = [item for item in source_group if item.translation_zho]
        no_translation = not translated
        if no_translation and any(item.translation_notes != NO_PRINTED_TRANSLATION for item in source_group):
            raise ValueError(f"{sid}: no printing has a translation, and not every printing says none is printed")
        # Every note the student wrote goes on its sentence, verbatim; where one
        # sentence stands for several printings, each note names its printing.
        notes_from_review = [
            (f"{REVIEW_NOTE_PREFIX}, {item.unit_id}: " if len(source_group) > 1
             else f"{REVIEW_NOTE_PREFIX}: ") + review_notes[item.unit_id]
            for item in source_group if item.unit_id in review_notes
        ]
        book_notes = [BOOK_NOTES[item.unit_id] for item in source_group if item.unit_id in BOOK_NOTES]
        used_book_notes |= {item.unit_id for item in source_group if item.unit_id in BOOK_NOTES}
        form_notes = " ".join(unique_values(
            [form_notes_of(item, used_replacements, removed_notes) for item in source_group]
            + ([bracket_note(item) for item in source_group] if PRINT_NOTES else [])
            + book_notes
            + ([NO_PRINTED_TRANSLATION] if no_translation else [])
            + notes_from_review
        ))

        def ended(text: str, item: SourceUnit) -> str:
            song_line = item.unit_id in SONG_LINE_COMMA_UNITS
            if song_line and text.translate(TO_FULL_WIDTH).endswith("，"):
                song_lines_seen.add(item.unit_id)
            return end_translation(text, song_line=song_line)

        base_translation = ended(translated[0].translation_zho, translated[0]) if translated else ""
        primary_form = normalize_surface_form(unit)
        add_form(sentence, "original", end_sentence(sentence_line(primary_form), base_translation), form_notes)

        seen_zho: set[str] = set()
        if translated:
            base = translated[0]
            translation_notes = base.translation_notes
            if base.unit_id in DROPPED_TRANSCRIPTION_NOTES:
                if translation_notes != DROPPED_TRANSCRIPTION_NOTES[base.unit_id][1]:
                    raise ValueError(f"{base.unit_id}: the translation note to drop is not its translation_notes")
                translation_notes = ""
                _USED.setdefault("dropped_translation_note", set()).add(base.unit_id)
            add_translation(sentence, base_translation, notes=translation_notes)
            seen_zho.add(base_translation)
        for item in source_group:
            paired_translations = paired_variant_translations(item, decisions)
            translations = [item.translation_zho]
            translations.extend(split_alternates(item.alternate_translations_zho))
            for alternate in translations:
                # Compared as published, so a printing that differs only by a final 。 adds nothing.
                if not alternate or ended(alternate, item) in seen_zho or alternate in paired_translations:
                    continue
                if (item.unit_id, alternate) in dropped:
                    used_drops.add((item.unit_id, alternate))
                    continue
                seen_zho.add(ended(alternate, item))
                if item.added:
                    notes = item.translation_notes
                else:
                    notes = f"Printed translation in source unit {item.unit_id}."
                    if item.translation_notes:
                        notes = f"{notes} {item.translation_notes}"
                add_translation(
                    sentence, ended(alternate, item), alternate=True, notes=notes
                )
        for english_index, translation in enumerate(
            unique_values([item.translation_eng for item in source_group])
        ):
            add_translation(
                sentence,
                translation,
                language="eng",
                alternate=english_index > 0,
            )
        used_gloss_notes |= add_word_tier(sentence, sid, source_group, gloss_notes)
        used_word_variants |= add_word_variants(sentence, source_group, decisions)

        for index, (form, translation, variant_rows) in enumerate(
            accepted_variants(source_group, decisions), start=1
        ):
            suffixes = {row.id_suffix for row in variant_rows}
            if len(suffixes) != 1 or not next(iter(suffixes)):
                raise ValueError(f"{sid}: alternative {form!r} needs one id_suffix, has {sorted(suffixes)}")
            variant_id = f"{sid}-{suffixes.pop()}"
            variant_sources = [
                source_reference(next(item for item in source_group if item.unit_id == row.unit_id))
                for row in variant_rows
            ]
            variant_sentence = ET.SubElement(
                root,
                "S",
                {
                    "id": variant_id,
                    "source": "; ".join(variant_sources) + f"; accepted source alternative {index}",
                },
            )
            reasons = " ".join(unique_values([row.note for row in variant_rows]))
            variant_unit = next(item for item in source_group if item.unit_id == variant_rows[0].unit_id)
            variant_translation = ended(translation, variant_unit)
            add_form(variant_sentence, "original", end_sentence(sentence_line(form), variant_translation), reasons)
            add_translation(variant_sentence, variant_translation)
            # ALTERNATIVE_WORD_GLOSSES: the word tier, from the gloss line every printing gives it.
            gloss_lines = {row.glosses for row in variant_rows}
            if len(gloss_lines) != 1:
                raise ValueError(f"{variant_id}: its printings give different glosses {sorted(gloss_lines)}")
            gloss_line = gloss_lines.pop()
            if gloss_line:
                reading = replace(variant_unit, unit_id=f"{variant_unit.unit_id}-alt{index:02d}", form=form,
                                  alternate_forms="", reviewed_glosses=tuple(gloss_line.split()), review_fields=())
                add_word_tier(variant_sentence, variant_id, [reading])

    # Every ruling keyed to a word or sentence must have done something; a stale one is an error.
    ids = [s.get("id") for s in root.findall("S")]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate sentence ids")
    expected_use = {
        "printing": set(WORDS_FROM_PRINTING),
        "proclitic": set(PROCLITIC_WORDS),
        "no_m": set(NO_MORPHEME_WORDS) if review else set(),   # in the transcription alone, paqenanum is not there
        "last_piece": set(UNGLOSSED_LAST_PIECE),
        "dropped_form_note": set(DROPPED_TRANSCRIPTION_NOTES),
        "dropped_translation_note": set(DROPPED_TRANSCRIPTION_NOTES),
        # Rows for examples this build loads (an example added after review is not in the transcription alone).
        "word_glosses": set(WORD_GLOSS_OVERRIDES) & {unit.unit_id for unit in source_units},
        "morphemes": {key for key in MORPHEME_OVERRIDES if key[0] in {unit.unit_id for unit in source_units}},
    }
    # A gloss or morpheme row must name an example that exists, in the transcription or among the added examples.
    known = set()
    for path in (SOURCE_UNITS, SOURCE_ADDITIONS):
        with path.open(encoding="utf-8", newline="") as handle:
            known |= {row["unit_id"] for row in csv.DictReader(handle, delimiter="\t")}
    unknown = sorted(set(WORD_GLOSS_OVERRIDES) - known) + sorted(str(key) for key in MORPHEME_OVERRIDES if key[0] not in known)
    if unknown:
        raise ValueError(f"gloss or morpheme rows for examples that do not exist: {unknown}")
    # A gloss row also decides what is published when the student corrected only the example's words: her correction
    # is applied with the row's glosses when the units are loaded, before this build starts counting.
    _USED.setdefault("word_glosses", set()).update(
        unit.unit_id for unit in source_units if unit.unit_id in WORD_GLOSS_OVERRIDES
        and unit.reviewed_glosses is not None and "glosses" not in unit.review_fields)
    for kind, expected in expected_use.items():
        if expected - _USED.get(kind, set()):
            raise ValueError(f"{kind} rulings that changed nothing: {sorted(expected - _USED.get(kind, set()))}")
    # Every adjudication row must have done something; a stale ruling is an error.
    unused_word_variants = {key for key, row in decisions.items() if row.decision == WORD_VARIANT} - used_word_variants
    if unused_word_variants:
        raise ValueError(f"word_variant decisions that wrote nothing: {sorted(unused_word_variants)}")
    if dropped - used_drops:
        raise ValueError(f"adjudication drops translations that are not printed: {sorted(dropped - used_drops)}")
    if set(gloss_notes) - used_gloss_notes:
        raise ValueError(f"adjudication notes words that do not exist: {sorted(set(gloss_notes) - used_gloss_notes)}")
    if SONG_LINE_COMMA_UNITS - song_lines_seen:
        raise ValueError(f"song lines that no longer end in a comma: {sorted(SONG_LINE_COMMA_UNITS - song_lines_seen)}")
    if set(TRAILING_HYPHEN_NOTES) - removed_notes:
        raise ValueError(f"trailing-hyphen notes to remove that no printing has: "
                         f"{sorted(set(TRAILING_HYPHEN_NOTES) - removed_notes)}")
    if set(BOOK_NOTES) - used_book_notes:
        raise ValueError(f"book notes for units that are not included: {sorted(set(BOOK_NOTES) - used_book_notes)}")
    for unit_id, index in sorted(CIRCUMFIX_WORDS):
        word = root.find(f"S/W[@id='S-{unit_id}W{index}']")
        if word is None or (word.findtext("M/FORM") or "") not in {f"{prefix}-an" for prefix in CIRCUMFIX_PREFIXES}:
            raise ValueError(f"CIRCUMFIX_WORDS lists {unit_id} word {index}, which has no circumfix morpheme")
    if review and set(HANDWRITING_NOTE_REPLACEMENTS) != used_replacements:
        raise ValueError(f"handwriting notes listed for units whose handwriting is not followed: "
                         f"{sorted(set(HANDWRITING_NOTE_REPLACEMENTS) - used_replacements)}")
    known = {unit.unit_id for unit in source_units if unit.decision == "include"}
    if set(review_notes) - known:
        raise ValueError(f"review notes for units that are not included: {sorted(set(review_notes) - known)[:5]}")
    return ET.ElementTree(root)


def _mixed_text(value: str | None) -> str | None:
    """Text inside an element that holds <UNCLEAR/>: whitespace with a line break is
    indentation (ours, or add_phonology's pretty-printing) and is dropped; any other
    text, including a plain space between two <UNCLEAR/>, is content and is kept."""
    if value is not None and not value.strip() and "\n" in value:
        return None
    return value


def serialize(tree: ET.ElementTree) -> str:
    root = tree.getroot()
    # ET.indent would overwrite the whitespace of mixed content, so a gloss such as
    # <UNCLEAR/>-你 or "qan <UNCLEAR/> <UNCLEAR/>" is saved first and restored after it.
    mixed = [(element, _mixed_text(element.text), [_mixed_text(child.tail) for child in element])
             for element in root.iter() if element.find("UNCLEAR") is not None]
    ET.indent(root, space="  ")
    for element, text, tails in mixed:
        element.text = text
        for child, tail in zip(element, tails):
            child.tail = tail
    body = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    return f'<?xml version="1.0" ?>\n{body}\n'


def render() -> str:
    return serialize(build_tree())


def source_stage_from_generated(path: Path = OUT_XML) -> str:
    """The generated XML minus what the shared tools add after this script: PHON (add_phonology.py) and the
    standard FORM tier (standardize.py)."""
    tree = ET.parse(path)
    for parent in tree.getroot().iter():
        for child in list(parent):
            if child.tag == "PHON" or (child.tag == "FORM" and child.get("kindOf") == "standard"):
                parent.remove(child)
    return serialize(tree)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated XML differs from a fresh source-stage build")
    parser.add_argument("--stats", action="store_true", help="print reviewed-ledger and output counts")
    args = parser.parse_args()

    units = load_source_units()
    xml = serialize(build_tree(units))
    if args.check:
        if not OUT_XML.exists() or source_stage_from_generated() != xml:
            print(f"stale generated XML: {OUT_XML}", file=sys.stderr)
            return 1
    else:
        OUT_XML.parent.mkdir(parents=True, exist_ok=True)
        OUT_XML.write_text(xml, encoding="utf-8")
        print(f"wrote {OUT_XML}")

    if args.stats:
        included = [unit for unit in units if unit.decision == "include"]
        groups = group_source_units(units)
        decisions = load_variant_decisions(units)
        variants = sum(len(accepted_variants(group, decisions)) for group in groups)
        aligned = [
            group for group in groups if any(word_alignment(unit) for unit in group)
        ]
        print(f"reviewed source units: {len(units)}")
        print(f"included source occurrences: {len(included)}")
        print(f"emitted primary XML sentences: {len(groups)}")
        print(f"emitted alternative XML sentences: {variants}")
        print(f"word-aligned XML sentences: {len(aligned)}")
        print(f"coverage-only vocabulary entries: {sum(unit.unit_type == 'vocabulary_entry' for unit in units)}")
        corrections = load_review_corrections()
        if corrections:
            applied = adjudicate_corrections(corrections, load_review_adjudication())
            print(f"student review corrections: {sum(map(len, corrections.values()))} fields across "
                  f"{len(corrections)} units; applied as ruled: {sum(map(len, applied.values()))} fields "
                  f"across {len(applied)} units")
        print(f"examples added after review: {sum(unit.added for unit in units)}")
        print(f"maintainer rulings in review_adjudication.tsv: {len(load_review_adjudication())}")
        print(f"student notes published: {len(load_review_notes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
