# Alternate FORMs & Attribute Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Govern `FORM[@kindOf="alternate"]` with a policy and three validation rules, and make the XML attribute set a closed, documented, test-enforced surface.

**Architecture:** Three new validator rules (V149 HARD, V150 SOFT, V151 SOFT) added to the existing rule modules; every XSD attribute gains an `xs:documentation` annotation; a new `attributes_catalogue.py` generates `ATTRIBUTES.md` from those annotations and fails CI when they are missing or stale, mirroring the existing `rules_catalogue.py` → `RULES.md` pattern. Two new policies (POL-028, POL-053) and an amendment to POL-025. No published XML changes — the two remediation items go on a worklist.

**Tech Stack:** Python 3.13 (repo `.venv`), lxml, pytest, XSD 1.0.

**Spec:** [docs/superpowers/specs/2026-09-08-alternate-form-standardization-design.md](../specs/2026-09-08-alternate-form-standardization-design.md)

## Global Constraints

- **Run everything from the worktree root** using the repo venv: `/workspace/FormosanBank/.venv/bin/python`. Do not `cd` to the main checkout.
- **No published XML may be modified.** Nothing under `Corpora/*/XML/` changes in this plan. Latham-1862 and Glosbe remediation are worklist items only.
- **Next free rule id is V149.** Use V149, V150, V151 and no others.
- **Rule functions take exactly** `(tree: etree._ElementTree, path: Path, index: CorpusIndex | None) -> list[Finding]`.
- **Rule mnemonics are derived from function names** by `_rule_titles.py`; there is no separate registration table. A rule must be appended to its module's `RULES` list to run at all.
- **`RULES.md` is generated**, never hand-edited: `python QC/validation/rules_catalogue.py`. `tests/validators/test_rules_catalogue.py` fails until you regenerate.
- **V150 thresholds, exact values:** overlap ratio `0.6`, short-form exemption `shorter <= 2`, proportion factor `longer > 2 * shorter`.
- **V151 ships SOFT.** Do not put it in `hard.py`. Promotion to HARD belongs to the Glosbe worklist item (Task 7), not to this plan.
- **Expected end state:** zero new HARD findings repo-wide; exactly 12 V150 findings; V151 findings only in Glosbe's three `_tmem.xml` files, totalling 4,157.

---

### Task 1: V149 — an alternate FORM requires a non-alternate sibling

**Files:**
- Modify: `QC/validation/rules/hard.py` (add function; append to `RULES` list at end of file)
- Test: `tests/validators/test_alternate_forms.py` (create)

**Interfaces:**
- Consumes: `Finding`, `Severity` from `QC.validation._finding`; `CorpusIndex` from `QC.validation._corpus_index` — all already imported at the top of `hard.py`.
- Produces: `v149_alternate_FORM_requires_base_sibling(tree, path, index) -> list[Finding]`, emitting `rule_id="V149"`, `Severity.HARD`, one Finding per offending alternate, `location=f"{parent.tag}={parent_id}"`.

- [ ] **Step 1: Write the failing test**

Create `tests/validators/test_alternate_forms.py`:

```python
"""Tests for the POL-028 alternate-FORM rules (V149 HARD, V150 SOFT)."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from lxml import etree

from QC.validation.rules import hard as hard_rules

_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="pwn">'
)


def _tree(body: str) -> etree._ElementTree:
    return etree.parse(BytesIO((_HEAD + body + "</TEXT>").encode("utf-8")))


def test_v149_alternate_without_base_sibling_is_hard():
    tree = _tree('<S id="S1"><FORM kindOf="alternate">soa</FORM></S>')
    findings = hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    )
    assert len(findings) == 1
    assert findings[0].rule_id == "V149"
    assert findings[0].location == "S=S1"


def test_v149_alternate_with_original_sibling_passes():
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<FORM kindOf="alternate">soa</FORM>'
        '</S>'
    )
    assert hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    ) == []


def test_v149_alternate_with_standard_sibling_passes():
    """The sibling need not be the original tier — any non-alternate counts."""
    tree = _tree(
        '<W id="S1W1">'
        '<FORM kindOf="standard">poken-en</FORM>'
        '<FORM kindOf="alternate">poken</FORM>'
        '</W>'
    )
    assert hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    ) == []


def test_v149_checks_own_parent_not_ancestors():
    """An S-level original does not license a bare alternate on a child W."""
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<W id="S1W1"><FORM kindOf="alternate">soa</FORM></W>'
        '</S>'
    )
    findings = hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    )
    assert [f.location for f in findings] == ["W=S1W1"]


def test_v149_file_with_no_alternates_is_silent():
    tree = _tree('<S id="S1"><FORM kindOf="original">so</FORM></S>')
    assert hard_rules.v149_alternate_FORM_requires_base_sibling(
        tree, Path("test.xml"), None
    ) == []
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_alternate_forms.py -v
```

Expected: all five FAIL with `AttributeError: module ... has no attribute 'v149_alternate_FORM_requires_base_sibling'`.

- [ ] **Step 3: Write the implementation**

In `QC/validation/rules/hard.py`, add immediately after `v085_multi_same_lang_transl_requires_ver`:

```python
def v149_alternate_FORM_requires_base_sibling(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V149: a FORM[@kindOf='alternate'] must have a non-alternate FORM
    sibling on the same parent.

    Per POL-028 an alternate is a spelling variant *of something*: it is
    read against the parent's unmarked FORM. An alternate with nothing to
    vary from asserts a variant of no known base, and no downstream tool
    can interpret it. This also covers "an alternate must not be a
    parent's only FORM".

    Clean across the whole bank at the time of writing (116 alternates,
    zero violations); the rule locks that state in.
    """
    findings: list[Finding] = []
    for parent in tree.iter("S", "W", "M"):
        forms = [child for child in parent if child.tag == "FORM"]
        alternates = [f for f in forms if f.get("kindOf") == "alternate"]
        if not alternates:
            continue
        if any(f.get("kindOf") != "alternate" for f in forms):
            continue
        p_id = parent.get("id")
        findings.append(Finding(
            rule_id="V149",
            severity=Severity.HARD,
            message=(
                f"{parent.tag} id={p_id!r} has {len(alternates)} "
                "FORM[@kindOf='alternate'] but no non-alternate FORM to vary "
                "from (POL-028)"
            ),
            path=path,
            location=f"{parent.tag}={p_id}" if p_id else parent.tag,
        ))
    return findings
```

Then add to the `RULES` list at the bottom of `hard.py`, after `v085_multi_same_lang_transl_requires_ver,`:

```python
    # POL-028 alternate FORMs (2026-09-08)
    v149_alternate_FORM_requires_base_sibling,
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_alternate_forms.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Confirm the rule is clean across the whole bank**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py by_path --path Corpora --no-exit-on-hard 2>&1 | grep -i "V149" || echo "V149: no findings (expected)"
```

Expected: `V149: no findings (expected)`. If V149 reports anything, stop — the spec's claim of zero violations is wrong and the finding needs triage before continuing.

- [ ] **Step 6: Regenerate the rules catalogue and commit**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/rules_catalogue.py
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_rules_catalogue.py -v
git add QC/validation/rules/hard.py QC/validation/RULES.md tests/validators/test_alternate_forms.py
git commit -m "Add V149: an alternate FORM requires a non-alternate sibling (POL-028)"
```

---

### Task 2: V150 — alternate FORMs must overlap, and stay in proportion

**Files:**
- Modify: `QC/validation/rules/soft.py` (add helpers + function; append to `RULES`)
- Test: `tests/validators/test_alternate_forms.py:1` (extend the file from Task 1)

**Interfaces:**
- Consumes: `Finding`, `Severity` (already imported in `soft.py`).
- Produces: `v150_alternate_FORM_low_overlap(tree, path, index) -> list[Finding]`, emitting `rule_id="V150"`, `Severity.SOFT`, **one Finding per offending alternate** with `location` populated.

**Why per-element and not aggregated:** `soft.py`'s module docstring says SOFT rules pre-aggregate to avoid flooding the CSV. That guard exists for rules producing thousands of rows; V150 produces 12 repo-wide, and a reviewer cannot act on an aggregate — they need to see which pair. Per-element SOFT findings carrying `location` are an established pattern in `text.py`. V151 (Task 3) *does* aggregate, because it produces 4,157.

- [ ] **Step 1: Write the failing test**

Append to `tests/validators/test_alternate_forms.py`:

```python
from QC.validation.rules import soft as soft_rules


