---
icon: wrench
---

# Fix-up utilities

> Three targeted, in-place fixers that resolve specific validator findings — missing dialects, colliding morpheme ids, and redundant translations.

## What it's for

These are small, surgical fixers. Each one answers a particular finding raised by the validators (`validate_dialect.py`, `validate_xml.py`, `validate_glosses.py`) and does nothing else. You run them after a validator has told you *what* is wrong; the fixer applies the mechanical correction so you don't hand-edit XML.

All three **mutate XML in place** (the same convention as `standardize.py` and `clean_xml.py`). `fix_dialects.py` and `fix_multiple_translations.py` write at the byte level so they preserve whitespace, quote style, the XML declaration, and trailing newlines exactly; `fix_ids.py` re-serializes the tree but only touches files that actually change. **Always `git diff` before committing.**

## fix_dialects.py

### How it works

For every `.xml` file under `--path`, it inspects the root `<TEXT>`. If `TEXT/@dialect` is already non-empty, the file is left untouched (the script is idempotent). Otherwise it sets `@dialect` based on the `xml:lang` code, driven by `QC/validation/_dialect_inventory.py`:

- **Single-dialect languages** → the language name itself (e.g. `xml:lang="tsu"` → `dialect="Tsou"`).
- **Multi-dialect languages, and `xml:lang="trv"`** (ambiguous between Truku and Seediq) → `dialect="unknown"`.

Files whose root is not `<TEXT>`, that fail to parse, or whose opening tag the byte-level regex can't locate, are skipped and reported on stderr without aborting the run.

This answers **missing-`@dialect` findings from `validate_dialect.py`** (see [validate_dialect.py](validate-dialect.md)).

### Usage

```bash
source .venv/bin/activate
python QC/utilities/fix_dialects.py --path Corpora/ePark/XML
```

| Flag     | Default      | Meaning                                                  |
| -------- | ------------ | -------------------------------------------------------- |
| `--path` | **required** | File or directory; directories are walked recursively for `*.xml`. |

### Output & side effects

In place, no dry-run. Per-file `set dialect=...` / skip lines go to stderr, followed by a summary (scanned / updated / already-set / skipped, plus a breakdown of new dialect values). `"unknown"` rows should then be resolved to a real dialect by a human or by [dialect_detector.py](dialect-detector.md). Diff before committing.

## fix_ids.py

### How it works

For each `<W>` in each target file, it renumbers every `<M>` child to `<W.id>M<n>`, where `n` is the 1-based position of the morpheme in document order under that `<W>`. This repairs **V039 duplicate-id collisions** (where the source pipeline reused one M id for two distinct morphemes that share a surface form) and gaps (e.g. `M1, M2, M4` where `M3` was elided). Scope is **M ids only** — `S` and `W` ids are left alone. `<W>` elements with no id are skipped. An M whose id already matches its computed value is not counted as a change, so unchanged files are never rewritten.

It reuses `validate_xml.py`'s discovery helpers, so corpus/language targeting matches the validator's: canonical XML under `<corpus>/XML/`, working files under `CodeAndDocs/` excluded.

This answers **V039 (id uniqueness across S/W/M)** from [validate_xml.py](validate-xml.md).

### Usage

```bash
source .venv/bin/activate

# Preview without writing
python QC/utilities/fix_ids.py --dry-run by_path --path Corpora/ePark/XML

# By corpus / language
python QC/utilities/fix_ids.py by_corpus   --corpus ePark --corpora_path Corpora
python QC/utilities/fix_ids.py by_language --language Amis --corpora_path Corpora

# Apply, listing every individual change
python QC/utilities/fix_ids.py --verbose by_path --path Corpora/ePark/XML/example.xml
```

| Flag / positional | Default      | Meaning                                                      |
| ----------------- | ------------ | ------------------------------------------------------------ |
| `search_by`       | **required** | One of `by_path`, `by_corpus`, `by_language`.                |
| `--path`          | (by_path)    | File or directory.                                           |
| `--corpus` + `--corpora_path` | (by_corpus) | Corpus name and the `Corpora/` root.            |
| `--language` + `--corpora_path` | (by_language) | Language name and the `Corpora/` root.        |
| `--dry-run`       | off          | Print planned `old_id -> new_id` changes, write nothing.     |
| `--verbose`       | off          | List each individual id change (otherwise per-file counts only). |

### Output & side effects

Writes in place unless `--dry-run`. Re-serializes with `xml_declaration=True` and no pretty-print, so existing indentation is preserved. Per-file change counts print to stdout; a grand total prints to stderr. Diff before committing.

## fix_multiple_translations.py

### How it works

Within each parent element (`S`, `W`, or `M`), `TRANSL` children are grouped by `xml:lang`. When a parent has more than one `TRANSL` for the same language, the **first** in document order is treated as the primary and left alone; every later same-language sibling gets `ver="alt"` added. This lets downstream tooling tell the primary translation from alternates (common in corpora like `Virginia_Fey_Dictionary` that carry several English or Chinese glosses per entry).

Conservative and idempotent: a non-first `TRANSL` that *already* has a `ver` attribute (any value) is left untouched and reported — the script never clobbers an existing `ver` — and after one run the alternates already carry `ver="alt"`, so re-running is a no-op. The edit is byte-level (splicing ` ver="alt"` into the specific opening tags), preserving formatting. Parse errors and non-XML files are skipped and reported.

This answers **redundant/ambiguous same-language `TRANSL` findings** surfaced by [validate_glosses.py](validate-glosses.md).

### Usage

```bash
source .venv/bin/activate
python QC/utilities/fix_multiple_translations.py --path Corpora/Virginia_Fey_Dictionary/XML
```

| Flag     | Default      | Meaning                                                  |
| -------- | ------------ | -------------------------------------------------------- |
| `--path` | **required** | File or directory; walked recursively for `*.xml`.       |

### Output & side effects

In place, no dry-run. Per-file `added N ver="alt"` lines go to stderr, then a summary (scanned / changed / added / alternates-already-set / skipped). Idempotent, so safe to re-run. Diff before committing.

## When to run it

After the relevant validator flags the issue, and before re-running that validator to confirm the finding is cleared. In a fresh port these typically come up during [Porting a Corpus In](../porting-a-corpus.md) and [Running an Audit](../running-an-audit.md): `fix_dialects.py` once dialects are confirmed, `fix_ids.py` when V039 fires on a word/morpheme-segmented corpus, and `fix_multiple_translations.py` for dictionary-style corpora with multiple glosses per entry. None of them transliterate or otherwise change text content.

## Related

- [validate_dialect.py](validate-dialect.md)
- [validate_xml.py](validate-xml.md)
- [validate_glosses.py](validate-glosses.md)
- [dialect_detector.py](dialect-detector.md)
- [standardize.py](standardize.md)
- [QC Pipeline overview](README.md)
