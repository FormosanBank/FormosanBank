"""Shared accent-stripping for Formosan orthography handling.

No Formosan orthography uses accents phonemically, so an accented vowel in a
source text (e.g. Glosbe marks stress: "máduk", "dálix") is just the plain
vowel wearing a diacritic. Two QC utilities need to treat it as the bare vowel:

- ``standardize.py`` strips accents from the *standard* tier before applying a
  conversion table, so a table entry keyed on the plain vowel still matches
  (the *original* tier keeps its exact source spelling and is never touched).
- ``orthography_detector.py`` strips accents before scoring, so an accented
  vowel is not miscounted as an "unexpected token" against an orthography that
  legitimately contains the plain vowel.

Only the combining marks actually seen in the corpora are listed. The stripping
logic is otherwise mark-agnostic, so extending coverage is just adding to the
set below.
"""
import unicodedata

ACCENTS_TO_STRIP = frozenset({
    "́",  # combining acute accent (á é í ó ú …)
    "̆",  # combining breve (ŭ …)
})


def strip_accents(text: str) -> str:
    """Remove ACCENTS_TO_STRIP from ``text``, leaving every base letter intact.

    Decomposes to NFD so precomposed accented vowels split into base + mark,
    drops the listed marks, then recomposes to NFC. Base letters that are
    distinct phonemes in their own right (ə, ʉ, ɨ, ŋ, …) are untouched because
    they carry no combining mark.
    """
    decomposed = unicodedata.normalize("NFD", text)
    without_accents = "".join(ch for ch in decomposed if ch not in ACCENTS_TO_STRIP)
    return unicodedata.normalize("NFC", without_accents)
