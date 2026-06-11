# Additional Corpus Time-Series Metrics — Design

**Date:** 2026-06-11
**Branch / worktree:** `feature/corpus-metrics-timeseries` at `../FormosanBank-metrics-timeseries`
**Status:** approved in brainstorming; pending spec review

## Goal

Track three more corpus metrics over time, alongside the existing token series, with the same CSV-plus-PNG treatment:

1. **Transcribed audio** — duration (`transcribed_audio_seconds`, plotted as hours)
2. **Mandarin-translated text** — `zho_transl_count` (Formosan words in sentences that have a Chinese `TRANSL`)
3. **Glossed text** — `glossed_words` (Formosan words in sentences containing at least one glossed morpheme)

All three already exist as per-corpus columns produced by `QC/utilities/get_corpus_stats.py`; this work surfaces them into the size-over-time series and adds plots.

## Background (current state)

After the pipeline-unification work (branch `feature/claude-tooling-phase-0`, the base of this worktree):

- `QC/corpus_counts.py` is the shared counting module. `analyze_root(root)` already computes `glossed_words`, `zho_transl_count`, and `transcribed_audio_count` per file (but **not** `transcribed_audio_seconds` — durations need audio files and are computed only by the manual `QC/utilities/update_audio_stats.py`).
- `QC/corpus_metrics.py` builds the size-over-time history. Two record-building paths feed `aggregate_records` → `totals`:
  - `read_stats_dir(stats_dir)` — aggregates the committed per-corpus `statistics/*_corpora_stats.csv` (used by the normal CI `--history` append). These CSVs contain all three target columns, **including `transcribed_audio_seconds`**.
  - `analyze_xml_root` (XML walk; also the `--history-rebuild` git-blob path) — delegates to `corpus_counts.analyze_root`, which has `glossed_words`/`zho_transl_count` but cannot produce `transcribed_audio_seconds`.
- History rows are written by `history_row` (current checkout), `history_row_from_records` (rebuild), and `append_history_row` (normal `--history`), with columns fixed in `write_history_csv`'s `fieldnames`.
- `statistics/corpus_size_history.csv` columns today: `date, commit, tokens, sentences, xml_files, sources, languages, parse_errors`. Its rows currently hold **old-rule** token numbers (pre-unification); a `--history-rebuild` will restate them.
- `plot_history(rows, output_dir)` plots a single series (tokens) to `corpus_size_over_time.png`, embedded in `README.md` and `QC/README.md`.
- CI: `.github/workflows/corpus-metrics.yaml` runs `get_corpus_stats.py --all --strict`, then `corpus_metrics.py Corpora --stats-dir statistics --history --history-cache statistics/corpus_size_history.csv`, then commits the history CSV + PNG (and per-corpus CSVs).

## Decisions (from brainstorming)

- **Audio = duration**, plotted in hours. Forward-only: it can only come from the committed per-corpus CSVs (the `--stats-dir` append path), never from git-blob reconstruction. Historical rebuild rows get `transcribed_audio_seconds = 0`.
- **One CSV, more columns.** Extend `corpus_size_history.csv` rather than create parallel files.
- **Backfill via a one-time `--history-rebuild`**, run as part of this work (locally, in this worktree), committing the regenerated CSV + PNGs. The rebuild restates `tokens` under the new rules and backfills `zho_transl_count` + `glossed_words` across history; `transcribed_audio_seconds` stays 0 for historical rows. A follow-up normal `--stats-dir --history` append then replaces the HEAD row so it carries today's real audio seconds — the first real point of the duration series.
- **Three separate PNGs** (not a combined panel), matching the existing single-series style and the "equivalent files" framing.

## Design

### Data model

`corpus_size_history.csv` gains three columns (11 total):

```
date, commit, tokens, sentences, xml_files, sources, languages, parse_errors,
transcribed_audio_seconds, zho_transl_count, glossed_words
```

New columns are appended after the existing ones so any reader keying by name is unaffected and column order stays stable.

### Code changes (`QC/corpus_metrics.py`)

1. **Surface the fields into records.**
   - `analyze_xml_root`: add `glossed_words` and `zho_transl_count` from the `corpus_counts.analyze_root` record; add `transcribed_audio_seconds: 0` (uncomputable from XML).
   - `read_stats_dir`: add `glossed_words`, `zho_transl_count`, `transcribed_audio_seconds` from the CSV row (via the existing `as_int`/float read; seconds is a float).
