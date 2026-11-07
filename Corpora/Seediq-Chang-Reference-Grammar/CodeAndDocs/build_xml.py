#!/usr/bin/env python3
"""Build canonical FormosanBank XML from the reviewed source inventory."""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "CodeAndDocs" / "source_inventory.tsv"
OUT_DIR = ROOT / "XML" / "Seediq"
OUT_XML = OUT_DIR / "chang-2000-seediq-reference-grammar.xml"
ACCEPTED_TSV = ROOT / "CodeAndDocs" / "extracted_examples.tsv"
REJECTED_TSV = ROOT / "CodeAndDocs" / "rejected_candidates.tsv"
DEDUP_TSV = ROOT / "CodeAndDocs" / "deduplicated_variants.tsv"
CHAPTER5_TSV = ROOT / "CodeAndDocs" / "chapter5_inventory.tsv"
CORRECTIONS_TSV = ROOT / "CodeAndDocs" / "review_corrections.tsv"
XML_NOTES_TSV = ROOT / "CodeAndDocs" / "review_xml_notes.tsv"
OUT_XML_LONG = OUT_DIR / "chang-2000-seediq-long-texts.xml"

# The only subscript the source uses: a coindexation mark tying a bound pronoun
# to its antecedent (printed page 80 / PDF 96).  It is the linguist's apparatus,
# not Seediq spelling -- the same class of thing as the focus labels (受事焦點)
# this build already leaves out of the FORM, and like them it is recoverable
# from the morphosyntactic gloss.  It is dropped at intake and recorded nowhere
# (maintainer, 2026-09-11).  Keeping it made yaku and yakuᵢ distinct tokens in
# every count and attestation dictionary, and forced add_phonology to emit its
# unmapped-letter marker '*' (POL-003).
COINDEX_MARKS = "\u1d62"

# POL-017: '*(X)' and '(*X)' are opposites, not spellings of one another.
_FORBIDDEN_IN_PARENS = re.compile(r"\(\*([^)]*)\)")
_OBLIGATORY_IN_PARENS = re.compile(r"\*\(([^)]*)\)")
SOURCE_PDF_SHA256 = "81b2a4a109c2151b6bc9f8dc09f882a4e4f2996ef05bf5b9692df15f933f355e"

# Records which corrections actually landed, so an orphan can be reported
# rather than silently ignored.
_CORRECTIONS_APPLIED: set = set()

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


@dataclass(frozen=True)
class SourceRecord:
    record_id: str
    source_locator: str
    form: str
    gloss: str
    translation: str
    pairs: tuple[tuple[str, str], ...]
    review_notes: str
    # printed word -> (base, variant): two readings of one word published as
    # one S with a ver="alt" FORM (POL-028); see word_variants.tsv.
    word_variants: tuple[tuple[str, tuple[str, str]], ...] = ()


@dataclass
class Variant:
    source: SourceRecord
    variant_number: int
    pairs: tuple[tuple[str, str], ...]
    translation: str
    alternate_translations: tuple[str, ...]
    # Other variants whose published FORM was identical to this one and which
    # were therefore merged into it (POL-022).  Their locators ride along in
    # S/@source so no provenance is lost.
    merged: list["Variant"] = field(default_factory=list)
    # Translations carried over from merged duplicates. Chang often gives the
    # same sentence a slightly different Mandarin rendering in a later chapter;
    # collapsing the sentences must not throw the other rendering away, so it
    # is published as a same-language alternate (TRANSL/@ver="alt"), which is
    # exactly what that attribute is for.
    merged_translations: list[str] = field(default_factory=list)
    sentence_id: str = ""

    @property
    def form(self) -> str:
        return " ".join(word for word, _ in self.pairs)

    @property
    def gloss(self) -> str:
        return " ".join(gloss for _, gloss in self.pairs)

    @property
    def source_locators(self) -> str:
        seen = [self.source.source_locator]
        seen += [other.source.source_locator for other in self.merged]
        return "; ".join(dict.fromkeys(seen))


def translation_key(text: str) -> str:
    """A translation stripped to its content, for deciding whether two renderings
    of the same sentence actually differ.

    Chang's Mandarin renderings of a repeated example often differ in something
    real -- an aspect 了, a progressive 在, a cleft 是 -- and those are worth
    keeping as alternates. A difference of only spacing or a trailing comma is
    not, and publishing it as an alternate reading would be noise.
    """
    return re.sub(r"[\s，。、！？,.!?]+", "", text)


# Records whose published translations are written out by hand rather than
# taken from the inventory: an alternation whose translation differs by reading,
# or a source translation that needed restating. Kept as data (POL-039) in
# translation_readings.tsv: a row with a trigger word applies to the reading that
# contains that word; a row without one gives the record's primary translation
# and its alternates. A reviewed translation for one of these records cannot be
# overlaid mechanically, so load_review_corrections refuses it.
TRANSLATION_READINGS_TSV = ROOT / "CodeAndDocs" / "translation_readings.tsv"


def _load_translation_readings():
    by_trigger: dict[str, tuple[tuple[str, str], ...]] = {}
    fixed: dict[str, tuple[str, tuple[str, ...]]] = {}
    with TRANSLATION_READINGS_TSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["trigger_word"]:
                by_trigger[row["record_id"]] = by_trigger.get(row["record_id"], ()) + (
                    (row["trigger_word"], row["translation"]),)
            else:
                alternates = tuple(json.loads(row["alternate_translations"] or "[]"))
                fixed[row["record_id"]] = (row["translation"], alternates)
    return by_trigger, fixed


_TRANSLATION_BY_TRIGGER, _TRANSLATION_FIXED = _load_translation_readings()
HAND_WRITTEN_TRANSLATIONS = frozenset(_TRANSLATION_BY_TRIGGER) | frozenset(_TRANSLATION_FIXED)


# Alternatives the source writes with a slash that are two readings of one word,
# not two words: published as one S, the second reading a ver="alt" FORM on the
# S, the W and the M (POL-028). Which slashes are variants is a ruling about the
# source, so it is data, per record (word_variants.tsv); every other slash
# still gives one S per option (POL-027).
WORD_VARIANTS_TSV = ROOT / "CodeAndDocs" / "word_variants.tsv"


def _load_word_variants() -> dict[str, dict[str, tuple[str, str]]]:
    out: dict[str, dict[str, tuple[str, str]]] = {}
    with WORD_VARIANTS_TSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if _SEGMENTATION_MARKS.findall(row["base"]) != _SEGMENTATION_MARKS.findall(
                    row["variant"]):
                # A reading with a different morpheme segmentation is a separate
                # S, never a variant (POL-028 as amended 2026-10-15).
                raise RuntimeError(f"{row['record_id']}: {row['base']!r} and "
                                   f"{row['variant']!r} differ in segmentation")
            out.setdefault(row["record_id"], {})[row["printed"]] = (
                row["base"], row["variant"])
    return out


_SEGMENTATION_MARKS = re.compile(r"[-=<>]")
WORD_VARIANTS = _load_word_variants()


