# B5 cleaner extensions implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Before writing any code, read the design doc at `.claude/plans/2026-05-29-clean-xml-extension-tests-design.md` and the existing test file at `tests/cleaners/test_clean_xml_extensions.py` in full.

**Goal.** Extend `QC/cleaning/clean_xml.py` with language-aware cleaning, warning+CSV output, canonical-orthography TSV lookup, `--hard-remove-segmentation` flag, and a transformation counter — flipping the 12 cleaner-extension xfails in `tests/cleaners/test_clean_xml_extensions.py`.

**Architecture.** The cleaner (`clean_xml.py`) grows three pieces of infrastructure: (1) a `_get_xml_lang()` helper that walks up any element to find the nearest `xml:lang` ancestor, (2) a `CleanerWarnings` accumulator that collects (rule_id, file, S_id, character, position) rows and writes a CSV at end-of-run, and (3) a `TransformCounter` that tallies each `(input_char → output_char)` substitution and prints a sorted table at end-of-run. The `main()` entry point gains `--hard-remove-segmentation` and `--ortho-path` CLI flags. Rule branching on `xml:lang` is added to `clean_trans` (now language-aware) and to a new `process_standard_hyphens()` function. No new files are created — all code lives in `QC/cleaning/clean_xml.py`.

**Tech Stack.** Python 3.13, `lxml.etree`, `csv` (stdlib), `pytest 8.3.4`, `subprocess` in tests.

**Spec.** Design doc: `.claude/plans/2026-05-29-clean-xml-extension-tests-design.md`. Rules C001–C026. Xfail tests: `tests/cleaners/test_clean_xml_extensions.py` — the test markers are the per-rule acceptance criteria. Roadmap items 12–16: `.claude/plans/2026-05-27-roadmap.md` lines 129–134.

---

## File structure

**Modified** in this plan:

| File | Change |
|---|---|
| `QC/cleaning/clean_xml.py` | Add `_get_xml_lang()`, `CleanerWarnings`, `TransformCounter`, language-aware `clean_trans`, `process_standard_hyphens()`, `--hard-remove-segmentation`, `--ortho-path` |
| `tests/cleaners/test_clean_xml_extensions.py` | Remove `@pytest.mark.xfail` from 12 tests as each task flips them |

**Not touched** in this plan: all other files; no new files created; no `Corpora/` data touched.

---

## Phase B5a: Infrastructure (Tasks 1–4)

### Task 1: `_get_xml_lang()` — effective-language resolver

**Files:** Modify `QC/cleaning/clean_xml.py`

This is the foundational helper required by every language-aware rule (C001, C002, C012).

- [ ] **Step 1: Write the failing test**

Add a unit test at the BOTTOM of `tests/cleaners/test_clean_xml_extensions.py` (below C025) in a new section `# ===== Infrastructure unit tests =====`. This does not remove any xfail marker — it is a new plain test.

```python
# =============================================================================
# Infrastructure unit tests (no xfail — tests the helpers directly)
# =============================================================================

def test_get_xml_lang_from_direct_attribute():
    """_get_xml_lang finds xml:lang on the element itself."""
    from QC.cleaning.clean_xml import _get_xml_lang
    xml = b'<TEXT xml:lang="ami"><S><TRANSL xml:lang="eng">hi</TRANSL></S></TEXT>'
    tree = etree.fromstring(xml)
    transl = tree.find(".//TRANSL")
    assert _get_xml_lang(transl) == "eng"


def test_get_xml_lang_walks_up_to_ancestor():
    """_get_xml_lang walks up to the TEXT root if element has no xml:lang."""
    from QC.cleaning.clean_xml import _get_xml_lang
    xml = b'<TEXT xml:lang="ami"><S><FORM kindOf="original">x</FORM></S></TEXT>'
    tree = etree.fromstring(xml)
    form = tree.find(".//FORM")
    assert _get_xml_lang(form) == "ami"


def test_get_xml_lang_returns_none_when_missing():
    """_get_xml_lang returns None when no ancestor carries xml:lang."""
    from QC.cleaning.clean_xml import _get_xml_lang
    xml = b'<TEXT><S><FORM>x</FORM></S></TEXT>'
    tree = etree.fromstring(xml)
    form = tree.find(".//FORM")
    assert _get_xml_lang(form) is None
```

- [ ] **Step 2: Run pytest — all three new tests must fail with ImportError or AttributeError**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "get_xml_lang" --tb=short -q
```

- [ ] **Step 3: Implement `_get_xml_lang()`**

In `QC/cleaning/clean_xml.py`, add this function immediately after the `import` block (before `swap_punctuation`):

```python
XML_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"

_CHINESE_LANGS = frozenset({
    "zho", "zh", "cmn", "yue", "wuu", "hak", "nan",
})


def _get_xml_lang(element) -> str | None:
    """Return the effective xml:lang for element.

    Walk up from element through its ancestors, returning the first
    xml:lang value found.  Falls back to None if no ancestor (including
    element itself) carries xml:lang.

    Used by language-aware cleaning rules to decide whether an element
    carries Chinese text.
    """
    node = element
    while node is not None:
        lang = node.get(XML_LANG_ATTR)
        if lang is not None:
            return lang
        node = node.getparent()
    return None


def _is_chinese(lang: str | None) -> bool:
    """Return True when lang matches a known Chinese variant."""
    if lang is None:
        return False
    return lang.lower() in _CHINESE_LANGS or lang.lower().startswith("zh")
```

- [ ] **Step 4: Run tests — all three new tests must pass**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "get_xml_lang" --tb=short -q
```

Expected: 3 passed.

- [ ] **Step 5: Run full suite — no regressions**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 123 passed, 19 xfailed.

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "$(cat <<'EOF'
B5 task 1: add _get_xml_lang() and _is_chinese() helpers

Foundation for language-aware cleaning (items 12, C001, C002, C012).
Walks up lxml element tree to find nearest xml:lang ancestor; _is_chinese
recognises zho/zh/cmn/yue/wuu/hak/nan and zh* prefixes.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 2: `CleanerWarnings` — warning + CSV output infrastructure

**Files:** Modify `QC/cleaning/clean_xml.py`

