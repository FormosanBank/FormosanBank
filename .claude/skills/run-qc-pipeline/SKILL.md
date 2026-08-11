---
name: run-qc-pipeline
description: Run the canonical QC pipeline on a Formosan-<CORPUS> dev repo. Sequences clean_xml → orthography_detector (HUMAN INPUT) → standardize → add_phonology → validators, producing a README-style summary at the end. Use when a corpus dev repo needs QC before porting into FormosanBank.
---

# run-qc-pipeline

Run the full QC sequence on a corpus development repo, pausing for human judgment at orthography detection. **Operates in `Formosan-<CORPUS>/` dev repos**, not in published `FormosanBank/Corpora/<Name>/` trees.

## Inputs (gather via `AskUserQuestion` if missing)

- `corpus_path` — default current working directory. Should be a `Formosan-<CORPUS>/` dev repo root.
- `output_dir` — default `<corpus_path>/qc-output/<UTC-timestamp>/`.
- `xml_subdir` — auto-detect from common patterns (`XML/`, `Final_XML/`, `xml/`, root-level `*.xml`). If ambiguous, ask.
- `formosanbank_path` — default sibling `../FormosanBank/`. Required because the QC scripts live there.

## Pre-checks

1. Verify `corpus_path` exists and contains XML files (under `xml_subdir`).
2. Verify `formosanbank_path/QC/cleaning/clean_xml.py` exists.
3. Verify `corpus_path/.venv/bin/python3` exists; if missing, refuse and direct the user to `setup-new-dev-repo` or to create a `.venv` manually.
4. Create `output_dir`.

## Recipe phases

All `python3` invocations use `<corpus_path>/.venv/bin/python3` (not the system python). All script paths are relative to `<formosanbank_path>`.

### Phase 0: Apply manual edits

Re-apply any recorded hand edits before cleaning, so later phases see them. No-op (and prints so) if the corpus has no `CodeAndDocs/manual_edits.xml`.

```bash
.venv/bin/python3 <formosanbank_path>/QC/cleaning/apply_manual_edits.py \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/00_apply_manual_edits.log
```

This phase must run on freshly built (pre-manual) XML. Any `NO-OP manual edit (KEPT)` warnings in the log mean the fresh build already contains that record's content — the upstream build likely absorbed the fix. Surface them in the summary; if the maintainer confirms the records are obsolete, re-run with `--prune` to remove them (never prune without confirmation).

### Phase 1: Clean

```bash
.venv/bin/python3 <formosanbank_path>/QC/cleaning/clean_xml.py \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/01_clean_xml.log
```

No decisions. Capture log. Two normalizations here are **expected behavior,
not data loss** (cite POLICIES.md POL-010/011/012 if the operator or a later
audit questions them): all dash/hyphen look-alikes and typographic
apostrophes/quotes canonicalize to ASCII, and null-morpheme glyphs `ø`/`Ø`
in morpheme position canonicalize to `∅`. A `cleaner_warnings.csv` may
appear next to the XML — it is a per-run report (POL-033): read it into the
summary, do not commit it.

### Phase 2: Orthography detection (HUMAN JUDGMENT REQUIRED)

Run the detector. Note: `orthography_detector.py` takes the XML path as a positional argument (no `--corpora_path` flag) and defaults to analyzing the **original** tier — which is what we want at this stage, before Phase 3 creates the standard tier.

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/orthography_detector.py \
  <xml_path> 2>&1 | tee <output_dir>/02_orthography_detector.log
```

The detector's output is interpretive — it doesn't give a clean answer. Read the log, then use `AskUserQuestion` to ask the user what the corpus's original orthography is. Phrase the question with the detector evidence as context. Offer answer options derived from what the detector suggested, plus an "Other (specify)" fallback for orthographies not in the obvious candidates.

Common candidate orthographies (refine based on what the detector suggests): `Ortho113`, `Ortho94`, `Church`, `MinEd`, `Folk`, `Ferrell`, `Huang`, `Montgomery`.

**Store the answer** for Phase 3.

### Phase 3: Standardize

First check the language's designated standard orthography in
`<formosanbank_path>/standards.csv`. A **blank** scheme cell means "no
standard designated yet" — standard-tier PHON will be deliberately skipped
in Phase 4; note that in the summary so it doesn't read as a failure.

If the user's answer was **Ortho113**:

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/standardize.py \
  --copy --corpora_path <xml_path> 2>&1 | tee <output_dir>/03_standardize.log
```

