#!/usr/bin/env python3
"""check_pending_lists.py — a changed corpus may not shelter on a pending list.

Four tests skip legacy corpora through root-level pending lists
(generate_xml_pending.txt, provenance_pending.txt, readme_sections_pending.txt,
xml_dir_pending.txt). The lists only shrink, and a corpus that is being
re-ported is the moment they are meant to shrink — but nothing enforced that,
so a re-port that left its corpus listed was never gated (the ILRDF and ePark
re-ports both did). This script is the gate: given the XML files a PR changes,
it names every changed corpus that still appears on any list and exits 1.

    git diff --name-only origin/main...HEAD -- 'Corpora/*/XML/**' \\
        | python QC/validation/check_pending_lists.py
    python QC/validation/check_pending_lists.py --changed changed_xml.txt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PENDING_LISTS = (
    "generate_xml_pending.txt",
    "provenance_pending.txt",
    "readme_sections_pending.txt",
    "xml_dir_pending.txt",
)


def corpora_of(changed_paths: list[str]) -> set[str]:
    """Corpus names whose published XML/ is among the changed paths."""
    out = set()
    for raw in changed_paths:
        parts = Path(raw.strip()).parts
        if len(parts) >= 3 and parts[0] == "Corpora" and parts[2] == "XML":
            out.add(parts[1])
    return out


def listed_corpora(pending_file: Path) -> set[str]:
    """Corpus names on one list; the first token of each non-comment line."""
    if not pending_file.exists():
        return set()
    names = set()
    for line in pending_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            names.add(line.split()[0])
    return names


def sheltered(changed: set[str], repo_root: Path = REPO_ROOT) -> list[tuple[str, str]]:
    """(corpus, list file) for every changed corpus still on a pending list."""
    hits = []
    for name in PENDING_LISTS:
        for corpus in sorted(changed & listed_corpora(repo_root / name), key=str.lower):
            hits.append((corpus, name))
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changed", type=Path, default=None,
                    help="file listing changed paths, one per line (default: stdin)")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    a = ap.parse_args(argv)
    lines = (a.changed.read_text(encoding="utf-8").splitlines() if a.changed
             else sys.stdin.read().splitlines())
    changed = corpora_of(lines)
    hits = sheltered(changed, a.repo_root)
    print(f"changed corpora: {', '.join(sorted(changed)) or '(none)'}")
    if not hits:
        print("none of them is on a pending list")
        return 0
    for corpus, name in hits:
        print(f"::error::{corpus} changes XML/ in this PR but is still listed in {name}; "
              f"a re-port or rebuild is when that line is deleted (the list only shrinks)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
