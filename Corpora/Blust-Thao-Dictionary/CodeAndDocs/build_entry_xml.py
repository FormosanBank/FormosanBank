#!/usr/bin/env python3
"""Build XML from the parsed entry apparatus (entry-records.json).

Hunter's build_xml.py publishes the example sentences only: it reads the
dictionary as a stream of Thao/English pairs and never sees the entry they sit
in. This one reads the schema parse - 6,519 entries, their headwords, sense
numbers, grammatical labels, definitions, etymologies, notes and
cross-references - and emits two families of TEXT:

    blust_2003_thao_entries_XXXX_YYYY.xml    one S per SENSE
        FORM  the Thao headword or derived form
        TRANSL the English definition, notes lifted out by the shared
               parenthetical classifier

    blust_2003_thao_examples_XXXX_YYYY.xml   one S per EXAMPLE
        FORM  the Thao example sentence, with its W and M tiers
        TRANSL the English translation

They are separate files on purpose. `source-lock.json` records the authorized
scope as the example sentences; the definitions are the entry apparatus and
their publication is a rights question the maintainer has not yet settled, so
the two are kept in files that can be published independently.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_xml import (  # noqa: E402
    CATALOG_URL,
    DICTIONARY_PARTS,
    PDF_URL,
    BASECAMP_CARD,
    XML_LANG,
    _note_label,
    add_translation,
    add_word_tier,
    normalize_blust_quotes,
    THAO_PARTICLES,
    text_root,
    translation_tiers,
)

from expand_source import (  # noqa: E402
    OPTION_RE,
    expand_optional,
    word_internal_variants,
)
from QC.utilities.parentheticals import split_in_step, take_notes  # noqa: E402
from QC.utilities.slash_alternatives import resolve_scope  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

#: Translations whose slash scope the resolver cannot settle, ruled by the
#: maintainer and shared with expand_source.py.
SLASH_TRANSLATIONS = {
    key: value
    for key, value in json.loads(
        (ROOT / "CodeAndDocs" / "slash-translations.json").read_text(encoding="utf-8")
    ).items()
    if not key.startswith("_")
}


#: Readings the automatic rules cannot derive, ruled by the maintainer and
#: keyed by the printed Thao.
CURATED_READINGS = {
    key: value
    for key, value in json.loads(
        (ROOT / "CodeAndDocs" / "curated-readings.json").read_text(encoding="utf-8")
    ).items()
    if not key.startswith("_")
}

#: Blust cites a phonemic shape between slashes - `/lh-um-bakbak/`. That is a
#: delimiter, not an alternation, and in these two records it is a typo
#: (maintainer, 2026-09-11).
CITATION_SLASHES = re.compile(r"^/([^/]+)/$")


#: Punctuation that is not part of a Thao word, for comparing two spellings.
_EDGE = ".,;:?!`'\"()"


def _words(text: str) -> list[str]:
    return [bare for bare in (t.strip(_EDGE) for t in text.split()) if bare]


def repeats_an_alternant(printed: str, alternants, readings) -> bool:
    """A published reading says an ALTERNATING word oftener than the page does.

    No longer decides anything: "if a resolution that otherwise seems sensible
    results in a repeated word, it is worth someone looking at" (maintainer,
    2026-09-11). The review page reports it; the build is decided by
    `_alternants_reorder` and `_reading_loses_its_own_part`. Kept as a standing
    check so that a frame which starts inventing material says so.
    """
    alternating = {w for a in alternants for w in _words(a) if len(w) > 2}
    if not alternating:
        return False
    most: dict[str, int] = {}
    for part in (piece for piece in printed.split("/") if piece.strip()):
        counts: dict[str, int] = {}
        for word in _words(part):
            if word in alternating:
                counts[word] = counts.get(word, 0) + 1
        for word, n in counts.items():
            most[word] = max(most.get(word, 0), n)
    for reading in readings:
        counts = {}
        for word in _words(reading):
            if word in alternating:
                counts[word] = counts.get(word, 0) + 1
        if any(n > most.get(word, 0) for word, n in counts.items()):
            return True
    return False


def _splice_repeats_an_alternant(printed: str, scope) -> bool:
    """A reading says an ALTERNATING word more often than the page ever does.

    resolve_scope expands a slash by finding what the alternants share and
    splicing the rest between them. That is right when the slash separates two
    words inside one frame, and wrong when the alternants are the same sentence
    said another way, because then there is no frame to splice into:

        printed   ruza pia-biskaw/pia-biskaw sa ruza
        spliced   ruza pia-biskaw ruza

    Only words the slash is actually alternating count. A sentence may repeat a
    word of its own on either side of the slash - p.990 prints `antu yaku sa
    m-ara, tima/suma painan sa m-ara` and means it - and counting those made the
    frame look invented when it was not (maintainer, 2026-09-11).
    """
    alternating = {w for a in scope.alternants for w in _words(a) if len(w) > 2}
    if not alternating:
        return False
    most: dict[str, int] = {}
    for part in (piece for piece in printed.split("/") if piece.strip()):
        counts: dict[str, int] = {}
        for word in _words(part):
            if word in alternating:
                counts[word] = counts.get(word, 0) + 1
        for word, n in counts.items():
            most[word] = max(most.get(word, 0), n)
    for option in scope.options:
        counts = {}
        for word in _words(option):
            if word in alternating:
                counts[word] = counts.get(word, 0) + 1
        if any(n > most.get(word, 0) for word, n in counts.items()):
            return True
    return False


#: Blust's ordinals, for the district formula below.
_ONES = "first|second|third|fourth|fifth|sixth|seventh|eighth|ninth"
_ORDINAL = (
    rf"(?:{_ONES}|tenth|eleventh|twelfth"
    r"|(?:thir|four|fif|six|seven|eigh|nine)teenth"
    rf"|(?:twent|thirt|fort|fift)(?:ieth|y-(?:{_ONES})))"
)
#: The gloss's head phrase IS the word `name`, with an article and at most three
#: modifiers before it: `male name`, `a lineage name`, `a Thao dog name`.
NAMES_A_KIND_OF_NAME = re.compile(r"^(?:an? |the )?(?:[A-Za-z'’-]+ ){0,3}name$", re.I)
#: ... or it OPENS with `name of` / `name for` and goes on to say of what:
#: `name of a boat built by the Kao family in the story of the white deer`,
#: `name for a male buffalo`. 14 of these, ruled in by the maintainer on
#: 2026-09-11 ("Yes, boat names and similar should follow the proper-name
#: rule"). `Hakka, name for the Hakka people` is not one: its head, up to the
#: comma, is `Hakka`, which is a translation.
NAMES_WHAT_IT_IS = re.compile(r"^(?:an? |the )?names? (?:of|for) ", re.I)
#: Blust numbers the districts round the lake and glosses each place by its
#: position: `first district clockwise from Qaqcin, ...`.
DISTRICT_FORMULA = re.compile(
    rf"^(?:an? [a-z]+ )?{_ORDINAL} district clockwise from ", re.I
)


def _is_published_bound_root(entry, form_text: str) -> bool:
    """True when this sense IS the bar- or colon-marked root of its entry.

    Only when the entry also carries at least one sense derived from that
    root. An entry whose single sense is its own bar-marked header is a word
    the book decorated oddly, not a bound root - see the ruling quoted at the
    call site.
    """
    if not entry.get("root_marker") or not form_text:
        return False
    headword = entry["headword"].replace("\u2013", "-")
    if form_text.replace("\u2013", "-") != headword:
        return False
    for other in entry["senses"]:
        derived = sense_form(other, entry["headword"])
        if derived and derived.replace("\u2013", "-") != headword:
            return True
    return False


def _negative_imperative_only(sense) -> bool:
    """True when the whole gloss is Blust's optional-`(don't)` notation."""
    return (sense.get("definition") or "").strip().startswith("(don't)")


def describes_rather_than_translates(headword: str, definition: str) -> bool:
    """True when the gloss says what KIND of name the headword is.

    `Abish` is not English for anything; `male name (husband of Kaluzut)` tells
    you what sort of name it is. The English for `Abish` is Abish, and the
    description belongs in @notes - the maintainer's ruling on `Rariku`,
    `Lhqapamumu` and `Lhqatafatu`, 2026-09-11, extended to the rest of the class
    by a mechanical test so that no judgement of mine is in the pipeline.

    Two shapes, and nothing else:

    * the head of the gloss, up to its first bracket or clause break, IS the
      word `name` - `male name`, `female name`, `a lineage name`, `place name`,
      `a Thao dog name`. Fourteen distinct heads in the book, all of that form.
    * or that head OPENS with `name of` / `name for` and says of what: `name of
      a boat built by the Kao family in the story of the white deer`, `name for
      a male buffalo`, `name of a place (Bunun)`. 14 senses.
    * Blust's district formula, an ordinal and `district clockwise from`.

    The headword must be capitalised, and that condition does real work: it is
    what separates a word that IS a name from a word that MEANS `name`. Without
    it the test also takes `lhanaz` "name", `t-m-u-lhanaz` "to name, give a name
    to" and `shiduq` "family name, surname", which are ordinary Thao vocabulary
    and whose glosses are true translations.

    It stays narrower than every capitalised headword. `Maranash` "Japanese",
    `Shput` "Han people, Chinese", `Rawaraway` "the Thao name for the Bunun" and
    `Kakitlan` "Hakka, name for the Hakka people" are left alone, because their
    glosses are translations: the head of each is a word of English that means
    the thing, not a description of what sort of name it is.
    """
    if not headword[:1].isupper():
        return False
    head = re.split(r"[(,;.]", definition, 1)[0].strip()
    return (
        bool(NAMES_A_KIND_OF_NAME.match(head))
        or bool(NAMES_WHAT_IT_IS.match(head))
        or bool(DISTRICT_FORMULA.match(definition))
    )


def _alternants_reorder(printed: str, threshold: float = 0.5) -> bool:
    """The two sides of the slash are near enough the same words in another order.

    This is the reading a human reaches first, and it is the maintainer's
    (2026-09-11): "the two sides were almost identical but in a different order,
    so it made a lot more sense to assume what the compiler is doing is showing
    us two possible word orders". Two word orders share no frame, so the slash
    is taken at face value.

    The measure is the shared words over the LONGER side, not the shorter. Over
    the shorter side it reads 0.75 for p.924, where four words hang off a
    sixteen-word sentence and nothing is being reordered at all - the maintainer
    predicted exactly that failure: "for very long sentences, Rule 1 may not
    work, because words are more likely to be repeated in very long sentences".
    Over the longer side that case falls to 0.19.

    Across the 36 printed slashes the maintainer has ruled, the measure puts the
    highest "keep" at 0.40 and the lowest reordering the rule needs to catch at
    0.50, so the threshold sits in a real gap rather than on a guess.
    """
    parts = [piece.strip() for piece in printed.split("/") if piece.strip()]
    if len(parts) != 2:
        return False
    left, right = _words(parts[0]), _words(parts[1])
    if not left or not right or left == right:
        return False
    counts = {}
    for word in left:
        counts[word] = counts.get(word, 0) + 1
    shared = 0
    for word in right:
        if counts.get(word):
            counts[word] -= 1
            shared += 1
    return shared / max(len(left), len(right)) >= threshold


def _reading_loses_its_own_part(printed: str, scope) -> bool:
    """A reading no longer contains the part of the page it came from.

    Shared material is added at one end, so a reading must still open or close
    with its own printed part, whole and in order. Printed p.1022 sets
    `a mu-tusi-wak Qariwan/a mu-tusi yaku Qariwan`; the resolver read `yaku
    Qariwan` as a shared tail and produced `a mu-tusi-wak yaku Qariwan`, which
    is neither printed part - it fuses the two. "Your proposal required not a
    shared tail but actually fusing the two forms. Make sure you aren't doing
    that somewhere else" (maintainer, 2026-09-11).
    """
    parts = [piece.strip() for piece in printed.split("/") if piece.strip()]
    if len(parts) != len(scope.options):
        return False
    for part, option in zip(parts, scope.options):
        printed_words, option_words = _words(part), _words(option)
        if not printed_words:
            continue
        n = len(printed_words)
        if option_words[:n] != printed_words and option_words[-n:] != printed_words:
            return True
    return False


def readings(form: str, english: str) -> list[tuple[str, str, str | None]]:
    """Every published reading of one printed form, as (form, english, alternate).

    Three shapes, and the printed notation tells them apart:

    * a bracket attached to a WORD - ``bizu(h)``, ``(k)-m-alhus`` - is one
      lexeme spelt two ways, so it stays one sentence and the second spelling
      is a ``ver="alt"`` FORM (POL-028). Dropping the optional material drops
      its morpheme boundary with it: ``(k)-m-alhus`` gives ``m-alhus``, not
      ``-m-alhus``.
    * a SLASH is an alternation, one reading each. When the English carries a
      slash too they are about the same thing and split together.
    * a bracket standing as its own TOKEN is optional material, two readings,
      and the English follows only if it pairs - a bracketed particle never
      pairs, so ``ata (tu) karkar-i`` / ``Don't chew (it)!`` shares its English.
    """
    curated = CURATED_READINGS.get(form)
    if curated:
        # `alternate` is how a curated ruling says "one lexeme, two spellings":
        # p.832 prints `masa-rima masay rima use the hand for some purpose`
        # with the alternation slash dropped, and the maintainer ruled the two
        # spellings one word, so the second becomes a ver="alt" FORM (POL-028).
        return [
            (r["thao"], r.get("english", english), r.get("alternate"))
            for r in curated
        ]

    citation = CITATION_SLASHES.match(form.strip())
    if citation:
        return [(citation.group(1), english, None)]

    base, alternate = word_internal_variants(form)
    if alternate is not None:
        return [(base, english, alternate)]

    if "/" in form:
        # Count the slashes in the TRANSLATION, not in the translation plus its
        # notes: `I'll peel a banana/husk a peanut and eat it
        # (lit. I will eat a banana/husk a peanut, peel its skin)` has two, and
        # the mismatch drove the scope to low confidence so the record never
        # expanded at all.
        spoken, _notes = take_notes(form, english, never_pairs=THAO_PARTICLES)
        scope = resolve_scope(form, translation=spoken)
        if scope.confidence == "low" or len(scope.options) < 2:
            return [(form, english, None)]
        # A repeated word no longer decides anything on its own - it is a
        # reason for someone to look, and the review page flags it. What
        # decides is the shape of the page: two word orders, or a reading that
        # has lost its own printed half (maintainer, 2026-09-11).
        if (_alternants_reorder(form)
                or _reading_loses_its_own_part(form, scope)):
            scope.options = [
                piece.strip() for piece in form.split("/") if piece.strip()
            ]
        englishes = [english] * len(scope.options)
        curated = SLASH_TRANSLATIONS.get(form)
        if curated and len(curated) == len(scope.options):
            englishes = curated
        elif "/" in spoken:
            gloss = resolve_scope(spoken)
            if gloss.confidence != "low" and len(gloss.options) == len(scope.options):
                englishes = gloss.options
        return [(f, e, None) for f, e in zip(scope.options, englishes)]

    if OPTION_RE.search(form):
        paired = split_in_step(form, english, never_pairs=THAO_PARTICLES)
        expanded = [f for f, _labels in expand_optional(form)]
        if paired is not None and len(paired) == len(expanded):
            return [(f, e, None) for f, e in paired]
        return [(f, english, None) for f in expanded]

    return [(form, english, None)]
