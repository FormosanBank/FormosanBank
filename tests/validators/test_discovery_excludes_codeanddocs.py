"""Validator discovery must skip CodeAndDocs/ (POL-035 snapshots).

Regression for the 2026-08-12 SEALS33 finding: validating a corpus ROOT
(not its XML/ dir) pulled the pre-correction snapshot copies in as
targets, and V081 reported every snapshotted TEXT id as a cross-corpus
collision with its published original.
"""
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from QC.validation._discovery import discover_xml_files  # noqa: E402

XML = ('<?xml version="1.0" ?>\n'
       '<TEXT id="toy_text" xml:lang="ami" dialect="unknown" citation="c" '
       'copyright="p" BibTeX_citation="b">'
       '<S id="1"><FORM kindOf="original">a</FORM></S></TEXT>')


def _make_corpus_with_snapshot(root: Path) -> Path:
    corpus = root / "Corpora" / "Toy"
    (corpus / "XML").mkdir(parents=True)
    (corpus / "XML" / "a.xml").write_text(XML, encoding="utf-8")
    snap = corpus / "CodeAndDocs" / "pre_correction_snapshot" / "XML"
    snap.mkdir(parents=True)
    (snap / "a.xml").write_text(XML, encoding="utf-8")
    return corpus


def test_discovery_skips_codeanddocs_under_corpus_root(tmp_path):
    corpus = _make_corpus_with_snapshot(tmp_path)
    found = discover_xml_files(corpus)
    assert found == [corpus / "XML" / "a.xml"]


def test_discovery_honors_explicit_codeanddocs_target(tmp_path):
    corpus = _make_corpus_with_snapshot(tmp_path)
    snap_dir = corpus / "CodeAndDocs" / "pre_correction_snapshot"
    found = discover_xml_files(snap_dir)
    assert found == [snap_dir / "XML" / "a.xml"]


def test_discovery_single_file_passthrough(tmp_path):
    corpus = _make_corpus_with_snapshot(tmp_path)
    f = corpus / "CodeAndDocs" / "pre_correction_snapshot" / "XML" / "a.xml"
    assert discover_xml_files(f) == [f]
