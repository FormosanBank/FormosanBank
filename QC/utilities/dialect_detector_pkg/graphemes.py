from __future__ import annotations

import csv
from pathlib import Path

_NON_DIALECT_COLUMNS = {"letter", "letters", "default", "standard", "ipa"}


def load_letter_inventories(
    language_name: str, orthographies_path: Path
) -> dict[str, frozenset[str]]:
    """Return {dialect_column: frozenset(letters)} from <Language>.tsv.

    A letter belongs to a dialect when that dialect's cell is non-empty and
    not 'NA'. The 'letter'/'default'/'standard'/'ipa' columns are not dialects.
    Returns {} if the TSV is missing or has no dialect columns.
    """
    tsv_path = Path(orthographies_path) / f"{language_name}.tsv"
    if not tsv_path.exists():
        return {}
    with open(tsv_path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fields = reader.fieldnames or []
        letter_col = next((c for c in fields if c in ("letter", "letters")), None)
        if letter_col is None:
            return {}
        dialect_cols = [c for c in fields if c.lower() not in _NON_DIALECT_COLUMNS]
        if not dialect_cols:
            return {}
        inv: dict[str, set[str]] = {c: set() for c in dialect_cols}
        for row in reader:
            letter = (row.get(letter_col) or "").strip()
            if not letter:
                continue
            for col in dialect_cols:
                cell = (row.get(col) or "").strip()
                if cell and cell.upper() != "NA":
                    inv[col].add(letter)
    return {d: frozenset(s) for d, s in inv.items()}
