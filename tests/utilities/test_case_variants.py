"""Tests for QC/utilities/_case_variants.py.

Case-variant derivation lets conversion tables list only lowercase rules;
standardize.py derives Title/ALL-CAPS variants unless the capital is a
distinct grapheme of the source orthography (per the source profile,
resolved from the table's filename).
Spec: docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md
"""
from pathlib import Path

from QC.utilities._case_variants import (
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
