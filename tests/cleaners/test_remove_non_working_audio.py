"""Tests for QC/cleaning/remove_non_working_audio.py.

IMPORTANT: All tests in this file are CURRENTLY XFAIL because the
script's current interface (legacy ePark-specific, no CLI args,
hardcoded CSV input) doesn't match the test design. These tests
specify the BEHAVIORAL CONTRACT we expect after sub-project B
refactors the script:

  - Accepts `--corpora_path <dir>` (dir/XML/*.xml is walked)
  - Detects broken <AUDIO file="..."/> refs by checking file existence
  - Removes broken refs in place; valid refs survive
  - Exits 0 on success, non-zero on failure
  - Outputs the list of scrubbed audio files so the operator can review
    what was removed (stdout or stderr; structured or human-readable)
  - Emits a warning indicator (e.g. "WARNING" / "WARN" in output) whenever
    any non-working audio is encountered, so silent-success can't mask
    real data loss

When B's refactor lands and the tests start passing, pytest will flag
them as XPASSED (because strict=True). At that point the xfail markers
should be removed.

XML is built inline via tmp_path rather than as a standalone fixture
because the audio paths must be dynamic (point at real tmp_path WAVs
that audio_file_factory generates) — a committed fixture file would
encode absolute paths that wouldn't resolve on other machines.

For the "no audio" case the existing valid_minimal.xml fixture is used
directly, since its content doesn't depend on dynamic paths.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


REMOVE_AUDIO = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "remove_non_working_audio.py"
XFAIL_REASON = (
    "remove_non_working_audio.py interface refactor deferred to sub-project B "
    "(currently hardcoded-CSV + ePark-specific; spec'd behavior here is the "
    "desired post-refactor contract)"
)


def _write_xml_with_audio_refs(path: Path, audio_paths: list[Path]) -> None:
    """Build an XML file referencing the given audio paths.

    Each entry in audio_paths becomes an <AUDIO> element with file="...".
    Paths are passed through as strings; whether they exist on disk
    determines what remove_non_working_audio.py considers valid.
    """
    root = ET.Element("TEXT", attrib={
        "id": "TEST_AUDIO",
        "citation": "test",
        "BibTeX_citation": "@test{test}",
        "copyright": "test",
        "xml:lang": "ami",
    })
    for i, audio_path in enumerate(audio_paths, 1):
        s = ET.SubElement(root, "S", attrib={"id": f"S_{i}"})
        ET.SubElement(s, "FORM", attrib={"kindOf": "original"}).text = f"Sentence {i}."
        ET.SubElement(s, "FORM", attrib={"kindOf": "standard"}).text = f"Sentence {i}."
        ET.SubElement(s, "AUDIO", attrib={
            "file": str(audio_path),
            "start": "0",
            "end": "1",
        })
    ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)


def _audio_refs(xml_path: Path) -> list[str]:
    """Return the list of file="..." values from all <AUDIO> elements."""
    root = ET.parse(xml_path).getroot()
    return [
        ref
        for a in root.iter("AUDIO")
        if (ref := a.get("file")) is not None
    ]


def _run_remove(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REMOVE_AUDIO), "--corpora_path", str(corpora_path)],
        capture_output=True,
        text=True,
    )


def _make_xml_dir(tmp_path: Path) -> Path:
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    return d


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_all_valid_audio_refs_are_kept(tmp_path, audio_file_factory):
    xml_dir = _make_xml_dir(tmp_path)
    good_a = audio_file_factory(0.1)
    good_b = audio_file_factory(0.1)
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [good_a, good_b])

    proc = _run_remove(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # The refactored script must report what it processed; a silent no-op (e.g.
    # the legacy code that ignores --corpora_path and reads a CSV instead) would
    # produce empty stdout and would NOT satisfy this assertion.
    assert (proc.stdout + proc.stderr).strip() != "", (
        "expected the refactored script to emit some progress indication "
        "(stdout or stderr) when given --corpora_path"
    )

    refs = _audio_refs(xml)
    assert len(refs) == 2, f"expected 2 audio refs retained, got {refs}"
    assert str(good_a) in refs
    assert str(good_b) in refs


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_broken_audio_ref_is_removed_others_retained(tmp_path, audio_file_factory):
    xml_dir = _make_xml_dir(tmp_path)
    good = audio_file_factory(0.1)
    broken = tmp_path / "does_not_exist.wav"  # never created
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [good, broken])

    proc = _run_remove(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    refs = _audio_refs(xml)
    assert str(good) in refs, "valid audio ref was incorrectly removed"
    assert str(broken) not in refs, "broken audio ref was not removed"


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_corpus_with_no_audio_is_a_noop(tmp_path, fixtures_dir, copy_fixture):
    """valid_minimal.xml has no <AUDIO> elements; script should leave it byte-exact."""
    work = copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    before = work.read_bytes()

    proc = _run_remove(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # The refactored script must report what it processed; a silent no-op (e.g.
    # the legacy code that ignores --corpora_path and reads a CSV instead) would
    # produce empty stdout and would NOT satisfy this assertion.
    assert (proc.stdout + proc.stderr).strip() != "", (
        "expected the refactored script to emit some progress indication "
        "(stdout or stderr) when given --corpora_path"
    )
    assert work.read_bytes() == before, (
        "cleaner modified a corpus that had no AUDIO elements"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_all_broken_audio_refs_are_all_removed(tmp_path):
    xml_dir = _make_xml_dir(tmp_path)
    broken_a = tmp_path / "missing_a.wav"
    broken_b = tmp_path / "missing_b.wav"
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [broken_a, broken_b])

    proc = _run_remove(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    refs = _audio_refs(xml)
    assert refs == [], f"expected all broken refs removed, got: {refs}"

    # Surviving XML should still be well-formed and parseable, with both
    # sentences retained but their AUDIO children gone.
    root = ET.parse(xml).getroot()
    sentences = list(root.iter("S"))
    assert len(sentences) == 2, "sentences should not have been removed, only their AUDIO children"
    for s in sentences:
        assert s.find("AUDIO") is None
        assert s.find("FORM") is not None


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_outputs_list_of_scrubbed_files(tmp_path):
    """The refactored script must report which audio files it removed.

    A run that silently scrubs broken refs without naming them gives the
    operator no way to review or recover from a mistake. The script must
    print enough information (on stdout or stderr) for the operator to
    identify each scrubbed reference — at minimum the basename of each
    removed audio path. Exact format (one-per-line, JSON, CSV) is
    intentionally not specified — sub-project B picks it.
    """
    xml_dir = _make_xml_dir(tmp_path)
    broken_a = tmp_path / "missing_a.wav"
    broken_b = tmp_path / "missing_b.wav"
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [broken_a, broken_b])

    proc = _run_remove(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    combined = proc.stdout + proc.stderr
    # Each scrubbed file must be identifiable SOMEWHERE the operator
    # can find — either in the script's stdout/stderr OR in a sidecar
    # log/CSV the script wrote under corpora_path. Match on basename
    # rather than full path so the script has freedom in how it reports
    # (relative path, absolute path, just the filename, summary line
    # + sidecar file, etc.). A summary-to-stdout + per-file-to-sidecar
    # design is the most likely B implementation for large scrub lists.
    def _named_anywhere(name: str) -> bool:
        if name in combined:
            return True
        for path in tmp_path.rglob("*"):
            if path.suffix.lower() not in (".log", ".csv", ".txt"):
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if name in content:
                return True
        return False

    assert _named_anywhere(broken_a.name), (
        f"expected scrubbed file {broken_a.name!r} named in output or any "
        f"sidecar log/csv/txt under tmp_path; got:\n"
        f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )
    assert _named_anywhere(broken_b.name), (
        f"expected scrubbed file {broken_b.name!r} named in output or any "
        f"sidecar log/csv/txt under tmp_path; got:\n"
        f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_warns_when_non_working_audio_encountered(tmp_path, audio_file_factory):
    """The refactored script must emit a warning indicator when ANY non-working
    audio is encountered.

    A successful-looking run (exit 0, no visible alert) that silently removed
    references is a recipe for unnoticed data loss. The script must signal —
    via the literal token "WARNING" or "WARN" in its output (case-insensitive)
    — that something was wrong. Catches a regression where the cleaner becomes
    too quiet about its work.
    """
    xml_dir = _make_xml_dir(tmp_path)
    good = audio_file_factory(0.1)
    broken = tmp_path / "broken.wav"  # never created
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [good, broken])

    proc = _run_remove(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    combined = (proc.stdout + proc.stderr).lower()
    assert "warn" in combined, (
        f"expected a WARNING indicator in output when broken audio encountered; "
        f"got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_REASON)
def test_cleaner_is_idempotent(tmp_path, audio_file_factory):
    """Critical for in-place mutators: running twice produces the same
    state as running once. Catches a regression where the cleaner
    re-removes audio refs that have become valid since the previous run."""
    xml_dir = _make_xml_dir(tmp_path)
    good = audio_file_factory(0.1)
    broken = tmp_path / "does_not_exist.wav"
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [good, broken])

    _run_remove(tmp_path)
    after_one = _audio_refs(xml)
    # The first run must have actually removed the broken ref; otherwise the
    # idempotency check below is vacuously satisfied by a no-op script.
    assert str(broken) not in after_one, (
        "first run did not remove the broken audio ref — idempotency check "
        "would be vacuously true"
    )
    _run_remove(tmp_path)
    after_two = _audio_refs(xml)

    assert after_one == after_two, "cleaner is not idempotent"
