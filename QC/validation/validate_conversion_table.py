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


def load_orthography(path: Path, dialect: str | None) -> Orthography:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        column = select_value_column(fieldnames, dialect, key="letter")
        ipa_of: dict[str, str] = {}
        for row in reader:
            letter = (row.get("letter") or "").strip()
            value = (row.get(column) or "").strip()
            if not letter or value == "NA" or value == "":
                continue
            ipa_of.setdefault(letter, value)
    return Orthography(ipa_of=ipa_of, column=column)


def tokenize(text: str, letters) -> tuple[list[str], list[str]]:
    ordered = sorted({lt for lt in letters if lt}, key=len, reverse=True)
    graphemes: list[str] = []
    unmatched: list[str] = []
    index = 0
    while index < len(text):
        match = next((lt for lt in ordered if text.startswith(lt, index)), None)
        if match is None:
            graphemes.append(text[index])
            unmatched.append(text[index])
            index += 1
        else:
            graphemes.append(match)
            index += len(match)
    return graphemes, unmatched


def target_ipa(tgt: str, output: Orthography) -> tuple[str | None, list[str]]:
    graphemes, unmatched = tokenize(tgt, output.ipa_of.keys())
    if unmatched:
        return None, unmatched
    return "".join(output.ipa_of[g] for g in graphemes), []
