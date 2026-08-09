# Conversion-table Validator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `QC/validation/validate_conversion_table.py`, a CLI auditor that checks — transitively through IPA — that an orthography conversion table maps a source orthography onto a target orthography as closely as possible, and reports where it cannot.

**Architecture:** One self-contained module (matching sibling single-file validators). Both orthography TSVs are loaded to grapheme→IPA maps; the conversion table's target column is re-tokenized through the *output* orthography's longest-match grapheme map so its IPA can be compared to the source IPA. Each conversion row resolves to Confirmed / Warning / Unresolved by a two-stage IPA normalization (safe glyph-only vs. segmentation-changing). Information-loss (merges, unrepresentable phonemes) and coverage are computed across the whole table. A markdown report is emitted; exit code is nonzero only on Unresolved mismatches and table-integrity errors.

**Tech Stack:** Python 3.13, stdlib only (`csv`, `re`, `unicodedata`, `argparse`, `dataclasses`, `enum`, `pathlib`). Tests: pytest with `tmp_path`.

## Global Constraints

- Python 3.13, stdlib only — no new dependencies (matches repo `requirements.txt`).
- Tokenization is **case-sensitive** exact longest-match. Do NOT reuse `add_phonology.apply_phonology_mappings`, whose casefold fallback would conflate case-distinct graphemes like Li's `T` (ʈ) vs `t` (t).
- Tests live in `tests/validators/test_validate_conversion_table.py`, build throwaway TSVs under `tmp_path`, and import `from QC.validation import validate_conversion_table as vct`. No `__init__.py` files (QC is a namespace package; pytest runs from repo root).
- TSV cell value `NA` means "absent in this dialect" — skip it on load (same convention as `add_phonology.load_profile`).
- Exit nonzero ONLY for verdicts `MISMATCH`, `UNKNOWN_SOURCE`, `UNTOKENIZABLE`. Warnings, merges, can't-encode, and coverage gaps are exit 0.
- Run all tests from repo root: `python -m pytest tests/validators/test_validate_conversion_table.py -v`.

---

## File Structure

- **Create:** `QC/validation/validate_conversion_table.py` — the entire tool: dataclasses, loaders, tokenizer, IPA normalization, audit engine, report renderer, CLI.
- **Create:** `tests/validators/test_validate_conversion_table.py` — all 18 tests.

Data model (defined in Task 1, referenced throughout):

```python
class Verdict(Enum):
    CONFIRMED = "confirmed"
    WARNING = "warning"
    MISMATCH = "mismatch"
    UNKNOWN_SOURCE = "unknown_source"   # conversion src not in original profile
    UNTOKENIZABLE = "untokenizable"     # conversion tgt not spellable in output profile

@dataclass(frozen=True)
class Orthography:
    ipa_of: dict[str, str]   # grapheme -> IPA
    column: str              # value column actually used

@dataclass(frozen=True)
class RowResult:
    src: str
    tgt: str
    verdict: Verdict
    src_ipa: str | None
    tgt_ipa: str | None
    reason: str = ""                 # warning transform label, else ""
    unmatched: tuple[str, ...] = ()  # untokenizable target graphemes

@dataclass
class Report:
    dialect: str | None
    rows: list[RowResult]
    merges: list[tuple[str, list[str]]]      # (output_ipa, sorted distinct source_ipas)
    cant_encode: list[str]                   # output phonemes the source cannot produce
    coverage_gaps: list[tuple[str, str]]     # (source grapheme, its IPA)
```

---

### Task 1: Data model + value-column selection

**Files:**
- Create: `QC/validation/validate_conversion_table.py`
- Test: `tests/validators/test_validate_conversion_table.py`

**Interfaces:**
- Produces: `Verdict`, `Orthography`, `RowResult`, `Report` (above); `select_value_column(fieldnames: list[str], dialect: str | None, key: str) -> str`.

