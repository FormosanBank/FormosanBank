# standardize owns standard-tier cleaning — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move the standard-tier-specific cleaning (C012 hyphen/clitic/Ø stripping) out of `clean_xml.py` and into `standardize.py` (applied when it creates each standard FORM), add dash canonicalization to `clean_xml`'s original-tier cleanup, and thereby eliminate the redundant post-`standardize` `clean_xml` pass.

**Architecture:** `standardize` already regenerates every standard FORM (S/W/M) via `root.findall('.//FORM/..')`. It becomes the sole owner of standard-tier cleaning: after writing each standard FORM it applies C012 **only when the element is an `S`**. `clean_xml` stops touching any `FORM[@kindOf='standard']` and instead canonicalizes all dash/hyphen look-alikes to ASCII `-` on the original tier. No shared cleaning module — C012 lives in `standardize`, general cleanup stays in `clean_xml`.

**Tech Stack:** Python 3.13, stdlib + lxml (already used). Tests: pytest via subprocess on `tmp_path/XML/` copies (existing convention).

## Global Constraints

- Both scripts mutate XML in place; every test operates on a `tmp_path` copy, never a fixture in place. `--corpora_path` is a **collection root** — place the test XML at `tmp_path/XML/<file>.xml` and pass `tmp_path`.
- Scripts are driven by **subprocess** in tests (`sys.executable, str(SCRIPT), ...`), matching `tests/utilities/test_standardize.py` and `tests/cleaners/test_clean_xml.py`.
- `standardize` owns `FORM[@kindOf='standard']` at every level; `clean_xml` owns all `FORM[@kindOf='original']` + TRANSL + metadata.
- **C012 is S-level only** — W/M standard FORMs are recreated but never C012-stripped (they keep segmentation).
- Bunun (`bnn`) and Thao (`ssf`) are the only languages where `-` is an orthographic letter → preserve `-` (warn c012); every other language strips `-`.
- Run the full suites from the worktree root: `python -m pytest tests/utilities/test_standardize.py tests/cleaners/ -q`.

---

## File Structure

- **Modify** `QC/utilities/standardize.py` — gains the C012 machinery (moved from clean_xml), an `_apply_standard_hyphens` step, `--hard-remove-segmentation` / `--ortho-path` flags, and c012/c022 warnings.
- **Modify** `QC/cleaning/clean_xml.py` — FORM loop skips standard FORMs; C012 call + flags + the moved functions removed; `swap_punctuation` gains dash canonicalization.
- **Modify** `tests/utilities/test_standardize.py` — new C012 tests (behavior relocated here).
- **Modify** `tests/cleaners/test_clean_xml_extensions.py` — remove the now-obsolete `test_C012_*` tests; add dash-canonicalization test; fix the C003/C012 interaction test.

---

### Task 1: standardize applies C012 to the S-level standard FORM

**Files:**
- Modify: `QC/utilities/standardize.py`
- Test: `tests/utilities/test_standardize.py`

**Interfaces:**
- Produces: `_apply_standard_hyphens(element, lang_code, ortho_path, hard_remove, warnings, file_path)` — no-op unless `element.tag == 'S'`; strips/preserves hyphens in that S's `FORM[@kindOf='standard']`. Plus the moved `_process_standard_hyphens`, `_hyphen_is_letter`, `_resolve_ortho_path`, `_ISO_TO_LANG_NAME`, `_HYPHEN_IS_LETTER_CACHE`.
- New CLI flags: `--hard-remove-segmentation` (store_true), `--ortho-path` (str, default None).

- [ ] **Step 1: Write the failing tests**

Add to `tests/utilities/test_standardize.py`. These build XML inline (original tier carries the segmentation) and run `standardize --copy`:

