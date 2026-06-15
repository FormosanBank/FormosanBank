"""Unit tests for QC/cleaning/manual_edits_common.py (pure helpers)."""
import sys
from pathlib import Path

from lxml import etree

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.cleaning import manual_edits_common as mec


def _s(xml: str) -> etree._Element:
    return etree.fromstring(xml)


def test_strip_s_removes_standard_forms_at_all_levels():
    s = _s(
        '<S id="x">'
        '<FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM>'
        '<W id="x1"><FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM></W>'
        "</S>"
    )
    out = mec.strip_s(s)
    kinds = [f.get("kindOf") for f in out.findall(".//FORM")]
    assert kinds == ["original", "original"]


def test_strip_s_removes_all_phon():
    s = _s(
        '<S id="x"><FORM kindOf="original">a</FORM>'
        '<PHON kindOf="original">a</PHON>'
        '<W id="x1"><PHON kindOf="original">a</PHON></W></S>'
    )
    out = mec.strip_s(s)
    assert out.findall(".//PHON") == []


def test_strip_s_drops_after_and_action_attrs():
    s = _s('<S id="x" after="w" action="delete"><FORM kindOf="original">a</FORM></S>')
    out = mec.strip_s(s)
    assert "after" not in out.attrib
    assert "action" not in out.attrib


def test_strip_s_does_not_mutate_input():
    s = _s('<S id="x"><FORM kindOf="standard">A</FORM></S>')
    mec.strip_s(s)
    assert s.findall(".//FORM") != []  # original element untouched


def test_canonical_s_ignores_standard_phon_and_whitespace():
    a = _s('<S id="x">\n  <FORM kindOf="original">a</FORM>\n</S>')
    b = _s(
        '<S id="x"><FORM kindOf="original">a</FORM>'
        '<FORM kindOf="standard">A</FORM><PHON kindOf="original">a</PHON></S>'
    )
    assert mec.canonical_s(a) == mec.canonical_s(b)


def test_canonical_s_distinguishes_different_original_text():
    a = _s('<S id="x"><FORM kindOf="original">a</FORM></S>')
    b = _s('<S id="x"><FORM kindOf="original">b</FORM></S>')
    assert mec.canonical_s(a) != mec.canonical_s(b)


def test_render_s_shows_original_form_and_translations():
    s = _s(
        '<S id="x"><FORM kindOf="original">hala</FORM>'
        '<TRANSL xml:lang="zho">你好</TRANSL></S>'
    )
    out = mec.render_s(s)
    assert "hala" in out and "你好" in out


def test_default_manual_file_is_codeanddocs_sibling(tmp_path):
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir()
    got = mec.default_manual_file(xml_dir)
    assert got == (tmp_path / "CodeAndDocs" / "manual_edits.xml")


def test_changelog_path_swaps_suffix(tmp_path):
    assert mec.changelog_path(tmp_path / "CodeAndDocs" / "manual_edits.xml") == (
        tmp_path / "CodeAndDocs" / "manual_edits.md"
    )
