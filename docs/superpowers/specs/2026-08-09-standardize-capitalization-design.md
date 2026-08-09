# Case-aware standardization: auto-derived capital variants

Date: 2026-08-09
Status: approved

## Problem

`standardize.py` applies conversion-table rules as literal, case-sensitive
`str.replace` calls. A table rule `o→u` does not convert sentence-initial `O`,
so table authors have duplicated rows in both cases (`o→u` plus `O→U`). This
is easy to forget, bloats tables, and produced audit findings #5/#7
(`claudeplans/conversion-table-audit-findings.md`): uppercase rows flagged as
unknown sources because the source-orthography profiles don't list capitals.

The complication: some orthographies use capital letters **phonemically**.
Li's Rukai writes /ʈ/ as `T`, distinct from `t` (the profile
`Orthographies/Li/Rukai.tsv` lists `T`, `D`, `L` as graphemes, and the table
maps `T→tr` with no lowercase `t` row at all). MinEd-style schemes do the
same (`Lh`, `Ch`, `Z`, …). Case handling must not touch those letters.

## Design

### 1. Source-profile resolution from the table filename

Conversion tables follow `<Language>_<Scheme>_113.tsv` (all 40 current tables
conform). When `--tsv_path` is given, standardize.py parses the basename with
`^(?P<language>[^_]+)_(?P<scheme>[^_]+)_113\.tsv$` and resolves the source
profile as `Orthographies/<folder>/<Language>.tsv`, where `<folder>` is:

| scheme token | folder |
|---|---|
| `94` | `Ortho94` |
| `113` | `Ortho113` |
| `113lib` | `Ortho113Liberal` |
| anything else | the token itself (`Church`, `MinEd`, `Li`, …) |

No new CLI argument. If the filename doesn't parse **or** the resolved profile
file doesn't exist, standardize.py prints a prominent warning and performs
**no derivation** — exact status-quo behavior. Rationale: deriving blindly
could clobber phonemic capitals for schemes whose profile is missing
(e.g. `Kavalan_MinEd`, whose MinEd profile is not on disk).

### 2. Case-variant derivation at table-load time

After loading the `(original, replacement)` pairs for the selected target
column (the existing logic in `main`), and before `apply_standard` runs:

- For each rule whose source contains at least one cased letter and is fully
  lowercase, compute up to two variants:
  - **title**: `src[0].upper() + src[1:]` → replacement
    `repl[0].upper() + repl[1:]` (empty replacement stays empty)
  - **ALL-CAPS**: `src.upper()` → `repl.upper()`
    (skipped when identical to the title variant, i.e. single-letter sources)
- A variant is **suppressed** when its source string:
  - already appears as an explicit `original` in the table (explicit rows
    always win), or
  - appears in the `letter` column of the resolved source profile
    (phonemic capital), or
  - equals the lowercase source (nothing to derive).
- Derived variants are inserted immediately after their parent rule so they
  inherit its position in the replacement order. `apply_standard` itself is
  unchanged.

Replacements whose characters have no case (`'`, `ʔ`, `ə`…) pass through
`upper()` unchanged — the variant is still derived (the *source* has case).

### 3. One-time table cleanup (this branch)

Remove an uppercase row from a conversion table **only if** the derivation
machinery, run on the cleaned table, would regenerate the identical mapping —
same source, same replacement, in **every** value column of the row. In
practice:

- Removed: `Amis_94`/`Amis_113lib`/`Amis_Church` `U`/`O` rows (exact
  title-case derivations of `u`/`o`), `Amis_Church G→Ng`,
  `Paiwan_Ferrell Ts→C`, and any others that pass the identity test.
- Kept automatically: every phonemic-capital row (`Rukai_Li T/D/L`,
  `Puyuma_MinEd T/D/Z/R/L`, `Saaroa_MinEd Lh`, …) — their profiles suppress
  derivation, and no lowercase rule regenerates their mappings.
- Kept and flagged for the maintainer: rows where the mapping differs from
  the derivation, notably `Amis_Church Ng→ŋ` (derivation would give `Ŋ`).
  Deciding whether `ŋ` was intentional is a human call, out of scope here.

### 4. Equivalence harness (uncommitted)

Before any table edit is committed, a throwaway script (kept out of git)
verifies behavior preservation per table and per value column:

- Build the **old** rule list (current code, pre-cleanup table) and the
  **new** rule list (derivation-aware code, cleaned table).
- Apply both to synthetic text that exercises every source grapheme of the
  old table — lowercase, title-case, and ALL-CAPS, each in word-initial and
  word-internal position.
- **Hard requirement:** outputs are byte-identical for every input the old
  table handled (all lowercase rules plus all explicit uppercase rows).
- **Report only:** inputs the old table did *not* handle (e.g. `NG` where no
  row existed) that the new code now converts — listed as intended new
  coverage, not failures.

### 5. Committed tests

Unit tests (following the existing `tests/` layout) for:

- filename → profile resolution, including the `94`/`113lib` token mapping,
  a non-conforming filename (warn + no derivation), and a conforming
  filename with a missing profile (warn + no derivation);
- derivation semantics: title + ALL-CAPS generation, single-letter dedupe,
  caseless-replacement passthrough, explicit-row suppression,
  profile-grapheme suppression, insertion order;
- end-to-end: `apply_standard` via `main` on a fixture XML + fixture
  table/profile pair, covering a sentence-initial capital, an all-caps word,
  and a phonemic capital left alone.

## Out of scope

- `validate_conversion_table.py` keeps its case-sensitive model; audit
  findings #5/#7 remain open until it learns the same rule (future branch).
- The `Amis_Church Ng→ŋ` capitalization question (flagged, not resolved).
- The stray `Orthographies/ConversionTables/Saisiyat_folk_113 2.tsv`
  (space in filename, lowercase scheme token) — reported to the maintainer,
  untouched.
- Corpus XML regeneration: this branch changes tooling and tables only.
