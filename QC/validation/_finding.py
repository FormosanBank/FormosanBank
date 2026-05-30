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


SOFT_CSV_COLUMNS = ["file", "rule_id", "language", "character", "count"]


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
      language: resolved xml:lang (ISO 639-3) or empty.
      character: the offending character, or empty if not applicable.
      count: occurrence count for this (rule, file, language, character).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SOFT_CSV_COLUMNS)
        for finding in findings:
            if finding.severity is not Severity.SOFT:
                continue
            writer.writerow([
                str(finding.path),
                finding.rule_id,
                finding.language or "",
                finding.character or "",
                str(finding.count),
            ])
