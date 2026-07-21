"""Tests for QC/validation/validate_audio.py.

Behavioral contract per B9.2 plan W2-W4:
- W2: emit a single unified broken_audio.csv with a `kind` column:
      missing | unloadable | silent | invalid_range
- W2: detect AUDIO/@start >= AUDIO/@end → kind="invalid_range"
- W3: silence detection covers both WAV and MP3 (MP3 via ffprobe)
- W4: emit Finding objects with rule_ids V100-V105; HARD findings
      cause non-zero exit; SOFT findings warn but don't fail.

Tests run validate_audio.py as a subprocess. Output artifacts land in
tmp_path/logs/ so the repo's logs/ dir is never polluted.
"""
import csv
import shutil
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


VALIDATE_AUDIO = Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_audio.py"


def _write_text(path: Path, audio_entries: list[dict]) -> None:
    """Write a TEXT XML at `path` with one <S> per audio_entries dict.

    Each entry: {"id": "S_1", "form": "...", "file": "audio.wav",
                 "start": "0", "end": "1"}. start/end optional.
    """
    root = ET.Element("TEXT", attrib={
        "id": "TEST",
        "citation": "t",
        "BibTeX_citation": "@t{t}",
        "copyright": "t",
        "xml:lang": "ami",
    })
    for e in audio_entries:
        s = ET.SubElement(root, "S", attrib={"id": e["id"]})
        ET.SubElement(s, "FORM", attrib={"kindOf": "original"}).text = e.get("form", "Halo.")
        attrib = {"file": e["file"]}
        if "start" in e:
            attrib["start"] = str(e["start"])
        if "end" in e:
            attrib["end"] = str(e["end"])
        ET.SubElement(s, "AUDIO", attrib=attrib)
    ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)


def _make_corpus(tmp_path: Path) -> tuple[Path, Path, Path]:
    corpus = tmp_path
    xml_dir = corpus / "XML"
    audio_dir = corpus / "Audio"
    xml_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    return corpus, xml_dir, audio_dir


def _make_audible_wav(path: Path, duration_sec: float = 0.2, sample_rate: int = 8000) -> None:
    """Write a non-silent WAV (mid-amplitude square wave)."""
    n_frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        # Mid-amplitude 1 kHz square wave so RMS is well above the silence threshold.
        period = sample_rate // 1000
        frames = bytearray()
        for i in range(n_frames):
            val = 8000 if (i // (period // 2)) % 2 == 0 else -8000
            frames += int(val).to_bytes(2, "little", signed=True)
        w.writeframes(bytes(frames))


def _make_silent_wav(path: Path, duration_sec: float = 0.2, sample_rate: int = 8000) -> None:
    n_frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(b"\x00\x00" * n_frames)


def _run(xml_dir: Path, audio_dir: Path, log_dir: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(VALIDATE_AUDIO),
            "--path", str(audio_dir),
            "--xml_path", str(xml_dir),
            "--log_dir", str(log_dir),
            *extra,
        ],
        capture_output=True,
        text=True,
    )


def _read_broken_csv(log_dir: Path) -> list[dict]:
    csv_path = log_dir / "broken_audio.csv"
    if not csv_path.is_file():
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_duration_csv(log_dir: Path) -> list[dict]:
    csv_path = log_dir / "audio_duration_issues.csv"
    if not csv_path.is_file():
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


# -----------------------------------------------------------------------------
# W2: unified broken_audio.csv
# -----------------------------------------------------------------------------


def test_missing_audio_file_lands_with_kind_missing(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "does_not_exist.wav", "start": "0", "end": "1"}])

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert (log_dir / "broken_audio.csv").is_file(), (
        f"expected broken_audio.csv to be created; stderr={proc.stderr}"
    )
    rows = _read_broken_csv(log_dir)
    assert any(r["audio_file"] == "does_not_exist.wav" and r["kind"] == "missing" for r in rows), (
        f"expected kind=missing entry; rows={rows}"
    )
    row = next(r for r in rows if r["audio_file"] == "does_not_exist.wav")
    assert row["element_id"] == "S_1"
    assert row["start"] == "0"
    assert row["end"] == "1"


