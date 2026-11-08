#!/usr/bin/env python3
"""Snapshot the ILRDF_Dicts XML that `main` published before the v2 rebuild.

POL-035 baseline. The v2 build keeps main's sentence ids (POL-037), keeps the
main sentences that are no longer in the 2026 source, and falls back to main's
recordings where the 2026 source has none. All three need main's published XML
as a build input, and the build may only read committed files (POL-048), so
this script copies it -- byte for byte, gzip-compressed -- into
source_data/main_2024/ and records where it came from.

Run once, deliberately; never from generate_xml.sh:

    python CodeAndDocs/snapshot_main_xml.py <commit>

<commit> is the FormosanBank commit whose Corpora/ILRDF_Dicts/XML/ is the
baseline (the one recorded in source_data/main_2024/manifest.json).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess

from ilrdf_source import LANGUAGES

BASE = Path(__file__).resolve().parent
OUT = BASE / "source_data" / "main_2024"
REPO = BASE.parents[2]


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(REPO), *args], check=True, capture_output=True
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("commit")
    args = parser.parse_args()
    commit = git("rev-parse", "--verify", f"{args.commit}^{{commit}}").decode().strip()
    OUT.mkdir(parents=True, exist_ok=True)
    files = []
    for language in LANGUAGES:
        path = f"Corpora/ILRDF_Dicts/XML/{language}/{language}.xml"
        blob = git("rev-parse", f"{commit}:{path}").decode().strip()
        raw = git("cat-file", "blob", blob)
        target = OUT / f"{language}.xml.gz"
        # mtime=0 and no file name in the header: the same input always
        # compresses to the same bytes.
        with target.open("wb") as handle:
            with gzip.GzipFile(filename="", mode="wb", fileobj=handle,
                               compresslevel=9, mtime=0) as gz:
                gz.write(raw)
        files.append({
            "language": language,
            "file": target.name,
            "source_path": path,
            "git_blob": blob,
            "uncompressed_sha256": hashlib.sha256(raw).hexdigest(),
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
        })
        print(f"{language}: {len(raw):,} bytes -> {target.name}")
    manifest = {
        "_note": (
            "POL-035 snapshot of the ILRDF_Dicts XML published on main before "
            "the 2026 rebuild (the 2024 scrape). Written by snapshot_main_xml.py; "
            "never edit by hand (POL-038)."
        ),
        "formosanbank_commit": commit,
        "files": files,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
