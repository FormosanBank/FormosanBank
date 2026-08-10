# QC Pipeline Test Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the cross-stage test infrastructure the 2026-08-10 proposals identified as the top gap: rerun-stability tests, an end-to-end pipeline integration test, SOFT registry-consistency validation, manual-edits round-trip tests, and the warnings-sidecar fix these tests depend on.

**Architecture:** All pipeline scripts are exercised as subprocesses (the suite's existing pattern — `subprocess.run([sys.executable, SCRIPT, ...])`), never by importing `main()`, so tests see exactly what operators see. Rerun-stability is asserted as *run 2 output == run 1 output* (byte-for-byte), never *run 1 == input*, because a first run may legitimately reformat. Registry consistency is a new finding-based validator emitting SOFT findings (maintainer ruling 2026-08-10: registries may legitimately be out of sync; only unreadable files are HARD).

**Tech Stack:** pytest, subprocess, `xml.etree`/`lxml` (as in the existing suite), the `Finding`/`Severity` framework in `QC/validation/_finding.py`.

## Global Constraints

- Python 3.13, run via the repo `.venv` (`source .venv/bin/activate`).
- Tests live under `tests/` mirroring the existing split (`cleaners/`, `utilities/`, `validators/`, plus new `integration/` and `data_consistency/`).
- Invoke scripts via subprocess with `sys.executable`; never import and call `main()` directly.
- Fixtures are minimal synthetic XML in `tests/fixtures/`; never depend on published corpora under `Corpora/` (they change) or on real conversion tables (craft test-local TSVs).
- New validator rule IDs start at **V150** (V141 is the current maximum).
- Registry checks emit SOFT findings only; exit 1 only for unreadable/unparseable registry files (POL-034).
- Commit after each green task; do not batch.

## Empirical findings this plan encodes (2026-08-10 investigation)

The maintainer asked whether `clean_xml`/`standardize` can or should be idempotent. Investigation results, which reframe the original "idempotence tests" proposal:

**Maintainer ruling 2026-08-10:** per the findings below, rerun-stability tests are scoped to **clean_xml only**; standardize and add_phonology need no rerun tests (they are regenerators — rerun-stable by construction).

1. **`standardize.py` and `add_phonology.py` are not idempotence problems at all — they are regenerators.** In every mode, `create_standard` *replaces* the standard FORM with a fresh copy of the original before applying conversions ([standardize.py:304-330](../../QC/utilities/standardize.py)), and `add_phonology` rewrites the existing PHON of each kindOf rather than appending. Because conversion always starts from the original tier, even a non-idempotent table rule like Cauquelin Puyuma `l→ll` cannot double-apply (verified: two TSV runs on a synthetic corpus both yield `llima`, never `llllima`; two `--copy` runs and two `add_phonology` runs were byte-identical). The property to test is **regeneration determinism** (run 2 == run 1), and its two enabling invariants: derived tiers are *replaced not appended*, and conversion input is the *original* tier. These hold today; the tests pin them.
2. **`clean_xml.py` is a true idempotence question, and currently passes empirically but not by construction.** Its input *is* its own prior output in steady state (published corpora get re-cleaned). A double run over all 93 dirty test fixtures left every XML byte-identical on the second pass. Nothing guarantees this for future rules — each new cleaning rule must avoid producing output that another rule (or itself) transforms again. The test converts "not guaranteed" into "continuously verified", which is exactly what we want; if a future rule genuinely cannot be idempotent, the test failure forces that discussion rather than letting silent churn ship.
3. **One real non-idempotence bug found:** `CleanerWarnings.write_csv` opens its CSV in append mode ([clean_xml.py:151](../../QC/cleaning/clean_xml.py)), so every rerun appends duplicate rows for persistent warn-only findings (verified: run 2 doubled `cleaner_warnings.csv` from 84 to 166 rows while changing no XML). Task 1 fixes this (truncate per run, per POL-033: warnings CSVs are per-run reports) — a prerequisite for whole-tree rerun-stability assertions.

---

### Task 1: Warnings sidecar — rewrite per run, not append

**Files:**
- Modify: `QC/cleaning/clean_xml.py` (the `CleanerWarnings.write_csv` method, currently opening with mode `"a"`)
- Test: `tests/cleaners/test_cleaner_warnings_rewrite.py`

**Interfaces:**
- Consumes: `CleanerWarnings` dataclass (`csv_path: Path`, `.add(rule_id, file_path, s_id, character, position)`, `.write_csv()`).
- Produces: `write_csv()` now truncates: after any call, the CSV contains exactly the current run's rows (plus header). Also: `write_csv()` on an empty row set **removes** a stale CSV from a previous run if one exists (a rerun that finds nothing must not leave last run's findings lying around).

- [ ] **Step 1: Write the failing test**

