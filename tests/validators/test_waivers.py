"""HARD-finding waivers: QC/validation/_waivers.py and waivers.py.

The mechanism's value is entirely in its refusals, so most of these tests
assert that something is rejected. A waiver file that accepts anything is a
blindfold, which is the outcome this whole feature exists to avoid.
"""
from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

from QC.validation._finding import Finding, Severity
from QC.validation._waivers import (
    TODO_REASON,
    WAIVABLE_RULES,
    WaiverError,
    apply_waivers,
    corpus_root_for,
    load_waivers,
    relative_xml_name,
    waiver_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
WAIVERS_CLI = REPO_ROOT / "QC" / "validation" / "waivers.py"

WAIVABLE = sorted(WAIVABLE_RULES)[0]


def _corpus(tmp_path: Path, rows: list[tuple[str, str, str, str]] | None = None) -> Path:
    """A minimal corpus: XML/<Lang>/<file>.xml plus CodeAndDocs/."""
    corpus = tmp_path / "Corpora" / "Demo"
    (corpus / "XML" / "Lang").mkdir(parents=True)
    (corpus / "CodeAndDocs").mkdir(parents=True)
    (corpus / "XML" / "Lang" / "d.xml").write_text("<TEXT/>", encoding="utf-8")
    if rows is not None:
        _write_waivers(corpus, rows)
    return corpus


def _write_waivers(corpus: Path, rows: list[tuple[str, str, str, str]]) -> Path:
    path = waiver_path(corpus)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(("rule_id", "file", "location", "reason"))
        writer.writerows(rows)
    return path


def _hard(corpus: Path, rule_id: str = WAIVABLE, location: str = "S=1") -> Finding:
    return Finding(
        rule_id=rule_id,
        severity=Severity.HARD,
        message=f"{rule_id} demo",
        path=corpus / "XML" / "Lang" / "d.xml",
        location=location,
    )


# --- locating the corpus that owns a finding --------------------------------

def test_corpus_root_found_from_a_nested_xml_file(tmp_path):
    corpus = _corpus(tmp_path)
    found = corpus_root_for(corpus / "XML" / "Lang" / "d.xml")
    assert found == corpus.resolve()


def test_corpus_root_is_none_outside_a_corpus(tmp_path):
    loose = tmp_path / "loose.xml"
    loose.write_text("<TEXT/>", encoding="utf-8")
    assert corpus_root_for(loose) is None


def test_relative_name_is_the_path_below_XML(tmp_path):
    corpus = _corpus(tmp_path)
    name = relative_xml_name(corpus / "XML" / "Lang" / "d.xml", corpus)
    assert name == "Lang/d.xml"


# --- what a waiver does -----------------------------------------------------

def test_matching_waiver_reclassifies_hard_to_waived(tmp_path):
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", "a real reason")])
    out, stale = apply_waivers([_hard(corpus)])
    assert [f.severity for f in out] == [Severity.WAIVED]
    assert stale == []


def test_waived_finding_is_kept_not_dropped(tmp_path):
    """A waiver silences the build, never the record."""
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", "a real reason")])
    original = _hard(corpus)
    out, _ = apply_waivers([original])
    assert len(out) == 1
    kept = out[0]
    assert (kept.rule_id, kept.location, kept.message, kept.path) == (
        original.rule_id, original.location, original.message, original.path
    )


def test_waiver_does_not_reach_a_different_location(tmp_path):
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", "a real reason")])
    out, stale = apply_waivers([_hard(corpus, location="S=2")])
    assert [f.severity for f in out] == [Severity.HARD]
    assert [w.location for w in stale] == ["S=1"]


def test_no_waiver_file_leaves_findings_alone(tmp_path):
    corpus = _corpus(tmp_path)
    out, stale = apply_waivers([_hard(corpus)])
    assert [f.severity for f in out] == [Severity.HARD]
    assert stale == []


# --- the anti-drift rule ----------------------------------------------------

def test_waiver_matching_nothing_is_stale(tmp_path):
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=99", "outlived it")])
    out, stale = apply_waivers([_hard(corpus, location="S=1")])
    assert [f.severity for f in out] == [Severity.HARD]
    assert len(stale) == 1
    assert stale[0].location == "S=99"


def test_stale_waiver_is_detected_even_when_the_run_is_otherwise_clean(tmp_path):
    """The case that matters: nothing else is wrong, so nothing else fails."""
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", "outlived it")])
    clean = Finding(
        rule_id="V999", severity=Severity.SOFT, message="soft",
        path=corpus / "XML" / "Lang" / "d.xml", location="S=1",
    )
    _, stale = apply_waivers([clean])
    assert len(stale) == 1


# --- refusals ---------------------------------------------------------------

def test_reason_is_required(tmp_path):
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", "   ")])
    with pytest.raises(WaiverError, match="has no reason"):
        load_waivers(corpus)


def test_todo_placeholder_is_not_a_reason(tmp_path):
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", TODO_REASON)])
    with pytest.raises(WaiverError, match="has no reason"):
        load_waivers(corpus)


def test_structural_rule_may_not_be_waived(tmp_path):
    corpus = _corpus(tmp_path, [("V001", "Lang/d.xml", "S=1", "please no")])
    with pytest.raises(WaiverError, match="may not be waived"):
        load_waivers(corpus)


@pytest.mark.parametrize("row", [
    (WAIVABLE, "*", "S=1", "wildcard file"),
    (WAIVABLE, "Lang/d.xml", "*", "wildcard location"),
])
def test_wildcards_are_rejected(tmp_path, row):
    corpus = _corpus(tmp_path, [row])
    with pytest.raises(WaiverError, match="wildcards are not allowed"):
        load_waivers(corpus)


def test_duplicate_waiver_is_rejected(tmp_path):
    corpus = _corpus(tmp_path, [
        (WAIVABLE, "Lang/d.xml", "S=1", "first"),
        (WAIVABLE, "Lang/d.xml", "S=1", "second"),
    ])
    with pytest.raises(WaiverError, match="duplicate waiver"):
        load_waivers(corpus)


def test_missing_column_is_rejected(tmp_path):
    corpus = _corpus(tmp_path)
    waiver_path(corpus).write_text(
        "rule_id\tfile\tlocation\n" f"{WAIVABLE}\tLang/d.xml\tS=1\n",
        encoding="utf-8",
    )
    with pytest.raises(WaiverError, match="missing column"):
        load_waivers(corpus)


# --- the propose CLI --------------------------------------------------------

def _findings_csv(path: Path, rows: list[dict[str, str]]) -> Path:
    columns = ["file", "line", "severity", "rule_id", "title", "location",
               "language", "character", "count", "message"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
    return path


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(WAIVERS_CLI), *args],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )


def test_propose_writes_todo_rows_that_do_not_yet_validate(tmp_path):
    corpus = _corpus(tmp_path)
    xml = corpus / "XML" / "Lang" / "d.xml"
    csv_path = _findings_csv(tmp_path / "f.csv", [
        {"file": str(xml), "severity": "HARD", "rule_id": WAIVABLE,
         "location": "S=1", "count": "1", "message": "m"},
    ])
    proc = _run_cli("propose", "--csv", str(csv_path))
    assert proc.returncode == 0, proc.stderr

    written = waiver_path(corpus).read_text(encoding="utf-8")
    assert f"{WAIVABLE}\tLang/d.xml\tS=1\t{TODO_REASON}" in written
    # The whole point: proposing does not accept anything.
    with pytest.raises(WaiverError, match="has no reason"):
        load_waivers(corpus)


def test_propose_skips_non_waivable_rules_and_says_so(tmp_path):
    corpus = _corpus(tmp_path)
    xml = corpus / "XML" / "Lang" / "d.xml"
    csv_path = _findings_csv(tmp_path / "f.csv", [
        {"file": str(xml), "severity": "HARD", "rule_id": "V001",
         "location": "S=1", "count": "1", "message": "m"},
    ])
    proc = _run_cli("propose", "--csv", str(csv_path))
    assert proc.returncode == 0, proc.stderr
    assert not waiver_path(corpus).exists()
    assert "not waivable, fix instead: V001" in proc.stderr


def test_propose_ignores_soft_findings(tmp_path):
    corpus = _corpus(tmp_path)
    xml = corpus / "XML" / "Lang" / "d.xml"
    csv_path = _findings_csv(tmp_path / "f.csv", [
        {"file": str(xml), "severity": "SOFT", "rule_id": WAIVABLE,
         "location": "S=1", "count": "1", "message": "m"},
    ])
    proc = _run_cli("propose", "--csv", str(csv_path))
    assert proc.returncode == 0, proc.stderr
    assert not waiver_path(corpus).exists()


def test_propose_is_idempotent(tmp_path):
    """Re-running while TODOs are outstanding must not duplicate rows."""
    corpus = _corpus(tmp_path)
    xml = corpus / "XML" / "Lang" / "d.xml"
    csv_path = _findings_csv(tmp_path / "f.csv", [
        {"file": str(xml), "severity": "HARD", "rule_id": WAIVABLE,
         "location": "S=1", "count": "1", "message": "m"},
    ])
    _run_cli("propose", "--csv", str(csv_path))
    first = waiver_path(corpus).read_text(encoding="utf-8")
    proc = _run_cli("propose", "--csv", str(csv_path))
    assert proc.returncode == 0, proc.stderr
    assert waiver_path(corpus).read_text(encoding="utf-8") == first


def test_report_lists_the_banks_waivers(tmp_path):
    corpus = _corpus(tmp_path, [(WAIVABLE, "Lang/d.xml", "S=1", "why it is fine")])
    proc = _run_cli("report", "--repo-root", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert "Demo" in proc.stdout
    assert "why it is fine" in proc.stdout
    assert corpus.name == "Demo"
