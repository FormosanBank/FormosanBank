# Dialect detector

An **informational** utility that guesses `TEXT/@dialect` for a FormosanBank XML
file when its `xml:lang` is known but the dialect is missing, `unknown`, or not
yet trusted. It reads the **standard** tier only, never mutates XML, and never
gates CI — it ranks the candidate dialects and explains why, so a maintainer can
fill in or verify `TEXT/@dialect`.

- **In scope:** the multi-dialect languages in [`dialects.csv`](../../../dialects.csv) —
  Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, and `trv` (= Truku + Seediq's three
  dialects). Single-dialect languages are reported `unsupported`.
- **In scope but not trained yet:** Pazeh (Pazeh, Kaxabu) and Babuza-Favorlang
  (Babuza, Favorlang). Maintainer, 2026-10-18: "I see no reason not to include
  Pazeh (Pazeh, Kaxabu) and Babuza-Favorlang (Babuza, Favorlang), even though they
  don't have standard orthographies (yet)." As of that date there is nothing to
  train on: Babuza-Favorlang has 2 labelled files, both `Favorlang`; Pazeh's 3 files
  are all `dialect="unknown"`; all 5 have only an original tier. Add them (with a
  fallback for having no Ortho113 table) once each has standard-tier files labelled
  in at least two dialects.
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

Two kinds of labelled file are never training documents:
- anything under a corpus's `CodeAndDocs/` (snapshots there are copies of
  published files and would count twice);
- files matching a pattern in [`training_exclusions.tsv`](training_exclusions.tsv),
  each row with its reason. Today that is NTU_Paiwan_ASR's read speech, whose
  `dialect` names the reader rather than the passage read. `train` prints how many
  files the list removed.

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
(forced choice; retrained 2026-10-18 on 675 labelled files):

| Atayal · Bunun · Puyuma · Rukai | Seediq | Paiwan | Amis |
|:--:|:--:|:--:|:--:|
| 1.000 | 0.948 | 0.696 | 0.671 |

With the calibrated thresholds, Atayal, Bunun, Puyuma and Rukai commit **every**
file at 1.0 precision and Seediq commits ~99% at 0.96; **Amis commits ~40%** and
**Paiwan ~20%** (≥0.95 precision), returning `unknown` on the rest.

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
| `training_exclusions.tsv` | Labelled files never used for training, each with its reason. |
| `model.py` | `DialectModel`, `build_model` / `fit_model_from_docs`, save/load, `predict_root`, `train_all`. |
| `evaluate.py` | `cross_validate`, `calibrate_threshold`, metrics, per-language report. |
| `cli.py`, `__main__.py` | `train` / `predict` / `evaluate` / `crossvalidate`. |

Design and rationale: [`claudeplans/2026-06-11-dialect-detector-plan.md`](../../../claudeplans/2026-06-11-dialect-detector-plan.md)
and the implementation plan alongside it. Roadmap status: §F of
[`claudeplans/2026-05-27-roadmap.md`](../../../claudeplans/2026-05-27-roadmap.md).
