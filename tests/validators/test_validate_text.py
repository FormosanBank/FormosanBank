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
from io import BytesIO
from pathlib import Path

import pytest
from lxml import etree

from _helpers import combined_output, has_marker
from QC.validation._finding import Severity
from QC.validation.rules import text as text_rules


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


def test_soft_csv_rows_have_location_and_line(tmp_path):
    """SOFT CSV rows must include the offending element's id (location)
    and source line number, so the user can jump directly to the issue.

    Added 2026-06-01 per Joshua's request: the SOFT stderr summary is
    aggregated, so the CSV is the authoritative per-occurrence record.
    Without location + line, the CSV says "file X has 4 V116 findings"
    but not where to look.
    """
    import csv as _csv

    xml = (
        _TEXT_OPEN
        + '<S id="S_target">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">café</FORM>'  # 'é' triggers V116
        + '</S>'
        + _TEXT_CLOSE
    )
    written_path = _write_xml(tmp_path, xml)
    soft_csv = tmp_path / "loc_line.csv"
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATE_TEXT),
            "by_path", "--path", str(tmp_path / "XML"),
            "--soft-csv", str(soft_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert soft_csv.exists(), (
        f"CSV missing; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    with open(soft_csv, newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    v116_rows = [r for r in rows if r["rule_id"] == "V116"]
    assert v116_rows, f"expected V116 row in CSV; rows={rows!r}"
    row = v116_rows[0]
    assert row["location"], (
        f"V116 row missing 'location'; row={row!r}"
    )
    assert row["line"].isdigit() and int(row["line"]) > 0, (
        f"V116 row missing valid 'line'; row={row!r}"
    )
    # And the S id should be discoverable in the location field.
    assert "S_target" in row["location"], (
        f"expected S_target in location; got {row['location']!r}"
    )


def test_soft_csv_path_is_announced(tmp_path):
    """validate_text.py must print the SOFT-CSV output path so users can
    find the aggregated per-character SOFT data after a run.

    Stderr summary lists SOFT findings without per-element locations
    (aggregation is by design — see Finding docstring), so the CSV is
    the primary place to look up details. Silently writing the CSV
    leaves the user guessing where the file went.
    """
    # XML guaranteed to produce a SOFT finding (V126: '=' in S-standard).
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">a=b</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    soft_csv = tmp_path / "explicit_soft.csv"
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATE_TEXT),
            "by_path", "--path", str(tmp_path / "XML"),
            "--soft-csv", str(soft_csv),
        ],
        capture_output=True,
        text=True,
    )
    combined = proc.stdout + proc.stderr
    assert str(soft_csv) in combined, (
        f"expected SOFT CSV path {soft_csv!s} in script output; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
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


# Helper for V116 orthography-exclusion tests: build a fixture XML with a
# specified xml:lang so we can exercise per-language letter exclusion.
def _xml_with_lang_and_form(lang: str, form_text: str) -> str:
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<TEXT id="T1" citation="t" BibTeX_citation="@t{{t}}" '
        f'copyright="t" xml:lang="{lang}">'
        '<S id="S1">'
        f'<FORM kindOf="original">{form_text}</FORM>'
        f'<FORM kindOf="standard">{form_text}</FORM>'
        '</S>'
        + _TEXT_CLOSE
    )


