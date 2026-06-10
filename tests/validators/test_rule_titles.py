"""Tests for QC/validation/_rule_titles.

Human-readable mnemonics for rule ids, derived from the rule functions'
names (v<NNN>_<mnemonic>) so they never drift from the implementation.
Surfaced in the terminal summary and as a CSV column.
"""
from QC.validation._rule_titles import rule_titles


def test_titles_derived_from_function_names():
    t = rule_titles()
    assert t["V060"] == "W_count_matches_word_count"
    assert t["V061"] == "M_count_matches_form_segmentation"
    assert t["V068"] == "M_reconstructs_W"
    assert t["V141"] == "W_reconstructs_S"


def test_titles_cover_hard_and_text_rules():
    t = rule_titles()
    assert t["V110"] == "smart_quotes"
    assert t["V035"] == "xml_lang_is_iso_639_3"


def test_schema_rule_has_a_manual_title():
    # V000 is emitted inline (XSD/parse failures), not via a named function.
    assert "schema" in rule_titles()["V000"].lower()


def test_every_title_is_nonempty():
    assert all(v for v in rule_titles().values())
