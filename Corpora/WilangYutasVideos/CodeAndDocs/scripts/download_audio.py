"""
download_audio.py -- source refresh for the audio (run by ../refresh_source.sh, never by the build).

Reads each published XML file in XML/Atayal/ (read-only) for its YouTube URL and caption
timings, downloads the video's audio as WAV into Audio/Atayal/<text_id>.wav, and cuts:
  * one clip per transcribed sentence: <text_id>_<S id>.wav (its AUDIO start-end);
  * one clip per untranscribed gap of 1 s or more: <text_id>_untranscribed.wav, or
    <text_id>_untranscribed_1.wav, _2.wav ... when there are several.
These clips are what is published on Hugging Face.

It never writes XML: generate_xml.sh writes every AUDIO element, and the audio-only and
*_untranscribed.xml files come from CodeAndDocs/video_manifest.tsv (POL-047: a source refresh
only fetches source). If a refresh changes the gaps, update video_manifest.tsv to the clip names
printed here and rebuild. Maintainer 2026-10-17: keep it, "with the XML-writing removed".

Requires ffmpeg/ffprobe on PATH and the yt-dlp Python package.
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
    root = etree.parse(str(xml_path), parser).getroot()  # read-only

    # Wipe this video's prior untranscribed outputs up front so the
    # rebuild is deterministic. Scoped strictly to filenames matching
    # `<text_id>_untranscribed*` so we never touch other videos' files
    # or the master `<text_id>.wav`.
    prior_wavs = sorted(AUDIO_DIR.glob(f"{text_id}_untranscribed*.wav"))
    for p in prior_wavs:
        p.unlink()
        print(f"  [DEL]  {p.name}  (stale untranscribed WAV from prior run)")

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
    # No XML is written: the *_untranscribed.xml files come from video_manifest.tsv.


def segment_transcribed_xml(xml_path, text_id, src_wav):
    """Cut one clip per <S> from src_wav: Audio/Atayal/<text_id>_<s_id>.wav (read-only on the XML).

    The published XML writes the clip end as @end; @stop is accepted for older builds.
    (The pre-2026-10-17 version read only @stop, so against published XML every clip
    ran to the end of the video.)
    """
    root = etree.parse(str(xml_path)).getroot()
    for s in root.findall("S"):
        s_id = s.get("id", "unknown")
        audio_el = s.find("AUDIO")
        if audio_el is None or audio_el.get("start") is None:
            continue
        stop = audio_el.get("end") or audio_el.get("stop")  # None only for a final caption
        out_path = AUDIO_DIR / f"{text_id}_{s_id}.wav"
        if not out_path.exists():
            segment_wav(src_wav, audio_el.get("start"), stop, out_path)
            print(f"  [WAV]  {out_path.name}")

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
            # an audio-only video's clip is the whole <text_id>.wav; nothing to cut

    print(f"\nDone. Downloaded: {downloaded}  Errors: {errors}")



if __name__ == "__main__":
    main()
