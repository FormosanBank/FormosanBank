# tests/utilities/test_audio_durations.py
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "audio_durations",
    Path(__file__).resolve().parents[2] / "QC" / "utilities" / "audio_durations.py",
)
audio_durations = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(audio_durations)


def _write(stats_dir, text):
    stats_dir.mkdir(parents=True, exist_ok=True)
    (stats_dir / "audio_durations.csv").write_text(text, encoding="utf-8")


HEADER = ("corpus,language,dialect,transcribed_audio_seconds,untranscribed_audio_seconds,"
          "transcribed_audio_count,untranscribed_audio_count,computed_at\n")


def test_load_for_corpus_filters_and_keys(tmp_path):
    _write(tmp_path, HEADER
           + "ePark,ami,Coastal,100.0,0.0,5,0,2026-06-10\n"
           + "Other,tay,Sekolik,9.0,0.0,3,0,2026-06-10\n")
    got = audio_durations.load_for_corpus(tmp_path, "ePark")
    assert set(got) == {("ami", "Coastal")}
    assert got[("ami", "Coastal")]["transcribed_audio_seconds"] == 100.0
    assert got[("ami", "Coastal")]["transcribed_audio_count"] == 5


def test_load_for_corpus_missing_file_is_empty(tmp_path):
    assert audio_durations.load_for_corpus(tmp_path, "ePark") == {}


def test_is_stale_no_entry_with_audio():
    assert audio_durations.is_stale(3, 0, None) is True
    assert audio_durations.is_stale(0, 0, None) is False


def test_is_stale_count_mismatch_and_match():
    entry = {"transcribed_audio_count": 5, "untranscribed_audio_count": 0}
    assert audio_durations.is_stale(5, 0, entry) is False
    assert audio_durations.is_stale(7, 0, entry) is True


def test_is_stale_blank_count_is_stale():
    entry = {"transcribed_audio_count": None, "untranscribed_audio_count": None}
    assert audio_durations.is_stale(5, 0, entry) is True


def test_upsert_replaces_corpus_rows_keeps_others(tmp_path):
    _write(tmp_path, HEADER
           + "ePark,ami,Coastal,100.0,0.0,5,0,2026-06-10\n"
           + "Other,tay,Sekolik,9.0,0.0,3,0,2026-06-10\n")
    audio_durations.upsert_audio_durations(
        tmp_path, "ePark",
        [{"language": "ami", "dialect": "Coastal",
          "transcribed_audio_seconds": 200.0, "untranscribed_audio_seconds": 0.0,
          "transcribed_audio_count": 6, "untranscribed_audio_count": 0}],
        computed_at="2026-06-12",
    )
    rows = audio_durations.load_audio_durations(tmp_path)
    assert rows[("ePark", "ami", "Coastal")]["transcribed_audio_seconds"] == 200.0
    assert rows[("ePark", "ami", "Coastal")]["transcribed_audio_count"] == 6
    assert ("Other", "tay", "Sekolik") in rows  # untouched


def test_upsert_creates_file_when_missing(tmp_path):
    audio_durations.upsert_audio_durations(
        tmp_path, "NewCorpus",
        [{"language": "ami", "dialect": "Coastal",
          "transcribed_audio_seconds": 10.0, "untranscribed_audio_seconds": 0.0,
          "transcribed_audio_count": 2, "untranscribed_audio_count": 0}],
        computed_at="2026-06-12",
    )
    rows = audio_durations.load_audio_durations(tmp_path)
    assert ("NewCorpus", "ami", "Coastal") in rows