DATA_PATH = ROOT / "CodeAndDocs" / "entry-records.json"
DEFAULT_OUTPUT = ROOT / "XML" / "Thao"


def sense_form(sense: dict, headword: str) -> str:
    """The Thao side of a sense, or "" when there is nothing publishable.

    A form with no letter or digit in it is not a word: printed p. 1031 leaves
    a bare `~`, Blust's repetition glyph, standing where a headword should be.
    add_phonology then emits an empty PHON, which is V073 HARD. One sense and
    two entries are affected; they are dropped here and reported by E11.
    """
    value = (sense.get("form") or headword or "").strip()
    return value if any(c.isalnum() for c in value) else ""


def form_notes(entry: dict, sense: dict, first: bool) -> str | None:
    """What belongs to the Thao side rather than to the English."""
    parts = []
    if first and entry.get("etymology"):
        parts.append(f"Etymology: {entry['etymology']}")
    if sense.get("label"):
        parts.append(f"Grammatical label: {sense['label']}")
    if entry.get("homograph") is not None:
        parts.append(f"Homograph {entry['homograph']} of {entry['headword']}")
    if sense.get("number_inferred"):
        parts.append(
            "Sense number inferred from position; the page prints none"
        )
    return " | ".join(parts) or None


def translation_notes(sense: dict) -> list[str]:
    notes = [_note_label(note) for note in sense.get("notes") or []]
    # Blust's cross-references are `See acay:2` - a pointer to a sense number.
    # We do not publish sense numbers, so the pointer cannot be followed and is
    # not worth carrying even in a note (maintainer, 2026-09-11). The record
    # keeps every one of them in entry-records.json.
    return notes