```python
"""CleanerWarnings.write_csv must produce a per-run report, not a log.

POL-033: warnings sidecars are per-run reports. Before 2026-08-10 write_csv
opened in append mode, so rerunning clean_xml/standardize doubled every
persistent warn-only row (verified empirically: 84 -> 166 rows on a no-op
second run over tests/fixtures).
"""
import csv
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "QC" / "cleaning"))
from clean_xml import CleanerWarnings  # noqa: E402


def _rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_second_run_rewrites_instead_of_appending(tmp_path):
    csv_path = tmp_path / "cleaner_warnings.csv"

    run1 = CleanerWarnings(csv_path)
    run1.add("c022", "a.xml", "S_1", "*", 0)
    run1.write_csv()
    assert len(_rows(csv_path)) == 1

    run2 = CleanerWarnings(csv_path)  # fresh instance, as a rerun creates
    run2.add("c022", "a.xml", "S_1", "*", 0)
    run2.write_csv()
    rows = _rows(csv_path)
    assert len(rows) == 1, "rerun must not duplicate persistent warnings"
    assert rows[0]["rule_id"] == "c022"


def test_single_header_after_rewrite(tmp_path):
    csv_path = tmp_path / "w.csv"
    for _ in range(2):
        w = CleanerWarnings(csv_path)
        w.add("c002", "b.xml", "S_9", "'", 3)
        w.write_csv()
    text = csv_path.read_text(encoding="utf-8")
    assert text.count("rule_id") == 1


def test_empty_run_removes_stale_csv(tmp_path):
    csv_path = tmp_path / "w.csv"
    w1 = CleanerWarnings(csv_path)
    w1.add("c007", "c.xml", "S_2", "ㄅ", 1)
    w1.write_csv()
    assert csv_path.exists()

    w2 = CleanerWarnings(csv_path)  # rerun found nothing
    w2.write_csv()
    assert not csv_path.exists(), "clean rerun must not leave stale findings"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/cleaners/test_cleaner_warnings_rewrite.py -v`
Expected: FAIL — `test_second_run_rewrites_instead_of_appending` sees 2 rows; `test_empty_run_removes_stale_csv` sees the file still present.

- [ ] **Step 3: Fix `write_csv`**

Replace the body of `CleanerWarnings.write_csv` (currently: early-return on no rows; open with `"a"`; write header if `f.tell() == 0`):

```python
    def write_csv(self) -> None:
        """Write this run's rows, replacing any previous run's CSV.

        POL-033: the CSV is a per-run report, not a cumulative log. A run
        with no rows removes a stale CSV rather than leaving last run's
        findings in place (and still avoids creating empty files).
        """
        if not self._rows:
            self.csv_path.unlink(missing_ok=True)
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["rule_id", "file", "s_id", "character", "position"],
            )
            writer.writeheader()
            writer.writerows(self._rows)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/cleaners/test_cleaner_warnings_rewrite.py -v`
Expected: 3 passed.

- [ ] **Step 5: Run the full existing suite (regression check)**

Run: `pytest tests/ -q`
Expected: no new failures. If any existing test asserted append behavior or `f.tell()`-based headers, update it to the rewrite contract — cite POL-033 in the updated docstring.

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_cleaner_warnings_rewrite.py
git commit -m "fix: warnings sidecars are per-run reports, not append logs (POL-033)"
```

---

### Task 2: Shared runner helper + clean_xml idempotence test

**Files:**
- Modify: `tests/_helpers.py` (add `run_qc_script` and `snapshot_tree`)
- Test: `tests/integration/__init__.py` (empty), `tests/integration/test_rerun_stability.py`
- Create: `tests/fixtures/rerun_puyuma_l_to_ll.xml`, `tests/fixtures/rerun_l_to_ll_table.tsv`

**Interfaces:**
- Consumes: existing `tests/_helpers.py` module; scripts `QC/cleaning/clean_xml.py`, `QC/utilities/standardize.py`, `QC/utilities/add_phonology.py`.
- Produces (used by Tasks 3 and 5):
  - `run_qc_script(script_relpath: str, args: list[str]) -> subprocess.CompletedProcess` — runs `<repo>/QC/...` via `sys.executable`, `capture_output=True, text=True`.
  - `snapshot_tree(root: Path) -> dict[str, bytes]` — relative-path → file-bytes map of every file under `root` (the comparison currency for "byte-identical").

- [ ] **Step 1: Add the helpers to `tests/_helpers.py`**

```python
REPO_ROOT = Path(__file__).resolve().parents[1]


def run_qc_script(script_relpath: str, args: list[str]) -> subprocess.CompletedProcess:
    """Run a QC pipeline script exactly as an operator would.

    `script_relpath` is relative to the repo root, e.g.
    "QC/cleaning/clean_xml.py". Subprocess invocation (not importing main)
    is the suite-wide convention: tests must see argv parsing, exit codes,
    and stdout/stderr as shipped.
    """
    import sys as _sys
    return subprocess.run(
        [_sys.executable, str(REPO_ROOT / script_relpath), *args],
        capture_output=True,
        text=True,
    )


def snapshot_tree(root: Path) -> dict[str, bytes]:
    """Map of relative path -> bytes for every file under root.

    The currency for rerun-stability assertions: two runs are 'stable'
    iff their snapshots are equal — XML *and* sidecar CSVs alike.
    """
    return {
        str(p.relative_to(root)): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }
```

- [ ] **Step 2: Create the l→ll fixture pair**

`tests/fixtures/rerun_puyuma_l_to_ll.xml` — a doubling rule is the sharpest
probe that conversion reads the *original* tier, never its own output:

```xml
<?xml version="1.0" ?>
<TEXT id="rerun_pyu" citation="Rerun-stability fixture" BibTeX_citation="@misc{rerun_pyu}" copyright="CC" xml:lang="pyu" dialect="Nanwang">
    <S id="S1">
        <FORM kindOf="original">lima ∅-ku dálan</FORM>
        <TRANSL xml:lang="eng">five NULL-1SG road</TRANSL>
        <W id="S1_W1">
            <FORM kindOf="original">lima</FORM>
            <M id="S1_W1_M1">
                <FORM kindOf="original">lima</FORM>
                <TRANSL xml:lang="eng" kindOf="original">five</TRANSL>
            </M>
        </W>
    </S>
    <S id="S2">
        <FORM kindOf="original">talal na l</FORM>
        <TRANSL xml:lang="eng">plain sentence</TRANSL>
    </S>
</TEXT>
```

`tests/fixtures/rerun_l_to_ll_table.tsv` (tab-separated; deliberately NOT
named per the `<Language>_<Scheme>_113.tsv` convention, so no profile
resolves and no case variants derive — keeps the fixture self-contained):

```text
original	Nanwang
l	ll
á	a
```

- [ ] **Step 3: Write the test**

`tests/integration/test_rerun_stability.py` (maintainer ruling 2026-08-10:
clean_xml only — standardize/add_phonology are regenerators and need no
rerun test):

```python
"""clean_xml idempotence guard.

clean_xml's steady-state input is its own prior output (published
corpora are re-cleaned), so run2(run1(x)) == run1(x) is a hard
requirement. It holds empirically today (verified 2026-08-10 over all
93 dirty fixtures) but not by construction — every future cleaning rule
whose output falls inside another rule's input domain breaks it
silently. This test is the guard that rule runs into.

The assertion compares run 2 against run 1 — never run 1 against the
input, because a first run may legitimately reformat serialization.
"""
import shutil

from tests._helpers import REPO_ROOT, run_qc_script, snapshot_tree

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def test_clean_xml_idempotent_over_all_fixtures(tmp_path):
    """Second clean pass over every dirty fixture changes nothing."""
    corpus = tmp_path / "corpus" / "XML"
    corpus.mkdir(parents=True)
    for fixture in FIXTURES.glob("*.xml"):
        shutil.copy(fixture, corpus / fixture.name)
    argv = ["--corpora_path", str(tmp_path / "corpus")]

    first = run_qc_script("QC/cleaning/clean_xml.py", argv)
    assert first.returncode == 0, first.stderr
    snap1 = snapshot_tree(tmp_path / "corpus")

    second = run_qc_script("QC/cleaning/clean_xml.py", argv)
    assert second.returncode == 0, second.stderr
    snap2 = snapshot_tree(tmp_path / "corpus")

    assert snap1 == snap2
```

- [ ] **Step 4: Run the test — expect pass (pins current behavior)**

Run: `pytest tests/integration/test_rerun_stability.py -v`
Expected: 1 passed. This is a characterization test (the 2026-08-10
investigation verified the property by hand). If it fails on the warnings
CSV, Task 1 has not landed — it is a prerequisite. Any *XML* mismatch is a
real finding: diff the two snapshots and report before proceeding.

- [ ] **Step 5: Commit**

```bash
git add tests/_helpers.py tests/integration/ tests/fixtures/rerun_puyuma_l_to_ll.xml tests/fixtures/rerun_l_to_ll_table.tsv
git commit -m "test: rerun-stability guards for clean_xml/standardize/add_phonology"
```

---

### Task 3: End-to-end pipeline integration test

**Files:**
- Create: `tests/fixtures/pipeline_e2e_source.xml`
- Test: `tests/integration/test_pipeline_end_to_end.py`

**Interfaces:**
- Consumes: `run_qc_script`, `snapshot_tree`, `REPO_ROOT` from `tests/_helpers.py` (Task 2); fixture TSV `tests/fixtures/rerun_l_to_ll_table.tsv` (Task 2).
- Produces: nothing consumed downstream; this is the capstone assertion set.

- [ ] **Step 1: Create the end-to-end source fixture**

`tests/fixtures/pipeline_e2e_source.xml` — one file exercising every
cross-stage handoff: dirty typography for clean_xml (curly apostrophe,
em-dash, ø null glyph, doubled punctuation), null units and accents for
standardize, and a W/M null pair for the V069 invariant:

```xml
<?xml version="1.0" ?>
<TEXT id="e2e_pyu" citation="Pipeline e2e fixture" BibTeX_citation="@misc{e2e_pyu}" copyright="CC" xml:lang="pyu" dialect="Nanwang">
    <S id="S1">
        <FORM kindOf="original">lima ø-ku — dálan’a!!</FORM>
        <TRANSL xml:lang="eng">five NULL-1SG road</TRANSL>
        <W id="S1_W1">
            <FORM kindOf="original">ø-ku</FORM>
            <M id="S1_W1_M1">
                <FORM kindOf="original">ø</FORM>
                <TRANSL xml:lang="eng" kindOf="original">NULL</TRANSL>
            </M>
            <M id="S1_W1_M2">
                <FORM kindOf="original">ku</FORM>
                <TRANSL xml:lang="eng" kindOf="original">1SG</TRANSL>
            </M>
        </W>
    </S>
