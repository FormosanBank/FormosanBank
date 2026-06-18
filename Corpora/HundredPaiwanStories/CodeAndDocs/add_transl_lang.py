#!/usr/bin/env python3
"""Back-fill xml:lang="eng" on TRANSL elements that lack a language attribute.

The morpheme-level (M) interlinear glosses in this corpus were emitted as bare
``<TRANSL>...</TRANSL>`` elements with no xml:lang. The sentence-level (S) free
translations already carry ``xml:lang="eng"``. All of the bare glosses are
English (English words plus Leipzig glossing abbreviations such as ``pf``,
``af``, ``obl``), so the correct language tag is ``eng``. Validator rule V023
requires every TRANSL to declare xml:lang, so this script adds it.

The edit is a targeted string replacement (not a full lxml re-serialization) so
the diff touches only the TRANSL tags and leaves all other formatting intact.
The replacement is safe because existing tags are written
``<TRANSL xml:lang=...`` with a space after ``TRANSL``, so the literal matches
``<TRANSL>`` / ``<TRANSL/>`` / ``<TRANSL />`` never touch a tag that already has
an attribute. After editing each file the script re-parses it with lxml and
asserts that (a) the file still parses, (b) the total TRANSL element count is
unchanged, and (c) zero TRANSL elements remain without xml:lang.

Usage (defaults to the corpus's own XML/ directory):

    python add_transl_lang.py                 # edit in place
    python add_transl_lang.py --dry-run       # report only, no writes
    python add_transl_lang.py --xml_dir PATH  # target a different directory
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

# Bare (attribute-less) TRANSL forms -> same tag carrying xml:lang="eng".
REPLACEMENTS = (
    ("<TRANSL>", '<TRANSL xml:lang="eng">'),
    ("<TRANSL/>", '<TRANSL xml:lang="eng"/>'),
    ("<TRANSL />", '<TRANSL xml:lang="eng" />'),
)


def transl_stats(xml_bytes: bytes) -> tuple[int, int]:
    """Return (total TRANSL elements, TRANSL elements lacking xml:lang)."""
    root = etree.fromstring(xml_bytes)
    total = missing = 0
    for transl in root.iter("TRANSL"):
        total += 1
        if transl.get(XML_LANG) is None:
            missing += 1
    return total, missing


def process_file(path: Path, dry_run: bool) -> int:
    """Edit one file; return the number of bare TRANSL tags fixed."""
    original = path.read_text(encoding="utf-8")
    before_total, before_missing = transl_stats(original.encode("utf-8"))

    fixed = original
    n_replaced = 0
    for old, new in REPLACEMENTS:
        n_replaced += fixed.count(old)
        fixed = fixed.replace(old, new)

    if n_replaced != before_missing:
        raise AssertionError(
            f"{path}: string replacement count ({n_replaced}) != lxml "
            f"missing-xml:lang count ({before_missing})"
        )

    if n_replaced == 0:
        return 0

    after_total, after_missing = transl_stats(fixed.encode("utf-8"))
    if after_total != before_total:
        raise AssertionError(
            f"{path}: TRANSL count changed {before_total} -> {after_total}"
        )
    if after_missing != 0:
        raise AssertionError(
            f"{path}: {after_missing} TRANSL still missing xml:lang after edit"
        )

    if not dry_run:
        path.write_text(fixed, encoding="utf-8")
    return n_replaced


def main() -> int:
    default_xml = Path(__file__).resolve().parent.parent / "XML"
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xml_dir", type=Path, default=default_xml,
                        help=f"Directory of XML files (default: {default_xml})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Report what would change without writing files.")
    args = parser.parse_args()

    files = sorted(args.xml_dir.glob("*.xml"))
    if not files:
        print(f"No .xml files found in {args.xml_dir}", file=sys.stderr)
        return 1

    total_fixed = files_changed = 0
    for path in files:
        n = process_file(path, args.dry_run)
        if n:
            files_changed += 1
            total_fixed += n
            print(f"  {path.name}: {n} TRANSL tags tagged xml:lang=\"eng\"")

    verb = "would tag" if args.dry_run else "tagged"
    print(f"\n{verb} {total_fixed} TRANSL elements across {files_changed} "
          f"of {len(files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
