# QC/utilities/update_audio_stats.py
"""Recompute the audio-seconds columns of statistics/<Corpus>_corpora_stats.csv.

Run MANUALLY on a machine where the corpus audio is downloaded (CI never
runs this — audio is gitignored and absent on runners). get_corpus_stats.py
carries the seconds columns forward on every run; this script is the only
thing that refreshes them. Use it for new corpora and after audio updates:

    python QC/utilities/update_audio_stats.py Corpora/ePark
    python QC/utilities/update_audio_stats.py --all

If no audio file is found for a (language, dialect) bucket that previously
had nonzero seconds, the old value is KEPT and a warning is printed —
running this without audio downloaded must not wipe good data.
"""
import argparse
import csv
import sys
import wave
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import corpus_counts
from get_corpus_stats import FIELDNAMES, stats_paths

try:
    from mutagen.mp3 import MP3 as MutagenMP3
except ImportError:
    MutagenMP3 = None


def _get_audio_duration(file_path: str):
    """Return duration in seconds for an mp3 or wav file, or None on failure."""
    try:
        if file_path.endswith(".mp3"):
            if MutagenMP3 is None:
                return None
            return MutagenMP3(file_path).info.length
        if file_path.endswith(".wav"):
            with wave.open(file_path, "rb") as wf:
                return wf.getnframes() / wf.getframerate()
    except Exception:
        return None
    return None


def _resolve_audio_path(elem, xml_file: Path, corpus_root, audio_base: Path):
    """Find the audio file for one AUDIO element, trying mirrored layouts."""
    audio_filename = elem.attrib["file"]
    audio_path_obj = Path(audio_filename)
    alt_ext = ".wav" if audio_path_obj.suffix.lower() == ".mp3" else ".mp3"
    alt_filename = audio_path_obj.stem + alt_ext

    if corpus_root is not None:
        rel = xml_file.relative_to(corpus_root / "XML")
        rel_parts = rel.parent.parts
        rel_variants = [Path(*rel_parts[i:]) for i in range(len(rel_parts))] + [Path(".")]
        candidates = []
        for rel_var in rel_variants:
            for name in (audio_filename, alt_filename):
                candidates += [
                    audio_base / rel_var / name,
                    audio_base / rel_var / xml_file.stem / name,
                ]
        candidates += [audio_base / audio_filename, audio_base / alt_filename]
    else:
        candidates = [audio_base / audio_filename, audio_base / alt_filename]
    return next((c for c in candidates if c.is_file()), None)


def compute_seconds_by_bucket(xml_dir: Path) -> tuple[dict, int, int, int]:
    """Sum (transcribed, untranscribed) seconds per (language, dialect).

    Returns (buckets, n_elements, n_missing_files, n_mp3_skipped_no_mutagen)."""
    buckets = defaultdict(lambda: [0.0, 0.0])
    n_elements = 0
    n_missing = 0
    n_mp3_skipped = 0
    for xml_file in sorted(Path(xml_dir).rglob("*.xml")):
        try:
            root = ET.parse(xml_file).getroot()
        except Exception:
            continue  # parse errors are get_corpus_stats --strict's job
        key = (
            (root.get(corpus_counts.XML_LANG) or "").strip().lower(),
            (root.get("dialect") or "").strip(),
        )
        xml_file = xml_file.resolve()
        parts = xml_file.parts
        try:
            xml_idx = next(i for i in reversed(range(len(parts))) if parts[i] == "XML")
            corpus_root = Path(*parts[:xml_idx])
            audio_base = corpus_root / "Audio"
        except StopIteration:
            corpus_root, audio_base = None, xml_file.parent

        transcribed, untranscribed = corpus_counts.split_audio_elements(root)
        for slot, elems in ((0, transcribed), (1, untranscribed)):
            for elem in elems:
                n_elements += 1
                path = _resolve_audio_path(elem, xml_file, corpus_root, audio_base)
                if path is None:
                    n_missing += 1
                    continue
                if MutagenMP3 is None and str(path).endswith(".mp3"):
                    n_mp3_skipped += 1
                    continue
                duration = _get_audio_duration(str(path))
                if duration is not None:
                    buckets[key][slot] += duration
    return buckets, n_elements, n_missing, n_mp3_skipped


def update_corpus(corpus_path: Path) -> int:
    corpus_path = Path(corpus_path)
    xml_dir = corpus_path / "XML" if (corpus_path / "XML").is_dir() else corpus_path
    stats_dir, corpus_name = stats_paths(corpus_path)
    csv_path = stats_dir / f"{corpus_name}_corpora_stats.csv"
    if not csv_path.is_file():
        print(f"[update_audio_stats] ERROR: {csv_path} does not exist. "
              f"Run get_corpus_stats.py on this corpus first.", file=sys.stderr)
        return 1

    seconds, n_elements, n_missing, n_mp3_skipped = compute_seconds_by_bucket(xml_dir)
    if n_mp3_skipped:
        print(f"[update_audio_stats] WARNING: {n_mp3_skipped} .mp3 file(s) "
              f"encountered but mutagen is not installed; their durations were "
              f"skipped - pip install mutagen.", file=sys.stderr)
    if n_missing:
        print(f"[update_audio_stats] WARNING: {n_missing}/{n_elements} AUDIO "
              f"elements reference files not found on disk; buckets with no "
              f"located audio keep their previous seconds.", file=sys.stderr)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or FIELDNAMES

    n_updated = 0
    for row in rows:
        key = (row.get("language", ""), row.get("dialect", ""))
        t_sec, u_sec = seconds.get(key, (0.0, 0.0))
        # Keep old values when we found nothing (e.g. audio not downloaded
        # for this bucket) — never silently zero out good data.
        if t_sec or u_sec:
            row["transcribed_audio_seconds"] = round(t_sec, 1)
            row["untranscribed_audio_seconds"] = round(u_sec, 1)
            n_updated += 1

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated audio seconds for {n_updated} row(s) in {csv_path}")
    return 0


def main() -> int:
    default_corpora = Path(__file__).resolve().parents[2] / "Corpora"
    parser = argparse.ArgumentParser(
        description="Recompute audio-seconds columns of per-corpus stats CSVs "
                    "from local audio files (manual; not run in CI). Buckets "
                    "with no audio located on disk KEEP their previous seconds "
                    "(never zeroed) - to force a bucket to zero, edit the CSV "
                    "by hand.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("corpora_path", nargs="?",
                       help="Path to a single corpus directory (e.g. Corpora/ePark).")
    group.add_argument("--all", action="store_true",
                       help="Run on every corpus under --corpora_root.")
    parser.add_argument("--corpora_root", default=str(default_corpora))
    args = parser.parse_args()

    if args.all:
        corpora_root = Path(args.corpora_root).resolve()
        corpus_dirs = sorted(d for d in corpora_root.iterdir()
                             if d.is_dir() and (d / "XML").is_dir())
        worst = 0
        for corpus_dir in corpus_dirs:
            print(f"Processing {corpus_dir.name} …")
            worst = max(worst, update_corpus(corpus_dir))
        return worst
    return update_corpus(Path(args.corpora_path))


if __name__ == "__main__":
    raise SystemExit(main())
