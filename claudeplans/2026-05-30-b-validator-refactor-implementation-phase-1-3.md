# Validator refactor implementation plan — Phases 1–3

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal.** Replace [QC/validation/validate_xml.py](../../QC/validation/validate_xml.py) with a modular runner + scaffolding + one worked rule, then add the CLI surface (`--no-exit-on-hard`, `--soft-csv`) and the SOFT-CSV writer infrastructure. All currently-passing tests continue to pass; one new xfail (V017) flips to plain-pass as proof the new flow works end-to-end.

**Architecture.** Thin runner (`validate_xml.py` ~80 lines) walks the corpus once, parses each `.xml` tree, applies rules from `rules/{hard,soft,warn}.py`, emits HARD/WARN findings to stderr and SOFT findings to a per-run CSV. Exit code is 1 on any HARD finding (gated by `--no-exit-on-hard` for backward compat). Rule functions have a uniform `rule(tree, path, index) -> list[Finding]` signature; `index` is `None` for pass 1, populated `CorpusIndex` for pass 2 (cross-file rules — Phase 6, not in this plan).

**Tech Stack.** Python 3.13, `lxml.etree`, `pytest 8.3.4`, the existing XSD/DTD toolchain at [QC/validation/xml_template.dtd](../../QC/validation/xml_template.dtd).

**Spec.** Design doc: [.claude/plans/2026-05-30-b-validator-refactor-design.md](2026-05-30-b-validator-refactor-design.md). Rule catalogue: [.claude/plans/2026-05-29-xml-validation-design.md](2026-05-29-xml-validation-design.md). The xfail tests at [tests/validators/test_validate_xml.py](../../tests/validators/test_validate_xml.py) are the per-rule acceptance criteria.

**Out of scope for this plan.** Phases 4–7: DTD tightening, the ~25 Python HARD rule migrations, cross-file rules (V081/V082/V083), and SOFT rules (V010/V014). Each gets its own follow-up plan once Phase 1–3 lands and is reviewed.

---

## File structure

**Created** in this plan:

| File | Responsibility |
|---|---|
| `QC/validation/_finding.py` | `Finding` frozen dataclass, `Severity` enum, `write_soft_csv()` helper. |
| `QC/validation/_corpus_index.py` | `CorpusIndex` frozen dataclass: `ids: dict`, `langs: dict`. Builders for each. |
| `QC/validation/rules/__init__.py` | Empty package marker. |
| `QC/validation/rules/hard.py` | HARD rules. Each exports as a function; module exports `RULES: list[Callable]` and `CROSS_FILE_RULES: list[Callable]`. |
| `QC/validation/rules/soft.py` | SOFT rules. Same export shape. Empty for this plan. |
| `QC/validation/rules/warn.py` | WARN rules. Same export shape. Empty for this plan. |
| `tests/validators/test_finding.py` | Unit tests for `Finding`, `Severity`, `write_soft_csv()`. |
| `tests/validators/test_corpus_index.py` | Unit tests for `CorpusIndex`. |
| `tests/validators/test_runner.py` | Unit tests for the runner's file walking, tree caching, and rule dispatch. |

**Modified** in this plan:

| File | Change |
|---|---|
| `QC/validation/validate_xml.py` | Rewritten as a thin runner. Existing behavior (XSD validation, audio attribute check, language code check) migrated into the new structure as HARD rules. |
| `tests/validators/test_validate_xml.py` | Remove `@pytest.mark.xfail` from `test_V017_empty_FORM_negative` (Task 8). No other test changes. |

**Out of touch:** every other file in the repo. Specifically, the cleaner tests, the utilities tests, the design docs, and the rest of `QC/validation/`.

---

## Phase 1 — Scaffolding (Tasks 1–7)

### Task 1: Add `Finding` and `Severity` to a new `_finding.py`

**Files:**
- Create: `QC/validation/_finding.py`
- Create: `tests/validators/test_finding.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/validators/test_finding.py`:

```python
"""Unit tests for Finding and Severity."""
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from QC.validation._finding import Finding, Severity


def test_severity_values():
    assert Severity.HARD.value == "HARD"
    assert Severity.SOFT.value == "SOFT"
    assert Severity.WARN.value == "WARN"


def test_finding_minimal_construction():
    f = Finding(
        rule_id="V001",
        severity=Severity.HARD,
        message="root tag is 'NOT_TEXT', expected 'TEXT'",
        path=Path("/tmp/foo.xml"),
    )
    assert f.rule_id == "V001"
    assert f.severity is Severity.HARD
    assert f.location is None
    assert f.count == 1
    assert f.language is None
    assert f.character is None


def test_finding_with_location():
    f = Finding(
        rule_id="V015",
        severity=Severity.HARD,
        message="duplicate kindOf='original'",
        path=Path("/tmp/foo.xml"),
        location="S=ami_chapter01_S0042",
    )
    assert f.location == "S=ami_chapter01_S0042"


def test_finding_soft_with_aggregation():
    f = Finding(
        rule_id="V014",
        severity=Severity.SOFT,
        message="missing standard tier",
        path=Path("/tmp/foo.xml"),
        count=42,
        language="ami",
        character="",
    )
    assert f.count == 42
    assert f.language == "ami"
    assert f.character == ""


def test_finding_is_frozen():
    f = Finding(
        rule_id="V001",
        severity=Severity.HARD,
        message="msg",
        path=Path("/tmp/foo.xml"),
    )
    with pytest.raises(FrozenInstanceError):
        f.rule_id = "V002"


def test_finding_equality():
    a = Finding(rule_id="V001", severity=Severity.HARD, message="m", path=Path("/x.xml"))
    b = Finding(rule_id="V001", severity=Severity.HARD, message="m", path=Path("/x.xml"))
    assert a == b
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/validators/test_finding.py -v`
Expected: ImportError / ModuleNotFoundError on `QC.validation._finding`.

- [ ] **Step 3: Implement `_finding.py`**

Create `QC/validation/_finding.py`:

```python
"""Finding dataclass and Severity enum for the validator.

A Finding is the unit of validator output. HARD and WARN rules emit
one Finding per offending element, populating `location`. SOFT rules
pre-aggregate per (rule, file, language, character) and populate
`count`/`language`/`character`.
"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    WARN = "WARN"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: Path
    location: str | None = None
    count: int = 1
    language: str | None = None
    character: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/validators/test_finding.py -v`
Expected: 6 passed.

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: 66+6=72 passed, 42 xfailed (or however many xfails there are — the count should not change).

- [ ] **Step 6: Commit**

