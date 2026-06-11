---
name: audit-dev-repo
description: Guided audit of a Hunter S corpus dev repo (../Formosan-<Name>/) before QC + porting. Reads his preprocessing, maps it onto our current pipeline, runs our validators on his output, and diffs his original tier against the source for dropped characters/punctuation and ungrammatical artifacts — pausing for the maintainer's judgment. Use when starting to review a new dev repo's preprocessing.
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

**Audit scope: anything that touches the data.** Every transformation Hunter
applies should make sense and look correct — scrutinize each one, not just a fixed
checklist. The maintainer has **four highlighted concerns** he especially wants
checked, but they are priorities, **not the full scope**:
(a) eliminated orthography characters, (b) suppressed punctuation,
(c) other convention breaks, (d) source-extraction artifacts (e.g. ungrammatical
sentences left in). Beyond these, flag any character-, punctuation-, or
structure-altering step that could distort the data. Keep Hunter's profile in mind:
strong coder, does not read the languages, churn-prone — so trust nothing without
evidence.

## Inputs (gather via AskUserQuestion if missing)

- `repo_path` — the dev repo, e.g. `../Formosan-<Name>/`. Must be a sibling dev
  repo, not a published `Corpora/<Name>/` tree. Run this skill from `FormosanBank`
  with the dev repo added (`--add-dir`), so the pipeline and references are in scope.
- `language` — the ISO 639-3 / language name, to pick the right
  `QC/validation/reference/<Language>/` and `Orthographies/Ortho113/<Language>.tsv`.
- `xml_subdir` — where his built XML lives (auto-detect `XML/`, `Final_XML/`, root `*.xml`).

## Procedure (guided — pause at each ▣)

### 1. Read his preprocessing
Read the repo `README` and every scrape/parse/build script. Produce a plain-language
summary of the transformations he applies and their order — flag every step that
**deletes or substitutes characters** or **drops/normalizes punctuation**.
▣ Present the summary; confirm your read with the maintainer before proceeding.

### 2. Map each transformation to our pipeline
For each step, classify: (i) our pipeline already does this (and how it differs),
(ii) no-op for us, or (iii) conflicts with a convention (cite which). Pay special
attention to anything touching the **original** tier (must stay faithful) and W-tier
segmentation markers (`-`, `=`, `<…>` must survive).
▣ Present the mapping table; get the maintainer's reaction.

### 3. Run our validators on his XML output
Either invoke the `run-qc-pipeline` skill, or run the four validators directly:
`validate_xml.py`, `validate_text.py`, `validate_glosses.py` (if W/M present),
and `validate_orthography.py` (after `orthography_extract.py --kindOf original`).
Read the per-rule summary + the findings CSV(s). Organize hits by concern (a–d)
using the briefing's map (e.g. V129/V137–V139 → (d); V110–V116/V126/V133/V134 → (b);
orthography deltas → (a); schema/V063/V068/V141 → (c)).
▣ Present findings grouped by concern, with the CSV path(s).

### 4. Diff his output against the source (concerns a, b, d)
Sample sentences (use `sample_sentences.py` or pick representative ids). For each,
compare his `FORM[@kindOf="original"]` to the raw source:
- (a) Did any orthographic letter disappear? (Check his char inventory vs
  `reference/<Language>/` and vs the source. Watch curly apostrophes → loss.)
- (b) Did punctuation/segmentation in the original tier vanish vs the source?
- (d) Are there sentence-initial `*` (ungrammatical — should have been excluded),
  footnote digit leaks, or out-of-language runs?
▣ Present concrete before/after samples per concern; get the maintainer's call on
each class (real bug vs acceptable vs needs source check).

### 5. Record the report
Only after sign-off, write `claudeplans/audit-<Repo>.md`: what Hunter did, findings
by concern (a–d) with evidence, the pipeline mapping, and recommended remediation
(which conflicts must be fixed in his reproduction before porting).

## Notes
- This is an audit, not a fix: do not modify his repo or `Corpora/` here. Remediation
  belongs in his reproduction scripts (per the dev-repo workflow).
- Evidence over assertion: every finding cites file + id + a source/XML sample.
