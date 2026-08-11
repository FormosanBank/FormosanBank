# Case-Aware Standardization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** standardize.py auto-derives Title-case and ALL-CAPS variants of conversion-table rules (suppressed for phonemic capitals declared in the source orthography profile), and the published tables lose their now-redundant uppercase rows.

**Architecture:** A new pure-function module `QC/utilities/_case_variants.py` (profile resolution from the table filename, profile grapheme loading, rule expansion) is wired into `standardize.py`'s table-loading path. Table cleanup is a one-time uncommitted script; behavior preservation is proven by an uncommitted equivalence harness before any table edit is committed.

**Tech Stack:** Python 3.13 (repo `.venv`), stdlib only (`csv`, `re`, `pathlib`), pytest.

Spec: `docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md`

## Global Constraints

- Work in the worktree `/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/.claude/worktrees/standardize-capitalization` on branch `feature/standardize-capitalization`. All paths below are relative to it.
- Activate the venv before any Python: `source /Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/.venv/bin/activate`.
- Commit with `git -c commit.gpgsign=false commit …` (no TTY for gpg pinentry) and end commit messages with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Commit messages are plain sentences (repo style), not conventional-commit prefixes.
- The harness and cleanup scripts are **never committed**; they live in the session scratchpad `/private/tmp/claude-502/-Users-jkhartshorne-Documents-Projects-Formosan-FormosanBank/51632d6e-cefe-486e-96c4-ac8300e8e39e/scratchpad/`.
- Do not touch `Orthographies/ConversionTables/Saisiyat_folk_113 2.tsv` (stray file, out of scope).
- Derivation requires BOTH conventions: basename `<Language>_<Scheme>_113.tsv` AND the table living in a directory named `ConversionTables`. Either missing → warn + status-quo behavior (no derivation). This keeps existing tests (`tiny_mapping.tsv` in `tests/fixtures/`) passing unchanged.

---

### Task 1: Profile resolution + grapheme loading (`_case_variants.py`)

**Files:**
- Create: `QC/utilities/_case_variants.py`
- Test: `tests/utilities/test_case_variants.py`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces: `resolve_source_profile(tsv_path: str | Path) -> Path | None` (None = conventions not met; returned Path may not exist — caller checks), `load_profile_graphemes(profile_path) -> set[str]`, module constant `SCHEME_FOLDERS`.

- [ ] **Step 1: Write the failing tests**

Create `tests/utilities/test_case_variants.py`:

```python
"""Tests for QC/utilities/_case_variants.py.

Case-variant derivation lets conversion tables list only lowercase rules;
standardize.py derives Title/ALL-CAPS variants unless the capital is a
distinct grapheme of the source orthography (per the source profile,
resolved from the table's filename).
Spec: docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md
"""
from pathlib import Path

from QC.utilities._case_variants import (
    load_profile_graphemes,
    resolve_source_profile,
)


def _table(tmp_path, name):
    conv = tmp_path / "Orthographies" / "ConversionTables"
    conv.mkdir(parents=True, exist_ok=True)
    path = conv / name
    path.write_text("original\tstandard\n", encoding="utf-8")
    return path


def test_scheme_token_94_maps_to_ortho94_folder(tmp_path):
    table = _table(tmp_path, "Amis_94_113.tsv")
    assert resolve_source_profile(table) == (
        tmp_path / "Orthographies" / "Ortho94" / "Amis.tsv"
    )


def test_scheme_token_113lib_maps_to_ortho113liberal_folder(tmp_path):
    table = _table(tmp_path, "Amis_113lib_113.tsv")
    assert resolve_source_profile(table) == (
        tmp_path / "Orthographies" / "Ortho113Liberal" / "Amis.tsv"
    )


def test_named_scheme_token_is_the_folder_itself(tmp_path):
    table = _table(tmp_path, "Rukai_Li_113.tsv")
    assert resolve_source_profile(table) == (
        tmp_path / "Orthographies" / "Li" / "Rukai.tsv"
    )


def test_nonconforming_basename_returns_none(tmp_path):
    table = _table(tmp_path, "tiny_mapping.tsv")
    assert resolve_source_profile(table) is None


def test_table_outside_conversiontables_dir_returns_none(tmp_path):
    path = tmp_path / "Amis_94_113.tsv"
    path.write_text("original\tstandard\n", encoding="utf-8")
    assert resolve_source_profile(path) is None


def test_resolution_does_not_require_the_profile_to_exist(tmp_path):
    """resolve returns the conventional path; existence is the caller's check."""
    table = _table(tmp_path, "Kavalan_MinEd_113.tsv")
    profile = resolve_source_profile(table)
    assert profile == tmp_path / "Orthographies" / "MinEd" / "Kavalan.tsv"
    assert not profile.exists()


def test_load_profile_graphemes_reads_letter_column(tmp_path):
    profile = tmp_path / "Rukai.tsv"
    profile.write_text(
        "letter\tWutai\tDona\nT\ttr\ttr\nng\tŋ\tŋ\n\t\t\n",
        encoding="utf-8",
    )
    assert load_profile_graphemes(profile) == {"T", "ng"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/utilities/test_case_variants.py -v`
