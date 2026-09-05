"""Tests for QC/utilities/_accents.py.

``strip_accents`` removes source prosody (Glosbe-style stress marks) from the
standard tier and from orthography-detector input. Every Formosan orthography is
Latin, so stripping is a **Latin-script-only** operation: a Korean name, a
Chinese quotation or a Cyrillic gloss quoted in a Wikipedia article must come
out byte-identical, and NFC-composed — an earlier blanket-NFD implementation
left Hangul syllables as runs of conjoining jamo in 27 Wikipedias articles.
"""
import unicodedata

import pytest

from QC.utilities._accents import ALWAYS_KEEP, ACCENTS_TO_STRIP, accented_letters, strip_accents

# Korean strings written the way a source text has them (precomposed / NFC).
SEOUL = "서울"
HANGUL_NAME = "김대중"


def _has_combining(text: str) -> bool:
    return any(unicodedata.category(char).startswith("M") for char in text)


# --- Latin behavior is unchanged ------------------------------------------

@pytest.mark.parametrize("accented,plain", [
    ("á", "a"),
    ("é", "e"),
    ("í", "i"),
    ("ó", "o"),
    ("ú", "u"),
    ("ŭ", "u"),
    ("ā", "a"),
    ("ē", "e"),
    ("ō", "o"),
    ("máduk", "maduk"),
    ("dálix búyas", "dalix buyas"),
])
def test_latin_strip_marks_are_removed(accented, plain):
    assert strip_accents(accented) == plain


@pytest.mark.parametrize("letter", ["ê", "ñ", "ä", "ü", "ç"])
def test_latin_marks_outside_the_strip_set_are_kept_composed(letter):
    """Only ACCENTS_TO_STRIP is removed; other Latin diacritics survive, NFC."""
    out = strip_accents(letter)
    assert out == unicodedata.normalize("NFC", letter)
    assert len(out) == 1, f"{letter!r} came back decomposed: {out!r}"


def test_latin_decomposed_input_is_stripped_and_recomposed():
    """NFD Latin input: strip-mark dropped, surviving mark recomposed."""
    assert strip_accents(unicodedata.normalize("NFD", "á")) == "a"
    assert strip_accents(unicodedata.normalize("NFD", "ñ")) == "ñ"


def test_bare_phoneme_letters_are_untouched():
    """ə ʉ ɨ ŋ ʔ carry no combining mark and are Latin-script: unchanged."""
    text = "ə ʉ ɨ ŋ ʔ ʡ"
    assert strip_accents(text) == text


def test_keep_protects_an_attested_orthographic_accent():
    """Rukai's Ortho113 ``é`` is a real letter, so ``keep`` must preserve it."""
    assert strip_accents("é á", keep={"é"}) == "é a"
    assert strip_accents(unicodedata.normalize("NFD", "é"), keep={"é"}) == "é"


def test_accented_letters_selects_strip_mark_bearers():
    assert accented_letters(["é", "a", "ŭ", "ŋ", "ä"]) == frozenset({"é", "ŭ"})


# --- Non-Latin scripts are never touched ----------------------------------

def test_precomposed_hangul_is_unchanged():
    assert strip_accents(SEOUL) == SEOUL
    assert strip_accents(HANGUL_NAME) == HANGUL_NAME


def test_decomposed_hangul_input_comes_back_composed():
    """The regression: NFD Hangul must not be left as conjoining jamo."""
    decomposed = unicodedata.normalize("NFD", SEOUL)
    assert decomposed != SEOUL, "test precondition: NFD really decomposes Hangul"
    assert strip_accents(decomposed) == SEOUL


def test_hangul_output_is_nfc_stable():
    out = strip_accents(unicodedata.normalize("NFD", HANGUL_NAME))
    assert out == unicodedata.normalize("NFC", out) == HANGUL_NAME


@pytest.mark.parametrize("text", [
    "臺灣原住民族",          # CJK
    "日本語のカタカナとひらがな",  # kana
    "Русский язык",          # Cyrillic
    "Ελληνικά",              # Greek
    "العربية",                # Arabic
    "देवनागरी",                 # Devanagari
    "ภาษาไทย",                # Thai
    "עברית",                  # Hebrew
])
def test_non_latin_scripts_pass_through_byte_identical(text):
    assert strip_accents(text) == text


def test_non_latin_combining_marks_survive():
    """A combining acute on a Cyrillic/Greek base is script, not source prosody."""
    cyrillic_stress = "и" + "́"
    assert strip_accents(cyrillic_stress) == unicodedata.normalize("NFC", cyrillic_stress)
    assert _has_combining(unicodedata.normalize("NFD", strip_accents(cyrillic_stress)))

    greek = "ά"  # precomposed alpha with tonos
    assert strip_accents(greek) == greek


