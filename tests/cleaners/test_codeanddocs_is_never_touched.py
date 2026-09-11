"""No shared tool may read or write anything under `CodeAndDocs/`.

`CodeAndDocs/` holds reproduction infrastructure -- build scripts, raw
scrapes, and POL-035 pre-correction snapshots -- never published data. A
snapshot is a byte-for-byte ancestor of the corpus beside it, so a tool
handed a corpus root rather than `<corpus>/XML` either counts the same
text twice or rewrites a baseline that exists precisely to stay
untouched.

This is an end-to-end guard, not a source scan. A static check was tried
first and was not good enough: several validators reach the rule through
`_discovery.py` several call-frames away, so grepping for the guard near
the `rglob` gives false negatives, and grepping for it anywhere in the
file gives false positives. The only trustworthy question is what the
tool actually touched, so each case drives the real entry point at a
corpus root and then looks at the snapshot.

Two of these fail against the code as it stood on 2026-09-11:
`standardize.py` rewrote both snapshots outright, and `clean_xml.py`
rewrote any snapshot that had something to clean.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# A published FORM plus a character `clean_xml` is known to canonicalise:
# a decomposed a + COMBINING ACUTE ACCENT, which folds to U+00E1. Without
# it a clean corpus passes for the wrong reason -- the tool reads the
# snapshot but finds nothing to change.
DECOMPOSED = "oená"

TEXT = """<?xml version='1.0' encoding='UTF-8'?>
<TEXT id="{tid}" citation="c" BibTeX_citation="b" copyright="public domain"
      dialect="Favorlang" xml:lang="bzg">
  <S id="S1"><FORM kindOf="original">bahosa</FORM>
    <TRANSL xml:lang="eng">man</TRANSL></S>
  <S id="S2"><FORM kindOf="original">{extra}</FORM>
    <TRANSL xml:lang="eng">head</TRANSL></S>
</TEXT>
"""


@pytest.fixture()
def corpus(tmp_path):
    """A corpus root: published XML, and a POL-035 snapshot beside it.

    The snapshot carries the decomposed character so that a tool which
    reads it has something to rewrite.
    """
    published = tmp_path / "XML" / "Babuza-Favorlang"
    snapshot = tmp_path / "CodeAndDocs" / "pre_correction_snapshot" / "Babuza-Favorlang"
    published.mkdir(parents=True)
    snapshot.mkdir(parents=True)
    (published / "corpus.xml").write_text(
        TEXT.format(tid="published", extra="oeno"), encoding="utf-8"
    )
    (snapshot / "corpus.xml").write_text(
        TEXT.format(tid="published", extra=DECOMPOSED), encoding="utf-8"
    )
    return tmp_path


def _snapshot(corpus: Path) -> Path:
    return (
        corpus / "CodeAndDocs" / "pre_correction_snapshot"
        / "Babuza-Favorlang" / "corpus.xml"
    )


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / script), *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT), check=False,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT)},
    )


# Every shared tool that writes XML, with the arguments that point it at a
# corpus ROOT -- the invocation that exposes the snapshot. `id` is what
# pytest prints, so a failure names the tool directly.
WRITERS = [
    ("clean_xml", "QC/cleaning/clean_xml.py", ["--corpora_path", "{root}"]),
    ("standardize", "QC/utilities/standardize.py",
     ["--copy", "--corpora_path", "{root}"]),
    ("remove_duplicate_sentences", "QC/cleaning/remove_duplicate_sentences.py",
     ["by_path", "--path", "{root}", "--apply"]),
    ("suppress_transl_annotations", "QC/cleaning/suppress_transl_annotations.py",
     ["--corpora_path", "{root}", "--apply"]),
    ("add_phonology", "QC/utilities/add_phonology.py",
     ["--orthography", "Ortho113", "--corpora_path", "{root}"]),
]


@pytest.mark.parametrize("name,script,argv", WRITERS, ids=[w[0] for w in WRITERS])
def test_writer_leaves_the_snapshot_alone(corpus, tmp_path, name, script, argv):
    snapshot = _snapshot(corpus)
    before = snapshot.read_bytes()

    argv = [a.format(root=str(corpus)) for a in argv]
    if name == "clean_xml":
        argv += ["--warnings_dir", str(tmp_path / "warnings")]
    _run(script, *argv)

    assert snapshot.read_bytes() == before, (
        f"{name} modified a POL-035 snapshot under CodeAndDocs/. "
        f"It must skip reproduction paths -- see "
        f"QC.corpus_counts.is_reproduction_path."
    )


def test_the_fixture_would_catch_a_rewrite(corpus):
    """Guards the guard: the snapshot must really contain something a
    cleaner would change, or every case above passes vacuously."""
    text = _snapshot(corpus).read_text(encoding="utf-8")
    assert "́" in text, "snapshot lost its decomposed character"
    assert "á" not in text, "snapshot is already canonical"


def test_a_staging_tree_inside_codeanddocs_is_still_processed(tmp_path):
    """The rule is "do not wander into CodeAndDocs", not "refuse to touch
    it". Several builds stage into `<corpus>/CodeAndDocs/Final_XML/` and
    clean there before installing into `XML/` -- NTUFormosanCorpus does
    exactly that, with an absolute path. A tool that skipped what it was
    explicitly handed would turn those builds into a silent no-op, which
    is worse than the bug this guard exists to fix."""
    staging = tmp_path / "CodeAndDocs" / "Final_XML" / "Babuza-Favorlang"
    staging.mkdir(parents=True)
    staged = staging / "corpus.xml"
    staged.write_text(TEXT.format(tid="staged", extra=DECOMPOSED), encoding="utf-8")

    result = _run(
        "QC/cleaning/clean_xml.py",
        "--corpora_path", str(staging.parent),
        "--warnings_dir", str(tmp_path / "warnings"),
    )

    assert result.returncode == 0, result.stderr
    assert "corpus.xml" in result.stdout, (
        "clean_xml skipped a staging tree it was pointed at directly:\n"
        + result.stdout
    )
    assert "\u0301" not in staged.read_text(encoding="utf-8"), (
        "staged file was discovered but never cleaned"
    )


def test_published_data_is_still_processed(corpus, tmp_path):
    """The exclusion must not turn into 'skip everything'. Pointed at the
    corpus root, a cleaner still has to reach the published file."""
    published = corpus / "XML" / "Babuza-Favorlang" / "corpus.xml"
    result = _run(
        "QC/cleaning/clean_xml.py",
        "--corpora_path", str(corpus),
        "--warnings_dir", str(tmp_path / "warnings"),
    )
    assert result.returncode == 0, result.stderr
    assert published.is_file()
    assert "corpus.xml" in result.stdout, result.stdout
