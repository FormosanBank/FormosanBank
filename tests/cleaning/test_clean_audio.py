"""Tests for QC/cleaning/clean_audio.py.

Behavioral contract per B9.2 plan W1:
- Reads a broken_audio.csv with at least columns xml_file, audio_file, kind.
- Removes the matching <AUDIO> element from the XML file (regardless of `kind`).
- Optionally deletes the audio file from disk when --also-delete-files is set.
- Dry-run is the DEFAULT (--apply must be passed for changes to land).
- Walks `<corpus>/XML/`; resolves audio files in `<corpus>/Audio/`.
- CLI: --corpus_path, --broken_csv, --dry-run/--apply, --also-delete-files.
- Empty broken_audio.csv → no-op.

These tests are intentionally subprocess-based so they exercise the CLI
exactly the way the operator will.
"""
import csv
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


CLEAN_AUDIO = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_audio.py"


def _write_xml_with_audio_refs(path: Path, audio_filenames: list[str]) -> None:
    """Write an XML at `path` with one <S> per audio_filename, each carrying an <AUDIO>."""
    root = ET.Element("TEXT", attrib={
        "id": "TEST_AUDIO",
        "citation": "test",
        "BibTeX_citation": "@test{test}",
        "copyright": "test",
        "xml:lang": "ami",
    })
    for i, audio_filename in enumerate(audio_filenames, 1):
        s = ET.SubElement(root, "S", attrib={"id": f"S_{i}"})
        ET.SubElement(s, "FORM", attrib={"kindOf": "original"}).text = f"Sentence {i}."
        ET.SubElement(s, "FORM", attrib={"kindOf": "standard"}).text = f"Sentence {i}."
        ET.SubElement(s, "AUDIO", attrib={
            "file": audio_filename,
            "start": "0",
            "end": "1",
        })
    ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)


def _audio_refs(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [a.get("file") for a in root.iter("AUDIO")]


def _write_broken_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["xml_file", "audio_file", "kind"])
        writer.writeheader()
        writer.writerows(rows)


def _make_corpus(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Create <tmp_path>/XML/ and <tmp_path>/Audio/, return (corpus_root, xml_dir, audio_dir)."""
    corpus = tmp_path
    xml_dir = corpus / "XML"
    audio_dir = corpus / "Audio"
    xml_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    return corpus, xml_dir, audio_dir


def _run(corpus_path: Path, broken_csv: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(CLEAN_AUDIO),
            "--corpus_path", str(corpus_path),
            "--broken_csv", str(broken_csv),
            *extra,
        ],
        capture_output=True,
        text=True,
    )


def test_dry_run_default_does_not_modify_xml(tmp_path, audio_file_factory):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good_audio = audio_file_factory(0.1)
    audio_filename = good_audio.name
    # place a broken-shaped placeholder in Audio/
    audio_path = audio_dir / audio_filename
    audio_path.write_bytes(b"")  # zero-byte = broken

    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [audio_filename])
    before = xml.read_bytes()

    broken_csv = tmp_path / "broken_audio.csv"
    _write_broken_csv(broken_csv, [{
        "xml_file": str(xml),
        "audio_file": audio_filename,
        "kind": "unloadable",
    }])

    proc = _run(corpus, broken_csv)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # dry-run is the default: file untouched
    assert xml.read_bytes() == before, "dry-run modified XML"
    assert audio_path.exists(), "dry-run deleted audio file"
    # dry-run should still report what it WOULD do
    combined = proc.stdout + proc.stderr
    assert audio_filename in combined or "dry" in combined.lower()


def test_apply_removes_audio_element(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    audio_filename = "broken.wav"
    (audio_dir / audio_filename).write_bytes(b"")

    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [audio_filename, "good.wav"])

    broken_csv = tmp_path / "broken_audio.csv"
    _write_broken_csv(broken_csv, [{
        "xml_file": str(xml),
        "audio_file": audio_filename,
        "kind": "unloadable",
    }])

    proc = _run(corpus, broken_csv, "--apply")
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    refs = _audio_refs(xml)
    assert audio_filename not in refs, f"broken audio not removed; refs={refs}"
    assert "good.wav" in refs, "untargeted audio incorrectly removed"


def test_apply_removes_regardless_of_kind(tmp_path):
    """All `kind` values are HARD removals — script doesn't care which."""
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    files = ["missing.wav", "silent.wav", "unloadable.wav", "invalid.wav"]
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, files + ["safe.wav"])

    broken_csv = tmp_path / "broken_audio.csv"
    _write_broken_csv(broken_csv, [
        {"xml_file": str(xml), "audio_file": "missing.wav", "kind": "missing"},
        {"xml_file": str(xml), "audio_file": "silent.wav", "kind": "silent"},
        {"xml_file": str(xml), "audio_file": "unloadable.wav", "kind": "unloadable"},
        {"xml_file": str(xml), "audio_file": "invalid.wav", "kind": "invalid_range"},
    ])

    proc = _run(corpus, broken_csv, "--apply")
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    refs = _audio_refs(xml)
    assert refs == ["safe.wav"], f"expected only safe.wav to remain; got: {refs}"


def test_also_delete_files_removes_audio_from_disk(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    audio_filename = "broken.wav"
    audio_path = audio_dir / audio_filename
    audio_path.write_bytes(b"some-bytes")  # presence required to test deletion

    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [audio_filename])

    broken_csv = tmp_path / "broken_audio.csv"
    _write_broken_csv(broken_csv, [{
        "xml_file": str(xml),
        "audio_file": audio_filename,
        "kind": "unloadable",
    }])

    proc = _run(corpus, broken_csv, "--apply", "--also-delete-files")
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert not audio_path.exists(), "audio file not removed from disk"
    refs = _audio_refs(xml)
    assert refs == [], f"expected XML AUDIO removed too; refs={refs}"


def test_empty_broken_csv_is_noop(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, ["a.wav", "b.wav"])
    before = xml.read_bytes()

    broken_csv = tmp_path / "broken_audio.csv"
    _write_broken_csv(broken_csv, [])  # header only

    proc = _run(corpus, broken_csv, "--apply")
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert xml.read_bytes() == before, "empty CSV should leave XML unchanged"


def test_walks_corpus_XML_subdir_not_legacy_final_xml(tmp_path):
    """The script should look under <corpus_path>/XML/, not Final_XML/."""
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    # Put a XML file under the canonical XML/ dir
    xml = xml_dir / "sub" / "nested.xml"
    xml.parent.mkdir(parents=True, exist_ok=True)
    _write_xml_with_audio_refs(xml, ["broken.wav"])

    broken_csv = tmp_path / "broken_audio.csv"
    _write_broken_csv(broken_csv, [{
        "xml_file": str(xml),
        "audio_file": "broken.wav",
        "kind": "missing",
    }])

    proc = _run(corpus, broken_csv, "--apply")
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    refs = _audio_refs(xml)
    assert refs == [], f"expected nested XML's AUDIO removed; got {refs}"
