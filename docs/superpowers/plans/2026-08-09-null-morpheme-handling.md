# Null-Morpheme Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement null-morpheme (`∅`) handling across clean_xml, standardize, validate_glosses, and add_phonology, plus PHON punctuation hygiene, per `docs/superpowers/specs/2026-08-09-null-morpheme-handling-design.md`.

**Architecture:** clean_xml canonicalizes the marker glyph (`ø`/`Ø`/`∅` → `∅` in morpheme position, all FORM tiers) and stops deleting nulls; standardize.py removes null units from S-level standard FORMs (non-`--copy` modes) while W/M retain them; a new HARD gloss rule V069 enforces W→M null propagation; add_phonology renders nulls silent and drops unmapped punctuation from PHON.

**Tech Stack:** Python 3.13 (repo venv at `/workspace/FormosanBank/.venv`), pytest, lxml + xml.etree, regex.

## Global Constraints

- Branch: `feature/null-morpheme-handling`, worktree `/workspace/FormosanBank/.claude/worktrees/null-morpheme-on-shared-source`. All commands run from the worktree root.
- Run tests with: `/workspace/FormosanBank/.venv/bin/python -m pytest <path> -v`
- Canonical null marker is `∅` (U+2205 EMPTY SET). Legacy glyphs: `ø` (U+00F8), `Ø` (U+00D8).
- "Morpheme position" = both neighbors are a string edge, whitespace, or ASCII `-` (U+002D).
- "Null unit" = `∅-`, `-∅`, or standalone `∅` (marker + one bridging hyphen, removed together).
- Segmentation is ASCII `-` only. NEVER map dash punctuation (`–` U+2013, `—` U+2014, `－` U+FF0D, `−` U+2212) to `-`.
- Do NOT edit any file under `Corpora/` — tooling only; data updates happen on later cleaning runs.
- Do NOT touch C012's segmentation-stripping responsibilities beyond what Task 2 specifies — moving segmentation stripping to standardize.py belongs to a different branch.
- Commit messages end with: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`

---

### Task 1: clean_xml.py — glyph normalization (null markers + look-alike hyphens)

**Files:**
- Modify: `QC/cleaning/clean_xml.py` (new function near `normalize_caret_variants` ~line 328; `swap_punctuation` dict ~line 417; `clean_text` chain ~line 513)
- Create: `tests/fixtures/null_morpheme_normalization.xml`
- Test: `tests/cleaners/test_clean_xml_extensions.py`

**Interfaces:**
- Produces: `normalize_null_morphemes(text: str) -> str` (module-level in `QC/cleaning/clean_xml.py`), called inside `clean_text`. Tasks 2–6 assume FORM text reaching them uses only `∅`.

- [ ] **Step 1: Baseline** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/cleaners/ -q`. Expected: all pass. If not, STOP and report.

- [ ] **Step 2: Write failing tests** — append to `tests/cleaners/test_clean_xml_extensions.py`:

```python
def test_null_marker_glyphs_normalized_in_all_tiers(
    tmp_path, fixtures_dir, copy_fixture
):
    """ø/Ø/∅ in morpheme position normalize to canonical ∅ in every FORM
    (original AND standard, S/W/M levels). Letter-adjacent ø (Danish
    'Grønland') is untouched — it is a foreign letter, not an annotation."""
    work = copy_fixture(
        fixtures_dir / "null_morpheme_normalization.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    assert orig == "∅-sitangah bangcal-∅ ∅ ma-kero Grønland.", f"original: {orig!r}"
    assert _form_texts_with_kindof(work, "W", "original") == ["∅-sitangah"]
    assert _form_texts_with_kindof(work, "M", "original") == ["∅", "sitangah"]


def test_lookalike_hyphens_normalized_but_dashes_preserved(tmp_path):
    """U+2010/U+2011 hyphen look-alikes become ASCII '-'; dash punctuation
    (en dash, em dash, fullwidth, minus) passes through untouched."""
    corpus = tmp_path / "corpus" / "XML"
    corpus.mkdir(parents=True)
    xml = corpus / "dash.xml"
    xml.write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<TEXT id="T_DASH" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        'xml:lang="ami" dialect="unknown">\n'
        '  <S id="S_1">\n'
        '    <FORM kindOf="original">ma‐kero ma‑kero 8:1–19:14 '
        'a—b －5 −5</FORM>\n'
        "  </S>\n"
        "</TEXT>\n",
        encoding="utf-8",
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    orig = _form_texts_with_kindof(xml, "S", "original")[0]
    assert orig == "ma-kero ma-kero 8:1–19:14 a—b －5 −5", (
        f"original: {orig!r}"
    )
```