def locator(entry: dict, sense: dict, page: int | None = None) -> str:
    """Where this sits in the book.

    The page is the one the sense or example is PRINTED on, which is not
    always the page its entry opened on - a long entry runs over several, and
    naming the entry's page put 2,436 examples and 1,820 senses on the wrong
    one. The entry's own page is named too when they differ.
    """
    page = entry["printed_page"] if page is None else page
    where = f"printed p. {page}; entry {entry['headword']!r}"
    if page != entry["printed_page"]:
        where += f" (opens on p. {entry['printed_page']})"
    number = sense.get("number")
    if number is not None:
        where += f"; sense {number}{sense.get('subsense') or ''}"
    if entry.get("root_marker"):
        where += f"; bound root marked with {entry['root_marker']}"
    return where


def build_entries_part(start, end, entries, counter) -> tuple[str, ET.ElementTree]:
    text_id = f"blust_2003_thao_entries_{start:04d}_{end:04d}"
    root = text_root(
        text_id,
        f"Blust 2003 Thao-English dictionary entries, printed pp. {start}-{end} "
        f"(PDF pp. {start + 10}-{end + 10}); {CATALOG_URL}; {PDF_URL}; "
        f"Basecamp card {BASECAMP_CARD}",
    )
    for entry in entries:
        for index, sense in enumerate(entry["senses"]):
            # A bound root is not a word, so its own gloss is not a dictionary
            # entry - only the forms derived from it are (maintainer,
            # 2026-09-11). The root's line is the unnumbered first sense of a
            # format B entry.
            #
            # But a header that DEFINES something is not a bound root, whatever
            # the bars around it say: `|Rariku| first district clockwise from
            # Qaqcin` is a word, and so are the lineage names `|Lhqapamumu|` and
            # `|Lhqatafatu|`. "Bound forms that have definitions but do not have
            # senses should be included in the XML like any other dictionary
            # entry - I think these are simply mis-characterized as bound forms"
            # (maintainer, 2026-09-11). So the definition decides, not the
            # printed decoration, and the record keeps the marker either way.
            #
            # `GLOSS?` is Blust saying he could not settle the meaning, so there
            # is nothing to publish: 4 entries.
            if entry.get("root_marker") and index == 0 and sense["number"] is None:
                if not (sense.get("definition") or "").strip():
                    continue
            if (sense.get("definition") or "").strip() == "GLOSS?":
                continue
            form_text = sense_form(sense, entry["headword"])
            if _is_published_bound_root(entry, form_text):
                # "But also entries where the S FORM is a root printed in bars"
                # (maintainer, 2026-09-11). A bound root is not a word, so it
                # is not a dictionary entry; only what is derived from it is.
                # 34 senses.
                #
                # This does NOT disturb the earlier ruling above. That one
                # protects a bar-marked header which is the entry's ONLY
                # sense - `|Rariku|`, `|Lhqapamumu|`, `|Lhqatafatu|` and six
                # others, "simply mis-characterized as bound forms". Those
                # have nothing derived from them, so nothing here reaches
                # them; a root only goes when the entry proves it is a root by
                # carrying the forms built on it.
                continue
            if _negative_imperative_only(sense):
                # "Definitely remove all the glosses that open with
                # \"(don't)\"" (maintainer, 2026-09-11). The optional
                # `(don't)` is Blust telling the reader a bound form takes
                # either polarity, not a translation of anything. 395 senses,
                # every one of them the sense's only gloss, so no translation
                # is orphaned.
                continue
            if not form_text:
                continue
            page = sense.get("printed_page") or entry["printed_page"]
            definition = (sense.get("definition") or "").strip()
            extra = translation_notes(sense)
            if describes_rather_than_translates(entry["headword"], definition):
                # The English for a name is the name. What the book prints is a
                # description of it, and that is a note.
                extra = [definition] + extra
                definition = form_text
            every = readings(form_text, definition)
            for number, (reading, gloss, alternate) in enumerate(every, start=1):
                counter[page] = counter.get(page, 0) + 1
                where = locator(entry, sense, page)
                if len(every) > 1:
                    where += f"; reading {number} of {len(every)} of {form_text!r}"
                sentence = ET.SubElement(
                    root,
                    "S",
                    {
                        "id": f"blust-entry-p{page:04d}-s{counter[page]:03d}",
                        "source": where,
                    },
                )
                attributes = {"kindOf": "original"}
                notes = form_notes(entry, sense, index == 0)
                if notes:
                    attributes["notes"] = notes
                form = ET.SubElement(sentence, "FORM", attributes)
                form.text = normalize_blust_quotes(reading, set())
                if alternate:
                    variant = ET.SubElement(
                        sentence, "FORM", {"kindOf": "original", "ver": "alt"}
                    )
                    variant.text = normalize_blust_quotes(alternate, set())
                if gloss:
                    for position, (value, lifted) in enumerate(
                        translation_tiers(gloss, reading)
                    ):
                        combined = [n for n in ([lifted] if lifted else []) + extra]
                        add_translation(
                            sentence,
                            value,
                            alternate=position > 0,
                            notes=" | ".join(combined) or None,
                        )
                add_word_tier_if_segmentable(sentence, sentence.get("id"), form.text)
    ET.indent(root, space="    ")
    return f"{text_id}.xml", ET.ElementTree(root)


