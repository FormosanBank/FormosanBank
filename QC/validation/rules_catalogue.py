#!/usr/bin/env python3
"""Generate QC/validation/RULES.md — the list of every validation rule.

There is no hand-maintained list of rule ids anywhere, so a finding like
`V135 trailing_punct_mismatch` sends the reader grepping. This builds the
list from the code that actually runs, which is the only version that cannot
drift (POL-039: the table is derived, not retyped).

Each rule module exposes `RULES` (and sometimes `CROSS_FILE_RULES`) as a list
of functions named `v<nnn>_<mnemonic>` or `g<nnn>_<mnemonic>`, each with a
docstring whose first sentence says what it checks. That is all this needs.

    python QC/validation/rules_catalogue.py            # write RULES.md
    python QC/validation/rules_catalogue.py --check    # exit 1 if stale

`tests/validators/test_rules_catalogue.py` runs --check, so a new rule fails
CI until the catalogue is regenerated.
"""
from __future__ import annotations

import argparse
import importlib
import inspect
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

OUTPUT = Path(__file__).resolve().parent / "RULES.md"

# module -> the validator that runs it. Mirrors the imports in each
# validate_*.py; a module gaining a second consumer belongs here.
VALIDATORS: list[tuple[str, str, list[str]]] = [
    ("validate_xml.py", "XSD conformance and structure", ["hard", "soft", "warn"]),
    ("validate_text.py", "text and typography", ["text"]),
    ("validate_glosses.py", "word/morpheme glossing", ["gloss"]),
    ("audit_gloss_scrape.py", "scrape-vs-source audit", ["gloss_scrape"]),
]

# Modules whose name fixes the severity of everything in them. text, gloss and
# gloss_scrape mix severities and state them in the docstring instead.
MODULE_SEVERITY = {"hard": "HARD", "soft": "SOFT", "warn": "WARN"}

_ID = re.compile(r"^([vg]\d+)_(.*)$")
_SEVERITY = re.compile(r"\b(HARD|SOFT|WARN)\b")


def summarize(fn, module_name: str) -> tuple[str, str]:
    """(severity, one-line description) for a rule function."""
    doc = inspect.cleandoc(fn.__doc__ or "")
    first = doc.split("\n\n")[0].replace("\n", " ").strip()
    severity_match = _SEVERITY.search(first)
    severity = MODULE_SEVERITY.get(
        module_name, severity_match.group(1) if severity_match else "")
    # Drop the leading "V135 SOFT (TR14): " restatement; the columns carry it.
    text = re.sub(r"^[VG]\d+\b[^:]*:\s*", "", first).strip()
    if not text:
        text = first
    if not text.endswith("."):
        text += "."
    return severity, text


def collect() -> list[tuple[str, str, str, str, str, str]]:
    """(rule_id, mnemonic, severity, scope, validator, description), sorted.

    Rules are never deduplicated by id. Two rules sharing one makes every
    finding under it ambiguous in the findings CSV, which is exactly the
    thing a catalogue should show rather than tidy away.
    """
    rows = []
    for validator, _, modules in VALIDATORS:
        for module_name in modules:
            module = importlib.import_module(f"QC.validation.rules.{module_name}")
            for scope, attr in (("file", "RULES"), ("corpus", "CROSS_FILE_RULES")):
                for fn in getattr(module, attr, []):
                    match = _ID.match(fn.__name__)
                    if match is None:
                        continue
                    severity, description = summarize(fn, module_name)
                    rows.append((match.group(1).upper(), match.group(2),
                                 severity, scope, validator, description))
    return sorted(rows, key=lambda r: (r[0][0], int(r[0][1:]), r[4]))


def duplicate_ids(rows) -> dict[str, list[str]]:
    """rule_id -> the validators claiming it, for ids claimed more than once."""
    claims: dict[str, list[str]] = {}
    for rule_id, mnemonic, _s, _sc, validator, _d in rows:
        claims.setdefault(rule_id, []).append(f"{validator}:{mnemonic}")
    return {k: v for k, v in claims.items() if len(v) > 1}


def render() -> str:
    rows = collect()
    out = [
        "# Validation rules",
        "",
        "Every rule the validators run, generated from the code by",
        "`QC/validation/rules_catalogue.py`. **Do not edit by hand** — add the rule",
        "to its module's `RULES` list and regenerate.",
        "",
        "**HARD** fails the run (exit 1 unless `--no-exit-on-hard`); **SOFT** and",
        "**WARN** are reported and do not. Scope `corpus` means the rule needs the",
        "whole collection, not one file. Per-finding detail goes to the findings CSV",
        "the validator names on its `Details:` line, never to the terminal.",
        "",
    ]
    duplicates = duplicate_ids(rows)
    if duplicates:
        out += ["> **Duplicate rule ids.** These ids are claimed by more than one",
                "> rule, so a finding under one is ambiguous until they are",
                "> renumbered:", ""]
        for rule_id, claims in sorted(duplicates.items()):
            out.append(f"> - **{rule_id}** — " + "; ".join(f"`{c}`" for c in claims))
        out.append("")

    for validator, blurb, _ in VALIDATORS:
        subset = [r for r in rows if r[4] == validator]
        if not subset:
            continue
        out += [f"## `{validator}` — {blurb}", "",
                "| Rule | Mnemonic | Severity | Scope | Checks |",
                "| --- | --- | --- | --- | --- |"]
        for rule_id, mnemonic, severity, scope, _v, description in subset:
            out.append(f"| {rule_id} | `{mnemonic}` | {severity or '—'} | "
                       f"{scope} | {description} |")
        out.append("")
    out += [f"{len(rows)} rules.", ""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if RULES.md is not what this would write")
    args = parser.parse_args()
    rendered = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(f"{OUTPUT} is stale; run: python {Path(__file__).name}",
                  file=sys.stderr)
            return 1
        print(f"{OUTPUT} is current.")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    rows = collect()
    print(f"Wrote {OUTPUT} ({len(rows)} rules)")
    for rule_id, claims in sorted(duplicate_ids(rows).items()):
        print(f"  warning: {rule_id} is claimed by {len(claims)} rules: "
              + ", ".join(claims), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