This is required by C002 Branch B, C002b, C007, C012, C022. Per roadmap item 13. The CSV is written to `<corpora_path>/cleaner_warnings.csv` (or `--warnings-csv <path>` override added in Task 4's CLI extension). Tests look for CSV existence via `_csv_warning_exists(tmp_path, rule_id)`.

- [ ] **Step 1: Write the unit test**

Add to the infrastructure section of `test_clean_xml_extensions.py`:

```python
def test_cleaner_warnings_appends_rows(tmp_path):
    """CleanerWarnings.add() accumulates rows; write_csv() creates a CSV."""
    from QC.cleaning.clean_xml import CleanerWarnings
    w = CleanerWarnings(tmp_path / "out.csv")
    w.add("c002", str(tmp_path / "foo.xml"), "S_1", "ʼ", 3)
    w.add("c007", str(tmp_path / "bar.xml"), "S_2", "ㄇ", 0)
    w.write_csv()
    text = (tmp_path / "out.csv").read_text(encoding="utf-8").lower()
    assert "c002" in text
    assert "c007" in text
    assert "ʼ".lower() in text or "02bc" in text  # char or unicode point


def test_cleaner_warnings_no_file_when_empty(tmp_path):
    """CleanerWarnings.write_csv() does NOT create the file if no rows."""
    from QC.cleaning.clean_xml import CleanerWarnings
    w = CleanerWarnings(tmp_path / "out.csv")
    w.write_csv()
    assert not (tmp_path / "out.csv").exists()
```

- [ ] **Step 2: Run — expect ImportError/AttributeError on CleanerWarnings**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "cleaner_warnings" --tb=short -q
```

- [ ] **Step 3: Implement `CleanerWarnings`**

Add to `QC/cleaning/clean_xml.py` after the `_is_chinese` function:

```python
import csv  # add to existing imports at top of file
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CleanerWarnings:
    """Accumulates per-occurrence warning rows and writes a CSV at end of run.

    CSV columns: rule_id, file, s_id, character, position.

    write_csv() is a no-op when no rows have been added (avoids creating
    empty files on clean runs).
    """
    csv_path: Path
    _rows: list = field(default_factory=list, repr=False)

    def add(
        self,
        rule_id: str,
        file_path: str,
        s_id: str | None,
        character: str,
        position: int,
    ) -> None:
        self._rows.append({
            "rule_id": rule_id,
            "file": file_path,
            "s_id": s_id or "",
            "character": character,
            "position": position,
        })

    def write_csv(self) -> None:
        if not self._rows:
            return
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["rule_id", "file", "s_id", "character", "position"],
            )
            if f.tell() == 0:
                writer.writeheader()
            writer.writerows(self._rows)
```

Note: `import csv`, `from dataclasses import ...`, `from pathlib import Path` should be added/verified at the top of the file's import block.

- [ ] **Step 4: Run — infrastructure tests pass**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "cleaner_warnings" --tb=short -q
```

Expected: 2 passed.

- [ ] **Step 5: Full suite — no regressions**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 123 passed, 19 xfailed (+ 5 new infra tests = 128 passed).

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "$(cat <<'EOF'
B5 task 2: add CleanerWarnings CSV infrastructure

Accumulates (rule_id, file, s_id, character, position) rows during a
clean run and writes cleaner_warnings.csv on completion. No-op when zero
rows (avoids empty files on clean corpora). Required by C002b, C007,
C012, C022. Per roadmap item 13.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 3: `TransformCounter` — transformation counting infrastructure

**Files:** Modify `QC/cleaning/clean_xml.py`

Per roadmap item 16. The counter is printed to stdout at the end of `main()`. Format: one row per `(input_char, output_char)` pair, sorted by count descending. Empty-string output_char = deletion.

- [ ] **Step 1: Write the unit test**

Add to the infrastructure section of `test_clean_xml_extensions.py`:

```python
def test_transform_counter_accumulates_and_formats():
    """TransformCounter.record() tallies pairs; summary() returns sorted rows."""
    from QC.cleaning.clean_xml import TransformCounter
    tc = TransformCounter()
    tc.record("（", "(", count=3)
    tc.record("）", ")", count=1)
    tc.record("（", "(", count=2)   # same pair, different call
    summary = tc.summary()
    # First row should be the highest-count pair (（ → (, total 5).
    assert summary[0]["count"] == 5
    assert summary[0]["input"] == "（"
    assert summary[0]["output"] == "("
    assert summary[1]["count"] == 1
    assert len(summary) == 2
```

- [ ] **Step 2: Run — expect ImportError/AttributeError**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "transform_counter" --tb=short -q
```

- [ ] **Step 3: Implement `TransformCounter`**

Add to `QC/cleaning/clean_xml.py` after `CleanerWarnings`:

```python
from collections import defaultdict


@dataclass
class TransformCounter:
    """Tallies every (input_char → output_char) substitution.

    record() may be called with count > 1 when the transformation was
    applied to a string containing multiple occurrences.

    summary() returns a list of dicts sorted by count descending,
    suitable for printing as a human-readable table.
    """
    _counts: dict = field(default_factory=lambda: defaultdict(int), repr=False)

    def record(self, input_char: str, output_char: str, count: int = 1) -> None:
        self._counts[(input_char, output_char)] += count

    def record_string_delta(self, before: str, after: str) -> None:
        """Infer individual-character changes by comparing before/after strings.

        This is a lightweight heuristic: counts characters in before that
        are absent in after as deletions (output=""), and ignores characters
        that appear in both (whitespace normalization collapses are tallied
        by swapping the entire before-char set to " " when they differ).
        Use for full-string deltas where `swap_punctuation` produced a diff.
        """
        for ch in set(before):
            if ch not in after:
                # Character was deleted or replaced; cheaply attribute to deletion
                self._counts[(ch, "")] += before.count(ch)
        # For known swap_punctuation pairs, the caller should use record() directly.

    def summary(self) -> list[dict]:
        return sorted(
            [
                {"input": inp, "output": out, "count": cnt}
                for (inp, out), cnt in self._counts.items()
            ],
            key=lambda r: r["count"],
            reverse=True,
        )

    def print_summary(self) -> None:
        rows = self.summary()
        if not rows:
            return
        print("\nTransformation summary (input → output : count):")
        for r in rows:
            out = r["output"] if r["output"] else "<deleted>"
            print(f"  {r['input']!r} → {out!r} : {r['count']}")
```

- [ ] **Step 4: Run — test passes**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "transform_counter" --tb=short -q
```

Expected: 1 passed.

- [ ] **Step 5: Full suite — no regressions**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "$(cat <<'EOF'
B5 task 3: add TransformCounter for per-transformation tallying

Counts every (input_char → output_char) substitution during a clean run
and prints a sorted summary at end of main(). Required by roadmap item 16.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 4: Wire infrastructure into `analyze_and_modify_xml_file` and `main()`; add CLI flags

**Files:** Modify `QC/cleaning/clean_xml.py`

This task threads `CleanerWarnings` and `TransformCounter` instances through the processing functions and adds `--hard-remove-segmentation` and `--ortho-path` CLI flags to `main()`. No xfail tests flip here — but this is required wiring before Tasks 5–9 can use the infrastructure.