Expected: FAIL at import time — `ModuleNotFoundError: No module named 'QC.utilities._case_variants'`

- [ ] **Step 3: Write the implementation**

Create `QC/utilities/_case_variants.py`:

```python
"""Case-variant derivation for conversion-table standardization.

standardize.py applies conversion-table rules with literal, case-sensitive
str.replace, so a rule ``o -> u`` never converts sentence-initial ``O``.
This module derives Title-case and ALL-CAPS variants of lowercase rules —
except where a capital is a distinct grapheme of the source orthography
(e.g. Li's Rukai ``T`` = /ʈ/), detected via the source orthography
profile resolved from the conversion table's filename.

Spec: docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md
"""
import csv
import re
from pathlib import Path

# Scheme tokens whose Orthographies/ folder is not simply the token itself.
SCHEME_FOLDERS = {"94": "Ortho94", "113": "Ortho113", "113lib": "Ortho113Liberal"}

_TABLE_NAME = re.compile(r"^(?P<language>[^_]+)_(?P<scheme>[^_]+)_113\.tsv$")


def resolve_source_profile(tsv_path):
    """Conventional source-profile path for a conversion table, or None.

    Requires both published conventions: basename
    ``<Language>_<Scheme>_113.tsv`` and a parent directory named
    ``ConversionTables`` (so the ``Orthographies/`` root is its parent).
    The returned path may not exist — existence is the caller's check.
    """
    tsv_path = Path(tsv_path)
    match = _TABLE_NAME.match(tsv_path.name)
    if match is None or tsv_path.parent.name != "ConversionTables":
        return None
    folder = SCHEME_FOLDERS.get(match["scheme"], match["scheme"])
    return tsv_path.parent.parent / folder / f"{match['language']}.tsv"


def load_profile_graphemes(profile_path):
    """The set of graphemes in an orthography profile's ``letter`` column."""
    with open(profile_path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return {
            row["letter"].strip()
            for row in reader
            if row.get("letter") and row["letter"].strip()
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/utilities/test_case_variants.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/_case_variants.py tests/utilities/test_case_variants.py
git -c commit.gpgsign=false commit -m "Add source-profile resolution for conversion tables

Resolve Orthographies/<folder>/<Language>.tsv from a conversion table's
<Language>_<Scheme>_113.tsv basename (94->Ortho94, 113lib->Ortho113Liberal),
plus a loader for the profile's letter column. Groundwork for case-aware
standardization.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Rule expansion (`derive_case_variants`)

**Files:**
- Modify: `QC/utilities/_case_variants.py` (append function)
- Test: `tests/utilities/test_case_variants.py` (append tests)

**Interfaces:**
- Consumes: nothing new.
- Produces: `derive_case_variants(rules: list[tuple[str, str]], profile_graphemes: set[str]) -> list[tuple[str, str]]` — returns a NEW list; input untouched.

- [ ] **Step 1: Write the failing tests**

Append to `tests/utilities/test_case_variants.py` (add `derive_case_variants` to the existing import):

```python
def test_title_and_allcaps_variants_derived_for_digraph():
    rules = [("ng", "ŋ")]
    assert derive_case_variants(rules, set()) == [
        ("ng", "ŋ"),
        ("Ng", "Ŋ"),   # title: first char of replacement uppercased
        ("NG", "Ŋ"),   # ALL-CAPS: whole replacement uppercased
    ]


