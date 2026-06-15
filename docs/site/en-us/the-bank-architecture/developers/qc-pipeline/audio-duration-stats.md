---
icon: chart-line
---

# Audio duration stats

> The tooling that maintains `statistics/audio_durations.csv` — the source of truth for per-corpus audio seconds — by computing durations from local audio, and the on-demand path that pulls a corpus's audio from Hugging Face just to refresh it.

## What it's for

CI cannot measure audio: the `.wav`/`.mp3` files are gitignored and absent on runners. So audio *seconds* are precomputed and stored in `statistics/audio_durations.csv`, keyed by `(corpus, language, dialect)`, alongside the audio-element counts they were measured against (`count_at_compute`) and a date. This CSV is the **audio-seconds source of truth**: [`get_corpus_stats.py`](get-corpus-stats.md) (and thus the GitBook and the growth graphs) only *reads* it.

This page covers the three pieces that maintain it: the library that reads/writes the CSV, the script that recomputes seconds from already-local audio, and the on-demand script that fetches one corpus's audio from Hugging Face, recomputes, and deletes it again.

## When to run it

Refreshing audio durations is **always manual / on-demand — never part of CI or a normal merge.** Run it for a new corpus with audio, or after a corpus's audio changes, or when `get_corpus_stats.py --report-stale-audio` (or a `STALE AUDIO` warning) flags a bucket. Use `update_audio_stats.py` when the audio is already on disk; use `refresh_audio_stats.py` when it is not (it pulls from Hugging Face for you). Run from the repo root after `source .venv/bin/activate`.

## audio_durations.py — the source-of-truth library

**Library, not a CLI.** `QC/utilities/audio_durations.py` reads and writes `statistics/audio_durations.csv`. Columns: `corpus, language, dialect, transcribed_audio_seconds, untranscribed_audio_seconds, transcribed_audio_count, untranscribed_audio_count, computed_at`.

Key calls: `load_for_corpus` returns one corpus's rows keyed by `(language, dialect)`; `upsert_audio_durations` replaces all rows for a corpus while preserving other corpora's rows; `is_stale` decides whether a bucket's seconds are stale versus the current XML audio-counts. A bucket is **stale** when there is no entry but the corpus now has audio, when either count differs from `count_at_compute` (a blank/`None` anchor always differs), or when the corpus has audio but the recorded seconds are still 0 (never computed). Because nothing auto-regenerates this file, CI cannot clobber it.

## update_audio_stats.py — recompute from local audio

**How:** for each corpus it walks the XML, locates each `AUDIO` element's file on disk (trying mirrored layouts and the `.wav`/`.mp3` counterpart), measures durations (`wave` for WAV, `mutagen` for MP3), sums them per `(language, dialect)` split into transcribed/untranscribed, and upserts those seconds plus the current audio-counts into `audio_durations.csv`. Crucially, a bucket whose audio is **not** found on disk **keeps its previous seconds** (and anchor) rather than being zeroed — so running this without audio downloaded can never wipe good data. MP3s are skipped with a warning if `mutagen` is not installed.

**Usage:**

```bash
python QC/utilities/update_audio_stats.py Corpora/ePark
python QC/utilities/update_audio_stats.py --all
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `corpora_path` (positional) | — | One corpus directory. Mutually exclusive with `--all`. |
| `--all` | off | Every corpus with an `XML/` dir under `--corpora_root`. |
| `--corpora_root` | repo `Corpora/` | Collection root for `--all`. |

**Output:** updates `statistics/audio_durations.csv`. To force a bucket to 0, edit the CSV by hand.

## refresh_audio_stats.py — pull from Hugging Face, recompute, delete

**How:** the only on-demand path that recomputes durations when audio is *not* local. For one named corpus it runs the corpus's `download_audio_data.sh` to pull audio from Hugging Face, calls `update_audio_stats.update_corpus`, regenerates that corpus's per-corpus stats CSV via [`get_corpus_stats.py`](get-corpus-stats.md), and then deletes the downloaded `Audio/` directory (unless `--keep-audio`). A failed download leaves any partial `Audio/` on disk for inspection; otherwise audio is always cleaned up. Requires `git`, `git-lfs`, `jq`, and the `hf` CLI.

**Usage:**

```bash
python QC/utilities/refresh_audio_stats.py NTU_Paiwan_ASR
python QC/utilities/refresh_audio_stats.py WilangYutasVideos --keep-audio
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `corpus` (positional) | — | Corpus name, e.g. `NTU_Paiwan_ASR`. |
| `--keep-audio` | off | Do not delete the pulled audio afterwards. |
| `--corpora-root` | repo `Corpora/` | Where the corpus directory lives. |

**Output:** updates `statistics/audio_durations.csv` and the corpus's `*_corpora_stats.csv`. (The `refresh-audio-stats` skill wraps this workflow.) **Never run in CI or a merge.**

## Output & side effects

`audio_durations.csv` is written only by `update_audio_stats.py` / `refresh_audio_stats.py` (and the historical one-off migrations below). **CI never writes it** — `get_corpus_stats.py` and `corpus_metrics.py` only read it. `refresh_audio_stats.py` additionally rewrites one per-corpus stats CSV and downloads/deletes audio.

## Historical one-off migrations

Two scripts seeded `audio_durations.csv` once and are not part of any routine workflow: `QC/utilities/migrate_audio_durations.py` (seeded the CSV from the committed per-corpus CSVs, anchoring `count_at_compute` to a reference commit) and `QC/utilities/port_audio_seconds_from_gitbook.py` (a no-download alternative that ported seconds from the GitBook repo's per-corpus stats CSVs). They are retained for provenance; you should not need to run them.

## When to run it

See **When to run it** above — always manual, triggered by a new/changed corpus or a stale-audio flag from [`get_corpus_stats.py --report-stale-audio`](get-corpus-stats.md). It sits beside the stats step of [Porting a Corpus In](../porting-a-corpus.md).

## Related

- [QC Pipeline overview](README.md)
- [get_corpus_stats.py](get-corpus-stats.md) — reads these seconds and flags staleness
- [corpus_metrics.py](corpus-metrics.md) — plots transcribed-audio-over-time from the history CSV
- [Porting a Corpus In](../porting-a-corpus.md)
