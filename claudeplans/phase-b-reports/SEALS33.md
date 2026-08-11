# Phase B regeneration report — SEALS33 (round 2, rerun under 2026-08-11 rulings)

**Date:** 2026-08-11 · **Branch:** `sweep/g1-seals33` · **Group:** 1
**Corpus:** `Corpora/SEALS33` — 2024 SEALS conference website translations.
Seediq (`trv`, dialect="unknown", 29 S) and Saisiyat (`xsy`, 29 S). No audio,
no W/M segmentation. README-declared orthography: Ortho94 on the original tier.

This report supersedes round 1. Changes from round 1: `standardize.py
--remove_accents` replaces `--copy` (copy + accent deletion + S-level
null-unit removal); the whole pipeline is wrapped by a new committed
`CodeAndDocs/make_xml.sh`; the three unrelated UDHR translation files in
`CodeAndDocs/` are deleted.

## 1. POL-035 snapshot: TAKEN (before any cleaning)

The XML was hand-assembled by copy-and-paste from the conference website —
non-regenerable from source. Pristine `XML/` was snapshotted to
`CodeAndDocs/pre_correction_snapshot/XML/` before any pipeline step and
verified byte-identical to the git-HEAD XML (`diff -r`). Documented in the
corpus README. Per POL-038, `make_xml.sh` rebuilds `XML/` from this snapshot;
no data file is ever hand-edited.

## 2. Pipeline: new `CodeAndDocs/make_xml.sh` (executable, committed)

All post-scrape steps in order, FormosanBank root parameterized
(arg / `FORMOSANBANK_ROOT`, default = the checkout the corpus lives in;
`PYTHON` overrides the interpreter, default = root `.venv`):

0. restore `XML/` from the POL-035 snapshot (idempotence; explained in one
   line in the README as the pipeline's starting point)
1. `QC/cleaning/clean_xml.py`
2. `QC/utilities/standardize.py --remove_accents`
3. `QC/utilities/add_phonology.py --orthography Ortho94`

Per the 2026-08-11 ruling (no spurious no-op steps), the `apply_manual_edits`
step present in the earlier round-2 state was removed from both the script and
the README — this corpus has no `manual_edits.xml`.

`add_phonology` verified **idempotent** (second run byte-identical, md5).

## 3. Deletions performed

- `CodeAndDocs/Amistranslation` — UDHR in Amis (unrelated to SEALS33)
- `CodeAndDocs/Englishtranslation` — UDHR in English
- `CodeAndDocs/Mandarintranslation` — UDHR in Mandarin
- `Corpora/SEALS33/cleaner_warnings.csv` — stale committed sidecar
  (24 historical c022 rows; POL-033 violation), removed again

`CodeAndDocs/requirements.txt` (old dev-repo mirror) was left in place —
round-1 non-blocking observation stands; no ruling to delete it.

## 4. Warning sidecar (POL-033: summarized, then deleted)

`XML/cleaner_warnings.csv`, 97 rows — identical to round 1:

| rule | count | detail |
|---|---|---|
| c022 (unexpected `*` in FORM) | 6 | S25 in both files: reconstructed proto-forms `*-ʔ, *-h, *-∅` in one talk title (3 asterisks × 2 files) |
| c030 (ambiguous apostrophe, audit flag) | 91 | Saisiyat only: S7 ×35, S9 ×52, S27 ×4 |

No `standardize_warnings.csv` was produced (no C012-eligible sentences —
corpus is unsegmented). Sidecars reviewed and deleted; nothing committed.

## 5. Quote-correction expectations — all CONFIRMED

- **Seediq/Truku disarmed** (dictionaries deleted): no quote evaluation for
  the Seediq file; the `'Tayal` loan-autonym apostrophes (S16, S26) survived
  untouched — **4 occurrences after regen, 4 in the snapshot** (original +
  standard tiers).
- **Saisiyat armed: 0 rewrites.** No `quote_corrections.csv` was created
  anywhere; **0 c031/c032 rows**. The c030 flags land on exactly the 3
  sentences / 91 apostrophes predicted by Phase A REV 2
  (`claudeplans/phase-a-reviews/Saisiyat.md`). Would-be corrections file
  location (CodeAndDocs/, form_before/form_after) is moot — none produced.
- **UNEXPLAINED: none.**

## 6. Diff audit vs git HEAD — 100% classified

Element-by-element comparison, all 58 S × both files (scripted, not sampled).
Unchanged: all 58 original FORMs, 49/58 standard FORMs, 36/116 PHONs, all 90
TRANSLs, all TEXT/S attributes, S id set, child-element multisets.

**Changed values: 91 — every one classified, 0 UNEXPLAINED (100% ≥ 99.9%):**

| class | count | notes |
|---|---|---|
| XML declaration serializer rewrite | 2 | one per file |
| **Standard FORM rederived — accent removal (`--remove_accents`)** | 9 | 7 = pure copy of the (unchanged) original, restoring hyphens/`- ` bullets the old pipeline had stripped (V133 SOFT signal, by design); 2 = copy minus the S25 null unit (`*-∅` → `*`, one per file). The originals carry no accents, so accent *deletion* contributed zero character changes — the class is copy + null-unit removal here. |
| PHON regenerated (shared-source generator) | 80 | 40 per tier; every value reconciled mechanically (normalization + SequenceMatcher opcodes, per-instance FORM cross-checks); 0 residual substitutions |

PHON sub-effects within the 80:

| sub-effect | count | verification |
|---|---|---|
| legacy `x~y` → `[x|y]` variant notation | 142 occurrences | Saisiyat `s~θ`, `z~ð` |
| punctuation dropped from PHON | 66 values | `. , ; ( ) " - ' / ?` and, Seediq only, `:` (vowel length in Saisiyat — retained there) |
| S25 null glyph: old PHON's `*`-for-`∅` no longer emitted | 4 (2 tiers × 2 files) | new PHON emits nothing for `∅` (original tier still has `∅` in FORM; standard tier's `∅` was removed from FORM by `--remove_accents`); source-text asterisk counts otherwise identical |
| Seediq `ey` original tier → `əj` (`j` inserted after `ə`) | 10 instances | each machine-checked against an `ey` in the FORM (`peeyah`, `snlmeyan`, …) |
| Seediq `ey` standard tier → `e` (digraph profile; old emitted bare `ə`) | 10 instances | same per-instance FORM cross-check |