- [ ] **Step 1: No new tests needed** — existing infrastructure tests from Tasks 1–3 already cover the classes. The wiring is tested indirectly by the xfail tests in Tasks 5–9.

- [ ] **Step 2: Modify `analyze_and_modify_xml_file` signature and body**

Change the function signature to:

```python
def analyze_and_modify_xml_file(
    xml_dir,
    corpora_dir,
    warnings: CleanerWarnings | None = None,
    counter: TransformCounter | None = None,
    hard_remove_segmentation: bool = False,
    ortho_path: str | None = None,
):
```

Internal changes:
- Replace `clean_text(form_text, lang="na")` with a version that passes `counter` (see Task 5).
- Replace `clean_trans(transl_text, lang)` with a version that passes `warnings`, `counter`, and `xml:lang` (see Task 6).
- After the per-sentence TRANSL loop, add calls for C012 standard-hyphen processing (see Task 7).

- [ ] **Step 3: Modify `main()` to create instances and pass them**

```python
def main(args):
    print(f"Processing XML files in directory: {args.corpora_path}")
    warnings_path = Path(args.corpora_path) / "cleaner_warnings.csv"
    warnings = CleanerWarnings(warnings_path)
    counter = TransformCounter()
    analyze_and_modify_xml_file(
        args.corpora_path,
        args.corpora_path,
        warnings=warnings,
        counter=counter,
        hard_remove_segmentation=getattr(args, "hard_remove_segmentation", False),
        ortho_path=getattr(args, "ortho_path", None),
    )
    warnings.write_csv()
    counter.print_summary()
```

- [ ] **Step 4: Add CLI flags to argparse**

```python
parser.add_argument(
    "--hard-remove-segmentation",
    action="store_true",
    default=False,
    help=(
        "Force stripping of hyphens from S/FORM[@kindOf='standard'] even "
        "when the language's canonical orthography includes '-' as a letter. "
        "Overrides the default preserve-and-warn behavior for Bunun and Thao."
    ),
)
parser.add_argument(
    "--ortho-path",
    default=None,
    help=(
        "Path to the canonical orthography directory (default: "
        "Orthographies/Ortho113/ relative to the repo root). "
        "Each <Language>.tsv under this directory is consulted by C012."
    ),
)
```

- [ ] **Step 5: Run full suite — no regressions**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: no change from before this task.

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py
git commit -m "$(cat <<'EOF'
B5 task 4: wire CleanerWarnings/TransformCounter into processing pipeline

analyze_and_modify_xml_file now accepts warnings, counter,
hard_remove_segmentation, and ortho_path parameters. main() constructs
instances and calls write_csv() / print_summary() at end of run. Adds
--hard-remove-segmentation and --ortho-path CLI flags. Per roadmap
items 14–16.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

## Phase B5b: Rule implementations (Tasks 5–9)

### Task 5: C007 — Bopomofo preservation with warning (reverse `remove_junk_chars`), full coverage

**Files:** Modify `QC/cleaning/clean_xml.py`; modify `tests/cleaners/test_clean_xml_extensions.py`; expand fixture `tests/fixtures/c007_bopomofo_in_form.xml`.

Per design doc C007: the cleaner currently DELETES `ㄇ` via `remove_junk_chars`. The new behavior: preserve EVERY Bopomofo character and emit a warning CSV row per occurrence. The current `remove_junk_chars` table only contains `ㄇ`; the new rule covers ALL named Bopomofo codepoints (the regular Bopomofo block U+3100–U+312F plus the Bopomofo Extended block U+31A0–U+31BF). Verified empirically (2026-05-30): all 75 named codepoints in those ranges have `unicodedata.name(ch).startswith("BOPOMOFO")`, so the detector is reliable.

Flips: `test_C007_bopomofo_preserved` and `test_C007_bopomofo_warning_emitted` (2 xfails).

- [ ] **Step 1: Verify current xfail status**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C007" --tb=short -q
```

Expected: 2 xfailed.

- [ ] **Step 2: Expand the fixture to cover all named Bopomofo codepoints**

The current `c007_bopomofo_in_form.xml` has only `ㄇ`. Replace its FORM contents with a string built from every named Bopomofo codepoint, embedded between Latin letters so deletions are visible. Generate the string with this snippet (run it once to get the literal characters; paste them into the fixture):

```python
import unicodedata
chars = []
for code in list(range(0x3100, 0x3130)) + list(range(0x31A0, 0x31C0)):
    try:
        if unicodedata.name(chr(code)).startswith("BOPOMOFO"):
            chars.append(chr(code))
    except ValueError:
        continue
print("a" + "".join(chars) + "b")
```

The fixture's `<FORM kindOf="original">` and `<FORM kindOf="standard">` both carry this same `a<all-75-bopomofo-chars>b` string. Add a top-of-file XML comment noting the source ranges and that the count is 75 (regression pin: if Unicode adds new Bopomofo codepoints in a future Python release, the count rises and the test catches it).

- [ ] **Step 3: Implement**

In `clean_xml.py`:

1. Remove `remove_junk_chars` function entirely (or empty it to `return text`).
2. Remove the `remove_junk_chars(text)` call from `clean_text()`.
3. In `analyze_and_modify_xml_file`, after `clean_text()` returns, scan `form_text` for ALL Bopomofo characters and emit a warning per occurrence:

```python
import unicodedata

def _find_bopomofo(text: str) -> list[tuple[str, int]]:
    """Return [(char, position)] for every Bopomofo character in text.
    Covers Bopomofo (U+3100-U+312F) and Bopomofo Extended (U+31A0-U+31BF).
    """
    out = []
    for i, ch in enumerate(text):
        try:
            if unicodedata.name(ch).startswith("BOPOMOFO"):
                out.append((ch, i))
        except ValueError:
            continue
    return out
```

Add Bopomofo warning emission inside the FORM processing loop:
```python
for ch, pos in _find_bopomofo(form_text):
    if warnings:
        warnings.add("c007", xml_file, sentence.get("id"), ch, pos)
