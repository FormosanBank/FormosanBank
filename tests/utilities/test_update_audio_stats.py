# tests/utilities/test_update_audio_stats.py
"""update_audio_stats.py writes audio durations to statistics/audio_durations.csv
(the truth file). Run manually; CI never runs it (no audio on the runner)."""
import importlib.util as _ilu
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
UPDATE = REPO_ROOT / "QC" / "utilities" / "update_audio_stats.py"
GET_STATS = REPO_ROOT / "QC" / "utilities" / "get_corpus_stats.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus"


def _run(script, args):
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )


def _load_ad():
    """Load audio_durations module via importlib."""
    spec = _ilu.spec_from_file_location(
        "audio_durations",
        REPO_ROOT / "QC" / "utilities" / "audio_durations.py")
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def mini_corpus(tmp_path):
    corpus = tmp_path / "Corpora" / "MiniCorpus"
    shutil.copytree(FIXTURE, corpus)
    return corpus


def test_updates_seconds_in_truth_file(mini_corpus, tmp_path, audio_file_factory):
    """update_corpus writes seconds into the audio_durations truth file."""
    audio_dir = mini_corpus / "Audio"
    audio_dir.mkdir()
    shutil.copy(audio_file_factory(duration_sec=1.0), audio_dir / "clip.wav")
    shutil.copy(audio_file_factory(duration_sec=2.0), audio_dir / "full.wav")

    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr

    stats_dir = tmp_path / "statistics"
    ad = _load_ad()
    rows = ad.load_for_corpus(stats_dir, "MiniCorpus")
    truku = rows[("trv", "Truku")]
    assert truku["transcribed_audio_seconds"] == pytest.approx(1.0, abs=0.1)
    assert truku["untranscribed_audio_seconds"] == pytest.approx(2.0, abs=0.1)
    assert truku["transcribed_audio_count"] == 1
    assert truku["untranscribed_audio_count"] == 1
    # ami/Haian has no audio elements: it should not appear in the truth file.
    assert ("ami", "Haian") not in rows


def test_no_audio_on_disk_warns_and_keeps_seconds(mini_corpus, tmp_path):
    # Audio referenced in XML but not downloaded: keep existing seconds
    # rather than silently zeroing them out.
    # Pre-seed the truth file with known good seconds for trv/Truku.
    ad = _load_ad()
    stats_dir = tmp_path / "statistics"
    stats_dir.mkdir(parents=True, exist_ok=True)
    ad.upsert_audio_durations(stats_dir, "MiniCorpus", [
        {"language": "trv", "dialect": "Truku",
         "transcribed_audio_seconds": 55.0,
         "untranscribed_audio_seconds": 66.0,
         "transcribed_audio_count": 1,
         "untranscribed_audio_count": 1}], "2000-01-01")

    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    assert "not found on disk" in result.stderr
    rows = ad.load_for_corpus(stats_dir, "MiniCorpus")
    truku = rows[("trv", "Truku")]
    assert truku["transcribed_audio_seconds"] == pytest.approx(55.0)
    assert truku["untranscribed_audio_seconds"] == pytest.approx(66.0)
    assert truku["transcribed_audio_count"] == 1
    assert truku["untranscribed_audio_count"] == 1


def test_update_writes_truth_file_with_counts(tmp_path):
    # One corpus, one wav of known duration, one transcribed AUDIO referencing it.
    import importlib.util, wave, struct
    corpus = tmp_path / "Corpora" / "Mini"
    xml_dir = corpus / "XML" / "Amis"; xml_dir.mkdir(parents=True)
    audio_dir = corpus / "Audio" / "Amis"; audio_dir.mkdir(parents=True)
    # 1.0s wav: 8000 frames at 8000 Hz.
    with wave.open(str(audio_dir / "a.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
        w.writeframes(struct.pack("<8000h", *([0] * 8000)))
    (xml_dir / "a.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1"><FORM kindOf="standard">w</FORM><AUDIO file="a.wav"/></S></TEXT>',
        encoding="utf-8")
    stats_dir = tmp_path / "statistics"; stats_dir.mkdir()
    # A pre-existing per-corpus CSV is NOT required anymore; the truth file is created on demand.

    spec = importlib.util.spec_from_file_location(
        "update_audio_stats",
        Path(__file__).resolve().parents[2] / "QC" / "utilities" / "update_audio_stats.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    rc = mod.update_corpus(corpus, computed_at="2026-06-12")
    assert rc == 0

    ad = _load_ad()
    rows = ad.load_for_corpus(stats_dir, "Mini")
    assert rows[("ami", "Coastal")]["transcribed_audio_seconds"] == 1.0
    assert rows[("ami", "Coastal")]["transcribed_audio_count"] == 1
