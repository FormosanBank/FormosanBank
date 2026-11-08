---
icon: language
---

# BLEU evaluation

> Two `sacrebleu`-based scripts for comparing machine-translation output against a reference — one for sentence-aligned CSVs, one for long-text/paragraph blocks.

## What it's for

These are MT-evaluation utilities, not corpus QC. They score the output of translation systems (typically a FormosanBank MT model versus a baseline such as NotebookLM, or two model variants) against expert reference translations, using BLEU via `sacrebleu`. They support evaluation of the [Formosan MT Toolkit](../formosan-mt-toolkit.md); they do not touch corpus XML.

Both require `sacrebleu` (`pip install sacrebleu`) and exit with a clear message if it's missing. Pick by input shape: short sentence-aligned rows → `bleu_scores.py`; whole paragraphs/long texts → `bleu_long_texts.py`.

## When to run it

On demand, when you have MT output to evaluate against a reference. Not part of the automated QC pipeline and not invoked by [Running an Audit](../running-an-audit.md). Prerequisite is an input file in the expected layout (see each script below) plus `sacrebleu`.

## bleu_scores.py

### How it works

Reads a CSV where each row holds, in columns 3/4/5 (1-based): the **reference** translation, **model A**'s translation, and **model B**'s translation. It auto-detects a header row with a heuristic (treats the first row as a header unless those cells contain CJK characters). BLEU is computed only on rows where **both** models produced a non-empty translation; rows missing either are skipped and counted. Both models are scored with `sacrebleu.corpus_bleu(..., tokenize="zh")`, so this path assumes Chinese-side references.

### Usage

```bash
source .venv/bin/activate
python QC/bleu_scores.py path/to/file.csv
```

| Argument   | Default      | Meaning                                                     |
| ---------- | ------------ | ---------------------------------------------------------- |
| `csv_path` | **required** | CSV with reference / model-A / model-B in columns 3 / 4 / 5. |

### Output

Prints to stdout: the count of evaluated and skipped sentences, a two-row BLEU table (Model A vs Model B), and the full `sacrebleu` signature line for each. No files written. Exits with a message if the file is missing, empty, or has no valid rows.

## bleu_long_texts.py

### How it works

Parses a `long_texts.txt` file of paragraph-per-line blocks, each labelled by a known prefix (`Amis:`, `Expert Chinese:`, `FormosanBankMT Chinese:`, `NotebookLM Chinese:`, and optional `Expert English:` / `FormosanBankMT English:` / `NotebookLM English:`). A new `Amis:` line starts a new block; unlabelled lines (blank separators) are ignored. It then scores, separately for Chinese and English, the FormosanBankMT and NotebookLM hypotheses against the Expert reference — using only blocks that contain all three of the relevant labels. Chinese uses `tokenize="zh"`, English uses `tokenize="13a"`.

### Usage

```bash
source .venv/bin/activate
python QC/bleu_long_texts.py path/to/long_texts.txt
```

| Argument   | Default      | Meaning                                       |
| ---------- | ------------ | --------------------------------------------- |
| `txt_path` | **required** | The labelled long-texts file (see format above). |

### Output

Prints the number of text blocks found, then per-language BLEU lines (FormosanBankMT and NotebookLM) with full `sacrebleu` signatures; notes when no complete Chinese or English blocks exist. No files written. Exits with a message if the file is missing or contains no blocks.

## Related

- [Formosan MT Toolkit](../formosan-mt-toolkit.md)
- [QC Pipeline overview](README.md)