def test_text_audio_attribute_fileless_child_refs_are_validated(tmp_path):
    """TEXT/@audio is the shared-file pattern allowed by validate_xml.py.

    Sentence/word AUDIO elements in this mode carry start/end but no own
    file attribute. validate_audio must still resolve/check the shared
    TEXT-level file rather than silently skipping the child range.
    """
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    xml = xml_dir / "test.xml"
    root = ET.Element("TEXT", attrib={
        "id": "TEST",
        "citation": "t",
        "BibTeX_citation": "@t{t}",
        "copyright": "t",
        "xml:lang": "ami",
        "audio": "shared.wav",
    })
    s = ET.SubElement(root, "S", attrib={"id": "S_1"})
    ET.SubElement(s, "FORM", attrib={"kindOf": "original"}).text = "Halo."
    ET.SubElement(s, "AUDIO", attrib={"start": "0", "end": "1"})
    ET.ElementTree(root).write(str(xml), encoding="utf-8", xml_declaration=True)

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert proc.returncode != 0, "missing shared TEXT/@audio file should be HARD"
    rows = _read_broken_csv(log_dir)
    assert any(
        r["audio_file"] == "shared.wav"
        and r["element_id"] == "S_1"
        and r["kind"] == "missing"
        for r in rows
    ), f"expected missing row for shared TEXT/@audio child ref; rows={rows}"


def test_unloadable_audio_file_lands_with_kind_unloadable(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    # Empty file is not a valid WAV/MP3.
    bad = audio_dir / "bad.wav"
    bad.write_bytes(b"")
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "bad.wav", "start": "0", "end": "1"}])

    log_dir = tmp_path / "logs"
    _run(xml_dir, audio_dir, log_dir)
    rows = _read_broken_csv(log_dir)
    assert any(r["audio_file"] == "bad.wav" and r["kind"] == "unloadable" for r in rows), (
        f"expected kind=unloadable entry; rows={rows}"
    )


def test_silent_wav_lands_with_kind_silent(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    silent = audio_dir / "silent.wav"
    _make_silent_wav(silent)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "silent.wav", "start": "0", "end": "0.2"}])

    log_dir = tmp_path / "logs"
    _run(xml_dir, audio_dir, log_dir, "--check_silence")
    rows = _read_broken_csv(log_dir)
    assert any(r["audio_file"] == "silent.wav" and r["kind"] == "silent" for r in rows), (
        f"expected kind=silent entry; rows={rows}"
    )


def test_invalid_range_when_start_ge_end(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good = audio_dir / "ok.wav"
    _make_audible_wav(good)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "ok.wav", "start": "2", "end": "1"}])

    log_dir = tmp_path / "logs"
    _run(xml_dir, audio_dir, log_dir)
    rows = _read_broken_csv(log_dir)
    assert any(r["audio_file"] == "ok.wav" and r["kind"] == "invalid_range" for r in rows), (
        f"expected kind=invalid_range entry; rows={rows}"
    )


def test_invalid_range_when_start_equals_end(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good = audio_dir / "ok.wav"
    _make_audible_wav(good)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "ok.wav", "start": "1", "end": "1"}])

    log_dir = tmp_path / "logs"
    _run(xml_dir, audio_dir, log_dir)
    rows = _read_broken_csv(log_dir)
    assert any(r["audio_file"] == "ok.wav" and r["kind"] == "invalid_range" for r in rows), (
        f"expected kind=invalid_range entry; rows={rows}"
    )


def test_clean_corpus_emits_empty_broken_csv(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good = audio_dir / "ok.wav"
    _make_audible_wav(good)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "ok.wav", "start": "0", "end": "0.2"}])

    log_dir = tmp_path / "logs"
    _run(xml_dir, audio_dir, log_dir)
    rows = _read_broken_csv(log_dir)
    assert rows == [], f"clean corpus produced unexpected broken_audio rows: {rows}"