`--copy` is pure duplication: segmentation hyphens and null units stay in
the standard tier, and V120/V133 will flag them SOFT in Phase 5 — that is
the designed "re-standardize when a conversion table exists" signal, not a
defect.

Otherwise, resolve the TSV mapping path. The convention is
`Orthographies/ConversionTables/<Language>_<Scheme>_113.tsv` (e.g.
`Puyuma_Cauquelin_113.tsv`). The filename matters beyond lookup:
`standardize.py` resolves the source orthography profile from it to derive
Title/ALL-CAPS variants of lowercase rules — a non-conforming name prints a
warning and skips capital-variant derivation. **If the mapping path is
ambiguous, surface to user before proceeding.**

Before trusting a table (especially a new or recently edited one), validate
it:

```bash
# positional args: <source-profile.tsv> <target-profile.tsv> <table.tsv>
# e.g. Orthographies/Cauquelin/Puyuma.tsv Orthographies/Ortho113/Puyuma.tsv \
#      Orthographies/ConversionTables/Puyuma_Cauquelin_113.tsv
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_conversion_table.py \
  <source_profile_tsv> <target_profile_tsv> <mapping_tsv> \
  2>&1 | tee <output_dir>/03a_validate_conversion_table.log
```

Unresolved mismatches or crashes here mean the standard tier will be built
from a defective mapping — surface to the user before running standardize.

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/standardize.py \
  --tsv_path <mapping_tsv> \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/03_standardize.log
```

(Omit `--target_column`: standardize auto-selects the value column from the
TEXT's dialect for multi-dialect languages, falling back to `standard`.
Pass it only when the log shows the wrong column was chosen.)

After standardize, check for `<xml_path>/standardize_warnings.csv` (c012 =
hyphen handling in morpheme-segmented standard FORMs, c022 = `*` in a
standard FORM). Per-run report (POL-033): fold its counts into the summary,
do not commit it.

### Phase 4: Add phonology

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/add_phonology.py \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/04_add_phonology.log
```

No decisions. Standard PHON uses the language's designated scheme per
`standards.csv`; a "no designated standard orthography" message means the
registry cell is blank (deliberate — e.g. Pazeh, Siraya), not a failure.
PHON is regenerated from FORM on every run, is marker-free (`-`, `=`,
infix brackets omitted; infix *content* kept), drops unmapped punctuation,
and renders unmapped letters as `*` (POL-003).

**Note:** `add_phonology.py` adds `<PHON>` elements. These are now valid under the schema — `xml_template.xsd` defines `PHON_Type` and allows `PHON` within `S`/`W`/`M` (and the DTD fallback declares `PHON*` on each), so `validate_xml.py` in Phase 5 accepts them. (Earlier versions of this skill warned that PHON would fail `validate_xml.py`; that schema drift has since been resolved, so no such caveat is needed in the summary.)

### Phase 5: Validate (informational)

Run each validator, capturing output. Do NOT abort the recipe on failures — these are info-gathering:

```bash
# DTD/XSD conformance. --no-exit-on-hard so the pipeline does not
# abort on HARD findings — this phase is informational; the log is
# the artifact. The validator's default behavior is to exit 1 on HARD
# findings, which is the right behavior for CI gating but wrong for
# this dev-repo discovery flow.
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_xml.py by_path \
  --path <xml_path> --no-exit-on-hard 2>&1 | tee <output_dir>/05a_validate_xml.log

# Text-content validation (punctuation, character set, null/segmentation
# markers). B9.4 consolidated the old validate_punct.py + non_ascii_counts.py
# into a single staged-pipeline validator (rules in QC/validation/rules/text.py).
# --no-exit-on-hard so this informational phase does not abort the recipe.
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_text.py by_path \
  --path <xml_path> --no-exit-on-hard \
  --soft-csv <output_dir>/05b_validate_text_soft.csv \
  2>&1 | tee <output_dir>/05b_validate_text.log

# Orthography extraction
.venv/bin/python3 <formosanbank_path>/QC/orthography/orthography_extract.py \
  --corpus all --language All --kindOf standard --by_dialect true \
  --corpora_path <xml_path> \
  --output_dir <output_dir>/extract_logs 2>&1 | tee <output_dir>/05c_orthography_extract.log

# Orthography comparison vs reference
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_orthography.py \
  --o_info <output_dir>/extract_logs \
  --reference <formosanbank_path>/QC/validation/reference 2>&1 \
  | tee <output_dir>/05d_validate_orthography.log

# Vocabulary comparison vs reference
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_vocabulary.py \
  --o_info <output_dir>/extract_logs \
  --reference <formosanbank_path>/QC/validation/reference 2>&1 \
  | tee <output_dir>/05e_validate_vocabulary.log

# Dialect distribution (informational). Prints an (xml:lang, dialect) ->
# count table; a human reads it to judge whether the distribution looks
# right (missing dialects, a dialect leaking into the wrong language).
# It does not flag values as invalid — that's validate_xml.py's V036.
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_dialect.py \
  --path <xml_path> 2>&1 | tee <output_dir>/05f_validate_dialect.log

# Duplicate sentences within the corpus. Interpret per POL-022:
# every finding is SOFT (narratives may legitimately repeat; the
# maintainer decides) UNLESS this corpus's CodeAndDocs declares a
# dedup step, in which case findings arrive as HARD — dedup should
# have removed them, so leftovers signal a pipeline defect. Compares
# the standard tier, which Phase 3 created. The script always exits 0
# (informational); the log and CSV are the artifacts.
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_duplicate_sentences.py by_path \
  --path <xml_path> --verbose \
  --output <output_dir>/05g_duplicate_sentences.csv \
  2>&1 | tee <output_dir>/05g_validate_duplicate_sentences.log
```

