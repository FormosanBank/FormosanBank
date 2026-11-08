---
icon: table-list
---

# lint_hidden_tables.py

> Lists the build files under a corpus's `CodeAndDocs/` that keep language data as Python string literals — translation tables, overrides, exclusion lists — which POL-039 wants in reviewable registries. Advisory: it warns and never fails.

## What it's for

POL-039: data that critical steps depend on lives in prominent, human-readable registries, never hard-coded in Python. Seediq-Chang's `build_xml.py` carried a 36-row translation table, 115 overrides, 27 exclusions and 12 OCR fixes as literals until October 2026, and silently ignored a student's fix to one of them. The signal is not clean — Song's override dictionaries are deliberate, keyed by sentence id and page-cited — so this is a lint a human reads, not a gate (maintainer, 2026-10-17: "Advisory lint (warn, never fail)").

## How it works

For every Python file under `CodeAndDocs/` (test directories excluded) it parses the file, takes every string literal except docstrings, and counts the tokens that read as language data: tokens with CJK characters, or words attested in the reference vocabulary of a language the corpus publishes (`QC/validation/reference/<Language>/`). Everyday English is excluded so log messages do not count. Files holding 30 or more such tokens are listed with their most frequent ones.

## Usage

```bash
python QC/validation/lint_hidden_tables.py --corpus Corpora/Song-Kanakanavu-Grammar
python QC/validation/lint_hidden_tables.py --corpus Corpora/<Name> --threshold 50
```

## Output & exit codes

```
Song-Kanakanavu-Grammar: build files holding language data as Python literals (POL-039, advisory):
     39  CodeAndDocs/scripts/extract_dictionary.py   e.g. patʉ, maan, mavʉrʉvʉrʉ, ramisi
    126  CodeAndDocs/scripts/extract_interlinear.py   e.g. 人名, 主, vanai, 原因
Deliberate, documented override tables are fine; a table nobody can review or edit without reading code is not.
```

Always exit 0. `tests/corpora/test_hidden_tables_lint.py` runs it for every corpus and turns a listing into a pytest warning.

## When to run it

During a dev-repo audit, and whenever a build script grows a dictionary of sentence text. A listing is a question — is this table documented, keyed by id, cited? — not a verdict.

## Related

- [QC Pipeline overview](README.md)
- [Running an Audit](../running-an-audit.md)
