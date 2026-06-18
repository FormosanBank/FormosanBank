# Audio-stats persistence: a dedicated source of truth + on-demand HF refresh

**Date:** 2026-06-12
**Status:** Approved (design)
**Topic:** Make corpus audio-duration stats persist robustly across CI stat regeneration, detect staleness, and add an on-demand "pull HF + recompute" command.

## Problem

Audio-duration columns (`transcribed_audio_seconds`, `untranscribed_audio_seconds`) can only be computed when a corpus's audio files are present locally, which they usually are not — audio is gitignored and downloading it is slow/large. CI runs `get_corpus_stats.py` with no audio, so it recomputes every column **from XML except the seconds**, which it carries forward keyed by `(language, dialect)` from the existing per-corpus CSV.

This carry-forward has two silent failure modes, both observed live on `NTU_Paiwan_ASR`:

1. **New/renamed `(language, dialect)` key → 0.** The Year-2 data added a `pwn / Southern` dialect; CI recomputed its audio *count* (331 from XML) but there was no prior key to carry seconds from, so `transcribed_audio_seconds = 0.0`.
2. **Existing key keeps stale seconds when audio grows.** Central/Eastern/Northern audio counts grew (158/503/874 → 237/1132/1412) but their seconds stayed at the previously-computed values (3034/9841/16554), now under-counting — with no signal that they are out of date.

A third, structural fragility: the seconds live inside the per-corpus CSV, which is auto-regenerated and auto-committed by CI and is therefore merge-conflict-prone. The recent `feature/corpus-metrics-timeseries` merge had to hand-resolve a conflict that was *literally* these audio seconds inside a regenerated CSV.

## Goals

- Audio seconds **persist going forward** and are isolated from the CI-regenerated, merge-prone per-corpus CSVs.
- **Staleness is detectable**: when a corpus's audio has changed since its seconds were computed, keep the last good value but flag it.
- An **on-demand** process pulls a single corpus's audio from Hugging Face and recomputes its seconds — run only when explicitly requested, never in CI/merge.

## Non-goals

- Computing audio seconds in CI (runners have no audio; unchanged).
- Changing how non-audio columns are counted.
- Within-corpus duplicate handling, language/dialect logic, or any other QC concern.

## Architecture

### Component 1 — `statistics/audio_durations.csv` (source of truth)

A single committed file, keyed by `(corpus, language, dialect)`:

```
corpus,language,dialect,transcribed_audio_seconds,untranscribed_audio_seconds,transcribed_audio_count,untranscribed_audio_count,computed_at
```

- `*_seconds` — the authoritative durations.
- `*_count` — the audio-element counts **at the moment the seconds were computed** (the staleness anchor), not the live count.
- `computed_at` — ISO date the row was last computed (informational).

**Only** `update_audio_stats.py` and `refresh_audio_stats.py` write this file. `get_corpus_stats.py` (CI) only reads it. Because it is never auto-regenerated, CI cannot clobber it and it does not participate in the per-corpus-CSV merge-conflict surface.

### Component 2 — `get_corpus_stats.py` (reader + staleness; the CI path)

- Replace `load_carry_seconds(csv_path)` (reads the per-corpus CSV) with `load_audio_durations(corpus_name)` (reads `audio_durations.csv`, filtered to the corpus, keyed by `(language, dialect)` → `(t_sec, u_sec, t_count_at_compute, u_count_at_compute)`).
- When writing a per-corpus CSV, fill the seconds columns from the truth file (counts continue to come from XML).
- **Staleness check**: for each `(language, dialect)` whose current XML audio-count > 0, compare that count to the truth file's `count_at_compute`:
  - equal → current.
  - differs, or no truth row for the key → **STALE**. Keep the last good seconds (0 if never computed) and print a warning on the existing stderr channel:
    `[get_corpus_stats] STALE AUDIO <corpus> <lang>/<dialect>: XML has N audio elements; seconds computed against M (run refresh_audio_stats).`
- New `--report-stale-audio` mode: scan all corpora and print every stale `(corpus, language, dialect)` as a worklist (no CSV writes).
- No new column in the per-corpus CSV (warnings + report suffice; revisit if the Gitbook needs a machine-readable flag).

### Component 3 — `update_audio_stats.py` (writer)

