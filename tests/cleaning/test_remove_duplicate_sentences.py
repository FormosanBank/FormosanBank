"""
Tests for QC/cleaning/remove_duplicate_sentences.py

Behavior (per B9.5 plan):
  - Identifies duplicate groups using the same equivalence as
    validate_duplicate_sentences (whitespace-normalized, --tier).
  - Keeps the first occurrence by (file, S id) sort order; removes the rest.
  - --dry-run is the default: no files are modified unless --apply is passed.
  - --scope file (default) only removes within-file duplicates.
  - --scope corpus also removes within-corpus cross-file duplicates.
"""

import os
import sys
from pathlib import Path

import pytest
from lxml import etree

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "QC" / "cleaning"))

import remove_duplicate_sentences as rds  # noqa: E402


def _write_xml(path: Path, sentences):
    """sentences: list of (s_id, [(kindOf, text), ...])"""
    parts = ['<?xml version="1.0" encoding="utf-8"?>',
             '<TEXT id="T1" xml:lang="ami" citation="x" '
             'BibTeX_citation="x" copyright="x">']
    for sid, forms in sentences:
        parts.append(f'  <S id="{sid}">')
        for kind, text in forms:
            parts.append(f'    <FORM kindOf="{kind}">{text}</FORM>')
        parts.append('  </S>')
    parts.append('</TEXT>')
    path.write_text("\n".join(parts), encoding="utf-8")


def _s_ids(xml_path: Path):
    root = etree.parse(str(xml_path)).getroot()
    return [s.get("id") for s in root.iter("S")]


# ---------------------------------------------------------------------------
# Planning (dry-run path) - reports duplicates without touching files
# ---------------------------------------------------------------------------

def test_plan_identifies_within_file_duplicates(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "same")]),
        ("S_2", [("standard", "different")]),
        ("S_3", [("standard", "same")]),  # duplicate of S_1
    ])
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    # First by (file, S id): S_1 kept; S_3 removed.
    assert plan == [(str(f.resolve()), "S_3")]


def test_plan_does_not_remove_across_files_when_scope_file(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    _write_xml(a, [("S_1", [("standard", "shared")])])
    _write_xml(b, [("S_1", [("standard", "shared")])])
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    assert plan == []


def test_plan_removes_across_files_when_scope_corpus(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    _write_xml(a, [("S_1", [("standard", "shared")])])
    _write_xml(b, [("S_1", [("standard", "shared")])])
    plan = rds.plan_removals(str(tmp_path), scope="corpus", tier="standard")
    # Sort order is by file path then s_id.  a.xml < b.xml -> a kept, b removed.
    assert plan == [(str(b.resolve()), "S_1")]


def test_plan_keeps_first_by_s_id_sort_within_file(tmp_path):
    """When multiple <S> in the same file are duplicates, keep the first by
    s_id sort (not document order)."""
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_5", [("standard", "dup")]),
        ("S_1", [("standard", "dup")]),
        ("S_3", [("standard", "dup")]),
    ])
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    # Sorted s_ids: S_1, S_3, S_5 -> keep S_1, remove S_3 and S_5
    removed_ids = sorted(s_id for _, s_id in plan)
    assert removed_ids == ["S_3", "S_5"]


def test_plan_whitespace_only_diff_is_duplicate(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "hello world")]),
        ("S_2", [("standard", "hello  world")]),
    ])
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    assert plan == [(str(f.resolve()), "S_2")]


# ---------------------------------------------------------------------------
# Apply path - mutates files
# ---------------------------------------------------------------------------

def test_dry_run_does_not_modify_files(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "same")]),
        ("S_2", [("standard", "same")]),
    ])
    before = f.read_text(encoding="utf-8")
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    assert len(plan) == 1
    # No apply() call: file untouched.
    after = f.read_text(encoding="utf-8")
    assert before == after


def test_apply_removes_duplicate_within_file(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "same")]),
        ("S_2", [("standard", "other")]),
        ("S_3", [("standard", "same")]),
    ])
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    rds.apply_removals(plan)
    assert _s_ids(f) == ["S_1", "S_2"]


def test_apply_removes_only_planned_s(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_5", [("standard", "dup")]),
        ("S_1", [("standard", "dup")]),
        ("S_3", [("standard", "dup")]),
        ("S_7", [("standard", "unique")]),
    ])
    plan = rds.plan_removals(str(tmp_path), scope="file", tier="standard")
    rds.apply_removals(plan)
    remaining = _s_ids(f)
    # Kept the lowest-id of the duplicate group plus the unique S.
    assert sorted(remaining) == ["S_1", "S_7"]


def test_apply_corpus_scope_removes_cross_file_duplicates(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    _write_xml(a, [("S_1", [("standard", "shared")])])
    _write_xml(b, [("S_1", [("standard", "shared")]),
                   ("S_2", [("standard", "unique-to-b")])])
    plan = rds.plan_removals(str(tmp_path), scope="corpus", tier="standard")
    rds.apply_removals(plan)
    assert _s_ids(a) == ["S_1"]
    assert _s_ids(b) == ["S_2"]


# ---------------------------------------------------------------------------
# CLI smoke
# ---------------------------------------------------------------------------

def test_cli_dry_run_default_does_not_mutate(tmp_path, monkeypatch, capsys):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "dup")]),
        ("S_2", [("standard", "dup")]),
    ])
    before = f.read_text(encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "remove_duplicate_sentences.py",
        "by_path", "--path", str(tmp_path),
    ])
    rc = rds.main()
    assert rc == 0
    after = f.read_text(encoding="utf-8")
    assert before == after  # default dry-run
    captured = capsys.readouterr().out
    assert "dry-run" in captured.lower() or "would remove" in captured.lower()


def test_cli_apply_mutates(tmp_path, monkeypatch):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "dup")]),
        ("S_2", [("standard", "dup")]),
    ])
    monkeypatch.setattr(sys, "argv", [
        "remove_duplicate_sentences.py",
        "by_path", "--path", str(tmp_path),
        "--apply",
    ])
    rc = rds.main()
    assert rc == 0
    assert _s_ids(f) == ["S_1"]