```python
def _write_collection(tmp_path, xml_text: str) -> Path:
    d = tmp_path / "XML"
    d.mkdir(parents=True, exist_ok=True)
    (d / "t.xml").write_text(xml_text, encoding="utf-8")
    return tmp_path


def _std_text(tmp_path):
    tree = ET.parse(tmp_path / "XML" / "t.xml")
    return tree.find(".//S/FORM[@kindOf='standard']").text


AMIS = ('<TEXT id="t" citation="c" copyright="c" xml:lang="ami">'
        '<S id="S1"><FORM kindOf="original">mkan-ku-nhapuy</FORM></S></TEXT>')
BUNUN = ('<TEXT id="t" citation="c" copyright="c" xml:lang="bnn">'
         '<S id="S1"><FORM kindOf="original">ma-baliv-an</FORM></S></TEXT>')
THAO = ('<TEXT id="t" citation="c" copyright="c" xml:lang="ssf">'
        '<S id="S1"><FORM kindOf="original">qa-li-ka-tu</FORM></S></TEXT>')


def test_standardize_strips_hyphens_for_non_letter_language(tmp_path):
    root = _write_collection(tmp_path, AMIS)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    assert _std_text(root) == "mkankunhapuy"


def test_standardize_preserves_hyphens_for_bunun(tmp_path):
    root = _write_collection(tmp_path, BUNUN)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    assert _std_text(root) == "ma-baliv-an"


def test_standardize_preserves_hyphens_for_thao(tmp_path):
    root = _write_collection(tmp_path, THAO)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    assert _std_text(root) == "qa-li-ka-tu"


def test_standardize_hard_remove_strips_bunun(tmp_path):
    root = _write_collection(tmp_path, BUNUN)
    proc = _run_standardize(
        ["--corpora_path", str(root), "--copy", "--hard-remove-segmentation"])
    assert proc.returncode == 0, proc.stderr
    assert _std_text(root) == "mabalivan"


def test_standardize_strips_null_morpheme_marker(tmp_path):
    xml = ('<TEXT id="t" citation="c" copyright="c" xml:lang="ami">'
           '<S id="S1"><FORM kindOf="original">ka-Ø-en</FORM></S></TEXT>')
    root = _write_collection(tmp_path, xml)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    assert _std_text(root) == "kaen"


def test_standardize_leaves_WM_standard_segmentation(tmp_path):
    xml = ('<TEXT id="t" citation="c" copyright="c" xml:lang="ami">'
           '<S id="S1"><FORM kindOf="original">a-b</FORM>'
           '<W id="W1"><FORM kindOf="original">a-b</FORM>'
           '<M id="M1"><FORM kindOf="original">a-b</FORM></M></W></S></TEXT>')
    root = _write_collection(tmp_path, xml)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    tree = ET.parse(root / "XML" / "t.xml")
    assert tree.find(".//S/FORM[@kindOf='standard']").text == "ab"        # S stripped
    assert tree.find(".//W/FORM[@kindOf='standard']").text == "a-b"       # W kept
    assert tree.find(".//M/FORM[@kindOf='standard']").text == "a-b"       # M kept
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/utilities/test_standardize.py -k "hyphen or null_morpheme or WM_standard or hard_remove" -q`
Expected: FAIL — standard still contains hyphens (C012 not applied yet).

- [ ] **Step 3: Implement**

In `QC/utilities/standardize.py`, **copy verbatim** from `QC/cleaning/clean_xml.py` these blocks (they are being *moved*; Task 3 deletes them from clean_xml): `_ISO_TO_LANG_NAME` (clean_xml.py:81-98), `_HYPHEN_IS_LETTER_CACHE` (:99), `_resolve_ortho_path` (:102-111), `_hyphen_is_letter` (:113-152), `_process_standard_hyphens` (:154-192). Place them after the imports. (`re`, `Path` are already imported in standardize.)

Then add the S-guarded applier:

```python
def _apply_standard_hyphens(element, lang_code, ortho_path, hard_remove,
                            warnings, file_path):
    """Apply C012 to an S element's standard FORM. No-op for W/M (they keep
    segmentation) and for elements without a standard FORM."""
    if element.tag != "S":
        return
    form = element.find("FORM[@kindOf='standard']")
    if form is None or not form.text:
        return
    new_text = _process_standard_hyphens(
        form.text, file_path, element.get("id"), lang_code,
        warnings, hard_remove, ortho_path,
    )
    if new_text != form.text:
        form.text = new_text
```

Extract the ISO lang code once per file and call the applier after every
`create_standard`/`apply_standard` in all three mode branches. Right after
`root = tree.getroot()` (standardize.py ~line 194):

```python
                    lang_code = (
                        root.get("{http://www.w3.org/XML/1998/namespace}lang")
                        or root.get("xml:lang")
                        or root.get("lang")
                    )
```

Copy mode:
```python
                    if args.copy:
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            _apply_standard_hyphens(
                                element, lang_code, args.ortho_path,
                                args.hard_remove_segmentation, None, file)
```
remove_accents mode: same, add the `_apply_standard_hyphens(...)` call after `apply_standard(element, [])`. Normal mode: same, after `apply_standard(element, standard)`.

