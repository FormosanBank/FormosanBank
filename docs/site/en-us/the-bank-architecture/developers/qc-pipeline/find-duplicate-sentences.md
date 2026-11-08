---
icon: clipboard-list
---

# Find duplicate sentences (cross-corpus)

> Find sentences from one source corpus that are duplicated in *other* corpora for the same language.

## What it's for

When the same source text is ingested by more than one corpus (a website scraped twice, a textbook that also appears in a dictionary, etc.), the same sentences end up in two places. `find_duplicate_sentences.py` detects that overlap: it takes one source corpus and reports every sentence of it that also appears in any other corpus for the same language.

This is the **cross-corpus** counterpart to [validate_duplicate_sentences.py](validate-duplicate-sentences.md), which finds duplicates **within** a single corpus. Use this one to discover that, say, half of `Glosbe` Amis overlaps with `ePark` Amis; use the validator to find a corpus repeating itself internally.

## How it works

The script collects, from the source, every `<S>` that has a direct-child `<FORM kindOf="standard">` (configurable via `--kind-of`), keyed by its lowercased text into a lookup index — so matching is case-insensitive but otherwise exact (no normalization beyond `.strip().lower()`). At most one matching FORM per `<S>` is indexed.

It then walks the entire `--corpora` tree for every other `*.xml` whose path contains the `--language` folder name, excluding the source file(s) themselves, and looks up each of their sentences in the index. Parse errors are warned about and skipped. Every hit becomes a match row. The corpus name for a match is derived from the top-level folder under `Corpora/`.

The source can be either a whole corpus (`--source-corpus`, which reads `Corpora/<corpus>/XML/<language>/*.xml`) or a single file (`--source-xml`). These two are mutually exclusive and one is required.

## Usage

```bash
source .venv/bin/activate

# Compare Glosbe Amis against all other Amis corpora (standard forms, default)
python QC/utilities/find_duplicate_sentences.py --source-corpus Glosbe --language Amis

# Compare ePark Paiwan against all other Paiwan corpora
python QC/utilities/find_duplicate_sentences.py --source-corpus ePark --language Paiwan

# Use original rather than standard forms
python QC/utilities/find_duplicate_sentences.py --source-corpus Glosbe --language Amis --kind-of original

# Point directly at a specific source XML file
python QC/utilities/find_duplicate_sentences.py \
    --source-xml Corpora/Glosbe/XML/Amis/amis_glosbe.xml --language Amis
```

| Flag              | Default                                   | Meaning                                                       |
| ----------------- | ----------------------------------------- | ------------------------------------------------------------ |
| `--source-corpus` | — (mutually exclusive, one required)      | Source corpus folder name under `Corpora/`.                  |
| `--source-xml`    | — (mutually exclusive, one required)      | A specific source XML file instead of a whole corpus.        |
| `--language`      | **required**                              | Language folder name to compare within (e.g. `Amis`).        |
| `--corpora`       | `Corpora`                                 | Path to the `Corpora/` directory.                            |
| `--kind-of`       | `standard`                                | `FORM/@kindOf` value to compare on.                          |
| `--output`        | `<source_corpus>_<language>_duplicates.csv` | Output CSV path.                                            |

## Output & side effects

Writes one CSV with columns `source_id, corpus, xml_file, match_id` — the source sentence id, the matching corpus, the matching file (relative to `Corpora/`), and the matched sentence's id. Rows are sorted by source id (numeric suffix aware). Read-only with respect to the corpora. Progress and counts print to stdout; the source directory or file errors out (exit via `sys.exit`) if missing or empty.

## When to run it

Optional, run when you suspect overlap between corpora — e.g. before publishing a new corpus you want to know how much it duplicates existing ones, or when deciding whether one corpus subsumes another. The resulting CSV feeds [remove_duplicate_sentences.py](remove-duplicate-sentences.md) if you decide to prune the overlap. For internal duplication, use [validate_duplicate_sentences.py](validate-duplicate-sentences.md) instead.

## Related

- [validate_duplicate_sentences.py](validate-duplicate-sentences.md) — the within-corpus equivalent
- [remove_duplicate_sentences.py](remove-duplicate-sentences.md)
- [sample_sentences.py](sample-sentences.md)
- [QC Pipeline overview](README.md)
