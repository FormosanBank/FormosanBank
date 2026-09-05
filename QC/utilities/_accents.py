"""Shared accent-stripping for Formosan orthography handling.

Accents in a source text are *usually* prosodic noise — Glosbe marks stress
("máduk", "dálix") on a vowel that is really just the plain vowel wearing a
diacritic — so QC utilities normalize such a vowel to its bare form. But this
is not universal: a few reference orthographies use an accented letter as a
genuine orthographic letter (e.g. Rukai's Ortho113 spells a vowel ``é``). An
accent that a language's own orthography tables attest must therefore survive.

Two QC utilities strip accents, each keeping the letters its own tables attest:

- ``standardize.py`` strips accents from the *standard* tier before applying a
  conversion table, so a table entry keyed on the plain vowel still matches;
  diacritic-bearing letters that the conversion table lists explicitly are
  protected first (the *original* tier keeps its source spelling untouched).
- ``orthography_detector.py`` strips accents before scoring, so an accented
  vowel is not miscounted as an "unexpected token" against an orthography that
  legitimately contains the plain vowel — but it passes ``keep`` for the
  accented letters attested in that language's (or dialect's) orthographies, so
  a real orthographic accent such as Rukai ``é`` is preserved and scored.

Only the combining marks actually seen in the corpora are listed. The stripping
logic is otherwise mark-agnostic, so extending coverage is just adding to the
set below.

The macron is the clearest case of why ``keep`` matters. It is prosodic or
loanword notation in most of the bank — Saisiyat, Amis, Truku, Atayal and
Paiwan all carry macrons while attesting no macron letter. A caller that strips
it without a ``keep`` set merges any real macron letter with its bare base.
Callers should pass :func:`standard_orthography_accents` for their language: the
accented letters its *designated standard* orthography table actually lists.

Stripping applies to **Latin vowels only** (maintainer ruling 2026-09-05): a
prosodic mark sits on a vowel, so a diacritic on a consonant belongs to the
letter. That is what keeps Favorlang's ``ḡ``, Turkish ``ğ``, Slavic ``ć ś ń``
and MontgomeryTexts' ``ř``/``f̆`` intact without any exception list.

Stripping applies to **Latin-script characters only** (maintainer ruling). Every
Formosan orthography is Latin, so a prosodic accent worth removing is always on
a Latin base letter; a non-Latin character quoted in an article (Korean, CJK,
Cyrillic, Greek, Arabic, Devanagari, Thai, Hebrew, kana …) is passed through
untouched and NFC-composed. That last part matters: Hangul syllables decompose
into conjoining *jamo* rather than combining marks, so a blanket NFD pass used
to leave them decomposed in the standard tier.
"""
import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Iterable

ACCENTS_TO_STRIP = frozenset({
    "́",  # combining acute accent (á é í ó ú …)
    "̆",  # combining breve (ŭ …)
    "̄",  # combining macron (ā ē ī ō ū …)
})

# No unconditional keep set. Siraya's 'ǣ' and Favorlang's 'ḡ' were held here
# because neither language has a designated standard orthography to derive a
# keep set from. Verified 2026-09-05 that nothing strips them: Siraya_Gospels
# builds its standard tier with its own CodeAndDocs/regenerate_standard_tier.py
# and never runs standardize.py, Campbell-Favorlang publishes no standard tier
# at all, and neither corpus has a single PHON element. strip_accents is
# therefore never applied to either letter.
#
# If either language is ever standardized with the shared tool, give it a
# standards.csv entry and an Orthographies/<scheme>/<Language>.tsv that lists
# the letter — that is what standard_orthography_accents reads, and it will
# then protect it. Do NOT reintroduce a hardcoded exception list.
ALWAYS_KEEP = frozenset()


# A prosodic mark sits on a VOWEL. Stripping is therefore restricted to vowel
# bases, which is what separates a tone or stress mark from a letter that
# merely happens to carry a diacritic: Favorlang's 'ḡ', Turkish 'ğ', Slavic
# 'ć ś ń ž', and MontgomeryTexts' 'ř' and 'f̆' are consonants and are never
# touched, so no exception list is needed for them.
#
# 'y' and 'w' are deliberately absent: every Formosan orthography here maps
# them to the glides /j/ and /w/, so 'ý' is a consonant with a diacritic.
# The non-ASCII entries are the vowels the bank's orthographies actually use
# (Formosan barred/central vowels, and the IPA that reaches PHON generation).
_VOWELS = frozenset("aeiouæɑɐəɛɘɨɪɔœøʉʊʌ")


def _is_vowel(base: str) -> bool:
    """True if ``base`` is a vowel letter, ignoring case."""
    return base.casefold() in _VOWELS


def _has_stripped_mark(letter: str) -> bool:
    """True if ``letter`` carries one of the combining marks we strip."""
    return any(ch in ACCENTS_TO_STRIP for ch in unicodedata.normalize("NFD", letter))


def accented_letters(letters: Iterable[str]) -> frozenset:
    """Return the subset of ``letters`` that carry a strip-mark, as NFC strings.

    Used to derive the ``keep`` set for :func:`strip_accents` from an
    orthography's letter inventory: an accented letter that an orthography
    attests (e.g. Rukai ``é``) is one whose combining mark we would otherwise
    strip.
    """
    return frozenset(
        unicodedata.normalize("NFC", letter)
        for letter in letters
        if _has_stripped_mark(letter)
    )


