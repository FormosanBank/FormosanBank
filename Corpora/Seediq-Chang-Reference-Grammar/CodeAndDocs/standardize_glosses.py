#!/usr/bin/env python3
"""Standardized W/M glosses for the Chang Seediq grammar. NOT YET PART OF THE BUILD.

    python CodeAndDocs/standardize_glosses.py XML/Seediq/*.xml           # report only
    python CodeAndDocs/standardize_glosses.py XML/Seediq/*.xml --write   # add them

Gloss standardization is additive (POL-036): the source's own gloss stays in
`TRANSL[@kindOf="original"]`, and a standardized form is added beside it as
`TRANSL[@kindOf="standard"]`. Nothing here rewrites an original gloss.

One rule so far, ruled by the maintainer 2026-10-14 for `turima` 洗(AF):

  A category label the source prints in parentheses after a stem marks a
  category the word carries without showing it as a separate piece. In
  Leipzig style that is a dot, not a hyphen: 洗(AF) and 洗（AF） become 洗.AF;
  未來式（AF）-吃 becomes 未來式.AF-吃. Only all-capital labels are touched, so
  a parenthesized Chinese word such as （屬格） or （杯） is left alone.

Not wired into generate_xml.sh: glosses are to be standardized as a whole,
later, and this is its starting point. One known obstacle when it is: V085
(`multi_same_lang_transl_requires_ver`) groups TRANSL by language alone, so an
original and a standard gloss in the same language need a `ver` until the
`fix/v085-transl-kindof` FormosanBank branch merges.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lxml import etree

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
# A stem followed directly by an all-capital label in parentheses, either width.
PAREN_LABEL = re.compile(r"(?<=[^\s(（])[(（]([A-Z][A-Z0-9]*)[)）]")


def standardize(gloss: str) -> str:
    """The standardized form of one gloss (unchanged if no rule applies)."""
    return PAREN_LABEL.sub(lambda m: "." + m.group(1), gloss)


def process(path: Path, write: bool) -> list[tuple[str, str, str]]:
    # lxml keeps the file's own layout, so --write adds lines and changes no others.
    tree = etree.parse(str(path), etree.XMLParser(remove_blank_text=False))
    changes = []
    for node in tree.getroot().iter("W", "M"):
        # A W/M gloss with no kindOf is the source's own (this corpus omits it).
        originals = [t for t in node.findall("TRANSL")
                     if t.get("kindOf") in (None, "original") and t.get(XML_LANG) == "zho"
                     and t.get("ver") is None]
        if len(originals) != 1 or node.find("TRANSL[@kindOf='standard']") is not None:
            continue
        before = originals[0].text or ""
        after = standardize(before)
        if after == before:
            continue
        changes.append((node.get("id", ""), before, after))
        if write:
            original = originals[0]
            standard = etree.Element("TRANSL", {XML_LANG: "zho", "kindOf": "standard"})
            standard.text = after
            # The new line takes the original's place in the layout: if the
            # original was the last child, its tail is the closing indent.
            previous = original.getprevious()
            sibling_indent = previous.tail if previous is not None else node.text
            standard.tail = original.tail
            original.tail = sibling_indent
            original.addnext(standard)
    if write and changes:
        text = path.read_text(encoding="utf-8")
        declaration = text.split("\n", 1)[0]
        ending = "\n" if text.endswith("\n") else ""
        body = etree.tostring(tree.getroot(), encoding="unicode")
        path.write_text(declaration + "\n" + body + ending, encoding="utf-8")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("xml", nargs="+", type=Path)
    parser.add_argument("--write", action="store_true",
                        help="add the standard glosses (default: report only)")
    args = parser.parse_args()
    total = 0
    for path in args.xml:
        changes = process(path, args.write)
        total += len(changes)
        for node_id, before, after in changes:
            print(f"{path.name}\t{node_id}\t{before}\t{after}")
    verb = "added" if args.write else "would add"
    print(f"{verb} {total} standard glosses", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
