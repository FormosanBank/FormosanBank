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

- Create placeholders: `XML/.gitkeep`, `CodeAndDocs/.gitkeep`.
- Generate `README.md` from `.claude/skills/setup-new-dev-repo/README.template.md`, substituting `{{CORPUS_NAME}}`, `{{LANGUAGE}}`, `{{CREATED_DATE}}` (today, YYYY-MM-DD).
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

## Decisions to surface (do NOT guess)

- Whether to set up a git remote and what URL
- Audio scaffolding (default off)
- Any additional libs beyond FormosanBank `requirements.txt`

## What this skill is NOT

- Not a corpus ingestion tool. Scaffolds structure; populating `XML/` is the user's job.
- Not a port-in tool. See `port-corpus-in` for moving a finished dev repo into FormosanBank.
- Not a FormosanBank cloner. Assumes FormosanBank is already locally cloned.
