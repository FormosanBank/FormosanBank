"""Tests for QC/validation/validate_xml.py against the design at
.claude/plans/2026-05-29-xml-validation-design.md.

Many rules in the design are not currently enforced by validate_xml.py
("Currently checked? No" or "Partial"). Tests for those rules are
marked pytest.mark.xfail(strict=True). When sub-project B updates the
validator, the tests will start passing and pytest will flag XPASS so
the xfail markers can be removed.

Test pattern (HARD rules): subprocess-invoke validate_xml.py via
`by_path --path <dir>`, then check output for evidence of the
violation. The current validators never sys.exit(1), so tests assert
on output content (presence of finding markers), not on exit code —
per the design's V083 note.

Output markers
--------------
The current validator prints a summary:
  Total issues found: <N>
  <If N == 0:> "No issues found."
  <If N > 0:> "Files with issues:\\n<paths>"
plus per-file ERROR lines for each rule that triggered.

NEGATIVE_MARKERS below cover every shape of finding output we expect a
revised validator to keep using (or extend with named rule markers).

Positive assertion: the file appears in NO "Files with issues" section
AND the summary reports "Total issues found: 0". We assert presence of
"no issues found" / "total issues found: 0" rather than absence of
error markers, because XSD lines for OTHER files in the corpus could
otherwise pollute the output.
"""
import subprocess
import sys
from pathlib import Path

import pytest


VALIDATE_XML = Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_xml.py"

# Generic finding markers — any of these in the combined stdout+stderr
# (case-insensitive) indicates the validator reported a problem. Tests
# that expect a finding assert at least one of these is present.
NEGATIVE_MARKERS: tuple[str, ...] = (
    "error",
    "violation",
    "invalid",
    "files with issues",
)

# Reason constant for xfail tests covering rules the validator does not
# currently enforce per the design doc.
XFAIL_NOT_YET_CHECKED = (
    "Per design doc 2026-05-29-xml-validation-design.md: this rule is "
    "'Currently checked? No' (or Partial). Tracked for sub-project B."
)


def _run_validate(corpus_xml_dir: Path) -> subprocess.CompletedProcess:
    """Invoke validate_xml.py against a directory containing an XML/ subdir.

    The validator is given the directory whose contents include /XML/<files>.xml.
    by_path mode walks the tree and validates each .xml file whose path
    contains 'XML'.
    """
    return subprocess.run(
        [sys.executable, str(VALIDATE_XML), "by_path", "--path", str(corpus_xml_dir)],
        capture_output=True,
        text=True,
    )


def _combined(proc: subprocess.CompletedProcess) -> str:
    return (proc.stdout + proc.stderr).lower()


def _has_finding(proc: subprocess.CompletedProcess) -> bool:
    """Did the validator's output mention ANY generic finding marker?

    Used for HARD rules the validator already enforces (V001, V003–V005,
    V011–V012, V016, V030–V035, V038, V083). For those, we don't care
    which error class the validator chooses — just that SOME finding
    appears.
    """
    combined = _combined(proc)
    return any(m.lower() in combined for m in NEGATIVE_MARKERS)


def _has_rule_finding(
    proc: subprocess.CompletedProcess, rule_markers: tuple[str, ...]
) -> bool:
    """Did the validator's output mention a RULE-SPECIFIC marker?

    Used for xfail tests targeting rules not yet enforced. The xfail
    assertion must NOT be satisfied by the validator's generic "Files
    with issues" or by a coincidental ERROR line from a different rule
    — otherwise xfail-strict turns into XPASS. So we require at least
    one of the caller's rule-specific markers (e.g., the rule ID
    'v053', or rule-specific phrasing like 'orphan audio') to appear
    in the output. The current validator does not include such markers,
    so xfail correctly XFAILs. When B implements the rule, it should
    emit one of these markers, flipping the test to XPASS so the xfail
    can be removed.
    """
    combined = _combined(proc)
    return any(m.lower() in combined for m in rule_markers)


def _is_clean(proc: subprocess.CompletedProcess) -> bool:
    """Did the validator report a clean run (no issues)?"""
    combined = _combined(proc)
    return ("total issues found: 0" in combined) and ("no issues found" in combined)


# -----------------------------------------------------------------------------
# Structural / hierarchy: V001, V003, V004, V005
# -----------------------------------------------------------------------------


