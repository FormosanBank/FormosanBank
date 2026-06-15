---
icon: chart-line
---

# Token counting & counting rules

> The shared counting rules (`corpus_counts.py`) and the token-count tooling built on them: per-language/dialect JSON counts, the delta between two counts, and the bar-chart plotters — all wired into the Token Count Delta CI.

## What it's for

This page groups the scripts that define and exercise FormosanBank's **token counting**. The rules themselves live in one place, `QC/corpus_counts.py`, which every counting script imports so the stats CSVs, the size tracker, and the PR token deltas can never disagree. The rest of the scripts compute a JSON snapshot of counts per language/dialect, diff two snapshots, and plot both.

## When to run it

`corpus_counts.py` is a library — you never run it directly. `count_tokens.py` / `tokens_delta.py` / the plotters are run automatically by the **Token Count Delta** GitHub Action (`.github/workflows/token-comparison.yaml`) on pull requests and on pushes to `main` (and `v1.*` tags) that touch `Corpora/` or any of these scripts. Run them by hand only to reproduce a PR's token delta locally. Run everything from the repo root after `source .venv/bin/activate`.

## corpus_counts.py — the counting source of truth

**Library, not a CLI.** This module is the single source of truth for how FormosanBank counts, imported by [`get_corpus_stats.py`](get-corpus-stats.md), [`corpus_metrics.py`](corpus-metrics.md), and `count_tokens.py`.

The rules (decided 2026-06-10):

- A **token** is a whitespace-separated chunk containing at least one Unicode letter or digit — so `123` counts, but `?` does not.
- Per sentence, count the `standard` sentence-tier `FORM` if non-empty, else the `original` `FORM`, else 0. Only direct `FORM` children of `S` count; `W`/`M` FORMs are **never** counted as tokens.
- **Language identity** comes from `xml:lang` + `dialect` only: `trv` + dialect `Truku` → Truku; `trv` + anything else → Seediq. The 16 ISO codes map to display names via `LANG_CODE_TO_NAME`.

It also tallies per-file structural counts (sentences, segmented/glossed words, English/Mandarin translation tokens, `W`/`M`/`TRANSL`/`AUDIO` element counts) and splits audio into transcribed (under `S`/`W`) vs untranscribed (direct `TEXT` child). Malformed XML raises `ParseError`; callers decide whether to collect or abort.

## count_tokens.py — per-language/dialect token JSON

**How:** parses every XML under a corpora path via `corpus_counts.collect_records` and emits JSON shaped `{LanguageName: [total_tokens, {dialect: tokens}]}`. It computes from **XML, not from `statistics/*.csv`**, because it runs on arbitrary checkouts (e.g. a PR base in a git worktree) where committed CSVs may be stale or absent.

**Usage:**

```bash
python QC/count_tokens.py Corpora > current_token_count.json
```

**Output:** JSON on stdout (a stable interface consumed by `tokens_delta.py` and `plot_counts.py`).

## tokens_delta.py — diff two token JSONs

**How:** loads an old and a new `count_tokens.py` JSON and writes the per-language and per-dialect difference (`new − old`) to an output JSON, same shape with deltas in place of counts.

**Usage:** positional args, in order `<old> <new> <out>`:

```bash
python QC/tokens_delta.py base_token_count.json current_token_count.json token_delta.json
```

**Output:** the deltas JSON at the third path.

## plot_counts.py — bar chart of counts

**How:** reads a `count_tokens.py` JSON and draws a horizontal bar chart to `plot.png` in the working directory. The second positional arg is a mode: starting with `1` plots language totals only (top 25); otherwise it plots per-language-and-dialect rows (top 40).

**Usage:**

```bash
python QC/plot_counts.py current_token_count.json 0   # language + dialect
python QC/plot_counts.py current_token_count.json 1   # language totals only
```

**Output:** `plot.png` (CI renames it to `language_dialect_counts.png` / `language_counts.png`).

## plot_deltas.py — bar chart of a delta

**How:** reads a `tokens_delta.py` JSON and draws a diverging bar chart (positive green, negative red) of the top 40 non-zero changes by absolute size.

**Usage:**

```bash
python QC/plot_deltas.py token_delta.json
```

**Output:** `language_dialect_deltas.png` in the working directory.

## The Token Count Delta GitHub Action

`.github/workflows/token-comparison.yaml` runs on PRs and on pushes to `main`/`v1.*` tags. It checks out the compare ref, resolves a base ref (PR base SHA, or the push's "before" SHA, or `origin/main`), runs `count_tokens.py` on both (the base in a detached `git worktree`), computes the delta with `tokens_delta.py`, writes a Markdown delta summary to the job summary, and renders the three plots. Artifacts (`current_token_count.json`, `base_token_count.json`, `token_delta.json`, and the PNGs) are uploaded; this workflow has read-only permissions and **commits nothing**.

## Related

- [QC Pipeline overview](README.md)
- [get_corpus_stats.py](get-corpus-stats.md) — per-corpus CSVs using the same rules
- [corpus_metrics.py](corpus-metrics.md) — collection-level aggregation and growth history
- [Porting a Corpus In](../porting-a-corpus.md)
