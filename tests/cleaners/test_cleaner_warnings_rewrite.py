"""CleanerWarnings.write_csv must produce a per-run report, not a log.

POL-033: warnings sidecars are per-run reports. Before 2026-08-10 write_csv
opened in append mode, so rerunning clean_xml/standardize doubled every
persistent warn-only row (verified empirically: 84 -> 166 rows on a no-op
second run over tests/fixtures).
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "QC" / "cleaning"))
from clean_xml import CleanerWarnings  # noqa: E402


def _rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_second_run_rewrites_instead_of_appending(tmp_path):
    csv_path = tmp_path / "cleaner_warnings.csv"

    run1 = CleanerWarnings(csv_path)
    run1.add("c022", "a.xml", "S_1", "*", 0)
    run1.write_csv()
    assert len(_rows(csv_path)) == 1

    run2 = CleanerWarnings(csv_path)  # fresh instance, as a rerun creates
    run2.add("c022", "a.xml", "S_1", "*", 0)
    run2.write_csv()
    rows = _rows(csv_path)
    assert len(rows) == 1, "rerun must not duplicate persistent warnings"
    assert rows[0]["rule_id"] == "c022"


def test_single_header_after_rewrite(tmp_path):
    csv_path = tmp_path / "w.csv"
    for _ in range(2):
        warnings = CleanerWarnings(csv_path)
        warnings.add("c002", "b.xml", "S_9", "'", 3)
        warnings.write_csv()
    text = csv_path.read_text(encoding="utf-8")
    assert text.count("rule_id") == 1


def test_empty_run_removes_stale_csv(tmp_path):
    csv_path = tmp_path / "w.csv"
    run1 = CleanerWarnings(csv_path)
    run1.add("c007", "c.xml", "S_2", "ㄅ", 1)
    run1.write_csv()
    assert csv_path.exists()

    run2 = CleanerWarnings(csv_path)  # rerun found nothing
    run2.write_csv()
    assert not csv_path.exists(), "clean rerun must not leave stale findings"


def test_append_mode_accumulates_across_runs(tmp_path):
    """POL-035: the quote-correction log is durable — append, never replace."""
    csv_path = tmp_path / "quote_corrections.csv"
    run1 = CleanerWarnings(csv_path, append=True)
    run1.add("c031", "a.xml", "S_1", "'", 4)
    run1.write_csv()
    run2 = CleanerWarnings(csv_path, append=True)
    run2.add("c032", "b.xml", "S_9", "'", 0)
    run2.write_csv()
    rows = _rows(csv_path)
    assert [r["rule_id"] for r in rows] == ["c031", "c032"]
    text = csv_path.read_text(encoding="utf-8")
    assert text.count("rule_id") == 1, "header written once"


def test_append_mode_empty_run_preserves_log(tmp_path):
    csv_path = tmp_path / "quote_corrections.csv"
    run1 = CleanerWarnings(csv_path, append=True)
    run1.add("c031", "a.xml", "S_1", "'", 4)
    run1.write_csv()
    run2 = CleanerWarnings(csv_path, append=True)  # nothing corrected
    run2.write_csv()
    assert csv_path.exists()
    assert len(_rows(csv_path)) == 1, "committed log must survive empty runs"