def test_V116_excludes_chars_from_matching_language_orthography(tmp_path):
    """V116: 'ṟ' (Atayal orthography letter) in a tay-tagged file is excluded.

    'ṟ' (U+1E5F) appears in the first column of Orthographies/Ortho113/Atayal.tsv.
    A file whose TEXT/@xml:lang is 'tay' (Atayal ISO 639-3) should not have
    'ṟ' flagged by V116, because the letter is part of the language's
    legitimate orthography.
    """
    xml = _xml_with_lang_and_form("tay", "kaṟal")
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v116" not in combined, (
        f"V116 should exclude 'ṟ' for tay (Atayal); "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V116_still_triggers_for_chars_only_in_other_languages_orthography(tmp_path):
    """V116: 'ʉ' (Kanakanavu / Tsou / Saaroa letter) is NOT in Atayal orthography
    and should still be flagged in a tay-tagged file."""
    xml = _xml_with_lang_and_form("tay", "kʉal")
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(proc, ("v116", "non_ascii", "non-ascii")), (
        f"expected V116 finding for 'ʉ' in tay file; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V116_excludes_chars_from_any_orthography_subdir(tmp_path):
    """V116: pools first-column letters across ALL Orthographies/*/ TSVs.

    'ř' (U+0159) for Amis only appears in Orthographies/Montgomery/Amis.tsv,
    not Ortho113 or Ortho94. The rule must pool across orthography subdirs.
    """
    xml = _xml_with_lang_and_form("ami", "ŕaři")
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    # 'ŕ' (U+0155) is NOT in any Amis orthography; should still trigger.
    assert _has_text_finding(proc, ("v116", "non_ascii", "non-ascii")), (
        f"V116 should trigger for 'ŕ' (not in Amis orthography); "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    # 'ř' is in Montgomery/Amis.tsv — only the 'ŕ' finding should appear,
    # not a separate finding citing 'ř'.
    assert "u+0159" not in combined and "'ř'" not in combined, (
        f"V116 should exclude 'ř' (in Montgomery/Amis.tsv); "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V116_unknown_xml_lang_falls_back_to_legacy_behavior(tmp_path):
    """V116: when xml:lang is an unknown / unmapped code, no orthography
    exclusion is applied and V116 behaves as it did pre-enhancement."""
    xml = _xml_with_lang_and_form("xyz", "café")
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(proc, ("v116", "non_ascii", "non-ascii")), (
        f"V116 should still trigger for unknown xml:lang; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
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
# V140: null in S-original FORM must propagate DOWN to at least one W AND
# that W must have at least one M FORM with null (HARD).
# Converse of V125 (which propagates UP). Added 2026-06-01.
# -----------------------------------------------------------------------------


def test_V140_S_original_null_not_in_any_W_negative(tmp_path):
    """V140 HARD: S-original has ∅ but no W FORM contains ∅."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">∅ sua</FORM>'
        + '<FORM kindOf="standard">sua</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">sua</FORM>'
        + '<FORM kindOf="standard">sua</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">sua</FORM>'
        + '<FORM kindOf="standard">sua</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v140", "s-original null", "s original null", "null in s-original")
    ), (
        f"expected V140 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V140_S_original_null_in_W_but_not_in_M_negative(tmp_path):
    """V140 HARD: a W FORM has ∅ but that W's Ms have no ∅."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">∅ sua</FORM>'
        + '<FORM kindOf="standard">sua</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">∅</FORM>'
        + '<FORM kindOf="standard">∅</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">a</FORM>'
        + '<FORM kindOf="standard">a</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v140", "s-original null", "s original null", "null in s-original")
    ), (
        f"expected V140 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V140_S_original_null_fully_propagated_OK(tmp_path):
    """V140 OK: a W has ∅ AND that W has a child M with ∅."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">∅ sua</FORM>'
        + '<FORM kindOf="standard">sua</FORM>'
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
    assert "v140" not in combined, (
        f"V140 should not fire when fully propagated; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V140_no_null_in_S_original_no_ops(tmp_path):
    """V140: S-original has no ∅ -> rule never fires."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v140" not in combined, (
        f"V140 should not fire when S-original has no ∅; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V140_S_with_no_W_children_no_ops(tmp_path):
    """V140: S has ∅ but no W children at all (unsegmented S) -> rule no-ops.

    Mirrors V063's no-segmentation no-op semantics: when no tokenization
    tier exists, the propagation rule has nothing to check against.
    Catching unsegmented S elements is V060's job, not V140's.
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">∅ sua</FORM>'
        + '<FORM kindOf="standard">sua</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v140" not in combined, (
        f"V140 should no-op on unsegmented S; "
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


def test_V129_asterisk_in_original_FORM_negative(tmp_path):
    """V129 HARD: '*' in ORIGINAL tier is also forbidden (policy change 2026-06-01).

    The original tier was previously allowed to preserve source-text
    metalinguistic markers, but Joshua's call: asterisks in FormosanBank
    corpora are project artifacts, not faithful source-text preservation,
    so the rule applies in both tiers.
    """
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
    assert _has_text_finding(
        proc, ("v129", "asterisk", "* in")
    ), (
        f"expected V129 finding on original tier; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
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


# TR12 V133 SOFT — '-' (segmentation marker) in S-level standard FORM.

def test_V133_dash_in_S_standard_FORM_soft(tmp_path):
    """V133 SOFT: '-' in S-level standard FORM (segmentation leftover)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">ma-luhay</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v133", "dash in s", "segmentation", "- in")
    ), (
        f"expected V133 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V133_dash_in_S_original_does_not_trigger(tmp_path):
    """V133: '-' in S-original tier is preserved (source) — not flagged."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">ma-luhay</FORM>'
        + '<FORM kindOf="standard">maluhay</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v133" not in combined, (
        f"V133 should not fire on original tier; stdout={proc.stdout!r}"
    )


def test_V133_dash_in_W_standard_does_not_trigger(tmp_path):
    """V133: '-' in W-level standard FORM is permitted by V133.

    V133 targets S-level standard only; morpheme boundaries inside W are
    not in scope.
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">maluhay</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">ma-luhay</FORM>'
        + '<FORM kindOf="standard">ma-luhay</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v133" not in combined, (
        f"V133 should not fire on W-level dash; stdout={proc.stdout!r}"
    )


# TR13 V134 SOFT — '<' or '>' (infix delimiter) in S-level FORM either tier.
#
# In XML source these are written as `&lt;` and `&gt;`; the parser
# decodes them, so we look for literal '<' or '>' in S-level FORM.text.

def test_V134_lt_in_S_standard_FORM_soft(tmp_path):
    """V134 SOFT: '<' in S-level standard FORM."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">a&lt;b</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v134", "infix", "angle bracket", "&lt;", "< or >")
    ), (
        f"expected V134 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V134_gt_in_S_original_FORM_soft(tmp_path):
    """V134 SOFT: '>' in S-level original FORM is also flagged."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">a&gt;b</FORM>'
        + '<FORM kindOf="standard">ab</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v134", "infix", "angle bracket", "&gt;", "< or >")
    ), (
        f"expected V134 finding for original tier; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V134_W_level_angle_brackets_do_not_trigger(tmp_path):
    """V134: '<' '>' in W-level FORM are not in scope."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">stdsentence</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">a&lt;b&gt;c</FORM>'
        + '<FORM kindOf="standard">abc</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v134" not in combined, (
        f"V134 should not fire on W-level angle brackets; "
        f"stdout={proc.stdout!r}"
    )


# TR14 V135 SOFT — trailing-punctuation mismatch between original and
# standard tiers (per-S).
#
# Compares the trailing run of recognized punctuation characters (after
# stripping trailing whitespace) between the S-level original and
# standard FORMs. A mismatch (e.g., original ends with '.', standard
# ends with '!', or one has punct and the other doesn't) is flagged.

def test_V135_punct_mismatch_period_vs_bang_soft(tmp_path):
    """V135 SOFT: original ends in '.', standard ends in '!'."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello world.</FORM>'
        + '<FORM kindOf="standard">hello world!</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v135", "trailing punct", "trailing-punct", "punct mismatch")
    ), (
        f"expected V135 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V135_original_has_punct_standard_does_not_soft(tmp_path):
    """V135 SOFT: original ends in '.', standard ends in no punct."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello.</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v135", "trailing punct", "trailing-punct", "punct mismatch")
    ), (
        f"expected V135 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V135_matching_punct_OK(tmp_path):
    """V135: both tiers end with the same punctuation — no finding."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello.</FORM>'
        + '<FORM kindOf="standard">hello.</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v135" not in combined, (
        f"V135 should not fire on matching trailing punct; "
        f"stdout={proc.stdout!r}"
    )


def test_V135_both_no_trailing_punct_OK(tmp_path):
    """V135: both tiers have no trailing punct — no finding."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v135" not in combined, (
        f"V135 should not fire when both tiers have no trailing punct; "
        f"stdout={proc.stdout!r}"
    )


# TR18 V136 SOFT — mixed-script confusables.
#
# Pragmatic heuristic: flag a FORM that contains characters from two or
# more of {Latin, Cyrillic, Greek} simultaneously. Other scripts
# (CJK, Hiragana, Katakana, Hangul, Arabic, Hebrew) are NOT included
# because they don't visually confuse with Latin in the same way the
# corpus is concerned about (mixed Latin+CJK is common and legitimate
# in this dataset).

def test_V136_latin_with_cyrillic_a_soft(tmp_path):
    """V136 SOFT: a Latin word with a Cyrillic а (U+0430) hidden inside."""
    # "cаfe" — the 'а' is Cyrillic U+0430, not Latin 'a' U+0061.
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">cаfe</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v136", "mixed script", "mixed-script", "confusable")
    ), (
        f"expected V136 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V136_latin_with_greek_omicron_soft(tmp_path):
    """V136 SOFT: a Latin word with a Greek omicron hidden inside."""
    # "hellο" — the 'ο' is Greek U+03BF, not Latin 'o'.
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hellο</FORM>'
        + '<FORM kindOf="standard">hello</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v136", "mixed script", "mixed-script", "confusable")
    ), (
        f"expected V136 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V136_pure_latin_OK(tmp_path):
    """V136 OK: pure Latin content has no mixed-script finding."""
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
    assert "v136" not in combined, (
        f"V136 should not fire on pure Latin; stdout={proc.stdout!r}"
    )


def test_V136_latin_with_cjk_OK(tmp_path):
    """V136 OK: Latin + CJK is legitimate (Chinese annotation), not flagged."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello 你好</FORM>'
        + '<FORM kindOf="standard">hello 你好</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v136" not in combined, (
        f"V136 should not fire on Latin + CJK; stdout={proc.stdout!r}"
    )


# TR19 V137 SOFT — trailing-decimal footnote (`word.1`, `word.2`) at end of
# S-level FORM or TRANSL.

def test_V137_trailing_decimal_in_S_FORM_soft(tmp_path):
    """V137 SOFT: text ending in `word.1` (digit glued to non-digit via '.')."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">hello world.1</FORM>'
        + '<FORM kindOf="standard">hello world</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v137", "trailing decimal", "trailing-decimal", "footnote")
    ), (
        f"expected V137 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V137_trailing_decimal_in_TRANSL_soft(tmp_path):
    """V137 SOFT: TRANSL ending in `word.2`."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<TRANSL xml:lang="eng">to speak.2</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v137", "trailing decimal", "trailing-decimal", "footnote")
    ), (
        f"expected V137 finding in TRANSL; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V137_plain_decimal_number_OK(tmp_path):
    """V137: ends with a plain decimal `3.14` (digit before .). Not flagged.

    The plan: 'Require the digit glued to a non-digit'. The character
    immediately before the '.' must be a non-digit for the pattern to
    fire — guards against numerals (3.14, 2025.12) being misclassified.
    """
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">pi is 3.14</FORM>'
        + '<FORM kindOf="standard">pi is 3.14</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v137" not in combined, (
        f"V137 should not fire on decimal numerals; stdout={proc.stdout!r}"
    )


