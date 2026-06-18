# E: Claude Code Project Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the five Phase-0 Claude Code tooling items for FormosanBank — two hooks and three skills that together make the porting/QC workflow reproducible and add safety rails around the most-dangerous repository state.

**Architecture:** Two `PreToolUse`/`SessionStart` hooks implemented as small Python scripts under `.claude/hooks/`, registered via `.claude/settings.local.json`. Three skills authored as markdown recipes under `.claude/skills/`. Skills use `AskUserQuestion` for human-in-the-loop decision points and shell out to existing `FormosanBank/QC/*.py` scripts for the actual work. Tests for the hook scripts follow the existing repo pattern (hand-rolled PASS/FAIL counters, similar to `QC/test_find_duplicate_sentences.py`) since formal pytest infrastructure is sub-project A's job, not E's.

**Tech Stack:** Python 3.10 (matches FormosanBank `.venv`), Claude Code hooks API, Claude Code skills API, macOS shell.

---

## File Structure

### Created

- `.claude/hooks/block-statistics-edits.py` — Task 1 hook script
- `.claude/hooks/test_block_statistics_edits.py` — Task 1 test
- `.claude/hooks/check-venv.py` — Task 2 hook script
- `.claude/hooks/test_check_venv.py` — Task 2 test
- `.claude/skills/setup-new-dev-repo.md` — Task 3 skill recipe (with frontmatter)
- `.claude/skills/setup-new-dev-repo/README.template.md` — Task 3 README template for new dev repos
- `.claude/skills/setup-new-dev-repo/gitignore.template` — Task 3 .gitignore template
- `.claude/skills/setup-new-dev-repo/download_audio_data.sh.template` — Task 3 audio stub template
- `.claude/skills/run-qc-pipeline.md` — Task 4 skill recipe
- `.claude/skills/run-qc-pipeline/summary.template.md` — Task 4 QC-summary template
- `.claude/skills/port-corpus-in.md` — Task 5 skill recipe
- `.claude/skills/port-corpus-in/README.template.md` — Task 5 template for ported-corpus READMEs

### Modified

- `.claude/settings.local.json` — register the two hooks under a new top-level `"hooks"` key (Tasks 1 and 2)

### Not touched

Per user permission constraints: no edits to `Corpora/`, `Orthographies/`, `QC/`, `statistics/`, `.github/workflows/`, or any associated sibling repo. This plan stays entirely within `.claude/`.

---

## Task 1: Hook — Block writes under `statistics/`

**Files:**
- Create: `.claude/hooks/block-statistics-edits.py`
- Create: `.claude/hooks/test_block_statistics_edits.py`
- Modify: `.claude/settings.local.json`

- [ ] **Step 1.1: Write the failing test**

Create `.claude/hooks/test_block_statistics_edits.py` with this content:

```python
#!/usr/bin/env python3
"""Tests for block-statistics-edits.py hook. Hand-rolled PASS/FAIL counter
matching the repo's existing test style (see QC/test_find_duplicate_sentences.py)."""
import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).parent / "block-statistics-edits.py"
REPO_ROOT = Path(__file__).resolve().parents[2]  # .claude/hooks/ -> repo root

PASS = 0
FAIL = 0


def check(condition: bool, label: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {label}")
    else:
        FAIL += 1
        print(f"FAIL: {label}")


def run_hook(tool_input: dict) -> tuple[int, str]:
    """Run the hook with given input, return (exit_code, stderr)."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(tool_input),
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stderr


def test_blocks_edit_to_statistics() -> None:
    code, err = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(REPO_ROOT / "statistics/corpus_size_history.csv")},
    })
    check(code == 2, "blocks Edit on statistics/ file (exit 2)")
    check("statistics/" in err, "explanatory message mentions statistics/")


def test_blocks_write_to_statistics() -> None:
    code, _ = run_hook({
        "tool_name": "Write",
        "tool_input": {"file_path": str(REPO_ROOT / "statistics/new_chart.png")},
    })
    check(code == 2, "blocks Write on statistics/ file")


def test_blocks_multiedit_to_statistics() -> None:
    code, _ = run_hook({
        "tool_name": "MultiEdit",
        "tool_input": {"file_path": str(REPO_ROOT / "statistics/anything.csv")},
    })
    check(code == 2, "blocks MultiEdit on statistics/ file")


def test_blocks_notebookedit_to_statistics() -> None:
    code, _ = run_hook({
        "tool_name": "NotebookEdit",
        "tool_input": {"notebook_path": str(REPO_ROOT / "statistics/foo.ipynb")},
    })
    check(code == 2, "blocks NotebookEdit on statistics/ notebook")


def test_allows_edit_elsewhere() -> None:
    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {"file_path": str(REPO_ROOT / "QC/something.py")},
    })
    check(code == 0, "allows Edit on non-statistics file")


def test_allows_non_matching_tool() -> None:
    code, _ = run_hook({
        "tool_name": "Bash",
        "tool_input": {"command": "ls"},
    })
    check(code == 0, "allows tools other than Edit/Write/MultiEdit/NotebookEdit")


def test_handles_invalid_json() -> None:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input="not json",
        capture_output=True,
        text=True,
        env=env,
    )
    check(proc.returncode == 0, "handles invalid JSON gracefully (exit 0)")


def test_handles_missing_file_path() -> None:
    code, _ = run_hook({
        "tool_name": "Edit",
        "tool_input": {},
    })
    check(code == 0, "handles missing file_path gracefully")


if __name__ == "__main__":
    test_blocks_edit_to_statistics()
    test_blocks_write_to_statistics()
    test_blocks_multiedit_to_statistics()
    test_blocks_notebookedit_to_statistics()
    test_allows_edit_elsewhere()
    test_allows_non_matching_tool()
    test_handles_invalid_json()
    test_handles_missing_file_path()
    print(f"\n{PASS} pass, {FAIL} fail")
    sys.exit(0 if FAIL == 0 else 1)
```

