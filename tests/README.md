# FormosanBank test suite

Pytest-based tests for the FormosanBank QC code. See [.claude/plans/2026-05-28-a-test-infrastructure-design.md](../.claude/plans/2026-05-28-a-test-infrastructure-design.md) for the design.

## Running tests

From the repo root, with the project's `.venv`:

```bash
.venv/bin/pytest                              # run everything
.venv/bin/pytest tests/cleaners/              # run one concern bucket
.venv/bin/pytest -v -k validate_xml           # tests whose name contains "validate_xml"
.venv/bin/pytest -v -k "V050 or V051"         # specific rule IDs
```

Coverage is reported automatically (configured in [pyproject.toml](../pyproject.toml)). For uncovered-line detail:

```bash
.venv/bin/pytest --cov-report=term-missing
```

The suite mixes plain-passing tests with `xfail(strict=True)` tests targeting sub-project B's deferred work. Run pytest for the current pass/xfail breakdown.

## Layout

Tests are grouped **by concern** (risk class), not by source-tree path:

- `tests/validators/` — hard pass/fail checks (DTD conformance, attribute correctness, structural invariants).
- `tests/cleaners/` — in-place XML mutators (`clean_xml`, `remove_non_working_audio`).
- `tests/utilities/` — helpers and one-offs (`standardize`, `find_duplicate_sentences`).
- `tests/soft_checks/`, `tests/metrics/` — future buckets; will be created when the relevant scripts get tests.

A source file's test lives in the concern bucket matching its risk class, **not** its source directory. Example: `QC/cleaning/remove_non_working_audio.py` is tested at [`tests/cleaners/test_remove_non_working_audio.py`](cleaners/test_remove_non_working_audio.py) (same bucket); `QC/utilities/standardize.py` is tested at [`tests/utilities/test_standardize.py`](utilities/test_standardize.py).

When a source file straddles concerns (e.g., `validate_audio.py` has both hard-check and soft-check sides), the test file goes in the bucket of greatest blast radius (hard > soft), with internal grouping (pytest classes or naming) marking the distinction.

## Fixtures

All test XML lives in [tests/fixtures/](fixtures/). Two naming patterns coexist:

- **`valid_<description>.xml`** — positive fixtures (e.g. [`valid_minimal.xml`](fixtures/valid_minimal.xml), `valid_with_word_level.xml`).
- **`<prefix>###_<short_description>.xml`** — negative fixtures tied to a specific rule from a design doc. Prefix is `v` for validation rules ([2026-05-29-xml-validation-design.md](../.claude/plans/2026-05-29-xml-validation-design.md)) and `c` for cleaner rules ([2026-05-29-clean-xml-extension-tests-design.md](../.claude/plans/2026-05-29-clean-xml-extension-tests-design.md)). The number matches the rule ID (e.g. [`v013_S_only_standard_no_original.xml`](fixtures/v013_S_only_standard_no_original.xml) targets rule V013).

Every XML fixture starts with a top-of-file `<!-- ... -->` comment explaining its purpose, shape, and what invariant it exercises. **Never use `--` inside that comment** — the sequence terminates an XML comment and breaks the file.

