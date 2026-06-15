# Reproducible manual XML edits — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Before writing any code, read the design doc at `claudeplans/2026-06-15-manual-edits-reproducibility-design.md` in full, and skim `QC/cleaning/clean_xml.py` (CLI + in-place write pattern) and `tests/cleaners/test_clean_xml.py` (subprocess test pattern).

**Goal:** Generalize the Nowbucyang `manual_sentences.xml` pattern into two reusable QC scripts — `QC/utilities/capture_manual_edits.py` (snapshot hand edits into `CodeAndDocs/manual_edits.xml`) and `QC/cleaning/apply_manual_edits.py` (re-apply them first in the cleaning pipeline, prune no-ops with a warning, emit a `manual_edits.md` changelog) — working across multi-file corpora.

**Architecture:** A shared module `QC/cleaning/manual_edits_common.py` holds the data-model helpers (strip/canonical/render, manual-file read/write, git access, path resolution). `capture` is a dumb snapshotter that diffs the working tree against a git baseline and writes full (stripped) `<S>` blocks. `apply` is the smart half: it is the only script with `O` (the pre-manual on-disk XML), so it applies upsert/insert/delete, prunes entries that are no-ops against `O`, and regenerates the changelog.

**Tech Stack:** Python 3.13, `lxml.etree`, `subprocess` (git access + tests), `pytest`. No new dependencies.

---

## Background facts an implementer needs

- **CLI convention:** QC scripts take `--corpora_path` pointing at an XML directory and walk it for `*.xml` (see `clean_xml.py`). Both new scripts follow this. `--corpora_path` is the corpus's XML root.
- **Import convention:** there are no `__init__.py` files; scripts put the repo root on `sys.path` and import via the `QC.*` namespace (see `QC/validation/validate_glosses.py:36-48`, `QC/utilities/standardize.py:14-15`). Both new scripts do the same so they can `from QC.cleaning.manual_edits_common import ...`.
- **In-place writes:** cleaners parse with `lxml.etree` and write with `tree.write(path, xml_declaration=True, pretty_print=True, encoding="utf-8")` (see `clean_xml.py:655`).
- **Tests:** invoke scripts via `subprocess.run([sys.executable, str(SCRIPT), ...])` and assert on `tmp_path` copies; pure helpers may be imported directly. Fixtures `tmp_path`, `fixtures_dir`, `copy_fixture` exist in `tests/conftest.py`; shared assert helpers in `tests/_helpers.py`. `pyproject.toml` sets `testpaths=["tests"]`, `python_files="test_*.py"`.
- **Data model** (full detail in the design doc):
  - `manual_edits.xml`: `<MANUAL_EDITS>` → `<FILE path="rel/to/corpora_path.xml">` → `<S>` blocks.
  - `<S id="...">…</S>` = upsert (replace-by-id, else insert); `<S id="..." after="X">` = upsert of a *new* id placed after `X`; `<S id="..." action="delete"/>` = delete-by-id.
  - Recorded `<S>` are stored on the **strip()** basis: all standard-tier FORM + all PHON removed, `after`/`action` are bookkeeping only.
- **The strip/no-op contract:** `apply`'s no-op prune (`strip(O[id]) == strip(R)` → delete `R`) is correct only when `O` is fresh pre-manual build output. This is a documented discipline, not enforced.

---

## File structure

**Create:**
| File | Responsibility |
|---|---|
| `QC/cleaning/manual_edits_common.py` | Shared data-model + git + path helpers, imported by both scripts |
| `QC/cleaning/apply_manual_edits.py` | Cleaner: apply + prune + changelog |
| `QC/utilities/capture_manual_edits.py` | Utility: snapshot hand edits vs git baseline |
| `tests/cleaners/test_manual_edits_common.py` | Unit tests for the shared module |
| `tests/cleaners/test_apply_manual_edits.py` | Integration tests for `apply` (subprocess) |
| `tests/utilities/test_capture_manual_edits.py` | Integration tests for `capture` (subprocess, real git) |

**Modify (docs only, final task):**
| File | Change |
|---|---|
| `QC/README.md` | Document the two scripts + workflow; place `apply` first in the pipeline order |
| `CLAUDE.md` | Brief mention under QC cleaning conventions |
| `.claude/skills/run-qc-pipeline/SKILL.md` | Add `apply_manual_edits.py` as Phase 0; describe the capture loop |

**Not touched:** any `Corpora/` data; other QC scripts; CI workflows.

---

## Task 1: Shared module — strip / canonical / render / path helpers

**Files:**
- Create: `QC/cleaning/manual_edits_common.py`
- Test: `tests/cleaners/test_manual_edits_common.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/cleaners/test_manual_edits_common.py`:

```python
"""Unit tests for QC/cleaning/manual_edits_common.py (pure helpers)."""
import sys
from pathlib import Path

from lxml import etree

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.cleaning import manual_edits_common as mec


def _s(xml: str) -> etree._Element:
    return etree.fromstring(xml)


def test_strip_s_removes_standard_forms_at_all_levels():
    s = _s(
        '<S id="x">'
        '<FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM>'
        '<W id="x1"><FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM></W>'
        "</S>"
    )
    out = mec.strip_s(s)
    kinds = [f.get("kindOf") for f in out.findall(".//FORM")]
    assert kinds == ["original", "original"]


def test_strip_s_removes_all_phon():
    s = _s(
        '<S id="x"><FORM kindOf="original">a</FORM>'
        '<PHON kindOf="original">a</PHON>'
        '<W id="x1"><PHON kindOf="original">a</PHON></W></S>'
    )
    out = mec.strip_s(s)
    assert out.findall(".//PHON") == []


def test_strip_s_drops_after_and_action_attrs():
    s = _s('<S id="x" after="w" action="delete"><FORM kindOf="original">a</FORM></S>')
    out = mec.strip_s(s)
    assert "after" not in out.attrib
    assert "action" not in out.attrib


def test_strip_s_does_not_mutate_input():
    s = _s('<S id="x"><FORM kindOf="standard">A</FORM></S>')
    mec.strip_s(s)
    assert s.findall(".//FORM") != []  # original element untouched


def test_canonical_s_ignores_standard_phon_and_whitespace():
    a = _s('<S id="x">\n  <FORM kindOf="original">a</FORM>\n</S>')
    b = _s(
        '<S id="x"><FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM><PHON kindOf="original">a</PHON></S>'
    )
    assert mec.canonical_s(a) == mec.canonical_s(b)


def test_canonical_s_distinguishes_different_original_text():
    a = _s('<S id="x"><FORM kindOf="original">a</FORM></S>')
    b = _s('<S id="x"><FORM kindOf="original">b</FORM></S>')
    assert mec.canonical_s(a) != mec.canonical_s(b)


def test_render_s_shows_original_form_and_translations():
    s = _s(
        '<S id="x"><FORM kindOf="original">hala</FORM>'
        '<TRANSL xml:lang="zho">你好</TRANSL></S>'
    )
    out = mec.render_s(s)
    assert "hala" in out and "你好" in out


def test_default_manual_file_is_codeanddocs_sibling(tmp_path):
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir()
    got = mec.default_manual_file(xml_dir)
    assert got == (tmp_path / "CodeAndDocs" / "manual_edits.xml")


def test_changelog_path_swaps_suffix(tmp_path):
    assert mec.changelog_path(tmp_path / "CodeAndDocs" / "manual_edits.xml") == (
        tmp_path / "CodeAndDocs" / "manual_edits.md"
    )
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py -q`
Expected: collection/import error — `ModuleNotFoundError: No module named 'QC.cleaning.manual_edits_common'`.

- [ ] **Step 3: Write the module (this slice)**

Create `QC/cleaning/manual_edits_common.py`:

```python
"""Shared helpers for the manual-edits capture/apply pair.

manual_edits.xml records hand edits to a corpus's XML as full <S> blocks
(see claudeplans/2026-06-15-manual-edits-reproducibility-design.md):

    <MANUAL_EDITS>
      <FILE path="Amis/story01.xml">
        <S id="...">...</S>                  upsert (replace-by-id or insert)
        <S id="..." after="...">...</S>      upsert of a NEW id, placement hint
        <S id="..." action="delete"/>        delete-by-id
      </FILE>
    </MANUAL_EDITS>

Recorded <S> blocks are stored on the strip() basis: all standard-tier
FORM and all PHON removed, because standardize.py / add_phonology.py
regenerate those tiers downstream (apply runs before them).
"""
from __future__ import annotations

import copy
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


# ----- path resolution -------------------------------------------------------

def default_manual_file(corpora_path) -> Path:
    """Default manual-edits file: <corpus-root>/CodeAndDocs/manual_edits.xml,
    i.e. a CodeAndDocs/ sibling of the XML directory given as corpora_path."""
    return Path(corpora_path).resolve().parent / "CodeAndDocs" / "manual_edits.xml"


def changelog_path(manual_file) -> Path:
    """Human-readable changelog path next to the manual file (.md suffix)."""
    return Path(manual_file).with_suffix(".md")


# ----- the strip()/canonical basis -------------------------------------------

def strip_s(s_elem: etree._Element) -> etree._Element:
    """Deep copy of <S> reduced to manual-relevant content: every standard-tier
    FORM and every PHON removed (S/W/M), and after/action attrs dropped."""
    el = copy.deepcopy(s_elem)
    el.attrib.pop("after", None)
    el.attrib.pop("action", None)
    for form in el.findall(".//FORM[@kindOf='standard']"):
        form.getparent().remove(form)
    for phon in el.findall(".//PHON"):
        phon.getparent().remove(phon)
    return el


def canonical_s(s_elem: etree._Element) -> str:
    """Canonical (c14n) string of an <S> on the strip() basis, for equality.

    Reparsed with remove_blank_text so indentation differences don't make two
    otherwise-identical blocks compare unequal.
    """
    stripped = strip_s(s_elem)
    reparsed = etree.fromstring(
        etree.tostring(stripped), parser=etree.XMLParser(remove_blank_text=True)
    )
    return etree.tostring(reparsed, method="c14n").decode("utf-8")


def render_s(s_elem: etree._Element) -> str:
    """One-line human rendering for the changelog: original FORM + TRANSLs."""
    parts: list[str] = []
    originals = s_elem.findall("FORM[@kindOf='original']")
    if not originals:
        originals = s_elem.findall("FORM")[:1]
    for form in originals:
        if form.text and form.text.strip():
            parts.append(form.text.strip())
    for tr in s_elem.findall("TRANSL"):
        lang = tr.get(XML_LANG, "")
        text = (tr.text or "").strip()
        if text:
            parts.append(f"[{lang}] {text}")
    return " / ".join(parts)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py -q`
Expected: PASS (9 tests).

- [ ] **Step 5: Commit**

```bash
git add QC/cleaning/manual_edits_common.py tests/cleaners/test_manual_edits_common.py
git commit -m "feat(manual-edits): shared strip/canonical/render/path helpers"
```

---

## Task 2: Shared module — manual-file model + git helpers

**Files:**
- Modify: `QC/cleaning/manual_edits_common.py`
- Test: `tests/cleaners/test_manual_edits_common.py`

- [ ] **Step 1: Add the failing tests**

Append to `tests/cleaners/test_manual_edits_common.py`:

```python
import subprocess


def test_manual_root_roundtrip_and_groups(tmp_path):
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "Amis/a.xml")
    fg.append(_s('<S id="S1"><FORM kindOf="original">a</FORM></S>'))
    path = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    mec.write_manual(root, path)
    assert path.exists()
    back = mec.load_manual(path)
    assert mec.find_file_group(back, "Amis/a.xml") is not None
    assert mec.find_file_group(back, "nope.xml") is None


def test_load_manual_missing_returns_none(tmp_path):
    assert mec.load_manual(tmp_path / "absent.xml") is None


def test_upsert_record_replaces_by_id(tmp_path):
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "a.xml")
    mec.upsert_record(fg, _s('<S id="S1"><FORM kindOf="original">old</FORM></S>'))
    mec.upsert_record(fg, _s('<S id="S1"><FORM kindOf="original">new</FORM></S>'))
    ss = fg.findall("S")
    assert len(ss) == 1
    assert ss[0].find("FORM").text == "new"


def test_upsert_record_appends_new_id_in_order(tmp_path):
    root = mec.new_manual_root()
    fg = mec.get_or_create_file_group(root, "a.xml")
    mec.upsert_record(fg, _s('<S id="S1"/>'))
    mec.upsert_record(fg, _s('<S id="S2"/>'))
    assert [s.get("id") for s in fg.findall("S")] == ["S1", "S2"]


def test_write_manual_drops_empty_file_groups(tmp_path):
    root = mec.new_manual_root()
    mec.get_or_create_file_group(root, "empty.xml")  # no <S>
    fg = mec.get_or_create_file_group(root, "a.xml")
    fg.append(_s('<S id="S1"/>'))
    path = tmp_path / "m.xml"
    mec.write_manual(root, path)
    back = mec.load_manual(path)
    assert mec.find_file_group(back, "empty.xml") is None
    assert mec.find_file_group(back, "a.xml") is not None


def test_git_root_and_show(tmp_path):
    repo = tmp_path
    (repo / "f.txt").write_text("v1\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    subprocess.run(["git", "add", "f.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "c1"], cwd=repo, check=True)
    (repo / "f.txt").write_text("v2\n", encoding="utf-8")  # uncommitted
    assert mec.git_root(repo).resolve() == repo.resolve()
    assert mec.git_show(repo, "HEAD", "f.txt") == b"v1\n"
    assert mec.git_show(repo, "HEAD", "missing.txt") is None


def test_git_root_outside_repo_returns_none(tmp_path):
    # tmp_path here has no git repo initialized
    assert mec.git_root(tmp_path) is None
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py -q`
Expected: FAIL — `AttributeError: module ... has no attribute 'new_manual_root'`.

- [ ] **Step 3: Append the implementation**

Append to `QC/cleaning/manual_edits_common.py`:

```python
import subprocess


# ----- manual-file model -----------------------------------------------------

def new_manual_root() -> etree._Element:
    return etree.Element("MANUAL_EDITS")


def load_manual(manual_file):
    """Parse manual_edits.xml -> <MANUAL_EDITS> root, or None if absent."""
    p = Path(manual_file)
    if not p.exists():
        return None
    return etree.parse(str(p)).getroot()


def find_file_group(root, rel_path):
    for fe in root.findall("FILE"):
        if fe.get("path") == rel_path:
            return fe
    return None


def get_or_create_file_group(root, rel_path):
    fe = find_file_group(root, rel_path)
    if fe is None:
        fe = etree.SubElement(root, "FILE", {"path": rel_path})
    return fe


def upsert_record(file_group, s_record):
    """Replace the <S> with matching id, or append s_record if id is new."""
    sid = s_record.get("id")
    for existing in file_group.findall("S"):
        if existing.get("id") == sid:
            file_group.replace(existing, s_record)
            return
    file_group.append(s_record)


def remove_record(file_group, sid) -> bool:
    for existing in file_group.findall("S"):
        if existing.get("id") == sid:
            file_group.remove(existing)
            return True
    return False


def write_manual(root, manual_file):
    """Serialize the manual root (dropping empty <FILE> groups), pretty-printed."""
    for fe in list(root.findall("FILE")):
        if not fe.findall("S"):
            root.remove(fe)
    p = Path(manual_file)
    p.parent.mkdir(parents=True, exist_ok=True)
    tree = etree.ElementTree(root)
    etree.indent(tree, space="    ")
    tree.write(str(p), xml_declaration=True, pretty_print=True, encoding="utf-8")


# ----- git access ------------------------------------------------------------

def git_root(path):
    """Top-level of the git work tree containing path, or None."""
    res = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        return None
    return Path(res.stdout.strip())


def git_show(repo_root, ref, rel_path):
    """Bytes of <ref>:<rel_path>, or None if not present at that ref."""
    res = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{rel_path}"],
        capture_output=True,
    )
    if res.returncode != 0:
        return None
    return res.stdout
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py -q`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add QC/cleaning/manual_edits_common.py tests/cleaners/test_manual_edits_common.py
git commit -m "feat(manual-edits): manual-file model + git helpers"
```

---

## Task 3: `capture_manual_edits.py` — CLI + change capture

**Files:**
- Create: `QC/utilities/capture_manual_edits.py`
- Test: `tests/utilities/test_capture_manual_edits.py`

- [ ] **Step 1: Write the failing test (with a git fixture helper)**

Create `tests/utilities/test_capture_manual_edits.py`:

```python
"""Integration tests for QC/utilities/capture_manual_edits.py.

capture diffs the working XML tree against a git baseline and records
hand edits into <corpus-root>/CodeAndDocs/manual_edits.xml. Tests build a
real git repo in tmp_path: repo root = tmp_path, XML root = tmp_path/XML.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

CAPTURE = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "capture_manual_edits.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True, text=True)


def _init_repo(repo: Path) -> None:
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _commit_all(repo: Path, msg: str = "c") -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)


def _doc(*sentences: str) -> str:
    body = "".join(sentences)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<TEXT id="T" xml:lang="ami">{body}</TEXT>\n'


def _sent(sid: str, original: str, standard: str | None = None) -> str:
    std = f'<FORM kindOf="standard">{standard}</FORM>' if standard else ""
    return f'<S id="{sid}"><FORM kindOf="original">{original}</FORM>{std}</S>'


def _run_capture(corpora_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CAPTURE), "--corpora_path", str(corpora_path), *extra],
        capture_output=True, text=True,
    )


def _manual_root(repo: Path):
    return etree.parse(str(repo / "CodeAndDocs" / "manual_edits.xml")).getroot()


def test_change_is_recorded_stripped_under_file_group(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "Amis" / "a.xml"
    _write(xml, _doc(_sent("S1", "old", "OLD")))
    _init_repo(repo)
    _commit_all(repo)
    # hand-edit the original tier
    _write(xml, _doc(_sent("S1", "new", "OLD")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    root = _manual_root(repo)
    fg = root.find("FILE[@path='Amis/a.xml']")
    assert fg is not None
    s = fg.find("S[@id='S1']")
    assert s.find("FORM[@kindOf='original']").text == "new"
    # standard tier stripped from the recorded block
    assert s.find("FORM[@kindOf='standard']") is None


def test_unchanged_tree_writes_no_manual_file(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()


def test_standard_only_change_is_not_captured(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x", "X")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S1", "x", "DIFFERENT")))  # only standard tier changed
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/utilities/test_capture_manual_edits.py -q`
Expected: FAIL — script does not exist (non-zero return; assertions fail).

- [ ] **Step 3: Write `capture_manual_edits.py` (this slice — change capture only)**

Create `QC/utilities/capture_manual_edits.py`:

```python
"""Snapshot hand edits to a corpus's XML into CodeAndDocs/manual_edits.xml.

