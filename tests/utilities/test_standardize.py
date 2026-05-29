"""Tests for QC/utilities/standardize.py.

Standardize copies the `original` tier to a `standard` tier (with --copy)
or transliterates via a TSV mapping. It mutates XML in place, so all
tests work on a tmp_path copy of the fixture, never on the fixture
file itself.

CLI shape notes:
  --corpora_path is treated as a *collection* root: the script does
  os.listdir(corpora_path) to enumerate corpus directories, then walks
  each one for XML files. To point at a single fixture file, arrange
  tmp_path/ as the collection root and place the file in tmp_path/XML/.

  --tsv_path mode uses a column named "original" (not "source") as the
  lookup key; the target column is named via --target_column.
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

STANDARDIZE = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "standardize.py"


def _run_standardize(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(STANDARDIZE), *args],
        capture_output=True,
        text=True,
    )


def _standard_forms(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [
        f.text
        for s in root.iter("S")
        for f in s
        if f.tag == "FORM" and f.get("kindOf") == "standard" and f.text is not None
    ]


def _original_forms(xml_path: Path) -> list[str]:
    root = ET.parse(xml_path).getroot()
    return [
        f.text
        for s in root.iter("S")
        for f in s
        if f.tag == "FORM" and f.get("kindOf") == "original" and f.text is not None
    ]


def test_copy_adds_standard_tier_when_only_original_exists(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    assert _standard_forms(work) == _original_forms(work)
    assert _standard_forms(work) == ["Halo, hapinangha.", "Nawhani kako tayni i toron."]


def test_copy_overwrites_existing_standard_tier(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_both_tiers.xml", tmp_path)
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    standard = _standard_forms(work)
    assert "REPLACE ME" not in standard
    assert standard == _original_forms(work)


def test_tsv_mapping_transforms_standard_tier(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_original_only.xml", tmp_path)
    tsv = fixtures_dir / "tiny_mapping.tsv"
    proc = _run_standardize([
        "--tsv_path", str(tsv),
        "--target_column", "target",
        "--corpora_path", str(tmp_path),
    ])
    assert proc.returncode == 0, f"stderr: {proc.stderr}"
    standard = _standard_forms(work)
    assert standard == ["Hello, greeting.", "Nawhani kako tayni i toron."], (
        f"expected mapped sentence in standard tier, got: {standard!r}"
    )


def test_errors_when_no_original_tier(tmp_path, fixtures_dir, copy_fixture):
    work = copy_fixture(fixtures_dir / "valid_no_original_tier.xml", tmp_path)
    before = work.read_text()
    proc = _run_standardize(["--copy", "--corpora_path", str(tmp_path)])
    assert proc.returncode != 0, (
        f"expected non-zero exit; got returncode={proc.returncode}, "
        f"stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
    combined = (proc.stderr + proc.stdout).lower()
    assert "no original" in combined or "missing original" in combined, (
        f"expected error message naming the missing original tier; "
        f"got stdout={proc.stdout!r}, stderr={proc.stderr!r}"
    )
    # Atomicity: the script should not mutate the file when it errors out.
    assert work.read_text() == before, (
        "standardize.py modified the input file even though it errored on "
        "missing original tier"
    )