def test_single_letter_source_gets_one_variant():
    """Title and ALL-CAPS coincide for one-letter sources — no duplicate."""
    assert derive_case_variants([("o", "u")], set()) == [("o", "u"), ("O", "U")]


def test_explicit_uppercase_row_suppresses_derivation():
    rules = [("ng", "ŋ"), ("Ng", "ŋ")]
    assert derive_case_variants(rules, set()) == [
        ("ng", "ŋ"),
        ("NG", "Ŋ"),   # ALL-CAPS still derived; title was explicit
        ("Ng", "ŋ"),   # explicit row kept verbatim, in place
    ]


def test_profile_grapheme_suppresses_derivation():
    """Li Rukai: T is phonemic — t's rule must not spawn a T variant."""
    assert derive_case_variants([("t", "c")], {"T"}) == [("t", "c")]


def test_uncased_source_is_not_derived():
    assert derive_case_variants([("'", "q")], set()) == [("'", "q")]


def test_mixed_case_source_is_not_derived():
    """Only fully-lowercase sources derive variants."""
    assert derive_case_variants([("Ng", "ŋ")], set()) == [("Ng", "ŋ")]


def test_caseless_replacement_passes_through():
    """A cased source with an uncased replacement still derives variants."""
    assert derive_case_variants([("q", "ʔ")], set()) == [
        ("q", "ʔ"),
        ("Q", "ʔ"),
    ]


def test_empty_replacement_deletion_rule():
    assert derive_case_variants([("h", "")], set()) == [("h", ""), ("H", "")]


def test_variants_inserted_immediately_after_parent():
    rules = [("o", "u"), ("ng", "ŋ")]
    assert derive_case_variants(rules, set()) == [
        ("o", "u"),
        ("O", "U"),
        ("ng", "ŋ"),
        ("Ng", "Ŋ"),
        ("NG", "Ŋ"),
    ]


def test_input_list_is_not_mutated():
    rules = [("o", "u")]
    derive_case_variants(rules, set())
    assert rules == [("o", "u")]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/utilities/test_case_variants.py -v`
Expected: the 10 new tests FAIL with `ImportError: cannot import name 'derive_case_variants'`; the 7 Task-1 tests still pass.

- [ ] **Step 3: Write the implementation**

Append to `QC/utilities/_case_variants.py`:

```python
def _title(text):
    return text[:1].upper() + text[1:]


def derive_case_variants(rules, profile_graphemes):
    """Expand (source, replacement) rules with derived capital variants.

    For each fully-lowercase source, append a Title-case variant
    (first char of source and replacement uppercased) and an ALL-CAPS
    variant (both fully uppercased) immediately after it. A variant is
    suppressed when its source is an explicit rule source elsewhere in
    the table, a grapheme of the source orthography profile (phonemic
    capital), or already emitted (single-letter title == ALL-CAPS).
    Returns a new list; ``rules`` is not mutated.
    """
    explicit = {source for source, _ in rules}
    expanded = []
    emitted = set()
    for source, replacement in rules:
        expanded.append((source, replacement))
        emitted.add(source)
        if not source.islower():
            # islower() is False for uncased sources like "'" and for
            # anything already containing a capital.
            continue
        for variant, variant_replacement in (
            (_title(source), _title(replacement)),
            (source.upper(), replacement.upper()),
        ):
            if (
                variant in explicit
                or variant in profile_graphemes
                or variant in emitted
            ):
                continue
            expanded.append((variant, variant_replacement))
            emitted.add(variant)
    return expanded
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/utilities/test_case_variants.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/_case_variants.py tests/utilities/test_case_variants.py
git -c commit.gpgsign=false commit -m "Derive Title/ALL-CAPS variants of lowercase conversion rules

