"""Audit an orthography conversion table transitively through IPA.

Given an original orthography profile, an output orthography profile, and a
conversion table (source grapheme -> target grapheme), check that applying
the table reproduces the output orthography as closely as possible, and
report the cases where it cannot: notational near-equivalences (warnings),
phoneme merges, phonemes the source cannot encode, coverage gaps, and
table-integrity errors. See docs/superpowers/specs/2026-08-09-conversion-
table-validator-design.md.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Verdict(Enum):
    CONFIRMED = "confirmed"
    WARNING = "warning"
    MISMATCH = "mismatch"
    UNKNOWN_SOURCE = "unknown_source"
    UNTOKENIZABLE = "untokenizable"


@dataclass(frozen=True)
class Orthography:
    ipa_of: dict[str, str]
    column: str


@dataclass(frozen=True)
class RowResult:
    src: str
    tgt: str
    verdict: Verdict
    src_ipa: str | None
    tgt_ipa: str | None
    reason: str = ""
    unmatched: tuple[str, ...] = ()


@dataclass
class Report:
    dialect: str | None
    rows: list[RowResult] = field(default_factory=list)
    merges: list[tuple[str, list[str]]] = field(default_factory=list)
    cant_encode: list[str] = field(default_factory=list)
    coverage_gaps: list[tuple[str, str]] = field(default_factory=list)

    def blocking(self) -> list[RowResult]:
        blocking_verdicts = {
            Verdict.MISMATCH, Verdict.UNKNOWN_SOURCE, Verdict.UNTOKENIZABLE
        }
        return [r for r in self.rows if r.verdict in blocking_verdicts]


_FALLBACK_COLUMNS = ("default", "IPA", "standard")


def select_value_column(fieldnames: list[str], dialect: str | None, key: str) -> str:
    """Choose the IPA/target column: dialect, then a known fallback, then lone column."""
    value_columns = [c for c in fieldnames if c != key]
    if dialect and dialect in value_columns:
        return dialect
    for fallback in _FALLBACK_COLUMNS:
        if fallback in value_columns:
            return fallback
    if len(value_columns) == 1:
        return value_columns[0]
    raise ValueError(
        f"no unambiguous value column for dialect {dialect!r} in {fieldnames}"
    )
