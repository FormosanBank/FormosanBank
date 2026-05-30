# Validator refactor design (sub-project B, piece 1)

**Date:** 2026-05-30
**Status:** Approved (brainstorming complete; ready for implementation planning).

## Purpose

Take [QC/validation/validate_xml.py](../../QC/validation/validate_xml.py) from a 334-line monolithic CLI that emits informational logs and never `sys.exit(1)` into a modular runner + rule-set that:

1. Implements the rules catalogued in [2026-05-29-xml-validation-design.md](2026-05-29-xml-validation-design.md) (V001–V083).
2. Emits structured output suitable for CI consumption and trend tracking.
3. In CI mode, blocks merges on HARD findings — the gating purpose that sub-project B is named after.

The xfail tests in [tests/validators/test_validate_xml.py](../../tests/validators/test_validate_xml.py) (23 of 41) are already shaped to expect the markers this refactor will emit. Each landed rule = one xfail removed, giving a built-in checklist of progress.

## Non-goals

- **Other validators.** `validate_punct.py`, `validate_glosses.py`, `validate_orthography.py`, `validate_vocabulary.py` are out of scope. They get their own design passes when their time comes.
- **SOFT threshold calibration.** Tracked under roadmap B4 — depends on running this refactored validator over all published corpora and observing the empirical drift distributions.
- **CI wiring.** Adding the validator as a PR-blocking GitHub Actions check is a separate B piece. The work here *makes that possible* by giving the validator a useful exit code and CSV output.

## Architecture

```
QC/validation/
├── validate_xml.py           ← thin runner (~80 lines: argparse, walk, orchestrate, exit)
├── xml_template.dtd          ← tightened where one-line constraints fit
├── _finding.py               ← Finding dataclass + Severity enum + CSV writer
├── _corpus_index.py          ← CorpusIndex built in pass 1 (id→path, path→lang, …)
└── rules/
    ├── __init__.py
    ├── hard.py               ← rules whose violation should block merge (exit 1)
    ├── soft.py               ← rules whose violation feeds the drift CSV (no exit impact)
    └── warn.py               ← rules at advisory severity (stderr only, no exit impact)
```

**Module organization is by severity, not by category.** Rationale: the runner can short-circuit by severity (e.g., abort after first HARD if `--fail-fast` is added later), and CI consumers read severity first. Category navigation is still trivial via the rule ID (every rule function is named `v###_short_description`).

The per-rule severity assignment lives in [2026-05-29-xml-validation-design.md](2026-05-29-xml-validation-design.md), which is authoritative. The implementation places each rule in the module matching its design-doc severity; this design does not re-enumerate the assignment to avoid drift between two sources.

**Why not "one rule per file"?** ~33 rules → ~33 small files inflates the directory without buying isolation; clear function naming gets the same benefit within fewer files.

## Finding shape

```python
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

class Severity(Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    WARN = "WARN"

@dataclass(frozen=True)
class Finding:
    rule_id: str                 # "V015"
    severity: Severity
    message: str                 # "duplicate kindOf='original' on FORM"
    path: Path                   # the file the finding is about
    location: str | None = None  # e.g. "S=ami_chapter01_S0042" — HARD/WARN populate
    count: int = 1               # >1 only for aggregated SOFT
    language: str | None = None  # SOFT findings keyed by language
    character: str | None = None # SOFT findings keyed by character
```

Flat with optional fields beats a `SoftFinding(Finding)` hierarchy because:
- One type to import and reason about.
- `frozen=True` keeps unused fields cheap.
- The CSV writer maps fields → columns trivially.
- Python doesn't enforce subclass invariants at runtime anyway.

## Emission model: hybrid

Per the per-element vs aggregated decision:

- **HARD and WARN rules** emit one Finding per offending element. `location` is populated with a pinpoint identifier (e.g., `"S=ami_chapter01_S0042"`, `"S=… FORM[kindOf='standard']"`). The message uses rule-specific phrasing the xfail-test markers expect.
- **SOFT rules** pre-aggregate before returning. A rule that detects orthography drift returns one Finding per `(rule_id, file, language, character)` tuple, with `count` set to the occurrence count. The runner does no further aggregation on SOFT findings — it just writes them to CSV.

This boundary matters because SOFT volume can be very high (thousands of offending characters per file) and per-element emission would flood stderr. HARD volume is bounded by the corpus's "wrongness" and is rare in well-formed data.

## Rule signature

```python
def v015_duplicate_original_FORM(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    ...
```

