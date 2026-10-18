---
icon: wand-magic-sparkles
---

# dialect_detector

> A per-language machine-learning tool that guesses a corpus file's `TEXT/@dialect` from its standard-tier text — a maintainer aid, never a CI gate, and not yet wired into the core audit/port loop.

## What it's for

Several Formosan languages have multiple dialects (Amis, Atayal, Bunun, Paiwan, Puyuma, Rukai, and `trv` = Truku + Seediq). `dialect_detector` learns, per language, what each dialect's spelling and word usage look like, then predicts the dialect of new (or mislabeled) files from the **standard** tier. It is a newer addition: useful for catching or proposing dialect labels, but **read-only** — it never mutates XML — and it is not part of the standard validator sequence.

## How it works

It is a Python **package** (`QC/utilities/dialect_detector/`) run via `python -m`. Training builds one model per in-scope language (codes `ami`, `tay`, `bnn`, `pwn`, `pyu`, `dru`, `trv`) from the already-labeled XMLs under `Corpora/`. A file is a labeled training document when its `xml:lang` matches, its `dialect` attribute is a recognized candidate (not blank/`unknown`), and it has non-empty standard-tier text. Files under a corpus's `CodeAndDocs/`, and files matching a pattern in `QC/utilities/dialect_detector/training_exclusions.tsv` (today: NTU_Paiwan_ASR read speech), are never training documents.

Each model combines four per-dialect feature components — **orthography** (grapheme inventory from `Orthographies/Ortho113`), **char** unigrams, **bigram**, and **word** profiles — into a single probability via a small learned per-language weighting (logistic combiner). Prediction returns a full ranked list of dialects with calibrated probabilities and a per-component breakdown, returning **`unknown`** when the top probability is below the model's threshold or the file has no standard tier. `train` calibrates each language's threshold from a held-out cross-validation so it commits as much as possible while keeping accuracy-on-committed ≥ 0.95.

**Model storage.** Models are JSON, one per language, under `QC/utilities/dialect_models/`, named by language *name* — so `trv` is written as `Seediq.json` (the table that carries both Truku and Seediq dialect columns); there is no separate `Truku.json`.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. The package needs the repo root on `PYTHONPATH`:

```bash
# (Re)train all per-language models -> QC/utilities/dialect_models/*.json
PYTHONPATH=. python -m QC.utilities.dialect_detector train

# Predict the dialect of one file or a directory of files
PYTHONPATH=. python -m QC.utilities.dialect_detector predict \
  --path Corpora/<Corpus>/XML/<file>.xml

# Honest held-out accuracy (stratified k-fold, refits per fold)
PYTHONPATH=. python -m QC.utilities.dialect_detector crossvalidate --language ami

# Apparent (train = test) accuracy — optimistic; prefer crossvalidate
PYTHONPATH=. python -m QC.utilities.dialect_detector evaluate --language ami
```

Subcommands: **`train`**, **`predict`**, **`crossvalidate`**, **`evaluate`**.

| Flag | Subcommands | Default | Notes |
| --- | --- | --- | --- |
| `--corpora_path` | all | `Corpora/` | Source of labeled XML. |
| `--orthographies` | all | `Orthographies/Ortho113` | Grapheme inventories for the orthography feature. |
| `--models_dir` | all | `QC/utilities/dialect_models` | Where models are written/read. |
| `--top_n` | all | `2000` | Per-dialect profile size (top-N tokens kept). |
| `--path` | `predict` | (required) | File or directory of XML to label. |
| `--lang` | `predict` | from `xml:lang` | Override the language code. |
| `--language` | `evaluate`, `crossvalidate` | all in-scope | Restrict to one language code. |
| `--k` | `crossvalidate` | `5` | Cross-validation folds. |
| `--precision_floor` | `crossvalidate` | `0.95` | Accuracy-on-committed floor used for threshold calibration. |

Use `crossvalidate` for honest numbers; `evaluate` is train-on-test and optimistic.

## Output & side effects

`predict`, `evaluate`, and `crossvalidate` are read-only and print to stdout. **`train` is the only command that writes**, regenerating `QC/utilities/dialect_models/*.json`; re-run it when new labeled XMLs land so the models grow with the bank. No command ever modifies corpus XML.

## When to run it

Outside the core pipeline, on demand — to sanity-check or propose `dialect` labels for multi-dialect languages, or after adding labeled data (`train`). It complements, but does not replace, the dialect-attribute checks in [validate_dialect.py](validate-dialect.md). Full design and interpretation notes live in `QC/utilities/dialect_detector/README.md`.

## Related

- [QC Pipeline overview](README.md)
- [validate_dialect.py](validate-dialect.md)
- [orthography_detector.py](orthography-detector.md)
- [orthography_extract.py](orthography-extract.md)
