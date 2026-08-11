---
name: audit-dev-repo
description: Guided audit of an assistant-built corpus dev repo (../Formosan-<Name>/) before QC + porting. Reads the assistant's preprocessing, maps it onto our current pipeline, runs our validators on its output, and diffs its original tier against the source for dropped characters/punctuation and ungrammatical artifacts — pausing for the maintainer's judgment. Use when starting to review a new dev repo's preprocessing.
---

# audit-dev-repo

Guided, one-repo-at-a-time audit of a corpus dev repo's preprocessing against the
current FormosanBank pipeline. **Pauses for human judgment** — do not draw
conclusions or write the report without the maintainer signing off on each concern.

## Step 0 — Get oriented (REQUIRED, before touching the repo)

Read, in this order, and do not skip:
1. `claudeplans/2026-06-09-dev-repo-audit-briefing.md` — the objectives, our
   conventions, the current pipeline, and the **concern → tool map**. This is the
   spine of the audit.
2. `FormosanBank/CLAUDE.md` (auto-loaded) and `QC/README.md` — conventions + pipeline order.

**Audit scope: anything that touches the data.** Every transformation the assistant
applies should make sense and look correct — scrutinize each one, not just a fixed
checklist. The maintainer has **four highlighted concerns** they especially want
checked, but they are priorities, **not the full scope**:
(a) eliminated orthography characters, (b) suppressed punctuation,
(c) other convention breaks, (d) source-extraction artifacts (e.g. ungrammatical
sentences left in). Beyond these, flag any character-, punctuation-, or
structure-altering step that could distort the data. Keep the assistant's profile in mind:
strong coder, does not read the languages, churn-prone — so trust nothing without
evidence.

## Inputs (gather via AskUserQuestion if missing)

- `repo_path` — the dev repo, e.g. `../Formosan-<Name>/`. Must be a sibling dev
  repo, not a published `Corpora/<Name>/` tree. Run this skill from `FormosanBank`
  with the dev repo added (`--add-dir`), so the pipeline and references are in scope.
- `language` — the ISO 639-3 / language name, to pick the right
  `QC/validation/reference/<Language>/` and `Orthographies/Ortho113/<Language>.tsv`.
- `xml_subdir` — where the built XML lives (auto-detect `XML/`, `Final_XML/`, root `*.xml`).

## Procedure (guided — pause at each ▣)

### 1. Read the preprocessing
Read the repo `README` and every scrape/parse/build script. Produce a plain-language
summary of the transformations it applies and their order — flag every step that
**deletes or substitutes characters** or **drops/normalizes punctuation**.
▣ Present the summary; confirm your read with the maintainer before proceeding.

### 2. Map each transformation to our pipeline
For each step, classify: (i) our pipeline already does this (and how it differs),
(ii) no-op for us, or (iii) conflicts with a convention (cite which). Pay special
attention to anything touching the **original** tier (must stay faithful) and W-tier
segmentation markers (`-`, `=`, `<…>` must survive).
▣ Present the mapping table; get the maintainer's reaction.

### 3. Run our validators on the XML output
Either invoke the `run-qc-pipeline` skill, or run the four validators directly:
`validate_xml.py`, `validate_text.py`, `validate_glosses.py` (if W/M present),
and `validate_orthography.py` (after `orthography_extract.py --kindOf original`).
Read the per-rule summary + the findings CSV(s). Organize hits by concern (a–d)
using the briefing's map (e.g. V129/V137–V139 → (d); V110–V116/V126/V133/V134 → (b);
orthography deltas → (a); schema/V063/V068/V141 → (c)).
▣ Present findings grouped by concern, with the CSV path(s).

### 4. Diff the output against the source (concerns a, b, d)
Sample sentences (use `sample_sentences.py` or pick representative ids). For each,
compare the `FORM[@kindOf="original"]` to the **actual original text** (the printed
page image / true source — *not* merely the raw scrape). The original tier is meant
to match the real source, so OCR/scrape-error corrections toward it are **expected
and legitimate**; the check is fidelity to the true text, not "did it change the
scrape?":
- (a) Did any orthographic letter disappear vs the *source*? (Check the char
  inventory vs `reference/<Language>/` and vs the source. Watch curly apostrophes →
  loss.) A `u`→`ʉ`-type correction that matches the printed page is good — verify it
  actually matches the page, don't flag it as a violation.
- (b) Did punctuation/segmentation the *source has* vanish from the original tier?
  (Punctuation *normalization* that preserves spelling is fine; the bug is source
  punctuation/segmentation silently disappearing.)
- (d) Are there sentence-initial `*` (ungrammatical — should have been excluded),
  footnote digit leaks, or out-of-language runs?
- (d) **Starred-parenthesis sweep (POL-017).** Grep the *source* (and extraction
  ledgers) for `*(` and `(*`: `*(X)` = X obligatory (X must be in FORM,
  unstarred); `(*X)` = X forbidden (X must NOT be in FORM). Trace every hit into
  the XML and flag any script that treats the two identically — that inversion
  published an ungrammatical sentence in NTU Rukai (`*(malra)`).
- (a) **Null-glyph check (POL-012).** Grep the XML for `ø`/`Ø` in morpheme
  position: preprocessing that emits non-canonical null glyphs leaves the whole
  V069/V120/V123–V125/V140 family vacuously blind until `clean_xml` normalizes
  them to `∅`. Flag as "normalize at intake", not as data loss.

**Expected normalizations — do not flag as data loss** (cite the POLICIES.md
entry instead): dash/hyphen look-alikes → ASCII `-` (POL-011); typographic
apostrophes/quotes → ASCII `'`/`"` in Formosan text (POL-010 — including a dev
repo's `’`→`'` in its build scripts); null glyphs `ø`/`Ø` → `∅` in morpheme
position (POL-012); curly quotes absent from PHON (PHON drops unmapped
punctuation, POL-003). Re-flagging these wastes a maintainer round-trip.

▣ Present concrete before/after samples per concern; get the maintainer's call on
each class (real bug vs acceptable vs needs source check).

### 5. Record the report
Only after sign-off, write `claudeplans/audit-<Repo>.md`: what the assistant did, findings
by concern (a–d) with evidence, the pipeline mapping, and recommended remediation
(which conflicts must be fixed in the reproduction before porting).

### 6. Regression fixtures (when a finding leads to a FormosanBank code fix)
If remediation lands in FormosanBank code (a cleaner rule, a validator, a
pipeline script — as opposed to the dev repo's own build scripts), the fix is
not complete until a minimal reproduction fixture and one test exist under
`tests/fixtures/audit_regressions/` (see its README for naming). Add creating
them to the remediation list.

## Notes
- This is an audit, not a fix: do not modify the dev repo or `Corpora/` here. Remediation
  belongs in the reproduction scripts (per the dev-repo workflow).
- Evidence over assertion: every finding cites file + id + a source/XML sample.

## Data files change only via code (POL-038)

Never modify XML or raw scrape files by hand or ad hoc — only via committed code (pipeline scripts, `manual_edits.xml` via the capture/apply tooling, or a one-off script committed to `CodeAndDocs/`). This includes POL-035 snapshots: fix snapshot defects with a committed script, never a direct edit. A non-code edit is unreproducible and is destroyed on regeneration.