Then check whether the corpus has `<W>` or `<M>` elements (quick grep across XML files). If yes:

```bash
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_glosses.py \
  <xml_path> --output_dir <output_dir> 2>&1 | tee <output_dir>/05h_validate_glosses.log
```

Then check whether the corpus has audio (quick grep for `<AUDIO` across the XML files). If yes, locate the audio directory (commonly `<corpus_path>/Audio/`; if ambiguous, ask). If the audio files aren't present locally (dev repos often defer the download), skip the run and record that in the summary as an open item instead:

```bash
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_audio.py \
  --path <audio_dir> --xml_path <xml_path> \
  --log_dir <output_dir> --no-exit-on-hard \
  2>&1 | tee <output_dir>/05i_validate_audio.log
```

### Phase 6: Summary

Generate `<output_dir>/qc-summary.md` from `.claude/skills/run-qc-pipeline/summary.template.md`, substituting:
- `{{CORPUS_NAME}}` — basename of `corpus_path`
- `{{DEV_REPO_PATH}}` — absolute `corpus_path`
- `{{TIMESTAMP_UTC}}` — same timestamp used in `output_dir`
- `{{XML_PATH}}` — absolute `xml_path`
- `{{ORIGINAL_ORTHOGRAPHY}}` — user's Phase 2 answer
- `{{STANDARDIZE_ARGS}}` — the actual standardize.py args used
- `{{N_TEXTS}}`, `{{N_SENTENCES}}`, etc. — extract from the various logs
- `{{XML_RESULT}}`, `{{TEXT_RESULT}}`, etc. — read each validator's log to determine pass/fail
- `{{ORTHO_SIM}}`, `{{VOCAB_OVERLAP}}` — pull numbers from soft-check logs
- Fill the "Unusual things surfaced" section with anything notable from any phase — including the dialect distribution table if anything about it looks off
- When null-family rules fire, interpret them for the reader instead of
  listing raw counts: V120 SOFT = null units in S-standard (expected under
  `--copy`; means "re-standardize when a table exists"); V069 HARD = null in
  a W FORM without a null M child; V123–V125/V140 HARD = null propagation
  broken between tiers. All of these are only trustworthy if the corpus's
  null glyphs are canonical `∅` — if Phase 1 normalized `ø`/`Ø`, say so.
- Include `standardize_warnings.csv` / `cleaner_warnings.csv` counts (per-run
  reports; POL-033)
- Fill the "Ready to port?" verdict — heuristic only:
  - "yes" if the XML/punct/duplicate-sentence/glosses/audio hard gates pass AND soft check numbers look reasonable
  - "no — see Hard-gate findings" if hard gates fail
  - "needs review" otherwise (including when audio exists but wasn't locally available to validate)

Print the path to the summary and a tight 5-line preview.

## Decisions the skill surfaces (does NOT guess)

- Original orthography (Phase 2)
- TSV mapping path for non-Ortho113 corpora (Phase 3)
- Whether the XML location is ambiguous (Pre-checks)
- Where the audio directory is, if the corpus has audio and the location is ambiguous (Phase 5)
- Whether to proceed if pre-checks find issues

## What this skill is NOT

- Not a fix-it tool. Reports findings; user decides what to fix.
- Not coupled to porting. Can be re-run on a dev repo as many times as needed during development.
- Not a guarantee. The "Ready to port?" verdict is heuristic and the operator's judgment governs.