def _pair(base_kind: str, base: str, alt: str) -> etree._ElementTree:
    return _tree(
        f'<W id="W1">'
        f'<FORM kindOf="{base_kind}">{base}</FORM>'
        f'<FORM kindOf="alternate">{alt}</FORM>'
        f'</W>'
    )


def _v150(tree):
    return soft_rules.v150_alternate_FORM_low_overlap(tree, Path("t.xml"), None)


def test_v150_high_overlap_passes():
    """so/soa — a real Latham spelling variant, ratio 0.80."""
    assert _v150(_pair("original", "so", "soa")) == []


def test_v150_both_forms_short_is_exempt():
    """a/u scores 0.00 but is a correct one-letter variant (Wakelin Kwaway
    S2W3). Neither condition may fire: the ratio is unmeasurable at this
    length, and the lengths are equal."""
    assert _v150(_pair("original", "a", "u")) == []


def test_v150_cross_lexeme_fails_overlap():
    """tau/ratta — Latham 'hair', two different words. Overlap fails
    (ratio 0.50, shorter form 3 > 2); proportion passes (5 <= 2*3). This is
    the defect a looser overlap cutoff would hide."""
    findings = _v150(_pair("original", "tau", "ratta"))
    assert len(findings) == 1
    assert findings[0].rule_id == "V150"
    assert findings[0].severity is soft_rules.Severity.SOFT
    assert findings[0].location == "W=W1"
    assert "overlap" in findings[0].message


def test_v150_short_against_long_fails_proportion_only():
    """am/namen — Wakelin. The shorter form is 2, so the overlap condition
    is exempt; only proportion catches it (5 > 2*2).

    This test is what proves the proportion condition is load-bearing:
    delete `proportion_fails` from the rule and this test goes green
    wrongly."""
    findings = _v150(_pair("original", "am", "namen"))
    assert len(findings) == 1
    assert "lengths" in findings[0].message
    assert "overlap" not in findings[0].message


def test_v150_wildly_mismatched_lengths_fail_both():
    """The control case: a short form paired with a very long one is never a
    spelling variant, and must be caught even if either condition is later
    refactored."""
    findings = _v150(
        _pair("original", "dog", "supercalifragilisticexpialidocious")
    )
    assert len(findings) == 1
    assert "overlap" in findings[0].message
    assert "lengths" in findings[0].message


def test_v150_truncation_fails_proportion():
    """tigpapahoang/tigp — Utrecht W118, 12 vs 4."""
    findings = _v150(_pair("original", "tigpapahoang", "tigp"))
    assert len(findings) == 1
    assert "lengths" in findings[0].message


def test_v150_compares_against_closest_sibling():
    """With both an original and a standard present, the alternate is judged
    against whichever it resembles most — here the standard."""
    tree = _tree(
        '<W id="W1">'
        '<FORM kindOf="original">zzzzzz</FORM>'
        '<FORM kindOf="standard">poken-en</FORM>'
        '<FORM kindOf="alternate">poken</FORM>'
        '</W>'
    )
    assert _v150(tree) == []


def test_v150_ignores_diacritics_and_case():
    """NFD-stripped, casefolded: mi-kalakala/mi-karakara differs only in
    letters, and Kan/kan-u only in case."""
    assert _v150(_pair("original", "Kan", "kan-u")) == []


def test_v150_no_base_sibling_is_left_to_v149():
    tree = _tree('<W id="W1"><FORM kindOf="alternate">soa</FORM></W>')
    assert _v150(tree) == []
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_alternate_forms.py -k v150 -v
```

Expected: FAIL with `AttributeError: module ... has no attribute 'v150_alternate_FORM_low_overlap'`.

- [ ] **Step 3: Write the implementation**

At the top of `QC/validation/rules/soft.py`, add to the imports:

```python
import difflib
import unicodedata
```

Add the constants after the existing `_XML_LANG` definition:

```python
# POL-028 alternate-FORM thresholds. Deliberately here rather than in
# POLICIES.md: the policy states the requirement in words so these can be
# tuned from evidence without a re-ruling.
_ALT_OVERLAP_RATIO = 0.6      # below this, the pair does not look related
_ALT_SHORT_EXEMPT = 2         # shorter form <= this: ratio is meaningless
_ALT_LENGTH_FACTOR = 2        # longer form may not exceed this * shorter


def _fold(text: str | None) -> str:
    """Casefold and drop combining marks, so 'tâu' compares as 'tau'."""
    decomposed = unicodedata.normalize("NFD", (text or "").strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))
```

Add the rule function after `v148_W_less_S_in_segmented_file`:

```python
def v150_alternate_FORM_low_overlap(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V150 SOFT (POL-028): an alternate FORM that does not look like a
    spelling variant of its sibling.

    Two independent conditions, either of which flags:

    * **overlap** — the similarity ratio against the closest non-alternate
      sibling is below 0.6. Pairs whose *shorter* form is 2 characters or
      fewer are exempt, because a one- or two-letter form cannot produce a
      meaningful ratio (Wakelin's `a`/`u` scores 0.00 and is correct).
    * **proportion** — the longer form is more than twice the shorter. This
      is what makes the short-form exemption safe: on its own that exemption
      would wave through any short form paired with a long one, and a
      truncation or expansion is not a spelling variant however it scores.

    SOFT, not HARD: legitimate pairs sit below the ratio and cannot be
    separated by any threshold (`pipangn-epen`/`pipangengne-eben`, 0.57).
    A reviewer resolves each; confirmed-fine pairs are recorded in the
    worklist so they are not re-litigated.

    Emits one Finding per offending alternate rather than aggregating: the
    population is ~12 bank-wide, and an aggregate count tells a reviewer
    nothing about which pair to look at.
    """
    findings: list[Finding] = []
    for parent in tree.iter("S", "W", "M"):
        forms = [child for child in parent if child.tag == "FORM"]
        alternates = [f for f in forms if f.get("kindOf") == "alternate"]
        bases = [f for f in forms if f.get("kindOf") != "alternate"]
        if not alternates or not bases:
            continue          # bare alternates are V149's business
        for alt in alternates:
            alt_text = (alt.text or "").strip()
            ratio, base_text = max(
                (
                    (
                        difflib.SequenceMatcher(
                            None, _fold(alt_text), _fold(base.text)
                        ).ratio(),
                        (base.text or "").strip(),
                    )
                    for base in bases
                ),
                key=lambda pair: pair[0],
            )
            lo = min(len(alt_text), len(base_text))
            hi = max(len(alt_text), len(base_text))
            reasons: list[str] = []
            if ratio < _ALT_OVERLAP_RATIO and lo > _ALT_SHORT_EXEMPT:
                reasons.append(f"overlap {ratio:.2f} < {_ALT_OVERLAP_RATIO}")
            if hi > _ALT_LENGTH_FACTOR * lo:
                reasons.append(
                    f"lengths {lo} vs {hi}, more than "
                    f"{_ALT_LENGTH_FACTOR}x apart"
                )
            if not reasons:
                continue
            p_id = parent.get("id")
            findings.append(Finding(
                rule_id="V150",
                severity=Severity.SOFT,
                message=(
                    f"{parent.tag} id={p_id!r}: alternate {alt_text!r} does "
                    f"not look like a spelling variant of {base_text!r} "
                    f"({'; '.join(reasons)}) — POL-028"
                ),
                path=path,
                location=f"{parent.tag}={p_id}" if p_id else parent.tag,
                language=_tree_language(tree, path, index),
                character="",
            ))
    return findings
```

Append to the `RULES` list at the bottom of `soft.py`, after `v148_W_less_S_in_segmented_file,`:

```python
    # POL-028 alternate FORMs (2026-09-08)
    v150_alternate_FORM_low_overlap,
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_alternate_forms.py -v
```

Expected: 14 passed (5 from Task 1, 9 here).

- [ ] **Step 5: Verify the count against the real corpora**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py by_path --path Corpora --no-exit-on-hard 2>&1 | grep -i "V150"
```

Expected: `V150 alternate_FORM_low_overlap: 12`.

If the number is not 12, stop and reconcile against the spec's finding table before continuing — the thresholds are evidence-backed and a different count means either the data or the implementation has drifted.

- [ ] **Step 6: Regenerate the catalogue and commit**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/rules_catalogue.py
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_rules_catalogue.py -v
git add QC/validation/rules/soft.py QC/validation/RULES.md tests/validators/test_alternate_forms.py
git commit -m "Add V150: alternate FORMs must overlap and stay in proportion (POL-028)"
```

---

### Task 3: V151 — S-level TRANSL must not carry @kindOf

**Files:**
- Modify: `QC/validation/rules/soft.py` (add function; append to `RULES`)
- Test: `tests/validators/test_transl_kindof.py` (create)

**Interfaces:**
- Produces: `v151_S_TRANSL_has_no_kindOf(tree, path, index) -> list[Finding]`, `rule_id="V151"`, `Severity.SOFT`, **one Finding per file** with `count` = number of offending S-level TRANSLs.

**Why aggregated, unlike V150:** Glosbe emits 4,157 of these. That is precisely the flood `soft.py`'s docstring guards against, and the remediation is a single scripted strip per file, so per-element rows would add no actionable information.

- [ ] **Step 1: Write the failing test**

Create `tests/validators/test_transl_kindof.py`:

```python
"""V151: TRANSL/@kindOf is a gloss-level distinction, not a sentence one.

At W and M level a TRANSL carries a gloss, and kindOf separates the
source's own gloss from a standardized one — the axis a future gloss
standardization will use. At S level a TRANSL is a free translation, there
is no original-vs-standard axis, and kindOf means nothing.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from lxml import etree

from QC.validation._finding import Severity
from QC.validation.rules import soft as soft_rules

_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="pwn">'
)


def _tree(body: str) -> etree._ElementTree:
    return etree.parse(BytesIO((_HEAD + body + "</TEXT>").encode("utf-8")))


def _v151(tree):
    return soft_rules.v151_S_TRANSL_has_no_kindOf(tree, Path("t.xml"), None)


def test_v151_kindof_on_S_transl_flags():
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<TRANSL xml:lang="eng" kindOf="original">two</TRANSL>'
        '</S>'
    )
    findings = _v151(tree)
    assert len(findings) == 1
    assert findings[0].rule_id == "V151"
    assert findings[0].severity is Severity.SOFT
    assert findings[0].count == 1