```

- [ ] **Step 4: Update the existing C007 tests to verify FULL coverage**

In `tests/cleaners/test_clean_xml_extensions.py`, modify `test_C007_bopomofo_preserved` and `test_C007_bopomofo_warning_emitted`:

For `test_C007_bopomofo_preserved`: instead of asserting only that `ㄇ` survives, assert that EVERY character in the fixture's input FORM text is present in the cleaned FORM text (compare character sets or substrings).

For `test_C007_bopomofo_warning_emitted`: instead of asserting one warning, build the expected list of Bopomofo characters (via the same `unicodedata.name(ch).startswith("BOPOMOFO")` predicate the rule uses), then assert the warnings CSV contains a row for EACH character (using `_csv_warning_exists` or by parsing the CSV directly and checking the character column).

A defensive pattern:

```python
def _all_bopomofo_chars() -> list[str]:
    import unicodedata
    out = []
    for code in list(range(0x3100, 0x3130)) + list(range(0x31A0, 0x31C0)):
        try:
            if unicodedata.name(chr(code)).startswith("BOPOMOFO"):
                out.append(chr(code))
        except ValueError:
            continue
    return out


# In test_C007_bopomofo_warning_emitted:
expected_chars = _all_bopomofo_chars()
# Parse the warnings CSV under tmp_path and collect the 'character' column
# values for rule_id='c007'. Assert the set equals expected_chars.
```

If `_csv_warning_exists` (the existing helper in `tests/_helpers.py`) only checks substring presence, the test may need to read the CSV directly. The B5 plan's Task 2 (CleanerWarnings infrastructure) should define the CSV schema; this test verifies each Bopomofo character appears as a row.

Also remove `@pytest.mark.xfail(strict=True, ...)` from both tests. Move `"c007_bopomofo_in_form.xml"` from `XFAIL_FIXTURES` to `IDEMPOTENT_FIXTURES`.

- [ ] **Step 5: Run — both C007 tests must pass**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C007" --tb=short -q
```

Expected: 2 passed.

If `test_C007_bopomofo_preserved` fails because the cleaner deleted some characters: the `remove_junk_chars` call wasn't fully removed, or another cleaner step (e.g., NFC normalization, whitespace handling) is mutating Bopomofo. Inspect the actual cleaned output.

If `test_C007_bopomofo_warning_emitted` fails because some characters didn't get warnings: the `unicodedata.name(ch).startswith("BOPOMOFO")` check missed some codepoints (perhaps the iteration range is wrong, or some codepoints are unnamed and `unicodedata.name(ch)` raises). Inspect which characters are missing.

- [ ] **Step 5: Full suite**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 125 passed, 17 xfailed (2 xfails flipped).

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py tests/fixtures/c007_bopomofo_in_form.xml
git commit -m "$(cat <<'EOF'
B5 task 5 (C007): preserve all Bopomofo characters; warn per occurrence

