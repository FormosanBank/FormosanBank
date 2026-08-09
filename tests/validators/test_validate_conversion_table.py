import subprocess
import sys
from pathlib import Path

import pytest

from QC.validation import validate_conversion_table as vct

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "QC" / "validation" / "validate_conversion_table.py"
)


def _tsv(path: Path, header: list[str], rows: list[list[str]]) -> Path:
    lines = ["\t".join(header)] + ["\t".join(r) for r in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_select_value_column_prefers_dialect():
    cols = ["letter", "Wutai", "Eastern", "default"]
    assert vct.select_value_column(cols, "Eastern", key="letter") == "Eastern"


def test_dialect_column_selected_per_dialect_with_default_fallback():
    cols = ["letter", "Wutai", "Eastern", "default"]
    # Dona has no column -> fall back to 'default'
    assert vct.select_value_column(cols, "Dona", key="letter") == "default"


def test_single_value_column_profile():
    cols = ["letter", "IPA"]
    assert vct.select_value_column(cols, "Wutai", key="letter") == "IPA"


def test_select_value_column_ambiguous_raises():
    cols = ["original", "Southern", "Coastal"]
    with pytest.raises(ValueError):
        vct.select_value_column(cols, "Malan", key="original")
