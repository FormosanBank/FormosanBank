"""run_conversion_table_checks: never-blocking CI driver (2026-08-10 ruling).

The heavy lifting is validate_conversion_table.py's (separately tested);
these tests pin the driver's contract: exit 0 regardless of findings,
two-section report, structural classification for unresolvable tables.
"""
from pathlib import Path

from tests._helpers import run_qc_script

SCRIPT = "QC/validation/run_conversion_table_checks.py"


def _mini_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "Orthographies" / "ConversionTables").mkdir(parents=True)
    (root / "Orthographies" / "Ortho113").mkdir()
    return root


def test_empty_tables_dir_reports_zero_and_exits_zero(tmp_path):
    root = _mini_repo(tmp_path)
    proc = run_qc_script(SCRIPT, ["--repo-root", str(root)])
    assert proc.returncode == 0, proc.stderr
    assert "0 OK" in proc.stdout and "(of 0)" in proc.stdout


def test_unresolvable_table_is_structural_and_never_fails(tmp_path):
    root = _mini_repo(tmp_path)
    tables = root / "Orthographies" / "ConversionTables"
    (tables / "weird name.tsv").write_text("original\tstandard\na\tb\n",
                                           encoding="utf-8")
    (tables / "Amis_Ghost_113.tsv").write_text("original\tstandard\na\tb\n",
                                               encoding="utf-8")
    proc = run_qc_script(SCRIPT, ["--repo-root", str(root)])
    assert proc.returncode == 0, "driver must never fail (informational only)"
    assert "Structural defects" in proc.stdout
    assert "weird name.tsv" in proc.stdout
    assert "Amis_Ghost_113.tsv" in proc.stdout
    assert "source profile missing" in proc.stdout
