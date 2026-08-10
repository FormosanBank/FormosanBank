# `'`-as-quotation correction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing quote/glottal classifier into `clean_xml` so that, before `standardize.py`, `original`-tier apostrophes used as quotation are rewritten to `"`, glottal apostrophes are left, and ambiguous ones are logged as warnings — delivered end-to-end for Amis.

**Architecture:** A pure correction function in `classify_quotes.py` turns the classifier's per-`'` verdicts into (rewritten text, corrected positions, ambiguous positions). A new generator builds a precomputed per-language attestation dictionary under `QC/validation/reference/<Language>/attestation.txt`. `clean_xml` resolves each file's language, loads that dictionary (skipping correction when absent — the roll-out gate), and applies the correction to sentence-level `original` FORMs, logging `c024` per rewrite and `c023` per ambiguous (suppressed for the Wikipedias corpus).

**Tech Stack:** Python 3.13, `lxml`, `pytest`. Reuses `QC/utilities/classify_quotes.py` and `QC/corpus_counts.resolve_language`.

## Global Constraints

- Correction applies to **sentence-level `original` FORMs only** — never `standard` (owned by `standardize.py`), never W/M FORMs.
- Correction runs **after** `clean_text` normalization (quotes already ASCII) and **before** `standardize.py`.
- Dictionaries and words are compared **casefolded**.
- Attestation dictionary is **one file per language** (not per dialect): `QC/validation/reference/<Language>/attestation.txt`, newline-delimited, sorted, casefolded.
- Default interior-token frequency threshold is **3**, exposed as `--min-freq`.
- Every `'`→`"` rewrite is logged as a `c024` warning row; every ambiguous `'` as a `c023` row (except under the Wikipedias corpus, where `c023` is suppressed).
- Cross-`QC` imports in a run-as-script file require inserting the repo root into `sys.path` first (pattern: `QC/cleaning/apply_manual_edits.py:14-16`).
- `QUOTE = "'"` (ASCII apostrophe) throughout.

---

### Task 1: `apply_quote_corrections()` — pure correction function

**Files:**
- Modify: `QC/utilities/classify_quotes.py` (add one function near `classify`)
- Test: `tests/utilities/test_classify_quotes.py` (append)

**Interfaces:**
- Consumes: existing `classify(form_text, dictionary) -> list[(int, str)]`, `translation_confirms_glottal(form_text, transl_texts) -> bool`, module constant `QUOTE`.
- Produces: `apply_quote_corrections(form_text: str, transls: list[str], dictionary) -> tuple[str, list[int], list[int]]` returning `(new_text, corrected_positions, ambiguous_positions)`. `corrected_positions` and `ambiguous_positions` are indices into `form_text` (same indexing as `classify`); `new_text` is `form_text` with `'`→`"` at every `corrected_positions` index. Glottal outcomes are neither rewritten nor reported.

- [ ] **Step 1: Write the failing tests**

Append to `tests/utilities/test_classify_quotes.py`:

```python
# --- apply_quote_corrections tests (temporary) ---
from QC.utilities.classify_quotes import apply_quote_corrections as aqc


def test_apply_rewrites_quotation_pair():
    # 'cima (after ':') ... tayni' -> QUOTATION pair; both ' become "
    text = "pasowal: 'cima tayni'"
    new_text, corrected, ambiguous = aqc(text, [], DICT)
    assert ambiguous == []
    assert len(corrected) == 2
    # every corrected index is now a double quote, and nothing else changed
    for i in corrected:
        assert new_text[i] == '"'
    assert new_text == "".join('"' if i in corrected else c
                               for i, c in enumerate(text))


def test_apply_leaves_glottal_pair_untouched():
    text = "o 'ayam ko faloco' iso"
    new_text, corrected, ambiguous = aqc(text, [], DICT)
    assert new_text == text
    assert corrected == []
    assert ambiguous == []


def test_apply_reports_ambiguous_without_rewriting():
    text = "'ayam faloco',"
    new_text, corrected, ambiguous = aqc(text, [], DICT)
    assert new_text == text
    assert corrected == []
    assert len(ambiguous) == 2


def test_apply_transl_first_pass_short_circuits():
    # A quotation-looking pair, but the TRANSL has no quotes -> all glottal.
    text = "pasowal: 'cima tayni'"
    new_text, corrected, ambiguous = aqc(text, ["he spoke to Cima"], DICT)
    assert new_text == text
    assert corrected == []
    assert ambiguous == []


def test_apply_no_quote_is_noop():
    text = "o wawa no tao"
    assert aqc(text, [], DICT) == (text, [], [])
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/utilities/test_classify_quotes.py -k apply -v`
Expected: FAIL — `cannot import name 'apply_quote_corrections'`.

