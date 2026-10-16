"""Orthography tables must be unambiguous.

Both families are keyed lookups: an orthography profile
(`Orthographies/<Scheme>/<Language>.tsv`) maps a letter to IPA for
`add_phonology`, and a conversion table
(`Orthographies/ConversionTables/<Language>_<Scheme>_113.tsv`) maps a letter to
another orthography for `standardize`. Neither consumer has any way to honour a
key twice: `add_phonology` scans longest-first and takes the earliest match,
`standardize` stages each rule once. A repeated key is therefore a row that
silently does nothing, and which of the two wins is decided by file order.

`Orthographies/Ortho94/Saaroa.tsv` carried `e → ə` and `e → e`. The second was a
leftover from the Ortho113 file it was derived from (maintainer, 2026-09-09) and
had been dead since the file was written; had the rows been the other way round
the profile would have asserted the wrong vowel.
"""
import csv
import glob
import os

import pytest

REPO_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")


def _tables():
    profiles = [
        p
        for p in glob.glob(os.path.join(REPO_ROOT, "Orthographies", "*", "*.tsv"))
        if "ConversionTables" not in p and not p.endswith(".rules.tsv")
    ]
    conversions = glob.glob(
        os.path.join(REPO_ROOT, "Orthographies", "ConversionTables", "*.tsv")
    )
    return sorted(profiles + conversions)


def _key_column(fieldnames):
    for candidate in ("letter", "original"):
        if candidate in (fieldnames or []):
            return candidate
    return None


@pytest.mark.parametrize(
    "path", _tables(), ids=lambda p: os.path.relpath(p, REPO_ROOT)
)
def test_no_repeated_key(path):
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        key = _key_column(reader.fieldnames)
        if key is None:
            pytest.skip(f"{os.path.basename(path)} has no letter/original column")
        seen = {}
        for line, row in enumerate(reader, start=2):
            value = (row.get(key) or "").strip()
            if not value:
                continue
            if value in seen:
                pytest.fail(
                    f"{os.path.relpath(path, REPO_ROOT)}: {value!r} appears on "
                    f"lines {seen[value]} and {line}; the second row is dead"
                )
            seen[value] = line
