#!/usr/bin/env python3
"""Well-formedness gate for the published XML, with no external dependency.

This check used to shell out to `xmllint`, which is not part of the documented
environment -- the build promises only a FormosanBank checkout and its Python --
so on a machine without libxml2-utils it reported "command not found" (exit 127)
rather than a verdict, while the run still claimed every command exited zero.
`lxml` ships with that Python.

Redundant with validate_xml.py's schema check in the success case, and
deliberately kept: it is the cheap first gate, and its failure message points at
the byte offset rather than at a schema rule.
"""

from __future__ import annotations

import sys
from pathlib import Path

from lxml import etree

XML_DIR = Path(__file__).resolve().parents[1] / "XML" / "Seediq"


def main() -> int:
    paths = sorted(XML_DIR.glob("*.xml"))
    if not paths:
        print(f"No XML under {XML_DIR}", file=sys.stderr)
        return 2
    failed = 0
    for path in paths:
        try:
            etree.parse(str(path))
        except etree.XMLSyntaxError as error:
            print(f"NOT well-formed: {path.name}: {error}", file=sys.stderr)
            failed = 1
        else:
            print(f"well-formed: {path.name}")
    return failed


if __name__ == "__main__":
    sys.exit(main())
