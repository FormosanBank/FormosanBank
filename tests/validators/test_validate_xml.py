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

from _helpers import combined_output, csv_has, has_marker


VALIDATE_XML = Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_xml.py"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_CORPORA_ROOT = _REPO_ROOT / "Corpora"

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


def _run_validate(
    corpus_xml_dir: Path,
    published_corpora: Path | None = None,
) -> subprocess.CompletedProcess:
    """Invoke validate_xml.py against a directory containing an XML/ subdir.

    The validator is given the directory whose contents include /XML/<files>.xml.
    by_path mode walks the tree and validates each .xml file whose path
    contains 'XML'.

    SOFT CSV is directed into corpus_xml_dir so this helper never
    pollutes the repo root with a logs/ directory.

    published_corpora: path passed to --published-corpora. Defaults to
    corpus_xml_dir (the test's tmp_path, which contains only the fixture
    under test) to avoid walking the real Corpora/ on every test call.
    Pass _CORPORA_ROOT explicitly for tests that exercise V081.
    """
    if published_corpora is None:
        published_corpora = corpus_xml_dir
    return subprocess.run(
        [
            sys.executable, str(VALIDATE_XML),
            "--published-corpora", str(published_corpora),
            "by_path", "--path", str(corpus_xml_dir),
            "--soft-csv", str(corpus_xml_dir / "soft.csv"),
        ],
        capture_output=True,
        text=True,
    )


def _has_finding(proc: subprocess.CompletedProcess) -> bool:
    """Did the validator's summary report at least one issue?

    Since 2026-06-09 the terminal shows only the per-rule count summary
    (per-finding detail moved to the CSV). A run with findings prints
    "... N with issues ===" where N > 0; a clean run prints
    "... 0 with issues ===". So "has a finding" == the summary mentions
    issues and the count is not zero.
    """
    combined = combined_output(proc)
    return ("with issues" in combined) and ("0 with issues" not in combined)


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
    return has_marker(proc, rule_markers)


def _is_clean(proc: subprocess.CompletedProcess) -> bool:
    """Did the validator report no HARD findings?

    These positive tests assert a fixture triggers no HARD (schema/format)
    violation; SOFT findings (e.g. V010/V014) are allowed and do not make a
    run "unclean" in this sense. Under the 2026-06-09 summary contract the
    validator exits 0 iff there are no HARD findings, and always prints the
    summary header, so: ran + exit 0 == HARD-clean.
    """
    combined = combined_output(proc)
    return proc.returncode == 0 and "validation summary" in combined


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
    combined = combined_output(proc)
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