def build_examples_part(start, end, entries, counter) -> tuple[str, ET.ElementTree]:
    text_id = f"blust_2003_thao_examples_{start:04d}_{end:04d}"
    root = text_root(
        text_id,
        f"Blust 2003 Thao-English dictionary example sentences, printed pp. "
        f"{start}-{end} (PDF pp. {start + 10}-{end + 10}); {CATALOG_URL}; "
        f"{PDF_URL}; Basecamp card {BASECAMP_CARD}",
    )
    for entry in entries:
        for sense in entry["senses"]:
            # No guard on the root's own sense here. An example sentence is
            # Thao with a translation whatever the line above it is, and Blust
            # prints ten of them directly under a bound-root header. Skipping
            # the sense dropped all ten from the corpus in silence (maintainer,
            # 2026-09-11).
            for example in sense.get("examples") or []:
                thao = (example.get("thao") or "").strip()
                if not thao:
                    continue
                page = example.get("printed_page") or entry["printed_page"]
                english = (example.get("english") or "").strip()
                every = readings(thao, english)
                for number, (reading, gloss, alternate) in enumerate(every, start=1):
                    counter[page] = counter.get(page, 0) + 1
                    where = locator(entry, sense, page)
                    if example.get("exemplifies"):
                        where += f"; illustrates {example['exemplifies']!r}"
                    if len(every) > 1:
                        where += f"; reading {number} of {len(every)} of {thao!r}"
                    sentence = ET.SubElement(
                        root,
                        "S",
                        {
                            "id": f"blust-ex-p{page:04d}-e{counter[page]:03d}",
                            "source": where,
                        },
                    )
                    attributes = {"kindOf": "original"}
                    if example.get("source_note"):
                        attributes["notes"] = f"Source note: {example['source_note']}"
                    form = ET.SubElement(sentence, "FORM", attributes)
                    form.text = normalize_blust_quotes(reading, set())
                    if alternate:
                        variant = ET.SubElement(
                            sentence, "FORM", {"kindOf": "original", "ver": "alt"}
                        )
                        variant.text = normalize_blust_quotes(alternate, set())
                    if gloss:
                        for position, (value, lifted) in enumerate(
                            translation_tiers(gloss, reading)
                        ):
                            add_translation(
                                sentence, value, alternate=position > 0, notes=lifted
                            )
                    add_word_tier_if_segmentable(
                        sentence, sentence.get("id"), form.text
                    )
                    # A Thao question quoted inside an "answer to ..."
                    # parenthetical is a sentence with a translation, not a
                    # note. It gets its own S, sharing the host's locator
                    # (maintainer's ruling, 2026-09-11). Four in the book, and
                    # only the first reading carries them.
                    for index, quote in enumerate(
                        (example.get("quoted") or []) if number == 1 else [], start=1
                    ):
                        quoted = ET.SubElement(
                            root,
                            "S",
                            {
                                "id": f"{sentence.get('id')}-q{index:02d}",
                                "source": f"{where}; quoted in the translation of "
                                          f"{sentence.get('id')}",
                            },
                        )
                        quoted_form = ET.SubElement(
                            quoted, "FORM", {"kindOf": "original"}
                        )
                        quoted_form.text = normalize_blust_quotes(quote["thao"], set())
                        add_translation(quoted, quote["english"])
                        add_word_tier_if_segmentable(
                            quoted, quoted.get("id"), quoted_form.text
                        )
    ET.indent(root, space="    ")
    return f"{text_id}.xml", ET.ElementTree(root)


