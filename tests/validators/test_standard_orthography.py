"""Tests for the per-language standard-orthography registry (standards.csv).

The registry declares each language's designated standard orthography (an
Orthographies/<scheme> folder name) as data, with a blank value meaning "no
standard designated yet". Consumed by QC/utilities/add_phonology.py.
"""
import pytest

from QC.validation._dialect_inventory import (
    ISO_TO_LANGUAGE,
    _load_standard_map,
    standard_orthography,
)


def test_every_known_language_has_a_standard_row():
    """Adding a language to ISO_TO_LANGUAGE must not silently skip the registry."""
    for language in ISO_TO_LANGUAGE.values():
        # Resolves without raising (value may be a scheme name or None).
        standard_orthography(language)


def test_standard_orthography_returns_the_designated_scheme():
    assert standard_orthography("Amis") == "Ortho113"


def test_unknown_language_raises():
    with pytest.raises(KeyError):
        standard_orthography("Klingon")


def test_blank_value_parses_to_none(tmp_path):
    """A blank standard_orthography cell means 'no standard designated yet'."""
    csv_path = tmp_path / "standards.csv"
    csv_path.write_text(
        "language,standard_orthography\nAmis,Ortho113\nSiraya,\n",
        encoding="utf-8",
    )
    mapping = _load_standard_map(csv_path)
    assert mapping["Amis"] == "Ortho113"
    assert mapping["Siraya"] is None
