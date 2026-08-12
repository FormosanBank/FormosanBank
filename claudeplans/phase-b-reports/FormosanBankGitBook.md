# FormosanBankGitBook regeneration: full diff vs sweep tip (Phase B, Group 1 — ROUND 2)

Round-2 sweep turn executed 2026-08-11 on branch `sweep/g1-gitbook` (reset to
sweep tip `fa125f1e4`, pristine XML), redoing round 1 under the updated
maintainer rulings: **`standardize.py --remove_accents` replaces `--copy`**,
and the post-scrape pipeline is now wrapped by a new executable
**`CodeAndDocs/make_xml.sh`** (which this run used, proving it works):
`clean_xml` → `standardize --remove_accents` →
`add_phonology --orthography Ortho113`.

**Fixup (2026-08-11 overnight rulings)**: `apply_manual_edits` removed from
`make_xml.sh` and the README (no manual edits exist for this corpus — no
spurious no-op steps); README trimmed to current-pipeline/data-user content
only (legacy u→o provenance note and meta-rationale prose removed). The
updated `make_xml.sh` was re-run over the committed XML: **byte-for-byte
no-op** (idempotent), and validate_xml (clean) / validate_text (37 SOFT:
V122 ×34, V133 ×3) are unchanged.

Element-by-element comparison of every FORM/PHON/TRANSL of every S element
against git HEAD (`fa125f1e4`), matched by (file, S id). **0 differences
unclassified** — every change is in a named category below.

## Comparison scope

- 102 S elements across 6 files, identical structure both sides (no S added
  or removed; corpus has no W/M tiers).
- Tiers compared: FORM original (102), FORM standard (102), TRANSL (204:
  zho + eng per S), PHON (none existed on `main`).

## POL-035 snapshot: NOT required (verified)

The corpus has a runnable reproduction pipeline — verified this round:
`CodeAndDocs/process_raw.py` regenerates XML from the committed
`CodeAndDocs/raw_data/` (and sets `dialect="Eastern"` itself), and the new
`CodeAndDocs/make_xml.sh` runs every post-scrape step. (Additionally, the
original tier was byte-identical after the run — nothing to snapshot
against.)

## make_xml.sh (new this round)

`CodeAndDocs/make_xml.sh`, executable, runs the three post-scrape steps in
order over the corpus's `XML/` directory. Paths resolve from the script's
own location, so it works from any cwd; the FormosanBank repo root is a
parameter (`./make_xml.sh [FB_ROOT]`) defaulting to the repository
enclosing the corpus (`git rev-parse --show-toplevel`); `PYTHON` env var
selects the interpreter (default: the FB root's `.venv` python when
present, else `python3`). The README keeps the per-step prose as the
reference; make_xml.sh is the executable form. This regeneration was
produced by running it (with `PYTHON` pointed at the shared checkout's
venv, since the worktree has no `.venv` of its own).

## Pipeline step outcomes

| step | outcome |
|---|---|
| `clean_xml.py` | **content no-op** — zero warnings, no `cleaner_warnings.csv` created, no `quote_corrections.csv` created (Paiwan armed: 131-entry edge-filtered attestation dictionary present) |
| `standardize.py --remove_accents` | rewrote the standard tier as a copy of original; accent deletion and null-unit removal had **zero targets** (see classes 1 and 3); no `standardize_warnings.csv` created |
| `add_phonology.py --orthography Ortho113` | added 204 PHON elements (see class 2) |

Per POL-033 there were no warnings sidecars to review or delete — neither
`cleaner_warnings.csv` nor `standardize_warnings.csv` was created (zero
warnings), which is itself the per-run report content: empty.

## Expected differences (100% of the diff, with counts)

### Class 1 — FORM standard tier: legacy u→o substitution reverted (99 S, 846 chars)

99 of 102 standard FORMs changed; the other 3 were already identical to
their originals (no `u` in them). Every changed value satisfies, character
for character:

- new standard == original tier text, and
- old standard == new standard with `o` substituted at (a subset of) `u`
  positions — 846 `o`→`u` character reverts in all, and **no other
  character-level difference of any kind**.

Identical to round 1's class 1 (same 99 S, same 846 characters) — expected,
since `--remove_accents` reduces to a pure copy on this corpus (class 3).
Provenance (established in round 1, unchanged): the published standard tier
was produced by the legacy no-TSV standardize default (blanket u→o), never
documented in the README, which even asserted standardize "makes no
changes". Ruling: documented flags win; the u→o is reverted. (Per the
fixup rulings the provenance lives here in the report, not in the README.)

Example (Contributing_to_FormosanBank S0):
- old: `kemoda itjen a posaladj toa FormosanBank?`
- new: `kemuda itjen a pusaladj tua FormosanBank?` (== original)

### Class 2 — PHON tiers added (102 original + 102 standard)

`main` had **no PHON anywhere** in this corpus. The regeneration adds one
PHON per FORM (204 total), generated from the Ortho113 Paiwan profile
(dialect column: Eastern). Conventions verified:

- punctuation not carried into PHON (commas, periods, `?`, `:` absent);
- no legacy `x~y` variant notation anywhere (fresh generation, current
  profile);
- unmapped characters surface as `*`: **70 occurrences in 46 PHON values**,
  all traced to digits, `%`, and Latin loanwords/proper nouns
  (`FormosanBank`→`*urmusanbank`, `NSF`→`ns*`, `XML`→`*mɭ`,
  `CC-BY-4.0`→`ʦʦbj**`, year/number digit runs → `*`);
