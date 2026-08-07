"""Tests for QC/utilities/orthography_detector.py.

No Formosan orthography uses accents phonemically, so the detector must treat
an accented vowel as its bare vowel when scoring text against an orthography.
Otherwise an accent-marked source (e.g. Glosbe's stress-marked Truku "máduk")
is miscounted as an "unexpected token" and the true orthography is under-scored.
"""
import unicodedata

from QC.utilities.orthography_detector import (
    calculate_orthography_score,
    extract_letters,
    extract_text_from_xml,
)


def _write_xml(tmp_path, form_text: str):
    xml = tmp_path / "sample.xml"
    xml.write_text(
        '<TEXT xml:lang="trv" dialect="Truku">'
        f'<S id="1"><FORM kindOf="original">{form_text}</FORM></S></TEXT>',
        encoding="utf-8",
    )
    return str(xml)


def test_extracted_text_has_accents_stripped(tmp_path):
    """Accented vowels are normalized to their base vowel before analysis."""
    xml = _write_xml(tmp_path, "máduk dálix búyas dourŭk")
    text, language, dialect = extract_text_from_xml(xml)
    assert language == "trv"
    # The bare vowels survive; no combining acute or breve remains.
    decomposed = unicodedata.normalize("NFD", text)
    assert "́" not in decomposed and "̆" not in decomposed, (
        f"detector text still carries a combining accent: {text!r}"
    )
    assert "maduk" in text and "dalix" in text and "douruk" in text, (
        f"expected accent-free vowels in extracted text; got {text!r}"
    )


def test_accented_vowel_is_not_counted_as_unexpected_token(tmp_path):
    """Statistics use the accent-free vowel: an accented vowel counts as its
    base letter, so it is matched (not flagged as an unexpected token) against
    an orthography that contains the plain vowel."""
    # Orthography for a language whose inventory is exactly the plain letters
    # of "maduk". The source spells it with a stress accent ("máduk").
    orthography_letters = {"m", "a", "d", "u", "k"}
    xml = _write_xml(tmp_path, "máduk")

    text, _, _ = extract_text_from_xml(xml)
    text_letters, letter_counts = extract_letters(text)
    result = calculate_orthography_score(
        text_letters, orthography_letters, letter_counts, text
    )
    match_score, _matched, _unexpected_types, _unexpected_pct, _eff, unexpected_tokens, _common = result

    assert "á" not in unexpected_tokens and "́" not in "".join(unexpected_tokens), (
        f"accented vowel leaked into orthography statistics: {unexpected_tokens!r}"
    )
    assert letter_counts.get("a", 0) == 1, (
        f"the accented 'á' should be counted as a bare 'a'; counts={dict(letter_counts)!r}"
    )
    # Every letter is now in the orthography, so nothing is unexpected.
    assert not unexpected_tokens, f"expected no unexpected tokens; got {unexpected_tokens!r}"
    # Score is an internal ratio (~1.0 for a full match; the CLI multiplies by
    # 100 for display). With the accent stripped it must be a strong match,
    # not the negative score an unexpected token drags it to.
    assert match_score > 0.99, f"expected a near-perfect match; got {match_score}"