# A gloss the book prints once under a slash pair, given per reading where the
# shared gloss does not fit one of them (R193: AF-在 under m-enaq/gaga; bare gaga
# has no AF). Ruled per record, so it is data (reading_glosses.tsv); the printed
# word and gloss must still match, or the row is stale and the build stops.
READING_GLOSSES_TSV = ROOT / "CodeAndDocs" / "reading_glosses.tsv"


def _load_reading_glosses() -> dict[tuple[str, str], tuple[str, str]]:
    with READING_GLOSSES_TSV.open(encoding="utf-8", newline="") as handle:
        return {(row["record_id"], row["printed_word"]): (row["printed_gloss"],
                                                          row["gloss_per_reading"])
                for row in csv.DictReader(handle, delimiter="\t")}


READING_GLOSSES = _load_reading_glosses()


# A suffix the book prints once, on the last alternative of a slash, that
# belongs to every alternative: laqi/sapah-mu is laqi-mu / sapah-mu (R070,
# ruled 2026-10-16). Per record, so data (slash_scope.tsv); a stale row stops
# the build.
SLASH_SCOPE_TSV = ROOT / "CodeAndDocs" / "slash_scope.tsv"


def _load_slash_scope() -> dict[tuple[str, str], tuple[str, str, str]]:
    with SLASH_SCOPE_TSV.open(encoding="utf-8", newline="") as handle:
        return {(row["record_id"], row["printed_word"]):
                (row["printed_gloss"], row["word"], row["gloss"])
                for row in csv.DictReader(handle, delimiter="\t")}


SLASH_SCOPE = _load_slash_scope()


def load_review_corrections() -> dict[str, dict[str, tuple[str, str]]]:
    """Reviewed corrections: record id -> field -> (was, now).

    Written by apply_review.py from the student review page. `words` and
    `glosses` hold the whole row, space-joined (no token contains a space);
    `translation` holds the free translation. They sit in their own file rather
    than being folded back into the inventories, so "what the transcription pass
    read" and "what review corrected" stay legible as two separate things.
    """
    if not CORRECTIONS_TSV.exists():
        return {}
    out: dict[str, dict[str, tuple[str, str]]] = defaultdict(dict)
    with CORRECTIONS_TSV.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["field"] not in {"words", "glosses", "translation"}:
                raise RuntimeError(f"Unknown review field {row['field']!r} "
                                   f"for {row['record_id']}")
            out[row["record_id"]][row["field"]] = (row["was"], row["now"])
    for record_id, fields in out.items():
        if "translation" in fields and record_id in HAND_WRITTEN_TRANSLATIONS:
            raise RuntimeError(
                f"{record_id}: a reviewed translation cannot be applied, because "
                "this record's published translations are written out by hand in "
                "translations_for(). Edit them there and drop the correction."
            )
    return dict(out)


def correct_row(row: dict[str, str],
                corrections: dict[str, dict[str, tuple[str, str]]],
                applied: set) -> dict[str, str]:
    """Overlay one record's reviewed words, glosses and translation.

    Applied to the raw inventory row, before any cleaning, because raw is what
    the reviewer was shown. A correction whose `was` no longer matches the
    inventory is a stale review -- the transcription moved under it -- and is
    refused rather than applied to whatever is there now.
    """
    fields = corrections.get(row["record_id"])
    if not fields:
        return row
    pairs = json.loads(row["word_gloss_json"])
    current = {
        "words": " ".join(word for word, _ in pairs),
        "glosses": " ".join(gloss for _, gloss in pairs),
        "translation": row["translation"],
    }
    corrected = dict(current)
    for field, (was, now) in fields.items():
        if was != current[field]:
            raise RuntimeError(
                f"Stale review correction for {row['record_id']} {field}: the "
                f"review was against {was!r}, the inventory now has "
                f"{current[field]!r}. Re-export and re-review rather than "
                "applying it."
            )
        corrected[field] = now
    words = corrected["words"].split()
    glosses = corrected["glosses"].split()
    if len(words) != len(glosses):
        raise RuntimeError(
            f"Review correction for {row['record_id']} leaves {len(words)} words "
            f"but {len(glosses)} glosses; every word needs a gloss box (∅ if none is printed)."
        )
    applied.add(row["record_id"])
    out = dict(row)
    out["word_gloss_json"] = json.dumps(list(map(list, zip(words, glosses))),
                                        ensure_ascii=False)
    out["form"] = corrected["words"]
    if "glosses" in fields:
        out["gloss"] = corrected["glosses"]
    out["translation"] = corrected["translation"]
    return out


# Square and lenticular brackets in the Seediq line and the free translation mark
# an embedded clause ([m-un-ekan ido], p. 79) or highlighted words (【wada ...】,
# p. 135); they are notation, not text. Ruled 2026-10-15: remove them, never turn
# them into parentheses -- which is what the shared cleaner would do, and
# parentheses mean optional material here. So this runs on the raw row, before
# the cleaner and before anything else reads the words. The gloss-line brackets
# that delimit an example are a different thing, handled in transcribe_chapter5.
TEXT_BRACKETS = str.maketrans("", "", "[]［］【】")


def strip_text_brackets(row: dict[str, str]) -> dict[str, str]:
    pairs = json.loads(row["word_gloss_json"])
    words = [word.translate(TEXT_BRACKETS) for word, _ in pairs]
    if any(not word for word in words):
        raise RuntimeError(f"{row['record_id']}: a word is nothing but brackets")
    out = dict(row)
    out["word_gloss_json"] = json.dumps(
        [[word, gloss] for word, (_, gloss) in zip(words, pairs)], ensure_ascii=False)
    out["form"] = row["form"].translate(TEXT_BRACKETS)
    out["translation"] = row["translation"].translate(TEXT_BRACKETS)
    return out


# Parentheses are standardized (ruled 2026-10-14): full-width in the Chinese glosses
# and translations, ASCII in the Seediq. The source mixes both widths.
TO_FULL_WIDTH = str.maketrans("()", "（）")
TO_ASCII = str.maketrans("（）", "()")


def standardize_parentheses(row: dict[str, str]) -> dict[str, str]:
    pairs = [[word.translate(TO_ASCII), gloss.translate(TO_FULL_WIDTH)]
             for word, gloss in json.loads(row["word_gloss_json"])]
    out = dict(row)
    out["word_gloss_json"] = json.dumps(pairs, ensure_ascii=False)
    out["form"] = row["form"].translate(TO_ASCII)
    out["gloss"] = row["gloss"].translate(TO_FULL_WIDTH)
    out["translation"] = row["translation"].translate(TO_FULL_WIDTH)
    return out


def strip_coindex(text: str) -> str:
    """Remove coindexation subscripts. See COINDEX_MARKS."""
    return text.translate({ord(mark): None for mark in COINDEX_MARKS})


