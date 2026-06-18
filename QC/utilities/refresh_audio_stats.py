# QC/utilities/refresh_audio_stats.py
"""On-demand: pull a single corpus's audio from Hugging Face, recompute its
audio durations into statistics/audio_durations.csv, refresh its per-corpus
CSV, then delete the downloaded audio.

    python QC/utilities/refresh_audio_stats.py NTU_Paiwan_ASR
    python QC/utilities/refresh_audio_stats.py WilangYutasVideos --keep-audio

NEVER run in CI or a merge. This is the only Python-level path that recomputes
audio durations on demand (see run_audio_downloads.sh for bulk audio downloads).
Requires git, git-lfs, jq and the `hf` CLI (same as download_audio_data.sh).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import update_audio_stats


def _default_download(corpus_dir: Path) -> None:
    script = corpus_dir / "download_audio_data.sh"
    if not script.is_file():
        raise FileNotFoundError(f"{script} not found; cannot pull HF audio.")
    subprocess.run(["bash", str(script)], cwd=corpus_dir, check=True)


def _default_regen_stats(corpus_dir: Path) -> None:
    script = Path(__file__).resolve().parent / "get_corpus_stats.py"
    # get_corpus_stats takes the corpus dir as a positional arg.
    subprocess.run([sys.executable, str(script), str(corpus_dir)], check=True)


def _delete_audio(corpus_dir: Path) -> None:
    for audio_dir in (corpus_dir / "Audio", corpus_dir / "audio"):
        if audio_dir.is_dir():
            shutil.rmtree(audio_dir)


def refresh_corpus(corpus_dir: Path, keep_audio: bool = False,
                   download=_default_download, regen_stats=_default_regen_stats,
                   computed_at: str | None = None) -> int:
    corpus_dir = Path(corpus_dir)
    # Download is outside the try/finally: if it fails partway, any partial
    # Audio/ is left on disk for the operator to inspect (not auto-deleted).
    download(corpus_dir)
    try:
        rc = update_audio_stats.update_corpus(corpus_dir, computed_at=computed_at)
        regen_stats(corpus_dir)
    finally:
        if not keep_audio:
            _delete_audio(corpus_dir)
    return rc


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", help="Corpus name, e.g. NTU_Paiwan_ASR.")
    parser.add_argument("--keep-audio", action="store_true",
                        help="Do not delete the downloaded audio afterwards.")
    parser.add_argument("--corpora-root", default=str(repo_root / "Corpora"))
    args = parser.parse_args()
    corpus_dir = Path(args.corpora_root) / args.corpus
    if not corpus_dir.is_dir():
        print(f"[refresh_audio_stats] ERROR: {corpus_dir} not found.", file=sys.stderr)
        return 1
    return refresh_corpus(corpus_dir, keep_audio=args.keep_audio)


if __name__ == "__main__":
    raise SystemExit(main())
