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
