"""prettify() must be idempotent over mixed content.

Regression for the 2026-08-11 WilangYutas finding: the old line-based
leading-space rewrite doubled *content* whitespace that started a line
(e.g. the tail of an inline <UNCLEAR/>) on every run, so the pipeline had
no byte-level fixed point.
"""
import importlib.util
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_spec = importlib.util.spec_from_file_location(
    "standardize", _REPO / "QC" / "utilities" / "standardize.py")
standardize = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(standardize)

MIXED = ('<TEXT id="t"><S id="1">'
         '<FORM kindOf="original">before <UNCLEAR/>\n     after</FORM>'
         '</S></TEXT>')


def _strip_decl(s: str) -> str:
    return s.split("\n", 1)[1]


def test_prettify_is_idempotent_over_inline_unclear():
    once = standardize.prettify(ET.fromstring(MIXED))
    twice = standardize.prettify(ET.fromstring(_strip_decl(once)))
    assert once == twice


def test_prettify_preserves_mixed_content_whitespace():
    out = standardize.prettify(ET.fromstring(MIXED))
    # The content whitespace around <UNCLEAR/> must survive verbatim.
    assert "before <UNCLEAR/>\n     after" in out


def test_prettify_indents_structural_lines_four_spaces():
    out = standardize.prettify(ET.fromstring(MIXED))
    assert '\n    <S id="1">' in out