- [ ] **Step 1.2: Run the test to verify it fails**

Run from repo root:

```bash
python3 .claude/hooks/test_block_statistics_edits.py
```

Expected: fails with `FileNotFoundError` because `block-statistics-edits.py` doesn't exist yet.

- [ ] **Step 1.3: Write the hook script**

Create `.claude/hooks/block-statistics-edits.py`:

```python
#!/usr/bin/env python3
"""PreToolUse hook: block Edit/Write/MultiEdit/NotebookEdit on files under statistics/.

statistics/ is auto-managed by .github/workflows/corpus-metrics.yaml.
CLAUDE.md mandates "do not hand-edit"; this hook enforces it.
"""
import json
import os
import sys
from pathlib import Path


def repo_root() -> Path:
    """Resolve repo root from $CLAUDE_PROJECT_DIR, falling back to cwd."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def is_under_statistics(file_path: str, root: Path) -> bool:
    """True if file_path resolves inside <root>/statistics/."""
    if not file_path:
        return False
    try:
        target = Path(file_path).resolve()
        protected = (root / "statistics").resolve()
        target.relative_to(protected)
        return True
    except (ValueError, OSError):
        return False


def collect_paths(tool_name: str, tool_input: dict) -> list[str]:
    """Return the file paths a given tool call would write to."""
    paths: list[str] = []
    if tool_name in ("Edit", "Write", "MultiEdit"):
        fp = tool_input.get("file_path")
        if fp:
            paths.append(fp)
    elif tool_name == "NotebookEdit":
        np = tool_input.get("notebook_path")
        if np:
            paths.append(np)
    return paths


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Not JSON; don't block. The harness will continue.
        return 0

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}
    root = repo_root()

    for path in collect_paths(tool_name, tool_input):
        if is_under_statistics(path, root):
            print(
                f"Blocked: {path} is under statistics/.\n"
                f"This directory is auto-managed by .github/workflows/corpus-metrics.yaml. "
                f"Don't hand-edit. To change what gets committed, modify the workflow "
                f"or upstream data (QC/corpus_metrics.py etc.). If you have a genuine "
                f"reason to override, disable this hook in .claude/settings.local.json.",
                file=sys.stderr,
            )
            return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 1.4: Run the test to verify it passes**

Run from repo root:

```bash
python3 .claude/hooks/test_block_statistics_edits.py
```

Expected output ends with:

```
8 pass, 0 fail
```

Exit code: 0.

- [ ] **Step 1.5: Register the hook in settings.local.json**

Read current `.claude/settings.local.json`. It currently contains `permissions` and `enabledPlugins` keys. Add a top-level `hooks` key (or extend if one already exists).

Add this block to `.claude/settings.local.json` so the final file has the existing keys plus a `hooks` entry containing:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit|NotebookEdit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/block-statistics-edits.py\""
        }
      ]
    }
  ]
}
```

The complete file should be valid JSON. Verify by running:

```bash
python3 -m json.tool .claude/settings.local.json > /dev/null && echo "OK"
```

