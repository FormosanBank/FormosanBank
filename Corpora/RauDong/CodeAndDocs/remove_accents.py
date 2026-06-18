#!/usr/bin/env python3
"""Remove lexical-accent marks from the RauDong *standard* tier.

Rau & Dong (2006) mark lexical accent with an acute accent on vowels
(a/e/i/o). That marking is faithful to the source, so it is kept in the
``original`` tier; but the ``standard`` tier uses FormosanBank's common
orthography, which does not write the accent. This script strips the acute
accent from every ``<FORM kindOf="standard">`` element at the S, W, and M
levels and rewrites each file in place. The ``original`` tier, and all PHON
and TRANSL elements, are left untouched.

    python remove_accents.py                       # default: ../XML (RauDong)
    python remove_accents.py --corpora_path <dir>  # any directory of XMLs

Files are modified in place -- diff before committing.
"""
import argparse
from pathlib import Path

from lxml import etree

# Acute-accented vowels -> plain vowel. Upper-case and `u` are included
# defensively; only the lower-case a/e/i/o forms actually occur in RauDong as
# of this writing.
ACUTE = str.maketrans({
    "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
    "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
})


def process_file(path):
    """Strip acute accents from standard-tier FORMs; rewrite if changed.

    Returns the number of FORM elements modified.
    """
    tree = etree.parse(str(path))
    changed = 0
    for form in tree.iter("FORM"):
        if form.get("kindOf") == "standard" and form.text:
            stripped = form.text.translate(ACUTE)
            if stripped != form.text:
                form.text = stripped
                changed += 1
    if changed:
        # Same serialization settings clean_xml.py uses, so the only change to
        # each file is the removed accents.
        tree.write(str(path), xml_declaration=True, pretty_print=True,
                   encoding="utf-8")
    return changed


def main():
    default_xml = Path(__file__).resolve().parent.parent / "XML"
    parser = argparse.ArgumentParser(
        description="Remove acute accent marks from the standard tier.")
    parser.add_argument(
        "--corpora_path", default=str(default_xml),
        help="Directory of XML files (searched recursively). "
             "Default: %(default)s")
    args = parser.parse_args()

    root = Path(args.corpora_path)
    if not root.exists():
        parser.error(f"Path does not exist: {root}")

    files = sorted(root.rglob("*.xml"))
    print(f"Scanning {len(files)} file(s) under {root}")
    total_files = total_forms = 0
    for f in files:
        n = process_file(f)
        if n:
            total_files += 1
            total_forms += n
            print(f"  {f.name}: {n} standard FORM(s) updated")
    print(f"\nDone. Removed accents from {total_forms} standard FORM "
          f"element(s) across {total_files} of {len(files)} file(s).")


if __name__ == "__main__":
    main()
