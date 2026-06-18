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


# --------------------------------------------------------------------------- #
# --history-extend: fill every XML-changing commit since the last cached row  #
# --------------------------------------------------------------------------- #

HISTORY_HEADER = (
    "date,commit,tokens,sentences,xml_files,sources,languages,parse_errors\n"
)


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t.test")
    _git(repo, "config", "user.name", "Tester")
    _git(repo, "config", "commit.gpgsign", "false")


def _xml(tokens: int) -> str:
    words = " ".join(f"w{i}" for i in range(tokens))
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<TEXT xml:lang="ami">\n'
        '  <S id="1"><FORM kindOf="standard">' + words + "</FORM></S>\n"
        "</TEXT>\n"
    )


def _add_xml(repo: Path, rel: str, tokens: int, message: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_xml(tokens), encoding="utf-8")
    _git(repo, "add", rel)
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _run_in(repo: Path, args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=repo,
    )


def test_history_extend_fills_intermediate_commits(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    c1 = _add_xml(repo, "Corpora/Mini/XML/Amis/a.xml", 2, "c1: a.xml (2)")
    c2 = _add_xml(repo, "Corpora/Mini/XML/Amis/b.xml", 3, "c2: b.xml (+3)")
    c3 = _add_xml(repo, "Corpora/Mini/XML/Amis/c.xml", 1, "c3: c.xml (+1)")

    # Cache holds only the seed commit (c1); c2 and c3 are the gap to fill.
    cache = repo / "statistics" / "corpus_size_history.csv"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        HISTORY_HEADER + f"2025-01-01T00:00:00+00:00,{c1},2,1,1,1,1,0\n"
    )

    out = tmp_path / "out"
    result = _run_in(repo, [str(repo / "Corpora"), "--output-dir", str(out),
                            "--no-plots", "--history-extend",
                            "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr

    with open(out / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    # seed (c1) preserved + one new row each for c2 and c3
    assert [r["commit"] for r in rows] == [c1, c2, c3]
    assert [r["tokens"] for r in rows] == ["2", "5", "6"]      # cumulative
    assert [r["xml_files"] for r in rows] == ["1", "2", "3"]


def test_history_extend_appends_one_row_when_no_gap(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    c1 = _add_xml(repo, "Corpora/Mini/XML/Amis/a.xml", 2, "c1")
    c2 = _add_xml(repo, "Corpora/Mini/XML/Amis/b.xml", 3, "c2")

    # Cache already at the second-to-last commit => only HEAD is new (<=1).
    cache = repo / "statistics" / "corpus_size_history.csv"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        HISTORY_HEADER + f"2025-01-01T00:00:00+00:00,{c1},2,1,1,1,1,0\n"
    )

    out = tmp_path / "out"
    result = _run_in(repo, [str(repo / "Corpora"), "--output-dir", str(out),
                            "--no-plots", "--history-extend",
                            "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr
    with open(out / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert [r["commit"] for r in rows] == [c1, c2]
    assert rows[-1]["tokens"] == "5"


def test_history_extend_falls_back_when_cache_tip_unrelated(tmp_path):
    repo = tmp_path / "repo"
    _init_repo(repo)
    _add_xml(repo, "Corpora/Mini/XML/Amis/a.xml", 2, "c1")
    c2 = _add_xml(repo, "Corpora/Mini/XML/Amis/b.xml", 3, "c2")

    # Cache tip is a commit that is NOT an ancestor of HEAD -> safe append only.
    cache = repo / "statistics" / "corpus_size_history.csv"
    cache.parent.mkdir(parents=True)
    bogus = "0" * 40
    cache.write_text(
        HISTORY_HEADER + f"2025-01-01T00:00:00+00:00,{bogus},99,9,9,1,1,0\n"
    )

    out = tmp_path / "out"
    result = _run_in(repo, [str(repo / "Corpora"), "--output-dir", str(out),
                            "--no-plots", "--history-extend",
                            "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr
    with open(out / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    # bogus cached row preserved; exactly one HEAD row appended (no walk).
    assert len(rows) == 2
    assert rows[0]["commit"] == bogus
    assert rows[1]["commit"] == c2
    assert rows[1]["tokens"] == "5"


def test_snapshot_aggregates_new_metrics(tmp_path):
    # _write_stats seeds: ami,Haian has glossed_words=3, zho_transl_count=3;
    # trv,Truku has transcribed_audio_seconds=1.0; everything else 0.
    _write_stats(tmp_path / "statistics")
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots"])
    assert result.returncode == 0, result.stderr
    totals = json.loads((tmp_path / "out" / "corpus_metrics.json").read_text())["totals"]
    assert totals["glossed_words"] == 3
    assert totals["zho_transl_count"] == 3
    assert totals["transcribed_audio_seconds"] == 1.0


def test_xml_path_aggregates_glossed_and_mandarin_but_zero_seconds(tmp_path):
    # XML walk over the fixture corpus: ami_haian contributes glossed=3, zho=3.
    # transcribed_audio_seconds is uncomputable from XML, so it must be 0.
    result = _run(["tests/fixtures/stats_corpus",
                   "--output-dir", str(tmp_path / "out"), "--no-plots"])
    assert result.returncode == 0, result.stderr
    totals = json.loads((tmp_path / "out" / "corpus_metrics.json").read_text())["totals"]
    assert totals["glossed_words"] == 3
    assert totals["zho_transl_count"] == 3
    assert totals["transcribed_audio_seconds"] == 0


def test_history_row_carries_new_metric_columns(tmp_path):
    _write_stats(tmp_path / "statistics")
    cache = tmp_path / "cache.csv"
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots",
                   "--history", "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr
    with open(tmp_path / "out" / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    head = rows[-1]
    assert "transcribed_audio_seconds" in head
    assert "zho_transl_count" in head
    assert "glossed_words" in head
    assert int(head["glossed_words"]) == 3
    assert int(head["zho_transl_count"]) == 3
    assert float(head["transcribed_audio_seconds"]) == 1.0


def test_history_plots_emit_four_pngs(tmp_path):
    # Use the real subprocess path WITH plots (omit --no-plots). Seed stats and
    # a one-row cache so there is a dated row to plot.
    _write_stats(tmp_path / "statistics")
    out = tmp_path / "out"
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(out), "--history",
                   "--history-cache", str(tmp_path / "cache.csv")])
    assert result.returncode == 0, result.stderr
    for name in ("corpus_size_over_time.png",
                 "corpus_transcribed_audio_over_time.png",
                 "corpus_mandarin_words_over_time.png",
                 "corpus_glossed_words_over_time.png"):
        assert (out / name).is_file(), f"missing {name}"
