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


_TIE_BAR = "͡"
_LIGATURE_TO_TIEBAR = {
    "ʦ": "t͡s", "ʣ": "d͡z",
    "ʧ": "t͡ʃ", "ʤ": "d͡ʒ",
    "ʨ": "t͡ɕ", "ʥ": "d͡ʑ",
}
_LENGTH = re.compile(r"(.)[ː:]")  # a segment followed by a length mark


def canonical_safe(ipa: str) -> str:
    """Normalize only in segment-preserving ways (glyph variants)."""
    text = unicodedata.normalize("NFC", ipa)
    for ligature, tiebar in _LIGATURE_TO_TIEBAR.items():
        text = text.replace(ligature, tiebar)
    text = text.replace("ɡ", "g")  # IPA script g -> Latin g
    return text


def _expand_length(text: str) -> str:
    return _LENGTH.sub(r"\1\1", text)  # 'aː' / 'a:' -> 'aa'


def reconcile(src_ipa: str, tgt_ipa: str) -> tuple[Verdict, str]:
    safe_src, safe_tgt = canonical_safe(src_ipa), canonical_safe(tgt_ipa)
    if safe_src == safe_tgt:
        return Verdict.CONFIRMED, ""

    reasons = []
    if _expand_length(safe_src) == _expand_length(safe_tgt):
        reasons.append("length↔doubling")
    if safe_src.replace(_TIE_BAR, "") == safe_tgt.replace(_TIE_BAR, ""):
        reasons.append("digraph↔affricate")
    # combined: both transforms together
    combined_src = _expand_length(safe_src).replace(_TIE_BAR, "")
    combined_tgt = _expand_length(safe_tgt).replace(_TIE_BAR, "")
    if combined_src == combined_tgt:
        return Verdict.WARNING, "+".join(reasons) if reasons else "length+affricate"
    return Verdict.MISMATCH, ""


def load_conversion_table(
    path: Path, dialect: str | None
) -> tuple[list[tuple[str, str]], str]:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        key = fieldnames[0]
        column = select_value_column(fieldnames, dialect, key=key)
        rows: list[tuple[str, str]] = []
        for row in reader:
            src = (row.get(key) or "").strip()
            tgt = (row.get(column) or "").strip()
            if not src or tgt in ("", "NA"):
                continue
            rows.append((src, tgt))
    return rows, column


def audit(
    original: Orthography,
    output: Orthography,
    rows: list[tuple[str, str]],
    dialect: str | None,
) -> Report:
    report = Report(dialect=dialect)
    out_ipa_to_src_ipas: dict[str, set[str]] = {}
    for src, tgt in rows:
        src_ipa = original.ipa_of.get(src)
        if src_ipa is None:
            # Try tokenizing the source as a sequence of original graphemes.
            graphemes, unmatched = tokenize(src, original.ipa_of.keys())
            if unmatched:
                report.rows.append(RowResult(src, tgt, Verdict.UNKNOWN_SOURCE, None, None))
                continue
            src_ipa = "".join(original.ipa_of[g] for g in graphemes)
        tgt_ipa, unmatched = target_ipa(tgt, output)
        if tgt_ipa is None:
            report.rows.append(
                RowResult(src, tgt, Verdict.UNTOKENIZABLE, src_ipa, None,
                          unmatched=tuple(unmatched))
            )
            continue
        verdict, reason = reconcile(src_ipa, tgt_ipa)
        report.rows.append(RowResult(src, tgt, verdict, src_ipa, tgt_ipa, reason))
        out_ipa_to_src_ipas.setdefault(
            canonical_safe(tgt_ipa), set()
        ).add(canonical_safe(src_ipa))

    report.merges = sorted(
        (out_ipa, sorted(src_ipas))
        for out_ipa, src_ipas in out_ipa_to_src_ipas.items()
        if len(src_ipas) > 1
    )

    producible = {canonical_safe(v) for v in original.ipa_of.values()}
    producible |= set(out_ipa_to_src_ipas.keys())
    report.cant_encode = sorted(
        {canonical_safe(v) for v in output.ipa_of.values()} - producible
    )

    converted = {src for src, _ in rows}
    for grapheme, ipa in original.ipa_of.items():
        if grapheme in converted:
            continue
        out_ipa = output.ipa_of.get(grapheme)
        if out_ipa is not None and canonical_safe(out_ipa) == canonical_safe(ipa):
            continue
        report.coverage_gaps.append((grapheme, ipa))
    report.coverage_gaps.sort()
    return report


