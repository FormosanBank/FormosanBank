---
name: setup-new-dev-repo
description: Bootstrap a new Formosan-<CORPUS>/ development repository with the standard layout, Python environment, gitignore, README scaffold, and Claude Code safety rails. Use when starting work on a new corpus that doesn't already have its own dev repo.
---

# setup-new-dev-repo

Bootstrap a fresh corpus development repository at `<parent_dir>/Formosan-<corpus_name>/`. Pairs with the SessionStart venv-check hook (which is installed into the new repo by this skill).

## Inputs (gather via `AskUserQuestion` if missing)

- `corpus_name` — the suffix after `Formosan-` (e.g., `Bunun-NewDialect`). Required.
- `language` — primary Formosan language (for README pre-fill). Required.
- `has_audio` — boolean, whether to include audio scaffolding. Default `false`.
- `parent_dir` — default `~/Documents/Projects/Formosan/`.
- `remote_url` — optional git remote URL.

## Pre-checks

0. **Re-read `POLICIES.md` before going on.** If any instruction in this skill contradicts a policy, stop and show the maintainer both texts before continuing; the policies file moves faster than this skill.
1. Locate FormosanBank: usually `<parent_dir>/FormosanBank/`. If not found, prompt user for path. Required for `requirements.txt` and the `check-venv.py` hook to copy.
2. Verify `<formosanbank_path>/requirements.txt` and `<formosanbank_path>/.claude/hooks/check-venv.py` both exist. If either is missing, refuse and surface to the user — the bootstrap depends on both.
3. Verify target directory `<parent_dir>/Formosan-<corpus_name>/` does NOT already exist. If it does, refuse — operator must delete first or choose a new name.

## Recipe phases

### Phase 1: Confirm intent