- [ ] **Step 3: Create the fixture** `tests/fixtures/null_morpheme_normalization.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<!--
  Glyph-normalization fixture (Sakizaya): null markers ø (U+00F8), Ø (U+00D8),
  and ∅ (U+2205) in morpheme position (string edge / whitespace / '-' on both
  sides) normalize to the canonical ∅ in EVERY FORM: original and standard,
  S/W/M levels. "Grønland" pins the guard: a letter-adjacent ø is a foreign
  letter, never an annotation, and must survive in all tiers.
  "ma-kero" pins that ordinary segmentation hyphens are unrelated to
  normalization (C012 handles them, standard tier only).
-->
<TEXT id="TEST_NULL_NORM" citation="test" BibTeX_citation="@test{test}" copyright="test" xml:lang="szy" dialect="unknown">
  <S id="S_1">
    <FORM kindOf="original">ø-sitangah bangcal-Ø ∅ ma-kero Grønland.</FORM>
    <FORM kindOf="standard">ø-sitangah bangcal-Ø ∅ ma-kero Grønland.</FORM>
    <W id="S_1_W_1">
      <FORM kindOf="original">ø-sitangah</FORM>
      <M id="S_1_W_1_M_1">
        <FORM kindOf="original">ø</FORM>
      </M>
      <M id="S_1_W_1_M_2">
        <FORM kindOf="original">sitangah</FORM>
      </M>
    </W>
  </S>
</TEXT>
```

- [ ] **Step 4: Run tests to verify they fail** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/cleaners/test_clean_xml_extensions.py -k "null_marker_glyphs or lookalike_hyphens" -v`. Expected: FAIL (original still `ø-sitangah…` / `ma‐kero…`).

- [ ] **Step 5: Implement.** In `QC/cleaning/clean_xml.py`:

(a) Add after `normalize_caret_variants` (~line 351):

```python
# Null-morpheme markers attested in source data: 'ø' (U+00F8, NTU Grammar
# Sakizaya/Kanakanavu), 'Ø' (U+00D8, legacy), and the canonical '∅'
# (U+2205 EMPTY SET). A glyph counts as a null morpheme ONLY in morpheme
# position — both neighbors are a string edge, whitespace, or the ASCII
# segmentation hyphen — so the same letters inside foreign proper nouns
# (Danish 'Grønland', 'Børn' in the Wikipedia corpora) are never touched.
_NULL_MORPHEME_RE = re.compile(r"(^|[\s\-])[øØ∅](?=[\s\-]|$)")


def normalize_null_morphemes(text: str) -> str:
    """Canonicalize null-morpheme marker glyphs to '∅' (U+2205).

    Applies to every FORM tier, original included: the marker glyph is
    annotation, not source spelling, so canonicalizing it keeps the
    original tier faithful. Removal of null units is standardize.py's
    job (S-level standard FORMs only) — this function only renames.
    """
    return _NULL_MORPHEME_RE.sub(lambda m: m.group(1) + "∅", text)
```

(b) In `swap_punctuation`'s `fullwidth_to_regular` dict, add (with this exact comment):

```python
        '‐': '-',  # U+2010 HYPHEN — look-alike of ASCII hyphen-minus
        '‑': '-',  # U+2011 NON-BREAKING HYPHEN — look-alike
        # NEVER add dash punctuation here (– U+2013, — U+2014, － U+FF0D,
        # − U+2212): dashes are range/parenthetical punctuation in the
        # corpora; mapping them to '-' would fabricate segmentation.
```

(c) In `clean_text`, insert between `swap_punctuation` and `normalize_whitespace`:

```python
    text = swap_punctuation(text)
    text = normalize_null_morphemes(text)
    text = normalize_whitespace(text)
```

and add to the docstring pipeline list, after item 2:

```
      2b. normalize_null_morphemes — ø/Ø/∅ in morpheme position → canonical
          '∅' (U+2205). Letter-adjacent glyphs (foreign loanwords) untouched.
```

- [ ] **Step 6: Run tests to verify they pass** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/cleaners/test_clean_xml_extensions.py -k "null_marker_glyphs or lookalike_hyphens" -v`. Expected: PASS. NOTE: the two pre-existing `test_C012_null_morpheme_*` tests may now fail because normalization feeds `∅` into C012's old `Ø`-only deletion regex — that is Task 2's subject. If they fail, confirm the failure mode is the null marker surviving (or glyph mismatch), then proceed to Task 2 BEFORE committing; commit Tasks 1+2 together in that case.

