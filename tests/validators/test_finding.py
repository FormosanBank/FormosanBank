"""Unit tests for Finding and Severity."""
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from QC.validation._finding import Finding, Severity


def test_severity_values():
    assert Severity.HARD.value == "HARD"
    assert Severity.SOFT.value == "SOFT"
    assert Severity.WARN.value == "WARN"


def test_finding_minimal_construction():
    f = Finding(
        rule_id="V001",
        severity=Severity.HARD,
        message="root tag is 'NOT_TEXT', expected 'TEXT'",
        path=Path("/tmp/foo.xml"),
    )
    assert f.rule_id == "V001"
    assert f.severity is Severity.HARD
    assert f.location is None
    assert f.count == 1
    assert f.language is None
    assert f.character is None


def test_finding_with_location():
    f = Finding(
        rule_id="V015",
        severity=Severity.HARD,
        message="duplicate kindOf='original'",
        path=Path("/tmp/foo.xml"),
        location="S=ami_chapter01_S0042",
    )
    assert f.location == "S=ami_chapter01_S0042"


def test_finding_soft_with_aggregation():
    f = Finding(
        rule_id="V014",
        severity=Severity.SOFT,
        message="missing standard tier",
        path=Path("/tmp/foo.xml"),
        count=42,
        language="ami",
        character="",
    )
    assert f.count == 42
    assert f.language == "ami"
    assert f.character == ""


def test_finding_is_frozen():
    f = Finding(
        rule_id="V001",
        severity=Severity.HARD,
        message="msg",
        path=Path("/tmp/foo.xml"),
    )
    with pytest.raises(FrozenInstanceError):
        f.rule_id = "V002"


def test_finding_equality():
    a = Finding(rule_id="V001", severity=Severity.HARD, message="m", path=Path("/x.xml"))
    b = Finding(rule_id="V001", severity=Severity.HARD, message="m", path=Path("/x.xml"))
    assert a == b


import csv


def test_write_soft_csv_empty(tmp_path):
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "soft.csv"
    write_soft_csv(out, [])
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    # SOFT_CSV columns were extended on 2026-06-01 to add `location` and
    # `line`, so per-occurrence rules can pin each row to a specific
    # S/W/M element. Aggregated rules leave these blank.
    assert rows == [
        ["file", "rule_id", "location", "line", "language", "character", "count"]
    ]


def test_write_soft_csv_one_finding(tmp_path):
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "soft.csv"
    findings = [
        Finding(
            rule_id="V014",
            severity=Severity.SOFT,
            message="missing standard tier",
            path=Path("/abs/path/to/ami_chapter01.xml"),
            count=3,
            language="ami",
            character="",
        ),
    ]
    write_soft_csv(out, findings)
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    # No location/line on this finding (aggregated rule shape) -> blank.
    assert rows == [
        ["file", "rule_id", "location", "line", "language", "character", "count"],
        ["/abs/path/to/ami_chapter01.xml", "V014", "", "", "ami", "", "3"],
    ]


def test_write_soft_csv_skips_non_soft(tmp_path):
    """write_soft_csv is the SOFT writer; HARD/WARN findings are not
    its concern even if accidentally passed in."""
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "soft.csv"
    findings = [
        Finding(rule_id="V001", severity=Severity.HARD, message="m", path=Path("/x.xml")),
        Finding(rule_id="V014", severity=Severity.SOFT, message="m",
                path=Path("/y.xml"), count=2, language="ami", character=""),
        Finding(rule_id="V088", severity=Severity.WARN, message="m", path=Path("/z.xml")),
    ]
    write_soft_csv(out, findings)
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 2
    assert rows[1][1] == "V014"


def test_write_soft_csv_creates_parent_dir(tmp_path):
    """If the requested output path's parent does not exist, it is created."""
    from QC.validation._finding import write_soft_csv

    out = tmp_path / "logs" / "subdir" / "soft.csv"
    write_soft_csv(out, [])
    assert out.exists()


# --- summarize ---------------------------------------------------------------


