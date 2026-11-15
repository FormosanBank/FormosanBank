"""get_corpus_stats.py --all --changed-only regenerates only corpora whose inputs changed.

CI uses it so that a merge touching one corpus does not re-parse all of them. The
recorded fingerprint covers the corpus folder's committed tree, the statistics code
and the corpus's audio-duration rows; uncommitted edits always regenerate.
"""
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "QC/utilities/get_corpus_stats.py"
CODE = ("QC/utilities/get_corpus_stats.py", "QC/utilities/audio_durations.py",
        "QC/corpus_counts.py", "QC/xml_forms.py", "languages.csv")
XML = ('<TEXT id="{c}" xml:lang="ami" dialect="Coastal" citation="c" BibTeX_citation="b" copyright="CC BY 4.0">'
       '<S id="1"><FORM kindOf="original">{w}</FORM><FORM kindOf="standard">{w}</FORM></S></TEXT>')


def _git(root, *args):
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", *args], cwd=root,
                   check=True, capture_output=True)


def _repo(tmp_path):
    root = tmp_path / "repo"
    for rel in CODE:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(REPO / rel, root / rel)
    for c in ("A", "B"):
        d = root / "Corpora" / c / "XML" / "Amis"
        d.mkdir(parents=True)
        (d / "t.xml").write_text(XML.format(c=c, w="nga'ay ho"), encoding="utf-8")
    (root / "statistics").mkdir()
    _git(root, "init", "-q"); _git(root, "add", "."); _git(root, "commit", "-qm", "base")
    return root


def _run(root):
    proc = subprocess.run([sys.executable, str(root / SCRIPT), "--all", "--changed-only",
                           "--corpora_root", str(root / "Corpora")],
                          cwd=root, capture_output=True, text=True, check=True)
    return sorted(l.split()[1] for l in proc.stdout.splitlines() if l.startswith("Processing"))


def test_only_the_changed_corpus_is_regenerated(tmp_path):
    root = _repo(tmp_path)
    assert _run(root) == ["A", "B"]          # nothing recorded yet
    assert _run(root) == []                  # nothing changed
    (root / "Corpora/B/XML/Amis/t.xml").write_text(XML.format(c="B", w="nga'ay ho kiso"), encoding="utf-8")
    assert _run(root) == ["B"]               # uncommitted edit: always regenerated
    _git(root, "commit", "-qam", "B changed")
    assert _run(root) == ["B"]               # committed: new tree id, regenerated once
    assert _run(root) == []
    assert "kiso" not in (root / "statistics/A_corpora_stats.csv").read_text()


def test_a_code_change_regenerates_every_corpus(tmp_path):
    root = _repo(tmp_path)
    _run(root)
    with open(root / "QC/corpus_counts.py", "a", encoding="utf-8") as f:
        f.write("\n")
    _git(root, "commit", "-qam", "code changed")
    assert _run(root) == ["A", "B"]
