"""One predicate decides what counts as published corpus XML.

`corpus_counts.is_published_xml` is that predicate, and every counter must go
through it (maintainer ruling 2026-08-11: no two counting scripts may arrive
at different file sets).

The case that made this a test: a POL-035 pre-correction snapshot lives at
`Corpora/<name>/CodeAndDocs/pre_correction_snapshot/XML/...` and is a
byte-for-byte ancestor of the corpus beside it, so counting one doubles that
corpus's apparent size. `corpus_counts` had excluded `CodeAndDocs` since
2026-08-11; `corpus_metrics` -- which writes `corpus_size_history.csv` and the
growth graph -- had its own copy of the walk that did not.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO_ROOT), str(REPO_ROOT / "QC")]

from QC import corpus_counts  # noqa: E402
import corpus_metrics  # noqa: E402

PUBLISHED = "Corpora/Example/XML/Amis/text.xml"
NESTED = "Corpora/Example/Sub/Folder/XML/Amis/text.xml"
SNAPSHOT = "Corpora/Example/CodeAndDocs/pre_correction_snapshot/XML/Amis/text.xml"
RAW_SCRAPE = "Corpora/Example/CodeAndDocs/raw_xml/XML/text.xml"
NOT_XML_DIR = "Corpora/Example/notes/text.xml"


@pytest.mark.parametrize("path", [PUBLISHED, NESTED])
def test_published_paths_count(path):
    assert corpus_counts.is_published_xml(path)
    assert corpus_counts.is_published_xml(Path(path)), "Path and str must agree"


@pytest.mark.parametrize("path", [SNAPSHOT, RAW_SCRAPE, NOT_XML_DIR])
def test_codeanddocs_and_non_xml_dirs_do_not_count(path):
    assert not corpus_counts.is_published_xml(path)
    assert not corpus_counts.is_published_xml(Path(path))


def test_corpus_metrics_walk_uses_the_predicate(tmp_path):
    """The filesystem walk behind XML mode and the growth history."""
    for rel in (PUBLISHED, NESTED, SNAPSHOT, RAW_SCRAPE, NOT_XML_DIR):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("<TEXT/>", encoding="utf-8")

    found = {
        str(f.relative_to(tmp_path))
        for f in corpus_metrics.find_xml_files(tmp_path / "Corpora")
    }
    assert found == {PUBLISHED, NESTED}, f"unexpected file set: {sorted(found)}"


def test_history_pathspec_excludes_snapshots():
    """The git-side twin of the predicate, used by --history-extend.

    `**` crosses directories even under :(glob), so the pathspec needs an
    explicit exclusion; without it a commit touching only a snapshot reads as
    an XML-changing commit and its files inflate the history row.
    """
    import subprocess

    # -z: paths with non-ASCII or spaces come back quoted otherwise, and
    # several corpora have both.
    listed = [
        p for p in subprocess.run(
            ["git", "ls-files", "-z", "--", *corpus_metrics.XML_HISTORY_PATHSPECS],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout.split("\0") if p
    ]
    if not listed:
        pytest.skip("no tracked corpus XML in this checkout")
    offenders = [p for p in listed if "CodeAndDocs" in p.split("/")]
    assert not offenders, f"history pathspec still selects: {offenders[:5]}"
    assert set(listed) == {
        str(f.relative_to(REPO_ROOT))
        for f in corpus_metrics.find_xml_files(REPO_ROOT / "Corpora")
    }, "the git pathspec and the filesystem walk must select the same files"


def test_the_two_walks_agree_on_the_real_repository():
    """The regression itself: XML mode and the per-corpus CSVs must match.

    Before the fix, corpus_metrics counted 11 CodeAndDocs XML files across
    SEALS33, WakelinTexts and MontgomeryTexts that get_corpus_stats did not.
    """
    corpora = REPO_ROOT / "Corpora"
    if not corpora.is_dir():
        pytest.skip("no Corpora/ in this checkout")

    metrics_files = set(corpus_metrics.find_xml_files(corpora))
    counts_files = {
        f
        for corpus in sorted(corpora.iterdir()) if corpus.is_dir()
        for d in corpus_counts.corpus_xml_dirs(corpus)
        for f in d.rglob("*.xml")
        if "CodeAndDocs" not in f.parts
    }
    assert metrics_files == counts_files, (
        "corpus_metrics and corpus_counts disagree on the published file set: "
        f"only in metrics={sorted(metrics_files - counts_files)[:5]} "
        f"only in counts={sorted(counts_files - metrics_files)[:5]}"
    )