def resolve_starred_parens(word: str, gloss: str) -> tuple[str, str, bool]:
    """POL-017. The two starred-parenthesis notations mean opposite things.

    ``*(X)`` marks X **obligatory**: the sentence is ungrammatical *without* X,
    so X stays and loses only its star.  ``(*X)`` marks X **forbidden**: X must
    not appear at all.  Handling them alike published an ungrammatical sentence
    in NTU Rukai (``*(malra)``), and in this corpus it published R173 and R174
    as ``tena m-ekan ido ka yaku`` -- precisely the string the source stars --
    while losing both real examples.

    Returns ``(word, gloss, keep)``; ``keep`` is False when the whole token was
    forbidden and the word drops out with its gloss.
    """
    if _FORBIDDEN_IN_PARENS.search(word):
        remainder = _FORBIDDEN_IN_PARENS.sub("", word).strip("- ")
        if not remainder:
            return "", "", False
        return remainder, gloss, True
    if _OBLIGATORY_IN_PARENS.search(word):
        return _OBLIGATORY_IN_PARENS.sub(r"\1", word), gloss, True
    return word, gloss, True


def read_inventory() -> list[dict[str, str]]:
    with INVENTORY.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 353:
        raise RuntimeError(f"Expected 353 reviewed inventory rows, found {len(rows)}")
    if any(row["decision"] not in {"include", "exclude"} for row in rows):
        raise RuntimeError(
            "Every source inventory row must have an include/exclude decision"
        )
    return rows


def source_records(rows: list[dict[str, str]]) -> list[SourceRecord]:
    corrections = load_review_corrections()
    applied: set = set()
    records: list[SourceRecord] = []
    for row in rows:
        if row["decision"] != "include":
            continue
        row = correct_row(row, corrections, applied)
        row = standardize_parentheses(strip_text_brackets(row))
        pairs = tuple(
            (strip_coindex(word), strip_coindex(gloss))
            for word, gloss in json.loads(row["word_gloss_json"])
        )
        pairs = apply_reading_glosses(row["record_id"], apply_slash_scope(row["record_id"], pairs))
        if not pairs or len(pairs) != len(row["form"].split()):
            raise RuntimeError(f"Incomplete word alignment at {row['record_id']}")
        records.append(
            SourceRecord(
                record_id=row["record_id"],
                source_locator=row["source_locator"],
                form=strip_coindex(row["form"]),
                gloss=strip_coindex(row["gloss"]),
                translation=row["translation"],
                pairs=pairs,
                review_notes=row["review_notes"],
                word_variants=tuple(WORD_VARIANTS.get(row["record_id"], {}).items()),
            )
        )
    _CORRECTIONS_APPLIED.update(applied)
    if set(SLASH_SCOPE) - _APPLIED_SLASH_SCOPE:
        raise RuntimeError("slash_scope.tsv rows match no printed word: "
                           f"{sorted(set(SLASH_SCOPE) - _APPLIED_SLASH_SCOPE)}")
    if set(READING_GLOSSES) - _APPLIED_READING_GLOSSES:
        raise RuntimeError("reading_glosses.tsv rows match no printed word: "
                           f"{sorted(set(READING_GLOSSES) - _APPLIED_READING_GLOSSES)}")
    unused = set(WORD_VARIANTS) - {record.record_id for record in records}
    unused |= {
        f"{record.record_id}:{printed}"
        for record in records
        for printed, _ in record.word_variants
        if printed not in {word for word, _ in record.pairs}
    }
    if unused:
        raise RuntimeError(f"word_variants.tsv rows match no printed word: {sorted(unused)}")
    return records


def apply_reading_glosses(record_id: str, pairs: tuple[tuple[str, str], ...]
                          ) -> tuple[tuple[str, str], ...]:
    out = []
    for word, gloss in pairs:
        override = READING_GLOSSES.get((record_id, word))
        if override:
            printed, per_reading = override
            if gloss != printed:
                raise RuntimeError(f"reading_glosses.tsv is stale for {record_id} {word}: "
                                   f"expected printed gloss {printed!r}, found {gloss!r}")
            _APPLIED_READING_GLOSSES.add((record_id, word))
            gloss = per_reading
        out.append((word, gloss))
    return tuple(out)


_APPLIED_READING_GLOSSES: set[tuple[str, str]] = set()


def apply_slash_scope(record_id: str, pairs: tuple[tuple[str, str], ...]
                      ) -> tuple[tuple[str, str], ...]:
    out = []
    for word, gloss in pairs:
        rule = SLASH_SCOPE.get((record_id, word))
        if rule:
            printed_gloss, new_word, new_gloss = rule
            if gloss != printed_gloss:
                raise RuntimeError(f"slash_scope.tsv is stale for {record_id} {word}: "
                                   f"expected gloss {printed_gloss!r}, found {gloss!r}")
            _APPLIED_SLASH_SCOPE.add((record_id, word))
            word, gloss = new_word, new_gloss
        out.append((word, gloss))
    return tuple(out)


_APPLIED_SLASH_SCOPE: set[tuple[str, str]] = set()


def split_gloss_alternatives(gloss: str) -> list[str]:
    # A set of alternatives the source wraps in one pair of brackets, e.g.
    # （現在/昨天/明天） under (saya/*ciga/*kusun), is unwrapped first, as the
    # word itself is; splitting first left （ on one reading and ） on another.
    if gloss[:1] in "(（" and gloss[-1:] in ")）" and "/" in gloss:
        inner = gloss[1:-1]
        if not any(ch in inner for ch in "()（）"):
            gloss = inner
    alternatives = [part.strip("() ") for part in gloss.split("/")]
    for index in range(1, len(alternatives)):
        if alternatives[index].startswith("-"):
            base = alternatives[0].split("-", 1)[0]
            alternatives[index] = base + alternatives[index]
    return alternatives


# Optional material inside a word, h-(um)-uwa (R275, p. 127). Ruled 2026-10-15:
# a reading whose morpheme segmentation differs is a separate S, not a ver="alt"
# variant, because the W/M tier differs (POL-028 as amended). So, like a whole
# optional word, it gives two readings, the bare one first: huwa (怎樣) and
# h-um-uwa (怎樣-AF). The bare reading's gloss drops the optional morpheme's.
_OPTIONAL_MORPHEME = re.compile(r"(^|-)\(([^()*/]+)\)(-|$)")


def optional_morpheme_options(word: str, gloss: str) -> list[tuple[tuple[str, str], ...]]:
    found = _OPTIONAL_MORPHEME.search(word)
    if found is None or len(_OPTIONAL_MORPHEME.findall(word)) != 1 or "(" in (
            word[:found.start()] + word[found.end():]):
        # Optional letters that are not a whole morpheme, (u)m-lavi, leave the
        # segmentation unchanged and would be a ver="alt" variant instead. None
        # occur in this book; one appearing deserves a human's eye.
        raise RuntimeError(f"Unhandled optional material inside {word!r}")
    optional = found[2]
    full = word[:found.start()] + found[1] + optional + found[3] + word[found.end():]
    # The bare reading drops the morpheme with its hyphens: h-(um)-uwa -> huwa,
    # puken-(en) -> puken, (ma)-lavi -> lavi.
    bare = word[:found.start()] + word[found.end():]
    morphemes = morpheme_pairs(full, gloss)
    kept = [(form, part) for form, part in morphemes if form.strip("-") != optional]
    if len(kept) != len(morphemes) - 1:
        raise RuntimeError(f"Cannot find the optional morpheme {optional!r} in "
                           f"{full!r} / {gloss!r}: {morphemes!r}")
    bare_gloss = "-".join(part for _, part in kept)
    if len([part for part in bare.split("-") if part]) != len(kept):
        raise RuntimeError(f"{bare!r} does not segment like its gloss {bare_gloss!r}")
    return [((bare, bare_gloss),), ((full, gloss),)]


