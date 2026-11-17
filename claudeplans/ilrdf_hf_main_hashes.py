#!/usr/bin/env python3
"""List the SHA-256 fingerprint and size of every file in the ILRDF_Dicts Hugging Face dataset, at the revision
pinned in audio_sources.json. Downloads NO audio: it reads Hugging Face's file listing (the LFS fingerprint
Hugging Face stores for each file).

Run on the Mac from the FormosanBank checkout root (safe to run while the fingerprint script is running):

    python3 claudeplans/ilrdf_hf_main_hashes.py

Writes claudeplans/ilrdf-hf-main-hashes.tsv (path, size, sha256). If the dataset needs a login: export HF_TOKEN=...
Python standard library + curl only.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "ilrdf-hf-main-hashes.tsv"
REPO = "FormosanBank/ILRDF_Dicts"


def pinned_revision() -> str:
    d = json.loads((HERE.parent / "audio_sources.json").read_text(encoding="utf-8"))
    return next(x["revision"] for x in d["datasets"] if x["corpus"] == "ILRDF_Dicts")


def next_link(headers: str) -> str | None:
    """The rel="next" URL from an HTTP Link header, if any."""
    for line in headers.splitlines():
        if line.lower().startswith("link:"):
            m = re.search(r'<([^>]+)>;\s*rel="next"', line)
            if m:
                return m.group(1)
    return None


def rows_from_page(entries: list) -> list[dict]:
    out = []
    for e in entries:
        if e.get("type") != "file":
            continue
        lfs = e.get("lfs") or {}
        out.append(dict(path=e["path"], size=lfs.get("size", e.get("size", "")),
                        sha256=lfs.get("oid", ""), note="" if lfs else "not LFS: no sha256 given"))
    return out


def fetch(url: str, tmp: str, token: str | None) -> tuple[str, list]:
    cmd = ["curl", "-sfL", "--retry", "4", "--retry-delay", "3", "--max-time", "120", "-D", tmp + ".h", "-o", tmp]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    r = subprocess.run(cmd + [url], capture_output=True)
    if r.returncode != 0:
        sys.exit(f"curl failed ({r.returncode}) on {url}")
    return Path(tmp + ".h").read_text(errors="replace"), json.loads(Path(tmp).read_text(encoding="utf-8"))


def main() -> None:
    import os
    token = os.environ.get("HF_TOKEN")
    rev = pinned_revision()
    url = f"https://huggingface.co/api/datasets/{REPO}/tree/{rev}?recursive=true"
    rows, pages = [], 0
    with tempfile.TemporaryDirectory() as d:
        while url:
            headers, entries = fetch(url, os.path.join(d, "page"), token)
            rows += rows_from_page(entries); pages += 1
            if pages % 10 == 0:
                print(f"  {pages} pages, {len(rows)} files", flush=True)
            url = next_link(headers)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "size", "sha256", "note"], delimiter="\t")
        w.writeheader(); w.writerows(rows)
    print(f"revision {rev}: {len(rows)} files in {pages} pages "
          f"({sum(1 for r in rows if r['sha256'])} with a sha256). Wrote {OUT}")


if __name__ == "__main__":
    main()
