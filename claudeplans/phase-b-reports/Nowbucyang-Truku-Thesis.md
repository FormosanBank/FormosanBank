# Nowbucyang-Truku-Thesis regeneration: full diff vs `main` (Phase B batch 2)

Sweep turn executed 2026-08-12 on `sweep/b2-nowbucyang`; **revised the same day**
to carry out the maintainer's rulings (segmentation-retained sentences,
issue #81 parts 2 and 3, second-`clean_xml` removal, duplicate-pair disposition)
— see "Maintainer rulings" below.

The corpus is rebuilt end-to-end by `CodeAndDocs/make_xml.sh`, the single
documented entry point: Phase 1 (`pipeline.py --step build_formosanbank_xml`
from the **committed** `data/processed/` intermediates +
`data/manual/manual_sentences.xml` merge, then the internal structural check) →
Phase 2 (`apply_manual_edits` → `clean_xml` →
`standardize --tsv_path Seediq_94_113.tsv` →
`remove_duplicate_sentences --tier original --apply` → `add_phonology
--orthography Ortho94`). Every FORM/PHON/TRANSL of every S/W/M was matched by
element id against `main` and each difference classified by character-level
edit operations. **0 differences unclassified.**

Key run facts:

- **POL-035**: regenerable — the build runs entirely from committed inputs
  (verified: Phase 1 regenerates `xml_index.csv`, `gloss_alignment_audit.csv`,
  `xml_variant_audit.csv`, `manual_qc_*` byte-identically). No snapshot needed.
- **Idempotent**: a second full `make_xml.sh` run reproduces the published
  file byte-identically (re-verified **after** the second-`clean_xml` removal:
  `apply: 9 edit(s), 0 no-op(s)`; `Removing 5 duplicate <S>`; `Merged 6
  distinct TRANSL(s)` on both runs, same output bytes).
- **standardize `--copy`/`--remove_accents` ruling**: not applicable — this
  corpus standardizes via a conversion table (TSV mode already includes
  accent-stripping, null-unit removal, and C012), so the documented flow
  stands unchanged. Reconciliation documented in the README.
- **Conversion table**: `validate_conversion_table.py Ortho94/Seediq.tsv
  Ortho113/Seediq.tsv Seediq_94_113.tsv --dialect Truku` → **PASS**. The
  `Truku` column carries zero letter conversions (header-only table), so
  standardization = copy + accent strip + de-segmentation.
- **Second `clean_xml` pass**: **removed** from `make_xml.sh` per the
  maintainer's ruling — see "Ruling 4" below. Removal is a byte-level no-op.
- **Quote correction**: Truku's attestation dictionary is deleted (disarmed).
  No `quote_corrections.csv` was produced (make_xml.sh hard-fails if one ever
  appears). Zero apostrophe changes anywhere in the diff.
- **Sidecars (POL-033)**: no `cleaner_warnings.csv` / `standardize_warnings.csv`
  emitted (empty runs write nothing); build dir removed by the script.
- **Pipeline fix**: `scripts/pipeline.py`'s internal step-15 validator
  whitelisted only {FORM, TRANSL, W/M} children and flagged 214 "forbidden
  child PHON" — the whitelist predates `manual_sentences.xml` records carrying
  PHON tiers (which add_phonology regenerates anyway). Fixed to allow PHON;
  internal validation now PASS, and the stale committed
  `validation_report.md` (written when the corpus had 276 S) is refreshed.
- **Wrapper-script cleanup**: `scripts/` carried **16 four-line stubs**
  (`build_formosanbank_xml.py`, `dedupe_examples.py`, … each just
  `from pipeline import main`, relying on `argv[0]` to name the step) —
  wrappers around a wrapper. All 16 deleted; `pipeline.py --step` is now
  **required** and `choices`-validated, and `make_xml.sh` (which already called
  `pipeline.py` directly) is the sole entry point. The three report strings
  inside `pipeline.py` that named a stub now name `pipeline.py --step …`, and
  the two committed reports quoting them (`import_report.md`,
  `xml_quality_review.md`) were updated to match. Also documented in
  `pipeline.py`: `generate_reports` writes a *dev-repo* `README.md` at `ROOT`
  and must never be run inside the published corpus (it would clobber the
  corpus README) — `make_xml.sh` deliberately does not call it.

## Maintainer rulings (2026-08-12)

### Ruling 1 — the 9 segmentation-retained sentences: fixed via `manual_edits.xml`

