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
XML_DIR = SCRIPT_DIR.parent / "Final_XML/Atayal"
AUDIO_DIR = SCRIPT_DIR.parent / "Audio/Atayal"


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
    one <AUDIO start="..." stop="..." file="..."/> child per untranscribed segment.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    orig_root = etree.parse(str(original_xml_path), parser).getroot()

    new_root = etree.Element("TEXT")
    for k, v in orig_root.attrib.items():
        new_root.set(k, v)
    new_root.set("id", f"{text_id}_untranscribed")

    for start, stop, wav_filename in segments:
        audio_el = etree.SubElement(new_root, "AUDIO")
        audio_el.set("start", f"{start:.3f}")
        audio_el.set("stop",  f"{stop:.3f}")
        audio_el.set("file",  wav_filename)

    out_path = original_xml_path.parent / f"{text_id}_untranscribed.xml"
    etree.ElementTree(new_root).write(
        str(out_path), encoding="utf-8", pretty_print=True, xml_declaration=True
    )
    print(f"  [XML]  Wrote {out_path.name} ({len(segments)} untranscribed segment(s))")


def handle_untranscribed_segments(xml_path, text_id, src_wav):
    """Detect untranscribed leading/trailing audio and create WAV segments + XML.

    Checks for audio before the first <S> and after the last <S>.  Any gap
    longer than MIN_GAP seconds is segmented into a WAV file and referenced in
    a companion <text_id>_untranscribed.xml placed alongside the original XML.
    """
    MIN_GAP = 1.0  # seconds — gaps shorter than this are ignored

    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.parse(str(xml_path), parser).getroot()

    # Collect start/stop times for every transcribed sentence
    covered = []
    for s in root.findall("S"):
        audio_el = s.find("AUDIO")
        if audio_el is None:
            continue
        start_str = audio_el.get("start")
        stop_str  = audio_el.get("stop")
        if start_str is None:
            continue
        stop = float(stop_str) if stop_str is not None else None
        covered.append((float(start_str), stop))

    if not covered:
        return

    covered.sort()
    total_duration = get_wav_duration(src_wav)

    gaps = []

    # Leading gap: audio before the first sentence
    first_start = covered[0][0]
    if first_start >= MIN_GAP:
        gaps.append((0.0, first_start))

    # Trailing gap: audio after the last sentence's stop time.
    # If the last sentence has no stop time it is assumed to run to the end.
    last_stop = covered[-1][1]
    if last_stop is not None and total_duration - last_stop >= MIN_GAP:
        gaps.append((last_stop, total_duration))

    if not gaps:
        return

    segments = []
    for i, (gap_start, gap_stop) in enumerate(gaps):
        if len(gaps) == 1:
            wav_filename = f"{text_id}_untranscribed.wav"
        else:
            wav_filename = f"{text_id}_untranscribed_{i + 1}.wav"

        out_path = AUDIO_DIR / wav_filename
        if not out_path.exists():
            segment_wav(src_wav, gap_start, gap_stop, out_path)
            print(f"  [WAV]  {wav_filename}  ({gap_start:.2f}s – {gap_stop:.2f}s)")
        else:
            print(f"  [SKIP] {wav_filename}  (already exists)")

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
    AUDIO_DIR.mkdir(exist_ok=True)

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
