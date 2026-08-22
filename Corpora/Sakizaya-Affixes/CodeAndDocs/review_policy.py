"""Release dispositions added by the 2026-08-14 expert XML review."""

from __future__ import annotations


EXPERT_REVIEW_STATUS = "excluded_expert_review"


def effective_status(dataset: str, row: dict[str, str]) -> str:
    """Return the release status while preserving raw extraction ledgers."""

    if dataset in {"summary", "late"}:
        return EXPERT_REVIEW_STATUS
    return row["status"]
