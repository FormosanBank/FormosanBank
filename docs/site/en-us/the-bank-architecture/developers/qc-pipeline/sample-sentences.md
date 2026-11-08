---
icon: clipboard-list
---

# Sample sentences for expert review

> Pull N random `<S>` elements from a corpus and format them as a print- or email-ready markdown report for a human expert to spot-check.

## What it's for

Automated validators catch schema, orthography, and gloss problems, but they can't judge whether a translation is *correct*, whether content is natural, or whether a sentence is grammatical. `sample_sentences.py` is the maintainer-facing tool for that human pass: it draws a random sample of sentences and renders everything a reviewer needs — forms, phonology, translations, audio references, and the full word/morpheme tier — as readable markdown.

It is wrapped by the **sample-sentences-for-expert-review** skill, which walks a maintainer through generating the sample and sending it to an expert.

## How it works

The script walks the corpus and collects one record per `<S>`. If `<corpus_path>/XML/` exists, only that subdirectory is walked (matching the validators' canonical-walk convention); otherwise the whole `<corpus_path>/` is walked, for corpora not yet re-laid-out. Files that fail to parse, and roots that aren't `<TEXT>`, are skipped silently.

For each sentence it captures: the S id and the TEXT's `xml:lang`, the source file, `FORM` text by `kindOf` (original/standard/alternate — other kinds are dropped), `PHON`, `TRANSL` grouped by language (multiple same-language translations joined with ` | `), `AUDIO` `file=` references, and the complete `W` tier, including each word's `FORM`/`PHON`/`TRANSL`/`AUDIO` and its `M` children with the same fields.

Sampling uses `random.Random(seed)`: pass `--seed` for a reproducible sample. `--n` is capped at the corpus's total sentence count. The chosen sentences are sorted by `(file, s_id)` before rendering, so the report reads in document order. In the report, a sentence-tier FORM line is suppressed when its text duplicates an earlier kind already printed (e.g. `standard == original`).

## Usage

```bash
source .venv/bin/activate

# 20 sentences (default) to stdout
python QC/utilities/sample_sentences.py --corpus_path Corpora/ePark

# 30 reproducible sentences to a file
python QC/utilities/sample_sentences.py --corpus_path Corpora/ePark --n 30 --seed 42 --output sample.md
```

| Flag            | Default        | Meaning                                                          |
| --------------- | -------------- | --------------------------------------------------------------- |
| `--corpus_path` | **required**   | Corpus directory (typically `Corpora/<Name>/`). If `XML/` exists, only it is walked. |
| `--n`           | `20`           | Number of `<S>` to sample (capped at the total S count).        |
| `--seed`        | `None`         | Random seed for reproducibility (default: nondeterministic).    |
| `--output`      | stdout         | Write the markdown report to this file instead of stdout.       |

## Output & side effects

Writes a markdown report — either to stdout or, with `--output`, to a file (parent directories are created). The only side effect is that output file. Read-only with respect to the corpus. Exit codes: `1` if `--corpus_path` is not a directory or no `<S>` elements are found, `0` otherwise.

## When to run it

Optional, outside the automated text-QC loop. Run it once a corpus has otherwise passed validation, when you want a human to sanity-check translation quality, naturalness, or content accuracy — typically near the end of [Running an Audit](../running-an-audit.md) or before publishing via [Porting a Corpus In](../porting-a-corpus.md). Prefer the **sample-sentences-for-expert-review** skill, which handles seed choice and report delivery.

## Related

- [find_duplicate_sentences.py](find-duplicate-sentences.md)
- [QC Pipeline overview](README.md)
