# GitBook stats: single source of truth + port-time population — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `FormosanBank/statistics/` the single source of truth the GitBook reads from (deleting the GitBook's stale duplicate), and have `port-corpus-in` populate a newly-ported corpus's stats tables during the port.

**Architecture:** Redirect the two GitBook-side stats readers (`update_corpus_stats.py`, `manage_corpus_pages.py check`) at the sibling `FormosanBank/statistics/`; delete `FormosanBankGitbook/statistics/`; extend the skill's Phase 5 with a `get_corpus_stats` + inject step and a detect-and-guide audio-durations step. Spec: [docs/superpowers/specs/2026-06-15-gitbook-stats-single-source-design.md](../specs/2026-06-15-gitbook-stats-single-source-design.md).

**Tech Stack:** Python 3 stdlib (argparse, os, pathlib), pytest. Two repos: `FormosanBankGitbook` (`feature/corpus-page-tooling`) and `FormosanBank` worktree (`feature/gitbook-sync-part-d`).

**Repo paths in this environment:**
- GitBook repo: `/workspace/FormosanBankGitbook` (branch `feature/corpus-page-tooling`).
- FormosanBank worktree: `/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d` (branch `feature/gitbook-sync-part-d`).
- GitBook test python: `/workspace/FormosanBankGitbook/.venv/bin/python3`. FormosanBank python: `/workspace/FormosanBank/.venv/bin/python3`.

**Context the implementer needs:**
- `update_corpus_stats.py` currently hardcodes `STATS_DIR = REPO_ROOT / 'statistics'` (line 21) and `main()` (line 486) takes no args / no argparse. Functions read the module global `STATS_DIR` (lines 373, 496).
- `manage_corpus_pages.py` `run_check(gitbook_root, corpora_path, ignore_path)` sets `statistics = root / "statistics"` (line 222). `corpora_path` is `<FormosanBank>/Corpora`, so `Path(corpora_path).parent` is the FormosanBank root.
- The GitBook repo has a pytest harness from prior work (`tests/conftest.py`, `tests/test_manage_corpus_pages.py`, `pytest.ini` with `pythonpath = .`).

---

## File Structure

**GitBook repo:**
- Modify: `update_corpus_stats.py` — add `resolve_stats_dir()` + argparse in `main()`.
- Modify: `manage_corpus_pages.py` — `run_check` reads sister stats dir.
- Modify: `tests/conftest.py` — fixture's stats CSVs move under the sibling `FormosanBank/statistics`.
- Modify: `tests/test_manage_corpus_pages.py` — one stats reference updated.
- Create: `tests/test_update_corpus_stats.py` — `resolve_stats_dir` unit tests.
- Delete: `statistics/` (the stale duplicate).

**FormosanBank worktree:**
- Modify: `.claude/skills/port-corpus-in/SKILL.md` — Phase 5 stats + audio steps.
- Modify: `claudeplans/2026-05-27-roadmap.md` — Part D L1 item 1.
- Modify: `docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md` — flip the design-only note.

---

## Task 1: `resolve_stats_dir()` + argparse in `update_corpus_stats.py`

**Files:**
- Modify: `/workspace/FormosanBankGitbook/update_corpus_stats.py`
- Test: `/workspace/FormosanBankGitbook/tests/test_update_corpus_stats.py`

- [ ] **Step 1: Write the failing tests** — create `tests/test_update_corpus_stats.py`

```python
import os

import pytest

import update_corpus_stats as ucs


def test_resolve_prefers_cli_flag(tmp_path):
    d = tmp_path / "cli_stats"
    d.mkdir()
    out = ucs.resolve_stats_dir(cli_stats_dir=str(d), env={}, repo_root=tmp_path)
    assert out == d.resolve()


def test_resolve_uses_env_when_no_flag(tmp_path):
    d = tmp_path / "env_stats"
    d.mkdir()
    out = ucs.resolve_stats_dir(
        cli_stats_dir=None,
        env={"FORMOSANBANK_STATS_DIR": str(d)},
        repo_root=tmp_path,
    )
    assert out == d.resolve()


def test_resolve_defaults_to_sibling_formosanbank(tmp_path):
    # repo_root is the gitbook checkout; default is ../FormosanBank/statistics
    gitbook_root = tmp_path / "FormosanBankGitbook"
    gitbook_root.mkdir()
    sibling = tmp_path / "FormosanBank" / "statistics"
    sibling.mkdir(parents=True)
    out = ucs.resolve_stats_dir(cli_stats_dir=None, env={}, repo_root=gitbook_root)
    assert out == sibling.resolve()


def test_resolve_hard_errors_when_missing(tmp_path):
    with pytest.raises(SystemExit) as exc:
        ucs.resolve_stats_dir(cli_stats_dir=None, env={}, repo_root=tmp_path)
    assert "stats dir not found" in str(exc.value)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_update_corpus_stats.py -q 2>&1 | tail -12
```
Expected: FAIL — `AttributeError: module 'update_corpus_stats' has no attribute 'resolve_stats_dir'`.