def test_summarize_empty():
    from QC.validation._finding import summarize

    assert summarize([]) == {Severity.HARD: {}, Severity.SOFT: {}, Severity.WARN: {}}


def test_summarize_counts_by_rule_within_severity():
    from QC.validation._finding import summarize

    findings = [
        Finding("V064", Severity.HARD, "m", Path("/a.xml")),
        Finding("V064", Severity.HARD, "m", Path("/a.xml")),
        Finding("V000", Severity.HARD, "m", Path("/a.xml")),
        Finding("V116", Severity.SOFT, "m", Path("/a.xml"), count=7),
        Finding("V068", Severity.SOFT, "m", Path("/a.xml"), count=1),
    ]
    s = summarize(findings)
    assert s[Severity.HARD] == {"V064": 2, "V000": 1}
    assert s[Severity.SOFT] == {"V116": 7, "V068": 1}
    assert s[Severity.WARN] == {}


def test_summarize_sums_count_field_across_aggregated_soft_rows():
    from QC.validation._finding import summarize

    findings = [
        Finding("V116", Severity.SOFT, "m", Path("/a.xml"), count=3),
        Finding("V116", Severity.SOFT, "m", Path("/b.xml"), count=4),
    ]
    assert summarize(findings)[Severity.SOFT] == {"V116": 7}


# --- write_findings_csv (all severities, one CSV) ----------------------------


def test_write_findings_csv_header_only_when_empty(tmp_path):
    from QC.validation._finding import write_findings_csv

    out = tmp_path / "f.csv"
    write_findings_csv(out, [])
    with open(out, newline="") as f:
        rows = list(csv.reader(f))
    assert rows == [[
        "file", "line", "severity", "rule_id", "title", "location",
        "language", "character", "count", "message",
    ]]


def test_write_findings_csv_fills_title_column_from_map(tmp_path):
    from QC.validation._finding import write_findings_csv

    findings = [Finding("V068", Severity.SOFT, "m", Path("/a.xml"))]
    out = tmp_path / "f.csv"
    write_findings_csv(out, findings, titles={"V068": "M_reconstructs_W"})
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["title"] == "M_reconstructs_W"


def test_write_findings_csv_blank_title_when_unmapped(tmp_path):
    from QC.validation._finding import write_findings_csv

    findings = [Finding("V999", Severity.SOFT, "m", Path("/a.xml"))]
    out = tmp_path / "f.csv"
    write_findings_csv(out, findings, titles={})  # no entry for V999
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["title"] == ""


def test_write_findings_csv_includes_both_hard_and_soft(tmp_path):
    from QC.validation._finding import write_findings_csv

    findings = [
        Finding("V064", Severity.HARD, "M has no TRANSL child",
                Path("/a.xml"), location="M=s1w2m3", line=88),
        Finding("V116", Severity.SOFT, "non-ASCII 'ə' in FORM",
                Path("/a.xml"), count=7, language="bnn", character="ə"),
    ]
    out = tmp_path / "f.csv"
    write_findings_csv(out, findings)
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 2
    assert rows[0]["severity"] == "HARD" and rows[0]["rule_id"] == "V064"
    assert rows[0]["location"] == "M=s1w2m3" and rows[0]["line"] == "88"
    assert rows[0]["message"] == "M has no TRANSL child"
    assert rows[1]["severity"] == "SOFT" and rows[1]["count"] == "7"
    assert rows[1]["character"] == "ə" and rows[1]["language"] == "bnn"


def test_write_findings_csv_quotes_message_with_commas(tmp_path):
    from QC.validation._finding import write_findings_csv

    findings = [Finding("V068", Severity.SOFT,
                        "reconstruct only 41%, W FORM='a,b'", Path("/a.xml"))]
    out = tmp_path / "f.csv"
    write_findings_csv(out, findings)
    with open(out, newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["message"] == "reconstruct only 41%, W FORM='a,b'"


def test_write_findings_csv_creates_parent_dir(tmp_path):
    from QC.validation._finding import write_findings_csv

    out = tmp_path / "logs" / "sub" / "f.csv"
    write_findings_csv(out, [])
    assert out.exists()
