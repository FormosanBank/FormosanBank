---
icon: spell-check
---

# orthography_compare.py

> Quantifies how similar two corpora's orthographies and vocabularies are, using the `orthographic_info` objects produced by `orthography_extract.py`.

## What it's for

When the same language appears in more than one corpus, their spelling and word distributions should be comparable (especially on the standard tier). `orthography_compare.py` takes two extracted orthography profiles and reports a battery of similarity / distance metrics over their character sets, character frequencies, and bigram frequencies, plus a side-by-side character-frequency plot.

It is a diagnostic aid for deciding whether two sources agree orthographically — for example, to confirm that a newly standardized corpus lines up with an existing one for the same language.

## How it works

It does **not** read XML. Instead it loads the two pickled `orthographic_info` files written by [orthography_extract.py](orthography-extract.md) (one per `--o_info_*` directory) and computes:

- **Unique-character set** — Jaccard similarity and overlap coefficient.
- **Character frequencies** (normalized to distributions) — cosine similarity, Euclidean distance, KL divergence.
- **Bigram frequencies** (normalized) — cosine similarity, Euclidean distance.

All metrics are printed to the terminal. It then renders a grouped bar chart of per-character relative frequencies (log-odds scale) across the two corpora, restricted to alphabetic characters and apostrophes.

The language label used in the plot is inferred by matching a known language name inside the `--o_info_1` path, so point `--o_info_1` at a directory whose path contains the language name (the layout `orthography_extract.py` already produces).

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. First extract both corpora (see [orthography_extract.py](orthography-extract.md)), then:

```bash
python QC/orthography/orthography_compare.py \
  --o_info_1 /path/to/extract_logs_A/Amis \
  --o_info_2 /path/to/extract_logs_B/Amis \
  --corpus_1 CorpusA \
  --corpus_2 CorpusB
```

Each `--o_info_*` argument must be a **directory** that contains a file literally named `orthographic_info` (the script appends that filename itself).

| Flag | Default | Notes |
| --- | --- | --- |
| `--o_info_1` | (required) | Directory holding the first `orthographic_info` file. |
| `--o_info_2` | (required) | Directory holding the second `orthographic_info` file. |
| `--corpus_1` | (required) | Display name for the first corpus (used in the plot). |
| `--corpus_2` | (required) | Display name for the second corpus (used in the plot). |

## Output & side effects

Read-only — it touches neither XML nor the input pickles. It prints the metrics to stdout and writes one plot:

- `QC/orthography/compare_logs/<Language>/character_frequency_comparison_<corpus_1>_<corpus_2>.png`

(The log directory is created next to the script, not under `--output_dir`; this script has no `--output_dir` flag.)

## When to run it

Optional / on demand, after both corpora have been processed with `orthography_extract.py`. It is not a gating check; use it when investigating cross-corpus orthographic agreement for a shared language.

## Related

- [QC Pipeline overview](README.md)
- [orthography_extract.py](orthography-extract.md)
- [validate_orthography.py](validate-orthography.md)
- [validate_vocabulary.py](validate-vocabulary.md)
