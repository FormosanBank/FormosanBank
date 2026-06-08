"""
download_audio.py

For every XML file in Final_XML/, reads the audio URL and id from the <TEXT>
element, downloads the audio track, and converts it to WAV using ffmpeg.

Output files are placed in Audio/ and named after the TEXT id attribute
(e.g. "20180728_Yutas_Wilang_MVI_1079_...xml" → "20180728_....wav").

Requires ffmpeg to be installed and on PATH.
"""

import os
import subprocess
from pathlib import Path
from lxml import etree
import yt_dlp

# Resolve paths relative to this script's location
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
XML_DIR = SCRIPT_DIR.parent / "../XML/Atayal"
AUDIO_DIR = SCRIPT_DIR.parent / "../Audio/Atayal"


def parse_xml_metadata(xml_path):
    """Return (text_id, youtube_url, has_transcript) from a FormosanBank XML file, or None on error."""
    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
        text_id = root.get("id")
        youtube_url = root.get("audio")
        if not text_id or not youtube_url:
            return None
        has_transcript = root.find("S") is not None
        return text_id, youtube_url, has_transcript
    except Exception as e:
        print(f"  [WARN] Could not parse {xml_path.name}: {e}")
        return None


def add_audio_element_to_stub(xml_path, wav_filename):
    """Add <AUDIO file="..."/> as a child of <TEXT> for stub XMLs (no <S> elements)."""
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    # Idempotent: remove any existing top-level AUDIO element first
    for existing in root.findall("AUDIO"):
        root.remove(existing)

    audio_el = etree.SubElement(root, "AUDIO")
    audio_el.set("file", wav_filename)
    tree.write(str(xml_path), encoding="utf-8", pretty_print=True, xml_declaration=True)
    print(f"  [XML]  Added <AUDIO file=\"{wav_filename}\"/> to {xml_path.name}")


def download_as_wav(youtube_url, output_stem, audio_dir):
    """Download best audio for youtube_url and convert to WAV via ffmpeg."""
    # yt-dlp writes a temp file then ffmpeg converts; final file is <stem>.wav
    outtmpl = str(audio_dir / f"{output_stem}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": False,
        "no_warnings": False,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])


