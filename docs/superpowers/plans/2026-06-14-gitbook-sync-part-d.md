# GitBook sync (Part D) + port-corpus-in GitBook integration — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make porting a corpus also publish its GitBook page, via a reusable `manage_corpus_pages.py` helper (GitBook repo) whose `check` mode doubles as a CI drift lint; then port `Formosan-Nowbucyang-Truku-Thesis` live to exercise it.

**Architecture:** A hybrid helper in the GitBook repo owns the three mechanical integration points (page file, `SUMMARY.md` nav bullet, `CSV_TO_MD` stats-map entry); prose is filled by the `port-corpus-in` skill. The same helper's `check` subcommand is the Layer-1 drift lint and runs in a new GitBook CI workflow. Spec: [docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md](../specs/2026-06-14-gitbook-sync-part-d-design.md).

**Tech Stack:** Python 3.13/3.14 stdlib only (argparse, pathlib, re), pytest. Two repos: `FormosanBankGitbook` (helper, tests, CI, ignore-list) and `FormosanBank` (skill template, SKILL.md, roadmap).

**Repo paths in this environment:**
- GitBook repo: `/workspace/FormosanBankGitbook` (its own git repo; cut a branch `feature/corpus-page-tooling` before editing — Task 0).
- FormosanBank worktree: `/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d` (branch `feature/gitbook-sync-part-d`, already created).
- GitBook Python: `/workspace/FormosanBankGitbook/.venv/bin/python3`.

---

## File Structure

**GitBook repo (`/workspace/FormosanBankGitbook`):**
- Create: `manage_corpus_pages.py` — the helper (add + check subcommands + pure text-transform functions).
- Create: `corpus_pages_ignore.txt` — documented list of `Corpora/` dirs intentionally not published.
- Create: `requirements-dev.txt` — `pytest`.
- Create: `tests/conftest.py` — fixture building a miniature GitBook tree + fake `Corpora/`.
- Create: `tests/test_manage_corpus_pages.py` — unit tests.
- Create: `tests/fixtures/corpus_page.template.md` — minimal template for `add` tests.
- Create: `.github/workflows/corpus-page-lint.yaml` — CI running `check --strict`.

**FormosanBank repo (worktree):**
- Create: `.claude/skills/port-corpus-in/corpus_page.template.md` — the real page template.
- Modify: `.claude/skills/port-corpus-in/SKILL.md` — insert Phase 5 "Add to GitBook", renumber summary to Phase 6.
- Modify: `claudeplans/2026-05-27-roadmap.md` — update Part D status.

---

## Task 0: Cut the GitBook working branch

**Files:** none (git only).

- [ ] **Step 1: Create a feature branch in the GitBook repo**

The GitBook repo is currently on `main`. Branch off it so helper/CI work is isolated (the publish-branch decision for *content* happens later, at live-port time).

Run:
```bash
cd /workspace/FormosanBankGitbook
git checkout -b feature/corpus-page-tooling
git rev-parse --abbrev-ref HEAD
```
Expected: `feature/corpus-page-tooling`

- [ ] **Step 2: Commit nothing yet** — proceed to Task 1.

---

## Task 1: GitBook test infrastructure + template fixture

**Files:**
- Create: `/workspace/FormosanBankGitbook/requirements-dev.txt`
- Create: `/workspace/FormosanBankGitbook/pytest.ini`
- Create: `/workspace/FormosanBankGitbook/tests/conftest.py`
- Create: `/workspace/FormosanBankGitbook/tests/fixtures/corpus_page.template.md`

- [ ] **Step 1: Write `requirements-dev.txt`**

```
pytest>=8.0
```

- [ ] **Step 1b: Write `pytest.ini`** so `import manage_corpus_pages` (a repo-root module) resolves regardless of how pytest is invoked:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

- [ ] **Step 2: Write the template fixture** `tests/fixtures/corpus_page.template.md`

```markdown
# {{TITLE}}

{{DESCRIPTION}}

***

<!-- CORPUS STATS START -->
<!-- CORPUS STATS END -->

## **Access Details**

{{ACCESS}}

***

## **Copyright**

{{COPYRIGHT}}

***

## Citation

{{CITATION}}
```

- [ ] **Step 3: Write `tests/conftest.py`** — a fixture that builds a miniature but realistic GitBook tree plus a fake FormosanBank `Corpora/`.

