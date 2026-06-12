from __future__ import annotations

from QC.validation._dialect_inventory import UNKNOWN_DIALECT, valid_dialects
from QC.utilities.dialect_detector.hints import DIALECT_ALIASES


def candidate_dialects(lang_code: str) -> list[str]:
    """Sorted candidate dialects for a language code (valid set minus unknown).
    Empty for single-dialect / unknown codes."""
    valid = valid_dialects(lang_code)
    if valid is None:
        return []
    cands = sorted(d for d in valid if d != UNKNOWN_DIALECT)
    # single-dialect languages have exactly {LanguageName} here; treat as out of
    # scope by returning [] when only one candidate remains.
    return cands if len(cands) >= 2 else []


def reconcile_label(raw: str, candidates: list[str]) -> str | None:
    """Map a raw dialect attribute to a candidate, via exact match or alias."""
    raw = (raw or "").strip()
    if raw in candidates:
        return raw
    aliased = DIALECT_ALIASES.get(raw)
    if aliased is not None and aliased in candidates:
        return aliased
    return None
