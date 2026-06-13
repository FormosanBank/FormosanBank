# QC/utilities/port_audio_seconds_from_gitbook.py
"""Port transcribed/untranscribed audio SECONDS from the FormosanBank Gitbook
repo's per-corpus stats CSVs into statistics/audio_durations.csv.

The Gitbook (../FormosanBankGitbook) carries audio durations that were
computed when the audio was available; CI here cannot compute them. This is a
cheap, no-download alternative to refresh_audio_stats.py for corpora whose
durations already exist in the Gitbook.

    python QC/utilities/port_audio_seconds_from_gitbook.py ePark

count_at_compute is set to the GITBOOK's audio counts (the counts those
seconds were measured against), so get_corpus_stats reads a bucket as
not-stale only when our current XML audio-count still matches the Gitbook's;
drift since the Gitbook snapshot is correctly flagged stale.

Single-dialect languages: the Gitbook predates fix_dialects.py and leaves
their dialect blank, while our data labels it with the language name. When an
(our) (language, dialect) key has no direct Gitbook match, we fall back to
matching by language IF both sides have exactly one row for that language (the
single-dialect case) — unambiguous. Multi-dialect dialects only ever match
directly; any of our dialects the Gitbook lacks is left unmatched (it stays
flagged stale for a real refresh).
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import audio_durations
from get_corpus_stats import stats_paths


def load_per_corpus_seconds(csv_path: Path) -> dict:
    """Read a per-corpus stats CSV -> {(language, dialect): {t_count,u_count,t_sec,u_sec}}."""
    out: dict = {}
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row.get("language", "").strip().lower(), row.get("dialect", "").strip())
            out[key] = {
                "t_count": int(float(row.get("transcribed_audio_count") or 0)),
                "u_count": int(float(row.get("untranscribed_audio_count") or 0)),
                "t_sec": float(row.get("transcribed_audio_seconds") or 0),
                "u_sec": float(row.get("untranscribed_audio_seconds") or 0),
            }
    return out


def build_port_rows(gitbook: dict, our_keys) -> tuple[list, list]:
    """Build audio_durations rows porting Gitbook seconds onto OUR keys.

    Returns (rows, unmatched_our_keys). Each row carries the Gitbook seconds
    and the Gitbook counts as count_at_compute, written under OUR dialect label.
    """
    gb_by_lang: dict[str, list] = defaultdict(list)
    for (lang, dialect), v in gitbook.items():
        gb_by_lang[lang].append((dialect, v))
    our_by_lang: dict[str, list] = defaultdict(list)
    for (lang, dialect) in our_keys:
        our_by_lang[lang].append(dialect)

    rows, unmatched = [], []
    for (lang, dialect) in sorted(our_keys):
        if (lang, dialect) in gitbook:
            v = gitbook[(lang, dialect)]
        elif len(gb_by_lang.get(lang, [])) == 1 and len(our_by_lang[lang]) == 1:
            # single-dialect language: Gitbook left the dialect blank, we use
            # the language name. Exactly one row per side -> unambiguous.
            v = gb_by_lang[lang][0][1]
        else:
            unmatched.append((lang, dialect))
            continue
        rows.append({
            "language": lang, "dialect": dialect,
            "transcribed_audio_seconds": v["t_sec"],
            "untranscribed_audio_seconds": v["u_sec"],
            "transcribed_audio_count": v["t_count"],
            "untranscribed_audio_count": v["u_count"],
        })
    return rows, unmatched


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", help="Corpus name, e.g. ePark.")
    parser.add_argument("--gitbook", default=str(repo_root.parent / "FormosanBankGitbook"),
                        help="Path to the FormosanBankGitbook repo (default: sibling).")
    parser.add_argument("--stats-dir", default=str(repo_root / "statistics"))
    args = parser.parse_args()

    stats_dir = Path(args.stats_dir)
    gb_csv = Path(args.gitbook) / "statistics" / f"{args.corpus}_corpora_stats.csv"
    our_csv = stats_dir / f"{args.corpus}_corpora_stats.csv"
    if not gb_csv.is_file():
        print(f"[port] ERROR: no Gitbook CSV at {gb_csv}", file=sys.stderr)
        return 1
    if not our_csv.is_file():
        print(f"[port] ERROR: no local CSV at {our_csv}", file=sys.stderr)
        return 1

    gitbook = load_per_corpus_seconds(gb_csv)
    our_keys = set(load_per_corpus_seconds(our_csv))
    rows, unmatched = build_port_rows(gitbook, our_keys)

    audio_durations.upsert_audio_durations(stats_dir, args.corpus, rows, date.today().isoformat())
    t_sec = sum(r["transcribed_audio_seconds"] for r in rows)
    u_sec = sum(r["untranscribed_audio_seconds"] for r in rows)
    print(f"Ported {len(rows)} bucket(s) for {args.corpus}: "
          f"{t_sec:.0f}s transcribed, {u_sec:.0f}s untranscribed "
          f"into {audio_durations.audio_durations_path(stats_dir)}")
    if unmatched:
        print(f"  {len(unmatched)} bucket(s) had no Gitbook match (left for a real "
              f"refresh): {sorted(unmatched)}")
    print("Now regenerate the per-corpus CSV: "
          f"python QC/utilities/get_corpus_stats.py Corpora/{args.corpus}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