def test_v151_bare_S_transl_passes():
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<TRANSL xml:lang="eng">two</TRANSL>'
        '</S>'
    )
    assert _v151(tree) == []


def test_v151_kindof_on_W_and_M_transl_passes():
    """The HundredPaiwanStories pattern: 61,493 W/M glosses carry kindOf and
    are correct. Stripping these would destroy the gloss-standardization
    axis."""
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original">so</FORM>'
        '<TRANSL xml:lang="eng">two</TRANSL>'
        '<W id="S1W1">'
        '<FORM kindOf="original">so</FORM>'
        '<TRANSL xml:lang="eng" kindOf="original">two</TRANSL>'
        '<M id="S1W1M1">'
        '<FORM kindOf="original">so</FORM>'
        '<TRANSL xml:lang="eng" kindOf="original">two</TRANSL>'
        '</M>'
        '</W>'
        '</S>'
    )
    assert _v151(tree) == []


def test_v151_aggregates_per_file():
    """Glosbe emits thousands; one Finding carrying the count, not thousands
    of rows."""
    sentences = "".join(
        f'<S id="S{i}">'
        f'<FORM kindOf="original">so</FORM>'
        f'<TRANSL xml:lang="eng" kindOf="original">two</TRANSL>'
        f'</S>'
        for i in range(5)
    )
    findings = _v151(_tree(sentences))
    assert len(findings) == 1
    assert findings[0].count == 5
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_transl_kindof.py -v
```

Expected: FAIL with `AttributeError: module ... has no attribute 'v151_S_TRANSL_has_no_kindOf'`.

- [ ] **Step 3: Write the implementation**

In `QC/validation/rules/soft.py`, after `v150_alternate_FORM_low_overlap`:

```python
def v151_S_TRANSL_has_no_kindOf(
    tree: etree._ElementTree,
    path: Path,
    index: CorpusIndex | None,
) -> list[Finding]:
    """V151 SOFT: an S-level TRANSL must not carry @kindOf.

    `kindOf` on a TRANSL is a gloss-level distinction. At W and M level a
    TRANSL carries a gloss, and `kindOf` separates the source's own gloss
    (`original`) from a standardized one (`standard`) — the axis a future
    gloss-standardization pass will use, and the reason
    HundredPaiwanStories' 61,493 W/M uses are correct and must not be
    stripped. At S level a TRANSL is a free translation: there is no
    original-vs-standard axis and the attribute carries no information.

    SOFT while Glosbe's 4,157 legacy S-level attributes remain in published
    XML; shipping it HARD would fail CI on every branch in flight. It is
    promoted to HARD by the Glosbe remediation, not here.

    Aggregated per file — unlike V150, the population is in the thousands
    and the fix is one scripted strip per file.
    """
    count = sum(
        1 for s in tree.iter("S")
        for child in s
        if child.tag == "TRANSL" and child.get("kindOf") is not None
    )
    if count == 0:
        return []
    return [Finding(
        rule_id="V151",
        severity=Severity.SOFT,
        message=(
            f"{count} S-level TRANSL elements carry @kindOf; kindOf is a "
            "gloss-level distinction and is meaningless on a free "
            "translation (POL-025 amendment)"
        ),
        path=path,
        count=count,
        language=_tree_language(tree, path, index),
        character="",
    )]
```

Append to `RULES` in `soft.py`, after `v150_alternate_FORM_low_overlap,`:

```python
    v151_S_TRANSL_has_no_kindOf,
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_transl_kindof.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Verify against the real corpora**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py by_path --path Corpora --no-exit-on-hard 2>&1 | grep -i "V151"
```

Expected: `V151 S_TRANSL_has_no_kindOf: 4157`.

Confirm the findings are confined to Glosbe and that HundredPaiwanStories is untouched. Write the CSV to an explicit path — the default is `logs/validate_xml_findings.csv` relative to the working directory, and `logs/` is gitignored but still inside the tree:

```bash
export SCRATCH=/tmp/claude-1000/-workspace-FormosanBank/83bf3e4c-40a0-4dc5-9249-f21fdec5afdd/scratchpad
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py \
    by_path --path Corpora --no-exit-on-hard --csv "$SCRATCH/findings.csv" >/dev/null 2>&1
/workspace/FormosanBank/.venv/bin/python - <<'PY'
import csv, collections, os
corpora = collections.Counter()
with open(os.environ["SCRATCH"] + "/findings.csv") as fh:
    for row in csv.DictReader(fh):
        if row["rule_id"] == "V151":
            corpora[row["file"].split("/")[1]] += int(row["count"])
print(dict(corpora))
PY
```

Expected: `{'Glosbe': 4157}` and nothing else. If `HundredPaiwanStories` appears, the rule is matching W/M TRANSLs — fix before continuing.

- [ ] **Step 6: Regenerate the catalogue and commit**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/rules_catalogue.py
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/ -v
git add QC/validation/rules/soft.py QC/validation/RULES.md tests/validators/test_transl_kindof.py
git commit -m "Add V151: S-level TRANSL must not carry @kindOf (SOFT pending Glosbe remediation)"
```

---

### Task 4: Annotate every XSD attribute and enumerate TRANSL/@kindOf

**Files:**
- Modify: `QC/validation/xml_template.xsd`
- Test: `tests/validators/test_xsd_annotations.py` (create)

**Interfaces:**
- Produces: an XSD in which every one of the 30 `xs:attribute` declarations carries `xs:annotation/xs:documentation`, plus a new named simple type `TRANSL_kindOf_Type`. Task 5's generator reads exactly this structure.

**Note on scope:** XSD 1.0 cannot express "kindOf is forbidden on an S-level TRANSL" — `S`, `W` and `M` all use one `TRANSL_Type`. The schema restricts the *values*; V151 restricts the *level*. Do not attempt to model the level here.

`xml_template.dtd` is a retained fallback only and is **not** updated.

- [ ] **Step 1: Write the failing test**

Create `tests/validators/test_xsd_annotations.py`:

```python
"""POL-053: every attribute in the XSD carries documentation.

The XSD declares no anyAttribute, so it is already a closed whitelist —
an undeclared attribute fails validate_xml. This test makes the other half
true: the closed set is also a *documented* set, so an attribute cannot be
added without saying what it means.
"""
from __future__ import annotations

from pathlib import Path

from lxml import etree

XSD = Path(__file__).resolve().parents[2] / "QC/validation/xml_template.xsd"
XS = "{http://www.w3.org/2001/XMLSchema}"


def _attributes():
    tree = etree.parse(str(XSD))
    return list(tree.iter(f"{XS}attribute"))


def test_every_attribute_has_documentation():
    undocumented = []
    for attr in _attributes():
        name = attr.get("name") or attr.get("ref")
        doc = attr.find(f"{XS}annotation/{XS}documentation")
        if doc is None or not (doc.text or "").strip():
            undocumented.append(name)
    assert not undocumented, (
        "POL-053: these XSD attributes have no xs:documentation: "
        f"{undocumented}"
    )


def test_transl_kindof_is_enumerated():
    tree = etree.parse(str(XSD))
    simple = [
        t for t in tree.iter(f"{XS}simpleType")
        if t.get("name") == "TRANSL_kindOf_Type"
    ]
    assert simple, "TRANSL_kindOf_Type is not defined"
    values = {
        e.get("value")
        for e in simple[0].iter(f"{XS}enumeration")
    }
    assert values == {"original", "standard"}


def test_schema_still_compiles():
    etree.XMLSchema(etree.parse(str(XSD)))


def test_schema_still_accepts_a_representative_document():
    from io import BytesIO

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.parse(BytesIO(
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        b'xml:lang="pwn" source="s" dialect="d">'
        b'<S id="S1">'
        b'<FORM kindOf="original" notes="n">so</FORM>'
        b'<FORM kindOf="alternate">soa</FORM>'
        b'<PHON kindOf="original">so</PHON>'
        b'<TRANSL xml:lang="eng" ver="alt">two</TRANSL>'
        b'<W id="S1W1" class="num" sclass="card">'
        b'<FORM kindOf="original">so</FORM>'
        b'<TRANSL xml:lang="eng" kindOf="original">two</TRANSL>'
        b'</W>'
        b'</S></TEXT>'
    ))
    schema.assertValid(doc)


def test_schema_rejects_an_undeclared_attribute():
    """The whitelist half of POL-053, asserted rather than assumed."""
    from io import BytesIO

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.parse(BytesIO(
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        b'xml:lang="pwn">'
        b'<S id="S1"><FORM kindOf="original" mood="jussive">so</FORM></S>'
        b'</TEXT>'
    ))
    assert not schema.validate(doc)


def test_schema_rejects_a_bad_transl_kindof():
    from io import BytesIO

    schema = etree.XMLSchema(etree.parse(str(XSD)))
    doc = etree.parse(BytesIO(
        b'<?xml version="1.0" encoding="utf-8"?>'
        b'<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" copyright="t" '
        b'xml:lang="pwn">'
        b'<S id="S1"><FORM kindOf="original">so</FORM>'
        b'<TRANSL xml:lang="eng" kindOf="provenance">two</TRANSL></S>'
        b'</TEXT>'
    ))
    assert not schema.validate(doc)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_xsd_annotations.py -v
```

Expected: `test_every_attribute_has_documentation` FAILS listing all 30 names; `test_transl_kindof_is_enumerated` FAILS; `test_schema_rejects_a_bad_transl_kindof` FAILS (currently `xs:string` accepts anything). The other three PASS.

- [ ] **Step 3: Add the TRANSL_kindOf_Type simple type**

In `QC/validation/xml_template.xsd`, immediately after the existing `PHON_kindOf_Type` definition:

```xml
  <xs:simpleType name="TRANSL_kindOf_Type">
    <xs:restriction base="xs:string">
      <xs:enumeration value="original"/>
      <xs:enumeration value="standard"/>
    </xs:restriction>
  </xs:simpleType>
```

Then in `TRANSL_Type`, change:

```xml
    <xs:attribute name="kindOf" type="xs:string"/>
```

to:

```xml
    <xs:attribute name="kindOf" type="TRANSL_kindOf_Type"/>
```

- [ ] **Step 4: Note V026's new partial redundancy**

The XSD now enforces at every level what `v026_M_transl_kindof_enum` enforced only at M level. V026 stays — a named rule produces a far more readable finding than a raw XSD error — but a future reader needs to know why both exist. In `QC/validation/rules/hard.py`, append to `v026_M_transl_kindof_enum`'s docstring:

```
    Partly redundant since 2026-09-08: the XSD's TRANSL_kindOf_Type now
    restricts this value at every level, so a bad value fails V000 first.
    Kept because a named rule reports the offending element far more
    legibly than an XSD error, and because V026 is M-scoped by design
    while the schema type is shared by S, W and M.
```

- [ ] **Step 5: Annotate all 30 attributes**

Every `xs:attribute` gets an `xs:annotation/xs:documentation` child. An attribute with a child element can no longer be self-closing — change `<xs:attribute .../>` to `<xs:attribute ...>…</xs:attribute>`.

The pattern, using `FORM/@kindOf` as the worked example:

```xml
    <xs:attribute name="kindOf" type="FORM_kindOf_Type" use="required">
      <xs:annotation>
        <xs:documentation>
          Which tier this FORM belongs to. `original` is the text as the
          actual source prints it, preserving the source's orthographic
          choices. `standard` is that content transliterated into
          FormosanBank's common standard orthography. `alternate` is a
          spelling variant of a sibling FORM on the same node (POL-028);
          it requires a non-alternate sibling (V149) and must overlap it
          or stay in proportion to it (V150).
        </xs:documentation>
      </xs:annotation>
    </xs:attribute>
```

Write the remaining 29 in the same shape, using this text:

| Element | Attribute | Documentation |
| --- | --- | --- |
| TEXT | `id` | Stable public identifier for this text, unique across the published bank (V081). Renaming one breaks external references — see POL-037. |
| TEXT | `citation` | Human-readable bibliographic citation for the source. Required on every published TEXT (POL-042). |
| TEXT | `BibTeX_citation` | The same source as a BibTeX entry, for machine reuse. Required on every published TEXT. |
| TEXT | `copyright` | The rights statement under which this text is published. Required on every published TEXT; POL-042 through POL-045 govern what may go here. |
| TEXT | `xml:lang` | ISO 639-3 code for the language of the Formosan-text tiers, validated against `QC/validation/iso-639-3.txt` (V035). Note `trv` covers the whole Seediq family: `trv` plus `dialect="Truku"` is Truku, anything else is Seediq. |
| TEXT | `source` | Free-text provenance for the whole text — the publication, page, URL or collection it came from. |
| TEXT | `audio` | Name or identifier of the audio collection this text's recordings belong to. Present only for corpora with audio. |
| TEXT | `glottocode` | Glottolog code for the variety, where one is useful alongside the ISO 639-3 code. |
| TEXT | `dialect` | Dialect label, from the canonical list in `dialects.csv` (V036). Together with `xml:lang` this determines language identity and which reference materials apply. |
| S | `id` | Sentence identifier, unique across all S, W and M within the file (V039). Part of the public identifier surface (POL-037). A sentence split from another for optional material takes the original's id plus `-opt` (POL-026). |
| S | `audio_url` | Source URL for this sentence's audio, where the recording is addressed by URL rather than by file. |
| S | `source` | Sentence-specific provenance — page, column, or editorial note about where this particular sentence came from. |
| W | `id` | Word identifier, unique across all S, W and M within the file (V039). |
| W | `class` | Grammatical class label for the word. The schema imposes no controlled vocabulary. |
| W | `sclass` | Grammatical subclass label for the word. The schema imposes no controlled vocabulary. |
| M | `id` | Morpheme identifier, unique across all S, W and M within the file (V039). |
| M | `class` | Grammatical class label for the morpheme. The schema imposes no controlled vocabulary. |
| M | `sclass` | Grammatical subclass label for the morpheme. The schema imposes no controlled vocabulary. |
| FORM | `notes` | Human-readable qualification of this FORM — a transcription note, a review status, or what the source actually printed where the tier departs from it. |
| PHON | `kindOf` | Which FORM tier this IPA representation was derived from, `original` or `standard` (V071). A parent may carry at most one PHON per value (V072). |
| TRANSL | `xml:lang` | ISO 639-3 code for the language this translation is *into* — not the language of the text (V023, V035). |
| TRANSL | `kindOf` | Only meaningful at W and M level, where a TRANSL carries a gloss: `original` is the source's own gloss, `standard` a standardized one. Forbidden on an S-level TRANSL, which is a free translation with no such axis (V151). |
| TRANSL | `ver` | Discriminates multiple translations into the same language on one parent (POL-025). When a parent has two or more same-language TRANSLs, all but one must carry this (V085). The allowed values are owned by V084's allowlist — currently `{"alt"}` — deliberately not duplicated as an XSD enumeration, so there is one place to update. |
| TRANSL | `notes` | Human-readable qualification of this translation — translator, review status, or a literal reading kept out of the translation text itself (POL-024). |
| AUDIO | `start` | Start offset in seconds within the referenced audio file. Typed `xs:double`, so non-numeric values fail at schema time. |
| AUDIO | `end` | End offset in seconds within the referenced audio file. Must be greater than `start` (V054). |
| AUDIO | `file` | Name of the audio file this element refers to. Audio files are gitignored and fetched per corpus by `download_audio_data.sh`. |
| AUDIO | `url` | URL the audio can be fetched from, where it is addressed remotely rather than by filename. |
| AUDIO | `source` | Provenance of the recording — for example the video or broadcast a clip was extracted from. |