Expected: `OK`.

- [ ] **Step 1.6: Manual end-to-end smoke test**

Either in this Claude Code session (after settings reload) or in a fresh session, attempt to edit a file under `statistics/`. The harness should refuse and surface the explanatory message. (Note: if you're in the session that just added the hook, you may need to reload settings or `/clear` for the hook to be picked up.)

If you don't want to run a destructive smoke test, this command exercises the same code path the harness would:

```bash
echo '{"tool_name":"Edit","tool_input":{"file_path":"statistics/corpus_size_history.csv"}}' \
  | CLAUDE_PROJECT_DIR="$(pwd)" python3 .claude/hooks/block-statistics-edits.py
echo "exit: $?"
```

Expected: prints the "Blocked: ..." message to stderr, exits with `2`.

- [ ] **Step 1.7: Commit**

```bash
git add .claude/hooks/block-statistics-edits.py \
        .claude/hooks/test_block_statistics_edits.py \
        .claude/settings.local.json
git commit -m "$(cat <<'EOF'
Add hook blocking edits under statistics/

statistics/ is auto-managed by the corpus-metrics workflow; this hook
makes the "don't hand-edit" rule from CLAUDE.md mechanically enforced
instead of advisory.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Hook — SessionStart `.venv` check

**Files:**
- Create: `.claude/hooks/check-venv.py`
- Create: `.claude/hooks/test_check_venv.py`
- Modify: `.claude/settings.local.json`

- [ ] **Step 2.1: Write the failing test**

Create `.claude/hooks/test_check_venv.py`:

```python
#!/usr/bin/env python3
"""Tests for check-venv.py hook."""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(__file__).parent / "check-venv.py"

PASS = 0
FAIL = 0


def check(condition: bool, label: str) -> None:
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"PASS: {label}")
    else:
        FAIL += 1
        print(f"FAIL: {label}")


def run_hook(project_dir: Path) -> tuple[int, str, str]:
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


def test_silent_when_venv_and_deps_ok() -> None:
    """If a usable .venv with required deps exists, the hook prints nothing."""
    # Use the FormosanBank repo's own .venv as a known-good fixture.
    formosanbank_root = Path(__file__).resolve().parents[2]
    code, out, _ = run_hook(formosanbank_root)
    check(code == 0, "silent OK -> exit 0")
    check(out.strip() == "", f"silent OK -> empty stdout (got: {out!r})")


def test_warns_when_venv_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        code, out, _ = run_hook(root)
        # We don't fail-block on missing venv; just warn.
        check(code == 0, "missing venv -> exit 0 (warning only)")
        check("venv" in out.lower(), f"missing venv -> warning mentions venv (got: {out!r})")


def test_warns_when_venv_missing_python() -> None:
    """A .venv directory exists but bin/python3 doesn't."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".venv").mkdir()
        code, out, _ = run_hook(root)
        check(code == 0, "broken venv -> exit 0")
        check("python" in out.lower() or "venv" in out.lower(),
              f"broken venv -> warning (got: {out!r})")


if __name__ == "__main__":
    test_silent_when_venv_and_deps_ok()
    test_warns_when_venv_missing()
    test_warns_when_venv_missing_python()
    print(f"\n{PASS} pass, {FAIL} fail")
    sys.exit(0 if FAIL == 0 else 1)
```

- [ ] **Step 2.2: Run the test to verify it fails**

```bash
python3 .claude/hooks/test_check_venv.py
```

Expected: fails because `check-venv.py` doesn't exist.

- [ ] **Step 2.3: Write the hook script**

Create `.claude/hooks/check-venv.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook: verify .venv exists in project root and has expected deps.

Silent on success; prints a single-line warning to stdout on any problem so
Claude (reading session context) knows not to blindly invoke python commands
that will fail. Never fail-blocks the session start (always exits 0).
"""
import os
import subprocess
import sys
from pathlib import Path


# Load-bearing deps from FormosanBank/requirements.txt. Keep this list short:
# importing slow deps (e.g. matplotlib) adds session-start latency.
REQUIRED_IMPORTS = ["lxml", "pandas", "regex"]


def project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env).resolve()
    return Path.cwd().resolve()


def warn(msg: str) -> None:
    """Single-line warning to stdout (becomes session context Claude reads)."""
    print(f"[venv-check] WARNING: {msg}")


