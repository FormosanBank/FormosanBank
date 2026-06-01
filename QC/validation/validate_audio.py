"""validate_audio.py — always-on broken-audio + duration checks.

Walks a corpus's XML (and the audio dir referenced by it) and reports
broken audio in four classes:

  V100 missing       — file referenced by <AUDIO @file> not found
  V101 unloadable    — file present but mutagen/wave can't decode it
  V102 silent        — RMS amplitude (WAV) or ffprobe silencedetect (MP3) below threshold
  V103 invalid_range — AUDIO/@start >= AUDIO/@end

Plus two SOFT signals (warn, don't fail):

  V104 declared-vs-actual duration  — currently absorbed by V105 (not yet split)
  V105 words/sec or chars/sec out of range

Output:
  <log_dir>/broken_audio.csv         — kind ∈ {missing, unloadable, silent, invalid_range}
  <log_dir>/audio_duration_issues.csv — words/sec + chars/sec rows (SOFT)

This validator integrates with the Finding framework
(`QC/validation/_finding.py`): each broken-audio class is emitted as a
HARD Finding with the corresponding rule_id; words/sec issues are SOFT.
HARD findings cause non-zero exit; SOFT findings warn but don't fail
(mirroring `validate_xml.py`'s exit semantics).

Legacy CSVs (`non_working_audio.csv`, `missing_audio.csv`,
`silent_audio.csv`) are NOT written by this script anymore — the
single `broken_audio.csv` with a `kind` column subsumes them. See
B9.2 plan W2 / Open Question 3.
"""
import argparse
import array
import csv
import os
import subprocess
import sys
import wave
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from mutagen.mp3 import MP3
from tqdm import tqdm

# Make _finding importable whether we're run as a script or imported as a module.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.validation._finding import Finding, Severity  # noqa: E402


# -----------------------------------------------------------------------------
# Rule IDs
# -----------------------------------------------------------------------------
RULE_MISSING = "V100"
RULE_UNLOADABLE = "V101"
RULE_SILENT = "V102"
RULE_INVALID_RANGE = "V103"
RULE_WORDS_PER_SEC = "V105"

KIND_TO_RULE = {
    "missing": RULE_MISSING,
    "unloadable": RULE_UNLOADABLE,
    "silent": RULE_SILENT,
    "invalid_range": RULE_INVALID_RANGE,
}


# -----------------------------------------------------------------------------
# Lang resolution (kept for legacy callers; not used by the new pipeline).
# -----------------------------------------------------------------------------
_LANGS = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou',
          'Saisiyat', 'Yami', 'Thao', 'Kavalan', 'Truku', 'Sakizaya',
          'Seediq', 'Saaroa', 'Kanakanavu', 'Siraya']


def get_lang(path, file):
    for lang in _LANGS:
        if lang in path or (file.split('.')[0] == lang and file.split('.')[1:] == ['xml']):
            return lang


# -----------------------------------------------------------------------------
# Audio inspection helpers
# -----------------------------------------------------------------------------

def get_audio_duration(file_path):
    """Return the duration of an audio file in seconds, or None on failure."""
    try:
        if file_path.endswith('.mp3'):
            audio = MP3(file_path)
            return audio.info.length
        elif file_path.endswith('.wav'):
            with wave.open(file_path, "rb") as wav_file:
                return wav_file.getnframes() / wav_file.getframerate()
    except Exception:
        return None
    return None


def is_silent_wav(file_path, threshold=10):
    """Return True if a WAV file appears silent (RMS amplitude below threshold).

    Returns None if the file cannot be read or is not PCM.
    """
    try:
        with wave.open(file_path, "rb") as wf:
            sampwidth = wf.getsampwidth()
            nframes = wf.getnframes()
            if nframes == 0:
                return True
            raw = wf.readframes(nframes)
        typecode = {1: 'b', 2: 'h', 4: 'i'}.get(sampwidth)
        if typecode is None:
            return None
        samples = array.array(typecode, raw)
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        max_val = (1 << (sampwidth * 8 - 1)) - 1
        normalised_threshold = threshold * max_val / 32767
        return rms < normalised_threshold
    except Exception:
        return None


