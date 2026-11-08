"""site_stats: statistics tables rendered from statistics/*.csv at build time."""

from pathlib import Path

import pytest

import site_stats

FIXTURES = Path(__file__).parent / "fixtures" / "statistics"
MULTI = {"Amis", "Babuza-Favorlang", "Seediq"}


@pytest.fixture
def rows():
    return site_stats.load_stats(FIXTURES)


def test_corpus_table_matches_legacy_format(rows):
    table = site_stats.corpus_table(rows, "Latham-1862", multi=MULTI)
    lines = table.splitlines()
    assert lines[0] == "| | Babuza-Favorlang<br>Favorlang | Siraya |"
    assert "| Word count | 31 | 16 |" in lines
    assert "| Total audio | 0 | 0 |" in lines
    # Written before the column existed: shown as missing, never as zero.
    assert f"| {site_stats.INDENT}Transcribed words | — | — |" in lines
    assert f"| {site_stats.INDENT}English | 31 | 16 |" in lines


def test_audio_hours_and_dialect_unknown_column(rows):
    table = site_stats.corpus_table(rows, "Mini", multi=MULTI)
    header = table.splitlines()[0]
    assert "Amis<br>Coastal" in header and "Amis<br>unknown" in header
    lines = table.splitlines()
    # Columns: Amis Coastal, Amis unknown, Seediq Tegudaya, Truku, Yami (ISO tao).
    assert f"| {site_stats.INDENT}Transcribed | 13.4h | 0 | 0 | 0 | 0 |" in lines
    assert "| Total audio | 13.4h | 1.0h | 0 | 0 | 0 |" in lines
    assert f"| {site_stats.INDENT}Transcribed words | 250 | 0 | 0 | 0 | 0 |" in lines


def test_truku_split_from_seediq(rows):
    header = site_stats.language_table(rows).splitlines()[0]
    assert "Truku" in header and "Seediq" in header


def test_dialect_table_unknown_column_and_order(rows):
    table = site_stats.dialect_table(rows, "Amis", multi=MULTI)
    assert table.splitlines()[0] == "| | Coastal | unknown |"
    assert "| Word count | 300 | 50 |" in table


def test_no_dialect_table_for_single_dialect_language(rows):
    assert site_stats.dialect_table(rows, "Thao", multi=MULTI) is None


def test_corpus_table_missing_csv(rows):
    assert site_stats.corpus_table(rows, "NoSuchCorpus", multi=MULTI) == site_stats.NOT_YET_COMPUTED


def test_parse_error_placeholder_row_dropped(rows):
    assert all(row["language"] for row in rows)


def test_unknown_language_code_raises(tmp_path):
    (tmp_path / "X_corpora_stats.csv").write_text(
        "language,dialect,word_count\nzzz,,5\n", encoding="utf-8"
    )
    with pytest.raises(KeyError, match="zzz"):
        site_stats.load_stats(tmp_path)


def test_multi_dialect_languages_from_registry():
    multi = site_stats.multi_dialect_languages()
    assert {"Amis", "Paiwan", "Rukai"} <= multi
    assert "Thao" not in multi and "Kavalan" not in multi
