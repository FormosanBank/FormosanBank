---
icon: circle-check
---

# validate_vocabulary.py

> Compares a corpus's most-frequent words against a per-language/dialect reference vocabulary and warns when the high-frequency vocabularies diverge.

## What it's for

This is the word-level companion to [validate_orthography.py](validate-orthography.md). Where that script asks "do the characters look right?", this one asks "do the most common words look right?" — a quick way to catch a corpus that has been mislabeled by language/dialect, transliterated incorrectly, or that contains large amounts of foreign-language material.

It compares the top-100 most frequent words in the corpus against the top-100 in a curated reference and reports set-overlap metrics, listing the offending high-frequency words when overlap is low.

## How it works

Like its orthography sibling, it does **not** read XML. It consumes the `orthographic_info` pickle files produced by [orthography_extract.py](orthography-extract.md), using their `word_frequency` counter.

It expects the same folder layout under `--o_info` (mirrored under `--reference`): a folder per language, containing either a bare `orthographic_info` file (legacy / non-dialect) or one subfolder per dialect, each with its own `orthographic_info`. The script auto-detects which case applies.

For each language (or dialect) it loads both profiles, takes `word_frequency.most_common(100)` from each, and computes:

1. **Jaccard similarity** of the two top-100 word sets.
2. **Overlap coefficient** of the two top-100 word sets.

| Metric | Warns when |
|---|---|
| Jaccard similarity (top-100 words) | < 0.975 |
| Overlap coefficient (top-100 words) | < 0.975 |

When either metric trips, it additionally emits warnings listing the high-frequency words present in the corpus but not in the reference, and vice versa — the concrete words to investigate. Warnings are raised via Python's `warnings.warn` (so they print once per message text). If a reference profile is missing for a language/dialect, it prints a `WARNING` and skips that label.

> This script is **not** built on the Finding framework (`QC/validation/_finding.py`). It emits no `Vxxx` rule IDs and writes no findings CSV — only printed metrics and `warnings.warn` messages.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. Extract the corpus's profile first, then compare against the bundled reference.

```bash
# 1) Extract the standard-tier orthographic profile (also carries word_frequency).
python QC/orthography/orthography_extract.py \
    --corpora_path Corpora --corpus ePark \
    --kindOf standard --by_dialect true \
    --output_dir logs/ortho_ePark

# 2) Compare top-frequency vocabularies against the per-language reference.
python QC/validation/validate_vocabulary.py \
    --o_info logs/ortho_ePark \
    --reference QC/validation/reference
```

Restrict to one language:

```bash
python QC/validation/validate_vocabulary.py \
    --o_info logs/ortho_ePark \
    --reference QC/validation/reference \
    --language Amis
```

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--o_info` | yes | — | Folder of extracted `orthographic_info` profiles to analyze. |
| `--reference` | yes | — | Folder of reference profiles, normally `QC/validation/reference`. |
| `--language` | no | all languages found under `--o_info` | Limit analysis to one language folder. |
| `--quiet` | no | off | Warnings as plain `WARNING:` lines on stdout instead of Python `warnings` on stderr, and no matplotlib font messages. The skills run with it. |

> The help text claims `--reference` defaults to the bundled folder when blank, but the code calls `parser.error` if it is omitted — both `--o_info` and `--reference` are required and must exist on disk.

## Output & exit codes

- **stdout / stderr**: per-language/dialect Jaccard and overlap values of the top-100 word lists, a warning when either is below .975 (naming the words on each side only), and one greppable line per group that an audit quotes:

  ```
  SUMMARY vocabulary | Amis / Coastal | top100_jaccard=0.88 overlap=1.00 | corpus_only=[fafahi kaying] reference_only=[] | warnings=1
  ```

  A group with no reference prints `SUMMARY vocabulary | <group> | reference=missing | warnings=1`.

This validator is **informational**: warnings never change the exit code, and there is no HARD/SOFT classification or `--no-exit-on-hard` flag. A warning is a prompt for human review (likely a mislabeled language/dialect or noisy source text), not a build failure.

## When to run it

Run it alongside [validate_orthography.py](validate-orthography.md) in the orthography-checking stage of the canonical pipeline (step 5), after a `standard` tier exists and after [orthography_extract.py](orthography-extract.md) has produced the profiles. Prerequisites: a populated `standard` tier (use [standardize.py](standardize.md) `--copy` if absent) and reference profiles under `QC/validation/reference/<Language>/`.

## Related

- [validate_orthography.py](validate-orthography.md) — character-level sibling check.
- [orthography_extract.py](orthography-extract.md) — produces the `orthographic_info` profiles this script consumes.
- [Running an Audit](../running-an-audit.md)
- [QC Pipeline overview](README.md)
