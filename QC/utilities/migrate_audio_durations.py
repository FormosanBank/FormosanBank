# QC/utilities/migrate_audio_durations.py
"""One-time migration: seed statistics/audio_durations.csv from the committed
per-corpus CSVs.

Seconds come from the CURRENT per-corpus CSV (the values we trust). The
count_at_compute anchor comes from a reference commit (the "unified counting
rules" seeding, d1bd8f4d8) via `git show`, matched by (language, dialect):
- unchanged corpora: reference count == current count -> get_corpus_stats
  reads them NOT stale (no download needed).
- changed corpora (e.g. NTU_Paiwan_ASR, WilangYutasVideos): reference count
  < current count -> read STALE -> refresh_audio_stats recomputes them.

Run once, then commit statistics/audio_durations.csv.
"""
from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_durations

REFERENCE_COMMIT = "d1bd8f4d8"


def _parse_per_corpus(text: str) -> list[dict]:
    return list(csv.DictReader(io.StringIO(text)))


def reference_counts_factory(repo_root: Path, reference_commit: str):
    """Return f(corpus) -> {(language, dialect): (t_count, u_count)} at the ref commit."""
    def get(corpus: str) -> dict:
        rel = f"statistics/{corpus}_corpora_stats.csv"
        try:
            out = subprocess.run(
                ["git", "show", f"{reference_commit}:{rel}"],
                cwd=repo_root, capture_output=True, text=True, check=True).stdout
        except subprocess.CalledProcessError:
            return {}  # corpus did not exist at the reference commit
        result = {}
        for row in _parse_per_corpus(out):
            key = (row.get("language", ""), row.get("dialect", ""))
            result[key] = (int(float(row.get("transcribed_audio_count") or 0)),
                           int(float(row.get("untranscribed_audio_count") or 0)))
        return result
    return get


def build_rows_for_corpus(corpus: str, current_csv_text: str, ref_counts) -> list[dict]:
    """Build audio_durations rows for one corpus. `ref_counts(corpus)` -> dict."""
    ref = ref_counts(corpus)
    rows = []
    for row in _parse_per_corpus(current_csv_text):
        key = (row.get("language", ""), row.get("dialect", ""))
        t_count = int(float(row.get("transcribed_audio_count") or 0))
        u_count = int(float(row.get("untranscribed_audio_count") or 0))
        t_sec = float(row.get("transcribed_audio_seconds") or 0)
        u_sec = float(row.get("untranscribed_audio_seconds") or 0)
        if (t_count + u_count) == 0:
            continue  # no audio in this bucket
        ref_t, ref_u = ref.get(key, (t_count, u_count))  # fallback: current (unchanged)
        rows.append({"language": key[0], "dialect": key[1],
                     "transcribed_audio_seconds": t_sec,
                     "untranscribed_audio_seconds": u_sec,
                     "transcribed_audio_count": ref_t,
                     "untranscribed_audio_count": ref_u})
    return rows


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-commit", default=REFERENCE_COMMIT)
    parser.add_argument("--stats-dir", default=str(repo_root / "statistics"))
    args = parser.parse_args()
    stats_dir = Path(args.stats_dir)
    ref_counts = reference_counts_factory(repo_root, args.reference_commit)
    stamp = date.today().isoformat()

    n = 0
    for csv_path in sorted(stats_dir.glob("*_corpora_stats.csv")):
        corpus = csv_path.name[: -len("_corpora_stats.csv")]
        rows = build_rows_for_corpus(corpus, csv_path.read_text(encoding="utf-8"), ref_counts)
        if rows:
            audio_durations.upsert_audio_durations(stats_dir, corpus, rows, stamp)
            n += len(rows)
            print(f"  {corpus}: {len(rows)} bucket(s)")
    print(f"Migrated {n} bucket(s) into {audio_durations.audio_durations_path(stats_dir)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
