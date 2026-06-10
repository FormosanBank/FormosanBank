"""Tests for QC/validation/_report.report_findings.

The shared reporter prints a compact per-rule count summary (HARD then
SOFT) to a stream, writes the one detail CSV when there are findings, and
returns whether any HARD finding was present (for the caller's exit code).
"""
import io
from pathlib import Path

from QC.validation._finding import Finding, Severity
from QC.validation._report import report_findings


def _run(findings, csv_path, file_count, titles=None):
    buf = io.StringIO()
    has_hard = report_findings(
        findings, csv_path, file_count=file_count, out=buf, titles=titles
    )
    return has_hard, buf.getvalue()


def test_clean_run_writes_header_csv_but_prints_no_details_line(tmp_path):
    # Contract: the CSV is ALWAYS written (header-only when clean) so CI
    # artifact uploads stay robust, but the terminal stays minimal — no
    # per-rule sections and no "Details:" line on a clean run.
    csv_path = tmp_path / "f.csv"
    has_hard, text = _run([], csv_path, file_count=3)
    assert has_hard is False
    assert "3 files, 0 with issues" in text
    assert "No issues found" in text
    assert "Details:" not in text
    assert csv_path.exists()  # header-only


def test_hard_and_soft_summary_and_csv(tmp_path):
    csv_path = tmp_path / "f.csv"
    findings = [
        Finding("V064", Severity.HARD, "m", Path("/a.xml"), location="M1"),
        Finding("V064", Severity.HARD, "m", Path("/a.xml"), location="M2"),
        Finding("V000", Severity.HARD, "m", Path("/a.xml")),
        Finding("V116", Severity.SOFT, "m", Path("/b.xml"), count=7),
    ]
    titles = {"V064": "every_M_has_TRANSL", "V000": "schema_validation",
              "V116": "non_ascii_in_form"}
    has_hard, text = _run(findings, csv_path, file_count=4, titles=titles)
    assert has_hard is True
    assert "4 files, 2 with issues" in text  # /a.xml and /b.xml
    assert "HARD — 3 total" in text
    # Summary lines carry the mnemonic next to the rule id.
    assert "V064 every_M_has_TRANSL: 2" in text
    assert "V000 schema_validation: 1" in text
    assert "SOFT — 7 total" in text
    assert "V116 non_ascii_in_form: 7" in text
    assert f"Details: {csv_path}" in text
    assert csv_path.exists()
    # ...and the CSV has a populated title column.
    import csv as _csv
    with open(csv_path, newline="") as fh:
        rows = list(_csv.DictReader(fh))
    assert {r["rule_id"]: r["title"] for r in rows}["V064"] == "every_M_has_TRANSL"


def test_soft_only_returns_false_and_omits_hard_section(tmp_path):
    csv_path = tmp_path / "f.csv"
    findings = [Finding("V068", Severity.SOFT, "m", Path("/a.xml"))]
    has_hard, text = _run(findings, csv_path, file_count=1)
    assert has_hard is False
    assert "HARD" not in text  # no HARD section when there are no HARD findings
    assert "SOFT — 1 total" in text
    assert csv_path.exists()


def test_rules_listed_sorted_within_severity(tmp_path):
    csv_path = tmp_path / "f.csv"
    findings = [
        Finding("V137", Severity.SOFT, "m", Path("/a.xml")),
        Finding("V110", Severity.SOFT, "m", Path("/a.xml")),
        Finding("V122", Severity.SOFT, "m", Path("/a.xml")),
    ]
    _, text = _run(findings, csv_path, file_count=1)
    assert text.index("V110") < text.index("V122") < text.index("V137")
