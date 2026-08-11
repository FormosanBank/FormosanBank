# Null-morpheme handling across the QC pipeline — design

**Date:** 2026-08-09
**Branch:** `feature/null-morpheme-handling` (based on `feature/shared-source-phonology`)
**Status:** approved design, pre-implementation

## Problem

Linguistic sources mark null (zero) morphemes with a "zero" glyph — attested in
published corpora as lowercase `ø` (NTU Grammar: Sakizaya `ø-sitangah`,
Kanakanavu standalone `ø`) and historically as `Ø` (U+00D8, handled by C012 on
main). The canonical FormosanBank marker is `∅` (U+2205 EMPTY SET). Today, on
`feature/shared-source-phonology`:

- clean_xml C012 deletes only `Ø` from the standard S-level FORM; `ø` and `∅`
  are untouched.
- add_phonology has no null handling at all: `∅` (category Sm) falls through
  `phonologize()`'s final filter and becomes `*`; `ø` becomes `*` too.
- Nothing validates that a null morpheme in a W-level FORM is represented in
  its M children.
- Unmapped punctuation is copied verbatim into PHON.

A separate hazard: the same glyphs appear as **real letters in foreign proper
nouns** (Danish/Norwegian `Grønland`, `Børn`, `Støre` in Amis, Seediq, Atayal,
and Sakizaya Wikipedia articles). Any null-marker logic must not touch those.

## Scope

Null-morpheme handling plus PHON punctuation hygiene, on top of
`feature/shared-source-phonology`. Explicitly **out of scope**: moving
segmentation stripping (C012's `-`/`=` job) from clean_xml into standardize.py
— that migration happens on a different branch. This branch only makes the
minimal C012 change nulls require (see §2).

## Interaction with the pre-existing null-rule family (V120/V123–V125/V140)

`QC/validation/rules/text.py` had a null-rule family (V120, V123–V125, V140)
before this branch. Two decisions required post-review (2026-08-09):

**V120 downgraded HARD → SOFT.** V120 flags `∅` in S-level standard FORM. Before
this branch, `ø`/`Ø` in S-standard was invisible to V120 (both are not U+2205).
After this branch, clean_xml normalizes them to `∅` in all tiers, and only
non-`--copy` standardize removes them from S-standard. For `--copy` corpora
(e.g. NTUFormosanCorpus, the spec's primary data-impact example), `∅` persists
legitimately in S-standard: the `--copy` design explicitly preserves it as a
"heads-up, re-standardize with a TSV" signal. Keeping V120 HARD would newly
hard-fail that corpus's canonical QC pipeline. V120 is therefore SOFT: a warning
to re-standardize when convenient, not a blocker.

**V069 kept alongside V125 (both intentional).** V125 (text-level, HARD) requires
that *some* M FORM *contain* `∅` (substring) and that the S-level original FORM
also contain `∅`. V069 (gloss-level, HARD, added by this branch) is stricter on
the M side: the M FORM must be *exactly* `∅` in standalone morpheme position.
V069 is also silent on the S-original requirement. The two rules intentionally
coexist: V125 is the text-validation anchor that fires across all corpora in
`validate_text.py`; V069 adds finer-grained morpheme-position enforcement in
`validate_glosses.py`. Docstrings in both functions cross-reference each other.

## Addendum: merge with feature/standardize-owns-standard-cleaning (2026-08-10)

This branch merged in `feature/standardize-owns-standard-cleaning`, which moves
C012 (standard-tier hyphen handling) from clean_xml into standardize.py and
stops clean_xml touching the standard tier entirely. Three maintainer rulings
resolved the cross-branch contradictions:

1. **Dash policy reversed** (supersedes "Hyphen vs dash" below): ALL dash and
   hyphen look-alikes (U+2010, U+2011, U+2012, U+2013, U+2014, U+2015, U+2212,
   U+FE58, U+FE63, U+FF0D) canonicalize to ASCII `-` in `swap_punctuation`.
   Rationale: much of the corpus text is OCRed, so a source's hyphen-vs-dash
   choice is not principled; standardize to one character and let context
   decide. The protections against mangling move downstream: standardize's
   C012 strips `-` from S-level standard FORMs only in morpheme-segmented
   sentences (S has an M descendant) and keeps digit-flanked `-` (dates,
   verse ranges) everywhere.
2. **`--copy` is a pure duplication** (this spec's §3 policy wins): no C012,
   no null-unit removal in copy mode. A `--copy` corpus's standard tier keeps
   segmentation hyphens and null units; V120 (SOFT) and V133 (SOFT) flag them
   as "re-standardize when a conversion table exists" signals.
3. **Null-morpheme handling retained in full** (§§1, 3–6 unchanged in effect):
   the C012 ported into standardize.py lost its legacy `Ø-|-Ø|Ø` deletion
   (removal lives only in `remove_null_units`, which runs before C012 in
   non-copy modes), and its hyphen stripping skips `∅`-adjacent hyphens as
   defense in depth. §2's clean_xml C012 changes are superseded: clean_xml no
   longer has C012 at all, and glyph normalization applies to the original
   tier (S/W/M); the standard tier inherits it via `create_standard`'s copy.

## Design

### Definitions

- **Null markers**: `ø` (U+00F8), `Ø` (U+00D8), `∅` (U+2205). Canonical: `∅`.
- **Morpheme position**: a marker occurrence whose both neighbors are a string
  edge, whitespace, or ASCII hyphen-minus `-`. This matches all attested
  null-marker data (`ø-sitangah`, `bangcal-Ø`, standalone `ø`) and excludes
  all attested foreign-letter data (`Grønland`: letters on both sides).
- **Null unit**: the marker together with one bridging segmentation hyphen —
  `∅-`, `-∅`, or standalone `∅`. Removal always operates on units so no
  dangling hyphen is left (matters for Bunun/Thao, where `-` is a letter).
- **Hyphen vs dash**: segmentation is ASCII `-` (U+002D) only. Typographic
  dashes (`–` U+2013, `—` U+2014, `－` U+FF0D, `−` U+2212) are punctuation in
  the corpora (verse ranges `8:1–19:14`, parentheticals) and are never
  segmentation. All 130 repo TSVs contain only U+002D (verified 2026-08-09).

### 1. clean_xml.py — glyph normalization (all tiers, all levels)

In the per-FORM cleaning pass (which already visits every FORM element:
S/W/M, original and standard), normalize each null marker in morpheme
position to `∅`. The original tier is included deliberately: the marker glyph
is annotation, not source spelling, so canonicalizing it keeps the tier
faithful (per the original-tier convention that annotation fixes are
expected).

Also normalize the look-alike hyphens U+2010 HYPHEN and U+2011 NON-BREAKING
HYPHEN to ASCII `-`. Both have zero occurrences in the corpora today; the
rule pins the invariant "anything hyphen-shaped that means segmentation is
U+002D". Dash punctuation (`–`, `—`, `－`, `−`) is NOT converted — converting
it would fabricate segmentation and mangle ranges when hyphens are stripped.

### 2. clean_xml.py — C012 stops deleting nulls

C012 (`_process_standard_hyphens`) loses its null-deletion regex
(`Ø-|-Ø|Ø`). Null removal now lives in exactly one place (standardize.py,
§3); C012 deleting them too would defeat the `--copy` exception whenever
clean_xml re-runs after standardization.

C012 keeps its segmentation-stripping job on this branch (the migration to
standardize.py is another branch's work), so to avoid fusing `∅-dhuq` into
`∅dhuq` when it strips hyphens, its hyphen stripping skips hyphens adjacent
to `∅` — the null unit survives intact for standardize.py to remove. This is
a minimal, commented change so the other branch's migration can carry it
along with the rest of the function.

### 3. standardize.py — remove nulls from S-level standard FORM

In all modes except `--copy` (i.e. `--remove_accents` and TSV mode),
immediately after `create_standard` copies original → standard and **before**
`apply_standard` runs letter mappings: for **S elements only**, remove null
units from the standard FORM, collapsing any doubled whitespace. Running
before any other transformation guarantees the bridging hyphens still exist,
so units are recognizable.

W and M elements are never touched: their standard FORMs retain `∅` (the
morpheme tier is where a null is meaningful). `--copy` mode remains a pure
duplication — its standard tier keeps null units.

### 4. validate_glosses.py — new rule V069 (HARD)

`v069_null_morpheme_in_W_requires_null_M`, modeled directly on V066 (clitic
propagation): if a W's preferred FORM contains a standalone `∅` (morpheme
position) and the W has at least one M child, then at least one child M FORM
(any kindOf) must be exactly `∅`. No-op for Ws without M children (V061
covers M counts). Registered in `QC/validation/rules/gloss.py::RULES`.

### 5. add_phonology.py — null morphemes are silent

In `phonologize()`, uniformly for every tier and level (uniformity also
covers `--copy` corpora, whose standard S tier legitimately retains nulls):

- If the whole FORM text (stripped) is `∅` → return `∅`. PHON is never empty
  (empty tiers trip validators); a visible `∅` states "this morpheme is
  silent". This is the M-level case.
- Otherwise remove null units (`∅-`, `-∅`, `∅`) before the grapheme
  tokenizer, so PHON is clean IPA with no `*` residue.
- Only canonical `∅` is treated as null here. `ø`/`Ø` normalization is
  clean_xml's job; a Danish `ø` reaching phonologize follows the normal
  unknown-letter path (`*`), never silent deletion.

### 6. add_phonology.py — unmapped punctuation deleted from PHON

In `phonologize()`'s final character filter, punctuation — ASCII
`string.punctuation` and Unicode category P — that is not in the profile's
IPA character set is deleted instead of copied through. Mapped punctuation
(e.g. orthographic `'` → `ʔ`) is consumed by the tokenizer before the filter
and is unaffected. Whitespace, combining marks (category M), and the `*`
unknown-character convention are unchanged. Example: `kaku, ca'ay.` →
`kaku ʦaʡaj`. Typographic dashes in FORM text are punctuation and disappear
from PHON here.

## Data impact

- NTU Grammar Sakizaya (12 `ø`) and Kanakanavu: markers normalize to `∅` on
  the next cleaning run; standard S tiers lose them on the next
  standardization; W/M tiers keep them.
- Amis/Seediq/Atayal/Sakizaya Wikipedia files: `Grønland`/`Børn`/`Støre`
  etc. are letter-adjacent, untouched by every rule above.
- No corpus data is edited on this branch; the tooling handles data on its
  next run.

## Testing

- **clean_xml**: each glyph normalizes at word start / word end / standalone
  / hyphen-bridged, in original-tier and W/M FORMs; `Grønland` and `Børn`
  survive in all tiers; C012 no longer deletes `∅`; null-adjacent hyphen
  survives C012 while ordinary segmentation hyphens are still stripped;
  U+2010/U+2011 → `-`; `–`/`—`/`－`/`−` pass through unconverted.
- **standardize**: S-level standard loses `∅-x`, `x-∅`, standalone `∅` in
  TSV and `--remove_accents` modes; `--copy` retains; W-level and M-level
  standard FORMs retain `∅` in every mode.
- **validate_glosses**: V069 fires (HARD) when W has `∅` but no `∅` M child;
  passes when one exists; no-ops without M children.
- **add_phonology**: all-null M FORM → PHON `∅`; `∅-fangcal` → clean IPA
  with no `*`; Danish `ø` is not deleted (becomes `*` via the normal path);
  unmapped punctuation absent from PHON; a profile that maps `'` still maps
  it; whitespace preserved.
