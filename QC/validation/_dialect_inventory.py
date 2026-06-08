"""Shared dialect inventory derived from dialects.csv + ISO 639-3 codes.

Consumed by:
  - QC/validation/rules/hard.py (V036)
  - QC/utilities/fix_dialects.py
  - QC/validation/validate_dialect.py

Convention (2026-06-03):
  - TEXT/@dialect is REQUIRED on every TEXT element.
  - "unknown" is a valid value for any language (means: dialect not yet
    identified).
  - For multi-dialect languages (those with at least one Official entry
    in dialects.csv), the valid set is those Official dialects plus
    "unknown".
  - For single-dialect languages (those in ISO_TO_LANGUAGE with no
    Official entries in dialects.csv), the valid set is just the language
    name itself plus "unknown" (e.g., dialect="Tsou" for xml:lang="tsu").
  - xml:lang="trv" is the one ambiguous code: ISO 639-3 lumps Truku and
    Seediq together. Valid set is Truku (the language name of the
    single-dialect side) + Seediq's three Official dialects + "unknown".
"""
from __future__ import annotations

import csv
from pathlib import Path

UNKNOWN_DIALECT = "unknown"


def _load_dialect_map() -> dict[str, set[str]]:
    """Read dialects.csv and return {Language: {Official, ...}}.

    Languages with no Official entries (single-dialect / single-language)
    do not appear in the result. The CSV's Language and Official columns
    are stripped; empty Official rows are dropped via the truthiness check.
    """
    dialects_path = Path(__file__).resolve().parents[2] / "dialects.csv"
    result: dict[str, set[str]] = {}
    with open(dialects_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lang = row["Language"].strip()
            dialect = row["Official"].strip()
            if lang and dialect:
                result.setdefault(lang, set()).add(dialect)
    return result


# ISO 639-3 code -> human-readable Language name (matches dialects.csv
# "Language" column). Mirrors QC/corpus_metrics.py LANG_CODES.
ISO_TO_LANGUAGE: dict[str, str] = {
    "ami": "Amis",
    "tay": "Atayal",
    "pwn": "Paiwan",
    "bnn": "Bunun",
    "pyu": "Puyuma",
    "dru": "Rukai",
    "tsu": "Tsou",
    "xsy": "Saisiyat",
    "tao": "Yami",
    "ssf": "Thao",
    "ckv": "Kavalan",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "sxr": "Saaroa",
    "xnb": "Kanakanavu",
    "fos": "Siraya",
}

DIALECT_MAP: dict[str, set[str]] = _load_dialect_map()


def is_multi_dialect_language(language: str) -> bool:
    """True if `language` has more than one Official dialect in dialects.csv."""
    return language in DIALECT_MAP


def default_dialect_for_lang_code(lang_code: str) -> str:
    """Return the value fix_dialects.py should write for a TEXT missing @dialect.

    Single-dialect languages: the language name itself (e.g., "Tsou").
    Multi-dialect languages: "unknown" (caller must identify it manually).
    trv: "unknown" — ambiguous between Truku and Seediq, cannot safely auto-assign.
    Unknown ISO code: "unknown".
    """
    if lang_code == "trv":
        return UNKNOWN_DIALECT
    language = ISO_TO_LANGUAGE.get(lang_code)
    if language is None:
        return UNKNOWN_DIALECT
    if is_multi_dialect_language(language):
        return UNKNOWN_DIALECT
    return language


def valid_dialects(lang_code: str) -> frozenset[str] | None:
    """Return the set of valid dialect values for `lang_code`, or None if unknown code.

    Returning None lets V036 skip the check (V035 will already flag the
    invalid lang code).
    """
    if lang_code == "trv":
        return frozenset(DIALECT_MAP.get("Seediq", set()) | {"Truku", UNKNOWN_DIALECT})
    language = ISO_TO_LANGUAGE.get(lang_code)
    if language is None:
        return None
    if is_multi_dialect_language(language):
        return frozenset(DIALECT_MAP[language] | {UNKNOWN_DIALECT})
    return frozenset({language, UNKNOWN_DIALECT})
