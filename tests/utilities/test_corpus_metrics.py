# tests/utilities/test_corpus_metrics.py
"""corpus_metrics.py --stats-dir: aggregate per-corpus CSVs (the inverted
pipeline) and append one history row per run at HEAD."""
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "corpus_metrics.py"

CSV_HEADER = (
    "language,dialect,segmented_words,glossed_words,"
    "transcribed_audio_count,transcribed_audio_seconds,"
    "untranscribed_audio_count,untranscribed_audio_seconds,"
    "eng_transl_count,zho_transl_count,word_count,file_count,"
    "sentences,word_elements,morpheme_elements,translation_elements,"
    "audio_elements,parse_errors\n"
)


def _write_stats(stats_dir: Path):
    stats_dir.mkdir()
    (stats_dir / "MiniCorpus_corpora_stats.csv").write_text(
        CSV_HEADER
        + ",,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1\n"
        + "ami,,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0\n"
        + "ami,Haian,3,3,0,0,0,0,5,3,5,1,3,3,1,5,0,0\n"
        + "trv,Truku,0,0,1,1.0,1,2.0,0,0,2,1,1,0,0,0,2,0\n"
        + "trv,unknown,0,0,0,0,0,0,0,0,3,1,1,0,0,0,0,0\n"
    )
    (stats_dir / "OtherCorpus_corpora_stats.csv").write_text(
        CSV_HEADER + "pwn,Paridrayan,0,0,0,0,0,0,0,0,10,2,4,0,0,0,0,0\n"
    )


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def test_snapshot_from_stats_dir(tmp_path):
    _write_stats(tmp_path / "statistics")
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots"])
    assert result.returncode == 0, result.stderr
    metrics = json.loads((tmp_path / "out" / "corpus_metrics.json").read_text())

    assert metrics["totals"]["tokens"] == 21        # 11 + 10
    assert metrics["totals"]["sentences"] == 10     # 6 + 4
    assert metrics["totals"]["xml_files"] == 6      # file_count sums
    assert metrics["totals"]["sources"] == 2
    assert metrics["totals"]["parse_errors"] == 1
    assert metrics["by_language"]["Amis"]["tokens"] == 6
    assert metrics["by_language"]["Truku"]["tokens"] == 2
    assert metrics["by_language"]["Seediq"]["tokens"] == 3
    assert metrics["by_source"]["MiniCorpus"]["tokens"] == 11


def test_history_appends_one_row_at_head(tmp_path):
    _write_stats(tmp_path / "statistics")
    cache = tmp_path / "cache.csv"
    cache.write_text(
        "date,commit,tokens,sentences,xml_files,sources,languages,parse_errors\n"
        "2025-01-01T00:00:00+00:00,0000000000000000000000000000000000000000,100,10,5,1,1,0\n"
    )
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots",
                   "--history", "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr

    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True, cwd=REPO_ROOT).stdout.strip()
    with open(tmp_path / "out" / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2                      # cached row kept + HEAD appended
    assert rows[0]["tokens"] == "100"
    assert rows[1]["commit"] == head
    assert rows[1]["tokens"] == "21"

    # Re-running on the same HEAD must replace, not duplicate.
    cache2 = tmp_path / "out" / "corpus_size_history.csv"
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots",
                   "--history", "--history-cache", str(cache2)])
    assert result.returncode == 0, result.stderr
    with open(tmp_path / "out" / "corpus_size_history.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == 2
