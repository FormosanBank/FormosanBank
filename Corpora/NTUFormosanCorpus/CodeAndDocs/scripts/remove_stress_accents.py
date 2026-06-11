#!/usr/bin/env python3
"""remove_stress_accents.py

Remove stress-accent marks from the *standard* tier.

The Grammar subcorpus (Kanakanavu and Sakizaya) marks stress with an
acute accent in elicited examples: ``Namásia``, ``matárava``,
``mʉ́rʉpʉ``, ``Pánay``/``Panáy``. Evidence that these are stress marks
and not orthographic letters: they occur only in the Grammar files; the
same lexemes appear unaccented in the Sentences/Stories subcorpora
(``mámia``~``mamia``, ``vutúkuru``~``vutukuru``) with the same meaning;
Sakizaya proper names carry the accent on varying syllables
(``Pánay`` vs ``Panáy``); and the accent appears on all six vowels
including ``ʉ`` — for which no precomposed accented codepoint exists,
so ``ʉ́`` is stored as ``ʉ`` + U+0301 COMBINING ACUTE ACCENT.

Treatment mirrors the RauDong corpus: the accent is faithful to the
source, so it is kept in the ``original`` tier and removed from the
``standard`` tier (the project's common orthography does not write
stress).

Implementation: standard-tier FORM text is NFD-decomposed, U+0301 is
dropped, and the result is NFC-recomposed. This handles both the
precomposed vowels (``á é í ó ú``) and the necessarily-decomposed
``ʉ́`` in one operation; no other diacritics are affected. Where a FORM
changes (and for any element whose standard PHON is out of sync), the
standard PHON is recomputed through the same Ortho113 mapping
``add_phonology.py`` uses — but only for elements whose original tier
witnesses the mapping (converting the original FORM reproduces the
original PHON exactly). Note this also repairs PHON: the mapping
renders unknown characters as ``*``, so accented words currently have
broken standard PHON (``Namásia`` -> ``nam*sia``); after this step the
standard PHON is ``namasia``-style.

Pipeline position: run after ``standardize.py --copy`` and before
``add_phonology.py`` when regenerating (the PHON regeneration is a
no-op when PHON does not exist yet); on the published corpus it runs
post-hoc and updates standard PHON in place.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python remove_stress_accents.py            # corpus XML/ by default
    python remove_stress_accents.py --dry-run
"""

import argparse
import collections
import os
import sys
import unicodedata
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phon_regen import language_of, load_mappings, regen_standard_phon  # noqa: E402

_ACUTE = "́"


def deaccent(text):
    return unicodedata.normalize(
        "NFC",
        "".join(c for c in unicodedata.normalize("NFD", text) if c != _ACUTE))


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    mp = load_mappings(language_of(root))
    modified = False
    for level in ("S", "W", "M"):
        for el in root.iter(level):
            touched = False
            for child in el:
                if child.tag != "FORM" or child.get("kindOf") != "standard":
                    continue
                text = child.text or ""
                if _ACUTE not in unicodedata.normalize("NFD", text):
                    continue
                child.text = deaccent(text)
                stats[f"FORM cleaned ({level})"] += 1
                touched = True
            if touched:
                if regen_standard_phon(el, mp, stats):
                    pass
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