def test_V001_root_must_be_TEXT_positive(tmp_path, fixtures_dir, copy_fixture):
    """V001: a document rooted at TEXT validates cleanly."""
    copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation; got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_V001_root_must_be_TEXT_negative(tmp_path, fixtures_dir, copy_fixture):
    """V001: a document rooted at S (not TEXT) is rejected by the schema."""
    copy_fixture(fixtures_dir / "v001_root_is_S_not_TEXT.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected validation finding for non-TEXT root; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V003_S_only_child_of_TEXT_negative(tmp_path, fixtures_dir, copy_fixture):
    """V003: S nested inside W is rejected by the schema."""
    copy_fixture(fixtures_dir / "v003_S_nested_in_W.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for S nested inside W; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V004_W_only_child_of_S_negative(tmp_path, fixtures_dir, copy_fixture):
    """V004: W as a direct child of TEXT (no intervening S) is rejected."""
    copy_fixture(fixtures_dir / "v004_W_direct_under_TEXT.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for W directly under TEXT; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V005_M_only_child_of_W_negative(tmp_path, fixtures_dir, copy_fixture):
    """V005: M as a direct child of S (no intervening W) is rejected."""
    copy_fixture(fixtures_dir / "v005_M_direct_under_S.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for M directly under S; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# FORM tier: V010 (SOFT), V011, V012, V013, V014 (SOFT), V015, V016, V017
# -----------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V010 SOFT: per design, an S with no FORM should be COUNTED, not "
        "rejected. Currently the XSD rejects it (HARD). After B's update, "
        "the validator should accept this file and emit a count."
    ),
)
def test_V010_S_without_FORM_is_counted_not_fatal(tmp_path, fixtures_dir, copy_fixture):
    """V010 SOFT: missing FORM on S is counted, not fatal.

    The desired post-revision behavior: the validator accepts the file
    (no HARD violation) but emits an indicator showing the S was
    counted as 'missing FORM'. We assert the run is clean of HARD
    findings AND emits some count/standard-tier indicator.
    """
    copy_fixture(fixtures_dir / "v010_S_without_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"V010 should not produce HARD findings; got stdout={proc.stdout!r}"
    )
    combined = _combined(proc)
    # Some signal that the count was produced. The exact format is up
    # to B (CSV per V014 spec); we just look for any of a few sensible
    # indicators.
    assert any(t in combined for t in ("count", "missing", "soft")), (
        f"expected SOFT-count indicator; got stdout={proc.stdout!r}"
    )


def test_V011_W_must_have_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V011: W without a FORM child is rejected by the schema."""
    copy_fixture(fixtures_dir / "v011_W_without_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for W with no FORM; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V012_M_must_have_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V012: M without a FORM child is rejected by the schema."""
    copy_fixture(fixtures_dir / "v012_M_without_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for M with no FORM; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V013_S_must_have_original_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V013: an S whose only FORM is kindOf="standard" must produce a finding."""
    copy_fixture(fixtures_dir / "v013_S_only_standard_no_original.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v013", "missing original", "no original")), (
        f"expected finding about missing original FORM; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V014 SOFT: per design, the validator should COUNT missing-standard "
        "elements and emit them in a CSV-style report. Currently NOT checked."
    ),
)
def test_V014_missing_standard_FORM_is_counted(tmp_path, fixtures_dir, copy_fixture):
    """V014 SOFT-count: missing standard FORM is counted (not fatal).

    Desired behavior: the validator emits a count or list of elements
    missing the standard tier. Not fatal — _is_clean may still hold —
    but some 'missing standard' indicator must appear in the output.
    """
    copy_fixture(fixtures_dir / "v014_missing_standard_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    combined = _combined(proc)
    # The XML is structurally valid; HARD pipeline must not flag it.
    assert _is_clean(proc), (
        f"V014 missing-standard should not produce HARD findings; "
        f"got stdout={proc.stdout!r}"
    )
    # But some SOFT-count signal must be present.
    assert "missing standard" in combined or "missing-standard" in combined, (
        f"expected SOFT-count 'missing standard' indicator; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V015_duplicate_original_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V015: two FORM kindOf="original" siblings under the same S is forbidden."""
    copy_fixture(fixtures_dir / "v015_duplicate_original_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v015", "duplicate form", "duplicate kindof")), (
        f"expected finding about duplicate FORM kindOf; got stdout={proc.stdout!r}"
    )


def test_V016_unknown_kindOf_value_negative(tmp_path, fixtures_dir, copy_fixture):
    """V016: FORM kindOf="draft" is rejected by the XSD enumeration."""
    copy_fixture(fixtures_dir / "v016_unknown_kindOf_value.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for unknown kindOf value; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V017_empty_FORM_content_negative(tmp_path, fixtures_dir, copy_fixture):
    """V017: a FORM with empty text content is a bug."""
    copy_fixture(fixtures_dir / "v017_empty_FORM_content.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v017", "empty form", "form is empty")), (
        f"expected finding for empty FORM content; got stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# TRANSL: V021, V022, V023, V024, V026
# -----------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V021_M_single_TRANSL_must_be_original_negative(tmp_path, fixtures_dir, copy_fixture):
    """V021: on M, a lone TRANSL without kindOf="original" must produce a finding."""
    copy_fixture(fixtures_dir / "v021_M_single_TRANSL_not_original.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v021", "lone transl", "single transl")), (
        f"expected finding about M lone-TRANSL kindOf; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V022_M_multiple_originals_must_have_distinct_lang_negative(
    tmp_path, fixtures_dir, copy_fixture
):
    """V022: multiple kindOf="original" TRANSLs on the same M must have distinct xml:lang."""
    copy_fixture(fixtures_dir / "v022_M_two_originals_same_lang.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v022", "duplicate xml:lang", "same xml:lang")), (
        f"expected finding about duplicate-lang originals on M; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V023_TRANSL_must_have_xml_lang_negative(tmp_path, fixtures_dir, copy_fixture):
    """V023: every TRANSL must have an xml:lang attribute."""
    copy_fixture(fixtures_dir / "v023_TRANSL_missing_xml_lang.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v023", "transl missing xml:lang", "transl has no xml:lang")), (
        f"expected finding about missing TRANSL xml:lang; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V024_TRANSL_xml_lang_must_be_iso_639_3_negative(tmp_path, fixtures_dir, copy_fixture):
    """V024: TRANSL/@xml:lang must be a valid ISO 639-3 code."""
    copy_fixture(fixtures_dir / "v024_TRANSL_invalid_iso_code.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v024", "transl xml:lang", "transl iso")), (
        f"expected finding about invalid TRANSL iso code; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V026_M_TRANSL_kindOf_must_be_original_or_standard_negative(
    tmp_path, fixtures_dir, copy_fixture
):
    """V026: TRANSL/@kindOf at M must be 'original' or 'standard'."""
    copy_fixture(fixtures_dir / "v026_M_TRANSL_freeform_kindOf.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v026", "m-level transl kindof", "transl kindof on m")), (
        f"expected finding about disallowed M-level TRANSL kindOf; "
        f"got stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# Attribute / TEXT metadata: V030–V036, V038, V039
# -----------------------------------------------------------------------------


def test_V030_TEXT_must_have_id_negative(tmp_path, fixtures_dir, copy_fixture):
    """V030: TEXT without an id is rejected by the schema."""
    copy_fixture(fixtures_dir / "v030_TEXT_missing_id.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing TEXT/@id; got stdout={proc.stdout!r}"
    )


def test_V031_TEXT_must_have_citation_negative(tmp_path, fixtures_dir, copy_fixture):
    """V031: TEXT without a citation is rejected by the schema."""
    copy_fixture(fixtures_dir / "v031_TEXT_missing_citation.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing TEXT/@citation; got stdout={proc.stdout!r}"
    )


def test_V032_TEXT_must_have_BibTeX_citation_negative(tmp_path, fixtures_dir, copy_fixture):
    """V032: TEXT without a BibTeX_citation is rejected by the schema."""
    copy_fixture(fixtures_dir / "v032_TEXT_missing_bibtex.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing TEXT/@BibTeX_citation; got stdout={proc.stdout!r}"
    )


def test_V033_TEXT_must_have_copyright_negative(tmp_path, fixtures_dir, copy_fixture):
    """V033: TEXT without a copyright is rejected by the schema."""
    copy_fixture(fixtures_dir / "v033_TEXT_missing_copyright.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing TEXT/@copyright; got stdout={proc.stdout!r}"
    )


def test_V034_TEXT_must_have_xml_lang_negative(tmp_path, fixtures_dir, copy_fixture):
    """V034: TEXT without xml:lang is rejected by the schema/validate_lang_code."""
    copy_fixture(fixtures_dir / "v034_TEXT_missing_xml_lang.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing TEXT/@xml:lang; got stdout={proc.stdout!r}"
    )


def test_V035_TEXT_xml_lang_must_be_iso_639_3_negative(tmp_path, fixtures_dir, copy_fixture):
    """V035: TEXT/@xml:lang must be a valid ISO 639-3 code."""
    copy_fixture(fixtures_dir / "v035_TEXT_invalid_iso_code.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc, ("iso", "639", "lang")), (
        f"expected finding for invalid xml:lang code; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V036_TEXT_dialect_must_be_valid_negative(tmp_path, fixtures_dir, copy_fixture):
    """V036 HARD-part: TEXT/@dialect, if set, must be in dialects.csv for the language."""
    copy_fixture(fixtures_dir / "v036_TEXT_invalid_dialect.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v036", "dialect")), (
        f"expected finding for invalid dialect; got stdout={proc.stdout!r}"
    )


def test_V038_S_must_have_id_negative(tmp_path, fixtures_dir, copy_fixture):
    """V038: S without an id attribute is rejected by the schema."""
    copy_fixture(fixtures_dir / "v038_S_missing_id.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing S/@id; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V039_duplicate_id_across_types_negative(tmp_path, fixtures_dir, copy_fixture):
    """V039: an S id and a W id cannot collide within the same file."""
    copy_fixture(fixtures_dir / "v039_duplicate_id_across_types.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v039", "duplicate id", "id collision")), (
        f"expected finding for duplicate ids across element types; "
        f"got stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# AUDIO: V051, V052, V053, V054, V056
# -----------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V051: segmented-mode AUDIO with empty @file must produce a finding. "
        "Current validator's 'diarized' magic check uses the wrong sentinel "
        "AND the wrong indicator. Tracked for sub-project B."
    ),
)
def test_V051_AUDIO_empty_file_attr_negative(tmp_path, fixtures_dir, copy_fixture):
    """V051: AUDIO with file="" must produce a finding."""
    copy_fixture(fixtures_dir / "v051_AUDIO_empty_file_attr.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v051", "empty file", "empty audio/@file")), (
        f"expected finding for empty AUDIO/@file; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V052: single-file mode requires TEXT/@audio + AUDIO/@start + @end. "
        "Current validator partially checks this but with the wrong mode "
        "entry condition. Tracked for sub-project B."
    ),
)
def test_V052_single_file_mode_missing_start_end_negative(tmp_path, fixtures_dir, copy_fixture):
    """V052: AUDIO with no file, in single-file mode, must have start/end."""
    copy_fixture(fixtures_dir / "v052_single_file_missing_start_end.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v052", "single-file mode", "missing start", "missing end")), (
        f"expected finding for missing AUDIO start/end in single-file mode; "
        f"got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V053_orphan_AUDIO_negative(tmp_path, fixtures_dir, copy_fixture):
    """V053: AUDIO with no @file and no TEXT/@audio is unmoored."""
    copy_fixture(fixtures_dir / "v053_orphan_AUDIO.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v053", "orphan audio", "unmoored")), (
        f"expected finding for orphan AUDIO; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V054_AUDIO_end_before_start_negative(tmp_path, fixtures_dir, copy_fixture):
    """V054: AUDIO end < start must produce a finding."""
    copy_fixture(fixtures_dir / "v054_AUDIO_end_before_start.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v054", "end < start", "end before start", "end >= start")), (
        f"expected finding for AUDIO end < start; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V056: AUDIO is legal under TEXT, S, W, M. Current XSD only "
        "permits AUDIO under S/W/M, so an AUDIO directly under TEXT is "
        "WRONGLY rejected today. After XSD update, this fixture should "
        "validate cleanly."
    ),
)
def test_V056_AUDIO_under_TEXT_positive(tmp_path, fixtures_dir, copy_fixture):
    """V056 (positive): AUDIO under TEXT should validate cleanly after XSD update."""
    copy_fixture(fixtures_dir / "v056_AUDIO_under_TEXT.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"V056: AUDIO directly under TEXT should be valid; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W/M segmentation: V062
# -----------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V062_infix_M_without_angle_gloss_negative(tmp_path, fixtures_dir, copy_fixture):
    """V062 (negative): infix-shaped M FORM without an angle-bracket gloss on W's TRANSL."""
    copy_fixture(fixtures_dir / "v062_infix_M_without_angle_gloss.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v062", "infix", "angle-bracket gloss")), (
        f"expected finding about missing infix gloss; got stdout={proc.stdout!r}"
    )


