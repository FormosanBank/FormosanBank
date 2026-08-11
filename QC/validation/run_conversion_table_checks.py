"""Run validate_conversion_table.py over every conversion table (CI driver).

Never fails (exit 0 always): per the 2026-08-10 maintainer ruling, phoneme
-level mismatches are often *legitimate* — earlier orthographies commonly
under-distinguish phonemes that Ortho113 distinguishes, and inventories
shift between orthographies as linguists reanalyze. So this driver only
*reports*, in two sections:

  1. STRUCTURAL — fix these: validator crashes, missing/unresolvable
     profiles, table-integrity errors. Data bugs; no linguistic judgment.
  2. PHONEME-LEVEL — review: mismatch/merge reports from tables that ran
     to completion. May be legitimate under-differentiation; record
     accepted cases in the table's construction notes.

Writes a Markdown summary to $GITHUB_STEP_SUMMARY when set (GitHub
Actions); always prints a plain-text version to stdout.

Usage: python QC/validation/run_conversion_table_checks.py [--repo-root PATH]
"""
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).resolve()
sys.path.insert(0, str(_HERE.parents[2]))

from QC.utilities._case_variants import resolve_source_profile  # noqa: E402

_TABLE_NAME = re.compile(r"^(?P<language>[^_]+)_(?P<scheme>[^_]+)_113\.tsv$")


def check_table(table: Path, repo_root: Path) -> tuple:
    """Return (category, table_name, detail) for one conversion table.

    category: 'ok' | 'structural' | 'phoneme'
    """
    match = _TABLE_NAME.match(table.name)
    if match is None:
        return ("structural", table.name,
                "filename does not follow <Language>_<Scheme>_113.tsv; "
                "profiles cannot be resolved")
    source_profile = resolve_source_profile(table)
    target_profile = (repo_root / "Orthographies" / "Ortho113"
                      / f"{match['language']}.tsv")
    if source_profile is None or not source_profile.exists():
        return ("structural", table.name,
                f"source profile missing: {source_profile}")
    if not target_profile.exists():
        return ("structural", table.name,
                f"target profile missing: {target_profile}")

    proc = subprocess.run(
        [sys.executable,
         str(repo_root / "QC" / "validation" / "validate_conversion_table.py"),
         str(source_profile), str(target_profile), str(table)],
        capture_output=True, text=True)
    if proc.stderr.strip() and "Traceback" in proc.stderr:
        last = proc.stderr.strip().splitlines()[-1]
        return ("structural", table.name, f"CRASH: {last}")
    if proc.returncode != 0:
        # Blocking verdicts from the validator = unresolved mismatches.
        tail = [line for line in proc.stdout.splitlines() if line.strip()][-3:]
        return ("phoneme", table.name, " | ".join(tail))
    return ("ok", table.name, "")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Report conversion-table health (never fails)")
    parser.add_argument("--repo-root", type=Path, default=_HERE.parents[2])
    args = parser.parse_args(argv)
    tables_dir = args.repo_root / "Orthographies" / "ConversionTables"

    results = [check_table(t, args.repo_root)
               for t in sorted(tables_dir.glob("*.tsv"))]
    ok = [r for r in results if r[0] == "ok"]
    structural = [r for r in results if r[0] == "structural"]
    phoneme = [r for r in results if r[0] == "phoneme"]

    lines = [
        f"# Conversion-table check: {len(ok)} OK, "
        f"{len(structural)} structural, {len(phoneme)} phoneme-level "
        f"(of {len(results)})",
        "",
        "## Structural defects — fix these (data bugs)",
    ]
    lines += [f"- **{name}**: {detail}" for _, name, detail in structural] \
        or ["- none"]
    lines += ["", "## Phoneme-level mismatches — review "
              "(may be legitimate under-differentiation)"]
    lines += [f"- **{name}**: {detail}" for _, name, detail in phoneme] \
        or ["- none"]
    report = "\n".join(lines)
    print(report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(report + "\n")
    return 0  # informational only, by maintainer ruling


if __name__ == "__main__":
    raise SystemExit(main())
