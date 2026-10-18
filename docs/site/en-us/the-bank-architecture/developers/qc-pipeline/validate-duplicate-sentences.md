---
icon: circle-check
---

# validate_duplicate_sentences.py

> Detects `<S>` sentences whose chosen-tier FORM text is duplicated within a single corpus — flagging same-file duplicates as HARD and cross-file (same corpus) duplicates as SOFT.

## What it's for

Duplicate sentences inside one corpus usually mean one of two things: an ingestion bug copied the same `<S>` twice into a file (almost always wrong), or genuinely repeated material appears across stories (e.g. the same proverb in two texts — often legitimate). This validator separates those two cases by scope so a maintainer can act on the dangerous one and judge the benign one.

Cross-**corpus** duplicate detection is explicitly out of scope here; for that, use the separate utility [find_duplicate_sentences.py](find-duplicate-sentences.md).

## How it works

It walks every `*.xml` file under the scan root and, for each `<S>`, takes the text of its first direct-child `FORM` whose `kindOf` matches the chosen `--tier` (default `standard`). The text is normalized for comparison by collapsing whitespace runs to a single space and stripping the ends; comparison is **case-sensitive** and otherwise exact. Files that fail to parse are skipped with a `WARNING` on stderr.

It builds an index of `normalized_text -> [occurrences]`. Any normalized text appearing in two or more `<S>` elements becomes a finding, classified by how many distinct files it spans:

- **HARD** — every occurrence in the group is in the **same file** (likely an ingestion bug).
- **SOFT** — the group spans **two or more files** within the scan root (possibly legitimate repeated material).

This script uses its own lightweight `Finding`/`Occurrence` dataclasses, not the shared `QC/validation/_finding.py` framework, and it does **not** assign `Vxxx` rule IDs. Findings are sorted HARD-first, then by text and first occurrence.

Search modes (the standard `search_by` positional):

- `by_path --path <file-or-dir>` — scan one path directly.
- `by_corpus --corpora_path <dir> --corpus <Name>` — scans `<corpora_path>/<Name>`.
- `by_language --corpora_path <dir> --language <Name>` — iterates every corpus under `corpora_path`, scanning only its `XML/<Language>/` subtree; HARD/SOFT stays scoped within each corpus (never cross-corpus).

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`.

```bash
# Scan one corpus's XML directory (default tier: standard).
python QC/validation/validate_duplicate_sentences.py by_path \
    --path Corpora/ePark/XML \
    --output logs/dupes_ePark.csv

# Compare on the original (source-faithful) tier instead.
python QC/validation/validate_duplicate_sentences.py by_path \
    --path Corpora/ePark/XML --tier original \
    --output logs/dupes_ePark.csv
```

By corpus name, or sweeping one language across all corpora:

```bash
python QC/validation/validate_duplicate_sentences.py by_corpus \
    --corpora_path Corpora --corpus ePark --output logs/dupes_ePark.csv

python QC/validation/validate_duplicate_sentences.py by_language \
    --corpora_path Corpora --language Paiwan --output logs/dupes_Paiwan.csv
```

| Flag | Default | Meaning |
|---|---|---|
| `search_by` (positional) | — | `by_path`, `by_corpus`, or `by_language`. |
| `--path` | — | XML file or directory (required for `by_path`). |
| `--corpora_path` | — | Corpora root (required for `by_corpus` / `by_language`). |
| `--corpus` | — | Corpus name (required for `by_corpus`). |
| `--language` | — | Language name (required for `by_language`). |
| `--tier` | `standard` | `FORM @kindOf` value to compare: `standard` or `original`. |
| `--output` | `duplicate_sentences_findings.csv` | CSV output path. |
| `--verbose` | off | Print one line per finding to stdout. |

## Output & exit codes

It writes a CSV at `--output` with one row per (finding, occurrence): columns `severity, normalized_text, file, s_id, raw_text`. The `file` paths are relative to the scan root. A short summary prints to stdout, e.g. the count of HARD and SOFT groups and their occurrence totals, followed by the findings CSV path.

This validator is **informational and always exits 0**, even when HARD duplicates are present. The HARD/SOFT labels classify severity in the CSV but do not gate the build, so there is no `--no-exit-on-hard` flag here. To actually delete duplicates, feed a downstream remover; see [remove_duplicate_sentences.py](remove-duplicate-sentences.md).

## When to run it

Run it during corpus QC after the XML validates structurally, and before treating sentence counts as final. A populated `standard` tier is assumed for the default `--tier standard`; if a corpus has only an original tier, either pass `--tier original` or create the standard tier first with [standardize.py](standardize.md) `--copy`. Pair it with [find_duplicate_sentences.py](find-duplicate-sentences.md) when you also need to check for overlap **across** corpora.

## Related

- [find_duplicate_sentences.py](find-duplicate-sentences.md) — cross-corpus duplicate detection (out of scope for this validator).
- [remove_duplicate_sentences.py](remove-duplicate-sentences.md) — removes duplicate sentences from XML.
- [validate_xml.py](validate-xml.md) — run first to ensure the XML is structurally valid.
- [Running an Audit](../running-an-audit.md)
- [QC Pipeline overview](README.md)