Build a concrete plan and present via `AskUserQuestion`:
- Target directory
- What gets created (list each file/dir)
- Deps to install (from FormosanBank's `requirements.txt`)
- Whether to set up a git remote
- Whether to include audio scaffolding

User can approve, request changes, or abort. **No filesystem changes before approval.**

### Phase 2: Create directory and init git

```bash
mkdir -p "<target>/XML" "<target>/CodeAndDocs" "<target>/Private"
cd "<target>"
git init -b main
# If remote_url:
git remote add origin "<remote_url>"
```

Note: brace expansion (`mkdir -p "<target>/{XML,CodeAndDocs}"`) does NOT work inside double quotes — it would create a single literal directory named `{XML,CodeAndDocs}`. Either pass the two paths separately as above, or unquote the braces: `mkdir -p "<target>"/{XML,CodeAndDocs}`.

Note: The "Private" folder is for things that should not be copied into the public repo.

### Phase 3: Create .venv

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r "<formosanbank_path>/requirements.txt"
```

Capture pip output. If any install fails, surface immediately to user — do not continue with broken env.

### Phase 4: Scaffold layout

Canonical corpus folders match the published `Corpora/<Name>/` tree: **`XML/`** (the corpus XML), **`Audio/`** (downloaded audio, gitignored — audio corpora only), and **`CodeAndDocs/`** (scripts that reproduce `XML/`). Use these names, **never `Final_XML`/`Final_audio`** (a legacy naming being phased out of older dev repos).

- Create placeholders: `XML/.gitkeep`, `CodeAndDocs/.gitkeep`, `CodeAndDocs/tests/`.
- Generate `README.md` from `.claude/skills/setup-new-dev-repo/README.template.md`, substituting `{{CORPUS_NAME}}`, `{{LANGUAGE}}`, `{{CREATED_DATE}}` (today, YYYY-MM-DD). It already carries the three sections the port later requires: `## Rights` (POL-044), the reproduction section that names `generate_xml.sh` and links `provenance.json` (POL-047/052), and `## Notes and Issues` (POL-055).
- Copy `generate_xml.sh.template` to `CodeAndDocs/generate_xml.sh` and `chmod +x` it. It is the one entry point (POL-047) with the five canonical steps written out and commented, a staging build with install (idempotent), FormosanBank located from either layout, and the provenance write at the end. Replace `<Language>` / `<SourceOrthography>` and the step-1 command; delete the steps the corpus does not have (no standard tier → no steps 4–5) and say so in the README with a `**POL-047 deviation:**` line.
- Copy `test_source_accounting.py.template` to `CodeAndDocs/tests/test_source_accounting.py`. **Tests first** (maintainer, Poinsot, 2026-10-17: "Please start by writing appropriate tests for these decisions"): fill in `source_units()` before writing the parser, so the parser is written against a count the source itself gives. The test skips when the source is absent, which is how a corpus with a private PDF still ships it.
- Copy `.claude/skills/setup-new-dev-repo/gitignore.template` to `.gitignore` (it already ignores `Audio/`, `*.mp3`, `*.wav`).
- If `has_audio`: copy and substitute `download_audio_data.sh.template` to `download_audio_data.sh` (it downloads into `Audio/`); `chmod +x` it.

### Phase 5: Install Claude Code safety rails

- Create `<target>/.claude/hooks/check-venv.py` by copying from `<formosanbank_path>/.claude/hooks/check-venv.py`. (Copy the *file*; the new repo shouldn't depend on FormosanBank's filesystem location.)
- Split the Claude Code settings between two files:
  - **Committed** (project-wide, in version control): `<target>/.claude/settings.json` carries the hook config so anyone cloning the dev repo gets the same safety rail.
  - **Per-user** (gitignored — the `.gitignore` from Phase 4 already excludes it): `<target>/.claude/settings.local.json` carries `additionalDirectories`, which is the operator's machine layout and shouldn't be shared.

Create `<target>/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/check-venv.py\""
          }
        ]
      }
    ]
  }
}
```

Create `<target>/.claude/settings.local.json`:

```json
{
  "permissions": {
    "additionalDirectories": [
      "<parent_dir>"
    ]
  }
}
```

### Phase 6: Initial commit

```bash
git add .
git commit -m "Initial scaffold for Formosan-<corpus_name>"
```

If `remote_url` was set and remote is reachable, ask whether to push now (do not auto-push).

### Phase 7: Summary

Print summary including:
- What was created (top-level dirs, key files)
- How to activate venv: `source .venv/bin/activate`
- Recommended next steps:
  - Add source material under `XML/`
  - Add ingestion scripts under `CodeAndDocs/`
  - When source XML is in place, run the `run-qc-pipeline` skill from this directory
  - When QC passes, run `port-corpus-in` from FormosanBank
- Forward-looking notes to include in the summary:
  - Check `FormosanBank/standards.csv` for this language: a blank scheme cell
    means no standard orthography is designated yet, so standard-tier PHON
    will be deliberately skipped during QC.
  - Scrapers need not normalize typography themselves: `clean_xml` will
    canonicalize dashes, typographic apostrophes/quotes, and null-morpheme
    glyphs (`ø`/`Ø` → `∅`) at QC time (POLICIES.md POL-010/011/012). Scrapers
    SHOULD get `*(X)`/`(*X)` right, though — obligatory vs forbidden material
    is semantic, not typographic (POL-017).
  - Hand edits made during QC must be reproducible: record them with
    `FormosanBank/QC/utilities/capture_manual_edits.py` into
    `CodeAndDocs/manual_edits.xml`; `apply_manual_edits.py` re-applies them
    first on every pipeline run (POL-030). Never hand-edit standard FORMs or
    PHON — they are regenerated (POL-002/003).
  - If the corpus will standardize via a conversion table, name it
    `Orthographies/ConversionTables/<Language>_<Scheme>_113.tsv` and document
    it in the README's reproduction section; run
    `validate_conversion_table.py` on it before first use.
  - **Decisions about specific records go in a content-gated table, not in
    code.** The pattern five corpora converged on: a file (TSV or JSON) keyed
    by the stable record id *and the input text the decision expects*, with
    the reason, the date and the maintainer's words; the build refuses the row
    when the input has drifted ("Source override … no longer matches
    upstream"). Worked examples: `Corpora/Safolu-Amis-Dictionary/CodeAndDocs/`
    (`safolu_source_overrides.json`, ordinal + expected form) and
    `Corpora/Seediq-Chang-Reference-Grammar/CodeAndDocs/review_corrections.tsv`
    (`was` must match or the build fails as a stale review). `manual_edits.xml`
    keys on positional ids and cannot carry a standard-tier edit; a dict of
    sentence text inside `build_xml.py` is what `lint_hidden_tables.py` warns
    about (POL-039).

## Decisions to surface (do NOT guess)

- Whether to set up a git remote and what URL
- Audio scaffolding (default off)
- Any additional libs beyond FormosanBank `requirements.txt`

## What this skill is NOT

- Not a corpus ingestion tool. Scaffolds structure; populating `XML/` is the user's job.
- Not a port-in tool. See `port-corpus-in` for moving a finished dev repo into FormosanBank.
- Not a FormosanBank cloner. Assumes FormosanBank is already locally cloned.

## Data files change only via code (POL-038)

Never modify XML or raw scrape files by hand or ad hoc — only via committed code (pipeline scripts, `manual_edits.xml` via the capture/apply tooling, or a one-off script committed to `CodeAndDocs/`). This includes POL-035 snapshots: fix snapshot defects with a committed script, never a direct edit. A non-code edit is unreproducible and is destroyed on regeneration.
