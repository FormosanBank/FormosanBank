# Unify Corpus Statistics Pipelines Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One counting implementation feeds both the per-corpus Gitbook CSVs (`get_corpus_stats.py`) and the size-over-time tracker (`corpus_metrics.py`), with the new counting rules (standard tier with original fallback; digit-only chunks count, punctuation-only chunks don't) locked in by tests.

**Architecture:** A new shared module `QC/corpus_counts.py` is the single source of truth for counting rules. `get_corpus_stats.py` becomes the counting engine that produces per-corpus CSVs committed under `statistics/`; `corpus_metrics.py` becomes an aggregator/visualizer that reads those CSVs for its snapshot outputs and appends one history row per CI run. XML-level counting remains importable (from `corpus_counts`) because two paths cannot run from CSVs: the PR token-comparison (`count_tokens.py` runs on arbitrary checkouts whose CSVs may be stale) and full history rebuilds from git blobs.

**Tech Stack:** Python 3.10 stdlib (`xml.etree`, `csv`), pytest (existing suite in `tests/`), GitHub Actions.

---

## Design decisions (already agreed with Joshua or verified against the repo)

1. **Direction of merge: inverted, as Joshua proposed, with two caveats.** `get_corpus_stats.py` computes; `corpus_metrics.py` aggregates per-corpus CSVs. Caveats that keep XML-level counting alive inside `corpus_counts.py`:
   - The token-comparison workflow runs `count_tokens.py` against two arbitrary checkouts (PR head and base via `git worktree`). CSVs on those checkouts are stale or absent, so this path must compute from XML.
   - Rebuilding `statistics/corpus_size_history.csv` from scratch walks git blobs at historical commits; no CSVs exist there. The rebuild path stays in `corpus_metrics.py` behind `--history-rebuild`, computed via the shared module.
2. **Tokenization rule:** a token is a whitespace-separated chunk containing at least one Unicode letter or digit (`any(c.isalnum() for c in chunk)`). Digit-only chunks count; punctuation-only chunks (`.` `?` `—` `"`) don't. This replaces both old rules (`corpus_metrics`: every `\S+` chunk; `get_corpus_stats`: delete `[0-9",!]` then split).
3. **Tier rule:** per sentence, use the `standard` FORM if it has non-whitespace text, else the `original` FORM, else count 0. Empirically verified 2026-06-10: all 437,302 sentences currently have a `standard` FORM, so the fallback is insurance, not a hot path.
4. **S-level only:** tokens come only from direct FORM children of S. The old `get_corpus_stats` fallback to W-level FORMs (when a file has no S-level FORM of the chosen kind) is **removed**; such sentences contribute 0 and are surfaced as a warning.
5. **Language identity:** from `xml:lang` + `dialect` attributes only (no path inference). `trv` + dialect `Truku` (case-insensitive) → Truku; `trv` + anything else → Seediq; all other codes map directly. **Verified caveat (scanned 2026-06-10):** every file has `xml:lang`, but 13,375 files in 4 corpora still lack `dialect`: Wikipedias (13,278 — the whole corpus: ami 2006, pwn 474, szy 5715, tay 3023, trv 2060), ePark (88 — exactly the 8 no-dialect-subdivision languages × 11 files), ILRDF_Dicts (8 — the same 8 languages), Glosbe (1 Amis file). Joshua is fixing these in the XMLs separately; the pipeline reports missing `dialect`/`xml:lang` as a warning with counts, not a hard failure, and such rows aggregate under dialect `''` (rendered "Not Specified" in reports, "UK" by the Gitbook).
6. **Per-corpus CSV is the published interface.** `FormosanBankGitbook/update_corpus_stats.py` reads it by column name (`language`, `dialect`, `word_count`, `segmented_words`, `glossed_words`, `eng_transl_count`, `zho_transl_count`, `transcribed_audio_count/seconds`, `untranscribed_audio_count/seconds`, `file_count`) and already promotes `('trv','Truku')` to Truku. **All existing column names are preserved**; new columns are appended (`sentences`, `word_elements`, `morpheme_elements`, `translation_elements`, `audio_elements`, `parse_errors`). Parse failures produce a pseudo-row with `language=''`, `dialect=''`, all data fields 0, `parse_errors=N` — the Gitbook's `row_has_data()` filters it out, verified by reading that function.
7. **Audio durations can't be computed in CI** (audio is gitignored; the runner has no audio files). Decision (Joshua, 2026-06-10): `get_corpus_stats.py` **never** computes durations — it always carries the seconds columns forward from the existing committed CSV (zeros for rows with no prior value), so local and CI runs behave identically. A separate manual command, `QC/utilities/update_audio_stats.py`, recomputes the seconds columns in place from local audio files; Joshua runs it for new corpora or when audio is re-downloaded/updated. Audio *counts* are always recomputed from XML by `get_corpus_stats.py`.
8. **History semantics change:** the tracker appends **one row per CI run at HEAD** (computed from the freshly generated CSVs) instead of one row per XML-changing commit. The blob-rollback machinery survives only behind `--history-rebuild`. Joshua has accepted the resulting discontinuity in the series (old rows = old rules, new rows = new rules; a full restatement is possible later via `--history-rebuild`).
9. **Known intentional behavior changes** (each gets a test): digit-only tokens now count; punctuation-only tokens no longer count; counting moves from original-tier to standard-tier; two same-language TRANSLs in one sentence no longer double-count that sentence's words; gloss/translation word counts use the same selected tier as the main count (was hardcoded `original`).
10. **Out of scope:** migrating XMLs to add missing `dialect` attributes; the Gitbook repo's copy of the CSVs (it has its own `statistics/` folder — syncing it stays whatever manual process it is today); `tokens_delta.py` / `plot_counts.py` / `plot_deltas.py` (unchanged — `count_tokens.py` keeps its exact JSON output shape).

Baseline numbers for sanity-checking (measured 2026-06-10 on 14,413 files): old `corpus_metrics` (form `first`): 8,058,955 tokens; old `get_corpus_stats`: 7,954,580. The new rule will land near but not exactly on either; Task 11 records the actual number.

---

### Task 1: `count_words` in the new shared module

**Files:**
- Create: `QC/corpus_counts.py`
- Create: `tests/utilities/test_corpus_counts.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/utilities/test_corpus_counts.py
"""Tests for QC/corpus_counts.py — the single source of truth for
FormosanBank counting rules (tokenization, tier selection, language
resolution, per-file analysis records)."""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "QC"))

import corpus_counts


class TestCountWords:
    def test_plain_words(self):
        assert corpus_counts.count_words("ina kaen wawa") == 3

    def test_digit_only_chunk_counts(self):
        # Joshua's rule 1: whitespace-separated digit-only chunks ARE words.
        assert corpus_counts.count_words("ina 123 wawa") == 3

    def test_punctuation_only_chunks_do_not_count(self):
        assert corpus_counts.count_words("ina wawa .") == 2
        assert corpus_counts.count_words("? ! — … \" '") == 0

    def test_mixed_alnum_and_punct_chunk_counts_once(self):
        assert corpus_counts.count_words("ma- kaen?") == 2

    def test_empty_and_none(self):
        assert corpus_counts.count_words("") == 0
        assert corpus_counts.count_words("   ") == 0
        assert corpus_counts.count_words(None) == 0

    def test_unicode_letters_count(self):
        # ʉ is a Unicode letter used in Formosan orthographies.
        assert corpus_counts.count_words("kʉnʉ ʉ") == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `source .venv/bin/activate` then `pytest tests/utilities/test_corpus_counts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'corpus_counts'`

- [ ] **Step 3: Write the minimal implementation**

```python
# QC/corpus_counts.py
"""Single source of truth for FormosanBank corpus counting rules.

Both statistics pipelines import from here:
  - QC/utilities/get_corpus_stats.py (per-corpus CSVs for the Gitbook)
  - QC/corpus_metrics.py and QC/count_tokens.py (size tracker + PR deltas)

Rules (decided 2026-06-10):
  - A token is a whitespace-separated chunk containing at least one
    Unicode letter or digit. "123" counts; "?" does not.
  - Per sentence, count the `standard` FORM if non-empty, else the
    `original` FORM, else 0. Word counts come from the S tier only —
    W and M FORMs are never counted as tokens.
  - Language identity comes from xml:lang + dialect attributes only:
    trv + dialect "Truku" is Truku; trv + anything else is Seediq.
"""
from __future__ import annotations

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

LANG_CODE_TO_NAME = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}

# All display names a record can resolve to (the 16 codes plus Truku,
# which is distinguished from Seediq by dialect rather than ISO code).
LANGUAGE_NAMES = sorted(set(LANG_CODE_TO_NAME.values()) | {"Truku"})

ENG_CODES = {"eng", "en"}
ZHO_CODES = {"zho", "zh", "zh-hant", "zh-hans"}


