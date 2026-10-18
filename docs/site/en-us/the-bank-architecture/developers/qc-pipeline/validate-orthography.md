---
icon: circle-check
---

# validate_orthography.py

> Compares a corpus's extracted character-level orthographic profile against a per-language/dialect reference and flags how far the two diverge.

## What it's for

Formosan orthographies are not strongly standardized, so after a corpus has been transliterated into the project's common `standard` tier we want a sanity check: does its character inventory and character-frequency distribution look like the language it claims to be? This script answers that by comparing the corpus's orthographic profile against a curated reference profile for the same language (and dialect).

It does not "fix" anything and it does not gate the pipeline. It prints similarity metrics and human-readable `WARNING` lines when a metric falls outside the range that normally holds even across different orthographies, plus it saves a side-by-side character-frequency bar chart for visual inspection.

## How it works

This validator does **not** read XML directly. It consumes the `orthographic_info` pickle files produced by [orthography_extract.py](orthography-extract.md). Each such file is a dict containing `unique_characters`, `character_frequency`, `2-grams`, `word_frequency`, etc.

Layout it expects under `--o_info` (and mirrored under `--reference`):

- A language folder per language (e.g. `Amis/`).
- Either a bare `orthographic_info` file directly inside the language folder (legacy / non-dialect layout), **or** one subfolder per dialect (`Amis/Coastal/orthographic_info`, including a `default/` dialect if present). The script auto-detects which case it's in.

For each language (or each dialect within a language) it loads the corpus profile and the matching reference profile, then:

1. Excludes numerals (`string.digits`) from the character sets.
2. Computes **Jaccard similarity** and **overlap coefficient** of the unique-character sets.
3. Builds a frequency vector over the union of all reference characters plus the corpus's top-30 most-frequent characters, normalizes each, and computes **cosine similarity**, **Euclidean distance**, and **KL divergence** of character frequencies.
4. Computes **cosine similarity** and **Euclidean distance** of bigram (`2-grams`) frequencies.
5. Saves a `<label>_frequency_comparison.png` bar chart into the corpus's own `o_info` folder (the `c1_dir`).

Each metric prints a value and, if outside its expected band, a `WARNING` line. The thresholds (informational only) are:

| Metric | Warns when |
|---|---|
| Jaccard similarity (chars) | < 0.95 |
| Cosine similarity (char freq) | < 0.975 |
| Euclidean distance (char freq) | > 0.03 |
| KL divergence (char freq) | > 0.03 |
| Cosine similarity (bigram freq) | < 0.95 |
| Euclidean distance (bigram freq) | > 0.04 |

If a reference `orthographic_info` is absent for a given language/dialect, it prints a `WARNING: No reference orthographic info found ...` and skips that label.

> This script is **not** built on the Finding framework (`QC/validation/_finding.py`). It emits no `Vxxx` rule IDs and no findings CSV — only printed metrics, `WARNING` lines, and the PNG.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. First extract the corpus's orthographic profile, then compare it against the bundled reference set.

```bash
# 1) Extract the standard-tier orthographic profile for a corpus, split by dialect.
python QC/orthography/orthography_extract.py \
    --corpora_path Corpora --corpus ePark \
    --kindOf standard --by_dialect true \
    --output_dir logs/ortho_ePark

# 2) Compare that profile against the per-language reference profiles.
python QC/validation/validate_orthography.py \
    --o_info logs/ortho_ePark \
    --reference QC/validation/reference
```

Restrict to a single language:

```bash
python QC/validation/validate_orthography.py \
    --o_info logs/ortho_ePark \
    --reference QC/validation/reference \
    --language Amis
```

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--o_info` | yes | — | Folder of extracted `orthographic_info` profiles to analyze (output of `orthography_extract.py`). |
| `--reference` | yes | — | Folder of reference profiles, normally `QC/validation/reference`. |
| `--language` | no | all languages found under `--o_info` | Limit analysis to one language folder. |
| `--quiet` | no | off | Only the group header, the metric lines, `WARNING` lines and the `SUMMARY` line; also silences matplotlib's font messages. The skills run with it; the default is the full development output (the pickles' key lists and the reference's character-frequency table). |

> Despite the help text saying `--reference` defaults to the bundled folder "if blank," the code calls `parser.error` when it is omitted — both `--o_info` and `--reference` are effectively required, and each path must exist on disk.

## Output & exit codes

- **stdout**: per-language/dialect blocks of metric values and any `WARNING` lines, ending in one greppable line per group that an audit quotes:

  ```
  SUMMARY orthography | Amis / Coastal | jaccard=0.97 overlap=1.00 cosine=0.995 euclid=0.012 kl=0.008 bigram_cosine=0.97 bigram_euclid=0.03 | corpus_only=[ʉ] reference_only=[] | warnings=1
  ```

  `corpus_only` lists the characters the corpus uses and the reference does not, `reference_only` the reverse; `warnings` counts the thresholds crossed. A group with no reference prints `SUMMARY orthography | <group> | reference=missing | warnings=1`.
- **PNG**: `<label>_frequency_comparison.png` written into each corpus profile folder under `--o_info`.

This validator is **informational**: warnings do not change the exit code. There is no HARD/SOFT classification and no `--no-exit-on-hard` flag here. A `WARNING` means "look at this," typically a stray or missing character class versus the reference; treat it as a prompt for a human to review the orthography, not a build failure.

## When to run it

Run it in the orthography-checking stage of the pipeline, after a `standard` tier exists and after [orthography_extract.py](orthography-extract.md) has produced profiles (canonical pipeline step 4 feeds step 5). Pair it with [validate_vocabulary.py](validate-vocabulary.md), which uses the same `--o_info`/`--reference` profiles for high-frequency words. Prerequisites: a populated `standard` tier (create one with [standardize.py](standardize.md) `--copy` if missing) and reference profiles under `QC/validation/reference/<Language>/`.

## Related

- [orthography_extract.py](orthography-extract.md) — produces the `orthographic_info` profiles this script consumes.
- [validate_vocabulary.py](validate-vocabulary.md) — sibling check on high-frequency words.
- [Running an Audit](../running-an-audit.md)
- [QC Pipeline overview](README.md)