Dumb snapshotter: for each <S>, compare the working tree (W) against a git
baseline (B, default HEAD) on the strip() basis. B != W -> record strip(W);
present in B but absent in W -> record a delete; new id -> record with an
`after` placement hint. No O, no changelog, no pruning (apply does those).

See claudeplans/2026-06-15-manual-edits-reproducibility-design.md.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.cleaning import manual_edits_common as mec


def _s_map(root):
    return {s.get("id"): s for s in root.findall(".//S") if s.get("id")}


def _s_order(root):
    return [s.get("id") for s in root.findall(".//S") if s.get("id")]


def capture(corpora_path, manual_file, baseline_ref) -> int:
    corpora_path = Path(corpora_path).resolve()
    repo = mec.git_root(corpora_path)
    if repo is None:
        print(f"ERROR: {corpora_path} is not inside a git work tree; "
              f"capture needs a '{baseline_ref}' baseline to diff against.",
              file=sys.stderr)
        return 2

    root = mec.load_manual(manual_file) or mec.new_manual_root()
    dirty = False

    for xml_path in sorted(corpora_path.rglob("*.xml")):
        rel_corpora = xml_path.relative_to(corpora_path).as_posix()
        rel_repo = xml_path.relative_to(repo).as_posix()
        baseline_bytes = mec.git_show(repo, baseline_ref, rel_repo)
        if baseline_bytes is None:
            print(f"WARNING: {rel_corpora} is not present at {baseline_ref}; "
                  f"skipping (treated as new build output, not hand edits).")
            continue

        w_root = etree.parse(str(xml_path)).getroot()
        b_root = etree.fromstring(baseline_bytes)
        w_map, b_map = _s_map(w_root), _s_map(b_root)
        w_order = _s_order(w_root)

        for idx, sid in enumerate(w_order):
            w_s = w_map[sid]
            if sid in b_map:
                if mec.canonical_s(w_s) == mec.canonical_s(b_map[sid]):
                    continue  # B == W: leave untouched
                record = mec.strip_s(w_s)  # change
            else:
                record = mec.strip_s(w_s)  # new S
                if idx > 0:
                    record.set("after", w_order[idx - 1])
            fg = mec.get_or_create_file_group(root, rel_corpora)
            mec.upsert_record(fg, record)
            dirty = True

        for sid in b_map:
            if sid not in w_map:  # deletion
                fg = mec.get_or_create_file_group(root, rel_corpora)
                mec.upsert_record(fg, etree.Element("S", {"id": sid, "action": "delete"}))
                dirty = True

    if dirty:
        mec.write_manual(root, manual_file)
        print(f"capture: wrote {manual_file}")
    else:
        print("capture: no hand edits detected; manual file unchanged.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Snapshot hand edits into manual_edits.xml")
    parser.add_argument("--corpora_path", required=True, help="the corpus XML root")
    parser.add_argument("--manual_file", default=None,
                        help="manual edits file (default <corpus-root>/CodeAndDocs/manual_edits.xml)")
    parser.add_argument("--baseline-ref", dest="baseline_ref", default="HEAD",
                        help="git ref to diff against (default HEAD)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if not Path(args.corpora_path).exists():
        parser.error(f"--corpora_path does not exist: {args.corpora_path}")
    manual_file = args.manual_file or mec.default_manual_file(args.corpora_path)
    return capture(args.corpora_path, manual_file, args.baseline_ref)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/utilities/test_capture_manual_edits.py -q`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/capture_manual_edits.py tests/utilities/test_capture_manual_edits.py
git commit -m "feat(manual-edits): capture change snapshots vs git baseline"
```

---

## Task 4: `capture` — additions/anchors, chains, deletions, new-file skip, no-git error

**Files:**
- Modify: `tests/utilities/test_capture_manual_edits.py` (add tests; implementation already covers these — this task verifies and hardens)

> The Task 3 implementation already handles additions, anchors, chains, deletions, the new-file warning, and the no-git error. This task adds the tests that prove it and fixes anything they surface.

- [ ] **Step 1: Add the tests**

Append to `tests/utilities/test_capture_manual_edits.py`:

```python
def test_new_s_is_recorded_with_after_anchor(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "one")))
    _init_repo(repo)
    _commit_all(repo)
    # split: edit S1, add S1b after it
    _write(xml, _doc(_sent("S1", "one-a"), _sent("S1b", "one-b")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S1']").find("FORM").text == "one-a"
    s1b = fg.find("S[@id='S1b']")
    assert s1b.get("after") == "S1"


def test_split_chain_anchors_on_immediate_predecessor(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S1", "x"), _sent("S1b", "b"), _sent("S1c", "c")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S1b']").get("after") == "S1"
    assert fg.find("S[@id='S1c']").get("after") == "S1b"


def test_first_sentence_addition_has_no_after(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S0", "new-first"), _sent("S1", "x")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert "after" not in fg.find("S[@id='S0']").attrib


def test_deletion_is_recorded(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x"), _sent("S2", "y")))
    _init_repo(repo)
    _commit_all(repo)
    _write(xml, _doc(_sent("S1", "x")))  # S2 removed
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S2']").get("action") == "delete"


def test_capture_is_additive_to_existing_entries(tmp_path):
    repo = tmp_path
    xml = repo / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x"), _sent("S2", "y")))
    _init_repo(repo)
    _commit_all(repo)
    # pre-existing manual file with an unrelated entry
    man = repo / "CodeAndDocs" / "manual_edits.xml"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(
        '<MANUAL_EDITS><FILE path="a.xml">'
        '<S id="S9"><FORM kindOf="original">keep</FORM></S>'
        "</FILE></MANUAL_EDITS>",
        encoding="utf-8",
    )
    _write(xml, _doc(_sent("S1", "edited"), _sent("S2", "y")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    fg = _manual_root(repo).find("FILE[@path='a.xml']")
    assert fg.find("S[@id='S9']") is not None  # survived
    assert fg.find("S[@id='S1']").find("FORM").text == "edited"


def test_file_absent_from_baseline_is_warned_and_skipped(tmp_path):
    repo = tmp_path
    a = repo / "XML" / "a.xml"
    _write(a, _doc(_sent("S1", "x")))
    _init_repo(repo)
    _commit_all(repo)
    # brand-new file never committed
    _write(repo / "XML" / "new.xml", _doc(_sent("N1", "z")))
    proc = _run_capture(repo / "XML")
    assert proc.returncode == 0, proc.stderr
    assert "new.xml" in proc.stdout and "skipping" in proc.stdout.lower()
    assert not (repo / "CodeAndDocs" / "manual_edits.xml").exists()


def test_not_a_git_repo_errors(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))  # no git init
    proc = _run_capture(tmp_path / "XML")
    assert proc.returncode == 2
    assert "git" in proc.stderr.lower()
```

- [ ] **Step 2: Run the tests**

Run: `.venv/bin/python -m pytest tests/utilities/test_capture_manual_edits.py -q`
Expected: PASS. If any fail, fix `capture_manual_edits.py` to satisfy them (do not weaken the tests).

- [ ] **Step 3: Commit**

```bash
git add tests/utilities/test_capture_manual_edits.py QC/utilities/capture_manual_edits.py
git commit -m "test(manual-edits): capture additions/chains/deletions/edge cases"
```

---

## Task 5: `apply_manual_edits.py` — CLI, missing-file no-op, upsert replace + insert

**Files:**
- Create: `QC/cleaning/apply_manual_edits.py`
- Test: `tests/cleaners/test_apply_manual_edits.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/cleaners/test_apply_manual_edits.py`:

```python
"""Integration tests for QC/cleaning/apply_manual_edits.py.

apply runs first in the cleaning pipeline, on the pre-manual build output
(O). It applies upsert/insert/delete, prunes no-op entries (with a console
warning), and regenerates CodeAndDocs/manual_edits.md.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

APPLY = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "apply_manual_edits.py"


def _doc(*sentences: str) -> str:
    body = "".join(sentences)
    return f'<?xml version="1.0" encoding="utf-8"?>\n<TEXT id="T" xml:lang="ami">{body}</TEXT>\n'


def _sent(sid: str, original: str) -> str:
    return f'<S id="{sid}"><FORM kindOf="original">{original}</FORM></S>'


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _run_apply(corpora_path: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(APPLY), "--corpora_path", str(corpora_path), *extra],
        capture_output=True, text=True,
    )


def _ids(xml_path: Path) -> list[str]:
    root = etree.parse(str(xml_path)).getroot()
    return [s.get("id") for s in root.findall(".//S")]


def _form(xml_path: Path, sid: str) -> str:
    root = etree.parse(str(xml_path)).getroot()
    s = root.find(f".//S[@id='{sid}']")
    return s.find("FORM[@kindOf='original']").text


def test_missing_manual_file_is_a_clean_noop(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "x")))
    before = xml.read_bytes()
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0
    assert "nothing to do" in proc.stdout.lower()
    assert xml.read_bytes() == before


def test_upsert_replaces_existing_sentence(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "build")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1"><FORM kindOf="original">manual</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _form(xml, "S1") == "manual"


def test_new_id_with_after_inserts_adjacent(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a"), _sent("S2", "c")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1b" after="S1"><FORM kindOf="original">b</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _ids(xml) == ["S1", "S1b", "S2"]


def test_new_id_without_resolvable_anchor_appends(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="SX" after="DOES_NOT_EXIST"><FORM kindOf="original">x</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _ids(xml) == ["S1", "SX"]
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/cleaners/test_apply_manual_edits.py -q`
Expected: FAIL — script missing.

- [ ] **Step 3: Write `apply_manual_edits.py` (this slice — apply without prune/changelog yet)**

Create `QC/cleaning/apply_manual_edits.py`:

```python
"""Re-apply recorded manual edits to a corpus's XML, first in the cleaning
pipeline. Applies upsert/insert/delete from CodeAndDocs/manual_edits.xml,
prunes entries that are no-ops against the current (pre-manual) XML O (with
a console warning), and regenerates CodeAndDocs/manual_edits.md.

See claudeplans/2026-06-15-manual-edits-reproducibility-design.md.
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from lxml import etree

from QC.cleaning import manual_edits_common as mec


def _s_map(root):
    return {s.get("id"): s for s in root.findall(".//S") if s.get("id")}


def _apply_file(xml_path, file_group, changelog, pruned):
    """Apply one FILE group's operations to xml_path. Returns True if the XML
    file was modified. Appends changelog entries and pruned (rel,id) tuples."""
    rel = file_group.get("path")
    tree = etree.parse(str(xml_path))
    text_root = tree.getroot()
    o_map = _s_map(text_root)
    modified = False

    for record in list(file_group.findall("S")):
        sid = record.get("id")
        if record.get("action") == "delete":
            if sid not in o_map:
                pruned.append((rel, sid)); mec.remove_record(file_group, sid); continue
            target = o_map.pop(sid)
            before = mec.render_s(target)
            target.getparent().remove(target)
            changelog.append({"file": rel, "sid": sid, "action": "deleted",
                              "before": before, "after": None})
            modified = True
            continue

        if sid in o_map:
            if mec.canonical_s(record) == mec.canonical_s(o_map[sid]):
                pruned.append((rel, sid)); mec.remove_record(file_group, sid); continue
            before = mec.render_s(o_map[sid])
            new_el = mec.strip_s(record)  # strip after/action for the live tree
            o_map[sid].getparent().replace(o_map[sid], new_el)
            o_map[sid] = new_el
            changelog.append({"file": rel, "sid": sid, "action": "changed",
                              "before": before, "after": mec.render_s(new_el)})
            modified = True
        else:
            after = record.get("after")
            new_el = mec.strip_s(record)
            anchor = o_map.get(after) if after else None
            if anchor is not None:
                anchor.addnext(new_el)
            else:
                text_root.append(new_el)
            o_map[sid] = new_el
            changelog.append({"file": rel, "sid": sid, "action": "added",
                              "before": None, "after": mec.render_s(new_el)})
            modified = True

    if modified:
        etree.indent(tree, space="    ")
        tree.write(str(xml_path), xml_declaration=True, pretty_print=True, encoding="utf-8")
    return modified


def apply(corpora_path, manual_file) -> int:
    corpora_path = Path(corpora_path).resolve()
    root = mec.load_manual(manual_file)
    if root is None:
        print(f"no manual-edits file found at {manual_file}; nothing to do")
        return 0

    changelog: list[dict] = []
    pruned: list[tuple] = []
    applied_files = 0

    for fg in root.findall("FILE"):
        rel = fg.get("path")
        xml_path = corpora_path / rel
        if not xml_path.exists():
            print(f"WARNING: {rel} not found under {corpora_path}; skipping its manual edits.")
            continue
        if _apply_file(xml_path, fg, changelog, pruned):
            applied_files += 1

    for rel, sid in pruned:
        print(f"WARNING: pruned no-op manual edit: {rel} / {sid}")

    if pruned:
        mec.write_manual(root, manual_file)

    print(f"apply: {len(changelog)} edit(s) across {applied_files} file(s); "
          f"{len(pruned)} no-op(s) pruned.")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Apply manual_edits.xml to corpus XML")
    parser.add_argument("--corpora_path", required=True, help="the corpus XML root")
    parser.add_argument("--manual_file", default=None,
                        help="manual edits file (default <corpus-root>/CodeAndDocs/manual_edits.xml)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if not Path(args.corpora_path).exists():
        parser.error(f"--corpora_path does not exist: {args.corpora_path}")
    manual_file = args.manual_file or mec.default_manual_file(args.corpora_path)
    return apply(args.corpora_path, manual_file)


if __name__ == "__main__":
    raise SystemExit(main())
```

> Note: `_apply_file` already implements prune + changelog accumulation; Tasks 6–7 add the tests that exercise them and the changelog file write (Task 7 wires `write_changelog`). This task's tests only cover replace/insert/append/no-op-missing-file.

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/cleaners/test_apply_manual_edits.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add QC/cleaning/apply_manual_edits.py tests/cleaners/test_apply_manual_edits.py
git commit -m "feat(manual-edits): apply upsert/insert + missing-file no-op"
```

---

## Task 6: `apply` — deletions, no-op prune + warning, chain insertion

**Files:**
- Modify: `tests/cleaners/test_apply_manual_edits.py`

> The Task 5 implementation already deletes, prunes, and chains. This task adds the proving tests and fixes anything they surface.

- [ ] **Step 1: Add the tests**

Append to `tests/cleaners/test_apply_manual_edits.py`:

```python
def _manual_ids(man_path: Path):
    root = etree.parse(str(man_path)).getroot()
    return [s.get("id") for s in root.findall(".//S")]


def test_delete_removes_sentence(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a"), _sent("S2", "b")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S2" action="delete"/></FILE></MANUAL_EDITS>')
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _ids(xml) == ["S1"]


def test_noop_upsert_is_pruned_with_warning(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "same")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1"><FORM kindOf="original">same</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert "pruned no-op" in proc.stdout.lower()
    assert _manual_ids(man) == []  # entry removed; empty file group dropped


def test_noop_delete_of_absent_id_is_pruned(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="GONE" action="delete"/></FILE></MANUAL_EDITS>')
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert "pruned no-op" in proc.stdout.lower()
    assert _manual_ids(man) == []


def test_split_chain_inserts_in_reading_order(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "a"), _sent("S2", "z")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1b" after="S1"><FORM kindOf="original">b</FORM></S>'
                '<S id="S1c" after="S1b"><FORM kindOf="original">c</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _ids(xml) == ["S1", "S1b", "S1c", "S2"]


def test_multi_file_routes_operations(tmp_path):
    a = tmp_path / "XML" / "Amis" / "a.xml"
    b = tmp_path / "XML" / "Amis" / "b.xml"
    _write(a, _doc(_sent("S1", "a")))
    _write(b, _doc(_sent("T1", "t")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS>'
                '<FILE path="Amis/a.xml"><S id="S1"><FORM kindOf="original">A!</FORM></S></FILE>'
                '<FILE path="Amis/b.xml"><S id="T1" action="delete"/></FILE>'
                "</MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _form(a, "S1") == "A!"
    assert _ids(b) == []
```

- [ ] **Step 2: Run the tests**

Run: `.venv/bin/python -m pytest tests/cleaners/test_apply_manual_edits.py -q`
Expected: PASS. Fix `apply_manual_edits.py` if any fail (do not weaken tests).

- [ ] **Step 3: Commit**

```bash
git add tests/cleaners/test_apply_manual_edits.py QC/cleaning/apply_manual_edits.py
git commit -m "test(manual-edits): apply delete/prune/chain/multi-file"
```

---

## Task 7: `apply` — changelog generation (`manual_edits.md`)

**Files:**
- Modify: `QC/cleaning/manual_edits_common.py` (add `write_changelog`)
- Modify: `QC/cleaning/apply_manual_edits.py` (call it)
- Test: `tests/cleaners/test_apply_manual_edits.py`, `tests/cleaners/test_manual_edits_common.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/cleaners/test_manual_edits_common.py`:

```python
def test_write_changelog_groups_by_file_with_before_after(tmp_path):
    entries = [
        {"file": "a.xml", "sid": "S1", "action": "changed", "before": "old", "after": "new"},
        {"file": "a.xml", "sid": "S2", "action": "added", "before": None, "after": "fresh"},
        {"file": "b.xml", "sid": "T1", "action": "deleted", "before": "gone", "after": None},
    ]
    path = tmp_path / "manual_edits.md"
    mec.write_changelog(entries, path)
    text = path.read_text(encoding="utf-8")
    assert "## a.xml" in text and "## b.xml" in text
    assert "S1" in text and "changed" in text and "old" in text and "new" in text
    assert "S2" in text and "added" in text and "fresh" in text
    assert "T1" in text and "deleted" in text and "gone" in text
```

Append to `tests/cleaners/test_apply_manual_edits.py`:

```python
def test_apply_writes_changelog_md(tmp_path):
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "build")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1"><FORM kindOf="original">manual</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    md = tmp_path / "CodeAndDocs" / "manual_edits.md"
    assert md.exists()
    text = md.read_text(encoding="utf-8")
    assert "S1" in text and "manual" in text
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py::test_write_changelog_groups_by_file_with_before_after tests/cleaners/test_apply_manual_edits.py::test_apply_writes_changelog_md -q`
Expected: FAIL — `write_changelog` missing; md not written.

- [ ] **Step 3: Add `write_changelog` to the shared module**

Append to `QC/cleaning/manual_edits_common.py`:

```python
def write_changelog(entries, path):
    """Write the human-readable per-<S> changelog grouped by file.

    entries: list of dicts with keys file, sid, action, before, after
    (before/after are rendered strings or None). Regenerated every run; an
    empty list yields a header-only file (git no-ops when unchanged).
    """
    by_file: dict[str, list] = {}
    for e in entries:
        by_file.setdefault(e["file"], []).append(e)
    lines = ["# Manual edits changelog", ""]
    for f in sorted(by_file):
        lines.append(f"## {f}")
        lines.append("")
        for e in by_file[f]:
            lines.append(f"### {e['sid']} — {e['action']}")
            if e["before"] is not None:
                lines.append(f"- before: {e['before']}")
            if e["after"] is not None:
                lines.append(f"- after:  {e['after']}")
            lines.append("")
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
```

- [ ] **Step 4: Call it from `apply`**

In `QC/cleaning/apply_manual_edits.py`, inside `apply(...)`, replace the final block (from `for rel, sid in pruned:` through `return 0`) with:

```python
    for rel, sid in pruned:
        print(f"WARNING: pruned no-op manual edit: {rel} / {sid}")

    if pruned:
        mec.write_manual(root, manual_file)

    mec.write_changelog(changelog, mec.changelog_path(manual_file))

    print(f"apply: {len(changelog)} edit(s) across {applied_files} file(s); "
          f"{len(pruned)} no-op(s) pruned.")
    return 0
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py tests/cleaners/test_apply_manual_edits.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/manual_edits_common.py QC/cleaning/apply_manual_edits.py \
        tests/cleaners/test_manual_edits_common.py tests/cleaners/test_apply_manual_edits.py
git commit -m "feat(manual-edits): emit manual_edits.md changelog from apply"
```

---

## Task 8: Round-trip + documented prune-on-double-apply behavior

**Files:**
- Modify: `tests/cleaners/test_apply_manual_edits.py`

- [ ] **Step 1: Add the tests**

Append to `tests/cleaners/test_apply_manual_edits.py`:

```python
def test_capture_then_apply_roundtrip(tmp_path):
    """End-to-end: a build, a hand edit captured, then a fresh build re-applied
    reproduces the edit. Uses both scripts."""
    capture = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "capture_manual_edits.py"

    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True,
                       capture_output=True, text=True)

    xml = tmp_path / "XML" / "a.xml"
    build = _doc(_sent("S1", "build"))
    _write(xml, build)
    git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t")
    git("add", "-A"); git("commit", "-q", "-m", "build")
    # hand-edit + capture
    _write(xml, _doc(_sent("S1", "edited")))
    proc = subprocess.run([sys.executable, str(capture), "--corpora_path", str(tmp_path / "XML")],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    # simulate a fresh rebuild (O reset to build output), then apply
    _write(xml, build)
    proc = _run_apply(tmp_path / "XML")
    assert proc.returncode == 0, proc.stderr
    assert _form(xml, "S1") == "edited"


def test_second_apply_without_rebuild_prunes_documented_behavior(tmp_path):
    """DOCUMENTED behavior (design caveat): apply expects fresh pre-manual O.
    Re-running apply on already-applied XML prunes entries as no-ops (with a
    warning), because O == R. The pipeline always rebuilds first, so this only
    bites manual misuse."""
    xml = tmp_path / "XML" / "a.xml"
    _write(xml, _doc(_sent("S1", "build")))
    man = tmp_path / "CodeAndDocs" / "manual_edits.xml"
    _write(man, '<MANUAL_EDITS><FILE path="a.xml">'
                '<S id="S1"><FORM kindOf="original">manual</FORM></S>'
                "</FILE></MANUAL_EDITS>")
    assert _run_apply(tmp_path / "XML").returncode == 0          # applies
    assert _form(xml, "S1") == "manual"
    proc = _run_apply(tmp_path / "XML")                          # second run, no rebuild
    assert proc.returncode == 0
    assert "pruned no-op" in proc.stdout.lower()
    assert _manual_ids(man) == []
```

- [ ] **Step 2: Run the tests**

Run: `.venv/bin/python -m pytest tests/cleaners/test_apply_manual_edits.py -q`
Expected: PASS.

- [ ] **Step 3: Run the whole new suite + a broad regression check**

Run: `.venv/bin/python -m pytest tests/cleaners/test_manual_edits_common.py tests/cleaners/test_apply_manual_edits.py tests/utilities/test_capture_manual_edits.py -q`
Expected: PASS (all).

Run: `.venv/bin/python -m pytest tests/cleaners -q`
Expected: PASS (no regressions in existing cleaner tests).

- [ ] **Step 4: Commit**

```bash
git add tests/cleaners/test_apply_manual_edits.py
git commit -m "test(manual-edits): capture/apply round-trip + documented prune behavior"
```

---

## Task 9: Documentation

**Files:**
- Modify: `QC/README.md`
- Modify: `CLAUDE.md`
- Modify: `.claude/skills/run-qc-pipeline/SKILL.md`

- [ ] **Step 1: Document in `QC/README.md`**

Find the pipeline-order section (the numbered list described in `CLAUDE.md` as "The typical order is: 1. validate_xml … 2. standardize --copy …"). Add a new first step and a subsection. Insert, before the existing step 1, a new step:

```markdown
0. `QC/cleaning/apply_manual_edits.py` — re-apply recorded hand edits (see "Manual edits" below). Runs first, before any other cleaning, so it works on the pre-standardization build output. No-op if the corpus has no `CodeAndDocs/manual_edits.xml`.
```

Then add this subsection (place it after the pipeline list):

```markdown
### Manual edits (reproducible hand edits)

Some corrections (often surfaced by `validate_text`/`validate_glosses`) can only be made by hand. To keep them reproducible across rebuilds, record them instead of editing the published XML ad hoc:

1. Hand-edit the `<S>` blocks in the corpus XML directly.
2. Run `python QC/utilities/capture_manual_edits.py --corpora_path <XML-dir>`. It diffs the working tree against the git baseline (`--baseline-ref`, default `HEAD`) and records each changed/added/deleted `<S>` into `<corpus-root>/CodeAndDocs/manual_edits.xml` (standard tier + PHON stripped; new sentences get an `after` placement hint).
3. Commit `manual_edits.xml`.
4. On every rebuild, `python QC/cleaning/apply_manual_edits.py --corpora_path <XML-dir>` re-applies them (first in the cleaning pipeline), prunes entries that have become no-ops (printing a `pruned no-op` warning for each), and regenerates the readable `CodeAndDocs/manual_edits.md` changelog.

Splitting a multi-option sentence: edit the original `<S>` to a single variant and add new `<S>` (with fresh ids) for the others; `capture`/`apply` keep them adjacent via the `after` hint.

**Discipline:** `apply` expects `O` to be fresh pre-manual build output. Run it on a freshly rebuilt tree; re-running it on already-applied XML prunes entries as no-ops (recoverable via git, and announced by warnings).
```

- [ ] **Step 2: Mention in `CLAUDE.md`**

In `CLAUDE.md`, in the "QC script conventions" or cleaning area, add a short bullet:

```markdown
- **Reproducible hand edits.** `QC/utilities/capture_manual_edits.py` records hand edits to a corpus's XML (diffed against git) into `<corpus>/CodeAndDocs/manual_edits.xml`; `QC/cleaning/apply_manual_edits.py` re-applies them first in the cleaning pipeline, prunes no-ops (with a warning), and writes a `manual_edits.md` changelog. Shared logic lives in `QC/cleaning/manual_edits_common.py`. See `claudeplans/2026-06-15-manual-edits-reproducibility-design.md`.
```

- [ ] **Step 3: Add Phase 0 to the run-qc-pipeline skill**

In `.claude/skills/run-qc-pipeline/SKILL.md`, add a phase before "Phase 1: Clean":

```markdown
### Phase 0: Apply manual edits

Re-apply any recorded hand edits before cleaning, so later phases see them. No-op (and prints so) if the corpus has no `CodeAndDocs/manual_edits.xml`.

`.venv/bin/python3 <formosanbank_path>/QC/cleaning/apply_manual_edits.py --corpora_path <xml_path> 2>&1 | tee <output_dir>/00_apply_manual_edits.log`

This phase must run on freshly built (pre-manual) XML. Any `pruned no-op` warnings in the log mean an entry was dropped — surface them in the summary.
```

- [ ] **Step 4: Verify docs reference real paths**

Run: `.venv/bin/python -m pytest tests/cleaners tests/utilities/test_capture_manual_edits.py -q`
Expected: PASS (sanity re-run; docs changes don't affect tests but confirm nothing broke).

- [ ] **Step 5: Commit**

```bash
git add QC/README.md CLAUDE.md .claude/skills/run-qc-pipeline/SKILL.md
git commit -m "docs(manual-edits): document capture/apply in README, CLAUDE.md, skill"
```

---

## Self-review checklist (run after implementing)

- [ ] Every spec section maps to a task: capture (T3–4), apply incl. prune/anchor/delete (T5–6), changelog (T7), strip/canonical data model (T1), multi-file `<FILE>` grouping (T2, T6), `after` anchor + chains (T4, T6), no-git error + new-file skip (T4), missing-file no-op (T5), round-trip + documented caveat (T8), docs (T9).
- [ ] No placeholders; every code step has complete code.
- [ ] Names consistent across tasks: `strip_s`, `canonical_s`, `render_s`, `default_manual_file`, `changelog_path`, `new_manual_root`, `load_manual`, `find_file_group`, `get_or_create_file_group`, `upsert_record`, `remove_record`, `write_manual`, `git_root`, `git_show`, `write_changelog`.
- [ ] `--baseline-ref` (capture) and `--manual_file` (both) defaults match the design.
- [ ] `apply` strips `after`/`action` before writing `<S>` into the live corpus XML (via `strip_s`).
```
