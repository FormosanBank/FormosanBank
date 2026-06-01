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
# V060: W-count vs. word-count (SOFT)
# ---------------------------------------------------------------------------


def test_V060_matching_W_and_word_count_clean():
    """Clean S: 3 whitespace words and 3 direct W children -> no V060."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
        <W id="W2"><FORM kindOf="original">b</FORM></W>
        <W id="W3"><FORM kindOf="original">c</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert findings == [], f"expected no V060 finding; got {findings!r}"


def test_V060_mismatched_W_and_word_count_emits_SOFT():
    """3 words in FORM but 2 W children -> one SOFT V060 finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
        <W id="W2"><FORM kindOf="original">b</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert len(findings) == 1, f"expected 1 V060 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V060"
    assert f.severity is Severity.SOFT
    assert "S1" in f.location
    assert "3" in f.message and "2" in f.message


def test_V060_uses_original_FORM_in_preference_to_standard():
    """Original tier wins as the word-count source; standard tier ignored."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <FORM kindOf="standard">a b c d e</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
        <W id="W2"><FORM kindOf="original">b</FORM></W>
        <W id="W3"><FORM kindOf="original">c</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert findings == [], (
        f"V060 must use FORM[@kindOf='original'] (3 words) not standard "
        f"(5 words); got {findings!r}"
    )


def test_V060_no_FORM_at_all_emits_nothing():
    """S with no FORM at all: rule no-ops (V010/V013 handle that)."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <W id="W1"><FORM kindOf="original">a</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v060_W_count_matches_word_count, xml)
    assert findings == [], f"expected no V060 finding; got {findings!r}"


# ---------------------------------------------------------------------------
# V061: M-count vs. implied-morpheme-count (SOFT)
# ---------------------------------------------------------------------------


def test_V061_monomorphemic_with_no_M_clean():
    """W FORM 'ka' (1 morpheme) with 0 M children -> exception, no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ka</FORM>
        <W id="W1"><FORM kindOf="original">ka</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_hyphenated_with_matching_M_clean():
    """W FORM 'ika-doa' (2 morphemes) with 2 M children -> no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ika-doa</FORM>
        <W id="W1">
          <FORM kindOf="original">ika-doa</FORM>
          <M id="M1"><FORM>ika</FORM></M>
          <M id="M2"><FORM>doa</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_infix_with_matching_M_clean():
    """W FORM 'k<um>ita' (infix + root = 2 morphemes) with 2 M -> no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">k&lt;um&gt;ita</FORM>
        <W id="W1">
          <FORM kindOf="original">k&lt;um&gt;ita</FORM>
          <M id="M1"><FORM>-um-</FORM></M>
          <M id="M2"><FORM>kita</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_infix_with_too_few_M_emits_SOFT():
    """W FORM 'k<um>ita' (expected 2) with only 1 M -> SOFT V061."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">k&lt;um&gt;ita</FORM>
        <W id="W1">
          <FORM kindOf="original">k&lt;um&gt;ita</FORM>
          <M id="M1"><FORM>kita</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert len(findings) == 1, f"expected 1 V061 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V061"
    assert f.severity is Severity.SOFT
    assert "W1" in f.location


def test_V061_clitic_boundary_clean():
    """W FORM 'ma=luhay' (= boundary, 2 morphemes) with 2 M -> no finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">ma=luhay</FORM>
        <W id="W1">
          <FORM kindOf="original">ma=luhay</FORM>
          <M id="M1"><FORM>ma</FORM></M>
          <M id="M2"><FORM>luhay</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


def test_V061_W_with_no_FORM_emits_nothing():
    """W with no FORM at all: rule no-ops (V011 handles missing FORM)."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">x</FORM>
        <W id="W1"></W>
      </S>""")
    findings = _findings_for(gloss_rules.v061_M_count_matches_form_segmentation, xml)
    assert findings == [], f"expected no V061 finding; got {findings!r}"


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


# ---------------------------------------------------------------------------
# V063: W-FORM segmentation preservation (HARD)
# ---------------------------------------------------------------------------


def test_V063_low_marker_count_below_threshold_emits_nothing():
    """S-level FORM has 3 markers (not > 3) -> V063 does not fire."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">M-kan =ku n-hapuy.</FORM>
        <W id="W1"><FORM kindOf="original">M-kan</FORM><FORM kindOf="standard">M-kan</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v063_W_FORM_retains_segmentation, xml)
    assert findings == [], (
        f"V063 should not fire when S-FORM has <=3 markers; got {findings!r}"
    )