- [ ] **Step 7: Run the whole cleaner suite** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/cleaners/ -q`. If only `test_C012_null_morpheme_*` fail → proceed to Task 2 and commit jointly. If anything else fails, fix before proceeding.

- [ ] **Step 8: Commit** (or defer to Task 2's commit if C012 tests are red):

```bash
git add QC/cleaning/clean_xml.py tests/fixtures/null_morpheme_normalization.xml tests/cleaners/test_clean_xml_extensions.py
git commit -m "Normalize null-morpheme glyphs to canonical ∅ in clean_xml

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: clean_xml.py — C012 stops deleting nulls, skips null-adjacent hyphens

**Files:**
- Modify: `QC/cleaning/clean_xml.py:154-190` (`_process_standard_hyphens`)
- Modify: `tests/cleaners/test_clean_xml_extensions.py` (the two `test_C012_null_morpheme_*` tests, ~line 793-840)
- Modify: `tests/fixtures/c012_null_morpheme_in_standard_trv.xml`, `tests/fixtures/c012_null_morpheme_in_standard_bunun.xml` (comment blocks only)

**Interfaces:**
- Consumes: Task 1's normalization (C012 runs after `clean_text`, so it sees only `∅`).
- Produces: C012 that never deletes `∅` and never strips a hyphen adjacent to `∅`. Task 3 (standardize.py) is the sole remover of null units.

- [ ] **Step 1: Rewrite the two existing C012 null tests** to pin the new behavior (replace their bodies entirely):

```python
def test_C012_null_unit_survives_standard_hyphen_stripping(
    tmp_path, fixtures_dir, copy_fixture
):
    """C012 no longer deletes null morphemes: removal lives in
    standardize.py alone (spec 2026-08-09-null-morpheme-handling). The
    marker is normalized to ∅ (clean_text) and its bridging hyphen is
    SKIPPED by hyphen stripping so the unit stays recognizable."""
    work = copy_fixture(
        fixtures_dir / "c012_null_morpheme_in_standard_trv.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert std == "∅-dhuq sapah ka tama da.", f"standard: {std!r}"

    orig = _form_texts_with_kindof(work, "S", "original")[0]
    assert orig == "∅-dhuq sapah ka tama da.", f"original: {orig!r}"


def test_C012_null_unit_and_letter_hyphens_both_survive(
    tmp_path, fixtures_dir, copy_fixture
):
    """Bunun ('-' is a letter): letter hyphens are preserved as before,
    and the null unit's bridging hyphen is preserved too (as part of the
    unit, not as a letter)."""
    work = copy_fixture(
        fixtures_dir / "c012_null_morpheme_in_standard_bunun.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert std == "∅-ma-baliv-an.", f"standard: {std!r}"


def test_C012_ordinary_hyphens_still_stripped_alongside_null_unit(
    tmp_path, fixtures_dir, copy_fixture
):
    """In the normalization fixture (Sakizaya, '-' not a letter): ordinary
    segmentation hyphens are stripped from S-standard while every
    null-adjacent hyphen survives."""
    work = copy_fixture(
        fixtures_dir / "null_morpheme_normalization.xml", tmp_path
    )
    proc = _run_clean(tmp_path)
    assert proc.returncode == 0, f"stderr: {proc.stderr}"

    std = _form_texts_with_kindof(work, "S", "standard")[0]
    assert std == "∅-sitangah bangcal-∅ ∅ makero Grønland.", f"standard: {std!r}"
```

- [ ] **Step 2: Run to verify failures** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/cleaners/test_clean_xml_extensions.py -k "C012_null or C012_ordinary" -v`. Expected: FAIL (old code deletes `Ø` only / strips all hyphens).

- [ ] **Step 3: Implement.** Replace `_process_standard_hyphens`'s body (keep the signature). New docstring and code:

```python
_HYPHEN_NOT_NULL_ADJACENT_RE = re.compile(r"(?<!∅)-(?!∅)")


def _strip_segmentation_keeping_null_units(text: str) -> str:
    """Strip segmentation '-' and clitic '=' but keep null units intact.

    A hyphen bridging a null morpheme ('∅-' / '-∅') is part of the null
    unit, which standardize.py removes as a whole (non---copy modes);
    stripping it here would fuse the marker into the word ('∅dhuq') and
    make it unrecognizable — notably in --copy corpora, whose standard
    tier legitimately retains null units.
    """
    return _HYPHEN_NOT_NULL_ADJACENT_RE.sub("", text).replace("=", "")