def test_V062_infix_M_with_angle_gloss_positive(tmp_path, fixtures_dir, copy_fixture):
    """V062 (positive): infix M FORM correctly paired with angle-bracket gloss.

    A well-formed pairing of infix-shaped M FORM ("-um-") and a W TRANSL
    containing "<AV>" must validate cleanly. This test currently passes
    because V062 is not enforced (so nothing complains); after B
    implements V062 it must still pass because the pairing is legal.
    """
    copy_fixture(fixtures_dir / "v062_infix_M_with_angle_gloss.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"V062 positive should validate cleanly; "
        f"got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# PHON: V070, V071, V072, V073
# -----------------------------------------------------------------------------


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V070_PHON_directly_under_TEXT_negative(tmp_path, fixtures_dir, copy_fixture):
    """V070: PHON directly under TEXT (illegal placement)."""
    copy_fixture(fixtures_dir / "v070_PHON_directly_under_TEXT.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v070", "phon placement", "phon must be a child")), (
        f"expected finding about PHON placement; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V071_PHON_invalid_kindOf_negative(tmp_path, fixtures_dir, copy_fixture):
    """V071: PHON kindOf="alternate" is not a valid value."""
    copy_fixture(fixtures_dir / "v071_PHON_invalid_kindOf.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v071", "phon kindof", "phon/@kindof")), (
        f"expected finding about invalid PHON kindOf; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V072_duplicate_PHON_kindOf_negative(tmp_path, fixtures_dir, copy_fixture):
    """V072: two PHON kindOf="original" siblings under the same parent."""
    copy_fixture(fixtures_dir / "v072_duplicate_PHON_kindOf.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v072", "duplicate phon")), (
        f"expected finding about duplicate PHON kindOf; got stdout={proc.stdout!r}"
    )


