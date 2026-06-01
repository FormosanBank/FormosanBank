"""Tests for QC/validation/validate_text.py (B9.4).

Pattern mirrors test_validate_xml.py:
- subprocess-invoke validate_text.py via `by_path --path <dir>`
- assert on output content (presence of rule-specific markers)
- `_has_text_finding` requires a rule-specific marker (rule ID or rule
  message phrasing) so that fixture filenames (which encode rule IDs)
  do not accidentally satisfy the assertion.

Rule ID assignments for B9.4 (recorded in commit messages too):
  V110 = TR(W1) smart_quotes in S-standard FORM (SOFT)
  V111 = TR(W1) imbalanced_parens in S-standard FORM (SOFT)
  V112 = TR(W1) repeated_punct in S-standard FORM (SOFT)
  V113 = TR(W1) consecutive_dashes in S-standard FORM (SOFT)
  V114 = TR(W1) multiple_whitespace in S-standard FORM (SOFT)
  V115 = TR(W1) mismatched_quotes in S-standard FORM (SOFT)
  V116 = TR(W2) non_ascii_in_form across all tiers (SOFT)
  V120 = TR1 null symbol in S-level standard FORM (HARD)
  V121 = TR2 parens or '/' in W- or M-level FORM (HARD)
  V122 = TR3 parens or '/' anywhere in FORM/TRANSL (SOFT)
  V123 = TR4 null in W/M std FORM ⇒ also in sister original (HARD)
  V124 = TR5 null in M FORM ⇒ also in parent W FORM AND in
         parent S-level original FORM (HARD)
  V125 = TR6 null in W FORM ⇒ also in some child M FORM AND in
         parent S-level original FORM (HARD)
  V126 = TR7 '=' in S-level standard FORM (SOFT)
"""
import subprocess
import sys
from pathlib import Path

import pytest

from _helpers import combined_output, has_marker


VALIDATE_TEXT = (
    Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_text.py"
)


def _run_validate_text(corpus_xml_dir: Path) -> subprocess.CompletedProcess:
    """Invoke validate_text.py against a directory of XML fixtures.

    SOFT CSV is directed into corpus_xml_dir so this helper never
    pollutes the repo root with a logs/ directory.
    """
    return subprocess.run(
        [
            sys.executable, str(VALIDATE_TEXT),
            "by_path", "--path", str(corpus_xml_dir),
            "--soft-csv", str(corpus_xml_dir / "soft.csv"),
        ],
        capture_output=True,
        text=True,
    )


def _has_text_finding(
    proc: subprocess.CompletedProcess, rule_markers: tuple[str, ...]
) -> bool:
    """Did the validator output mention one of the rule-specific markers?

    The combined output has file paths stripped (so fixture basenames
    don't accidentally satisfy the assertion). We then look for any of
    the supplied markers case-insensitively.
    """
    return has_marker(proc, rule_markers)


def _is_clean(proc: subprocess.CompletedProcess) -> bool:
    """Did the validator report a clean run (no HARD issues)?"""
    combined = combined_output(proc)
    return ("total issues found: 0" in combined) and ("no issues found" in combined)


def _write_xml(path: Path, content: str) -> Path:
    """Write a tiny XML test file. Returns the path written."""
    xml_dir = path / "XML"
    xml_dir.mkdir(parents=True, exist_ok=True)
    f = xml_dir / "test.xml"
    f.write_text(content, encoding="utf-8")
    return f


# Common minimal valid corpus header / footer used by ad-hoc XML fixtures.
_TEXT_OPEN = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="ami">'
)
_TEXT_CLOSE = "</TEXT>"


# -----------------------------------------------------------------------------
# Sanity: a clean minimal XML produces zero HARD findings.
# -----------------------------------------------------------------------------