def count_words(text: str | None) -> int:
    """Count whitespace-separated chunks containing >=1 letter or digit."""
    if not text:
        return 0
    return sum(1 for chunk in text.split() if any(c.isalnum() for c in chunk))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add QC/corpus_counts.py tests/utilities/test_corpus_counts.py
git commit -m "feat(QC): shared corpus_counts module with agreed tokenization rule"
```

---

### Task 2: `select_sentence_form` (standard tier, original fallback)

**Files:**
- Modify: `QC/corpus_counts.py`
- Modify: `tests/utilities/test_corpus_counts.py`

- [ ] **Step 1: Write the failing tests** (append to the test file)

```python
def _sentence(*forms):
    """Build an <S> with (kindOf, text) FORM children."""
    s = ET.Element("S")
    for kind, text in forms:
        f = ET.SubElement(s, "FORM", {"kindOf": kind})
        f.text = text
    return s


class TestSelectSentenceForm:
    def test_prefers_standard(self):
        s = _sentence(("original", "orig text"), ("standard", "std text"))
        assert corpus_counts.select_sentence_form(s) == "std text"

    def test_falls_back_to_original_when_no_standard(self):
        s = _sentence(("original", "orig text"))
        assert corpus_counts.select_sentence_form(s) == "orig text"

    def test_falls_back_when_standard_is_empty(self):
        s = _sentence(("standard", "   "), ("original", "orig text"))
        assert corpus_counts.select_sentence_form(s) == "orig text"

    def test_none_when_no_usable_form(self):
        assert corpus_counts.select_sentence_form(_sentence()) is None
        assert corpus_counts.select_sentence_form(_sentence(("original", ""))) is None

    def test_ignores_w_level_forms(self):
        # S-tier only: a FORM nested under W must not be selected.
        s = ET.Element("S")
        w = ET.SubElement(s, "W")
        f = ET.SubElement(w, "FORM", {"kindOf": "standard"})
        f.text = "word-level"
        assert corpus_counts.select_sentence_form(s) is None
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: TestSelectSentenceForm tests FAIL with `AttributeError: module 'corpus_counts' has no attribute 'select_sentence_form'`

- [ ] **Step 3: Implement** (append to `QC/corpus_counts.py`)

```python
def select_sentence_form(sentence) -> str | None:
    """Return the text to count for one <S>: standard tier, else original.

    Only direct FORM children of S are considered (S-tier rule)."""
    for kind in ("standard", "original"):
        for form in sentence.findall("FORM"):
            if form.get("kindOf") == kind and form.text and form.text.strip():
                return form.text
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: 11 passed

- [ ] **Step 5: Commit**

```bash
git add QC/corpus_counts.py tests/utilities/test_corpus_counts.py
git commit -m "feat(QC): standard-with-original-fallback tier selection"
```

---

### Task 3: `resolve_language` (ISO code + dialect, Truku rule)

**Files:**
- Modify: `QC/corpus_counts.py`
- Modify: `tests/utilities/test_corpus_counts.py`

- [ ] **Step 1: Write the failing tests** (append)

```python
class TestResolveLanguage:
    def test_plain_code(self):
        assert corpus_counts.resolve_language("ami", "Haian") == "Amis"

    def test_trv_truku_dialect_is_truku(self):
        assert corpus_counts.resolve_language("trv", "Truku") == "Truku"
        assert corpus_counts.resolve_language("trv", "truku") == "Truku"

    def test_trv_other_dialect_is_seediq(self):
        assert corpus_counts.resolve_language("trv", "Tgdaya") == "Seediq"
        assert corpus_counts.resolve_language("trv", "unknown") == "Seediq"
        assert corpus_counts.resolve_language("trv", "") == "Seediq"

    def test_case_and_whitespace_normalized(self):
        assert corpus_counts.resolve_language(" AMI ", "x") == "Amis"

    def test_unknown_or_missing_code_returns_none(self):
        assert corpus_counts.resolve_language("xx", "y") is None
        assert corpus_counts.resolve_language("", "y") is None
        assert corpus_counts.resolve_language(None, "y") is None
```

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: TestResolveLanguage FAIL with AttributeError

- [ ] **Step 3: Implement** (append to `QC/corpus_counts.py`)

```python
def resolve_language(language_code: str | None, dialect: str | None) -> str | None:
    """Resolve (xml:lang, dialect) to a display language name.

    trv + dialect 'Truku' is Truku; trv + anything else is Seediq.
    Returns None for unknown or missing codes (caller decides how to
    label those)."""
    code = (language_code or "").strip().lower()
    if not code:
        return None
    if code == "trv" and (dialect or "").strip().lower() == "truku":
        return "Truku"
    return LANG_CODE_TO_NAME.get(code)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: 16 passed

- [ ] **Step 5: Commit**

```bash
git add QC/corpus_counts.py tests/utilities/test_corpus_counts.py
git commit -m "feat(QC): language resolution from xml:lang + dialect (Truku rule)"
```

---

### Task 4: Fixture corpus + `analyze_file` / `collect_records`

**Files:**
- Create: `tests/fixtures/stats_corpus/MiniCorpus/XML/ami_haian.xml`
- Create: `tests/fixtures/stats_corpus/MiniCorpus/XML/trv_truku.xml`
- Create: `tests/fixtures/stats_corpus/MiniCorpus/XML/trv_unknown.xml`
- Create: `tests/fixtures/stats_corpus/MiniCorpus/XML/ami_nodialect.xml`
- Create: `tests/fixtures/stats_corpus/MiniCorpus/XML/bad.xml`
- Modify: `QC/corpus_counts.py`
- Modify: `tests/utilities/test_corpus_counts.py`

- [ ] **Step 1: Create the fixture XMLs**

`tests/fixtures/stats_corpus/MiniCorpus/XML/ami_haian.xml` — exercises tier fallback, digit/punct tokens, gloss counting, TRANSL dedup, W-only sentences:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEXT id="fixA" xml:lang="ami" dialect="Haian" citation="test" BibTeX_citation="@misc{test}" copyright="CC BY-SA">
  <S id="fixA_s1">
    <FORM kindOf="original">O 123 wawa .</FORM>
    <FORM kindOf="standard">O 123 wawa .</FORM>
    <TRANSL xml:lang="eng">The child</TRANSL>
    <TRANSL xml:lang="zho">小孩</TRANSL>
    <W id="fixA_s1_w1">
      <FORM kindOf="original">wawa</FORM>
      <M id="fixA_s1_w1_m1">
        <FORM kindOf="original">wawa</FORM>
        <TRANSL xml:lang="eng">child</TRANSL>
      </M>
    </W>
  </S>
  <S id="fixA_s2">
    <FORM kindOf="original">ma- kaen ?</FORM>
    <TRANSL xml:lang="eng">eaten</TRANSL>
    <TRANSL xml:lang="eng" ver="literal">it is eaten</TRANSL>
  </S>
  <S id="fixA_s3">
    <W id="fixA_s3_w1"><FORM kindOf="original">foo</FORM></W>
    <W id="fixA_s3_w2"><FORM kindOf="original">bar</FORM></W>
  </S>
</TEXT>
```

Hand-computed expectations for this file: tokens 5 (s1: `O`,`123`,`wawa` = 3 — the `.` is punctuation-only; s2 falls back to original: `ma-`,`kaen` = 2 — `?` excluded; s3 has no S-level FORM → 0, with a warning); sentences 3; segmented_words 3 and glossed_words 3 (only s1 has M / M-with-TRANSL); eng_transl_count 5 (s1's 3 + s2's 2 — s2's two English TRANSLs count once); zho_transl_count 3; W elements 3; M elements 1; TRANSL elements 5.

`tests/fixtures/stats_corpus/MiniCorpus/XML/trv_truku.xml` — Truku resolution + audio:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEXT id="fixB" xml:lang="trv" dialect="Truku" citation="test" BibTeX_citation="@misc{test}" copyright="CC BY-SA">
  <AUDIO file="full.wav" url="http://example.com/full.wav"/>
  <S id="fixB_s1">
    <FORM kindOf="standard">Kari Truku .</FORM>
    <AUDIO file="clip.wav" start="0" end="1"/>
  </S>
</TEXT>
```

Expected: tokens 2; 1 transcribed AUDIO (inside S), 1 untranscribed (child of TEXT); audio_elements 2.

`tests/fixtures/stats_corpus/MiniCorpus/XML/trv_unknown.xml` — Seediq resolution:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEXT id="fixC" xml:lang="trv" dialect="unknown" citation="test" BibTeX_citation="@misc{test}" copyright="CC BY-SA">
  <S id="fixC_s1">
    <FORM kindOf="standard">kndsan na 5</FORM>
  </S>
</TEXT>
```

Expected: tokens 3 (digit-only `5` counts); resolves to Seediq.

`tests/fixtures/stats_corpus/MiniCorpus/XML/ami_nodialect.xml` — missing-dialect warning:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEXT id="fixD" xml:lang="ami" citation="test" BibTeX_citation="@misc{test}" copyright="CC BY-SA">
  <S id="fixD_s1">
    <FORM kindOf="standard">ina !</FORM>
  </S>
</TEXT>
```