Variants are suppressed for explicit table rows, for capitals the source
profile declares as distinct graphemes (phonemic capitals), and for
single-letter duplicates. Derived pairs sit directly after their parent
rule so they inherit its replacement priority.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Wire derivation into standardize.py

**Files:**
- Modify: `QC/utilities/standardize.py` (import block near line 18; the TSV-loading `else` branch near lines 139–143; the per-file rule-loading block near lines 234–245)
- Test: `tests/utilities/test_standardize.py` (append tests)

**Interfaces:**
- Consumes: all three Task-1/2 functions.
- Produces: standardize.py behavior — in `--tsv_path` mode, rules are expanded via `derive_case_variants` when the source profile resolves and exists; otherwise a warning line starting with `Warning:` is printed once and behavior is unchanged. `--copy` / `--remove_accents` are untouched.

- [ ] **Step 1: Write the failing tests**

Append to `tests/utilities/test_standardize.py`:

```python
def _write_case_fixture(tmp_path, xml_text):
    """Build Orthographies/{ConversionTables,Ortho94}/ + a collection root.

    Table rules: o->u, ng->ŋ, t->c. Profile declares T a distinct
    grapheme, so t must not spawn a T variant.
    Returns (table_path, collection_root, xml_path).
    """
    conv = tmp_path / "Orthographies" / "ConversionTables"
    prof = tmp_path / "Orthographies" / "Ortho94"
    conv.mkdir(parents=True)
    prof.mkdir(parents=True)
    table = conv / "Amis_94_113.tsv"
    table.write_text(
        "original\tstandard\no\tu\nng\tŋ\nt\tc\n", encoding="utf-8"
    )
    prof.joinpath("Amis.tsv").write_text(
        "letter\tstandard\nT\tʈ\no\to\nng\tŋ\nt\tt\n",
        encoding="utf-8",
    )
    collection = tmp_path / "collection"
    xml_dir = collection / "XML"
    xml_dir.mkdir(parents=True)
    xml_path = xml_dir / "doc.xml"
    xml_path.write_text(xml_text, encoding="utf-8")
    return table, collection, xml_path


_CASE_XML = (
    '<?xml version="1.0"?>\n'
    '<TEXT id="t" xml:lang="ami">\n'
    '  <S id="s1"><FORM kindOf="original">O to ngi NGA Ti</FORM></S>\n'
    "</TEXT>\n"
)


def test_case_variants_applied_from_conforming_table(tmp_path):
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    proc = _run_standardize([
        "--tsv_path", str(table),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    # o->u converts 'o' and (derived) 'O'; ng->ŋ converts 'ngi' and
    # (derived ALL-CAPS) 'NGA' -> 'ŊA'; t->c converts lowercase 't'
    # ('to' became 'tu' after o->u, then 'cu') but the profile's phonemic
    # 'T' in 'Ti' must survive untouched.
    assert _standard_forms(xml_path) == ["U cu ŋi ŊA Ti"]


def test_nonconforming_table_name_warns_and_derives_nothing(tmp_path):
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    plain = table.with_name("tiny_mapping.tsv")
    table.rename(plain)
    proc = _run_standardize([
        "--tsv_path", str(plain),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "Warning:" in proc.stdout and "NOT be derived" in proc.stdout
    # Status quo: lowercase rules apply, capitals pass through.
    assert _standard_forms(xml_path) == ["O cu ŋi NGA Ti"]


def test_missing_profile_warns_and_derives_nothing(tmp_path):
    table, collection, xml_path = _write_case_fixture(tmp_path, _CASE_XML)
    (tmp_path / "Orthographies" / "Ortho94" / "Amis.tsv").unlink()
    proc = _run_standardize([
        "--tsv_path", str(table),
        "--target_column", "standard",
        "--corpora_path", str(collection),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert "Warning:" in proc.stdout and "NOT be derived" in proc.stdout
    assert _standard_forms(xml_path) == ["O cu ŋi NGA Ti"]
```