- [ ] **Step 3: Implement `apply_quote_corrections`**

Add to `QC/utilities/classify_quotes.py`, immediately after the `classify` function:

```python
def apply_quote_corrections(form_text, transls, dictionary):
    """Decide each ' in an original-tier FORM and apply quotation rewrites.

    Runs the TRANSL first pass, then the per-' classifier. Returns
    ``(new_text, corrected_positions, ambiguous_positions)`` where:
      - new_text            -- form_text with every QUOTATION ' replaced by "
      - corrected_positions -- indices in form_text rewritten ' -> "
      - ambiguous_positions -- indices in form_text classified AMBIGUOUS
    Glottal outcomes leave the ' untouched and are not reported. Positions
    index into the ORIGINAL form_text (rewrites are 1-char-for-1-char).
    """
    if QUOTE not in form_text:
        return form_text, [], []
    if translation_confirms_glottal(form_text, transls):
        return form_text, [], []
    corrected, ambiguous = [], []
    for idx, label in classify(form_text, dictionary):
        if label == "QUOTATION":
            corrected.append(idx)
        elif label == "AMBIGUOUS":
            ambiguous.append(idx)
    if corrected:
        chars = list(form_text)
        for idx in corrected:
            chars[idx] = '"'
        new_text = "".join(chars)
    else:
        new_text = form_text
    return new_text, corrected, ambiguous
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/utilities/test_classify_quotes.py -v`
Expected: PASS (all prior tests plus the 5 new ones).

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/classify_quotes.py tests/utilities/test_classify_quotes.py
git commit -m "classify_quotes: apply_quote_corrections (QUOTATION '->\" + ambiguous positions)"
```

---

### Task 2: `build_attestation_dict.py` — per-language dictionary generator

**Files:**
- Create: `QC/utilities/build_attestation_dict.py`
- Test: `tests/utilities/test_build_attestation_dict.py`
- Modify: `.claude/skills/port-corpus-in/SKILL.md` (add regen step)
- Generate (artifact, committed): `QC/validation/reference/Amis/attestation.txt`

**Interfaces:**
- Consumes: `QC.corpus_counts.resolve_language(code, dialect) -> str | None`, `QC.corpus_counts.XML_LANG`; from `QC.utilities.classify_quotes`: `PUNCT`, `_strip_flanking_punct`, `_is_letter`.
- Produces: CLI `build_attestation_dict.py --language <Name> [--min-freq N] [--corpora_path P] [--reference_dir R]`; and importable `build_attestation_set(forms_by_sentence: list[list[str]], min_freq: int) -> set[str]` where each inner list is the whitespace-split tokens of one S-FORM. Writes `<reference_dir>/<Language>/attestation.txt`.

- [ ] **Step 1: Write the failing test**

Create `tests/utilities/test_build_attestation_dict.py`:

```python
import importlib.util
from pathlib import Path

_MODULE = (Path(__file__).resolve().parents[2] / "QC" / "utilities"
           / "build_attestation_dict.py")
_spec = importlib.util.spec_from_file_location("build_attestation_dict", _MODULE)
bad = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bad)


def test_build_set_unions_singleword_and_frequent_interior():
    # sentence tokenizations (already whitespace-split):
    forms = [
        ["faloco'"],                       # single-word S-FORM -> included
        ["o", "wawa", "no", "tao"],        # interior: wawa, no
        ["o", "wawa", "ko", "'ayam"],      # interior: wawa, ko
        ["a", "wawa", "sa", "ira"],        # interior: wawa, sa
    ]
    result = bad.build_attestation_set(forms, min_freq=3)
    assert "faloco'" in result          # single-word S-FORM (any length)
    assert "wawa" in result             # interior freq 3 >= 3
    assert "no" not in result           # interior freq 1 < 3
    assert "o" not in result            # sentence-initial, never counted
    assert "tao" not in result          # sentence-final, never counted


