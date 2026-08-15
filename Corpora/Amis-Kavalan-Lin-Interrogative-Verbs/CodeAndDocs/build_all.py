#!/usr/bin/env python3
"""Rebuild Lin XML and all machine-owned tiers in policy order."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "CodeAndDocs"
XML = ROOT / "XML"
REQUIRED_QC_COMMIT = "3a3c47c220520113f747e6a2d441494000e13c4b"


def run(command: list[str]) -> None:
    print("==>", " ".join(command), flush=True)
    subprocess.run(command, check=True, cwd=ROOT)


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def resolve_formosanbank() -> Path:
    configured = os.environ.get("FORMOSANBANK_PATH") or os.environ.get("FORMOSANBANK_QC_ROOT")
    path = Path(configured).expanduser() if configured else ROOT.parent / "FormosanBank"
    path = path.resolve()
    if not (path / "QC").is_dir() or not (path / "Orthographies").is_dir():
        raise RuntimeError("Set FORMOSANBANK_PATH to the governing FormosanBank checkout")
    if git_output(path, "status", "--porcelain"):
        raise RuntimeError("The read-only FormosanBank checkout must be clean")
    if git_output(path, "rev-parse", "HEAD") != REQUIRED_QC_COMMIT:
        raise RuntimeError(f"FormosanBank must be pinned to {REQUIRED_QC_COMMIT}")
    git_output(path, "rev-parse", "--verify", "refs/remotes/origin/main")
    if subprocess.run(
        [
            "git",
            "-C",
            str(path),
            "diff",
            "--quiet",
            "origin/main",
            "--",
            "QC",
            "Orthographies",
            "standards.csv",
            "dialects.csv",
            "languages.csv",
        ],
        check=False,
    ).returncode:
        raise RuntimeError("FormosanBank tools or registries differ from fetched origin/main")
    return path


def main() -> None:
    formosanbank = resolve_formosanbank()
    dependency_before = (
        git_output(formosanbank, "rev-parse", "HEAD"),
        git_output(formosanbank, "status", "--porcelain"),
    )
    qc_python = Path(
        os.environ.get("FORMOSANBANK_QC_PYTHON", str(formosanbank / ".venv/bin/python"))
    )
    if not os.access(qc_python, os.X_OK):
        raise RuntimeError(f"QC Python is not executable: {qc_python}")

    run([sys.executable, str(CODE / "build_xml.py")])
    run(
        [
            str(qc_python),
            str(formosanbank / "QC/cleaning/apply_manual_edits.py"),
            "--corpora_path",
            str(XML),
        ]
    )
    run(
        [
            str(qc_python),
            str(formosanbank / "QC/cleaning/clean_xml.py"),
            "--corpora_path",
            str(XML),
        ]
    )
    run(
        [
            str(qc_python),
            str(formosanbank / "QC/validation/validate_conversion_table.py"),
            str(CODE / "Orthographies/LinAmis/Amis.tsv"),
            str(formosanbank / "Orthographies/Ortho113/Amis.tsv"),
            str(CODE / "Orthographies/ConversionTables/Amis_LinAmis_113.tsv"),
            "--dialect",
            "Xiuguluan",
        ]
    )
    run(
        [
            str(qc_python),
            str(formosanbank / "QC/utilities/standardize.py"),
            "--tsv_path",
            str(CODE / "Orthographies/ConversionTables/Amis_LinAmis_113.tsv"),
            "--target_column",
            "Xiuguluan",
            "--corpora_path",
            str(XML / "Amis"),
        ]
    )
    run(
        [
            str(qc_python),
            str(formosanbank / "QC/utilities/standardize.py"),
            "--remove_accents",
            "--corpora_path",
            str(XML / "Kavalan"),
        ]
    )
    run(
        [
            sys.executable,
            str(CODE / "generate_amis_phonology.py"),
            "--formosanbank-root",
            str(formosanbank),
            "--corpora-path",
            str(XML / "Amis"),
        ]
    )
    run(
        [
            str(qc_python),
            str(formosanbank / "QC/utilities/add_phonology.py"),
            "--orthography",
            "Ortho113",
            "--corpora_path",
            str(XML / "Kavalan"),
        ]
    )

    for sidecar in (
        XML / "cleaner_warnings.csv",
        XML / "standardize_warnings.csv",
        XML / "Amis/standardize_warnings.csv",
        XML / "Kavalan/standardize_warnings.csv",
    ):
        if sidecar.exists():
            sidecar.unlink()

    run([sys.executable, str(CODE / "audit_source_alignment.py")])
    dependency_after = (
        git_output(formosanbank, "rev-parse", "HEAD"),
        git_output(formosanbank, "status", "--porcelain"),
    )
    if dependency_after != dependency_before:
        raise RuntimeError("The build modified the read-only FormosanBank dependency")


if __name__ == "__main__":
    main()