def pair_options(word: str, gloss: str) -> list[tuple[tuple[str, str], ...]]:
    word, gloss, keep = resolve_starred_parens(word, gloss)
    if not keep:
        return [()]

    optional = word == "(ka)"
    if optional:
        return [(), (("ka", gloss),)]

    if _OPTIONAL_MORPHEME.search(word) and not (word.startswith("(") and word.endswith(")")):
        return optional_morpheme_options(word, gloss)

    wrapped = word.startswith("(") and word.endswith(")")
    if wrapped:
        word = word[1:-1]

    word_alternatives = word.split("/")
    gloss_alternatives = split_gloss_alternatives(gloss)
    options: list[tuple[tuple[str, str], ...]] = []
    for index, alternative in enumerate(word_alternatives):
        if alternative.startswith("*"):
            continue
        selected_gloss = (
            gloss_alternatives[index]
            if len(gloss_alternatives) == len(word_alternatives)
            else gloss
        )
        options.append(((alternative, selected_gloss),))
    if not options:
        raise RuntimeError(f"No grammatical alternative remains for {word!r}")
    return options


def brace_alternation(
    group: list[tuple[str, str]]
) -> list[tuple[tuple[str, str], ...]]:
    """Read a braced group as an alternation whose scope spans words.

    Chang braces an alternation only when it is not word-for-word:
    ``{laqi gaga/temi}`` alternates `laqi gaga` with `temi`. A single word
    alternating with a single word needs no braces and is handled by
    pair_options' plain slash split -- verified across this corpus, where all 50
    slash-bearing tokens sit inside one whitespace token and no alternative
    contains a space.

    The slash is the pivot: everything to its left inside the braces belongs to
    the first reading, everything to its right to the second. Anything this
    cannot read raises rather than guesses -- there is exactly one braced
    example in the book, so a second one deserves a human's eye, not a silent
    reinterpretation.
    """
    slashed = [index for index, (word, _) in enumerate(group) if "/" in word]
    if len(slashed) != 1:
        raise RuntimeError(
            f"Braced group needs exactly one '/' pivot, found {len(slashed)}: {group!r}"
        )
    pivot = slashed[0]
    word, gloss = group[pivot]
    word_sides = word.split("/")
    gloss_sides = gloss.split("/")
    if len(word_sides) != 2 or len(gloss_sides) != 2:
        raise RuntimeError(f"Braced pivot must be two-way: {group[pivot]!r}")
    first = [*group[:pivot], (word_sides[0], gloss_sides[0])]
    second = [(word_sides[1], gloss_sides[1]), *group[pivot + 1 :]]
    for reading in (first, second):
        if not reading or any(not w for w, _ in reading):
            raise RuntimeError(f"Braced group produced an empty reading: {group!r}")
    return [tuple(first), tuple(second)]


def expand_pairs(
    pairs: tuple[tuple[str, str], ...],
    word_variants: tuple[tuple[str, tuple[str, str]], ...] = (),
) -> list[tuple[tuple[str, str], ...]]:
    variant_bases = {printed: base for printed, (base, _) in word_variants}
    units: list[list[tuple[tuple[str, str], ...]]] = []
    index = 0
    while index < len(pairs):
        word, gloss = pairs[index]
        if word.startswith("{"):
            group: list[tuple[str, str]] = []
            while index < len(pairs):
                group_word, group_gloss = pairs[index]
                end = group_word.endswith("}")
                group.append((group_word.lstrip("{").rstrip("}"), group_gloss))
                index += 1
                if end:
                    break
            else:
                raise RuntimeError(f"Unclosed braced group starting at {word!r}")
            units.append(brace_alternation(group))
            continue
        if word.startswith("(") and not word.endswith(")"):
            group: list[tuple[str, str]] = [(word.removeprefix("("), gloss)]
            index += 1
            while index < len(pairs):
                group_word, group_gloss = pairs[index]
                end = group_word.endswith(")")
                group.append((group_word.removesuffix(")"), group_gloss))
                index += 1
                if end:
                    break
            else:
                raise RuntimeError(f"Unclosed optional group starting at {word!r}")
            units.append([(), tuple(group)])
            continue
        if word in variant_bases:
            # One reading of a word variant; the other rides along as ver="alt".
            units.append([((variant_bases[word], gloss),)])
        else:
            units.append(pair_options(word, gloss))
        index += 1

    variants: list[tuple[tuple[str, str], ...]] = []
    for choices in product(*units):
        variant = tuple(pair for choice in choices for pair in choice)
        if variant and variant not in variants:
            variants.append(variant)
    return variants


def translations_for(
    record: SourceRecord, pairs: tuple[tuple[str, str], ...]
) -> tuple[str, tuple[str, ...]]:
    words = {word.strip(".,;:?!") for word, _ in pairs}
    for trigger, translation in _TRANSLATION_BY_TRIGGER.get(record.record_id, ()):
        if trigger in words:
            return translation, ()
    if record.record_id in _TRANSLATION_FIXED:
        return _TRANSLATION_FIXED[record.record_id]
    if "=" in record.translation:
        primary, *alternates = [part.strip() for part in record.translation.split("=")]
        return primary, tuple(part for part in alternates if part)
    # Two translations the source quotes separately and joins with 或, as for an
    # ambiguous sentence (R081, p. 75): '你打了小孩' 或 '小孩打了你'. Ruled
    # 2026-10-14: one sentence, the second as an alternate translation.
    quoted = re.fullmatch(r"'([^']+)'\s*或\s*'([^']+)'", record.translation.strip())
    if quoted:
        return quoted[1].strip(), (quoted[2].strip(),)
    return record.translation, ()


def expand_records(records: list[SourceRecord]) -> list[Variant]:
    variants: list[Variant] = []
    for record in records:
        for number, pairs in enumerate(
                expand_pairs(record.pairs, record.word_variants), start=1):
            translation, alternates = translations_for(record, pairs)
            variants.append(Variant(record, number, pairs, translation, alternates))
    return variants


