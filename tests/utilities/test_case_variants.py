"""Tests for QC/utilities/_case_variants.py.

Case-variant derivation lets conversion tables list only lowercase rules;
standardize.py derives Title/ALL-CAPS variants unless the capital is a
distinct grapheme of the source orthography (per the source profile,
resolved from the table's filename).
Spec: docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md
"""
import pytest

from QC.utilities._case_variants import (
    derive_case_variants,
    load_profile_graphemes,
    resolve_source_profile,
)


def _table(tmp_path, name):
    conv = tmp_path / "Orthographies" / "ConversionTables"
    conv.mkdir(parents=True, exist_ok=True)
    path = conv / name
    path.write_text("original\tstandard\n", encoding="utf-8")
    return path


def test_scheme_token_94_maps_to_ortho94_folder(tmp_path):
    table = _table(tmp_path, "Amis_94_113.tsv")
    assert resolve_source_profile(table) == (
        tmp_path / "Orthographies" / "Ortho94" / "Amis.tsv"
    )


def test_scheme_token_113lib_maps_to_ortho113liberal_folder(tmp_path):
    table = _table(tmp_path, "Amis_113lib_113.tsv")
    assert resolve_source_profile(table) == (
        tmp_path / "Orthographies" / "Ortho113Liberal" / "Amis.tsv"
    )


def test_named_scheme_token_is_the_folder_itself(tmp_path):
    table = _table(tmp_path, "Rukai_Li_113.tsv")
    assert resolve_source_profile(table) == (
        tmp_path / "Orthographies" / "Li" / "Rukai.tsv"
    )


def test_nonconforming_basename_returns_none(tmp_path):
    table = _table(tmp_path, "tiny_mapping.tsv")
    assert resolve_source_profile(table) is None


def test_table_outside_conversiontables_dir_returns_none(tmp_path):
    path = tmp_path / "Amis_94_113.tsv"
    path.write_text("original\tstandard\n", encoding="utf-8")
    assert resolve_source_profile(path) is None


def test_resolution_does_not_require_the_profile_to_exist(tmp_path):
    """resolve returns the conventional path; existence is the caller's check."""
    table = _table(tmp_path, "Kavalan_MinEd_113.tsv")
    profile = resolve_source_profile(table)
    assert profile == tmp_path / "Orthographies" / "MinEd" / "Kavalan.tsv"
    assert not profile.exists()


def test_load_profile_graphemes_reads_letter_column(tmp_path):
    profile = tmp_path / "Rukai.tsv"
    profile.write_text(
        "letter\tWutai\tDona\nT\ttr\ttr\nng\tŋ\tŋ\n\t\t\n",
        encoding="utf-8",
    )
    assert load_profile_graphemes(profile) == {"T", "ng"}


def test_load_profile_graphemes_raises_without_letter_column(tmp_path):
    """A missing 'letter' column must fail loudly, not return an empty set.

    An empty set reads to the caller as "no phonemic capitals" and lets
    derivation run with zero suppression -- the exact failure this
    machinery exists to prevent.
    """
    profile = tmp_path / "Rukai.tsv"
    profile.write_text(
        "grapheme\tWutai\tDona\nT\ttr\ttr\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_profile_graphemes(profile)


def test_title_and_allcaps_variants_derived_for_digraph():
    rules = [("ng", "ŋ")]
    assert derive_case_variants(rules, set()) == [
        ("ng", "ŋ"),
        ("Ng", "Ŋ"),   # title: first char of replacement uppercased
        ("NG", "Ŋ"),   # ALL-CAPS: whole replacement uppercased
    ]


def test_single_letter_source_gets_one_variant():
    """Title and ALL-CAPS coincide for one-letter sources — no duplicate."""
    assert derive_case_variants([("o", "u")], set()) == [("o", "u"), ("O", "U")]


def test_explicit_uppercase_row_suppresses_derivation():
    rules = [("ng", "ŋ"), ("Ng", "ŋ")]
    assert derive_case_variants(rules, set()) == [
        ("ng", "ŋ"),
        ("NG", "Ŋ"),   # ALL-CAPS still derived; title was explicit
        ("Ng", "ŋ"),   # explicit row kept verbatim, in place
    ]


def test_profile_grapheme_suppresses_derivation():
    """Li Rukai: T is phonemic — t's rule must not spawn a T variant."""
    assert derive_case_variants([("t", "c")], {"T"}) == [("t", "c")]


def test_uncased_source_is_not_derived():
    assert derive_case_variants([("'", "q")], set()) == [("'", "q")]


def test_mixed_case_source_is_not_derived():
    """Only fully-lowercase sources derive variants."""
    assert derive_case_variants([("Ng", "ŋ")], set()) == [("Ng", "ŋ")]


def test_caseless_replacement_passes_through():
    """A cased source with an uncased replacement still derives variants."""
    assert derive_case_variants([("q", "ʔ")], set()) == [
        ("q", "ʔ"),
        ("Q", "ʔ"),
    ]


def test_empty_replacement_deletion_rule():
    assert derive_case_variants([("h", "")], set()) == [("h", ""), ("H", "")]


def test_variants_inserted_immediately_after_parent():
    rules = [("o", "u"), ("ng", "ŋ")]
    assert derive_case_variants(rules, set()) == [
        ("o", "u"),
        ("O", "U"),
        ("ng", "ŋ"),
        ("Ng", "Ŋ"),
        ("NG", "Ŋ"),
    ]


def test_input_list_is_not_mutated():
    rules = [("o", "u")]
    derive_case_variants(rules, set())
    assert rules == [("o", "u")]
