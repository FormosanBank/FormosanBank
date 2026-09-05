#!/usr/bin/env python3
"""Report any change to a corpus's licence between two trees (POL-044).

Modelled on QC/tokens_delta.py. There is no committed baseline: a merge
check has both sides available, and a stored baseline is redundant state
that can itself drift. Exits 1 on any change, so a licence cannot move
without a maintainer overriding a red check.

Usage:
    python QC/validation/rights_delta.py --base <dir> --head <dir>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from QC.validation._rights import corpus_license  # noqa: E402


def licenses_at(corpora_path: Path) -> dict[str, str]:
    """Corpus name -> licence, for every corpus that publishes XML."""
    result: dict[str, str] = {}
    for corpus_dir in sorted(Path(corpora_path).iterdir()):
        if not corpus_dir.is_dir():
            continue
        value = corpus_license(corpus_dir)
        if value is not None:
            result[corpus_dir.name] = value
    return result


def compare(base: dict[str, str], head: dict[str, str]) -> list[str]:
    """Human-readable lines for every difference; empty when unchanged."""
    lines: list[str] = []
    for corpus in sorted(set(base) | set(head)):
        before, after = base.get(corpus), head.get(corpus)
        if before == after:
            continue
        if before is None:
            lines.append(f"{corpus}: added with {after!r}")
        elif after is None:
            lines.append(f"{corpus}: removed (was {before!r})")
        else:
            lines.append(f"{corpus}: {before!r} -> {after!r}")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--head", required=True, type=Path)
    args = parser.parse_args(argv)

    lines = compare(licenses_at(args.base), licenses_at(args.head))
    if not lines:
        print("No corpus licence changed.")
        return 0
    print("Corpus licence changes (POL-044 — these require maintainer review):")
    for line in lines:
        print(f"  {line}")
    print(
        "\nA licence change is never routine. If it is correct, a maintainer "
        "overrides this check; there is no label-based bypass."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
