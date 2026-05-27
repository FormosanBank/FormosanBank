---
name: port-corpus-in
description: Move a QC'd corpus from its Formosan-<CORPUS>/ dev repo into FormosanBank/Corpora/<Name>/ with the standard layout, interactively. Surfaces decisions rather than guessing. Use when a corpus has passed QC and is ready for publication into FormosanBank.
---

# port-corpus-in

Move a QC'd corpus from a development repo into FormosanBank with the standard published layout (`{README.md, XML/, CodeAndDocs/}`, optionally `download_audio_data.sh`).

## Inputs (gather via `AskUserQuestion` if missing)

- `source_path` — path to the dev repo (e.g., `~/Documents/Projects/Formosan/Formosan-Nowbucyang-Truku-Thesis/`). Required.
- `corpus_name` — name for the published version. Default: derive from source by stripping `Formosan-` prefix. User can override.
- `formosanbank_path` — default sibling `../FormosanBank/` relative to source.
- `assume_qc_passed` — default `false`. If `false` and no recent QC summary is found, refuse or ask.

## Pre-checks

1. Verify `source_path` exists.
2. Verify `formosanbank_path/Corpora/` exists.
3. Verify target `formosanbank_path/Corpora/<corpus_name>/` does NOT already exist. Refuse if it does — operator decides whether to merge, replace, or pick a new name.
4. Look for recent QC evidence in `source_path`:
   - `qc-output/<latest-timestamp>/qc-summary.md` exists, OR
   - User explicitly passed `assume_qc_passed=true`.
   - If neither: surface to user. Either ask to run `run-qc-pipeline` first or to set `assume_qc_passed=true`.

## Recipe phases

### Phase 1: Assess source layout

Read `source_path` top-level. Identify and report:

- Does a `README.md` exist?
- Where is the XML? Detect:
  - `XML/` (standard already)
  - `Final_XML/` (common in dev repos)
  - `xml/<chapter>.xml` (common for chapter-segmented corpora)
  - Root-level `*.xml` (monolithic — see below)
- Is the XML monolithic (single file with many `<TEXT>` or `<S>` elements)? If yes, prompt the user: "This corpus has a monolithic XML. Run `split-monolithic-xml` first, then re-invoke port-corpus-in. Do NOT proceed without splitting." (`split-monolithic-xml` is a deferred-backlog item; it may not exist yet.)
- What scripts exist (at root or in a `scripts/` subdir) that likely belong in `CodeAndDocs/`?
- What source data artifacts exist at root (e.g., original PDFs, extracted text files, decrypted source documents) that may belong in `CodeAndDocs/` for reproducibility — *unless* they contain private content per CLAUDE.md's "private source data" caveat, in which case surface to user.
- What scratch dirs exist that should be dropped (`data/`, `raw_data/`, `Original/`, `img-by-page/`, `text-by-page/`, `logs/`, etc.)?
- Is there a `download_audio_data.sh`?

### Phase 2: Present plan

Build a concrete file-by-file plan and present via `AskUserQuestion`:

- **Copy these to `Corpora/<corpus_name>/XML/`**: <list of XML paths>
- **Copy these to `Corpora/<corpus_name>/CodeAndDocs/`**: <list of scripts and docs>
- **Drop these (won't be ported)**: <list of scratch dirs / build artifacts>
- **README handling**: copy as-is | generate from template | skip
- **Copy or move?**: default copy (leave dev repo intact)
- **Include `download_audio_data.sh`?**: yes/no based on audio presence

User can: approve, request changes to the plan, or abort. **No filesystem changes before approval.**

### Phase 3: Execute the plan

For each item in the approved plan:

```bash
mkdir -p "<formosanbank_path>/Corpora/<corpus_name>/XML"
mkdir -p "<formosanbank_path>/Corpora/<corpus_name>/CodeAndDocs"

# Copy XML
cp -r <source XML> "<formosanbank_path>/Corpora/<corpus_name>/XML/"

# Copy scripts
cp <source scripts> "<formosanbank_path>/Corpora/<corpus_name>/CodeAndDocs/"

# README: either copy or generate from template
# If copy:
cp <source README> "<formosanbank_path>/Corpora/<corpus_name>/README.md"
# If generate: render template at .claude/skills/port-corpus-in/README.template.md
# with substitutions from QC summary + user input.

# Audio:
# If has_audio: cp <source download_audio_data.sh> "<formosanbank_path>/Corpora/<corpus_name>/"
```

Drop nothing from the source dev repo unless explicitly approved.

### Phase 4: Validate after port

Run `validate_xml.py` on the new published XML to confirm DTD conformance:

```bash
<python> <formosanbank_path>/QC/validation/validate_xml.py by_path \
  --path "<formosanbank_path>/Corpora/<corpus_name>/XML"
```

**Resolve `<python>` in this order:**
1. `<source_path>/.venv/bin/python3` if it exists (dev repos created via `setup-new-dev-repo` have one)
2. Otherwise `<formosanbank_path>/.venv/bin/python3` — FormosanBank always has a venv with the deps
3. If neither, refuse and tell the user to install one before validating

Quick spot-check counts (file count, total size) vs source. If discrepancies, report — do not auto-fix.

### Phase 5: Summary

Print:
- What was created (paths)
- What was dropped (paths)
- DTD validation result
- Spot-check results
- Open items, e.g.:
  - "README is a stub — please flesh out the {{REPRODUCIBILITY_STEPS}} section before opening a PR"
  - "DTD validation failed on N files — investigate before opening PR"
  - "audio download script copied but not tested; run it to verify it still works in the published location"
- Recommended next steps:
  - Review the new `Corpora/<corpus_name>/` contents
  - Commit and open a PR

## Decisions the skill surfaces (does NOT guess)

- Monolithic XML splitting (if applicable)
- Ambiguous source layouts (multiple plausible XML locations)
- README handling when source has none
- Whether to copy or move source files
- Whether QC evidence is sufficient to proceed

## What this skill is NOT

- Not a fix-it tool. If QC found problems, fix them in the dev repo (or accept them) before porting; don't try to fix during port.
- Not a git operation. Creates files in the working tree; user commits.
- Not a force-port. Will refuse to overwrite an existing published corpus.