def deduplicate(variants: list[Variant]) -> tuple[list[Variant], list[dict[str, str]]]:
    """POL-022: publish each distinct sentence once, and disclose the merges.

    Chang reuses examples across chapters, so the same sentence arrives from
    several source records -- 14 groups covering 29 variants before this step.
    A repeated example does not need publishing twice. The first occurrence is
    kept and every merged record's locator rides along in ``S/@source``, so
    collapsing them costs no provenance.

    This is the dedup step POL-022 looks for: with it declared, any duplicate
    left in the published XML is a pipeline defect and
    ``validate_duplicate_sentences.py`` reports it HARD rather than SOFT.

    Returns the kept variants (with ``sentence_id`` assigned) and the rows for
    the disclosure ledger (POL-051).
    """
    kept: list[Variant] = []
    first_by_form: dict[str, Variant] = {}
    ledger: list[dict[str, str]] = []
    for variant in variants:
        first = first_by_form.get(variant.form)
        if first is None:
            first_by_form[variant.form] = variant
            kept.append(variant)
            continue
        first.merged.append(variant)
        known = {
            translation_key(text)
            for text in (
                first.translation,
                *first.alternate_translations,
                *first.merged_translations,
            )
            if text
        }
        for candidate in (variant.translation, *variant.alternate_translations):
            if candidate and translation_key(candidate) not in known:
                first.merged_translations.append(candidate)
                known.add(translation_key(candidate))
        # A merged copy whose gloss or translation differs is not simply a
        # repeat: one of the two readings is wrong, or the source genuinely
        # glossed the same string two ways. Record which, rather than letting
        # the merge hide it.
        differs = sorted(
            name
            for name, same in (
                ("gloss", variant.gloss == first.gloss),
                ("translation", variant.translation == first.translation),
                (
                    "alternate_translations",
                    variant.alternate_translations == first.alternate_translations,
                ),
            )
            if not same
        )
        ledger.append(
            {
                "merged_into_source_id": first.source.record_id,
                "merged_into_variant": str(first.variant_number),
                "dropped_source_id": variant.source.record_id,
                "dropped_variant": str(variant.variant_number),
                "dropped_source_locator": variant.source.source_locator,
                "form": variant.form,
                "differs_in": ",".join(differs),
                "dropped_gloss": variant.gloss,
                "dropped_translation": variant.translation,
                "translation_kept_as": (
                    "alternate"
                    if translation_key(variant.translation)
                    != translation_key(first.translation)
                    else "same"
                ),
            }
        )
    assign_ids(kept)
    return kept, ledger


def assign_ids(variants: list[Variant]) -> None:
    """POL-028 naming: one base id per source record, siblings take ``-opt``.

    A record that yields more than one S -- because a whole optional word makes
    the sentence's word inventory change, or because the source offers competing
    lexemes -- keeps its base id on the first block and names the rest
    ``-opt``, ``-opt3``, ``-opt4``. There is deliberately no ``-opt2``: the
    second block is the common case and stays unnumbered so published ids do
    not move when a third reading turns up.

    The base id is the source record's own id (R275, so R275, R275-opt, ...),
    ruled 2026-10-16 (POL-037): adding, excluding or merging a record never
    renumbers any other record's sentences, and adding or dropping a reading
    inside a record shifts nothing either.

    Run after deduplicate(), so a merged-away first reading cannot leave an
    ``-opt`` orphaned from the base it was named against.
    """
    by_record: dict[str, list[Variant]] = {}
    for variant in variants:
        by_record.setdefault(variant.source.record_id, []).append(variant)
    for record_id, siblings in by_record.items():
        base = record_id
        for position, variant in enumerate(siblings):
            if position == 0:
                variant.sentence_id = base
            elif position == 1:
                variant.sentence_id = f"{base}-opt"
            else:
                variant.sentence_id = f"{base}-opt{position + 1}"


def load_xml_notes() -> dict[str, list[tuple[str, str]]]:
    """Notes from the 2026-10 review, record id -> [(target, note)]. Target is
    FORM (the sentence), TRANSL (its free translation) or W:<word> (that word's
    gloss). A curated, committed table: what the reviewer reported about each
    example, attributed to the source she named, else to the review itself."""
    if not XML_NOTES_TSV.exists():
        return {}
    out: dict[str, list[tuple[str, str]]] = {}
    with XML_NOTES_TSV.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            out.setdefault(row["record_id"], []).append((row["target"], row["note"]))
    return out


_NOTES_ATTACHED: set[tuple[str, str, str]] = set()


def attach_notes(sentence: ET.Element, record_ids: list[str],
                 notes: dict[str, list[tuple[str, str]]]) -> None:
    def add(element: ET.Element | None, note: str) -> bool:
        if element is None:
            return False
        existing = element.get("notes")
        element.set("notes", f"{existing} {note}" if existing else note)
        return True

    bare = lambda text: (text or "").strip(".,;:!?\"")
    for record_id in record_ids:
        for target, note in notes.get(record_id, []):
            if target == "FORM":
                done = add(sentence.find("FORM[@kindOf='original']"), note)
            elif target == "TRANSL":
                done = add(next((t for t in sentence.findall("TRANSL")
                                 if t.get("ver") is None), None), note)
            elif target.startswith("W:"):
                word = next((w for w in sentence.findall("W")
                             if bare(w.findtext("FORM[@kindOf='original']"))
                             == target[2:]), None)
                done = add(word.find("TRANSL") if word is not None else None, note)
            else:
                raise RuntimeError(f"{record_id}: unknown note target {target!r}")
            if done:
                _NOTES_ATTACHED.add((record_id, target, note))


def check_notes_attached(notes: dict[str, list[tuple[str, str]]]) -> None:
    wanted = {(r, t, n) for r, items in notes.items() for t, n in items}
    missing = sorted(wanted - _NOTES_ATTACHED)
    if missing:
        raise SystemExit(f"{len(missing)} review notes attached to nothing: {missing[:3]}")


def add_text(
    parent: ET.Element, tag: str, value: str, attrs: dict[str, str] | None = None
) -> ET.Element:
    child = ET.SubElement(parent, tag, attrs or {})
    child.text = value
    return child


# Word pairs the book glosses as one unit: a single gloss printed under both words
# (POL-060). Ruled 2026-10-15 from the scan; the table, with the evidence for each
# pair, is data (POL-039): shared_gloss_pairs.tsv.
SHARED_GLOSS_PAIRS_TSV = ROOT / "CodeAndDocs" / "shared_gloss_pairs.tsv"
with SHARED_GLOSS_PAIRS_TSV.open(encoding="utf-8", newline="") as _handle:
    SHARED_GLOSS_PAIRS = frozenset(
        (row["first"], row["second"]) for row in csv.DictReader(_handle, delimiter="\t"))
PUNCTUATION = ".,;:?!"
UNKNOWN_GLOSS = "?"   # POL-061: a word the source leaves unglossed


