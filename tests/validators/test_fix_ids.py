"""Tests for QC/validation/fix_ids.py.

fix_ids.py renumbers <M> ids by position within each parent <W>: for
each W, its k-th M child in document order is assigned id = "<W.id>Mk".
Tests pin the three observed shapes:
  - collision: two siblings sharing an M id get distinct ids
  - gap: M1, M2, M4 → M1, M2, M3
  - clean: already-sequential M ids are not touched

Tests use the in-process API (compute_m_id_changes / apply_m_id_changes
/ fix_file) where possible — fast and avoids subprocess churn. One
end-to-end subprocess test covers the by_path CLI.
"""
import subprocess
import sys
from pathlib import Path

from lxml import etree

from QC.utilities.fix_ids import (
    apply_m_id_changes,
    compute_m_id_changes,
    fix_file,
)


FIX_IDS = Path(__file__).resolve().parents[2] / "QC" / "utilities" / "fix_ids.py"


def _m_ids_by_w(tree: etree._ElementTree) -> dict[str, list[str]]:
    """Return {W.id: [M.id, ...]} in document order for one tree."""
    out: dict[str, list[str]] = {}
    for w in tree.iter("W"):
        wid = w.get("id") or ""
        out[wid] = [m.get("id") or "" for m in w.findall("M")]
    return out


def test_compute_m_id_changes_collision_and_gap(fixtures_dir):
    """compute returns the right (old, new) pairs for collisions and gaps,
    and DOES NOT include the clean W3 whose ids already match position.
    """
    tree = etree.parse(str(fixtures_dir / "fix_ids_M_collisions_and_gaps.xml"))
    changes = compute_m_id_changes(tree)
    pairs = [(old, new) for (_m, old, new) in changes]
    # W1: 3rd M is duplicate W1M2 -> should become W1M3; 4th M is W1M4
    # -> should become W1M4 (already correct after renumber-by-position).
    # Wait: position 4 in W1 is the 4th M, so new_id = "W1M4". The OLD
    # id is also "W1M4" so this M is NOT in the changes list.
    # Only the 3rd M (old="W1M2", new="W1M3") changes in W1.
    assert ("W1M2", "W1M3") in pairs, (
        f"expected W1's third M to be renumbered W1M2 -> W1M3; got {pairs!r}"
    )
    # W2: third M old="W2M4", new="W2M3"
    assert ("W2M4", "W2M3") in pairs, (
        f"expected W2's third M to be renumbered W2M4 -> W2M3; got {pairs!r}"
    )
    # W3 is already clean — must NOT appear in changes.
    assert not any(old.startswith("W3M") for (old, _new) in pairs), (
        f"W3 is already sequential and must not be touched; got {pairs!r}"
    )
    # Exactly two changes total for this fixture.
    assert len(changes) == 2, f"expected exactly 2 changes; got {changes!r}"


def test_apply_m_id_changes_makes_ids_unique_and_positional(fixtures_dir):
    """After apply_, every W's M ids are exactly [W.id+'M1', ..., W.id+'MN']."""
    tree = etree.parse(str(fixtures_dir / "fix_ids_M_collisions_and_gaps.xml"))
    changes = compute_m_id_changes(tree)
    apply_m_id_changes(changes)
    after = _m_ids_by_w(tree)
    assert after["W1"] == ["W1M1", "W1M2", "W1M3", "W1M4"], after["W1"]
    assert after["W2"] == ["W2M1", "W2M2", "W2M3"], after["W2"]
    assert after["W3"] == ["W3M1", "W3M2"], after["W3"]


def test_fix_file_writes_changes_in_place(tmp_path, fixtures_dir, copy_fixture):
    """fix_file in non-dry-run mode rewrites the file with renumbered ids.

    Read the file back from disk (NOT the in-memory tree) so we verify
    the write path itself works, not just the in-memory mutation.
    """
    copy = copy_fixture(
        fixtures_dir / "fix_ids_M_collisions_and_gaps.xml", tmp_path
    )
    n = fix_file(copy, dry_run=False, verbose=False)
    assert n == 2, f"expected 2 renumbering changes; got {n}"
    re_read = etree.parse(str(copy))
    after = _m_ids_by_w(re_read)
    assert after["W1"] == ["W1M1", "W1M2", "W1M3", "W1M4"]
    assert after["W2"] == ["W2M1", "W2M2", "W2M3"]
    assert after["W3"] == ["W3M1", "W3M2"]


