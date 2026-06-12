#!/usr/bin/env python3
"""
Remove PHON[@kindOf="original"] elements whose phonemic content is entirely
unmapped — i.e. add_phonology emitted only "*" placeholders because the source
orthography has no letter->IPA mapping for that dialect.

Concrete case: jiu_jie_jiao_cai YilanZeaol Atayal is phonologized with Ortho94
(per the README), but Ortho94/Atayal.tsv's YilanZeaol column is 100% NA, so
every grapheme becomes "*" and the original-tier PHON comes out as e.g.
"**** ****, ***** ** **?". The published corpus omits such PHON entirely rather
than storing the placeholder string.

This only touches the ORIGINAL tier. The STANDARD-tier PHON is built from the
standardized text (which IS mappable) and is correct, so it is left untouched.
Partially-unmapped PHON like "ta*aj" (a single unmapped letter inside otherwise
real IPA) is also kept — only PHON with no alphabetic character at all is dropped.

Run after add_phonology, e.g.:
    python drop_unmapped_phon.py --final_xml_dir Final_XML
"""
import argparse
from pathlib import Path
from lxml import etree


def is_unmapped(text):
    """True when PHON text is only "*" placeholders (no real phonemic content)."""
    return bool(text) and "*" in text and not any(c.isalpha() for c in text)


def process_file(path):
    tree = etree.parse(str(path))
    root = tree.getroot()
    removed = 0
    for phon in root.findall(".//PHON[@kindOf='original']"):
        if is_unmapped(phon.text):
            # Removing the element also drops its tail whitespace, so the next
            # sibling inherits the previous element's indentation cleanly (no
            # blank line, no reflow of the rest of the file).
            phon.getparent().remove(phon)
            removed += 1
    if removed:
        tree.write(str(path), xml_declaration=True, encoding="utf-8")
    return removed


def main():
    ap = argparse.ArgumentParser(
        description="Drop fully-unmapped (all-'*') original-tier PHON elements."
    )
    ap.add_argument("--final_xml_dir", default="Final_XML",
                    help="Path to the Final_XML directory (default: Final_XML)")
    args = ap.parse_args()

    base = Path(args.final_xml_dir)
    if not base.exists():
        ap.error(f"the path provided for --final_xml_dir, {base}, doesn't exist.")

    files = total = 0
    for p in sorted(base.rglob("*.xml")):
        r = process_file(p)
        if r:
            files += 1
            total += r
            print(f"  {p.relative_to(base)}: removed {r}")
    print(f"Removed {total} unmapped original PHON element(s) across {files} file(s).")


if __name__ == "__main__":
    main()