Expected: tokens 1; warning `missing dialect`.

`tests/fixtures/stats_corpus/MiniCorpus/XML/bad.xml` — parse error (deliberately truncated):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<TEXT id="bad" xml:lang="ami" dialect="X">
  <S id="bad_s1">
```

- [ ] **Step 2: Write the failing tests** (append to `tests/utilities/test_corpus_counts.py`)

```python
FIXTURE_XML = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus" / "XML"


class TestAnalyzeFile:
    def test_ami_haian_record(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML / "ami_haian.xml")
        assert rec["language"] == "ami"
        assert rec["dialect"] == "Haian"
        assert rec["word_count"] == 5
        assert rec["sentences"] == 3
        assert rec["segmented_words"] == 3
        assert rec["glossed_words"] == 3
        assert rec["eng_transl_count"] == 5  # two eng TRANSLs in s2 count once
        assert rec["zho_transl_count"] == 3
        assert rec["word_elements"] == 3
        assert rec["morpheme_elements"] == 1
        assert rec["translation_elements"] == 5
        assert rec["audio_elements"] == 0
        assert rec["file_count"] == 1
        # s3 has W-level FORMs but no S-level FORM: contributes 0, warned.
        assert any("no countable FORM" in w for w in rec["warnings"])

    def test_truku_record_and_audio_counts(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML / "trv_truku.xml")
        assert rec["word_count"] == 2
        assert rec["transcribed_audio_count"] == 1
        assert rec["untranscribed_audio_count"] == 1
        assert rec["audio_elements"] == 2
        assert corpus_counts.resolve_language(rec["language"], rec["dialect"]) == "Truku"

    def test_missing_dialect_warns(self):
        rec = corpus_counts.analyze_file(FIXTURE_XML / "ami_nodialect.xml")
        assert rec["word_count"] == 1
        assert rec["dialect"] == ""
        assert any("missing dialect" in w for w in rec["warnings"])

    def test_parse_error_raises(self):
        with pytest.raises(ET.ParseError):
            corpus_counts.analyze_file(FIXTURE_XML / "bad.xml")


class TestCollectRecords:
    def test_walks_xml_dir_and_collects_errors(self):
        records, errors = corpus_counts.collect_records(FIXTURE_XML)
        assert len(records) == 4
        assert len(errors) == 1
        assert errors[0]["path"].endswith("bad.xml")
        assert sum(r["word_count"] for r in records) == 11  # 5 + 2 + 3 + 1
```

- [ ] **Step 3: Run tests to verify the new ones fail**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: TestAnalyzeFile / TestCollectRecords FAIL with AttributeError

- [ ] **Step 4: Implement** (append to `QC/corpus_counts.py`)

```python
import xml.etree.ElementTree as ET
from pathlib import Path

COUNT_FIELDS = (
    "word_count",
    "sentences",
    "segmented_words",
    "glossed_words",
    "eng_transl_count",
    "zho_transl_count",
    "transcribed_audio_count",
    "untranscribed_audio_count",
    "word_elements",
    "morpheme_elements",
    "translation_elements",
    "audio_elements",
    "file_count",
)


def split_audio_elements(root) -> tuple[list, list]:
    """Return (transcribed, untranscribed) AUDIO elements with a file attr.

    Transcribed = nested in S or W; untranscribed = direct child of TEXT."""
    transcribed = [e for e in root.findall(".//S/AUDIO") if "file" in e.attrib]
    transcribed += [e for e in root.findall(".//W/AUDIO") if "file" in e.attrib]
    untranscribed = [e for e in root.findall("AUDIO") if "file" in e.attrib]
    return transcribed, untranscribed


def analyze_root(root) -> dict:
    """Compute the per-file statistics record from a parsed TEXT element."""
    language = (root.get(XML_LANG) or "").strip().lower()
    dialect = (root.get("dialect") or "").strip()
    warnings = []
    if not language:
        warnings.append("missing xml:lang attribute")
    if not dialect:
        warnings.append("missing dialect attribute")

    record = {field: 0 for field in COUNT_FIELDS}
    record.update({"language": language, "dialect": dialect, "file_count": 1})

    for sentence in root.findall(".//S"):
        record["sentences"] += 1
        text = select_sentence_form(sentence)
        if text is None:
            if sentence.find("FORM") is None:
                warnings.append(
                    f"sentence {sentence.get('id', '?')} has no countable FORM at the S level"
                )
            n = 0
        else:
            n = count_words(text)
        record["word_count"] += n

        transl_langs = {
            (t.get(XML_LANG) or "").strip().lower()
            for t in sentence.findall("TRANSL")
            if t.text and t.text.strip()
        }
        if transl_langs & ENG_CODES:
            record["eng_transl_count"] += n
        if transl_langs & ZHO_CODES:
            record["zho_transl_count"] += n
        if sentence.find(".//M") is not None:
            record["segmented_words"] += n
        if sentence.find(".//M/TRANSL") is not None:
            record["glossed_words"] += n

    transcribed, untranscribed = split_audio_elements(root)
    record["transcribed_audio_count"] = len(transcribed)
    record["untranscribed_audio_count"] = len(untranscribed)
    record["word_elements"] = len(root.findall(".//W"))
    record["morpheme_elements"] = len(root.findall(".//M"))
    record["translation_elements"] = len(root.findall(".//TRANSL"))
    record["audio_elements"] = len(root.findall(".//AUDIO"))
    record["warnings"] = warnings
    return record


def analyze_file(xml_path) -> dict:
    """Parse one XML file and return its statistics record.

    Raises xml.etree.ElementTree.ParseError on malformed XML — callers
    decide whether to collect or abort."""
    root = ET.parse(xml_path).getroot()
    record = analyze_root(root)
    record["path"] = str(xml_path)
    return record


def collect_records(xml_dir) -> tuple[list[dict], list[dict]]:
    """Analyze every *.xml under xml_dir. Returns (records, parse_errors)."""
    records, parse_errors = [], []
    for xml_file in sorted(Path(xml_dir).rglob("*.xml")):
        try:
            records.append(analyze_file(xml_file))
        except Exception as exc:
            parse_errors.append({"path": str(xml_file), "error": str(exc)})
    return records, parse_errors
```

Move the `import xml.etree.ElementTree as ET` / `from pathlib import Path` lines up to the top of the module with the other imports.

- [ ] **Step 5: Run the full test file**

Run: `pytest tests/utilities/test_corpus_counts.py -v`
Expected: 22 passed

- [ ] **Step 6: Commit**

```bash
git add QC/corpus_counts.py tests/utilities/test_corpus_counts.py tests/fixtures/stats_corpus/
git commit -m "feat(QC): per-file analysis records + fixture mini-corpus"
```

---

### Task 5: Rewrite `get_corpus_stats.py` on the shared module

**Files:**
- Rewrite: `QC/utilities/get_corpus_stats.py`
- Create: `tests/utilities/test_get_corpus_stats.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/utilities/test_get_corpus_stats.py
"""End-to-end tests for QC/utilities/get_corpus_stats.py.

The script is run via subprocess (repo convention). The fixture corpus
is copied to tmp_path/Corpora/MiniCorpus/ so the script's repo-root
derivation (the path component before 'Corpora') lands on tmp_path and
the CSV goes to tmp_path/statistics/."""
import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "utilities" / "get_corpus_stats.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus"


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


@pytest.fixture
def mini_corpus(tmp_path):
    corpus = tmp_path / "Corpora" / "MiniCorpus"
    shutil.copytree(FIXTURE, corpus)
    return corpus


def _read_rows(tmp_path):
    csv_path = tmp_path / "statistics" / "MiniCorpus_corpora_stats.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {(r["language"], r["dialect"]): r for r in csv.DictReader(f)}