```python
import textwrap
from pathlib import Path

import pytest


SUMMARY_TEMPLATE = """\
# Table of contents

* [Welcome](README.md)

## The Bank Architecture

* [Corpora](the-bank-architecture/corpora/README.md)
  * [ePark](the-bank-architecture/corpora/epark.md)
  * [Wikipedias](the-bank-architecture/corpora/wikipedias.md)
* [Developers](the-bank-architecture/developers/README.md)
  * [Folder structure](the-bank-architecture/developers/folder-structure.md)
"""

UPDATE_STATS_TEMPLATE = '''\
"""Fake update_corpus_stats.py for tests."""

CSV_TO_MD = {
    'ePark_corpora_stats.csv':      'epark.md',
    'Wikipedias_corpora_stats.csv': 'wikipedias.md',
}


def main():
    pass
'''


@pytest.fixture
def gitbook(tmp_path):
    """Build a miniature GitBook repo + sibling FormosanBank/Corpora.

    Returns an object with .root (gitbook), .corpora (FB Corpora dir),
    and helpers to read SUMMARY/update_corpus_stats back.
    """
    root = tmp_path / "FormosanBankGitbook"
    corpora_pages = root / "en-us" / "the-bank-architecture" / "corpora"
    corpora_pages.mkdir(parents=True)
    (root / "statistics").mkdir()

    # Two existing, fully-wired corpora: ePark, Wikipedias
    (corpora_pages / "epark.md").write_text("# ePark\n\nText.\n", encoding="utf-8")
    (corpora_pages / "wikipedias.md").write_text("# Wikipedias\n\nText.\n", encoding="utf-8")
    (root / "en-us" / "SUMMARY.md").write_text(SUMMARY_TEMPLATE, encoding="utf-8")
    (root / "update_corpus_stats.py").write_text(UPDATE_STATS_TEMPLATE, encoding="utf-8")
    for name in ("ePark", "Wikipedias"):
        (root / "statistics" / f"{name}_corpora_stats.csv").write_text("x\n", encoding="utf-8")

    # parallel translation trees (pwn missing wikipedias -> translation lag)
    pwn = root / "pwn" / "the-bank-architecture" / "corpora"
    pwn.mkdir(parents=True)
    (pwn / "epark.md").write_text("# ePark\n", encoding="utf-8")
    zh = root / "zh-TW" / "the-bank-architecture" / "corpora"
    zh.mkdir(parents=True)
    (zh / "epark.md").write_text("# ePark\n", encoding="utf-8")

    # fake FormosanBank Corpora with ePark + Wikipedias shipped
    corpora = tmp_path / "FormosanBank" / "Corpora"
    for name in ("ePark", "Wikipedias"):
        (corpora / name / "XML").mkdir(parents=True)

    class GB:
        pass

    gb = GB()
    gb.root = root
    gb.corpora = corpora
    gb.summary = root / "en-us" / "SUMMARY.md"
    gb.stats_script = root / "update_corpus_stats.py"
    gb.pages = corpora_pages
    gb.template = Path(__file__).parent / "fixtures" / "corpus_page.template.md"
    return gb
```

- [ ] **Step 4: Verify pytest collects (no tests yet is fine)**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/ -q 2>&1 | tail -5
```
Expected: `no tests ran` (pytest may need install — if `pytest` missing, run `.venv/bin/python3 -m pip install -r requirements-dev.txt` first).

- [ ] **Step 5: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add requirements-dev.txt pytest.ini tests/conftest.py tests/fixtures/corpus_page.template.md
git commit -m "test: GitBook test scaffold + page template fixture"
```

---

## Task 2: Pure text-transform functions — `render_page`, `insert_nav_entry`, `insert_csv_to_md_entry`

**Files:**
- Create: `/workspace/FormosanBankGitbook/manage_corpus_pages.py`
- Test: `/workspace/FormosanBankGitbook/tests/test_manage_corpus_pages.py`

- [ ] **Step 1: Write failing tests** for the three pure functions in `tests/test_manage_corpus_pages.py`

