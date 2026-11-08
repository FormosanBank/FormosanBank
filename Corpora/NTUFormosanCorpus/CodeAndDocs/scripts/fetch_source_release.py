#!/usr/bin/env python3
"""Fetch NTU's published source JSONs at a pinned release (POL-047 acquisition).

NTU publishes the corpus JSONs from its glossParser tool
(github.com/liao961120/glossParser) to that repository's ``gh-pages`` branch,
served at https://yongfu.name/glossParser/<path>. Each rebuild there is a
release. ``source_release.tsv`` pins one release (a gh-pages commit) and maps
every local source file to the upstream file it is taken from -- NTU renames
files between releases, and sometimes re-publishes an edit under a new name,
so the mapping is explicit rather than assumed.

    python fetch_source_release.py            # write the pinned release into
                                              # grammar/ sentence/ story/ and
                                              # rewrite source_snapshot.json
    python fetch_source_release.py --check    # compare, change nothing
    python fetch_source_release.py --latest   # is there a newer release than the pin?

Every downloaded file must match the sha256 in the table, so a fetch can
never silently install different bytes. Never run by the build: the build reads
only the committed JSONs.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

CODEDOCS = Path(__file__).resolve().parents[1]
TABLE = CODEDOCS / "source_release.tsv"
SNAPSHOT = CODEDOCS / "source_snapshot.json"
REPO = "liao961120/glossParser"
SOURCE_DIRS = ("grammar", "sentence", "story")


def read_table() -> tuple[str, list]:
    lines = TABLE.read_text(encoding="utf-8").splitlines()
    commit = next(line.split("commit ", 1)[1].split()[0] for line in lines
                  if line.startswith("#") and "commit " in line)
    rows = list(csv.DictReader([line for line in lines if not line.startswith("#")],
                               delimiter="\t"))
    return commit, rows


def fetch(commit: str, path: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{REPO}/{commit}/{urllib.parse.quote(path)}"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except OSError:
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))
    raise AssertionError("unreachable")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def latest_release() -> str:
    url = f"https://api.github.com/repos/{REPO}/branches/gh-pages"
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)["commit"]["sha"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="download and compare with the committed files; change nothing")
    ap.add_argument("--latest", action="store_true",
                    help="report whether NTU has published a release newer than the pin")
    args = ap.parse_args()
    commit, rows = read_table()

    if args.latest:
        tip = latest_release()
        print(f"pinned release: {commit}\nlatest release: {tip}")
        print("up to date" if tip == commit else
              "NEWER RELEASE AVAILABLE: review it and update source_release.tsv")
        return 0 if tip == commit else 1

    local_rows = [r for r in rows if r["local_path"] != "-"]
    problems, entries = [], []
    for r in local_rows:
        data = fetch(r.get("commit") or commit, r["upstream_path"])   # a row may pin its own commit
        if sha256(data) != r["sha256"]:
            problems.append(f"{r['upstream_path']}: upstream bytes differ from the table's sha256")
            continue
        dest = CODEDOCS / r["local_path"]
        if args.check:
            if not dest.exists() or sha256(dest.read_bytes()) != r["sha256"]:
                problems.append(f"{r['local_path']}: committed file differs from the pinned release")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        entries.append({"path": r["local_path"], "status": r["relation"],
                        "upstream_path": r["upstream_path"], "sha256": r["sha256"],
                        "records": int(r["records"]),
                        **({"upstream_commit": r["commit"]} if r.get("commit") else {})})
    listed = {r["local_path"] for r in local_rows}
    stray = sorted(p.relative_to(CODEDOCS).as_posix() for d in SOURCE_DIRS
                   for p in (CODEDOCS / d).rglob("*.json")
                   if p.relative_to(CODEDOCS).as_posix() not in listed)
    if args.check:
        problems += [f"{p}: not in source_release.tsv" for p in stray]
    else:
        for p in stray:
            (CODEDOCS / p).unlink()
            print(f"removed {p} (not in the pinned release)")
        SNAPSHOT.write_text(json.dumps({
            "schema_version": 1,
            "source_page": "https://corpus.linguistics.ntu.edu.tw/",
            "data_store": "https://yongfu.name/glossParser/",
            "upstream_repository": f"https://github.com/{REPO}",
            "upstream_branch": "gh-pages",
            "upstream_commit": commit,
            "notes": "Written by scripts/fetch_source_release.py from source_release.tsv. "
                     "'status' is the relation to the upstream file: same, renamed, or "
                     "edited_variant (NTU re-published an edit under another name).",
            "files": sorted(entries, key=lambda e: e["path"]),
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for p in problems:
        print(p, file=sys.stderr)
    print(f"{'checked' if args.check else 'wrote'} {len(entries)} files from release {commit[:7]}; "
          f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