Add the flags in the argparse block:
```python
    parser.add_argument("--hard-remove-segmentation", dest="hard_remove_segmentation",
                        action="store_true", default=False,
                        help="strip '-' from standard even where it is a letter (Bunun/Thao)")
    parser.add_argument("--ortho-path", dest="ortho_path", default=None,
                        help="orthography dir for the hyphen-is-letter check (default Ortho113)")
```

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/utilities/test_standardize.py -q`
Expected: PASS (new tests + all existing standardize tests).

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/standardize.py tests/utilities/test_standardize.py
git commit -m "standardize: apply C012 hyphen handling to S-level standard FORM"
```

---

### Task 2: standardize emits c012/c022 warnings

**Files:**
- Modify: `QC/utilities/standardize.py`
- Test: `tests/utilities/test_standardize.py`

**Interfaces:**
- Consumes: `_apply_standard_hyphens` (Task 1), `CleanerWarnings` (imported from `QC.cleaning.clean_xml`).
- Produces: a `standardize_warnings.csv` under `--corpora_path` holding c012 (hyphen preserved) and c022 (`*` in standard FORM) rows.

- [ ] **Step 1: Write the failing tests**

```python
def _warnings_csv(tmp_path):
    p = tmp_path / "standardize_warnings.csv"
    return p.read_text(encoding="utf-8") if p.exists() else ""


def test_standardize_warns_c012_on_preserved_bunun(tmp_path):
    root = _write_collection(tmp_path, BUNUN)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    assert "c012" in _warnings_csv(root)


def test_standardize_warns_c022_on_star_in_standard(tmp_path):
    xml = ('<TEXT id="t" citation="c" copyright="c" xml:lang="ami">'
           '<S id="S1"><FORM kindOf="original">ka*en</FORM></S></TEXT>')
    root = _write_collection(tmp_path, xml)
    proc = _run_standardize(["--corpora_path", str(root), "--copy"])
    assert proc.returncode == 0, proc.stderr
    assert "c022" in _warnings_csv(root)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest tests/utilities/test_standardize.py -k "c012 or c022" -q`
Expected: FAIL — no `standardize_warnings.csv` written.

- [ ] **Step 3: Implement**

Import the warnings accumulator near the other QC imports in standardize.py:
```python
from QC.cleaning.clean_xml import CleanerWarnings  # noqa: E402
```
In `main(args)`, before the corpus loop, create the accumulator and, after the loop, write it:
```python
    warnings = CleanerWarnings(Path(args.corpora_path) / "standardize_warnings.csv")
    ...
    warnings.write_csv()
```
Thread `warnings` (instead of `None`) into every `_apply_standard_hyphens(...)` call. Extend `_apply_standard_hyphens` to emit c022 after C012:
```python
    if warnings is not None and form.text and "*" in form.text:
        for i, ch in enumerate(form.text):
            if ch == "*":
                warnings.add("c022", file_path, element.get("id"), ch, i)
```
(The c012 rows come for free — `_process_standard_hyphens` already calls `warnings.add("c012", ...)` on the Bunun/Thao preserve path.)

- [ ] **Step 4: Run to verify they pass**

Run: `python -m pytest tests/utilities/test_standardize.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/standardize.py tests/utilities/test_standardize.py
git commit -m "standardize: write c012/c022 warnings to standardize_warnings.csv"
```

---

### Task 3: clean_xml stops touching the standard tier

**Files:**
- Modify: `QC/cleaning/clean_xml.py`
- Test: `tests/cleaners/test_clean_xml_extensions.py`

**Interfaces:**
- Removes from `clean_xml`: the C012 call, `--hard-remove-segmentation`/`--ortho-path` flags, `ortho_path`/`hard_remove_segmentation` threading, and the moved functions (`_ISO_TO_LANG_NAME`, `_HYPHEN_IS_LETTER_CACHE`, `_resolve_ortho_path`, `_hyphen_is_letter`, `_process_standard_hyphens`).
- After this task, `clean_xml` never modifies a `FORM[@kindOf='standard']`.

- [ ] **Step 1: Write the failing test**

Add to `tests/cleaners/test_clean_xml_extensions.py` — clean_xml must leave the standard tier byte-exact while cleaning the original:

```python
def test_clean_xml_leaves_standard_forms_untouched(tmp_path):
    xml = ('<TEXT id="t" citation="c" copyright="c" xml:lang="ami">'
           '<S id="S1"><FORM kindOf="original">a-b</FORM>'
           '<FORM kindOf="standard">a-b</FORM></S></TEXT>')
    d = tmp_path / "XML"; d.mkdir(parents=True)
    (d / "t.xml").write_text(xml, encoding="utf-8")
    proc = subprocess.run([sys.executable, str(CLEAN_XML),
                           "--corpora_path", str(tmp_path)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    tree = etree.parse(str(d / "t.xml"))
    assert tree.find(".//S/FORM[@kindOf='standard']").text == "a-b"  # untouched
```

