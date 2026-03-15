"""
extract_audio_clips.py

For every XML file under Final_XML, reads the audio filename from the <TEXT>
audio attribute, locates the corresponding WAV in Final_Audio (mirroring the
subdirectory structure), then for each <S> element extracts the audio segment
defined by its <AUDIO start="..." end="..."/> child and saves it as
  {XML-basename}_{S-id}.wav
in the same folder as the source WAV.

The saved filename is also written back to the XML as a `file` attribute on
the <AUDIO> element, and the XML is updated in place.

If --audio_root is not supplied the script checks for an `Audio` folder then
a `Final_Audio` folder (relative to the current working directory) and uses
whichever is found first.

Usage
-----
    python extract_audio_clips.py [--xml_root Final_XML] [--audio_root <path>]
"""

import argparse
import sys
import wave
from pathlib import Path

from lxml import etree


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def extract_wav_segment(src_path: Path, dst_path: Path,
                         start_sec: float, end_sec: float) -> None:
    """Extract [start_sec, end_sec) from *src_path* and write to *dst_path*."""
    with wave.open(str(src_path), "rb") as src:
        frame_rate = src.getframerate()
        n_channels = src.getnchannels()
        samp_width = src.getsampwidth()
        n_frames    = src.getnframes()

        start_frame = min(int(start_sec * frame_rate), n_frames)
        end_frame   = min(int(end_sec   * frame_rate), n_frames)

        if end_frame <= start_frame:
            raise ValueError(
                f"Empty segment: start={start_sec}s end={end_sec}s "
                f"in {src_path.name}"
            )

        src.setpos(start_frame)
        frames = src.readframes(end_frame - start_frame)

    with wave.open(str(dst_path), "wb") as dst:
        dst.setnchannels(n_channels)
        dst.setsampwidth(samp_width)
        dst.setframerate(frame_rate)
        dst.writeframes(frames)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

def resolve_audio_dir(xml_file: Path, xml_root: Path,
                       audio_root: Path) -> Path:
    """
    Map an XML file's directory to the corresponding audio directory.

    Final_XML/Paiwan/Belmira/  →  Final_Audio/Belmira/

    Strategy:
    1. Compute the XML directory relative to xml_root.
    2. Try audio_root / rel_dir.
    3. If that doesn't exist, try stripping the first path component
       (handles the extra 'Paiwan/' layer in Final_XML).
    """
    rel_dir = xml_file.parent.relative_to(xml_root)  # e.g. Paiwan/Belmira
    candidate = audio_root / rel_dir
    if candidate.is_dir():
        return candidate

    # strip one leading component (e.g. 'Paiwan')
    parts = rel_dir.parts
    if len(parts) > 1:
        candidate2 = audio_root / Path(*parts[1:])
        if candidate2.is_dir():
            return candidate2

    # fall back to xml_root-relative even if it doesn't exist yet
    return candidate


# ---------------------------------------------------------------------------
# Per-XML processing
# ---------------------------------------------------------------------------

def process_xml(xml_file: Path, xml_root: Path, audio_root: Path) -> None:
    tree = etree.parse(str(xml_file))
    root = tree.getroot()

    # Locate <TEXT> element (could be the root or a child)
    text_elem = root if root.tag == "TEXT" else root.find(".//TEXT")
    if text_elem is None:
        print(f"  [SKIP] No <TEXT> element in {xml_file.name}", file=sys.stderr)
        return

    audio_filename = text_elem.get("audio")
    if not audio_filename:
        print(f"  [SKIP] No audio attribute on <TEXT> in {xml_file.name}",
              file=sys.stderr)
        return

    audio_dir = resolve_audio_dir(xml_file, xml_root, audio_root)
    src_wav = audio_dir / audio_filename

    if not src_wav.is_file():
        print(f"  [WARN] WAV not found: {src_wav}", file=sys.stderr)
        return

    xml_stem = xml_file.stem          # e.g. 02SC105-1_Belmira
    modified  = False

    for s_elem in root.iter("S"):
        s_id = s_elem.get("id")
        if not s_id:
            continue

        audio_elem = s_elem.find("AUDIO")
        if audio_elem is None:
            continue

        try:
            start = float(audio_elem.get("start"))
            end   = float(audio_elem.get("end"))
        except (TypeError, ValueError):
            print(f"  [WARN] Bad start/end on <AUDIO> in <S id={s_id!r}>",
                  file=sys.stderr)
            continue

        clip_name = f"{xml_stem}_{s_id}.wav"
        clip_path = audio_dir / clip_name

        try:
            extract_wav_segment(src_wav, clip_path, start, end)
        except Exception as exc:
            print(f"  [ERROR] {clip_name}: {exc}", file=sys.stderr)
            continue

        audio_elem.set("file", clip_name)
        modified = True
        print(f"  Saved {clip_name}")

    if modified:
        tree.write(
            str(xml_file),
            xml_declaration=True,
            encoding="utf-8",
            pretty_print=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--xml_root",
        default="Final_XML",
        help="Root directory containing XML files (default: Final_XML)",
    )
    parser.add_argument(
        "--audio_root",
        default=None,
        help=(
            "Root directory containing WAV files. "
            "If omitted, the script looks for an 'Audio' folder then a "
            "'Final_Audio' folder in the current working directory."
        ),
    )
    args = parser.parse_args()

    xml_root = Path(args.xml_root).resolve()

    if args.audio_root is not None:
        audio_root = Path(args.audio_root).resolve()
    else:
        cwd = Path.cwd()
        for candidate_name in ("Audio", "Final_Audio"):
            candidate = cwd / candidate_name
            if candidate.is_dir():
                audio_root = candidate.resolve()
                print(f"Using audio root: {audio_root}")
                break
        else:
            print(
                "ERROR: Could not find an 'Audio' or 'Final_Audio' folder in "
                f"{cwd}. Pass --audio_root explicitly.",
                file=sys.stderr,
            )
            sys.exit(1)

    xml_files = sorted(xml_root.rglob("*.xml"))
    if not xml_files:
        print(f"No XML files found under {xml_root}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(xml_files)} XML file(s) under {xml_root}")
    for xml_file in xml_files:
        print(f"\nProcessing {xml_file.relative_to(xml_root)}")
        process_xml(xml_file, xml_root, audio_root)

    print("\nDone.")


if __name__ == "__main__":
    main()