```python
import manage_corpus_pages as mcp


def test_render_page_substitutes_title_only():
    tpl = "# {{TITLE}}\n\n{{DESCRIPTION}}\n"
    out = mcp.render_page(tpl, "My Corpus")
    assert "# My Corpus" in out
    assert "{{DESCRIPTION}}" in out  # prose left for the skill


def test_insert_nav_entry_appends_after_last_corpora_subbullet(gitbook):
    text = gitbook.summary.read_text(encoding="utf-8")
    out = mcp.insert_nav_entry(text, "newcorpus.md", "New Corpus")
    lines = out.splitlines()
    # inserted as an indented sub-bullet, immediately before Developers
    nav_idx = next(i for i, l in enumerate(lines) if "corpora/newcorpus.md" in l)
    dev_idx = next(i for i, l in enumerate(lines) if "developers/README.md" in l)
    assert lines[nav_idx].startswith("  * [New Corpus]")
    assert nav_idx < dev_idx
    # last existing sub-bullet (wikipedias) stays before the new one
    wiki_idx = next(i for i, l in enumerate(lines) if "corpora/wikipedias.md" in l)
    assert wiki_idx < nav_idx


def test_insert_nav_entry_idempotent(gitbook):
    text = gitbook.summary.read_text(encoding="utf-8")
    once = mcp.insert_nav_entry(text, "newcorpus.md", "New Corpus")
    twice = mcp.insert_nav_entry(once, "newcorpus.md", "New Corpus")
    assert once == twice


def test_insert_csv_to_md_entry_appends_before_close(gitbook):
    text = gitbook.stats_script.read_text(encoding="utf-8")
    out = mcp.insert_csv_to_md_entry(text, "NewCorpus", "newcorpus.md")
    assert "'NewCorpus_corpora_stats.csv': 'newcorpus.md'," in out
    # entry sits inside the dict, before its closing brace
    lines = out.splitlines()
    entry_idx = next(i for i, l in enumerate(lines) if "NewCorpus_corpora_stats.csv" in l)
    close_idx = next(i for i, l in enumerate(lines) if l.rstrip() == "}")
    assert entry_idx < close_idx
    # still valid Python
    ns = {}
    exec(out, ns)
    assert ns["CSV_TO_MD"]["NewCorpus_corpora_stats.csv"] == "newcorpus.md"


def test_insert_csv_to_md_entry_idempotent(gitbook):
    text = gitbook.stats_script.read_text(encoding="utf-8")
    once = mcp.insert_csv_to_md_entry(text, "NewCorpus", "newcorpus.md")
    twice = mcp.insert_csv_to_md_entry(once, "NewCorpus", "newcorpus.md")
    assert once == twice
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -q 2>&1 | tail -15
```
Expected: FAIL — `ModuleNotFoundError: No module named 'manage_corpus_pages'` (or AttributeError once the file exists but functions don't).

- [ ] **Step 3: Implement the three functions** in `manage_corpus_pages.py`

```python
#!/usr/bin/env python3
"""Manage FormosanBank GitBook corpus pages.

Two subcommands:
  add    scaffold a new corpus page + nav entry + CSV_TO_MD stats-map entry
  check  drift lint: every shipped corpus is fully wired; no leftover
         placeholders; (informational) Coming-Soon drift + translation lag

The three integration points for a published corpus are:
  1. en-us/the-bank-architecture/corpora/<slug>          (the page)
  2. a sub-bullet in en-us/SUMMARY.md                    (the nav entry)
  3. a CSV_TO_MD entry in update_corpus_stats.py         (the stats map)
"""
import argparse
import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"\{\{[A-Z_]+\}\}")
CORPORA_LINK = "the-bank-architecture/corpora/"


def render_page(template_text: str, title: str) -> str:
    """Substitute {{TITLE}} only; leave prose placeholders for the skill."""
    return template_text.replace("{{TITLE}}", title)


def insert_nav_entry(summary_text: str, slug: str, label: str) -> str:
    """Insert an indented Corpora sub-bullet for <slug> as the last sub-bullet.

    Idempotent: if a bullet already links to corpora/<slug>, returns unchanged.
    """
    link = f"{CORPORA_LINK}{slug}"
    if f"({link})" in summary_text:
        return summary_text
    lines = summary_text.splitlines(keepends=True)
    last_idx = None
    for i, line in enumerate(lines):
        # indented sub-bullet (excludes the top-level "* [Corpora]" line)
        if line[:1].isspace() and line.lstrip().startswith("*") and CORPORA_LINK in line:
            last_idx = i
    if last_idx is None:
        raise ValueError("Could not locate the Corpora sub-list in SUMMARY.md")
    indent = lines[last_idx][: len(lines[last_idx]) - len(lines[last_idx].lstrip())]
    entry = f"{indent}* [{label}]({link})\n"
    # ensure the anchor line ends with a newline before inserting after it
    if not lines[last_idx].endswith("\n"):
        lines[last_idx] = lines[last_idx] + "\n"
    lines.insert(last_idx + 1, entry)
    return "".join(lines)


def insert_csv_to_md_entry(script_text: str, fbdir: str, slug: str) -> str:
    """Append '<fbdir>_corpora_stats.csv': '<slug>', before CSV_TO_MD's close.

    Idempotent: if the key already exists, returns unchanged.
    """
    key = f"'{fbdir}_corpora_stats.csv'"
    if key in script_text:
        return script_text
    lines = script_text.splitlines(keepends=True)
    start = next((i for i, l in enumerate(lines) if l.startswith("CSV_TO_MD")), None)
    if start is None:
        raise ValueError("CSV_TO_MD not found in update_corpus_stats.py")
    close = next((i for i in range(start, len(lines)) if lines[i].rstrip() == "}"), None)
    if close is None:
        raise ValueError("CSV_TO_MD closing brace not found")
    lines.insert(close, f"    {key}: '{slug}',\n")
    return "".join(lines)
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -q 2>&1 | tail -15
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add manage_corpus_pages.py tests/test_manage_corpus_pages.py
git commit -m "feat: corpus-page text-transform helpers (render/nav/stats-map)"
```

---

## Task 3: `add` subcommand orchestration + CLI

**Files:**
- Modify: `/workspace/FormosanBankGitbook/manage_corpus_pages.py`
- Test: `/workspace/FormosanBankGitbook/tests/test_manage_corpus_pages.py`

- [ ] **Step 1: Write failing tests** (append to `tests/test_manage_corpus_pages.py`)

```python
def test_cmd_add_wires_all_three_points(gitbook):
    rc = mcp.cmd_add(
        corpus="NewCorpus",
        slug="newcorpus.md",
        nav_label="New Corpus",
        title="New Corpus",
        template=str(gitbook.template),
        gitbook_root=str(gitbook.root),
    )
    assert rc == 0
    page = gitbook.pages / "newcorpus.md"
    assert page.exists()
    assert "# New Corpus" in page.read_text(encoding="utf-8")
    assert "{{DESCRIPTION}}" in page.read_text(encoding="utf-8")  # prose left
    assert "corpora/newcorpus.md" in gitbook.summary.read_text(encoding="utf-8")
    assert "NewCorpus_corpora_stats.csv" in gitbook.stats_script.read_text(encoding="utf-8")


def test_cmd_add_is_idempotent(gitbook):
    kwargs = dict(
        corpus="NewCorpus", slug="newcorpus.md", nav_label="New Corpus",
        title="New Corpus", template=str(gitbook.template),
        gitbook_root=str(gitbook.root),
    )
    assert mcp.cmd_add(**kwargs) == 0
    summary_after_1 = gitbook.summary.read_text(encoding="utf-8")
    script_after_1 = gitbook.stats_script.read_text(encoding="utf-8")
    assert mcp.cmd_add(**kwargs) == 0  # second run: clean no-op
    assert gitbook.summary.read_text(encoding="utf-8") == summary_after_1
    assert gitbook.stats_script.read_text(encoding="utf-8") == script_after_1


def test_cmd_add_missing_template_errors(gitbook):
    with pytest.raises(FileNotFoundError):
        mcp.cmd_add(
            corpus="NewCorpus", slug="newcorpus.md", nav_label="New Corpus",
            title="New Corpus", template=str(gitbook.root / "nope.md"),
            gitbook_root=str(gitbook.root),
        )
```

Add `import pytest` at the top of the test file if not already present.

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k cmd_add -q 2>&1 | tail -15
```
Expected: FAIL — `AttributeError: module 'manage_corpus_pages' has no attribute 'cmd_add'`.

- [ ] **Step 3: Implement `cmd_add`** (append to `manage_corpus_pages.py`, before the CLI section you add in Task 5)

```python
def cmd_add(corpus, slug, nav_label, title, template, gitbook_root):
    """Wire a corpus's three integration points idempotently. Returns 0/exit code."""
    root = Path(gitbook_root)
    page_path = root / "en-us" / "the-bank-architecture" / "corpora" / slug
    summary_path = root / "en-us" / "SUMMARY.md"
    stats_script = root / "update_corpus_stats.py"

    report = []

    if page_path.exists():
        report.append(("page", "already present"))
    else:
        template_text = Path(template).read_text(encoding="utf-8")  # raises if missing
        page_path.write_text(render_page(template_text, title), encoding="utf-8")
        report.append(("page", "created"))

    summary_text = summary_path.read_text(encoding="utf-8")
    new_summary = insert_nav_entry(summary_text, slug, nav_label)
    if new_summary != summary_text:
        summary_path.write_text(new_summary, encoding="utf-8")
        report.append(("nav", "created"))
    else:
        report.append(("nav", "already present"))

    script_text = stats_script.read_text(encoding="utf-8")
    new_script = insert_csv_to_md_entry(script_text, corpus, slug)
    if new_script != script_text:
        stats_script.write_text(new_script, encoding="utf-8")
        report.append(("stats_map", "created"))
    else:
        report.append(("stats_map", "already present"))

    for name, status in report:
        print(f"  {name}: {status}")
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k cmd_add -q 2>&1 | tail -15
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add manage_corpus_pages.py tests/test_manage_corpus_pages.py
git commit -m "feat: add subcommand orchestration (idempotent corpus-page wiring)"
```

---

## Task 4: `check` subcommand — drift lint + translation lag

**Files:**
- Modify: `/workspace/FormosanBankGitbook/manage_corpus_pages.py`
- Test: `/workspace/FormosanBankGitbook/tests/test_manage_corpus_pages.py`

- [ ] **Step 1: Write failing tests** (append to `tests/test_manage_corpus_pages.py`)

```python
def test_check_clean_tree_passes(gitbook):
    result = mcp.run_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=None,
    )
    assert result.integration_issues == []
    assert result.placeholder_issues == []
    # wikipedias present in en-us but missing from pwn + zh-TW -> lag (informational)
    assert any("wikipedias.md" in m for m in result.translation_lag)
    assert result.ok is True  # ok ignores informational lag


