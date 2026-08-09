"""Case-variant derivation for conversion-table standardization.

standardize.py applies conversion-table rules with literal, case-sensitive
str.replace, so a rule ``o -> u`` never converts sentence-initial ``O``.
This module derives Title-case and ALL-CAPS variants of lowercase rules —
except where a capital is a distinct grapheme of the source orthography
(e.g. Li's Rukai ``T`` = /ʈ/), detected via the source orthography
profile resolved from the conversion table's filename.

Spec: docs/superpowers/specs/2026-08-09-standardize-capitalization-design.md
"""
import csv
import re
from pathlib import Path

# Scheme tokens whose Orthographies/ folder is not simply the token itself.
SCHEME_FOLDERS = {"94": "Ortho94", "113": "Ortho113", "113lib": "Ortho113Liberal"}

_TABLE_NAME = re.compile(r"^(?P<language>[^_]+)_(?P<scheme>[^_]+)_113\.tsv$")


def resolve_source_profile(tsv_path):
    """Conventional source-profile path for a conversion table, or None.

    Requires both published conventions: basename
    ``<Language>_<Scheme>_113.tsv`` and a parent directory named
    ``ConversionTables`` (so the ``Orthographies/`` root is its parent).
    The returned path may not exist — existence is the caller's check.
    """
    tsv_path = Path(tsv_path)
    match = _TABLE_NAME.match(tsv_path.name)
    if match is None or tsv_path.parent.name != "ConversionTables":
        return None
    folder = SCHEME_FOLDERS.get(match["scheme"], match["scheme"])
    return tsv_path.parent.parent / folder / f"{match['language']}.tsv"


def load_profile_graphemes(profile_path):
    """The set of graphemes in an orthography profile's ``letter`` column."""
    with open(profile_path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return {
            row["letter"].strip()
            for row in reader
            if row.get("letter") and row["letter"].strip()
        }


def _title(text):
    return text[:1].upper() + text[1:]


def derive_case_variants(rules, profile_graphemes):
    """Expand (source, replacement) rules with derived capital variants.

    For each fully-lowercase source, append a Title-case variant
    (first char of source and replacement uppercased) and an ALL-CAPS
    variant (both fully uppercased) immediately after it. A variant is
    suppressed when its source is an explicit rule source elsewhere in
    the table, a grapheme of the source orthography profile (phonemic
    capital), or already emitted (single-letter title == ALL-CAPS).
    Returns a new list; ``rules`` is not mutated.
    """
    explicit = {source for source, _ in rules}
    expanded = []
    emitted = set()
    for source, replacement in rules:
        expanded.append((source, replacement))
        emitted.add(source)
        if not source.islower():
            # islower() is False for uncased sources like "'" and for
            # anything already containing a capital.
            continue
        for variant, variant_replacement in (
            (_title(source), _title(replacement)),
            (source.upper(), replacement.upper()),
        ):
            if (
                variant in explicit
                or variant in profile_graphemes
                or variant in emitted
            ):
                continue
            expanded.append((variant, variant_replacement))
            emitted.add(variant)
    return expanded