def test_clean_xml_produces_zero_findings(tmp_path):
    """A clean FORM with ASCII content and balanced punctuation passes."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello world.</FORM>'
        + '<FORM kindOf="standard">hello world.</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _is_clean(proc), (
        f"expected clean run; got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W1: ported validate_punct.py rules
# -----------------------------------------------------------------------------


def test_V110_smart_quotes_in_standard_form(tmp_path):
    """V110 SOFT: smart quotes counted in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig text</FORM>'
        + '<FORM kindOf="standard">‘hello’ “world”.</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(proc, ("v110", "smart_quotes", "smart quote")), (
        f"expected V110 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V111_imbalanced_parens_in_standard_form(tmp_path):
    """V111 SOFT: imbalanced parens in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">(hello world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v111", "imbalanced_parens", "imbalanced paren")
    ), (
        f"expected V111 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V112_repeated_punct_in_standard_form(tmp_path):
    """V112 SOFT: repeated terminal punctuation in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">hello!!</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v112", "repeated_punct", "repeated punct")
    ), (
        f"expected V112 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V113_consecutive_dashes_in_standard_form(tmp_path):
    """V113 SOFT: consecutive dashes in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">hello--world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v113", "consecutive_dashes", "consecutive dash")
    ), (
        f"expected V113 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V114_multiple_whitespace_in_standard_form(tmp_path):
    """V114 SOFT: multiple consecutive spaces in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">hello   world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v114", "multiple_whitespace", "multiple whitespace")
    ), (
        f"expected V114 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V115_mismatched_quotes_in_standard_form(tmp_path):
    """V115 SOFT: mismatched smart quote pairs in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">“hello world.</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v115", "mismatched_quotes", "mismatched quote")
    ), (
        f"expected V115 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_W1_rules_only_check_standard_tier(tmp_path):
    """W1 rules (V110-V115) check S-level standard FORM only.

    Smart quotes in the original tier (only) should not trigger V110;
    the original tier is meant to preserve the source's punctuation
    choices verbatim.
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">“hello”</FORM>'
        + '<FORM kindOf="standard">hello.</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v110" not in combined, (
        f"V110 should not flag smart quotes in original tier; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W2: ported non_ascii_counts.py rule
# -----------------------------------------------------------------------------


def test_V116_non_ascii_in_form(tmp_path):
    """V116 SOFT: non-ASCII characters (excluding CJK) in any FORM tier."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">café</FORM>'
        + '<FORM kindOf="standard">cafe</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(proc, ("v116", "non_ascii", "non-ascii")), (
        f"expected V116 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V116_chinese_characters_are_excluded(tmp_path):
    """V116 excludes CJK characters (preserves non_ascii_counts behavior)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">你好</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v116" not in combined, (
        f"V116 should exclude CJK; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V116_scans_all_FORM_tiers(tmp_path):
    """V116 walks every FORM (not just standard) — matches non_ascii_counts."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">café</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(proc, ("v116", "non_ascii", "non-ascii")), (
        f"expected V116 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W4: TR1 — null symbol in S-level standard FORM (HARD)
# -----------------------------------------------------------------------------


def test_V120_null_in_S_standard_FORM_negative(tmp_path):
    """V120 HARD: null symbol in S-level standard FORM is forbidden.

    Null symbol is U+2205 EMPTY SET ('∅').
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">hello ∅ world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v120", "null symbol", "null in s-level", "null in s standard")
    ), (
        f"expected V120 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V120_null_in_original_tier_does_not_trigger(tmp_path):
    """V120: null in original tier is allowed (rule targets standard only)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v120" not in combined, (
        f"V120 should not flag original tier; stdout={proc.stdout!r}"
    )


def test_V120_null_in_W_level_FORM_does_not_trigger_V120(tmp_path):
    """V120: null in W-level FORM only (not S-level) is allowed by V120.

    W-level null is governed by TR4/TR5/TR6 propagation rules, not TR1.
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">stdtext</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v120" not in combined, (
        f"V120 should not flag W-level null; stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# W5: TR2 (parens/slashes in W/M FORM, HARD) + TR3 (parens/slashes anywhere SOFT)
# -----------------------------------------------------------------------------


def test_V121_parens_in_W_FORM_negative(tmp_path):
    """V121 HARD: parens in W-level FORM is forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">stdtext</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">(hello)</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v121", "parens in w", "parens in m", "paren in w/m", "slash in w/m")
    ), (
        f"expected V121 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V121_slash_in_M_FORM_negative(tmp_path):
    """V121 HARD: forward slash in M-level FORM is forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">stdtext</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">a/b</FORM>'
        + '<FORM kindOf="standard">a</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v121", "parens in w", "parens in m", "paren in w/m", "slash in w/m")
    ), (
        f"expected V121 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V122_parens_in_S_standard_FORM_soft(tmp_path):
    """V122 SOFT: parens in S-level standard FORM are flagged (TR3, SOFT)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">hello (world)</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v122", "paren or slash", "parens or slash")
    ), (
        f"expected V122 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V122_slash_in_TRANSL_soft(tmp_path):
    """V122 SOFT: forward slash in TRANSL is flagged (TR3 covers FORM AND TRANSL)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">stdtext</FORM>'
        + '<TRANSL xml:lang="eng">apple/orange</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v122", "paren or slash", "parens or slash")
    ), (
        f"expected V122 finding for / in TRANSL; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W6: TR4 — null in W/M standard FORM ⇒ also in sister original FORM (HARD)
# -----------------------------------------------------------------------------


def test_V123_W_null_in_standard_not_in_original_negative(tmp_path):
    """V123 HARD: W standard FORM has null but original FORM does not."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v123", "null in", "sister original", "null propagation")
    ), (
        f"expected V123 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V123_M_null_in_standard_and_original_OK(tmp_path):
    """V123: M with null in BOTH standard and original is OK."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig ∅</FORM>'
        + '<FORM kindOf="standard">std ∅</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    # V123 specifically should not fire — original has null too.
    assert "v123" not in combined, (
        f"V123 should not fire when both tiers have null; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W7: TR5 — null in M FORM ⇒ also in parent W FORM AND in S-level original (HARD)
# -----------------------------------------------------------------------------


def test_V124_M_null_not_in_parent_W_negative(tmp_path):
    """V124 HARD: M FORM has null but parent W FORM does not."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig ∅</FORM>'
        + '<FORM kindOf="standard">std ∅</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v124", "m null", "null in m", "parent w", "m-level null")
    ), (
        f"expected V124 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V124_M_null_not_in_S_original_negative(tmp_path):
    """V124 HARD: M FORM has null and parent W FORM has null but S original does not."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">hello ∅</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v124", "m null", "null in m", "s-level original", "m-level null")
    ), (
        f"expected V124 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V124_M_null_fully_propagated_OK(tmp_path):
    """V124 OK: null in M, parent W, AND S-level original is fine."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig ∅ abc</FORM>'
        + '<FORM kindOf="standard">std ∅ abc</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</M>'
        + '</W>'
        + '<W id="W2">'
        + '<FORM kindOf="original">abc</FORM>'
        + '<FORM kindOf="standard">abc</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v124" not in combined, (
        f"V124 should not fire when null is fully propagated; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W8: TR6 — null in W FORM ⇒ also in SOME child M FORM AND in S-original (HARD)
# -----------------------------------------------------------------------------


def test_V125_W_null_no_child_M_null_negative(tmp_path):
    """V125 HARD: W FORM has null but no child M FORM has null."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig ∅</FORM>'
        + '<FORM kindOf="standard">std ∅</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">a</FORM>'
        + '<FORM kindOf="standard">a</FORM>'
        + '</M>'
        + '<M id="M2">'
        + '<FORM kindOf="original">b</FORM>'
        + '<FORM kindOf="standard">b</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v125", "w null", "null in w", "w-level null", "child m")
    ), (
        f"expected V125 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V125_W_null_not_in_S_original_negative(tmp_path):
    """V125 HARD: W FORM has null, a child M has null, but S original does not."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">std ∅</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v125", "w null", "null in w", "w-level null", "s-level original")
    ), (
        f"expected V125 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V125_W_null_fully_propagated_OK(tmp_path):
    """V125 OK: W null with a child M null and S-level original null."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">a ∅ b</FORM>'
        + '<FORM kindOf="standard">a ∅ b</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v125" not in combined, (
        f"V125 should not fire when fully propagated; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W9: TR7 — `=` in S-level standard FORM (SOFT)
# -----------------------------------------------------------------------------


def test_V126_equal_sign_in_S_standard_FORM_soft(tmp_path):
    """V126 SOFT: '=' in S-level standard FORM (leftover clitic marker)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">ma=luhay</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v126", "equal sign", "clitic", "= in")
    ), (
        f"expected V126 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V126_equal_sign_in_original_does_not_trigger(tmp_path):
    """V126: '=' in original tier is fine (preserves source)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">ma=luhay</FORM>'
        + '<FORM kindOf="standard">maluhay</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v126" not in combined, (
        f"V126 should not fire on original tier; stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# W10: brainstorm-derived rules (V127-V139)
# -----------------------------------------------------------------------------


# TR8 V127 HARD — smart quotes (curly + Chinese full-width) in either FORM tier.

def test_V127_curly_single_quote_in_standard_FORM_negative(tmp_path):
    """V127 HARD: U+2019 RIGHT SINGLE QUOTATION MARK in standard FORM is forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">it’s</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v127", "smart quote", "non-ascii quote")
    ), (
        f"expected V127 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V127_curly_double_quote_in_original_FORM_negative(tmp_path):
    """V127 HARD: U+201C/U+201D in ORIGINAL FORM is also forbidden (TR8 spans both tiers)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">“hello”</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v127", "smart quote", "non-ascii quote")
    ), (
        f"expected V127 finding for original tier; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V127_chinese_brackets_in_FORM_negative(tmp_path):
    """V127 HARD: Chinese full-width quote brackets in FORM are forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">「hello」</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v127", "smart quote", "non-ascii quote")
    ), (
        f"expected V127 finding for Chinese brackets; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V127_ascii_apostrophe_and_quote_OK(tmp_path):
    """V127 OK: ASCII straight apostrophe U+0027 and quote U+0022 are allowed."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">it\'s "ok"</FORM>'
        + '<FORM kindOf="standard">it\'s "ok"</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v127" not in combined, (
        f"V127 should not fire on ASCII quotes; stdout={proc.stdout!r}"
    )


def test_V127_curly_quote_in_TRANSL_does_not_trigger(tmp_path):
    """V127 scope is FORM only (per plan). TRANSL is not flagged here.

    Different non-ASCII-content rules (e.g. V132) may flag TRANSL text.
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<TRANSL xml:lang="eng">it’s fine</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v127" not in combined, (
        f"V127 should not fire on TRANSL; stdout={proc.stdout!r}"
    )


# TR10 V128 HARD — control characters (codepoint < 0x20) other than \t \n \r.
#
# C0 controls are forbidden in XML 1.0; XML 1.1 permits them only via
# numeric character references, and lxml/libxml2 still refuses to load
# the characters into the tree (the C-API setter raises). The rule
# remains defensive — it scans element.text for disallowed C0 control
# chars — but in practice can only be exercised at the helper level.
#
# V128 is unit-tested at the helper level rather than via the
# subprocess+file path because both well-formed XML 1.0 / XML 1.1 parsers
# AND lxml's own API refuse to load or hold most C0 control characters
# (the `_setNodeText` C-API path raises ValueError). The rule is
# implemented defensively — if upstream data ever leaks through, the
# HARD finding will fire — but the only realistic test target is the
# string-scanning helper. The end-to-end OK path is exercised via the
# subprocess so the "clean run produces zero findings" invariant holds.


def test_V128_detects_vertical_tab_in_text():
    """V128 HARD: U+000B (vertical tab) is flagged by the helper."""
    from QC.validation.rules.text import _disallowed_control_chars

    assert _disallowed_control_chars("hi\x0bthere") == frozenset(["\x0b"])


def test_V128_detects_form_feed_and_null():
    """V128 HARD: U+000C (form feed) and U+0000 (NUL) are both flagged."""
    from QC.validation.rules.text import _disallowed_control_chars

    assert "\x0c" in _disallowed_control_chars("a\x0cb")
    assert "\x00" in _disallowed_control_chars("a\x00b")


def test_V128_allows_tab_newline_carriage_return_at_helper_level():
    """V128: \\t \\n \\r are explicitly allowed."""
    from QC.validation.rules.text import _disallowed_control_chars

    assert _disallowed_control_chars("hi\tthere\nfriend\r\n") == frozenset()


def test_V128_clean_form_does_not_trigger(tmp_path):
    """V128 OK: end-to-end clean run produces no V128 finding."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hi\tthere</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v128" not in combined, (
        f"V128 should not fire on clean input; stdout={proc.stdout!r}"
    )


# TR11 V129 HARD — '*' in standard-tier FORM.

def test_V129_asterisk_in_S_standard_FORM_negative(tmp_path):
    """V129 HARD: '*' in S-level standard FORM is forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">*ungrammatical</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v129", "asterisk", "* in")
    ), (
        f"expected V129 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V129_asterisk_in_W_standard_FORM_negative(tmp_path):
    """V129 HARD: '*' in W-level standard FORM is forbidden (any tier=standard)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">stdsentence</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">word</FORM>'
        + '<FORM kindOf="standard">*word</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v129", "asterisk", "* in")
    ), (
        f"expected V129 finding for W-level standard; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V129_asterisk_in_original_does_not_trigger(tmp_path):
    """V129: '*' in ORIGINAL tier is preserved (rule targets standard only)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">*ungrammatical</FORM>'
        + '<FORM kindOf="standard">ungrammatical</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v129" not in combined, (
        f"V129 should not fire on original tier; stdout={proc.stdout!r}"
    )


# TR15 V130 HARD — leading/trailing whitespace in any FORM.

def test_V130_leading_whitespace_in_FORM_negative(tmp_path):
    """V130 HARD: leading space in S-standard FORM is forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard"> hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v130", "leading", "trailing", "whitespace")
    ), (
        f"expected V130 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V130_trailing_whitespace_in_FORM_negative(tmp_path):
    """V130 HARD: trailing space in S-original FORM is forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello </FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v130", "leading", "trailing", "whitespace")
    ), (
        f"expected V130 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V130_W_level_leading_whitespace_negative(tmp_path):
    """V130 HARD: leading whitespace in W-level FORM is forbidden too."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original"> word</FORM>'
        + '<FORM kindOf="standard">word</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v130", "leading", "trailing", "whitespace")
    ), (
        f"expected V130 finding for W-level; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V130_inner_whitespace_OK(tmp_path):
    """V130: whitespace inside the FORM (not at edges) is fine."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello world</FORM>'
        + '<FORM kindOf="standard">hello world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v130" not in combined, (
        f"V130 should not fire on inner whitespace; stdout={proc.stdout!r}"
    )


def test_V130_empty_FORM_OK(tmp_path):
    """V130: empty FORM is not flagged by the whitespace rule."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original"></FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v130" not in combined, (
        f"V130 should not fire on empty FORM; stdout={proc.stdout!r}"
    )