`C01_E008Bb, C01_E008Cb, C01_E011Fb, C01_E021Ab, C01_E027Ab, C01_E027Cb,
C03_E034b` (automated slash/parenthesis-variant expansions whose gloss
alignment could not carry over) and `C01_E011K, C01_E011L` (hand additions from
`manual_sentences.xml`) have **no W/M tier**. Ruling: they should not have one —
they were never fully glossed — so their **original** tier must carry no
segmentation notation either.

Implemented as a POL-030 record: the nine original FORMs were hand-edited
(`M-gay =ku pila…` → `Mgay ku pila…`), captured with
`QC/utilities/capture_manual_edits.py --corpora_path
Corpora/Nowbucyang-Truku-Thesis/XML --baseline-ref HEAD` into
`CodeAndDocs/manual_edits.xml`, and re-applied as **step 0** of Phase 2 by
`apply_manual_edits.py` (now a real step, not a no-op; changelog
`CodeAndDocs/manual_edits.md`). Per POL-002/003 the capture tool strips
standard FORM and PHON from the records, so each record holds only the original
FORM + its TRANSL and the derived tiers are regenerated by
`standardize`/`add_phonology` downstream.

Verified after the rerun: all nine are **marker-free in original FORM, standard
FORM, original PHON and standard PHON** (0 of 36 tiers contain `-` or `=`), and
the SOFT findings the old state produced are gone — `validate_text` is back to
SOFT 16 (V126 ×4 and V133 ×7 both drop to **0**).

### Ruling 2 — issue #81 part 2: declared-dedup leftovers

The corpus **does** declare a dedup step (`dedupe_examples`,
`dedupe_against_formosanbank`), so POL-022 makes leftovers HARD; but that step's
key is the exact (Truku form, Chinese translation) *pair*. After ruling 1
restores the nine de-segmented standard forms there are **8 within-file
duplicate groups** (the same 8 `main` has). They split cleanly on the
**original** tier, which is why the shared tool is run as
`remove_duplicate_sentences.py by_path --path <build> --tier original --scope
file --apply` rather than with its default standard tier — no new logic:

- **Merged (POL-025): 5 groups.** Identical original FORM, different Chinese
  free translation → the same source sentence twice. The tool deletes the later
  member and merges the TRANSLs the survivor lacks as `ver="alt"`:
  **5 `<S>` removed** (`C01_E025A1`, `C03_E017A`, `C03_E034`, `C03_E039A`,
  `C04_E014A`), **6 TRANSLs merged as `ver="alt"`** (survivors `C01_E009B` ×2,
  `C01_E026B_0080_01`, `C03_E007A`, `C03_E038A`, `C04_E003A`).
  One of the six (`C01_E026B_0080_01`) differs from its survivor's translation
  only by a trailing `。`; the tool's (lang, text) key treats it as distinct, so
  it lands as an `alt`. Noted, not special-cased.
- **Retained deliberately: 3 groups.** They agree only *after* de-segmentation
  — the thesis renders them with different morpheme notation in the two places:
  `Mgay =ku …` / `Mgay ku …` (`C01_E011D` / `C01_E008Bb`), `M-tgsa …` /
  `Mtgsa …` (`C01_E026A_0079_01` / `C03_E034b`), `N-nima …` / `Nnima …`
  (`C03_E012B` / `C04_E002C`). Under POL-022's distinct-provenance nuance these
  are separate attestations of the source's own notation, not pipeline defects,
  so **nothing is done to them** and the residual HARD duplicate finding for
  these three groups is expected. Documented in the corpus README
  ("Duplicates") so a later reader does not "fix" it.
  The `C01_E026A_0079_01` / `C03_E034b` pair — previously surfaced here as an
  open caveat because it differs in *both* segmentation and translation — is
  now **settled**: see Ruling 5.

Note that 2 of the 3 retained groups exist only because of ruling 1 — before
the manual edit those pairs did not share a standard form at all.

### Ruling 3 — issue #81 part 3: V152

Recorded disposition, **no CSV changes made**. V152
(`conversion_table_dialect_unknown`, POL-034 SOFT) fires on
`Seediq_94_113.tsv` and `Seediq_Church_113.tsv` because their value column
`Truku` is not found among `dialects.csv`'s dialect names. That is a **defect
in the V152 rule**, not in the registries: `Truku` is its own language row in
`languages.csv` (`trv` — "covers both Seediq and Truku; dialect=\"Truku\"
resolves to Truku") and has its own `Truku,,,,` row in `dialects.csv`; the
column resolves correctly at run time (`Using dialect-specific column: Truku`)
and `validate_conversion_table.py … --dialect Truku` returns **PASS** with zero
mismatches. Fixing V152 (teach it that a value column may name a language that
`languages.csv` folds into another ISO code) is a separate repo-wide task.

### Ruling 4 — remove the second `clean_xml` pass

The maintainer is systematically removing the post-`standardize` `clean_xml`
pass from every corpus that carries one. Here it was step 3 of Phase 2, labeled
"kept from the historically documented order". **Removed**, along with its
comment; the README's documented pipeline was updated to match and now states
that `clean_xml` runs once and must not be re-added.

The pass historically existed to de-segment the standard tier after
`standardize` re-introduced `- = < >` markers. Consequences, measured by
re-running `make_xml.sh` end-to-end with the pass gone:

- **Output is byte-identical** to the version built with the pass (`diff`
  against the committed file: no differences). The pass was genuinely
  redundant, as the maintainer expected.
- **Zero segmentation markers survive** into any standard S-FORM. A full scan
  of the 278 published sentences finds `-` and `=` **only** in `original`
  S-FORMs (203 and 104 sentences respectively, which is the point of that
  tier); standard S-FORM, original S-PHON and standard S-PHON contain **0**
  occurrences of `-`, `=`, `<` or `>`. `<`/`>` infix brackets do not occur
  anywhere in this corpus at all (0 occurrences across every S/W/M FORM and
  PHON), so the one marker shape C012 does not handle is simply not present
  here.
- **Why C012 suffices**: `standardize.py`'s `_apply_standard_hyphens` strips
  both `-` and `=` from the S-level standard FORM of every sentence that has an
  `<M>` tier; the Bunun/Thao hyphen-is-a-letter exemption does not apply
  (`trv`), so stripping is silent and unconditional. That covers the 269
  morpheme-segmented sentences.
- **The 9 W/M-less sentences**: C012 explicitly no-ops on sentences without an
  `<M>` tier, so it never touches these — they are marker-free because Ruling 1
  rewrote their *original* FORMs via `manual_edits.xml`, and the standard tier
  is copied from that. **Re-verified after the removal**: all nine are
  marker-free in original FORM, standard FORM, original PHON and standard PHON
  (0 of 36 tiers contain `-`, `=`, `<` or `>`). Between C012 (269) and
  `manual_edits.xml` (9), all 278 sentences are covered with no gap.
- **Validators and tokens**: no deltas. `validate_xml` clean → clean;
  `validate_text` SOFT 16 (V116 ×4, V122 ×12) → identical; `validate_glosses`
  HARD 120 (V064) / SOFT 97 (V060 ×14, V065 ×83) → identical; token count
  1,192 → 1,192 (Δ 0).
- **Idempotency preserved**: two consecutive `make_xml.sh` runs after the
  removal produce byte-identical output.

No `clean_xml` pass was re-added and no XML was hand-edited.

### Ruling 5 — duplicate pair `C01_E026A_0079_01` / `C03_E034b`: keep both

**Settled decision, documentation only — no data change.** The pair differs in
*both* its original segmentation (`M-tgsa …` vs the marker-free variant
expansion `Mtgsa …`) and its Chinese free translation. The maintainer ruled to
**keep both members** on exactly that basis: differing on two independent axes
makes them two distinct attestations rather than one sentence recorded twice.

It therefore joins `C01_E011D` / `C01_E008Bb` and `C03_E012B` / `C04_E002C` as
a deliberately-retained group, and the earlier framing of it as "the one group a
future maintainer call could move into the merge category" is withdrawn. The
corpus README's "Duplicates" section states all three retentions as settled and
warns against merging them. The residual HARD duplicate finding remains 3
groups / 6 occurrences, unchanged.

## Comparison scope

Structure vs `main`: 283 → **278 S**, 1,153 → **1,130 W**, 1,451 → **1,424 M**,
2,717 → **2,666 TRANSL**. The only structural removals are the 5 dedup-merged
sentences and the 23 W / 27 M they contained; **nothing else** was added or
removed, and no TEXT attribute changed. TRANSL arithmetic checks out exactly:
2,717 − 57 (carried by the 5 removed S) + 6 (merged as `ver="alt"`) = 2,666.

Token count (corpus counting rules): 1,215 → **1,192, delta −23** — entirely
the 5 dedup-merged sentences.

## Diff classification — 1,797 changes, 100% classified

Each differing text was aligned character-by-character (difflib opcodes) and
every edit operation labeled; a change counts once per element per label.

| class | S | W | M | why expected |
|---|---|---|---|---|
| PHON segmentation dropped (orig / std) | 233 / — | 352 / 352 | 160 / 160 | new `add_phonology` is marker-free (POL-003): `-`, `=` no longer surface in PHON (standard S-PHON already had none — C012 had de-segmented that FORM on `main`) |
| PHON sentence punctuation dropped (orig / std) | 246 / 246 | — | — | same: unmapped punctuation is not sound |
| PHON uvular lowering → `e` (std) | 75 | 80 | 81 | Ortho113 Seediq rules sidecar (4470173f9): `i`/`ə` lower to `e` next to `q`/`ħ` (Truku column) |
| PHON uvular lowering `u`→`o` (std) | — | 9 | — | same sidecar |
| PHON palatal `ʦ`→`c` (std) | 14 | 15 | 15 | same sidecar: `c` is palatal [c] before `i`/`y` |
| PHON syllabic mark `m̩`→`m` dropped (std) | 17 | 4 | 4 | Ortho113 profile recode (no syllabic diacritic) |
| null glyph `Ø`→`∅` (FORM orig+std) | 2 | 4 | 4 | POL-012 canonical null marker (clean_xml) |
| null PHON repaired `*`→`∅` / silent | 2 | 4 | 4 | old pipeline mapped `Ø` to unknown-char `*`; nulls are now silent in PHON |
| **manual edit: original de-segmented** | **9** | — | — | **ruling 1** — the nine W/M-less sentences (`manual_edits.xml`) |
| **dedup: `<S>` removed (+ its W/M)** | **5** | **23** | **27** | **ruling 2** — POL-025 merge of the 5 translation-differing groups |
| **dedup: TRANSL merged as `ver="alt"`** | **6** | — | — | **ruling 2** — the survivors' gained readings |

(One element can carry several labels; column values are label totals per tier.
The standard FORMs of the nine manually edited sentences are **unchanged** vs
`main` — `main`'s old second-`clean_xml` pass produced exactly the same
de-segmented strings that the manual edit now feeds forward from the original
tier.)

## Validators before → after

| validator | main | this branch | delta |
|---|---|---|---|
| validate_xml | clean | clean | — |
| validate_text | SOFT 16 (V116 4, V122 12) | SOFT 16 (V116 4, V122 12) | — (V126/V133 never appear) |
| validate_glosses | V064 HARD 120; V060 14, V065 83 | identical | — (issue #81 linguistic worklist untouched — the 5 merged-away sentences carried no gloss findings) |
| duplicate QC (POL-022 HARD, dedup declared) | 8 groups / 16 occurrences | 3 groups / 6 | −5 groups merged per ruling 2; 3 retained deliberately |
| validate_registries | V152 ×2 | V152 ×2 | — (ruling 3: rule defect, no CSV change) |
| token count | 1,215 | 1,192 | −23 (dedup) |

Removing the second `clean_xml` pass (Ruling 4) moved **none** of these
numbers: measured immediately before and after the removal on this branch,
every validator count and the token count are identical, and the rebuilt XML is
byte-identical.

## Issue #81 claim dispositions

1. **"add M glosses" (V064 ×120, V065 ×83, V060 ×14)** — confirmed exact counts
   on main and unchanged after regen. Source-supported gloss restoration work,
   i.e. a linguistic worklist item for the generator/manual file, **not** part
   of this regeneration turn. Nothing fabricated into the XML.
2. **"declared-dedup leftovers"** — resolved per ruling 2 above: 5 groups
   merged (POL-025), 3 retained deliberately and documented in the README. All
   three retentions are settled, including `C01_E026A_0079_01` / `C03_E034b`
   (ruling 5); nothing is left open.
3. **"Seediq_94_113.tsv route triggers V152; resolve routing first"** —
   resolved per ruling 3 above: V152 rule defect, no CSV change, separate task.

## UNEXPLAINED

None. 1,797/1,797 changes classified (100%), including the two new
ruling-driven categories (`manual_edit_desegment_original`, 9; dedup removals +
alt-TRANSL merges, 66). Rulings 4 and 5 add no change classes: ruling 4 is a
byte-identical build-script simplification and ruling 5 is documentation only.