def test_fix_file_dry_run_leaves_file_unchanged(
    tmp_path, fixtures_dir, copy_fixture
):
    """--dry-run reports the change count but does not write to disk."""
    copy = copy_fixture(
        fixtures_dir / "fix_ids_M_collisions_and_gaps.xml", tmp_path
    )
    before_bytes = copy.read_bytes()
    n = fix_file(copy, dry_run=True, verbose=False)
    assert n == 2, f"expected 2 planned changes in dry-run; got {n}"
    after_bytes = copy.read_bytes()
    assert before_bytes == after_bytes, (
        "dry-run must not modify the file on disk"
    )


def test_fix_file_no_changes_returns_zero(tmp_path, fixtures_dir, copy_fixture):
    """A file whose ids are already correct returns 0 and is not rewritten.

    Use valid_minimal.xml: a TEXT/S/FORM file with no W and no M, so
    compute_m_id_changes can't produce anything.
    """
    copy = copy_fixture(fixtures_dir / "valid_minimal.xml", tmp_path)
    before_bytes = copy.read_bytes()
    n = fix_file(copy, dry_run=False, verbose=False)
    assert n == 0
    after_bytes = copy.read_bytes()
    assert before_bytes == after_bytes, (
        "no-change run must not touch the file (avoids spurious "
        "whitespace-only rewrites)"
    )


def test_cli_by_path_end_to_end(tmp_path, fixtures_dir, copy_fixture):
    """End-to-end subprocess invocation of fix_ids.py by_path --path <dir>.

    Confirms:
      - the script runs and exits 0
      - the target file is modified
      - the summary line on stderr reports the right counts
    """
    copy = copy_fixture(
        fixtures_dir / "fix_ids_M_collisions_and_gaps.xml", tmp_path
    )
    proc = subprocess.run(
        [
            sys.executable, str(FIX_IDS),
            "by_path", "--path", str(copy.parent),
        ],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        f"fix_ids.py exited {proc.returncode}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    re_read = etree.parse(str(copy))
    after = _m_ids_by_w(re_read)
    assert after["W1"] == ["W1M1", "W1M2", "W1M3", "W1M4"]
    assert after["W2"] == ["W2M1", "W2M2", "W2M3"]
    # Stderr summary mentions 2 renumberings across 1 file.
    assert "2 M id(s) renumbered" in proc.stderr, (
        f"missing summary line; stderr={proc.stderr!r}"
    )
    assert "1 file(s)" in proc.stderr, (
        f"summary should mention 1 file(s); stderr={proc.stderr!r}"
    )


def test_cli_dry_run_does_not_modify(tmp_path, fixtures_dir, copy_fixture):
    """CLI --dry-run: subprocess prints planned changes, file unchanged."""
    copy = copy_fixture(
        fixtures_dir / "fix_ids_M_collisions_and_gaps.xml", tmp_path
    )
    before_bytes = copy.read_bytes()
    proc = subprocess.run(
        [
            sys.executable, str(FIX_IDS),
            "--dry-run",
            "by_path", "--path", str(copy.parent),
        ],
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    after_bytes = copy.read_bytes()
    assert before_bytes == after_bytes, "dry-run must not modify the file"
    assert "[dry-run]" in proc.stdout, (
        f"expected [dry-run] marker on stdout; got {proc.stdout!r}"
    )


def test_post_fix_file_passes_validate_xml(
    tmp_path, fixtures_dir, copy_fixture
):
    """After fix_ids.py rewrites a colliding-M file, validate_xml.py V039
    no longer fires on it.

    This is the load-bearing integration: the whole purpose of fix_ids.py
    is to clear V039 collisions. Failing to clear them would defeat the
    point of the script.
    """
    copy = copy_fixture(
        fixtures_dir / "fix_ids_M_collisions_and_gaps.xml", tmp_path
    )
    fix_file(copy, dry_run=False, verbose=False)
    validate = (
        Path(__file__).resolve().parents[2]
        / "QC" / "validation" / "validate_xml.py"
    )
    proc = subprocess.run(
        [
            sys.executable, str(validate),
            "--published-corpora", str(tmp_path),
            "by_path", "--path", str(copy.parent),
            "--soft-csv", str(tmp_path / "soft.csv"),
        ],
        capture_output=True, text=True,
    )
    combined = (proc.stdout + proc.stderr).lower()
    assert "v039" not in combined, (
        f"V039 should no longer fire after fix_ids.py; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert "duplicate key-sequence" not in combined, (
        f"schema-level duplicate-id violation should be cleared; "
        f"stderr={proc.stderr!r}"
    )