- [ ] **Step 6: Run the tests to verify they pass**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_xsd_annotations.py -v
```

Expected: 6 passed.

- [ ] **Step 7: Confirm the whole bank still validates**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py by_path --path Corpora --no-exit-on-hard 2>&1 | grep -iE "V000|schema" | head
```

Expected: no V000 schema failures. Annotations are inert, and every `TRANSL/@kindOf` in the bank is already `original`, so the new enumeration rejects nothing that exists.

- [ ] **Step 8: Commit**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/ -q
git add QC/validation/xml_template.xsd tests/validators/test_xsd_annotations.py
git commit -m "Document every XSD attribute and enumerate TRANSL/@kindOf (POL-053)"
```

---

### Task 5: Generate ATTRIBUTES.md from the XSD

**Files:**
- Create: `QC/validation/attributes_catalogue.py`
- Create: `QC/validation/ATTRIBUTES.md` (generated — do not hand-write)
- Test: `tests/validators/test_attributes_catalogue.py` (create)

**Interfaces:**
- Consumes: the annotated XSD from Task 4.
- Produces: `collect() -> list[tuple[str, str, str, str, str]]` returning `(element, attribute, use, allowed_values, documentation)` sorted by element then attribute; `render() -> str`; a `--check` CLI flag exiting 1 when stale or undocumented.

- [ ] **Step 1: Write the failing test**

Create `tests/validators/test_attributes_catalogue.py`:

```python
"""QC/validation/ATTRIBUTES.md must match the XSD that actually validates.

Same contract as test_rules_catalogue.py: the documented attribute set is
generated, so it cannot drift from the schema. POL-053 requires an
attribute to be declared, annotated, catalogued and given a policy entry;
this test enforces the first three.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "QC/validation/attributes_catalogue.py"
CATALOGUE = REPO_ROOT / "QC/validation/ATTRIBUTES.md"

sys.path.insert(0, str(REPO_ROOT))


def test_catalogue_is_current():
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    assert result.returncode == 0, (
        f"{CATALOGUE.name} is stale — run "
        f"`python QC/validation/attributes_catalogue.py`.\n"
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )


def test_every_attribute_is_documented():
    from QC.validation.attributes_catalogue import collect

    missing = [
        f"{element}/@{attribute}"
        for element, attribute, _use, _values, doc in collect()
        if not doc.strip()
    ]
    assert not missing, f"attributes with no xs:documentation: {missing}"


def test_catalogue_names_every_attribute():
    from QC.validation.attributes_catalogue import collect

    text = CATALOGUE.read_text(encoding="utf-8")
    for element, attribute, _use, _values, _doc in collect():
        assert f"| `{attribute}` |" in text, (
            f"{element}/@{attribute} is not in {CATALOGUE.name}"
        )


def test_enumerated_values_are_surfaced():
    from QC.validation.attributes_catalogue import collect

    rows = {(e, a): v for e, a, _u, v, _d in collect()}
    assert rows[("FORM", "kindOf")] == "original | standard | alternate"
    assert rows[("TRANSL", "kindOf")] == "original | standard"
    assert rows[("PHON", "kindOf")] == "original | standard"


def test_required_attributes_are_marked():
    from QC.validation.attributes_catalogue import collect

    rows = {(e, a): u for e, a, u, _v, _d in collect()}
    assert rows[("TEXT", "id")] == "required"
    assert rows[("FORM", "kindOf")] == "required"
    assert rows[("TEXT", "source")] == "optional"
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_attributes_catalogue.py -v
```

Expected: all FAIL — `attributes_catalogue.py` does not exist.

- [ ] **Step 3: Write the generator**

Create `QC/validation/attributes_catalogue.py`:

```python
#!/usr/bin/env python3
"""Generate QC/validation/ATTRIBUTES.md — every attribute the XML may carry.

POL-053: the XML attribute set is closed and documented. The XSD declares
no `anyAttribute`, so an undeclared attribute already fails validate_xml —
that is the whitelist. This builds the human-readable half from the same
schema, so the documentation cannot drift from what actually validates
(POL-039: the table is derived, not retyped).

    python QC/validation/attributes_catalogue.py            # write ATTRIBUTES.md
    python QC/validation/attributes_catalogue.py --check    # exit 1 if stale

`tests/validators/test_attributes_catalogue.py` runs --check, so a new
attribute fails CI until it is annotated and the catalogue regenerated.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

SCHEMA = Path(__file__).resolve().parent / "xml_template.xsd"
OUTPUT = Path(__file__).resolve().parent / "ATTRIBUTES.md"

XS = "{http://www.w3.org/2001/XMLSchema}"

# Document order, so the catalogue reads top-down like the XML does rather
# than alphabetically.
ELEMENT_ORDER = ["TEXT", "S", "W", "M", "FORM", "PHON", "TRANSL", "AUDIO"]


def _element_name(complex_type: etree._Element) -> str | None:
    """The element a complexType describes.

    Named types follow the `<ELEMENT>_Type` convention; an inline type is
    named by the xs:element that contains it (TEXT).
    """
    name = complex_type.get("name")
    if name:
        return name[:-5] if name.endswith("_Type") else name
    parent = complex_type.getparent()
    if parent is not None and parent.tag == f"{XS}element":
        return parent.get("name")
    return None


def _enumerations(schema: etree._ElementTree) -> dict[str, str]:
    """simpleType name -> 'a | b | c' for every enumerated type."""
    out: dict[str, str] = {}
    for simple in schema.iter(f"{XS}simpleType"):
        name = simple.get("name")
        if not name:
            continue
        values = [e.get("value") for e in simple.iter(f"{XS}enumeration")]
        if values:
            out[name] = " | ".join(values)
    return out


def _documentation(attribute: etree._Element) -> str:
    node = attribute.find(f"{XS}annotation/{XS}documentation")
    if node is None or not node.text:
        return ""
    # xs:documentation is indented block text; collapse to one line.
    return re.sub(r"\s+", " ", node.text).strip()


def collect() -> list[tuple[str, str, str, str, str]]:
    """(element, attribute, use, allowed_values, documentation).

    Sorted by the element's position in the XML, then attribute name.
    """
    schema = etree.parse(str(SCHEMA))
    enums = _enumerations(schema)
    rows: list[tuple[str, str, str, str, str]] = []
    for complex_type in schema.iter(f"{XS}complexType"):
        element = _element_name(complex_type)
        if element is None:
            continue
        for attribute in complex_type.findall(f"{XS}attribute"):
            name = attribute.get("name") or attribute.get("ref") or "?"
            use = attribute.get("use") or "optional"
            type_name = attribute.get("type") or ""
            values = enums.get(type_name, "")
            if not values and type_name.startswith("xs:"):
                values = type_name
            rows.append((element, name, use, values, _documentation(attribute)))

    def sort_key(row):
        element, attribute = row[0], row[1]
        rank = (ELEMENT_ORDER.index(element)
                if element in ELEMENT_ORDER else len(ELEMENT_ORDER))
        return (rank, element, attribute)

    return sorted(rows, key=sort_key)


