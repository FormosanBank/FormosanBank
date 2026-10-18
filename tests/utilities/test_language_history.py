"""QC/language_history.py: per-corpus, per-language word-count history from git."""

import csv
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "QC"))
import language_history  # noqa: E402


def _xml(lang: str, dialect: str | None, sentences: list[tuple[str, bool, bool]]) -> str:
    """sentences: (text, has_audio, glossed)."""
    dialect_attr = f' dialect="{dialect}"' if dialect else ""
    body = []
    for i, (text, audio, glossed) in enumerate(sentences):
        parts = [f'<FORM kindOf="original">{text}</FORM>']
        if audio:
            parts.append('<AUDIO file="a.wav" start="0" end="1"/>')
        if glossed:
            parts.append('<W id="w"><FORM kindOf="original">x</FORM><M id="m"><FORM kindOf="original">x</FORM><TRANSL xml:lang="eng">X</TRANSL></M></W>')
        parts.append('<TRANSL xml:lang="zho">中</TRANSL>')
        body.append(f'<S id="s{i}">{"".join(parts)}</S>')
    return f'<TEXT id="t" xml:lang="{lang}"{dialect_attr}>{"".join(body)}</TEXT>'


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=repo, check=True, capture_output=True, text=True,
    ).stdout.strip()


def _write(repo: Path, rel: str, text: str) -> None:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    # commit 1: corpus A, Amis Coastal, 3 words (2 with audio)
    _write(repo, "Corpora/A/XML/a1.xml", _xml("ami", "Coastal", [("one two", True, False), ("three", False, False)]))
    _git(repo, "add", "-A"); _git(repo, "commit", "-q", "-m", "c1")
    # commit 2: corpus B (Truku, glossed) + A grows; a snapshot under CodeAndDocs is ignored
    _write(repo, "Corpora/B/XML/b1.xml", _xml("trv", "Truku", [("a b c d", False, True)]))
    _write(repo, "Corpora/A/XML/a2.xml", _xml("ami", None, [("x y", False, False)]))
    _write(repo, "Corpora/A/CodeAndDocs/snap/XML/a1.xml", _xml("ami", "Coastal", [("ignored words here", True, False)]))
    _git(repo, "add", "-A"); _git(repo, "commit", "-q", "-m", "c2")
    # commit 3: delete a2
    (repo / "Corpora/A/XML/a2.xml").unlink()
    _git(repo, "add", "-A"); _git(repo, "commit", "-q", "-m", "c3")
    return repo


def _by_commit(rows):
    out: dict = {}
    for row in rows:
        out.setdefault(row["commit"], {})[(row["corpus"], row["language"], row["dialect"])] = row
    return out


def test_rebuild_rows_per_commit_corpus_language_dialect(repo):
    rows = language_history.rebuild(repo)
    commits = _git(repo, "log", "--reverse", "--format=%H").splitlines()
    by = _by_commit(rows)
    assert list(by) == commits
    c1, c2, c3 = (by[c] for c in commits)
    assert c1 == {("A", "Amis", "Coastal"): c1[("A", "Amis", "Coastal")]}
    assert int(c1[("A", "Amis", "Coastal")]["words"]) == 3
    assert int(c1[("A", "Amis", "Coastal")]["transcribed_words"]) == 2
    assert int(c1[("A", "Amis", "Coastal")]["zho_transl_count"]) == 3
    assert set(c2) == {("A", "Amis", "Coastal"), ("A", "Amis", "unknown"), ("B", "Truku", "Truku")}
    assert int(c2[("B", "Truku", "Truku")]["glossed_words"]) == 4
    assert int(c2[("B", "Truku", "Truku")]["segmented_words"]) == 4
    assert set(c3) == {("A", "Amis", "Coastal"), ("B", "Truku", "Truku")}
    assert all(row["date"] for row in rows)


def test_write_and_load_round_trip(repo, tmp_path):
    rows = language_history.rebuild(repo)
    out = tmp_path / "h.csv"
    language_history.write_csv(rows, out)
    with open(out, newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle))
    assert tuple(header) == language_history.HISTORY_FIELDS
    assert language_history.load_csv(out) == [
        {k: str(v) for k, v in row.items()} for row in rows
    ]


def test_extend_appends_only_new_commits(repo, tmp_path):
    out = tmp_path / "h.csv"
    language_history.write_csv(language_history.rebuild(repo), out)
    before = language_history.load_csv(out)
    _write(repo, "Corpora/B/XML/b2.xml", _xml("trv", "Truku", [("e f", False, False)]))
    _git(repo, "add", "-A"); _git(repo, "commit", "-q", "-m", "c4")
    _git(repo, "commit", "-q", "--allow-empty", "-m", "no xml change")
    rows = language_history.extend(repo, out)
    assert rows[: len(before)] == before
    new = rows[len(before):]
    head_xml_commit = _git(repo, "log", "-1", "--format=%H", "HEAD~1")
    assert {row["commit"] for row in new} == {head_xml_commit}
    truku = [row for row in new if row["corpus"] == "B"][0]
    assert int(truku["words"]) == 6


def test_extend_with_no_new_commits_is_a_no_op(repo, tmp_path):
    out = tmp_path / "h.csv"
    language_history.write_csv(language_history.rebuild(repo), out)
    assert language_history.extend(repo, out) == language_history.load_csv(out)


def test_extend_diverged_tip_rebuilds(repo, tmp_path):
    out = tmp_path / "h.csv"
    rows = language_history.rebuild(repo)
    for row in rows:
        row["commit"] = "0" * 40 if row is rows[-1] else row["commit"]
    language_history.write_csv(rows, out)
    rebuilt = language_history.extend(repo, out)
    assert rebuilt == [{k: str(v) for k, v in r.items()} for r in language_history.rebuild(repo)]
