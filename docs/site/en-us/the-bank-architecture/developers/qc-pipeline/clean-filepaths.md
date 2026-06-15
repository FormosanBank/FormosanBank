---
icon: broom
---

# clean_filepaths.py

> Renames XML (and CSV) files on disk to strip characters that are illegal or reserved in Windows filenames, so the corpus is portable across Windows and Unix.

## What it's for

Formosan corpus filenames are sometimes generated from source titles or sentence text and can contain characters that are reserved on Windows (`< > : " | ? *`). Such files check out fine on Unix but fail to clone or extract on Windows. `clean_filepaths.py` sweeps a corpus directory and renames any offending file so the same checkout works on both platforms.

It only renames *files*; it does not edit file contents, and it deliberately leaves path separators (slashes) alone, since those legitimately differ between systems.

## How it works

`main` lists the immediate subdirectories of `--corpora_path` and, for each, walks it recursively (`os.walk`). Every file ending in `.xml` **or `.csv`** is passed to `sanitize_filename`.

Sanitization operates on the **basename only** (the directory path and extension are split off and preserved):

1. Replace each reserved character `< > : " | ? *` with `_`.
2. Collapse runs of underscores (`_+` → `_`).
3. Strip leading/trailing underscores, then strip surrounding whitespace.

If the sanitized path differs from the original, the file is `os.rename`d. To avoid collisions when two distinct source names sanitize to the same string, `get_non_conflicting_path` appends ` (1)`, ` (2)`, … before the extension until an unused name is found (raising after 1000 attempts, which would indicate a deeper corpus problem). A conflict prints `Conflicting pathname detected, adding postfix`.

This is a pure filesystem operation — no XML parsing, no content changes.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`:

```bash
# Sanitize filenames throughout a corpus
python QC/cleaning/clean_filepaths.py --corpora_path Corpora/SomeCorpus

# Can be pointed at any directory whose subdirectories hold XML/CSV files
python QC/cleaning/clean_filepaths.py --corpora_path Corpora/ePark
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--corpora_path` | *(required)* | Directory whose subdirectories are walked recursively; `*.xml` and `*.csv` files are renamed in place. |

> **Note:** `main` only descends into the *subdirectories* of `--corpora_path`, not files sitting directly in it. Point it at a directory one level above the files (e.g. a corpus root that contains `XML/`).

## Output & side effects

- **Renames files on disk in place.** There is **no dry-run flag** — running the script performs the renames immediately. Run it on a clean working tree so the renames show up clearly in `git status`.
- Only filenames change; **file contents are never modified**.
- Collision handling can append ` (N)` suffixes to filenames.
- **Review `git status` / `git diff` before committing** so you can confirm the renames are the ones you intended (and that no XML elsewhere references the old names by literal filename).

## When to run it

Run as a portability cleanup when preparing a corpus, especially one whose filenames were generated from titles or text. It pairs naturally with [clean_xml.py](clean-xml.md) during corpus QC and before [porting a corpus in](../porting-a-corpus.md). It has no dependency on the XML schema, so order relative to the validators is flexible.

## Related

- [clean_xml.py](clean-xml.md)
- [Porting a Corpus In](../porting-a-corpus.md)
- [QC Pipeline overview](README.md)