def test_V013_S_must_have_original_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V013: an S whose only FORM is kindOf="standard" must produce a finding."""
    copy_fixture(fixtures_dir / "v013_S_only_standard_no_original.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v013", "missing original", "no original")), (
        f"expected finding about missing original FORM; got stdout={proc.stdout!r}"
    )


def test_V014_missing_standard_FORM_is_counted(tmp_path, fixtures_dir, copy_fixture):
    """V014 SOFT-count: missing standard FORM is counted (not fatal).

    Desired behavior: the validator emits a count or list of elements
    missing the standard tier. Not fatal — _is_clean may still hold —
    but some 'missing standard' indicator must appear in the output.
    """
    copy_fixture(fixtures_dir / "v014_missing_standard_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    # The XML is structurally valid; HARD pipeline must not flag it.
    assert _is_clean(proc), (
        f"V014 missing-standard should not produce HARD findings; "
        f"got stdout={proc.stdout!r}"
    )
    # But the SOFT V014 finding must be recorded in the findings CSV.
    assert csv_has(tmp_path / "soft.csv", "V014", "missing standard"), (
        f"expected a V014 'missing standard' row in the CSV; "
        f"got stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V015_duplicate_original_FORM_negative(tmp_path, fixtures_dir, copy_fixture):
    """V015: two FORM kindOf="original" siblings under the same S is forbidden."""
    copy_fixture(fixtures_dir / "v015_duplicate_original_FORM.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v015", "duplicate kindof")), (
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


def test_V017_empty_FORM_content_negative(tmp_path, fixtures_dir, copy_fixture):
    """V017: a FORM with empty text content is a bug."""
    copy_fixture(fixtures_dir / "v017_empty_FORM_content.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v017", "empty form", "form is empty")), (
        f"expected finding for empty FORM content; got stdout={proc.stdout!r}"
    )


# -----------------------------------------------------------------------------
# TRANSL: V022, V023, V024, V026
# (V021 removed 2026-05-31 — TRANSL does not need kindOf at all; per user
# direction. See .claude/plans/2026-05-31-corpus-cleanup-tasks.md.)
# -----------------------------------------------------------------------------


def test_V022_M_multiple_originals_must_have_distinct_lang_negative(
    tmp_path, fixtures_dir, copy_fixture
):
    """V022: multiple kindOf="original" TRANSLs on the same M must have distinct xml:lang."""
    copy_fixture(fixtures_dir / "v022_M_two_originals_same_lang.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v022", "duplicate xml:lang", "same xml:lang")), (
        f"expected finding about duplicate-lang originals on M; got stdout={proc.stdout!r}"
    )


def test_V023_TRANSL_must_have_xml_lang_negative(tmp_path, fixtures_dir, copy_fixture):
    """V023: every TRANSL must have an xml:lang attribute."""
    copy_fixture(fixtures_dir / "v023_TRANSL_missing_xml_lang.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v023", "transl missing xml:lang", "transl has no xml:lang")), (
        f"expected finding about missing TRANSL xml:lang; got stdout={proc.stdout!r}"
    )


def test_V084_TRANSL_ver_value_must_be_in_allowlist_negative(
    tmp_path, fixtures_dir, copy_fixture
):
    """V084: TRANSL/@ver must be in the project allowlist (currently {"alt"})."""
    copy_fixture(fixtures_dir / "v084_TRANSL_ver_invalid_value.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v084", "ver=", "allowed set")), (
        f"expected V084 finding for invalid ver value; got stdout={proc.stdout!r}"
    )


def test_V085_multi_same_lang_TRANSL_no_ver_negative(
    tmp_path, fixtures_dir, copy_fixture
):
    """V085: multiple TRANSL same xml:lang on same parent must have >=1 ver."""
    copy_fixture(fixtures_dir / "v085_S_two_same_lang_TRANSL_no_ver.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v085", "ver attribute", "discriminate")), (
        f"expected V085 finding for ambiguous same-lang TRANSLs; got stdout={proc.stdout!r}"
    )


def test_V085_multi_same_lang_TRANSL_with_ver_positive(
    tmp_path, fixtures_dir, copy_fixture
):
    """V085: when one of the same-lang TRANSLs has ver, no V085 finding fires.

    Also exercises V084 with a valid `ver="alt"` — should NOT trigger V084.
    """
    copy_fixture(fixtures_dir / "v085_S_two_same_lang_TRANSL_one_with_ver.xml", tmp_path)
    proc = _run_validate(tmp_path)
    combined = (proc.stdout + proc.stderr).lower()
    # Match the rule-id marker shape "[v085]" rather than the bare
    # substring "v085", because as of 2026-06-03 the validator prints
    # the file path on each finding line and that path can contain
    # "v085" (the fixture's basename) without V085 itself firing.
    assert "[v085]" not in combined, (
        f"V085 should not fire when ver discriminates; got stdout={proc.stdout!r}"
    )
    assert "[v084]" not in combined, (
        f"V084 should not fire on valid ver='alt'; got stdout={proc.stdout!r}"
    )


def test_S_audio_url_and_source_and_AUDIO_source_are_clean(
    tmp_path, fixtures_dir, copy_fixture
):
    """Schema regression: S/@audio_url, S/@source, AUDIO/@source, FORM/@notes, TRANSL/@notes.

    Added 2026-06-03 to support YeddaPalemeqBlog-style sentence metadata
    where each S has both a per-sentence audio URL and a per-sentence
    source-page URL, AUDIO carries the original recording URL in @source
    alongside @file, and FORM may carry a free-text @notes annotation.
    TRANSL/@notes added 2026-06-09 (same optional free-text annotation,
    extended to the translation tier). Pins all five optional attributes
    against schema regression.
    """
    copy_fixture(
        fixtures_dir / "valid_S_audio_url_source_and_AUDIO_source.xml", tmp_path
    )
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_UNCLEAR_in_FORM_PHON_TRANSL_is_clean(
    tmp_path, fixtures_dir, copy_fixture
):
    """Schema regression: <UNCLEAR/> child in FORM/PHON/TRANSL validates.

    Added 2026-06-08 to schematize a pattern already in published data
    (WilangYutasVideos, YeddaPalemeqBlog). FORM_Type, PHON_Type and
    TRANSL_Type became mixed content allowing zero or more UNCLEAR
    children. Pins three shapes: whole-tier (FORM=<UNCLEAR/>), partial
    inline (FORM='halo <UNCLEAR/> world'), and TRANSL-level.
    """
    copy_fixture(
        fixtures_dir / "valid_UNCLEAR_in_FORM_PHON_TRANSL.xml", tmp_path
    )
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation for UNCLEAR fixture; got "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_audio_only_TEXT_no_S_is_clean(tmp_path, fixtures_dir, copy_fixture):
    """Schema regression: TEXT with single AUDIO child and no S validates.

    Added 2026-06-03 to support audio-only files (no transcription yet).
    Example in published data: Corpora/Whitehorn_Collection/XML/Amis/
    hymns_of_praise_side_a_whitehorn_Amis.xml. Pins S/@minOccurs=0
    against schema regression.
    """
    copy_fixture(fixtures_dir / "valid_audio_only_TEXT_no_S.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation for audio-only TEXT; got "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_V050_AUDIO_with_file_only_is_clean(tmp_path, fixtures_dir, copy_fixture):
    """V050 positive: AUDIO with @file (no start/end) is valid per the spec.

    The whole referenced file IS the clip, so start/end are NOT required.
    Regression pin for the prior bug where v050 unconditionally required
    start/end on every AUDIO.
    """
    copy_fixture(fixtures_dir / "valid_audio_with_file.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V024_TRANSL_xml_lang_must_be_iso_639_3_negative(tmp_path, fixtures_dir, copy_fixture):
    """V024: TRANSL/@xml:lang must be a valid ISO 639-3 code.

    Implemented by v035_xml_lang_is_iso_639_3, which walks every element
    with xml:lang (not only TEXT). The "transl xml:lang" marker matches
    the rule's message format (`TRANSL xml:lang='xyz' is not a valid
    ISO 639-3 code`).
    """
    copy_fixture(fixtures_dir / "v024_TRANSL_invalid_iso_code.xml", tmp_path)
    proc = _run_validate(tmp_path)
    # v035_xml_lang_is_iso_639_3 flags this as a V035 finding whose message
    # names the TRANSL element. Detail lives in the CSV now, not stderr.
    assert csv_has(tmp_path / "soft.csv", "V035", "transl"), (
        f"expected a V035 row naming the invalid TRANSL iso code in the CSV; "
        f"got stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


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
    assert _has_finding(proc), (
        f"expected finding for invalid xml:lang code; got stdout={proc.stdout!r}"
    )


def test_V036_TEXT_dialect_must_be_valid_negative(tmp_path, fixtures_dir, copy_fixture):
    """V036 HARD-part: TEXT/@dialect, if set, must be in dialects.csv for the language."""
    copy_fixture(fixtures_dir / "v036_TEXT_invalid_dialect.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v036", "dialect")), (
        f"expected finding for invalid dialect; got stdout={proc.stdout!r}"
    )


def test_V035_zh_Hans_is_accepted(tmp_path, fixtures_dir, copy_fixture):
    """V035 positive: xml:lang='zh-Hans' is accepted via the explicit
    non-ISO allow-list.

    ISO 639-3 has no way to distinguish Simplified vs Traditional Chinese
    (both collapse to 'zho'). zh-Hans is preserved as a documented
    exception because the script distinction is load-bearing in some
    corpora (notably Glosbe).
    """
    copy_fixture(fixtures_dir / "valid_zh_Hans_transl.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected zh-Hans to validate clean; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V036_trv_with_truku_dialect_is_clean(tmp_path, fixtures_dir, copy_fixture):
    """V036 positive: xml:lang='trv' with dialect='Truku' validates cleanly.

    trv has two language identities in FormosanBank convention: 'Truku' (for
    dialect='Truku') and 'Seediq' (for the three Seediq Official dialects).
    This pins the fix for a prior bug where trv was hardcoded to 'Seediq'
    and dialect='Truku' falsely triggered V036 across all published Truku
    corpus files.
    """
    copy_fixture(fixtures_dir / "valid_trv_truku.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation for trv+Truku; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


def test_V036_missing_dialect_is_negative(tmp_path, fixtures_dir, copy_fixture):
    """V036 negative: TEXT/@dialect is REQUIRED under the new convention.

    A missing dialect attribute must produce a HARD V036 finding. The
    "unknown" sentinel exists specifically to let authors record "we
    don't know the dialect" without leaving the attribute off, which
    used to be indistinguishable from "we forgot".
    """
    copy_fixture(fixtures_dir / "v036_TEXT_missing_dialect.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v036", "dialect")), (
        f"expected finding for missing dialect; got stdout={proc.stdout!r}"
    )


def test_V036_dialect_unknown_is_clean(tmp_path, fixtures_dir, copy_fixture):
    """V036 positive: dialect='unknown' is accepted for any language."""
    copy_fixture(fixtures_dir / "valid_dialect_unknown.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation for dialect='unknown'; "
        f"got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_V036_single_dialect_language_name_is_clean(tmp_path, fixtures_dir, copy_fixture):
    """V036 positive: single-dialect languages use the language name as dialect.

    e.g., xml:lang='tsu' (Tsou) must accept dialect='Tsou'. This is how
    single-dialect languages avoid branching code throughout the toolchain —
    every TEXT has a meaningful dialect value, even when there's only one.
    """
    copy_fixture(fixtures_dir / "valid_single_dialect_language_name.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"expected clean validation for xml:lang='tsu' dialect='Tsou'; "
        f"got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )


def test_V038_S_must_have_id_negative(tmp_path, fixtures_dir, copy_fixture):
    """V038: S without an id attribute is rejected by the schema."""
    copy_fixture(fixtures_dir / "v038_S_missing_id.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for missing S/@id; got stdout={proc.stdout!r}"
    )


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


def test_V051_AUDIO_empty_file_attr_negative(tmp_path, fixtures_dir, copy_fixture):
    """V051: AUDIO with file="" must produce a finding."""
    copy_fixture(fixtures_dir / "v051_AUDIO_empty_file_attr.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v051", "empty file", "empty audio/@file")), (
        f"expected finding for empty AUDIO/@file; got stdout={proc.stdout!r}"
    )


def test_V052_single_file_mode_missing_start_end_negative(tmp_path, fixtures_dir, copy_fixture):
    """V052: AUDIO with no file, in single-file mode, must have start/end."""
    copy_fixture(fixtures_dir / "v052_single_file_missing_start_end.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v052", "single-file mode", "missing start", "missing end")), (
        f"expected finding for missing AUDIO start/end in single-file mode; "
        f"got stdout={proc.stdout!r}"
    )


def test_V053_orphan_AUDIO_negative(tmp_path, fixtures_dir, copy_fixture):
    """V053: AUDIO with no @file and no TEXT/@audio is unmoored."""
    copy_fixture(fixtures_dir / "v053_orphan_AUDIO.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v053", "orphan audio", "unmoored")), (
        f"expected finding for orphan AUDIO; got stdout={proc.stdout!r}"
    )


def test_V054_AUDIO_end_before_start_negative(tmp_path, fixtures_dir, copy_fixture):
    """V054: AUDIO end < start must produce a finding."""
    copy_fixture(fixtures_dir / "v054_AUDIO_end_before_start.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v054", "end < start", "end before start", "end >= start")), (
        f"expected finding for AUDIO end < start; got stdout={proc.stdout!r}"
    )


def test_V056_AUDIO_under_TEXT_positive(tmp_path, fixtures_dir, copy_fixture):
    """V056 (positive): AUDIO under TEXT validates cleanly.

    DTD updated in Phase 4 to allow AUDIO under TEXT (and M); previously
    DTD only permitted AUDIO under S/W. Flipped from xfail to plain-pass
    when the DTD change landed.
    """
    copy_fixture(fixtures_dir / "v056_AUDIO_under_TEXT.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _is_clean(proc), (
        f"V056: AUDIO directly under TEXT should be valid; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )


# -----------------------------------------------------------------------------
# W/M segmentation: V062
# (V062 was moved to QC/validation/rules/gloss.py during B9.3; it is
# exercised by validate_glosses.py, not validate_xml.py. The positive
# test stays here as a regression: a well-formed file with an infix M
# correctly paired with an angle-bracket gloss must still validate
# cleanly under validate_xml.py. The negative test moved to
# tests/validators/test_validate_glosses.py.)
# -----------------------------------------------------------------------------


def test_V062_infix_M_with_angle_gloss_positive(tmp_path, fixtures_dir, copy_fixture):
    """V062 (positive): infix M FORM correctly paired with angle-bracket gloss.

    A well-formed pairing of infix-shaped M FORM ("-um-") and a W TRANSL
    containing "<AV>" must validate cleanly under validate_xml.py
    (V062 no longer participates here; nothing else should fire).
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


def test_V070_PHON_directly_under_TEXT_negative(tmp_path, fixtures_dir, copy_fixture):
    """V070: PHON directly under TEXT (illegal placement)."""
    copy_fixture(fixtures_dir / "v070_PHON_directly_under_TEXT.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v070", "phon placement", "phon must be a child")), (
        f"expected finding about PHON placement; got stdout={proc.stdout!r}"
    )


def test_V071_PHON_invalid_kindOf_negative(tmp_path, fixtures_dir, copy_fixture):
    """V071: PHON kindOf="alternate" is not a valid value."""
    copy_fixture(fixtures_dir / "v071_PHON_invalid_kindOf.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v071", "phon kindof", "phon/@kindof")), (
        f"expected finding about invalid PHON kindOf; got stdout={proc.stdout!r}"
    )


def test_V072_duplicate_PHON_kindOf_negative(tmp_path, fixtures_dir, copy_fixture):
    """V072: two PHON kindOf="original" siblings under the same parent."""
    copy_fixture(fixtures_dir / "v072_duplicate_PHON_kindOf.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v072", "duplicate phon")), (
        f"expected finding about duplicate PHON kindOf; got stdout={proc.stdout!r}"
    )


def test_V073_PHON_empty_content_negative(tmp_path, fixtures_dir, copy_fixture):
    """V073: PHON with empty text content."""
    copy_fixture(fixtures_dir / "v073_PHON_empty_content.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_rule_finding(proc, ("v073", "empty phon", "phon is empty")), (
        f"expected finding about empty PHON content; got stdout={proc.stdout!r}"
    )


def test_V073_PHON_empty_when_sister_FORM_is_null_OK():
    """V073: empty PHON is OK when the parent's FORM[@kindOf='original'] is '∅'.

    Rule-level test (in-memory): a null morpheme has no phonological
    content by definition. Both original and standard PHON of a null
    morpheme are legitimately empty, so V073 must not fire for either.
    Confirmed by Joshua's request on 2026-06-01.
    """
    from io import BytesIO
    from lxml import etree as _etree

    from QC.validation.rules import hard as hard_rules

    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
        'copyright="t" xml:lang="ami">'
        '<S id="S1">'
        '<FORM kindOf="original">a ∅ b</FORM>'
        '<FORM kindOf="standard">a ∅ b</FORM>'
        '<W id="W1">'
        '<FORM kindOf="original">∅</FORM>'
        '<FORM kindOf="standard">∅</FORM>'
        '<PHON kindOf="original"></PHON>'
        '<PHON kindOf="standard"></PHON>'
        '<M id="M1">'
        '<FORM kindOf="original">∅</FORM>'
        '<FORM kindOf="standard">∅</FORM>'
        '<PHON kindOf="original"></PHON>'
        '<PHON kindOf="standard"></PHON>'
        '</M>'
        '</W>'
        '</S>'
        '</TEXT>'
    )
    tree = _etree.parse(BytesIO(xml.encode("utf-8")))
    findings = hard_rules.v073_phon_non_empty(tree, Path("test.xml"), None)
    assert findings == [], (
        f"V073 should not fire when sister FORM is '∅'; got {findings!r}"
    )


def test_V073_PHON_empty_when_sister_FORM_is_non_null_negative():
    """V073: empty PHON when sister FORM has real content (no '∅') still fires."""
    from io import BytesIO
    from lxml import etree as _etree

    from QC.validation.rules import hard as hard_rules

    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
        'copyright="t" xml:lang="ami">'
        '<S id="S1">'
        '<FORM kindOf="original">halo</FORM>'
        '<PHON kindOf="original"></PHON>'
        '</S>'
        '</TEXT>'
    )
    tree = _etree.parse(BytesIO(xml.encode("utf-8")))
    findings = hard_rules.v073_phon_non_empty(tree, Path("test.xml"), None)
    assert len(findings) == 1, (
        f"V073 should fire when sister FORM has real content; got {findings!r}"
    )


# -----------------------------------------------------------------------------
# Cross-corpus: V081, V083
# -----------------------------------------------------------------------------


def test_V081_cross_corpus_TEXT_id_collision_negative(tmp_path, fixtures_dir, copy_fixture):
    """V081: a fixture whose TEXT/@id is also present in published Corpora.

    The fixture uses 'Yedda_Ljeljeng_lja_Palemek's_Blog', which is a real
    id in Corpora/YeddaPalemeqBlog/XML/Paiwan/Paiwan_Yedda_Blog.xml.
    When validate_xml.py implements V081, it should walk
    FormosanBank/Corpora/ and surface the collision.
    """
    copy_fixture(fixtures_dir / "v081_TEXT_id_collides_with_published.xml", tmp_path)
    proc = _run_validate(tmp_path, published_corpora=_CORPORA_ROOT)
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


# -----------------------------------------------------------------------------
# Regression: comprehensive_test.xml
#
# Joshua maintains tests/fixtures/comprehensive_test.xml as a real-world
# example carrying many distinct issues. The fixture grows over time as
# new patterns surface; this test asserts the CURRENTLY-FLAGGED set is
# always a SUBSET of what fires. New findings are fine — silently
# dropping any of these is a regression.
# -----------------------------------------------------------------------------


def test_comprehensive_test_xml_regression():
    """Lock in validate_xml.py findings on comprehensive_test.xml.

    When Joshua adds new examples, add the corresponding (rule, marker)
    pair below. When a rule is renamed or restructured, update the
    marker — but don't delete the entry until the underlying issue is
    actually resolved in the fixture.
    """
    fixture = _REPO_ROOT / "tests" / "fixtures" / "comprehensive_test.xml"
    assert fixture.exists(), f"comprehensive fixture missing at {fixture}"
    csv_out = "/tmp/comprehensive_xml_soft.csv"
    proc = subprocess.run(
        [
            sys.executable, str(VALIDATE_XML),
            "--published-corpora", str(_CORPORA_ROOT),
            "by_path", "--path", str(fixture),
            "--csv", csv_out,
        ],
        capture_output=True,
        text=True,
    )
    # Per-finding detail (rule ids, offending element ids, messages) now lives
    # in the CSV, not on the terminal. Match against the CSV contents.
    combined = Path(csv_out).read_text(encoding="utf-8").lower()
    # (rule_id, identifying marker) — both must appear in the CSV.
    expected: tuple[tuple[str, str], ...] = (
        # V000 schema: duplicated id key-sequences (multiple lines).
        ("v000", "duplicate key-sequence"),
        # V017 empty FORM at the typo'd id "ap3_S_2_W0_M0_0a".
        ("v017", "ap3_s_2_w0_m0_0a"),
        # V039 duplicate-id collisions (many; sample one as a marker).
        ("v039", "ap3_s_2_w0"),
        # V085 duplicate TRANSL xml:lang without `ver` at ap3_S_2.
        ("v085", "ap3_s_2"),
        # V081 cross-corpus TEXT id collision.
        ("v081", "id collision"),
    )
    missing: list[tuple[str, str]] = []
    for rule, marker in expected:
        if rule not in combined or marker not in combined:
            missing.append((rule, marker))
    assert not missing, (
        f"comprehensive_test.xml regression: missing expected findings "
        f"{missing!r}; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_V083_schema_validation_negative(tmp_path, fixtures_dir, copy_fixture):
    """V083: a file with an unknown child element (FOO) fails schema validation."""
    copy_fixture(fixtures_dir / "v083_unknown_child_element.xml", tmp_path)
    proc = _run_validate(tmp_path)
    assert _has_finding(proc), (
        f"expected finding for unknown child element; got stdout={proc.stdout!r}, "
        f"stderr={proc.stderr!r}"
    )
