"""Tests for QC/xml_forms.py — shared FORM selection.

POL-028 (revised 2026-09-09) made a tier a *base* FORM (no ``ver``) plus
zero or more ``ver="alt"`` variants. Every consumer that wants "this
node's text" wants the base: a variant is a secondary reading, and
picking one silently substitutes it for the canonical form.

``ElementTree.find`` returns the first match in *document order*, so
every ``find("FORM[@kindOf='original']")` in the bank was one
variant-first node away from selecting a variant. This module is the
single place that knows the base/variant distinction; these tests pin
the two rules that matter:

1. A base is selected by identity (no ``ver``), never by position.
2. A tier carrying variants but no base has no base — the helper says
   so rather than substituting a variant (maintainer ruling 2026-09-10).
   V149 (HARD) already owns that shape; nothing else should paper over
   it.
"""
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from QC.xml_forms import base_form_text, find_base_form, iter_base_forms  # noqa: E402


def _node(xml: str, parser):
    """Parse one node with ElementTree or lxml, so both are covered."""
    return parser(xml)


PARSERS = pytest.mark.parametrize(
    "parse",
    [ET.fromstring, etree.fromstring],
    ids=["elementtree", "lxml"],
)


@PARSERS
def test_base_is_found_when_a_variant_precedes_it(parse):
    """The bug this module exists to prevent: base chosen by ver, not order."""
    node = _node(
        '<S id="1">'
        '<FORM kindOf="original" ver="alt">áku</FORM>'
        '<FORM kindOf="original">náku</FORM>'
        "</S>",
        parse,
    )
    assert find_base_form(node, "original").text == "náku"


@PARSERS
def test_base_is_found_when_it_precedes_its_variant(parse):
    node = _node(
        '<S id="1">'
        '<FORM kindOf="original">náku</FORM>'
        '<FORM kindOf="original" ver="alt">áku</FORM>'
        "</S>",
        parse,
    )
    assert find_base_form(node, "original").text == "náku"


@PARSERS
def test_a_tier_with_only_variants_has_no_base(parse):
    """Maintainer ruling 2026-09-10: strict. V149 HARD owns this shape."""
    node = _node(
        '<S id="1"><FORM kindOf="original" ver="alt">áku</FORM></S>',
        parse,
    )
    assert find_base_form(node, "original") is None
    assert base_form_text(node, "original") == ""


@PARSERS
def test_kind_is_respected(parse):
    node = _node(
        '<S id="1">'
        '<FORM kindOf="original">náku</FORM>'
        '<FORM kindOf="standard">naku</FORM>'
        "</S>",
        parse,
    )
    assert find_base_form(node, "standard").text == "naku"
    assert find_base_form(node, "original").text == "náku"


@PARSERS
def test_without_a_kind_the_first_base_of_any_kind_wins(parse):
    node = _node(
        '<S id="1">'
        '<FORM kindOf="original" ver="alt">áku</FORM>'
        '<FORM kindOf="standard">naku</FORM>'
        "</S>",
        parse,
    )
    assert find_base_form(node).text == "naku"


@PARSERS
def test_only_direct_children_are_considered(parse):
    """A W's lookup must never reach down into its M's FORM."""
    node = _node(
        '<W id="W1">'
        "<M id=\"W1M1\"><FORM kindOf=\"original\">ma</FORM></M>"
        "</W>",
        parse,
    )
    assert find_base_form(node, "original") is None
    assert list(iter_base_forms(node, "original")) == []


@PARSERS
def test_iter_returns_every_base_in_document_order(parse):
    node = _node(
        '<S id="1">'
        '<FORM kindOf="original">a</FORM>'
        '<FORM kindOf="original" ver="alt">b</FORM>'
        '<FORM kindOf="standard">c</FORM>'
        "</S>",
        parse,
    )
    assert [f.text for f in iter_base_forms(node)] == ["a", "c"]


@PARSERS
def test_base_form_text_collects_mixed_content(parse):
    """UNCLEAR is an element child; its tail text belongs to the FORM."""
    node = _node(
        '<S id="1">'
        '<FORM kindOf="original">ina <UNCLEAR/> wawa</FORM>'
        "</S>",
        parse,
    )
    assert base_form_text(node, "original") == "ina  wawa"


@PARSERS
def test_legacy_alternate_kindof_is_not_a_base_of_any_tier(parse):
    """kindOf="alternate" (deprecated, V157) names no tier, so asking for
    an original base must not return it."""
    node = _node(
        '<S id="1"><FORM kindOf="alternate">áku</FORM></S>',
        parse,
    )
    assert find_base_form(node, "original") is None