@lru_cache(maxsize=None)
def standard_orthography_accents(language: str) -> frozenset:
    """Accented letters the language's **designated standard** orthography lists.

    This is the keep set callers should use: a diacritic survives stripping iff
    the orthography the bank standardizes that language to actually spells a
    letter with it. The scheme comes from ``standards.csv`` (POL-003) and the
    letters from that scheme's ``<Language>.tsv`` ``letter`` column — the same
    curated table ``add_phonology`` maps through, so a kept letter is always a
    mappable one.

    Deliberately NOT derived from ``QC/validation/reference/<Language>/*/
    unique_characters.txt``: those files are generated by
    ``orthography_extract.py`` from sample text and list every character
    observed, punctuation and digits included. They support the fuzzy
    set-similarity scoring ``validate_orthography.py`` does, but they cannot
    distinguish an orthographic letter from a prosodic diacritic that merely
    occurs in the sample — which is exactly the judgement this keep set makes.

    A language whose ``standards.csv`` entry is blank has no designated
    standard, so it returns empty — every accent on its Latin letters folds.
    Give the language a standards.csv entry and table if that is wrong.
    """
    # Imported lazily: this module is otherwise dependency-free, and the
    # registry pulls in the language tables.
    from QC.utilities._case_variants import load_profile_graphemes
    from QC.validation._dialect_inventory import (
        STANDARD_ORTHOGRAPHY_MAP,
        standard_orthography,
    )

    if language not in STANDARD_ORTHOGRAPHY_MAP:
        return frozenset()
    scheme = standard_orthography(language)
    if not scheme:
        return frozenset()
    path = (
        Path(__file__).resolve().parents[2]
        / "Orthographies"
        / scheme
        / f"{language}.tsv"
    )
    if not path.exists():
        return frozenset()
    try:
        return accented_letters(load_profile_graphemes(path))
    except ValueError:
        return frozenset()


@lru_cache(maxsize=None)
def _is_latin(char: str) -> bool:
    """True if ``char`` is a Latin-script character.

    Tested on the character's *decomposed* base so a precomposed letter whose
    own name does not begin with ``LATIN`` (e.g. U+212B ANGSTROM SIGN) is still
    recognized. Digits, punctuation, whitespace and every non-Latin script
    answer False.
    """
    base = unicodedata.normalize("NFD", char)[:1]
    return unicodedata.name(base, "").startswith("LATIN")


def _strip_latin_cluster(cluster: str, keep_nfc: frozenset) -> str:
    """Drop ACCENTS_TO_STRIP from one Latin base letter + its combining marks.

    Only vowels are stripped: a prosodic mark sits on a vowel, so a diacritic on
    a consonant is part of the letter (see ``_VOWELS``).
    """
    composed = unicodedata.normalize("NFC", cluster)
    if composed in keep_nfc:
        return composed
    decomposed = unicodedata.normalize("NFD", cluster)
    base, marks = decomposed[0], decomposed[1:]
    if not _is_vowel(base):
        return composed
    kept_marks = [mark for mark in marks if mark not in ACCENTS_TO_STRIP]
    return unicodedata.normalize("NFC", base + "".join(kept_marks))


def strip_accents(text: str, keep: Iterable[str] = frozenset()) -> str:
    """Remove ACCENTS_TO_STRIP from the **Latin** parts of ``text``.

    Latin-script characters are decomposed so precomposed accented vowels split
    into base + mark, the listed marks are dropped, and the letter is recomposed
    to NFC. Base letters that are distinct phonemes in their own right
    (ə, ʉ, ɨ, ŋ, …) are untouched because they carry no combining mark.

    Non-Latin characters — Hangul, CJK, kana, Cyrillic, Greek, Arabic,
    Devanagari, Thai, Hebrew … — are **never** stripped: their diacritics and
    conjoining parts are part of the script, not source prosody. They are
    emitted NFC-composed, so a Hangul syllable stays (or becomes) a precomposed
    syllable instead of a run of conjoining jamo.

    ``keep`` is an optional set of accented letters (matched in NFC form) that
    must survive stripping — the orthography attests them as real letters, so
    their diacritic is orthographic, not prosodic. Latin clusters whose NFC form
    is in ``keep`` pass through unchanged; every other Latin cluster has its
    strip-marks removed as before.
    """
    keep_nfc = frozenset(
        unicodedata.normalize("NFC", letter) for letter in keep
    ) | ALWAYS_KEEP

    result = []
    pending = []  # run of non-Latin text, flushed through NFC as a unit
    index = 0
    length = len(text)
    while index < length:
        base = text[index]
        index += 1
        marks = []
        while index < length and unicodedata.category(text[index]).startswith("M"):
            marks.append(text[index])
            index += 1
        cluster = base + "".join(marks)
        if _is_latin(base):
            if pending:
                result.append(unicodedata.normalize("NFC", "".join(pending)))
                pending = []
            result.append(_strip_latin_cluster(cluster, keep_nfc))
        else:
            # Buffered rather than emitted one cluster at a time: composing a
            # jamo sequence (L + V + T) into a syllable needs the whole run.
            pending.append(cluster)
    if pending:
        result.append(unicodedata.normalize("NFC", "".join(pending)))
    return "".join(result)