</TEXT>
```

- [ ] **Step 2: Write the test**

`tests/integration/test_pipeline_end_to_end.py`:

```python
"""One corpus through the full pipeline in canonical order.

Order per QC/README.md: apply_manual_edits (no-op here, exercised in
tests/cleaners/test_manual_edits_survival.py) -> clean_xml -> standardize
-> add_phonology. Asserts the cross-stage invariants each stage's spec
*assumes* about its predecessor — exactly what per-module tests cannot
see:

  clean_xml -> standardize: null glyph is canonical ∅ (POL-012) and
      dashes are ASCII '-' (POL-011) BEFORE standardize looks for null
      units and hyphens.
  standardize -> add_phonology: standard S-FORM has no null units;
      standard tier exists at S, W, and M.
  add_phonology output: whole-null M FORM gets PHON '∅'; PHON is
      marker-free (POL-003); punctuation absent from PHON.
"""
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from tests._helpers import REPO_ROOT, run_qc_script

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _pipeline(tmp_path: Path) -> Path:
    corpus_root = tmp_path / "corpus"
    (corpus_root / "XML").mkdir(parents=True)
    shutil.copy(FIXTURES / "pipeline_e2e_source.xml",
                corpus_root / "XML" / "pipeline_e2e_source.xml")
    for script, args in [
        ("QC/cleaning/clean_xml.py",
         ["--corpora_path", str(corpus_root)]),
        ("QC/utilities/standardize.py",
         ["--tsv_path", str(FIXTURES / "rerun_l_to_ll_table.tsv"),
          "--corpora_path", str(corpus_root)]),
        ("QC/utilities/add_phonology.py",
         ["--corpora_path", str(corpus_root)]),
    ]:
        proc = run_qc_script(script, args)
        assert proc.returncode == 0, f"{script}: {proc.stderr}"
    return corpus_root / "XML" / "pipeline_e2e_source.xml"


def test_full_pipeline_invariants(tmp_path):
    out = _pipeline(tmp_path)
    text = out.read_text(encoding="utf-8")
    root = ET.parse(out).getroot()

    # clean_xml handoffs (original tier)
    s_orig = root.find(".//S/FORM[@kindOf='original']").text
    assert "ø" not in s_orig and "∅" in s_orig      # POL-012 canonical glyph
    assert "—" not in s_orig and "-" in s_orig      # POL-011 dash -> ASCII
    assert "’" not in text                          # POL-010 apostrophe
    assert "!!" not in s_orig                       # repeated punct trimmed

    # standardize handoffs
    s_std = root.find(".//S/FORM[@kindOf='standard']").text
    assert "∅" not in s_std                         # null units removed at S
    assert "á" not in s_std                         # accents stripped
    assert "llima" in s_std                         # table applied
    for tier in (".//W", ".//M"):
        for el in root.findall(tier):
            assert el.find("FORM[@kindOf='standard']") is not None

    # W/M null propagation survives standardize (V069's precondition)
    w_std = root.find(".//W/FORM[@kindOf='standard']").text
    m1_std = root.find(".//M/FORM[@kindOf='standard']").text
    assert "∅" in w_std and m1_std == "∅"

    # add_phonology handoffs
    m1_phon = root.find(".//M/PHON[@kindOf='standard']").text
    assert m1_phon == "∅"                           # whole-null FORM -> PHON ∅
    s_phon = root.find(".//S/PHON[@kindOf='standard']").text
    assert s_phon is not None
    for banned in ("-", "=", "<", ">", "!", "∅"):
        assert banned not in s_phon                 # marker-free, null silent


```

- [ ] **Step 3: Run the test**

Run: `pytest tests/integration/test_pipeline_end_to_end.py -v`
Expected: 1 passed. Assertion-by-assertion failures here are *findings*,
not test bugs — e.g. if `’` survives into a TRANSL, check whether the
apostrophe rule is FORM-only by design before "fixing" the test; consult
POL-010 and report mismatches between policy and behavior.

- [ ] **Step 4: Commit**

```bash
git add tests/fixtures/pipeline_e2e_source.xml tests/integration/test_pipeline_end_to_end.py
git commit -m "test: end-to-end pipeline integration invariants"
```

---

### Task 4: Registry-consistency validator (SOFT findings)

**Files:**
- Create: `QC/validation/validate_registries.py`
- Test: `tests/validators/test_validate_registries.py`

**Interfaces:**
- Consumes: `Finding`, `Severity`, `summarize`, `write_findings_csv` from `QC/validation/_finding.py`; `ISO_TO_LANGUAGE` and dialect loaders from `QC/validation/_dialect_inventory.py`; on-disk registries `standards.csv`, `dialects.csv`, `Orthographies/<Scheme>/<Language>.tsv` profiles, `Orthographies/ConversionTables/*.tsv`.
- Produces: CLI `python QC/validation/validate_registries.py [--repo-root PATH] [--csv PATH]`. Exit 0 when all registries are readable (SOFT findings do not affect exit code, POL-034); exit 1 only when a registry file is missing/unparseable. Rule IDs:
  - `V150 language_missing_from_standards` (SOFT): a language in `ISO_TO_LANGUAGE` has no row in `standards.csv`.
  - `V151 standards_scheme_folder_missing` (SOFT): a non-blank `standards.csv` scheme has no `Orthographies/<scheme>/` folder.
  - `V152 conversion_table_dialect_unknown` (SOFT): a conversion-table value column (other than `original`/`standard`) is not a canonical dialect name in `dialects.csv`.
  - `V153 rules_sidecar_dialect_unknown` (SOFT): a `dialect` value in an `Orthographies/**/*.rules.tsv` sidecar (other than `default`) is not canonical per `dialects.csv`.

- [ ] **Step 1: Write the failing tests**

```python
"""validate_registries: cross-file consistency as SOFT findings.

Maintainer ruling 2026-08-10 (POL-034): registries may be legitimately
out of sync mid-migration, so consistency findings are SOFT and never
fail the run. Only an unreadable registry is HARD (exit 1). The findings
CSV uses the standard one-CSV shape so the same triage tooling applies.

Tests build a miniature repo layout under tmp_path and point the
validator at it with --repo-root; they never depend on the real
registries (which drift).
"""
import csv
from pathlib import Path