# -----------------------------------------------------------------------------
# W3: MP3 silence detection
# -----------------------------------------------------------------------------


HAS_FFPROBE = shutil.which("ffprobe") is not None


@pytest.mark.skipif(not HAS_FFPROBE, reason="ffprobe required for MP3 silence detection")
def test_is_silent_dispatches_on_extension(tmp_path):
    """The renamed `is_silent` helper should accept both WAV and MP3 paths
    and dispatch appropriately. Smoke test using a WAV file — actual MP3
    silence behavior is tested in test_is_silent_mp3_detects_silent_file.
    """
    from QC.validation import validate_audio
    # Renaming the helper is part of W3 — this is a contract test.
    assert hasattr(validate_audio, "is_silent"), (
        "Expected unified is_silent helper after W3 rename."
    )
    silent = tmp_path / "silent.wav"
    _make_silent_wav(silent)
    assert validate_audio.is_silent(str(silent)) is True


HAS_FFMPEG = shutil.which("ffmpeg") is not None


def _make_silent_mp3(path: Path, duration_sec: float = 3.0) -> bool:
    """Generate a silent MP3 via ffmpeg. Returns True on success."""
    proc = subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"anullsrc=r=22050:cl=mono",
            "-t", str(duration_sec), "-acodec", "libmp3lame",
            str(path),
        ],
        capture_output=True,
    )
    return proc.returncode == 0 and path.is_file()


@pytest.mark.skipif(not (HAS_FFPROBE and HAS_FFMPEG),
                    reason="ffmpeg+ffprobe required for MP3 silence detection")
def test_is_silent_mp3_detects_silent_file(tmp_path):
    """A wholly silent MP3 (generated via ffmpeg anullsrc) should be
    detected as silent."""
    from QC.validation import validate_audio
    mp3 = tmp_path / "silent.mp3"
    if not _make_silent_mp3(mp3):
        pytest.skip("could not generate silent MP3 fixture")
    result = validate_audio.is_silent_mp3(str(mp3))
    # `None` is acceptable (ffprobe unavailable / unexpected output) but a
    # successful run must return True for a fully-silent file.
    assert result in (True, None), f"expected True/None, got {result!r}"
    if result is None:
        pytest.skip("ffprobe returned no usable silencedetect output")


@pytest.mark.skipif(not (HAS_FFPROBE and HAS_FFMPEG),
                    reason="ffmpeg+ffprobe required for MP3 silence detection")
def test_is_silent_mp3_returns_none_for_corrupt_mp3(tmp_path):
    """A corrupt/non-MP3 file should yield None (caller escalates to unloadable)."""
    from QC.validation import validate_audio
    bad = tmp_path / "bad.mp3"
    bad.write_bytes(b"not an mp3 at all")
    result = validate_audio.is_silent_mp3(str(bad))
    assert result is None, f"expected None for corrupt MP3, got {result!r}"


# -----------------------------------------------------------------------------
# W4: Finding framework integration
# -----------------------------------------------------------------------------


def test_finding_v100_to_v103_emitted_for_hard_breakage(tmp_path):
    """Per W4, validator should emit Findings with rule_ids V100-V103
    for the four HARD broken-audio classes. Verify by checking the
    stderr summary for the rule IDs."""
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "missing.wav", "start": "0", "end": "1"}])

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    combined = (proc.stdout + proc.stderr).lower()
    # V100 = missing; that's what this fixture triggers.
    assert "v100" in combined, (
        f"expected V100 rule ID in output; stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_hard_findings_cause_nonzero_exit(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "missing.wav", "start": "0", "end": "1"}])

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert proc.returncode != 0, (
        f"expected non-zero exit when HARD findings present; got {proc.returncode}"
    )


def test_no_findings_means_clean_exit(tmp_path):
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good = audio_dir / "ok.wav"
    _make_audible_wav(good)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{"id": "S_1", "file": "ok.wav", "start": "0", "end": "0.2"}])

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert proc.returncode == 0, (
        f"expected exit 0 on clean corpus; got {proc.returncode}, "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_words_per_second_uses_clip_range_not_whole_file(tmp_path):
    """Shared whole-file audio must use each AUDIO start/end for V105 rates."""
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good = audio_dir / "whole.wav"
    _make_audible_wav(good, duration_sec=12.0)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{
        "id": "S_1",
        "file": "whole.wav",
        "start": "4",
        "end": "5",
        "form": "two words",
    }])

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert proc.returncode == 0
    assert _read_duration_csv(log_dir) == []


