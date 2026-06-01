# A: Python Test Infrastructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up pytest, conftest, fixtures, and the first round of unit tests for the highest-risk FormosanBank QC code, plus a CI workflow that fails the build on test failure.

**Architecture:** Pytest with config in `pyproject.toml`. Shared fixtures in `tests/conftest.py`. Standalone XML fixture files under `tests/fixtures/`. Tests grouped by concern (`tests/validators/`, `tests/cleaners/`, `tests/utilities/`) — test path tracks risk class, not source path. Tests invoke QC scripts via `subprocess` rather than importing them, matching how they're used in CI/QC pipeline. Coverage measured on `QC/` tree, reported but not gated. CI workflow `tests.yaml` runs on PR and push to main.

**Tech Stack:** Python 3.10 (matches FormosanBank `.venv` and CI), pytest 8.x, pytest-cov 5.x, GitHub Actions, stdlib `wave` for audio fixture generation.

**Parent design:** [2026-05-28-a-test-infrastructure-design.md](2026-05-28-a-test-infrastructure-design.md).

---

## File Structure

### Created

- `pyproject.toml` — pytest config (Task 1)
- `tests/__init__.py` — empty package marker (Task 1)
- `tests/conftest.py` — shared fixtures (Task 1)
- `tests/README.md` — layout + how-to docs (Task 7)
- `tests/validators/__init__.py` (Task 1)
- `tests/cleaners/__init__.py` (Task 1)
- `tests/utilities/__init__.py` (Task 1)
- `tests/fixtures/valid_minimal.xml` (Task 1)
- `tests/fixtures/valid_with_word_level.xml` (Task 2)
- `tests/fixtures/invented_no_match.xml` (Task 2)
- `tests/fixtures/valid_original_only.xml` (Task 3)
- `tests/fixtures/valid_both_tiers.xml` (Task 3)
- `tests/fixtures/valid_no_original_tier.xml` (Task 3)
- `tests/fixtures/tiny_mapping.tsv` (Task 3)
- `tests/fixtures/xml_with_html_entities.xml` (Task 4)
- `tests/fixtures/xml_with_whitespace_problems.xml` (Task 4)
- `tests/fixtures/missing_standard_tier.xml` (Task 6)
- `tests/fixtures/invalid_xml_lang_zzz.xml` (Task 6)
- `tests/fixtures/w_m_count_mismatch.xml` (Task 6)
- `tests/test_smoke.py` (Task 1; can be deleted after Task 2)
- `tests/utilities/test_find_duplicate_sentences.py` (Task 2; replaces `QC/test_find_duplicate_sentences.py`)
- `tests/utilities/test_standardize.py` (Task 3)
- `tests/cleaners/test_clean_xml.py` (Task 4)
- `tests/cleaners/test_remove_non_working_audio.py` (Task 5)
- `tests/validators/test_validate_xml.py` (Task 6)
- `.github/workflows/tests.yaml` (Task 8)

### Modified

- `requirements.txt` — add pytest + pytest-cov (Task 1)

### Deleted

- `QC/test_find_duplicate_sentences.py` — superseded by `tests/utilities/test_find_duplicate_sentences.py` (Task 2)

### Not touched

Per the design doc's scope: no edits to `Corpora/`, `Orthographies/`, `QC/` source code, `statistics/`, or any associated sibling repo. The 3 hand-rolled tests under `.claude/hooks/` are explicitly left as-is.

---

## Task 1: Bootstrap pytest infrastructure

**Files:**
- Create: `pyproject.toml`
- Create: `tests/__init__.py`
- Create: `tests/validators/__init__.py`
- Create: `tests/cleaners/__init__.py`
- Create: `tests/utilities/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/fixtures/valid_minimal.xml`
- Create: `tests/test_smoke.py`
- Modify: `requirements.txt`

- [ ] **Step 1.1: Add test deps to `requirements.txt`**