def test_V063_above_threshold_with_preserved_markers_clean():
    """S has 5 markers (>3); W-original and W-standard each retain >=3 -> clean."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">Pa-rakat-en =ku n-hapuy=mu</FORM>
        <W id="W1">
          <FORM kindOf="original">Pa-rakat-en</FORM>
          <FORM kindOf="standard">Pa-rakat-en</FORM>
        </W>
        <W id="W2">
          <FORM kindOf="original">=ku</FORM>
          <FORM kindOf="standard">=ku</FORM>
        </W>
        <W id="W3">
          <FORM kindOf="original">n-hapuy=mu</FORM>
          <FORM kindOf="standard">n-hapuy=mu</FORM>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v063_W_FORM_retains_segmentation, xml)
    assert findings == [], f"expected no V063 findings; got {findings!r}"


def test_V063_above_threshold_with_stripped_original_emits_HARD():
    """S has 5 markers; W-original retains 0 -> HARD V063."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">Pa-rakat-en =ku n-hapuy=mu</FORM>
        <W id="W1">
          <FORM kindOf="original">Parakaten</FORM>
          <FORM kindOf="standard">Pa-rakat-en</FORM>
        </W>
        <W id="W2">
          <FORM kindOf="original">ku</FORM>
          <FORM kindOf="standard">=ku</FORM>
        </W>
        <W id="W3">
          <FORM kindOf="original">nhapuymu</FORM>
          <FORM kindOf="standard">n-hapuy=mu</FORM>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v063_W_FORM_retains_segmentation, xml)
    assert any(f.rule_id == "V063" and f.severity is Severity.HARD for f in findings), (
        f"expected at least one HARD V063 finding for stripped W-original; "
        f"got {findings!r}"
    )


def test_V063_above_threshold_with_stripped_standard_emits_HARD():
    """S has 5 markers; W-standard retains 0 -> HARD V063."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">Pa-rakat-en =ku n-hapuy=mu</FORM>
        <W id="W1">
          <FORM kindOf="original">Pa-rakat-en</FORM>
          <FORM kindOf="standard">Parakaten</FORM>
        </W>
        <W id="W2">
          <FORM kindOf="original">=ku</FORM>
          <FORM kindOf="standard">ku</FORM>
        </W>
        <W id="W3">
          <FORM kindOf="original">n-hapuy=mu</FORM>
          <FORM kindOf="standard">nhapuymu</FORM>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v063_W_FORM_retains_segmentation, xml)
    assert any(f.rule_id == "V063" and f.severity is Severity.HARD for f in findings), (
        f"expected at least one HARD V063 finding for stripped W-standard; "
        f"got {findings!r}"
    )


def test_V063_S_with_no_W_children_no_ops():
    """Legitimately unsegmented S (no W children) -> rule no-ops."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a-b-c=d-e</FORM>
      </S>""")
    findings = _findings_for(gloss_rules.v063_W_FORM_retains_segmentation, xml)
    assert findings == [], f"expected no V063 finding; got {findings!r}"


def test_V063_S_with_no_segmentation_markers_no_ops():
    """S-FORM has 0 markers -> rule no-ops."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">abc def</FORM>
        <W id="W1">
          <FORM kindOf="original">abc</FORM>
          <FORM kindOf="standard">abc</FORM>
        </W>
        <W id="W2">
          <FORM kindOf="original">def</FORM>
          <FORM kindOf="standard">def</FORM>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v063_W_FORM_retains_segmentation, xml)
    assert findings == [], f"expected no V063 finding; got {findings!r}"


# ---------------------------------------------------------------------------
# V064: every M has TRANSL (HARD)
# ---------------------------------------------------------------------------


def test_V064_M_with_TRANSL_clean():
    """Every M with a TRANSL child -> no V064."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a-b</FORM>
        <W id="W1">
          <FORM kindOf="original">a-b</FORM>
          <M id="M1"><FORM>a</FORM><TRANSL xml:lang="eng">A</TRANSL></M>
          <M id="M2"><FORM>b</FORM><TRANSL xml:lang="eng">B</TRANSL></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v064_every_M_has_TRANSL, xml)
    assert findings == [], f"expected no V064 finding; got {findings!r}"


def test_V064_one_M_missing_TRANSL_emits_one_HARD():
    """One M lacks TRANSL -> one HARD V064 citing that M's id."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a-b</FORM>
        <W id="W1">
          <FORM kindOf="original">a-b</FORM>
          <M id="M1"><FORM>a</FORM><TRANSL xml:lang="eng">A</TRANSL></M>
          <M id="M2"><FORM>b</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v064_every_M_has_TRANSL, xml)
    assert len(findings) == 1, f"expected 1 V064 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V064"
    assert f.severity is Severity.HARD
    assert "M2" in f.location