Walkthrough of the first test's expected value, rule by rule over
`O to ngi NGA Ti` (derived rules marked *):

| rule | text after |
|---|---|
| `o→u` | `O tu ngi NGA Ti` |
| *`O→U` | `U tu ngi NGA Ti` |
| `ng→ŋ` | `U tu ŋi NGA Ti` |
| *`Ng→Ŋ` | (no match) |
| *`NG→Ŋ` | `U tu ŋi ŊA Ti` |
| `t→c` | `U cu ŋi ŊA Ti` (profile suppresses any `T` variant) |

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/utilities/test_standardize.py -v`
Expected: the 3 new tests FAIL (first: standard form is `"O cu ŋi NGA Ti"` — no derivation yet; other two: missing `Warning:` in stdout). The 15 pre-existing tests still pass.

- [ ] **Step 3: Implement the wiring**

In `QC/utilities/standardize.py`, extend the existing `QC.utilities` import block (after the `strip_accents` import near line 18):

```python
from QC.utilities._case_variants import (  # noqa: E402
    derive_case_variants,
    load_profile_graphemes,
    resolve_source_profile,
)
```

In `main()`, replace the TSV-loading `else` branch (currently lines 139–143):

```python
    else:
        # Load the TSV file to get available columns
        with open(args.tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            available_columns = reader.fieldnames

        # Resolve the source-orthography profile from the table's filename
        # so capital-letter variants of lowercase rules can be derived —
        # except for capitals the profile declares as distinct graphemes.
        profile_graphemes = None
        profile_path = resolve_source_profile(args.tsv_path)
        if profile_path is None:
            print(
                f"Warning: {os.path.basename(args.tsv_path)} does not follow the "
                "Orthographies/ConversionTables/<Language>_<Scheme>_113.tsv "
                "convention; capital-letter variants will NOT be derived."
            )
        elif not profile_path.exists():
            print(
                f"Warning: source orthography profile not found at {profile_path}; "
                "capital-letter variants will NOT be derived."
            )
        else:
            profile_graphemes = load_profile_graphemes(profile_path)
```

In the per-file rule-loading block (currently lines 234–245), after the `standard.append((original_value, standard_value))` loop completes, add:

```python
                        if profile_graphemes is not None:
                            standard = derive_case_variants(standard, profile_graphemes)
```

(Immediately before the `# Iterate over all <S> elements` comment, at the same indentation as the `with open(args.tsv_path), …` statement above it.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/utilities/test_standardize.py tests/utilities/test_case_variants.py -v`
Expected: 35 passed (18 standardize + 17 case-variants).

Watch `test_reviewed_source_conversion_tables` especially: it runs the REAL
tables, and derivation is now active for `Rukai_Li_113.tsv`,
`Bunun_Huang_113.tsv`, and `Seediq_Ochiai_113.tsv` (their source profiles
exist). Their expected outputs must be UNCHANGED — the inputs contain no
derivable capitals (`T`/`D` in the Rukai case are phonemic, suppressed by
the Li profile). If any of these fail, the derivation logic is wrong;
investigate — do not edit the test expectations.

- [ ] **Step 5: Run the full suite to catch regressions**

Run: `python -m pytest tests/ -q`
Expected: everything passes (baseline was 769 passed, 3 skipped; now 789 passed, 3 skipped with the 20 new tests from Tasks 1–3). If anything else fails, stop and investigate before committing.

- [ ] **Step 6: Commit**

```bash
git add QC/utilities/standardize.py tests/utilities/test_standardize.py
git -c commit.gpgsign=false commit -m "Apply derived capital variants in standardize.py

In --tsv_path mode, resolve the source profile from the table filename
and expand the loaded rules with Title/ALL-CAPS variants. Non-conforming
table paths or a missing profile warn and fall back to the exact old
behavior. --copy and --remove_accents are unchanged.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Equivalence harness (uncommitted) — phase 1 run

**Files:**
- Create: `/private/tmp/claude-502/-Users-jkhartshorne-Documents-Projects-Formosan-FormosanBank/51632d6e-cefe-486e-96c4-ac8300e8e39e/scratchpad/equivalence_harness.py` (NOT committed)

**Interfaces:**
- Consumes: `resolve_source_profile`, `load_profile_graphemes`, `derive_case_variants`; git HEAD blobs of the tables.
- Produces: exit 0 + report when no hard failures; exit 1 listing `(table, column, probe, old, new)` otherwise. Task 5 reruns it after cleanup.

- [ ] **Step 1: Write the harness**

```python
"""Equivalence harness for case-aware standardization. NOT FOR COMMIT.

Compares OLD behavior (git-HEAD table, literal rules — the pre-feature
code path) against NEW behavior (working-tree table + derive_case_variants)
for every value column of every published conversion table.

HARD FAILURE: any probe the OLD table handled (a lowercase rule source or
an explicit uppercase row) whose output changed.
REPORT ONLY: probes the old table did not map (derived Title/ALL-CAPS
forms) that now convert — the intended new coverage.

Usage: python equivalence_harness.py /path/to/worktree
"""
import csv
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO))
from QC.utilities._case_variants import (  # noqa: E402
    derive_case_variants,
    load_profile_graphemes,
    resolve_source_profile,
)