Every rule has the same signature for runner simplicity. The `index` arg is `None` in pass 1 and populated `CorpusIndex` in pass 2. Each rule docstring declares whether it consults `index` — that determines which pass the runner uses to call it.

```python
@dataclass(frozen=True)
class CorpusIndex:
    ids: dict[str, list[tuple[Path, str]]]    # TEXT/@id → list of (path, location-str)
    langs: dict[Path, str]                    # path → resolved xml:lang
    # extend as needed by cross-file rules
```

## Two-pass runner

**Pass 1.** Walk the corpus, parse each `.xml` file once with `lxml.etree.parse`, store the parsed tree in a cache keyed by path. For each tree, call every rule whose docstring declares it does not consult `index`. Collect findings. While iterating, also populate `CorpusIndex` (TEXT id → path, xml:lang resolution, etc.).

**Pass 2.** For each rule that does consult `index`, iterate the cached trees and call the rule with the populated `CorpusIndex`.

Tree caching is mandatory — re-parsing every file twice for the sake of cross-file rules would double parse time for no benefit.

The runner walks files via the existing `by_path` / `by_corpus` / `by_language` mode dispatch. Discovery logic stays in the runner (not in rules).

## Output channels

- **HARD findings → stderr,** one line per Finding:
  ```
  [V015] HARD ami/chapter01.xml S=ami_chapter01_S0042: duplicate kindOf='original' on FORM
  ```
  Format: `[<rule_id>] <severity> <relative-path-to-corpora-root> <location>: <message>`.
- **WARN findings → stderr,** same shape, severity tag `WARN`. Never affects exit code.
- **SOFT findings → CSV** at `--soft-csv <path>` (default `logs/validation_soft.csv`). Columns:
  `file,rule_id,language,character,count`. End-of-run summary names the CSV path.
- **End-of-run summary → stderr:**
  ```
  Total findings: 34 HARD, 1042 SOFT, 6 WARN. SOFT details in logs/validation_soft.csv.
  ```

Per the path-strip pattern in [tests/_helpers.py](../../tests/_helpers.py), tests already strip `<path>` tokens before marker matching, so the validator's output containing file paths does not pollute xfail assertions.

## Exit code semantics

**Default behavior changes:** the validator exits 1 if any HARD findings are produced. This is the entire point of B's CI-gating goal and the reason the current "always returns 0" behavior is a CI dead end.

SOFT and WARN never affect the exit code — SOFT is a tracked drift counter (the threshold mechanism that gates SOFT lives in B4), and WARN is advisory.

For backward compatibility (e.g., if any local script or skill currently depends on `validate_xml.py` always exiting 0), add `--no-exit-on-hard` that restores the legacy behavior.

## CLI

Preserve the existing CLI surface:

```
python validate_xml.py by_path     --path <file-or-dir>
python validate_xml.py by_corpus   --corpus <name>   --corpora_path <path>
python validate_xml.py by_language --language <name> --corpora_path <path>
```

Add:

- `--soft-csv <path>` (default `logs/validation_soft.csv`)
- `--no-exit-on-hard` (opt-out of the new exit-1 behavior; default off)

Keep:

- `--verbose`
- `--log_dir <path>`

## DTD allocation

The mixed rule: tighten the DTD where the constraint fits in a single attribute/element declaration; otherwise write a Python rule.

A rule lands in the DTD if it is expressible as:
- Required attribute (`#REQUIRED`).
- Fixed/enum attribute value.
- Cardinality (`?`, `*`, `+`).
- Required element under a parent.