```bash
git add QC/validation/_finding.py tests/validators/test_finding.py
git commit -m "$(cat <<'EOF'
Add Finding dataclass and Severity enum for validator refactor

Foundational types for the modular validate_xml.py runner. A Finding
carries rule_id, severity, message, and source path; HARD/WARN rules
populate location for per-element findings; SOFT rules populate
count/language/character for pre-aggregated drift data.

Frozen dataclass; one type for all severities (flat with optional
fields beats a hierarchy: simpler imports, cheap with frozen=True).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: Add `CorpusIndex` to a new `_corpus_index.py`

**Files:**
- Create: `QC/validation/_corpus_index.py`
- Create: `tests/validators/test_corpus_index.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/validators/test_corpus_index.py`:

```python
"""Unit tests for CorpusIndex."""
from pathlib import Path

from QC.validation._corpus_index import CorpusIndex


def test_empty_index():
    idx = CorpusIndex(ids={}, langs={})
    assert idx.ids == {}
    assert idx.langs == {}


def test_index_with_one_id_and_lang():
    p = Path("/tmp/foo.xml")
    idx = CorpusIndex(
        ids={"ami_chapter01": [(p, "TEXT")]},
        langs={p: "ami"},
    )
    assert idx.ids["ami_chapter01"] == [(p, "TEXT")]
    assert idx.langs[p] == "ami"


def test_index_with_id_collision_across_files():
    p1 = Path("/tmp/foo.xml")
    p2 = Path("/tmp/bar.xml")
    idx = CorpusIndex(
        ids={"shared_id": [(p1, "TEXT"), (p2, "TEXT")]},
        langs={p1: "ami", p2: "pwn"},
    )
    assert len(idx.ids["shared_id"]) == 2
    assert idx.langs[p1] == "ami"
    assert idx.langs[p2] == "pwn"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/validators/test_corpus_index.py -v`
Expected: ImportError on `QC.validation._corpus_index`.

- [ ] **Step 3: Implement `_corpus_index.py`**

Create `QC/validation/_corpus_index.py`:

```python
"""CorpusIndex: the cross-file accumulator built in pass 1.

The validator runner makes one parse pass over every file in the
target, collecting per-file structured data into a CorpusIndex.
Pass 2 then applies cross-file rules (V081 id uniqueness, …) with
the populated index as their third argument.

Fields:
  ids: TEXT/@id -> list of (path, location-str). location-str is the
       in-file pinpoint (currently always "TEXT" for the root, but
       reserved for future per-W/per-M ids if those ever participate
       in cross-file uniqueness).
  langs: path -> resolved xml:lang for that file's <TEXT> root.
"""
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CorpusIndex:
    ids: dict[str, list[tuple[Path, str]]]
    langs: dict[Path, str]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/validators/test_corpus_index.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: 75 passed, 42 xfailed.

- [ ] **Step 6: Commit**

```bash
git add QC/validation/_corpus_index.py tests/validators/test_corpus_index.py
git commit -m "$(cat <<'EOF'
Add CorpusIndex for cross-file rule pass-2 plumbing

The validator runner builds a CorpusIndex during pass 1 (walking and
parsing every file once). Pass 2 applies cross-file rules with the
populated index as a third argument. Only V081 needs this today,
but the infrastructure goes in now so cross-file rules don't
require structural changes when they land.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: Add `write_soft_csv()` to `_finding.py`

**Files:**
- Modify: `QC/validation/_finding.py`
- Modify: `tests/validators/test_finding.py`

- [ ] **Step 1: Write the failing tests**

Append to `tests/validators/test_finding.py`:

```python
import csv


def test_write_soft_csv_empty(tmp_path):
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "soft.csv"
    write_soft_csv(out, [])
    # Even with no findings, the file exists with just the header.
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    assert rows == [["file", "rule_id", "language", "character", "count"]]


def test_write_soft_csv_one_finding(tmp_path):
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "soft.csv"
    findings = [
        Finding(
            rule_id="V014",
            severity=Severity.SOFT,
            message="missing standard tier",
            path=Path("/abs/path/to/ami_chapter01.xml"),
            count=3,
            language="ami",
            character="",
        ),
    ]
    write_soft_csv(out, findings)
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    assert rows == [
        ["file", "rule_id", "language", "character", "count"],
        ["/abs/path/to/ami_chapter01.xml", "V014", "ami", "", "3"],
    ]


def test_write_soft_csv_skips_non_soft(tmp_path):
    """write_soft_csv is the SOFT writer; HARD/WARN findings are not
    its concern even if accidentally passed in."""
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "soft.csv"
    findings = [
        Finding(rule_id="V001", severity=Severity.HARD, message="m", path=Path("/x.xml")),
        Finding(rule_id="V014", severity=Severity.SOFT, message="m",
                path=Path("/y.xml"), count=2, language="ami", character=""),
        Finding(rule_id="V088", severity=Severity.WARN, message="m", path=Path("/z.xml")),
    ]
    write_soft_csv(out, findings)
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    # Header + one SOFT row only.
    assert len(rows) == 2
    assert rows[1][1] == "V014"


def test_write_soft_csv_creates_parent_dir(tmp_path):
    """If the requested output path's parent does not exist, it is created."""
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "logs" / "subdir" / "soft.csv"
    write_soft_csv(out, [])
    assert out.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/validators/test_finding.py -v`
Expected: 4 new tests fail (ImportError on `write_soft_csv`); the original 6 still pass.

- [ ] **Step 3: Implement `write_soft_csv`**

Append to `QC/validation/_finding.py`:

```python
import csv
from collections.abc import Iterable


SOFT_CSV_COLUMNS = ["file", "rule_id", "language", "character", "count"]


def write_soft_csv(path: Path, findings: Iterable[Finding]) -> None:
    """Write all SOFT findings in `findings` to a CSV at `path`.

    The CSV is overwritten on each call (not appended). The parent
    directory is created if it does not exist. Non-SOFT findings in
    `findings` are silently skipped: the runner separates output
    channels by severity, but if a SOFT writer is ever invoked with a
    mixed list, only SOFT rows belong in the SOFT CSV.

    Column shape per the validator design doc:
      file: absolute path to the XML file the finding came from.
      rule_id: uppercase rule identifier (e.g., "V014").
      language: resolved xml:lang (ISO 639-3) or empty.
      character: the offending character, or empty if not applicable.
      count: occurrence count for this (rule, file, language, character).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SOFT_CSV_COLUMNS)
        for finding in findings:
            if finding.severity is not Severity.SOFT:
                continue
            writer.writerow([
                str(finding.path),
                finding.rule_id,
                finding.language or "",
                finding.character or "",
                str(finding.count),
            ])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/pytest tests/validators/test_finding.py -v`
Expected: 10 passed.

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: 79 passed, 42 xfailed.

- [ ] **Step 6: Commit**

```bash
git add QC/validation/_finding.py tests/validators/test_finding.py
git commit -m "$(cat <<'EOF'
Add write_soft_csv() for the validator's per-run SOFT output

Writes Finding objects to a CSV at the path given, with the column
schema from the design doc (file, rule_id, language, character,
count). Overwrites per run; creates parent dirs if needed. Skips
non-SOFT findings even if passed in (defensive: HARD/WARN belong on
stderr, not in this CSV).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Empty `rules/` package + per-module RULES lists

**Files:**
- Create: `QC/validation/rules/__init__.py`
- Create: `QC/validation/rules/hard.py`
- Create: `QC/validation/rules/soft.py`
- Create: `QC/validation/rules/warn.py`

- [ ] **Step 1: Create the empty package**

Create `QC/validation/rules/__init__.py` (empty file).

- [ ] **Step 2: Create empty rule modules**

Create `QC/validation/rules/hard.py`:

```python
"""HARD-severity rules: violations cause the validator to exit nonzero.

