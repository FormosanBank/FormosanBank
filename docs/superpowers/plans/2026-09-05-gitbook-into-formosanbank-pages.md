# GitBook → FormosanBank GitHub Pages Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fold the `FormosanBankGitbook` repository into the public `FormosanBank` repository and publish all three language editions from it via GitHub Pages, eliminating every cross-repo sync in the process.

**Architecture:** The GitBook repo's three content directories (`en-us/`, `pwn/`, `zh-TW/`) move into `docs/site/` in this repo, carrying their git history. Hunter's reverted PR #78 build pipeline (`prepare_site.py` → `properdocs`/mkdocs-material → `check_site.py`) is revived at new paths and extended. Every document that was previously *copied* between the two repos (POLICIES.md, AUDIO-PERMISSIONS.md, corpus statistics) stops being copied and becomes a **build-time inclusion** — read from its canonical location in this repo when the site is built, never committed as a duplicate. That structurally removes the drift class that `sync_upstream_docs.py` and its drift test existed to police.

**Tech Stack:** Python 3.13, `properdocs` 1.6.7 (MkDocs successor, Tom Christie), `mkdocs-material` 9.7.7, `mkdocs-literate-nav` 0.6.3, GitHub Pages via `actions/deploy-pages`, pytest.

**Spec:** This document's "Requirements and decisions" section below. Background design docs that this supersedes in part: [docs/superpowers/specs/2026-06-14-gitbook-sync-part-d-design.md](../specs/2026-06-14-gitbook-sync-part-d-design.md) (Layers 0 and 1 are resolved by this migration) and [docs/superpowers/specs/2026-06-15-gitbook-stats-single-source-design.md](../specs/2026-06-15-gitbook-stats-single-source-design.md).

---

## Requirements and decisions

Decisions taken by the maintainer on 2026-09-05:

- Publish via **GitHub Pages**, not GitBook. GitBook's Git Sync is a paid-tier feature; the trial lapsed and the integration is gone. The web editor — GitBook's one real advantage — has never originated any content here.
- The docs move **into the `FormosanBank` repo**. `FormosanBank` is public (`private: false`), so Pages is free; `FormosanBankGitbook` is private, where Pages would require a paid GitHub plan.
- All cross-repo syncing must be reworked, not merely repointed.
- Hunter's PR #78 work is the starting point. Its tests are ported and extended.

### Global constraints

- Python **3.13** (repo `.venv`; `source .venv/bin/activate` before running anything).
- Pinned site deps, exact versions: `mkdocs-material==9.7.7`, `mkdocs-literate-nav==0.6.3`, `properdocs==1.6.7`.
- **English (`en-us/`) is canonical.** `pwn/` and `zh-TW/` are partial translations and must never gate a build or a merge.
- The three language source directory names stay `en-us`, `pwn`, `zh-TW` (the `Corpora/FormosanBankGitBook` corpus is built from `pwn/` and `zh-TW/` prose; renaming them would break its provenance).
- Published URL paths stay `/` (English), `/zh/`, `/paiwan/` — matching PR #78, so translated links keep working.
- No generated file is ever committed: `.build/` and `site/` are gitignored.
- `statistics/*.csv` remain auto-committed by `corpus-metrics.yaml`. Nothing in this plan may hand-edit them.

### Open questions — resolve before Task 3

1. **Pages URL.** This plan assumes the zero-cost default: a project Pages site at `https://formosanbank.github.io/FormosanBank/`. Alternatives are a custom domain, or creating an org-root `formosanbank.github.io` repo. PR #78 hardcoded `https://formosanbank.github.io/` (org root), which is wrong for a project site and is a plausible reason it was reverted. Task 3 exists to settle this; if a custom domain is chosen, do Task 3 with that value instead.
2. **Why was PR #78 reverted?** Ask Hunter (`hunterschep`) before starting. If the revert was for a reason not covered by Task 3, fold the fix into Task 2.

---

## File structure

**Imported from `FormosanBankGitbook` (Task 1), history preserved:**

| Old path | New path | Responsibility |
|---|---|---|
| `en-us/**` | `docs/site/en-us/**` | English content (canonical), 96 pages |
| `pwn/**` | `docs/site/pwn/**` | Paiwan translation, 24 pages |
| `zh-TW/**` | `docs/site/zh-TW/**` | Mandarin translation, 22 pages |
| `manage_corpus_pages.py` | `docs/tools/manage_corpus_pages.py` | Corpus-page scaffolding + drift lint |
| `update_corpus_stats.py` | `docs/tools/update_corpus_stats.py` | Stats-table rendering (becomes build-time) |
| `corpus_pages_ignore.txt` | `docs/tools/corpus_pages_ignore.txt` | Lint ignore list |
| `tests/test_manage_corpus_pages.py` | `tests/site/test_manage_corpus_pages.py` | Ported |
| `tests/test_update_corpus_stats.py` | `tests/site/test_update_corpus_stats.py` | Ported |
| `tests/fixtures/corpus_page.template.md` | `tests/site/fixtures/corpus_page.template.md` | Ported fixture |

**Retired at import (Task 1), not carried across:**

- `sync_upstream_docs.py` and `tests/test_upstream_doc_sync.py` — replaced by build-time inclusion (Task 5).
- `.github/workflows/corpus-page-lint.yaml`, `.github/workflows/tests.yaml` — folded into this repo's `tests.yaml` (Task 9).
- `requirements-dev.txt`, `pytest.ini` — this repo's `requirements.txt` and `pyproject.toml` take over.
- `en-us/the-bank-architecture/policies.md` — becomes generated (Task 5).

**Revived from PR #78 commit `f8e7d8f` (Task 2), at new paths:**

| PR #78 path | New path |
|---|---|
| `scripts/prepare_site.py` | `docs/tools/prepare_site.py` |
| `scripts/check_site.py` | `docs/tools/check_site.py` |
| `scripts/build-site.sh` | `docs/tools/build-site.sh` |
| `tests/test_prepare_site.py` | `tests/site/test_prepare_site.py` |
| `theme/**` | `docs/theme/**` |
| `mkdocs.yml`, `mkdocs.zh.yml`, `mkdocs.paiwan.yml` | repo root, unchanged names |
| `requirements-site.txt` | repo root, unchanged name |

**Created new:**

