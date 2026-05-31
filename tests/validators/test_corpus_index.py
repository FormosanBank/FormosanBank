"""Unit tests for CorpusIndex."""
from pathlib import Path

import pytest

from QC.validation._corpus_index import (
    CorpusIndex,
    build_current_index,
    build_published_index,
)


def test_empty_index():
    idx = CorpusIndex(ids={}, langs={}, published_ids={})
    assert idx.ids == {}
    assert idx.langs == {}
    assert idx.published_ids == {}


def test_index_with_one_id_and_lang():
    p = Path("/tmp/foo.xml")
    idx = CorpusIndex(
        ids={"ami_chapter01": [(p, "TEXT")]},
        langs={p: "ami"},
        published_ids={},
    )
    assert idx.ids["ami_chapter01"] == [(p, "TEXT")]
    assert idx.langs[p] == "ami"
    assert idx.published_ids == {}


def test_index_with_id_collision_across_files():
    p1 = Path("/tmp/foo.xml")
    p2 = Path("/tmp/bar.xml")
    idx = CorpusIndex(
        ids={"shared_id": [(p1, "TEXT"), (p2, "TEXT")]},
        langs={p1: "ami", p2: "pwn"},
        published_ids={},
    )
    assert len(idx.ids["shared_id"]) == 2
    assert idx.langs[p1] == "ami"
    assert idx.langs[p2] == "pwn"


def test_index_published_ids():
    p = Path("/corpora/foo/XML/bar.xml")
    idx = CorpusIndex(
        ids={},
        langs={},
        published_ids={"foo_bar": [p]},
    )
    assert idx.published_ids["foo_bar"] == [p]


# ---------------------------------------------------------------------------
# build_current_index tests
# ---------------------------------------------------------------------------

def test_build_current_index_empty():
    ids, langs = build_current_index([])
    assert ids == {}
    assert langs == {}


def test_build_current_index_single_file(tmp_path):
    xml = tmp_path / "test.xml"
    xml.write_text(
        '<?xml version="1.0"?>'
        '<TEXT id="corpus_foo" xml:lang="ami" citation="x" BibTeX_citation="x" copyright="x">'
        '<S id="S1"><FORM kindOf="original">hello</FORM></S>'
        '</TEXT>',
        encoding="utf-8",
    )
    ids, langs = build_current_index([xml])
    assert "corpus_foo" in ids
    assert ids["corpus_foo"] == [(xml, "TEXT")]
    assert langs[xml] == "ami"


def test_build_current_index_skips_parse_error(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("this is not xml", encoding="utf-8")
    ids, langs = build_current_index([bad])
    assert ids == {}
    assert langs == {}


def test_build_current_index_skips_non_TEXT_root(tmp_path):
    xml = tmp_path / "test.xml"
    xml.write_text(
        '<?xml version="1.0"?><S id="s1"></S>',
        encoding="utf-8",
    )
    ids, langs = build_current_index([xml])
    assert ids == {}
    assert langs == {}


# ---------------------------------------------------------------------------
# build_published_index tests
# ---------------------------------------------------------------------------

def test_build_published_index_nonexistent_root(tmp_path):
    result = build_published_index(tmp_path / "nonexistent")
    assert result == {}


def test_build_published_index_empty_dir(tmp_path):
    result = build_published_index(tmp_path)
    assert result == {}


def test_build_published_index_single_file(tmp_path):
    xml = tmp_path / "corpus" / "XML" / "file.xml"
    xml.parent.mkdir(parents=True)
    xml.write_text(
        '<?xml version="1.0"?>'
        '<TEXT id="published_id" xml:lang="pwn" citation="x" BibTeX_citation="x" copyright="x">'
        '<S id="S1"><FORM kindOf="original">hi</FORM></S>'
        '</TEXT>',
        encoding="utf-8",
    )
    result = build_published_index(tmp_path)
    assert "published_id" in result
    assert result["published_id"] == [xml]


def test_build_published_index_skips_parse_error(tmp_path):
    bad = tmp_path / "bad.xml"
    bad.write_text("not xml", encoding="utf-8")
    result = build_published_index(tmp_path)
    assert result == {}


def test_build_published_index_skips_non_TEXT_root(tmp_path):
    xml = tmp_path / "file.xml"
    xml.write_text(
        '<?xml version="1.0"?><S id="s1"></S>',
        encoding="utf-8",
    )
    result = build_published_index(tmp_path)
    assert result == {}


def test_build_published_index_multiple_files(tmp_path):
    """Multiple corpora each contribute one file under their XML/ subdir.

    build_published_index walks <corpora_root>/<corpus>/XML/ for each
    top-level subdirectory; files placed directly at the corpora_root
    level (or under CodeAndDocs/) are excluded as non-canonical.
    """
    for i in range(3):
        xml = tmp_path / f"corpus_{i}" / "XML" / f"file{i}.xml"
        xml.parent.mkdir(parents=True)
        xml.write_text(
            f'<?xml version="1.0"?>'
            f'<TEXT id="corpus_{i}" xml:lang="ami" citation="x" BibTeX_citation="x" copyright="x">'
            f'<S id="S1"><FORM kindOf="original">text</FORM></S>'
            f'</TEXT>',
            encoding="utf-8",
        )
    result = build_published_index(tmp_path)
    assert len(result) == 3
    for i in range(3):
        assert f"corpus_{i}" in result


def test_build_published_index_excludes_non_canonical_locations(tmp_path):
    """Regression pin: files under <corpus>/CodeAndDocs/ or at the
    corpora_root level are NOT picked up — only <corpus>/XML/**/*.xml.

    Without this exclusion, ePark's CodeAndDocs/.../class.xml (root
    element <dataroot>) would produce false V000 findings, and
    Glosbe's CodeAndDocs/work/reference_amis/Amis.xml would produce
    false V081 cross-corpus id collisions.
    """
    canonical = tmp_path / "corpus_a" / "XML" / "valid.xml"
    canonical.parent.mkdir(parents=True)
    canonical.write_text(
        '<?xml version="1.0"?>'
        '<TEXT id="canonical_id" xml:lang="ami" citation="x" BibTeX_citation="x" copyright="x">'
        '<S id="S1"><FORM kindOf="original">x</FORM></S>'
        '</TEXT>',
        encoding="utf-8",
    )
    working = tmp_path / "corpus_a" / "CodeAndDocs" / "scratch.xml"
    working.parent.mkdir(parents=True)
    working.write_text(
        '<?xml version="1.0"?>'
        '<TEXT id="working_id" xml:lang="ami" citation="x" BibTeX_citation="x" copyright="x">'
        '<S id="S1"><FORM kindOf="original">x</FORM></S>'
        '</TEXT>',
        encoding="utf-8",
    )
    result = build_published_index(tmp_path)
    assert "canonical_id" in result
    assert "working_id" not in result