- FORM↔PHON alignment: every letter-bearing FORM token has a PHON token.
  Two sentences (FormosanBank.xml S5, S24) have a free-standing `:` token
  in FORM; PHON drops it (punctuation convention), so a naive
  whitespace-split count differs by exactly 1 there — classified under this
  class, not a misalignment. (Round 1's blanket "word counts align in every
  element" glossed over these two.)

### Class 3 — accent removal (`--remove_accents`): **0 members** (the round-2 delta, measured empty)

The ruling's new flag copies original→standard AND deletes accents and
removes null-morpheme units. Measured on this corpus:

- accented/diacritic-bearing characters in any FORM: **0** (verified by NFD
  decomposition over all 6 files);
- null glyphs (`∅`/`ø`/`Ø`): **0**;
- C012 hyphen handling inside `--remove_accents` only fires on
  M-segmented sentences; this corpus has no W/M tier, so the three English
  hyphens (`open-source`, `CC-BY-NC`, `CC-BY-4.0`) are untouched (V133
  baseline unchanged, see below).

Consequently `--remove_accents` ≡ `--copy` here: **new standard == new
original byte-for-byte on all 102 S**, and the round-1 diff classes carry
over exactly.

### Class 4 — serialization convergence (4 files: XML declaration + trailing newline)

Contributing_to_FormosanBank, FormosanBank, Formosan_Languages, and
Terms_of_Use had `<?xml version='1.0' encoding='UTF-8'?>` and a trailing
newline at HEAD; the pipeline's writer (standardize/add_phonology
`prettify`) emits `<?xml version="1.0" ?>` and no trailing newline — the
form Welcome and Contributors already had. Purely mechanical writer
convergence; no content in these lines. **Correction to round 1**, whose
report claimed "XML declaration … unchanged": the two declaration styles
were already present at round 1's HEAD (`ef1ebb621`; `fa125f1e4` did not
touch this corpus's XML), so round 1's serialization claim was inaccurate —
the same convergence must have been in its diff too.

### Classes with zero members (verified, not just absent)

- **FORM original tier: 0 changes** — byte-identical on all 102 S.
- **TRANSL: 0 changes** (204 translations compared).
- **Dash/quote/tilde canonicalization (C001/C002/C029), entity decoding
  (C028), null glyphs: 0** — clean_xml made no content changes.
- Raw git diff audit: after removing `<PHON` insertions and
  `FORM kindOf="standard"` line replacements, the only remaining +/- lines
  are the class-4 declaration/trailing-newline lines — no indentation or
  attribute changes anywhere.

## Quote corrections (Paiwan armed)

Paiwan is armed (`QC/validation/reference/Paiwan/attestation.txt`, 131
entries post edge-filter) and Phase A predicted **0** corrections for this
corpus (its single apostrophe is the word-internal glottal in `pu'ui`,
Contributing_to_FormosanBank S25). Confirmed: **no
`CodeAndDocs/quote_corrections.csv` was created — 0 c031/c032 rows** (the
new location/columns per the round-1 review commit were therefore not
exercised). The apostrophe in `pu'ui` is untouched in original and
standard, and appears as `ʔ` (`puʔui`) in both PHON tiers.

## Token count and validators

- **Token delta: 0** — `count_tokens.py`: Paiwan/Eastern 1,855 before and
  after (standard-tier u↔o substitutions don't alter tokenization).
- **validate_xml**: clean before, clean after (6 files, 0 issues).
- **validate_text**: identical before and after — 37 SOFT
  (V122 parens_slashes_anywhere ×34, V133 dash_in_S_standard_FORM ×3);
  findings CSVs identical modulo the line-number column (inserted PHON
  lines). The V133 dashes are the hyphens in `open-source` / `CC-BY-NC` /
  `CC-BY-4.0` (English tokens), pre-existing and expected to persist (no
  M tier → no C012 in `--remove_accents`).

## README

Rewritten to the published layout (`XML/` paths) with:

- **`make_xml.sh` documented** as the executable form of the post-scrape
  pipeline, with the per-step prose retained as the reference (per the
  ruling);
- standardize step updated to **`standardize --remove_accents`** (with what
  it does: copy + accent deletion + null-unit removal; both empty here);
- the quote-correction arming note (armed, 0 corrections,
  `CodeAndDocs/quote_corrections.csv` as the would-be log location);
- the `*` unknown-char note under add_phonology;
- the stale `add_dialect.py` step dropped (script doesn't exist in
  `CodeAndDocs/`; `process_raw.py` sets `dialect="Eastern"` itself).

Per the fixup rulings, the README carries **no** `apply_manual_edits` step
(no manual edits exist), no legacy u→o provenance note, and no
refactoring/sweep rationale — only what the corpus is, its source, the
current pipeline with per-step explanations, and how to reproduce. (The
u→o provenance remains documented in this report, class 1 above.)

POL-038 compliance: no data file was hand-edited; all XML changes were
produced by the committed pipeline (`make_xml.sh`).

## UNEXPLAINED — blocks merge

None. 100% of changed values classified (846/846 standard-tier character
edits; 204/204 PHON additions; 4/4 serialization lines; 0 changes in all
other tiers; accent-removal class measured empty).
