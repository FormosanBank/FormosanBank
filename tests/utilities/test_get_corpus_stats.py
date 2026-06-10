# tests/utilities/test_get_corpus_stats.py
"""End-to-end tests for QC/utilities/get_corpus_stats.py.

The script is run via subprocess (repo convention). The fixture corpus
is copied to tmp_path/Corpora/MiniCorpus/ so the script's repo-root
derivation (the path component before 'Corpora') lands on tmp_path and
the CSV goes to tmp_path/statistics/."""
import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "utilities" / "get_corpus_stats.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus"


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
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


def test_csv_contents(mini_corpus, tmp_path):
    result = _run([str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    rows = _read_rows(tmp_path)

    haian = rows[("ami", "Haian")]
    assert int(haian["word_count"]) == 5
    assert int(haian["sentences"]) == 3
    assert int(haian["segmented_words"]) == 3
    assert int(haian["glossed_words"]) == 3
    assert int(haian["eng_transl_count"]) == 5
    assert int(haian["zho_transl_count"]) == 3
    assert int(haian["file_count"]) == 1

    truku = rows[("trv", "Truku")]
    assert int(truku["word_count"]) == 2
    assert int(truku["transcribed_audio_count"]) == 1
    assert int(truku["untranscribed_audio_count"]) == 1
    # No prior CSV to carry from, and this script never computes durations
    # (that's update_audio_stats.py's job) — seconds are zero.
    assert float(truku["transcribed_audio_seconds"]) == 0.0
    assert float(truku["untranscribed_audio_seconds"]) == 0.0

    assert int(rows[("trv", "unknown")]["word_count"]) == 3
    assert int(rows[("ami", "")]["word_count"]) == 1

    # Parse-error pseudo-row: zero in all Gitbook-displayed fields so
    # update_corpus_stats.py's row_has_data() filters it out.
    err = rows[("", "")]
    assert int(err["parse_errors"]) == 1
    assert int(err["word_count"]) == 0

    # Gitbook contract: every column its update_corpus_stats.py reads exists.
    for col in ("language", "dialect", "word_count", "segmented_words",
                "glossed_words", "eng_transl_count", "zho_transl_count",
                "transcribed_audio_count", "transcribed_audio_seconds",
                "untranscribed_audio_count", "untranscribed_audio_seconds",
                "file_count"):
        assert col in haian


def test_audio_seconds_carried_from_existing_csv(mini_corpus, tmp_path):
    # Seconds columns are a manually-maintained value (update_audio_stats.py);
    # re-running get_corpus_stats must preserve them while recomputing counts.
    stats_dir = tmp_path / "statistics"
    stats_dir.mkdir()
    seed = stats_dir / "MiniCorpus_corpora_stats.csv"
    seed.write_text(
        "language,dialect,segmented_words,glossed_words,"
        "transcribed_audio_count,transcribed_audio_seconds,"
        "untranscribed_audio_count,untranscribed_audio_seconds,"
        "eng_transl_count,zho_transl_count,word_count,file_count\n"
        "trv,Truku,0,0,1,99.0,1,42.0,0,0,2,1\n"
    )
    result = _run([str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    truku = _read_rows(tmp_path)[("trv", "Truku")]
    assert float(truku["transcribed_audio_seconds"]) == pytest.approx(99.0)
    assert float(truku["untranscribed_audio_seconds"]) == pytest.approx(42.0)
    assert int(truku["transcribed_audio_count"]) == 1  # recomputed from XML


def test_strict_fails_on_parse_error(mini_corpus):
    result = _run([str(mini_corpus), "--strict"])
    assert result.returncode == 1
    assert "bad.xml" in result.stderr


def test_warnings_reported_on_stderr(mini_corpus):
    result = _run([str(mini_corpus)])
    assert "missing dialect" in result.stderr