def test_check_detects_missing_integration(gitbook):
    # ship a third corpus with no page/nav/map/csv
    (gitbook.corpora / "Orphan" / "XML").mkdir(parents=True)
    result = mcp.run_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=None,
    )
    joined = " ".join(result.integration_issues)
    assert "Orphan" in joined
    assert result.ok is False


def test_check_ignore_list_suppresses(gitbook, tmp_path):
    (gitbook.corpora / "Orphan" / "XML").mkdir(parents=True)
    ignore = tmp_path / "ignore.txt"
    ignore.write_text("# intentional\nOrphan\n", encoding="utf-8")
    result = mcp.run_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=str(ignore),
    )
    assert all("Orphan" not in m for m in result.integration_issues)
    assert result.ok is True


def test_check_detects_leftover_placeholder(gitbook):
    (gitbook.pages / "epark.md").write_text("# ePark\n\n{{DESCRIPTION}}\n", encoding="utf-8")
    result = mcp.run_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=None,
    )
    assert any("epark.md" in m for m in result.placeholder_issues)
    assert result.ok is False


def test_check_coming_soon_is_informational_not_gating(gitbook):
    readme = gitbook.root / "en-us" / "the-bank-architecture" / "corpora" / "README.md"
    readme.write_text("Coming Soon: Wikipedias is on the way.\n", encoding="utf-8")
    result = mcp.run_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=None,
    )
    assert any("Wikipedias" in m for m in result.coming_soon)
    assert result.ok is True  # coming-soon never gates
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k check -q 2>&1 | tail -15
```
Expected: FAIL — `AttributeError: module 'manage_corpus_pages' has no attribute 'run_check'`.

- [ ] **Step 3: Implement the check internals** (append to `manage_corpus_pages.py`)

```python
from dataclasses import dataclass, field


@dataclass
class CheckResult:
    integration_issues: list = field(default_factory=list)
    placeholder_issues: list = field(default_factory=list)
    coming_soon: list = field(default_factory=list)       # informational
    translation_lag: list = field(default_factory=list)   # informational

    @property
    def ok(self) -> bool:
        # only integration + placeholders gate
        return not self.integration_issues and not self.placeholder_issues


def find_shipped_corpora(corpora_path: Path) -> list:
    return sorted(
        d.name for d in corpora_path.iterdir()
        if d.is_dir() and (d / "XML").is_dir()
    )


def load_ignore(ignore_path) -> set:
    if not ignore_path:
        return set()
    p = Path(ignore_path)
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line)
    return out


def parse_csv_to_md(script_text: str) -> dict:
    result = {}
    in_dict = False
    for line in script_text.splitlines():
        if line.startswith("CSV_TO_MD"):
            in_dict = True
            continue
        if in_dict and line.rstrip() == "}":
            break
        if in_dict:
            m = re.search(r"'([^']+)'\s*:\s*'([^']+)'", line)
            if m:
                result[m.group(1)] = m.group(2)
    return result


