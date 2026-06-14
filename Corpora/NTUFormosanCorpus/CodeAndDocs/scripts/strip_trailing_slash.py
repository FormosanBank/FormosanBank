#!/usr/bin/env python3
"""strip_trailing_slash.py

Strip a stray trailing ``/`` from W/M FORM and PHON.

Background
----------
A run of source records (Bunun ``63``) ends a word with a slash and an
empty second alternative -- ``bunbun?/``, ``ha?/``, ``mai-babu=tan?/`` --
where the ``?`` is sentence-final punctuation the tokenizer kept on the
last word and the ``/`` is a transcription artifact, not a real
alternation. The matching glosses carry no slash (survey 2026-06: 0 of
72 gloss tiers on these words is slashed), confirming there is no
alternation to expand; the sentence-level FORM never contains the stray
slash either. Slashes are forbidden in W/M FORMs (validate_text V121).

This step removes trailing ``/`` characters (only at the very end of a
FORM/PHON text) from W- and M-level elements. A genuine alternation has
``/`` between forms, never at the end, so real ``a/b`` forms (handled by
expand_slash_alternatives.py) are untouched. No other character is
changed.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python strip_trailing_slash.py            # corpus XML/ by default
    python strip_trailing_slash.py --dry-run
"""

import argparse
import collections
import os
from pathlib import Path

import lxml.etree as etree


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    modified = False
    for level in ("W", "M"):
        for el in root.iter(level):
            for child in el:
                if child.tag not in ("FORM", "PHON"):
                    continue
                text = child.text or ""
                if text.endswith("/"):
                    child.text = text.rstrip("/")
                    stats[f"{child.tag} trailing / stripped ({level})"] += 1
                    modified = True
    if modified and not dry_run:
        with open(path, "wb") as f:
            f.write(serialize(tree))
    return modified


def main():
    corpus = Path(__file__).resolve().parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = collections.Counter()
    files = 0
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            if process_file(os.path.join(dirpath, fn), args.dry_run, stats):
                files += 1
                print(f"  modified: {fn}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