A rule lands in Python if it requires:
- Conditional logic on attribute *values* (e.g., "FORM with `kindOf='original'` must appear exactly once" — DTD can't express attribute-conditional cardinality cleanly).
- Cross-element or cross-file knowledge (V081).
- Filesystem checks (V051's actual audio-file existence).
- Computation (string length, regex match, character-set membership).

Each rule in [2026-05-29-xml-validation-design.md](2026-05-29-xml-validation-design.md) gets annotated `Enforcement: DTD | Python` as part of implementation. Rules promoted to the DTD do not need a Python rule (the existing XSD-validation step catches them for free via the validator's existing DTD check).

**Known DTD-promotable rules** (preliminary, to confirm during implementation):
- V030 (TEXT must have `@citation`) → `#REQUIRED`
- V032 (TEXT must have `@copyright`) → `#REQUIRED`
- V050 (AUDIO must have `@file`) → `#REQUIRED`

**Known Python-required rules** (preliminary):
- V015 (duplicate `kindOf="original"` FORM) — attribute-conditional cardinality.
- V017 (empty FORM) — DTD `mixed` content can't express "must have text".
- V051 (audio start ≥ end) — computational.
- V081 (cross-corpus id uniqueness) — cross-file.

## Testing strategy

The xfail tests in [tests/validators/test_validate_xml.py](../../tests/validators/test_validate_xml.py) are the target spec. Each is keyed to a rule ID and asserts rule-specific markers. The Finding format `[V015] HARD … : duplicate kindOf='original' on FORM` includes both the rule ID (`v015` after lowercasing — what `combined_output` produces) and the rule-specific phrasing (`duplicate kindof`), satisfying the marker tuples already encoded in the tests.

For each rule landed:
1. Write the rule function in the right severity module.
2. (If DTD-promotable) update [xml_template.dtd](../../QC/validation/xml_template.dtd).
3. Remove the `xfail` marker from the corresponding test.
4. Verify the test goes plain-pass (not XPASS-strict — that means the marker matched something unrelated; investigate).

The existing test fixtures (`v###_*.xml`) are the negative cases; `valid_minimal.xml` and similar are the positives.

Cross-file rules (V081) need a fixture for the synthetic test corpus *and* must resolve a real-corpus path during the pass. The test in [tests/validators/test_validate_xml.py:622](../../tests/validators/test_validate_xml.py#L622) is already shaped to copy `v081_TEXT_id_collides_with_published.xml` into `tmp_path`, point the validator at `tmp_path`, and expect the validator's pass-2 walk to discover the collision against `Corpora/`. The fixture's id (`ILRDF_Dicts_Paiwan`, `xml:lang="pwn"`) is selected to be apostrophe-free and stable.

## Migration path

The current [QC/validation/validate_xml.py](../../QC/validation/validate_xml.py) is replaced wholesale by the refactored runner plus the new modules under `_finding.py`, `_corpus_index.py`, and `rules/`. Because the CLI surface is preserved:

- The [run-qc-pipeline](../../.claude/skills/run-qc-pipeline.md) skill continues to work.
- The [QC/README.md](../../QC/README.md) examples continue to work.
- The gitbook docs that reference `validate_xml.py` continue to be accurate.

Behavioral change visible to callers: the validator now exits 1 on HARD findings unless `--no-exit-on-hard` is passed. Local interactive use is unaffected (the user still sees the same stderr output); CI behavior changes from "logs and passes" to "logs and fails on HARD".

The new SOFT CSV file appears at `--soft-csv <path>` (default `logs/validation_soft.csv`) on every run; it is overwritten per run (not appended), matching the existing per-corpus log pattern.

## Implementation order

Suggested order for the implementation plan:

1. **Scaffolding.** `_finding.py`, `_corpus_index.py`, empty `rules/{hard,soft,warn}.py`, runner skeleton that walks files, parses once, calls "no rules" (returns 0 findings). Migrate existing XSD validation into the new runner. All existing passing tests continue to pass.
2. **Migrate one existing rule** as a worked example (e.g., V001 root-must-be-TEXT — currently implicit in XSD validation; make it explicit so the rule structure is exercised). Verify a fresh xfail removal goes plain-pass.
3. **Exit-code semantics + CLI surface.** Land `--no-exit-on-hard` and the SOFT CSV file plumbing. No SOFT rules yet; just the writer infrastructure.
4. **DTD tightening pass.** Promote the obvious DTD-side wins (V030 / V032 / V050 etc.). Remove the corresponding xfails.
5. **Python-side HARD rules,** category by category (structural, FORM tier, TRANSL, attribute, audio, segmentation, PHON). Each rule = one xfail removed.
6. **Cross-file rules.** Pass-2 plumbing + V081 + V082 / V083 (path discipline rules).
7. **SOFT rules.** V010, V014, then orthography-drift (which may need infrastructure from B7).

Each step lands as its own PR (or series of small PRs) so review stays tractable.

## Open questions for implementation

None blocking — the architecture above is approvable. Implementation-time questions to surface as they arise:

- Whether SOFT CSV should be per-corpus (one CSV per `--corpora_path`) or one CSV for the whole run when multiple corpora are walked. Current default: one CSV per run, regardless of how many corpora the path covers. Revisit if the CSV gets unwieldy.
- Whether the runner should support `--fail-fast` (stop after first HARD). YAGNI for now; add if needed.
- WARN severity rules: the design doc lists most rules as HARD or SOFT; the WARN category exists as a future placeholder. Don't introduce WARN rules speculatively.