SKIP = {"Saisiyat_folk_113 2.tsv"}  # stray file, out of scope


def parse(text):
    reader = csv.DictReader(text.splitlines(), delimiter="\t")
    cols = [c for c in (reader.fieldnames or []) if c != "original"]
    return cols, list(reader)


def rules_for(rows, col):
    out = []
    for row in rows:
        src = (row.get("original") or "").strip()
        tgt = (row.get(col) or "").strip()
        if src:
            out.append((src, tgt))
    return out


def apply(rules, text):
    for src, tgt in rules:
        text = text.replace(src, tgt)
    return text


def title(s):
    return s[:1].upper() + s[1:]


failures, coverage = [], []
tables = sorted((REPO / "Orthographies" / "ConversionTables").glob("*.tsv"))
for table in tables:
    if table.name in SKIP:
        continue
    proc = subprocess.run(
        ["git", "-C", str(REPO), "show", f"HEAD:{table.relative_to(REPO)}"],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        print(f"note: {table.name} not in HEAD, skipping")
        continue
    old_cols, old_rows = parse(proc.stdout)
    new_cols, new_rows = parse(table.read_text(encoding="utf-8"))
    profile = resolve_source_profile(table)
    graphemes = (
        load_profile_graphemes(profile)
        if profile is not None and profile.exists()
        else None
    )
    for col in old_cols:
        old_rules = rules_for(old_rows, col)
        new_rules = rules_for(new_rows, col)
        if graphemes is not None:
            new_rules = derive_case_variants(new_rules, graphemes)
        old_sources = {s for s, _ in old_rules}
        for src in sorted(old_sources):
            for probe in sorted({src, title(src), src.upper()}):
                old_out = apply(old_rules, probe)
                new_out = apply(new_rules, probe)
                if old_out == new_out:
                    continue
                record = (table.name, col, probe, old_out, new_out)
                if probe in old_sources:
                    failures.append(record)
                else:
                    coverage.append(record)

print(f"\n{len(tables) - len(SKIP)} tables checked.")
if coverage:
    print(f"\nNEW COVERAGE ({len(coverage)} probes, intended improvement):")
    for rec in coverage:
        print("  %s [%s] %r: %r -> %r" % rec)
if failures:
    print(f"\nHARD FAILURES ({len(failures)}):")
    for rec in failures:
        print("  %s [%s] %r: OLD %r != NEW %r" % rec)
    sys.exit(1)
print("\nNo hard failures: old-covered behavior is preserved.")
```

- [ ] **Step 2: Run phase 1 (tables not yet cleaned)**

Run (from the worktree root, venv active):
`python <scratchpad>/equivalence_harness.py "$PWD"`
Expected: exit 0, `No hard failures`, and a NEW COVERAGE list (read it — every line should be a previously-unhandled capital now converting; anything surprising means stop and investigate). Explicit uppercase rows always win over derived variants, so phase 1 hard failures indicate a bug in `derive_case_variants` — fix before proceeding. Nothing to commit in this task.

---

### Task 5: Clean the published tables

**Files:**
- Create: `<scratchpad>/clean_uppercase_rows.py` (NOT committed)
- Modify: `Orthographies/ConversionTables/*.tsv` (whichever rows pass the identity test — expected from the audit: the `U`/`O` rows of `Amis_94_113.tsv`, `Amis_113lib_113.tsv`, `Amis_Church_113.tsv`; `Amis_Church_113.tsv`'s `G`; `Paiwan_Ferrell_113.tsv`'s `Ts`; possibly others the script proves)

**Interfaces:**
- Consumes: Task 1–2 functions; the harness from Task 4.
- Produces: cleaned tables, a printed keep/remove/flag report, and a passing phase-2 harness run.

- [ ] **Step 1: Write the cleanup script**

```python
"""One-time removal of derivable uppercase conversion-table rows. NOT FOR COMMIT.

A row is removed ONLY if derive_case_variants, run on the table without it,
regenerates the identical (source, replacement) pair in EVERY value column.
Rows whose capital the profile declares phonemic are kept silently; rows
that differ from their derivation are kept and FLAGGED for the maintainer.

Usage: python clean_uppercase_rows.py /path/to/worktree
"""
import csv
import sys
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(REPO))
from QC.utilities._case_variants import (  # noqa: E402
    derive_case_variants,
    load_profile_graphemes,
    resolve_source_profile,
)

SKIP = {"Saisiyat_folk_113 2.tsv"}


def parse_lines(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    cols = [c for c in header[1:]]
    return lines, header, cols


def rules_from_lines(lines, header, col, exclude_source=None):
    idx = header.index(col)
    out = []
    for line in lines[1:]:
        fields = line.split("\t")
        src = fields[0].strip() if fields else ""
        if not src or src == exclude_source:
            continue
        tgt = fields[idx].strip() if idx < len(fields) else ""
        out.append((src, tgt))
    return out


removed, flagged, phonemic = [], [], []
for table in sorted((REPO / "Orthographies" / "ConversionTables").glob("*.tsv")):
    if table.name in SKIP:
        continue
    profile = resolve_source_profile(table)
    if profile is None or not profile.exists():
        continue  # no derivation will ever run for this table; leave as-is
    graphemes = load_profile_graphemes(profile)
    lines, header, cols = parse_lines(table)
    keep = [lines[0]]
    for line in lines[1:]:
        fields = line.split("\t")
        src = fields[0].strip() if fields else ""
        if not src or src == src.lower():
            keep.append(line)          # lowercase/uncased/blank: never touched
            continue
        if src in graphemes:
            phonemic.append((table.name, src))
            keep.append(line)          # phonemic capital: keep silently
            continue
        identical = True
        for col in cols:
            idx = header.index(col)
            explicit_tgt = fields[idx].strip() if idx < len(fields) else ""
            base = rules_from_lines(lines, header, col, exclude_source=src)
            derived = dict(derive_case_variants(base, graphemes))
            if derived.get(src) != explicit_tgt:
                identical = False
                break
        if identical:
            removed.append((table.name, src))
        else:
            flagged.append((table.name, src, line))
            keep.append(line)
    if len(keep) != len(lines):
        table.write_text("\n".join(keep) + "\n", encoding="utf-8")

print(f"REMOVED ({len(removed)}):")
for name, src in removed:
    print(f"  {name}: {src}")
print(f"\nKEPT — phonemic capitals ({len(phonemic)}):")
for name, src in phonemic:
    print(f"  {name}: {src}")
print(f"\nKEPT AND FLAGGED — mapping differs from derivation ({len(flagged)}):")
for name, src, line in flagged:
    print(f"  {name}: {src}  (row: {line!r})")
```

- [ ] **Step 2: Run it and read the report**

Run: `python <scratchpad>/clean_uppercase_rows.py "$PWD"`
Expected removals (from the audit + table inspection): `Amis_94_113` `U`,`O`; `Amis_113lib_113` `U`,`O`; `Amis_Church_113` `U`,`O`,`G`; `Paiwan_Ferrell_113` `Ts`. Expected flagged: `Amis_Church_113` `Ng` (maps to `ŋ` where derivation gives `Ŋ`). Expected phonemic keeps include `Rukai_Li_113` `T`,`D`,`L` and the capitals of the other phonemic-capital tables whose profiles exist (`Puyuma_Folk`, `Puyuma_MinEd`, `Rukai_Church`, `Rukai_MinEd`, `Bunun_MinEd`, …) — a capital in one of those tables that is NOT in its profile will surface as flagged instead; that's the conservative path, not an error. Only `Saisiyat_Tsuchida_113` (profile `Tsuchida/Saisiyat.tsv` missing), `Kavalan_MinEd_113` (`MinEd/Kavalan.tsv` missing), and `Yami_Wakelin_113` (`Wakelin/Yami.tsv` missing) are skipped outright. The printed report is the source of truth — if it differs materially from these expectations, stop and show the maintainer before continuing.

- [ ] **Step 3: Run the harness (phase 2) against the cleaned tables**

Run: `python <scratchpad>/equivalence_harness.py "$PWD"`
Expected: exit 0, `No hard failures` — the removed rows' behavior is now supplied by derivation, byte-identical. Any hard failure: restore the tables (`git checkout -- Orthographies/ConversionTables/`), fix, re-run from Step 2.

- [ ] **Step 4: Review the diff and run the full suite**

Run: `git diff --stat Orthographies/ConversionTables/ && git diff Orthographies/ConversionTables/ | head -60`
Expected: only row deletions, only in the tables named by the report.
Run: `python -m pytest tests/ -q`
Expected: same pass count as Task 3 Step 5 (no test reads the removed rows).

- [ ] **Step 5: Commit the table cleanup**

```bash
git add Orthographies/ConversionTables/
git -c commit.gpgsign=false commit -m "Remove uppercase conversion rows now derived automatically

Each removed row is regenerated exactly by derive_case_variants (verified
by an old-vs-new equivalence harness over every value column of every
table). Phonemic capitals (Rukai_Li T/D/L etc.) and rows whose mapping
differs from the derivation (Amis_Church Ng->ŋ) are kept.

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Final verification and maintainer report

**Files:**
- None created; read-only checks.

- [ ] **Step 1: Full suite, clean tree**

Run: `python -m pytest tests/ -q` and `git status --short`
Expected: full suite passes; working tree clean (harness/cleanup scripts live in the scratchpad, not the repo).

- [ ] **Step 2: Smoke-run standardize.py against a real table**

Run (on a scratch copy — never the published corpora):

```bash
mkdir -p <scratchpad>/smoke/XML
cat > <scratchpad>/smoke/XML/doc.xml <<'EOF'
<?xml version="1.0"?>
<TEXT id="t" xml:lang="ami">
  <S id="s1"><FORM kindOf="original">O wawa</FORM></S>
</TEXT>
EOF
python QC/utilities/standardize.py \
  --tsv_path Orthographies/ConversionTables/Amis_94_113.tsv \
  --target_column Southern \
  --corpora_path <scratchpad>/smoke
grep -o 'kindOf="standard">[^<]*' <scratchpad>/smoke/XML/doc.xml
```

(`Amis_94_113.tsv`'s value columns are `Southern Xiuguluan Coastal Malan Hengchun`; Southern maps `o→u`.)

Expected: no `Warning:` about derivation, and the standard FORM shows `U wawa` — sentence-initial `O` converted by the derived variant even though the explicit `U`/`O` rows are now gone from the table.

- [ ] **Step 3: Report to the maintainer**

Summarize: rows removed per table, phonemic keeps, the flagged `Ng→ŋ` decision left open, tables skipped for missing profiles (their uppercase rows intentionally untouched), and the audit items this resolves for standardize.py (findings #5/#7 remain open on the validator side by design).