def render() -> str:
    rows = collect()
    out = [
        "# XML attributes",
        "",
        "Every attribute a FormosanBank XML file may carry, generated from",
        "`QC/validation/xml_template.xsd` by",
        "`QC/validation/attributes_catalogue.py`. **Do not edit by hand** —",
        "annotate the attribute in the XSD and regenerate.",
        "",
        "The schema declares no `anyAttribute`, so this list is exhaustive:",
        "an attribute not named here fails `validate_xml.py`. Adding one",
        "requires an XSD declaration, an `xs:documentation` annotation, a",
        "regenerated catalogue, and a policy entry (POL-053).",
        "",
    ]
    current = None
    for element, attribute, use, values, doc in rows:
        if element != current:
            current = element
            out += [
                f"## `<{element}>`",
                "",
                "| Attribute | Use | Allowed values | Meaning |",
                "| --- | --- | --- | --- |",
            ]
        shown = f"`{values}`" if values else "—"
        out.append(f"| `{attribute}` | {use} | {shown} | {doc} |")
    out += ["", f"{len(rows)} attributes across {len(set(r[0] for r in rows))} elements.", ""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if ATTRIBUTES.md is not what this would write")
    args = parser.parse_args()

    undocumented = [
        f"{element}/@{attribute}"
        for element, attribute, _use, _values, doc in collect()
        if not doc.strip()
    ]
    if undocumented:
        print("POL-053: these attributes have no xs:documentation in the XSD:",
              file=sys.stderr)
        for name in undocumented:
            print(f"  {name}", file=sys.stderr)
        return 1

    rendered = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(f"{OUTPUT.name} is stale — regenerate it.", file=sys.stderr)
            return 1
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Generate the catalogue**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/attributes_catalogue.py
head -30 QC/validation/ATTRIBUTES.md
```

Expected: `wrote .../ATTRIBUTES.md`, and the head shows the `<TEXT>` table with `id`, `citation`, `BibTeX_citation` and their documentation.

- [ ] **Step 5: Run the tests to verify they pass**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/validators/test_attributes_catalogue.py -v
```

Expected: 5 passed.

- [ ] **Step 6: Verify the guard actually bites**

Temporarily add an undocumented attribute and confirm both halves fail:

```bash
/workspace/FormosanBank/.venv/bin/python - <<'PY'
from pathlib import Path
p = Path("QC/validation/xml_template.xsd")
original = p.read_text(encoding="utf-8")
p.write_text(original.replace(
    '<xs:attribute name="glottocode"',
    '<xs:attribute name="mood" type="xs:string"/>\n      <xs:attribute name="glottocode"',
    1), encoding="utf-8")
PY
/workspace/FormosanBank/.venv/bin/python QC/validation/attributes_catalogue.py --check; echo "exit=$? (expect 1)"
git checkout QC/validation/xml_template.xsd
/workspace/FormosanBank/.venv/bin/python QC/validation/attributes_catalogue.py --check; echo "exit=$? (expect 0)"
```

Expected: first `exit=1` naming `TEXT/@mood`, then `exit=0` after the revert. If the first run exits 0, the guard is not working — fix before committing.

- [ ] **Step 7: Commit**

```bash
git add QC/validation/attributes_catalogue.py QC/validation/ATTRIBUTES.md tests/validators/test_attributes_catalogue.py
git commit -m "Generate ATTRIBUTES.md from the XSD; fail CI on undocumented attributes (POL-053)"
```

---

### Task 6: Write POL-028 and POL-053, and amend POL-025

**Files:**
- Modify: `POLICIES.md` (POL-028 and POL-029 are free in §3; POL-053 is free in §6)

**Interfaces:** None — prose only. POL-028 is referenced by V149's and V150's docstrings written in Tasks 1–2; POL-053 by Task 5's generator docstring.

- [ ] **Step 1: Add POL-028 to section 3, immediately after POL-027**

```markdown
### POL-028 · RULED · 2026-09-08 · alternate FORMs

`FORM[@kindOf="alternate"]` records a **spelling variant** of a sibling FORM
on the same node. It is the only marking for this: not `ver`, not
`"alternative"`, not an `-opt` suffix.

- Every alternate must have at least one **non-alternate FORM sibling on the
  same parent** (V149 HARD), and must satisfy two independent conditions
  against it (V150 SOFT):
  1. **Overlap** — it must overlap the sibling highly, or, where both forms
     are too short for overlap to be measurable, simply be short.
  2. **Proportion** — neither form may be more than twice the length of the
     other. A spelling variant does not double a word's length.

  Proportion is a separate test because overlap alone cannot catch it: a
  short form paired with a long one shares a short member, and a short-form
  exemption written against the shorter string would wave it through. The
  operative thresholds live in V150, deliberately not here, so they can be
  tuned from evidence without a re-ruling.
- **The variation may span the whole form.** A one-letter word alternating
  `a`/`u` (WakelinTexts `Kwaway/S2W3`) is as valid an alternate as a letter
  changing inside a longer word. Nothing requires the variation to be
  word-internal.
- A competing **lexeme** for the same meaning, or a different gloss, is not
  an alternate; per POL-027 it becomes its own `S` block. Latham-1862
  currently carries 6 such cases; they are tracked for remediation.
- Alternates may sit at S, W or M, and belong on the node that actually
  varies. A word-list corpus whose `S` is a word is the S-level case.
- **Optional material is resolved by scope.** What forces a separate `S`
  block is not whether the variation sits inside a word, but whether the
  **sentence's word inventory changes**. A whole optional *word* —
  `x y (z)` — changes the W tier and the gloss alignment, so it becomes two
  `S` blocks (POL-026), the second taking the first's id plus `-opt`.
  Optional material that leaves the word count unchanged — `puken-(en)`,
  `(u)m-lavi`, and equally a whole short word alternating `a`/`u` — becomes
  an `alternate` FORM on the word that varies, never a second sentence.
  Neither mechanism leaves parentheses in a published FORM.
```

- [ ] **Step 2: Amend POL-025**

In POL-025, delete the sentence `(The XSD already requires a `ver` when a parent has two same-language TRANSLs.)` — XSD 1.0 cannot express this; V085 does. Replace it and extend the policy so the block reads:

```markdown
### POL-025 · RULED · 2026-08-10 · alternative translations
When a source gives more than one translation of a sentence into the same
language, they all live **in the same `<S>` block** as multiple TRANSL
elements, with all but one carrying `ver="alt"`. V085 enforces this and V084
restricts the value; the XSD does not and cannot express either. Do not drop
the extra readings (Puyuma-Teng audit found 7 lost) and do not create
duplicate S blocks for them.

`ver="alt"` is **not** confined to the S level — MontgomeryTexts, RauDong and
WakelinTexts use it on W and M, which is correct.

**`kindOf` on a TRANSL is a different axis and is not interchangeable with
`ver`.** It is meaningful only at W and M level, where a TRANSL carries a
gloss: `original` is the source's own gloss, `standard` a standardized one.
On an S-level TRANSL — a free translation — there is no such axis and the
attribute carries no information (V151). Amended 2026-09-08.
```

- [ ] **Step 3: Add POL-053 to section 6, after POL-052**

```markdown
### POL-053 · RULED · 2026-09-08 · XML attributes are a closed, documented set
Every attribute a FormosanBank XML file may carry is declared in
[QC/validation/xml_template.xsd](QC/validation/xml_template.xsd) and carries
an `xs:annotation/xs:documentation` stating its meaning and allowed values.

The schema declares no `anyAttribute`, so an undeclared attribute already
fails `validate_xml.py`. This policy names that as a deliberate guarantee
rather than an accident of the schema: **the attribute set is a whitelist.**

[QC/validation/ATTRIBUTES.md](QC/validation/ATTRIBUTES.md) is generated from
the XSD by `attributes_catalogue.py` and is never hand-edited, on the same
terms as `RULES.md` (POL-039 — derived, not retyped).

**Adding an attribute requires four things:** an XSD declaration, an
`xs:documentation` annotation, a regenerated catalogue, and a policy entry.
`tests/validators/test_attributes_catalogue.py` enforces the first three;
review enforces the fourth. No attribute is added ad hoc.
```

- [ ] **Step 4: Verify the policy ids are unique and the file still reads**

```bash
grep -o "POL-[0-9]\+" POLICIES.md | sort | uniq -d
```

Expected: no output (no duplicate ids).

```bash
grep -n "POL-028\|POL-053\|Amended 2026-09-08" POLICIES.md
```

Expected: POL-028 in section 3, POL-053 in section 6, the amendment note in POL-025.

- [ ] **Step 5: Commit**

```bash
git add POLICIES.md
git commit -m "POL-028 (alternate FORMs), POL-053 (attributes are closed and documented), amend POL-025"
```

---

### Task 7: Write the remediation worklist

**Files:**
- Create: `claudeplans/2026-09-08-alternate-form-worklist.md`

**Interfaces:** None. This file is the definition of done for the two remediation items, including V151's promotion to HARD — which deliberately does **not** happen in this plan.

- [ ] **Step 1: Regenerate the current finding list to populate the worklist**

```bash
export SCRATCH=/tmp/claude-1000/-workspace-FormosanBank/83bf3e4c-40a0-4dc5-9249-f21fdec5afdd/scratchpad
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py \
    by_path --path Corpora --no-exit-on-hard --csv "$SCRATCH/findings.csv" >/dev/null 2>&1
/workspace/FormosanBank/.venv/bin/python - <<'PY'
import csv, os
with open(os.environ["SCRATCH"] + "/findings.csv") as fh:
    for row in csv.DictReader(fh):
        if row["rule_id"] == "V150":
            print(row["file"], "|", row["location"], "|", row["message"])
PY
```

These 12 rows are what the worklist must enumerate by id. Read them rather than copying the table below on faith — if the data has moved, the worklist follows the data.

- [ ] **Step 2: Write the worklist**

Create `claudeplans/2026-09-08-alternate-form-worklist.md`:

```markdown
# Alternate-FORM and TRANSL/@kindOf remediation worklist

Opened 2026-09-08 alongside POL-028, POL-053 and rules V149–V151.
Spec: `docs/superpowers/specs/2026-09-08-alternate-form-standardization-design.md`

The rules shipped without remediating the data they flag, deliberately: a
HARD rule failing on published XML would block every branch in flight. This
file is what closes that gap.

## Item 1 — Latham-1862 cross-lexeme alternates (V150)

6 alternates are competing lexemes for the same gloss, not spelling
variants. Per POL-027 each becomes its own `S` block.

| S id | Gloss | original | alternate | ratio |
| --- | --- | --- | --- | --- |
| `S_favorlang_mouth` | mouth | `ranied` | `sabbacha` | 0.14 |
| `S_sida_foot` | foot | `rahpal` | `tiltil` | 0.17 |
| `S_favorlang_breast` | breast | `arrabis` | `zido` | 0.18 |
| `S_favorlang_neck` | neck | `bokkir` | `arribórribon` | 0.33 |
| `S_favorlang_man` | man | `bahosa` | `sjam` | 0.40 |
| `S_favorlang_hair` | hair | `tâu` | `ratta` | 0.50 |

`totto`/`tutta` (0.60) and `so`/`soa` (0.80) are genuine spelling variants
and stay as alternates.

Doing this means changing `CodeAndDocs/build_lexical_xml.py` so a
comma-separated source cell emits one `S` per option rather than an
alternate tier, then rebuilding via `make_xml.sh`. New S ids are new public
identifiers — POL-037 applies, so pick a scheme and record it in the corpus
README.

## Item 2 — Glosbe S-level TRANSL/@kindOf (V151)

4,157 S-level TRANSLs carry `kindOf="original"`, which means nothing on a
free translation. Confined to `Glosbe_{ami,tay,xsy}_eng_tmem.xml`; they are
legacy, since the current `glosbe_pipeline.py` emits only `xml:lang` and
`ver`. HundredPaiwanStories' 61,493 W/M uses are correct and must not be
touched.

Ordered; step 4 is what closes the item:

1. Add a strip step to `Corpora/Glosbe/CodeAndDocs/make_xml.sh` removing
   `@kindOf` from S-level TRANSLs. Glosbe's scrape is not reproducible and
   `make_xml.sh` operates in place on the published XML, so this is the
   POL-038-compliant way to make the change in code rather than by hand.
2. Run it. Confirm 4,157 attributes gone across the three files, and that
   no W- or M-level TRANSL was touched.
3. Confirm V151 reports zero bank-wide.
4. **Move `v151_S_TRANSL_has_no_kindOf` from `QC/validation/rules/soft.py`
   to `QC/validation/rules/hard.py`**, change `Severity.SOFT` to
   `Severity.HARD`, drop the `count`/`language`/`character` aggregation in
   favour of one Finding per offending element with `location`, update the
   docstring, and regenerate `RULES.md`.

Step 4 lives here rather than in the change that introduced V151 so that
introducing the rule could not fail CI on any branch already in flight.

## Confirmed fine — do not re-litigate

V150 flags these and they are correct. Re-checking them each sweep wastes
review time; they are recorded here so a reviewer can skip them.

| Corpus | Node | base / alternate | Why it flags | Why it is fine |
| --- | --- | --- | --- | --- |
| WakelinTexts | `M S13W1M2` | `nem` / `namen` | overlap 0.50 | The `nem ~ namen` pronoun alternation, documented in the corpus README |
| WakelinTexts | `M S17W1M2` | `nem` / `namen` | overlap 0.50 | Same alternation |
| WakelinTexts | `M S7W1M3` | `am` / `namen` | proportion 2 vs 5 | Same alternation, against a shorter original |
| WakelinTexts | `W S20W1` | `pipangn-epen` / `pipangengne-eben` | overlap 0.57 | A three-way source alternation; both forms long and genuinely related |

## Open judgment calls — UtrechtManuscriptWordList

Neither is obviously right or wrong; both need someone who can consult the
manuscript.

| Node | original / alternate | Question |
| --- | --- | --- |
| `S W118` | `tigpapahoang` / `tigp` | 12 vs 4 characters. Almost certainly a truncated transcription of van der Vlis's reading rather than a real variant — check the 1842 edition. |
| `S W375` | `iit` / `jih` | Three letters each, overlap 0.33. Either a genuine witness difference or two different words; the gloss should settle it. |

## Future — gloss standardization

W/M-level `TRANSL/@kindOf` is the axis a gloss-standardization pass will
use: the source's gloss stays as `kindOf="original"` and a standardized
gloss is added as a separate `kindOf="standard"` TRANSL. GitBook already
documents this. HundredPaiwanStories is the existing precedent.
```

- [ ] **Step 3: Verify the worklist matches the actual findings**

Cross-check every id in the worklist against the findings CSV:

```bash
/workspace/FormosanBank/.venv/bin/python - <<'PY'
import csv, os
worklist = open("claudeplans/2026-09-08-alternate-form-worklist.md").read()
rows = []
with open(os.environ["SCRATCH"] + "/findings.csv") as fh:
    rows = [r for r in csv.DictReader(fh) if r["rule_id"] == "V150"]
print("V150 findings:", len(rows))
missing = [r["location"] for r in rows
           if r["location"].split("=")[-1] not in worklist]
print("in findings but absent from the worklist:", missing)
PY
```

Expected: `V150 findings: 12` and an empty list. Every flagged element must appear somewhere in the worklist — as a defect, a confirmed-fine entry, or an open judgment call. An id in the findings but not the worklist means a reviewer will re-litigate it every sweep; add it before committing.

- [ ] **Step 4: Commit**

```bash
git add claudeplans/2026-09-08-alternate-form-worklist.md
git commit -m "Worklist: Latham cross-lexeme alternates, Glosbe S-level kindOf, V151 HARD promotion"
```

---

### Task 8: Update the GitBook XML-format documentation

**Files:**
- Modify: `../FormosanBankGitbook/en-us/the-bank-architecture/formosanbank-xml-format.md`

**This is a different repository.** It has its own git history and its own branch. Do not commit it in the FormosanBank worktree. The English version is canonical; other languages are out of date and are not updated here.

**Interfaces:** The attribute inventory published here is generated from the same XSD annotations as `ATTRIBUTES.md` (Task 5), so the two cannot drift.

- [ ] **Step 1: Create a branch in the GitBook repo**

```bash
cd ../FormosanBankGitbook
git status --short
git checkout -b docs/xml-attribute-inventory
```

If `git status` shows unrelated uncommitted work, stop and ask — this repo is shared.

- [ ] **Step 2: Fix the TRANSL/@kindOf description**

In `en-us/the-bank-architecture/formosanbank-xml-format.md`, the `<TRANSL>` section currently reads:

```markdown
* `kindOf`: The translation type, method, or provenance. At morpheme level, the validator limits this to `original` or `standard`.
```

That phrasing is an open-ended licence to attach any provenance string to any TRANSL, and is why Glosbe carries 4,157 meaningless S-level uses. Replace it with:

```markdown
* `kindOf`: `original` or `standard`, and **only meaningful at word and morpheme level**, where a `TRANSL` carries a gloss: `original` is the source's own gloss, `standard` a standardized one. It is **forbidden on a sentence-level `TRANSL`** — a free translation has no original-vs-standard axis, so the attribute would carry no information. The validator reports S-level uses (V151) and the schema restricts the value at every level.
```

- [ ] **Step 3: Sharpen the `alternate` description**

In the `<FORM>` section, replace:

```markdown
* `alternate`: A genuine alternate form retained alongside the main tiers.
```

with:

```markdown
* `alternate`: A **spelling variant** of a sibling FORM on the same node — for example a second witness's reading, or a source cell offering two spellings. It must have a non-alternate sibling to vary from, and must either overlap it closely or be short along with it; neither form may be more than twice the length of the other. A competing *word* for the same meaning is not an alternate: per POL-027 that becomes its own `<S>` block. The variation may span the whole form — a one-letter word alternating `a`/`u` is a perfectly good alternate. (Policy POL-028; validator rules V149 HARD and V150 SOFT.)
```

- [ ] **Step 4: Add the attribute inventory section**

Generate the tables from the repo's catalogue rather than retyping them:

```bash
cd /workspace/FormosanBank/.claude/worktrees/alternate-form-standardization
sed -n '/^## `<TEXT>`/,$p' QC/validation/ATTRIBUTES.md > /tmp/claude-1000/-workspace-FormosanBank/83bf3e4c-40a0-4dc5-9249-f21fdec5afdd/scratchpad/attr-tables.md
wc -l /tmp/claude-1000/-workspace-FormosanBank/83bf3e4c-40a0-4dc5-9249-f21fdec5afdd/scratchpad/attr-tables.md
```

Append a new section at the end of `formosanbank-xml-format.md`, before any trailing navigation, introduced by:

```markdown
***

### Every attribute, in one place

The attribute set is **closed**: the schema declares no `anyAttribute`, so an attribute not listed here fails validation. Adding one requires a schema declaration, documentation, a regenerated catalogue, and a policy entry (POL-053) — never ad hoc.

This table is generated from `QC/validation/xml_template.xsd` in the FormosanBank repo, where it is also published as `QC/validation/ATTRIBUTES.md`.
```

then paste the contents of `attr-tables.md` beneath it, demoting each `## ` heading to `#### ` so it nests under this section.

- [ ] **Step 5: Verify the GitBook tests still pass**

```bash
cd ../FormosanBankGitbook
python -m pytest tests/ -q
```

Expected: pass. If `manage_corpus_pages.py`'s linter complains about the new section, follow its message — it governs page structure.

- [ ] **Step 6: Commit in the GitBook repo**

```bash
git add en-us/the-bank-architecture/formosanbank-xml-format.md
git commit -m "Document the full XML attribute inventory; close the TRANSL/@kindOf ad-hoc licence

The kindOf line described the attribute as "the translation type, method,
or provenance", which reads as permission to attach any provenance string
to any TRANSL. Restrict it to original|standard at W/M level only, matching
POL-028/POL-053 and validator rule V151.

Also publishes every allowed attribute, generated from the XSD, so an
attribute legal in the schema can no longer be a validation surprise."
cd /workspace/FormosanBank/.claude/worktrees/alternate-form-standardization
```

---

### Task 9: Full verification sweep

**Files:** None modified. This task proves the end state.

- [ ] **Step 1: Run the full test suite**

```bash
/workspace/FormosanBank/.venv/bin/python -m pytest tests/ -q
```

Expected: all pass, no new failures. If anything unrelated fails, check whether it failed before your changes (`git stash` is unsafe here — use `git worktree` or compare against `main` in a separate checkout).

- [ ] **Step 2: Confirm zero new HARD findings across the bank**

```bash
export SCRATCH=/tmp/claude-1000/-workspace-FormosanBank/83bf3e4c-40a0-4dc5-9249-f21fdec5afdd/scratchpad
/workspace/FormosanBank/.venv/bin/python QC/validation/validate_xml.py \
    by_path --path Corpora --no-exit-on-hard --csv "$SCRATCH/findings.csv" \
    2>&1 | tee "$SCRATCH/sweep.txt" | grep -E "V(149|150|151)|HARD"
```

Expected exactly:
- `V149 alternate_FORM_requires_base_sibling` — absent (zero findings)
- `V150 alternate_FORM_low_overlap: 12`
- `V151 S_TRANSL_has_no_kindOf: 4157`
- No HARD rule that was not already failing before this work.

- [ ] **Step 3: Confirm no published XML was modified**

```bash
git diff --stat main -- Corpora/ | tail -3
```

Expected: no output. This plan changes no corpus data; if anything under `Corpora/` appears, revert it.

- [ ] **Step 4: Confirm both catalogues are current**

```bash
/workspace/FormosanBank/.venv/bin/python QC/validation/rules_catalogue.py --check; echo "RULES.md exit=$?"
/workspace/FormosanBank/.venv/bin/python QC/validation/attributes_catalogue.py --check; echo "ATTRIBUTES.md exit=$?"
```

Expected: both `exit=0`.

- [ ] **Step 5: Review the full diff before opening a PR**

```bash
git diff main --stat
```

Expected files, and no others:
```
POLICIES.md
QC/validation/ATTRIBUTES.md            (new)
QC/validation/RULES.md
QC/validation/attributes_catalogue.py  (new)
QC/validation/rules/hard.py
QC/validation/rules/soft.py
QC/validation/xml_template.xsd
claudeplans/2026-09-08-alternate-form-worklist.md  (new)
docs/superpowers/plans/2026-09-08-alternate-form-standardization.md  (new)
docs/superpowers/specs/2026-09-08-alternate-form-standardization-design.md  (new)
tests/validators/test_alternate_forms.py           (new)
tests/validators/test_attributes_catalogue.py      (new)
tests/validators/test_transl_kindof.py             (new)
tests/validators/test_xsd_annotations.py           (new)
```

- [ ] **Step 6: Open the PR**

Per POL-049 (pull-request scope), this is one coherent change: govern alternates and close the attribute surface. The GitBook change is a separate PR in its own repo (Task 8).

```bash
git push -u origin worktree-alternate-form-standardization
gh pr create --title "Govern alternate FORMs and close the XML attribute surface" --body "$(cat <<'EOF'
Implements `docs/superpowers/specs/2026-09-08-alternate-form-standardization-design.md`.

## What this adds

- **POL-028** — `FORM[@kindOf="alternate"]` is a spelling variant of a sibling FORM: it needs a non-alternate sibling, must overlap it or stay in proportion to it, and a competing lexeme becomes its own `S` block per POL-027. Also fixes the boundary between the two optional-material mechanisms, which was written down nowhere.
- **POL-053** — the XML attribute set is closed and documented. The XSD already rejected undeclared attributes; this names that as a guarantee and adds the documentation half.
- **POL-025 amendment** — the policy claimed the XSD requires `ver` on same-language TRANSLs. It does not and cannot; V085 does.
- **V149 HARD** — an alternate FORM requires a non-alternate sibling. Zero findings; locks in today's clean state.
- **V150 SOFT** — overlap and proportion. 12 findings, triaged in the worklist.
- **V151 SOFT** — S-level TRANSL must not carry `@kindOf`. 4,157 findings, all legacy Glosbe.
- **`ATTRIBUTES.md`**, generated from XSD annotations and CI-guarded, mirroring `RULES.md`.

## What this deliberately does not do

No published XML changes. The two remediation items — Latham's 6 cross-lexeme alternates and Glosbe's 4,157 S-level attributes — are tracked in `claudeplans/2026-09-08-alternate-form-worklist.md`.

**V151 ships SOFT on purpose.** Promoting it to HARD is step 4 of the Glosbe worklist item, so introducing the rule cannot fail CI on branches already in flight.

## Verification

- Full test suite passes.
- Bank-wide sweep: zero new HARD findings, exactly 12 V150, 4,157 V151 confined to Glosbe's three `_tmem.xml` files.
- `git diff main -- Corpora/` is empty.

A companion PR in `FormosanBankGitbook` publishes the attribute inventory and closes the `TRANSL/@kindOf` "type, method, or provenance" wording that produced Glosbe's S-level uses.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Notes for the executor

**If V150 does not report exactly 12**, do not adjust the thresholds to make the number match. The thresholds are fixed by evidence recorded in the spec: overlap 0.6, short exemption 2, proportion factor 2. A different count means the data changed or the implementation is wrong; reconcile against the spec's finding table first.

**If a `_tmem.xml` file has been regenerated** and Glosbe's V151 count is no longer 4,157, that is fine — report the actual number and update the worklist. The count is evidence, not a contract.

**Do not promote V151 to HARD in this plan** even if Glosbe happens to be clean when you run it. That promotion is Task 7's worklist item and belongs to the change that remediates the data.
