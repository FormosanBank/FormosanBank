"""Finding dataclass and Severity enum for the validator.

A Finding is the unit of validator output. HARD and WARN rules emit
one Finding per offending element, populating `location`. SOFT rules
pre-aggregate per (rule, file, language, character) and populate
`count`/`language`/`character`.
"""
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
