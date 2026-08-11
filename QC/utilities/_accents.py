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
"""
import unicodedata
from typing import Iterable

ACCENTS_TO_STRIP = frozenset({
    "́",  # combining acute accent (á é í ó ú …)
    "̆",  # combining breve (ŭ …)
})


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


def strip_accents(text: str, keep: Iterable[str] = frozenset()) -> str:
    """Remove ACCENTS_TO_STRIP from ``text``, leaving every base letter intact.

    Decomposes to NFD so precomposed accented vowels split into base + mark,
    drops the listed marks, then recomposes to NFC. Base letters that are
    distinct phonemes in their own right (ə, ʉ, ɨ, ŋ, …) are untouched because
    they carry no combining mark.

    ``keep`` is an optional set of accented letters (matched in NFC form) that
    must survive stripping — the orthography attests them as real letters, so
    their diacritic is orthographic, not prosodic. Grapheme clusters whose NFC
    form is in ``keep`` pass through unchanged; every other cluster has its
    strip-marks removed as before.
    """
    keep_nfc = frozenset(unicodedata.normalize("NFC", letter) for letter in keep)

    decomposed = unicodedata.normalize("NFD", text)
    result = []
    index = 0
    length = len(decomposed)
    while index < length:
        base = decomposed[index]
        index += 1
        marks = []
        while index < length and unicodedata.category(decomposed[index]).startswith("M"):
            marks.append(decomposed[index])
            index += 1
        cluster = unicodedata.normalize("NFC", base + "".join(marks))
        if cluster in keep_nfc:
            result.append(cluster)
        else:
            kept_marks = [mark for mark in marks if mark not in ACCENTS_TO_STRIP]
            result.append(unicodedata.normalize("NFC", base + "".join(kept_marks)))
    return "".join(result)