def run_check(gitbook_root, corpora_path, ignore_path) -> CheckResult:
    root = Path(gitbook_root)
    corpora = Path(corpora_path)
    pages_dir = root / "en-us" / "the-bank-architecture" / "corpora"
    summary_text = (root / "en-us" / "SUMMARY.md").read_text(encoding="utf-8")
    csv_to_md = parse_csv_to_md(
        (root / "update_corpus_stats.py").read_text(encoding="utf-8")
    )
    ignore = load_ignore(ignore_path)
    statistics = root / "statistics"
    shipped = find_shipped_corpora(corpora)

    res = CheckResult()

    # 1. integration
    for corpus in shipped:
        if corpus in ignore:
            continue
        csv_name = f"{corpus}_corpora_stats.csv"
        if not (statistics / csv_name).exists():
            res.integration_issues.append(
                f"{corpus}: no stats CSV ({csv_name}) in statistics/"
            )
        slug = csv_to_md.get(csv_name)
        if slug is None:
            res.integration_issues.append(
                f"{corpus}: no CSV_TO_MD entry for {csv_name}"
            )
            continue
        if not (pages_dir / slug).exists():
            res.integration_issues.append(
                f"{corpus}: mapped page {slug} does not exist"
            )
        if f"(the-bank-architecture/corpora/{slug})" not in summary_text:
            res.integration_issues.append(
                f"{corpus}: no SUMMARY.md nav entry for {slug}"
            )

    # 2. leftover placeholders in any corpus page
    for page in sorted(pages_dir.glob("*.md")):
        if PLACEHOLDER_RE.search(page.read_text(encoding="utf-8")):
            res.placeholder_issues.append(
                f"{page.name}: contains a leftover {{...}} placeholder"
            )

    # 3. coming-soon drift (informational)
    shipped_set = set(shipped)
    for md in sorted((root / "en-us").rglob("*.md")):
        for line in md.read_text(encoding="utf-8").splitlines():
            if "Coming Soon" in line:
                for corpus in shipped_set:
                    if corpus in line:
                        res.coming_soon.append(
                            f"{md.relative_to(root)}: 'Coming Soon' names shipped '{corpus}'"
                        )

    # 4. translation lag (informational): en-us pages missing from pwn / zh-TW
    en_pages = {p.name for p in pages_dir.glob("*.md")} - {"README.md"}
    for lang in ("pwn", "zh-TW"):
        lang_dir = root / lang / "the-bank-architecture" / "corpora"
        lang_pages = {p.name for p in lang_dir.glob("*.md")} if lang_dir.is_dir() else set()
        for missing in sorted(en_pages - lang_pages):
            res.translation_lag.append(f"{lang}: missing {missing}")

    return res
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k check -q 2>&1 | tail -15
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add manage_corpus_pages.py tests/test_manage_corpus_pages.py
git commit -m "feat: check subcommand (drift lint + informational lag report)"
```

---

## Task 5: CLI wiring + `cmd_check` printer + `corpus_pages_ignore.txt`

**Files:**
- Modify: `/workspace/FormosanBankGitbook/manage_corpus_pages.py`
- Create: `/workspace/FormosanBankGitbook/corpus_pages_ignore.txt`
- Test: `/workspace/FormosanBankGitbook/tests/test_manage_corpus_pages.py`

- [ ] **Step 1: Write failing test** for `cmd_check` exit-code behavior (append to test file)

```python
def test_cmd_check_strict_returns_nonzero_on_drift(gitbook, capsys):
    (gitbook.corpora / "Orphan" / "XML").mkdir(parents=True)
    rc = mcp.cmd_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=None,
        strict=True,
    )
    assert rc == 1
    out = capsys.readouterr().out
    assert "Orphan" in out


def test_cmd_check_nonstrict_returns_zero_on_drift(gitbook):
    (gitbook.corpora / "Orphan" / "XML").mkdir(parents=True)
    rc = mcp.cmd_check(
        gitbook_root=str(gitbook.root),
        corpora_path=str(gitbook.corpora),
        ignore_path=None,
        strict=False,
    )
    assert rc == 0
```

- [ ] **Step 2: Run to verify failure**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -k cmd_check -q 2>&1 | tail -10
```
Expected: FAIL — no attribute `cmd_check`.

- [ ] **Step 3: Implement `cmd_check` + `main()`/argparse** (append to `manage_corpus_pages.py`)