# TR16 V131 HARD — zero-width / BOM (U+200B U+200C U+200D U+FEFF) in
# FORM or TRANSL, anywhere.

def test_V131_ZWSP_in_FORM_negative(tmp_path):
    """V131 HARD: U+200B ZERO WIDTH SPACE inside FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">hello​world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v131", "zero-width", "zero width", "bom")
    ), (
        f"expected V131 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V131_BOM_at_FORM_start_negative(tmp_path):
    """V131 HARD: U+FEFF BOM at the start of a FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">﻿hello</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v131", "zero-width", "zero width", "bom")
    ), (
        f"expected V131 BOM finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V131_ZWNJ_in_TRANSL_negative(tmp_path):
    """V131 HARD: U+200C ZWNJ inside TRANSL."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<TRANSL xml:lang="eng">hi‌there</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v131", "zero-width", "zero width", "bom")
    ), (
        f"expected V131 finding in TRANSL; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V131_ZWJ_in_FORM_negative(tmp_path):
    """V131 HARD: U+200D ZWJ inside FORM is also forbidden."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">a‍b</FORM>'
        + '<FORM kindOf="standard">ab</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v131", "zero-width", "zero width", "bom")
    ), (
        f"expected V131 ZWJ finding; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V131_clean_FORM_OK(tmp_path):
    """V131 OK: ordinary ASCII content has no zero-width chars."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello world</FORM>'
        + '<FORM kindOf="standard">hello world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v131" not in combined, (
        f"V131 should not fire on clean text; stdout={proc.stdout!r}"
    )


# TR9 V132 SOFT — HTML entities in FORM/TRANSL after XML parse.
#
# The XML parser decodes well-formed XML entities (so `&amp;` in source
# becomes `&` in element.text). After parse, finding a literal `&amp;`
# substring in element.text implies the source contained `&amp;amp;`
# (double-encoded) — typical scrape residue from `html.escape(html_text)`
# being applied to already-escaped HTML. Same for `&apos;` `&lt;` `&gt;`.

def test_V132_double_encoded_amp_in_FORM_soft(tmp_path):
    """V132 SOFT: double-encoded `&amp;amp;` ⇒ post-parse `&amp;` in text."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">a &amp;amp; b</FORM>'
        + '<FORM kindOf="standard">a &amp;amp; b</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v132", "html entity", "html entities")
    ), (
        f"expected V132 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V132_double_encoded_lt_in_TRANSL_soft(tmp_path):
    """V132 SOFT: `&amp;lt;` in TRANSL ⇒ post-parse `&lt;`."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<TRANSL xml:lang="eng">a &amp;lt; b</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v132", "html entity", "html entities")
    ), (
        f"expected V132 finding in TRANSL; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V132_plain_ampersand_does_not_trigger(tmp_path):
    """V132: a plain `&` (entered as `&amp;` and decoded by parser) is fine."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">a &amp; b</FORM>'
        + '<FORM kindOf="standard">a &amp; b</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v132" not in combined, (
        f"V132 should not fire on a plain ampersand; "
        f"stdout={proc.stdout!r}"
    )


def test_V132_clean_text_OK(tmp_path):
    """V132 OK: ordinary clean text has no entity-looking substrings."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello world</FORM>'
        + '<FORM kindOf="standard">hello world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v132" not in combined, (
        f"V132 should not fire on clean text; stdout={proc.stdout!r}"
    )
