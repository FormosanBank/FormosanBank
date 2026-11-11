#!/usr/bin/env python3
"""Which corpora did a change touch? Lets a CI job skip corpora that cannot have changed.

    python QC/validation/touched_corpora.py --range "$BASE...HEAD" \
        --code QC/validation/rights_delta.py --code .github/workflows/rights-comparison.yaml \
        --out touched.txt

Prints one line, ``scope=all``, ``scope=some`` or ``scope=none`` (append it to
``$GITHUB_OUTPUT``), and writes the corpus names to ``--out``, one per line:

* ``all``  -- every corpus under Corpora/ that has an XML/ folder. Chosen when a
  ``--code`` path changed (the job's own script, shared code it uses, or its
  workflow file: then every result can change), when ``--range`` is empty
  (a manual run) or cannot be resolved (e.g. the push's old tip was rewritten).
* ``some`` -- each Corpora/<name>/ with any changed file. A name may be absent
  at HEAD (a deleted or renamed corpus); callers that read HEAD skip it.
* ``none`` -- nothing under Corpora/ changed and no --code path did.

A ``--code`` value ending in ``/`` matches everything below it.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def changed_files(rng: str, repo: Path) -> list[str] | None:
    proc = subprocess.run(
        ["git", "-c", "core.quotePath=false", "diff", "--name-only", "-z", rng],
        cwd=repo, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return None
    return [p for p in proc.stdout.split("\0") if p]


def all_corpora(repo: Path) -> list[str]:
    root = repo / "Corpora"
    return sorted(d.name for d in root.iterdir() if d.is_dir() and (d / "XML").is_dir())


def decide(files: list[str] | None, code: list[str], repo: Path) -> tuple[str, list[str], str]:
    if files is None:
        return "all", all_corpora(repo), "range could not be resolved"
    hits = [f for f in files for c in code if (f.startswith(c) if c.endswith("/") else f == c)]
    if hits:
        return "all", all_corpora(repo), f"code changed: {hits[0]}"
    touched = sorted({f.split("/")[1] for f in files if f.startswith("Corpora/") and f.count("/") >= 2})
    if touched:
        return "some", touched, f"{len(touched)} corpora touched"
    return "none", [], "no corpus or code path changed"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--range", default="", help='git diff range, e.g. "BASE...HEAD"; empty = everything')
    ap.add_argument("--code", action="append", default=[], help="path whose change means every corpus")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=REPO_ROOT)
    args = ap.parse_args(argv)
    if args.range:
        scope, names, why = decide(changed_files(args.range, args.repo), args.code, args.repo)
    else:
        scope, names, why = "all", all_corpora(args.repo), "no range given (manual run)"
    args.out.write_text("".join(n + "\n" for n in names), encoding="utf-8")
    print(f"scope={scope}")
    print(f"{why}; {len(names)} corpora: {' '.join(names)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