- `tests/site/__init__.py`, `tests/site/conftest.py`
- `tests/site/test_check_site.py` (PR #78 shipped `check_site.py` with no tests)
- `tests/site/test_site_content.py` (nav integrity, legacy-URL scan, directive-leak guard)
- `.github/workflows/pages.yaml`

**Modified:**

- `.gitignore`, `requirements.txt`, `pyproject.toml`, `CLAUDE.md`, `AGENTS.md`
- `.github/workflows/tests.yaml`
- `.claude/skills/port-corpus-in/SKILL.md`
- `QC/utilities/port_audio_seconds_from_gitbook.py`

---

### Task 1: Import the GitBook repo with history

Bring 15 months of documentation history — Hunter's and Joshua's authorship — into this repo rather than dropping a snapshot.

**Files:**
- Create: `docs/site/{en-us,pwn,zh-TW}/**`, `docs/tools/{manage_corpus_pages.py,update_corpus_stats.py,corpus_pages_ignore.txt}`, `tests/site/**`
- Modify: `.gitignore`

- [ ] **Step 1: Create the worktree**

Multiple Claude instances share this checkout. Never work on the shared branch.

```bash
cd /workspace/FormosanBank
git worktree add -b feature/docs-into-repo /workspace/wt-docs-migration main
cd /workspace/wt-docs-migration
```

- [ ] **Step 2: Prepare a path-rewritten clone of the GitBook repo**

`git-filter-repo` is not installed; install it into the venv first.

```bash
source /workspace/FormosanBank/.venv/bin/activate
pip install git-filter-repo
git clone /workspace/FormosanBankGitbook /tmp/gitbook-rewrite
cd /tmp/gitbook-rewrite
git checkout en-us
git filter-repo --force \
  --path-rename en-us/:docs/site/en-us/ \
  --path-rename pwn/:docs/site/pwn/ \
  --path-rename zh-TW/:docs/site/zh-TW/ \
  --path-rename manage_corpus_pages.py:docs/tools/manage_corpus_pages.py \
  --path-rename update_corpus_stats.py:docs/tools/update_corpus_stats.py \
  --path-rename corpus_pages_ignore.txt:docs/tools/corpus_pages_ignore.txt \
  --path-rename tests/:tests/site/ \
  --path .github/ --invert-paths
```

Note `--path-rename en-us/:docs/site/en-us/` renames the *directory*; the branch also named `en-us` is unaffected.

- [ ] **Step 3: Verify the rewrite before merging**

```bash
cd /tmp/gitbook-rewrite
git ls-tree -r --name-only HEAD | grep -c '^docs/site/en-us/'   # expect 96+ (md + assets)
git ls-tree -r --name-only HEAD | grep -v -E '^(docs/|tests/site/)' # expect only loose root files
git log --oneline | wc -l                                        # expect the full history, not 1
```

Expected: content lives only under `docs/` and `tests/site/`; history is hundreds of commits, not one.

- [ ] **Step 4: Merge into the worktree as an unrelated history**

```bash
cd /workspace/wt-docs-migration
git remote add gitbook-import /tmp/gitbook-rewrite
git fetch gitbook-import
git merge --allow-unrelated-histories --no-ff gitbook-import/en-us \
  -m "Import FormosanBankGitbook into docs/, preserving history"
```

- [ ] **Step 5: Delete the files that do not survive the move**

These are replaced by later tasks, not lost.

```bash
git rm -q docs/tools/sync_upstream_docs.py \
          tests/site/test_upstream_doc_sync.py \
          docs/site/en-us/the-bank-architecture/policies.md
git rm -q --ignore-unmatch requirements-dev.txt pytest.ini README.md.orig
git commit -m "Retire cross-repo sync scripts superseded by build-time inclusion"
```

If `git rm` reports a path is absent, the filter-repo rename put it elsewhere — run `git ls-files | grep sync_upstream` and adjust rather than skipping.

- [ ] **Step 6: Gitignore the build outputs**

Append to `.gitignore`:

```
# Documentation site build outputs
.build/
/site/
```

- [ ] **Step 7: Commit**

```bash
git add .gitignore
git commit -m "Ignore documentation site build outputs"
```

---

### Task 2: Revive the PR #78 build pipeline at its new paths

**Files:**
- Create: `docs/tools/prepare_site.py`, `docs/tools/check_site.py`, `docs/tools/build-site.sh`, `docs/theme/**`, `mkdocs.yml`, `mkdocs.zh.yml`, `mkdocs.paiwan.yml`, `requirements-site.txt`, `tests/site/__init__.py`, `tests/site/test_prepare_site.py`
- Test: `tests/site/test_prepare_site.py`

**Interfaces:**
- Produces: `prepare_site.prepare_site(repository_root: Path, output_root: Path) -> None`; `prepare_site.build_path_map(source_dir: Path) -> dict[PurePosixPath, PurePosixPath]`; `prepare_site.transform_markdown(text: str, *, current_source: PurePosixPath, current_output: PurePosixPath, mapping: dict[PurePosixPath, PurePosixPath], public_prefix: str) -> str`; `prepare_site.transform_summary(text: str) -> str`; `prepare_site.LANGUAGES: tuple[Language, ...]` where `Language(source: str, output: str, public_prefix: str)`.
- Consumes: nothing from Task 1 beyond the content tree it produced.

- [ ] **Step 1: Extract PR #78's files from the reverted commit**

The commit is still reachable even though it was reverted.

```bash
cd /workspace/wt-docs-migration
G=/workspace/FormosanBankGitbook
mkdir -p docs/tools docs/theme
git --git-dir=$G/.git show f8e7d8f:scripts/prepare_site.py > docs/tools/prepare_site.py
git --git-dir=$G/.git show f8e7d8f:scripts/check_site.py  > docs/tools/check_site.py
git --git-dir=$G/.git show f8e7d8f:scripts/build-site.sh  > docs/tools/build-site.sh
git --git-dir=$G/.git show f8e7d8f:requirements-site.txt  > requirements-site.txt
for f in mkdocs.yml mkdocs.zh.yml mkdocs.paiwan.yml; do
  git --git-dir=$G/.git show f8e7d8f:$f > $f
done
mkdir -p docs/theme/overrides docs/theme/static/assets docs/theme/static/stylesheets
git --git-dir=$G/.git show f8e7d8f:theme/overrides/main.html > docs/theme/overrides/main.html
git --git-dir=$G/.git show f8e7d8f:theme/static/assets/brand-mark.svg > docs/theme/static/assets/brand-mark.svg
git --git-dir=$G/.git show f8e7d8f:theme/static/stylesheets/extra.css > docs/theme/static/stylesheets/extra.css
mkdir -p tests/site
git --git-dir=$G/.git show f8e7d8f:tests/test_prepare_site.py > tests/site/test_prepare_site.py
touch tests/site/__init__.py
chmod +x docs/tools/build-site.sh
```

- [ ] **Step 2: Repoint the language sources at `docs/site/`**

In `docs/tools/prepare_site.py`, the `LANGUAGES` tuple names directories relative to the repository root. They moved under `docs/site/`.

Replace:

```python
LANGUAGES = (
    Language("en-us", "en", "/"),
    Language("zh-TW", "zh", "/zh/"),
    Language("pwn", "paiwan", "/paiwan/"),
)
```

with:

```python
LANGUAGES = (
    Language("docs/site/en-us", "en", "/"),
    Language("docs/site/zh-TW", "zh", "/zh/"),
    Language("docs/site/pwn", "paiwan", "/paiwan/"),
)
```

In the same file, `prepare_language` reads the theme from `repository_root / "theme" / "static"`. Change that one line to:

```python
    copy_static_assets(repository_root / "docs" / "theme" / "static", output_dir)
```

- [ ] **Step 3: Fix the import path in the ported test**

`tests/site/test_prepare_site.py` opens with `from scripts.prepare_site import ...`. The module now lives at `docs/tools/`, which is not an importable package. Replace the import block at the top of the file with:

```python
import importlib.util
import sys
from pathlib import Path, PurePosixPath

_MODULE_PATH = Path(__file__).resolve().parents[2] / "docs" / "tools" / "prepare_site.py"
_spec = importlib.util.spec_from_file_location("prepare_site", _MODULE_PATH)
prepare_site = importlib.util.module_from_spec(_spec)
sys.modules["prepare_site"] = prepare_site
_spec.loader.exec_module(prepare_site)

build_path_map = prepare_site.build_path_map
transform_markdown = prepare_site.transform_markdown
transform_summary = prepare_site.transform_summary
```

- [ ] **Step 4: Run the ported tests to verify they pass**

```bash
cd /workspace/wt-docs-migration
source /workspace/FormosanBank/.venv/bin/activate
pip install -r requirements-site.txt
pytest tests/site/test_prepare_site.py -v
```

Expected: PASS. These are PR #78's own tests; they exercise pure functions and do not depend on the move. If `test_build_path_map_uses_index_and_casefolded_routes` fails, the extraction in Step 1 was incomplete.

- [ ] **Step 5: Commit**

```bash
git add docs/tools docs/theme mkdocs*.yml requirements-site.txt tests/site
git commit -m "Revive the PR #78 static-site pipeline under docs/"
```

---

### Task 3: Correct the published site URL

PR #78 targets `https://formosanbank.github.io/` — the org-root domain, served by a repo literally named `formosanbank.github.io`. Deployed from `FormosanBank`, the real base is `https://formosanbank.github.io/FormosanBank/`. Left unfixed, every absolute URL and the link checker's host matching are wrong.

**Files:**
- Modify: `mkdocs.yml:2`, `mkdocs.zh.yml:2`, `mkdocs.paiwan.yml:2`, `docs/tools/prepare_site.py`, `docs/tools/check_site.py:15-16`
- Test: `tests/site/test_prepare_site.py`

**Interfaces:**
- Consumes: `prepare_site.transform_markdown` (Task 2).
- Produces: module constant `prepare_site.NEW_SITE: str` — the canonical published base URL, imported by tests and by `check_site.py`.

- [ ] **Step 1: Write the failing test**

Append to `tests/site/test_prepare_site.py`:

```python
def test_legacy_gitbook_urls_are_rewritten_to_the_project_pages_base() -> None:
    source = "See [the format](https://ai4commsci.gitbook.io/formosanbank/xml).\n"

    transformed = transform_markdown(
        source,
        current_source=PurePosixPath("page.md"),
        current_output=PurePosixPath("page.md"),
        mapping={PurePosixPath("page.md"): PurePosixPath("page.md")},
        public_prefix="/",
    )

    assert "ai4commsci.gitbook.io" not in transformed
    assert "https://formosanbank.github.io/FormosanBank/xml" in transformed
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/site/test_prepare_site.py::test_legacy_gitbook_urls_are_rewritten_to_the_project_pages_base -v
```

Expected: FAIL — the rewrite produces `https://formosanbank.github.io/xml`, missing the `/FormosanBank` base path.

- [ ] **Step 3: Set the base URL in one place**

In `docs/tools/prepare_site.py`, change:

```python
NEW_SITE = "https://formosanbank.github.io"
```

to:

```python
# The published base URL. A project Pages site is served under /<repo>/.
# If a custom domain is adopted, change this one constant and the three
# mkdocs `site_url` values together.
NEW_SITE = "https://formosanbank.github.io/FormosanBank"
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
pytest tests/site/test_prepare_site.py -v
```

Expected: PASS, all tests in the file.

- [ ] **Step 5: Align the mkdocs configs**

`mkdocs.yml` line 2: `site_url: https://formosanbank.github.io/FormosanBank/`
`mkdocs.zh.yml` line 2: `site_url: https://formosanbank.github.io/FormosanBank/zh/`
`mkdocs.paiwan.yml` line 2: `site_url: https://formosanbank.github.io/FormosanBank/paiwan/`

- [ ] **Step 6: Align the link checker's host and base**

`docs/tools/check_site.py` matches internal links against a bare host. With a project site the base path is part of every absolute internal URL. Replace:

```python
LOCAL_HOST = "formosanbank.github.io"
LEGACY_SITE = "ai4commsci.gitbook.io/formosanbank"
```

with:

```python
LOCAL_HOST = "formosanbank.github.io"
LOCAL_BASE = "/FormosanBank"
LEGACY_SITE = "ai4commsci.gitbook.io/formosanbank"
```

Then in `resolve_target`, immediately after `parsed = urlsplit(reference)`, strip the base so path resolution stays relative to the built site root:

```python
    if parsed.netloc == LOCAL_HOST and parsed.path.startswith(LOCAL_BASE):
        parsed = parsed._replace(path=parsed.path[len(LOCAL_BASE):] or "/")
```

- [ ] **Step 7: Commit**

```bash
git add docs/tools/prepare_site.py docs/tools/check_site.py mkdocs.yml mkdocs.zh.yml mkdocs.paiwan.yml tests/site/test_prepare_site.py
git commit -m "Target the project Pages base path rather than the org root"
```

---

### Task 4: Make the full three-language build run locally

**Files:**
- Modify: `docs/tools/build-site.sh`
- Test: manual build, verified by `check_site.py`

- [ ] **Step 1: Repoint the build script at the new tool locations**

Replace the body of `docs/tools/build-site.sh` with:

```bash
#!/usr/bin/env bash

set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
prepared_docs="$repository_root/.build/docs"
output_dir="${1:-$repository_root/site}"

python "$repository_root/docs/tools/prepare_site.py" \
  --repository-root "$repository_root" \
  --output-root "$prepared_docs"
python -m properdocs build --strict \
  --config-file "$repository_root/mkdocs.yml" \
  --site-dir "$output_dir"
python -m properdocs build --strict \
  --config-file "$repository_root/mkdocs.zh.yml" \
  --site-dir "$output_dir/zh"
python -m properdocs build --strict \
  --config-file "$repository_root/mkdocs.paiwan.yml" \
  --site-dir "$output_dir/paiwan"
python "$repository_root/docs/tools/check_site.py" "$output_dir"
```

Note the `../..` — the script moved one directory deeper than in PR #78.

- [ ] **Step 2: Run the build**

```bash
cd /workspace/wt-docs-migration
source /workspace/FormosanBank/.venv/bin/activate
./docs/tools/build-site.sh
```

Expected: three `properdocs build --strict` runs complete, then `check_site.py` reports no broken links. `--strict` turns MkDocs warnings into errors, so an unresolved nav entry or dangling link fails the build here rather than silently shipping.

- [ ] **Step 3: Fix whatever `--strict` surfaces**

Likely findings, each fixed in `docs/tools/prepare_site.py`'s `SOURCE_LINK_FIXES` map or in the offending source page:
- Links to `policies.md`, deleted in Task 1 Step 5 — leave broken for now; Task 5 regenerates that page. If the build blocks, comment the nav line in `docs/site/en-us/SUMMARY.md` and restore it in Task 5 Step 6.
- Cross-repo links of the form `../FormosanBankGitbook/...` — now same-repo; add to `SOURCE_LINK_FIXES`.

Record each fix in the commit message; do not suppress `--strict`.

- [ ] **Step 4: Spot-check the rendered output**

```bash
python -m http.server 8000 --directory site
```

Confirm in a browser: English at `/`, Mandarin at `/zh/`, Paiwan at `/paiwan/`; the nav tree matches `SUMMARY.md`; a corpus page renders its statistics table.

- [ ] **Step 5: Commit**

```bash
git add docs/tools/build-site.sh docs/site
git commit -m "Build all three language editions from the repo root"
```

---

### Task 5: Replace `sync_upstream_docs.py` with build-time inclusion

`POLICIES.md` and `AUDIO-PERMISSIONS.md` are canonical in this repo. The old design copied them into the GitBook and used a pytest drift check to notice when the copy went stale — a check that was not wired to CI for weeks, during which four POLICIES commits went unsynced. Same-repo, the copy is unnecessary: generate the page during the build and drift becomes structurally impossible.

**Files:**
- Modify: `docs/tools/prepare_site.py`, `docs/site/en-us/SUMMARY.md`
- Test: `tests/site/test_prepare_site.py`

**Interfaces:**
- Produces: `prepare_site.INCLUDED_DOCS: tuple[IncludedDoc, ...]` where `IncludedDoc(source: str, page: str, title: str, icon: str)`; `prepare_site.render_included_doc(repository_root: Path, doc: IncludedDoc) -> str`.
- Consumes: `prepare_site.LANGUAGES`, `prepare_site.prepare_language` (Task 2).

- [ ] **Step 1: Write the failing test**

Append to `tests/site/test_prepare_site.py`:

```python
def test_included_doc_is_rendered_from_the_canonical_upstream_file(tmp_path: Path) -> None:
    (tmp_path / "POLICIES.md").write_text(
        "# Policies\n\nPOL-001: canonical text.\n", encoding="utf-8"
    )
    doc = prepare_site.IncludedDoc(
        source="POLICIES.md",
        page="the-bank-architecture/policies.md",
        title="FormosanBank Policies",
        icon="scale-balanced",
    )

    rendered = prepare_site.render_included_doc(tmp_path, doc)

    assert "POL-001: canonical text." in rendered
    assert rendered.startswith("---\n")
    assert "icon: fontawesome/solid/scale-balanced" in rendered
    assert "Generated from" in rendered
    assert "POLICIES.md" in rendered
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/site/test_prepare_site.py::test_included_doc_is_rendered_from_the_canonical_upstream_file -v
```

Expected: FAIL with `AttributeError: module 'prepare_site' has no attribute 'IncludedDoc'`.

- [ ] **Step 3: Implement the inclusion**

Add to `docs/tools/prepare_site.py`, after the `Language` dataclass:

```python
@dataclass(frozen=True)
class IncludedDoc:
    """A page generated at build time from a canonical file in this repo.

    These documents version with the code that implements them — POLICIES.md
    with the rule IDs and scripts that enforce each ruling, AUDIO-PERMISSIONS.md
    with audio_permissions.json and the parity checks that read it. Rendering
    them at build time means the site cannot drift from the source.
    """

    source: str
    page: str
    title: str
    icon: str


INCLUDED_DOCS = (
    IncludedDoc(
        source="POLICIES.md",
        page="the-bank-architecture/policies.md",
        title="FormosanBank Policies",
        icon="scale-balanced",
    ),
    IncludedDoc(
        source="AUDIO-PERMISSIONS.md",
        page="the-bank-architecture/audio-permissions.md",
        title="Audio Permissions",
        icon="volume-high",
    ),
)


def render_included_doc(repository_root: Path, doc: IncludedDoc) -> str:
    """Render one canonical repository document as a site page."""
    body = (repository_root / doc.source).read_text(encoding="utf-8")
    return (
        f"---\nicon: fontawesome/solid/{doc.icon}\n---\n\n"
        f'<div class="admonition info">\n'
        f'<p class="admonition-title">Generated page</p>\n'
        f"<p>Generated from <code>{doc.source}</code> in this repository at "
        f"build time. Edit that file, not this page.</p>\n"
        f"</div>\n\n"
        f"{body}"
    )
```

Then, at the end of `prepare_language`, generate them for English only (translations of policy text are out of scope and would silently go stale):

```python
    if language.source.endswith("en-us"):
        for doc in INCLUDED_DOCS:
            target = output_dir / output_path(PurePosixPath(doc.page))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                render_included_doc(repository_root, doc), encoding="utf-8"
            )
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
pytest tests/site/test_prepare_site.py -v
```

Expected: PASS.

- [ ] **Step 5: Add a test that the built page really carries current policy text**

Append:

```python
def test_policies_page_is_generated_into_the_english_build(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / "docs" / "site" / "en-us").mkdir(parents=True)
    (repo / "docs" / "site" / "pwn").mkdir(parents=True)
    (repo / "docs" / "site" / "zh-TW").mkdir(parents=True)
    for lang in ("en-us", "pwn", "zh-TW"):
        (repo / "docs" / "site" / lang / "README.md").write_text(
            "# Home\n", encoding="utf-8"
        )
    (repo / "POLICIES.md").write_text("# Policies\n\nPOL-042: unique.\n", encoding="utf-8")
    (repo / "AUDIO-PERMISSIONS.md").write_text("# Audio\n", encoding="utf-8")

    prepare_site.prepare_site(repo, tmp_path / "out")

    page = (tmp_path / "out" / "en" / "the-bank-architecture" / "policies.md")
    assert "POL-042: unique." in page.read_text(encoding="utf-8")
    assert not (tmp_path / "out" / "zh" / "the-bank-architecture" / "policies.md").exists()
```

- [ ] **Step 6: Run, restore the nav entry, rebuild**

```bash
pytest tests/site/test_prepare_site.py -v
```

Expected: PASS. Then ensure `docs/site/en-us/SUMMARY.md` contains both nav lines (restore the policies line if Task 4 Step 3 commented it, and add audio-permissions beneath it):

```
* [FormosanBank Policies](the-bank-architecture/policies.md)
* [Audio Permissions](the-bank-architecture/audio-permissions.md)
```

Then `./docs/tools/build-site.sh` — expected: `--strict` passes, both pages resolve.

- [ ] **Step 7: Commit**

```bash
git add docs/tools/prepare_site.py docs/site/en-us/SUMMARY.md tests/site/test_prepare_site.py
git commit -m "Generate POLICIES and AUDIO-PERMISSIONS pages at build time"
```

---

### Task 6: Make corpus statistics a build-time injection

`update_corpus_stats.py` resolved a sibling `../FormosanBank/statistics` and wrote stats blocks into committed markdown. Same-repo, the CSVs are right there and are auto-regenerated by `corpus-metrics.yaml` on every push to `main`. Injecting at build time means a stats refresh reaches the site with no second commit and no possibility of a stale committed block.

**Files:**
- Modify: `docs/tools/update_corpus_stats.py`, `docs/tools/prepare_site.py`
- Test: `tests/site/test_update_corpus_stats.py`

**Interfaces:**
- Consumes: `prepare_site.prepare_language` (Task 2); `update_corpus_stats.CSV_TO_MD: dict[str, str]` (imported unchanged from the GitBook repo).
- Produces: `update_corpus_stats.resolve_stats_dir(cli_stats_dir=None, env=None, repo_root=None) -> Path` with in-repo default; `update_corpus_stats.inject_stats_into_tree(prepared_english_dir: Path, stats_dir: Path) -> int` returning the number of pages updated.

- [ ] **Step 1: Write the failing test for the in-repo default**

In `tests/site/test_update_corpus_stats.py`, append:

```python
def test_resolve_stats_dir_defaults_to_the_in_repo_statistics_directory(tmp_path):
    (tmp_path / "statistics").mkdir()

    resolved = update_corpus_stats.resolve_stats_dir(repo_root=tmp_path)

    assert resolved == tmp_path / "statistics"
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/site/test_update_corpus_stats.py::test_resolve_stats_dir_defaults_to_the_in_repo_statistics_directory -v
```

Expected: FAIL — the current default resolves `repo_root.parent / "FormosanBank" / "statistics"`, a sibling that no longer exists.

- [ ] **Step 3: Repoint the default**

In `docs/tools/update_corpus_stats.py`, change `REPO_ROOT` and the fallback branch of `resolve_stats_dir`:

```python
REPO_ROOT = Path(__file__).resolve().parents[2]
STATS_DIR = REPO_ROOT / 'statistics'
```

and inside `resolve_stats_dir`, replace the `else:` branch with:

```python
    else:
        d = Path(repo_root) / "statistics"
```

The `--stats-dir` flag and `FORMOSANBANK_STATS_DIR` env var keep working and keep their precedence; only the fallback changes.

- [ ] **Step 4: Run to verify it passes**

```bash
pytest tests/site/test_update_corpus_stats.py -v
```

Expected: PASS, whole file. Existing tests that pass an explicit `--stats-dir` are unaffected.

- [ ] **Step 5: Write the failing test for build-time injection**

```python
def test_stats_are_injected_into_the_prepared_tree(tmp_path):
    prepared = tmp_path / "en" / "the-bank-architecture" / "corpora"
    prepared.mkdir(parents=True)
    (prepared / "epark.md").write_text(
        "# ePark\n\n<!-- CORPUS STATS START -->\n<!-- CORPUS STATS END -->\n",
        encoding="utf-8",
    )
    stats = tmp_path / "statistics"
    stats.mkdir()
    (stats / "ePark_corpora_stats.csv").write_text(
        "Language,Dialect,Sentences,Tokens\nAmis,,10,100\n", encoding="utf-8"
    )

    updated = update_corpus_stats.inject_stats_into_tree(tmp_path / "en", stats)

    assert updated >= 1
    assert "Amis" in (prepared / "epark.md").read_text(encoding="utf-8")
```

- [ ] **Step 6: Run it to verify it fails**

```bash
pytest tests/site/test_update_corpus_stats.py::test_stats_are_injected_into_the_prepared_tree -v
```

Expected: FAIL with `AttributeError: ... has no attribute 'inject_stats_into_tree'`.

- [ ] **Step 7: Implement `inject_stats_into_tree`**

Add to `docs/tools/update_corpus_stats.py`. Reuse the existing marker-replacement and table-rendering helpers rather than duplicating them — locate the function that renders one CSV into a markdown table and the one that swaps content between `<!-- CORPUS STATS START -->` and `<!-- CORPUS STATS END -->`, and call them here. The only new logic is walking the prepared tree instead of the committed one, and accounting for `prepare_site`'s case-folding (`RauDong.md` → `raudong.md`):

```python
def inject_stats_into_tree(prepared_english_dir, stats_dir):
    """Inject stats tables into an already-prepared English build tree.

    `prepared_english_dir` is the output of prepare_site for en-us, so page
    names are case-folded and README.md has become index.md. Returns the
    number of pages updated.
    """
    prepared_english_dir = Path(prepared_english_dir)
    stats_dir = Path(stats_dir)
    corpora_dir = prepared_english_dir / "the-bank-architecture" / "corpora"
    updated = 0
    for csv_name, md_name in CSV_TO_MD.items():
        csv_path = stats_dir / csv_name
        if not csv_path.is_file():
            continue
        page = corpora_dir / md_name.casefold()
        if not page.is_file():
            continue
        if _inject_one(page, csv_path):
            updated += 1
    return updated
```

Name the existing single-page helper `_inject_one(page_path, csv_path) -> bool` if it does not already exist under another name; do not write a second table renderer.

- [ ] **Step 8: Run to verify it passes**

```bash
pytest tests/site/test_update_corpus_stats.py -v
```

Expected: PASS.

- [ ] **Step 9: Call it from the build**

At the end of `prepare_site.prepare_site`, after the language loop:

```python
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import update_corpus_stats

    update_corpus_stats.inject_stats_into_tree(
        output_root / "en", repository_root / "statistics"
    )
```

Add `import sys` to the module's imports if absent.

- [ ] **Step 10: Rebuild and verify a real page**

```bash
./docs/tools/build-site.sh
grep -c 'Amis' site/the-bank-architecture/corpora/epark/index.html
```

Expected: nonzero — the ePark page carries a real statistics table sourced from `statistics/ePark_corpora_stats.csv`.

- [ ] **Step 11: Commit**

```bash
git add docs/tools/update_corpus_stats.py docs/tools/prepare_site.py tests/site/test_update_corpus_stats.py
git commit -m "Inject corpus statistics at build time from the in-repo CSVs"
```

---

### Task 7: Repoint the corpus-page drift lint at in-repo paths

**Files:**
- Modify: `docs/tools/manage_corpus_pages.py`
- Test: `tests/site/test_manage_corpus_pages.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `manage_corpus_pages` CLI with `--gitbook-root` renamed to `--site-root` (default: the repo root) and `--corpora-path` defaulting to `<repo root>/Corpora`.

- [ ] **Step 1: Write the failing test**

Append to `tests/site/test_manage_corpus_pages.py`:

```python
def test_defaults_resolve_inside_this_repository(tmp_path, monkeypatch):
    args = manage_corpus_pages.parse_args(["check"])

    assert args.corpora_path.name == "Corpora"
    assert args.site_root.name == "FormosanBank" or args.site_root.is_dir()
```

- [ ] **Step 2: Run it to verify it fails**

```bash
pytest tests/site/test_manage_corpus_pages.py::test_defaults_resolve_inside_this_repository -v
```

Expected: FAIL — `--corpora-path` currently defaults to `../FormosanBank/Corpora` and the flag is `--gitbook-root`.

- [ ] **Step 3: Update the argument defaults**

In `docs/tools/manage_corpus_pages.py`, in `parse_args`:
- Rename `--gitbook-root` to `--site-root`, default `Path(__file__).resolve().parents[2]`. Keep `--gitbook-root` as a hidden deprecated alias (`dest="site_root"`, `help=argparse.SUPPRESS`) so any operator muscle memory or stale script still works.
- Change `--corpora-path` default from `../FormosanBank/Corpora` to `Path(__file__).resolve().parents[2] / "Corpora"`.
- Wherever the code builds page paths from the site root, insert the `docs/site` segment: pages now live at `<site_root>/docs/site/en-us/the-bank-architecture/corpora/`.

Also update the `translation_lag` check (around line 276) — it iterates `("pwn", "zh-TW")` and compares directory listings; those directories are now `docs/site/pwn` and `docs/site/zh-TW`.

- [ ] **Step 4: Run the full file to verify**

```bash
pytest tests/site/test_manage_corpus_pages.py -v
```

Expected: PASS. Any test still passing `--gitbook-root` should also pass, via the alias.

- [ ] **Step 5: Run the lint against real content**

```bash
python docs/tools/manage_corpus_pages.py check --ignore docs/tools/corpus_pages_ignore.txt --strict
```

Expected: exit 0. Every corpus under `Corpora/` has a page, nav entry, list bullet, and `CSV_TO_MD` entry. If it reports gaps, they are pre-existing drift — fix them in this commit and note which in the message.

- [ ] **Step 6: Commit**

```bash
git add docs/tools/manage_corpus_pages.py tests/site/test_manage_corpus_pages.py
git commit -m "Resolve corpus-page lint paths inside this repository"
```

---

### Task 8: Add the new site tests

PR #78 shipped `check_site.py` — 153 lines gating every deploy — with no tests at all. It also strips a fixed set of GitBook directives, so any directive outside that set leaks raw `{% ... %}` into published HTML silently.

**Files:**
- Create: `tests/site/test_check_site.py`, `tests/site/test_site_content.py`, `tests/site/conftest.py`
- Modify: `docs/tools/prepare_site.py`

**Interfaces:**
- Consumes: `prepare_site.transform_markdown`, `prepare_site.LANGUAGES` (Task 2); `check_site.resolve_target`, `check_site.parse_page` (Task 2).
- Produces: `prepare_site.UNKNOWN_DIRECTIVE: re.Pattern` and a `ValueError` raised on unrecognized directives.

- [ ] **Step 1: Write `tests/site/conftest.py`**

```python
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def load(name: str):
    """Import a docs/tools script that is not on a package path."""
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "docs" / "tools" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
```

- [ ] **Step 2: Write the failing directive-leak test**

Create `tests/site/test_site_content.py`:

```python
from pathlib import Path, PurePosixPath

import pytest

from conftest import REPO_ROOT, load

prepare_site = load("prepare_site")


def test_unknown_gitbook_directive_raises_instead_of_leaking() -> None:
    source = "# Page\n\n{% embed url=\"https://example.com\" %}\n"

    with pytest.raises(ValueError, match="unhandled GitBook directive"):
        prepare_site.transform_markdown(
            source,
            current_source=PurePosixPath("page.md"),
            current_output=PurePosixPath("page.md"),
            mapping={PurePosixPath("page.md"): PurePosixPath("page.md")},
            public_prefix="/",
        )
```

- [ ] **Step 3: Run it to verify it fails**

```bash
pytest tests/site/test_site_content.py::test_unknown_gitbook_directive_raises_instead_of_leaking -v
```

Expected: FAIL — no exception raised; the directive passes through untouched.

- [ ] **Step 4: Make unknown directives loud**

At the end of `transform_markdown` in `docs/tools/prepare_site.py`, just before the final return, add:

```python
    leftover = re.search(r"{%.*?%}", text)
    if leftover:
        raise ValueError(
            f"unhandled GitBook directive {leftover.group(0)!r} in {current_source}; "
            "add it to DIRECTIVE_LINE or translate it explicitly"
        )
```

- [ ] **Step 5: Run to verify it passes**

```bash
pytest tests/site/test_site_content.py -v
```

Expected: PASS.

- [ ] **Step 6: Add nav-integrity and legacy-URL tests**

Append to `tests/site/test_site_content.py`:

```python
import re

LANGUAGE_DIRS = ("en-us", "pwn", "zh-TW")


@pytest.mark.parametrize("language", LANGUAGE_DIRS)
def test_every_summary_nav_entry_resolves_to_a_file(language: str) -> None:
    root = REPO_ROOT / "docs" / "site" / language
    summary = root / "SUMMARY.md"
    if not summary.is_file():
        pytest.skip(f"{language} has no SUMMARY.md")

    missing = []
    for match in re.finditer(r"\]\(([^)]+\.md)\)", summary.read_text(encoding="utf-8")):
        target = root / match.group(1)
        if not target.is_file():
            missing.append(match.group(1))

    assert missing == [], f"{language}/SUMMARY.md points at missing pages: {missing}"


def test_no_page_links_to_the_retired_gitbook_site() -> None:
    offenders = []
    for language in LANGUAGE_DIRS:
        for page in (REPO_ROOT / "docs" / "site" / language).rglob("*.md"):
            if "ai4commsci.gitbook.io" in page.read_text(encoding="utf-8"):
                offenders.append(str(page.relative_to(REPO_ROOT)))

    assert offenders == [], f"pages still link to the retired GitBook site: {offenders}"
```

- [ ] **Step 7: Run and fix real findings**

```bash
pytest tests/site/test_site_content.py -v
```

The nav test may fail on the generated pages from Task 5 (`policies.md`, `audio-permissions.md`) — they exist only after the build. Add them to an explicit allowlist in the test rather than weakening it:

```python
GENERATED_PAGES = {
    "the-bank-architecture/policies.md",
    "the-bank-architecture/audio-permissions.md",
}
```

and skip those in the loop. Fix any genuine dangling links and legacy URLs in the content itself.

- [ ] **Step 8: Write `tests/site/test_check_site.py`**

```python
from pathlib import Path

import pytest

from conftest import load

check_site = load("check_site")


def test_relative_link_resolves_within_the_site(tmp_path: Path) -> None:
    (tmp_path / "guide").mkdir()
    source = tmp_path / "guide" / "index.html"
    source.write_text("<html></html>", encoding="utf-8")

    target, _ = check_site.resolve_target(tmp_path, source, "../index.html")

    assert target == tmp_path / "index.html"


def test_absolute_link_with_the_project_base_resolves(tmp_path: Path) -> None:
    source = tmp_path / "index.html"
    source.write_text("<html></html>", encoding="utf-8")

    target, _ = check_site.resolve_target(
        tmp_path, source, "https://formosanbank.github.io/FormosanBank/zh/"
    )

    assert target == tmp_path / "zh" / "index.html"


def test_external_link_is_reported_as_external(tmp_path: Path) -> None:
    source = tmp_path / "index.html"
    source.write_text("<html></html>", encoding="utf-8")

    with pytest.raises(ValueError, match="external"):
        check_site.resolve_target(tmp_path, source, "https://example.com/x")


def test_parse_page_collects_duplicate_ids(tmp_path: Path) -> None:
    page = tmp_path / "p.html"
    page.write_text(
        '<html lang="en"><h1>A</h1><div id="x"></div><div id="x"></div></html>',
        encoding="utf-8",
    )

    parsed = check_site.parse_page(page)

    assert parsed.duplicate_ids == {"x"}
    assert parsed.h1_count == 1
    assert parsed.language == "en"
```

- [ ] **Step 9: Run the whole site suite**

```bash
pytest tests/site/ -v
```

Expected: PASS. `test_absolute_link_with_the_project_base_resolves` specifically pins the Task 3 base-path fix.

- [ ] **Step 10: Commit**

```bash
git add tests/site docs/tools/prepare_site.py
git commit -m "Test check_site, nav integrity, and directive handling"
```

---

### Task 9: Wire CI — deploy workflow and folded test workflow

**Files:**
- Create: `.github/workflows/pages.yaml`
- Modify: `.github/workflows/tests.yaml`, `requirements.txt`

- [ ] **Step 1: Add the site deps to the repo requirements**

`tests/site/` must run in the existing `tests.yaml` job, which installs only `requirements.txt`. Append to `requirements.txt`:

```
# Documentation site build (docs/tools/build-site.sh, tests/site/)
mkdocs-material==9.7.7
mkdocs-literate-nav==0.6.3
properdocs==1.6.7
```

Keep `requirements-site.txt` as well, so the Pages job can install the site deps alone without the QC stack.

- [ ] **Step 2: Extend the existing test workflow's path filters**

`.github/workflows/tests.yaml` filters on `QC/**`, `tests/**`, `Corpora/**`, `requirements.txt`, `pyproject.toml`, and itself. Docs changes must now trigger it too. Add to **both** the `pull_request` and `push` path lists:

```yaml
      - 'docs/**'
      - 'mkdocs*.yml'
      - 'requirements-site.txt'
```

- [ ] **Step 3: Add the corpus-page lint to the same workflow**

The GitBook repo's `corpus-page-lint.yaml` checked out two repos. Same-repo it is one step. Add to the `pytest` job in `.github/workflows/tests.yaml`, after "Run pytest":

```yaml
      - name: Corpus-page drift lint (strict)
        run: |
          python docs/tools/manage_corpus_pages.py check \
            --ignore docs/tools/corpus_pages_ignore.txt \
            --strict
```

- [ ] **Step 4: Verify locally that CI would pass**

```bash
cd /workspace/wt-docs-migration
source /workspace/FormosanBank/.venv/bin/activate
pip install -r requirements.txt
pytest
python docs/tools/manage_corpus_pages.py check --ignore docs/tools/corpus_pages_ignore.txt --strict
```

Expected: pytest passes including `tests/site/`; the lint exits 0.

- [ ] **Step 5: Create the Pages deploy workflow**

Create `.github/workflows/pages.yaml`. It deploys only from `main`; on PRs it builds without deploying, so a broken site fails review rather than production.

```yaml
name: pages

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: pip
          cache-dependency-path: requirements-site.txt
      - name: Install site dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements-site.txt
      - name: Build all three language editions
        run: ./docs/tools/build-site.sh
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site

  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

`build-site.sh` ends with `check_site.py`, so a broken link fails the build step and nothing deploys.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/pages.yaml .github/workflows/tests.yaml requirements.txt
git commit -m "Build and deploy the documentation site from CI"
```

- [ ] **Step 7: Enable Pages in repository settings (manual, maintainer)**

GitHub → `FormosanBank/FormosanBank` → Settings → Pages → Source: **GitHub Actions**. Until this is set, the `deploy` job fails with "Pages is not enabled". Do this before merging to `main`.

---

### Task 10: Rewrite the `port-corpus-in` skill's GitBook phase

Phase 5 currently locates a sibling repo, asks the operator which branch GitBook publishes from, edits a second working tree, and tells the operator to open a second PR. All four of those disappear.

**Files:**
- Modify: `.claude/skills/port-corpus-in/SKILL.md:206-330`

- [ ] **Step 1: Rewrite Phase 5**

Replace the section beginning `### Phase 5: Add to GitBook` with a version that:
- Renames the phase to **"Add to the documentation site"**.
- Deletes step 1 ("Locate the GitBook repo") entirely.
- Deletes the `AskUserQuestion` about which branch GitBook publishes from — there is one branch and one repo now.
- Changes the helper invocation to:

```bash
<python> docs/tools/manage_corpus_pages.py add \
  --corpus "<FBDir>" \
  --slug "<slug>.md" \
  --nav-label "<label>" \
  --title "<title>" \
  --template .claude/skills/port-corpus-in/corpus_page.template.md \
  --descriptors "<descriptors>"
```

- Changes the prose-filling path to `docs/site/en-us/the-bank-architecture/corpora/<slug>`.
- Changes the check invocation to `<python> docs/tools/manage_corpus_pages.py check --ignore docs/tools/corpus_pages_ignore.txt --strict`.
- **Deletes the stats-injection sub-step** (old step "c. Inject the tables into the GitBook"). Statistics are injected at build time as of Task 6; there is nothing to run and nothing to commit.
- Changes the completion summary lines from "GitBook page created on branch <chosen>; commit and open the GitBook PR separately" to "Corpus page created at `docs/site/en-us/...`; it ships in this port's PR."

- [ ] **Step 2: Update the skill's front-matter option**

Line 18 documents `skip_gitbook`. Rename it to `skip_docs` and update the description to "If `true`, Phase 5 (Add to the documentation site) is skipped." Keep `skip_gitbook` mentioned once as a deprecated alias so existing invocations are understood.

- [ ] **Step 3: Verify no sibling-repo references remain**

```bash
grep -n -i 'gitbook_path\|FormosanBankGitbook\|which branch does GitBook' .claude/skills/port-corpus-in/SKILL.md
```

Expected: no matches.

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/port-corpus-in/SKILL.md
git commit -m "port-corpus-in: the corpus page is now part of the same repo and PR"
```

---

### Task 11: Update the surrounding documentation and helpers

**Files:**
- Modify: `CLAUDE.md:24`, `CLAUDE.md:104`, `AGENTS.md`, `QC/utilities/port_audio_seconds_from_gitbook.py`, `docs/site/en-us/the-bank-architecture/developers/repository-contracts/*.md`

- [ ] **Step 1: Rewrite the "Related repos" entry in CLAUDE.md**

Replace the `../FormosanBankGitbook/` bullet (line 24) with:

```markdown
- **[docs/site/](docs/site/)** — the public documentation site, published at
  https://formosanbank.github.io/FormosanBank/ via GitHub Pages. Three language
  editions: `en-us/` (canonical), `pwn/` (Paiwan), `zh-TW/` (Mandarin), served at
  `/`, `/paiwan/`, and `/zh/`. Built by `docs/tools/build-site.sh`
  (`prepare_site.py` → properdocs/mkdocs-material → `check_site.py`) and deployed
  by [.github/workflows/pages.yaml](.github/workflows/pages.yaml). The POLICIES and
  Audio Permissions pages are **generated at build time** from `POLICIES.md` and
  `AUDIO-PERMISSIONS.md`; corpus statistics tables are injected at build time from
  `statistics/*.csv`. Never commit a generated page or a stats block by hand.
  (Formerly the separate `FormosanBankGitbook` repo, published via GitBook Git Sync;
  merged in 2026-09 when that paid integration lapsed.)
```

- [ ] **Step 2: Update the corpus-metrics paragraph**

CLAUDE.md line 104 says the per-corpus CSVs are "the per-corpus CSVs the Gitbook consumes". Change that phrase to "the per-corpus CSVs the documentation site consumes at build time".

- [ ] **Step 3: Update AGENTS.md**

```bash
grep -n -i 'gitbook' AGENTS.md
```

Apply the same substitution: the sibling repo is now `docs/site/` in this repo.

- [ ] **Step 4: Repoint the audio-seconds helper**

`QC/utilities/port_audio_seconds_from_gitbook.py` reads from the sibling repo. Read it, then either update its path resolution to `docs/site/` or, if it was a one-time migration script that has already served its purpose, delete it. Decide by checking whether anything references it:

```bash
grep -rn 'port_audio_seconds_from_gitbook' --include='*.py' --include='*.md' --include='*.yaml' . | grep -v claudeplans
```

If nothing references it and its output (`statistics/audio_durations.csv`) is already populated, delete it and say so in the commit message.

- [ ] **Step 5: Update the Repository Contracts pages**

The `docs/site/en-us/the-bank-architecture/developers/repository-contracts/` section (added 2026-09-04) documents CI workflows, generated files, synced pages, and single sources of truth. Every one of those four is changed by this migration.

- `synced-pages.md` — describes `sync_upstream_docs.py`, which no longer exists. Rewrite as "generated pages", describing build-time inclusion.
- `ci-workflows.md` — add `pages.yaml`; remove the two GitBook-repo workflows.
- `generated-files.md` — add the generated policy/audio pages and the build-time stats blocks.
- `single-sources-of-truth.md` — POLICIES.md and AUDIO-PERMISSIONS.md are now single-sourced by construction rather than by a drift test.

- [ ] **Step 6: Verify and commit**

```bash
grep -rn 'FormosanBankGitbook' --include='*.md' --include='*.py' --include='*.yaml' . | grep -v '^./claudeplans' | grep -v '^./docs/superpowers'
```

Expected: no matches outside historical planning docs, which are records and stay as written.

```bash
git add CLAUDE.md AGENTS.md QC/utilities docs/site
git commit -m "Document the in-repo documentation site"
```

---

### Task 12: Cut over

**Files:** none in this repo — repository administration.

- [ ] **Step 1: Full verification before merge**

```bash
cd /workspace/wt-docs-migration
source /workspace/FormosanBank/.venv/bin/activate
pytest
python docs/tools/manage_corpus_pages.py check --ignore docs/tools/corpus_pages_ignore.txt --strict
./docs/tools/build-site.sh
```

Expected: all three exit 0. Do not proceed on a partial pass.

- [ ] **Step 2: Open the PR**

```bash
git push -u origin feature/docs-into-repo
```

Open it against `main`. The PR is large by construction (it carries an imported history); say so in the description and link this plan.

- [ ] **Step 3: Confirm the deployed site after merge**

After merge to `main`, watch the `pages` workflow, then check:
- `https://formosanbank.github.io/FormosanBank/` — English, nav intact
- `https://formosanbank.github.io/FormosanBank/zh/` and `/paiwan/` — translations render
- A corpus page shows a statistics table
- The Policies page shows current `POLICIES.md` content

- [ ] **Step 4: Archive the old repository (maintainer)**

Only after the new site is confirmed live. In `FormosanBank/FormosanBankGitbook` → Settings → Archive this repository. Archiving preserves it read-only; do not delete it. Add a line to its README first pointing at the new location.

- [ ] **Step 5: Clean up the worktree**

```bash
cd /workspace/FormosanBank
git worktree remove /workspace/wt-docs-migration
rm -rf /tmp/gitbook-rewrite
```

---

## What this migration removes

Worth stating plainly, because it is the point of the exercise:

| Removed | Replaced by |
|---|---|
| `sync_upstream_docs.py` + its drift test | Build-time inclusion — drift is impossible, not merely detected |
| `update_corpus_stats.py`'s sibling-repo resolution and the manual "inject and commit" step | Build-time injection from `statistics/*.csv` |
| Two GitHub workflows that checked out a second repository | One repo, one checkout |
| `port-corpus-in`'s "which branch does GitBook publish from?" question | One branch, one repo |
| A second PR for every corpus port | The page ships in the port's own PR |
| GitBook subscription | GitHub Pages, free on a public repo |
| A publishing integration that failed silently on a billing change | A build that fails loudly in CI |

## Self-review notes

- Every requirement in the decisions section maps to a task: Pages publishing → Tasks 2, 3, 4, 9; move into this repo → Task 1; rework syncing → Tasks 5, 6, 7; port the tests → Task 2 Step 3, Task 6, Task 7; add tests → Task 8.
- Interfaces are pinned: `NEW_SITE` (Task 3) is consumed by Task 8's `test_absolute_link_with_the_project_base_resolves`; `inject_stats_into_tree` (Task 6) is called from `prepare_site` in the same task; `IncludedDoc`/`render_included_doc` (Task 5) are used only within Task 5 and by Task 11's docs.
- Two decisions are deliberately left to the maintainer and flagged at the top rather than assumed silently: the published URL, and Hunter's reason for the revert.
