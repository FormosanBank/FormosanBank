"""Tests for QC/validation/validate_glosses.py and QC/validation/rules/gloss.py.

Two layers of test:

1. Rule-level: invoke each rule function directly against an in-memory
   lxml tree. Fast, side-effect free, exercises the rule's logic without
   depending on the orchestrator. Used for V060–V065.

2. Orchestrator-level: subprocess-invoke validate_glosses.py against a
   fixture directory. Exercises the CLI surface, CSV outputs, and exit
   semantics (mirrors the test pattern in test_validate_xml.py).
"""
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import pytest
from lxml import etree

from QC.validation.rules import gloss as gloss_rules
from QC.validation._finding import Severity


VALIDATE_GLOSSES = (
    Path(__file__).resolve().parents[2]
    / "QC"
    / "validation"
    / "validate_glosses.py"
)


def _parse(xml: str) -> etree._ElementTree:
    """Parse an inline XML string into an lxml ElementTree."""
    return etree.parse(BytesIO(xml.encode("utf-8")))


def _findings_for(rule, xml: str, path: Path | str = "test.xml"):
    """Run a single rule against the given XML and return its findings.

    The rule signature is (tree, path, index); index is None here
    because gloss rules don't consult the CorpusIndex.
    """
    tree = _parse(xml)
    return rule(tree, Path(path), None)


# Small reusable inline fixture. Use ``_TEXT_TEMPLATE.format(body=...)``
# inside tests for the smallest possible focused XML. Note the doubled
# braces in BibTeX_citation: ``{{t}}`` -> ``{t}`` after str.format.
_TEXT_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<TEXT id="T1" citation="t" BibTeX_citation="@t{{t}}" copyright="t" xml:lang="ami">
{body}
</TEXT>
"""


# ---------------------------------------------------------------------------
# V060: W-count vs. word-count (SOFT)
# ---------------------------------------------------------------------------


def test_V060_matching_W_and_word_count_clean():
    """Clean S: 3 whitespace words and 3 direct W children -> no V060."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
        <W id="W2"><FORM kindOf="original">b</FORM></W>
        <W id="W3"><FORM kindOf="original">c</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert findings == [], f"expected no V060 finding; got {findings!r}"


def test_V060_mismatched_W_and_word_count_emits_SOFT():
    """3 words in FORM but 2 W children -> one SOFT V060 finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
        <W id="W2"><FORM kindOf="original">b</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert len(findings) == 1, f"expected 1 V060 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V060"
    assert f.severity is Severity.SOFT
    assert "S1" in f.location
    assert "3" in f.message and "2" in f.message


def test_V060_uses_original_FORM_in_preference_to_standard():
    """Original tier wins as the word-count source; standard tier ignored."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <FORM kindOf="standard">a b c d e</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
        <W id="W2"><FORM kindOf="original">b</FORM></W>
        <W id="W3"><FORM kindOf="original">c</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert findings == [], (
        f"V060 must use FORM[@kindOf='original'] (3 words) not standard "
        f"(5 words); got {findings!r}"
    )


def test_V060_no_FORM_at_all_emits_nothing():
    """S with no FORM at all: rule no-ops (V010/V013 handle that)."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <W id="W1"><FORM kindOf="original">a</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert findings == [], f"expected no V060 finding; got {findings!r}"


# ---------------------------------------------------------------------------
# V061: M-count vs. implied-morpheme-count (SOFT)
# ---------------------------------------------------------------------------


def test_V061_monomorphemic_with_no_M_clean():
    """W FORM 'ka' (1 morpheme) with 0 M children -> exception, no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ka</FORM>
        <W id="W1"><FORM kindOf="original">ka</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_hyphenated_with_matching_M_clean():
    """W FORM 'ika-doa' (2 morphemes) with 2 M children -> no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ika-doa</FORM>
        <W id="W1">
          <FORM kindOf="original">ika-doa</FORM>
          <M id="M1"><FORM>ika</FORM></M>
          <M id="M2"><FORM>doa</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_infix_with_matching_M_clean():
    """W FORM 'k<um>ita' (infix + root = 2 morphemes) with 2 M -> no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">k&lt;um&gt;ita</FORM>
        <W id="W1">
          <FORM kindOf="original">k&lt;um&gt;ita</FORM>
          <M id="M1"><FORM>-um-</FORM></M>
          <M id="M2"><FORM>kita</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_infix_with_too_few_M_emits_SOFT():
    """W FORM 'k<um>ita' (expected 2) with only 1 M -> SOFT V061."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">k&lt;um&gt;ita</FORM>
        <W id="W1">
          <FORM kindOf="original">k&lt;um&gt;ita</FORM>
          <M id="M1"><FORM>kita</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert len(findings) == 1, f"expected 1 V061 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V061"
    assert f.severity is Severity.SOFT
    assert "W1" in f.location


def test_V061_clitic_boundary_clean():
    """W FORM 'ma=luhay' (= boundary, 2 morphemes) with 2 M -> no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ma=luhay</FORM>
        <W id="W1">
          <FORM kindOf="original">ma=luhay</FORM>
          <M id="M1"><FORM>ma</FORM></M>
          <M id="M2"><FORM>luhay</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_W_with_no_FORM_emits_nothing():
    """W with no FORM at all: rule no-ops (V011 handles missing FORM)."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">x</FORM>
        <W id="W1"></W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


# ---------------------------------------------------------------------------
# V062: infix M needs angle-bracket gloss (HARD)
# Moved from rules/hard.py to rules/gloss.py during B9.3. The pre-move
# fixture files (v062_infix_M_*.xml) are reused.
# ---------------------------------------------------------------------------


def test_V062_infix_M_without_angle_gloss_emits_HARD(fixtures_dir):
    """V062 (negative): infix M FORM lacking angle-bracket gloss -> HARD."""
    xml = (fixtures_dir / "v062_infix_M_without_angle_gloss.xml").read_text(encoding="utf-8")
    findings = _findings_for(gloss_rules.v062_infix_M_needs_angle_gloss, xml)
    assert len(findings) == 1, f"expected 1 V062 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V062"
    assert f.severity is Severity.HARD
    assert "infix" in f.message.lower()


def test_V062_infix_M_with_angle_gloss_emits_nothing(fixtures_dir):
    """V062 (positive): infix M FORM correctly paired with <AV> gloss."""
    xml = (fixtures_dir / "v062_infix_M_with_angle_gloss.xml").read_text(encoding="utf-8")
    findings = _findings_for(gloss_rules.v062_infix_M_needs_angle_gloss, xml)
    assert findings == [], f"expected no V062 finding; got {findings!r}"


def test_V062_non_infix_M_emits_nothing():
    """V062: non-infix-shaped M FORM doesn't trigger the rule."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ka</FORM>
        <W id="W1">
          <FORM kindOf="original">ka</FORM>
          <M id="M1"><FORM>ka</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v062_infix_M_needs_angle_gloss, xml)
    assert findings == [], f"expected no V062 finding; got {findings!r}"
