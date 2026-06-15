"""Integration tests for QC/utilities/capture_manual_edits.py.

capture diffs the working XML tree against a git baseline and records
hand edits into <corpus-root>/CodeAndDocs/manual_edits.xml. Tests build a
real git repo in tmp_path: repo root = tmp_path, XML root = tmp_path/XML.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

CAPTURE = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "capture_manual_edits.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit_all(repo: Path, msg: str = "c") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _doc(*sentences: str) -> str:
    body = "".join(sentences)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<TEXT id="T" xml:lang="ami">{body}</TEXT>\n'


def _sent(sid: str, original: str, standard: str | None = None) -> str:
    std = f'<FORM kindOf="standard">{standard}</FORM>' if standard else ""
    return f'<S id="{sid}"><FORM kindOf="original">{original}</FORM>{std}</S>'


def _run_capture(corpora_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CAPTURE), "--corpora_path", str(corpora_path), *extra],
        capture_output=True, text=True,
    )


def _manual_root(repo: Path):
    return etree.parse(str(repo / "CodeAndDocs" / "manual_edits.xml")).getroot()


def test_change_is_recorded_stripped_under_file_group(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "Amis" / "a.xml"
    _write(xml, _doc(_sent("S1", "old", "OLD")))
    _init_repo(repo)
    _commit_all(repo)
    # hand-edit the original tier
    _write(xml, _doc(_sent("S1", "new", "OLD")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    root = _manual_root(repo)
    fg = root.find("FILE[@path='Amis/a.xml']")
    assert fg is not None
    s = fg.find("S[@id='S1']")
    assert s.find("FORM[@kindOf='original']").text == "new"
    # standard tier stripped from the recorded block
    assert s.find("FORM[@kindOf='standard']") is None


def test_unchanged_tree_writes_no_manual_file(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()


def test_standard_only_change_is_not_captured(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x", "X")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S1", "x", "DIFFERENT")))  # only standard tier changed
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()
