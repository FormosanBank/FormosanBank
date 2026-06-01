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
