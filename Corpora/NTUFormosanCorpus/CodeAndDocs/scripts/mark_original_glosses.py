#!/usr/bin/env python3
"""Mark source-owned W/M glosses as original.

POL-036 requires source glosses to use ``TRANSL[@kindOf="original"]`` at
word and morpheme level.  NTU's parsers and repair scripts predate that
ownership attribute, so this finalization pass adds it after content-free
translations have been removed.  Sentence translations are not gloss tiers
and are left unchanged.  Existing original and standard gloss tiers are
preserved.

The pass refuses unknown ``kindOf`` values and files outside the corpus's
canonical lxml serialization.  It changes attributes only and is idempotent.
"""

from __future__ import annotations

import argparse
import collections
from pathlib import Path

from lxml import etree


ALLOWED_KINDS = {"original", "standard"}


def serialize(tree: etree._ElementTree) -> bytes:
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def validate_file(path: Path) -> None:
    original = path.read_bytes()
    tree = etree.parse(str(path))
    if serialize(tree) != original:
        raise AssertionError(f"XML does not round-trip canonically: {path}")

    for owner_tag in ("W", "M"):
        for owner in tree.iter(owner_tag):
            for translation in owner.findall("TRANSL"):
                kind = translation.get("kindOf")
                if kind is not None and kind not in ALLOWED_KINDS:
                    raise AssertionError(
                        f"unsupported TRANSL kindOf={kind!r}: "
                        f"{path} {owner.get('id')}"
                    )


def process_file(
    path: Path, *, prevalidated: bool = False
) -> collections.Counter[str]:
    if not prevalidated:
        validate_file(path)
    tree = etree.parse(str(path))

    counts: collections.Counter[str] = collections.Counter()
    for owner_tag in ("W", "M"):
        for owner in tree.iter(owner_tag):
            for translation in owner.findall("TRANSL"):
                kind = translation.get("kindOf")
                if kind is None:
                    translation.set("kindOf", "original")
                    counts[f"{owner_tag} glosses marked original"] += 1

    if counts:
        path.write_bytes(serialize(tree))

    missing = tree.xpath(".//W/TRANSL[not(@kindOf)] | .//W/M/TRANSL[not(@kindOf)]")
    if missing:
        raise AssertionError(f"unowned W/M glosses remain in {path}: {len(missing)}")
    return counts


def process_corpus(xml_dir: Path) -> collections.Counter[str]:
    paths = sorted(xml_dir.rglob("*.xml"))
    if not paths:
        raise AssertionError(f"no XML files found under {xml_dir}")

    # Validate the complete corpus before writing any file.  This prevents a
    # late serialization or ownership error from leaving a partial update.
    for path in paths:
        validate_file(path)

    totals: collections.Counter[str] = collections.Counter()
    for path in paths:
        counts = process_file(path, prevalidated=True)
        totals.update(counts)
        if counts:
            totals["XML files modified"] += 1
    totals["XML files checked"] = len(paths)
    return totals


def main() -> int:
    repo = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, default=repo / "XML")
    args = parser.parse_args()

    totals = process_corpus(args.xml_dir.resolve())
    print("Source gloss ownership passed")
    for label in (
        "XML files checked",
        "XML files modified",
        "W glosses marked original",
        "M glosses marked original",
    ):
        print(f"  {label}: {totals[label]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