- [ ] **Step 3: Add imports** — in `update_corpus_stats.py`, change the import block (currently `import csv` / `import re` / `from pathlib import Path`) to add `argparse` and `os`:

```python
import argparse
import csv
import os
import re
from pathlib import Path
```

- [ ] **Step 4: Add `resolve_stats_dir()`** — insert immediately after the `STATS_DIR = REPO_ROOT / 'statistics'` line (keep `STATS_DIR` as the module default; it is reassigned in `main()`):

```python
def resolve_stats_dir(cli_stats_dir=None, env=None, repo_root=None):
    """Resolve the canonical FormosanBank stats dir.

    Precedence: --stats-dir flag > FORMOSANBANK_STATS_DIR env > sibling
    <repo_root>/../FormosanBank/statistics. Hard-errors if the result is
    not an existing directory (never silently falls back).
    """
    repo_root = Path(repo_root) if repo_root is not None else REPO_ROOT
    env = env if env is not None else os.environ
    if cli_stats_dir:
        d = Path(cli_stats_dir)
    elif env.get("FORMOSANBANK_STATS_DIR"):
        d = Path(env["FORMOSANBANK_STATS_DIR"])
    else:
        d = repo_root.parent / "FormosanBank" / "statistics"
    d = d.resolve()
    if not d.is_dir():
        raise SystemExit(
            f"[update_corpus_stats] stats dir not found: {d}\n"
            f"Clone FormosanBank as a sibling of FormosanBankGitbook, "
            f"or pass --stats-dir <path>."
        )
    return d
```

- [ ] **Step 5: Run the tests to verify they pass**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_update_corpus_stats.py -q 2>&1 | tail -8
```
Expected: 4 passed.

- [ ] **Step 6: Wire it into `main()`** — change the start of `main()` (line ~486) so it parses args and sets the module-global `STATS_DIR` before any work. Replace:

```python
def main() -> None:
    print('Updating corpus markdown files with statistics…\n')
```

with:

```python
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inject corpus statistics tables into the GitBook markdown."
    )
    parser.add_argument(
        "--stats-dir",
        default=None,
        help="Path to FormosanBank/statistics (default: sibling FormosanBank "
             "checkout, or $FORMOSANBANK_STATS_DIR).",
    )
    args = parser.parse_args()

    global STATS_DIR
    STATS_DIR = resolve_stats_dir(cli_stats_dir=args.stats_dir)

    print(f'Reading stats from {STATS_DIR}\n')
    print('Updating corpus markdown files with statistics…\n')
```

- [ ] **Step 7: Smoke-test the CLI wiring**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 update_corpus_stats.py --help 2>&1 | head -8
```
Expected: argparse help text showing `--stats-dir`. (Do NOT run it without `--help` yet — that mutates the markdown; that happens in Task 7.)

- [ ] **Step 8: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add update_corpus_stats.py tests/test_update_corpus_stats.py
git commit -m "feat: update_corpus_stats reads canonical FormosanBank/statistics (sister)"
```

---

## Task 2: `manage_corpus_pages.py check` reads the sister stats dir

**Files:**
- Modify: `/workspace/FormosanBankGitbook/manage_corpus_pages.py`
- Modify: `/workspace/FormosanBankGitbook/tests/conftest.py`
- Modify: `/workspace/FormosanBankGitbook/tests/test_manage_corpus_pages.py`

- [ ] **Step 1: Update the conftest fixture** so the per-corpus stats CSVs live under the sibling FormosanBank dir, not the GitBook root.

In `tests/conftest.py`, **remove** the GitBook-root statistics creation (line ~68):
```python
    (root / "statistics").mkdir()
```
and the loop that writes CSVs there (lines ~76-77):
```python
    for name in ("ePark", "Wikipedias"):
        (root / "statistics" / f"{name}_corpora_stats.csv").write_text("x\n", encoding="utf-8")