from tests._helpers import run_qc_script

SCRIPT = "QC/validation/validate_registries.py"


def _mini_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "Orthographies" / "Ortho113").mkdir(parents=True)
    (root / "Orthographies" / "ConversionTables").mkdir(parents=True)
    (root / "standards.csv").write_text(
        "language,scheme\nAmis,Ortho113\nPuyuma,Ortho113\n",
        encoding="utf-8")
    (root / "dialects.csv").write_text(
        "language,dialect\nPuyuma,Nanwang\nAmis,Coastal\n",
        encoding="utf-8")
    return root


def _findings(csv_path: Path) -> list[dict]:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_consistent_mini_repo_is_clean(tmp_path):
    root = _mini_repo(tmp_path)
    out = tmp_path / "f.csv"
    proc = run_qc_script(SCRIPT, ["--repo-root", str(root),
                                  "--csv", str(out)])
    assert proc.returncode == 0
    assert "V15" not in proc.stdout


def test_unknown_conversion_table_dialect_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "Orthographies" / "ConversionTables"
     / "Puyuma_Test_113.tsv").write_text(
        "original\tNanwan\nl\tll\n", encoding="utf-8")  # typo'd dialect
    out = tmp_path / "f.csv"
    proc = run_qc_script(SCRIPT, ["--repo-root", str(root),
                                  "--csv", str(out)])
    assert proc.returncode == 0, "SOFT findings must not fail the run"
    assert "V152" in proc.stdout
    rows = [r for r in _findings(out) if r["rule_id"] == "V152"]
    assert rows and rows[0]["severity"] == "SOFT"
    assert "Nanwan" in rows[0]["message"]


def test_missing_scheme_folder_is_soft(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "standards.csv").write_text(
        "language,scheme\nAmis,OrthoNope\n", encoding="utf-8")
    proc = run_qc_script(SCRIPT, ["--repo-root", str(root),
                                  "--csv", str(tmp_path / "f.csv")])
    assert proc.returncode == 0
    assert "V151" in proc.stdout


def test_unreadable_registry_is_hard_exit(tmp_path):
    root = _mini_repo(tmp_path)
    (root / "standards.csv").unlink()
    proc = run_qc_script(SCRIPT, ["--repo-root", str(root),
                                  "--csv", str(tmp_path / "f.csv")])
    assert proc.returncode == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/validators/test_validate_registries.py -v`
Expected: FAIL — script does not exist.

- [ ] **Step 3: Implement the validator**

`QC/validation/validate_registries.py`:

```python
"""Cross-file registry consistency checks (SOFT findings; POL-034).

The QC pipeline depends on agreement among loosely-coupled data files:
standards.csv, dialects.csv, orthography profiles, conversion-table
headers, and rules sidecars. The first validate_conversion_table run
found 5 tables that crash purely on dialect-name drift; this validator
surfaces that class *before* anything crashes on it.

All consistency findings are SOFT by maintainer ruling (2026-08-10):
registries may be legitimately out of sync mid-migration. Exit 1 only
when a registry file itself is missing or unparseable.

Note the deliberate difference from V150's cousin in tests: this is a
repo-level validator (no corpus argument) — run it from CI or before a
release, not per corpus.
"""
import argparse
import csv
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[2]))

from QC.validation._finding import (  # noqa: E402
    Finding, Severity, summarize, write_findings_csv,
)

TITLES = {
    "V150": "language_missing_from_standards",
    "V151": "standards_scheme_folder_missing",
    "V152": "conversion_table_dialect_unknown",
    "V153": "rules_sidecar_dialect_unknown",
}
_NON_DIALECT_COLUMNS = {"original", "standard"}


