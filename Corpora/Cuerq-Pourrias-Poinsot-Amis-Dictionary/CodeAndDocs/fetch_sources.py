#!/usr/bin/env python3
"""Fetch the pinned upstream sources for the Amis-Chinese Poinsot build (build_amis_chinese_xml.py).

  wildjcrt/amis-chinese-poinsot-onefile   pourrias-poinsot.txt: the 2020 crowd transcription, one entry per line
  miaoski/amis-chinese-poinsot (toufu)    toufu.sq3: the 2020 proofreading database (printed page + line per line)
  miaoski/amis-francais                   txt/001.txt-004.txt: French pages 1-4, hand-checked upstream in 2015
                                          (data/french_pages_1_4.json was made from them)

The page scans used for checking (miaoski/amis-chinese-poinsot, branch master, convert/) are large and are not
needed to build; fetch them with --scans.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]   # the corpus root
DEFAULT_SOURCES_DIR = ROOT / "_sources"     # full upstream clones (gitignored); refresh_source.sh copies the two build inputs into source/

ONEFILE_URL = "https://github.com/wildjcrt/amis-chinese-poinsot-onefile.git"
ONEFILE_REF = "365cfceca84c0edbb6af08133ce4e05e5c5291c0"
TOUFU_URL = "https://github.com/miaoski/amis-chinese-poinsot.git"
TOUFU_REF = "a35e2cbfd48002e15ddca87f674045c0376ed2cc"          # branch toufu
FRANCAIS_URL = "https://github.com/miaoski/amis-francais.git"
FRANCAIS_REF = "8d74f90368279f8a2cd92a25c62f994dca573704"


def run(args: list[str], cwd: Path | None = None) -> None:
    subprocess.run(args, cwd=cwd, check=True)


def fetch_sparse(path: Path, url: str, ref: str, sparse_paths: list[str]) -> None:
    if not path.exists():
        run(["git", "clone", "--filter=blob:none", "--sparse", "--no-checkout", url, str(path)])
    run(["git", "sparse-checkout", "init", "--no-cone"], cwd=path)
    run(["git", "sparse-checkout", "set", *sparse_paths], cwd=path)
    run(["git", "fetch", "--depth", "1", "origin", ref], cwd=path)
    run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources-dir", type=Path, default=DEFAULT_SOURCES_DIR)
    parser.add_argument("--scans", action="store_true", help="also fetch the page scan strips (several GB)")
    args = parser.parse_args()
    d = args.sources_dir.resolve()
    fetch_sparse(d / "amis-chinese-poinsot-onefile", ONEFILE_URL, ONEFILE_REF, ["/pourrias-poinsot.txt", "/README.md"])
    fetch_sparse(d / "amis-chinese-poinsot-toufu", TOUFU_URL, TOUFU_REF, ["/toufu.sq3", "/README.md"])
    fetch_sparse(d / "amis-francais", FRANCAIS_URL, FRANCAIS_REF, ["/txt/001.txt", "/txt/002.txt", "/txt/003.txt",
                                                                  "/txt/004.txt", "/README.md"])
    if args.scans:
        fetch_sparse(d / "amis-chinese-poinsot-scans", TOUFU_URL, "master", ["/convert/"])


if __name__ == "__main__":
    main()