Each rule is a function with signature:
    rule(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]

Rules that do NOT consult `index` go in RULES; the runner calls them
in pass 1. Rules that DO consult `index` go in CROSS_FILE_RULES; the
runner calls them in pass 2 after the index is built.
"""
from QC.validation._finding import Finding

RULES: list = []
CROSS_FILE_RULES: list = []
```

Create `QC/validation/rules/soft.py`:

```python
"""SOFT-severity rules: violations populate the SOFT CSV but do not
affect exit code.

Each rule pre-aggregates per (rule_id, file, language, character).
Returning thousands of un-aggregated Findings per file would flood
the CSV writer.

Signature: same as HARD rules.
"""
from QC.validation._finding import Finding

RULES: list = []
CROSS_FILE_RULES: list = []
```

Create `QC/validation/rules/warn.py`:

```python
"""WARN-severity rules: violations log to stderr but do not affect
exit code.

Used for advisory checks; no rules populate this module yet.
"""
from QC.validation._finding import Finding

RULES: list = []
CROSS_FILE_RULES: list = []
```

- [ ] **Step 3: Verify imports work**

Run: `.venv/bin/python -c "from QC.validation.rules import hard, soft, warn; print(hard.RULES, soft.RULES, warn.RULES)"`
Expected: `[] [] []`.

- [ ] **Step 4: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: 79 passed, 42 xfailed.

- [ ] **Step 5: Commit**

```bash
git add QC/validation/rules/
git commit -m "$(cat <<'EOF'
Add empty rules/ package for the validator's modular rule layout

Per-severity modules (hard.py, soft.py, warn.py) each export RULES
(per-file rules, applied in pass 1) and CROSS_FILE_RULES (rules that
consult the CorpusIndex, applied in pass 2). Both lists start empty;
rule additions in subsequent commits append to them.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 5: Runner skeleton — file walk, tree caching, dispatch (no rules yet)

This task replaces the body of `QC/validation/validate_xml.py` with a runner that walks files, parses each tree once, calls all rules in `rules.{hard,soft,warn}.RULES` (currently empty), and emits findings. Existing CLI surface is preserved (the `by_path`/`by_corpus`/`by_language` modes).

**Files:**
- Modify: `QC/validation/validate_xml.py` (full rewrite, ~120 lines)
- Create: `tests/validators/test_runner.py`

- [ ] **Step 1: Read the existing `validate_xml.py` to capture behaviors we must preserve**

Run: `.venv/bin/python QC/validation/validate_xml.py --help`
Expected: usage text showing `by_path`, `by_corpus`, `by_language` modes with their flags. Capture this surface so the rewrite preserves it.

Read the existing `QC/validation/validate_xml.py` end-to-end. Note: (a) the file-walk via `get_files()`, (b) the XSD validation via `validate_xml_against_xsd()`, (c) `validate_audio_attr()` and `validate_lang_code()` per-file checks, (d) the end-of-run summary format (`Total issues found: N`, `Files with issues:`).

The new runner must keep the existing CLI surface and the "Total issues found: 0" / "no issues found" / "Files with issues" summary tokens because [tests/validators/test_validate_xml.py](../../tests/validators/test_validate_xml.py)'s `_is_clean` and `_has_finding` helpers match on those exact tokens.

- [ ] **Step 2: Write the failing runner tests**

Create `tests/validators/test_runner.py`:

```python
"""Unit tests for the validate_xml runner: file walking, tree caching,
dispatch. These tests import from QC.validation directly; they do not
subprocess. End-to-end behavior is covered by the existing
tests/validators/test_validate_xml.py against the CLI surface.
"""
from pathlib import Path

import pytest
from lxml import etree

from QC.validation._finding import Finding, Severity
from QC.validation.validate_xml import (
    discover_xml_files,
    parse_tree,
    run_per_file_rules,
)


VALID_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<TEXT id="t1" citation="c" BibTeX_citation="@b{x}" copyright="cc" xml:lang="ami">
  <S id="S1">
    <FORM kindOf="original">Halo.</FORM>
  </S>
</TEXT>
"""


def test_discover_xml_files_returns_only_xml(tmp_path):
    (tmp_path / "XML").mkdir()
    (tmp_path / "XML" / "a.xml").write_bytes(VALID_XML)
    (tmp_path / "XML" / "b.xml").write_bytes(VALID_XML)
    (tmp_path / "XML" / "note.txt").write_text("not xml")
    (tmp_path / "README.md").write_text("not xml")

    files = sorted(discover_xml_files(tmp_path))
    assert [p.name for p in files] == ["a.xml", "b.xml"]


def test_discover_xml_files_recurses(tmp_path):
    (tmp_path / "XML" / "Amis").mkdir(parents=True)
    (tmp_path / "XML" / "Amis" / "x.xml").write_bytes(VALID_XML)
    files = sorted(discover_xml_files(tmp_path))
    assert [p.name for p in files] == ["x.xml"]


def test_parse_tree_returns_etree(tmp_path):
    p = tmp_path / "x.xml"
    p.write_bytes(VALID_XML)
    tree = parse_tree(p)
    assert tree.getroot().tag == "TEXT"


def test_run_per_file_rules_invokes_each_rule(tmp_path):
    p = tmp_path / "x.xml"
    p.write_bytes(VALID_XML)
    tree = parse_tree(p)

    calls = []
    def rule_a(t, path, index):
        calls.append(("a", path))
        return []
    def rule_b(t, path, index):
        calls.append(("b", path))
        return [Finding(rule_id="V999", severity=Severity.HARD,
                        message="test", path=path)]

    findings = run_per_file_rules(tree, p, [rule_a, rule_b], index=None)
    assert [c[0] for c in calls] == ["a", "b"]
    assert len(findings) == 1
    assert findings[0].rule_id == "V999"
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/validators/test_runner.py -v`
Expected: ImportError on `discover_xml_files` / `parse_tree` / `run_per_file_rules`.

- [ ] **Step 4: Rewrite `QC/validation/validate_xml.py`**

Replace the entire contents of `QC/validation/validate_xml.py` with:

```python
"""validate_xml.py — modular FormosanBank XML validator.

Walks a target (by path, by corpus, or by language), parses each .xml
file once with lxml, applies the rules registered under
QC/validation/rules/{hard,soft,warn}.py, and emits HARD/WARN findings
to stderr and SOFT findings to a per-run CSV.

CLI shape (preserved from prior version):
    validate_xml.py by_path     --path <file-or-dir>
    validate_xml.py by_corpus   --corpus <name> --corpora_path <path>
    validate_xml.py by_language --language <name> --corpora_path <path>

Phase 1 (this commit): runner scaffolding only. No rules registered;
all input validates as clean. Subsequent commits add rules and the
CLI flags for the new behavior (--no-exit-on-hard, --soft-csv).
"""
import argparse
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity
from QC.validation.rules import hard as hard_rules
from QC.validation.rules import soft as soft_rules
from QC.validation.rules import warn as warn_rules


