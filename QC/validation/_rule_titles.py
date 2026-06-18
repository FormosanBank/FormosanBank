"""Human-readable mnemonics for rule ids.

Each validator rule is a function named ``v<NNN>_<mnemonic>`` (e.g.
``v060_W_count_matches_word_count``). We derive a {rule_id: mnemonic} map
straight from those names so the mnemonics never drift from the code —
adding a rule automatically gives it a title. A small manual table covers
rule ids that are emitted inline rather than by a named function (V000).

Consumed by QC/validation/_report.py (terminal summary + the CSV's
`title` column).
"""
from __future__ import annotations

import re

from QC.validation.rules import gloss, hard, soft, text, warn

# Rule ids not backed by a named rule function (emitted inline in the
# validators, e.g. XSD/parse failures).
_MANUAL_TITLES: dict[str, str] = {
    "V000": "schema_validation",
}

_NAME_RE = re.compile(r"^v(\d+)_(.+)$")


def _build() -> dict[str, str]:
    titles: dict[str, str] = dict(_MANUAL_TITLES)
    for module in (hard, soft, warn, gloss, text):
        rules = list(getattr(module, "RULES", []))
        rules += list(getattr(module, "CROSS_FILE_RULES", []))
        for rule in rules:
            match = _NAME_RE.match(getattr(rule, "__name__", ""))
            if match:
                titles[f"V{match.group(1)}"] = match.group(2)
    return titles


# Built once at import. The rule modules are pure and already imported by
# the validators, so this adds no measurable cost.
RULE_TITLES: dict[str, str] = _build()


def rule_titles() -> dict[str, str]:
    """Return the {rule_id: mnemonic} map (e.g. 'V060' -> 'W_count_matches_word_count')."""
    return RULE_TITLES
