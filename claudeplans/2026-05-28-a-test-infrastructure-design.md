# Sub-project A — Python Test Infrastructure

**Date:** 2026-05-28
**Status:** Design — approved through brainstorming, awaiting user spec review before implementation planning.
**Parent:** [2026-05-27-roadmap.md](2026-05-27-roadmap.md) item A.

## Goal

Establish a real test runner (`pytest`), shared fixtures, and the first round of unit tests for the highest-risk QC code, with discovery wired into CI so test failures block merge. Designed so the suite is easy to *grow* over time, not just stood up once.

## Scope

**In scope:**
- `pytest` infrastructure: `pyproject.toml`, `conftest.py`, `tests/` directory tree.
- Standalone XML fixture files under `tests/fixtures/`.
- 5 first-round tests (1 migration + 4 new), targeting the highest-risk QC files we can write tests for today.
- New CI workflow `.github/workflows/tests.yaml` that fails the build on test failure and uploads coverage as an artifact.
- A short `tests/README.md` explaining the layout and how to add tests.

**Not in scope (deferred, flagged in roadmap or for sub-project B):**
- Test framework alternatives — pytest only.
- Coverage *gating* — only reporting.
- Migration of the 3 hand-rolled tests under `.claude/hooks/` — they stay as-is.
- The `add-qc-test` meta-skill (Approach 3 from brainstorming) — deferred to sub-project B where it earns its keep.
- Linting / formatting (separate concern, separate decision).
- Hypothesis / property-based testing — revisit if simple tests prove insufficient.

## Architectural decisions (from brainstorming)

