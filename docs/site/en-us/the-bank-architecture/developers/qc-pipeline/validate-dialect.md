---
icon: circle-check
---

# validate_dialect.py

> Prints a `(xml:lang, dialect) -> count` table so a human can eyeball whether a corpus's dialect distribution looks right; it never flags a value as invalid.

## What it's for

`validate_dialect.py` is the *informative* companion to the `V036` dialect check in [validate_xml.py](validate-xml.md). Where `V036` decides pass/fail (is each `TEXT/@dialect` valid for its language?), this script just summarizes what's actually present: how many files carry each `(xml:lang, dialect)` pair. A maintainer reads the table to catch distribution problems that no hard rule can express — too many `unknown` files in one language, a dialect that leaked into the wrong language, or far fewer files for a dialect than expected.

It sits alongside the structural validation stage as a quick human-readable cross-check; it is not a gate.

## How it works

The script walks every `.xml` file under `--path` recursively. For each file it parses the tree, reads the root element's `xml:lang` and `dialect` attributes, and tallies a `Counter` keyed by `(xml:lang, dialect)`. It then prints a fixed-width table sorted by `xml:lang`, then `dialect`.

Only the root element is inspected, and there are no rule IDs — this script emits no `Vxxx` findings and consults no rule module. Special bucket labels appear in the `dialect` column for edge cases:

- `(missing)` — the root is `TEXT` but has no `dialect` attribute.
- `(not-TEXT)` — the file's root element is not `<TEXT>` (counted under an empty `xml:lang`).
- `(parse-error)` — the file could not be parsed (counted under an empty `xml:lang`).

Unlike [validate_xml.py](validate-xml.md), there is no Finding/Severity machinery here, no findings CSV, and no HARD/SOFT distinction — output is purely a stdout table.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. This script has **only** a `--path` flag — it does not use the shared `by_path`/`by_corpus`/`by_language` `search_by` positional that the rule-based validators use.

```bash
# Summarize dialects for one corpus's published XML
python QC/validation/validate_dialect.py --path Corpora/ePark/XML

# A single file works too
python QC/validation/validate_dialect.py --path Corpora/ePark/XML/some_file.xml

# Whole published tree
python QC/validation/validate_dialect.py --path Corpora
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--path` | *(required)* | File or directory to walk recursively for `.xml` files. |

## Output & exit codes

Output is a single fixed-width table on **stdout**, e.g.:

```
xml:lang  dialect      count
--------  -----------  -----
ami       Coastal      12
ami       Southern     8
ami       unknown      3
trv       Truku        22
```

A `Files scanned: N` line is printed to stderr. There are no findings, no CSV, no HARD/SOFT/WARN severities.

Exit codes: **0** on success. It exits **1** only when `--path` does not exist or no `.xml` files were found under it. It never exits nonzero because of any dialect value — judging validity is `V036`'s job in [validate_xml.py](validate-xml.md), and there is no `--no-exit-on-hard` override because there are no hard findings to override.

## When to run it

Run it whenever you want a human sanity check on dialect labeling — typically right after [validate_xml.py](validate-xml.md) reports clean (or reports `V036` failures you want to understand in context), and again before porting a corpus in. It has no prerequisites beyond well-formed-enough XML to read the root attributes (unparseable files are simply bucketed as `(parse-error)`).

## Related

- [QC Pipeline overview](README.md)
- [validate_xml.py](validate-xml.md)
- [validate_text.py](validate-text.md)
- [dialect_detector](dialect-detector.md)
- [Running an Audit](../running-an-audit.md)