- Computes seconds from local audio per `(language, dialect)` (existing logic), reads the current XML audio-counts for the same buckets, and **upserts** rows into `audio_durations.csv` for the corpus with `seconds + count_at_compute + computed_at`.
- Preserves the existing safety: if a bucket previously had nonzero seconds and no audio file is found now, keep the old value and warn — never wipe good data.
- No longer writes seconds into the per-corpus CSV (that is `get_corpus_stats`'s job, sourced from the truth file).

### Component 4 — `refresh_audio_stats.py` (on-demand HF command)

`python QC/utilities/refresh_audio_stats.py <corpus> [--keep-audio]`:

1. Run the corpus's `Corpora/<corpus>/download_audio_data.sh` to pull its audio from Hugging Face (in place under `Corpora/<corpus>/`).
2. Invoke the `update_audio_stats` logic for that corpus → writes the truth file.
3. Regenerate that corpus's per-corpus stats CSV (`get_corpus_stats` for the corpus) so its seconds columns reflect the new truth.
4. Delete the downloaded audio unless `--keep-audio` (audio is gitignored; deletion is safe and leaves no large files behind).

Never invoked by CI or a merge. A thin `refresh-audio-stats` skill wraps it (matches the repo's other workflow skills).

### Component 5 — Migration + one-time repair

The two corpora known to have changed audio (`WilangYutasVideos`, `NTU_Paiwan_ASR`) are repaired by a real recompute; everything else is migrated from version control without downloading.

- **Migration (all audio corpora except the two excepted ones)**: for each, copy the seconds currently in the committed per-corpus CSV into `audio_durations.csv`, and set `count_at_compute` to that corpus's audio-count **as recorded in version control at the revision where those seconds were established** (the count the seconds were actually computed against — found by walking the per-corpus CSV's git history). For corpora whose audio is unchanged this equals the current XML audio-count, so `get_corpus_stats` marks them **not stale** with no download. If a corpus silently changed since its seconds were computed, current count ≠ `count_at_compute` → it is correctly flagged **stale** (a safety net), to be refreshed later. This is why we use the historical count rather than blindly stamping the current count (which would mark everything not-stale by construction).
- **Repair (the two excepted corpora)**: run `refresh_audio_stats` for `WilangYutasVideos` and `NTU_Paiwan_ASR` (and any other corpus migration flags stale) to write real seconds + real `count_at_compute`, clearing their stale flags. **Contingent on HF egress in this environment** — probe first; if blocked, commit the mechanism + migration + the stale worklist for the maintainer to run on a suitable machine.

## Data flow

```
refresh_audio_stats <corpus>           update_audio_stats <corpus>     (manual / on-demand)
  └─ download_audio_data.sh (HF)          (audio already local)
  └─ compute seconds + counts ──────────────────┐
                                                 ▼
                              statistics/audio_durations.csv   ← source of truth (committed)
                                                 ▲ read-only
  get_corpus_stats.py (CI) ───────────────────────┘
     └─ fills seconds in <corpus>_corpora_stats.csv from the truth file
     └─ flags STALE where current XML audio-count != count_at_compute
                 │
                 ▼
  corpus_metrics.py aggregates per-corpus CSVs → corpus_size_history.csv (transcribed_audio_seconds)
```

## Error handling / edge cases

- **Brand-new corpus, no truth row, has audio**: seconds 0, flagged stale until `refresh_audio_stats` runs. Correct.
- **Truth row exists, audio removed from XML (count → 0)**: not flagged (no current audio to be stale about); the stale truth row is harmless and overwritten on the next refresh.
- **`download_audio_data.sh` missing or HF unreachable**: `refresh_audio_stats` fails loudly and changes nothing; the truth file is untouched.
- **`update_audio_stats` run with no audio present**: keeps existing truth values, warns; never writes 0 over a good number.

## Testing

Unit tests (`tests/utilities/`):
- `load_audio_durations`: parse, per-corpus filter, keying.
- Staleness: count mismatch → stale; missing row + audio present → stale; match → current.
- `get_corpus_stats`: fills seconds from the truth file; emits the stale warning; `--report-stale-audio` lists the right buckets.
- `update_audio_stats`: upsert into the truth file; don't-wipe-when-no-audio safety.
- Migration: builds the truth file from sample per-corpus CSVs with blank `count_at_compute`.
- `refresh_audio_stats`: compute + write + cleanup logic with a fake local audio dir and a stubbed download step (no real network in tests).

## Docs

- `CLAUDE.md` corpus-metrics section: audio seconds now live in `statistics/audio_durations.csv` (the source of truth, never CI-regenerated); refreshed via `refresh_audio_stats.py` (HF pull) or `update_audio_stats.py` (local audio); CI reads it and flags staleness.
- `QC/README.md`: document `audio_durations.csv`, `refresh_audio_stats.py`, and `--report-stale-audio`.
