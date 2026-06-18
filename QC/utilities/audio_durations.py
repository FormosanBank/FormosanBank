# QC/utilities/audio_durations.py
"""Source of truth for per-corpus audio durations: statistics/audio_durations.csv.

Keyed by (corpus, language, dialect). Holds the authoritative
*_audio_seconds plus the audio-element counts they were computed against
(count_at_compute) and the date. Only update_audio_stats.py /
refresh_audio_stats.py write this file; get_corpus_stats.py (CI) only reads
it. Because it is never auto-regenerated, CI cannot clobber it.
"""
from __future__ import annotations

import csv
from pathlib import Path

AUDIO_DURATIONS_FILENAME = "audio_durations.csv"
AUDIO_DURATIONS_HEADER = [
    "corpus", "language", "dialect",
    "transcribed_audio_seconds", "untranscribed_audio_seconds",
    "transcribed_audio_count", "untranscribed_audio_count",
    "computed_at",
]


def audio_durations_path(stats_dir: Path) -> Path:
    return Path(stats_dir) / AUDIO_DURATIONS_FILENAME


def _to_int(value):
    """Parse a count cell; blank -> None (unknown -> always stale)."""
    if value is None or str(value).strip() == "":
        return None
    return int(float(value))


def load_audio_durations(stats_dir: Path) -> dict:
    """Return {(corpus, language, dialect): entry}. Missing file -> {}."""
    path = audio_durations_path(stats_dir)
    out: dict = {}
    if not path.is_file():
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row.get("corpus", ""), row.get("language", ""), row.get("dialect", ""))
            out[key] = {
                "transcribed_audio_seconds": float(row.get("transcribed_audio_seconds") or 0),
                "untranscribed_audio_seconds": float(row.get("untranscribed_audio_seconds") or 0),
                "transcribed_audio_count": _to_int(row.get("transcribed_audio_count")),
                "untranscribed_audio_count": _to_int(row.get("untranscribed_audio_count")),
                "computed_at": row.get("computed_at", ""),
            }
    return out


def load_for_corpus(stats_dir: Path, corpus: str) -> dict:
    """Return {(language, dialect): entry} for one corpus."""
    return {
        (c, l, d)[1:]: entry
        for (c, l, d), entry in load_audio_durations(stats_dir).items()
        if c == corpus
    }


def is_stale(current_t_count: int, current_u_count: int, entry: dict | None) -> bool:
    """True when seconds are stale vs the current XML audio-counts.

    Stale when:
    - there is no entry but the corpus currently has audio, OR
    - either count differs from count_at_compute (a None/blank anchor always
      differs, so it is stale), OR
    - the corpus has audio but the recorded seconds are 0 — i.e. never
      computed. This catches a new (language, dialect) the migration could
      only anchor to its current count: counts match but the seconds are
      still 0, so it must be flagged for a refresh rather than read as
      current.
    """
    if entry is None:
        return (current_t_count + current_u_count) > 0
    if (entry["transcribed_audio_count"] != current_t_count
            or entry["untranscribed_audio_count"] != current_u_count):
        return True
    has_audio = (current_t_count + current_u_count) > 0
    no_seconds = (entry.get("transcribed_audio_seconds", 0)
                  + entry.get("untranscribed_audio_seconds", 0)) == 0
    return has_audio and no_seconds


def upsert_audio_durations(stats_dir: Path, corpus: str, rows: list, computed_at: str) -> Path:
    """Replace all rows for `corpus` with `rows`; keep other corpora. Sorted write."""
    existing = load_audio_durations(stats_dir)
    # Drop this corpus's existing rows, then add the new ones.
    merged = {k: v for k, v in existing.items() if k[0] != corpus}
    for r in rows:
        key = (corpus, r["language"], r["dialect"])
        merged[key] = {
            "transcribed_audio_seconds": float(r["transcribed_audio_seconds"]),
            "untranscribed_audio_seconds": float(r["untranscribed_audio_seconds"]),
            "transcribed_audio_count": r["transcribed_audio_count"],
            "untranscribed_audio_count": r["untranscribed_audio_count"],
            "computed_at": computed_at,
        }
    path = audio_durations_path(stats_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIO_DURATIONS_HEADER)
        writer.writeheader()
        for (c, l, d) in sorted(merged):
            e = merged[(c, l, d)]
            writer.writerow({
                "corpus": c, "language": l, "dialect": d,
                "transcribed_audio_seconds": round(e["transcribed_audio_seconds"], 1),
                "untranscribed_audio_seconds": round(e["untranscribed_audio_seconds"], 1),
                "transcribed_audio_count": "" if e["transcribed_audio_count"] is None
                else e["transcribed_audio_count"],
                "untranscribed_audio_count": "" if e["untranscribed_audio_count"] is None
                else e["untranscribed_audio_count"],
                "computed_at": e["computed_at"],
            })
    return path