def test_csv_contents(mini_corpus, tmp_path):
    result = _run([str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    rows = _read_rows(tmp_path)

    haian = rows[("ami", "Haian")]
    assert int(haian["word_count"]) == 5
    assert int(haian["sentences"]) == 3
    assert int(haian["segmented_words"]) == 3
    assert int(haian["glossed_words"]) == 3
    assert int(haian["eng_transl_count"]) == 5
    assert int(haian["zho_transl_count"]) == 3
    assert int(haian["file_count"]) == 1

    truku = rows[("trv", "Truku")]
    assert int(truku["word_count"]) == 2
    assert int(truku["transcribed_audio_count"]) == 1
    assert int(truku["untranscribed_audio_count"]) == 1
    # No prior CSV to carry from, and this script never computes durations
    # (that's update_audio_stats.py's job) — seconds are zero.
    assert float(truku["transcribed_audio_seconds"]) == 0.0
    assert float(truku["untranscribed_audio_seconds"]) == 0.0

    assert int(rows[("trv", "unknown")]["word_count"]) == 3
    assert int(rows[("ami", "")]["word_count"]) == 1

    # Parse-error pseudo-row: zero in all Gitbook-displayed fields so
    # update_corpus_stats.py's row_has_data() filters it out.
    err = rows[("", "")]
    assert int(err["parse_errors"]) == 1
    assert int(err["word_count"]) == 0

    # Gitbook contract: every column its update_corpus_stats.py reads exists.
    for col in ("language", "dialect", "word_count", "segmented_words",
                "glossed_words", "eng_transl_count", "zho_transl_count",
                "transcribed_audio_count", "transcribed_audio_seconds",
                "untranscribed_audio_count", "untranscribed_audio_seconds",
                "file_count"):
        assert col in haian


def test_audio_seconds_carried_from_existing_csv(mini_corpus, tmp_path):
    # Seconds columns are a manually-maintained value (update_audio_stats.py);
    # re-running get_corpus_stats must preserve them while recomputing counts.
    stats_dir = tmp_path / "statistics"
    stats_dir.mkdir()
    seed = stats_dir / "MiniCorpus_corpora_stats.csv"
    seed.write_text(
        "language,dialect,segmented_words,glossed_words,"
        "transcribed_audio_count,transcribed_audio_seconds,"
        "untranscribed_audio_count,untranscribed_audio_seconds,"
        "eng_transl_count,zho_transl_count,word_count,file_count\n"
        "trv,Truku,0,0,1,99.0,1,42.0,0,0,2,1\n"
    )
    result = _run([str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    truku = _read_rows(tmp_path)[("trv", "Truku")]
    assert float(truku["transcribed_audio_seconds"]) == pytest.approx(99.0)
    assert float(truku["untranscribed_audio_seconds"]) == pytest.approx(42.0)
    assert int(truku["transcribed_audio_count"]) == 1  # recomputed from XML


def test_strict_fails_on_parse_error(mini_corpus):
    result = _run([str(mini_corpus), "--strict"])
    assert result.returncode == 1
    assert "bad.xml" in result.stderr


def test_warnings_reported_on_stderr(mini_corpus):
    result = _run([str(mini_corpus)])
    assert "missing dialect" in result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/utilities/test_get_corpus_stats.py -v`
Expected: FAIL (old CLI has no `--strict`; old counting gives different numbers; old code computes audio durations instead of carrying)

- [ ] **Step 3: Rewrite the script**

Replace the entire contents of `QC/utilities/get_corpus_stats.py` with:

```python
"""Per-corpus statistics CSVs for FormosanBank (consumed by the Gitbook).

Counting rules live in QC/corpus_counts.py (shared with corpus_metrics.py
and count_tokens.py). Writes statistics/<CorpusName>_corpora_stats.csv.

Audio durations are NOT computed here (CI has no audio files): the
seconds columns are carried forward from the existing CSV and refreshed
only by the manual QC/utilities/update_audio_stats.py. Audio *counts*
are recomputed from XML on every run.

Column names through `file_count` are a published interface: the Gitbook's
update_corpus_stats.py reads them by name. Only append columns, never
rename or remove.
"""
import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import corpus_counts

FIELDNAMES = [
    "language", "dialect", "segmented_words", "glossed_words",
    "transcribed_audio_count", "transcribed_audio_seconds",
    "untranscribed_audio_count", "untranscribed_audio_seconds",
    "eng_transl_count", "zho_transl_count", "word_count", "file_count",
    # Appended 2026-06 (pipeline unification); safe for DictReader consumers.
    "sentences", "word_elements", "morpheme_elements",
    "translation_elements", "audio_elements", "parse_errors",
]

SUM_FIELDS = [f for f in FIELDNAMES if f not in
              ("language", "dialect",
               "transcribed_audio_seconds", "untranscribed_audio_seconds",
               "parse_errors")]


def load_carry_seconds(csv_path: Path) -> dict:
    """Read seconds columns from an existing CSV, keyed (language, dialect).

    Missing CSV is normal for a brand-new corpus: seconds start at 0 and
    get filled in by a manual update_audio_stats.py run."""
    carried = {}
    if not csv_path.is_file():
        return carried
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row.get("language", ""), row.get("dialect", ""))
            carried[key] = (
                float(row.get("transcribed_audio_seconds") or 0),
                float(row.get("untranscribed_audio_seconds") or 0),
            )
    return carried


def stats_paths(corpus_path: Path) -> tuple[Path, str]:
    """Derive (repo_root/statistics dir, corpus name) from the corpus path."""
    parts = corpus_path.resolve().parts
    corpora_idx = next((i for i, p in enumerate(parts) if p == "Corpora"), None)
    if corpora_idx is not None:
        repo_root = Path(*parts[:corpora_idx])
        name = parts[corpora_idx + 1] if corpora_idx + 1 < len(parts) else "unknown"
    else:
        repo_root = corpus_path.resolve()
        name = repo_root.name
    return repo_root / "statistics", name


def process_corpus(corpus_path: Path, strict: bool) -> int:
    """Analyze one corpus directory and write its CSV. Returns exit code."""
    corpus_path = Path(corpus_path)
    xml_dir = corpus_path / "XML" if (corpus_path / "XML").is_dir() else corpus_path
    stats_dir, corpus_name = stats_paths(corpus_path)
    csv_path = stats_dir / f"{corpus_name}_corpora_stats.csv"

    carried = load_carry_seconds(csv_path)

    buckets = defaultdict(lambda: {f: 0 for f in FIELDNAMES if f not in ("language", "dialect")})
    n_warnings = 0
    records, parse_errors = corpus_counts.collect_records(xml_dir)

    for record in records:
        key = (record["language"], record["dialect"])
        bucket = buckets[key]
        for field in SUM_FIELDS:
            bucket[field] += record[field]
        for warning in record["warnings"]:
            n_warnings += 1
            print(f"[get_corpus_stats] WARNING {record['path']}: {warning}", file=sys.stderr)

    for key, (t_sec, u_sec) in carried.items():
        if key in buckets:
            buckets[key]["transcribed_audio_seconds"] = t_sec
            buckets[key]["untranscribed_audio_seconds"] = u_sec

    for item in parse_errors:
        print(f"[get_corpus_stats] PARSE ERROR {item['path']}: {item['error']}", file=sys.stderr)
    if parse_errors:
        buckets[("", "")]["parse_errors"] = len(parse_errors)

    stats_dir.mkdir(exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for (language, dialect), values in sorted(buckets.items()):
            values["transcribed_audio_seconds"] = round(values["transcribed_audio_seconds"], 1)
            values["untranscribed_audio_seconds"] = round(values["untranscribed_audio_seconds"], 1)
            writer.writerow({"language": language, "dialect": dialect, **values})

    print(f"Corpus statistics saved to {csv_path} "
          f"({len(records)} files, {len(parse_errors)} parse errors, {n_warnings} warnings)")
    return 1 if (strict and parse_errors) else 0


def main() -> int:
    default_corpora = Path(__file__).resolve().parents[2] / "Corpora"
    parser = argparse.ArgumentParser(description="Per-corpus statistics CSVs.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("corpora_path", nargs="?",
                       help="Path to a single corpus directory (e.g. Corpora/ePark).")
    group.add_argument("--all", action="store_true",
                       help="Run on every corpus under --corpora_root.")
    parser.add_argument("--corpora_root", default=str(default_corpora),
                        help="Collection root used with --all (default: repo Corpora/).")
    parser.add_argument("--strict", action="store_true",
                        help="Exit nonzero if any XML file fails to parse.")
    args = parser.parse_args()

    if args.all:
        corpora_root = Path(args.corpora_root).resolve()
        corpus_dirs = sorted(d for d in corpora_root.iterdir()
                             if d.is_dir() and (d / "XML").is_dir())
        if not corpus_dirs:
            print(f"No corpus directories with XML/ in {corpora_root}", file=sys.stderr)
            return 1
        worst = 0
        for corpus_dir in corpus_dirs:
            print(f"Processing {corpus_dir.name} …")
            worst = max(worst, process_corpus(corpus_dir, args.strict))
        return worst
    return process_corpus(Path(args.corpora_path), args.strict)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/utilities/test_get_corpus_stats.py tests/utilities/test_corpus_counts.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/get_corpus_stats.py tests/utilities/test_get_corpus_stats.py
git commit -m "refactor(QC): get_corpus_stats on shared counting rules; seconds carried forward; strict errors"
```

---

### Task 5B: `update_audio_stats.py` — manual audio-duration refresh

**Files:**
- Create: `QC/utilities/update_audio_stats.py`
- Create: `tests/utilities/test_update_audio_stats.py`

This is the command Joshua runs by hand when a new corpus lands or audio is re-downloaded. It recomputes ONLY the `transcribed_audio_seconds` / `untranscribed_audio_seconds` columns of an existing per-corpus CSV, in place, from audio files on disk. All other columns are untouched.

- [ ] **Step 1: Write the failing tests**

```python
# tests/utilities/test_update_audio_stats.py
"""update_audio_stats.py rewrites ONLY the audio-seconds columns of an
existing per-corpus CSV, computed from audio files on disk. Run manually;
CI never runs it (no audio on the runner)."""
import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
UPDATE = REPO_ROOT / "QC" / "utilities" / "update_audio_stats.py"
GET_STATS = REPO_ROOT / "QC" / "utilities" / "get_corpus_stats.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus"


def _run(script, args):
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )


@pytest.fixture
def mini_corpus(tmp_path):
    corpus = tmp_path / "Corpora" / "MiniCorpus"
    shutil.copytree(FIXTURE, corpus)
    return corpus


def _read_rows(tmp_path):
    csv_path = tmp_path / "statistics" / "MiniCorpus_corpora_stats.csv"
    with open(csv_path, newline="", encoding="utf-8") as f:
        return {(r["language"], r["dialect"]): r for r in csv.DictReader(f)}


def test_updates_seconds_in_place(mini_corpus, tmp_path, audio_file_factory):
    audio_dir = mini_corpus / "Audio"
    audio_dir.mkdir()
    shutil.copy(audio_file_factory(duration_sec=1.0), audio_dir / "clip.wav")
    shutil.copy(audio_file_factory(duration_sec=2.0), audio_dir / "full.wav")

    # Seed the CSV with get_corpus_stats (seconds start at 0).
    result = _run(GET_STATS, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    before = _read_rows(tmp_path)
    assert float(before[("trv", "Truku")]["transcribed_audio_seconds"]) == 0.0

    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    rows = _read_rows(tmp_path)
    truku = rows[("trv", "Truku")]
    assert float(truku["transcribed_audio_seconds"]) == pytest.approx(1.0, abs=0.1)
    assert float(truku["untranscribed_audio_seconds"]) == pytest.approx(2.0, abs=0.1)
    # Everything else untouched.
    assert int(truku["word_count"]) == 2
    assert int(truku["transcribed_audio_count"]) == 1
    assert rows[("ami", "Haian")] == before[("ami", "Haian")]


def test_missing_csv_is_an_error(mini_corpus):
    # No prior get_corpus_stats run: nothing to update.
    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 1
    assert "get_corpus_stats" in result.stderr  # tells the user what to run first


def test_no_audio_on_disk_warns_and_keeps_seconds(mini_corpus, tmp_path):
    # Audio referenced in XML but not downloaded: keep existing seconds
    # rather than silently zeroing them out.
    result = _run(GET_STATS, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    csv_path = tmp_path / "statistics" / "MiniCorpus_corpora_stats.csv"
    text = csv_path.read_text().replace("trv,Truku,0,0,1,0,1,0", "trv,Truku,0,0,1,55.0,1,66.0")
    csv_path.write_text(text)

    result = _run(UPDATE, [str(mini_corpus)])
    assert result.returncode == 0, result.stderr
    assert "not found on disk" in result.stderr
    truku = _read_rows(tmp_path)[("trv", "Truku")]
    assert float(truku["transcribed_audio_seconds"]) == pytest.approx(55.0)
    assert float(truku["untranscribed_audio_seconds"]) == pytest.approx(66.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/utilities/test_update_audio_stats.py -v`
Expected: FAIL (script does not exist)

- [ ] **Step 3: Write the script**

```python
# QC/utilities/update_audio_stats.py
"""Recompute the audio-seconds columns of statistics/<Corpus>_corpora_stats.csv.

Run MANUALLY on a machine where the corpus audio is downloaded (CI never
runs this — audio is gitignored and absent on runners). get_corpus_stats.py
carries the seconds columns forward on every run; this script is the only
thing that refreshes them. Use it for new corpora and after audio updates:

    python QC/utilities/update_audio_stats.py Corpora/ePark
    python QC/utilities/update_audio_stats.py --all

If no audio file is found for a (language, dialect) bucket that previously
had nonzero seconds, the old value is KEPT and a warning is printed —
running this without audio downloaded must not wipe good data.
"""
import argparse
import csv
import sys
import wave
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import corpus_counts
from get_corpus_stats import FIELDNAMES, stats_paths

try:
    from mutagen.mp3 import MP3 as MutagenMP3
except ImportError:
    MutagenMP3 = None


def _get_audio_duration(file_path: str):
    """Return duration in seconds for an mp3 or wav file, or None on failure."""
    try:
        if file_path.endswith(".mp3"):
            if MutagenMP3 is None:
                return None
            return MutagenMP3(file_path).info.length
        if file_path.endswith(".wav"):
            with wave.open(file_path, "rb") as wf:
                return wf.getnframes() / wf.getframerate()
    except Exception:
        return None
    return None


def _resolve_audio_path(elem, xml_file: Path, corpus_root: Path | None, audio_base: Path):
    """Find the audio file for one AUDIO element, trying mirrored layouts."""
    audio_filename = elem.attrib["file"]
    audio_path_obj = Path(audio_filename)
    alt_ext = ".wav" if audio_path_obj.suffix.lower() == ".mp3" else ".mp3"
    alt_filename = audio_path_obj.stem + alt_ext

    if corpus_root is not None:
        rel = xml_file.relative_to(corpus_root / "XML")
        rel_parts = rel.parent.parts
        rel_variants = [Path(*rel_parts[i:]) for i in range(len(rel_parts))] + [Path(".")]
        candidates = []
        for rel_var in rel_variants:
            for name in (audio_filename, alt_filename):
                candidates += [
                    audio_base / rel_var / name,
                    audio_base / rel_var / xml_file.stem / name,
                ]
        candidates += [audio_base / audio_filename, audio_base / alt_filename]
    else:
        candidates = [audio_base / audio_filename, audio_base / alt_filename]
    return next((c for c in candidates if c.is_file()), None)


def compute_seconds_by_bucket(xml_dir: Path) -> tuple[dict, int, int]:
    """Sum (transcribed, untranscribed) seconds per (language, dialect).

    Returns (buckets, n_elements, n_missing_files)."""
    buckets = defaultdict(lambda: [0.0, 0.0])
    n_elements = 0
    n_missing = 0
    for xml_file in sorted(Path(xml_dir).rglob("*.xml")):
        try:
            root = ET.parse(xml_file).getroot()
        except Exception:
            continue  # parse errors are get_corpus_stats --strict's job
        key = (
            (root.get(corpus_counts.XML_LANG) or "").strip().lower(),
            (root.get("dialect") or "").strip(),
        )
        xml_file = xml_file.resolve()
        parts = xml_file.parts
        try:
            xml_idx = next(i for i in reversed(range(len(parts))) if parts[i] == "XML")
            corpus_root = Path(*parts[:xml_idx])
            audio_base = corpus_root / "Audio"
        except StopIteration:
            corpus_root, audio_base = None, xml_file.parent

        transcribed, untranscribed = corpus_counts.split_audio_elements(root)
        for slot, elems in ((0, transcribed), (1, untranscribed)):
            for elem in elems:
                n_elements += 1
                path = _resolve_audio_path(elem, xml_file, corpus_root, audio_base)
                if path is None:
                    n_missing += 1
                    continue
                duration = _get_audio_duration(str(path))
                if duration is not None:
                    buckets[key][slot] += duration
    return buckets, n_elements, n_missing


def update_corpus(corpus_path: Path) -> int:
    corpus_path = Path(corpus_path)
    xml_dir = corpus_path / "XML" if (corpus_path / "XML").is_dir() else corpus_path
    stats_dir, corpus_name = stats_paths(corpus_path)
    csv_path = stats_dir / f"{corpus_name}_corpora_stats.csv"
    if not csv_path.is_file():
        print(f"[update_audio_stats] ERROR: {csv_path} does not exist. "
              f"Run get_corpus_stats.py on this corpus first.", file=sys.stderr)
        return 1

    seconds, n_elements, n_missing = compute_seconds_by_bucket(xml_dir)
    if n_missing:
        print(f"[update_audio_stats] WARNING: {n_missing}/{n_elements} AUDIO "
              f"elements reference files not found on disk; buckets with no "
              f"located audio keep their previous seconds.", file=sys.stderr)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or FIELDNAMES

    n_updated = 0
    for row in rows:
        key = (row.get("language", ""), row.get("dialect", ""))
        t_sec, u_sec = seconds.get(key, (0.0, 0.0))
        # Keep old values when we found nothing (e.g. audio not downloaded
        # for this bucket) — never silently zero out good data.
        if t_sec or u_sec:
            row["transcribed_audio_seconds"] = round(t_sec, 1)
            row["untranscribed_audio_seconds"] = round(u_sec, 1)
            n_updated += 1

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Updated audio seconds for {n_updated} row(s) in {csv_path}")
    return 0


def main() -> int:
    default_corpora = Path(__file__).resolve().parents[2] / "Corpora"
    parser = argparse.ArgumentParser(
        description="Recompute audio-seconds columns of per-corpus stats CSVs "
                    "from local audio files (manual; not run in CI).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("corpora_path", nargs="?",
                       help="Path to a single corpus directory (e.g. Corpora/ePark).")
    group.add_argument("--all", action="store_true",
                       help="Run on every corpus under --corpora_root.")
    parser.add_argument("--corpora_root", default=str(default_corpora))
    args = parser.parse_args()

    if args.all:
        corpora_root = Path(args.corpora_root).resolve()
        corpus_dirs = sorted(d for d in corpora_root.iterdir()
                             if d.is_dir() and (d / "XML").is_dir())
        worst = 0
        for corpus_dir in corpus_dirs:
            print(f"Processing {corpus_dir.name} …")
            worst = max(worst, update_corpus(corpus_dir))
        return worst
    return update_corpus(Path(args.corpora_path))


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the tests**

Run: `pytest tests/utilities/test_update_audio_stats.py tests/utilities/test_get_corpus_stats.py -v`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add QC/utilities/update_audio_stats.py tests/utilities/test_update_audio_stats.py
git commit -m "feat(QC): manual update_audio_stats command for audio-seconds refresh"
```

---

### Task 6: `count_tokens.py` on the shared module

**Files:**
- Rewrite: `QC/count_tokens.py`
- Create: `tests/utilities/test_count_tokens.py`

The JSON output shape `{LanguageName: [total, {dialect: tokens}]}` is consumed by `tokens_delta.py`, `plot_counts.py`, `plot_deltas.py`, and the token-comparison workflow summary — it must not change.

- [ ] **Step 1: Write the failing test**

```python
# tests/utilities/test_count_tokens.py
"""count_tokens.py emits {LanguageName: [total, {dialect: tokens}]} JSON.
Shape is consumed by tokens_delta.py / plot_counts.py / plot_deltas.py
and the token-comparison workflow — keep it stable."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "count_tokens.py"
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "stats_corpus" / "MiniCorpus"


def test_json_shape_and_language_resolution(tmp_path):
    shutil.copytree(FIXTURE, tmp_path / "Corpora" / "MiniCorpus")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "Corpora")],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)

    assert data["Amis"][0] == 6
    assert data["Amis"][1] == {"Haian": 5, "Not Specified": 1}
    assert data["Truku"] == [2, {"Truku": 2}]
    assert data["Seediq"] == [3, {"unknown": 3}]
    # Every known language is present (zero-seeded), so deltas across
    # checkouts never KeyError.
    assert data["Bunun"] == [0, {}]
    assert len(data) >= 17
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/utilities/test_count_tokens.py -v`
Expected: FAIL (old code path-derives language; tokens computed with old rules)

- [ ] **Step 3: Rewrite the script**

Replace the entire contents of `QC/count_tokens.py` with:

```python
"""Token counts per language/dialect as JSON, for the token-comparison CI.

Computes from XML via QC/corpus_counts.py (NOT from statistics/*.csv —
this script runs on arbitrary checkouts, e.g. a PR base in a worktree,
where the committed CSVs may be stale or absent).

Output shape (stable interface for tokens_delta.py / plot_counts.py /
plot_deltas.py): {LanguageName: [total_tokens, {dialect: tokens}]}.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import corpus_counts


def get_counts(corpora_path):
    records, _parse_errors = corpus_counts.collect_records(Path(corpora_path))

    tokens_by_lang = {name: [0, {}] for name in corpus_counts.LANGUAGE_NAMES}
    tokens_by_source = defaultdict(int)

    corpora_path = Path(corpora_path).resolve()
    for record in records:
        language = corpus_counts.resolve_language(record["language"], record["dialect"])
        if language is None:
            code = record["language"]
            language = f"Unknown ({code})" if code else "Unknown"
        dialect = record["dialect"] or "Not Specified"
        entry = tokens_by_lang.setdefault(language, [0, {}])
        entry[0] += record["word_count"]
        entry[1][dialect] = entry[1].get(dialect, 0) + record["word_count"]

        try:
            source = Path(record["path"]).resolve().relative_to(corpora_path).parts[0]
        except (ValueError, IndexError):
            source = "Unknown"
        tokens_by_source[source] += record["word_count"]

    return tokens_by_lang, dict(tokens_by_source)


def main(corpora_path):
    tokens_by_lang, _tokens_by_source = get_counts(corpora_path)
    print(json.dumps(tokens_by_lang, indent=4, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Count tokens per language and dialect.")
    parser.add_argument("corpora_path", help="Path of the corpora collection root")
    args = parser.parse_args()
    main(args.corpora_path)
```

(The `--form-kind` flag is removed; the counting rule is now fixed. `import corpus_counts` works because Python adds the script's directory, `QC/`, to `sys.path`.)

- [ ] **Step 4: Run the test**

Run: `pytest tests/utilities/test_count_tokens.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add QC/count_tokens.py tests/utilities/test_count_tokens.py
git commit -m "refactor(QC): count_tokens on shared rules; drop form-kind; resolve Truku/Seediq by dialect"
```

---

### Task 7: `corpus_metrics.py` part A — shared counting, no form-kind

**Files:**
- Modify: `QC/corpus_metrics.py`

- [ ] **Step 1: Replace the counting internals**

In `QC/corpus_metrics.py`:

1. Add `import corpus_counts` after the stdlib imports.
2. **Delete** these definitions entirely: `LANG_CODE_TO_NAME`, `KNOWN_LANGUAGES`, `word_count()`, `select_sentence_form()`, `language_from_path()`, `language_for()`, `dialect_for()`.
3. **Replace** `analyze_xml_root` with:

```python
def display_language(language_code: str, dialect: str) -> str:
    resolved = corpus_counts.resolve_language(language_code, dialect)
    if resolved:
        return resolved
    return f"Unknown ({language_code})" if language_code else "Unknown"


def analyze_xml_root(corpora_path: Path, xml_file: Path, root: ET.Element) -> dict[str, Any]:
    record = corpus_counts.analyze_root(root)
    return {
        "source": source_for(corpora_path, xml_file),
        "language": display_language(record["language"], record["dialect"]),
        "language_code": record["language"] or None,
        "dialect": record["dialect"] or "Not Specified",
        "path": str(xml_file.relative_to(corpora_path.parent)),
        "tokens": record["word_count"],
        "sentences": record["sentences"],
        "xml_files": 1,
        "word_elements": record["word_elements"],
        "morpheme_elements": record["morpheme_elements"],
        "translation_elements": record["translation_elements"],
        "audio_elements": record["audio_elements"],
    }
```

4. Remove the `form_kind` parameter from every signature and call site: `analyze_xml_file`, `analyze_xml_bytes`, `collect_corpus_records`, `analyze_corpora`, `build_metrics`, `restore_xml_blob`, `roll_back_xml_commit`, `generate_history_from_cache`, `generate_history`. In `build_metrics`, replace the `"form_kind": form_kind` JSON key with `"counting": "standard tier (original fallback); tokens are whitespace chunks containing a letter or digit"`. In `write_markdown`, replace the `Token source:` line with `f"Token source: sentence-level FORM, standard tier with original fallback."`.
5. In `parse_args`, delete the `--form-kind` argument.

- [ ] **Step 2: Smoke-run on the fixture corpus**

Run: `python QC/corpus_metrics.py tests/fixtures/stats_corpus --output-dir /tmp/cm_smoke --no-plots`
Expected output line: `Totals: 11 tokens, 6 sentences, 4 XML files` (and 1 parse error reported on stderr; `Truku`, `Seediq`, and `Amis` appear as separate languages in /tmp/cm_smoke/corpus_metrics.json with 2, 3, and 6 tokens)

- [ ] **Step 3: Run the whole suite**

Run: `pytest`
Expected: all pass (count_tokens no longer imports the deleted `KNOWN_LANGUAGES`)

- [ ] **Step 4: Commit**

```bash
git add QC/corpus_metrics.py
git commit -m "refactor(QC): corpus_metrics counts via corpus_counts; remove form-kind and path-based language"
```

---

### Task 8: `corpus_metrics.py` part B — snapshot from CSVs, history append

**Files:**
- Modify: `QC/corpus_metrics.py`
- Create: `tests/utilities/test_corpus_metrics.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/utilities/test_corpus_metrics.py
"""corpus_metrics.py --stats-dir: aggregate per-corpus CSVs (the inverted
pipeline) and append one history row per run at HEAD."""
import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "QC" / "corpus_metrics.py"

CSV_HEADER = (
    "language,dialect,segmented_words,glossed_words,"
    "transcribed_audio_count,transcribed_audio_seconds,"
    "untranscribed_audio_count,untranscribed_audio_seconds,"
    "eng_transl_count,zho_transl_count,word_count,file_count,"
    "sentences,word_elements,morpheme_elements,translation_elements,"
    "audio_elements,parse_errors\n"
)


def _write_stats(stats_dir: Path):
    stats_dir.mkdir()
    (stats_dir / "MiniCorpus_corpora_stats.csv").write_text(
        CSV_HEADER
        + ",,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1\n"
        + "ami,,0,0,0,0,0,0,0,0,1,1,1,0,0,0,0,0\n"
        + "ami,Haian,3,3,0,0,0,0,5,3,5,1,3,3,1,5,0,0\n"
        + "trv,Truku,0,0,1,1.0,1,2.0,0,0,2,1,1,0,0,0,2,0\n"
        + "trv,unknown,0,0,0,0,0,0,0,0,3,1,1,0,0,0,0,0\n"
    )
    (stats_dir / "OtherCorpus_corpora_stats.csv").write_text(
        CSV_HEADER + "pwn,Paridrayan,0,0,0,0,0,0,0,0,10,2,4,0,0,0,0,0\n"
    )


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def test_snapshot_from_stats_dir(tmp_path):
    _write_stats(tmp_path / "statistics")
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots"])
    assert result.returncode == 0, result.stderr
    metrics = json.loads((tmp_path / "out" / "corpus_metrics.json").read_text())

    assert metrics["totals"]["tokens"] == 21        # 11 + 10
    assert metrics["totals"]["sentences"] == 10     # 6 + 4
    assert metrics["totals"]["xml_files"] == 6      # file_count sums
    assert metrics["totals"]["sources"] == 2
    assert metrics["totals"]["parse_errors"] == 1
    assert metrics["by_language"]["Amis"]["tokens"] == 6
    assert metrics["by_language"]["Truku"]["tokens"] == 2
    assert metrics["by_language"]["Seediq"]["tokens"] == 3
    assert metrics["by_source"]["MiniCorpus"]["tokens"] == 11


def test_history_appends_one_row_at_head(tmp_path):
    _write_stats(tmp_path / "statistics")
    cache = tmp_path / "cache.csv"
    cache.write_text(
        "date,commit,tokens,sentences,xml_files,sources,languages,parse_errors\n"
        "2025-01-01T00:00:00+00:00,0000000000000000000000000000000000000000,100,10,5,1,1,0\n"
    )
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots",
                   "--history", "--history-cache", str(cache)])
    assert result.returncode == 0, result.stderr

    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                          text=True, cwd=REPO_ROOT).stdout.strip()
    with open(tmp_path / "out" / "corpus_size_history.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2                      # cached row kept + HEAD appended
    assert rows[0]["tokens"] == "100"
    assert rows[1]["commit"] == head
    assert rows[1]["tokens"] == "21"

    # Re-running on the same HEAD must replace, not duplicate.
    cache2 = tmp_path / "out" / "corpus_size_history.csv"
    result = _run(["Corpora", "--stats-dir", str(tmp_path / "statistics"),
                   "--output-dir", str(tmp_path / "out"), "--no-plots",
                   "--history", "--history-cache", str(cache2)])
    assert result.returncode == 0, result.stderr
    with open(tmp_path / "out" / "corpus_size_history.csv", newline="") as f:
        assert len(list(csv.DictReader(f))) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/utilities/test_corpus_metrics.py -v`
Expected: FAIL (`--stats-dir` is not a recognized argument)

- [ ] **Step 3: Implement in `QC/corpus_metrics.py`**

Add after `collect_corpus_records`:

```python
STATS_SUFFIX = "_corpora_stats.csv"


def read_stats_dir(stats_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Build per-(corpus, language, dialect) records from the per-corpus CSVs
    written by QC/utilities/get_corpus_stats.py (the inverted pipeline:
    that script counts, this one aggregates)."""
    records: list[dict[str, Any]] = []
    parse_errors: list[dict[str, str]] = []
    csv_paths = sorted(Path(stats_dir).glob(f"*{STATS_SUFFIX}"))
    if not csv_paths:
        raise FileNotFoundError(f"No *{STATS_SUFFIX} files found in {stats_dir}")

    for csv_path in csv_paths:
        source = csv_path.name[: -len(STATS_SUFFIX)]
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):

                def as_int(field: str) -> int:
                    return int(float(row.get(field) or 0))

                if not (row.get("language") or "").strip() and as_int("parse_errors"):
                    parse_errors.extend(
                        {"path": f"{source} (file unknown; see get_corpus_stats log)",
                         "error": "XML parse error"}
                        for _ in range(as_int("parse_errors"))
                    )
                    continue
                language_code = (row.get("language") or "").strip()
                dialect = (row.get("dialect") or "").strip()
                records.append({
                    "source": source,
                    "language": display_language(language_code, dialect),
                    "language_code": language_code or None,
                    "dialect": dialect or "Not Specified",
                    "path": f"{source}:{language_code or 'unknown'}:{dialect or 'unknown'}",
                    "tokens": as_int("word_count"),
                    "sentences": as_int("sentences"),
                    "xml_files": as_int("file_count"),
                    "word_elements": as_int("word_elements"),
                    "morpheme_elements": as_int("morpheme_elements"),
                    "translation_elements": as_int("translation_elements"),
                    "audio_elements": as_int("audio_elements"),
                })
    return records, parse_errors
```

Add after `load_history_csv`:

```python
def append_history_row(repo_root: Path, cache_path: Path, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    """One history row per run, at HEAD, from the current snapshot totals.
    Re-running on the same commit replaces the row instead of duplicating."""
    rows = load_history_csv(cache_path)
    head = metrics["git"].get("commit") or git_value(["rev-parse", "HEAD"], repo_root) or ""
    row = {
        "commit": head,
        "date": commit_date(repo_root, head),
        "tokens": metrics["totals"]["tokens"],
        "sentences": metrics["totals"]["sentences"],
        "xml_files": metrics["totals"]["xml_files"],
        "sources": metrics["totals"]["sources"],
        "languages": metrics["totals"]["languages"],
        "parse_errors": metrics["totals"]["parse_errors"],
    }
    if rows and rows[-1].get("commit") == head:
        rows[-1] = row
    else:
        rows.append(row)
    return rows
```

In `parse_args`, add (and change `--history`'s help text accordingly):

```python
    parser.add_argument(
        "--stats-dir",
        default=None,
        help="Aggregate per-corpus CSVs from this directory (written by "
             "QC/utilities/get_corpus_stats.py) instead of parsing XML.",
    )
    parser.add_argument(
        "--history-rebuild",
        action="store_true",
        help="Rebuild the full size-over-time CSV from git history (slow; "
             "restates all rows under the current counting rules).",
    )
```

In `main`, replace the record collection and history block:

```python
    if args.stats_dir:
        progress(f"Aggregating per-corpus CSVs from {args.stats_dir}.")
        current_records, current_parse_errors = read_stats_dir(Path(args.stats_dir))
    else:
        progress(f"Counting current corpus XML from {corpora_path}.")
        current_records, current_parse_errors = collect_corpus_records(corpora_path)
    metrics = build_metrics(corpora_path.resolve(), current_records, current_parse_errors)
    ...
    if args.history_rebuild:
        if args.stats_dir:
            print("--history-rebuild requires XML mode (omit --stats-dir).", file=sys.stderr)
            return 2
        repo_root = repo_root_from(corpora_path.resolve())
        history_rows = generate_history(
            repo_root, args.max_history_commits, metrics,
            current_records=current_records,
            current_parse_errors=current_parse_errors,
            cache_path=None,
        )
        write_history_csv(history_rows, output_dir)
        if not args.no_plots:
            plot_history(history_rows, output_dir)
    elif args.history:
        repo_root = repo_root_from(corpora_path.resolve())
        cache = Path(args.history_cache) if args.history_cache else output_dir / "corpus_size_history.csv"
        history_rows = append_history_row(repo_root, cache, metrics)
        write_history_csv(history_rows, output_dir)
        if not args.no_plots:
            plot_history(history_rows, output_dir)
```

Delete `generate_history_from_cache` and the `cache_path` branch inside `generate_history` (the blob-walk full rebuild remains; per-commit incremental cache updating is superseded by `append_history_row`). Note for the implementer: records from `read_stats_dir` are per-(corpus, language, dialect), not per-file, but `aggregate_records` only sums `COUNT_FIELDS` and counts distinct sources/languages/dialects, so it works unchanged on both shapes.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/utilities/test_corpus_metrics.py -v` then `pytest`
Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add QC/corpus_metrics.py tests/utilities/test_corpus_metrics.py
git commit -m "feat(QC): corpus_metrics aggregates get_corpus_stats CSVs; history appends at HEAD"
```

---

### Task 9: Workflow updates

**Files:**
- Modify: `.github/workflows/corpus-metrics.yaml`
- Modify: `.github/workflows/token-comparison.yaml`

- [ ] **Step 1: Rewrite the generate/commit steps of `corpus-metrics.yaml`**

Replace the `Generate corpus metrics` step (lines 41–47) with:

```yaml
      - name: Generate per-corpus statistics CSVs
        run: |
          python3 QC/utilities/get_corpus_stats.py --all --strict

      - name: Generate corpus metrics
        run: |
          python3 QC/corpus_metrics.py Corpora \
            --stats-dir statistics \
            --output-dir corpus-metrics \
            --history \
            --history-cache statistics/corpus_size_history.csv
```

(The runner has no audio files; `get_corpus_stats.py` always carries the seconds columns forward from the committed CSVs, which are refreshed only by manual `update_audio_stats.py` runs. `--max-history-commits` is dropped along with the per-commit incremental mode.)

Replace the `Update README growth graph` step (lines 52–68) with:

```yaml
      - name: Commit updated statistics
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          mkdir -p statistics
          cp corpus-metrics/corpus_size_history.csv statistics/corpus_size_history.csv
          cp corpus-metrics/corpus_size_over_time.png statistics/corpus_size_over_time.png

          git add statistics/corpus_size_history.csv statistics/corpus_size_over_time.png statistics/*_corpora_stats.csv
          if git diff --cached --quiet; then
            echo "No statistics changes."
            exit 0
          fi

          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git commit -m "Update corpus statistics and growth graph"
          git push
```

In the `paths:` filters (both `push` and `pull_request`), add:

```yaml
      - "QC/corpus_counts.py"
      - "QC/utilities/get_corpus_stats.py"
```

- [ ] **Step 2: Add `QC/corpus_counts.py` to `token-comparison.yaml` paths**

In both `pull_request.paths` and `push.paths`, replace the `- "QC/corpus_metrics.py"` line with:

```yaml
      - "QC/corpus_metrics.py"
      - "QC/corpus_counts.py"
```

- [ ] **Step 3: Validate YAML**

Run: `python -c "import yaml; yaml.safe_load(open('.github/workflows/corpus-metrics.yaml')); yaml.safe_load(open('.github/workflows/token-comparison.yaml')); print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/corpus-metrics.yaml .github/workflows/token-comparison.yaml
git commit -m "ci: corpus-metrics runs get_corpus_stats then aggregates; commit per-corpus CSVs"
```

---

### Task 10: Documentation

**Files:**
- Modify: `QC/README.md` (the corpus metrics / token counting sections)
- Modify: `CLAUDE.md` (the "Corpus metrics and token deltas (CI-coupled)" section)
- Modify: `Corpora/README.md` only if it references token counting (check with `grep -n "token" Corpora/README.md`; skip if no hits)

- [ ] **Step 1: Update `CLAUDE.md`**

Replace the "Corpus metrics and token deltas (CI-coupled)" section body with:

```markdown
[QC/corpus_counts.py](QC/corpus_counts.py) is the single source of truth for counting rules (used by `get_corpus_stats.py`, `corpus_metrics.py`, and `count_tokens.py`): tokens come from sentence-level `FORM` only (standard tier, original fallback) and are whitespace chunks containing at least one letter or digit; language identity comes from `xml:lang` + `dialect` (`trv` + dialect `Truku` → Truku, otherwise Seediq). These scripts feed two GitHub Actions:

- **[.github/workflows/corpus-metrics.yaml](.github/workflows/corpus-metrics.yaml)** runs on push to `main`: `QC/utilities/get_corpus_stats.py --all` regenerates `statistics/*_corpora_stats.csv` (the per-corpus CSVs the Gitbook consumes), then [QC/corpus_metrics.py](QC/corpus_metrics.py) `--stats-dir statistics` aggregates them and appends one row at HEAD to [statistics/corpus_size_history.csv](statistics/corpus_size_history.csv). The workflow auto-commits the CSVs, the history CSV, and the growth PNG — **do not hand-edit any of them**. Audio *seconds* columns are never computed by `get_corpus_stats.py` (CI has no audio); they carry forward from the committed CSVs and are refreshed only by running [QC/utilities/update_audio_stats.py](QC/utilities/update_audio_stats.py) manually on a machine with the corpus audio downloaded (do this for new corpora or audio updates).
- **[.github/workflows/token-comparison.yaml](.github/workflows/token-comparison.yaml)** runs on PRs and pushes, comparing [QC/count_tokens.py](QC/count_tokens.py) output (computed from XML, since checkouts may have stale CSVs) against the PR base or previous push.

`QC/corpus_metrics.py --history-rebuild` (XML mode, no `--stats-dir`) restates the entire history CSV from git blobs under the current rules — a full first-parent walk that takes a long time. History rows written before 2026-06 used different counting rules (first FORM, all whitespace chunks); the discontinuity is accepted.
```

- [ ] **Step 2: Update `QC/README.md`**

Find the sections describing `corpus_metrics.py`, `count_tokens.py`, and `get_corpus_stats.py` (`grep -n "corpus_metrics\|count_tokens\|get_corpus_stats" QC/README.md`) and rewrite them to describe: the shared `corpus_counts.py` rules module, the inverted flow (get_corpus_stats counts → CSVs in `statistics/` → corpus_metrics aggregates), the manual `update_audio_stats.py` audio-seconds refresh, `--strict`, and `--history-rebuild`. Keep the existing document structure; this is a content update, not a reorganization.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md QC/README.md
git commit -m "docs: describe unified statistics pipeline"
```

---

### Task 11: Full local verification run

**Files:**
- Modify (regenerate): `statistics/*_corpora_stats.csv`

- [ ] **Step 1: Run the whole test suite**

Run: `pytest`
Expected: all pass. Quote the summary line in the report.

- [ ] **Step 2: Regenerate all per-corpus CSVs locally**

First remove any stale CSVs left by pre-rewrite runs so carried seconds start clean: `rm statistics/*_corpora_stats.csv` (they are untracked or about to be regenerated; verify with `git status statistics/` first).

Run: `python QC/utilities/get_corpus_stats.py --all --strict 2> /tmp/get_corpus_stats_warnings.log`
Expected: exit 0, 20 CSVs written with seconds columns all 0. Then inspect: `wc -l /tmp/get_corpus_stats_warnings.log` and `grep -c "missing dialect" /tmp/get_corpus_stats_warnings.log` — report the warning counts (per Design decision 5 there WILL be missing-dialect warnings until Joshua's XML fixes land; expected, not a failure).

- [ ] **Step 2b: Fill audio seconds from local audio (102k files are on disk)**

Run: `python QC/utilities/update_audio_stats.py --all 2> /tmp/update_audio_warnings.log`
Expected: exit 0. Report how many corpora got nonzero seconds and quote the missing-file warning counts from the log (corpora whose audio isn't downloaded locally will warn and keep zeros — list which ones).

- [ ] **Step 3: Run the aggregator from the CSVs and from XML, and compare**

Run: `python QC/corpus_metrics.py Corpora --stats-dir statistics --output-dir /tmp/cm_from_csv --no-plots`
Run: `python QC/corpus_metrics.py Corpora --output-dir /tmp/cm_from_xml --no-plots`
Expected: the `Totals:` lines of both runs report **identical** token, sentence, and XML-file counts (the CSV path and the XML path must agree — this is the consistency check that motivated the whole merge). Record the new total and compare against the old baselines (old tracker 8,058,955; old gitbook 7,954,580); the new number should land between roughly 7.9M and 8.1M. Investigate before committing if it doesn't.

- [ ] **Step 4: Sanity-check one corpus CSV by hand**

Read `statistics/ePark_corpora_stats.csv` and verify: language codes not names in the `language` column, seconds columns non-zero where audio exists locally, new columns present. Quote 2–3 rows in the report.

- [ ] **Step 5: Commit the regenerated CSVs**

```bash
git add statistics/*_corpora_stats.csv
git commit -m "stats: seed per-corpus CSVs under unified counting rules"
```

(These seeds matter: the first CI run uses `--audio-seconds carry`, which reads the seconds columns from exactly these committed files.)

---

## Self-review checklist (run after drafting, before handoff)

- Spec coverage: rule 1 (digits yes, punct no) → Tasks 1, 11; rule 2 (standard→original) → Task 2; rule 3 (language/dialect identity) → Tasks 3, 6, 7; rule 4 (error handling) → Tasks 4, 5 (`--strict`, warnings), 5B (missing-audio warnings, never zero out good seconds), 8 (parse-error rows propagate); rule 5 (discontinuity accepted) → Design decision 8, Task 10 docs; audio as a separate manual command (Joshua, 2026-06-10) → Design decision 7, Task 5B; inverted architecture → Tasks 5, 8, 9; tests for current correctness and regression → Tasks 1–8 (unit + golden fixtures), Task 11 (whole-corpus consistency check).
- Known risk: `corpus-metrics.yaml` `--strict` will fail CI if a malformed XML lands on main. That's intended (rule 4) but is a behavior change worth flagging in the PR description.
- Known risk: first post-merge CI run rewrites all 20 CSVs and appends a discontinuous history row. Expected; flag in the PR description.