def build_all() -> list[tuple[str, ET.ElementTree]]:
    entries = json.loads(DATA_PATH.read_text(encoding="utf-8"))["entries"]
    out = []
    assigned = 0
    # One counter per family for the WHOLE build, not per file. An entry that
    # opens on p.379 lands in the 0280-0379 file, but a sense or example of it
    # printed on p.380 numbers against p.380 - and a per-file counter would
    # restart there and collide with the 0380-0479 file's own p.380 ids.
    sense_counter, example_counter = {}, {}
    for start, end in DICTIONARY_PARTS:
        part = [e for e in entries if start <= e["printed_page"] <= end]
        assigned += len(part)
        out.append(build_entries_part(start, end, part, sense_counter))
        out.append(build_examples_part(start, end, part, example_counter))
    if assigned != len(entries):
        raise ValueError(
            f"{len(entries) - assigned} entries fall outside the published page ranges"
        )
    return out


# Lexicographic notation: an optional element "(kay) p-acay", an alternation
# "ka-p-acay-an a ayuzi/ka-p-acay-an a binanau'az", a repetition glyph "~".
# It is not part of any word, so a W or M built by splitting on whitespace
# carries it into the FORM - which is V121, HARD, 1,184 times. The right
# treatment is to expand the notation into separate S the way expand_source.py
# does for the example sentences; until that exists, the sentence simply takes
# no word tier. POL-041 makes a partial pass a SOFT V148, never a HARD error.
NOTATION = re.compile(r"[()/~\[\]]")


def add_word_tier_if_segmentable(sentence, sentence_id, form_text):
    if NOTATION.search(form_text):
        return False
    add_word_tier(sentence, sentence_id, form_text)
    return True


CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def refuse_control_characters(tree: ET.ElementTree, name: str) -> None:
    """No C0 control character may reach the XML.

    They are not legal PCDATA, so lxml refuses the file and the pipeline stops
    at clean_xml with a parse error instead of a useful message. The one that
    got here was a stress accent that never found its vowel.
    """
    for element in tree.getroot().iter():
        for value in [element.text] + list(element.attrib.values()):
            if value and CONTROL.search(value):
                raise ValueError(
                    f"{name}: {element.tag} carries a control character: {value[:40]!r}"
                )


def write_all(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, tree in build_all():
        refuse_control_characters(tree, name)
        tree.write(output_dir / name, encoding="utf-8", xml_declaration=True)
        with (output_dir / name).open("a", encoding="utf-8") as handle:
            handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    write_all(args.output_dir)
    trees = build_all()
    sentences = sum(len(tree.getroot()) for _, tree in trees)
    print(f"wrote {len(trees)} files, {sentences} S elements to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