def gloss_units(pairs: tuple[tuple[str, str], ...]) -> list[tuple[str, str]]:
    """The W tier's units, from the source's word/gloss pairs.

    The transcription marks the second word of a shared gloss, and a word the
    book leaves unglossed, the same way: gloss ∅. Here the two are told apart.
    A ∅ after the first word of a SHARED_GLOSS_PAIRS pair joins that word, so
    the pair is one W with the gloss once (POL-060). A pronoun the book prints
    inside the pair (ani-ku naq, ado-su ka) is written as an infix, ani<ku>naq
    with the gloss 雖然<我> (ruled 2026-10-15), and then handled like any other
    infix (POL-014). Any ∅ left is a word with no printed gloss: ? (POL-061).
    Runs after optional material and alternatives are expanded, so an optional
    pair such as (ani sa) still expands first.
    """
    out: list[tuple[str, str]] = []
    for word, gloss in pairs:
        if gloss == "∅" and out:
            previous_word, previous_gloss = out[-1]
            base, _, clitic = previous_word.strip(PUNCTUATION).partition("-")
            second = word.rstrip(PUNCTUATION)
            if (base, second) in SHARED_GLOSS_PAIRS:
                if clitic:
                    gloss_base, _, gloss_clitic = previous_gloss.partition("-")
                    out[-1] = (f"{base}<{clitic}>{second}{word[len(second):]}",
                               f"{gloss_base}<{gloss_clitic}>")
                else:
                    out[-1] = (f"{previous_word} {word}", previous_gloss)
                continue
        out.append((word, gloss))
    return [(word, gloss.replace("∅", UNKNOWN_GLOSS)) for word, gloss in out]


# The `?` above is only a placeholder while the gloss is still a string, so the
# morpheme split and the W/M piece counts treat it like any other gloss piece.
# What is published is <UNCLEAR/> (maintainer, 2026-10-17: "Our own POL-061 ?
# glosses become <UNCLEAR/>" -> "Yes"): `?` becomes <TRANSL><UNCLEAR/></TRANSL>
# and `?-你` becomes <TRANSL><UNCLEAR/>-你</TRANSL>. Only a gloss piece that is
# exactly `?` is replaced. It runs after ET.indent, which would otherwise put
# indentation whitespace inside a TRANSL whose only content is the element.
_GLOSS_PIECES = re.compile(r"([-<>])")


def unclear_glosses(root: ET.Element) -> int:
    """Replace each W/M gloss piece that is UNKNOWN_GLOSS with <UNCLEAR/>.

    Returns the number of TRANSL elements changed.
    """
    changed = 0
    for unit in (*root.iter("W"), *root.iter("M")):
        for transl in unit.findall("TRANSL"):
            if len(transl) or not transl.text:
                continue
            pieces = _GLOSS_PIECES.split(transl.text)
            if UNKNOWN_GLOSS not in pieces:
                continue
            transl.text = None
            last: ET.Element | None = None
            for piece in pieces:
                if piece == UNKNOWN_GLOSS:
                    last = ET.SubElement(transl, "UNCLEAR")
                elif last is None:
                    transl.text = (transl.text or "") + piece or None
                else:
                    last.tail = (last.tail or "") + piece or None
            changed += 1
    return changed


# Punctuation a morpheme never keeps. The morphemes are cut here, before the
# shared cleaner turns full-width punctuation into ASCII, so the full-width forms
# the book sets in a few Seediq lines (nii， on p. 155) and the quote marks of
# reported speech (C5-017) are listed too (ruled 2026-10-15). Words and sentences
# keep their punctuation.
MORPHEME_PUNCTUATION = ".,;:?!\"，。？！；：、「」『』"


INFIXES = ("um", "un", "in", "n")


def infix_layout(word: str, gloss: str) -> tuple[list[str], list[int], int] | None:
    """The word's hyphen pieces, infix positions and root position, when the
    book glosses it as a root interrupted by infixes: q-um-erac 抓-AF, b-n-eebu-su
    打-完成貌-你 -- one gloss piece for the discontinuous root, one per infix, one
    per suffix. None otherwise.

    A word the book glosses with one piece per hyphen piece -- m-un-ekan
    AF-完成貌-吃 -- is not read as infixed: its pieces are three morphemes in a
    row, as printed (ruled 2026-10-15, Q1b: "follow the book").
    """
    bare_word = word.strip(MORPHEME_PUNCTUATION)
    parts = [part for part in bare_word.split("-") if part]
    gloss_parts = [part for part in gloss.split("-") if part]
    if len(parts) < 3 or len(parts[0]) != 1:
        return None
    infixes: list[int] = []
    cursor = 1
    while cursor < len(parts) - 1 and parts[cursor] in INFIXES:
        infixes.append(cursor)
        cursor += 1
    if not infixes:
        return None
    root = infixes[-1] + 1
    if len(gloss_parts) != 1 + len(infixes) + len(parts[root + 1:]):
        return None
    return parts, infixes, root


def morpheme_pairs(word: str, gloss: str) -> list[tuple[str, str]]:
    bare_word = word.strip(MORPHEME_PUNCTUATION)
    # A pronoun written as an infix (gloss_units): root with a hyphen at the
    # infixation point, then the infix (POL-014): ani<ku>naq -> ani-naq, -ku-.
    angle = re.fullmatch(r"([^<]+)<([^>]+)>(.+)", bare_word)
    angle_gloss = re.fullmatch(r"([^<]+)<([^>]+)>", gloss)
    if angle and angle_gloss:
        return [(f"{angle[1]}-{angle[3]}", angle_gloss[1]),
                (f"-{angle[2]}-", angle_gloss[2])]
    word_parts = [part for part in bare_word.split("-") if part]
    gloss_parts = [part for part in gloss.split("-") if part]

    # A root interrupted by infixes (POL-014): one M for the root, written
    # with a hyphen at the infixation point, one per infix, then the suffixes.
    layout = infix_layout(word, gloss)
    if layout:
        parts, infixes, root = layout
        output = [("-".join([parts[0], parts[root]]), gloss_parts[0])]
        output.extend((f"-{parts[index]}-", gloss_parts[offset + 1])
                      for offset, index in enumerate(infixes))
        output.extend(zip(parts[root + 1:], gloss_parts[1 + len(infixes):], strict=True))
        return output

    if len(word_parts) == len(gloss_parts) and len(word_parts) > 1:
        return list(zip(word_parts, gloss_parts, strict=True))
    if len(gloss_parts) == len(word_parts) + 1 and len(word_parts) > 1:
        return [
            (word_parts[0], "-".join(gloss_parts[:2])),
            *zip(word_parts[1:], gloss_parts[2:], strict=True),
        ]
    return [(bare_word, gloss)]


def word_form_for_xml(word: str, gloss: str) -> str:
    """POL-014 at the word tier: b-n-eebu -> b<n>eebu (ruled 2026-10-15, Q1a).

    Only the word FORM changes. The sentence FORM keeps the book's hyphens, and
    the morphemes keep the root-with-hyphen shape POL-014 asks for at M level.
    """
    layout = infix_layout(word, gloss)
    if not layout:
        return word
    parts, infixes, root = layout
    bare = word.strip(MORPHEME_PUNCTUATION)
    lead = word[: len(word) - len(word.lstrip(MORPHEME_PUNCTUATION))]
    trail = word[len(word.rstrip(MORPHEME_PUNCTUATION)):]
    assert bare == "-".join(parts)
    infixed = parts[0] + "".join(f"<{parts[i]}>" for i in infixes) + parts[root]
    return lead + "-".join([infixed, *parts[root + 1:]]) + trail


