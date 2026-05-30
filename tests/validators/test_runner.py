"""Unit tests for the validate_xml runner: file walking, tree caching,
dispatch. These tests import from QC.validation directly; they do not
subprocess. End-to-end behavior is covered by the existing
tests/validators/test_validate_xml.py against the CLI surface.
"""
import subprocess
import sys
from pathlib import Path

import pytest
from lxml import etree

from QC.validation._finding import Finding, Severity
from QC.validation.validate_xml import (
    discover_xml_files,
    parse_tree,
    run_per_file_rules,
)


VALID_XML = b"""<?xml version="1.0" encoding="utf-8"?>
<TEXT id="t1" citation="c" BibTeX_citation="@b{x}" copyright="cc" xml:lang="ami">
  <S id="S1">
    <FORM kindOf="original">Halo.</FORM>
  </S>
</TEXT>
"""


def test_discover_xml_files_returns_only_xml(tmp_path):
    (tmp_path / "XML").mkdir()
    (tmp_path / "XML" / "a.xml").write_bytes(VALID_XML)
    (tmp_path / "XML" / "b.xml").write_bytes(VALID_XML)
    (tmp_path / "XML" / "note.txt").write_text("not xml")
    (tmp_path / "README.md").write_text("not xml")

    files = sorted(discover_xml_files(tmp_path))
    assert [p.name for p in files] == ["a.xml", "b.xml"]


def test_discover_xml_files_recurses(tmp_path):
    (tmp_path / "XML" / "Amis").mkdir(parents=True)
    (tmp_path / "XML" / "Amis" / "x.xml").write_bytes(VALID_XML)
    files = sorted(discover_xml_files(tmp_path))
    assert [p.name for p in files] == ["x.xml"]


def test_parse_tree_returns_etree(tmp_path):
    p = tmp_path / "x.xml"
    p.write_bytes(VALID_XML)
    tree = parse_tree(p)
    assert tree.getroot().tag == "TEXT"


def test_run_per_file_rules_invokes_each_rule(tmp_path):
    p = tmp_path / "x.xml"
    p.write_bytes(VALID_XML)
    tree = parse_tree(p)

    calls = []
    def rule_a(t, path, index):
        calls.append(("a", path))
        return []
    def rule_b(t, path, index):
        calls.append(("b", path))
        return [Finding(rule_id="V999", severity=Severity.HARD,
                        message="test", path=path)]

    findings = run_per_file_rules(tree, p, [rule_a, rule_b], index=None)
    assert [c[0] for c in calls] == ["a", "b"]
    assert len(findings) == 1
    assert findings[0].rule_id == "V999"


VALIDATE_XML_CLI = (
    Path(__file__).resolve().parents[2] / "QC" / "validation" / "validate_xml.py"
)


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_XML_CLI), *args],
        capture_output=True,
        text=True,
    )


def test_exit_zero_on_clean_corpus(tmp_path, fixtures_dir, copy_fixture):
    """When no HARD findings are produced, the validator exits 0."""
    copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"


def test_exit_nonzero_on_hard_findings(tmp_path, fixtures_dir, copy_fixture):
    """Default: any HARD finding causes exit 1."""
    copy_fixture(fixtures_dir / "v017_empty_FORM_content.xml", tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path)])
    assert proc.returncode == 1, (
        f"expected exit 1 on HARD findings; got {proc.returncode}\n"
        f"stderr: {proc.stderr}"
    )


def test_no_exit_on_hard_overrides_to_zero(tmp_path, fixtures_dir, copy_fixture):
    """--no-exit-on-hard restores legacy always-exit-0 behavior."""
    copy_fixture(fixtures_dir / "v017_empty_FORM_content.xml", tmp_path)
    proc = _run_cli(["by_path", "--path", str(tmp_path), "--no-exit-on-hard"])
    assert proc.returncode == 0, (
        f"expected --no-exit-on-hard to suppress nonzero exit; "
        f"got {proc.returncode}\nstderr: {proc.stderr}"
    )