Audio fixtures are generated at test time via the `audio_file_factory` conftest fixture (the project's [`.gitignore`](../.gitignore) excludes `*.wav`/`*.mp3`).

Tests may reference real corpus data at `Corpora/<X>/...` when synthesized data wouldn't exercise the diversity needed (currently: [`test_find_duplicate_sentences.py`](utilities/test_find_duplicate_sentences.py) uses real Glosbe sentences). Those tests must include a comment naming why a synthetic fixture wouldn't do.

## Shared conftest fixtures

[`tests/conftest.py`](conftest.py) exposes:

- `repo_root` — `Path` to the FormosanBank repo root.
- `fixtures_dir` — `Path` to `tests/fixtures/`.
- `valid_minimal_xml` — `Path` to `valid_minimal.xml`, the canonical positive baseline. Tier texts deliberately differ (`"Halo (orig)."` vs `"Halo (std)."`) so tests asserting on extracted content can catch a wrong-tier-extraction regression.
- `copy_fixture` — fixture-returning callable. Usage: `work = copy_fixture(fixtures_dir / "X.xml", tmp_path)`. Copies the named fixture into `tmp_path/XML/` and returns the path. Required for any test that invokes an in-place mutator (cleaners, `standardize.py`, etc.) — never let those scripts touch the source-of-truth fixture file.
- `audio_file_factory` — fixture-returning callable that generates a silent WAV at a given duration. Each call gets a unique filename (counter-based, see [`tests/conftest.py`](conftest.py)).

## xfail conventions

A large number of tests target behaviors that **sub-project B will implement** — language-aware cleaning, new validator rules, the cleaner's CSV warning output, etc. Those tests use `pytest.mark.xfail(strict=True, reason=...)` so:

- Today, they correctly XFAIL (the validator/cleaner doesn't yet emit the expected output).
- When B's implementation lands, they XPASS, and `strict=True` flips XPASS to a test failure — forcing the `xfail` marker to be removed.

The `strict=True` discipline is non-negotiable: it's what makes the test suite useful as a forward-looking spec rather than a permanently-amber dashboard.

**Path-strip pattern.** When a test asserts that the script's output contains a rule-specific marker (e.g., `"v051:"` or `"c007"`), the assertion must guard against false positives from fixture filenames that ALSO contain the rule ID. The shared `combined_output()` and `has_marker()` helpers in [`tests/_helpers.py`](_helpers.py) strip `.xml` file paths (and optionally the `corpora_path`) from the combined stdout+stderr before marker matching. Use those helpers when adding similar tests; do not re-roll the regex.

## CI workflow scope

The pytest workflow ([`.github/workflows/tests.yaml`](../.github/workflows/tests.yaml)) triggers on pushes/PRs that touch `QC/**`, `tests/**`, `Corpora/**`, `requirements.txt`, `pyproject.toml`, or the workflow file itself. The `Corpora/**` trigger is intentional: two tests transitively read `Corpora/` — [`test_find_duplicate_sentences.py`](utilities/test_find_duplicate_sentences.py) walks Glosbe XML, and the V081 cross-corpus id collision check (sub-project B) will walk every published corpus once implemented. A change to `Corpora/` can therefore flip those tests, so we run them.

The asymmetry: `Corpora/**` changes trigger **validator** runs (because validators are pure-read and a corpus change could legitimately move a real corpus into or out of compliance), but we do NOT auto-run **cleaners** (`clean_xml.py`, `remove_non_working_audio.py`) on Corpora changes. Cleaners mutate files in place; running them in CI on PR base data would either be a no-op (if the diff is unrelated) or destructive (if it modifies real files). Cleaners are tested via fixtures only.

## Adding a test

1. Identify the source file you're testing and its concern bucket.
2. Add the test file at `tests/<bucket>/test_<source_module>.py` (or extend an existing one).
3. Create any needed fixture XML files under `tests/fixtures/`, following the naming convention.
4. Use the shared conftest fixtures (`fixtures_dir`, `repo_root`, `copy_fixture`, `valid_minimal_xml`, `audio_file_factory`) where they fit.
5. For in-place mutators (cleaners, `standardize.py`): copy the fixture to `tmp_path` via `copy_fixture` before invoking the script; never mutate the fixture file directly.
6. Invoke QC scripts via `subprocess.run([sys.executable, str(SCRIPT), ...])` rather than importing them, so the tests cover the actual CLI surface that CI exercises.
7. If the rule isn't implemented yet, mark the test `pytest.mark.xfail(strict=True, reason="...")` with a reference to the relevant design doc rule ID.

## Adding a fixture

1. Pick a descriptive filename per the naming convention (`valid_<description>.xml`, `v###_<name>.xml`, or `c###_<name>.xml`).
2. Save under `tests/fixtures/`.
3. Add a top-of-file XML comment describing the fixture's purpose, shape, and which invariant it exercises (positive vs negative).
4. **No `--` in the XML comment body.** Rephrase any `--flag`-like wording (`--copy` → "copy mode", `--hard-remove-segmentation` → "the hard-remove-segmentation flag", etc.).
5. If you cross ~15 files in the flat directory, consider subdividing (`tests/fixtures/dtd_violations/`, `tests/fixtures/punct_problems/`, etc.).

## Related design docs

- [2026-05-28-a-test-infrastructure-design.md](../.claude/plans/2026-05-28-a-test-infrastructure-design.md) — the test suite design.
- [2026-05-28-a-test-infrastructure-implementation.md](../.claude/plans/2026-05-28-a-test-infrastructure-implementation.md) — the implementation plan (Tasks 1–8).
- [2026-05-29-xml-validation-design.md](../.claude/plans/2026-05-29-xml-validation-design.md) — rule-by-rule validation spec; `tests/validators/test_validate_xml.py` is its test counterpart.
- [2026-05-29-clean-xml-extension-tests-design.md](../.claude/plans/2026-05-29-clean-xml-extension-tests-design.md) — rule-by-rule cleaner-extension spec; `tests/cleaners/test_clean_xml_extensions.py` is its test counterpart.
- [2026-05-27-roadmap.md](../.claude/plans/2026-05-27-roadmap.md) — sub-projects A–E. xfail tests largely target sub-project B's deferred work.