def is_silent_mp3(file_path, noise_db=-50, min_silence_sec=0.5):
    """Return True if an MP3 appears silent end-to-end.

    Uses ffprobe's silencedetect audio filter. We treat the file as
    silent if every reported silence segment together covers (almost)
    the entire duration. Returns None when ffprobe is unavailable or
    the probe fails (caller should escalate to "unloadable").
    """
    duration = get_audio_duration(file_path)
    if duration is None:
        return None
    try:
        # silencedetect emits lines like:
        #   [silencedetect ...] silence_start: 0
        #   [silencedetect ...] silence_end: 1.234 | silence_duration: 1.234
        proc = subprocess.run(
            [
                "ffmpeg", "-hide_banner", "-nostats", "-i", file_path,
                "-af", f"silencedetect=noise={noise_db}dB:d={min_silence_sec}",
                "-f", "null", "-",
            ],
            stderr=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    output = proc.stderr.decode("utf-8", errors="ignore")
    total_silence = 0.0
    for line in output.splitlines():
        if "silence_duration:" in line:
            try:
                total_silence += float(line.split("silence_duration:")[1].strip())
            except (ValueError, IndexError):
                pass
    if duration <= 0:
        return None
    # If ≥95% of the file is reported as silence segments, call it silent.
    return (total_silence / duration) >= 0.95


def is_silent(file_path):
    """Dispatch silence detection on extension. Returns True/False/None."""
    if file_path.lower().endswith(".wav"):
        return is_silent_wav(file_path)
    if file_path.lower().endswith(".mp3"):
        return is_silent_mp3(file_path)
    return None


# -----------------------------------------------------------------------------
# Path resolution + reference collection
# -----------------------------------------------------------------------------

def resolve_audio_path(xml_file_path, xml_root, audio_root, audio_filename):
    xml_file = Path(xml_file_path)
    xml_root = Path(xml_root)
    audio_root = Path(audio_root)
    rel_dir = xml_file.parent.relative_to(xml_root)
    candidate = audio_root / rel_dir / audio_filename
    if candidate.is_file():
        return str(candidate)
    parts = rel_dir.parts
    if len(parts) > 1:
        candidate2 = audio_root / Path(*parts[1:]) / audio_filename
        if candidate2.is_file():
            return str(candidate2)
    candidate3 = audio_root / audio_filename
    if candidate3.is_file():
        return str(candidate3)
    # Final fallback: search the audio_root recursively for the filename.
    for found in audio_root.rglob(audio_filename):
        return str(found)
    return None


def _audio_extensions_ok(audio_filename: str) -> bool:
    return audio_filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a'))


def collect_sentence_refs(xml_root):
    """Return list of (xml_path, element_id, audio_filename, form_text, start, end)."""
    refs = []
    for root, dirs, files in os.walk(xml_root):
        for file in files:
            if file.endswith('.xml'):
                xml_path = os.path.join(root, file)
                try:
                    tree = ET.parse(xml_path)
                    root_elem = tree.getroot()
                    for elem in root_elem.findall('.//S') + root_elem.findall('.//W'):
                        audio_elem = elem.find('AUDIO')
                        form_elem = elem.find("FORM[@kindOf='original']")
                        if (audio_elem is not None
                                and 'file' in audio_elem.attrib
                                and form_elem is not None):
                            audio_filename = audio_elem.attrib['file']
                            if not _audio_extensions_ok(audio_filename):
                                continue
                            form_text = form_elem.text or ''
                            start = audio_elem.attrib.get('start')
                            end = audio_elem.attrib.get('end')
                            refs.append((xml_path, elem.attrib.get('id', ''),
                                         audio_filename, form_text, start, end))
                except Exception as e:
                    print(f"Warning: Could not parse {xml_path}: {e}", file=sys.stderr)
    return refs


def collect_text_audio_refs(xml_root):
    refs = []
    for root, dirs, files in os.walk(xml_root):
        for file in files:
            if file.endswith('.xml'):
                xml_path = os.path.join(root, file)
                try:
                    tree = ET.parse(xml_path)
                    root_elem = tree.getroot()
                    if root_elem.tag == 'TEXT':
                        for audio_elem in root_elem.findall('AUDIO'):
                            if 'file' in audio_elem.attrib:
                                audio_filename = audio_elem.attrib['file']
                                if not _audio_extensions_ok(audio_filename):
                                    continue
                                start = audio_elem.attrib.get('start')
                                end = audio_elem.attrib.get('end')
                                refs.append((xml_path, audio_filename, start, end))
                except Exception as e:
                    print(f"Warning: Could not parse {xml_path}: {e}", file=sys.stderr)
    return refs


# -----------------------------------------------------------------------------
# Validation passes — produce Findings
# -----------------------------------------------------------------------------

def _try_float(s):
    if s is None:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _check_invalid_range(start, end) -> bool:
    s = _try_float(start)
    e = _try_float(end)
    if s is None or e is None:
        return False
    return s >= e


def _check_unloadable(audio_path: str) -> bool:
    """Return True if mutagen/wave cannot decode the file."""
    try:
        if audio_path.lower().endswith('.mp3'):
            audio = MP3(audio_path)
            if audio is None or audio.info is None or not audio.info.length:
                return True
            return False
        if audio_path.lower().endswith('.wav'):
            with wave.open(audio_path, "rb") as wav_file:
                if wav_file.getnframes() == 0 or wav_file.getframerate() == 0:
                    return True
            return False
    except Exception:
        return True
    return False


def validate_corpus(xml_root: Path, audio_root: Path,
                    check_silence: bool = False) -> tuple[list[Finding], list[tuple]]:
    """Walk the corpus and return (broken_findings, duration_issue_rows).

    broken_findings: list of HARD Findings for missing/unloadable/silent/invalid_range.
    duration_issue_rows: tuples (xml_path, audio_filename, wps, cps) for the
    SOFT words/sec output; ALSO emitted as SOFT Findings into the returned list.
    """
    refs = collect_sentence_refs(xml_root)
    text_refs = collect_text_audio_refs(xml_root)

    findings: list[Finding] = []
    duration_rows: list[tuple] = []

    # --- Invalid range (independent of file existence) ---
    for xml_path, sent_id, audio_filename, form_text, start, end in refs:
        if _check_invalid_range(start, end):
            findings.append(Finding(
                rule_id=RULE_INVALID_RANGE,
                severity=Severity.HARD,
                message=f"AUDIO @start={start} >= @end={end} (invalid range)",
                path=Path(xml_path),
                location=audio_filename,
            ))
    for xml_path, audio_filename, start, end in text_refs:
        if _check_invalid_range(start, end):
            findings.append(Finding(
                rule_id=RULE_INVALID_RANGE,
                severity=Severity.HARD,
                message=f"AUDIO @start={start} >= @end={end} (invalid range)",
                path=Path(xml_path),
                location=audio_filename,
            ))

    # --- Resolve files; missing ones get V100 immediately ---
    resolved_refs = []
    for xml_path, sent_id, audio_filename, form_text, start, end in refs:
        audio_path = resolve_audio_path(xml_path, xml_root, audio_root, audio_filename)
        if audio_path is None:
            findings.append(Finding(
                rule_id=RULE_MISSING,
                severity=Severity.HARD,
                message=f"audio file not found: {audio_filename}",
                path=Path(xml_path),
                location=audio_filename,
            ))
        else:
            resolved_refs.append((xml_path, sent_id, audio_filename, audio_path, form_text))

    resolved_text_refs = []
    for xml_path, audio_filename, start, end in text_refs:
        audio_path = resolve_audio_path(xml_path, xml_root, audio_root, audio_filename)
        if audio_path is None:
            findings.append(Finding(
                rule_id=RULE_MISSING,
                severity=Severity.HARD,
                message=f"audio file not found: {audio_filename}",
                path=Path(xml_path),
                location=audio_filename,
            ))
        else:
            resolved_text_refs.append((xml_path, audio_filename, audio_path))

    # --- For resolved files, check unloadable then silent (mutex per file) ---
    for xml_path, sent_id, audio_filename, audio_path, form_text in tqdm(
        resolved_refs, desc="checking sentence/word audio", disable=not sys.stderr.isatty()
    ):
        if _check_unloadable(audio_path):
            findings.append(Finding(
                rule_id=RULE_UNLOADABLE,
                severity=Severity.HARD,
                message=f"audio file unreadable: {audio_filename}",
                path=Path(xml_path),
                location=audio_filename,
            ))
            continue  # Don't try silence/duration on a broken file.
        if check_silence:
            silent = is_silent(audio_path)
            if silent is True:
                findings.append(Finding(
                    rule_id=RULE_SILENT,
                    severity=Severity.HARD,
                    message=f"audio file is silent: {audio_filename}",
                    path=Path(xml_path),
                    location=audio_filename,
                ))
                # Fall through to also run the words/sec SOFT check; silent
                # audio shouldn't suppress that signal.

        # SOFT: words/sec + chars/sec
        duration = get_audio_duration(audio_path)
        if duration is not None and duration > 0:
            word_count = len(form_text.strip().split())
            num_char = len(form_text.strip())
            char_per_sec = num_char / duration
            words_per_sec = word_count / duration
            if (words_per_sec < .1 or char_per_sec > 17) or \
               (word_count < 5 and duration > 10) or \
               (word_count > 12 and duration < 7):
                duration_rows.append((xml_path, audio_filename,
                                      round(words_per_sec, 2), round(char_per_sec, 2)))
                findings.append(Finding(
                    rule_id=RULE_WORDS_PER_SEC,
                    severity=Severity.SOFT,
                    message=(f"words/sec={words_per_sec:.2f} chars/sec={char_per_sec:.2f} "
                             f"outside expected range"),
                    path=Path(xml_path),
                    location=audio_filename,
                ))

    # --- TEXT-level: existence + unloadable + silence (no words/sec) ---
    for xml_path, audio_filename, audio_path in tqdm(
        resolved_text_refs, desc="checking TEXT-level audio", disable=not sys.stderr.isatty()
    ):
        if _check_unloadable(audio_path):
            findings.append(Finding(
                rule_id=RULE_UNLOADABLE,
                severity=Severity.HARD,
                message=f"audio file unreadable: {audio_filename}",
                path=Path(xml_path),
                location=audio_filename,
            ))
            continue
        if check_silence:
            silent = is_silent(audio_path)
            if silent is True:
                findings.append(Finding(
                    rule_id=RULE_SILENT,
                    severity=Severity.HARD,
                    message=f"audio file is silent: {audio_filename}",
                    path=Path(xml_path),
                    location=audio_filename,
                ))

    return findings, duration_rows


# -----------------------------------------------------------------------------
# Output writers
# -----------------------------------------------------------------------------

BROKEN_CSV_HEADER = ["xml_file", "audio_file", "kind", "rule_id", "message"]
DURATION_CSV_HEADER = ["xml_file", "audio_file", "words_per_sec", "chars_per_sec"]


def write_broken_csv(path: Path, findings: list[Finding]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(BROKEN_CSV_HEADER)
        kind_by_rule = {v: k for k, v in KIND_TO_RULE.items()}
        for fnd in findings:
            if fnd.severity is not Severity.HARD:
                continue
            kind = kind_by_rule.get(fnd.rule_id, "")
            writer.writerow([str(fnd.path), fnd.location or "", kind, fnd.rule_id, fnd.message])


def write_duration_csv(path: Path, rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(DURATION_CSV_HEADER)
        for row in rows:
            writer.writerow(row)


def print_summary(findings: list[Finding]) -> None:
    hard = [f for f in findings if f.severity is Severity.HARD]
    soft = [f for f in findings if f.severity is Severity.SOFT]
    print(f"Audio validation: {len(hard)} HARD finding(s), {len(soft)} SOFT finding(s).",
          file=sys.stderr)
    if hard:
        print("HARD findings:", file=sys.stderr)
        for f in hard:
            loc = f" [{f.location}]" if f.location else ""
            print(f"  [{f.rule_id}]{loc} {f.path}: {f.message}", file=sys.stderr)
    if soft:
        print("SOFT findings:", file=sys.stderr)
        for f in soft:
            loc = f" [{f.location}]" if f.location else ""
            print(f"  [{f.rule_id}]{loc} {f.path}: {f.message}", file=sys.stderr)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validate audio files associated with a corpus."
    )
    p.add_argument("--path", required=True,
                   help="root dir containing audio files (corpus's Audio/ dir)")
    p.add_argument("--xml_path", required=True,
                   help="root dir containing XML files (corpus's XML/ dir)")
    p.add_argument("--check_silence", action="store_true",
                   help="enable silence detection (WAV via RMS, MP3 via ffprobe)")
    p.add_argument("--log_dir", type=Path, default=None,
                   help="output dir for broken_audio.csv and audio_duration_issues.csv "
                        "(default: ./logs/ relative to cwd)")
    p.add_argument("--no-exit-on-hard", action="store_true",
                   help="always exit 0, even if HARD findings present "
                        "(back-compat for callers that depend on legacy behavior)")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    log_dir = args.log_dir if args.log_dir is not None else Path("logs")

    audio_root = Path(args.path)
    xml_root = Path(args.xml_path)

    findings, duration_rows = validate_corpus(
        xml_root=xml_root, audio_root=audio_root, check_silence=args.check_silence
    )

    write_broken_csv(log_dir / "broken_audio.csv", findings)
    write_duration_csv(log_dir / "audio_duration_issues.csv", duration_rows)

    print_summary(findings)
    print(f"Wrote {log_dir / 'broken_audio.csv'}", file=sys.stderr)
    print(f"Wrote {log_dir / 'audio_duration_issues.csv'}", file=sys.stderr)

    has_hard = any(f.severity is Severity.HARD for f in findings)
    if has_hard and not args.no_exit_on_hard:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