```python
def cmd_check(gitbook_root, corpora_path, ignore_path, strict) -> int:
    res = run_check(gitbook_root, corpora_path, ignore_path)

    def section(title, items):
        print(f"\n{title}: {len(items)}")
        for m in items:
            print(f"  - {m}")

    section("Integration issues (gating)", res.integration_issues)
    section("Leftover placeholders (gating)", res.placeholder_issues)
    section("Coming-Soon drift (informational)", res.coming_soon)
    section("Translation lag (informational)", res.translation_lag)

    if res.ok:
        print("\nOK: every shipped corpus is fully wired; no leftover placeholders.")
        return 0
    print("\nFAIL: integration drift detected.")
    return 1 if strict else 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("add", help="scaffold a new corpus page + nav + stats-map entry")
    a.add_argument("--corpus", required=True, help="FormosanBank Corpora/ dir name")
    a.add_argument("--slug", required=True, help="page filename, e.g. my-corpus.md")
    a.add_argument("--nav-label", required=True, help="label shown in SUMMARY.md")
    a.add_argument("--title", required=True, help="page H1")
    a.add_argument("--template", required=True, help="path to the page template")
    a.add_argument("--gitbook-root", default=".", help="GitBook repo root")

    c = sub.add_parser("check", help="drift lint over shipped corpora")
    c.add_argument("--gitbook-root", default=".", help="GitBook repo root")
    c.add_argument("--corpora-path", default="../FormosanBank/Corpora",
                   help="FormosanBank Corpora/ directory")
    c.add_argument("--ignore", default=None,
                   help="path to ignore-list (default: <root>/corpus_pages_ignore.txt)")
    c.add_argument("--strict", action="store_true",
                   help="exit nonzero on integration drift")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "add":
        return cmd_add(
            corpus=args.corpus, slug=args.slug, nav_label=args.nav_label,
            title=args.title, template=args.template, gitbook_root=args.gitbook_root,
        )
    if args.command == "check":
        ignore = args.ignore
        if ignore is None:
            default_ignore = Path(args.gitbook_root) / "corpus_pages_ignore.txt"
            ignore = str(default_ignore) if default_ignore.exists() else None
        return cmd_check(
            gitbook_root=args.gitbook_root, corpora_path=args.corpora_path,
            ignore_path=ignore, strict=args.strict,
        )
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Write `corpus_pages_ignore.txt`**

```
# FormosanBank Corpora/ directory names intentionally NOT published to the GitBook.
# One name per line. Lines starting with # are comments.
# (Empty for now — every shipped corpus is expected to have a GitBook page.)
```

- [ ] **Step 5: Run the full test file**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -m pytest tests/test_manage_corpus_pages.py -q 2>&1 | tail -15
```
Expected: all pass (15 tests).

- [ ] **Step 6: Smoke-test the real CLI against the real repo**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 manage_corpus_pages.py check --gitbook-root . --corpora-path ../FormosanBank/Corpora 2>&1 | tail -40
```
Expected: prints the four sections. Integration issues here reveal real current drift (e.g. corpora with no page) — note them but do NOT fix in this task; they inform the ignore-list / Layer-1 follow-up. Exit 0 (no `--strict`).

- [ ] **Step 7: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add manage_corpus_pages.py corpus_pages_ignore.txt tests/test_manage_corpus_pages.py
git commit -m "feat: CLI (add/check) + ignore-list scaffold"
```

---

## Task 6: Populate the ignore-list from real drift; GitBook CI workflow

**Files:**
- Modify: `/workspace/FormosanBankGitbook/corpus_pages_ignore.txt`
- Create: `/workspace/FormosanBankGitbook/.github/workflows/corpus-page-lint.yaml`

- [ ] **Step 1: Inspect real drift and decide ignore entries**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 manage_corpus_pages.py check --gitbook-root . --corpora-path ../FormosanBank/Corpora 2>&1 | sed -n '/Integration issues/,/Leftover/p'
```
For each reported corpus, decide: is it genuinely meant to have no GitBook page (→ add to ignore-list with a comment) or is it real missing work (→ leave out of the list so it stays flagged; it becomes Layer-1 cleanup, out of scope here)? Add only the intentional-exclusion names to `corpus_pages_ignore.txt`, each with a brief `#` comment above it explaining why. **This is a human/operator judgment step — surface the list and reasoning during execution rather than guessing.**

- [ ] **Step 2: Write the CI workflow** `.github/workflows/corpus-page-lint.yaml`

```yaml
name: corpus-page-lint

on:
  push:
  pull_request:

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Check out GitBook repo
        uses: actions/checkout@v4
        with:
          path: gitbook

      - name: Check out FormosanBank (for Corpora/ source of truth)
        uses: actions/checkout@v4
        with:
          repository: FormosanBank/FormosanBank
          path: FormosanBank

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'

      - name: Install dev deps
        run: pip install -r gitbook/requirements-dev.txt

      - name: Run corpus-page drift lint (strict)
        run: |
          python gitbook/manage_corpus_pages.py check \
            --gitbook-root gitbook \
            --corpora-path FormosanBank/Corpora \
            --ignore gitbook/corpus_pages_ignore.txt \
            --strict
```

- [ ] **Step 3: Validate the workflow YAML parses**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/corpus-page-lint.yaml')); print('YAML OK')"
```
Expected: `YAML OK`. (If PyYAML isn't installed: `.venv/bin/python3 -m pip install pyyaml` first, or skip — the parse is a convenience check.)

- [ ] **Step 4: Commit**

```bash
cd /workspace/FormosanBankGitbook
git add corpus_pages_ignore.txt .github/workflows/corpus-page-lint.yaml
git commit -m "ci: corpus-page drift lint workflow + documented ignore-list"
```

---

## Task 7: The real page template (FormosanBank skill dir)

**Files:**
- Create: `.claude/skills/port-corpus-in/corpus_page.template.md` (in the FormosanBank worktree)

- [ ] **Step 1: Write the template** at `/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/.claude/skills/port-corpus-in/corpus_page.template.md`

Mirrors the established corpus-page shape (see `TangRecordingsOfTaroko.md`). Stats markers stay empty — `update_corpus_stats.py` fills them.

```markdown
# {{TITLE}}

{{DESCRIPTION}}

***

<!-- CORPUS STATS START -->
<!-- CORPUS STATS END -->

## **Access Details**

{{ACCESS}}

***

## **Copyright**

{{COPYRIGHT}}

***

## Citation

In accordance with our [Terms of Use](../../additional-resources/terms-of-use.md), if you use this corpus or any product derived from this corpus in any publication, you must cite both FormosanBank and:

