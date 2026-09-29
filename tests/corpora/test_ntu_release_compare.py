"""compare_release_builds.py: tying each published sentence to its own source records.

The tool answers "did this sentence change because its own source changed, or
because the pipeline reacted to something else?" (maintainer, 2026-09-28: look
for code that misfires after the release switch). Its classes are only as good
as the sentence -> records mapping, which these tests pin.
"""
from __future__ import annotations

import sys
from pathlib import Path

CODEDOCS = (Path(__file__).resolve().parents[2]
            / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs")
sys.path.insert(0, str(CODEDOCS / "qa"))

import compare_release_builds as crb  # noqa: E402


def rec(rid, gloss, s_end=True, **extra):
    return [rid, {"gloss": gloss, "s_end": s_end, **extra}]


def test_a_repeated_record_id_gets_the_name_uniquify_gives_its_sentence():
    """20200530-FW-Andrea-1.json has record 6 twice. Merging them made the
    unchanged first sentence look 'masked' because the second one changed."""
    recs = [rec(5, "a"), rec(6, "b"), rec(6, "c"), rec(7, "d")]
    groups = crb.group_records(recs, per_record=True)
    assert list(groups) == ["5", "6", "6-2", "7"]
    index = {("Sentences", "Rukai", "f"): groups}
    assert crb.records_for(("Sentences", "Rukai", "f_S_6"), index) == [recs[1]]
    assert crb.records_for(("Sentences", "Rukai", "f_S_6-2"), index) == [recs[2]]


def test_split_sentences_share_their_parents_records():
    groups = crb.group_records([rec(12, "a")], per_record=True)
    index = {("Sentences", "Rukai", "f"): groups}
    for sid in ("f_S_12-opt", "f_S_12-alt2", "f_S_12-opt-2"):
        assert crb.records_for(("Sentences", "Rukai", sid), index) == groups["12"], sid


def test_stories_group_records_until_s_end():
    recs = [rec(1, "a", s_end=False), rec(2, "b"), rec(3, "c")]
    assert {k: [r[0] for r in v] for k, v in crb.group_records(recs, per_record=False).items()} \
        == {"1": [1, 2], "3": [3]}


def test_changed_fields_names_what_moved():
    old = [rec(1, "a", s_a_span=[0, 1])]
    assert crb.changed_fields(old, [rec(1, "a", s_a_span=[0, 2])]) == ["s_a_span"]
    assert crb.changed_fields(old, [rec(1, "b", s_a_span=[0, 1])]) == ["gloss"]
    assert crb.changed_fields(old, old) == []
    assert crb.changed_fields(old, [rec(2, "a", s_a_span=[0, 1])]) == ["record ids"]


def test_classes():
    index = {("Stories", "Tsou", "f"): {"1": [rec(1, "a")], "2": [rec(2, "b")]}}
    new_index = {("Stories", "Tsou", "f"): {"1": [rec(1, "a")], "2": [rec(2, "B")]}}
    old_s = {("Stories", "Tsou", "f_S_1"): ("f.xml", "x"), ("Stories", "Tsou", "f_S_2"): ("f.xml", "y")}
    new_s = {("Stories", "Tsou", "f_S_1"): ("f.xml", "X"), ("Stories", "Tsou", "f_S_2"): ("f.xml", "y")}
    got = {r["sentence"]: (r["class"], r["changed_fields"])
           for r in crb.classify(old_s, new_s, index, new_index)}
    assert got == {"f_S_1": ("code_reacted", ""), "f_S_2": ("masked", "gloss")}