def test_V137_mid_text_decimal_now_flagged(tmp_path):
    """V137 (broadened 2026-06-01): mid-text `word.1` triggers."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">word.1 plus more</FORM>'
        + '<FORM kindOf="standard">word.1 plus more</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v137", "footnote")
    ), (
        f"expected V137 finding on mid-text `.1`; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V137_letter_plus_digit_in_S_FORM_soft(tmp_path):
    """V137: letter immediately followed by digits (e.g., 'nganai12') triggers."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">nganai12 isi ia</FORM>'
        + '<FORM kindOf="standard">nganai isi ia</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v137", "footnote")
    ), (
        f"expected V137 finding on `nganai12`; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V137_W_FORM_letter_plus_digit_soft(tmp_path):
    """V137 walks W-level FORM (broadened scope, 2026-06-01)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">nganai</FORM>'
        + '<FORM kindOf="standard">nganai</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">nganai12</FORM>'
        + '<FORM kindOf="standard">nganai</FORM>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v137", "footnote")
    ), (
        f"expected V137 finding in W FORM; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V137_M_FORM_letter_plus_digit_soft(tmp_path):
    """V137 walks M-level FORM (broadened scope, 2026-06-01)."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">nganai</FORM>'
        + '<FORM kindOf="standard">nganai</FORM>'
        + '<W id="W1">'
        + '<FORM kindOf="original">nganai</FORM>'
        + '<FORM kindOf="standard">nganai</FORM>'
        + '<M id="M1">'
        + '<FORM kindOf="original">nganai12</FORM>'
        + '<FORM kindOf="standard">nganai</FORM>'
        + '</M>'
        + '</W>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v137", "footnote")
    ), (
        f"expected V137 finding in M FORM; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V137_multiple_findings_per_FORM(tmp_path):
    """V137 writes one CSV row per occurrence (per-occurrence semantics).

    The S-level original FORM here contains two distinct footnote
    markers: `niaranai12` (letter+digit, mid-string) and `miana.19`
    (`.digit`, trailing). The SOFT CSV must carry two V137 rows so
    Joshua can pin each to its source line. Stderr aggregates by
    (rule, lang, character) so the test reads the CSV directly.
    """
    import csv as _csv

    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">'
        +     '∅-sua nganai isi ia, niaranai12 upeni kusai mʉna cenana miana.19'
        + '</FORM>'
        + '<FORM kindOf="standard">a b c</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    soft_csv = tmp_path / "v137_soft.csv"
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATE_TEXT),
            "by_path", "--path", str(tmp_path / "XML"),
            "--soft-csv", str(soft_csv),
        ],
        capture_output=True,
        text=True,
    )
    assert soft_csv.exists(), (
        f"expected SOFT CSV at {soft_csv}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    with open(soft_csv, newline="", encoding="utf-8") as fh:
        rows = [r for r in _csv.reader(fh)]
    header, *data = rows
    v137_rows = [r for r in data if r[header.index("rule_id")] == "V137"]
    assert len(v137_rows) >= 2, (
        f"expected >=2 V137 rows in CSV; got {len(v137_rows)}; rows={data!r}"
    )


# TR20 V138 SOFT — superscript-digit footnote (¹²³…) in FORM or TRANSL.

def test_V138_superscript_one_in_FORM_soft(tmp_path):
    """V138 SOFT: superscript ¹ in FORM is a footnote leak."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">word¹</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v138", "superscript", "footnote")
    ), (
        f"expected V138 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V138_superscript_two_in_TRANSL_soft(tmp_path):
    """V138 SOFT: superscript ² in TRANSL is a footnote leak."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<TRANSL xml:lang="eng">speak²</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v138", "superscript", "footnote")
    ), (
        f"expected V138 finding for TRANSL; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V138_extended_superscript_4_soft(tmp_path):
    """V138 SOFT: U+2074 SUPERSCRIPT FOUR also caught."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">word⁴</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v138", "superscript", "footnote")
    ), (
        f"expected V138 finding for ⁴; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V138_no_superscript_OK(tmp_path):
    """V138 OK: plain text without superscript digits is fine."""
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
    assert "v138" not in combined, (
        f"V138 should not fire on plain text; stdout={proc.stdout!r}"
    )


# TR21 V139 SOFT — bracketed-digit footnote `[1]`, `[12]` in FORM or
# TRANSL. Pattern: `\[\d+\]` (digits inside ASCII square brackets).

def test_V139_bracketed_digit_in_FORM_soft(tmp_path):
    """V139 SOFT: `word[1]` in FORM is a footnote marker."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">word[1]</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v139", "bracketed", "[d]", "footnote")
    ), (
        f"expected V139 finding; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V139_standalone_bracketed_digit_in_TRANSL_soft(tmp_path):
    """V139 SOFT: standalone `[2]` token in TRANSL."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig</FORM>'
        + '<FORM kindOf="standard">std</FORM>'
        + '<TRANSL xml:lang="eng">see footnote [2]</TRANSL>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    assert _has_text_finding(
        proc, ("v139", "bracketed", "[d]", "footnote")
    ), (
        f"expected V139 finding in TRANSL; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V139_brackets_without_digits_OK(tmp_path):
    """V139: `[note]` (no digits) is not flagged — only digits inside []."""
    xml = (
        _TEXT_OPEN
        + '<S id="S1">'
        + '<FORM kindOf="original">orig [note]</FORM>'
        + '<FORM kindOf="standard">orig [note]</FORM>'
        + '</S>'
        + _TEXT_CLOSE
    )
    _write_xml(tmp_path, xml)
    proc = _run_validate_text(tmp_path)
    combined = combined_output(proc)
    assert "v139" not in combined, (
        f"V139 should not fire on non-digit brackets; "
        f"stdout={proc.stdout!r}"
    )


def test_V139_clean_text_OK(tmp_path):
    """V139 OK: text without `[\\d+]` is fine."""
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
    assert "v139" not in combined, (
        f"V139 should not fire on clean text; stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# Regression: comprehensive_test.xml
#
# Companion to the same-named tests in test_validate_xml.py and
# test_validate_glosses.py. Joshua's growing real-world fixture.
# Per-occurrence findings live in the SOFT CSV; aggregated SOFT lines
# in stderr are matched by (rule_id + character).
# -----------------------------------------------------------------------------


def test_comprehensive_test_xml_regression(tmp_path):
    """Lock in validate_text.py findings on comprehensive_test.xml.

    Asserts each expected (rule_id, marker) pair appears in the
    combined CLI output (HARD findings) or in the per-occurrence SOFT
    CSV (SOFT findings).
    """
    import csv as _csv

    repo_root = Path(__file__).resolve().parents[2]
    fixture = repo_root / "tests" / "fixtures" / "comprehensive_test.xml"
    assert fixture.exists(), f"comprehensive fixture missing at {fixture}"
    soft_csv = tmp_path / "comp_soft.csv"
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATE_TEXT),
            "by_path", "--path", str(fixture),
            "--soft-csv", str(soft_csv),
            "--no-exit-on-hard",
        ],
        capture_output=True,
        text=True,
    )
    combined = (proc.stdout + proc.stderr).lower()
    # HARD findings: assert (rule_id, location-id) both appear in combined output.
    expected_hard: tuple[tuple[str, str], ...] = (
        ("v120", "ap3_s_2"),    # null '∅' in S-standard FORM
        ("v129", "s=1"),         # '*' in either FORM tier of S=1
        ("v129", "w=1_1"),       # '*' in W=1_1
        ("v140", "ap3_s_2"),     # S-original null not propagated down
    )
    missing_hard: list[tuple[str, str]] = []
    for rule, marker in expected_hard:
        if rule not in combined or marker not in combined:
            missing_hard.append((rule, marker))
    assert not missing_hard, (
        f"HARD regression missing: {missing_hard!r}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    # SOFT findings: assert rule_ids appear as CSV rows.
    assert soft_csv.exists(), (
        f"SOFT CSV missing for fixture run; stderr={proc.stderr!r}"
    )
    with open(soft_csv, newline="", encoding="utf-8") as fh:
        rows = list(_csv.DictReader(fh))
    soft_rule_ids_present = {r["rule_id"] for r in rows}
    expected_soft = {"V116", "V122", "V133", "V135", "V137"}
    missing_soft = expected_soft - soft_rule_ids_present
    assert not missing_soft, (
        f"SOFT regression missing: {missing_soft!r}; csv rows={rows!r}"
    )


# ---------------------------------------------------------------------------
# V141: W FORMs reconstruct the S FORM (SOFT) — rule-level tests
# (imports for these live at the top of the file with the rest)
# ---------------------------------------------------------------------------

_V141_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<TEXT id="T1" citation="t" BibTeX_citation="@t{{t}}" copyright="t" xml:lang="ami">
{body}
</TEXT>
"""


def _v141_findings(xml: str):
    tree = etree.parse(BytesIO(xml.encode("utf-8")))
    return text_rules.v141_W_reconstructs_S(tree, Path("test.xml"), None)


def test_V141_clean_reconstruction_no_finding():
    """W FORMs spell the S FORM (punctuation in S ignored) -> no finding."""
    xml = _V141_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ka en, taon.</FORM>
        <W id="W1"><FORM kindOf="original">ka</FORM></W>
        <W id="W2"><FORM kindOf="original">en</FORM></W>
        <W id="W3"><FORM kindOf="original">taon</FORM></W>
      </S>""")
    assert _v141_findings(xml) == []


def test_V141_misaligned_W_tier_emits_SOFT():
    """The W decomposition spells a different sentence -> SOFT V141."""
    xml = _V141_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ka en taon</FORM>
        <W id="W1"><FORM kindOf="original">mirung</FORM></W>
        <W id="W2"><FORM kindOf="original">cudju</FORM></W>
      </S>""")
    findings = _v141_findings(xml)
    assert len(findings) == 1, f"expected 1 V141 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V141"
    assert f.severity is Severity.SOFT
    assert "S1" in f.location


def test_V141_uses_original_tier_only():
    """Original tiers reconstruct; standard tiers diverge -> no finding."""
    xml = _V141_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ka en</FORM>
        <FORM kindOf="standard">zzzzz</FORM>
        <W id="W1"><FORM kindOf="original">ka</FORM><FORM kindOf="standard">qq</FORM></W>
        <W id="W2"><FORM kindOf="original">en</FORM><FORM kindOf="standard">pp</FORM></W>
      </S>""")
    assert _v141_findings(xml) == []


def test_V141_S_without_W_skipped():
    """An unsegmented S (no W children) is skipped."""
    xml = _V141_TEMPLATE.format(body="""
      <S id="S1"><FORM kindOf="original">ka en taon</FORM></S>""")
    assert _v141_findings(xml) == []
