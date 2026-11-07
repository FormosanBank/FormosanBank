---
icon: spell-check
---

# orthography_extract.py

> Builds a grapheme inventory and character / bigram / word / punctuation statistics for one language (optionally split by dialect) from a chosen sentence-tier `FORM`.

## What it's for

`orthography_extract.py` reads the sentence text of a corpus and summarizes *how it is spelled*: which characters appear, how often, which bigrams are common, which punctuation marks are used, and which words are frequent. The result is a serialized statistics object (`orthographic_info`) plus a set of plots.

This object is the raw material the orthography- and vocabulary-level validators consume. Run it before [validate_orthography.py](validate-orthography.md) and [validate_vocabulary.py](validate-vocabulary.md).

## How it works

For each requested language, the script walks the target path and parses every `*.xml` file whose path matches the language name. From each `<S>` it pulls a sentence-level `FORM`:

- With `--kindOf standard` (or `original`), it reads only `FORM[@kindOf='<value>']`.
- With **no** `--kindOf`, it reads *every* `FORM` in the sentence, which mixes the original and standard tiers together — undesirable for any corpus that has both. Always pass `--kindOf` explicitly; the QC default is `standard`.

The collected text is lowercased, HTML-entity-unescaped (so a literal `&amp;` counts as one `&`, not five characters), and NFC-normalized. It then computes, keeping only items occurring **at least 5 times**:

- `unique_characters` and `character_frequency`
- `character_classes` (by Unicode category), plus base-character / diacritic decomposition
- `2-grams` (bigram frequencies, spaces excluded)
- `punctuation` (characters in Unicode category `P*`)
- `word_frequency` (whitespace split, punctuation stripped except apostrophe)

With `--by_dialect true`, text is bucketed by each file's `TEXT/@dialect` attribute and a separate inventory is produced per dialect; files lacking a `dialect` attribute fall into a `default` bucket (with a warning). Without it, everything is pooled into one `default` bucket.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# One corpus, one language, standard tier, split by dialect
python QC/orthography/orthography_extract.py \
  --corpora_path Corpora \
  --corpus <CorpusName> \
  --language Amis \
  --kindOf standard \
  --by_dialect true \
  --output_dir /path/to/qc-output/extract_logs

# All corpora and all languages under a path
python QC/orthography/orthography_extract.py \
  --corpora_path /path/to/Final_XML \
  --corpus all \
  --language All \
  --kindOf standard \
  --by_dialect true \
  --output_dir /path/to/qc-output/extract_logs
```

| Flag | Default | Notes |
| --- | --- | --- |
| `--corpora_path` | (required) | Path containing the corpus/corpora. |
| `--corpus` | (required) | A corpus name, or `all` to process every corpus under `--corpora_path`. |
| `--language` | (required) | A Formosan language name (e.g. `Amis`), or `All` for every supported language. |
| `--kindOf` | none | `standard` or `original`. If omitted, **all** `FORM`s are pooled — pass `standard` for QC. |
| `--by_dialect` | `false` | `true`/`false`; the flag alone means `true`. Splits output per `TEXT/@dialect`. |
| `--output_dir` | `<corpus>/extract_logs` | Where the `orthographic_info` files and plots are written. |

## Output & side effects

Read-only with respect to the corpus XML — it never modifies the data. For each language (and dialect, if `--by_dialect`) it creates a folder under `--output_dir` (`<output_dir>/<Language>[/<dialect>]`) containing:

- `orthographic_info` — a pickled dict of all the statistics above (consumed by the validators).
- `unique_characters.txt`
- `character_frequencies.png`, `character_class_distribution.png`
- `bigram_heatmap.png`, `top_bigrams.png`
- `punctuation_frequencies.png`, `top_words.png`

An inventory with no punctuation still produces `punctuation_frequencies.png`, with a clear "No punctuation found" message instead of failing during visualization.

## When to run it

In the QC pipeline this runs **after** the standard tier exists (create it with [standardize.py](standardize.md) `--copy` if needed) and after text validation, and **before** the reference-comparison validators. See the [Running an Audit](../running-an-audit.md) and [Porting a Corpus In](../porting-a-corpus.md) workflows for placement.

## Related

- [QC Pipeline overview](README.md)
- [validate_orthography.py](validate-orthography.md)
- [validate_vocabulary.py](validate-vocabulary.md)
- [standardize.py](standardize.md)