def word_gloss_for_xml(word: str, gloss: str) -> str:
    """The W gloss to match word_form_for_xml: 抓-AF -> 抓<AF>, 打-完成貌-你 ->
    打<完成貌>-你. The infix gloss is written inline in angle brackets
    (maintainer, 2026-09-11), so a reader -- and V153, which counts a form's
    pieces and a gloss's pieces the same way, one per <...> plus one per
    hyphen-separated part -- sees the same shape in both. Other words keep the
    book's gloss as printed.
    """
    layout = infix_layout(word, gloss)
    if not layout:
        return gloss
    _, infixes, _ = layout
    gloss_parts = [part for part in gloss.split("-") if part]
    head = gloss_parts[0] + "".join(f"<{g}>" for g in gloss_parts[1:1 + len(infixes)])
    return "-".join([head, *gloss_parts[1 + len(infixes):]])


def text_attributes(text_id: str, source: str) -> dict[str, str]:
    """TEXT attributes shared by both published files, so they cannot drift."""
    return {
        "id": text_id,
        f"{{{XML_NS}}}lang": "trv",
        "dialect": "Tegudaya",
        "source": source,
        # POL-042: exactly one value from FormosanBank's rights_vocabulary.csv,
        # nothing else. The grantor, the date and the evidence pointer live in
        # README.md's "## Rights" section (POL-044).
        "copyright": "CC BY-NC 4.0",
        "citation": (
            "Chang, Yung-li 張永利. 2000. 賽德克語參考語法 "
            "[Seediq Reference Grammar]. "
            "Yuan-Liou Publishing 遠流出版事業股份有限公司."
        ),
        "BibTeX_citation": (
            "@book{chang2000seediq,"
            "title={賽德克語參考語法 [Seediq Reference Grammar]},"
            "author={Chang, Yung-li},year={2000},"
            "publisher={Yuan-Liou Publishing}}"
        ),
    }


# Translations are Chinese, so a Latin name inside one takes no spaces around it
# (ruled 2026-10-15, this corpus only): 我相信pawan會打敗walis的。 A space between
# two Latin words stays (Awi Tone, walis buni).
_CJK = r"[\u3000-\u303f\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]"
_SPACE_BESIDE_CJK = re.compile(rf"(?<={_CJK})\s+|\s+(?={_CJK})")


def translation_text(text: str) -> str:
    return _SPACE_BESIDE_CJK.sub("", text)


def add_sentence(parent: ET.Element, sentence_id: str, source: str,
                 pairs: tuple[tuple[str, str], ...], translations: list[str],
                 alternates: list[str]) -> ET.Element:
    """One S with its W and M tiers. Shared by both builds."""
    sentence = ET.SubElement(parent, "S", {"id": sentence_id, "source": source})
    add_text(sentence, "FORM", " ".join(word for word, _ in pairs),
             {"kindOf": "original"})
    for translation in translations:
        add_text(sentence, "TRANSL", translation_text(translation),
                 {f"{{{XML_NS}}}lang": "zho"})
    for alternate in alternates:
        add_text(sentence, "TRANSL", translation_text(alternate),
                 {f"{{{XML_NS}}}lang": "zho", "ver": "alt"})
    for word_number, (word, gloss) in enumerate(gloss_units(pairs), start=1):
        word_id = f"{sentence_id}W{word_number:02d}"
        word_element = ET.SubElement(sentence, "W", {"id": word_id})
        add_text(word_element, "FORM", word_form_for_xml(word, gloss), {"kindOf": "original"})
        add_text(word_element, "TRANSL", word_gloss_for_xml(word, gloss),
                 {f"{{{XML_NS}}}lang": "zho"})
        for morph_number, (morph_form, morph_gloss) in enumerate(
            morpheme_pairs(word, gloss), start=1
        ):
            morph = ET.SubElement(
                word_element, "M", {"id": f"{word_id}M{morph_number:02d}"}
            )
            add_text(morph, "FORM", morph_form, {"kindOf": "original"})
            add_text(morph, "TRANSL", morph_gloss, {f"{{{XML_NS}}}lang": "zho"})
    return sentence


def build_long_texts() -> tuple[ET.ElementTree, int]:
    """Chapter 5, the book's only connected narrative.

    Nothing here needs the chapters 3-4 machinery: the narrative carries no
    slash alternations, no optional material and no starred parentheses, so
    every block is one sentence and there is nothing to expand or deduplicate.
    Sentence ids run in narrative order, which is the order they must be read
    in -- unlike the elicited examples, where order carries no meaning.
    """
    with CHAPTER5_TSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = [row for row in csv.DictReader(handle, delimiter="\t")
                if row["decision"] == "include"]
    root = ET.Element(
        "TEXT",
        text_attributes(
            "chang-2000-seediq-long-texts",
            "Chang Yung-li 2000 Seediq Reference Grammar, chapter 5 "
            "賽德克語的長篇語料 (printed pp. 151-159); the sumuladuc 祭祀 "
            "narrative, told by 傅景賢 walis wadan and retold by 錢成鏡 "
            "pawan torih; reviewed from the primary scan SHA-256 "
            f"{SOURCE_PDF_SHA256}",
        ),
    )
    corrections = load_review_corrections()
    notes = load_xml_notes()
    for number, row in enumerate(rows, start=1):
        row = correct_row(row, corrections, _CORRECTIONS_APPLIED)
        row = standardize_parentheses(strip_text_brackets(row))
        pairs = tuple(
            (word, gloss) for word, gloss in json.loads(row["word_gloss_json"])
        )
        sentence = add_sentence(root, row["record_id"], row["source_locator"], pairs,
                                [row["translation"]], [])
        attach_notes(sentence, [row["record_id"]], notes)
    ET.indent(root, space="  ")
    print(f"chapter 5: {unclear_glosses(root)} W/M glosses published as <UNCLEAR/>")
    return ET.ElementTree(root), len(rows)