def test_V064_all_M_missing_TRANSL_emits_per_M():
    """All M missing TRANSL -> one Finding per M."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a-b</FORM>
        <W id="W1">
          <FORM kindOf="original">a-b</FORM>
          <M id="M1"><FORM>a</FORM></M>
          <M id="M2"><FORM>b</FORM></M>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v064_every_M_has_TRANSL, xml)
    assert len(findings) == 2, f"expected 2 V064 findings; got {findings!r}"
    locations = {f.location for f in findings}
    assert "M=M1" in locations
    assert "M=M2" in locations


def test_V064_no_M_at_all_no_ops():
    """W with no M children -> V064 doesn't fire."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v064_every_M_has_TRANSL, xml)
    assert findings == [], f"expected no V064 finding; got {findings!r}"


# ---------------------------------------------------------------------------
# V065: every W has TRANSL (SOFT)
# ---------------------------------------------------------------------------


def test_V065_W_with_TRANSL_clean():
    """W with a TRANSL child -> no V065."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a</FORM>
        <W id="W1">
          <FORM kindOf="original">a</FORM>
          <TRANSL xml:lang="eng">A</TRANSL>
        </W>
      </S>""")
    findings = _findings_for(gloss_rules.v065_every_W_has_TRANSL, xml)
    assert findings == [], f"expected no V065 finding; got {findings!r}"


def test_V065_W_without_TRANSL_emits_SOFT():
    """W with no TRANSL -> SOFT V065 finding."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM></W>
      </S>""")
    findings = _findings_for(gloss_rules.v065_every_W_has_TRANSL, xml)
    assert len(findings) == 1, f"expected 1 V065 finding; got {findings!r}"
    f = findings[0]
    assert f.rule_id == "V065"
    assert f.severity is Severity.SOFT
    assert "W1" in f.location


def test_V065_no_W_at_all_no_ops():
    """Unsegmented S (no W) -> V065 doesn't fire."""
    xml = _TEXT_TEMPLATE.format(body="""
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
      </S>""")
    findings = _findings_for(gloss_rules.v065_every_W_has_TRANSL, xml)
    assert findings == [], f"expected no V065 finding; got {findings!r}"


# ---------------------------------------------------------------------------
# Orchestrator-level: validate_glosses.py (W4)
# ---------------------------------------------------------------------------


def _write_xml(target_dir: Path, basename: str, body: str) -> Path:
    """Materialize an XML fixture from inline body into target_dir/XML/."""
    xml_dir = target_dir / "XML"
    xml_dir.mkdir(parents=True, exist_ok=True)
    path = xml_dir / basename
    path.write_text(_TEXT_TEMPLATE.format(body=body), encoding="utf-8")
    return path


def _run_validate_glosses(
    xml_folder: Path,
    output_dir: Path | None = None,
    extra_args: tuple[str, ...] = (),
) -> subprocess.CompletedProcess:
    """Invoke validate_glosses.py as a subprocess."""
    cmd = [
        sys.executable,
        str(VALIDATE_GLOSSES),
        "by_path",
        "--path",
        str(xml_folder),
    ]
    if output_dir is not None:
        cmd.extend(["--output_dir", str(output_dir)])
    cmd.extend(extra_args)
    return subprocess.run(cmd, capture_output=True, text=True)