Rule = Callable[[etree._ElementTree, Path, CorpusIndex | None], list[Finding]]


def discover_xml_files(root: Path) -> list[Path]:
    """Return every .xml file under root, recursively.

    Used for by_path, by_corpus, by_language modes uniformly. The
    caller assembles the right root (a single dir, a single file, or
    a filtered list).
    """
    if root.is_file():
        return [root] if root.suffix == ".xml" else []
    return sorted(p for p in root.rglob("*.xml"))


def parse_tree(path: Path) -> etree._ElementTree:
    """Parse a single XML file into an lxml ElementTree.

    No special error handling here: a parse failure raises and the
    runner reports it. Phase 4's DTD validation runs against the same
    parse output.
    """
    return etree.parse(str(path))


def run_per_file_rules(
    tree: etree._ElementTree,
    path: Path,
    rules: Iterable[Rule],
    index: CorpusIndex | None,
) -> list[Finding]:
    """Call each rule on this file's tree, return concatenated findings."""
    out: list[Finding] = []
    for rule in rules:
        out.extend(rule(tree, path, index))
    return out


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FormosanBank XML validator.")
    sub = parser.add_subparsers(dest="search_by", required=True)

    by_path = sub.add_parser("by_path")
    by_path.add_argument("--path", required=True, type=Path)

    by_corpus = sub.add_parser("by_corpus")
    by_corpus.add_argument("--corpus", required=True)
    by_corpus.add_argument("--corpora_path", required=True, type=Path)

    by_language = sub.add_parser("by_language")
    by_language.add_argument("--language", required=True)
    by_language.add_argument("--corpora_path", required=True, type=Path)

    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--log_dir", type=Path, default=None)
    return parser


def _resolve_target_files(args: argparse.Namespace) -> list[Path]:
    if args.search_by == "by_path":
        return discover_xml_files(args.path)
    if args.search_by == "by_corpus":
        return discover_xml_files(args.corpora_path / args.corpus)
    if args.search_by == "by_language":
        # Filter by xml:lang at parse time — fast scan of the root attribute.
        files = []
        for path in discover_xml_files(args.corpora_path):
            try:
                tree = parse_tree(path)
                lang_attr = "{http://www.w3.org/XML/1998/namespace}lang"
                if tree.getroot().get(lang_attr) == args.language:
                    files.append(path)
            except etree.XMLSyntaxError:
                continue
        return files
    raise AssertionError(f"unknown search_by mode: {args.search_by}")


def _print_summary(findings: list[Finding]) -> None:
    """Emit the summary tokens that test helpers match on.

    The token strings are preserved from the legacy validator because
    tests/validators/test_validate_xml.py asserts on
    `_is_clean` (looks for "total issues found: 0" + "no issues found")
    and `_has_finding` (looks for "files with issues" et al).
    """
    n = sum(1 for f in findings if f.severity is Severity.HARD)
    print(f"Total issues found: {n}", file=sys.stderr)
    if n == 0:
        print("No issues found.", file=sys.stderr)
        return
    paths_with_issues = sorted({str(f.path) for f in findings
                                if f.severity is Severity.HARD})
    print("Files with issues:", file=sys.stderr)
    for p in paths_with_issues:
        print(f"  {p}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    targets = _resolve_target_files(args)

    all_findings: list[Finding] = []
    all_rules = (
        hard_rules.RULES + soft_rules.RULES + warn_rules.RULES
    )

    for path in targets:
        try:
            tree = parse_tree(path)
        except etree.XMLSyntaxError as e:
            # Parse failure is a HARD finding. Match the legacy message
            # shape so tests/validators/test_validate_xml.py's
            # NEGATIVE_MARKERS ("error", "invalid", ...) match.
            all_findings.append(Finding(
                rule_id="V000",
                severity=Severity.HARD,
                message=f"XML parse error: {e}",
                path=path,
            ))
            continue
        all_findings.extend(run_per_file_rules(tree, path, all_rules, index=None))

    _print_summary(all_findings)
    return 0  # exit-1-on-HARD lands in Task 9.


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run runner unit tests to verify they pass**

Run: `.venv/bin/pytest tests/validators/test_runner.py -v`
Expected: 4 passed.

- [ ] **Step 6: Run full suite to verify legacy behavior preserved**

Run: `.venv/bin/pytest`
Expected: All previously passing tests still pass; the count goes up by 4 (the new test_runner.py tests).

If any test in `tests/validators/test_validate_xml.py` fails: the most likely cause is that the summary token shape ("Total issues found: 0", "No issues found.", "Files with issues:") drifted. Diff the runner's `_print_summary` against the legacy `validate_xml.py`'s summary printing and fix.

- [ ] **Step 7: Commit**

```bash
git add QC/validation/validate_xml.py tests/validators/test_runner.py
git commit -m "$(cat <<'EOF'
Replace validate_xml.py with modular runner skeleton

Rewrites validate_xml.py as a thin runner: walks files, parses each
tree once, applies rules from rules/{hard,soft,warn}.RULES (all
empty in this commit), and emits the legacy summary tokens. CLI
surface preserved: by_path / by_corpus / by_language modes plus
--verbose / --log_dir continue to work.

The runner returns exit 0 for now; --no-exit-on-hard + default
exit-1-on-HARD land in Task 9. SOFT-CSV output lands in Task 10.
Cross-file rules (pass-2 dispatch) land in Phase 6.

No behavior change visible to existing tests: with zero rules
registered, every input validates as clean ("Total issues found: 0"
+ "No issues found."). Existing XSD validation and the legacy audio
attribute / lang code checks migrate to rules/hard.py in Tasks 6-7.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

**Note on expected suite state after this commit:** the legacy validator did XSD validation, which Tasks 5–7 have NOT yet migrated. So the previously-passing negative tests like `test_V001_root_must_be_TEXT_negative` (which depend on the validator catching a non-TEXT root) will START FAILING here. This is expected and gets resolved in Tasks 6–7 when the existing checks migrate in. The full suite will return to all-green at the end of Task 7.

Verify the failure pattern: run `.venv/bin/pytest tests/validators/test_validate_xml.py` and confirm the failures are the negative tests for V001/V003/V004/V005 (XSD-enforced) and any tests depending on audio attribute or lang code checks. If failures extend beyond that set, something else broke and needs investigation before continuing.

---

### Task 6: Migrate XSD validation into a HARD rule

The legacy validator's XSD/DTD validation against [QC/validation/xml_template.dtd](../../QC/validation/xml_template.dtd) is the source of structural enforcement for V001–V006. We migrate it into a single HARD rule that runs on every file.

**Files:**
- Modify: `QC/validation/rules/hard.py`
- Create: helper inside `_finding.py` if needed (no — keep the rule self-contained).

- [ ] **Step 1: Identify the existing XSD/DTD logic in legacy code**

Run: `git show HEAD~5:QC/validation/validate_xml.py | grep -n "validate_xml_against_xsd\|DTD\|template" | head -20` (the commit hash will vary; the point is to retrieve the pre-rewrite logic). Capture the existing approach: it constructs a DTD validator from `QC/validation/xml_template.dtd` and calls `dtd.validate(tree)`, collecting `dtd.error_log` on failure.

- [ ] **Step 2: Write the rule**

Add to `QC/validation/rules/hard.py`:

```python
import os
from pathlib import Path

from lxml import etree

from QC.validation._corpus_index import CorpusIndex
from QC.validation._finding import Finding, Severity


_DTD_PATH = Path(__file__).resolve().parents[1] / "xml_template.dtd"
_DTD = etree.DTD(open(_DTD_PATH))  # parsed once at import time


def v000_dtd_validation(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Validate the parsed tree against the canonical DTD.

    DTD violations cover the bulk of V001 (root must be TEXT), V003
    (S under TEXT), V004 (W under S), V005 (M under W), V006 (FORM/
    TRANSL/AUDIO under their declared parents), V011 (W must have
    FORM), V012 (M must have FORM), V016 (FORM must have content
    where DTD specifies), V030–V038 (required attributes the DTD
    declares as #REQUIRED), V050 (AUDIO must have @file once DTD
    promotes it), and any other structural invariants the DTD
    enforces. Phase 4 (DTD tightening) extends this rule's reach by
    adding constraints to xml_template.dtd.
    """
    is_valid = _DTD.validate(tree)
    if is_valid:
        return []
    findings: list[Finding] = []
    for entry in _DTD.error_log:
        findings.append(Finding(
            rule_id="V000",
            severity=Severity.HARD,
            message=f"DTD violation: {entry.message}",
            path=path,
            location=f"line={entry.line}",
        ))
    return findings


RULES.append(v000_dtd_validation)
```

The `RULES: list = []` at the top of `hard.py` (from Task 4) gets populated by these `RULES.append(...)` calls as each rule is added. Don't redeclare or reset it.

- [ ] **Step 3: Run the validator end-to-end against an XSD-violating fixture**

Run: `.venv/bin/pytest tests/validators/test_validate_xml.py::test_V001_root_must_be_TEXT_negative -v`
Expected: PASS (the DTD catches the root tag mismatch via the migrated rule).

If the test still fails, the most likely cause is that the DTD rejects but the message format doesn't match `NEGATIVE_MARKERS` (`"error"`, `"violation"`, etc.). The rule message starts with `"DTD violation:"` which contains `"violation"` — that should match. Verify by adding `-s` and inspecting the actual stderr.

- [ ] **Step 4: Run the full validator suite**

Run: `.venv/bin/pytest tests/validators/test_validate_xml.py -v`
Expected: all currently-passing tests pass; the XSD-dependent ones (V001, V003, V004, V005) pass; the xfail tests stay xfail.

If a previously-passing test fails: the most likely cause is that the rule emits DTD findings for the *valid* fixtures (e.g., `valid_minimal.xml`). Inspect the DTD path resolution — `_DTD_PATH` should resolve to the existing `xml_template.dtd`. Print `_DTD_PATH` if needed.

- [ ] **Step 5: Run full suite to verify no regressions outside validate_xml tests**

Run: `.venv/bin/pytest`
Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add QC/validation/rules/hard.py
git commit -m "$(cat <<'EOF'
Migrate XSD/DTD validation into rules/hard.py as v000

The legacy validator's DTD validation step lands as the first rule
in the new modular structure. The DTD is parsed once at module
import time and reused across files. Violations become HARD findings
with location=line=N for easy in-file pinpointing.

This rule covers the bulk of V001-V006 (structural rules), V011/V012
(required FORM under W/M), V030-V038 (required attributes), and any
other constraint the DTD encodes. Phase 4 (DTD tightening) extends
this rule's reach by adding constraints to xml_template.dtd; no
parallel Python rule is needed when DTD can express the check.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: Migrate legacy audio_attr and lang_code checks into HARD rules

The legacy validator has two Python checks beyond XSD: `validate_audio_attr` (audio `start`/`end` attribute presence and ordering) and `validate_lang_code` (TEXT-level `xml:lang` must be a valid ISO 639-3 code). Both become HARD rules.

**Files:**
- Modify: `QC/validation/rules/hard.py`

- [ ] **Step 1: Read the legacy check logic**

Run: `git show HEAD~6:QC/validation/validate_xml.py | grep -A 30 "def validate_audio_attr\|def validate_lang_code"` (commit hash will vary; goal is to capture the existing audio attribute and language code check logic).

The legacy `validate_audio_attr` (lines ~135–163 of the pre-rewrite file) iterates all `<AUDIO>` elements and checks: `start` and `end` attributes are present, and `start < end`. It does NOT currently distinguish `audio="diarized"` vs `audio="segmented"` semantics correctly — there's a known bug. **Preserve the bug for now**; fixing it lives in Phase 5 with the V050–V056 rule migrations.

The legacy `validate_lang_code` (lines ~165–183) reads `QC/validation/iso-639-3.txt`, parses it into a set, and rejects TEXT-level `xml:lang` values not in the set.

- [ ] **Step 2: Add audio_attr rule**

Append to `QC/validation/rules/hard.py`:

```python
def v050_audio_attr_present(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """Each <AUDIO> element must have start and end attributes, and
    start must be < end.

    Preserves the legacy validate_audio_attr behavior. Note: the
    legacy code has a known bug around audio="diarized" vs
    audio="segmented" semantics. Phase 5's V050-V056 rule migrations
    will refactor this rule to fix the bug; for now we keep the bug
    so the existing tests continue to pass.
    """
    findings: list[Finding] = []
    for audio in tree.iter("AUDIO"):
        start = audio.get("start")
        end = audio.get("end")
        s_id = audio.getparent().get("id") if audio.getparent() is not None else None
        location = f"S={s_id}" if s_id else "AUDIO"
        if start is None or end is None:
            findings.append(Finding(
                rule_id="V050",
                severity=Severity.HARD,
                message="AUDIO missing required start or end attribute",
                path=path,
                location=location,
            ))
            continue
        try:
            if float(start) >= float(end):
                findings.append(Finding(
                    rule_id="V051",
                    severity=Severity.HARD,
                    message=f"AUDIO start ({start}) >= end ({end})",
                    path=path,
                    location=location,
                ))
        except ValueError:
            findings.append(Finding(
                rule_id="V050",
                severity=Severity.HARD,
                message=f"AUDIO start/end not numeric (start={start!r}, end={end!r})",
                path=path,
                location=location,
            ))
    return findings


RULES.append(v050_audio_attr_present)
```

- [ ] **Step 3: Add lang_code rule**

Continue appending to `QC/validation/rules/hard.py`:

```python
def _load_iso_639_3() -> frozenset[str]:
    """Load valid ISO 639-3 codes from the bundled reference file."""
    iso_path = Path(__file__).resolve().parents[1] / "iso-639-3.txt"
    codes: set[str] = set()
    with open(iso_path, encoding="utf-8") as f:
        # Skip header.
        next(f)
        for line in f:
            parts = line.split("\t")
            if parts:
                codes.add(parts[0].strip())
    return frozenset(codes)


_ISO_CODES = _load_iso_639_3()
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def v035_text_lang_is_iso_639_3(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """The TEXT root's xml:lang must be a valid ISO 639-3 code.

    Preserves the legacy validate_lang_code behavior at TEXT-level
    only. Element-level (S, W, M) xml:lang checks are deferred to
    Phase 5 (V035 expansion).
    """
    root = tree.getroot()
    if root.tag != "TEXT":
        return []  # let v000 (DTD validation) own this
    lang = root.get(_XML_LANG)
    if lang is None:
        return [Finding(
            rule_id="V035",
            severity=Severity.HARD,
            message="TEXT element missing xml:lang attribute",
            path=path,
            location="TEXT",
        )]
    if lang not in _ISO_CODES:
        return [Finding(
            rule_id="V035",
            severity=Severity.HARD,
            message=f"TEXT xml:lang={lang!r} is not a valid ISO 639-3 code",
            path=path,
            location="TEXT",
        )]
    return []


RULES.append(v035_text_lang_is_iso_639_3)
```

- [ ] **Step 4: Run the affected tests**

Run: `.venv/bin/pytest tests/validators/test_validate_xml.py -v`
Expected: All legacy-behavior tests pass. Pay particular attention to: V035 negative tests (invalid lang code), V050/V051 audio tests, and the positive tests on `valid_minimal.xml` (which must not produce any findings from these rules).

If `valid_minimal.xml` now produces a V050 finding: the most likely cause is that the fixture has an `<AUDIO>` element without start/end. Check the fixture and either add the attributes or accept that V050 fires on the fixture (and update the test).

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: All tests pass; the previously-failing tests from end of Task 5 are now passing.

- [ ] **Step 6: Commit**

```bash
git add QC/validation/rules/hard.py
git commit -m "$(cat <<'EOF'
Migrate audio_attr and lang_code checks into rules/hard.py

Two legacy Python checks join the modular structure as v050 (AUDIO
start/end attribute presence + ordering) and v035 (TEXT xml:lang is
valid ISO 639-3). Behavior preserved from the legacy validator
including the known diarized-vs-segmented audio attribute bug; fixing
that lives in Phase 5 alongside the V050-V056 rule migrations.

After this commit, the modular validator has full feature parity
with the pre-refactor validate_xml.py. The remaining xfail tests in
tests/validators/test_validate_xml.py become B's implementation
checklist for Phases 4-7.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Phase 2 — One worked rule: V017 (Tasks 8)

### Task 8: Implement V017 (FORM must have non-empty text content)

V017 is `xfail` in the current test suite. The current validator does not enforce it (DTD `mixed` content cannot express "must have text"). This is the first new Python rule; landing it proves the modular flow end-to-end and flips one xfail to plain-pass.

**Files:**
- Modify: `QC/validation/rules/hard.py`
- Modify: `tests/validators/test_validate_xml.py:300` (remove the xfail marker on V017's test)

- [ ] **Step 1: Read the V017 spec and existing xfail test**

Read [.claude/plans/2026-05-29-xml-validation-design.md](2026-05-29-xml-validation-design.md) for V017's rule text.

Read [tests/validators/test_validate_xml.py](../../tests/validators/test_validate_xml.py) around line 290–310 for the V017 test. The marker tuple is `("v017", "empty form", "form is empty")`. The rule message must contain one of these (case-insensitive).

Read [tests/fixtures/v017_empty_FORM.xml](../../tests/fixtures/v017_empty_FORM.xml) to confirm the fixture shape: a TEXT > S > FORM with empty text content.

- [ ] **Step 2: Confirm the test currently XFAILs**

Run: `.venv/bin/pytest tests/validators/test_validate_xml.py::test_V017_empty_FORM_negative -v`
Expected: XFAIL.

- [ ] **Step 3: Implement the V017 rule**

Append to `QC/validation/rules/hard.py`:

```python
def v017_form_must_have_content(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V017: every <FORM> element must have non-empty text content.

    "Non-empty" means: text exists AND, after stripping whitespace,
    is not the empty string. The DTD allows mixed content on FORM,
    so this constraint cannot be expressed in pure XSD/DTD.

    Per the design doc this is HARD-severity: an empty FORM is
    typically a scraping bug (the source had content the scraper
    didn't capture) and should block merge.
    """
    findings: list[Finding] = []
    for form in tree.iter("FORM"):
        text = form.text or ""
        if text.strip():
            continue
        parent_s = form.getparent()
        s_id = parent_s.get("id") if parent_s is not None else None
        kind = form.get("kindOf") or "(no kindOf)"
        findings.append(Finding(
            rule_id="V017",
            severity=Severity.HARD,
            message=f"empty FORM (kindOf={kind!r}) — form is empty",
            path=path,
            location=f"S={s_id}" if s_id else "FORM",
        ))
    return findings


RULES.append(v017_form_must_have_content)
```

The message contains `"form is empty"` so it matches the test's marker tuple `("v017", "empty form", "form is empty")`.

- [ ] **Step 4: Remove the xfail marker**

In `tests/validators/test_validate_xml.py`, find `test_V017_empty_FORM_negative` (around line 295) and remove the `@pytest.mark.xfail(...)` decorator (and the import-time `XFAIL_NOT_YET_CHECKED` reason it cites).

Before:
```python
@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V017_empty_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V017: FORM with empty text content is rejected."""
    copy_fixture(fixtures_dir / "v017_empty_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v017", "empty form", "form is empty")), (
        f"expected finding for empty FORM; got stdout={proc.stdout!r}"
    )
```

After:
```python
def test_V017_empty_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V017: FORM with empty text content is rejected."""
    copy_fixture(fixtures_dir / "v017_empty_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v017", "empty form", "form is empty")), (
        f"expected finding for empty FORM; got stdout={proc.stdout!r}"
    )
```

- [ ] **Step 5: Verify the test passes**

Run: `.venv/bin/pytest tests/validators/test_validate_xml.py::test_V017_empty_FORM_negative -v`
Expected: PASSED.

If it XPASSes instead of plain-passing, the xfail marker wasn't removed. If it fails, the most likely cause is that the rule's message text doesn't contain any marker from the tuple (`"v017"`, `"empty form"`, `"form is empty"`). The current message includes `"form is empty"` explicitly, so this should match.

- [ ] **Step 6: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: One fewer xfail (now 41 instead of 42), one more plain-pass.

- [ ] **Step 7: Commit**

```bash
git add QC/validation/rules/hard.py tests/validators/test_validate_xml.py
git commit -m "$(cat <<'EOF'
Add V017 (FORM must have non-empty content) as first new Python rule

V017 is a 'currently NOT checked' rule in the validation design doc.
The DTD can't express 'must have text' for mixed-content elements,
so this lands as a Python check in rules/hard.py.

The rule's message includes 'form is empty' which the existing xfail
test in tests/validators/test_validate_xml.py already targets via its
marker tuple. Removing the xfail marker flips the test from XFAIL to
plain-pass, exactly the pattern Phases 5-7 will repeat for each
remaining rule.

The xfail count goes from 42 to 41.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Phase 3 — CLI flags + SOFT CSV plumbing (Tasks 9–10)

### Task 9: Add `--no-exit-on-hard` and default exit-1 on HARD

**Files:**
- Modify: `QC/validation/validate_xml.py`
- Modify: `tests/validators/test_runner.py`

- [ ] **Step 1: Write failing tests for the exit code**

Append to `tests/validators/test_runner.py`:

```python
import subprocess
import sys


VALIDATE_XML_CLI = (
    Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_xml.py"
)


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_XML_CLI), *args],
        capture_output=True,
        text=True,
    )


def test_exit_zero_on_clean_corpus(tmp_path, fixtures_dir, copy_fixture):
    """When no HARD findings are produced, the validator exits 0."""
    copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"


def test_exit_nonzero_on_hard_findings(tmp_path, fixtures_dir, copy_fixture):
    """Default: any HARD finding causes exit 1."""
    copy_fixture(fixtures_dir / "v017_empty_FORM.xml", tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path)])
    assert proc.returncode == 1, (
        f"expected exit 1 on HARD findings; got {proc.returncode}\n"
        f"stderr: {proc.stderr}"
    )


def test_no_exit_on_hard_overrides_to_zero(tmp_path, fixtures_dir, copy_fixture):
    """--no-exit-on-hard restores legacy always-exit-0 behavior."""
    copy_fixture(fixtures_dir / "v017_empty_FORM.xml", tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path), "--no-exit-on-hard"])
    assert proc.returncode == 0, (
        f"expected --no-exit-on-hard to suppress nonzero exit; "
        f"got {proc.returncode}\nstderr: {proc.stderr}"
    )
```

Note: `fixtures_dir` and `copy_fixture` are conftest fixtures so they're available here.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/validators/test_runner.py::test_exit_nonzero_on_hard_findings -v`
Expected: FAILED (current runner returns 0 unconditionally).

- [ ] **Step 3: Implement the flag and exit-code logic**

In `QC/validation/validate_xml.py`, modify `_build_arg_parser`:

```python
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FormosanBank XML validator.")
    sub = parser.add_subparsers(dest="search_by", required=True)

    by_path = sub.add_parser("by_path")
    by_path.add_argument("--path", required=True, type=Path)

    by_corpus = sub.add_parser("by_corpus")
    by_corpus.add_argument("--corpus", required=True)
    by_corpus.add_argument("--corpora_path", required=True, type=Path)

    by_language = sub.add_parser("by_language")
    by_language.add_argument("--language", required=True)
    by_language.add_argument("--corpora_path", required=True, type=Path)

    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--log_dir", type=Path, default=None)
    parser.add_argument(
        "--no-exit-on-hard",
        action="store_true",
        help="Always exit 0, even if HARD findings are produced. "
             "Backward-compat for callers that depend on the legacy "
             "always-exit-0 behavior.",
    )
    return parser
```

And modify `main` so it returns the right exit code:

```python
def main(argv: list[str] | None = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    targets = _resolve_target_files(args)

    all_findings: list[Finding] = []
    all_rules = (
        hard_rules.RULES + soft_rules.RULES + warn_rules.RULES
    )

    for path in targets:
        try:
            tree = parse_tree(path)
        except etree.XMLSyntaxError as e:
            all_findings.append(Finding(
                rule_id="V000",
                severity=Severity.HARD,
                message=f"XML parse error: {e}",
                path=path,
            ))
            continue
        all_findings.extend(run_per_file_rules(tree, path, all_rules, index=None))

    _print_summary(all_findings)

    has_hard = any(f.severity is Severity.HARD for f in all_findings)
    if has_hard and not args.no_exit_on_hard:
        return 1
    return 0
```

- [ ] **Step 4: Run the new tests to verify they pass**

Run: `.venv/bin/pytest tests/validators/test_runner.py -v`
Expected: 7 tests passed.

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: All previously passing tests still pass. The existing tests in `tests/validators/test_validate_xml.py` don't assert on exit code (per the test file's docstring), so they continue to work despite the new default behavior.

