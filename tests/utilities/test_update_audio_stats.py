# tests/utilities/test_update_audio_stats.py
"""update_audio_stats.py rewrites ONLY the audio-seconds columns of an
existing per-corpus CSV, computed from audio files on disk. Run manually;
CI never runs it (no audio on the runner)."""
import csv
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


@pytest.fixture
def mini_corpus(tmp_path):
    corpus = tmp_path / "Corpora" / "MiniCorpus"
    shutil.copytree(FIXTURE, corpus)
    return corpus


def _read_rows(tmp_path):
    csv_path = tmp_path / "statistics" / "MiniCorpus_corpora_stats.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {(r["language"], r["dialect"]): r for r in csv.DictReader(f)}


def test_updates_seconds_in_place(mini_corpus, tmp_path, audio_file_factory):
    audio_dir = mini_corpus / "Audio"
    audio_dir.mkdir()
    shutil.copy(audio_file_factory(duration_sec=1.0), audio_dir / "clip.wav")
    shutil.copy(audio_file_factory(duration_sec=2.0), audio_dir / "full.wav")

    # Seed the CSV with get_corpus_stats (seconds start at 0).
    result = _run(GET_STATS, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    before = _read_rows(tmp_path)
    assert float(before[("trv", "Truku")]["transcribed_audio_seconds"]) == 0.0

    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    rows = _read_rows(tmp_path)
    truku = rows[("trv", "Truku")]
    assert float(truku["transcribed_audio_seconds"]) == pytest.approx(1.0, abs=0.1)
    assert float(truku["untranscribed_audio_seconds"]) == pytest.approx(2.0, abs=0.1)
    # Everything else untouched.
    assert int(truku["word_count"]) == 2
    assert int(truku["transcribed_audio_count"]) == 1
    assert rows[("ami", "Haian")] == before[("ami", "Haian")]


def test_missing_csv_is_an_error(mini_corpus):
    # No prior get_corpus_stats run: nothing to update.
    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 1
    assert "get_corpus_stats" in result.stderr  # tells the user what to run first


def test_no_audio_on_disk_warns_and_keeps_seconds(mini_corpus, tmp_path):
    # Audio referenced in XML but not downloaded: keep existing seconds
    # rather than silently zeroing them out.
    result = _run(GET_STATS, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    csv_path = tmp_path / "statistics" / "MiniCorpus_corpora_stats.csv"
    # Adaptation: actual CSV uses "0.0" not "0" for the seconds columns.
    text = csv_path.read_text().replace("trv,Truku,0,0,1,0.0,1,0.0", "trv,Truku,0,0,1,55.0,1,66.0")
    csv_path.write_text(text)

    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    assert "not found on disk" in result.stderr
    truku = _read_rows(tmp_path)[("trv", "Truku")]
    assert float(truku["transcribed_audio_seconds"]) == pytest.approx(55.0)
    assert float(truku["untranscribed_audio_seconds"]) == pytest.approx(66.0)
