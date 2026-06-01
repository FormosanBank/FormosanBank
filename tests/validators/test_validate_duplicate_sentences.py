"""
Tests for QC/validation/validate_duplicate_sentences.py

Per the B9.5 plan, this validator emits:
  - HARD findings for duplicate <S> within the same XML file
  - SOFT findings for duplicate <S> across different files in the same corpus

Equivalence: whitespace-normalized FORM text; comparison on kindOf="standard"
by default (--tier flag overrides).

Tests cover:
  - normalize_for_comparison helper (whitespace collapsing)
  - extract_sentences pulls only direct-child FORM @ chosen kindOf
  - within-file duplicates -> HARD
  - within-corpus cross-file duplicates -> SOFT
  - whitespace-only differences treated as duplicates
  - --tier original respects the chosen tier
  - empty FORM text skipped
"""

import os
import sys
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "QC" / "validation"))

import validate_duplicate_sentences as vds  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_xml(path: Path, sentences):
    """sentences: list of (s_id, [(kindOf, text), ...])"""
    parts = ['<?xml version="1.0" encoding="utf-8"?>',
             '<TEXT id="T1" xml:lang="ami" citation="x" BibTeX_citation="x" copyright="x">']
    for sid, forms in sentences:
        parts.append(f'  <S id="{sid}">')
        for kind, text in forms:
            parts.append(f'    <FORM kindOf="{kind}">{text}</FORM>')
        parts.append('  </S>')
    parts.append('</TEXT>')
    path.write_text("\n".join(parts), encoding="utf-8")


# ---------------------------------------------------------------------------
# normalize_for_comparison
# ---------------------------------------------------------------------------

def test_normalize_collapses_internal_whitespace():
    assert vds.normalize_for_comparison("hello   world") == "hello world"


def test_normalize_strips_leading_trailing_whitespace():
    assert vds.normalize_for_comparison("  hello world  ") == "hello world"


def test_normalize_handles_tabs_and_newlines():
    assert vds.normalize_for_comparison("hello\tworld\n  again") == "hello world again"


def test_normalize_does_not_lowercase():
    # Plan deliberately leaves case-sensitivity decision out of scope; do not lowercase.
    assert vds.normalize_for_comparison("Hello") != vds.normalize_for_comparison("hello")


# ---------------------------------------------------------------------------
# extract_sentences
# ---------------------------------------------------------------------------

def test_extract_sentences_returns_only_chosen_tier(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("original", "Halo"), ("standard", "halo")]),
        ("S_2", [("original", "Yes"), ("standard", "yes")]),
    ])
    forms = vds.extract_sentences(str(f), kind_of="standard")
    assert forms == [("S_1", "halo"), ("S_2", "yes")]

    orig = vds.extract_sentences(str(f), kind_of="original")
    assert orig == [("S_1", "Halo"), ("S_2", "Yes")]


def test_extract_sentences_skips_empty(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "hi")]),
        ("S_2", [("standard", "  ")]),  # only whitespace
        ("S_3", [("standard", "bye")]),
    ])
    forms = vds.extract_sentences(str(f), kind_of="standard")
    assert [sid for sid, _ in forms] == ["S_1", "S_3"]


# ---------------------------------------------------------------------------
# find_duplicates - within-file (HARD) and within-corpus cross-file (SOFT)
# ---------------------------------------------------------------------------

def test_within_file_duplicate_is_hard(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "same sentence")]),
        ("S_2", [("standard", "other sentence")]),
        ("S_3", [("standard", "same sentence")]),  # duplicate of S_1
    ])
    findings = vds.find_duplicates(str(tmp_path), kind_of="standard")
    hard = [f for f in findings if f.severity == "HARD"]
    soft = [f for f in findings if f.severity == "SOFT"]
    assert len(hard) == 1
    assert len(soft) == 0
    f0 = hard[0]
    assert f0.normalized_text == "same sentence"
    assert sorted(f0.s_ids) == ["S_1", "S_3"]
    # All occurrences within one file
    assert len({occ.file for occ in f0.occurrences}) == 1


def test_within_corpus_cross_file_is_soft(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    _write_xml(a, [("S_1", [("standard", "shared sentence")])])
    _write_xml(b, [("S_1", [("standard", "shared sentence")])])
    findings = vds.find_duplicates(str(tmp_path), kind_of="standard")
    assert [f.severity for f in findings] == ["SOFT"]
    f0 = findings[0]
    assert f0.normalized_text == "shared sentence"
    assert len({occ.file for occ in f0.occurrences}) == 2


def test_within_corpus_with_within_file_separately_categorized(tmp_path):
    a = tmp_path / "a.xml"
    b = tmp_path / "b.xml"
    _write_xml(a, [
        ("S_1", [("standard", "alpha")]),
        ("S_2", [("standard", "alpha")]),  # within-file dup
    ])
    _write_xml(b, [
        ("S_3", [("standard", "beta")]),
    ])
    # Also a cross-file pair on "beta"
    c = tmp_path / "c.xml"
    _write_xml(c, [
        ("S_4", [("standard", "beta")]),
    ])
    findings = vds.find_duplicates(str(tmp_path), kind_of="standard")
    by_text = {f.normalized_text: f for f in findings}
    assert by_text["alpha"].severity == "HARD"
    assert by_text["beta"].severity == "SOFT"


def test_whitespace_only_differences_are_duplicates(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "hello  world")]),
        ("S_2", [("standard", "hello world")]),
    ])
    findings = vds.find_duplicates(str(tmp_path), kind_of="standard")
    assert len(findings) == 1
    assert findings[0].severity == "HARD"
    assert findings[0].normalized_text == "hello world"


def test_no_duplicates_returns_empty(tmp_path):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "one")]),
        ("S_2", [("standard", "two")]),
        ("S_3", [("standard", "three")]),
    ])
    findings = vds.find_duplicates(str(tmp_path), kind_of="standard")
    assert findings == []


def test_tier_flag_only_affects_chosen_tier(tmp_path):
    """Original tier matches but standard differs -> only original-tier scan finds the dup."""
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("original", "spelled-the-old-way"), ("standard", "spelled the new way")]),
        ("S_2", [("original", "spelled-the-old-way"), ("standard", "completely different")]),
    ])
    std_findings = vds.find_duplicates(str(tmp_path), kind_of="standard")
    orig_findings = vds.find_duplicates(str(tmp_path), kind_of="original")
    assert std_findings == []
    assert len(orig_findings) == 1
    assert orig_findings[0].severity == "HARD"


# ---------------------------------------------------------------------------
# CLI smoke - exits 0 even with findings (informational, not a HARD failure of the run)
# ---------------------------------------------------------------------------

def test_cli_smoke_runs(tmp_path, capsys, monkeypatch):
    f = tmp_path / "a.xml"
    _write_xml(f, [
        ("S_1", [("standard", "same")]),
        ("S_2", [("standard", "same")]),
    ])
    out_csv = tmp_path / "out.csv"
    monkeypatch.setattr(sys, "argv", [
        "validate_duplicate_sentences.py",
        "by_path", "--path", str(tmp_path),
        "--output", str(out_csv),
    ])
    rc = vds.main()
    assert rc == 0
    assert out_csv.exists()
    contents = out_csv.read_text(encoding="utf-8")
    assert "HARD" in contents
    assert "S_1" in contents and "S_2" in contents
