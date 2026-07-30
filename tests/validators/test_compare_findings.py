"""Tests for baseline-aware validator finding comparison."""

import csv
from pathlib import Path

from QC.validation.compare_findings import new_findings


FIELDS = (
    "file",
    "line",
    "severity",
    "rule_id",
    "title",
    "location",
    "language",
    "character",
    "count",
    "message",
)


def _write_findings(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _finding(
    *,
    rule_id: str = "V066",
    location: str = "S=S1 W=W1",
    severity: str = "HARD",
    file: str = "candidate.xml",
) -> dict[str, str]:
    return {
        "file": file,
        "line": "",
        "severity": severity,
        "rule_id": rule_id,
        "title": "example",
        "location": location,
        "language": "",
        "character": "",
        "count": "1",
        "message": "detail that may differ without changing finding identity",
    }


def test_unchanged_finding_is_not_new(tmp_path):
    baseline = _write_findings(
        tmp_path / "baseline.csv", [_finding(file="baseline.xml")]
    )
    candidate = _write_findings(
        tmp_path / "candidate.csv", [_finding(file="candidate.xml")]
    )

    assert not new_findings(baseline, candidate)


def test_new_rule_or_location_is_reported(tmp_path):
    baseline = _write_findings(tmp_path / "baseline.csv", [_finding()])
    candidate = _write_findings(
        tmp_path / "candidate.csv",
        [_finding(), _finding(rule_id="V067", location="S=S2 W=W2")],
    )

    introduced = new_findings(baseline, candidate)

    assert sum(introduced.values()) == 1
    assert next(iter(introduced))[0:2] == ("V067", "S=S2 W=W2")


def test_duplicate_count_increase_is_reported(tmp_path):
    baseline = _write_findings(tmp_path / "baseline.csv", [_finding()])
    candidate = _write_findings(
        tmp_path / "candidate.csv", [_finding(), _finding()]
    )

    assert sum(new_findings(baseline, candidate).values()) == 1


def test_added_file_uses_empty_baseline(tmp_path):
    candidate = _write_findings(tmp_path / "candidate.csv", [_finding()])

    assert sum(new_findings(None, candidate).values()) == 1
