#!/usr/bin/env python3
"""Replace local filesystem paths in a QC evidence directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path


def path_variants(value: str) -> set[str]:
    """Return the common lexical and resolved spellings of a local path."""
    variants = {value, os.path.normpath(value), os.path.abspath(value), os.path.realpath(value)}
    for path in tuple(variants):
        if path.startswith("/var/"):
            variants.add(f"/private{path}")
        elif path.startswith("/private/var/"):
            variants.add(path.removeprefix("/private"))
        if path.startswith("/tmp/"):
            variants.add(f"/private{path}")
        elif path.startswith("/private/tmp/"):
            variants.add(path.removeprefix("/private"))
    return {path.rstrip("/") for path in variants if path and path != "/"}


def sanitize_file(path: Path, replacements: list[tuple[str, str]]) -> bool:
    try:
        content = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    sanitized = content
    for local_path, placeholder in replacements:
        sanitized = sanitized.replace(local_path, placeholder)
    if sanitized == content:
        return False
    path.write_text(sanitized, encoding="utf-8")
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc-dir", required=True, type=Path)
    parser.add_argument("--corpus-root", required=True)
    parser.add_argument("--formosanbank-root", required=True)
    parser.add_argument("--formosanbank-python", required=True)
    parser.add_argument("--scratch-root", required=True)
    args = parser.parse_args()

    replacements: list[tuple[str, str]] = []
    path_groups = (
        (str(args.qc_dir), "<QC_OUTPUT_DIR>"),
        (args.formosanbank_python, "<FORMOSANBANK_ROOT>/.venv/bin/python"),
        (args.corpus_root, "<CORPUS_ROOT>"),
        (args.formosanbank_root, "<FORMOSANBANK_ROOT>"),
        (args.scratch_root, "<QC_SCRATCH>"),
    )
    for local_path, placeholder in path_groups:
        replacements.extend(
            (variant, placeholder) for variant in path_variants(local_path)
        )
    replacements.sort(key=lambda replacement: len(replacement[0]), reverse=True)

    changed = 0
    for path in sorted(args.qc_dir.rglob("*")):
        if path.is_file() and sanitize_file(path, replacements):
            changed += 1
    print(f"Sanitized local paths in {changed} QC evidence files.")


if __name__ == "__main__":
    main()