def test_build_set_is_casefolded():
    forms = [["Wawa"], ["o", "WAWA", "ko", "x"], ["a", "wawa", "sa", "y"]]
    result = bad.build_attestation_set(forms, min_freq=2)
    assert "wawa" in result
    assert "Wawa" not in result and "WAWA" not in result


def test_generator_writes_reference_file(tmp_path):
    # Build a tiny Amis corpus and run the generator end-to-end.
    corp = tmp_path / "Corpora" / "Toy" / "XML"
    corp.mkdir(parents=True)
    (corp / "t.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEXT id="t" citation="c" copyright="p" xml:lang="ami">\n'
        '  <S id="1"><FORM kindOf="original">faloco\'</FORM></S>\n'
        '  <S id="2"><FORM kindOf="original">o wawa no tao</FORM></S>\n'
        '  <S id="3"><FORM kindOf="original">o wawa ko ira</FORM></S>\n'
        '  <S id="4"><FORM kindOf="original">a wawa sa nay</FORM></S>\n'
        '</TEXT>\n', encoding="utf-8")
    ref = tmp_path / "reference"
    bad.main([
        "--language", "Amis", "--min-freq", "3",
        "--corpora_path", str(tmp_path / "Corpora"),
        "--reference_dir", str(ref),
    ])
    out = (ref / "Amis" / "attestation.txt").read_text(encoding="utf-8")
    words = out.split()
    assert "faloco'" in words
    assert "wawa" in words
    assert "no" not in words
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/utilities/test_build_attestation_dict.py -v`
Expected: FAIL — module/file does not exist.

- [ ] **Step 3: Implement the generator**

Create `QC/utilities/build_attestation_dict.py`:

```python
"""Build a per-language attestation dictionary for the quote/glottal classifier.

The set is the union of:
  A) single-word sentence-level S-FORMs (whitespace-free tokens), and
  B) interior tokens (neither sentence-initial nor sentence-final),
     punctuation-stripped, containing >=1 letter/digit, with frequency
     >= --min-freq,
across all Corpora/*/XML files whose TEXT xml:lang resolves to <Language>,
using both original and standard S-FORM tiers. Output: newline-delimited,
sorted, casefolded, to <reference_dir>/<Language>/attestation.txt.

Regenerate whenever a corpus is ported (the port-corpus-in skill runs this),
or standalone at any time.
"""
import argparse
import glob
import os
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.corpus_counts import resolve_language, XML_LANG
from QC.utilities.classify_quotes import PUNCT, _strip_flanking_punct, _is_letter


def _has_letter_or_digit(word: str) -> bool:
    return any(_is_letter(ch) or ch.isdigit() for ch in word)


def build_attestation_set(forms_by_sentence, min_freq):
    """Union of single-word S-FORMs and >=min_freq interior tokens (casefolded).

    forms_by_sentence: list of token lists (each = one S-FORM, whitespace-split).
    """
    singleword = set()
    interior = Counter()
    for toks in forms_by_sentence:
        if len(toks) == 1:
            core = _strip_flanking_punct(toks[0]).casefold()
            if core:
                singleword.add(core)
        for t in toks[1:-1]:                       # exclude initial + final
            core = _strip_flanking_punct(t).casefold()
            if core and _has_letter_or_digit(core):
                interior[core] += 1
    return singleword | {w for w, n in interior.items() if n >= min_freq}