`select_value_column` picks the IPA/target column: the `dialect` column if present; else the first of `default`, `IPA`, `standard` that exists; else the lone non-key column; else raise `ValueError`. `key` is the grapheme column to exclude (`"letter"` for profiles, the table's first column for conversion tables).

- [ ] **Step 1: Write the failing tests**

```python
# tests/validators/test_validate_conversion_table.py
import subprocess
import sys
from pathlib import Path

import pytest

from QC.validation import validate_conversion_table as vct

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "QC" / "validation" / "validate_conversion_table.py"
)


def _tsv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    lines = ["\t".join(header)] + ["\t".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_select_value_column_prefers_dialect():
    cols = ["letter", "Wutai", "Eastern", "default"]
    assert vct.select_value_column(cols, "Eastern", key="letter") == "Eastern"


def test_dialect_column_selected_per_dialect_with_default_fallback():
    cols = ["letter", "Wutai", "Eastern", "default"]
    # Dona has no column -> fall back to 'default'
    assert vct.select_value_column(cols, "Dona", key="letter") == "default"


def test_single_value_column_profile():
    cols = ["letter", "IPA"]
    assert vct.select_value_column(cols, "Wutai", key="letter") == "IPA"


def test_select_value_column_ambiguous_raises():
    cols = ["original", "Southern", "Coastal"]
    with pytest.raises(ValueError):
        vct.select_value_column(cols, "Malan", key="original")
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: FAIL — `ModuleNotFoundError` / `AttributeError: module has no attribute 'select_value_column'`.

- [ ] **Step 3: Write minimal implementation**

```python
# QC/validation/validate_conversion_table.py
"""Audit an orthography conversion table transitively through IPA.

Given an original orthography profile, an output orthography profile, and a
conversion table (source grapheme -> target grapheme), check that applying
the table reproduces the output orthography as closely as possible, and
report the cases where it cannot: notational near-equivalences (warnings),
phoneme merges, phonemes the source cannot encode, coverage gaps, and
table-integrity errors. See docs/superpowers/specs/2026-08-09-conversion-
table-validator-design.md.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Verdict(Enum):
    CONFIRMED = "confirmed"
    WARNING = "warning"
    MISMATCH = "mismatch"
    UNKNOWN_SOURCE = "unknown_source"
    UNTOKENIZABLE = "untokenizable"


@dataclass(frozen=True)
class Orthography:
    ipa_of: dict[str, str]
    column: str


@dataclass(frozen=True)
class RowResult:
    src: str
    tgt: str
    verdict: Verdict
    src_ipa: str | None
    tgt_ipa: str | None
    reason: str = ""
    unmatched: tuple[str, ...] = ()


@dataclass
class Report:
    dialect: str | None
    rows: list[RowResult] = field(default_factory=list)
    merges: list[tuple[str, list[str]]] = field(default_factory=list)
    cant_encode: list[str] = field(default_factory=list)
    coverage_gaps: list[tuple[str, str]] = field(default_factory=list)

    def blocking(self) -> list[RowResult]:
        blocking_verdicts = {
            Verdict.MISMATCH, Verdict.UNKNOWN_SOURCE, Verdict.UNTOKENIZABLE
        }
        return [r for r in self.rows if r.verdict in blocking_verdicts]


_FALLBACK_COLUMNS = ("default", "IPA", "standard")


def select_value_column(fieldnames: list[str], dialect: str | None, key: str) -> str:
    """Choose the IPA/target column: dialect, then a known fallback, then lone column."""
    value_columns = [c for c in fieldnames if c != key]
    if dialect and dialect in value_columns:
        return dialect
    for fallback in _FALLBACK_COLUMNS:
        if fallback in value_columns:
            return fallback
    if len(value_columns) == 1:
        return value_columns[0]
    raise ValueError(
        f"no unambiguous value column for dialect {dialect!r} in {fieldnames}"
    )
```

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add QC/validation/validate_conversion_table.py tests/validators/test_validate_conversion_table.py
git commit -m "Add conversion-table validator: data model + column selection"
```

---

### Task 2: Orthography loader + case-sensitive tokenizer + target IPA

**Files:**
- Modify: `QC/validation/validate_conversion_table.py`
- Test: `tests/validators/test_validate_conversion_table.py`

**Interfaces:**
- Consumes: `Orthography`, `select_value_column` (Task 1).
- Produces:
  - `load_orthography(path: Path, dialect: str | None) -> Orthography`
  - `tokenize(text: str, letters) -> tuple[list[str], list[str]]` → (graphemes, unmatched chars); case-sensitive longest-match; unmatched chars are appended to BOTH lists (as single chars in graphemes) so callers can both spell and detect gaps.
  - `target_ipa(tgt: str, output: Orthography) -> tuple[str | None, list[str]]` → (concatenated IPA, unmatched); IPA is `None` iff there are unmatched graphemes.

- [ ] **Step 1: Write the failing tests**

```python
def test_load_orthography_maps_grapheme_to_ipa(tmp_path):
    p = _tsv(tmp_path / "src.tsv", ["letter", "IPA"],
             [["T", "ʈ"], ["t", "t"], ["x", "NA"]])
    ortho = vct.load_orthography(p, "Wutai")
    assert ortho.ipa_of == {"T": "ʈ", "t": "t"}  # NA row skipped


def test_tokenize_longest_match_is_case_sensitive(tmp_path):
    # 'tr' is one grapheme; must not split into t + r, and 'T' != 't'.
    letters = ["tr", "t", "r", "T"]
    graphemes, unmatched = vct.tokenize("trT", letters)
    assert graphemes == ["tr", "T"]
    assert unmatched == []


def test_target_ipa_tokenizes_multigrapheme_target(tmp_path):
    # 'tr' -> ʈ (single grapheme); 'aa' -> a + a (two graphemes).
    out = _tsv(tmp_path / "out.tsv", ["letter", "default"],
               [["tr", "ʈ"], ["a", "a"]])
    output = vct.load_orthography(out, "default")
    assert vct.target_ipa("tr", output) == ("ʈ", [])
    assert vct.target_ipa("aa", output) == ("aa", [])


def test_target_ipa_reports_untokenizable(tmp_path):
    out = _tsv(tmp_path / "out.tsv", ["letter", "default"], [["a", "a"]])
    output = vct.load_orthography(out, "default")
    ipa, unmatched = vct.target_ipa("aq", output)
    assert ipa is None
    assert "q" in unmatched
```

Note: this is Test #5 (`test_target_ipa_tokenizes_multigrapheme_target`) and Test #13 (`test_target_ipa_reports_untokenizable`) from the spec.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: FAIL — `AttributeError: ... 'load_orthography'`.

- [ ] **Step 3: Write minimal implementation** (append to the module)

```python
def load_orthography(path: Path, dialect: str | None) -> Orthography:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        column = select_value_column(fieldnames, dialect, key="letter")
        ipa_of: dict[str, str] = {}
        for row in reader:
            letter = (row.get("letter") or "").strip()
            value = (row.get(column) or "").strip()
            if not letter or value == "NA" or value == "":
                continue
            ipa_of.setdefault(letter, value)
    return Orthography(ipa_of=ipa_of, column=column)


def tokenize(text: str, letters) -> tuple[list[str], list[str]]:
    ordered = sorted({lt for lt in letters if lt}, key=len, reverse=True)
    graphemes: list[str] = []
    unmatched: list[str] = []
    index = 0
    while index < len(text):
        match = next((lt for lt in ordered if text.startswith(lt, index)), None)
        if match is None:
            graphemes.append(text[index])
            unmatched.append(text[index])
            index += 1
        else:
            graphemes.append(match)
            index += len(match)
    return graphemes, unmatched


def target_ipa(tgt: str, output: Orthography) -> tuple[str | None, list[str]]:
    graphemes, unmatched = tokenize(tgt, output.ipa_of.keys())
    if unmatched:
        return None, unmatched
    return "".join(output.ipa_of[g] for g in graphemes), []
```

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: PASS (8 tests total).

- [ ] **Step 5: Commit**

```bash
git add QC/validation/validate_conversion_table.py tests/validators/test_validate_conversion_table.py
git commit -m "Add orthography loader + case-sensitive tokenizer + target IPA"
```

---

### Task 3: IPA normalization + reconcile (the three verdict tiers)

**Files:**
- Modify: `QC/validation/validate_conversion_table.py`
- Test: `tests/validators/test_validate_conversion_table.py`

**Interfaces:**
- Produces:
  - `canonical_safe(ipa: str) -> str` — NFC; ligature affricates → tie-barred digraphs (`ʦ`→`t͡s`, `ʣ`→`d͡z`, `ʧ`→`t͡ʃ`, `ʤ`→`d͡ʒ`, `ʨ`→`t͡ɕ`, `ʥ`→`d͡ʑ`); IPA script `ɡ`(U+0261) → Latin `g`. Segment-preserving only.
  - `reconcile(src_ipa: str, tgt_ipa: str) -> tuple[Verdict, str]` — `CONFIRMED` if safe forms match; `WARNING` (with reason `length↔doubling`, `digraph↔affricate`, or `length+affricate`) if they match only after segmentation-changing transforms (length `ː`/`:` ↔ doubled segment; tie-bar removal); else `MISMATCH`.

- [ ] **Step 1: Write the failing tests**

```python
def test_exact_ipa_match_is_confirmed():
    assert vct.reconcile("ʈ", "ʈ") == (vct.Verdict.CONFIRMED, "")


def test_tiebar_ligature_is_confirmed():
    # ʦ and t͡s are the same single segment -> no warning.
    verdict, _ = vct.reconcile("ʦ", "t͡s")
    assert verdict == vct.Verdict.CONFIRMED


def test_length_notation_is_warning():
    verdict, reason = vct.reconcile("aː", "aa")  # aː vs aa
    assert verdict == vct.Verdict.WARNING
    assert "length" in reason


def test_bare_digraph_affricate_is_warning():
    # bare 'ts' (possibly a cluster) vs affricate t͡s -> ambiguous.
    verdict, reason = vct.reconcile("ts", "t͡s")
    assert verdict == vct.Verdict.WARNING
    assert "affricate" in reason


def test_true_mismatch():
    assert vct.reconcile("p", "b")[0] == vct.Verdict.MISMATCH


def test_short_vowel_not_equated_with_long():
    # length expansion must not make short 'a' match long 'aː'/'aa'.
    assert vct.reconcile("a", "aa")[0] == vct.Verdict.MISMATCH
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: FAIL — `AttributeError: ... 'reconcile'`.

- [ ] **Step 3: Write minimal implementation** (append to the module)

```python
_TIE_BAR = "͡"
_LIGATURE_TO_TIEBAR = {
    "ʦ": "t͡s", "ʣ": "d͡z",
    "ʧ": "t͡ʃ", "ʤ": "d͡ʒ",
    "ʨ": "t͡ɕ", "ʥ": "d͡ʑ",
}
_LENGTH = re.compile(r"(.)[ː:]")  # a segment followed by a length mark


def canonical_safe(ipa: str) -> str:
    """Normalize only in segment-preserving ways (glyph variants)."""
    text = unicodedata.normalize("NFC", ipa)
    for ligature, tiebar in _LIGATURE_TO_TIEBAR.items():
        text = text.replace(ligature, tiebar)
    text = text.replace("ɡ", "g")  # IPA script g -> Latin g
    return text


def _expand_length(text: str) -> str:
    return _LENGTH.sub(r"\1\1", text)  # 'aː' / 'a:' -> 'aa'


def reconcile(src_ipa: str, tgt_ipa: str) -> tuple[Verdict, str]:
    safe_src, safe_tgt = canonical_safe(src_ipa), canonical_safe(tgt_ipa)
    if safe_src == safe_tgt:
        return Verdict.CONFIRMED, ""

    reasons = []
    if _expand_length(safe_src) == _expand_length(safe_tgt):
        reasons.append("length↔doubling")
    if safe_src.replace(_TIE_BAR, "") == safe_tgt.replace(_TIE_BAR, ""):
        reasons.append("digraph↔affricate")
    # combined: both transforms together
    combined_src = _expand_length(safe_src).replace(_TIE_BAR, "")
    combined_tgt = _expand_length(safe_tgt).replace(_TIE_BAR, "")
    if combined_src == combined_tgt:
        return Verdict.WARNING, "+".join(reasons) if reasons else "length+affricate"
    return Verdict.MISMATCH, ""
```

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: PASS (14 tests total).

- [ ] **Step 5: Commit**

```bash
git add QC/validation/validate_conversion_table.py tests/validators/test_validate_conversion_table.py
git commit -m "Add IPA normalization + reconcile verdict tiers"
```

---

### Task 4: Conversion-table loader + audit engine

**Files:**
- Modify: `QC/validation/validate_conversion_table.py`
- Test: `tests/validators/test_validate_conversion_table.py`

**Interfaces:**
- Consumes: `Orthography`, `RowResult`, `Report`, `Verdict`, `select_value_column`, `target_ipa`, `reconcile`, `canonical_safe`.
- Produces:
  - `load_conversion_table(path: Path, dialect: str | None) -> tuple[list[tuple[str, str]], str]` → (`[(src, tgt), ...]`, column used). Key column is the TSV's first field. Skips rows whose target is empty or `NA`.
  - `audit(original: Orthography, output: Orthography, rows: list[tuple[str, str]], dialect: str | None) -> Report`.

Audit logic per row: `src` missing from `original.ipa_of` → `UNKNOWN_SOURCE`; else `target_ipa` unmatched → `UNTOKENIZABLE`; else `reconcile` → `CONFIRMED`/`WARNING`/`MISMATCH`. Across rows: **merge** = one output IPA (safe form) reached from ≥2 distinct source IPAs (safe forms). **cant_encode** = output-profile IPA values (safe form) that appear as no source grapheme's IPA and are produced by no row target. **coverage_gap** = original grapheme with no conversion row and no identity passthrough (same grapheme in output with safe-equal IPA).

- [ ] **Step 1: Write the failing tests**

```python
def _ortho(tmp_path, name, rows, header=("letter", "default")):
    return vct.load_orthography(
        _tsv(tmp_path / name, list(header), [list(r) for r in rows]), "default")


def test_load_conversion_table_reads_rows(tmp_path):
    p = _tsv(tmp_path / "conv.tsv", ["original", "standard"],
             [["T", "tr"], ["x", "NA"], ["y", ""]])
    rows, column = vct.load_conversion_table(p, "standard")
    assert rows == [("T", "tr")]      # NA and empty targets skipped
    assert column == "standard"


def test_audit_confirmed_row(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["T", "ʈ"]])
    output = _ortho(tmp_path, "o.tsv", [["tr", "ʈ"]])
    report = vct.audit(original, output, [("T", "tr")], "default")
    assert report.rows[0].verdict == vct.Verdict.CONFIRMED


def test_audit_unknown_source(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["T", "ʈ"]])
    output = _ortho(tmp_path, "o.tsv", [["tr", "ʈ"]])
    report = vct.audit(original, output, [("Z", "tr")], "default")
    assert report.rows[0].verdict == vct.Verdict.UNKNOWN_SOURCE


def test_audit_untokenizable_target(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["T", "ʈ"]])
    output = _ortho(tmp_path, "o.tsv", [["tr", "ʈ"]])
    report = vct.audit(original, output, [("T", "qq")], "default")
    assert report.rows[0].verdict == vct.Verdict.UNTOKENIZABLE


def test_audit_detects_phoneme_merge(tmp_path):
    # two distinct source IPAs (s, z) both land on output IPA s.
    original = _ortho(tmp_path, "s.tsv", [["s", "s"], ["z", "z"]])
    output = _ortho(tmp_path, "o.tsv", [["c", "s"]])
    report = vct.audit(original, output, [("s", "c"), ("z", "c")], "default")
    assert any(out_ipa == "s" for out_ipa, _ in report.merges)


def test_audit_detects_cant_encode(tmp_path):
    # output distinguishes /p/ and /b/; source can only ever produce /p/.
    original = _ortho(tmp_path, "s.tsv", [["p", "p"]])
    output = _ortho(tmp_path, "o.tsv", [["p", "p"], ["b", "b"]])
    report = vct.audit(original, output, [("p", "p")], "default")
    assert "b" in report.cant_encode
    assert "p" not in report.cant_encode


def test_audit_coverage_gap_and_identity_passthrough(tmp_path):
    # 'a' has no row but is identical in output -> passthrough, no gap.
    # 'q' has no row and no matching output grapheme -> gap.
    original = _ortho(tmp_path, "s.tsv", [["a", "a"], ["q", "q"]])
    output = _ortho(tmp_path, "o.tsv", [["a", "a"]])
    report = vct.audit(original, output, [], "default")
    gaps = {g for g, _ in report.coverage_gaps}
    assert gaps == {"q"}
```

Note: covers spec Tests #10 (merge), #11 (cant-encode), #12 (unknown source), #14 (coverage gap), #15 (identity passthrough), plus loader.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: FAIL — `AttributeError: ... 'load_conversion_table'`.

- [ ] **Step 3: Write minimal implementation** (append to the module)

```python
def load_conversion_table(
    path: Path, dialect: str | None
) -> tuple[list[tuple[str, str]], str]:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        key = fieldnames[0]
        column = select_value_column(fieldnames, dialect, key=key)
        rows: list[tuple[str, str]] = []
        for row in reader:
            src = (row.get(key) or "").strip()
            tgt = (row.get(column) or "").strip()
            if not src or tgt in ("", "NA"):
                continue
            rows.append((src, tgt))
    return rows, column


def audit(
    original: Orthography,
    output: Orthography,
    rows: list[tuple[str, str]],
    dialect: str | None,
) -> Report:
    report = Report(dialect=dialect)
    out_ipa_to_src_ipas: dict[str, set[str]] = {}
    for src, tgt in rows:
        src_ipa = original.ipa_of.get(src)
        if src_ipa is None:
            report.rows.append(RowResult(src, tgt, Verdict.UNKNOWN_SOURCE, None, None))
            continue
        tgt_ipa, unmatched = target_ipa(tgt, output)
        if tgt_ipa is None:
            report.rows.append(
                RowResult(src, tgt, Verdict.UNTOKENIZABLE, src_ipa, None,
                          unmatched=tuple(unmatched))
            )
            continue
        verdict, reason = reconcile(src_ipa, tgt_ipa)
        report.rows.append(RowResult(src, tgt, verdict, src_ipa, tgt_ipa, reason))
        out_ipa_to_src_ipas.setdefault(
            canonical_safe(tgt_ipa), set()
        ).add(canonical_safe(src_ipa))

    report.merges = sorted(
        (out_ipa, sorted(src_ipas))
        for out_ipa, src_ipas in out_ipa_to_src_ipas.items()
        if len(src_ipas) > 1
    )

    producible = {canonical_safe(v) for v in original.ipa_of.values()}
    producible |= set(out_ipa_to_src_ipas.keys())
    report.cant_encode = sorted(
        {canonical_safe(v) for v in output.ipa_of.values()} - producible
    )

    converted = {src for src, _ in rows}
    for grapheme, ipa in original.ipa_of.items():
        if grapheme in converted:
            continue
        out_ipa = output.ipa_of.get(grapheme)
        if out_ipa is not None and canonical_safe(out_ipa) == canonical_safe(ipa):
            continue
        report.coverage_gaps.append((grapheme, ipa))
    report.coverage_gaps.sort()
    return report
```

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: PASS (21 tests total).

- [ ] **Step 5: Commit**

```bash
git add QC/validation/validate_conversion_table.py tests/validators/test_validate_conversion_table.py
git commit -m "Add conversion-table loader + audit engine (verdicts, merges, coverage)"
```

---

### Task 5: Report renderer + per-dialect driver + CLI

**Files:**
- Modify: `QC/validation/validate_conversion_table.py`
- Test: `tests/validators/test_validate_conversion_table.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `output_dialects(path: Path) -> list[str | None]` — real per-dialect columns of the output profile (value columns minus `default`/`IPA`); `[None]` when the profile has only a fallback/single column.
  - `render_report(reports: list[Report]) -> str` — markdown with the spec's sections.
  - `run(original_path, output_path, table_path) -> tuple[str, int]` — build reports across dialects, render, compute exit code (1 iff any report has blocking rows).
  - `main(argv: list[str] | None = None) -> int` — argparse (`original`, `output`, `conversion_table` positionals; `--output` optional), prints or writes the report, returns exit code. Module ends with `if __name__ == "__main__": sys.exit(main())`.

- [ ] **Step 1: Write the failing tests**

```python
def test_output_dialects_lists_real_dialects(tmp_path):
    p = _tsv(tmp_path / "o.tsv", ["letter", "Wutai", "Eastern", "default"],
             [["a", "a", "a", "a"]])
    assert vct.output_dialects(p) == ["Wutai", "Eastern"]


def test_output_dialects_single_column_returns_none(tmp_path):
    p = _tsv(tmp_path / "o.tsv", ["letter", "IPA"], [["a", "a"]])
    assert vct.output_dialects(p) == [None]


def test_render_report_has_documented_sections(tmp_path):
    original = _ortho(tmp_path, "s.tsv", [["a", "a"]])
    output = _ortho(tmp_path, "o.tsv", [["a", "a"]])
    report = vct.audit(original, output, [("a", "a")], None)
    text = vct.render_report([report])
    for heading in ("Summary", "Confirmed", "Warnings", "Unresolved",
                    "Information loss", "Coverage", "Table integrity"):
        assert heading in text


def _write_trio(tmp_path, src_rows, out_rows, conv_rows,
                src_h=("letter", "IPA"), out_h=("letter", "default"),
                conv_h=("original", "standard")):
    src = _tsv(tmp_path / "src.tsv", list(src_h), [list(r) for r in src_rows])
    out = _tsv(tmp_path / "out.tsv", list(out_h), [list(r) for r in out_rows])
    conv = _tsv(tmp_path / "conv.tsv", list(conv_h), [list(r) for r in conv_rows])
    return src, out, conv


def _run_cli(src, out, conv):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(src), str(out), str(conv)],
        capture_output=True, text=True,
    )


def test_cli_exit_zero_when_only_warnings(tmp_path):
    # a: (/aː/) -> aa (/aa/) is a warning, not a mismatch.
    src, out, conv = _write_trio(
        tmp_path,
        src_rows=[["a", "a"], [":", "ː"]],
        out_rows=[["a", "a"]],
        conv_rows=[["a:", "aa"]],
    )
    result = _run_cli(src, out, conv)
    assert result.returncode == 0
    assert "length" in result.stdout


def test_cli_exit_nonzero_on_mismatch(tmp_path):
    src, out, conv = _write_trio(
        tmp_path,
        src_rows=[["p", "p"]],
        out_rows=[["b", "b"]],
        conv_rows=[["p", "b"]],
    )
    result = _run_cli(src, out, conv)
    assert result.returncode == 1


def test_cli_smoke_on_real_rukai_files():
    repo = Path(__file__).resolve().parents[2]
    src = repo / "Orthographies" / "Li" / "Rukai.tsv"
    out = repo / "Orthographies" / "Ortho113" / "Rukai.tsv"
    conv = repo / "Orthographies" / "ConversionTables" / "Rukai_Li_113.tsv"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(src), str(out), str(conv)],
        capture_output=True, text=True,
    )
    assert "Summary" in result.stdout
    # a: -> aa is a length-doubling equivalence, reported as a warning.
    assert "a:" in result.stdout
```

Note: covers spec Tests #16 (sections), #17 (exit-0 warnings), #18 (real-file smoke), plus dialect driver and CLI exit contract.

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: FAIL — `AttributeError: ... 'output_dialects'` and CLI tests failing (`SCRIPT` has no `main`).

- [ ] **Step 3: Write minimal implementation** (append to the module)

```python
def output_dialects(path: Path) -> list[str | None]:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
    dialects = [
        c for c in fieldnames
        if c != "letter" and c not in _FALLBACK_COLUMNS
    ]
    return dialects or [None]


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (none)"


def render_report(reports: list[Report]) -> str:
    lines: list[str] = ["# Conversion-table audit", ""]
    total_blocking = sum(len(r.blocking()) for r in reports)
    lines.append("## Summary")
    lines.append(f"Result: {'FAIL' if total_blocking else 'PASS'}")
    for report in reports:
        label = report.dialect or "(single column)"
        counts: dict[Verdict, int] = {}
        for row in report.rows:
            counts[row.verdict] = counts.get(row.verdict, 0) + 1
        summary = ", ".join(f"{v.value}={counts.get(v, 0)}" for v in Verdict)
        lines.append(f"- **{label}**: {summary}")
    lines.append("")

    for report in reports:
        label = report.dialect or "(single column)"
        lines.append(f"## Dialect: {label}")

        def rows_for(verdict: Verdict) -> list[str]:
            return [
                f"`{r.src}` → `{r.tgt}` ({r.src_ipa} / {r.tgt_ipa})"
                + (f" — {r.reason}" if r.reason else "")
                for r in report.rows if r.verdict == verdict
            ]

        lines.append("### Confirmed equivalences")
        lines.append(_bullet_lines(rows_for(Verdict.CONFIRMED)))
        lines.append("### Warnings — assumed equivalences")
        lines.append(_bullet_lines(rows_for(Verdict.WARNING)))
        lines.append("### Unresolved mismatches")
        lines.append(_bullet_lines(rows_for(Verdict.MISMATCH)))
        lines.append("### Information loss")
        loss = [f"merge: {ipa} ← {', '.join(srcs)}" for ipa, srcs in report.merges]
        loss += [f"cannot encode: {ipa}" for ipa in report.cant_encode]
        lines.append(_bullet_lines(loss))
        lines.append("### Coverage")
        lines.append(_bullet_lines(
            [f"`{g}` ({ipa}) has no conversion route" for g, ipa in report.coverage_gaps]
        ))
        lines.append("### Table integrity")
        integrity = [
            f"unknown source `{r.src}`"
            for r in report.rows if r.verdict == Verdict.UNKNOWN_SOURCE
        ] + [
            f"untokenizable target `{r.tgt}` (missing {' '.join(r.unmatched)})"
            for r in report.rows if r.verdict == Verdict.UNTOKENIZABLE
        ]
        lines.append(_bullet_lines(integrity))
        lines.append("")
    return "\n".join(lines)


def run(
    original_path: Path, output_path: Path, table_path: Path
) -> tuple[str, int]:
    reports = []
    for dialect in output_dialects(output_path):
        original = load_orthography(original_path, dialect)
        output = load_orthography(output_path, dialect)
        rows, _column = load_conversion_table(table_path, dialect)
        reports.append(audit(original, output, rows, dialect))
    text = render_report(reports)
    exit_code = 1 if any(r.blocking() for r in reports) else 0
    return text, exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path, help="original orthography TSV")
    parser.add_argument("output", type=Path, help="output orthography TSV")
    parser.add_argument("conversion_table", type=Path, help="conversion table TSV")
    parser.add_argument("--output", dest="report_path", type=Path, default=None,
                        help="write the report here instead of stdout")
    args = parser.parse_args(argv)
    text, exit_code = run(args.original, args.output, args.conversion_table)
    if args.report_path:
        args.report_path.write_text(text, encoding="utf-8")
    else:
        print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/validators/test_validate_conversion_table.py -v`
Expected: PASS (all tests). If `test_cli_smoke_on_real_rukai_files` fails because the real table produces a genuine mismatch/integrity error (exit 1), that is a real finding — inspect the printed report and, per the spec, either confirm it is a true defect (leave the test asserting only the report content, not returncode — the test above already does not assert returncode) or adjust. Do NOT weaken a mismatch to pass; the smoke test only asserts the report renders and mentions `a:`.

- [ ] **Step 5: Commit**

```bash
git add QC/validation/validate_conversion_table.py tests/validators/test_validate_conversion_table.py
git commit -m "Add report renderer, per-dialect driver, and CLI"
```

---

### Task 6: Run the real Rukai audit and record findings

**Files:**
- Modify: `docs/superpowers/specs/2026-08-09-conversion-table-validator-design.md` (append a "First run" note) OR write `claudeplans/conversion-table-rukai-li-findings.md` if there are actionable defects.

**Interfaces:** none (analysis task).

- [ ] **Step 1: Run the tool against every existing conversion table**

Run:
```bash
for conv in Orthographies/ConversionTables/*_113.tsv; do
  echo "=== $conv ===";
done
```
Then, for the Rukai/Li trio and any others where both orthography profiles exist, run the CLI and read the report. Determine language + source scheme from each conversion table's filename (`<Language>_<Scheme>_113.tsv`) and locate `Orthographies/<Scheme>/<Language>.tsv` + `Orthographies/Ortho113/<Language>.tsv`.

- [ ] **Step 2: Triage**

For each Unresolved mismatch / integrity error: decide whether it is a real table defect (fix the TSV in a follow-up) or a limitation of the checker's IPA model (record it). Warnings and coverage gaps are informational — summarize counts.

- [ ] **Step 3: Record findings**

Write a short markdown summary (counts per language, notable mismatches) to `claudeplans/conversion-table-audit-findings.md`. Do NOT edit conversion tables or orthography profiles in this task — corrections are separate, reviewed changes.

- [ ] **Step 4: Commit**

```bash
git add claudeplans/conversion-table-audit-findings.md
git commit -m "Record first conversion-table audit findings"
```

---

## Self-Review

**Spec coverage:**
- Inputs / three positional args + `--output` → Task 5 `main`. ✓
- Data shapes (profile, conversion table) → Tasks 2, 4 loaders. ✓
- Core model / transitive IPA + target re-tokenization → Tasks 2, 4. ✓
- Verdict tiers (Confirmed / Warning / Unresolved) + safe vs. segmentation-changing normalization → Task 3. ✓
- Phoneme merge, original-can't-encode, coverage gap, unknown source, untokenizable → Task 4. ✓
- Exit contract (nonzero on MISMATCH / UNKNOWN_SOURCE / UNTOKENIZABLE only) → Task 4 `Report.blocking`, Task 5 `run`; tests `test_cli_exit_*`. ✓
- Per-dialect evaluation with fallback → Task 1 `select_value_column`, Task 5 `output_dialects`/`run`. ✓
- Report sections → Task 5 `render_report`; test `test_render_report_has_documented_sections`. ✓
- All 18 spec tests map to tasks: #1→T1, #2→T1, #3→T1, #4→T3, #5→T2, #6→T3, #7→T3, #8→T3, #9→T3, #10→T4, #11→T4, #12→T4, #13→T2, #14→T4, #15→T4, #16→T5, #17→T5, #18→T5. ✓ (Spec's single test #7 is split into `test_tiebar_ligature_is_confirmed` + `test_bare_digraph_affricate_is_warning`; spec's #9 mismatch is `test_true_mismatch`.)

**Placeholder scan:** No TBD/TODO; all code steps carry runnable code. ✓

**Type consistency:** `Orthography.ipa_of: dict[str,str]`, `load_orthography`/`load_conversion_table` return types, `Verdict` members, and `Report` fields are used identically across Tasks 1–5. `select_value_column(fieldnames, dialect, key)` signature matches all three call sites (profile key=`"letter"`, table key=`fieldnames[0]`). ✓
