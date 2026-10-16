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
