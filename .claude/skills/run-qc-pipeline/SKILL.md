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

### Phase 1: Clean

```bash
.venv/bin/python3 <formosanbank_path>/QC/cleaning/clean_xml.py \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/01_clean_xml.log
```

No decisions. Capture log.

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

If the user's answer was **Ortho113**:

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/standardize.py \
  --copy --corpora_path <xml_path> 2>&1 | tee <output_dir>/03_standardize.log
```

Otherwise, resolve the TSV mapping path. The convention (per CLAUDE.md) is `Orthographies/ConversionTables/<source-orthography>-to-standard.tsv` or similar. **If the mapping path is ambiguous, surface to user before proceeding.**

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/standardize.py \
  --tsv_path <mapping_tsv> \
  --target_column standard \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/03_standardize.log
```

### Phase 4: Add phonology

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/add_phonology.py \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/04_add_phonology.log
```

No decisions.

**Caveat:** `add_phonology.py` produces `<PHON>` elements that the current DTD does not allow. `validate_xml.py` in Phase 5 will fail purely because of this drift. Note this in the summary; do not treat it as a corpus problem. Resolving belongs to B.

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
```

Then check whether the corpus has `<W>` or `<M>` elements (quick grep across XML files). If yes:

```bash
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_glosses.py \
  <xml_path> --output_dir <output_dir> 2>&1 | tee <output_dir>/05f_validate_glosses.log
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
- Fill the "Unusual things surfaced" section with anything notable from any phase
- Fill the "Ready to port?" verdict — heuristic only:
  - "yes" if XML/punct/glosses hard gates pass AND soft check numbers look reasonable
  - "no — see Hard-gate findings" if hard gates fail
  - "needs review" otherwise

Print the path to the summary and a tight 5-line preview.

## Decisions the skill surfaces (does NOT guess)

- Original orthography (Phase 2)
- TSV mapping path for non-Ortho113 corpora (Phase 3)
- Whether the XML location is ambiguous (Pre-checks)
- Whether to proceed if pre-checks find issues

## What this skill is NOT

- Not a fix-it tool. Reports findings; user decides what to fix.
- Not coupled to porting. Can be re-run on a dev repo as many times as needed during development.
- Not a guarantee. The "Ready to port?" verdict is heuristic and the operator's judgment governs.
