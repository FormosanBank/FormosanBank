#!/usr/bin/env python3
"""normalize_serialization.py --style minidom|lxml <xml_dir>

Rewrite every .xml under <xml_dir> in one of the corpus's two
serialization conventions, so the repair scripts' byte-identical
round-trip guards pass at each pipeline stage:

- ``minidom``: the parsers' style (minidom toprettyxml, 4-space indent,
  ``&quot;``-escaped quotes) — expected by repair_empty_morphemes.py
  (step 4). Reuses that script's own serializer so the two can never
  drift apart.
- ``lxml``: the published corpus's style (lxml, XML declaration, UTF-8)
  — expected by remove_stress_accents.py and steps 5-20.

Content-preserving: only the declaration, indentation and escaping
conventions change. Used by make.sh between pipeline stages; harmless
(idempotent) when the files are already in the requested style.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--style", choices=("minidom", "lxml"), required=True)
    ap.add_argument("xml_dir")
    args = ap.parse_args()

    if args.style == "minidom":
        import repair_empty_morphemes as rem

        def rewrite(path):
            root = rem.ET.parse(path).getroot()
            with open(path, "w", encoding="utf-8") as f:
                f.write(rem._serialize(root))
    else:
        import lxml.etree as etree

        def rewrite(path):
            tree = etree.parse(path)
            with open(path, "wb") as f:
                f.write(etree.tostring(tree, xml_declaration=True,
                                       encoding="UTF-8"))

    n = 0
    for dirpath, _, files in os.walk(args.xml_dir):
        for fn in sorted(files):
            if fn.endswith(".xml"):
                rewrite(os.path.join(dirpath, fn))
                n += 1
    print(f"normalized {n} files to {args.style} style under {args.xml_dir}")


if __name__ == "__main__":
    main()