def build_xml(variants: list[Variant]) -> ET.ElementTree:
    root = ET.Element(
        "TEXT",
        {
            "id": "chang-2000-seediq-reference-grammar",
            f"{{{XML_NS}}}lang": "trv",
            "dialect": "Tegudaya",
            "source": (
                "Chang Yung-li 2000 Seediq Reference Grammar; reviewed source inventory "
                f"from primary scan SHA-256 {SOURCE_PDF_SHA256}"
            ),
            # POL-042: exactly one value from FormosanBank's
            # rights_vocabulary.csv, nothing else. The grantor, the date and the
            # evidence pointer live in README.md's "## Rights" section (POL-044).
            "copyright": "CC BY-NC 4.0",
            "citation": (
                "Chang, Yung-li 張永利. 2000. 賽德克語參考語法 "
                "[Seediq Reference Grammar]. "
                "Yuan-Liou Publishing 遠流出版事業股份有限公司."
            ),
            "BibTeX_citation": (
                "@book{chang2000seediq,"
                "title={賽德克語參考語法 [Seediq Reference Grammar]},"
                "author={Chang, Yung-li},year={2000},"
                "publisher={Yuan-Liou Publishing}}"
            ),
        },
    )

    for variant in variants:
        sentence_id = variant.sentence_id
        sentence = ET.SubElement(
            root,
            "S",
            {"id": sentence_id, "source": variant.source_locators},
        )
        add_text(sentence, "FORM", variant.form, {"kindOf": "original"})
        alt_for = {base: alt for _, (base, alt) in variant.source.word_variants}
        if alt_for:
            words = [word.rstrip(PUNCTUATION) for word, _ in variant.pairs]
            if any(words.count(base) != 1 for base in alt_for):
                raise RuntimeError(f"{sentence_id}: a variant base is not exactly one word")
            add_text(sentence, "FORM", " ".join(
                alt_for[bare] + word[len(bare):] if bare in alt_for else word
                for bare, (word, _) in zip(words, variant.pairs)),
                {"kindOf": "original", "ver": "alt"})
        add_text(
            sentence,
            "TRANSL",
            translation_text(variant.translation),
            {f"{{{XML_NS}}}lang": "zho"},
        )
        for alternate in (
            *variant.alternate_translations,
            *variant.merged_translations,
        ):
            add_text(
                sentence,
                "TRANSL",
                translation_text(alternate),
                {f"{{{XML_NS}}}lang": "zho", "ver": "alt"},
            )

        for word_number, (word, gloss) in enumerate(gloss_units(variant.pairs), start=1):
            word_id = f"{sentence_id}W{word_number:02d}"
            word_element = ET.SubElement(sentence, "W", {"id": word_id})
            add_text(word_element, "FORM", word_form_for_xml(word, gloss), {"kindOf": "original"})
            bare = word.rstrip(PUNCTUATION)
            if bare in alt_for:
                add_text(word_element, "FORM", alt_for[bare] + word[len(bare):],
                         {"kindOf": "original", "ver": "alt"})
            add_text(
                word_element,
                "TRANSL",
                word_gloss_for_xml(word, gloss),
                {f"{{{XML_NS}}}lang": "zho"},
            )
            for morph_number, (morph_form, morph_gloss) in enumerate(
                morpheme_pairs(word, gloss), start=1
            ):
                morph = ET.SubElement(
                    word_element,
                    "M",
                    {"id": f"{word_id}M{morph_number:02d}"},
                )
                add_text(morph, "FORM", morph_form, {"kindOf": "original"})
                if bare in alt_for and morph_form == bare:
                    add_text(morph, "FORM", alt_for[bare],
                             {"kindOf": "original", "ver": "alt"})
                add_text(
                    morph,
                    "TRANSL",
                    morph_gloss,
                    {f"{{{XML_NS}}}lang": "zho"},
                )

    notes = load_xml_notes()
    for sentence, variant in zip(root.findall("S"), variants):
        attach_notes(sentence, [variant.source.record_id]
                     + [merged.source.record_id for merged in variant.merged], notes)
    ET.indent(root, space="  ")
    print(f"chapters 3-4: {unclear_glosses(root)} W/M glosses published as <UNCLEAR/>")
    return ET.ElementTree(root)


def write_audit_tables(
    variants: list[Variant],
    inventory_rows: list[dict[str, str]],
    dedup_rows: list[dict[str, str]],
) -> None:
    with ACCEPTED_TSV.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "s_id",
            "source_id",
            "variant",
            "source_locator",
            "merged_source_locators",
            "form",
            "gloss",
            "translation",
            "alternate_translations",
            "review_notes",
            "provenance",
        ]
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for variant in variants:
            writer.writerow(
                {
                    "s_id": variant.sentence_id,
                    "source_id": variant.source.record_id,
                    "variant": variant.variant_number,
                    "source_locator": variant.source.source_locator,
                    "merged_source_locators": "; ".join(
                        other.source.source_locator for other in variant.merged
                    ),
                    "form": variant.form,
                    "gloss": variant.gloss,
                    "translation": variant.translation,
                    "alternate_translations": " | ".join(
                        variant.alternate_translations
                    ),
                    "review_notes": variant.source.review_notes,
                    "provenance": "reviewed source inventory",
                }
            )

    rejected = [row for row in inventory_rows if row["decision"] == "exclude"]
    with REJECTED_TSV.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "source_id",
            "source_locator",
            "form",
            "gloss",
            "translation",
            "reason",
            "review_notes",
            "provenance",
        ]
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rejected:
            writer.writerow(
                {
                    "source_id": row["record_id"],
                    "source_locator": row["source_locator"],
                    "form": row["form"],
                    "gloss": row["gloss"],
                    "translation": row["translation"],
                    "reason": row["exclusion_reason"],
                    "review_notes": row["review_notes"],
                    "provenance": row["provenance"],
                }
            )

    # POL-051: a removal is disclosed, never silent.
    with DEDUP_TSV.open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "merged_into_source_id",
            "merged_into_variant",
            "dropped_source_id",
            "dropped_variant",
            "dropped_source_locator",
            "form",
            "differs_in",
            "translation_kept_as",
            "dropped_gloss",
            "dropped_translation",
        ]
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(dedup_rows)


def main() -> None:
    inventory_rows = read_inventory()
    records = source_records(inventory_rows)
    expanded = expand_records(records)
    variants, dedup_rows = deduplicate(expanded)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_xml(variants).write(OUT_XML, encoding="utf-8", xml_declaration=True)
    long_texts, long_count = build_long_texts()
    long_texts.write(OUT_XML_LONG, encoding="utf-8", xml_declaration=True)
    write_audit_tables(variants, inventory_rows, dedup_rows)
    check_notes_attached(load_xml_notes())
    print(
        f"Wrote {OUT_XML} with {len(records)} reviewed records, "
        f"{len(expanded)} grammatical variants, "
        f"{len(variants)} published sentences after dedup"
    )
    conflicted = [row for row in dedup_rows if row["differs_in"]]
    if conflicted:
        print(
            f"WARNING: {len(conflicted)} of {len(dedup_rows)} merged duplicates "
            "differ from the copy they were merged into:"
        )
        for row in conflicted:
            print(
                f"  {row['dropped_source_id']}.{row['dropped_variant']} -> "
                f"{row['merged_into_source_id']}.{row['merged_into_variant']}"
                f" differs in {row['differs_in']}: {row['form']!r}"
            )
    print(f"Wrote {OUT_XML_LONG} with {long_count} chapter-5 narrative sentences")
    print(f"Wrote {ACCEPTED_TSV}")
    print(f"Wrote {REJECTED_TSV}")
    print(f"Wrote {DEDUP_TSV}")
    corrections = load_review_corrections()
    if corrections:
        orphans = sorted(set(corrections) - _CORRECTIONS_APPLIED)
        print(f"Applied review corrections to {len(_CORRECTIONS_APPLIED)} of "
              f"{len(corrections)} corrected records")
        if orphans:
            raise SystemExit(
                f"{len(orphans)} review corrections matched no included record: "
                f"{orphans[:5]}. Re-export and re-review."
            )


if __name__ == "__main__":
    main()
