from pathlib import Path
from QC.utilities.dialect_detector_pkg.graphemes import load_letter_inventories

def _write_tsv(tmp_path: Path) -> Path:
    p = tmp_path / "Toy.tsv"
    p.write_text(
        "letter\tAlpha\tBeta\tdefault\n"
        "ng\tŋ\tŋ\tŋ\n"
        "f\tf\tNA\tf\n"
        "v\tNA\tv\tv\n"
        "a\ta\ta\ta\n",
        encoding="utf-8",
    )
    return tmp_path

def test_load_letter_inventories_splits_by_dialect_and_drops_NA(tmp_path):
    inv = load_letter_inventories("Toy", _write_tsv(tmp_path))
    assert set(inv) == {"Alpha", "Beta"}          # 'default' column excluded
    assert inv["Alpha"] == frozenset({"ng", "f", "a"})  # v is NA for Alpha
    assert inv["Beta"] == frozenset({"ng", "v", "a"})   # f is NA for Beta

def test_load_letter_inventories_missing_file_returns_empty(tmp_path):
    assert load_letter_inventories("DoesNotExist", tmp_path) == {}
