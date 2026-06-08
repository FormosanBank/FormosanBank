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