| Decision | Choice | Rationale |
|---|---|---|
| Test runner scope | QC tests only | Hook tests at `.claude/hooks/` stay hand-rolled — they already work and are tooling-infra, not QC. |
| Directory layout | By concern, not by source path | Reflects risk classes (hard gate / soft check / mutator / metric / utility), not where files happen to live. |
| Fixtures | Standalone `.xml` files in `tests/fixtures/` | Inspectable; filename is the documentation. |
| Audio fixtures | Generated at test time via stdlib `wave` | Project's `.gitignore` excludes `*.wav`; generation is fast and self-contained. |
| Coverage | Reported, not gated | Suite starts at ~0%; gating creates pressure to write low-value tests. Per-file gates considered later. |
| Test deps location | Single `requirements.txt` | Project has no production deployment; splitting saves nothing. |
| Config file | `pyproject.toml` | Modern central tool-config location. |
| Approach | Approach 2 from brainstorming | Roadmap-as-written: infrastructure + first ~5 tests. (Approach 3's meta-skill deferred to B.) |

## Directory layout

```
tests/
  __init__.py                # empty; lets pytest's default import mode play nicely
  conftest.py                # shared fixtures + path helpers (see below)
  README.md                  # layout + how to add tests + how to run locally
  fixtures/                  # standalone .xml files; flat until ~15
    valid_minimal.xml
    valid_with_word_level.xml
    valid_original_only.xml
    valid_both_tiers.xml
    valid_no_original_tier.xml
    missing_standard_tier.xml
    invalid_xml_lang_zzz.xml
    w_m_count_mismatch.xml
    xml_with_html_entities.xml
    xml_with_whitespace_problems.xml
    invented_no_match.xml
    tiny_mapping.tsv
  validators/                # hard gates: pass/fail correctness
    __init__.py
    test_validate_xml.py
  cleaners/                  # in-place XML mutators (highest blast radius)
    __init__.py
    test_clean_xml.py
    test_remove_non_working_audio.py
  utilities/
    __init__.py
    test_standardize.py
    test_find_duplicate_sentences.py
```

**Concern buckets (as the suite grows past the first round):**
- `validators/` — hard pass/fail: validate_xml, validate_punct, validate_glosses, validate_audio (hard part)
- `soft_checks/` — threshold-based: validate_orthography, validate_vocabulary, find_missing_dialect, validate_audio (soft part — see straddling principle)
- `cleaners/` — in-place XML mutators: clean_xml, remove_non_working_audio
- `metrics/` — count_tokens / corpus_metrics / get_corpus_stats / plot_* (pending consolidation; see follow-ups)
- `utilities/` — standardize, add_phonology, find_duplicate_sentences, etc.

**Principle for straddling files.** When a source file straddles concerns (`validate_audio.py` has both hard checks like "file exists" and soft checks like "length within range" — combined because audio access is expensive), the test file lives in the concern bucket of the greatest blast radius (hard > soft), with internal grouping (pytest classes or naming convention) marking the distinction:

```python
# tests/validators/test_validate_audio.py (illustration; not first round)
class TestHardChecks:
    def test_missing_audio_file_is_flagged(self, audio_fixture): ...
class TestSoftChecks:
    def test_length_within_expected_range(self, audio_fixture): ...
```

**Principle for source vs test path divergence.** Test path tracks *concern*, not source path. Example: `remove_non_working_audio.py` lives in `QC/cleaning/` but is functionally a cleaner of audio refs; its test is at `tests/cleaners/test_remove_non_working_audio.py`. Source and test paths can match (and often do), but the test-path layout is canonical when they disagree.

## Fixture conventions

**Where:** `tests/fixtures/`, flat until ~15 files. After that, subdivide by error class (`fixtures/dtd_violations/`, `fixtures/punct_problems/`, etc.).

**Naming:**
- **Positive:** `valid_<description>.xml` — e.g. `valid_minimal.xml`, `valid_with_w_m_tiers.xml`, `valid_with_audio.xml`.
- **Negative:** `<broken_invariant>.xml` — filename describes the failure mode. E.g. `missing_standard_tier.xml`, `invalid_xml_lang_zzz.xml`, `w_m_count_mismatch.xml`.

Filenames are documentation. A reader should know what a fixture exercises without opening it.

**Real-corpus-data exception.** Tests may reference `Corpora/<X>/...` when they genuinely benefit from real published data (the `find_duplicate_sentences` test plants real Glosbe sentences). The test must include a comment naming exactly why a synthetic fixture wouldn't do. This keeps the dependency explicit and grep-able.

**Audio fixtures.** Generated at test time via stdlib `wave`, exposed by the `audio_file_factory` conftest fixture. No `.wav` files committed to the repo (per the project's audio-via-LFS convention).

## Configuration files

### `pyproject.toml` (new, at repo root)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
addopts = "--cov=QC --cov-report=term-missing --cov-report=xml"
```

- `testpaths = ["tests"]` — discovery limited to the test tree; hand-rolled hook tests at `.claude/hooks/` are explicitly excluded.
- `--cov=QC` measures coverage on the QC tree only.
- Both reports: `term-missing` (readable in CI logs, with uncovered line numbers) and `xml` (machine-readable, attached as a CI artifact).

### `requirements.txt` additions

Two pinned entries, matching the existing pinning style:

```
pytest==<current-8.x>
pytest-cov==<current-5.x>
```

Exact versions chosen at implementation time, pinned to the latest stable at install. No separate `requirements-dev.txt` — the project has no production deployment, so splitting saves nothing.

### `tests/conftest.py`

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

Tests accept these as parameters: `def test_foo(valid_minimal_xml): ...`. The `tmp_path` fixture is pytest built-in; gives each test its own scratch directory, auto-cleaned.

## CI workflow

New file: `.github/workflows/tests.yaml`

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

**Path filter excludes `Corpora/**`.** Tests here cover QC *code*, not corpus data. Data-level validation belongs to sub-project B.

**Coverage as artifact, not gate.** XML uploaded with 30-day retention (matches the `corpus-metrics` retention pattern in CLAUDE.md). `if: always()` ensures upload even on test failure, useful for diagnosing whether a regression was a real test failure or a setup problem.

**Manual step, post-merge:** mark `tests / pytest` as a required status check in GitHub branch protection on `main`. Workflow file alone doesn't enforce blocking; repo settings do. Surface this in the PR description as a required follow-up action.

## First-round test targets

Five tests in suggested implementation order (easiest pattern-establishing first; highest-risk last):

### 1. Migration — `tests/utilities/test_find_duplicate_sentences.py`

Convert [`QC/test_find_duplicate_sentences.py`](../../QC/test_find_duplicate_sentences.py) to pytest style:
- Replace hand-rolled PASS/FAIL counter with pytest assertions.
- Replace inline `make_xml()` with three standalone fixtures: `valid_minimal.xml`, `valid_with_word_level.xml`, `invented_no_match.xml`.
- Keep the real-Glosbe-corpus dependency at `Corpora/Glosbe/...` per the real-corpus exception. Add the required justification comment.
- Delete the original `QC/test_find_duplicate_sentences.py` after migration.

### 2. `tests/utilities/test_standardize.py`

[`QC/utilities/standardize.py`](../../QC/utilities/standardize.py) — copies original tier to standard tier (`--copy`) or transliterates via TSV mapping. Mutates XML.

- **Positive (only original)**: input has only `original` tier + `--copy` → output has both tiers, identical content.
- **Positive (both tiers, overwrite)**: input already has both tiers + `--copy` → `standard` is overwritten with `original`'s content. (Confirms the documented "overwrite if both exist" behavior.)
- **Positive (with mapping)**: input has `original` tier + tiny TSV mapping → `standard` reflects the mapping.
- **Negative (no original)**: input has no `original` tier → raises a clear error.
- Fixtures: `valid_original_only.xml`, `valid_both_tiers.xml`, `valid_no_original_tier.xml`, `tiny_mapping.tsv`.

### 3. `tests/cleaners/test_clean_xml.py` (basic round only)

[`QC/cleaning/clean_xml.py`](../../QC/cleaning/clean_xml.py) — in-place XML mutator. Roadmap calls it "the most dangerous code in the repo."

**Test pattern for all in-place mutators**: copy fixture to `tmp_path` first; run the cleaner on the copy; assert on the copy. Never mutate the fixture file.

- **Positive**: `valid_minimal.xml` (already clean) → output unchanged.
- **Negative (HTML entities)**: input with known HTML entity escapes → output has them resolved correctly.
- **Negative (whitespace)**: input with whitespace problems → output normalized.
- **Idempotency**: running cleaner twice produces the same result as running once. Critical for this file.
- Fixtures: `valid_minimal.xml`, `xml_with_html_entities.xml`, `xml_with_whitespace_problems.xml`.

**Round 2 (deferred — see follow-ups):** corpus-mined positives and negatives. Mine published `Corpora/<X>/XML/` for sentences that *look like* cleaner targets but weren't touched (verify they correctly shouldn't be) and sentences that *were* touched (verify the changes were correct). Building this round requires its own design pass — designing good corpus-mined tests is non-trivial.

### 4. `tests/validators/test_validate_xml.py`

[`QC/validation/validate_xml.py`](../../QC/validation/validate_xml.py) — DTD conformance, the canonical XML check.

- **Positive**: `valid_minimal.xml` → no findings reported in output.
- **Negative (missing standard tier)**: `missing_standard_tier.xml` → output reports a finding of the right *class*.
- **Negative (invalid xml:lang)**: `invalid_xml_lang_zzz.xml` → output reports a finding.
- **Negative (W/M mismatch)**: `w_m_count_mismatch.xml` → output reports a finding.

Tests assert the *class* of finding (e.g., "DTD violation present", "ISO-639-3 violation present"), not exact wording — error message text is implementation detail. Note: per the roadmap, current validators never `sys.exit(1)`; assertions ride on output content. Sub-project B's `--exit-nonzero-on-findings` flag will later make exit codes meaningful too.

### 5. `tests/cleaners/test_remove_non_working_audio.py`

[`QC/cleaning/remove_non_working_audio.py`](../../QC/cleaning/remove_non_working_audio.py) — removes `<AUDIO>` references that point to missing or unreadable audio files. High blast radius: removes data from XML in place.

- **Positive (all valid)**: corpus where every audio ref resolves to a working file → no removal; XML unchanged.
- **Positive (one broken)**: corpus with one missing/unreadable audio ref → that ref removed, other refs retained, rest of XML untouched.
- **Edge (no audio)**: corpus with no `<AUDIO>` elements at all → no-op.
- **Edge (all broken)**: all audio refs broken → all removed; remaining structure is valid XML.
- Uses `audio_file_factory` from conftest to generate working WAVs at test time; broken refs are paths that don't exist on disk.

## Fixtures inventory after first round

~11 XML files + 1 TSV in `tests/fixtures/`:
- 5 positive: `valid_minimal.xml`, `valid_with_word_level.xml`, `valid_original_only.xml`, `valid_both_tiers.xml`, `valid_no_original_tier.xml`
- 5 negative: `missing_standard_tier.xml`, `invalid_xml_lang_zzz.xml`, `w_m_count_mismatch.xml`, `xml_with_html_entities.xml`, `xml_with_whitespace_problems.xml`
- 1 supporting: `invented_no_match.xml`
- 1 mapping: `tiny_mapping.tsv`

Well under the ~15 threshold for subdividing.

## Success criteria

A is done when:

1. `pytest` runs from repo root and discovers all tests under `tests/`.
2. All 5 first-round tests pass on `main`.
3. CI workflow `tests.yaml` runs on PR and push, fails the build on test failure, uploads coverage as an artifact.
4. `requirements.txt` has the new pytest + pytest-cov entries; `pip install -r requirements.txt` in a fresh `.venv` produces a working test runner.
5. The original `QC/test_find_duplicate_sentences.py` is deleted (replacement lives in `tests/utilities/`).
6. `tests/README.md` explains the layout, how to add a fixture, and how to run tests locally.
7. **Manual step, post-merge**: branch protection on `main` updated to require `tests / pytest`. Documented in the PR description as a required follow-up action.

## Deferred items (in scope for the project, just not for A)

- **`add-qc-test` skill** (Approach 3 of brainstorming) — deferred to sub-project B, where discovery work surfaces lots of test ideas and the skill earns its keep.
- **Per-file coverage gates** — particularly for `clean_xml.py`. Wait until we see natural coverage levels after a few iterations.
- **`clean_xml.py` deep-fixtures (corpus-mined positives and negatives)** — Round 2 of `test_clean_xml.py`. Mine published corpora for cleaner inputs / outputs that exercise the cleaner's logic against real-world cruft. Needs its own design pass.
- **`find_missing_dialect.py` output usefulness** — operator-flagged improvement; not part of A. Possibly under B's invariant work.
- **`./README.md` is significantly out of date** — flagged for a future cleanup/rewrite task. Not blocking A.

## Things flagged for sub-project B

- `validate_audio.py`'s hard/soft split is an opportunity to formalize the audio invariants in code (B3 territory).
- Fixture coverage of the spec/DTD drift cases the roadmap lists (PHON element, audio start/end always set, segmented-audio convention, etc.) — B1 discovery work produces fixtures A can later add to.
- Threshold calibration for soft-check tests (orthography/vocabulary similarity) — B4.

## Out of scope (not happening here at all)

- Test framework alternatives. Pytest only.
- Hypothesis / property-based testing — revisit if standard tests prove insufficient.
- Linting / formatting (ruff, black, etc.) — separate decision.
- The 3 hand-rolled hook tests under `.claude/hooks/` — left as-is.

## Immediate follow-up tasks (between this design and A's implementation)

1. **Metrics-script consolidation analysis.** Read `count_tokens.py`, `corpus_metrics.py`, `get_corpus_stats.py`, `plot_counts.py`, `plot_deltas.py`. Produce a short comparison covering: (a) what each computes, (b) where they overlap, (c) whether they'd produce different numbers on the same input, (d) what calls what (CI workflows, GitBook stats, etc.), (e) a merge recommendation that preserves the CI behavior `corpus_metrics.py` currently provides and the per-corpus GitBook stats `get_corpus_stats.py` produces. Tractable as a single session. Output: a short doc in `.claude/plans/`. Round 2 of metrics-file testing under A happens against the post-consolidation code.

2. **Confirm `clean_nonlatin.py` is gone** before A's implementation starts — user is removing it from README.md and CLAUDE.md and deleting the file. A's `tests/cleaners/` should not include `test_clean_nonlatin.py`.

3. **Confirm `count_durations.py` does not exist** — appears to have zero references and no source file. Quick double-check during implementation.

## Next step

Once user approves this design, invoke the `superpowers:writing-plans` skill to produce a step-by-step implementation plan.