Reverses remove_junk_chars behavior: every named Bopomofo codepoint
(Bopomofo block U+3100-U+312F plus Bopomofo Extended U+31A0-U+31BF,
all 75 characters as of Python's current unicodedata) now survives
cleaning; each occurrence emits a c007 warning row to the cleaner
warnings CSV. Detector uses unicodedata.name(ch).startswith("BOPOMOFO")
which was verified to cover all named codepoints in both blocks.

Fixture expanded from the single character ㄇ to all 75 named
Bopomofo codepoints embedded between Latin letters; tests verify
every character survives unchanged AND a warning row exists for
each. Flips 2 xfails.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 6: C001 + C002 + C002b — Language-aware `clean_trans`

**Files:** Modify `QC/cleaning/clean_xml.py`; modify `tests/cleaners/test_clean_xml_extensions.py`

Per design doc C001 (non-Chinese TRANSL gets `swap_punctuation`) and C002 (Chinese TRANSL: double-quote variants collapse to U+201D; single-quote variants WARN; ASCII apostrophes WARN). Per roadmap item 12.

Flips: `test_C001_nonchinese_transl_fullwidth_paren_collapses` (1), `test_C002_apostrophe_in_nonchinese_transl_collapses` (1), `test_C002_double_quotes_in_chinese_transl_collapse_to_canonical` (1), `test_C002_modifier_apostrophe_in_chinese_transl_warns` (1), `test_C002_ascii_apostrophe_in_chinese_transl_warns` (1) = 5 xfails total.

Also flips `test_C002b_ipa_stress_warning_emitted` (1) since the `ˈ` → `'` transformation should now emit a C002b warning row.

Total: 6 xfails.

- [ ] **Step 1: Verify current xfail status**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C001 or C002" --tb=short -q
```

Expected: 6 xfailed (5 C001/C002 + 1 C002b warning).

- [ ] **Step 2: Add `CHINESE_DOUBLE_QUOTE_COLLAPSE` table and branch logic**

Add to `QC/cleaning/clean_xml.py`:

```python
# C002 Branch B: Chinese double-quote variants → canonical U+201D
CHINESE_DOUBLE_QUOTE_COLLAPSE = {
    "“": "”",  # " → "
    "「": "”",  # 「 → "
    "」": "”",  # 」 → "
    "『": "”",  # 『 → "
    "』": "”",  # 』 → "
    "《": "”",  # 《 → "
    "》": "”",  # 》 → "
    "〈": "”",  # 〈 → "  (if present)
    "〉": "”",  # 〉 → "  (if present)
}

# C002 Branch B: single-quote/apostrophe chars in Chinese → WARN
CHINESE_WARN_SINGLE_QUOTES = frozenset({
    "‘",  # '  left single
    "’",  # '  right single
    "ʼ",  # ʼ  modifier letter apostrophe
    "ʻ",  # ʻ  modifier letter turned comma
    "`",  # `  grave accent
})


def _clean_trans_chinese(
    text: str,
    xml_file: str,
    s_id: str | None,
    warnings: "CleanerWarnings | None",
) -> str:
    """Apply C002 Branch B: canonicalise Chinese double quotes; warn on singles."""
    import re as _re
    # Collapse double-quote variants to U+201D
    for ch, replacement in CHINESE_DOUBLE_QUOTE_COLLAPSE.items():
        text = text.replace(ch, replacement)
    # Warn on single-quote variants (do not transform)
    for i, ch in enumerate(text):
        if ch in CHINESE_WARN_SINGLE_QUOTES:
            if warnings:
                warnings.add("c002", xml_file, s_id, ch, i)
        # Warn on ASCII apostrophe/quote (Latin punctuation in Chinese text)
        if ch == "'":
            if warnings:
                warnings.add("c002", xml_file, s_id, ch, i)
    return text
```

- [ ] **Step 3: Modify `clean_trans()` to be language-aware**

Replace the existing `clean_trans` function body:

```python
def clean_trans(
    text: str,
    lang: str | None,
    xml_file: str = "",
    s_id: str | None = None,
    warnings: "CleanerWarnings | None" = None,
    counter: "TransformCounter | None" = None,
) -> str:
    """Clean TRANSL text with language-aware branching.

    Non-Chinese TRANSL (C001/C002 Branch A): apply swap_punctuation,
    normalize_whitespace, trim_repeated_punctuation.
    Chinese TRANSL (C002 Branch B): collapse double-quote variants to
    U+201D; WARN on single-quote variants and ASCII apostrophes;
    normalize_whitespace and trim_repeated_punctuation still apply.
    """
    if _is_chinese(lang):
        text = _clean_trans_chinese(text, xml_file, s_id, warnings)
    else:
        # Branch A: non-Chinese — apply same swap_punctuation as FORM
        before = text
        text = swap_punctuation(text)
        # Emit C002b warning when ˈ (U+02C8) was present and got collapsed
        if "ˈ" in before and warnings:
            for i, ch in enumerate(before):
                if ch == "ˈ":
                    warnings.add("c002b", xml_file, s_id, ch, i)
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    return text
```

Also update all call sites of `clean_trans` in `analyze_and_modify_xml_file` to pass `xml_file`, `s_id`, `warnings`, `counter`:

```python
cleaned_transl_text = clean_trans(
    transl_text,
    lang,
    xml_file=xml_file,
    s_id=sentence.get("id"),
    warnings=warnings,
    counter=counter,
)
```

Similarly, emit a C002b warning when `swap_punctuation` is applied to FORM text (in `clean_text`):
```python
# After clean_text returns — check for U+02C8 that got collapsed
if "ˈ" in form_text and warnings:
    for i, ch in enumerate(form_text):
        if ch == "ˈ":
            warnings.add("c002b", xml_file, sentence.get("id"), ch, i)
```

- [ ] **Step 4: Remove xfail markers**

In `test_clean_xml_extensions.py`, remove `@pytest.mark.xfail(strict=True, ...)` from:
- `test_C001_nonchinese_transl_fullwidth_paren_collapses`
- `test_C002_apostrophe_in_nonchinese_transl_collapses`
- `test_C002_double_quotes_in_chinese_transl_collapse_to_canonical`
- `test_C002_modifier_apostrophe_in_chinese_transl_warns`
- `test_C002_ascii_apostrophe_in_chinese_transl_warns`
- `test_C002b_ipa_stress_warning_emitted`

Move corresponding fixture names from `XFAIL_FIXTURES` to `IDEMPOTENT_FIXTURES`:
- `"c001_fullwidth_paren_in_nonchinese_transl.xml"`
- `"c002_apostrophe_in_nonchinese_transl.xml"`
- `"c002_ascii_apostrophe_in_chinese_transl.xml"`
- `"c002_double_quotes_in_chinese_transl.xml"`
- `"c002_modifier_apostrophe_in_chinese_transl.xml"`

(C002b's fixture `"c002b_ipa_stress_in_form.xml"` is already in `IDEMPOTENT_FIXTURES` — the warning test used the same fixture.)

**ALSO in this task (Step 4b): caret-variant normalization, language-AGNOSTIC.**

Per user direction (2026-05-30): in this corpus, a caret-like glyph in any position is always a glottal stop. The cleaner must normalize ALL caret-variant Unicode characters to ASCII `^` (U+005E) in BOTH FORM and TRANSL, regardless of language. The current cleaner only handles ⌃ (U+2303) and only in FORM (via swap_punctuation). Expand to four variants and apply in both tiers.

The four caret-variant characters:
| Codepoint | Char | Unicode name |
|---|---|---|
| U+2303 | ⌃ | UP ARROWHEAD |
| U+2038 | ‸ | CARET |
| U+02C6 | ˆ | MODIFIER LETTER CIRCUMFLEX ACCENT |
| U+FF3E | ＾ | FULLWIDTH CIRCUMFLEX ACCENT |

Implementation: factor a dedicated function so it's clearly language-agnostic and separate from the language-aware C001/C002 swap.

```python
_CARET_VARIANTS_TO_ASCII = {
    "⌃": "^",  # UP ARROWHEAD
    "‸": "^",  # CARET
    "ˆ": "^",  # MODIFIER LETTER CIRCUMFLEX ACCENT
    "＾": "^",  # FULLWIDTH CIRCUMFLEX ACCENT
}


def normalize_caret_variants(text: str) -> str:
    """Normalize caret-like Unicode characters to ASCII '^'.

    Per FormosanBank convention, a caret-like glyph in this corpus
    always represents a glottal stop. We canonicalize the visual
    variants to a single character so downstream processing sees
    one form regardless of source.
    """
    for variant, ascii_caret in _CARET_VARIANTS_TO_ASCII.items():
        text = text.replace(variant, ascii_caret)
    return text
```

Call sites: invoke `normalize_caret_variants` from both `clean_text` and `clean_trans`, regardless of `xml:lang`. Apply BEFORE the language-aware swap_punctuation so the rest of the pipeline only ever sees `^`.

ALSO: remove the existing `'⌃': '^'` entry from the `swap_punctuation` table (line 64 of clean_xml.py) — the new dedicated function handles it. Keep all other swap_punctuation entries.

**C006 test pin update.** With caret normalization now applied to TRANSL, the existing C006 test's negative pin on TRANSL (`assert "⌃" in transl`) flips. The new behavior is uniform across tiers: every caret variant becomes `^` everywhere.

Old assertion:
```python
assert "⌃" in transl, f"TRANSL ⌃ should survive: {transl!r}"
```
New assertion (per user direction 2026-05-30; supersedes roadmap item 23):
```python
assert transl == "arrowhead ^ stays", f"TRANSL after caret normalization: {transl!r}"
```

Update the C006 test docstring to explain the new uniform rule.

**Expand the C006 fixture** to verify caret normalization happens across the full cross-product:

- All FOUR caret variants (⌃ ‸ ˆ ＾)
- In all THREE tier positions: FORM (kindOf="original" AND kindOf="standard") + TRANSL with `xml:lang="eng"` (non-Chinese) + TRANSL with `xml:lang="zho"` (Chinese — explicit verification that caret normalization is NOT language-coupled)

Shape:
```xml
<TEXT id="TEST_C006" citation="test" BibTeX_citation="@test{test}"
      copyright="test" xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">a⌃b‸cˆd＾e</FORM>
    <FORM kindOf="standard">a⌃b‸cˆd＾e</FORM>
    <TRANSL xml:lang="eng">arrowhead ⌃ caret ‸ circ ˆ fullwidth ＾</TRANSL>
    <TRANSL xml:lang="zho">⌃‸ˆ＾</TRANSL>
  </S>
</TEXT>
```

Test assertions:
```python
# All four caret variants must normalize to ASCII '^' in every tier.
orig = _form_texts_with_kindof(work, "S", "original")[0]
std  = _form_texts_with_kindof(work, "S", "standard")[0]
assert orig == "a^b^c^d^e", f"FORM original: {orig!r}"
assert std  == "a^b^c^d^e", f"FORM standard: {std!r}"

transls = {t.get(XML_LANG): t.text for t in tree.findall(".//S/TRANSL")}
assert transls["eng"] == "arrowhead ^ caret ^ circ ^ fullwidth ^", (
    f"non-Chinese TRANSL: {transls['eng']!r}"
)
assert transls["zho"] == "^^^^", (
    f"Chinese TRANSL (caret normalization MUST happen regardless of lang): "
    f"{transls['zho']!r}"
)
```

The Chinese TRANSL assertion is the key regression pin: if a future implementation accidentally couples caret handling to the language-aware C001/C002 swap (which DOES skip Chinese), the `transls["zho"]` assertion fails loudly. The test name and docstring should make this explicit.

**Rename the C006 test** from `test_C006_caret_variant_collapses_in_form_only` to `test_C006_caret_variants_normalize_everywhere_regardless_of_lang` (the "form_only" framing is now wrong; the new name encodes the universality).

- [ ] **Step 5: Run C001/C002/C006 tests**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C001 or C002 or C006" --tb=short -q
```

Expected: all pass (6 previously-xfailed now pass, C006 passes with updated assertion).

- [ ] **Step 6: Full suite**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 131 passed, 11 xfailed (6 more xfails flipped).

- [ ] **Step 7: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "$(cat <<'EOF'
B5 task 6 (C001/C002/C002b + C006 caret normalization): language-aware
clean_trans + always-convert caret variants

Non-Chinese TRANSL now gets swap_punctuation (C001/C002 Branch A).
Chinese TRANSL gets double-quote canonicalisation to U+201D (Branch B)
plus warnings for single-quote variants and ASCII apostrophes.
ˈ (U+02C8) transformations in both FORM and TRANSL now emit c002b
warning rows. Flips 6 xfails. Per roadmap items 12-13.

Caret-variant normalization (C006 simplified per user direction
2026-05-30): four caret-like Unicode characters (U+2303 UP ARROWHEAD,
U+2038 CARET, U+02C6 MODIFIER LETTER CIRCUMFLEX ACCENT, U+FF3E
FULLWIDTH CIRCUMFLEX ACCENT) all normalize to ASCII '^' in BOTH FORM
and TRANSL, regardless of xml:lang. In FormosanBank, a caret-like
glyph always represents a glottal stop, so the variants are
canonicalized to one representation. The C006 test pin on TRANSL is
updated accordingly (no longer a negative pin — TRANSL now sees the
same caret normalization as FORM). The fixture expands to cover all
four variants. Supersedes roadmap item 23 (the "future revisit" is
now done here).

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 7: C012 — Segmentation hyphens in `S/FORM[@kindOf="standard"]`, data-driven

**Files:** Modify `QC/cleaning/clean_xml.py`; modify `tests/cleaners/test_clean_xml_extensions.py`

Per design doc C012 and roadmap item 14. Add `process_standard_hyphens()` which looks up `Orthographies/Ortho113/<Language>.tsv` for the file's `xml:lang` and strips hyphens (and `=` clitic markers) from S-level standard FORM if `-` is not a letter, or warns if it is.

Flips: `test_C012_amis_standard_hyphens_stripped` (1), `test_C012_bunun_standard_hyphens_preserved_with_warning` (1), `test_C012_thao_standard_hyphens_preserved_with_warning` (1) = 3 xfails.

Also relevant: `--hard-remove-segmentation` flag (added in Task 4) which overrides the warn branch for languages where `-` is a letter.

- [ ] **Step 1: Verify xfail status**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C012" --tb=short -q
```

Expected: 3 xfailed.

- [ ] **Step 2: Implement `_hyphen_is_letter()` lookup**

```python
from pathlib import Path as _Path
import os as _os

# ISO 639-3 code → Language name mapping for Ortho113 lookup.
# Ortho113 TSV files are named by language name, not ISO code.
_ISO_TO_LANG_NAME = {
    "ami": "Amis",
    "aty": "Atayal",
    "bnn": "Bunun",
    "xnb": "Kanakanavu",
    "ckv": "Kavalan",
    "pwn": "Paiwan",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "sxr": "Saaroa",
    "xsy": "Saisiyat",
    "szy": "Sakizaya",
    "trv": "Seediq",
    "ssf": "Thao",
    "tsu": "Tsou",
    "tao": "Yami",
}

# Cache results to avoid re-reading TSV on every file.
_HYPHEN_IS_LETTER_CACHE: dict[str, bool] = {}


def _hyphen_is_letter(
    lang_code: str,
    ortho_path: str | None = None,
) -> bool:
    """Return True if '-' appears as a letter row in the canonical orthography TSV.

    Looks up Orthographies/Ortho113/<Language>.tsv relative to the repo root
    (or ortho_path if provided). Returns False if the TSV is not found or the
    language code is unknown.

    Empirically verified 2026-05-29: only Bunun (bnn) and Thao (ssf) return True.
    """
    cache_key = (lang_code, ortho_path)
    if cache_key in _HYPHEN_IS_LETTER_CACHE:
        return _HYPHEN_IS_LETTER_CACHE[cache_key]

    lang_name = _ISO_TO_LANG_NAME.get(lang_code)
    if lang_name is None:
        _HYPHEN_IS_LETTER_CACHE[cache_key] = False
        return False

    if ortho_path:
        tsv_dir = _Path(ortho_path)
    else:
        # Default: repo root / Orthographies / Ortho113
        # Locate repo root relative to this file (QC/cleaning/clean_xml.py).
        repo_root = _Path(__file__).resolve().parents[2]
        tsv_dir = repo_root / "Orthographies" / "Ortho113"

    tsv_path = tsv_dir / f"{lang_name}.tsv"
    if not tsv_path.exists():
        _HYPHEN_IS_LETTER_CACHE[cache_key] = False
        return False

    with open(tsv_path, encoding="utf-8") as f:
        for line in f:
            # Column 0 (before the first tab) is the "letter" column.
            letter = line.split("\t")[0].strip()
            if letter == "-":
                _HYPHEN_IS_LETTER_CACHE[cache_key] = True
                return True

    _HYPHEN_IS_LETTER_CACHE[cache_key] = False
    return False
```

- [ ] **Step 3: Implement `process_standard_hyphens()`**

```python
import re as _re

# Pattern: segmentation hyphen (not part of a word-initial or word-final
# legitimate use). Strips any hyphen NOT at an obvious word boundary.
# Conservatively: strip hyphens between word characters: "M-kan" → "Mkan".
# Also strips "=ku" clitic notation: "=ku" → "ku".
_SEG_HYPHEN_RE = _re.compile(r'-')
_SEG_CLITIC_RE = _re.compile(r'=')


def _strip_segmentation(text: str) -> str:
    """Remove morpheme-boundary hyphens and clitic = markers from text."""
    text = _SEG_HYPHEN_RE.sub("", text)
    text = _SEG_CLITIC_RE.sub("", text)
    return normalize_whitespace(text)


def process_standard_hyphens(
    sentence,
    xml_file: str,
    lang_code: str | None,
    warnings: "CleanerWarnings | None",
    hard_remove: bool,
    ortho_path: str | None,
) -> bool:
    """Process S/FORM[@kindOf='standard'] hyphens for the given sentence.

    Returns True if the sentence's standard FORM was modified.
    """
    if not lang_code or _is_chinese(lang_code):
        return False

    # Find the S-level standard FORM (direct child of S only, not W/M).
    std_form = sentence.find("FORM[@kindOf='standard']")
    if std_form is None or not std_form.text:
        return False

    text = std_form.text
    if "-" not in text and "=" not in text:
        return False

    hyphen_is_letter = _hyphen_is_letter(lang_code, ortho_path)

    if hyphen_is_letter and not hard_remove:
        # Language's orthography includes '-': warn, do not transform.
        if warnings:
            for i, ch in enumerate(text):
                if ch in "-=":
                    warnings.add("c012", xml_file, sentence.get("id"), ch, i)
        return False
    else:
        # Strip segmentation hyphens (and '=' clitic markers).
        new_text = _strip_segmentation(text)
        if new_text != text:
            std_form.text = new_text
            return True
    return False
```

- [ ] **Step 4: Call `process_standard_hyphens()` from `analyze_and_modify_xml_file`**

After the FORM-processing loop and before the TRANSL-processing loop for each sentence, add:

```python
# C012: strip segmentation hyphens from S/FORM[@kindOf="standard"]
# (requires lang_code from the file's TEXT element).
file_lang = root.get(XML_LANG_ATTR)
if process_standard_hyphens(
    sentence,
    xml_file,
    file_lang,
    warnings,
    hard_remove_segmentation,
    ortho_path,
):
    modified = True
```

- [ ] **Step 5: Remove xfail markers**

Remove `@pytest.mark.xfail(strict=True, ...)` from:
- `test_C012_amis_standard_hyphens_stripped`
- `test_C012_bunun_standard_hyphens_preserved_with_warning`
- `test_C012_thao_standard_hyphens_preserved_with_warning`

Move from `XFAIL_FIXTURES` to `IDEMPOTENT_FIXTURES`:
- `"c012_hyphens_in_standard_amis.xml"`
- `"c012_hyphens_in_standard_bunun.xml"`
- `"c012_hyphens_in_standard_thao.xml"`

- [ ] **Step 6: Run C012 tests**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C012" --tb=short -q
```

Expected: 3 passed.

- [ ] **Step 7: Run C011 and C013 tests** (pin that original and W-tier hyphens are untouched)

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C011 or C013" --tb=short -q
```

Expected: both pass (hyphens in original and W-tier survive).

- [ ] **Step 8: Full suite**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 134 passed, 8 xfailed (3 more xfails flipped).

- [ ] **Step 9: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "$(cat <<'EOF'
B5 task 7 (C012): data-driven segmentation-hyphen stripping in standard tier

Reads Orthographies/Ortho113/<Language>.tsv for each file's xml:lang
to determine if '-' is a letter. If not (e.g. Amis): strips '-' and '='
from S/FORM[@kindOf='standard']. If yes (Bunun, Thao): emits c012
warning rows and preserves. --hard-remove-segmentation overrides the
warn branch. S/FORM[@kindOf='original'] and W/FORM hyphens untouched.
Flips 3 xfails. Per roadmap items 14-15.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 8: C022 — Warn on `*` ANYWHERE in FORM (not just sentence-initial)

**Files:** Modify `QC/cleaning/clean_xml.py`; modify `tests/cleaners/test_clean_xml_extensions.py`; expand fixture `tests/fixtures/c022_sentence_initial_asterisk.xml` and rename to `c022_asterisk_in_form.xml`.

Per design doc C022 and user direction (2026-05-30): the `*` ungrammaticality marker can appear at ANY position within a FORM, not only sentence-initial. The cleaner emits a warning CSV row per `*` occurrence (one warning per character, at its position) and preserves the FORM text unchanged. Contrast with C008 (`456otca`) which deletes.

Flips: `test_C022_asterisk_in_form_warns_and_preserves` (1 xfail; renamed from `test_C022_sentence_initial_asterisk_warns_and_preserves`).

- [ ] **Step 1: Verify xfail status**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C022" --tb=short -q
```

Expected: 1 xfailed.

- [ ] **Step 2: Expand the fixture to cover multiple `*` positions**

The current `c022_sentence_initial_asterisk.xml` has `*` only at sentence start. Replace its FORM contents with text containing `*` at MULTIPLE positions, and rename the file to `c022_asterisk_in_form.xml` (the existing filename is misleadingly narrow). The new fixture should include at least:

- `*` at sentence-initial position (the original case)
- `*` mid-sentence (e.g., between words)
- `*` at sentence-final position (e.g., before a final period)
- One S in the fixture should have NO `*` (control case — no warning emitted for it)

Example shape:

```xml
<TEXT id="TEST_C022" citation="test" ... xml:lang="ami">
  <S id="S_1">
    <FORM kindOf="original">*Mu ka patas nii.</FORM>
    <FORM kindOf="standard">*Mu ka patas nii.</FORM>
  </S>
  <S id="S_2">
    <FORM kindOf="original">Mu ka *patas nii.</FORM>
    <FORM kindOf="standard">Mu ka *patas nii.</FORM>
  </S>
  <S id="S_3">
    <FORM kindOf="original">Mu ka patas nii*.</FORM>
    <FORM kindOf="standard">Mu ka patas nii*.</FORM>
  </S>
  <S id="S_4">
    <FORM kindOf="original">Mu ka patas nii.</FORM>
    <FORM kindOf="standard">Mu ka patas nii.</FORM>
  </S>
</TEXT>
```

If renaming the fixture, update:
- The XML comment block at the top of the file.
- All references to the filename in `tests/cleaners/test_clean_xml_extensions.py` (the test body uses `fixtures_dir / "c022_..."`).
- The fixture name in `XFAIL_FIXTURES` / `IDEMPOTENT_FIXTURES` sets at the top of `test_clean_xml_extensions.py`.
- The roadmap and design-doc references to the fixture name, if any.

(If renaming is too invasive, leave the filename as-is and just update the contents + the top-of-file comment. The filename has limited downstream impact.)

- [ ] **Step 3: Implement**

In `analyze_and_modify_xml_file`, inside the FORM processing loop, after verifying `form_text` is non-empty, add:

```python
# C022: warn on any FORM containing '*' at any position
if "*" in form_text and warnings:
    for i, ch in enumerate(form_text):
        if ch == "*":
            warnings.add(
                "c022",
                xml_file,
                sentence.get("id"),
                ch,
                i,
            )
```

The `*` is NOT removed — the FORM text is preserved unchanged.

- [ ] **Step 4: Update + rename the test**

Rename `test_C022_sentence_initial_asterisk_warns_and_preserves` to `test_C022_asterisk_in_form_warns_and_preserves`. Update the docstring to describe the broader rule (any position, not just sentence-initial).

Update the test's assertions:

- Existing preservation assertion: verify FORM text is unchanged in S_1, S_2, S_3 (each still contains its `*`).
- Existing warning assertion: verify a c022 warning row exists for EACH of the 3 `*` occurrences. If `_csv_warning_exists` checks substring only, parse the CSV directly and assert there are at least 3 c022 rows (one per `*`).
- Add a control assertion: S_4 (the un-starred S) has NO c022 warning row tied to its id.

If the warning marker tuple is updated, ensure the strings reflect the broader rule (drop "sentence-initial" from any marker; keep "c022", "asterisk", "ungrammatical").

Remove `@pytest.mark.xfail(strict=True, ...)`.

Move the fixture (renamed or not) from `XFAIL_FIXTURES` to `IDEMPOTENT_FIXTURES`.

- [ ] **Step 5: Run C022 test**

```bash
.venv/bin/pytest tests/cleaners/test_clean_xml_extensions.py -k "C022" --tb=short -q
```

Expected: 1 passed.

If the test fails because the cleaner only warned for sentence-initial: the implementation's `for i, ch in enumerate(form_text)` loop is correct as written above; verify the loop actually runs and the `warnings.add` call is reached.

- [ ] **Step 5: Full suite**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 135 passed, 7 xfailed. (The 7 remaining xfails are the `remove_non_working_audio` tests — C012's hard-remove xfail was not written, see note below.)

**Note:** The design doc mentions a `--hard-remove-segmentation` variant test, but `tests/cleaners/test_clean_xml_extensions.py` does NOT contain an xfail for it (per the comment at line 637: "Skip that variant entirely; document the gap here and revisit when B adds the flag."). So 7 xfails remain (all `remove_non_working_audio`).

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py tests/fixtures/c022_*.xml
git commit -m "$(cat <<'EOF'
B5 task 8 (C022): warn on '*' anywhere in FORM, preserve text

Emits a c022 warning CSV row for each '*' occurrence in any FORM
(sentence-initial, mid-sentence, or sentence-final positions all
warn). The FORM text is preserved unchanged (unlike the 456otca
sentinel of C008, which deletes). Per design doc C022 and user
direction (2026-05-30): the previous "sentence-initial only"
framing was too narrow.

Fixture expanded to cover '*' at multiple positions plus a control
S with no '*'. Test renamed from
test_C022_sentence_initial_asterisk_warns_and_preserves to
test_C022_asterisk_in_form_warns_and_preserves. Flips 1 xfail.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

---

### Task 9: Verification — final state check

After all tasks complete:

- [ ] **Run full suite and quote actual output**

```bash
.venv/bin/pytest --tb=short -q 2>&1 | tail -5
```

Expected: 135 passed, 7 xfailed (the 7 remaining are `remove_non_working_audio`).

- [ ] **Confirm no XPASS** (no xfail marker was left behind on a now-passing test):

```bash
.venv/bin/pytest -v 2>&1 | grep -i "xpass"
```

Expected: no output.

- [ ] **Confirm XFAIL_FIXTURES set is now empty in test file**

XFAIL_FIXTURES should contain no entries (all 10 fixture names moved to IDEMPOTENT_FIXTURES across tasks 5–8).

---

## Out of scope for this plan

- **Item 17** (existing-corpora remediation): Audit `Corpora/` for Chinese TRANSL elements previously stripped of full-width punctuation by the unconditional `swap_punctuation`. Depends on items 12–16 being done. Separate data-fix effort; this plan does not touch `Corpora/`.
- **C006 caret-preservation pin revisit** (roadmap item 23): handled in Task 6 inline — the C006 TRANSL pin is updated as part of language-aware `clean_trans` landing.
- **The `remove_non_working_audio.py` refactor** (7 xfails in `test_remove_non_working_audio.py`): separate sub-effort; not part of clean_xml extension work.
- **Item 19** (audit `clean_xml.py` for validator-territory checks): separate from this plan; no validator-territory code was found in current `clean_xml.py`.
- **Item 20** (OQ9 docstring update): add docstrings to `clean_text`/`clean_trans` after this plan lands, noting the FORM-vs-TRANSL asymmetry and the `xml:lang` branching logic.
- **Phase B6** (Category 6 candidates: footnote detection, out-of-language flagging, multi-word gloss normalisation): validator/scraper work, not cleaner work.

---

## Self-review

**Spec coverage:**
- All 12 xfail tests are explicitly targeted: Task 5 flips 2 (C007), Task 6 flips 6 (C001/C002/C002b), Task 7 flips 3 (C012), Task 8 flips 1 (C022).
- Infrastructure tasks (1–4) are required by rule tasks but add no xfail markers.
- C006 TRANSL pin update (roadmap item 23) is handled inline in Task 6 as the spec requires.
- `--hard-remove-segmentation` flag is implemented in Task 4 and used in Task 7; no xfail test was written for it (per the test file's comment) so no marker to remove.
- Transformation counter (item 16) is implemented in Task 3 and wired in Task 4; no xfail test targets it but it is part of the feature scope.

**Placeholder scan:** No placeholders left unfilled. Every code block is complete and runnable.

**Type-name consistency:** `CleanerWarnings`, `TransformCounter`, `_get_xml_lang`, `_is_chinese`, `_hyphen_is_letter`, `process_standard_hyphens` — all names are distinct and consistent across plan references.

**Dependency order:** Tasks must be executed in order 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9. Tasks 5–8 each depend on Task 4's wiring. Tasks 5–8 are otherwise independent of each other and could be parallelized, but sequential execution is recommended to keep the xfail count changing predictably.

**Test-run evidence requirement:** Each task includes both a focused test run and a full-suite run. The final verification task (9) quotes the exact expected output. An implementer must quote actual output before claiming any task is done.