```

Then, right after the `corpora = tmp_path / "FormosanBank" / "Corpora"` block (and its `mkdir` loop), **add**:
```python
    # per-corpus stats CSVs live in the canonical FormosanBank/statistics
    fb_statistics = tmp_path / "FormosanBank" / "statistics"
    fb_statistics.mkdir(parents=True)
    for name in ("ePark", "Wikipedias"):
        (fb_statistics / f"{name}_corpora_stats.csv").write_text("x\n", encoding="utf-8")
```

And expose it on the returned object — after `gb.corpora = corpora` add:
```python
    gb.fb_statistics = fb_statistics
```

- [ ] **Step 2: Point the failing test at the new location** — in `tests/test_manage_corpus_pages.py`, change the unlink in `test_check_missing_stats_csv_is_informational` (line ~168) from:
```python
    (gitbook.root / "statistics" / "Wikipedias_corpora_stats.csv").unlink()
```
to:
```python
    (gitbook.fb_statistics / "Wikipedias_corpora_stats.csv").unlink()
```

- [ ] **Step 3: Run the check tests to verify they now FAIL** (because `run_check` still reads `root / "statistics"`, which no longer exists)

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k check -q 2>&1 | tail -15
```
Expected: failures — `test_check_clean_tree_passes` etc. now report Wikipedias/ePark as missing stats CSVs (because `run_check` looks in the now-absent `root/statistics`).

- [ ] **Step 4: Update `run_check`** — in `manage_corpus_pages.py`, change line ~222 from:
```python
    statistics = root / "statistics"
```
to:
```python
    # canonical CSVs live in the sibling FormosanBank/statistics, not the GitBook repo
    statistics = corpora.parent / "statistics"
```

- [ ] **Step 5: Run the check tests to verify they pass**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k check -q 2>&1 | tail -8
```
Expected: 7 passed.

- [ ] **Step 6: Run the whole suite** (nothing else regressed)

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/ -q 2>&1 | tail -3
```
Expected: all pass (24 tests: 20 prior + 4 new from Task 1).

- [ ] **Step 7: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add manage_corpus_pages.py tests/conftest.py tests/test_manage_corpus_pages.py
git commit -m "feat: check reads stats CSVs from sister FormosanBank/statistics"
```

---

## Task 3: Delete the GitBook's stale `statistics/` duplicate

**Files:**
- Delete: `/workspace/FormosanBankGitbook/statistics/`

- [ ] **Step 1: Confirm nothing else reads `statistics/`** (only `update_corpus_stats.py`, now redirected)

Run:
```bash
cd /workspace/FormosanBankGitbook
grep -rIl "statistics" --include=*.py --include=*.yaml --include=*.yml . | grep -v tests/ | grep -v '\.venv'
grep -rn "REPO_ROOT / 'statistics'\|root / \"statistics\"\|/statistics" --include=*.py . | grep -v '\.venv' | grep -v tests/
```
Expected: the only remaining references are the `resolve_stats_dir` default-path construction and comments — no code still reads `REPO_ROOT/'statistics'` as the active dir. If anything else reads the local `statistics/`, STOP and report.

- [ ] **Step 2: Delete the directory**

Run:
```bash
cd /workspace/FormosanBankGitbook
git rm -r statistics/
```

- [ ] **Step 3: Confirm the test suite still passes** (it uses the fixture's sibling stats, not this dir)

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/ -q 2>&1 | tail -3
```
Expected: all pass (24 tests).

- [ ] **Step 4: Commit**

```bash
cd /workspace/FormosanBankGitbook
git commit -m "chore: delete stale GitBook statistics/ duplicate (read FormosanBank now)"
```

---

## Task 4: Add stats + audio steps to `port-corpus-in` Phase 5

**Files:**
- Modify: `/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/.claude/skills/port-corpus-in/SKILL.md`

- [ ] **Step 1: Read the current Phase 5** to find the insertion points

