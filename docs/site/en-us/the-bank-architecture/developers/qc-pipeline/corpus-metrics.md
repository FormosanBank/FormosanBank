---
icon: chart-line
---

# corpus_metrics.py

> Aggregates the per-corpus statistics CSVs (or raw XML) into the corpus-wide metrics report, benchmark comparison, and the size-over-time history CSV and growth graphs.

## What it's for

`QC/corpus_metrics.py` rolls everything up to the collection level. It produces `corpus_metrics.json` and `corpus_metrics.md` (totals plus per-language and per-source breakdowns and a benchmark comparison), a set of "current state" PNG bar charts, and — in its history modes — appends to `statistics/corpus_size_history.csv` and renders the growth-over-time line charts the GitBook embeds.

It can compute either from the per-corpus CSVs written by [`get_corpus_stats.py`](get-corpus-stats.md) (fast; pass `--stats-dir`) or directly from XML under `Corpora/`. Either way the counting rules come from [`corpus_counts.py`](token-counting.md), the single source of truth.

## How it works

In `--stats-dir` mode it reads every `*_corpora_stats.csv` and inverts the pipeline: `get_corpus_stats.py` counts, this script aggregates. Without `--stats-dir` it parses each `Corpora/**/XML/**/*.xml` itself. It aggregates records into totals, `by_source`, `by_language`, and `by_language_dialect`, then writes the JSON/MD report and (unless `--no-plots`) the PNGs.

The history CSV (`corpus_size_history.csv`) has three modes:

- **`--history`** — append a single row at HEAD from the current snapshot totals. Re-running on the same commit replaces that row rather than duplicating it.
- **`--history-extend`** (the incremental path CI uses) — resume from the cached CSV: seed the corpus state from the commit in its last row, then add one row for **every XML-changing first-parent commit since that row**, so a multi-commit push leaves no gaps in the graph. It falls back to a single HEAD append when the cache is empty, when the cached tip is not an ancestor of HEAD (diverged), or when there is no gap (≤1 new commit).
- **`--history-rebuild`** (XML mode only — must omit `--stats-dir`) — restate the *entire* history CSV from git blobs via a full first-parent walk over `Corpora/**/XML/**/*.xml`. Slow; restates all rows under the current counting rules. (History rows written before 2026-06 used the old rules; the discontinuity is accepted.)

`--history-rebuild` and `--history-extend` are mutually exclusive. History walks operate on first-parent, `--diff-filter=ADM` commits touching the XML pathspec, reading file blobs with `git cat-file --batch`.

## Usage

Run from the repo root after `source .venv/bin/activate`.

```bash
# Aggregate per-corpus CSVs + incrementally extend the history (what CI runs)
python QC/corpus_metrics.py Corpora \
  --stats-dir statistics \
  --output-dir corpus-metrics \
  --history-extend \
  --history-cache statistics/corpus_size_history.csv

# Report only, straight from XML, no history, no plots
python QC/corpus_metrics.py Corpora --no-plots

# Full restatement of the history CSV from git (slow; XML mode)
python QC/corpus_metrics.py Corpora --history-rebuild
```

| Flag | Default | Purpose |
| --- | --- | --- |
| `corpora_path` (positional) | `Corpora` | Path to the Corpora directory. |
| `--output-dir` | `corpus_metrics` | Directory for the JSON/MD/PNG artifacts. |
| `--stats-dir` | none | Aggregate the per-corpus CSVs in this dir instead of parsing XML. |
| `--benchmarks` | `QC/reference/corpus_benchmarks.json` | Optional external-benchmark JSON. |
| `--history` | off | Append one HEAD row to the history CSV. |
| `--history-extend` | off | Incrementally fill the history CSV for each XML-changing commit since the last cached row. |
| `--history-rebuild` | off | Rebuild the whole history CSV from git (XML mode only; slow). |
| `--history-cache` | `<output-dir>/corpus_size_history.csv` | Existing history CSV to read and append to. |
| `--max-history-commits` | `0` (no limit) | Cap on commits sampled (rebuild) or the fill window (extend). |
| `--no-plots` | off | Skip PNG generation. |
| `--fail-on-parse-error` | off | Exit nonzero if any XML file cannot be parsed. |

## Output & side effects

Into `--output-dir`: `corpus_metrics.json`, `corpus_metrics.md`, and (unless `--no-plots`) `corpus_language_tokens.png`, `corpus_source_tokens.png`, `corpus_benchmark_comparison.png`. In a history mode it also writes `corpus_size_history.csv` plus `corpus_size_over_time.png`, `corpus_transcribed_audio_over_time.png`, `corpus_mandarin_words_over_time.png`, and `corpus_glossed_words_over_time.png`.

In CI, the [Corpus Metrics workflow](get-corpus-stats.md) (`.github/workflows/corpus-metrics.yaml`) runs this with `--stats-dir statistics --history-extend`, then auto-commits `corpus_size_history.csv`, the four growth PNGs, and the per-corpus `*_corpora_stats.csv` files back to `main`. **Do not hand-edit any of these committed CSVs or PNGs.** This script never writes `statistics/audio_durations.csv`.

## When to run it

CI runs it on every push to `main` touching `Corpora/` or the counting scripts. Humans rarely run it by hand; the most likely manual use is a one-time `--history-rebuild` after a counting-rule change, or generating an ad-hoc local report. It is downstream of [`get_corpus_stats.py`](get-corpus-stats.md) in the stats pipeline.

## Related

- [QC Pipeline overview](README.md)
- [get_corpus_stats.py](get-corpus-stats.md) — produces the per-corpus CSVs this aggregates
- [Token counting & counting rules](token-counting.md) — `corpus_counts.py` source of truth
- [Audio duration stats](audio-duration-stats.md)