@pytest.mark.xfail(strict=True, reason=XFAIL_NOT_YET_CHECKED)
def test_V073_PHON_empty_content_negative(tmp_path, fixtures_dir, copy_fixture):
    """V073: PHON with empty text content."""
    copy_fixture(fixtures_dir / "v073_PHON_empty_content.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v073", "empty phon", "phon is empty")), (
        f"expected finding about empty PHON content; got stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# Cross-corpus: V081, V083
# -----------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "V081: cross-corpus TEXT/@id uniqueness. The validator must walk "
        "FormosanBank/Corpora/ (read-only) and check the corpus-under-test "
        "for id collisions. Currently NOT enforced. Tracked for sub-project B."
    ),
)
def test_V081_cross_corpus_TEXT_id_collision_negative(tmp_path, fixtures_dir, copy_fixture):
    """V081: a fixture whose TEXT/@id is also present in published Corpora.

    The fixture uses 'Yedda_Ljeljeng_lja_Palemek's_Blog', which is a real
    id in Corpora/YeddaPalemeqBlog/XML/Paiwan/Paiwan_Yedda_Blog.xml.
    When validate_xml.py implements V081, it should walk
    FormosanBank/Corpora/ and surface the collision.
    """
    copy_fixture(fixtures_dir / "v081_TEXT_id_collides_with_published.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v081", "cross-corpus", "id collision", "id collides")), (
        f"expected finding for cross-corpus id collision; got stdout={proc.stdout!r}"
    )


def test_V083_schema_validation_positive(tmp_path, fixtures_dir, copy_fixture):
    """V083: a well-formed, schema-conformant file validates cleanly."""
    copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation; got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_V083_schema_validation_negative(tmp_path, fixtures_dir, copy_fixture):
    """V083: a file with an unknown child element (FOO) fails schema validation."""
    copy_fixture(fixtures_dir / "v083_unknown_child_element.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for unknown child element; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )
