import csv

from QC.validation.compare_findings import new_findings


FIELDS = [
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
]


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _finding(file, severity="HARD", rule_id="V001"):
    return {
        "file": file,
        "line": "10",
        "severity": severity,
        "rule_id": rule_id,
        "title": "example",
        "location": "S=1",
        "language": "ami",
        "character": "",
        "count": "1",
        "message": "example finding",
    }


def test_ignores_existing_hard_findings_and_file_paths(tmp_path):
    current = tmp_path / "current.csv"
    baseline = tmp_path / "baseline.csv"
    _write(current, [_finding("Corpora/Test/current.xml")])
    _write(baseline, [_finding("/tmp/base.xml")])

    assert not new_findings(current, baseline)


def test_reports_only_new_hard_findings(tmp_path):
    current = tmp_path / "current.csv"
    baseline = tmp_path / "baseline.csv"
    _write(current, [_finding("file.xml"), _finding("file.xml", rule_id="V002")])
    _write(baseline, [_finding("base.xml")])

    added = new_findings(current, baseline)

    assert sum(added.values()) == 1
    assert next(iter(added))[0] == "V002"


def test_soft_findings_do_not_block(tmp_path):
    current = tmp_path / "current.csv"
    baseline = tmp_path / "baseline.csv"
    _write(current, [_finding("file.xml", severity="SOFT")])
    _write(baseline, [])

    assert not new_findings(current, baseline)
