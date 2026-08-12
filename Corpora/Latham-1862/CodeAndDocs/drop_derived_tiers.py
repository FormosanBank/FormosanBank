#!/usr/bin/env python3
"""Delete the derived tiers (standard FORM, PHON) from Latham-1862 XML.

Adapted from ``Corpora/WakelinTexts/CodeAndDocs/drop_derived_tiers.py``,
deliberately unchanged in mechanism so the two corpora that publish an
original tier only behave identically.

Why this corpus drops its standard tier
---------------------------------------
Latham 1862 is a 19th-century comparative wordlist in Babuza-Favorlang
(``bzg``) and Siraya (``fos``). Neither variety has a settled modern
orthography that this material could be transliterated into: Siraya is
under a standing FormosanBank ruling not to standardize to Ortho113 or
anything else for now, and both varieties' ``standard_orthography``
cells in the repo-root ``standards.csv`` are blank. A ``standard`` FORM
is a claim that the text
has been transliterated into FormosanBank's common orthography. We
cannot make that claim, so the published corpus carries **only** the
``original`` tier: what Latham prints. How (or whether) to standardize
this material is an open question tracked outside the repo.

The pre-correction snapshot (POL-035) is the build's own output and it
*does* contain a standard tier — 62 S-level FORMs, a verbatim
``standardize.py --copy`` of the original (letter-for-letter identical,
Latham's diacritics included), which is exactly the kind of tier that
asserts a standardization nobody performed. The snapshot is never
edited (POL-038): it is the fixed baseline. Instead this step, run by
``make_xml.sh`` as part of the pipeline, removes the tier on the way to
``XML/``. Deleting a derived tier is exactly the kind of change that
must happen in committed code rather than by hand, because it must be
reproducible from the snapshot on every run.

PHON is handled here too even though this corpus has never had any
(README, "Extraction Decisions": a historical lexical table with no
living pronunciation reference gets no PHON tier). The guarantee this
step provides is "the published corpus asserts no orthography and no
pronunciation", and a guarantee that only holds by accident is not a
guarantee.

Usage:
    python drop_derived_tiers.py --corpora_path <dir-of-XML> [--bank <root>]
"""

import argparse
import importlib
import sys
from pathlib import Path

from lxml import etree

# <bank>/Corpora/Latham-1862/CodeAndDocs/this-file
_DEFAULT_BANK = Path(__file__).resolve().parents[3]


def _load_prettify(bank: Path):
    """Import QC/utilities/_prettify.py from a FormosanBank checkout.

    Borrowed rather than reimplemented: it is the shared, mixed-content-
    safe, idempotent indenter that standardize.py and add_phonology.py
    write through, so this corpus serializes exactly like every other.
    """
    sys.path.insert(0, str(bank))
    return importlib.import_module("QC.utilities._prettify").prettify


def _is_derived(elem) -> bool:
    """True for a derived-tier element: a standard FORM, or any PHON."""
    if elem.tag == "PHON":
        return True
    return elem.tag == "FORM" and elem.get("kindOf") == "standard"


def drop_derived(root) -> tuple[int, int]:
    """Remove every standard FORM and PHON in the tree, in place.

    Returns (standard_forms_removed, phons_removed). Indentation is
    preserved by hand: an element's tail is the whitespace that precedes
    its *next* sibling, so dropping a non-final child drops exactly the
    right amount of whitespace, while dropping the final child requires
    handing its tail (the parent's closing indent) back to the sibling
    that becomes final.
    """
    n_form = n_phon = 0
    for parent in root.iter():
        for child in list(parent):
            if not _is_derived(child):
                continue
            if child.getnext() is None:
                prev = child.getprevious()
                if prev is not None:
                    prev.tail = child.tail
                else:
                    parent.text = child.tail
            if child.tag == "PHON":
                n_phon += 1
            else:
                n_form += 1
            parent.remove(child)
    return n_form, n_phon


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpora_path", required=True,
                    help="directory containing the XML files (searched recursively)")
    ap.add_argument("--bank", default=str(_DEFAULT_BANK),
                    help="FormosanBank checkout to import QC/ helpers from "
                         "(default: the checkout this corpus lives in)")
    args = ap.parse_args()

    prettify = _load_prettify(Path(args.bank).resolve())
    root_dir = Path(args.corpora_path)
    files = sorted(root_dir.rglob("*.xml"))
    if not files:
        sys.exit(f"no XML files under {root_dir}")

    total_form = total_phon = 0
    for path in files:
        tree = etree.parse(str(path))
        root = tree.getroot()
        n_form, n_phon = drop_derived(root)
        total_form += n_form
        total_phon += n_phon
        # Same write idiom as standardize.py: prettify, then drop the
        # blank lines it can leave behind (including the trailing one).
        xml_string = prettify(root)
        xml_string = "\n".join(
            line for line in xml_string.split("\n") if line.strip() != "")
        path.write_text(xml_string, encoding="utf-8")
        print(f"{path}: removed {n_form} standard FORM, {n_phon} PHON")

    print(f"TOTAL: removed {total_form} standard FORM, {total_phon} PHON "
          f"across {len(files)} files")


if __name__ == "__main__":
    main()
