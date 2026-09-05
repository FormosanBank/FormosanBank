# ILRDF_Dicts v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the ILRDF_Dicts corpus PR on source-stable sentence ids, restore its rights declaration, publish per-language headword dictionaries, split reproduction into re-scrape vs rebuild, and move every source-fidelity repair out of a post-hoc standard-tier patcher into `manual_edits.xml`.

**Architecture:** Two shell entry points. `refresh_source.sh` re-scrapes ILRDF into committed snapshots and is *not* part of reproduction. `make_xml.sh` builds `XML/` from those snapshots and is the whole reproduction path. `generate_xml.py` emits only source-owned tiers (original `FORM`, `TRANSL`, `AUDIO`) and never writes a standard tier or a `PHON` — those come from `standardize.py` and `add_phonology.py` alone. Sentence ids derive from the source's own GUIDs rather than from a hash of the text, which makes ids survive corrections and re-enables `manual_edits.xml` for this corpus.

**Tech Stack:** Python 3.13 (repo `.venv`), lxml, stdlib `ElementTree` for generation, pytest. Shell: bash.

**Spec:** This document. Maintainer requirements captured 2026-09-05; the numbered items in "Requirements" are the maintainer's own words condensed, and the "Findings" section records what was verified against the data before planning.

**Base:** `work/ilrdf-dicts-v2`, branched from `963d1579e` (PR #179 head). Worktree at `/workspace/ilrdf-v2`.

## Global Constraints

- Corpus dev normally happens in a dev repo, but ILRDF_Dicts is already published in `Corpora/`; this is a maintenance rework of a published corpus, so it stays here.
- `Orthographies/`, `QC/`, and every other shared tool are **read-only** in this plan. If a shared tool needs changing, stop and raise it — do not couple a repo-wide change to a corpus PR.
- Pinned authority commit for reproduction stays a real commit hash, updated once at the end (Task 12).
- Every standard-tier value must be produced by `QC/utilities/standardize.py`. No other script may write, edit, or whitespace-normalize `FORM[@kindOf="standard"]` or `PHON`.
- Sentence and entry ids must be stable across text corrections. No content hashing.
- `xml:lang` per language from [languages.csv](../../../languages.csv); `trv` + `dialect="Truku"` → Truku, otherwise Seediq.
- Run tests from the worktree root: `source .venv/bin/activate && python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests -q`.
- Commit after every task. Do not push until the maintainer reviews.

---

## Findings that shaped this plan

Verified against the 16 committed snapshots and the committed XML before writing.

| Question | Answer |
|---|---|
| Are the source GUIDs safe as ids? | Yes. 211,595 sentence items, **0** missing an id, 210,502 distinct GUIDs, **0** GUIDs carrying more than one distinct text/translation/audio set, **0** GUIDs appearing in more than one language. Word GUIDs (144,029) and explanation GUIDs (169,859) are equally clean. |
| What is `=`? | **Not** a null marker. It occurs 4 times, all Thao, as the source's "same as" notation joining equivalent phrasings — `ata tu kmaanasapunuqi! = ata tu kmasapunuqi!` and one inline `(= katzangqaw)`. `standardization.tsv` deletes it, producing a run-on two-sentence standard tier. |
| Is C012 being followed? | Yes, by correctly doing nothing. `_apply_standard_hyphens` returns early unless the sentence has an `<M>` tier (`QC/utilities/standardize.py:170`). ILRDF has no W/M, so C012 is a structural no-op. Its 3,882 standard-tier hyphens are proper names (`Tai-uan`, `Cung-yang-san-may`), Bunun/Thao orthographic letters, and loans — not segmentation. Verified end-to-end on a scratch corpus. |
| Does the apostrophe rule in `standardization.tsv` matter? | It is the single most load-bearing line in the PR. The original tier holds 99,821 `ʼ` (U+02BC) and 97 ASCII `'`; the standard tier holds 0 and 99,918. The row performs the corpus's entire glottal-letter canonicalization. |
| Why doesn't `clean_xml` already do that? | It has the identical mapping (`clean_xml.py:450`) but (a) it no longer touches the standard tier (`clean_xml.py:696`) and (b) `generate_xml.py restore-source` reverts the original tier to raw source, discarding clean_xml's work. |
| Does the committed XML match its own `reproduce.sh`? | Partly. C012's no-op explains the hyphens, but this must be re-verified from scratch in Task 12 rather than assumed. |

## Maintainer decisions taken 2026-09-05

1. **Dedup:** dedup by text; id = lowest GUID in the merged group.
2. **Dictionary location:** inside `Corpora/ILRDF_Dicts/XML/<Language>/`, accepting that published sentence counts roughly double (~167k → ~312k) and the growth graph steps.
3. **Headword audio:** deferred to a follow-up PR.

---

## File Structure

**Corpora/ILRDF_Dicts/CodeAndDocs/**

| File | Responsibility | Status |
|---|---|---|
| `ilrdf_source.py` | Snapshot loading, verification, source normalization, sentence + entry extraction, id derivation | Modify |
| `generate_xml.py` | Build source-tier-only XML for sentences; `audit` mode | Modify |
| `generate_dictionary.py` | Build source-tier-only XML for headword entries | **Create** |
| `refresh_source.py` | Re-scrape ILRDF into snapshots (unchanged behaviour) | Keep |
| `refresh_source.sh` | Full-regeneration entry point: re-scrape only | **Create** |
| `make_xml.sh` | Reproduction entry point: snapshots → XML | **Create** (replaces `reproduce.sh`) |
| `reproduce.sh` | — | **Delete** |
| `source_data/standardization.tsv` | — | **Delete** |
| `source_data/source_repairs.json` | The 13 attestation-supported repairs + the 4 `=` decisions, as reviewed source-repair records | **Create** |
| `manual_edits.xml` | Generated by `capture_manual_edits.py` from `source_repairs.json` application | **Create** (generated) |
| `manual_edits.md` | Generated changelog | **Create** (generated) |
| `docs/qc_report.md` | Updated QC report | Modify |
| `docs/id_scheme.md` | Why GUID ids, what stability they guarantee, how dedup picks the canonical | **Create** |
| `tests/test_ilrdf_source.py` | Extraction + id tests | Modify |
| `tests/test_ids.py` | Id uniqueness, stability, dedup | **Create** |
| `tests/test_dictionary.py` | Dictionary generation | **Create** |
| `tests/test_refresh_source.py` | Unchanged | Keep |

**Corpora/ILRDF_Dicts/**

| File | Responsibility |
|---|---|
| `README.md` | Rewrite: rights, two-script pipeline, id scheme, manual edits, dictionary |
| `XML/<Language>/<Language>.xml` | Sentences (existing, regenerated) |
| `XML/<Language>/<Language>_dictionary.xml` | Headword entries (new) |

**Outside the corpus (documentation only):** `../FormosanBankGitbook/` corpus page — Task 11.

---

### Task 1: Freeze a comparison baseline

Nothing in this plan is safe to judge without a before/after diff, and the corpus is too large to eyeball.

**Files:**
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/tests/baseline/README.md`
- Create: scratch baseline under `/tmp/.../ilrdf-baseline/` (not committed)

- [ ] **Step 1: Snapshot the current XML outside the tree**

```bash
cd /workspace/ilrdf-v2
BASE=/tmp/claude-1000/-workspace-FormosanBank/ilrdf-baseline
mkdir -p "$BASE" && cp -r Corpora/ILRDF_Dicts/XML "$BASE/XML-pr179"
```

- [ ] **Step 2: Record the baseline inventory**

```bash
source .venv/bin/activate
python QC/count_tokens.py by_corpus --corpus ILRDF_Dicts --corpora_path Corpora \
  > "$BASE/tokens-pr179.txt"
python - <<'PY' > "$BASE/inventory-pr179.txt"
import glob, collections
from lxml import etree
tot = collections.Counter()
for p in sorted(glob.glob("Corpora/ILRDF_Dicts/XML/*/*.xml")):
    r = etree.parse(p).getroot()
    S = r.findall("S")
    tot["S"] += len(S)
    tot["TRANSL"] += sum(len(s.findall("TRANSL")) for s in S)
    tot["AUDIO"] += sum(len(s.findall("AUDIO")) for s in S)
for k, v in sorted(tot.items()):
    print(k, v)
PY
cat "$BASE/inventory-pr179.txt"
```

Expected: `S 167821`, `TRANSL 169946`, `AUDIO 132402` — matching `docs/qc_report.md`. If they differ, stop: the committed XML is not what the QC report describes, and that must be resolved before anything else.

- [ ] **Step 3: Write the baseline note**

Create `Corpora/ILRDF_Dicts/CodeAndDocs/tests/baseline/README.md`:

```markdown
# Baseline for the v2 rework

The v2 rework is judged against PR #179's committed XML (`963d1579e`).
Recreate the baseline with:

    git show 963d1579e:Corpora/ILRDF_Dicts/XML/<Lang>/<Lang>.xml

Expected PR #179 inventory: 167,821 S / 169,946 TRANSL / 132,402 AUDIO.
Every count change from that baseline must be explained in docs/qc_report.md.
```

- [ ] **Step 4: Commit**

```bash
git add Corpora/ILRDF_Dicts/CodeAndDocs/tests/baseline/README.md
git commit -m "ILRDF v2: record the PR #179 comparison baseline"
```

---

### Task 2: GUID-derived sentence ids

Replaces `sentence_id(language, original)` — a truncated SHA-256 of the sentence text — with an id derived from the source's own sentence-item GUID. The text hash retires an id every time the text is corrected, which is backwards for a corpus whose purpose is progressive source-fidelity correction, and it makes `manual_edits.xml` (which matches records by `S/@id`) structurally unusable.

**Files:**
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/ilrdf_source.py`
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_ids.py`

**Interfaces:**
- Produces: `sentence_id(language: str, guid: str) -> str` — `f"{language}_{guid.replace('-', '')[:16]}"`
- Produces: `Sentence` gains `language: str` and an `identifier` property.
- Consumes: nothing from earlier tasks.

**Note — the data is already there.** `Sentence` already carries
`source_ids: set[str]`, populated at `ilrdf_source.py:353` with each merged
item's GUID and then never read. PR #179 collects exactly the key it needs and
hashes the text instead. This task uses what is already being gathered.

**Existing signatures to respect** (do not change them):

```python
extract_sentences(
    language: str,
    snapshot: dict[str, object],
    excluded_audio_ids: set[str],
    translation_overrides: dict[tuple[str, str, str], str],
    used_overrides: set[tuple[str, str, str]],
    translation_exclusions: set[tuple[str, str, str]] | None = None,
    used_exclusions: set[tuple[str, str, str]] | None = None,
) -> tuple[list[Sentence], ExtractionStats]

verify_and_load_snapshot(language: str, snapshot_dir: Path,
                         manifest: dict[str, object]) -> dict[str, object]

LANGUAGES: dict[str, LanguageInfo]          # keys are language names
snapshot_date = manifest["snapshot_commit_date"]
```

- [ ] **Step 1: Write the failing tests**

Create `Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_ids.py`:

```python
import gzip
import json
import unittest
from collections import Counter
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ilrdf_source import (
    LANGUAGES, extract_sentences, load_audio_exclusions,
    load_translation_exclusions, load_translation_overrides, sentence_id,
    verify_and_load_snapshot,
)

BASE = Path(__file__).resolve().parents[1]
SOURCE_DATA = BASE / "source_data"
SNAPSHOTS = SOURCE_DATA / "snapshots"


def _manifest():
    return json.loads(
        (SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))


def _sentences(language):
    """Call extract_sentences with its real signature, defaults for the rest."""
    snapshot = verify_and_load_snapshot(language, SNAPSHOTS, _manifest())
    sentences, _stats = extract_sentences(
        language,
        snapshot,
        load_audio_exclusions(SOURCE_DATA / "audio_exclusions.json"),
        load_translation_overrides(
            SOURCE_DATA / "translation_language_overrides.json"),
        set(),
        load_translation_exclusions(
            SOURCE_DATA / "source_content_exclusions.json"),
        set(),
    )
    return sentences


class TestSentenceId(unittest.TestCase):
    def test_id_is_derived_from_guid_not_text(self):
        a = sentence_id("Amis", "20a69646-e70a-f011-bd65-00155db40116")
        b = sentence_id("Amis", "20a69646-e70a-f011-bd65-00155db40116")
        self.assertEqual(a, b)
        self.assertTrue(a.startswith("Amis_"))

    def test_id_has_no_hyphens_and_is_fixed_width(self):
        got = sentence_id("Amis", "20a69646-e70a-f011-bd65-00155db40116")
        self.assertEqual(got, "Amis_20a69646e70af011")

    def test_ids_unique_within_every_language(self):
        for language in LANGUAGES:
            sentences = _sentences(language)
            ids = [s.identifier for s in sentences]
            duplicates = [i for i, n in Counter(ids).items() if n > 1]
            self.assertEqual(duplicates, [], f"{language}: duplicate ids")

    def test_canonical_id_is_the_lowest_guid_in_the_merge_group(self):
        for language in LANGUAGES:
            sentences = _sentences(language)
            for s in sentences:
                self.assertEqual(
                    s.identifier,
                    sentence_id(language, min(s.source_ids)),
                    f"{language}: {s.identifier} is not the lowest-GUID id",
                )

    def test_id_survives_a_text_correction(self):
        """The whole point: correcting the text must not retire the id."""
        language = "Saaroa"
        sentences = _sentences(language)
        target = sentences[0]
        before = target.identifier
        target.original = target.original + " corrected"
        self.assertEqual(before, sentence_id(language, min(target.source_ids)))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify they fail**

Run: `source .venv/bin/activate && python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_ids.py -q`
Expected: FAIL — `sentence_id` takes `original`, and `Sentence` has no `guids` or `identifier`.

- [ ] **Step 3: Change the id function**

In `ilrdf_source.py`, replace:

```python
def sentence_id(language: str, original: str) -> str:
    digest = hashlib.sha256(original.encode("utf-8")).hexdigest()[:16]
    return f"{language}_{digest}"
```

with:

```python
def sentence_id(language: str, guid: str) -> str:
    """Id derived from the source's own sentence-item GUID.

    The source GUID is stable across ILRDF reorderings and — unlike a hash
    of the sentence text — across our own corrections to that text. A
    published id therefore keeps pointing at the same source record, which
    is what POL-037 asks for and what manual_edits.xml needs (it matches
    records by S/@id, and POL-030 sends hand edits to the original tier).

    Verified 2026-09-05 across all 16 snapshots: every sentence item has an
    id, no GUID carries two different texts, and no GUID appears in two
    languages.
    """
    compact = guid.replace("-", "")
    if len(compact) < 16 or not all(c in "0123456789abcdef" for c in compact.lower()):
        raise ValueError(f"{language}: unusable source GUID {guid!r}")
    return f"{language}_{compact[:16]}"
```

Remove the now-unused `hashlib` import if nothing else uses it.

- [ ] **Step 4: Expose the identifier on `Sentence`**

`Sentence` already collects the GUIDs. Add only `language` and the property:

```python
@dataclass
class Sentence:
    original: str
    translations: list[tuple[str, str]] = field(default_factory=list)
    audio_urls: list[str] = field(default_factory=list)
    source_ids: set[str] = field(default_factory=set)
    language: str = ""

    @property
    def identifier(self) -> str:
        """Canonical id: the lowest source GUID merged into this record."""
        if not self.source_ids:
            raise ValueError(f"{self.original!r}: no source GUID")
        return sentence_id(self.language, min(self.source_ids))
```

In `extract_sentences` at `ilrdf_source.py:350`, pass the language into the
record and make a missing GUID fatal rather than silently skipped:

```python
record = grouped.setdefault(
    original, Sentence(original=original, language=language)
)
source_id = item.get("id")
if not source_id:
    raise ValueError(f"{language}: sentence item without an id")
record.source_ids.add(str(source_id))
```

(The current code at line 351-353 does `if source_id:` — a silent skip. All
211,595 items have an id, so making it fatal costs nothing and catches an
upstream schema change loudly.)

Dedup stays keyed on the normalized text — that is the POL-022 behaviour the
corpus wants — but the canonical id is now the lowest GUID in the group rather
than a side effect of the id function.

- [ ] **Step 5: Update the call site**

In `generate_xml.py`, `_build_tree` currently calls
`sentence_id(language, sentence.original)`. Replace with `sentence.identifier`.

- [ ] **Step 6: Run the tests**

Run: `source .venv/bin/activate && python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/ -q`
Expected: PASS, including the pre-existing suite.

- [ ] **Step 7: Record the id migration**

Create `Corpora/ILRDF_Dicts/CodeAndDocs/docs/id_scheme.md`:

```markdown
# Sentence and entry ids

Ids are `<Language>_<first 16 hex digits of the source GUID>`, e.g.
`Amis_20a69646e70af011`.

## Why not a content hash

PR #179 derived ids from a truncated SHA-256 of the sentence's own original
FORM. That is immune to upstream reordering, but it stabilises the wrong
axis: the id survives only while the text never changes. Every OCR fix,
POL-001 restoration, or punctuation correction retires one id and mints
another — worst behaviour exactly where this corpus most expects to improve.
It also forecloses manual_edits.xml, which matches records by S/@id while
POL-030 sends hand edits to the original tier the hash is derived from.

## Why the source GUID

The ILRDF API assigns a GUID to every word, explanation, and sentence item.
Verified across all 16 committed snapshots on 2026-09-05:

- 211,595 sentence items, 0 without an id
- 210,502 distinct GUIDs, 0 carrying more than one distinct text,
  translation, or audio set
- 0 GUIDs appearing in more than one language
- 144,029 word GUIDs and 169,859 explanation GUIDs, equally unambiguous

## Dedup and the canonical id

The same sentence often appears under several headwords. 21,057 distinct
texts carry 2+ GUIDs (36,421 extra GUIDs). Records are merged by normalized
original text, keeping every distinct translation, and the merged record's
id is the **lowest GUID in the group**.

Consequence to know: a correction that makes two previously distinct texts
identical will merge them and retire one id. That is rare, and
tests/test_ids.py fails loudly if ids stop being unique.

## Migration from PR #179

Every id changes. No id from the 2026-08-23 build is preserved. Nothing
downstream had consumed them — that build was never merged.
```

- [ ] **Step 8: Commit**

```bash
git add Corpora/ILRDF_Dicts/CodeAndDocs/
git commit -m "ILRDF v2: derive sentence ids from source GUIDs, not text hashes"
```

---

### Task 3: generate_xml stops writing derived tiers

Item 8: `generate_xml.py` must never copy a preexisting XML, and must never produce a standard tier by any route other than `standardize.py`. Today `_restore_processed` reads back the processed tree and, among other things, does `standard_form.text = re.sub(r"\s+", " ", standard_form.text).strip()` — an edit to the standard tier from outside `standardize.py`.

It also reverts the original tier to raw source, which discards `clean_xml`'s punctuation canonicalization and is the only reason `standardization.tsv` had to exist (Task 4).

**Files:**
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/generate_xml.py`
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_ilrdf_source.py`

**Interfaces:**
- Produces: `generate_xml.py` modes become `generate` and `audit` only. `restore-source` is removed.
- Produces: `audit` checks published ids against `source_data/published_ids.csv` (see Step 4) instead of byte-comparing source tiers.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_ilrdf_source.py`:

```python
def test_generate_writes_no_derived_tiers(tmp_path):
    """generate must emit source tiers only: no standard FORM, no PHON."""
    import generate_xml
    root = generate_xml._build_tree("Amis", [_one_sentence()], "2026-08-21")
    for sentence in root.findall("S"):
        forms = sentence.findall("FORM")
        assert [f.get("kindOf") for f in forms] == ["original"]
        assert sentence.find("PHON") is None


def test_no_restore_source_mode():
    import generate_xml
    assert "restore-source" not in generate_xml._MODES
```

Add a `_one_sentence()` helper returning a `Sentence` with one GUID, one
translation and one audio url.

- [ ] **Step 2: Run to verify it fails**

Run: `python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_ilrdf_source.py -q -k "derived or restore"`
Expected: FAIL — `_MODES` does not exist and `restore-source` is still a choice.

- [ ] **Step 3: Delete `_restore_processed` and the mode**

Remove `_restore_processed` entirely. Replace the argparse choices:

```python
_MODES = ("generate", "audit")
...
parser.add_argument("mode", nargs="?", choices=_MODES, default="generate")
```

and drop the `elif mode == "restore-source":` branch.

- [ ] **Step 4: Replace source-drift auditing with an id ledger**

**Maintainer ruling, 2026-09-05.** Zero-source-drift is the wrong invariant.
A reproducibility check is just a diff of the rebuild against the published
tree — it needs no in-pipeline enforcement. A refresh after upstream changes
*should* change the text. What must actually hold is **id stability**: an id
never silently changes meaning. Ids may be **deleted** (an item is suppressed)
and **added** (new upstream items, or a split), but never quietly reassigned.

The old `_audit` enforced byte-equality of original/TRANSL/AUDIO against a
fresh generate, which is what forced `restore-source` to exist, which is what
forced `standardization.tsv` to exist. Removing it dissolves all three.

Replace it with a committed ledger. Per POL-039 the table is human-readable
and lives in one documented place, loaded through one loader:

`Corpora/ILRDF_Dicts/CodeAndDocs/source_data/published_ids.csv`

```
id,source_guids,status,note
Amis_20a69646e70af011,20a69646-e70a-f011-bd65-00155db40116,active,
Atayal_605c631ca81eecac_a,605c631c-a81e-ecac-...,active,split from numbered record
Atayal_605c631ca81eecac_b,605c631c-a81e-ecac-...,active,split from numbered record
Atayal_605c631ca81eecac,605c631c-a81e-ecac-...,split-parent,superseded by _a/_b
Kanakanavu_1f0e…,1f0e…,suppressed,lesson number not a translation
```

`audit` then checks, and fails on any unexplained case:

| Condition | Verdict |
|---|---|
| Ledger id present in XML, same `source_guids` | OK |
| Ledger id absent, status `suppressed` or `split-parent` | OK |
| Ledger id absent, status `active` | **FAIL** — silent deletion |
| XML id absent from ledger | **FAIL** — undeclared addition (add a row deliberately) |
| Ledger id present but `source_guids` differ | **FAIL** — id reassigned to different source material |

The last row is the one that matters and the one nothing currently catches: a
text correction that makes two previously distinct sentences identical merges
them and retires an id. Task 2 flagged that as the residual risk of
text-keyed dedup; the ledger is what catches it.

This is generalizable — if it works here it is worth a POL and a shared
validator. Do **not** generalize it in this PR.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/ -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add Corpora/ILRDF_Dicts/CodeAndDocs/
git commit -m "ILRDF v2: generate_xml emits source tiers only; audit allows documented canonicalization"
```

---

### Task 4: Delete standardization.tsv

Item 10. With Task 3 done, `clean_xml`'s original-tier canonicalization is no
longer reverted, so `standardize --remove_accents` can build the standard tier
from an already-canonical original. The three apostrophe rows and the four
identity rows become unnecessary; `=` is handled in Task 5.

**Files:**
- Delete: `Corpora/ILRDF_Dicts/CodeAndDocs/source_data/standardization.tsv`
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/make_xml.sh` (created in Task 9)

**Note for the reviewer:** this converts 99,821 `ʼ` (U+02BC) to `'` **in the
original tier**, where PR #179 kept them. That is consistent with every other
corpus — `clean_xml.py:450` maps `ʼ → '` corpus-wide, and repo policy treats
`'` as the glottal letter — and it is codepoint canonicalization, not a
spelling change. It is nonetheless a visible change to the published original
tier and is called out for the maintainer's sign-off in the Task 12 report.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_ilrdf_source.py`:

```python
def test_no_corpus_local_standardization_table():
    from pathlib import Path
    base = Path(__file__).resolve().parents[1]
    assert not (base / "source_data" / "standardization.tsv").exists(), (
        "standard-tier construction belongs to standardize.py and the "
        "canonical Orthographies/ConversionTables/, not a corpus-local table"
    )
```

- [ ] **Step 2: Run to verify it fails**

Expected: FAIL — the file exists.

- [ ] **Step 3: Delete the table**

```bash
git rm Corpora/ILRDF_Dicts/CodeAndDocs/source_data/standardization.tsv
```

- [ ] **Step 4: Verify the accent behaviour it was masking**

The four identity rows protected `è í ē ǔ` from `standardize`'s accent
stripping. Under `--remove_accents`, only accents attested in each language's
own `QC/validation/reference/<Language>/*/unique_characters.txt` survive.
Check what changes:

```bash
source .venv/bin/activate
python - <<'PY'
import glob, os, collections
from lxml import etree
tab = collections.defaultdict(collections.Counter)
for p in sorted(glob.glob("Corpora/ILRDF_Dicts/XML/*/*.xml")):
    L = os.path.basename(p)[:-4]
    for s in etree.parse(p).iter("S"):
        f = s.find('./FORM[@kindOf="standard"]')
        if f is None or not f.text:
            continue
        for c in "èíēǔ":
            if c in f.text:
                tab[L][c] += f.text.count(c)
for L in sorted(tab):
    print(L, dict(tab[L]))
PY
```

Expected after the rebuild: Thao `í` (attested) and Puyuma `ē` (attested)
survive; Amis `ē` ×5, Paiwan `è` ×1 and Paiwan `ǔ` ×1 are stripped, because
no Amis or Paiwan reference orthography attests them. That is the correct
per-language behaviour the flat table was overriding. Record the seven stripped
characters in `docs/qc_report.md`.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/ -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A Corpora/ILRDF_Dicts/CodeAndDocs/
git commit -m "ILRDF v2: delete the corpus-local standardization table"
```

---

### Task 5: Split source-side alternatives into separate `S`

**Maintainer ruling, 2026-09-05.** Different options become **different `S`
blocks**, not alternate FORMs. Splitting happens on the **original** tier,
early — before `clean_xml` and `standardize` — so the raw `hatomi^/foliki^`
string is not published; each resulting `S` carries one clean reading, with
the source string preserved in `FORM/@notes`. Anything the cascade cannot
interpret is **deleted**, and the counts are reported in the README and the
GitBook page.

`FORM[@kindOf="alternate"]` is **not** used. Checked: its only two uses in the
repo are `Corpora/Latham-1862/` (8, a word list where each `S` is a single
lexical item) and `Corpora/WakelinTexts/` (17, all at **W** level). Neither is
a precedent for two readings of a sentence.

Split ids take a letter suffix: `Atayal_605c631ca81eecac_a`, `_b`, `_c`. Each
is a declared addition in `published_ids.csv`; the parent becomes
`status=split-parent`.

#### The cascade

Applied in two stages, because a numbered record often *also* contains word
alternations and the flat version conflates them.

**Stage A — sentence-level, produces separate `S`:**

1. Numbered multi-example — `1. … 2. …`
2. Sentence alternation — a slash after `.`, `!` or `?`
3. Bracketed phrase alternation — `(A) / (B)`, substituted back into the frame

**Stage B — word-level, on each Stage A fragment:**

4. Exactly one alternation site, exactly two options → 2 `S`
5. Exactly one site, N options that are mutually similar (SequenceMatcher
   ≥ .5, catching `nyaʼ / nya` and `pnqas / pinqasan` alike) → N `S`
6. **Anything else → delete the record.** That means: more than one
   alternation site (you cannot know which combinations the source licenses —
   splitting would manufacture ungrammatical sentences), or an N-way site
   whose options are not mutually similar.

Also in Stage A, per Safolu (`build_formosanbank_xml.py:57-100`): repair a
bracketed annotation that **straddles** a split point, dropping the dangling
bracket from the form and the orphaned head from the remainder. This is what
fixes two of the three cases PR #63 leaves residue on.

#### Measured outcome (against the PR #179 XML, 2026-09-05)

| | Sentences | Result |
|---|---:|---|
| Stage A: numbered | 12 | → 38 `S` |
| Stage A: sentence-final slash | 6 | → 12 `S` |
| Stage A: bracketed phrase | 1 | → 4 `S` |
| Stage B: word-level only | 1,497 | → 3,014 `S` |
| **Split total** | **1,516** | **→ 3,068 `S`** |
| Deleted: more than one site | 862 | uninterpretable |
| Deleted: N-way dissimilar | 32 | uninterpretable |
| **Delete total** | **894** | |

`S` produced per surviving sentence: 1,478 give 2, 31 give 3, 4 give 4, 3 give
1. **Maximum 4.** No explosion, and therefore **no hard variant cap is
needed** — the maintainer predicted this and it holds: **866 of the 894
deletions (96.9%) are exactly the sentences whose cartesian expansion exceeds
3**, and only 4 surviving sentences exceed it. The cap is redundant with the
"more than one site" rule, so it is not implemented.

#### For the README and GitBook page

| Figure | Value |
|---|---:|
| Sentences split into separate records | 1,516 → 3,068 |
| Alternation sites that were spelling or morphological variants | 1,315 |
| Alternation sites between distinct words | 195 |
| Sites where one option is attested nowhere else in that language | 523 |
| Records deleted as uninterpretable | 894 |

Attestation is **reported, never enforced.** The cascade above decides what is
split and what is deleted; attestation contributes nothing to that decision.
It is carried only as a review column, because a site whose option appears
nowhere else in the language is worth a linguist's eye: `hatomi^ / foliki^` is
structurally unambiguous, yet `hatomi^` occurs nowhere outside that one
sentence. With 99.2% of ordinary tokens attested, the 523 flagged sites are a
short review list rather than a defect list — deleting on rarity would discard
good data. (Adapted from the Glosbe test at `glosbe_pipeline.py:2340`, which
uses "try the whole, else require every part to validate" for gloss matching,
not for admitting or rejecting corpus records.)

**Files:**
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/split_alternatives.py`
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_split_alternatives.py`
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/make_xml.sh` (runs right after generate)

**Interfaces:**
- Produces: `stage_a(text: str) -> list[str]` — sentence-level fragments.
- Produces: `stage_b(language: str, text: str) -> list[str] | None` — word-level
  readings, or `None` when the fragment is uninterpretable.
- Produces: `split_record(language: str, text: str) -> list[str] | None` —
  the composition; `None` means delete.
- Produces: CLI `python split_alternatives.py --xml-dir ../XML --apply`,
  writing `docs/split_report.csv` (id, verdict, site count, similarity,
  attestation) for the README figures.

- [ ] **Step 1: Write the failing tests**

```python
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from split_alternatives import stage_a, split_record


class TestStageA(unittest.TestCase):
    def test_numbered(self):
        self.assertEqual(
            stage_a("1. cyux su maniq bway nanu? 2. cyux suʼ maniq bway nanuʼ?"),
            ["cyux su maniq bway nanu?", "cyux suʼ maniq bway nanuʼ?"])

    def test_sentence_final_slash(self):
        self.assertEqual(
            stage_a("Ini iyah na./Mnarig ka patas bgay mu laqi na"),
            ["Ini iyah na.", "Mnarig ka patas bgay mu laqi na"])

    def test_bracketed_phrase_substitutes_into_the_frame(self):
        self.assertEqual(
            stage_a("cyux szwi na (krahu bayhuy) / (hopa na behuy) qu qhuniq."),
            ["cyux szwi na krahu bayhuy qu qhuniq.",
             "cyux szwi na hopa na behuy qu qhuniq."])

    def test_plain_sentence_is_one_fragment(self):
        self.assertEqual(stage_a("hatomi^ han ako."), ["hatomi^ han ako."])


class TestSplitRecord(unittest.TestCase):
    def test_two_options(self):
        self.assertEqual(
            split_record("Amis", "hatomi^/foliki^ han ako ko paliding."),
            ["hatomi^ han ako ko paliding.", "foliki^ han ako ko paliding."])

    def test_three_similar_options(self):
        self.assertEqual(
            split_record("Atayal", "cyux inuʼ qu lukus makuʼ / maku / mu?"),
            ["cyux inuʼ qu lukus makuʼ?", "cyux inuʼ qu lukus maku?",
             "cyux inuʼ qu lukus mu?"])

    def test_two_sites_is_uninterpretable(self):
        self.assertIsNone(split_record(
            "Atayal", "ana cipuq/cipoq pila gitan lga, musa pzyux/piyux nanak la."))

    def test_n_way_dissimilar_is_uninterpretable(self):
        self.assertIsNone(split_record(
            "Atayal", "mutux klayun snyu / snyuw / gasil ru rmugan."))

    def test_no_slash_is_a_single_record(self):
        self.assertEqual(split_record("Amis", "hatomi^ han ako."),
                         ["hatomi^ han ako."])

    def test_no_delimiter_survives_a_split(self):
        for out in split_record("Amis", "hatomi^/foliki^ han ako."):
            self.assertNotIn("/", out)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_split_alternatives.py -q`
Expected: FAIL — module does not exist.

- [ ] **Step 3: Implement `split_alternatives.py`**

Build the attestation vocabulary once per language from snapshot sentences
that contain no slash, plus every headword — an alternation must not attest
itself. Similarity uses `difflib.SequenceMatcher(None, a.lower(), b.lower())`.

- [ ] **Step 4: Run the tests**

Expected: PASS.

- [ ] **Step 5: Corpus-wide run and reconciliation**

```bash
source .venv/bin/activate
cd Corpora/ILRDF_Dicts/CodeAndDocs && python split_alternatives.py --xml-dir ../XML --apply
```

Expected, matching the table above: 1,516 split into 3,068, 894 deleted, no
`/` surviving in any original FORM, and every produced id present in
`published_ids.csv`. Any deviation from those counts means the classifier
drifted from the measured baseline — investigate before committing.

- [ ] **Step 6: Wire into `make_xml.sh`**

Immediately after `generate_xml.py generate`, before `apply_manual_edits.py`.

- [ ] **Step 7: Commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: split source-side alternatives into separate S on the original tier"
```

---
### Task 6: The 13 attestation-supported repairs, via manual_edits

Item 7. These are the repairs from `origin/fix/ilrdf-standard-surface-forms`
(PR #63) that PR #179 does not have and still needs. Unlike the `=` cases,
these are *source-fidelity* problems — the ILRDF API returned a category label
(`數詞`, "numeral") where a word should be, or a Chinese editor note welded onto
the end of a Formosan sentence. Under item 5 and POL-030/POL-002 they belong in
the **original** tier via `manual_edits.xml`, not in a standard-tier patcher.

Still broken on PR #179 and verified present in the current snapshots:

| Class | Count | Example (original tier) |
|---|---:|---|
| CJK category label inside a word | 6 (Saaroa) | `u數詞u paapuhla…` → `ʉnʉmʉ paapuhla…` |
| Trailing Chinese editor note | 6 | `…mawtu zau.這` → `…mawtu zau.` |
| Parenthesised building number | 1 (Sakizaya) | `luma' (101)` → `luma' 101` |

Evidence for each is a dictionary headword or a clean duplicate sentence in
the same language snapshot — the same standard of proof PR #179 already used
for its 97 `?`-corruption recoveries.

**Files:**
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/source_data/source_repairs.json`
- Create: `Corpora/ILRDF_Dicts/manual_edits.xml` (generated)
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_source_repairs.py`

**Interfaces:**
- Consumes: `sentence_id` from Task 2 — repair records are keyed by the **GUID-derived id**, which is exactly what Task 2 made possible.
- Produces: `source_repairs.json` — a list of `{id, language, before, after, evidence}` records.

- [ ] **Step 1: Recover the repair inventory from PR #63**

```bash
cd /workspace/FormosanBank
git show origin/fix/ilrdf-standard-surface-forms:Corpora/ILRDF_Dicts/CodeAndDocs/normalize_standard_forms.py \
  > /tmp/claude-1000/-workspace-FormosanBank/pr63_normalizer.py
git show origin/fix/ilrdf-standard-surface-forms:Corpora/ILRDF_Dicts/CodeAndDocs/standard_form_normalization_qc.md \
  > /tmp/claude-1000/-workspace-FormosanBank/pr63_qc.md
```

The 13 values are in `STANDARD_OVERRIDES`. They are keyed by PR #63's
sequential ids (`Saaroa_1716`), which no longer exist — re-key them by
matching the *before* text against the current snapshots.

- [ ] **Step 2: Write the failing test**

Create `tests/test_source_repairs.py`:

```python
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

BASE = Path(__file__).resolve().parents[1]
REPAIRS = BASE / "source_data" / "source_repairs.json"


class TestSourceRepairs(unittest.TestCase):
    def setUp(self):
        self.records = json.loads(REPAIRS.read_text(encoding="utf-8"))["repairs"]

    def test_every_repair_has_evidence(self):
        for r in self.records:
            self.assertTrue(r.get("evidence"), f"{r['id']} has no evidence")

    def test_no_repair_is_a_no_op(self):
        for r in self.records:
            self.assertNotEqual(r["before"], r["after"], r["id"])

    def test_no_repair_introduces_cjk(self):
        for r in self.records:
            self.assertFalse(
                any("一" <= c <= "鿿" for c in r["after"]),
                f"{r['id']} still contains CJK",
            )

    def test_expected_inventory(self):
        self.assertEqual(len(self.records), 13)
```

- [ ] **Step 3: Run to verify it fails**

Expected: FAIL — `source_repairs.json` does not exist.

- [ ] **Step 4: Build source_repairs.json**

Write a one-off helper (do not commit it) that, for each of PR #63's 13
`before` strings, finds the matching sentence item in the snapshots, computes
its GUID-derived id, and emits:

```json
{
  "schema_version": 1,
  "repairs": [
    {
      "id": "Saaroa_<guid16>",
      "language": "Saaroa",
      "before": "u數詞u paapuhla ualuia laihla upatu.",
      "after": "ʉnʉmʉ paapuhla ualuia laihla upatu.",
      "class": "cjk-category-label",
      "evidence": "Dictionary numeral headword ʉnʉmʉ; 18 Saaroa sentences attest the intact token."
    }
  ]
}
```

Fill `evidence` from PR #63's QC table, re-verified against the current
snapshots. If any `before` string no longer occurs, drop that record and note
it in the QC report rather than forcing a match.

- [ ] **Step 5: Apply them as manual edits**

Generate `manual_edits.xml` by applying the repairs to the original tier and
capturing the diff with the repo's own tool:

```bash
source .venv/bin/activate
# 1. apply source_repairs.json to XML/ original tiers (one-off helper)
# 2. capture the hand edits against git
python QC/utilities/capture_manual_edits.py --corpora_path Corpora/ILRDF_Dicts
```

Expected: `Corpora/ILRDF_Dicts/manual_edits.xml` with 13 `<S>` records, and a
generated `manual_edits.md` changelog.

- [ ] **Step 6: Verify re-application is a no-op**

```bash
python QC/cleaning/apply_manual_edits.py --corpora_path Corpora/ILRDF_Dicts
```

Expected: all 13 records apply cleanly with no warnings. Because ids now come
from GUIDs rather than the text, a record still matches after the text it
edits has changed — this is the concrete payoff of Task 2, and it is worth
noting in the QC report.

- [ ] **Step 7: Run the tests**

Run: `python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/ -q`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: restore the 13 attestation-supported source repairs as manual edits"
```

---

### Task 7: Restore the rights declaration

Item 2. PR #179 stripped `CC-BY-NC` from the XML `copyright` attribute on the
grounds that ILRDF grants no Creative Commons licence. The maintainer's
ruling: restore `CC BY-NC` in the XML, and in the documentation state that we
operate under the fair-use terms the owners themselves describe, linking to
their statement.

**Files:**
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/ilrdf_source.py` (`root_attributes`)
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/source_data/RIGHTS.md`
- Modify: `Corpora/ILRDF_Dicts/README.md` (Task 10)

- [ ] **Step 1: Write the failing test**

Add to `tests/test_ilrdf_source.py`:

```python
def test_root_declares_cc_by_nc():
    from ilrdf_source import root_attributes
    attrs = root_attributes("Amis", "2026-08-21")
    assert attrs["copyright"] == "CC BY-NC"
```

- [ ] **Step 2: Run to verify it fails**

Expected: FAIL — the current value is whatever PR #179 substituted.

- [ ] **Step 3: Set the attribute**

In `root_attributes`, set `"copyright": "CC BY-NC"`.

- [ ] **Step 4: Rewrite RIGHTS.md**

```markdown
# Rights status

FormosanBank publishes this corpus under `CC BY-NC`.

The ILRDF online dictionary's own copyright statement allows quotation for
research and teaching within a reasonable scope, with attribution, and
requires permission for uses beyond that. FormosanBank's use of the
dictionary's example sentences and headword entries for non-commercial
research and teaching is made under those terms, with attribution to the
Indigenous Languages Research and Development Foundation.

Source statement (reviewed 2026-08-21, re-checked 2026-09-05):
https://e-dictionary.ilrdf.org.tw/about?id=6c987092-47c7-ef11-bd58-00155db40116

Downstream users remain responsible for the source's attribution
requirements and applicable law.
```

- [ ] **Step 5: Run the tests**

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: restore CC BY-NC and document the source's fair-use terms"
```

---

### Task 8: Per-language headword dictionaries

Item 3. One `<S>` per headword entry; each sense becomes a `<TRANSL>`. No `W`,
no `M`. The entries go through the same cleaning, standardization and
phonology pipeline as the sentences.

Inventory from the snapshots: 144,610 headword entries (144,029 distinct word
GUIDs — 581 exact repeats), 170,616 senses, all with a Chinese gloss, 54,273
carrying a part of speech.

Part of speech has nowhere to live on `S` (the XSD gives `S` only
`id`/`class`/`sclass`, and `class` is used for word-class on `W`). `TRANSL`
*does* have a free-text `notes` attribute, so the sense's POS rides on its own
`TRANSL` — one fact per sense, which is where it belongs.

**Files:**
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/generate_dictionary.py`
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/ilrdf_source.py` (add `extract_entries`)
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_dictionary.py`
- Create: `Corpora/ILRDF_Dicts/XML/<Language>/<Language>_dictionary.xml` (generated, 16 files)

**Interfaces:**
- Produces: `entry_id(language: str, guid: str) -> str` — same shape as `sentence_id`, over the **word** GUID.
- Produces: `Entry` dataclass — `headword: str`, `guids: list[str]`, `senses: list[Sense]`, `language: str`; `Sense` — `gloss: str`, `part_of_speech: str | None`.
- Produces: `extract_entries(language: str, snapshot: dict) -> list[Entry]` — argument order matches `extract_sentences`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_dictionary.py`:

```python
import gzip
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ilrdf_source import LANGUAGES, entry_id, extract_entries
from test_ids import _sentences  # the extract_sentences wrapper from Task 2
import generate_dictionary

SNAPSHOTS = Path(__file__).resolve().parents[1] / "source_data" / "snapshots"


def _load(language):
    with gzip.open(SNAPSHOTS / f"{language}.json.gz", "rt", encoding="utf-8") as fh:
        return json.load(fh)


class TestEntries(unittest.TestCase):
    def test_entry_ids_unique_per_language(self):
        for language in LANGUAGES:
            entries = extract_entries(language, _load(language))
            ids = [e.identifier for e in entries]
            self.assertEqual(
                [i for i, n in Counter(ids).items() if n > 1], [], language)

    def test_entry_ids_do_not_collide_with_sentence_ids(self):
        """Both live in the same corpus; V081/unique-id checks span files."""
        for language in LANGUAGES:
            entry_ids = {e.identifier for e in extract_entries(language, _load(language))}
            sent_ids = {s.identifier for s in _sentences(language)}
            self.assertEqual(entry_ids & sent_ids, set(), language)

    def test_every_entry_has_a_headword_and_at_least_one_sense(self):
        entries = extract_entries("Saaroa", _load("Saaroa"))
        for e in entries:
            self.assertTrue(e.headword.strip())
            self.assertTrue(e.senses)

    def test_tree_shape(self):
        entries = extract_entries("Saaroa", _load("Saaroa"))[:5]
        root = generate_dictionary._build_tree("Saaroa", entries, "2026-08-21")
        for s in root.findall("S"):
            forms = s.findall("FORM")
            self.assertEqual([f.get("kindOf") for f in forms], ["original"])
            self.assertTrue(s.findall("TRANSL"))
            self.assertIsNone(s.find("W"))
            self.assertIsNone(s.find("PHON"))

    def test_part_of_speech_rides_on_the_sense(self):
        entries = extract_entries("Saaroa", _load("Saaroa"))
        with_pos = [e for e in entries if any(s.part_of_speech for s in e.senses)]
        self.assertTrue(with_pos)
        root = generate_dictionary._build_tree("Saaroa", with_pos[:1], "2026-08-21")
        notes = [t.get("notes") for t in root.iter("TRANSL")]
        self.assertTrue(any(notes))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run to verify they fail**

Expected: FAIL — `extract_entries`, `entry_id` and `generate_dictionary` do not exist.

- [ ] **Step 3: Add `entry_id` and `extract_entries`**

In `ilrdf_source.py`:

```python
@dataclass
class Sense:
    gloss: str
    part_of_speech: str | None = None


@dataclass
class Entry:
    headword: str
    language: str
    guids: list[str] = field(default_factory=list)
    senses: list[Sense] = field(default_factory=list)

    @property
    def identifier(self) -> str:
        return entry_id(self.language, sorted(self.guids)[0])


def entry_id(language: str, guid: str) -> str:
    """Headword-entry id, derived from the source's word GUID.

    Prefixed 'd' so an entry id can never collide with a sentence id even
    if the API ever reused a GUID across item types.
    """
    compact = guid.replace("-", "")
    if len(compact) < 16 or not all(c in "0123456789abcdef" for c in compact.lower()):
        raise ValueError(f"{language}: unusable source GUID {guid!r}")
    return f"{language}_d{compact[:16]}"


def extract_entries(language: str, snapshot: dict) -> list[Entry]:
    """One Entry per published headword, merged by normalized headword text."""
    grouped: dict[str, Entry] = {}
    for response in snapshot.get("responses", []):
        for word in response.get("words") or []:
            if not isinstance(word, dict) or not is_published(word):
                continue
            headword = normalize_source_form(word.get("name"))
            if headword in PLACEHOLDERS or not any(c.isalnum() for c in headword):
                continue
            guid = word.get("id")
            if not guid:
                raise ValueError(f"{language}: word without an id")
            entry = grouped.setdefault(
                headword, Entry(headword=headword, language=language))
            if guid not in entry.guids:
                entry.guids.append(guid)
            for explanation in word.get("explanationItems") or []:
                gloss = normalize_source_text(explanation.get("chineseExplanation"))
                if not gloss or gloss in PLACEHOLDERS:
                    continue
                pos = explanation.get("partOfSpeech") or []
                sense = Sense(gloss=gloss,
                              part_of_speech="; ".join(pos) if pos else None)
                if sense not in entry.senses:
                    entry.senses.append(sense)
    return [e for e in grouped.values() if e.senses]
```

- [ ] **Step 4: Add `generate_dictionary.py`**

```python
#!/usr/bin/env python3
"""Generate per-language headword dictionaries from committed ILRDF snapshots.

Emits source tiers only: FORM[@kindOf="original"] and TRANSL. The standard
tier comes from standardize.py and PHON from add_phonology.py, exactly as
for the sentence files.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from ilrdf_source import (
    LANGUAGES, XML_LANG, extract_entries, root_attributes,
    verify_and_load_snapshot,
)

BASE = Path(__file__).resolve().parent
SOURCE_DATA = BASE / "source_data"
SNAPSHOT_DIR = SOURCE_DATA / "snapshots"
XML_DIR = BASE.parent / "XML"


def _build_tree(language: str, entries: list, snapshot_date: str) -> ET.Element:
    attributes = dict(root_attributes(language, snapshot_date))
    attributes["id"] = f"{attributes['id']}_dictionary"
    root = ET.Element("TEXT", attributes)
    for entry in entries:
        element = ET.SubElement(root, "S", {"id": entry.identifier})
        ET.SubElement(element, "FORM",
                      {"kindOf": "original"}).text = entry.headword
        for index, sense in enumerate(entry.senses):
            attrs = {XML_LANG: "zho"}
            if index:
                attrs["ver"] = "alt"
            if sense.part_of_speech:
                attrs["notes"] = sense.part_of_speech
            ET.SubElement(element, "TRANSL", attrs).text = sense.gloss
    return root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--languages", nargs="*", default=None)
    args = parser.parse_args()
    manifest = json.loads(
        (SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))
    snapshot_date = manifest["snapshot_commit_date"]
    for language in (args.languages or LANGUAGES):
        snapshot = verify_and_load_snapshot(language, SNAPSHOT_DIR, manifest)
        entries = extract_entries(language, snapshot)
        root = _build_tree(language, entries, snapshot_date)
        ET.indent(root, space="    ")
        path = XML_DIR / language / f"{language}_dictionary.xml"
        path.parent.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(str(path), encoding="UTF-8",
                                   xml_declaration=True)
        print(f"{language}: {len(entries)} entries -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Reuse `generate_xml.py`'s `_write_tree` if its signature fits rather than
duplicating the write logic; the point is that only source tiers are written.

- [ ] **Step 5: Run the tests**

Run: `python -m pytest Corpora/ILRDF_Dicts/CodeAndDocs/tests/test_dictionary.py -q`
Expected: PASS.

- [ ] **Step 6: Generate and validate**

```bash
source .venv/bin/activate
cd Corpora/ILRDF_Dicts/CodeAndDocs && python generate_dictionary.py && cd -
python QC/validation/validate_xml.py by_path --path Corpora/ILRDF_Dicts/XML
```

Expected: 32 files, no findings. Note the expected new stats impact in the QC
report: roughly +144,000 `S` and their tokens in `statistics/`.

- [ ] **Step 7: Commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: publish per-language headword dictionaries"
```

---

### Task 9: Split the pipeline into refresh and rebuild

Items 4 and 9. `refresh_source.sh` re-scrapes; `make_xml.sh` rebuilds from
whatever snapshots are committed. **Reproduction is `make_xml.sh` alone.**
Full regeneration is both, in order.

**Files:**
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/refresh_source.sh`
- Create: `Corpora/ILRDF_Dicts/CodeAndDocs/make_xml.sh`
- Delete: `Corpora/ILRDF_Dicts/CodeAndDocs/reproduce.sh`

- [ ] **Step 1: Write `refresh_source.sh`**

```bash
#!/usr/bin/env bash
# FULL REGENERATION ONLY — not part of reproduction.
#
# Re-scrapes the ILRDF dictionary API into source_data/snapshots/*.json.gz
# and rewrites source_data/source_manifest.json. Requires network access to
# https://e-dictionary.ilrdf.org.tw/. Running this changes the source of
# truth; run make_xml.sh afterwards to rebuild XML/ from the new snapshots.
set -euo pipefail
CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"

"$PYTHON" "$CODEDOCS/refresh_source.py" "$@"
echo "Snapshots refreshed. Run make_xml.sh to rebuild XML/."
```

- [ ] **Step 2: Write `make_xml.sh`**

```bash
#!/usr/bin/env bash
# REPRODUCTION ENTRY POINT.
#
# Rebuilds Corpora/ILRDF_Dicts/XML/ from the committed snapshots in
# source_data/snapshots/. No network access required. Requires a pinned
# FormosanBank checkout in $FORMOSANBANK_AUTHORITY.
set -euo pipefail

EXPECTED_AUTHORITY_COMMIT="__SET_IN_TASK_12__"
CODEDOCS="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CORPUS="$(dirname "$CODEDOCS")"
AUTHORITY="${FORMOSANBANK_AUTHORITY:?Set FORMOSANBANK_AUTHORITY to the pinned FormosanBank checkout}"
PYTHON="${FORMOSANBANK_PYTHON:-python3}"
XML_PATH="$CORPUS/XML"

actual_commit="$(git -C "$AUTHORITY" rev-parse HEAD)"
if [[ "$actual_commit" != "$EXPECTED_AUTHORITY_COMMIT" ]]; then
    echo "Authority commit mismatch: expected $EXPECTED_AUTHORITY_COMMIT, found $actual_commit" >&2
    exit 1
fi
test -z "$(git -C "$AUTHORITY" status --porcelain)"

reference_dir="$(mktemp -d)"
trap 'rm -rf -- "$reference_dir"' EXIT
cd "$CODEDOCS"

step() { echo; echo "== $* =="; }

step "1. generate source tiers from snapshots"
"$PYTHON" "$CODEDOCS/generate_xml.py" generate
"$PYTHON" "$CODEDOCS/generate_dictionary.py"

step "2. re-apply recorded manual edits (original tier)"
"$PYTHON" "$AUTHORITY/QC/cleaning/apply_manual_edits.py" --corpora_path "$CORPUS"

step "3. clean_xml (original tier, TRANSL, metadata)"
"$PYTHON" "$AUTHORITY/QC/cleaning/clean_xml.py" \
    --corpora_path "$XML_PATH" --reference_dir "$reference_dir"

step "4. standardize (builds every standard tier)"
"$PYTHON" "$AUTHORITY/QC/utilities/standardize.py" \
    --corpora_path "$XML_PATH" --remove_accents \
    --ortho-path "$AUTHORITY/Orthographies/Ortho113"

step "5. reviewed standard-tier repairs"
"$PYTHON" "$CODEDOCS/standard_repairs.py" --xml-dir "$XML_PATH" --apply

step "6. phonology"
"$PYTHON" "$AUTHORITY/QC/utilities/add_phonology.py" \
    --corpora_path "$XML_PATH" --orthography Ortho113

step "7. fail-closed source audit"
"$PYTHON" "$CODEDOCS/generate_xml.py" audit

rm -f -- "$XML_PATH/cleaner_warnings.csv" \
         "$XML_PATH/html_entities.log" \
         "$XML_PATH/standardize_warnings.csv"

"$PYTHON" -m unittest discover -s "$CODEDOCS/tests"
echo "Rebuilt and verified $XML_PATH"
```

Two ordering changes from `reproduce.sh` matter and should be called out in
review: `apply_manual_edits` now runs first (per the documented pipeline
order), and `standardize` now runs **after** `clean_xml` so the standard tier
is built from an already-canonical original — which is what makes Task 4's
deletion of `standardization.tsv` safe.

- [ ] **Step 3: Note the discarded warning files**

`rm -f` on `cleaner_warnings.csv` and `standardize_warnings.csv` implements
POL-033 (don't commit them) but also throws away review signal. Before the
`rm`, print their row counts so a rebuild reports how many c002/c012/c022
warnings it produced:

```bash
for f in cleaner_warnings.csv standardize_warnings.csv; do
    [[ -f "$XML_PATH/$f" ]] && echo "$f: $(( $(wc -l < "$XML_PATH/$f") - 1 )) rows"
done
```

- [ ] **Step 4: Swap the files in**

```bash
chmod +x Corpora/ILRDF_Dicts/CodeAndDocs/{refresh_source.sh,make_xml.sh}
git rm Corpora/ILRDF_Dicts/CodeAndDocs/reproduce.sh
```

- [ ] **Step 5: Commit**

```bash
git add Corpora/ILRDF_Dicts/CodeAndDocs/
git commit -m "ILRDF v2: split reproduction (make_xml.sh) from re-scraping (refresh_source.sh)"
```

---

### Task 10: Rebuild and reconcile

- [ ] **Step 1: Full rebuild**

```bash
cd /workspace/ilrdf-v2 && source .venv/bin/activate
FORMOSANBANK_AUTHORITY=/workspace/ilrdf-v2 \
FORMOSANBANK_PYTHON="$(which python)" \
  Corpora/ILRDF_Dicts/CodeAndDocs/make_xml.sh
```

- [ ] **Step 2: Rebuild a second time and diff**

Expected: byte-identical XML across two consecutive full runs. If not, find
the non-determinism before continuing.

- [ ] **Step 3: Classify every change against the baseline**

```bash
BASE=/tmp/claude-1000/-workspace-FormosanBank/ilrdf-baseline
diff -r "$BASE/XML-pr179" Corpora/ILRDF_Dicts/XML | head -50
```

Every difference must fall into one of these expected classes. Anything else
is a bug:

| Class | Expected |
|---|---|
| Every `S/@id` changed | Task 2 |
| 99,821 `ʼ` → `'` in the original tier | Task 4 |
| 7 accented characters stripped (Amis `ē`×5, Paiwan `è`×1, `ǔ`×1) | Task 4 |
| Sentences split into separate `S` (1,516 → 3,068) | Task 5 |
| Records deleted as uninterpretable | 894 | Task 5 |
| 13 original-tier repairs | Task 6 |
| `copyright="CC BY-NC"` on all roots | Task 7 |
| 16 new `*_dictionary.xml` files | Task 8 |
| `PHON` values changed where the standard tier changed | consequential |

- [ ] **Step 4: Full QC pass**

```bash
python QC/validation/validate_xml.py by_path --path Corpora/ILRDF_Dicts/XML
python QC/validation/validate_text.py by_path --path Corpora/ILRDF_Dicts/XML --log_dir /tmp/ilrdf-qc
python QC/validation/validate_dialect.py by_path --path Corpora/ILRDF_Dicts/XML
python QC/validation/validate_duplicate_sentences.py by_path --path Corpora/ILRDF_Dicts/XML
python QC/validation/validate_port_readiness.py --corpus ILRDF_Dicts
python QC/count_tokens.py by_corpus --corpus ILRDF_Dicts --corpora_path Corpora
```

Expected: 0 HARD findings. SOFT counts will move — record the new V122/V133
numbers and the token delta in the QC report. The token delta will be large
and positive because of the dictionaries; that is expected and must be stated
explicitly so the `token-comparison` CI check is not read as a regression.

- [ ] **Step 5: Commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: rebuild XML from snapshots under the v2 pipeline"
```

---

### Task 11: Documentation

Items 2, 5 and 7 all end in documentation, and item 5 specifically requires
that `manual_edits.xml` be linked and explained from both the README and the
GitBook page, because those are changes to the source.

**Files:**
- Modify: `Corpora/ILRDF_Dicts/README.md`
- Modify: `Corpora/ILRDF_Dicts/CodeAndDocs/docs/qc_report.md`
- Modify: `../FormosanBankGitbook/` ILRDF corpus page

- [ ] **Step 1: Rewrite the README**

Sections, in order: what the corpus is; **rights** (CC BY-NC + the fair-use
paragraph and the ILRDF link from Task 7); what is in it (sentences *and*
dictionaries, with counts); **reproduction** (`make_xml.sh`, no network) vs
**full regeneration** (`refresh_source.sh` then `make_xml.sh`, network
required); the **id scheme** (link `CodeAndDocs/docs/id_scheme.md`);
**changes to the source** — link `manual_edits.xml` and `manual_edits.md`,
list the three repair classes and say why each is a fidelity fix rather than
an edit; **standard-tier repairs** — the four Thao `=` sentences, with the
rule and why they cannot be fixed in the original tier.

- [ ] **Step 2: Update the QC report**

Refresh every count; add the change-classification table from Task 10 Step 3;
record the seven stripped accents; record the expected statistics impact of the
dictionaries; keep the publication-gate paragraph but update it to match the
new RIGHTS.md.

- [ ] **Step 3: Update the GitBook page**

Per the four integration points (page + nav + README list + stats map). Mirror
the README's rights, manual-edits and standard-repairs sections. Use the
English page as canonical.

```bash
cd ../FormosanBankGitbook && python manage_corpus_pages.py --lint
```

- [ ] **Step 4: Commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: document rights, ids, manual edits and standard repairs"
```

---

### Task 12: Pin the authority commit and final verification

- [ ] **Step 1: Merge current `main` and resolve**

```bash
git fetch origin && git merge origin/main
```

- [ ] **Step 2: Set the pinned commit**

Replace `__SET_IN_TASK_12__` in `make_xml.sh` with `git rev-parse origin/main`.

- [ ] **Step 3: Rebuild twice from a clean checkout and confirm byte-identical output**

- [ ] **Step 4: Record the digest manifest in the QC report**

- [ ] **Step 5: Final commit**

```bash
git add Corpora/ILRDF_Dicts/
git commit -m "ILRDF v2: pin the authority commit and record the rebuild digest"
```

---

## Deliberately out of scope

Recorded so the next reader knows these were considered, not missed.

1. **The 92 numbered multi-example records** (`1. … 2. …` in one `S`). Task 5
   Step 7 inventories them; splitting one record into several `S` is a
   reviewed source-structure change with its own id consequences and belongs
   in its own PR.
2. **Headword audio** — 123,081 items, deferred by decision.
3. **The 24 unresolved `?` corruptions** PR #179 could not attest. Unchanged.
4. **The 316 blank sentence items** in the snapshots, already skipped.
5. **A stats-exclusion mechanism for dictionary files** — a repo-wide,
   CI-coupled change that must not ride along in a corpus PR.
6. **`Corpora/ILRDF_Dicts/qc_mt_text_remediation_20260729.csv`** — a stray
   committed artifact at the corpus root, inherited from before PR #179.
   Likely a POL-033 violation; raise separately.

## Open questions for the maintainer

1. **Original-tier apostrophes.** Task 4 converts 99,821 `ʼ` (U+02BC) to ASCII
   `'` in the *original* tier. This matches every other corpus and repo policy
   that `'` is the glottal letter, and it is what makes the corpus-local table
   deletable. But it is a visible change to published source text. Confirm.
2. **Dictionary file naming.** `<Language>_dictionary.xml` alongside
   `<Language>.xml`. An alternative is `XML/<Language>/dictionary.xml`.
3. **Entry id prefix.** Entry ids use a `d` prefix (`Amis_d20a69646e70af011`)
   to guarantee no collision with sentence ids. Confirm the shape reads well.

---

## Appendix A: `standard_form_normalization_qc.md` from PR #63

Reproduced verbatim, because it lives only on `origin/fix/ilrdf-standard-surface-forms`
and the maintainer has no easy access to that branch. It is the source of the
13 repairs in Task 6, and its opening paragraph is the most useful thing in it:
a recorded first-attempt failure.

> # Standard-form repair QC
>
> Baseline: FormosanBank `dc89d0899b92f1c884aa1b09d3e5d720201b5a71`.
>
> The first version of this change removed every hyphen and underscore. That was
> not correct. Hyphens have mixed uses in this dictionary corpus, including
> proper names such as `Tai-uan` and `Ma-Ing-Cyo`, punctuation, morphology, and
> Bunun/Thao notation. Underscores encode Atayal schwa. The corrected normalizer
> retains both.
>
> The corrected script changes 193 direct sentence-level standards while leaving
> all originals, translations, PHON, AUDIO, attributes, IDs, and structure
> unchanged. A canonical comparison verified the protected content across all 16
> files.
>
> ## Change inventory
>
> | Reviewed source pattern | Standards affected |
> |---|---:|
> | Parenthetical alternative or annotation | 146 |
> | Slash-ordered alternative | 32 |
> | Exact source repair | 13 |
> | Equals-ordered alternative | 2 |
>
> The 13 exact repairs include six Saaroa extraction failures, six unambiguous
> trailing Chinese editor notes, and the Sakizaya `101` building number. The
> Saaroa repairs are supported by dictionary headwords or a duplicate clean
> sentence. For example:
>
> | Corrupt standard | Repaired standard | Evidence |
> |---|---|---|
> | `u數詞u paapuhla...` | `ʉnʉmʉ paapuhla...` | Dictionary numeral headword `ʉnʉmʉ` |
> | `muasala isiparu tu數詞u...` | `muasala 'isiparʉtʉnʉmʉ...` | Exact clean duplicate in Saaroa S 92 |
> | `kapita數詞ia` | `kapitanʉia` | Dictionary headword `kapitanʉ` |
> | `luma' (101)` | `luma' 101` | Translation identifies the 101 building |
>
> ## Retained notation
>
> | Notation | Direct standards retained | Decision |
> |---|---:|---|
> | ASCII hyphen | 3,118 | Mixed orthographic, name, punctuation, and morphology uses require review |
> | Underscore | 214 | Retain Atayal schwa notation |
>
> The remaining validator markers are therefore an inventory for review, not
> evidence that 3,118 sentences are mechanically segmentable.
>
> ## Verification
>
> | Check | Result |
> |---|---|
> | Unit tests | 9 passed |
> | Normalizer second dry run | 0 changes |
> | XML validator | 16 files, no findings |
> | Text validator | 0 HARD findings |
> | Protected-content comparison | No unexpected differences across 16 files |
>
> The text validator reports soft V133 findings for the retained hyphens. It also
> reports source notation in protected originals and translations. No validator
> HARD finding remains.

### What of this survives into v2

| PR #63 element | v2 disposition |
|---|---|
| 13 exact source repairs | **Kept** — Task 6, moved to the original tier via `manual_edits.xml` |
| 2 equals-ordered alternatives | **Kept and extended** — Task 5 covers all 4 current cases |
| Hyphen/underscore retention decision | **Kept, with a better reason** — C012's `<M>`-tier guard makes it automatic; the underscore-is-Atayal-schwa note is worth preserving |
| 146 parenthetical + 32 slash alternatives | **Deferred** — see "Deliberately out of scope" |
| `normalize_standard_forms.py` itself | **Dropped** — id-keyed against retired sequential ids, and it patches published XML in place rather than living in the build |

## Appendix B: what `=` actually is

All four occurrences in the entire corpus, from the raw snapshots:

```
Thao  ata tu kmaanasapunuqi! = ata tu kmasapunuqi!            不要打到頭！
Thao  ata tu kmanasapunuqi! = ata tu kmasapunuqi!             不要打到頭！
Thao  qunriuq thithu naak a ranaw. = thithu qunriuq naak a ranaw   他在偷我的雞。
Thao  lhmazawan mathuaw mabrith, mingqarayza makitzangqaw (= katzangqaw).
                                                              開始時很重，久了就越來越輕。
```

Each `=` joins two phrasings the dictionary presents as equivalent, under one
translation. It is not a null marker (`standardization.tsv`'s note is wrong)
and not a clitic boundary (which is what `standardize.py`'s C012 assumes when
it strips `=` — but C012 never fires here, so that assumption is inert).

PR #179 deletes the character, leaving `ata tu kmaanasapunuqi! ata tu
kmasapunuqi!` — one standard-tier "sentence" containing two sentences, which
inflates token counts and is not a well-formed utterance. Task 5 keeps the
first variant instead.

## Appendix C: what PR #63 actually did, and how

`normalize_standard_forms.py` was a **post-hoc patcher**: it opened the
already-published XML, rewrote `S/FORM[@kindOf="standard"]` in place, and
saved. It was never part of a build. Its `normalize_standard()` applied four
things in a fixed order, only ever to the standard tier:

**1. Exact override, keyed by id.** A 13-entry `STANDARD_OVERRIDES` dict
mapping sentence id → finished replacement string. If an id matched, that
value was used and the other three rules were skipped. These are the
attestation-supported repairs (Task 6). Because they were keyed by PR #63's
sequential ids (`Saaroa_1716`), every key is now dead.

**2. Equals alternatives, gated by id.** `REVIEWED_EQUALS_IDS` held two Thao
ids. For those, `text.split("=", 1)[0]` — keep everything before the first
`=`. Only two of today's four cases were covered.

**3. Parenthetical stripping, ungated.**

```python
PAREN_RE = re.compile(r"\([^()]*\)")

def strip_parenthetical_alternatives(text):
    previous = None
    while text != previous:          # loop handles nesting
        previous = text
        text = PAREN_RE.sub("", text)
    return text
```

Deletes every innermost `(…)` repeatedly until nothing changes. It does not
distinguish a Latin alternative from a Chinese annotation — both just
disappear. This ran on any sentence containing a parenthesis, with no review
gate.

**4. Slash alternatives, gated by id.** `REVIEWED_SLASH_IDS` held 32
hand-reviewed ids. For those only:

```python
FULL_CLAUSE_ALT_RE = re.compile(r"(?<=[.!?])\s*/\s*")
TOKEN_ALT_RE = re.compile(r"(?P<left>\S+?)\s*/\s*(?P<right>\S+)")
```

A slash *after sentence punctuation* separated two whole clauses, so the
clause after it was excised up to the next sentence boundary. A slash *inside*
a clause separated neighbouring word variants, so the left token was kept —
and if the discarded right token carried trailing punctuation the left token
did not, that punctuation was moved over. Then any surviving `/` was deleted.

Finally, whitespace was collapsed, space-before-punctuation removed, and
doubled sentence punctuation folded. A `--apply`-less dry run printed counts,
and re-running after `--apply` had to report zero.

### How it holds up on today's data

Run over the current, fuller snapshots in its real composition order
(parentheses stripped, then slashes), it resolves **2,734 of 2,737**
alternative-bearing standard forms with no leftover delimiter. The three it
cannot handle:

| Residue | Cause |
|---|---|
| `cyux szwi na cyaba na behuy) qu …` | unbalanced parentheses in the source |
| `Mindaduin或 inak lulu.` | bare CJK `或` ("or") outside any bracket |
| `… arahu matash.你` | trailing CJK note plus an inline paren |

That is a good result and the algorithm is worth keeping. Three things change
in v2:

| PR #63 | v2 |
|---|---|
| Slash rule gated to 32 hand-picked ids | Ungated — the rule is uniform, and the id list was only ever a caution |
| Parenthetical stripping treats CJK and Latin alike | CJK annotation removed; Latin content becomes an alternate reading |
| Discarded variants are lost | Preserved as `FORM[@kindOf="alternate"]` where there is exactly one |
| Runs on published XML, id-keyed | Runs inside `make_xml.sh`, no id list |