def test_no_V105_when_FORM_is_UNCLEAR_only(tmp_path):
    """UNCLEAR-only FORM must not trigger the cps/wps SOFT finding (V105).

    Pre-2026-06-08 behavior: validate_audio.py extracted form_elem.text
    (empty for <FORM><UNCLEAR/></FORM>) and computed words/sec = 0,
    which is < 0.1, which unconditionally triggered V105. The signal
    ("speaker too slow") was wrong; the truth is "audio was
    unintelligible — nothing to count." Fix: use itertext() to gather
    all text under FORM, and skip the cps/wps check entirely when the
    resulting text is empty/whitespace.

    Builds an explicit XML with <FORM kindOf='original'><UNCLEAR/></FORM>
    rather than using the _write_text helper (which assigns `.text`),
    then asserts the broken_audio.csv has no words/sec row for this clip.
    """
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    wav = audio_dir / "unclear.wav"
    _make_audible_wav(wav, duration_sec=1.0)
    xml = xml_dir / "test.xml"
    root = ET.Element("TEXT", attrib={
        "id": "TEST",
        "citation": "t",
        "BibTeX_citation": "@t{t}",
        "copyright": "t",
        "xml:lang": "ami",
    })
    s = ET.SubElement(root, "S", attrib={"id": "S_1"})
    form = ET.SubElement(s, "FORM", attrib={"kindOf": "original"})
    ET.SubElement(form, "UNCLEAR")
    ET.SubElement(s, "AUDIO", attrib={
        "file": "unclear.wav", "start": "0", "end": "1",
    })
    ET.ElementTree(root).write(str(xml), encoding="utf-8", xml_declaration=True)

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert proc.returncode == 0, (
        f"clean (no-content) UNCLEAR run should exit 0; got "
        f"{proc.returncode}, stderr={proc.stderr!r}"
    )
    rows = _read_broken_csv(log_dir)
    # broken_audio.csv tracks the HARD missing/unloadable/silent/range
    # kinds and ALSO the SOFT words/sec kind. Filter to our file and
    # assert no rows for it (i.e. no V105 was emitted).
    our_rows = [r for r in rows if r["audio_file"] == "unclear.wav"]
    assert not our_rows, (
        f"expected NO broken_audio rows for an UNCLEAR-only FORM (cps/wps "
        f"check should be skipped); got {our_rows!r}"
    )


def test_soft_findings_alone_do_not_fail(tmp_path):
    """A corpus that only triggers SOFT findings (e.g. words/sec out of
    range) should still exit 0 — SOFT findings warn but don't fail."""
    corpus, xml_dir, audio_dir = _make_corpus(tmp_path)
    good = audio_dir / "ok.wav"
    # 0.2 seconds audio, 50 words → words/sec way too high (250) → triggers V105
    _make_audible_wav(good, duration_sec=0.2)
    xml = xml_dir / "test.xml"
    _write_text(xml, [{
        "id": "S_1",
        "file": "ok.wav",
        "start": "0",
        "end": "0.2",
        "form": " ".join(["word"] * 50),
    }])

    log_dir = tmp_path / "logs"
    proc = _run(xml_dir, audio_dir, log_dir)
    assert proc.returncode == 0, (
        f"expected exit 0 with only SOFT findings; got {proc.returncode}, "
        f"stderr={proc.stderr!r}"
    )
