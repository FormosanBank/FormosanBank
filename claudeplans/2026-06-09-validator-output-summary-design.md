# Validator output: summary-to-terminal + one detail CSV

**Date:** 2026-06-09
**Status:** Approved (design). Implementation in progress.

## Problem

The finding-based validators (`validate_xml`, `validate_glosses`, `validate_text`,
`validate_audio`) each print every HARD and SOFT finding to stderr via a bespoke
`_print_summary`. On large corpora this overflows the terminal scrollback. The
output format also differs per validator (xml dumps all; text aggregates SOFT to
CSV; glosses prints inline), so there is no single mental model.

## Goal (per user, 2026-06-09)

- **Terminal:** a compact summary — per-`rule_id` counts, split into HARD and SOFT
  sections with totals. No per-finding detail on screen.
- **Detail:** **one CSV** with every finding (both severities) and enough context
  to understand each without opening the XML. The CSV path is printed to the
  terminal. (User chose one CSV with a prose `message` column over per-rule CSVs.)
- Exit-code behavior unchanged (1 if any HARD, unless `--no-exit-on-hard`).

## Design

### 1. `QC/validation/_finding.py` — two new functions
- `summarize(findings) -> dict[Severity, dict[str, int]]`: per-`rule_id` counts by
  severity. Data behind the terminal summary.
- `write_findings_csv(path, findings)`: the one CSV, **all** severities, columns:
  `file, line, severity, rule_id, location, language, character, count, message`.
  The existing `write_soft_csv` stays (no external breakage), but validators stop
  calling it.

### 2. `QC/validation/_report.py` (new) — single source of truth for output
`report_findings(findings, csv_path, *, file_count, out=sys.stderr) -> bool`
(returns `has_hard`). Prints:

```
=== Validation summary: 4 files, 2 with issues ===
HARD — 15 total:
  V000   3
  V064  12
SOFT — 52 total:
  V061  30
  V068  15
  V116   7
Details: logs/validate_xml_findings.csv
```

Clean run prints `=== Validation summary: N files, 0 with issues ===` / `No issues
found.` and writes **no** CSV (nothing to detail), so no `Details:` line.

### 3. Each validator `main()`
Replace the bespoke `_print_summary` + `write_soft_csv` with one
`report_findings(...)` call; delete the four `_print_summary`s. Add `--csv <path>`
(default `logs/<validator>_findings.csv`). Keep `--soft-csv` as a **deprecated
alias** for the same destination so `run-qc-pipeline` and `xml-validation.yaml`
keep working (their `--soft-csv path` now receives all findings, not just SOFT —
intended). `--no-exit-on-hard` and exit logic unchanged.

### 4. Tests (mechanical bulk)
Per-finding markers move from terminal text to the CSV. Add to `tests/_helpers.py`:
`csv_rows(path)` and `has_csv_finding(rows, rule_id, marker)`. Convert the affected
assertions (currently `_has_rule_finding`/`_has_text_finding` scanning stderr) to
read the CSV; switch clean-checks to the new summary line. Full `pytest` stays the
green gate.

## Scope
In: `validate_xml`, `validate_glosses`, `validate_text`, `validate_audio` (the
finding-based validators) via the shared `_report.py`.
Out (for now): `validate_duplicate_sentences` (keeps its group-count output + own
CSV) and `validate_dialect` (a distribution table, not finding-based).

## Implemented (2026-06-09)

Landed test-first; full suite green (453 passed). New: `QC/validation/_report.py`
(`report_findings`) + `_finding.summarize`/`write_findings_csv` (+ tests
`test_report.py`, extended `test_finding.py`). Wired `validate_xml`,
`validate_glosses`, `validate_text` through `report_findings`; their per-finding
`_print_summary`s deleted. Test helper `tests/_helpers.csv_has`/`csv_rows` added;
affected assertions read the CSV instead of stderr.

Deviations from the design above, decided during implementation:
- **CSV always written** (header-only on clean), not "no CSV on clean" — keeps CI
  artifact uploads and run-qc-pipeline robust. `Details:` line still only prints
  when there are findings.
- **`validate_glosses`**: dropped the legacy `validation_results.csv` /
  `validation_m_mismatches.csv` and the `--check_morpho` flag (the legacy re-parse
  of `location` was the id-truncation bug). `--output_dir` is retained and now
  names the directory for the one findings CSV, so CI/skill invocations are
  unchanged. Truncation fixed by construction (verbatim `location`); regression
  test `test_validate_glosses_csv_preserves_space_containing_ids`.
- **`validate_audio`**: kept its domain-specific `broken_audio.csv` (the `kind`-
  tagged CSV consumed by `clean_audio.py`) and `audio_duration_issues.csv`; only
  its terminal `print_summary` switched to the compact per-rule count format
  (reusing `summarize`). It does not route through `report_findings`.
- **`.xml`-only**: `_resolve_target_files` filters to `.xml` defensively; test
  `test_validate_glosses_ignores_non_xml_files` pins a README being skipped.
- **CI** (`xml-validation.yaml`): "Top 10 rule_ids" steps now count the `rule_id`
  column from the CSV (robust) instead of grepping `[V###]` stderr lines.

## Decisions locked
- One CSV, prose `message` column for context (user choice).
- `--soft-csv` retained as alias; meaning widens to "all findings".
- **Mnemonic rule names (added 2026-06-09, per user):** each rule function is
  named `v<NNN>_<mnemonic>`, so `QC/validation/_rule_titles.py` derives a
  {rule_id: mnemonic} map from the rule registries (zero maintenance; V000 has a
  manual entry). The mnemonic is shown next to the rule id in the terminal
  summary (`V060 W_count_matches_word_count: 1`) and as a `title` column in the
  CSV (inserted after `rule_id`, so `rule_id` stays column 4 and CI counting is
  unaffected). `report_findings(..., titles=)` defaults to the derived map; audio
  keeps its own `kind`-column mnemonics. Tests: `test_rule_titles.py` + additions
  to `test_finding.py`/`test_report.py`.
- duplicate-sentences / dialect untouched.