def _read_two_column_csv(path: Path) -> list[tuple[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{path}: empty registry")
        return [(row[0].strip(), row[1].strip() if len(row) > 1 else "")
                for row in reader if row and row[0].strip()]


def check(repo_root: Path) -> list[Finding]:
    findings: list[Finding] = []
    standards_path = repo_root / "standards.csv"
    dialects_path = repo_root / "dialects.csv"
    standards = dict(_read_two_column_csv(standards_path))
    dialects = {d for _, d in _read_two_column_csv(dialects_path)}

    # V150: every known language has a standards.csv row. Uses the live
    # ISO map so adding a language to the code forces a registry entry.
    from QC.validation._dialect_inventory import ISO_TO_LANGUAGE  # noqa: E402
    for language in sorted(set(ISO_TO_LANGUAGE.values())):
        if language not in standards:
            findings.append(Finding(
                rule_id="V150", severity=Severity.SOFT,
                message=(f"{language} is in ISO_TO_LANGUAGE but has no "
                         f"standards.csv row (blank scheme = 'no standard "
                         f"yet' is fine; a missing row is drift)"),
                path=standards_path, language=language))

    # V151: non-blank scheme folders exist.
    for language, scheme in sorted(standards.items()):
        if scheme and not (repo_root / "Orthographies" / scheme).is_dir():
            findings.append(Finding(
                rule_id="V151", severity=Severity.SOFT,
                message=(f"standards.csv maps {language} -> {scheme} but "
                         f"Orthographies/{scheme}/ does not exist"),
                path=standards_path, language=language))

    # V152: conversion-table value columns name canonical dialects.
    tables_dir = repo_root / "Orthographies" / "ConversionTables"
    for table in sorted(tables_dir.glob("*.tsv")):
        with open(table, newline="", encoding="utf-8") as f:
            header = f.readline().rstrip("\n").split("\t")
        for column in header[1:]:
            column = column.strip()
            if column and column not in _NON_DIALECT_COLUMNS \
                    and column not in dialects:
                findings.append(Finding(
                    rule_id="V152", severity=Severity.SOFT,
                    message=(f"{table.name} value column {column!r} is not "
                             f"a canonical dialect in dialects.csv (this "
                             f"is the class that crashes "
                             f"validate_conversion_table)"),
                    path=table, character=column))

    # V153: rules-sidecar dialect values are canonical.
    for sidecar in sorted((repo_root / "Orthographies").rglob("*.rules.tsv")):
        with open(sidecar, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            if reader.fieldnames is None or "dialect" not in reader.fieldnames:
                continue
            seen = set()
            for row in reader:
                value = (row.get("dialect") or "").strip()
                if value and value != "default" and value not in dialects \
                        and value not in seen:
                    seen.add(value)
                    findings.append(Finding(
                        rule_id="V153", severity=Severity.SOFT,
                        message=(f"{sidecar.name} scopes rules to dialect "
                                 f"{value!r}, not canonical per "
                                 f"dialects.csv"),
                        path=sidecar, character=value))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Cross-file registry consistency (SOFT; POL-034)")
    parser.add_argument("--repo-root", type=Path,
                        default=_HERE.parents[2],
                        help="repository root (default: this checkout)")
    parser.add_argument("--csv", type=Path, default=None,
                        help="findings CSV path (default: "
                             "<repo-root>/logs/registry_findings.csv)")
    args = parser.parse_args(argv)

    try:
        findings = check(args.repo_root)
    except (OSError, ValueError) as error:
        print(f"HARD: unreadable registry: {error}", file=sys.stderr)
        return 1

    csv_path = args.csv or (args.repo_root / "logs" / "registry_findings.csv")
    for severity, by_rule in summarize(findings).items():
        for rule_id, count in sorted(by_rule.items()):
            print(f"{rule_id} {TITLES.get(rule_id, '')}: {count}")
    if findings:
        write_findings_csv(csv_path, findings, TITLES)
        print(f"Details: {csv_path}")
    else:
        print("Registries consistent: no findings.")
    return 0  # SOFT findings never fail the run (POL-034)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/validators/test_validate_registries.py -v`
Expected: 4 passed.

- [ ] **Step 5: Run it against the real repo and record the baseline**

Run: `python QC/validation/validate_registries.py`
Expected: SOFT findings for the known legacy drift (the Rukai/Seediq
conversion-table dialect names at minimum). Paste the summary counts into
the commit message body — that is the shrink-over-time baseline.

- [ ] **Step 6: Commit**

```bash
git add QC/validation/validate_registries.py tests/validators/test_validate_registries.py
git commit -m "feat: registry-consistency validator, SOFT findings (POL-034)"
```

---

### Task 5: Manual-edits round-trip and pipeline-survival tests

**Files:**
- Test: `tests/cleaners/test_manual_edits_survival.py`

**Interfaces:**
- Consumes: `run_qc_script`, `REPO_ROOT` from `tests/_helpers.py` (Task 2); existing scripts `QC/utilities/capture_manual_edits.py`, `QC/cleaning/apply_manual_edits.py` (CLI flags: consult each script's `--help` in Step 1 and transcribe the exact flags into the test constants — the suite already invokes them in `tests/cleaners/test_apply_manual_edits.py`; reuse its invocation constants if present rather than duplicating).
- Produces: nothing downstream.

- [ ] **Step 1: Read the existing harness**

Read `tests/cleaners/test_apply_manual_edits.py` and reuse its fixture-
building helpers/constants for corpus layout and script invocation. The new
file adds the two missing properties, not a parallel harness.

- [ ] **Step 2: Write the tests**

```python
"""Manual-edits guarantees the per-script tests do not cover.

1. Survival: an applied hand edit is still present after clean_xml and
   standardize run (the pipeline order puts apply_manual_edits FIRST;
   nothing later may undo the edit).
2. Original-tier scope: a hand edit to the original FORM survives, and
   the standard FORM regenerated afterwards reflects it (POL-002: the
   standard tier is derived from the original, so editing the original
   is the ONLY durable way to change the standard).
"""
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from tests._helpers import REPO_ROOT, run_qc_script

FIXTURES = REPO_ROOT / "tests" / "fixtures"


def _corpus_with_edit(tmp_path: Path) -> Path:
    """A corpus whose manual_edits.xml rewrites S1's original FORM."""
    corpus = tmp_path / "corpus"
    (corpus / "XML").mkdir(parents=True)
    (corpus / "CodeAndDocs").mkdir()
    shutil.copy(FIXTURES / "rerun_puyuma_l_to_ll.xml",
                corpus / "XML" / "rerun_puyuma_l_to_ll.xml")
    # Upsert record: same S id, corrected original text ("talal" ->
    # "talral"), standard/PHON stripped per the manual-edits contract.
    # Schema per QC/cleaning/manual_edits_common.py: FILE/@path is
    # relative to the corpora_path (the XML root), and an <S> child with
    # a matching id is an upsert (replace-by-id).
    (corpus / "CodeAndDocs" / "manual_edits.xml").write_text(
        """<?xml version="1.0" ?>
<MANUAL_EDITS>
    <FILE path="rerun_puyuma_l_to_ll.xml">
        <S id="S2">
            <FORM kindOf="original">talral na l</FORM>
            <TRANSL xml:lang="eng">plain sentence</TRANSL>
        </S>
    </FILE>
</MANUAL_EDITS>
""", encoding="utf-8")
    return corpus


def _s2_form(corpus: Path, kind: str) -> str:
    root = ET.parse(corpus / "XML" / "rerun_puyuma_l_to_ll.xml").getroot()
    for s in root.findall("S"):
        if s.get("id") == "S2":
            return s.find(f"FORM[@kindOf='{kind}']").text
    raise AssertionError("S2 missing")


def test_edit_survives_full_pipeline(tmp_path):
    corpus = _corpus_with_edit(tmp_path)
    for script, args in [
        # apply_manual_edits takes the XML root; it resolves the manual
        # file as <root>/../CodeAndDocs/manual_edits.xml (see
        # manual_edits_common.default_manual_file).
        ("QC/cleaning/apply_manual_edits.py",
         ["--corpora_path", str(corpus / "XML")]),
        ("QC/cleaning/clean_xml.py", ["--corpora_path", str(corpus)]),
        ("QC/utilities/standardize.py",
         ["--tsv_path", str(FIXTURES / "rerun_l_to_ll_table.tsv"),
          "--corpora_path", str(corpus)]),
    ]:
        proc = run_qc_script(script, args)
        assert proc.returncode == 0, f"{script}: {proc.stderr}"
    assert _s2_form(corpus, "original") == "talral na l"
    assert "tallrall" in _s2_form(corpus, "standard"), (
        "standard tier must be regenerated FROM the edited original")


def test_reapply_is_idempotent(tmp_path):
    corpus = _corpus_with_edit(tmp_path)
    script = "QC/cleaning/apply_manual_edits.py"
    argv = ["--corpora_path", str(corpus / "XML")]
    assert run_qc_script(script, argv).returncode == 0
    before = (corpus / "XML" / "rerun_puyuma_l_to_ll.xml").read_bytes()
    assert run_qc_script(script, argv).returncode == 0
    after = (corpus / "XML" / "rerun_puyuma_l_to_ll.xml").read_bytes()
    assert before == after
```

Record schema and CLI verified against `QC/cleaning/manual_edits_common.py`
2026-08-10: `<MANUAL_EDITS><FILE path="…relative to XML root…"><S id=…>`
(an `<S>` matching an existing id is an upsert; `action="delete"` deletes;
`after=` is a placement hint), and `apply_manual_edits.py --corpora_path`
takes the **XML root**, resolving the manual file as its
`../CodeAndDocs/manual_edits.xml` sibling. Cross-check invocation details
against `tests/cleaners/test_apply_manual_edits.py` in Step 1 anyway; the
two assertions (survival through the pipeline; reapply idempotence) are
the point.

- [ ] **Step 3: Run, fix schema mismatches, re-run**

Run: `pytest tests/cleaners/test_manual_edits_survival.py -v`
Expected after schema correction: 2 passed. A genuine failure of
`test_edit_survives_full_pipeline` (edit clobbered) or
`test_reapply_is_idempotent` is a real bug — stop and report it, do not
adjust the assertion.

- [ ] **Step 4: Commit**

```bash
git add tests/cleaners/test_manual_edits_survival.py
git commit -m "test: manual edits survive the pipeline and reapply cleanly"
```

---

### Task 6: standardize_warnings contract test + audit-regression fixture convention

**Files:**
- Test: `tests/utilities/test_standardize_warnings_contract.py`
- Create: `tests/fixtures/audit_regressions/README.md`
- Modify: `tests/README.md` (add the convention paragraph)

**Interfaces:**
- Consumes: `run_qc_script` (Task 2); `standardize.py` C012/c022 behavior; Task 1's rewrite semantics.
- Produces: the `tests/fixtures/audit_regressions/` directory that future audit remediations drop fixtures into.

- [ ] **Step 1: Write the warnings contract test**

```python
"""standardize_warnings.csv contract: schema, content, no duplication.

The CSV is the operator's triage artifact for C012 (hyphen removed from a
morpheme-segmented standard FORM) and c022 ('*' in standard FORM); skills
read it into run summaries, so its shape is a contract.
"""
import csv
import shutil
from pathlib import Path

from tests._helpers import REPO_ROOT, run_qc_script

FIXTURES = REPO_ROOT / "tests" / "fixtures"
COLUMNS = ["rule_id", "file", "s_id", "character", "position"]


def _corpus(tmp_path: Path) -> Path:
    corpus = tmp_path / "corpus"
    (corpus / "XML").mkdir(parents=True)
    # Reuse the segmented fixture; inject a '*' so c022 fires alongside
    # C012's hyphen handling (S1 has M descendants -> C012 eligible).
    text = (FIXTURES / "rerun_puyuma_l_to_ll.xml").read_text(encoding="utf-8")
    text = text.replace("talal na l", "talal *na-l")
    (corpus / "XML" / "warnings_probe.xml").write_text(text, encoding="utf-8")
    return corpus


def _rows(corpus: Path) -> list[dict]:
    with open(corpus / "standardize_warnings.csv", newline="",
              encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_schema_and_single_reporting(tmp_path):
    corpus = _corpus(tmp_path)
    args = ["--tsv_path", str(FIXTURES / "rerun_l_to_ll_table.tsv"),
            "--corpora_path", str(corpus)]
    assert run_qc_script("QC/utilities/standardize.py", args).returncode == 0
    rows = _rows(corpus)
    assert rows, "expected at least a c022 row for the injected '*'"
    assert list(rows[0].keys()) == COLUMNS
    c022 = [r for r in rows if r["rule_id"] == "c022"]
    assert len(c022) == len({(r["s_id"], r["position"]) for r in c022}), (
        "same occurrence reported twice in one run")

    # Task 1 contract: a second run REPLACES the CSV, count unchanged.
    assert run_qc_script("QC/utilities/standardize.py", args).returncode == 0
    assert len(_rows(corpus)) == len(rows)
```

- [ ] **Step 2: Run it**

Run: `pytest tests/utilities/test_standardize_warnings_contract.py -v`
Expected: 1 passed (depends on Task 1; if the second-run count doubles,
Task 1 regressed).

- [ ] **Step 3: Create the audit-regression convention**

`tests/fixtures/audit_regressions/README.md`:

```markdown
# Audit-finding regression fixtures

Every audit finding that led to a FormosanBank *code* fix gets a minimal
fixture here plus one test, named after the finding:

    <yyyy-mm>-<corpus-slug>-<finding-slug>.xml
    e.g. 2026-08-ntu-rukai-starred-parens.xml

Convention (also stated in the audit-dev-repo / audit-gloss-scrape
skills): the audit's remediation is not complete until the fixture and
its test exist. Fixtures stay minimal — one TEXT, only the elements the
finding needs. Findings fixed in a *dev repo's* build scripts (not in
FormosanBank code) do not belong here; they belong in that repo's tests.
```

Append to `tests/README.md`:

```markdown
## Audit-regression fixtures

`tests/fixtures/audit_regressions/` holds minimal reproductions of audit
findings whose fix landed in FormosanBank code — see the README there.
An audit remediation is complete when its fixture and test exist.
```

- [ ] **Step 4: Commit**

```bash
git add tests/utilities/test_standardize_warnings_contract.py tests/fixtures/audit_regressions/README.md tests/README.md
git commit -m "test: standardize_warnings contract; audit-regression fixture convention"
```

---

## Self-review notes

- **Spec coverage:** proposals 1.1 (Task 3), 1.2-as-reframed (Task 2 + findings section), 1.3 with the 2026-08-10 SOFT ruling (Task 4), 1.4 (Task 5), 1.5 (Task 6 step 3), 1.6 (Task 6 step 1), plus the warnings-append bug the investigation surfaced (Task 1). Deliberately NOT planned: a real-corpus smoke test (published corpora drift; the fixture suite covers the rule surface).
- **Known unknowns, flagged inline rather than hidden:** Task 5's manual-edits record schema and CLI flags must be transcribed from the existing test file before running; Task 3's per-assertion failures are findings to report, not tests to silently adjust.
- **Type consistency:** `run_qc_script`/`snapshot_tree`/`REPO_ROOT` are defined once (Task 2) and consumed by Tasks 3, 5, 6 with the same signatures. Rule IDs V150–V153 appear only in Task 4 and match `TITLES`.
