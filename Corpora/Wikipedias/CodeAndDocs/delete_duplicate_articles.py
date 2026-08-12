#!/usr/bin/env python3
"""Delete duplicate-download copies of articles (maintainer ruling 2026-08-12).

The Wikipedia scrape saved some articles twice: the duplicate download was
written as ``<name> (1).xml`` (or ``(2)``) next to ``<name>.xml``, but the
TEXT/@id — derived from the article title, not the filename — came out
identical, violating POL-037 (TEXT ids must be unique across FormosanBank).
29 id groups / 58 files are affected (the V081 baseline).

Ruling: keep exactly ONE file per group and delete the rest (rather than
disambiguating the ids of the extra copies).

Deterministic keep rule:

- If the group has exactly one file WITHOUT a duplicate-download counter,
  that canonically-named file is kept (e.g. ``Haba.xml`` over ``Haba (1).xml``).
- Otherwise (a group made only of counter-named files, e.g. Atayal ``msin``
  and Sakizaya ``Oro’raw``) the lowest counter is kept, i.e. ``(1)``.
- A group with two or more counter-less files is an error (cannot choose).

Every group in the corpus is byte-identical across its copies (verified),
so nothing is lost. Should that ever stop holding, the script does not
guess: it keeps the canonical file per the rule above and prints a
``CONTENT DIFFERS`` block listing the FORM-level differences, so the
divergence lands in the run log rather than being silently dropped.

Idempotent: once each id has a single file, reruns delete nothing.
"""

import argparse
import difflib
import hashlib
import re
import sys
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

COUNTER_RE = re.compile(r" \((\d+)\)\.xml$")
ID_RE = re.compile(r'(<TEXT\b[^>]*?\bid=")([^"]*)(")', re.DOTALL)


def text_id(path: Path) -> str:
    m = ID_RE.search(path.read_text(encoding="utf-8"))
    if not m:
        sys.exit(f"no TEXT id found in {path}")
    return m.group(2)


def forms(path: Path) -> list[str]:
    """Flat list of ``kindOf: text`` strings for every FORM in the file."""
    root = ET.parse(path).getroot()
    return [f"{e.get('kindOf')}: {(e.text or '').strip()}"
            for e in root.iter("FORM")]


def keeper(group: list[Path]) -> Path:
    plain = [f for f in group if not COUNTER_RE.search(f.name)]
    if len(plain) == 1:
        return plain[0]
    if plain:
        sys.exit(f"cannot choose a keeper among {len(plain)} counter-less "
                 f"files: {plain}")
    return min(group, key=lambda f: int(COUNTER_RE.search(f.name).group(1)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpora_path", type=Path,
                    default=Path(__file__).resolve().parent.parent / "XML",
                    help="Wikipedias XML root (default: sibling XML/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be deleted without deleting")
    args = ap.parse_args()

    ids = defaultdict(list)
    for f in sorted(args.corpora_path.rglob("*.xml")):
        ids[text_id(f)].append(f)

    groups = 0
    deleted = 0
    differing = 0
    for tid, group in sorted(ids.items()):
        if len(group) < 2:
            continue
        groups += 1
        keep = keeper(group)
        drop = [f for f in group if f != keep]

        hashes = {hashlib.md5(f.read_bytes()).hexdigest() for f in group}
        if len(hashes) > 1:
            differing += 1
            print(f"CONTENT DIFFERS in id {tid!r} (keeping {keep.name}):")
            base = forms(keep)
            for f in drop:
                diff = list(difflib.unified_diff(
                    base, forms(f), keep.name, f.name, lineterm="", n=0))
                print("\n".join("  " + line for line in diff) or
                      f"  {f.name}: FORMs identical, bytes differ")

        for f in drop:
            print(f"delete {f}  (duplicate of {keep.name}; id {tid!r})")
            if not args.dry_run:
                f.unlink()
            deleted += 1

    verb = "would delete" if args.dry_run else "deleted"
    print(f"{verb} {deleted} duplicate article files in {groups} id groups "
          f"({differing} group(s) with differing content)")


if __name__ == "__main__":
    main()
