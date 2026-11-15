"""touched_corpora.py: the 'skip corpora that cannot have changed' rule used by CI."""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "QC" / "validation" / "touched_corpora.py"


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def _repo(tmp_path):
    repo = tmp_path / "r"
    for c in ("A", "B", "C"):
        (repo / "Corpora" / c / "XML").mkdir(parents=True)
        (repo / "Corpora" / c / "XML" / "f.xml").write_text("<TEXT/>")
    (repo / "QC").mkdir()
    (repo / "QC" / "tool.py").write_text("")
    _git(repo, "init", "-q")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "base")
    return repo


def _commit(repo, path, text="x"):
    p = repo / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "add", ".")
    _git(repo, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "c")


def _run(repo, out, *args):
    proc = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), "--out", str(out), *args],
                          capture_output=True, text=True, check=True)
    return proc.stdout.strip(), out.read_text().split()


def test_only_the_touched_corpus(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, "Corpora/B/XML/f.xml", "<TEXT id='b'/>")
    _commit(repo, "Corpora/B/README.md")
    assert _run(repo, tmp_path / "o", "--range", "HEAD~2...HEAD", "--code", "QC/tool.py") == ("scope=some", ["B"])


def test_a_code_change_means_every_corpus(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, "Corpora/B/XML/f.xml", "<TEXT id='b'/>")
    _commit(repo, "QC/tool.py", "print()")
    assert _run(repo, tmp_path / "o", "--range", "HEAD~2...HEAD", "--code", "QC/tool.py") == ("scope=all", ["A", "B", "C"])


def test_a_code_folder_matches_below_it(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, "QC/sub/x.py")
    assert _run(repo, tmp_path / "o", "--range", "HEAD~1...HEAD", "--code", "QC/sub/")[0] == "scope=all"


def test_nothing_relevant_changed(tmp_path):
    repo = _repo(tmp_path)
    _commit(repo, "docs/page.md")
    assert _run(repo, tmp_path / "o", "--range", "HEAD~1...HEAD", "--code", "QC/tool.py") == ("scope=none", [])


def test_no_range_or_a_bad_range_means_every_corpus(tmp_path):
    repo = _repo(tmp_path)
    assert _run(repo, tmp_path / "o")[0] == "scope=all"
    assert _run(repo, tmp_path / "o", "--range", "0123456789abcdef...HEAD") == ("scope=all", ["A", "B", "C"])
