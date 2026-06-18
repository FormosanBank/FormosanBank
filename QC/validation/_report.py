"""Shared terminal reporter for the finding-based validators.

Single source of truth for how validate_xml / validate_glosses /
validate_text / validate_audio present results: a compact per-rule count
summary on the terminal (HARD then SOFT), plus one detail CSV (written only
when there are findings) whose path is printed. Per-finding detail no longer
floods the terminal — it lives in the CSV.

Usage from a validator's main():

    has_hard = report_findings(all_findings, args.csv, file_count=len(targets))
    if has_hard and not args.no_exit_on_hard:
        return 1
    return 0
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import TextIO

from QC.validation._finding import (
    Finding,
    Severity,
    summarize,
    write_findings_csv,
)
from QC.validation._rule_titles import RULE_TITLES

# Order severities appear in the summary.
_SECTION_ORDER = (Severity.HARD, Severity.SOFT, Severity.WARN)


def report_findings(
    findings: list[Finding],
    csv_path: Path,
    *,
    file_count: int,
    out: TextIO = sys.stderr,
    titles: dict[str, str] | None = None,
) -> bool:
    """Print the summary, write the detail CSV (if any findings), return has_hard.

    - ``findings``: every finding from the run (all severities).
    - ``csv_path``: where the one detail CSV is written. Only written when
      there is at least one finding; its path is then printed.
    - ``file_count``: total files processed (including clean ones), for the
      header line. Files-with-issues is derived from the findings.
    - ``out``: stream to print the summary to (default stderr).

    Returns True if any HARD finding was present.
    """
    if titles is None:
        titles = RULE_TITLES

    files_with_issues = len({str(f.path) for f in findings})
    print(
        f"=== Validation summary: {file_count} files, "
        f"{files_with_issues} with issues ===",
        file=out,
    )

    # The CSV is always written (header-only when clean) so downstream tooling
    # — CI artifact uploads, the run-qc-pipeline skill — always has a file.
    write_findings_csv(csv_path, findings, titles)

    if not findings:
        print("No issues found.", file=out)
        return False

    counts = summarize(findings)
    for severity in _SECTION_ORDER:
        per_rule = counts[severity]
        if not per_rule:
            continue
        total = sum(per_rule.values())
        print(f"{severity.value} — {total} total:", file=out)
        for rule_id in sorted(per_rule):
            mnemonic = titles.get(rule_id, "")
            label = f"{rule_id} {mnemonic}" if mnemonic else rule_id
            print(f"  {label}: {per_rule[rule_id]}", file=out)

    print(f"Details: {csv_path}", file=out)

    return bool(counts[Severity.HARD])
