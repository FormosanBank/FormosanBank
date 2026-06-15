---
icon: pen-to-square
---

# Manual edits (reproducible hand edits)

> A cooperating pair of scripts — `capture_manual_edits.py` records hand edits to a corpus's XML, and `apply_manual_edits.py` replays them on every rebuild — so manual corrections survive reprocessing and leave a readable changelog.

## What it's for

Some corpus problems can't be fixed by any automated step — they surface in [validate_text.py](validate-text.md) or [validate_glosses.py](validate-glosses.md) findings and require a maintainer to hand-edit individual `<S>` blocks. Raw hand edits are fragile: they are **clobbered the next time the corpus is rebuilt from source**, and they leave no record of what changed or why.

This pair makes hand edits reproducible. The maintainer edits the XML in place, runs **`capture_manual_edits.py`** to snapshot the edits into `CodeAndDocs/manual_edits.xml`, and commits that file. On every subsequent rebuild, **`apply_manual_edits.py`** replays the recorded edits as the *first* cleaning step, so the corrections are reproduced rather than lost — and it regenerates a human-readable `CodeAndDocs/manual_edits.md` changelog. This is reproducibility infrastructure for **dev repos**; both `manual_edits.xml` and `manual_edits.md` live in `CodeAndDocs/` and are committed (and ported) with the corpus.

{% hint style="info" %}
The recorded edits hold only **pre-standardization** content — original-tier `FORM`, `TRANSL`, and `W`/`M` structure. Because `apply_manual_edits.py` runs before [standardize.py](standardize.md) and [add_phonology.py](add-phonology.md), the standard tier and `PHON` are regenerated downstream and are deliberately stripped from the recorded blocks. Shared logic for both scripts lives in `QC/cleaning/manual_edits_common.py`.
{% endhint %}

## The editing loop

1. Run the full pipeline (clean → standardize → phonology → validators) to get the findings CSVs.
2. Decide what to correct.
3. Hand-edit the relevant `<S>` blocks directly in the (standardized, phonologized) XML.
4. Run `capture_manual_edits.py` — it records each edit on the `strip()` basis (standard tier + `PHON` dropped).
5. Re-run the pipeline; `apply_manual_edits.py` reproduces the edits first, before any other cleaning.

## capture_manual_edits.py

`QC/utilities/capture_manual_edits.py` — the "dumb snapshotter". It diffs the working-tree XML against a git **baseline** (`--baseline-ref`, default `HEAD`) and records the differences.

### How it works

For each `*.xml` under `--corpora_path`, it loads the working-tree tree (`W`) and the baseline blob (`B`) and compares them per `<S>` id on a canonicalized, stripped basis:

- **Changed** (`B` and `W` differ): record `strip(W)` — the working sentence with its standard tier and `PHON` removed.
- **New** (id present in `W`, absent in `B`): record `strip(W)` plus an `after="<previous-id>"` placement hint so apply can re-insert it in the right spot.
- **Deleted** (id present in `B`, absent in `W`): record an `<S id="…" action="delete"/>` marker.
- **Unchanged** (`B == W`): left untouched.

Records are upserted into per-file `<FILE path="…">` groups in `<corpus-root>/CodeAndDocs/manual_edits.xml`. A file that does not exist at the baseline is skipped with a warning (treated as new build output, not a hand edit). The corpus must be inside a git work tree and the baseline ref must resolve, or the script exits `2`.

## apply_manual_edits.py

`QC/cleaning/apply_manual_edits.py` — the "smart half". It re-applies the recorded edits to the current (pre-manual) XML, which it treats as the original `O`.

### How it works

For each `<FILE>` group in `manual_edits.xml`, against the matching XML file:

- **delete** — remove the matching `<S>` (no-op pruned if the id is already gone).
- **change** — replace the existing `<S>` with the recorded block (stripped of `after`/`action`).
- **add** — insert the recorded `<S>` after its `after` anchor, or append if the anchor is missing.

Entries that have become **no-ops** against the current XML (a delete for an already-absent id, or a change identical to what's already there) are **pruned** from `manual_edits.xml` with a `pruned no-op` warning. Every applied edit is recorded in the regenerated `CodeAndDocs/manual_edits.md` changelog (file, id, action, before/after one-line rendering). If `manual_edits.xml` is absent, the script prints `nothing to do` and exits `0` — so it is safe to wire unconditionally into a build.

## Usage

Run from the FormosanBank repo root after `source .venv/bin/activate`. `--corpora_path` is the corpus **XML** directory; the manual file defaults to its sibling `CodeAndDocs/manual_edits.xml`.

```bash
# 1. After hand-editing the XML, record the edits (diffed against HEAD)
python QC/utilities/capture_manual_edits.py --corpora_path Corpora/<Name>/XML

# Diff against a different baseline (e.g. the last release tag)
python QC/utilities/capture_manual_edits.py --corpora_path Corpora/<Name>/XML \
    --baseline-ref v1.2.0

# 2. On every rebuild, replay them first in the cleaning pipeline
python QC/cleaning/apply_manual_edits.py --corpora_path Corpora/<Name>/XML
```

| Flag | Default | Applies to | Purpose |
|------|---------|------------|---------|
| `--corpora_path` | *(required)* | both | The corpus XML root to walk. |
| `--manual_file` | `<corpus-root>/CodeAndDocs/manual_edits.xml` | both | Override the manual-edits file location. |
| `--baseline-ref` | `HEAD` | capture | Git ref to diff the working tree against. |
| `--verbose` | off | both | Extra logging. |

## Output & side effects

- **`capture`** writes/updates `CodeAndDocs/manual_edits.xml` (or prints "no hand edits detected" and leaves it unchanged). It does **not** modify the corpus XML.
- **`apply`** modifies the corpus XML **in place** (full lxml reparse-and-reserialize, `pretty_print`), rewrites `manual_edits.xml` if it pruned any no-ops, and regenerates `CodeAndDocs/manual_edits.md`. Diff before committing.
- Commit `manual_edits.xml` (and the regenerated `manual_edits.md`) so the edits travel with the corpus.

## When to run it

`apply_manual_edits.py` is **step 0 of the cleaning pipeline** — it runs *before* [clean_xml.py](clean-xml.md), [standardize.py](standardize.md), and [add_phonology.py](add-phonology.md). `capture_manual_edits.py` is run by hand, once, right after you make the edits. This capability is used in `Formosan-<Name>/` dev repos; the captured files are then [ported in](../porting-a-corpus.md) under `CodeAndDocs/` as part of the corpus's reproduction set.

## Related

- [clean_xml.py](clean-xml.md) — the next cleaning step
- [validate_text.py](validate-text.md) · [validate_glosses.py](validate-glosses.md) — the findings that usually motivate a hand edit
- [standardize.py](standardize.md) · [add_phonology.py](add-phonology.md)
- [QC Pipeline overview](README.md)
- [Porting a Corpus In](../porting-a-corpus.md)