- [ ] **Step 6: Commit**

```bash
git add QC/validation/validate_xml.py tests/validators/test_runner.py
git commit -m "$(cat <<'EOF'
Add --no-exit-on-hard flag; default exit 1 on HARD findings

The validator now exits nonzero (1) if any HARD findings are produced.
This is the core enabling change for sub-project B's CI-gating goal:
the validator becomes useful as a PR-blocking check.

--no-exit-on-hard restores the legacy always-exit-0 behavior for any
caller that depends on it. SOFT and WARN findings never affect the
exit code (by design: SOFT feeds the drift CSV, WARN is advisory).

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 10: Add `--soft-csv` flag and wire SOFT-CSV writer

There are no SOFT rules yet (those land in Phase 7), so this task adds the plumbing and verifies the file shape with a hand-injected SOFT finding in a test. Phase 7 will plug actual rules into the existing infrastructure.

**Files:**
- Modify: `QC/validation/validate_xml.py`
- Modify: `tests/validators/test_runner.py`

- [ ] **Step 1: Write failing test for the CSV output**

Append to `tests/validators/test_runner.py`:

```python
import csv


def test_soft_csv_written_with_header_when_no_soft_findings(tmp_path, fixtures_dir, copy_fixture):
    """Even with no SOFT findings, the CSV is created with just the header."""
    copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    csv_path = tmp_path / "soft.csv"
    proc = _run_cli([
        "by_path", "--path", str(tmp_path),
        "--soft-csv", str(csv_path),
    ])
    assert proc.returncode == 0
    assert csv_path.exists()
    with open(csv_path, newline="") as f:
        rows = list(csv.reader(f))
    assert rows == [["file", "rule_id", "language", "character", "count"]]