Run:
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
grep -n "Scaffold the four integration points\|Fill the prose\|Verify the page is fully wired" .claude/skills/port-corpus-in/SKILL.md
```
The new steps go **after** the "Verify the page is fully wired" step (step 6 of Phase 5) — they need the page wired and prose filled first.

- [ ] **Step 2: Insert the audio + stats steps** — after Phase 5 step 6 (the `check --strict` verify step) and before the closing of Phase 5, add:

````markdown
7. **Populate the stats tables (audio-aware).** The page's stats block and the
   `corpora/README.md` aggregate are filled by `update_corpus_stats.py` from the
   corpus's stats CSV. Generate that CSV and inject it, in this order:

   a. **Audio gate (detect + guide).** Check whether the ported XML has audio:
      ```bash
      grep -rl "<AUDIO" "<formosanbank_path>/Corpora/<corpus_name>/XML" | head -1
      ```
      - **No match (no audio):** skip to step 7b.
      - **Has audio:** the audio-seconds columns need `statistics/audio_durations.csv`
        populated for this corpus *before* `get_corpus_stats` runs (otherwise audio
        seconds are 0). Do NOT automate this — surface the choice to the maintainer
        via `AskUserQuestion`:
        - *Audio is available locally* (downloaded into the corpus dir) →
          `<python> <formosanbank_path>/QC/utilities/update_audio_stats.py Corpora/<corpus_name>`
        - *Audio is only on Hugging Face* (`download_audio_data.sh` ported + uploaded) →
          use the `refresh-audio-stats` skill / `refresh_audio_stats.py <corpus_name>`
        - *Maintainer chooses to skip:* proceed; note in the Phase 6 summary that the
          page's audio columns are pending a later `refresh-audio-stats` run.

   b. **Generate the per-corpus stats CSV:**
      ```bash
      <python> <formosanbank_path>/QC/utilities/get_corpus_stats.py \
        "<formosanbank_path>/Corpora/<corpus_name>"
      ```
      This writes `<formosanbank_path>/statistics/<corpus_name>_corpora_stats.csv`.
      Commit it with the corpus (CI later regenerates the identical CSV via `--all`).

   c. **Inject the tables into the GitBook:**
      ```bash
      <python> <gitbook_path>/update_corpus_stats.py --stats-dir "<formosanbank_path>/statistics"
      ```
      Pass `--stats-dir` explicitly so it reads the *active* FormosanBank checkout
      (the sibling default may point at a different checkout that lacks the new CSV).
      This fills the new page's stats block and refreshes the `corpora/README.md`
      aggregate. Commit the changed `.md` in the GitBook repo.

   d. **Re-verify:** `manage_corpus_pages.py check --strict` passes and the new
      corpus's "missing stats CSV" informational line is gone.
````

- [ ] **Step 3: Update the Phase 6 summary bullet** — find the Phase 6 summary's GitBook line and add that the stats tables were populated (or, if audio was skipped, that audio columns are pending). Locate it:
```bash
grep -n "GitBook page:" .claude/skills/port-corpus-in/SKILL.md
```
Add a sibling bullet after it:
```markdown
- Stats tables populated from `<corpus_name>_corpora_stats.csv` (audio columns pending if the audio-durations step was skipped).
```

- [ ] **Step 4: Sanity-check the skill file structure**

Run:
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
grep -n "### Phase\|^7\. \*\*Populate" .claude/skills/port-corpus-in/SKILL.md
```
Expected: Phases 1–6 intact, with the new step 7 under Phase 5.

- [ ] **Step 5: Commit**

```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
git add .claude/skills/port-corpus-in/SKILL.md
git commit -m "feat(port-corpus-in): Phase 5 populates stats tables (audio-aware)"
```

---

## Task 5: Update roadmap + prior spec note

**Files:**
- Modify: `/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/claudeplans/2026-05-27-roadmap.md`
- Modify: `/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md`

- [ ] **Step 1: Update Part D Layer 1 item 1** — read it first:
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
grep -n "GitHub Actions workflow in \`FormosanBankGitbook\` for stats CSV regeneration" claudeplans/2026-05-27-roadmap.md
```
Change that `[NOT STARTED]` item to `[DONE — via sister-read]` with a one-line note: the cross-repo stats-CSV duplication is removed by pointing `update_corpus_stats.py` + `manage_corpus_pages.py check` at the canonical `FormosanBank/statistics`; per-corpus population happens in `port-corpus-in` Phase 5. Reference `docs/superpowers/specs/2026-06-15-gitbook-stats-single-source-design.md`.

- [ ] **Step 2: Flip the prior spec's design-only note** — in `docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md`, find the line describing "L1 cross-repo stats-CSV regeneration" as DESIGN-ONLY:
```bash
grep -n "cross-repo stats-CSV regeneration\|cross-repo stats sync" docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md
```
Append to that line: ` — **resolved 2026-06-15 via sister-read; see [2026-06-15-gitbook-stats-single-source-design.md](2026-06-15-gitbook-stats-single-source-design.md).**`

- [ ] **Step 3: Commit**

```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
git add claudeplans/2026-05-27-roadmap.md docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md
git commit -m "docs: mark Part D L1 cross-repo stats sync resolved via sister-read"
```

---

## Task 6: Integration — refresh all tables + populate Nowbucyang, verify

**This task is operational (no new unit tests). It exercises the whole change end-to-end against the real repos and produces the one-time refresh diff.**

**Files:** mutates GitBook `.md` (all corpus pages + `corpora/README.md`) and `FormosanBank/statistics/Nowbucyang-Truku-Thesis_corpora_stats.csv`.

- [ ] **Step 1: One-time refresh of all GitBook stats tables** from the canonical FormosanBank stats (the stale April → current diff). Use the worktree's statistics as the source so it's consistent with where Nowbucyang's CSV will land:
```bash
cd /workspace/FormosanBankGitbook
/workspace/FormosanBank/.venv/bin/python3 update_corpus_stats.py \
  --stats-dir /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/statistics 2>&1 | tail -5
