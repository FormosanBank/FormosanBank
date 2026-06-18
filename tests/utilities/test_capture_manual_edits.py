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


def test_new_s_is_recorded_with_after_anchor(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "one")))
    _init_repo(repo)
    _commit_all(repo)
    # split: edit S1, add S1b after it
    _write(xml, _doc(_sent("S1", "one-a"), _sent("S1b", "one-b")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S1']").find("FORM").text == "one-a"
    s1b = fg.find("S[@id='S1b']")
    assert s1b.get("after") == "S1"


def test_split_chain_anchors_on_immediate_predecessor(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S1", "x"), _sent("S1b", "b"), _sent("S1c", "c")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S1b']").get("after") == "S1"
    assert fg.find("S[@id='S1c']").get("after") == "S1b"


def test_first_sentence_addition_has_no_after(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S0", "new-first"), _sent("S1", "x")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert "after" not in fg.find("S[@id='S0']").attrib


def test_deletion_is_recorded(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x"), _sent("S2", "y")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S1", "x")))  # S2 removed
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S2']").get("action") == "delete"


def test_capture_is_additive_to_existing_entries(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x"), _sent("S2", "y")))
    _init_repo(repo)
    _commit_all(repo)
    # pre-existing manual file with an unrelated entry
    man = repo / "CodeAndDocs" / "manual_edits.xml"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(
        '<MANUAL_EDITS><FILE path="a.xml">'
        '<S id="S9"><FORM kindOf="original">keep</FORM></S>'
        "</FILE></MANUAL_EDITS>",
        encoding="utf-8",
    )
    _write(xml, _doc(_sent("S1", "edited"), _sent("S2", "y")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S9']") is not None  # survived
    assert fg.find("S[@id='S1']").find("FORM").text == "edited"


def test_file_absent_from_baseline_is_warned_and_skipped(tmp_path):
    repo = tmp_path
    a = repo / "XML" / "a.xml"
    _write(a, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    # brand-new file never committed
    _write(repo / "XML" / "new.xml", _doc(_sent("N1", "z")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    assert "new.xml" in proc.stdout and "skipping" in proc.stdout.lower()
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()


def test_not_a_git_repo_errors(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))  # no git init
    proc = _run_capture(tmp_path / "XML")
    assert proc.returncode == 2
    assert "git" in proc.stderr.lower()


def test_bad_baseline_ref_errors(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    proc = _run_capture(repo / "XML", "--baseline-ref", "NOPE")
    assert proc.returncode == 2
    assert "nope" in proc.stderr.lower() or "ref" in proc.stderr.lower()
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()