def output_dialects(path: Path) -> list[str | None]:
    with open(path, encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
    dialects = [
        c for c in fieldnames
        if c != "letter" and c not in _FALLBACK_COLUMNS
    ]
    return dialects or [None]


def _bullet_lines(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (none)"


def render_report(reports: list[Report]) -> str:
    lines: list[str] = ["# Conversion-table audit", ""]
    total_blocking = sum(len(r.blocking()) for r in reports)
    lines.append("## Summary")
    lines.append(f"Result: {'FAIL' if total_blocking else 'PASS'}")
    for report in reports:
        label = report.dialect or "(single column)"
        counts: dict[Verdict, int] = {}
        for row in report.rows:
            counts[row.verdict] = counts.get(row.verdict, 0) + 1
        summary = ", ".join(f"{v.value}={counts.get(v, 0)}" for v in Verdict)
        lines.append(f"- **{label}**: {summary}")
    lines.append("")

    for report in reports:
        label = report.dialect or "(single column)"
        lines.append(f"## Dialect: {label}")

        def rows_for(verdict: Verdict) -> list[str]:
            return [
                f"`{r.src}` → `{r.tgt}` ({r.src_ipa} / {r.tgt_ipa})"
                + (f" — {r.reason}" if r.reason else "")
                for r in report.rows if r.verdict == verdict
            ]

        lines.append("### Confirmed equivalences")
        lines.append(_bullet_lines(rows_for(Verdict.CONFIRMED)))
        lines.append("### Warnings — assumed equivalences")
        lines.append(_bullet_lines(rows_for(Verdict.WARNING)))
        lines.append("### Unresolved mismatches")
        lines.append(_bullet_lines(rows_for(Verdict.MISMATCH)))
        lines.append("### Information loss")
        loss = [f"merge: {ipa} ← {', '.join(srcs)}" for ipa, srcs in report.merges]
        loss += [f"cannot encode: {ipa}" for ipa in report.cant_encode]
        lines.append(_bullet_lines(loss))
        lines.append("### Coverage")
        lines.append(_bullet_lines(
            [f"`{g}` ({ipa}) has no conversion route" for g, ipa in report.coverage_gaps]
        ))
        lines.append("### Table integrity")
        integrity = [
            f"unknown source `{r.src}`"
            for r in report.rows if r.verdict == Verdict.UNKNOWN_SOURCE
        ] + [
            f"untokenizable target `{r.tgt}` (missing {' '.join(r.unmatched)})"
            for r in report.rows if r.verdict == Verdict.UNTOKENIZABLE
        ]
        lines.append(_bullet_lines(integrity))
        lines.append("")
    return "\n".join(lines)


def run(
    original_path: Path, output_path: Path, table_path: Path
) -> tuple[str, int]:
    reports = []
    for dialect in output_dialects(output_path):
        original = load_orthography(original_path, dialect)
        output = load_orthography(output_path, dialect)
        rows, _column = load_conversion_table(table_path, dialect)
        reports.append(audit(original, output, rows, dialect))
    text = render_report(reports)
    exit_code = 1 if any(r.blocking() for r in reports) else 0
    return text, exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path, help="original orthography TSV")
    parser.add_argument("output", type=Path, help="output orthography TSV")
    parser.add_argument("conversion_table", type=Path, help="conversion table TSV")
    parser.add_argument("--output", dest="report_path", type=Path, default=None,
                        help="write the report here instead of stdout")
    args = parser.parse_args(argv)
    text, exit_code = run(args.original, args.output, args.conversion_table)
    if args.report_path:
        args.report_path.write_text(text, encoding="utf-8")
    else:
        print(text)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