def main() -> int:
    root = project_root()
    venv_python = root / ".venv" / "bin" / "python3"

    if not venv_python.exists():
        # Don't warn for arbitrary directories — only complain if this looks
        # like a FormosanBank-ecosystem repo (has requirements.txt OR Corpora/
        # OR XML/ — heuristic).
        if not _looks_like_formosanbank(root):
            return 0
        warn(
            f".venv/bin/python3 not found in {root}. "
            f"Run 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt' "
            f"(or invoke the setup-new-dev-repo skill for a fresh dev repo) "
            f"before running QC scripts."
        )
        return 0

    # Test that key deps import.
    import_check = "; ".join(f"import {m}" for m in REQUIRED_IMPORTS)
    proc = subprocess.run(
        [str(venv_python), "-c", import_check],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # Stderr has the ImportError. Surface module name if possible.
        err = (proc.stderr or "").strip().splitlines()[-1] if proc.stderr else "import failed"
        warn(
            f".venv at {root}/.venv exists but a required dep is missing: {err}. "
            f"Run '.venv/bin/pip install -r requirements.txt'."
        )

    return 0


def _looks_like_formosanbank(root: Path) -> bool:
    """Heuristic: is this a FormosanBank-ecosystem repo worth warning about?"""
    if (root / "requirements.txt").exists():
        return True
    if (root / "Corpora").is_dir():
        return True
    if (root / "XML").is_dir() or (root / "Final_XML").is_dir():
        return True
    return False


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2.4: Run the test to verify it passes**

```bash
python3 .claude/hooks/test_check_venv.py
```

Expected output ends with:

```
3 pass, 0 fail
```

Exit code: 0.

If "silent OK" fails, your `.venv` is missing one of `lxml`, `pandas`, or `regex`. Install them with `.venv/bin/pip install -r requirements.txt` and re-run the test.

- [ ] **Step 2.5: Register the hook in settings.local.json**

Extend the existing `hooks` key in `.claude/settings.local.json` to add a `SessionStart` entry. After this step the `hooks` value should contain BOTH the `PreToolUse` entry from Task 1 AND a new `SessionStart` entry:

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "Edit|Write|MultiEdit|NotebookEdit",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/block-statistics-edits.py\""
        }
      ]
    }
  ],
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
```

Validate:

```bash
python3 -m json.tool .claude/settings.local.json > /dev/null && echo "OK"
```

Expected: `OK`.

- [ ] **Step 2.6: Manual smoke test**

Direct invocation (matches what the harness will do on SessionStart):

```bash
CLAUDE_PROJECT_DIR="$(pwd)" python3 .claude/hooks/check-venv.py
```

Expected (when `.venv` is healthy): no output, exit code 0.

To verify the warning path, point the hook at a directory without a `.venv`:

```bash
CLAUDE_PROJECT_DIR="$(mktemp -d)" python3 .claude/hooks/check-venv.py
```

Expected: silent (because the mktemp dir doesn't look like a FormosanBank repo). To exercise the warning, create a fake repo:

```bash
TMPDIR_FAKE=$(mktemp -d)
touch "$TMPDIR_FAKE/requirements.txt"
CLAUDE_PROJECT_DIR="$TMPDIR_FAKE" python3 .claude/hooks/check-venv.py
rm -rf "$TMPDIR_FAKE"
```

Expected: prints `[venv-check] WARNING: .venv/bin/python3 not found in ...`, exit 0.

- [ ] **Step 2.7: Commit**

```bash
git add .claude/hooks/check-venv.py \
        .claude/hooks/test_check_venv.py \
        .claude/settings.local.json
git commit -m "$(cat <<'EOF'
Add SessionStart hook that warns when .venv is missing or incomplete

Defensive backstop for the "wrong env" pitfall: warns Claude (via session
context) at session start if the project's .venv is absent or missing a
load-bearing dep, so subsequent python invocations don't fail confusingly.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Skill — `setup-new-dev-repo`

**Files:**
- Create: `.claude/skills/setup-new-dev-repo.md`
- Create: `.claude/skills/setup-new-dev-repo/README.template.md`
- Create: `.claude/skills/setup-new-dev-repo/gitignore.template`
- Create: `.claude/skills/setup-new-dev-repo/download_audio_data.sh.template`

Skill recipes are prose markdown that Claude follows. There's no test framework for skills; verification is "follow the recipe and observe the resulting filesystem state." The test target is a known throwaway directory.

- [ ] **Step 3.1: Write the README template**

Create `.claude/skills/setup-new-dev-repo/README.template.md`:

```markdown
# Formosan-{{CORPUS_NAME}}

**Primary language:** {{LANGUAGE}}
**Status:** Pre-QC, in development
**Created:** {{CREATED_DATE}}

## Source

<!-- Describe the source data: where it came from, who collected it, what format the original is in, any licensing/access constraints. -->

TBD.

## Attribution

<!-- Citations for the original source(s). Include APA-style and BibTeX. -->

TBD.

## Scripts (in CodeAndDocs/)

<!-- Inventory of scripts that produce the contents of XML/ from the original source data. List each with one-line purpose. -->

TBD.

## How to reproduce

<!-- Step-by-step: from the original source data to the contents of XML/.
This is reproducibility infrastructure; treat it that way. -->

TBD.

## QC notes

<!-- Anything specific about this corpus that affects QC: unusual orthography,
mixed dialects, code-switching, audio quality, etc. Populated by run-qc-pipeline
summaries over time. -->

TBD.

## Port-in checklist

When this corpus is ready to port into FormosanBank/Corpora/:
- [ ] Last `run-qc-pipeline` run passed and the summary is acceptable
- [ ] README is no longer all TBDs
- [ ] No private source data remains in the dev repo (or is gitignored)
- [ ] Run `port-corpus-in` from this directory
```

- [ ] **Step 3.2: Write the .gitignore template**

Create `.claude/skills/setup-new-dev-repo/gitignore.template`:

```gitignore
# Python
.venv/
__pycache__/
*.pyc

# Logs and scratch
*.log
qc-output/
data/
raw_data/
Original/
img-by-page/
text-by-page/

# OS
.DS_Store

# Claude
.claude/settings.local.json
```

- [ ] **Step 3.3: Write the audio download template**

Create `.claude/skills/setup-new-dev-repo/download_audio_data.sh.template`:

```bash
#!/bin/bash
# download_audio_data.sh - download audio files for Formosan-{{CORPUS_NAME}}
# Requires: git-lfs, jq, hf (huggingface CLI)
set -euo pipefail

# TODO: fill in the actual download logic for this corpus.
# Common patterns:
#   - Hugging Face dataset: `hf download <repo> --local-dir <target>`
#   - git-lfs from a public repo: `git lfs pull`
#   - Direct URL list: `while read url; do curl -O "$url"; done < urls.txt`

echo "TODO: implement audio download for Formosan-{{CORPUS_NAME}}" >&2
exit 1
```

- [ ] **Step 3.4: Write the skill recipe**

Create `.claude/skills/setup-new-dev-repo.md`:

````markdown
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
2. Verify target directory `<parent_dir>/Formosan-<corpus_name>/` does NOT already exist. If it does, refuse — operator must delete first or choose a new name.

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
mkdir -p "<target>/{XML,CodeAndDocs}"
cd "<target>"
git init -b main
# If remote_url:
git remote add origin "<remote_url>"
```

### Phase 3: Create .venv

```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r "<formosanbank_path>/requirements.txt"
```

Capture pip output. If any install fails, surface immediately to user — do not continue with broken env.

### Phase 4: Scaffold layout

- Create placeholders: `XML/.gitkeep`, `CodeAndDocs/.gitkeep`.
- Generate `README.md` from `.claude/skills/setup-new-dev-repo/README.template.md`, substituting `{{CORPUS_NAME}}`, `{{LANGUAGE}}`, `{{CREATED_DATE}}` (today, YYYY-MM-DD).
- Copy `.claude/skills/setup-new-dev-repo/gitignore.template` to `.gitignore`.
- If `has_audio`: copy and substitute `download_audio_data.sh.template` to `download_audio_data.sh`; `chmod +x` it.

### Phase 5: Install Claude Code safety rails

- Create `<target>/.claude/hooks/check-venv.py` by copying from `<formosanbank_path>/.claude/hooks/check-venv.py`. (Copy the *file*; the new repo shouldn't depend on FormosanBank's filesystem location.)
- Create `<target>/.claude/settings.local.json` with:

```json
{
  "permissions": {
    "additionalDirectories": [
      "<parent_dir>"
    ]
  },
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
````

- [ ] **Step 3.5: Verify the skill file is valid markdown with frontmatter**

```bash
head -5 .claude/skills/setup-new-dev-repo.md
```

Expected: the first line is `---`, name and description are on subsequent lines, then `---` to close the frontmatter.

- [ ] **Step 3.6: Manual end-to-end recipe walkthrough**

Pick a throwaway corpus name (e.g., `TestSetup-DELETE_ME`) and invoke the skill mentally — or actually run it — against a temp parent dir:

```bash
TEST_PARENT=$(mktemp -d)
cd "$TEST_PARENT"
# Manually walk through phases 1–7 of the recipe targeting Formosan-TestSetup
# in this temp parent dir. Verify each phase produces the expected files.
ls -la Formosan-TestSetup/
test -d Formosan-TestSetup/XML
test -d Formosan-TestSetup/CodeAndDocs
test -d Formosan-TestSetup/.venv
test -f Formosan-TestSetup/README.md
test -f Formosan-TestSetup/.gitignore
test -f Formosan-TestSetup/.claude/hooks/check-venv.py
test -f Formosan-TestSetup/.claude/settings.local.json
python3 -m json.tool Formosan-TestSetup/.claude/settings.local.json > /dev/null
# Cleanup:
cd /
rm -rf "$TEST_PARENT"
```

Expected: every `test` command exits 0; the JSON validates.

- [ ] **Step 3.7: Commit**

```bash
git add .claude/skills/setup-new-dev-repo.md \
        .claude/skills/setup-new-dev-repo/
git commit -m "$(cat <<'EOF'
Add setup-new-dev-repo skill

Bootstraps a fresh Formosan-<CORPUS>/ development repo with standard layout,
Python .venv populated from FormosanBank requirements, README template, the
venv-check SessionStart hook, and a .gitignore matching repo conventions.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Skill — `run-qc-pipeline`

**Files:**
- Create: `.claude/skills/run-qc-pipeline.md`
- Create: `.claude/skills/run-qc-pipeline/summary.template.md`

- [ ] **Step 4.1: Write the QC-summary template**

Create `.claude/skills/run-qc-pipeline/summary.template.md`:

```markdown
# QC Summary: {{CORPUS_NAME}}

**Dev repo:** {{DEV_REPO_PATH}}
**Run timestamp:** {{TIMESTAMP_UTC}}
**XML location:** {{XML_PATH}}

## Orthography

- Original (determined in Phase 2): **{{ORIGINAL_ORTHOGRAPHY}}**
- Detector output that informed the decision: see `<output_dir>/orthography_detector.log`
- Standardize args used: `{{STANDARDIZE_ARGS}}`

## Counts

| Metric | Value |
|---|---|
| Texts | {{N_TEXTS}} |
| Sentences | {{N_SENTENCES}} |
| Words (W-tier) | {{N_WORDS_OR_NA}} |
| Morphemes (M-tier) | {{N_MORPHEMES_OR_NA}} |
| Languages | {{LANGUAGES_LIST}} |
| Dialects | {{DIALECTS_LIST}} |

## Hard-gate findings

| Check | Result | Notes |
|---|---|---|
| `validate_xml.py` (DTD) | {{XML_RESULT}} | {{XML_NOTES}} |
| `validate_punct.py` | {{PUNCT_RESULT}} | {{PUNCT_NOTES}} |
| `validate_glosses.py` | {{GLOSSES_RESULT_OR_NA}} | {{GLOSSES_NOTES}} |

## Soft checks (info-only)

| Check | Number | Note |
|---|---|---|
| Orthography similarity vs reference | {{ORTHO_SIM}} | Thresholds uncalibrated (B Phase B4 work) |
| Vocabulary overlap vs reference | {{VOCAB_OVERLAP}} | Cross-genre comparisons may be noisy |

## Unusual things surfaced

<!-- Anything the validators flagged that doesn't fit a category above, or that needs human judgment. -->

## Known limitations of this summary

- `validate_xml.py` may fail after Phase 4 (`add_phonology.py`) purely because the DTD currently has no `<PHON>` element. This is schema/code drift, not a corpus error. Resolving belongs to B's reconciliation work.

## Ready to port?

<!-- One-line verdict + reasoning. NOT a guarantee — the operator decides. -->
```

- [ ] **Step 4.2: Write the skill recipe**

Create `.claude/skills/run-qc-pipeline.md`:

````markdown
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

Run the detector:

```bash
.venv/bin/python3 <formosanbank_path>/QC/utilities/orthography_detector.py \
  --corpora_path <xml_path> 2>&1 | tee <output_dir>/02_orthography_detector.log
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
# DTD conformance
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_xml.py by_path \
  --path <xml_path> 2>&1 | tee <output_dir>/05a_validate_xml.log

# Orthography extraction
.venv/bin/python3 <formosanbank_path>/QC/orthography/orthography_extract.py \
  --corpus all --language All --kindOf standard --by_dialect true \
  --corpora_path <xml_path> \
  --output_dir <output_dir>/extract_logs 2>&1 | tee <output_dir>/05b_orthography_extract.log

# Orthography comparison vs reference
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_orthography.py \
  --o_info <output_dir>/extract_logs \
  --reference <formosanbank_path>/QC/validation/reference 2>&1 \
  | tee <output_dir>/05c_validate_orthography.log

# Vocabulary comparison vs reference
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_vocabulary.py \
  --o_info <output_dir>/extract_logs \
  --reference <formosanbank_path>/QC/validation/reference 2>&1 \
  | tee <output_dir>/05d_validate_vocabulary.log
```

Then check whether the corpus has `<W>` or `<M>` elements (quick grep across XML files). If yes:

```bash
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_glosses.py \
  <xml_path> --output_dir <output_dir> 2>&1 | tee <output_dir>/05e_validate_glosses.log
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
- `{{XML_RESULT}}`, `{{PUNCT_RESULT}}`, etc. — read each validator's log to determine pass/fail
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
````

- [ ] **Step 4.3: Verify the skill file is valid**

```bash
head -5 .claude/skills/run-qc-pipeline.md
```

Expected: frontmatter `---` / `name:` / `description:` / `---`.

- [ ] **Step 4.4: Manual recipe walkthrough — dry run**

Pick the most advanced unpublished dev repo (`Formosan-Nowbucyang-Truku-Thesis/`) and mentally trace through each phase. For each phase, verify:
- Required scripts exist at the cited paths in FormosanBank.
- The CLI flags shown actually exist (cross-check against the script's `argparse` definition).
- Logs go where the template expects.

If any phase calls a script that doesn't exist or uses a flag the script doesn't accept, fix the recipe before committing.

- [ ] **Step 4.5: Manual recipe walkthrough — wet run (optional but recommended)**

Run the recipe end-to-end against a small dev repo (or a copy of one). Verify the summary is produced and looks reasonable. This is the real validation; the dry run above only catches typos.

If you skip this step, mark "manually verified end-to-end" as **not done** and revisit before relying on the skill.

- [ ] **Step 4.6: Commit**

```bash
git add .claude/skills/run-qc-pipeline.md \
        .claude/skills/run-qc-pipeline/
git commit -m "$(cat <<'EOF'
Add run-qc-pipeline skill

Sequences the canonical QC pipeline on a Formosan-<CORPUS> dev repo:
clean_xml -> orthography_detector (HUMAN PAUSE) -> standardize ->
add_phonology -> validators. Produces a README-style summary at end.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Skill — `port-corpus-in`

**Files:**
- Create: `.claude/skills/port-corpus-in.md`
- Create: `.claude/skills/port-corpus-in/README.template.md`

- [ ] **Step 5.1: Write the published-corpus README template**

Create `.claude/skills/port-corpus-in/README.template.md`:

```markdown
# {{CORPUS_NAME}}

**Languages:** {{LANGUAGES}}
**Dialects:** {{DIALECTS}}
**Source:** {{SOURCE_DESCRIPTION}}
**License:** {{LICENSE}}

## Citation

<!-- APA-style citation(s). Multiple citations separated by | per FormosanBank XML format conventions. -->

{{CITATION}}

## Reproducibility

See `CodeAndDocs/` for the scripts that produce the contents of `XML/` from the original source data.

To rebuild from source:

<!-- Step-by-step instructions. Fill from the dev repo's README. -->

{{REPRODUCIBILITY_STEPS}}

## QC status

- Last QC run: {{LAST_QC_DATE}}
- Status: {{QC_VERDICT}}
- See dev repo: {{DEV_REPO_LINK_OR_NOTE}}

## Audio

{{AUDIO_STATUS}}
```

- [ ] **Step 5.2: Write the skill recipe**

Create `.claude/skills/port-corpus-in.md`:

````markdown
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
- What scripts exist at the root (likely belong in `CodeAndDocs/`)?
- What scratch dirs exist that should be dropped (`data/`, `raw_data/`, `Original/`, `img-by-page/`, `text-by-page/`, etc.)?
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
.venv/bin/python3 <formosanbank_path>/QC/validation/validate_xml.py by_path \
  --path "<formosanbank_path>/Corpora/<corpus_name>/XML"
```

(Use a venv that has the FormosanBank deps. If running from a dev repo's venv, that's fine.)

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
````

- [ ] **Step 5.3: Verify the skill file is valid**

```bash
head -5 .claude/skills/port-corpus-in.md
```

Expected: frontmatter present.

- [ ] **Step 5.4: Manual recipe walkthrough — dry run**

Pick a candidate unpublished dev repo (`Formosan-Nowbucyang-Truku-Thesis/`). Mentally trace through phases 1–5 against it. For each phase, verify:
- Pre-checks would pass (QC evidence exists or you'd surface to the user).
- The phase-1 layout assessment would correctly identify XML, scripts, scratch dirs.
- The phase-2 plan would map source paths to the standard target layout.
- Phase-4 validation would actually run.

If any phase makes an assumption that doesn't hold for this dev repo, fix the recipe.

- [ ] **Step 5.5: Manual recipe walkthrough — wet run (optional)**

If you have a corpus that's actually ready to port, run the recipe end-to-end. Otherwise, skip and mark as "needs first real port-in run before reliance."

- [ ] **Step 5.6: Commit**

```bash
git add .claude/skills/port-corpus-in.md \
        .claude/skills/port-corpus-in/
git commit -m "$(cat <<'EOF'
Add port-corpus-in skill

Interactive guided checklist for moving a QC'd corpus from its dev repo
into FormosanBank/Corpora/<Name>/ with the standard published layout.
Surfaces decisions for the operator rather than guessing.

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

---

## Post-implementation: cross-cutting verification

After all five tasks are committed, verify the whole hook+skill set works end-to-end in a fresh Claude Code session:

- [ ] **CC.1: `/clear` or start a new session** so the hooks are reloaded.

- [ ] **CC.2: Watch for the venv-check hook output** in session context. If `.venv` is healthy, output should be empty. If unhealthy, you'll see the `[venv-check] WARNING:` line.

- [ ] **CC.3: Try to edit something under `statistics/` via Claude.** The block-statistics hook should refuse with the explanatory message.

- [ ] **CC.4: List available skills** to confirm `setup-new-dev-repo`, `run-qc-pipeline`, and `port-corpus-in` show up under user-invocable skills.

- [ ] **CC.5: Optional**: invoke one of the skills against a throwaway target to verify end-to-end flow.

---

## Self-review checklist

Run through this once after writing the plan (not after each task — that's per-task TDD's job).

### Spec coverage

- [x] Item 1 (block-statistics hook) → Task 1
- [x] Item 4 (SessionStart venv check) → Task 2
- [x] Item 5 (setup-new-dev-repo) → Task 3
- [x] Item 2 (run-qc-pipeline) → Task 4
- [x] Item 3 (port-corpus-in) → Task 5
- [x] Cross-cutting plugin disables → already done per user (noted in spec, no task needed)
- [x] pyright-lsp investigation → already done earlier in session (verified marker plugin works)
- [x] Deferred backlog → not in scope (separate plan when triggered)

### Placeholder scan

- No "TBD" / "TODO" / "fill in" placeholders in the plan body (the README templates intentionally contain TBDs for the *user* to fill — that's the template's purpose, not a placeholder in the plan).
- All Python code is complete and runnable as shown.
- All shell commands have expected outputs documented.

### Type / name consistency

- Hook script file names match between the `Files:` section, settings.json registration, and tests.
- `CLAUDE_PROJECT_DIR` env var used consistently in both hooks and tests.
- Skill names match: `setup-new-dev-repo`, `run-qc-pipeline`, `port-corpus-in` — same in file names, frontmatter `name:`, and cross-references.

### Known uncertainties (not bugs, but worth flagging)

- The `CLAUDE_PROJECT_DIR` env var name is assumed. If the harness uses a different name, both hooks fall back to `os.getcwd()` which works for most scenarios but not all (e.g., `pwd` differs from the project root). If a fresh session shows hooks misbehaving, this is the first thing to check.
- The `SessionStart` hook's `matcher` field is omitted (no matcher means it always fires). If matchers are required, settings will need adjustment.
- The `add_phonology.py` -> `validate_xml.py` DTD failure is documented but not worked around in `run-qc-pipeline` Phase 5 — the validator will fail on DTD because `<PHON>` isn't in the schema. The summary template notes this. Real fix belongs to B.

---

## Execution handoff

Two options for executing this plan:

1. **Subagent-Driven (recommended)**: dispatch a fresh subagent per task, review between tasks. Best for catching mistakes early and keeping the main context lean.
2. **Inline execution**: execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

Which approach?
