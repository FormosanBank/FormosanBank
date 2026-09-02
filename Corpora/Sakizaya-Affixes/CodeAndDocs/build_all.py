#!/usr/bin/env python3
"""Rebuild every committed XML/report output in dependency order."""

from __future__ import annotations

import csv
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "XML"
CODE = ROOT / "CodeAndDocs"
REQUIRED_QC_COMMIT = "3a3c47c220520113f747e6a2d441494000e13c4b"
SOURCE_SCRIPTS = (
    "build_xml.py",
    "build_table_xml.py",
)
STANDARDIZATION_TABLE = CODE / "source_data/sakizaya_affixes_standardization.tsv"
AUDIT_SCRIPTS = (
    "audit_source_alignment.py",
    "audit_table_outputs.py",
    "audit_xml_format.py",
    "audit_source_spot_checks.py",
    "audit_random_source_checks.py",
    "audit_complete_source_review.py",
    "write_page_coverage.py",
)


def run(command: list[str], *, cwd: Path = ROOT) -> None:
    print("==>", " ".join(command), flush=True)
    subprocess.run(command, check=True, cwd=cwd)


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args],
        text=True,
    ).strip()


def resolve_qc_root() -> Path:
    configured = os.environ.get("FORMOSANBANK_QC_ROOT")
    qc_root = Path(configured).expanduser() if configured else ROOT.parent / "FormosanBank"
    qc_root = qc_root.resolve()
    if not (qc_root / "QC").is_dir() or not (qc_root / "Orthographies/Ortho113").is_dir():
        raise RuntimeError("Set FORMOSANBANK_QC_ROOT to a FormosanBank checkout with QC and Orthographies/Ortho113")
    if git_output(qc_root, "status", "--porcelain"):
        raise RuntimeError("Refusing build: the read-only FormosanBank dependency is not clean")
    git_output(qc_root, "rev-parse", "--verify", "refs/remotes/origin/main")
    diff = subprocess.run(
        [
            "git",
            "-C",
            str(qc_root),
            "diff",
            "--quiet",
            "origin/main",
            "--",
            "QC",
            "Orthographies",
        ],
        check=False,
    )
    if diff.returncode != 0:
        raise RuntimeError(
            "Refusing build: checked-out QC/Orthographies differ from fetched origin/main"
        )
    return qc_root


def normalize_cleaner_warning_paths(path: Path) -> None:
    """Keep generated evidence reproducible across local checkout paths."""

    if not path.exists():
        return
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames
    if not fieldnames:
        raise RuntimeError(f"Cleaner warning CSV has no header: {path}")
    for row in rows:
        warning_path = Path(row["file"])
        try:
            row["file"] = str(warning_path.relative_to(ROOT))
        except ValueError:
            row["file"] = warning_path.name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    qc_root = resolve_qc_root()
    qc_head = git_output(qc_root, "rev-parse", "HEAD")
    if qc_head != REQUIRED_QC_COMMIT:
        raise RuntimeError(
            f"FormosanBank must be pinned to {REQUIRED_QC_COMMIT}; found {qc_head}"
        )
    qc_status = git_output(qc_root, "status", "--porcelain")
    qc_python = Path(
        os.environ.get("FORMOSANBANK_QC_PYTHON", str(qc_root / ".venv/bin/python"))
    )
    if not os.access(qc_python, os.X_OK):
        raise RuntimeError(f"FormosanBank QC Python is not executable: {qc_python}")

    for script in SOURCE_SCRIPTS:
        run([sys.executable, str(CODE / script)])

    run(
        [
            str(qc_python),
            str(qc_root / "QC/cleaning/apply_manual_edits.py"),
            "--corpora_path",
            str(FINAL),
        ]
    )
    run(
        [
            str(qc_python),
            str(qc_root / "QC/cleaning/clean_xml.py"),
            "--corpora_path",
            str(FINAL),
        ]
    )
    generated_warnings = FINAL / "cleaner_warnings.csv"
    committed_warnings = CODE / "cleaner_warnings.csv"
    if generated_warnings.exists():
        shutil.move(str(generated_warnings), committed_warnings)
        normalize_cleaner_warning_paths(committed_warnings)
    elif committed_warnings.exists():
        committed_warnings.unlink()

    run(
        [
            str(qc_python),
            str(qc_root / "QC/utilities/standardize.py"),
            "--tsv_path",
            str(STANDARDIZATION_TABLE),
            "--target_column",
            "standard",
            "--corpora_path",
            str(FINAL),
        ]
    )
    run(
        [
            str(qc_python),
            str(qc_root / "QC/utilities/add_phonology.py"),
            "--corpora_path",
            str(FINAL),
        ]
    )

    for script in AUDIT_SCRIPTS:
        run([sys.executable, str(CODE / script)])

    if git_output(qc_root, "rev-parse", "HEAD") != qc_head or git_output(
        qc_root, "status", "--porcelain"
    ) != qc_status:
        raise RuntimeError("Build modified the read-only FormosanBank dependency")


if __name__ == "__main__":
    main()
