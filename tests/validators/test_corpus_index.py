"""Unit tests for CorpusIndex."""
from pathlib import Path

from QC.validation._corpus_index import CorpusIndex


def test_empty_index():
    idx = CorpusIndex(ids={}, langs={})
    assert idx.ids == {}
    assert idx.langs == {}


def test_index_with_one_id_and_lang():
    p = Path("/tmp/foo.xml")
    idx = CorpusIndex(
        ids={"ami_chapter01": [(p, "TEXT")]},
        langs={p: "ami"},
    )
    assert idx.ids["ami_chapter01"] == [(p, "TEXT")]
    assert idx.langs[p] == "ami"


def test_index_with_id_collision_across_files():
    p1 = Path("/tmp/foo.xml")
    p2 = Path("/tmp/bar.xml")
    idx = CorpusIndex(
        ids={"shared_id": [(p1, "TEXT"), (p2, "TEXT")]},
        langs={p1: "ami", p2: "pwn"},
    )
    assert len(idx.ids["shared_id"]) == 2
    assert idx.langs[p1] == "ami"
    assert idx.langs[p2] == "pwn"