def test_keep_does_not_leak_into_non_latin_handling():
    assert strip_accents(SEOUL + " á", keep={"é"}) == SEOUL + " a"


# --- Mixed text ------------------------------------------------------------

def test_mixed_latin_and_hangul_strips_only_the_latin_part():
    text = f"máduk {SEOUL} dálix"
    assert strip_accents(text) == f"maduk {SEOUL} dalix"


def test_mixed_text_keeps_hangul_composed_even_when_input_is_decomposed():
    text = f"máduk {unicodedata.normalize('NFD', SEOUL)} dálix"
    assert strip_accents(text) == f"maduk {SEOUL} dalix"


def test_adjacent_hangul_and_latin_without_separator():
    text = f"{SEOUL}á{SEOUL}"
    assert strip_accents(text) == f"{SEOUL}a{SEOUL}"


def test_punctuation_digits_and_whitespace_are_preserved():
    text = 'Taywan 1984, "a-b" — (x)\t\n'
    assert strip_accents(text) == text


# --- Idempotence -----------------------------------------------------------

@pytest.mark.parametrize("text", [
    "máduk dálix",
    SEOUL,
    unicodedata.normalize("NFD", SEOUL),
    f"máduk {SEOUL} 臺灣 Русский ά",
    "ê ō ñ ə ʉ",
    "",
])
def test_idempotent(text):
    once = strip_accents(text)
    assert strip_accents(once) == once


def test_idempotent_with_keep():
    once = strip_accents(f"é á {SEOUL}", keep={"é"})
    assert strip_accents(once, keep={"é"}) == once


def test_no_strip_mark_survives_on_latin_text():
    out = unicodedata.normalize("NFD", strip_accents("máduk dálix dourŭk"))
    assert not any(mark in out for mark in ACCENTS_TO_STRIP)



# --- macron ---------------------------------------------------------------
# The macron is prosodic or loanword notation in most of the bank (Saisiyat,
# Amis, Truku, Atayal, Paiwan all carry macrons while attesting no macron
# letter) but is a real letter in Puyuma, Siraya and Favorlang. It is therefore
# only safe to strip alongside a keep set.

def test_macron_is_stripped_by_default():
    # Mandarin kin terms quoted in Paiwan; Paiwan attests no macron letter.
    assert strip_accents("āyí") == "ayi"
    assert strip_accents("yípó") == "yipo"


def test_attested_macron_letter_survives():
    # Puyuma's reference orthography lists 'ē' beside plain 'e'.
    assert strip_accents("sēhu", keep={"ē"}) == "sēhu"
    assert strip_accents("sēhu") == "sehu"


def test_no_unconditional_keep_set():
    """There is no hardcoded exception list, and none is needed.

    ALWAYS_KEEP held Siraya's 'ae-ligature-macron' and Favorlang's 'g-macron'
    because neither language has a designated standard orthography. The
    vowels-only rule protects the Favorlang letter structurally -- 'g' is a
    consonant -- and neither corpus is standardized by the shared tool anyway.
    When either language gains a standards.csv orthography, that table will
    list its letters and standard_orthography_accents will keep them."""
    assert ALWAYS_KEEP == frozenset()
    assert strip_accents("pa\u1e21a") == "pa\u1e21a"      # consonant: never stripped
    assert strip_accents("\u01e3uh") == "\u00e6uh"        # vowel: stripped, absent a table
    assert strip_accents("\u01e3uh", keep={"\u01e3"}) == "\u01e3uh"


def test_only_vowels_are_stripped():
    """A prosodic mark sits on a vowel; a diacritic on a consonant is part of
    the letter. This is what keeps Slavic, Turkish and transcription letters
    intact without an exception list."""
    assert strip_accents("t\u00faturu") == "tuturu"        # vowel + acute
    assert strip_accents("dour\u016dk") == "douruk"        # vowel + breve
    assert strip_accents("\u0101y\u00ed") == "ayi"        # vowel + macron, vowel + acute
    for consonant_word in ("Nikoli\u0107", "i\u0159a", "\u011fa", "\u015bin", "\u0144a"):
        assert strip_accents(consonant_word) == consonant_word, consonant_word
    # 'y' and 'w' are glides in these orthographies, not vowels.
    assert strip_accents("\u00fdnna") == "\u00fdnna"


def test_bare_bases_are_untouched():
    """A base letter carries no strip-mark, so it is never rewritten."""
    assert strip_accents("æ") == "æ"
    assert strip_accents("g") == "g"


def test_macron_on_non_latin_is_untouched():
    assert strip_accents("稲葉浩志") == "稲葉浩志"


def test_accented_letters_reports_macron_letters():
    assert accented_letters({"e", "ē", "a"}) == frozenset({"ē"})