def test_soft_csv_default_path(tmp_path, fixtures_dir, copy_fixture, monkeypatch):
    """Without --soft-csv, the writer goes to logs/validation_soft.csv
    relative to the current working directory."""
    copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    monkeypatch.chdir(tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path)])
    assert proc.returncode == 0
    assert (tmp_path / "logs" / "validation_soft.csv").exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/pytest tests/validators/test_runner.py::test_soft_csv_written_with_header_when_no_soft_findings -v`
Expected: FAILED on the assertion that the CSV exists (or on the `--soft-csv` argument being unknown).

- [ ] **Step 3: Wire the `--soft-csv` flag and call the writer**

In `QC/validation/validate_xml.py`:

1. Add the argparse flag:

```python
    parser.add_argument(
        "--soft-csv",
        dest="soft_csv",
        type=Path,
        default=Path("logs") / "validation_soft.csv",
        help="Path where SOFT findings are written as CSV. "
             "Overwritten per run; parent dirs created if absent.",
    )
```

2. Import the writer at the top of the file:

```python
from QC.validation._finding import Finding, Severity, write_soft_csv
```

3. Add the call in `main`, after the file-walking loop and before exit:

```python
    _print_summary(all_findings)
    write_soft_csv(args.soft_csv, all_findings)

    has_hard = any(f.severity is Severity.HARD for f in all_findings)
    if has_hard and not args.no_exit_on_hard:
        return 1
    return 0