Difference vs round 1 (both expected): (a) the 9 rederived standard FORMs now
include the 2 S25 null-unit removals (round 1's `--copy` kept `∅` in the
standard tier); (b) accordingly V120/V116 drop (below) and the standard-tier
PHON no longer sees a null at all.

## 7. Token counts and validators

| metric | before (HEAD) | after | Δ |
|---|---|---|---|
| tokens Saisiyat | 604 | 604 | **0** |
| tokens Seediq (dialect unknown) | 560 | 560 | **0** |
| validate_xml | 0 issues | 0 issues | — |
| validate_text HARD | V129 ×4 | V129 ×4 | 0 (pre-existing: S25 proto-form asterisks, faithful to source) |
| validate_text SOFT | 221 | 193 | −28 |

SOFT movement: **V147 30→0** (legacy PHON tildes eliminated — the sweep's
target metric), V114 3→0 (old standard tier's double spaces gone),
V120 2→0 (null units removed from the standard tier by `--remove_accents`),
V116 4→2 (the two standard-tier `∅` glyphs gone; the original-tier pair
remains, faithful), V133 0→+9 (designed dash-restoration signal),
V122 170 / V137 12 unchanged.

## 8. README

Rewritten: stale dev-repo instructions (clone Formosan-SEALS, `Final_XML`,
`raw_data`, "Paiwan" note) replaced with the published layout, the
`make_xml.sh` wrapper **plus the per-step explanations** (kept per ruling),
the POL-035 snapshot + POL-038 note, quote-correction status, sidecar policy,
and the S25 / vowel-length caveats.

Trimmed per the 2026-08-11 README content policy: the no-op manual-edits step,
run-report specifics in the quote-correction note (c030 counts/sentence IDs),
and the V129 validator citation in the S25 caveat. What remains is corpus
description, source, the current three-step pipeline with per-step
explanations, the snapshot note, and reproduction instructions.

## 9. Observations for the maintainer (non-blocking)

- `CodeAndDocs/requirements.txt` still mirrors the old dev repo and is not
  needed by `make_xml.sh` (which uses the repo `.venv`); delete at will.
- GitBook corpus-page update (per-corpus procedure step 9) deferred to
  post-merge with the other closing steps.

**UNEXPLAINED items: none.**