```

and in `_process_standard_hyphens`:
- DELETE the line `text = re.sub(r"Ø-|-Ø|Ø", "", text)` and the docstring paragraph about `Ø` stripping; replace that paragraph with:

```
    Null morphemes are NOT deleted here (they were prior to the 2026-08-09
    null-morpheme spec): standardize.py removes them from S-level standard
    FORMs. C012 only guarantees it never destroys a null unit — hyphens
    adjacent to '∅' are skipped when stripping, and skipped by the
    hyphen-is-letter warning (they are annotation, not letters).
```

- Replace both `return text.replace("-", "").replace("=", "")` occurrences with `return _strip_segmentation_keeping_null_units(text)`.
- In the warning loop (hyphen-is-letter preserve path), skip null-adjacent hyphens:

```python
        if warnings is not None:
            for i, ch in enumerate(text):
                if ch != "-":
                    continue
                if (i > 0 and text[i - 1] == "∅") or (
                    i + 1 < len(text) and text[i + 1] == "∅"
                ):
                    continue  # null-unit hyphen: annotation, not a letter
                warnings.add("c012", xml_file, s_id, ch, i)
```

- [ ] **Step 4: Update the two fixture comment blocks** to describe the new behavior (normalization + unit preservation; removal deferred to standardize.py). Do not change the fixture data — `Ø` input pins the normalization path.

- [ ] **Step 5: Run tests** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/cleaners/ -q`. Expected: ALL PASS (including Task 1's if deferred).

- [ ] **Step 6: Commit**

```bash
git add QC/cleaning/clean_xml.py tests/cleaners/test_clean_xml_extensions.py tests/fixtures/c012_null_morpheme_in_standard_trv.xml tests/fixtures/c012_null_morpheme_in_standard_bunun.xml
git commit -m "C012: stop deleting null morphemes, keep null units intact

Null removal now lives in standardize.py alone; C012 skips hyphens
adjacent to ∅ so the unit survives for it (and in --copy corpora).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: standardize.py — remove null units from S-level standard FORMs

**Files:**
- Modify: `QC/utilities/standardize.py` (new function after `apply_standard` ~line 89; two call sites in `main` ~lines 196-202 and 277-280)
- Test: `tests/utilities/test_standardize.py`

**Interfaces:**
- Consumes: FORM text canonicalized to `∅` (Task 1).
- Produces: `remove_null_units(element)` — takes an S/W/M element, edits its `FORM[@kindOf='standard']` text in place. Called ONLY for `element.tag == "S"` in non-`--copy` modes, after `create_standard`, before `apply_standard`.

- [ ] **Step 1: Write failing tests** — append to `tests/utilities/test_standardize.py`:

```python
_NULL_XML = (
    '<TEXT id="T_NULL" citation="t" BibTeX_citation="@t{t}" copyright="t" '
    'xml:lang="szy" dialect="unknown">'
    '<S id="1"><FORM kindOf="original">∅-sitangah kero-∅ ∅ misa</FORM>'
    '<W id="1-W1"><FORM kindOf="original">∅-sitangah</FORM>'
    '<M id="1-W1-M1"><FORM kindOf="original">∅</FORM></M>'
    '<M id="1-W1-M2"><FORM kindOf="original">sitangah</FORM></M>'
    "</W></S></TEXT>"
)


def test_remove_accents_strips_null_units_from_S_standard_only(tmp_path):
    """Non-copy modes remove null units (∅-, -∅, standalone ∅) from the
    S-level standard FORM before any other transformation; W/M standard
    FORMs and the original tier retain them."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(corpus, "n.xml", _NULL_XML)
    proc = _run_standardize(["--remove_accents", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    assert root.findtext("./S/FORM[@kindOf='standard']") == "sitangah kero misa"
    assert root.findtext("./S/W/FORM[@kindOf='standard']") == "∅-sitangah"
    assert root.findtext("./S/W/M/FORM[@kindOf='standard']") == "∅"
    assert (
        root.findtext("./S/FORM[@kindOf='original']") == "∅-sitangah kero-∅ ∅ misa"
    )


def test_tsv_mode_strips_null_units_from_S_standard(tmp_path):
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(corpus, "n.xml", _NULL_XML)
    tsv = tmp_path / "map.tsv"
    tsv.write_text("original\ttarget\nkero\tkiro\n", encoding="utf-8")
    proc = _run_standardize([
        "--tsv_path", str(tsv),
        "--target_column", "target",
        "--corpora_path", str(corpus),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    assert root.findtext("./S/FORM[@kindOf='standard']") == "sitangah kiro misa"
    assert root.findtext("./S/W/FORM[@kindOf='standard']") == "∅-sitangah"
    assert root.findtext("./S/W/M/FORM[@kindOf='standard']") == "∅"


def test_copy_mode_retains_null_units_in_S_standard(tmp_path):
    """--copy is a pure duplication: the standard tier keeps null units."""
    corpus = tmp_path / "corpus"
    work = _write_corpus_xml(corpus, "n.xml", _NULL_XML)
    proc = _run_standardize(["--copy", "--corpora_path", str(corpus)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    root = ET.parse(work).getroot()
    assert (
        root.findtext("./S/FORM[@kindOf='standard']") == "∅-sitangah kero-∅ ∅ misa"
    )
```

- [ ] **Step 2: Run to verify failure** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/utilities/test_standardize.py -k "null_units" -v`. Expected: the two non-copy tests FAIL (standard still contains `∅`); the `--copy` test PASSES already (pin it anyway).

- [ ] **Step 3: Implement.** In `QC/utilities/standardize.py`, add after `apply_standard`:

```python
# Null-morpheme units in an S-level standard FORM: the canonical marker
# '∅' (U+2205) plus one bridging segmentation hyphen. Removed as a unit
# so no dangling hyphen is left (matters where '-' is a letter: Bunun,
# Thao). Must run BEFORE any hyphen stripping elsewhere in the pipeline,
# while units are still recognizable.
_NULL_UNIT_RE = re.compile(r"∅-|-∅|∅")


def remove_null_units(element):
    """Remove null-morpheme units from an element's standard FORM.

    Called for S elements only (never W/M — the morpheme tier is where a
    null is meaningful) and never in --copy mode (pure duplication).
    """
    form = element.find("FORM[@kindOf='standard']")
    if form is None or not form.text:
        return
    stripped = _NULL_UNIT_RE.sub("", form.text)
    if stripped != form.text:
        form.text = re.sub(r" {2,}", " ", stripped).strip()
```

Call sites in `main` — the `--remove_accents` branch becomes:

```python
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            if element.tag == "S":
                                remove_null_units(element)
                            apply_standard(element, [])
```

and the TSV-mode loop becomes:

```python
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            if element.tag == "S":
                                remove_null_units(element)
                            apply_standard(element, standard)
```

The `--copy` branch is untouched.

- [ ] **Step 4: Run tests** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/utilities/test_standardize.py -q`. Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/standardize.py tests/utilities/test_standardize.py
git commit -m "standardize: remove null-morpheme units from S-level standard FORMs

All modes except --copy; W/M standard FORMs retain ∅ (the morpheme
tier is where a null is meaningful).

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: validate_glosses — new HARD rule V069 (null in W requires null M)

**Files:**
- Modify: `QC/validation/rules/gloss.py` (new rule after `v068_M_reconstructs_W` ~line 630; register in `RULES` ~line 634)
- Test: `tests/validators/test_validate_glosses.py`

**Interfaces:**
- Consumes: `_get_w_form(w_elem)` (preferred FORM: original > any > ''), `_m_forms(m_elem)` (all direct-child FORM texts), `Finding`, `Severity` — all already in `gloss.py`.
- Produces: `v069_null_morpheme_in_W_requires_null_M(tree, path, index) -> list[Finding]`, registered in `RULES` (rule title auto-derives from the function name via `_rule_titles.py` — no other registration needed).

- [ ] **Step 1: Write failing tests** — append to `tests/validators/test_validate_glosses.py` (uses the existing `_TEXT_TEMPLATE` / `_findings_for` helpers):

```python
# ---------------------------------------------------------------------------
# V069: null morpheme in W FORM requires a null M child (HARD)
# ---------------------------------------------------------------------------


def test_v069_fires_when_W_has_null_but_no_null_M():
    xml = _TEXT_TEMPLATE.format(body=(
        '<S id="s1"><FORM kindOf="original">∅-dhuq</FORM>'
        '<W id="w1"><FORM kindOf="original">∅-dhuq</FORM>'
        '<M id="m1"><FORM>dhuq</FORM></M>'
        "</W></S>"
    ))
    findings = _findings_for(
        gloss_rules.v069_null_morpheme_in_W_requires_null_M, xml
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "V069"
    assert findings[0].severity is Severity.HARD
    assert "w1" in findings[0].message


def test_v069_passes_when_null_M_present():
    xml = _TEXT_TEMPLATE.format(body=(
        '<S id="s1"><FORM kindOf="original">∅-dhuq</FORM>'
        '<W id="w1"><FORM kindOf="original">∅-dhuq</FORM>'
        '<M id="m1"><FORM>∅</FORM></M>'
        '<M id="m2"><FORM>dhuq</FORM></M>'
        "</W></S>"
    ))
    assert _findings_for(
        gloss_rules.v069_null_morpheme_in_W_requires_null_M, xml
    ) == []


def test_v069_noop_without_M_children():
    xml = _TEXT_TEMPLATE.format(body=(
        '<S id="s1"><FORM kindOf="original">∅-dhuq</FORM>'
        '<W id="w1"><FORM kindOf="original">∅-dhuq</FORM></W></S>'
    ))
    assert _findings_for(
        gloss_rules.v069_null_morpheme_in_W_requires_null_M, xml
    ) == []


def test_v069_ignores_non_standalone_null_glyph():
    """A ∅ embedded between letters is not a null morpheme (morpheme
    position requires edge/whitespace/'-' neighbors)."""
    xml = _TEXT_TEMPLATE.format(body=(
        '<S id="s1"><FORM kindOf="original">a∅b</FORM>'
        '<W id="w1"><FORM kindOf="original">a∅b</FORM>'
        '<M id="m1"><FORM>a∅b</FORM></M>'
        "</W></S>"
    ))
    assert _findings_for(
        gloss_rules.v069_null_morpheme_in_W_requires_null_M, xml
    ) == []
```

- [ ] **Step 2: Run to verify failure** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_validate_glosses.py -k v069 -v`. Expected: FAIL with `AttributeError: ... no attribute 'v069_null_morpheme_in_W_requires_null_M'`.

- [ ] **Step 3: Implement.** In `QC/validation/rules/gloss.py`, after `v068_M_reconstructs_W` and before the `RULES` list:

```python
# ---------------------------------------------------------------------------
# V069: null morpheme '∅' in W FORM must appear as its own M FORM (HARD)
# ---------------------------------------------------------------------------

_STANDALONE_NULL_RE = re.compile(r"(?:^|(?<=[\s\-]))∅(?=[\s\-]|$)")


def v069_null_morpheme_in_W_requires_null_M(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V069 HARD: if a W's preferred FORM contains a standalone null-morpheme
    marker '∅' (bordered by string edges, whitespace, or segmentation '-')
    and the W has at least one child M, then at least one child M FORM (any
    kindOf) must be exactly '∅'.

    Rationale: the standard tier keeps null morphemes at the W and M levels
    (standardize.py strips them from S-level FORMs only), so a W spelled
    '∅-dhuq' must decompose into M '∅' + M 'dhuq'. A missing null M silently
    drops the zero morpheme from the gloss tier.

    No-ops on Ws with no M children (V061 covers M counts).
    """
    findings: list[Finding] = []
    for w in tree.iter("W"):
        w_form = _get_w_form(w)
        if not _STANDALONE_NULL_RE.search(w_form):
            continue
        ms = [child for child in w if child.tag == "M"]
        if not ms:
            continue
        null_m_present = any(
            text.strip() == "∅"
            for m in ms
            for text in _m_forms(m)
        )
        if null_m_present:
            continue
        w_id = w.get("id") or ""
        parent_s = w.getparent()
        s_id = parent_s.get("id") if parent_s is not None and parent_s.tag == "S" else None
        loc = f"W={w_id}" if w_id else "W"
        if s_id:
            loc = f"S={s_id} {loc}"
        findings.append(Finding(
            rule_id="V069",
            severity=Severity.HARD,
            message=(
                f"W id={w_id!r}: W FORM {w_form!r} contains a null morpheme "
                "'∅' but no child M FORM is '∅'; the null morpheme must "
                "appear on the M tier"
            ),
            path=path,
            location=loc,
        ))
    return findings
```

Add `v069_null_morpheme_in_W_requires_null_M,` to `RULES` after `v068_M_reconstructs_W,`.

- [ ] **Step 4: Run tests** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_validate_glosses.py -q`. Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add QC/validation/rules/gloss.py tests/validators/test_validate_glosses.py
git commit -m "Add V069 (HARD): null morpheme in W FORM requires a null M child

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: add_phonology — null morphemes are silent

**Files:**
- Modify: `QC/utilities/add_phonology.py` (`phonologize`, ~line 288)
- Test: `tests/utilities/test_add_phonology.py`

**Interfaces:**
- Consumes: `phonologize(text, profile)`, `load_profile`, and the `_write_profile(monkeypatch, tmp_path, *, language, tsv, rules=None, scheme=...)` test helper.
- Produces: `NULL_MARKER = "∅"` module constant; `phonologize` returns `"∅"` for whole-null forms and silently drops embedded null units. Applies uniformly to every tier/level (also covers `--copy` corpora's standard S tier, which retains nulls).

- [ ] **Step 1: Write failing tests** — append to `tests/utilities/test_add_phonology.py`:

```python
def test_whole_null_form_gets_visible_null_phon(tmp_path, monkeypatch):
    """A FORM that IS a null morpheme (the M-level case) gets PHON '∅' —
    never an empty PHON element."""
    scheme = _write_profile(
        monkeypatch, tmp_path, language="Yami", tsv="letter\tIPA\na\tɑ\nk\tk\n"
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("∅", profile) == "∅"
    assert phonologize(" ∅ ", profile) == "∅"


def test_embedded_null_units_are_silent(tmp_path, monkeypatch):
    """Null units inside a larger form are dropped as units (marker +
    bridging hyphen) before mapping, so PHON is clean IPA with no '*'."""
    scheme = _write_profile(
        monkeypatch, tmp_path, language="Yami", tsv="letter\tIPA\na\tɑ\nk\tk\n"
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("∅-aka", profile) == "ɑkɑ"
    assert phonologize("aka-∅", profile) == "ɑkɑ"
    assert phonologize("aka ∅ aka", profile) == "ɑkɑ ɑkɑ"


def test_foreign_o_slash_is_not_treated_as_null(tmp_path, monkeypatch):
    """Only canonical '∅' is null. A Danish 'ø' (foreign letter, e.g.
    'Grønland') follows the normal unknown-letter path — starred, never
    silently deleted."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\ng\tg\nr\tr\nn\tn\nl\tl\na\tɑ\nd\td\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("Grønland", profile) == "gr*nlɑnd"
```

- [ ] **Step 2: Run to verify failure** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/utilities/test_add_phonology.py -k "null_phon or null_units or o_slash" -v`. Expected: first two FAIL (`∅` → `*` today); the third may already PASS (pin it regardless).

- [ ] **Step 3: Implement.** In `QC/utilities/add_phonology.py`, add module constants after the `_REPO_ROOT` import block:

```python
NULL_MARKER = "∅"
# A null unit is the marker plus one bridging segmentation hyphen, removed
# as a unit so no dangling hyphen is left where '-' is a mapped letter
# (Bunun, Thao). Only the canonical U+2205 counts: 'ø'/'Ø' normalization is
# clean_xml's job, so foreign letters are never swallowed here.
_NULL_UNIT_RE = re.compile(r"∅-|-∅|∅")
```

(ensure `import re` exists at the top — add it if missing). Then change the head of `phonologize`:

```python
def phonologize(text: str, profile: PhonologyProfile) -> str:
    """Convert FORM text with a TSV profile and its ordered contextual rules."""
    # A form that IS a null morpheme has no sound; keep a visible marker so
    # the PHON tier is never empty (the M-level '∅' case).
    if text.strip() == NULL_MARKER:
        return NULL_MARKER
    # Null morphemes inside a larger form are silent: drop the unit before
    # mapping so PHON is clean IPA.
    stripped = _NULL_UNIT_RE.sub("", text)
    if stripped != text:
        text = re.sub(r" {2,}", " ", stripped).strip()
    result = apply_phonology_mappings(
        text,
        profile.mappings,
    )
```

(the rest of the function is unchanged in this task).

- [ ] **Step 4: Run tests** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/utilities/test_add_phonology.py -q`. Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/add_phonology.py tests/utilities/test_add_phonology.py
git commit -m "add_phonology: null morphemes are silent; whole-null FORM gets PHON ∅

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: add_phonology — drop unmapped punctuation from PHON

**Files:**
- Modify: `QC/utilities/add_phonology.py` (`phonologize` final filter, ~lines 296-310)
- Modify: `tests/utilities/test_add_phonology.py` (`test_unknown_characters_star_but_unicode_punct_and_marks_survive`, ~line 503)

**Interfaces:**
- Consumes: Task 5's `phonologize` head (the `∅` early return must stay BEFORE the filter).
- Produces: PHON output free of unmapped punctuation. Mapped punctuation (consumed by the tokenizer, e.g. `'` → `ʔ`) is unaffected; whitespace, combining marks (category M), profile IPA characters, and `*` survive.

- [ ] **Step 1: Write failing test + update the pinned old behavior.** Append:

```python
def test_unmapped_punctuation_dropped_from_phon(tmp_path, monkeypatch):
    """PHON is a phonetic tier: punctuation that no mapping consumed is
    deleted, not copied through. Mapped punctuation (the orthographic
    apostrophe here) is consumed by the tokenizer and unaffected."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\nk\tk\na\tɑ\nu\tu\nc\tʦ\ny\tj\n'\tʔ\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("kaku, ca'ay.", profile) == "kɑku ʦɑʔɑj"


def test_dash_punctuation_dropped_from_phon(tmp_path, monkeypatch):
    """Typographic dashes (en dash here) are punctuation, not segmentation:
    they are dropped by the punctuation filter, not hyphen handling."""
    scheme = _write_profile(
        monkeypatch, tmp_path, language="Yami", tsv="letter\tIPA\na\tɑ\n"
    )
    profile = load_profile(scheme, "Yami", "Yami")
    assert phonologize("a–a", profile) == "ɑɑ"
```

and REPLACE `test_unknown_characters_star_but_unicode_punct_and_marks_survive` with:

```python
def test_unknown_characters_star_marks_survive_punctuation_dropped(
    tmp_path, monkeypatch
):
    """Unmapped characters become `*`, combining marks (M*) survive, and
    unmapped punctuation — ASCII and Unicode P* alike — is dropped (the
    2026-08-09 null-morpheme/punctuation spec; previously punctuation was
    copied through to PHON)."""
    scheme = _write_profile(
        monkeypatch,
        tmp_path,
        language="Yami",
        tsv="letter\tIPA\na\tɑ\n",
    )
    profile = load_profile(scheme, "Yami", "Yami")

    # a -> ɑ; `…` (Po) dropped; space survives; `卐` (Lo) and `◇` (So) -> `*`.
    assert phonologize("a… 卐◇", profile) == "ɑ **"
    # a combining acute (Mn, U+0301) rides through rather than being starred,
    # whereas a precomposed accented letter (a base Ll not in the table) is
    # unknown and becomes `*`. (Use the escape sequences verbatim — NFC
    # á and NFD a+combining are visually identical in source code.)
    assert phonologize("a\u0301", profile) == "\u0251\u0301"
    assert phonologize("\u00e1", profile) == "*"
```

- [ ] **Step 2: Run to verify failure** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/utilities/test_add_phonology.py -k "punctuation_dropped or dash_punctuation" -v`. Expected: FAIL (punctuation currently survives).

- [ ] **Step 3: Implement.** Replace the final filter loop in `phonologize` with:

```python
    output = []
    for character in result:
        category = unicodedata.category(character)
        if (
            character in profile.ipa_characters
            or character == "*"
            or character.isspace()
            or category.startswith("M")
        ):
            output.append(character)
        elif character in string.punctuation or category.startswith("P"):
            # Unmapped punctuation is not sound: drop it from PHON. Mapped
            # punctuation (e.g. an orthographic apostrophe) was consumed by
            # the tokenizer above and is unaffected.
            continue
        else:
            output.append("*")
    return "".join(output)
```

(`character == "*"` keeps both the `*` characters this loop emits for unknown letters and any `*` already present in FORM text — `*` is ASCII punctuation and would otherwise be dropped.)

- [ ] **Step 4: Run tests** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/utilities/test_add_phonology.py -q`. Expected: ALL PASS.

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/add_phonology.py tests/utilities/test_add_phonology.py
git commit -m "add_phonology: drop unmapped punctuation from PHON output

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Full-suite verification

**Files:**
- No new files. Fix any fallout in the files touched above only.

- [ ] **Step 1: Run the entire test suite** — Run: `/workspace/FormosanBank/.venv/bin/python -m pytest tests/ -q`. Expected: ALL PASS. Known interaction risks to check if failures appear: V068 `M_reconstructs_W` with `∅` forms; C022 `*`-warning tests; orthography-detector tests consuming `clean_text`.

- [ ] **Step 2: Sanity-run the two touched CLIs on a scratch copy** (never on `Corpora/` in place):

```bash
mkdir -p /tmp/nulltest && cp -r Corpora/NTUFormosanCorpus/XML/Grammar/Sakizaya /tmp/nulltest/XML
/workspace/FormosanBank/.venv/bin/python QC/cleaning/clean_xml.py --corpora_path /tmp/nulltest
grep -c "∅" /tmp/nulltest/XML/Sakizaya.xml   # expect > 0 (ø normalized)
grep -c "ø-" /tmp/nulltest/XML/Sakizaya.xml  # expect 0
rm -rf /tmp/nulltest
```

- [ ] **Step 3: Commit any fallout fixes** (if none, no commit):

```bash
git add -u
git commit -m "Fix test fallout from null-morpheme handling

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