2. **Aggregate them.** Add the three to the totals computation so `aggregate_records` sums them. `transcribed_audio_seconds` is a float sum; the other two are ints. (Implementation note: the existing `COUNT_FIELDS`/`add_counts` use `int(...)`. Seconds must sum as float — either add a small float-aware path or keep seconds out of the int `COUNT_FIELDS` and sum it separately into `totals`. The plan will pick the least-invasive option and test it.)
3. **Write them in history rows.** Extend `history_row`, `history_row_from_records`, and `append_history_row` to include the three new keys, and add them to `write_history_csv`'s `fieldnames`. `load_history_csv` already returns dicts keyed by column, so older rows missing the columns read back as absent keys — the rebuild rewrites every row, so post-rollout all rows have all columns.
4. **Generalize plotting.** Refactor `plot_history` into a helper that plots one named column with a label, y-axis formatter, and output filename; call it for each of the four series. Tokens keeps its existing filename and look. New outputs:
   - `corpus_transcribed_audio_over_time.png` — y in hours (`seconds / 3600`), title "Transcribed Audio Over Time", caption noting duration tracking begins at rollout (early points may be sparse).
   - `corpus_mandarin_words_over_time.png` — y in words, title "Mandarin-Translated Words Over Time".
   - `corpus_glossed_words_over_time.png` — y in words, title "Glossed Words Over Time".

### CI changes (`.github/workflows/corpus-metrics.yaml`)

- No new compute steps — the existing `--stats-dir --history` run already produces the extended row (with seconds from the committed CSVs) once the code emits the columns.
- The "Commit updated statistics" step's `cp`/`git add` list gains the three new PNGs.

### Docs

- Embed the three new PNGs in `README.md` next to the existing growth graph, and in `QC/README.md`.
- Note in `QC/README.md` that `transcribed_audio_seconds` in the history is forward-only (no historical reconstruction) and depends on the per-corpus CSVs' seconds being kept current via `update_audio_stats.py`.

### Tests (`tests/utilities/test_corpus_metrics.py`)

- Extend the `--stats-dir` snapshot test: seed per-corpus CSVs with nonzero `glossed_words`, `zho_transl_count`, `transcribed_audio_seconds`; assert the totals and the written history row carry all three.
- Add a test that the XML/rebuild path writes `transcribed_audio_seconds = 0` while still populating `zho_transl_count`/`glossed_words` (using the existing fixture mini-corpus, which has glossed morphemes and a zho TRANSL).
- Add a plotting smoke test: call the generalized plot helper for each series against a small rows list and assert the four PNG files are created (matching how any existing plot test works; if none exists, assert no-exception + file presence).

### Rollout (run in this worktree, committed here)

1. Implement + test the code, CI, docs changes.
2. Regenerate per-corpus CSVs: `get_corpus_stats.py --all --strict` (counts fresh; seconds carried — already seeded for ILRDF/Tang/Wilang/Whitehorn).
3. `corpus_metrics.py Corpora --history-rebuild --output-dir <tmp>` → restates the full history CSV (tokens new-rule; Mandarin/glossed backfilled; audio seconds 0 historically). Inspect.
4. `corpus_metrics.py Corpora --stats-dir statistics --history --history-cache <rebuilt csv>` → replaces the HEAD row with one carrying today's real audio seconds; regenerates all four PNGs.
5. Copy the regenerated `corpus_size_history.csv` + four PNGs into `statistics/`, commit. Read the actual CSV (row counts, the HEAD row's new columns) and eyeball the PNGs before committing — quote evidence.

## Non-goals

- Per-language or per-dialect time series (the history is whole-corpus totals only, as today).
- Computing historical audio durations (impossible without historical audio; accepted).
- Changing the token counting rules (already settled in the prior work).
- A combined multi-metric dashboard panel.

## Risks / notes

- **Float vs int summing for seconds** is the one non-mechanical code point; the plan must handle it without breaking the int-based `COUNT_FIELDS` aggregation used by every other metric.
- **`--history-rebuild` is slow** (full first-parent walk of XML-changing commits). It's a one-time rollout cost, run locally here, not in CI.
- **The audio duration series starts sparse** (one real point at rollout). Expected; captioned on the plot.
- This worktree lacks downloaded audio, but the rebuild/append don't need it — seconds come from the committed per-corpus CSVs, not recomputation.
