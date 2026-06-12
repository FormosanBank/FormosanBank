# Dialect detector

An **informational** utility that guesses `TEXT/@dialect` for a FormosanBank XML
file when its `xml:lang` is known but the dialect is missing, `unknown`, or not
yet trusted. It reads the **standard** tier only, never mutates XML, and never
gates CI — it ranks the candidate dialects and explains why, so a maintainer can
fill in or verify `TEXT/@dialect`.

- **In scope:** the multi-dialect languages in [`dialects.csv`](../../../dialects.csv) —
  Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, and `trv` (= Truku + Seediq's three
  dialects). Single-dialect languages are reported `unsupported`.
- **Out of scope:** writing the canonical `TEXT/@dialect`, any hard pass/fail.

> Run everything from the repo root with the project venv. The examples use
> `python`; in this repo that is `PYTHONPATH=. .venv/bin/python`.

## Quick start — guess a dialect

```bash
PYTHONPATH=. python -m QC.utilities.dialect_detector predict \
  --path Corpora/<Corpus>/XML/<file-or-dir>
```

Example output:

```
File: Corpora/.../Paiwan/Some_File.xml
Language: pwn -> Paiwan
  existing dialect: Eastern        # shown when the file already has dialect=
  guess: Eastern  (top1 p=1.000)
    Eastern        p=1.000  orthography=+1.000  char=-2.957  bigram=-5.447  word=-7.276
    Central        p=0.000  orthography=+1.000  char=-3.433  bigram=-6.299  word=-8.429
    Southern       p=0.000  ...
    Northern       p=0.000  ...
```

Reading it:
- **`guess`** is the top dialect, or **`unknown`** when the model's confidence is
  below the language's calibrated threshold (or the file has no standard tier).
- The ranked rows give each candidate's probability plus the **per-component
  breakdown**: `orthography` (TSV letter-inventory fit), `char` / `bigram`
  (grapheme distributions), `word` (lexical distribution). This is how you see
  *why* a dialect won or was ruled out.
- **`existing dialect:`** is printed when the file already carries a `dialect=`
  attribute, so you can compare the guess against the current label at a glance.

`--path` accepts a single `.xml` file or a directory (scored recursively).
Pass `--lang <iso>` to override the language code read from `xml:lang`.

## Retraining when more data lands

The models are trained from the already-labeled XMLs under `Corpora/`, so they
should be **retrained as FormosanBank grows** (new labeled corpora, dialect fixes):

```bash
PYTHONPATH=. python -m QC.utilities.dialect_detector train
```

This rebuilds one model per in-scope language and writes
[`QC/utilities/dialect_models/<Language>.json`](../dialect_models/) (committed, ~1.5 MB
total). `train` also **calibrates each language's `unknown` threshold** from a
held-out cross-validation (it maximizes how often the model commits while keeping
held-out accuracy-on-committed ≥ 0.95), and bakes that threshold into the saved
model. Commit the regenerated `dialect_models/*.json` after retraining.

Flags: `--top_n` (profile size per dialect, default 2000), `--models_dir`,
`--corpora_path`, `--orthographies`. `train --calibrate` is on by default;
internals expose `calibrate=False` for a quick uncalibrated build.

## Checking how well it works

```bash
# Honest, held-out (stratified per-dialect 5-fold; refits profiles AND combiner per fold)
PYTHONPATH=. python -m QC.utilities.dialect_detector crossvalidate [--language ami]

# Apparent (train = test) — optimistic; use crossvalidate for honest numbers
PYTHONPATH=. python -m QC.utilities.dialect_detector evaluate [--language ami]
```

**Prefer `crossvalidate`.** `evaluate` is train-on-test and optimistic, because a
file's own words sit in its dialect's profile. Current honest held-out top-1
(forced choice):

| Atayal · Bunun · Puyuma · Rukai · Seediq | Paiwan | Amis |
|:--:|:--:|:--:|
| 1.000 | 0.854 | 0.819 |

With the calibrated thresholds, those five languages commit **every** file at ~1.0
precision; **Amis commits ~72%** and **Paiwan ~66%** (≥0.95 precision), returning
`unknown` on the rest.

### Why Amis and Paiwan are harder

Their dialects are written with **identical letter inventories** — Paiwan's four
dialects share one alphabet (see [`Orthographies/Ortho113/Paiwan.tsv`](../../../Orthographies/Ortho113/Paiwan.tsv):
no `NA` cells), and Amis's four "common" dialects share one writing system (通用版;
only Southern/南勢 is orthographically distinct). So they can only be told apart
**lexically**, and short or genre-neutral text legitimately comes back `unknown`.
There is no orthographic signal to add for these — see the note in
[`hints.py`](hints.py).

## How it works (one paragraph)

One model per language. The standard-tier text is tokenized into **graphemes**
(longest-match against the language's TSV letters, so digraphs like `ng` stay
whole). Each candidate dialect gets four interpretable scores — `orthography`
(reward letters in this dialect's inventory, penalize letters attested only in
*other* dialects), and smoothed log-probabilities of `char`, `bigram`, and `word`
distributions under that dialect's trained profile. A small **learned per-language
combiner** (softmax conditional-logit, 4 weights + biases) fuses them into a
calibrated probability — so the orthography-vs-lexical weighting is *learned from
the data*, not hand-set. Below the calibrated threshold the model abstains
(`unknown`) rather than guess.

## Files

| File | Responsibility |
|---|---|
| `graphemes.py` | Load TSV letter inventories; longest-match grapheme tokenizer. |
| `features.py` | Component scorers: orthography, smoothed log-prob, count extraction. |
| `combiner.py` | Softmax conditional-logit fit (`fit_combiner`, `predict_proba`). |
| `candidates.py`, `hints.py` | Candidate dialect set + label/alias reconciliation. |
| `data.py` | Corpus walking + standard-tier extraction. |
| `model.py` | `DialectModel`, `build_model` / `fit_model_from_docs`, save/load, `predict_root`, `train_all`. |
| `evaluate.py` | `cross_validate`, `calibrate_threshold`, metrics, per-language report. |
| `cli.py`, `__main__.py` | `train` / `predict` / `evaluate` / `crossvalidate`. |

Design and rationale: [`claudeplans/2026-06-11-dialect-detector-plan.md`](../../../claudeplans/2026-06-11-dialect-detector-plan.md)
and the implementation plan alongside it. Roadmap status: §F of
[`claudeplans/2026-05-27-roadmap.md`](../../../claudeplans/2026-05-27-roadmap.md).
