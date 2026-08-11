# Per-language standard orthography registry

Date: 2026-08-09
Status: approved

## Problem

`add_phonology.py` hardcodes `STANDARD_ORTHOGRAPHY = "Ortho113"` and assumes
Ortho113 is *the* standard orthography for every language when generating the
standard-tier PHON. This is wrong for languages whose standard is not Ortho113,
and for dormant/extinct languages (e.g. Pazeh, Siraya) where no standard has
been chosen yet. Today, Pazeh only "works" because `Ortho113/Pazeh.tsv` happens
not to exist, so the standard tier is silently skipped — the assumption is
implicit, not declared.

We want the designated standard orthography to be **declared data, per
language**, including the ability to declare that a language has **no standard
yet**.

## Scope

- A per-language registry mapping each language to its designated standard
  orthography (an `Orthographies/<scheme>` folder name), with an explicit
  "no standard yet" value supported.
- `add_phonology.py` consults the registry for the standard tier instead of the
  hardcoded constant, and runs on whatever tiers exist.
- `standardize.py` gets an unrelated cleanup: rename `--ortho113` to
  `--remove_accents`. **standardize.py does not consult the registry** — it
  never needs to know whether a standard exists.

Out of scope: any standardize/registry coupling; populating source or standard
orthography tables for Siraya; changing `--copy`; validating that a
standardize mode matches a language's designated scheme.

## Design

### 1. Registry: `standards.csv` + loader

New CSV at repo root, keyed by the table-bearing language name (the values of
`ISO_TO_LANGUAGE`):

```
language,standard_orthography
Amis,Ortho113
...
Pazeh,Ortho113
Siraya,Ortho113
```

- **Value** = an `Orthographies/<scheme>` folder name (the standard used for the
  standard tier). Usually `Ortho113`, free to differ per language.
- **Empty value** = "no standard designated yet" — a supported mechanism.
- **Initial data**: every language maps to `Ortho113`, so behaviour is
  byte-identical to the current hardcoded constant. No real language uses the
  empty value yet; a maintainer blanks a cell later when a language's standard
  is decided (or decided to be absent). We deliberately do **not** pin any
  language (including Pazeh/Siraya) to "no standard" now.

Loaded by `QC/validation/_dialect_inventory.py`, mirroring `_load_dialect_map`.
New public helper:

```python
def standard_orthography(language: str) -> str | None:
    """Designated standard orthography scheme for a language, or None if the
    registry declares no standard yet. Raises for an unknown language."""
```

Keys are `ISO_TO_LANGUAGE.values()`; Truku is not a separate key (it resolves
through the Seediq table's dialect column, as today).

### 2. `add_phonology.py`

In `process_file`, replace the hardcoded `STANDARD_ORTHOGRAPHY` with
`scheme = standard_orthography(language)`:

- `scheme` set (the normal case) -> `load_profile(scheme, language, dialect)`
  for the standard tier. A missing `<scheme>/<Language>.tsv` still prints the
  existing "Standard orthography TSV not found" warning and skips the tier.
- `scheme is None` -> skip the standard tier and print a distinct warning,
  e.g. `No designated standard orthography for <language>; skipping standard
  PHON`.
- The original tier is unchanged (still `--orthography`). Both tiers already run
  independently (no early `continue`); this removes the last hardcoded
  assumption. A file with only an original tier produces only original PHON.

### 3. `standardize.py`

- Rename `--ortho113` -> `--remove_accents`, identical behaviour (copy
  original->standard, then `strip_accents`). Update the flag, mode banner, help
  text, and the mutual-exclusion check
  (`Exactly one of --copy, --remove_accents, or --tsv_path`).
- No registry lookup, no gate. `--tsv_path` works as long as its TSV exists;
  `--copy` and `--remove_accents` run on anything.
- Clean rename; no `--ortho113` alias (no external callers).

## Testing

- **Delete** `test_pazeh_is_a_supported_single_dialect_language` (it tests the
  dialect inventory, unrelated to this change).
- **Unchanged** `test_original_phonology_does_not_require_an_ortho113_table`
  (Pazeh -> Ortho113 -> table missing -> same warning, standard PHON empty).
- **Registry coverage**: every `ISO_TO_LANGUAGE` language has a `standards.csv`
  row.
- **Standard tier uses the designated standard**: a designated-standard language
  (Amis -> Ortho113) produces standard PHON from that table; plus a
  non-Ortho113 case via a monkeypatched registry, proving `add_phonology` uses
  the designated scheme, not a hardcoded `Ortho113`.
- **Runs with only an original tier**: an XML with an original FORM but no
  standard FORM (language that has a standard) -> original PHON via
  `--orthography`, no standard PHON, exit 0.
- **Empty-sentinel path**: monkeypatch the registry to return `None` for a
  language -> `add_phonology` warns and skips the standard tier while still
  producing original PHON.
- **standardize**: rename the two `--ortho113` tests to `--remove_accents`
  (behaviour identical).

All work continues on the `feature/dialect-scoped-phon-rules` worktree branch.