def segment_wav(src_wav, start, stop, out_path):
    """Extract a slice of src_wav from start to stop (seconds) into out_path.

    If stop is None, extracts from start to end of file.
    Uses ffmpeg stream-copy for speed (no re-encoding).
    """
    cmd = ["ffmpeg", "-y", "-i", str(src_wav), "-ss", str(start)]
    if stop is not None:
        cmd += ["-to", str(stop)]
    cmd += ["-c", "copy", str(out_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_wav_duration(wav_path):
    """Return total duration in seconds of wav_path using ffprobe."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(wav_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def create_untranscribed_xml(original_xml_path, text_id, segments):
    """Write (or overwrite) a <text_id>_untranscribed.xml file.

    Copies the <TEXT> attributes from the original XML, updates 'id', and adds
    one <AUDIO file="..."/> child per untranscribed segment.

    Updated 2026-06-03: start/stop attributes are no longer written.
    Each segment WAV (cut by segment_wav above) IS the untranscribed
    region in full; writing source-video offsets here was misleading
    because a reader would expect them to be offsets within @file and
    they weren't. The `segments` tuple shape (start, stop, filename) is
    retained because handle_untranscribed_segments still logs the
    source-video offsets to stdout for debugging.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    orig_root = etree.parse(str(original_xml_path), parser).getroot()

    new_root = etree.Element("TEXT")
    for k, v in orig_root.attrib.items():
        new_root.set(k, v)
    new_root.set("id", f"{text_id}_untranscribed")

    for _start, _stop, wav_filename in segments:
        audio_el = etree.SubElement(new_root, "AUDIO")
        audio_el.set("file", wav_filename)

    out_path = original_xml_path.parent / f"{text_id}_untranscribed.xml"
    etree.ElementTree(new_root).write(
        str(out_path), encoding="utf-8", pretty_print=True, xml_declaration=True
    )
    print(f"  [XML]  Wrote {out_path.name} ({len(segments)} untranscribed segment(s))")


def handle_untranscribed_segments(xml_path, text_id, src_wav):
    """Detect every untranscribed audio gap and create WAV segments + XML.

    Computes the complement of the transcribed <S> time ranges over
    [0, total_duration]: every leading, interior, and trailing region of
    src_wav that no <S> covers. Each gap of duration >= MIN_GAP is
    segmented into its own WAV file and referenced in a companion
    <text_id>_untranscribed.xml placed alongside the original XML.

    Updated 2026-06-03: previously only the leading gap (before the first
    S) and trailing gap (after the last S) were extracted; interior gaps
    between two transcribed S's were silently dropped, leaving that
    audio referenced by no XML anywhere. The fix unifies the three cases
    under a single complement-of-coverage computation.

    Updated 2026-06-08: positional naming (_1.wav, _2.wav, ...) plus the
    prior skip-if-exists guard meant that a re-run could leave an old
    WAV at a filename now bound to a different gap, silently
    desynchronizing the XML from its referenced audio. To make re-runs
    deterministic, this function now DELETES all existing
    <text_id>_untranscribed*.wav files in AUDIO_DIR and the companion
    <text_id>_untranscribed.xml alongside the original XML before
    regenerating. Scope is narrow (only this text_id's outputs); other
    videos' outputs are untouched. Each deletion is printed.
    """
    MIN_GAP = 1.0  # seconds — gaps shorter than this are ignored

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(xml_path), parser).getroot()

    # Wipe this video's prior untranscribed outputs up front so the
    # rebuild is deterministic. Scoped strictly to filenames matching
    # `<text_id>_untranscribed*` so we never touch other videos' files
    # or the master `<text_id>.wav`.
    prior_wavs = sorted(AUDIO_DIR.glob(f"{text_id}_untranscribed*.wav"))
    prior_xml = xml_path.parent / f"{text_id}_untranscribed.xml"
    for p in prior_wavs:
        p.unlink()
        print(f"  [DEL]  {p.name}  (stale untranscribed WAV from prior run)")
    if prior_xml.exists():
        prior_xml.unlink()
        print(f"  [DEL]  {prior_xml.name}  (stale untranscribed XML from prior run)")

    total_duration = get_wav_duration(src_wav)

    # Collect (start, stop) for every transcribed <S>. A missing stop on
    # the final S means it runs to the end of the source WAV — see
    # make_xml.py:215-222 (only the last entry omits the end time).
    #
    # Attribute-name note (2026-06-08): the CodeAndDocs pipeline (make_xml.py
    # and the older create_untranscribed_xml) emits @stop, but the
    # published XMLs in Corpora/WilangYutasVideos/XML/ use @end. We accept
    # either, preferring @end since that's the canonical form on disk;
    # falling back to @stop keeps this code working against freshly-built
    # pipeline output. Without this dual lookup, reading the published
    # XMLs gave stop=None on every S → all S's looked like they ran to
    # total_duration → no gaps were ever found → existing
    # _untranscribed.xml files were deleted with nothing put in their
    # place.
    covered = []
    for s in root.findall("S"):
        audio_el = s.find("AUDIO")
        if audio_el is None:
            continue
        start_str = audio_el.get("start")
        stop_str  = audio_el.get("end") or audio_el.get("stop")
        if start_str is None:
            continue
        start = float(start_str)
        stop = float(stop_str) if stop_str is not None else total_duration
        covered.append((start, stop))

    if not covered:
        return

    # Merge overlapping/touching transcribed ranges so the complement
    # below can't produce negative-duration "gaps" between them. The
    # subtitle timestamps occasionally overlap by a few hundred ms.
    covered.sort()
    merged = [covered[0]]
    for s_start, s_stop in covered[1:]:
        prev_start, prev_stop = merged[-1]
        if s_start <= prev_stop:
            merged[-1] = (prev_start, max(prev_stop, s_stop))
        else:
            merged.append((s_start, s_stop))

    # Complement of `merged` over [0, total_duration], filtered by MIN_GAP.
    gaps = []
    cursor = 0.0
    for cov_start, cov_stop in merged:
        if cov_start - cursor >= MIN_GAP:
            gaps.append((cursor, cov_start))
        cursor = cov_stop
    if total_duration - cursor >= MIN_GAP:
        gaps.append((cursor, total_duration))

    if not gaps:
        return

    # Single gap → <text_id>_untranscribed.wav (preserved for back-compat
    # with the prior leading/trailing-only output); multiple gaps →
    # _untranscribed_1.wav, _untranscribed_2.wav, ...
    if len(gaps) == 1:
        planned_names = [f"{text_id}_untranscribed.wav"]
    else:
        planned_names = [
            f"{text_id}_untranscribed_{i + 1}.wav" for i in range(len(gaps))
        ]

    segments = []
    for (gap_start, gap_stop), wav_filename in zip(gaps, planned_names):
        out_path = AUDIO_DIR / wav_filename
        segment_wav(src_wav, gap_start, gap_stop, out_path)
        print(f"  [WAV]  {wav_filename}  ({gap_start:.2f}s – {gap_stop:.2f}s)")
        segments.append((gap_start, gap_stop, wav_filename))

    create_untranscribed_xml(xml_path, text_id, segments)


def segment_transcribed_xml(xml_path, text_id, src_wav):
    """Segment src_wav according to AUDIO timestamps in each <S> element.

    Segments are written to Audio/<text_id>_<s_id>.wav (all in the root Audio
    folder; the text_id prefix avoids collisions across XMLs).
    The 'file' attribute is added to each <AUDIO> element pointing to that file.
    The XML is updated in place.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(xml_path), parser)
    root = tree.getroot()

    sentences = root.findall("S")
    changed = False

    for s in sentences:
        s_id = s.get("id", "unknown")
        audio_el = s.find("AUDIO")
        if audio_el is None:
            continue

        start = audio_el.get("start")
        stop = audio_el.get("stop")  # may be None for final sentence
        if start is None:
            continue

        out_filename = f"{text_id}_{s_id}.wav"
        out_path = AUDIO_DIR / out_filename

        if not out_path.exists():
            segment_wav(src_wav, start, stop, out_path)

        if audio_el.get("file") != out_filename:
            audio_el.set("file", out_filename)
            changed = True

    if changed:
        tree.write(str(xml_path), encoding="utf-8", pretty_print=True, xml_declaration=True)
        print(f"  [XML]  Updated {len(sentences)} AUDIO elements in {xml_path.name}")


def main():
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(XML_DIR.glob("*.xml"))
    # Exclude companion untranscribed files — those are generated by this script
    xml_files = [p for p in xml_files if not p.stem.endswith("_untranscribed")]
    if not xml_files:
        print(f"No XML files found in {XML_DIR}")
        return

    print(f"Found {len(xml_files)} XML files. Downloading audio to {AUDIO_DIR}/\n")

    downloaded = 0
    errors = 0

    for xml_path in xml_files:
        result = parse_xml_metadata(xml_path)
        if result is None:
            print(f"[SKIP] {xml_path.name} — could not extract id/audio URL")
            continue

        text_id, youtube_url, has_transcript = result
        wav_filename = f"{text_id}.wav"
        wav_path = AUDIO_DIR / wav_filename

        if wav_path.exists():
            print(f"[SKIP] {wav_filename}  (already exists)")
        else:
            print(f"[DOWN] {text_id}")
            print(f"       {youtube_url}")
            try:
                download_as_wav(youtube_url, text_id, AUDIO_DIR)
                downloaded += 1
            except Exception as e:
                print(f"  [ERROR] {e}")
                errors += 1
                continue

        if wav_path.exists():
            if has_transcript:
                segment_transcribed_xml(xml_path, text_id, wav_path)
                handle_untranscribed_segments(xml_path, text_id, wav_path)
            else:
                add_audio_element_to_stub(xml_path, wav_filename)

    print(f"\nDone. Downloaded: {downloaded}  Errors: {errors}")



if __name__ == "__main__":
    main()
