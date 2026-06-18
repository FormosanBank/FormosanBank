"""Finding dataclass and Severity enum for the validator.

A Finding is the unit of validator output. HARD and WARN rules emit
one Finding per offending element, populating `location`. SOFT rules
pre-aggregate per (rule, file, language, character) and populate
`count`/`language`/`character`.
"""
import csv
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    WARN = "WARN"


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: Severity
    message: str
    path: Path
    location: str | None = None
    count: int = 1
    language: str | None = None
    character: str | None = None
    line: int | None = None


SOFT_CSV_COLUMNS = [
    "file", "rule_id", "location", "line", "language", "character", "count",
]

# One-CSV-for-everything column shape (2026-06-09). Unlike SOFT_CSV_COLUMNS
# this carries `severity` and the free-text `message` so a reader can view
# each finding's context without opening the XML, and holds HARD + SOFT +
# WARN rows together.
FINDINGS_CSV_COLUMNS = [
    "file", "line", "severity", "rule_id", "title", "location",
    "language", "character", "count", "message",
]


def summarize(findings: Iterable[Finding]) -> dict[Severity, dict[str, int]]:
    """Aggregate findings into per-rule occurrence counts, split by severity.

    Returns a dict with a key for every Severity (HARD, SOFT, WARN), each
    mapping rule_id -> total occurrences. "Occurrences" sums each finding's
    ``count`` field, so pre-aggregated SOFT rows (count=N) contribute N and
    per-element HARD rows (count=1) contribute 1. This is the data behind
    the terminal summary.
    """
    out: dict[Severity, dict[str, int]] = {
        Severity.HARD: {}, Severity.SOFT: {}, Severity.WARN: {},
    }
    for f in findings:
        bucket = out[f.severity]
        bucket[f.rule_id] = bucket.get(f.rule_id, 0) + f.count
    return out


def write_findings_csv(
    path: Path,
    findings: Iterable[Finding],
    titles: dict[str, str] | None = None,
) -> None:
    """Write ALL findings (every severity) to a single CSV at ``path``.

    Columns are FINDINGS_CSV_COLUMNS. The CSV is overwritten on each call;
    the parent directory is created if absent. This is the one detail file
    the validators announce on the terminal; the per-rule `message` carries
    the human-readable context.

    ``titles`` maps rule_id -> mnemonic to fill the `title` column (blank
    for any rule_id not in the map). Passing it lives with the caller so
    this module needn't import the rule registry.
    """
    titles = titles or {}
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(FINDINGS_CSV_COLUMNS)
        for finding in findings:
            writer.writerow([
                str(finding.path),
                str(finding.line) if finding.line is not None else "",
                finding.severity.value,
                finding.rule_id,
                titles.get(finding.rule_id, ""),
                finding.location or "",
                finding.language or "",
                finding.character or "",
                str(finding.count),
                finding.message,
            ])


def write_soft_csv(path: Path, findings: Iterable[Finding]) -> None:
    """Write all SOFT findings in `findings` to a CSV at `path`.

    The CSV is overwritten on each call (not appended). The parent
    directory is created if it does not exist. Non-SOFT findings in
    `findings` are silently skipped: the runner separates output
    channels by severity, but if a SOFT writer is ever invoked with a
    mixed list, only SOFT rows belong in the SOFT CSV.

    Column shape per the validator design doc:
      file: absolute path to the XML file the finding came from.
      rule_id: uppercase rule identifier (e.g., "V014").
      location: parent element ID where the finding occurred (e.g.
        "S=ap3_S_2") or empty for rules that aggregate per-file.
      line: 1-indexed source line of the offending element, or empty.
      language: resolved xml:lang (ISO 639-3) or empty.
      character: the offending character, or empty if not applicable.
      count: occurrence count for this row.

    Written as UTF-8 with BOM (utf-8-sig) so Excel renders non-ASCII
    characters correctly when opening the CSV directly (2026-06-11).

    `location` and `line` were added 2026-06-01 so per-occurrence rules
    can pin each row to a specific S/W/M element. Aggregated rules
    continue to emit one row per (file, language, character) with these
    columns blank.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(SOFT_CSV_COLUMNS)
        for finding in findings:
            if finding.severity is not Severity.SOFT:
                continue
            writer.writerow([
                str(finding.path),
                finding.rule_id,
                finding.location or "",
                str(finding.line) if finding.line is not None else "",
                finding.language or "",
                finding.character or "",
                str(finding.count),
            ])