{{CITATION}}
```

- [ ] **Step 2: Sanity-check it renders with the helper** (dry run into a temp dir)

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 - <<'EOF'
import manage_corpus_pages as mcp
tpl = open("/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/.claude/skills/port-corpus-in/corpus_page.template.md", encoding="utf-8").read()
out = mcp.render_page(tpl, "Test Title")
assert "# Test Title" in out
assert "{{DESCRIPTION}}" in out and "{{CITATION}}" in out
print("template renders OK")
EOF
```
Expected: `template renders OK`.

- [ ] **Step 3: Commit (FormosanBank worktree)**

```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
git add .claude/skills/port-corpus-in/corpus_page.template.md
git commit -m "feat(port-corpus-in): add GitBook corpus-page template"
```

---

## Task 8: Add Phase 5 "Add to GitBook" to the skill + renumber

**Files:**
- Modify: `.claude/skills/port-corpus-in/SKILL.md` (FormosanBank worktree)

- [ ] **Step 1: Insert the new Phase 5 and renumber the old Phase 5 → Phase 6**

In `SKILL.md`, the current `### Phase 5: Summary` becomes `### Phase 6: Summary`. Insert this **before** it, after the end of `### Phase 4: Validate after port`:

```markdown
### Phase 5: Add to GitBook

Publishing a corpus into `Corpora/` is only half-done until it appears in the
public GitBook. This phase wires the corpus's three GitBook integration points
(page, nav entry, stats map) using the GitBook repo's helper, then fills the
page prose. **Skippable with `--skip-gitbook`** if the operator wants to defer.

The helper does the mechanical edits; the skill (you) writes the prose. The
skill makes working-tree edits only — the operator commits and opens the GitBook
PR separately (this skill is **not a git committer**, consistent with Phase 3).

1. **Locate the GitBook repo.** Default sibling `<formosanbank_path>/../FormosanBankGitbook`.
   If absent, ask the operator for the path or offer to skip this phase.

2. **Resolve the publish branch (Roadmap Part D / Layer 0 is unresolved).** Report
   the current divergence so the operator can choose:
   ```bash
   cd <gitbook_path>
   git fetch --quiet
   echo "main ahead of en-us by: $(git rev-list --count origin/en-us..main 2>/dev/null || echo '?')"
   echo "en-us ahead of main by: $(git rev-list --count main..origin/en-us 2>/dev/null || echo '?')"
   ```
   Then `AskUserQuestion`: "Which branch does GitBook publish from? I'll make the
   page edits on a fresh feature branch off it." Check out / create a feature
   branch off the operator's choice in the GitBook working tree. Do NOT hardcode
   a branch.

3. **Derive identifiers** and confirm via `AskUserQuestion` (offer defaults, allow override):
   - `slug` — kebab-case of `corpus_name` + `.md` (e.g. `Nowbucyang-Truku-Thesis` → `nowbucyang-truku-thesis.md`).
   - `nav-label` — human label for the table of contents.
   - `title` — the page H1.

4. **Scaffold the three integration points** with the helper, passing the skill's template:
   ```bash
   <python> <gitbook_path>/manage_corpus_pages.py add \
     --gitbook-root "<gitbook_path>" \
     --corpus "<corpus_name>" \
     --slug "<slug>" \
     --nav-label "<nav-label>" \
     --title "<title>" \
     --template "<formosanbank_path>/.claude/skills/port-corpus-in/corpus_page.template.md"
   ```
   (`<python>` resolved as in Phase 4.)

5. **Fill the prose placeholders** in `<gitbook_path>/en-us/the-bank-architecture/corpora/<slug>`,
   reading the corpus README + QC summary:
   - `{{DESCRIPTION}}` — 1–3 sentences on what the corpus is and where it came from.
   - `{{COPYRIGHT}}` — the license/copyright line (e.g. `CC BY-NC`).
   - `{{CITATION}}` — APA-style citation(s); multiple separated by `|` per the XML format conventions.
   - `{{ACCESS}}` — the standard access line:
     `* The repo containing this corpus in FormosanBank as well as the code to reconstruct the corpus can be found [here](https://github.com/FormosanBank/FormosanBank/tree/main/Corpora/<corpus_name>).`

6. **Verify the page is fully wired and placeholder-free:**
   ```bash
   <python> <gitbook_path>/manage_corpus_pages.py check \
     --gitbook-root "<gitbook_path>" \
     --corpora-path "<formosanbank_path>/Corpora" \
     --strict
   ```
   A leftover `{{...}}` placeholder or a missing integration point fails this — fix
   before declaring the phase done. (The new corpus's stats CSV may not yet exist in
   the GitBook's `statistics/`; if `check` flags only that, note it as a known
   follow-up — stats CSVs are synced separately by the corpus-metrics pipeline.)
```

- [ ] **Step 2: Update the Phase 5 → Phase 6 heading and the Phase 5 summary body**

Change `### Phase 5: Summary` to `### Phase 6: Summary`, and add two bullets to its printed summary list:
- A `GitBook page: <path>` line.
- `"GitBook page created on branch <chosen>; commit and open the GitBook PR separately."`

- [ ] **Step 3: Add `--skip-gitbook` to the Inputs section**

Under `## Inputs`, add:
```markdown
- `skip_gitbook` — default `false`. If `true`, Phase 5 (Add to GitBook) is skipped and the operator publishes the GitBook page later.
```

- [ ] **Step 4: Verify the skill file is coherent** (no dangling "Phase 5: Summary")

Run:
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
grep -n "### Phase" .claude/skills/port-corpus-in/SKILL.md
```
Expected: phases 1,2,3,4,5 (Add to GitBook),6 (Summary) in order.

- [ ] **Step 5: Commit**

```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
git add .claude/skills/port-corpus-in/SKILL.md
git commit -m "feat(port-corpus-in): Phase 5 Add to GitBook (page+nav+stats-map+prose)"
```

---

## Task 9: Update Roadmap Part D status

**Files:**
- Modify: `claudeplans/2026-05-27-roadmap.md` (FormosanBank worktree)

- [ ] **Step 1: Update the Part D status block and layer markers**

In `## D. Gitbook sync automation`, change the `Status (2026-05-30): [NOT STARTED]` line to a `[PARTIAL]` status dated 2026-06-14 summarizing: D-port (port-corpus-in Phase 5) BUILT; Layer 1 drift lint + CI BUILT (`manage_corpus_pages.py check`); Layer 3 pwn/zh-TW lag report BUILT (informational, part of `check`); Layer 0 branch policy, Layer 1 cross-repo stats sync, Layer 2 zh-TW automation, Layer 4 cleaning docs remain DESIGN-ONLY. Reference the spec path. Update the stale "en-us is ~19 commits ahead" note to the 2026-06-14 re-audit (main is 4 ahead of en-us; en-us lags).

Flip the individual layer markers that were built:
- Layer 1 item 2 ("Lint for missing per-corpus pages") → `[DONE]`.
- Layer 1 item 3 ("Lint for Coming Soon entries matching shipped corpora") → `[DONE — informational]`.
- Layer 3 item 7 ("Banner + missing-page lint output") → `[PARTIAL — lint output DONE; banner is policy]`.

Leave Layer 0, Layer 2, Layer 4, and Layer 1 item 1 (stats CSV regeneration workflow) as `[NOT STARTED]`/design-only, cross-referencing the spec.

- [ ] **Step 2: Commit**

```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
git add claudeplans/2026-05-27-roadmap.md
git commit -m "docs(roadmap): update Part D status (D-port + L1 lint/CI + L3 report built)"
```

---

## Task 10: Live port of `Formosan-Nowbucyang-Truku-Thesis`

**This task is operator-interactive — it runs the `port-corpus-in` skill end-to-end. It is the acceptance test for the whole plan. Do NOT script it blindly; follow the skill's `AskUserQuestion` prompts and surface decisions.**

**Files:** creates `Corpora/Nowbucyang-Truku-Thesis/` (FormosanBank) and a new GitBook page (GitBook repo). Exact paths depend on skill prompts.

- [ ] **Step 1: Confirm the dev repo exists and is QC'd**

Run:
```bash
ls -d /workspace/Formosan-Nowbucyang-Truku-Thesis 2>/dev/null \
  || ls -d ~/Documents/Projects/Formosan/Formosan-Nowbucyang-Truku-Thesis 2>/dev/null
```
Expected: the dev repo path. Also confirm a recent `qc-output/*/qc-summary.md` exists (the skill's Pre-checks require QC evidence, or `assume_qc_passed=true`). The audit at [claudeplans/audit-Formosan-Nowbucyang-Truku-Thesis.md](../../claudeplans/audit-Formosan-Nowbucyang-Truku-Thesis.md) is supporting evidence.

- [ ] **Step 2: Invoke the `port-corpus-in` skill** with `source_path` = the dev repo and `formosanbank_path` = the worktree root (`/workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d`). Follow Phases 1–6. At Phase 5 step 2, choose the GitBook publish branch when prompted.

- [ ] **Step 3: Verify the FormosanBank side**

Run:
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d
.venv/bin/python3 QC/validation/validate_xml.py by_path \
  --path "Corpora/Nowbucyang-Truku-Thesis/XML" --no-exit-on-hard 2>&1 | tail -20
```
Expected: no HARD findings (or only findings already accepted in the dev-repo QC).

- [ ] **Step 4: Verify the GitBook side**

Run:
```bash
cd /workspace/FormosanBankGitbook
.venv/bin/python3 manage_corpus_pages.py check \
  --gitbook-root . \
  --corpora-path /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d/Corpora \
  2>&1 | tail -40
```
Expected: the new corpus appears wired (page + nav + stats-map). A missing stats-CSV-only flag is acceptable (synced later). No leftover placeholders on the new page.

- [ ] **Step 5: Review diffs in both repos, then hand off**

Run:
```bash
cd /workspace/FormosanBank/.claude/worktrees/gitbook-sync-part-d && git status && git diff --stat
cd /workspace/FormosanBankGitbook && git status && git diff --stat
```
Surface both diffs to the operator. Per the skill, the operator commits and opens the PRs (one per repo). Do not auto-commit the live-port content without operator review.

---

## Self-review notes

- **Spec coverage:** Piece 1 → Tasks 2–6; Piece 2 (skill Phase 5) → Tasks 7–8; Piece 3 (template/CI/tests) → Tasks 1, 6, 7; roadmap update → Task 9; live port → Task 10; keep-repos-separate recommendation is documentation-only (no task). Design-only layers (L0/L2/L4, L1 stats sync) intentionally have no build task.
- **Dict name:** `CSV_TO_MD` (verified in `update_corpus_stats.py`), values are bare `.md` filenames; entries appended before the closing brace (dict is not sorted).
- **Function names used consistently:** `render_page`, `insert_nav_entry`, `insert_csv_to_md_entry`, `cmd_add`, `run_check`, `cmd_check`, `find_shipped_corpora`, `load_ignore`, `parse_csv_to_md`, `CheckResult`.
- **Gating:** only `integration_issues` + `placeholder_issues` affect `CheckResult.ok` / `--strict` exit; coming-soon + translation-lag are informational.
