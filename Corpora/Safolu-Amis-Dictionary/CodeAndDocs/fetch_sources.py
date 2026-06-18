#!/usr/bin/env python3
"""Fetch pinned upstream sources for the Safolu Amis dictionary build.

Only the Safolu source is needed here: the generated g0v/amis-moedict docs/s JSON
(current data) plus the deprecated miaoski/amis-safolu generator repo for
provenance. The Poinsot dictionary moved to the Formosan-Poinsot-Amis-Dictionary repository.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES_DIR = ROOT / "_sources"

AMIS_MOEDICT_URL = "https://github.com/g0v/amis-moedict.git"
AMIS_SAFOLU_URL = "https://github.com/miaoski/amis-safolu.git"

AMIS_MOEDICT_REF = "e7c6976a0766e9b0aeb7083e2c06db60f5485252"
AMIS_SAFOLU_REF = "f512d5ba0d08f81b26093a9b7b4a85acac760a30"


def run(args: list[str], cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def fetch_checkout(path: Path, url: str, ref: str, sparse_paths: list[str]) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--filter=blob:none", "--sparse", "--no-checkout", url, str(path)])

    run(["git", "sparse-checkout", "init", "--no-cone"], cwd=path)
    run(["git", "sparse-checkout", "set", *sparse_paths], cwd=path)
    run(["git", "fetch", "--depth", "1", "origin", ref], cwd=path)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-dir", type=Path, default=DEFAULT_SOURCES_DIR)
    parser.add_argument("--amis-moedict-ref", default=AMIS_MOEDICT_REF)
    parser.add_argument("--amis-safolu-ref", default=AMIS_SAFOLU_REF)
    args = parser.parse_args()

    sources_dir = args.sources_dir.resolve()
    fetch_checkout(
        sources_dir / "amis-moedict",
        AMIS_MOEDICT_URL,
        args.amis_moedict_ref,
        ["/README.md", "/Makefile", "/about.html", "/docs/about.html", "/docs/s/"],
    )
    fetch_checkout(
        sources_dir / "amis-safolu",
        AMIS_SAFOLU_URL,
        args.amis_safolu_ref,
        [
            "/README.md",
            "/PREV_README.md",
            "/generate-moedict-json.rb",
            "/generate-ufff-code-to-example.rb",
            "/link-json-to-terms.rb",
            "/generate-json-from-sqlite.rb",
        ],
    )


if __name__ == "__main__":
    main()