- [ ] **Step 2: Run to verify it fails / observe current behavior**

Run: `python -m pytest tests/cleaners/test_clean_xml_extensions.py -k leaves_standard -q`
Expected: FAIL — current clean_xml strips the standard hyphen (`a-b`→`ab`).

- [ ] **Step 3: Implement**

In `QC/cleaning/clean_xml.py`:
1. FORM loop ([:619](../../../QC/cleaning/clean_xml.py#L619)): restrict to non-standard FORMs. Change `form_elements = sentence.findall('.//FORM')` to:
   ```python
                    form_elements = [
                        f for f in sentence.findall('.//FORM')
                        if f.get("kindOf") != "standard"
                    ]
   ```
2. Delete the C012 block ([:665-682](../../../QC/cleaning/clean_xml.py#L665), the `# C012: handle hyphens…` comment through the `for s_form in sentence.findall("FORM[@kindOf='standard']"):` loop).
3. Delete the moved functions (`_ISO_TO_LANG_NAME`, `_HYPHEN_IS_LETTER_CACHE`, `_resolve_ortho_path`, `_hyphen_is_letter`, `_process_standard_hyphens`; clean_xml.py:81-192).
4. Remove the `--hard-remove-segmentation` and `--ortho-path` argparse entries and every reference to `hard_remove_segmentation` / `ortho_path` in `main`, `analyze_and_modify_xml_file`, and its signature.

- [ ] **Step 4: Remove the now-obsolete C012 tests**

In `tests/cleaners/test_clean_xml_extensions.py`, delete the C012-in-clean_xml tests whose behavior moved to standardize: `test_C012_amis_standard_hyphens_stripped`, `test_C012_bunun_standard_hyphens_preserved_with_warning`, `test_C012_thao_standard_hyphens_preserved_with_warning`, `test_C012_null_morpheme_marker_stripped_from_standard` (and any sibling C012/`--hard-remove-segmentation` cases in that block). For the C003+C012 interaction test (`test_...` near [:471](../../../tests/cleaners/test_clean_xml_extensions.py#L471) — "C003 collapses `---` → `-` in standard, then C012 strips"), update its expectation: clean_xml now only collapses `---`→`-` in the **original** tier and no longer strips it from standard. If the test asserted a standard-tier outcome, re-point it to the original tier or delete the standard-tier assertion.

- [ ] **Step 5: Run to verify**

Run: `python -m pytest tests/cleaners/ -q`
Expected: PASS (new test passes; obsolete C012 tests gone; no import errors from deleted functions — the tests import only `_get_xml_lang`, `CleanerWarnings`, `TransformCounter`, which remain).

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "clean_xml: stop cleaning the standard tier; remove C012 (moved to standardize)"
```

---

### Task 4: clean_xml canonicalizes dashes to '-'

**Files:**
- Modify: `QC/cleaning/clean_xml.py` (`swap_punctuation`)
- Test: `tests/cleaners/test_clean_xml_extensions.py`

**Interfaces:**
- Consumes: `swap_punctuation(text)` ([:411](../../../QC/cleaning/clean_xml.py#L411)).
- Produces: every hyphen/dash look-alike + full-width form maps to ASCII `-` (U+002D) in the original tier.

- [ ] **Step 1: Write the failing test**

```python
def test_clean_xml_canonicalizes_dashes_to_hyphen(tmp_path):
    variants = "‐‑‒–—―−﹘﹣－"
    xml = (f'<TEXT id="t" citation="c" copyright="c" xml:lang="ami">'
           f'<S id="S1"><FORM kindOf="original">a{variants}b</FORM></S></TEXT>')
    d = tmp_path / "XML"; d.mkdir(parents=True)
    (d / "t.xml").write_text(xml, encoding="utf-8")
    proc = subprocess.run([sys.executable, str(CLEAN_XML),
                           "--corpora_path", str(tmp_path)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    tree = etree.parse(str(d / "t.xml"))
    text = tree.find(".//S/FORM[@kindOf='original']").text
    assert text == "a" + "-" * len(variants) + "b"
```

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest tests/cleaners/test_clean_xml_extensions.py -k canonicalizes_dashes -q`
Expected: FAIL — the non-ASCII dashes survive unchanged.

- [ ] **Step 3: Implement**

In `swap_punctuation`'s `fullwidth_to_regular` dict, add the dash/hyphen family → `-`:
```python
        '‐': '-',  # HYPHEN
        '‑': '-',  # NON-BREAKING HYPHEN
        '‒': '-',  # FIGURE DASH
        '–': '-',  # EN DASH
        '—': '-',  # EM DASH
        '―': '-',  # HORIZONTAL BAR
        '−': '-',  # MINUS SIGN
        '﹘': '-',  # SMALL EM DASH
        '﹣': '-',  # SMALL HYPHEN-MINUS
        '－': '-',  # FULLWIDTH HYPHEN-MINUS
```

- [ ] **Step 4: Run to verify it passes**

Run: `python -m pytest tests/cleaners/ -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py
git commit -m "clean_xml: canonicalize dash/hyphen look-alikes to ASCII '-' on original tier"
```

---

### Task 5: Temporary regression run (NOT committed)

**Files:** none committed. Scratch scripts under `/tmp`.

**Interfaces:** none — this is a verification task.

- [ ] **Step 1: Equivalence snapshot of the C012 move**

For a `--copy` corpus (e.g. `Corpora/SEALS33`), a Bunun/Thao corpus, and a TSV corpus (e.g. `Corpora/Glosbe/XML/ami`): from a clean checkout of this branch's HEAD, run the OLD path (`git stash` the code changes → `standardize` then `clean_xml`) and the NEW path (code changes applied → `standardize` only), and diff the standard FORM + both PHON tiers with the content-level comparison from the audit work (whitespace-normalized, ignore serialization). Because Task 4 adds dash canonicalization, first canonicalize dashes on BOTH outputs so the comparison isolates the C012 move. Record any non-equal element.

Run (sketch):
```bash
python /tmp/equiv_check.py Corpora/SEALS33
```
Expected: no content differences beyond intended dash canonicalization.

- [ ] **Step 2: Song-Kanakanavu full pipeline**

Run the corpus's documented rebuild with the refactored scripts (drop the post-`standardize` `clean_xml`):
```bash
bash Corpora/Song-Kanakanavu-Grammar/CodeAndDocs/scripts/rebuild_final_xml.sh
```
Expected: `normalize_standard_forms.py` completes without raising (its asserts anchor the 128 decisions), and the final standard tier matches the committed one. If `normalize_standard_forms` only asserts decisions are *loaded* (not *applied*), add a throwaway assertion counting applied decisions == 128.

- [ ] **Step 3: Record findings**

Write a short note to `/tmp/refactor-regression-notes.md` (NOT committed) summarizing: equivalence result per corpus and the Kanakanavu outcome. Report back to the controller; do not commit anything in this task.

---

## Self-Review

**Spec coverage:**
- clean_xml restricted to non-standard FORMs → Task 3 step 3.1. ✓
- C012 removed from clean_xml + flags → Task 3 steps 3.2–3.4. ✓
- Dash canonicalization on original tier → Task 4. ✓
- standardize owns C012, S-level only, reusing lang/dialect, mixed-content safe → Task 1. ✓
- standardize gains flags → Task 1 step 3. ✓
- standardize emits c012/c022 to its own CSV → Task 2. ✓
- W/M recreated but keep segmentation → Task 1 `test_standardize_leaves_WM_standard_segmentation`. ✓
- Committed unit tests (dash map; C012 strip/preserve/hard-remove/mixed/W-M; clean_xml-leaves-standard; warnings) → Tasks 1,2,3,4. ✓
- Temporary equivalence + Kanakanavu → Task 5. ✓

**Placeholder scan:** The only "copy verbatim from clean_xml.py lines N–M" instructions (Task 1 step 3) are precise line-ranges for a code *move*, not placeholders; all new logic is given as runnable code. ✓

**Type consistency:** `_apply_standard_hyphens(element, lang_code, ortho_path, hard_remove, warnings, file_path)` — same 6-arg signature at its definition (Task 1) and all call sites (Tasks 1, 2). `_process_standard_hyphens(text, file_path, s_id, lang_code, warnings, hard_remove, ortho_path)` — matches the moved clean_xml signature and the Task 1 call. `CleanerWarnings(path)` + `.add(rule, file, s_id, ch, pos)` + `.write_csv()` — matches clean_xml usage. ✓

**Ordering note:** Task 1 adds C012 to standardize while clean_xml still has it (both apply it — idempotent, pipeline stays correct); Task 3 removes clean_xml's copy. No intermediate broken state.