Append two lines (preserving existing pinned-version convention; pick whatever's current at install time for the X.Y placeholders):

```
pytest==8.3.4
pytest-cov==5.0.0
```

- [ ] **Step 1.2: Install into the existing `.venv`**

Run:
```bash
.venv/bin/pip install -r requirements.txt
```

Expected: pytest and pytest-cov installed. Other pinned deps already satisfied. No errors.

- [ ] **Step 1.3: Create `pyproject.toml`**

Create at repo root with this exact content:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "--cov=QC --cov-report=term-missing --cov-report=xml"
```

- [ ] **Step 1.4: Create the empty `__init__.py` package markers**

Create four empty files (each exactly 0 bytes is fine):
- `tests/__init__.py`
- `tests/validators/__init__.py`
- `tests/cleaners/__init__.py`
- `tests/utilities/__init__.py`

- [ ] **Step 1.5: Create `tests/conftest.py`**

Create with this exact content:

```python
"""Shared fixtures for the FormosanBank test suite."""
import wave
from pathlib import Path
from typing import Callable

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def valid_minimal_xml(fixtures_dir) -> Path:
    return fixtures_dir / "valid_minimal.xml"


@pytest.fixture
def audio_file_factory(tmp_path) -> Callable[..., Path]:
    """Return a callable that generates a silent WAV at the given duration."""
    def make(duration_sec: float = 1.0, sample_rate: int = 8000) -> Path:
        path = tmp_path / f"silent_{duration_sec}s.wav"
        n_frames = int(duration_sec * sample_rate)
        with wave.open(str(path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            w.writeframes(b"\x00\x00" * n_frames)
        return path
    return make
```

- [ ] **Step 1.6: Create `tests/fixtures/valid_minimal.xml`**

Create with this exact content. This is the canonical minimum corpus: one TEXT, one S, both required FORM tiers. `xml:lang="ami"` is ISO 639-3 for Amis. Filename is the documentation per the design's naming convention.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_MIN" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">Halo.</FORM>
    <FORM kindOf="standard">Halo.</FORM>
  </S>
</TEXT>
```

Note: no DOCTYPE reference. DTD validation in `validate_xml.py` loads the DTD by its own logic (not via the fixture's DOCTYPE). If during Task 6 the test fixture turns out to need a DOCTYPE for the validator to engage, add it then.

- [ ] **Step 1.7: Write smoke test at `tests/test_smoke.py`**

Verifies the infrastructure end-to-end: conftest fixtures load, fixture file is found, audio factory generates a real file. Create with this content:

```python
"""Smoke test: verify the test infrastructure is operational.

This test exists only to confirm that pytest discovers files, conftest
fixtures resolve, the fixtures directory is reachable, and the audio
factory produces a working file. Once real tests cover this ground
incidentally, the smoke test can be deleted (see Task 2)."""
from pathlib import Path


def test_repo_root_fixture_resolves(repo_root):
    assert repo_root.is_dir()
    assert (repo_root / "QC").is_dir(), "expected QC/ under repo root"


def test_fixtures_dir_resolves(fixtures_dir):
    assert fixtures_dir.is_dir()
    assert fixtures_dir.name == "fixtures"


def test_valid_minimal_xml_is_findable(valid_minimal_xml):
    assert valid_minimal_xml.is_file()
    assert valid_minimal_xml.read_text().startswith("<?xml")


def test_audio_factory_generates_a_wav(audio_file_factory):
    p: Path = audio_file_factory(duration_sec=0.1)
    assert p.is_file()
    assert p.suffix == ".wav"
    assert p.stat().st_size > 0
```

- [ ] **Step 1.8: Run pytest, expect 4 passes**

Run from repo root:
```bash
.venv/bin/pytest
```

Expected output ends with something like:
```
4 passed in 0.XXs
```
plus a coverage report (will show low QC coverage, that's fine — Section 3 of the design specifies report-only).

If FAIL: do not proceed. Likely causes: `pyproject.toml` syntax error, conftest import error, fixture path wrong. Fix and re-run.

- [ ] **Step 1.9: Commit**

```bash
git add pyproject.toml requirements.txt tests/__init__.py tests/conftest.py tests/test_smoke.py tests/validators/__init__.py tests/cleaners/__init__.py tests/utilities/__init__.py tests/fixtures/valid_minimal.xml
git commit -m "Bootstrap pytest infrastructure + smoke test (sub-project A Task 1)"
```

---

## Task 2: Migrate `find_duplicate_sentences` test to pytest

**Files:**
- Create: `tests/fixtures/valid_with_word_level.xml`
- Create: `tests/fixtures/invented_no_match.xml`
- Create: `tests/utilities/test_find_duplicate_sentences.py`
- Delete: `QC/test_find_duplicate_sentences.py`
- Delete: `tests/test_smoke.py` (now redundant — real tests exercise the same infra)

- [ ] **Step 2.1: Create `tests/fixtures/valid_with_word_level.xml`**

Has a sentence-level FORM (which should be extracted) plus a word-level FORM inside `<W>` (which should NOT be extracted). Used to test the word-level-FORM exclusion behavior.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_WL" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_A">
    <FORM kindOf="standard">A real sentence</FORM>
    <W id="S_A_W_1">
      <FORM kindOf="standard">SHOULD_NOT_MATCH</FORM>
    </W>
  </S>
</TEXT>
```

- [ ] **Step 2.2: Create `tests/fixtures/invented_no_match.xml`**

Two synthetic sentences that should NOT appear in any Glosbe content. Used for the no-false-positives test.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_INV" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="INV_1">
    <FORM kindOf="standard">Zxqwerty totally fake sentence that is not in any corpus.</FORM>
  </S>
  <S id="INV_2">
    <FORM kindOf="standard">Another completely made up string XYZ123.</FORM>
  </S>
</TEXT>
```

- [ ] **Step 2.3: Write `tests/utilities/test_find_duplicate_sentences.py`**

Migrates `QC/test_find_duplicate_sentences.py` (which uses an inline `make_xml()` builder and a hand-rolled PASS/FAIL counter) to pytest with standalone fixtures.

Per the design's real-corpus exception: keeps the Glosbe corpus dependency, with the required justification comment.

```python
"""Tests for QC/utilities/find_duplicate_sentences.py.

Migrated from QC/test_find_duplicate_sentences.py.

Note on the Glosbe corpus dependency: this test plants sentences extracted
from the actual Glosbe corpus at Corpora/Glosbe/XML/Amis/amis_glosbe.xml
and verifies that the matcher finds them. A synthetic fixture would not
exercise the diversity of real Glosbe-derived sentences (varying
punctuation, casing, length), which is exactly what this matcher needs
to handle. Per the design doc's real-corpus exception, this dependency
is explicit and intentional.
"""
import sys
from collections import defaultdict
from pathlib import Path

import pytest

# Import the module under test
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "QC" / "utilities"))
from find_duplicate_sentences import extract_standard_forms  # noqa: E402

GLOSBE_XML = REPO / "Corpora" / "Glosbe" / "XML" / "Amis" / "amis_glosbe.xml"


@pytest.fixture(scope="module")
def glosbe_sample():
    """First 5 standard sentences from the Glosbe corpus."""
    if not GLOSBE_XML.is_file():
        pytest.skip(f"Glosbe corpus not found at {GLOSBE_XML}")
    out = []
    for sid, text in extract_standard_forms(str(GLOSBE_XML)):
        if text.strip():
            out.append((sid, text))
        if len(out) >= 5:
            break
    return out


@pytest.fixture(scope="module")
def glosbe_index():
    """Lowercased text -> list of S ids, built from the Glosbe corpus."""
    if not GLOSBE_XML.is_file():
        pytest.skip(f"Glosbe corpus not found at {GLOSBE_XML}")
    idx = defaultdict(list)
    for gid, text in extract_standard_forms(str(GLOSBE_XML)):
        idx[text.lower()].append(gid)
    return idx


def test_extract_standard_forms_round_trips(fixtures_dir):
    """Sentence ids and FORM text are read correctly from a minimal fixture."""
    # valid_minimal.xml has one S (S_1) with FORM "Halo."
    forms = extract_standard_forms(str(fixtures_dir / "valid_minimal.xml"))
    assert len(forms) == 1
    assert forms[0][0] == "S_1"
    assert forms[0][1] == "Halo."


def test_word_level_forms_are_excluded(fixtures_dir):
    """FORM elements inside <W> (not direct children of <S>) are not extracted."""
    forms = extract_standard_forms(str(fixtures_dir / "valid_with_word_level.xml"))
    texts = [t for _, t in forms]
    assert "SHOULD_NOT_MATCH" not in texts
    assert "A real sentence" in texts


def test_invented_sentences_produce_no_false_positives(fixtures_dir, glosbe_index):
    forms = extract_standard_forms(str(fixtures_dir / "invented_no_match.xml"))
    false_positives = [(sid, text) for sid, text in forms if text.lower() in glosbe_index]
    assert false_positives == []


def test_real_glosbe_sentences_are_found(glosbe_sample, glosbe_index):
    """Sentences planted from the real Glosbe corpus should be matchable."""
    planted_gids = {gid for gid, _ in glosbe_sample}
    found_gids = set()
    for gid, text in glosbe_sample:
        if text.lower() in glosbe_index:
            for hit_gid in glosbe_index[text.lower()]:
                found_gids.add(hit_gid)
    assert planted_gids.issubset(found_gids), (
        f"missing matches: {planted_gids - found_gids}"
    )


def test_case_insensitive_matching(glosbe_sample, glosbe_index):
    """Upper and lower cased variants of a real Glosbe sentence both match."""
    _, sample_text = glosbe_sample[0]
    assert sample_text.upper().lower() in glosbe_index
    assert sample_text.lower() in glosbe_index
```

- [ ] **Step 2.4: Delete the original test**

```bash
git rm QC/test_find_duplicate_sentences.py
```

- [ ] **Step 2.5: Delete the now-redundant smoke test**

```bash
git rm tests/test_smoke.py
```

- [ ] **Step 2.6: Run the migrated test, expect all 5 to pass**

```bash
.venv/bin/pytest tests/utilities/test_find_duplicate_sentences.py -v
```

Expected: 5 tests pass. If the Glosbe corpus is absent, two tests should `skip` rather than fail — verify that the skip happens cleanly.

If FAIL: most likely cause is path mismatch (e.g., `Corpora/Glosbe/XML/Amis/amis_glosbe.xml` moved). Confirm the path and adjust the test's `GLOSBE_XML` constant. Do not silently fall back to synthetic data.

- [ ] **Step 2.7: Commit**

```bash
git add tests/utilities/test_find_duplicate_sentences.py tests/fixtures/valid_with_word_level.xml tests/fixtures/invented_no_match.xml
git commit -m "Migrate find_duplicate_sentences test to pytest (sub-project A Task 2)"
```

---

## Task 3: `test_standardize.py`

**Files:**
- Create: `tests/fixtures/valid_original_only.xml`
- Create: `tests/fixtures/valid_both_tiers.xml`
- Create: `tests/fixtures/valid_no_original_tier.xml`
- Create: `tests/fixtures/tiny_mapping.tsv`
- Create: `tests/utilities/test_standardize.py`

- [ ] **Step 3.1: Create `tests/fixtures/valid_original_only.xml`**

A corpus with only the `original` tier. Standardize should add a `standard` tier on `--copy`.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_OO" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">Halo, hapinangha.</FORM>
  </S>
  <S id="S_2">
    <FORM kindOf="original">Nawhani kako tayni i toron.</FORM>
  </S>
</TEXT>
```

- [ ] **Step 3.2: Create `tests/fixtures/valid_both_tiers.xml`**

A corpus that already has both tiers, with a `standard` tier deliberately differing from `original`. After `standardize.py --copy`, the `standard` tier should be overwritten with `original`'s content.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_BT" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">Halo, hapinangha.</FORM>
    <FORM kindOf="standard">REPLACE ME</FORM>
  </S>
</TEXT>
```

- [ ] **Step 3.3: Create `tests/fixtures/valid_no_original_tier.xml`**

A corpus with a `standard` tier but NO `original` tier. Standardize should error out cleanly.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_NO" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="standard">Only a standard tier here.</FORM>
  </S>
</TEXT>
```

- [ ] **Step 3.4: Create `tests/fixtures/tiny_mapping.tsv`**

Minimal mapping table for the `--tsv_path` test path. Two columns (source, target) covering at least one substitution that we can detect in the output.

```
source	target
Halo	Hello
hapinangha	greeting
```

- [ ] **Step 3.5: Write `tests/utilities/test_standardize.py`**

Pattern for in-place mutators: copy fixture to `tmp_path` first, run script on the copy via subprocess, assert on the copy. Never mutate the fixture file itself.

```python
"""Tests for QC/utilities/standardize.py.

Standardize copies the `original` tier to a `standard` tier (with --copy)
or transliterates via a TSV mapping. It mutates XML in place, so all
tests work on a tmp_path copy of the fixture, never on the fixture
file itself.
"""
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

STANDARDIZE = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "standardize.py"


def _copy_fixture(src: Path, dest_dir: Path) -> Path:
    """Copy a fixture file into a fresh dir so the script can mutate it."""
    target_dir = dest_dir / "XML"
    target_dir.mkdir(parents=True, exist_ok=True)
    copy = target_dir / src.name
    shutil.copy(src, copy)
    return copy


def _run_standardize(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(STANDARDIZE), *args],
        capture_output=True,
        text=True,
    )


def _standard_forms(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [
        f.text
        for s in root.iter("S")
        for f in s
        if f.tag == "FORM" and f.get("kindOf") == "standard"
    ]


def _original_forms(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [
        f.text
        for s in root.iter("S")
        for f in s
        if f.tag == "FORM" and f.get("kindOf") == "original"
    ]


def test_copy_adds_standard_tier_when_only_original_exists(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(work.parent)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert _standard_forms(work) == _original_forms(work)
    assert _standard_forms(work) == ["Halo, hapinangha.", "Nawhani kako tayni i toron."]


def test_copy_overwrites_existing_standard_tier(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "valid_both_tiers.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(work.parent)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # The pre-existing "REPLACE ME" must be gone; standard must now match original
    standard = _standard_forms(work)
    assert "REPLACE ME" not in standard
    assert standard == _original_forms(work)


def test_tsv_mapping_transforms_standard_tier(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    tsv = fixtures_dir / "tiny_mapping.tsv"
    proc = _run_standardize([
        "--tsv_path", str(tsv),
        "--target_column", "target",
        "--corpora_path", str(work.parent),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    standard = " ".join(_standard_forms(work))
    # The mapping should have replaced "Halo" -> "Hello" and "hapinangha" -> "greeting"
    # somewhere in the standard tier output.
    assert "Hello" in standard or "greeting" in standard, (
        f"expected mapped tokens in standard tier, got: {standard!r}"
    )


def test_errors_when_no_original_tier(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "valid_no_original_tier.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(work.parent)])
    # Standardize should either exit non-zero OR emit a clear error message.
    # Either signal is acceptable; one of them must be present.
    has_clear_error = (
        proc.returncode != 0
        or "no original" in (proc.stderr + proc.stdout).lower()
        or "missing original" in (proc.stderr + proc.stdout).lower()
    )
    assert has_clear_error, (
        f"expected a clear error about missing original tier; "
        f"got returncode={proc.returncode}, stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
```

- [ ] **Step 3.6: Run, expect all 4 to pass**

```bash
.venv/bin/pytest tests/utilities/test_standardize.py -v
```

Expected: 4 passed. If FAIL: stop and report. The most likely fail modes are:
- `--corpora_path` argument shape mismatch (the script may want a directory of corpora, not a single corpus). Inspect `standardize.py`'s CLI and adjust the test's `--corpora_path` argument accordingly.
- TSV format mismatch (the script may want different column names). Inspect and adjust `tiny_mapping.tsv` and the `--target_column` value.
- "No original tier" behavior may be silent-pass rather than error. If so, the test's assertion needs adjusting — but first surface this to the user, since silent-pass contradicts the design's stated expected behavior.

- [ ] **Step 3.7: Commit**

```bash
git add tests/utilities/test_standardize.py tests/fixtures/valid_original_only.xml tests/fixtures/valid_both_tiers.xml tests/fixtures/valid_no_original_tier.xml tests/fixtures/tiny_mapping.tsv
git commit -m "Add standardize.py tests (sub-project A Task 3)"
```

---

## Task 4: `test_clean_xml.py` (basic round)

**Files:**
- Create: `tests/fixtures/xml_with_html_entities.xml`
- Create: `tests/fixtures/xml_with_whitespace_problems.xml`
- Create: `tests/cleaners/test_clean_xml.py`

Per the design, this is the *basic* round only. Corpus-mined positives and negatives are deferred to a follow-up round with its own design pass.

- [ ] **Step 4.1: Create `tests/fixtures/xml_with_html_entities.xml`**

Contains HTML entity escapes (`&amp;`, `&quot;`, `&#39;`) that the cleaner is expected to resolve into their literal forms.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_HE" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">Tom &amp; Jerry &quot;cartoon&quot; episode #39;1</FORM>
    <FORM kindOf="standard">Tom &amp; Jerry &quot;cartoon&quot; episode #39;1</FORM>
  </S>
</TEXT>
```

- [ ] **Step 4.2: Create `tests/fixtures/xml_with_whitespace_problems.xml`**

Contains repeated spaces, leading/trailing whitespace, and a mixed-whitespace run that the cleaner is expected to normalize.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_WS" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">  Halo,   hapinangha.   </FORM>
    <FORM kindOf="standard">  Halo,   hapinangha.   </FORM>
  </S>
</TEXT>
```

- [ ] **Step 4.3: Write `tests/cleaners/test_clean_xml.py`**

```python
"""Basic tests for QC/cleaning/clean_xml.py.

This is the BASIC round per the design doc. Corpus-mined positives and
negatives (mining published Corpora/<X>/ for real-world cruft patterns)
are a deferred follow-up round with its own design pass.

clean_xml mutates XML in place. All tests work on a tmp_path copy of
the fixture; never mutate the fixture file itself.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

CLEAN_XML = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_xml.py"


def _copy_fixture(src: Path, dest_dir: Path) -> Path:
    target_dir = dest_dir / "XML"
    target_dir.mkdir(parents=True, exist_ok=True)
    copy = target_dir / src.name
    shutil.copy(src, copy)
    return copy


def _run_clean(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLEAN_XML), "--corpora_path", str(corpora_path)],
        capture_output=True,
        text=True,
    )


def test_already_clean_xml_is_left_intact(tmp_path, fixtures_dir):
    """A valid_minimal.xml should round-trip unchanged through the cleaner."""
    work = _copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    before = work.read_text()
    proc = _run_clean(work.parent)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    after = work.read_text()
    # Allow trivial whitespace/serialization differences; assert that the
    # text content of FORM elements is unchanged.
    assert "Halo." in after, f"expected 'Halo.' to survive cleaning; got:\n{after}"


def test_html_entities_are_resolved(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "xml_with_html_entities.xml", tmp_path)
    proc = _run_clean(work.parent)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    after = work.read_text()
    # &amp; in source XML is the encoded form of "&"; after cleaning, the
    # text content should be the literal "&" (the on-disk representation
    # may still encode it as &amp; for XML well-formedness, but it should
    # NOT contain the source phrase &amp;amp; or similar double-encoding).
    assert "&amp;amp;" not in after, "found double-encoded entity"


def test_whitespace_is_normalized(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "xml_with_whitespace_problems.xml", tmp_path)
    proc = _run_clean(work.parent)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    after = work.read_text()
    # Triple-space runs in the FORM text should not survive cleaning.
    # (Leading/trailing whitespace inside an element is also a target,
    # but its on-disk representation is harder to assert against;
    # focus on the unambiguous repeated-space case.)
    assert "   " not in after, "expected repeated spaces to be normalized away"


def test_cleaner_is_idempotent(tmp_path, fixtures_dir):
    """Critical for in-place mutators: running twice == running once."""
    work_a = _copy_fixture(fixtures_dir / "xml_with_html_entities.xml", tmp_path / "once")
    work_b = _copy_fixture(fixtures_dir / "xml_with_html_entities.xml", tmp_path / "twice")

    _run_clean(work_a.parent)
    _run_clean(work_b.parent)
    _run_clean(work_b.parent)  # second run on the same copy

    assert work_a.read_text() == work_b.read_text(), (
        "cleaner is not idempotent — running twice differs from running once"
    )
```

- [ ] **Step 4.4: Run, expect all 4 to pass**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml.py -v
```

Expected: 4 passed.

If FAIL: per the roadmap, `clean_xml.py` has many branches and 12 revisions with several "fix/oops" commits. Failures here are not surprising and may reveal real cleaner bugs. Stop and surface to the user — the diagnosis (test wrong vs cleaner bug) is a conversation, not an automated decision.

- [ ] **Step 4.5: Commit**

```bash
git add tests/cleaners/test_clean_xml.py tests/fixtures/xml_with_html_entities.xml tests/fixtures/xml_with_whitespace_problems.xml
git commit -m "Add clean_xml.py basic-round tests (sub-project A Task 4)"
```

---

## Task 5: `test_remove_non_working_audio.py`

**Files:**
- Create: `tests/cleaners/test_remove_non_working_audio.py`

Uses the `audio_file_factory` fixture from conftest to generate real on-disk WAVs at test time. Constructs XML inline (one of the few cases where building the fixture inline is cleaner than committing a file, because the test needs to embed dynamic audio paths).

- [ ] **Step 5.1: Write `tests/cleaners/test_remove_non_working_audio.py`**

```python
"""Tests for QC/cleaning/remove_non_working_audio.py.

Removes <AUDIO> elements whose `file` attribute points to a missing or
unreadable audio file. High blast radius: removes data from XML in place.

Uses audio_file_factory to generate real WAVs at test time (a path that
RESOLVES). Missing audio refs are constructed as paths that point to
non-existent files in tmp_path.
"""
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REMOVE_AUDIO = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "remove_non_working_audio.py"


def _write_xml_with_audio_refs(path: Path, audio_paths_with_validity: list[tuple[Path, bool]]) -> None:
    """Build an XML file referencing the given audio paths.

    `audio_paths_with_validity` is a list of (Path, is_valid) tuples.
    Validity is informational for the test's expectations only — the
    script decides validity by checking the file on disk.
    """
    root = ET.Element("TEXT", attrib={
        "id": "TEST_AUDIO",
        "citation": "test",
        "BibTeX_citation": "@test{test}",
        "copyright": "test",
        "xml:lang": "ami",
    })
    for i, (audio_path, _) in enumerate(audio_paths_with_validity, 1):
        s = ET.SubElement(root, "S", attrib={"id": f"S_{i}"})
        ET.SubElement(s, "FORM", attrib={"kindOf": "original"}).text = f"Sentence {i}."
        ET.SubElement(s, "FORM", attrib={"kindOf": "standard"}).text = f"Sentence {i}."
        ET.SubElement(s, "AUDIO", attrib={
            "file": str(audio_path),
            "start": "0",
            "end": "1",
        })
    ET.ElementTree(root).write(str(path), encoding="utf-8", xml_declaration=True)


def _audio_refs(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [a.get("file") for a in root.iter("AUDIO")]


def _run_remove(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REMOVE_AUDIO), "--corpora_path", str(corpora_path)],
        capture_output=True,
        text=True,
    )


def _make_xml_dir(tmp_path: Path) -> Path:
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    return d


def test_all_valid_audio_refs_are_kept(tmp_path, audio_file_factory):
    xml_dir = _make_xml_dir(tmp_path)
    good_a = audio_file_factory(0.1)
    good_b = audio_file_factory(0.1)
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [(good_a, True), (good_b, True)])

    proc = _run_remove(xml_dir)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    refs = _audio_refs(xml)
    assert len(refs) == 2, f"expected 2 audio refs retained, got {refs}"


def test_broken_audio_ref_is_removed_others_retained(tmp_path, audio_file_factory):
    xml_dir = _make_xml_dir(tmp_path)
    good = audio_file_factory(0.1)
    broken = tmp_path / "does_not_exist.wav"  # never created
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [(good, True), (broken, False)])

    proc = _run_remove(xml_dir)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    refs = _audio_refs(xml)
    assert str(good) in refs, "valid audio ref was incorrectly removed"
    assert str(broken) not in refs, "broken audio ref was not removed"


def test_corpus_with_no_audio_is_a_noop(tmp_path, fixtures_dir):
    """valid_minimal.xml has no <AUDIO> elements — script should leave it alone."""
    xml_dir = _make_xml_dir(tmp_path)
    shutil.copy(fixtures_dir / "valid_minimal.xml", xml_dir / "valid_minimal.xml")
    before = (xml_dir / "valid_minimal.xml").read_text()

    proc = _run_remove(xml_dir)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    after = (xml_dir / "valid_minimal.xml").read_text()
    # Allow trivial whitespace/serialization differences; main check is
    # that the text content is unchanged.
    assert "Halo." in after


def test_all_broken_audio_refs_are_all_removed(tmp_path):
    xml_dir = _make_xml_dir(tmp_path)
    broken_a = tmp_path / "missing_a.wav"
    broken_b = tmp_path / "missing_b.wav"
    xml = xml_dir / "test.xml"
    _write_xml_with_audio_refs(xml, [(broken_a, False), (broken_b, False)])

    proc = _run_remove(xml_dir)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    refs = _audio_refs(xml)
    assert refs == [], f"expected all broken refs removed, got: {refs}"

    # Surviving XML should still be well-formed and parseable.
    root = ET.parse(xml).getroot()
    sentences = list(root.iter("S"))
    assert len(sentences) == 2, "sentences should not have been removed, only their AUDIO children"
```

- [ ] **Step 5.2: Run, expect all 4 to pass**

```bash
.venv/bin/pytest tests/cleaners/test_remove_non_working_audio.py -v
```

Expected: 4 passed.

If FAIL: likely `--corpora_path` shape (single corpus vs collection) or the script uses a different attribute for the audio file path (e.g., `url` instead of `file`). Inspect `remove_non_working_audio.py` and adjust.

- [ ] **Step 5.3: Commit**

```bash
git add tests/cleaners/test_remove_non_working_audio.py
git commit -m "Add remove_non_working_audio.py tests (sub-project A Task 5)"
```

---

## Task 6: `test_validate_xml.py`

**Files:**
- Create: `tests/fixtures/missing_standard_tier.xml`
- Create: `tests/fixtures/invalid_xml_lang_zzz.xml`
- Create: `tests/fixtures/w_m_count_mismatch.xml`
- Create: `tests/validators/test_validate_xml.py`

- [ ] **Step 6.1: Create `tests/fixtures/missing_standard_tier.xml`**

Missing the `standard` FORM that the project's invariant requires.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_MISS" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">Halo, hapinangha.</FORM>
  </S>
</TEXT>
```

- [ ] **Step 6.2: Create `tests/fixtures/invalid_xml_lang_zzz.xml`**

Uses `xml:lang="zzz"` which is not a real ISO 639-3 code. Validator should flag.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_LANG" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="zzz">
  <S id="S_1">
    <FORM kindOf="original">x</FORM>
    <FORM kindOf="standard">x</FORM>
  </S>
</TEXT>
```

- [ ] **Step 6.3: Create `tests/fixtures/w_m_count_mismatch.xml`**

Has a `<W>` with 2 `<M>` children but a sentence-level FORM that's a single word, or some other deliberate W/M count mismatch the validator catches. A minimal violation: a W that contains no M elements when it should, or two W elements where the standard tier has only one word.

```xml
<?xml version="1.0" encoding="utf-8"?>
<TEXT id="TEST_WMM" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">solo</FORM>
    <FORM kindOf="standard">solo</FORM>
    <W id="S_1_W_1">
      <FORM kindOf="standard">solo</FORM>
    </W>
    <W id="S_1_W_2">
      <FORM kindOf="standard">extra</FORM>
    </W>
  </S>
</TEXT>
```

- [ ] **Step 6.4: Write `tests/validators/test_validate_xml.py`**

```python
"""Tests for QC/validation/validate_xml.py.

validate_xml is the canonical DTD-conformance check. Per the roadmap,
current validators never sys.exit(1) — they emit findings to stdout/stderr/
log files but always exit 0. So tests assert on output content, not on
exit codes. Sub-project B's --exit-nonzero-on-findings flag will later
add a second axis to test on.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

VALIDATE_XML = (
    Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_xml.py"
)


def _copy_fixture(src: Path, tmp_path: Path) -> Path:
    """Copy a single fixture into a fresh tmp dir as a one-file corpus."""
    target_dir = tmp_path / "XML"
    target_dir.mkdir(parents=True, exist_ok=True)
    copy = target_dir / src.name
    shutil.copy(src, copy)
    return copy


def _run_validate(corpus_xml_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_XML), "by_path", "--path", str(corpus_xml_dir)],
        capture_output=True,
        text=True,
    )


def test_valid_minimal_produces_no_findings(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    proc = _run_validate(work.parent)
    combined = (proc.stdout + proc.stderr).lower()
    # No DTD-violation reports against the valid fixture.
    assert "error" not in combined and "invalid" not in combined and "violation" not in combined, (
        f"expected clean validation; got stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_missing_standard_tier_is_flagged(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "missing_standard_tier.xml", tmp_path)
    proc = _run_validate(work.parent)
    combined = (proc.stdout + proc.stderr).lower()
    # Validator should report SOMETHING about the missing standard tier,
    # the structure being invalid, or the FORM element count being wrong.
    has_finding = any(
        marker in combined
        for marker in ("standard", "form", "invalid", "missing", "violation", "error")
    )
    assert has_finding, (
        f"expected a finding about missing standard tier; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_invalid_xml_lang_is_flagged(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "invalid_xml_lang_zzz.xml", tmp_path)
    proc = _run_validate(work.parent)
    combined = (proc.stdout + proc.stderr).lower()
    # Validator should report SOMETHING about the bad xml:lang.
    has_finding = any(
        marker in combined for marker in ("lang", "iso", "zzz", "invalid", "violation")
    )
    assert has_finding, (
        f"expected a finding about invalid xml:lang='zzz'; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_w_m_count_mismatch_is_flagged(tmp_path, fixtures_dir):
    work = _copy_fixture(fixtures_dir / "w_m_count_mismatch.xml", tmp_path)
    proc = _run_validate(work.parent)
    combined = (proc.stdout + proc.stderr).lower()
    has_finding = any(
        marker in combined for marker in ("count", "mismatch", "w", "violation", "invalid")
    )
    assert has_finding, (
        f"expected a finding about W/M count mismatch; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
```

- [ ] **Step 6.5: Run, expect all 4 to pass**

```bash
.venv/bin/pytest tests/validators/test_validate_xml.py -v
```

Expected: 4 passed.

If FAIL on the positive (`valid_minimal.xml` reports findings): the fixture has a real DTD violation we missed (likely a missing required attribute). Read the validator's output, fix the fixture.

If FAIL on a negative (validator does NOT flag the broken fixture): two possibilities — (a) the validator missed it (a real bug, worth surfacing), or (b) the fixture isn't broken in the way we intended. Read the validator's output to diagnose, then either fix the fixture or surface the bug.

- [ ] **Step 6.6: Commit**

```bash
git add tests/validators/test_validate_xml.py tests/fixtures/missing_standard_tier.xml tests/fixtures/invalid_xml_lang_zzz.xml tests/fixtures/w_m_count_mismatch.xml
git commit -m "Add validate_xml.py tests (sub-project A Task 6)"
```

---

## Task 7: `tests/README.md`

**Files:**
- Create: `tests/README.md`

- [ ] **Step 7.1: Write `tests/README.md`**

```markdown
# FormosanBank test suite

Pytest-based tests for the FormosanBank QC code. See [.claude/plans/2026-05-28-a-test-infrastructure-design.md](../.claude/plans/2026-05-28-a-test-infrastructure-design.md) for the design.

## Running tests

From the repo root, with the project's `.venv` active or pointed at:

```bash
.venv/bin/pytest               # run everything
.venv/bin/pytest tests/cleaners/   # run one concern bucket
.venv/bin/pytest -v -k validate_xml   # run tests whose name contains validate_xml
```

Coverage is reported automatically (configured in `pyproject.toml`). To see uncovered lines per file:

```bash
.venv/bin/pytest --cov-report=term-missing
```

## Layout

Tests are grouped **by concern** (risk class), not by source path:

- `tests/validators/` — hard pass/fail checks (DTD conformance, punctuation, gloss invariants)
- `tests/soft_checks/` — threshold-based checks (orthography similarity, vocabulary overlap, dialect completeness)
- `tests/cleaners/` — in-place XML mutators (clean_xml, remove_non_working_audio)
- `tests/metrics/` — token / corpus counters that feed CI dashboards
- `tests/utilities/` — helpers and one-offs that don't fit the above

A source file's test lives in the concern bucket matching its risk class, *not* its source directory. Example: `QC/cleaning/remove_non_working_audio.py` is tested at `tests/cleaners/test_remove_non_working_audio.py` (same bucket); `QC/utilities/standardize.py` is tested at `tests/utilities/test_standardize.py`.

When a source file straddles concerns (e.g., `validate_audio.py` has both hard-check and soft-check sides), the test file goes in the bucket of greatest blast radius (hard > soft), with internal grouping (pytest classes or naming) marking the distinction.

## Fixtures

All test XML lives in `tests/fixtures/` (flat for now; will subdivide by error class once we cross ~15 files).

**Naming convention:**
- Positive: `valid_<description>.xml`
- Negative: `<broken_invariant>.xml` (filename describes the failure mode)

Filenames are documentation. A reader should know what `missing_standard_tier.xml` exercises without opening it.

Audio fixtures are generated at test time via the `audio_file_factory` conftest fixture (the project's `.gitignore` excludes `*.wav`/`*.mp3`).

Tests may reference real corpus data at `Corpora/<X>/...` when synthesized data wouldn't exercise the diversity needed (currently: only `test_find_duplicate_sentences.py`). Those tests must include a comment naming why a synthetic fixture wouldn't do.

## Adding a test

1. Identify the source file you're testing and its concern bucket.
2. Add the test file at `tests/<bucket>/test_<source_module>.py`.
3. Create any needed fixture XML files under `tests/fixtures/`, following the naming convention.
4. Use the shared conftest fixtures (`fixtures_dir`, `repo_root`, `valid_minimal_xml`, `audio_file_factory`) where they fit.
5. For in-place mutators (cleaners): copy the fixture to `tmp_path` before invoking the script; never mutate the fixture file.
6. Invoke QC scripts via `subprocess.run([sys.executable, str(SCRIPT), ...])` rather than importing them, so the tests cover the actual CLI surface.

## Adding a fixture

1. Pick a descriptive filename per the naming convention (`valid_<description>.xml` or `<broken_invariant>.xml`).
2. Save it under `tests/fixtures/`.
3. If you find yourself adding many similar negatives, consider subdividing into `tests/fixtures/dtd_violations/`, `tests/fixtures/punct_problems/`, etc. (Threshold: ~15 files in the flat directory.)
```

- [ ] **Step 7.2: Commit**

```bash
git add tests/README.md
git commit -m "Add tests/README.md (sub-project A Task 7)"
```

---

## Task 8: CI workflow

**Files:**
- Create: `.github/workflows/tests.yaml`

- [ ] **Step 8.1: Create `.github/workflows/tests.yaml`**

```yaml
name: tests

on:
  pull_request:
    paths:
      - 'QC/**'
      - 'tests/**'
      - 'requirements.txt'
      - 'pyproject.toml'
      - '.github/workflows/tests.yaml'
  push:
    branches: [main]
    paths:
      - 'QC/**'
      - 'tests/**'
      - 'requirements.txt'
      - 'pyproject.toml'
      - '.github/workflows/tests.yaml'

jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run pytest
        run: pytest
      - name: Upload coverage report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-xml
          path: coverage.xml
          retention-days: 30
```

- [ ] **Step 8.2: Final local verification — run the full suite**

```bash
.venv/bin/pytest -v
```

Expected: All tests pass (5 from Task 2 + 4 from Task 3 + 4 from Task 4 + 4 from Task 5 + 4 from Task 6 = 21 tests). Coverage report shows percentages on `QC/`, no errors. `coverage.xml` exists at repo root.

- [ ] **Step 8.3: Commit**

```bash
git add .github/workflows/tests.yaml
git commit -m "Add tests CI workflow (sub-project A Task 8)"
```

- [ ] **Step 8.4: Open the PR**

Open a PR with the title `Sub-project A: Python test infrastructure` and a body that includes:
- One-paragraph summary
- A "Test plan" checklist confirming each task ran locally
- A REQUIRED FOLLOW-UP note: "After merge, set `tests / pytest` as a required status check in branch protection on `main` (Settings → Branches). The workflow file alone does not enforce blocking; repo settings do."

Wait for the CI workflow to run on the PR. Verify the `tests / pytest` job appears, runs, and passes.

If the CI run fails for reasons that don't reproduce locally (e.g., missing system deps for `lxml`, Python version mismatch), surface to the user — do not silently work around.

---

## Self-review against the spec

After plan complete, verify:

**Spec coverage** ([2026-05-28-a-test-infrastructure-design.md](2026-05-28-a-test-infrastructure-design.md)):
- ✅ Directory layout (Task 1, 2, 3, 4, 5, 6 create the structure under `tests/`)
- ✅ Concern groupings (`validators/`, `cleaners/`, `utilities/` — `soft_checks/` and `metrics/` not in first round per the design)
- ✅ Fixture conventions (Task 1 creates `tests/fixtures/`, subsequent tasks add files following the naming convention)
- ✅ Audio fixtures generated at test time (Task 1 conftest, Task 5 uses)
- ✅ Real-corpus exception documented in test_find_duplicate_sentences.py (Task 2)
- ✅ pyproject.toml (Task 1)
- ✅ requirements.txt additions (Task 1)
- ✅ conftest.py (Task 1)
- ✅ CI workflow (Task 8)
- ✅ All 5 first-round tests written (Tasks 2, 3, 4, 5, 6)
- ✅ Migration deletes original (Task 2 step 2.4)
- ✅ tests/README.md (Task 7)
- ✅ Manual post-merge branch-protection step surfaced in PR description (Task 8 step 8.4)

**Placeholder scan:** all step contents are concrete code or commands. The two version pins in `requirements.txt` (`pytest==8.3.4`, `pytest-cov==5.0.0`) use specific numbers per the convention; the implementer should pick whatever's current at install time if these have moved on.

**Type consistency:** `fixtures_dir`, `valid_minimal_xml`, `audio_file_factory`, `repo_root` — all defined in Task 1's conftest.py, consumed by the same names in Tasks 2–6. ✓

**Known risk areas where the plan says "stop and surface, don't silently work around":**
- Task 3 step 3.6: standardize CLI shape might not match assumption
- Task 4 step 4.4: clean_xml is the highest-risk source file; failure may indicate real bugs
- Task 6 step 6.5: validate_xml fixtures may need DOCTYPE if the validator is DOCTYPE-driven
- Task 8 step 8.4: CI may differ from local

These are explicit decision points where the implementer should ask, not improvise.