git add en-us/the-bank-architecture/corpora/  # injector only touches corpus pages + README; avoids unrelated pre-existing en-us edits
git commit -m "refresh: regenerate all GitBook stats tables from FormosanBank/statistics"
```
Expected: it processes each corpus CSV and "Updated README.md". The diff is large but text-only (table cells). Note: Nowbucyang is NOT included yet (its CSV doesn't exist).

- [ ] **Step 2: Generate Nowbucyang's per-corpus CSV**
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
/workspace/FormosanBank/.venv/bin/python3 QC/utilities/get_corpus_stats.py \
  Corpora/Nowbucyang-Truku-Thesis 2>&1 | tail -3
ls -la statistics/Nowbucyang-Truku-Thesis_corpora_stats.csv
git add statistics/Nowbucyang-Truku-Thesis_corpora_stats.csv
git commit -m "stats: add Nowbucyang-Truku-Thesis_corpora_stats.csv"
```
Expected: "Corpus statistics saved to …Nowbucyang-Truku-Thesis_corpora_stats.csv".

- [ ] **Step 3: Inject Nowbucyang's tables into the GitBook**
```bash
cd /workspace/FormosanBankGitbook
/workspace/FormosanBank/.venv/bin/python3 update_corpus_stats.py \
  --stats-dir /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/statistics 2>&1 | grep -i nowbucyang
git add en-us/the-bank-architecture/corpora/  # injector only touches corpus pages + README; avoids unrelated pre-existing en-us edits
git commit -m "stats: populate Nowbucyang-Truku-Thesis GitBook tables"
```
Expected: a line showing `Nowbucyang-Truku-Thesis_corpora_stats.csv` processed; the new page's `<!-- CORPUS STATS START -->` block now contains a table.

- [ ] **Step 4: Verify the page is populated and the lint is clean**
```bash
cd /workspace/FormosanBankGitbook
sed -n '/CORPUS STATS START/,/CORPUS STATS END/p' \
  en-us/the-bank-architecture/corpora/nowbucyang-truku-thesis.md | head -20
/workspace/FormosanBank/.venv/bin/python3 manage_corpus_pages.py check \
  --gitbook-root . \
  --corpora-path /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/Corpora \
  --strict 2>&1 | grep -E "Integration issues|Missing stats|OK:|FAIL"
```
Expected: the page's stats block now shows a `| | Truku |` table (word count etc.); `check --strict` prints `Integration issues (gating): 0`, the "Missing stats CSVs" count no longer lists Nowbucyang, and `OK:`. Exit 0.

- [ ] **Step 5: Report the two repos' new commits** for the operator's PRs (no further commit needed — each step above committed).

---

## Self-review notes

- **Spec coverage:** Change 1 → Tasks 1–3; Change 2 → Task 4 (skill steps 7b/7c) + Task 6 (live exercise); Change 3 → Task 4 (skill step 7a); roadmap/prior-spec → Task 5; acceptance (Nowbucyang populated, lint clean) → Task 6.
- **Names used consistently:** `resolve_stats_dir(cli_stats_dir, env, repo_root)`, module global `STATS_DIR`, `--stats-dir`, `FORMOSANBANK_STATS_DIR`, `gb.fb_statistics`, `corpora.parent / "statistics"`.
- **Audio handled detect-and-guide only** (Task 4 step 7a) — no automation, matching the spec.
- **No CSV relocation:** `FormosanBank/statistics/` is untouched as the write target; only GitBook readers change and the GitBook duplicate is deleted.
- **Ordering enforced** in the skill: audio-durations (7a) → `get_corpus_stats` (7b) → `update_corpus_stats` (7c).
