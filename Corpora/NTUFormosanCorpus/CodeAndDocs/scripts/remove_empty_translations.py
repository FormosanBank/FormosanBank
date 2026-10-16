#!/usr/bin/env python3
"""Remove content-free TRANSL tiers from generated NTU XML."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import lxml.etree as etree


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def is_empty_translation(element: etree._Element) -> bool:
    return element.tag == "TRANSL" and not "".join(element.itertext()).strip()


def is_structural_unclear_translation(element: etree._Element) -> bool:
    """Return whether an otherwise text-empty TRANSL is exactly UNCLEAR."""
    if len(element) != 1:
        return False
    child = element[0]
    return (
        child.tag == "UNCLEAR"
        and not child.attrib
        and not (child.text or "").strip()
        and not (child.tail or "").strip()
    )


def remove_preserving_layout(element: etree._Element) -> None:
    parent = element.getparent()
    if parent is None:
        raise AssertionError("TRANSL has no parent")
    tail = element.tail
    previous = element.getprevious()
    parent.remove(element)
    if tail is not None:
        if previous is None:
            parent.text = tail
        else:
            previous.tail = tail


def process_file(path: Path, *, dry_run: bool = False) -> Counter[str]:
    tree = etree.parse(str(path))
    counts: Counter[str] = Counter()
    for translation in list(tree.iter("TRANSL")):
        if not is_empty_translation(translation):
            continue
        if is_structural_unclear_translation(translation):
            continue
        unexpected_attributes = set(translation.attrib) - {XML_LANG, "xml:lang"}
        if len(translation) or unexpected_attributes:
            raise AssertionError(
                f"refusing to remove structured empty TRANSL in {path}: "
                f"children={len(translation)} attributes={sorted(unexpected_attributes)}"
            )
        parent = translation.getparent()
        counts[f"empty {parent.tag} TRANSL removed"] += 1
        remove_preserving_layout(translation)
    if counts and not dry_run:
        path.write_bytes(etree.tostring(tree, xml_declaration=True, encoding="UTF-8"))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    totals: Counter[str] = Counter()
    changed_files = 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        counts = process_file(path, dry_run=args.dry_run)
        if counts:
            changed_files += 1
            totals.update(counts)
    print(f"files rewritten: {0 if args.dry_run else changed_files}")
    print(f"files requiring rewrite: {changed_files}")
    for label, count in sorted(totals.items()):
        print(f"{label}: {count}")


if __name__ == "__main__":
    main()