def _iter_language_forms(corpora_path, language):
    """Yield token lists for every original/standard S-FORM in `language`."""
    for path in glob.iglob(os.path.join(corpora_path, "**", "*.xml"),
                           recursive=True):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "TEXT":
            continue
        code = root.get(XML_LANG)
        dialect = root.get("dialect")
        if resolve_language(code, dialect) != language:
            continue
        for s in root.findall("S"):
            for form in s.findall("FORM"):
                if form.get("kindOf") in ("original", "standard"):
                    text = " ".join("".join(form.itertext()).split())
                    if text:
                        yield text.split()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--language", required=True, help="Display name, e.g. Amis")
    ap.add_argument("--min-freq", type=int, default=3)
    ap.add_argument("--corpora_path", default=str(_REPO_ROOT / "Corpora"))
    ap.add_argument("--reference_dir",
                    default=str(_REPO_ROOT / "QC" / "validation" / "reference"))
    args = ap.parse_args(argv)

    forms = list(_iter_language_forms(args.corpora_path, args.language))
    words = build_attestation_set(forms, args.min_freq)
    out_dir = Path(args.reference_dir) / args.language
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "attestation.txt"
    out_path.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    print(f"{args.language}: {len(forms)} S-FORMs scanned -> "
          f"{len(words)} words -> {out_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/utilities/test_build_attestation_dict.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Generate the real Amis dictionary**

Run: `.venv/bin/python QC/utilities/build_attestation_dict.py --language Amis`
Expected: prints a scan summary and writes `QC/validation/reference/Amis/attestation.txt` (order-of ~13k words). Sanity-check: `wc -l QC/validation/reference/Amis/attestation.txt` (thousands), and `grep -c "'" QC/validation/reference/Amis/attestation.txt` (thousands of glottal-bearing words).

- [ ] **Step 6: Add the regeneration step to the port-corpus-in skill**

In `.claude/skills/port-corpus-in/SKILL.md`, after the Phase 4 section (validate-after-port), add a new subsection:

```markdown
### Phase 4b: Refresh attestation dictionaries

The quote/glottal correction in `clean_xml` reads a precomputed per-language
attestation dictionary. Now that this corpus adds new data, refresh it for
each language the corpus contains:

```bash
<python> <formosanbank_path>/QC/utilities/build_attestation_dict.py --language <Name>
```

Run once per distinct language in the ported corpus. Commit the updated
`QC/validation/reference/<Name>/attestation.txt` alongside the port.
(Languages whose orthography does not use `'` can be skipped.)
```

- [ ] **Step 7: Commit**

```bash
git add QC/utilities/build_attestation_dict.py \
        tests/utilities/test_build_attestation_dict.py \
        QC/validation/reference/Amis/attestation.txt \
        .claude/skills/port-corpus-in/SKILL.md
git commit -m "build_attestation_dict: per-language dict generator; generate Amis; port-corpus-in regen step"
```

---

### Task 3: `clean_xml` integration — correction hook + warnings + Wikipedia fiat

**Files:**
- Modify: `QC/cleaning/clean_xml.py` (imports + `analyze_and_modify_xml_file` + `main`/argparse)
- Test: `tests/cleaners/test_clean_xml_quote_correction.py`
- Modify: `Corpora/Wikipedias/README.md` (fiat policy note)
- Modify: `QC/README.md` (pipeline note)

**Interfaces:**
- Consumes: `apply_quote_corrections(form_text, transls, dictionary)` (Task 1); `resolve_language`, `XML_LANG` (via `QC.corpus_counts`); `QC/validation/reference/<Language>/attestation.txt` (Task 2); existing `CleanerWarnings.add(rule_id, file, s_id, char, pos)`, `TransformCounter.record(inp, out, count)`.
- Produces: correction behavior in `clean_xml`; new CLI flag `--reference_dir` (default repo `QC/validation/reference`).

**Legacy-test interaction (measured).** 96 existing cleaner fixtures use
`xml:lang="ami"`. Once the real Amis dictionary exists (Task 2 step 5), any
legacy cleaner test run **without** `--reference_dir` defaults to the real
reference dir and activates correction. An empirical scan of every fixture
against the Amis union dictionary found exactly **one** fixture that fires:
`xml_with_html_entities.xml` (one `AMBIGUOUS` → a single `c023` row, **no** text
change; its one test asserts FORM text, not warnings). So the suite is green
today — but to keep the legacy punctuation tests decoupled from future growth
of the Amis dictionary, this task insulates their shared `_run_clean` helper
behind an empty reference dir (Step 8). The new correction behavior is tested
in its own file with an explicit tiny dictionary.

- [ ] **Step 1: Write the failing tests**

Create `tests/cleaners/test_clean_xml_quote_correction.py`:

```python
"""Quote/glottal correction inside clean_xml (original tier).

clean_xml is run via subprocess against a tmp corpus. A tiny attestation
dictionary is written into a tmp reference dir passed with --reference_dir,
so tests do not depend on the full generated Amis dictionary.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

CLEAN_XML = Path(__file__).resolve().parents[2] / "QC" / "cleaning" / "clean_xml.py"


def _run(corpora_path, reference_dir):
    return subprocess.run(
        [sys.executable, str(CLEAN_XML),
         "--corpora_path", str(corpora_path),
         "--reference_dir", str(reference_dir)],
        capture_output=True, text=True)


def _write_dict(reference_dir, language, words):
    d = reference_dir / language
    d.mkdir(parents=True)
    (d / "attestation.txt").write_text("\n".join(words) + "\n", encoding="utf-8")


def _form_originals(xml_path):
    tree = etree.parse(str(xml_path))
    return [f.text or "" for f in tree.findall(".//S/FORM")
            if f.get("kindOf") == "original"]


def _warnings_rows(corpora_path):
    csv_path = corpora_path / "cleaner_warnings.csv"
    if not csv_path.exists():
        return []
    import csv as _csv
    with open(csv_path, encoding="utf-8") as fh:
        return list(_csv.DictReader(fh))


def _make_corpus(tmp_path, sub, form_original, transl=None):
    xdir = tmp_path / sub
    xdir.mkdir(parents=True)
    transl_xml = f'<TRANSL xml:lang="eng">{transl}</TRANSL>' if transl else ""
    (xdir / "t.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<TEXT id="t" citation="c" copyright="p" xml:lang="ami">\n'
        f'  <S id="1"><FORM kindOf="original">{form_original}</FORM>{transl_xml}</S>\n'
        '</TEXT>\n', encoding="utf-8")
    return xdir


def test_quotation_pair_rewritten_to_doublequote(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "loma'", "'ayam", "romi'ad", "cima"])
    # 'cima (after ':') ... tayni' -> not attested, opener after punct -> QUOTATION
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'cima tayni'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert "'" not in orig.split(":")[1]         # both quotes converted
    assert orig.count('"') == 2
    rows = _warnings_rows(tmp_path)
    assert sum(r["rule_id"] == "c024" for r in rows) == 2


def test_glottal_pair_left_intact_no_warning(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "loma'", "'ayam", "romi'ad", "cima"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "o 'ayam ko faloco' iso")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "o 'ayam ko faloco' iso"
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] in ("c023", "c024") for r in rows)


def test_ambiguous_emits_c023(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "'ayam faloco',")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "'ayam faloco',"                 # unchanged
    rows = _warnings_rows(tmp_path)
    assert sum(r["rule_id"] == "c023" for r in rows) == 2


def test_wikipedia_suppresses_c023(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam"])
    _make_corpus(tmp_path, "Corpora/Wikipedias/XML/Amis", "'ayam faloco',")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] == "c023" for r in rows)


def test_transl_no_quotes_leaves_form_intact(tmp_path):
    ref = tmp_path / "reference"
    _write_dict(ref, "Amis", ["faloco'", "'ayam", "cima"])
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'cima tayni'",
                 transl="he spoke to Cima")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "pasowal: 'cima tayni'"          # TRANSL first pass -> glottal
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] in ("c023", "c024") for r in rows)


def test_missing_dictionary_is_noop(tmp_path):
    ref = tmp_path / "reference"       # no Amis/ subdir
    ref.mkdir()
    _make_corpus(tmp_path, "Corpora/Toy/XML", "pasowal: 'cima tayni'")
    proc = _run(tmp_path, ref)
    assert proc.returncode == 0, proc.stderr
    (orig,) = _form_originals(tmp_path / "Corpora/Toy/XML/t.xml")
    assert orig == "pasowal: 'cima tayni'"          # untouched
    rows = _warnings_rows(tmp_path)
    assert not any(r["rule_id"] in ("c023", "c024") for r in rows)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/cleaners/test_clean_xml_quote_correction.py -v`
Expected: FAIL — `--reference_dir` unrecognized / no correction happens.

- [ ] **Step 3: Add imports + repo-root sys.path to `clean_xml.py`**

At the top of `QC/cleaning/clean_xml.py`, after the existing `from pathlib import Path` line, add:

```python
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.corpus_counts import resolve_language, XML_LANG
from QC.utilities.classify_quotes import QUOTE, apply_quote_corrections

_DEFAULT_REFERENCE_DIR = _REPO_ROOT / "QC" / "validation" / "reference"
```

- [ ] **Step 4: Add a dictionary loader helper**

Add this helper in `QC/cleaning/clean_xml.py` (module level, near the other helpers):

```python
def _load_attestation(language, reference_dir, cache):
    """Return the casefolded attestation set for `language`, or None if absent.

    `cache` is a dict reused across files in one run. A missing file caches
    None so we do not stat it repeatedly.
    """
    if language in cache:
        return cache[language]
    result = None
    if language:
        path = Path(reference_dir) / language / "attestation.txt"
        if path.exists():
            with open(path, encoding="utf-8") as fh:
                result = {w.strip().casefold() for w in fh if w.strip()}
    cache[language] = result
    return result
```

- [ ] **Step 5: Thread `reference_dir` + cache through `analyze_and_modify_xml_file`**

Change the signature of `analyze_and_modify_xml_file` to accept `reference_dir` and an attestation cache:

```python
def analyze_and_modify_xml_file(
    xml_dir,
    corpora_dir,
    warnings: CleanerWarnings | None = None,
    counter: TransformCounter | None = None,
    metadata_counter: dict[str, int] | None = None,
    reference_dir=None,
    _attestation_cache: dict | None = None,
):
```

At the top of the function body, before the `os.walk`, add:

```python
    if reference_dir is None:
        reference_dir = _DEFAULT_REFERENCE_DIR
    if _attestation_cache is None:
        _attestation_cache = {}
```

After `root = tree.getroot()` (where `root` is available for the file), resolve the language and dictionary and Wikipedia flag once per file:

```python
                language = resolve_language(root.get(XML_LANG), root.get("dialect"))
                dictionary = _load_attestation(language, reference_dir, _attestation_cache)
                is_wikipedia = "Wikipedias" in Path(xml_file).parts
```

- [ ] **Step 6: Add the correction pass inside the `S` loop**

Inside `for sentence in root.findall('.//S'):`, **after** the existing FORM-cleaning loop and the TRANSL-cleaning loop (so `original` FORMs already carry `clean_text` output and TRANSLs are normalized), add:

```python
                    # Quote/glottal correction: sentence-level ORIGINAL FORM only.
                    # W/M FORMs and the standard tier are intentionally excluded.
                    if dictionary is not None:
                        transl_texts = [
                            "".join(t.itertext())
                            for t in sentence.findall('TRANSL')
                            if "".join(t.itertext()).strip()
                        ]
                        for form_element in sentence.findall('FORM'):
                            if form_element.get("kindOf") != "original":
                                continue
                            ft = form_element.text
                            if not ft or QUOTE not in ft:
                                continue
                            new_text, corrected, ambiguous = apply_quote_corrections(
                                ft, transl_texts, dictionary)
                            if corrected:
                                form_element.text = new_text
                                modified = True
                                if counter is not None:
                                    counter.record("'", '"', len(corrected))
                                if warnings is not None:
                                    for pos in corrected:
                                        warnings.add("c024", xml_file,
                                                     sentence.get("id"), "'", pos)
                            if warnings is not None and not is_wikipedia:
                                for pos in ambiguous:
                                    warnings.add("c023", xml_file,
                                                 sentence.get("id"), "'", pos)
```

Note: `sentence.findall('FORM')` returns only direct children of `S`, so W/M FORMs (deeper descendants) are never touched here.

- [ ] **Step 7: Add `--reference_dir` to `main`/argparse and pass it through**

In `main(args)`, pass the reference dir and a shared cache into the call:

```python
    analyze_and_modify_xml_file(
        args.corpora_path,
        args.corpora_path,
        warnings=warnings,
        counter=counter,
        metadata_counter=metadata_counter,
        reference_dir=getattr(args, "reference_dir", None),
        _attestation_cache={},
    )
```

In the `if __name__ == "__main__":` argparse block, add:

```python
    parser.add_argument('--reference_dir', default=None,
                        help='dir holding <Language>/attestation.txt '
                             '(default: QC/validation/reference)')
```

- [ ] **Step 8: Insulate the legacy cleaner test helpers**

To decouple the pre-existing punctuation/Unicode tests from the real Amis
dictionary, point their shared `_run_clean` helper at an empty reference dir
(a nonexistent `<Language>/attestation.txt` → correction is a no-op). Make the
identical edit in **both** `tests/cleaners/test_clean_xml.py` and
`tests/cleaners/test_clean_xml_extensions.py`:

Change each helper from:

```python
def _run_clean(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLEAN_XML), "--corpora_path", str(corpora_path)],
        capture_output=True,
        text=True,
    )
```

to:

```python
def _run_clean(corpora_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLEAN_XML), "--corpora_path", str(corpora_path),
         # isolate legacy tests from the quote-correction dictionary
         "--reference_dir", str(corpora_path / "_noref")],
        capture_output=True,
        text=True,
    )
```

(The two inline `subprocess.run` calls in `test_clean_xml_extensions.py` use
fixtures outside the measured blast radius and need no change.)

- [ ] **Step 9: Run the new tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/cleaners/test_clean_xml_quote_correction.py -v`
Expected: PASS (7 tests).

- [ ] **Step 10: Run the full clean_xml + classifier test suites (no regressions)**

Run: `.venv/bin/python -m pytest tests/cleaners/ tests/utilities/test_classify_quotes.py tests/utilities/test_build_attestation_dict.py -v`
Expected: PASS. Legacy cleaner tests are now insulated (Step 8), so the real
Amis dictionary cannot affect them. If anything still regresses, surface it —
do not silently adjust a fixture's expected output.

- [ ] **Step 11: Document the Wikipedia fiat + pipeline behavior**

In `Corpora/Wikipedias/README.md`, add a short section:

```markdown
## Apostrophe (`'`) handling

The apostrophe is the glottal-stop letter in these orthographies. FormosanBank's
`clean_xml` correction rewrites `'` used as a quotation mark to `"` in the
`original` tier. Wikipedia articles carry no translations, so the classifier
cannot confirm most cases; **ambiguous `'` in this corpus are accepted as glottal
stops by fiat** and are not warned on. This should be revisited when a more
complete Amis (and per-language) attestation dictionary is available.
```

In `QC/README.md`, in the pipeline description near `clean_xml`, add a sentence:

```markdown
`clean_xml.py` also performs the `'`-as-quotation correction on the `original`
tier for languages that have a `QC/validation/reference/<Language>/attestation.txt`
dictionary: apostrophes used as quotation marks become `"`, ambiguous cases are
logged as `c023` warnings (suppressed for the Wikipedias corpus), and each
rewrite is logged as `c024`. See
`docs/superpowers/specs/2026-08-10-quote-glottal-correction-design.md`.
```

- [ ] **Step 12: Commit**

```bash
git add QC/cleaning/clean_xml.py \
        tests/cleaners/test_clean_xml_quote_correction.py \
        tests/cleaners/test_clean_xml.py \
        tests/cleaners/test_clean_xml_extensions.py \
        Corpora/Wikipedias/README.md QC/README.md
git commit -m "clean_xml: '-as-quotation correction on original tier (c023/c024, Wikipedia fiat)"
```

---

## Self-Review

**Spec coverage:**
- §A classifier core reused → Task 1 (`apply_quote_corrections`) wraps `classify`/`translation_confirms_glottal`; `main()` CLI untouched. ✔
- §B dictionary generator + reference file + per-language + `--min-freq` + port-corpus-in trigger → Task 2 (steps 3, 5, 6). ✔
- §C clean_xml hook, lang resolution, missing-dict gate, after-`clean_text` ordering, original-tier-only → Task 3 (steps 3–7). ✔
- §D c023/c024 + Wikipedia suppression + README → Task 3 (steps 6, 11). ✔
- Legacy-test isolation from the real Amis dict → Task 3 step 8 (measured blast radius = 1 fixture, warning-only). ✔
- §E tier scope (sentence-level original only; W/M excluded) → Task 3 step 6 (`sentence.findall('FORM')` + `kindOf=="original"`), asserted by the design note. ✔
- Error handling (missing dict no-op, unparseable unchanged, unresolved language skipped) → `_load_attestation` returns None + `if dictionary is not None` gate; Task 3 step 4/6; `test_missing_dictionary_is_noop`. ✔
- Testing list → Tasks 1–3 tests cover correction application, ambiguous warning, Wikipedia suppression, TRANSL first pass, missing-dict gate, generator. ✔

**Placeholder scan:** No TBD/TODO; all code blocks concrete. ✔

**Type consistency:** `apply_quote_corrections(form_text, transls, dictionary) -> (str, list[int], list[int])` defined in Task 1, consumed identically in Task 3 step 6. `build_attestation_set(forms_by_sentence, min_freq)` and `main(argv)` consistent between Task 2 test and implementation. `resolve_language`/`XML_LANG` names match `QC/corpus_counts.py`. `CleanerWarnings.add`/`TransformCounter.record` signatures match `clean_xml.py`. ✔
