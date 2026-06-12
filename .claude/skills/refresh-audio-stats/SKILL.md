---
name: refresh-audio-stats
description: Recompute a single corpus's audio-duration stats by pulling its audio from Hugging Face, then deleting the audio. Use when a corpus's audio has changed (or get_corpus_stats --report-stale-audio flags it) and its statistics/audio_durations.csv seconds need refreshing. Never part of CI or a normal merge.
---

# refresh-audio-stats

Refresh the audio-seconds source of truth (`statistics/audio_durations.csv`) for ONE corpus whose audio changed. Audio is gitignored and large, so this is on-demand only — CI never recomputes seconds.

## When to run
- `python QC/utilities/get_corpus_stats.py --report-stale-audio` lists the corpus, or
- you just added/updated a corpus's audio on Hugging Face.

## Pre-checks
1. Repo `.venv` active (`source .venv/bin/activate`).
2. `git`, `git-lfs`, `jq`, and the `hf` CLI installed, and HF network egress available (the download step needs them).
3. `Corpora/<corpus>/download_audio_data.sh` exists.

## Recipe
```bash
source .venv/bin/activate
python QC/utilities/refresh_audio_stats.py <corpus>   # add --keep-audio to keep the download
```
This pulls the corpus's HF audio, recomputes its durations into `statistics/audio_durations.csv`, refreshes `statistics/<corpus>_corpora_stats.csv`, and deletes the audio.

## After
1. `git diff statistics/audio_durations.csv statistics/<corpus>_corpora_stats.csv` — review the new seconds.
2. Re-run `python QC/utilities/get_corpus_stats.py --report-stale-audio` and confirm the corpus is gone from the list.
3. Commit `statistics/audio_durations.csv` and the per-corpus CSV. The history PNG/`corpus_size_history.csv` audio series updates on the next push via the corpus-metrics CI.

## What this is NOT
- Not a CI step. Never wire it into a workflow.
- Not a bulk tool — one corpus at a time, by design (downloads are large).