```

- [ ] **Step 4: Run new tests to verify they pass**

Run: `.venv/bin/pytest tests/validators/test_runner.py -v`
Expected: 9 tests passed.

- [ ] **Step 5: Run full suite to verify no regressions**

Run: `.venv/bin/pytest`
Expected: All tests pass.

The default-path test (`test_soft_csv_default_path`) uses `monkeypatch.chdir` so it doesn't pollute the repo's actual `logs/` directory. The CSV path is relative to cwd, which is the correct behavior for a CLI tool.

- [ ] **Step 6: Confirm no stray CSV got written to the repo**

Run: `ls logs/validation_soft.csv 2>&1`
Expected: `ls: logs/validation_soft.csv: No such file or directory`.

If a stray CSV exists, the test isn't properly using `monkeypatch.chdir`. Delete the file and revise the test to ensure isolation.

- [ ] **Step 7: Commit**

```bash
git add QC/validation/validate_xml.py tests/validators/test_runner.py
git commit -m "$(cat <<'EOF'
Add --soft-csv flag and per-run SOFT CSV writer call

Wires the SOFT-CSV writer (added in Task 3) into the runner.
--soft-csv overrides the default path (logs/validation_soft.csv
relative to cwd). The CSV is overwritten per run; the parent
directory is created if absent.

Phase 1-3 work complete: the modular runner has feature parity with
the legacy validator, plus the new exit-code semantics and SOFT-CSV
infrastructure. Phases 4-7 (DTD tightening, ~25 Python HARD rules,
cross-file rules, SOFT rules) land in subsequent plans.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Self-review checklist (run after writing the plan, before sharing)

**Spec coverage:**

- [x] Modular split by severity → Tasks 4–7 implement `rules/{hard,soft,warn}.py`.
- [x] `Finding` dataclass + `Severity` enum → Task 1.
- [x] `CorpusIndex` for cross-file rules → Task 2.
- [x] Two-pass runner architecture → Tasks 5–7 implement pass 1; pass 2 + cross-file rules deferred to a Phase-6 plan (the runner signature already accepts `CorpusIndex | None` so adding pass 2 later is non-structural).
- [x] Hybrid emission (per-element HARD/WARN, aggregated SOFT) → Finding shape supports both; write_soft_csv enforces SOFT pre-aggregation by skipping non-SOFT.
- [x] Stderr for HARD/WARN, CSV for SOFT → Task 5 wires summary printing, Task 10 wires CSV.
- [x] Exit-1 on HARD with `--no-exit-on-hard` backward-compat → Task 9.
- [x] CLI surface preserved (by_path/by_corpus/by_language + --verbose + --log_dir) → Task 5's `_build_arg_parser`.
- [x] DTD allocation policy → Task 6 owns DTD-side enforcement via `v000_dtd_validation`. Phase 4 (separate plan) extends this rule's reach by tightening `xml_template.dtd`.
- [x] Migration: existing audio_attr and lang_code checks preserved → Task 7.
- [x] One worked rule (V017) flipped from xfail to plain-pass → Task 8.

**Placeholder scan:**
- No "TBD", "TODO", "implement later" or similar appear in any step.
- No "Add appropriate error handling" or vague guidance.
- No "Similar to Task N" cross-references — each task spells out its own code.
- All steps that change code include the actual code.
- All commands include expected output.

**Type and name consistency:**
- `Finding` fields are consistent across Tasks 1, 3, 5, 7, 8.
- `Severity.HARD/SOFT/WARN` used uniformly.
- `discover_xml_files`, `parse_tree`, `run_per_file_rules` defined in Task 5 and imported in Task 8's test.
- `write_soft_csv` signature `(path, findings)` consistent between Task 3 (definition) and Task 10 (call site).
- Rule signature `(tree, path, index)` consistent everywhere.
- `RULES` list-of-functions pattern consistent across all rule modules.

---

## After this plan

Once these 10 tasks land and the PR is reviewed, the next plans cover:

- **Phase 4 plan** — DTD tightening: promote V030 (citation), V032 (copyright), V050 (audio @file), and other one-line constraints to `#REQUIRED` in `xml_template.dtd`. Each promotion removes one xfail and lets `v000_dtd_validation` catch it.
- **Phase 5 plan** — Python HARD rule migrations, category by category: structural (V003–V006), FORM tier (V011–V016), TRANSL (V020–V026), attribute (V031, V033–V041), audio (V051–V056 fixing the diarized/segmented bug), segmentation (V060–V063), PHON (V070–V073). Each rule = one xfail removed.
- **Phase 6 plan** — Cross-file rules: pass-2 plumbing in the runner (call `CROSS_FILE_RULES` after building the `CorpusIndex`), V081 implementation, V082/V083 path discipline.
- **Phase 7 plan** — SOFT rules: V010 (S without FORM count), V014 (missing standard tier count), and the orthography drift integration (depends on roadmap B7).
