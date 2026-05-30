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
