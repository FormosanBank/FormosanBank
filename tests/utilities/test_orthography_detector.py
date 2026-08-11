"""Tests for QC/utilities/orthography_detector.py.

A *prosodic* accent (e.g. Glosbe's stress-marked Truku "máduk") should be
treated as its bare vowel when scoring, or it is miscounted as an "unexpected
token" and the true orthography is under-scored. But an accent that a
language's own orthography tables attest — Rukai's Ortho113 spells a vowel
``é`` — is a real orthographic letter and must survive stripping so it is
matched, not flattened. The detector therefore strips accents *except* those
attested for the language (or, when a dialect is set, that dialect).
"""
import unicodedata
from pathlib import Path

from QC.utilities.orthography_detector import (
    _attested_accents,
    calculate_orthography_score,
    extract_letters,
    extract_text_from_xml,
    load_orthography_data,
)

_ORTHOGRAPHIES_DIR = str(Path(__file__).resolve().parents[2] / "Orthographies")


def _write_xml(tmp_path, form_text: str, *, lang="trv", dialect="Truku"):
    xml = tmp_path / "sample.xml"
    xml.write_text(
        f'<TEXT xml:lang="{lang}" dialect="{dialect}">'
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


# --- Selective keep: accents attested by the orthography tables survive -------


def test_attested_accents_language_level_unions_all_dialects():
    """With no dialect, an accent counts as attested if any orthography for the
    language uses it (union across every dialect and table)."""
    lang_data = {
        "Maolin": {"Ortho113": {"é", "e", "a"}},
        "Wutai": {"Ortho113": {"e", "a"}},
        "default": {"Li": {"á", "e"}},
    }
    assert _attested_accents(lang_data, "") == frozenset({"é", "á"})


def test_attested_accents_dialect_narrows_to_that_dialect_plus_default():
    """A specified dialect keeps only accents attested for that dialect column
    (plus dialect-agnostic 'default' tables) — an accent NA for the dialect and
    absent from default is not kept."""
    lang_data = {
        "Maolin": {"Ortho113": {"é", "e"}},
        "Wutai": {"Ortho113": {"e"}},  # é is NA for Wutai
        "default": {"Church": {"e"}},  # dialect-agnostic, no accent
    }
    assert _attested_accents(lang_data, "Maolin") == frozenset({"é"})
    assert _attested_accents(lang_data, "Wutai") == frozenset()


def test_attested_accents_dialect_agnostic_table_applies_to_every_dialect():
    """An accent from a table with no dialect columns (stored under 'default')
    is attested for every dialect, including one whose own column omits it."""
    lang_data = {
        "Wutai": {"Ortho113": {"e"}},   # é NA for Wutai in Ortho113
        "default": {"Li": {"é", "e"}},  # but Li spells é for Rukai generally
    }
    assert _attested_accents(lang_data, "Wutai") == frozenset({"é"})


def test_attested_accents_unknown_dialect_falls_back_to_all():
    """A dialect not present in the tables behaves like no dialect: keep every
    attested accent (mirrors the detector testing all orthographies)."""
    lang_data = {
        "Maolin": {"Ortho113": {"é"}},
        "default": {"Church": {"e"}},
    }
    assert _attested_accents(lang_data, "Budai") == frozenset({"é"})


def test_rukai_orthographic_accent_is_kept_with_orthography_data(tmp_path):
    """End to end: Rukai's é is attested (Ortho113/Li), so with the tables
    loaded it survives stripping — while a prosodic breve is still removed."""
    ortho = load_orthography_data(_ORTHOGRAPHIES_DIR)
    xml = _write_xml(tmp_path, "élré dourŭk", lang="dru", dialect="Maolin")
    text, language, _ = extract_text_from_xml(xml, orthography_data=ortho)
    assert language == "dru"
    assert "é" in text, f"attested Rukai é should be kept; got {text!r}"
    # The breve is not attested for Rukai, so it is still flattened to a bare u.
    assert "douruk" in text, f"unattested breve should be stripped; got {text!r}"


def test_accents_all_stripped_without_orthography_data(tmp_path):
    """Back-compat: callers that pass no orthography data get every accent
    stripped, exactly as before (é included)."""
    xml = _write_xml(tmp_path, "élré", lang="dru", dialect="Maolin")
    text, _, _ = extract_text_from_xml(xml)
    decomposed = unicodedata.normalize("NFD", text)
    assert "́" not in decomposed, f"expected all accents stripped; got {text!r}"
    assert "elre" in text, f"expected bare vowels; got {text!r}"