def test_validate_glosses_clean_fixture_zero_findings(tmp_path):
    """Clean fixture: validate_glosses.py exits 0, emits no findings.

    Specifically:
    - exit code 0
    - validation_results.csv is either absent or header-only
    - validation_m_mismatches.csv is either absent or header-only
    """
    _write_xml(tmp_path, "clean.xml", """
      <S id="S1">
        <FORM kindOf="original">a b</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM><TRANSL xml:lang="eng">A</TRANSL></W>
        <W id="W2"><FORM kindOf="original">b</FORM><TRANSL xml:lang="eng">B</TRANSL></W>
      </S>""")
    out = tmp_path / "out"
    proc = _run_validate_glosses(tmp_path / "XML", output_dir=out)
    assert proc.returncode == 0, (
        f"clean fixture should pass; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    w_csv = out / "validation_results.csv"
    m_csv = out / "validation_m_mismatches.csv"
    for csv_path in (w_csv, m_csv):
        if csv_path.exists():
            lines = [
                l for l in csv_path.read_text(encoding="utf-8").splitlines() if l.strip()
            ]
            # Header may or may not be written when there are no rows;
            # either way there must be no data rows.
            assert len(lines) <= 1, (
                f"{csv_path.name} unexpectedly has data rows: {lines!r}"
            )


def test_validate_glosses_W_mismatch_emits_finding_and_csv_row(tmp_path):
    """W-count mismatch -> SOFT V060 + row in validation_results.csv. Exit 0."""
    _write_xml(tmp_path, "wmm.xml", """
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <W id="W1"><FORM kindOf="original">a</FORM><TRANSL xml:lang="eng">A</TRANSL></W>
        <W id="W2"><FORM kindOf="original">b</FORM><TRANSL xml:lang="eng">B</TRANSL></W>
      </S>""")
    out = tmp_path / "out"
    proc = _run_validate_glosses(tmp_path / "XML", output_dir=out)
    assert proc.returncode == 0, (
        f"SOFT-only run should exit 0; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    w_csv = out / "validation_results.csv"
    assert w_csv.exists(), "validation_results.csv should exist"
    contents = w_csv.read_text(encoding="utf-8")
    assert "S1" in contents, f"expected S1 row in CSV; got {contents!r}"


def test_validate_glosses_M_mismatch_emits_finding_and_csv_row(tmp_path):
    """M-count mismatch -> SOFT V061 + row in validation_m_mismatches.csv. Exit 0."""
    _write_xml(tmp_path, "mmm.xml", """
      <S id="S1">
        <FORM kindOf="original">k&lt;um&gt;ita</FORM>
        <W id="W1">
          <FORM kindOf="original">k&lt;um&gt;ita</FORM>
          <TRANSL xml:lang="eng">walk &lt;AV&gt;</TRANSL>
          <M id="M1"><FORM>kita</FORM><TRANSL xml:lang="eng">walk</TRANSL></M>
        </W>
      </S>""")
    out = tmp_path / "out"
    proc = _run_validate_glosses(tmp_path / "XML", output_dir=out)
    assert proc.returncode == 0, (
        f"SOFT-only run should exit 0; stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    m_csv = out / "validation_m_mismatches.csv"
    assert m_csv.exists(), "validation_m_mismatches.csv should exist"
    contents = m_csv.read_text(encoding="utf-8")
    assert "W1" in contents, f"expected W1 row in CSV; got {contents!r}"


def test_validate_glosses_HARD_V062_causes_nonzero_exit(tmp_path):
    """A HARD V062 violation causes a nonzero exit code."""
    _write_xml(tmp_path, "v062.xml", """
      <S id="S1">
        <FORM kindOf="original">rumakat</FORM>
        <W id="W1">
          <FORM kindOf="original">rumakat</FORM>
          <TRANSL xml:lang="eng">walk</TRANSL>
          <M id="M1"><FORM>-um-</FORM><TRANSL xml:lang="eng">AV</TRANSL></M>
          <M id="M2"><FORM>rkt</FORM><TRANSL xml:lang="eng">walk</TRANSL></M>
        </W>
      </S>""")
    out = tmp_path / "out"
    proc = _run_validate_glosses(tmp_path / "XML", output_dir=out)
    assert proc.returncode != 0, (
        f"HARD V062 should cause nonzero exit; got rc={proc.returncode}, "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    combined = (proc.stdout + proc.stderr).lower()
    assert "v062" in combined, (
        f"expected V062 mention; got stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )


def test_validate_glosses_check_morpho_flag(tmp_path):
    """--check_morpho still works: legacy 'has_morphemes' column appears."""
    # W3 has no M children -> should be flagged with has_morphemes='F'.
    # Also creates a V060 SOFT (3 words vs 3 W, but the rule fires on
    # check_morpho=True even when word/W counts match because at least
    # one W lacks M children, mirroring the legacy condition).
    _write_xml(tmp_path, "morpho.xml", """
      <S id="S1">
        <FORM kindOf="original">a b c</FORM>
        <W id="W1">
          <FORM kindOf="original">a</FORM>
          <TRANSL xml:lang="eng">A</TRANSL>
          <M id="M1"><FORM>a</FORM><TRANSL xml:lang="eng">A</TRANSL></M>
        </W>
        <W id="W2">
          <FORM kindOf="original">b</FORM>
          <TRANSL xml:lang="eng">B</TRANSL>
          <M id="M2"><FORM>b</FORM><TRANSL xml:lang="eng">B</TRANSL></M>
        </W>
        <W id="W3">
          <FORM kindOf="original">c</FORM>
          <TRANSL xml:lang="eng">C</TRANSL>
        </W>
      </S>""")
    out = tmp_path / "out"
    proc = _run_validate_glosses(
        tmp_path / "XML", output_dir=out, extra_args=("--check_morpho",)
    )
    # SOFT-only run; exit should be 0.
    assert proc.returncode == 0, (
        f"--check_morpho SOFT-only run should exit 0; rc={proc.returncode}, "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    w_csv = out / "validation_results.csv"
    if w_csv.exists():
        contents = w_csv.read_text(encoding="utf-8")
        # Header should reflect the check_morpho column.
        assert "has_morphemes" in contents.splitlines()[0], (
            f"expected has_morphemes column header; got {contents!r}"
        )
