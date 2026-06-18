#!/usr/bin/env python3
"""remove_null_symbols.py

Remove null-morpheme symbols from the *standard* tier at S and W level.

The Kanakanavu sentence subcorpus writes a null-morpheme placeholder
inside words (e.g. ``cinimʉ'ʉraku niarisinatʉ∅kee.``), and the Sakizaya
grammar writes a null prefix slot (``ø-sitangah``). This is linguist's
annotation, not pronounceable orthography, so it is kept in the
``original`` tier but removed from the ``standard`` tier.

Scope and safety:
- Only ``FORM`` elements with ``kindOf="standard"`` that are direct
  children of S or W are touched. M-level null symbols are left alone
  deliberately: there the symbol constitutes a whole morpheme slot
  (``ø-sitangah`` -> M1 ``ø`` + M2 ``sitangah``), and stripping it
  would create exactly the empty-FORM morphemes that
  ``repair_empty_morphemes.py`` exists to eliminate.
- Boundary markers orphaned by the removal are cleaned up token-wise:
  ``ø-sitangah`` -> ``sitangah`` (not ``-sitangah``); doubled markers
  collapse. Tokens that did not contain a null symbol are untouched.
- An element is never emptied: if stripping would leave no text, the
  element is skipped and reported.
- The element's standard PHON is recomputed through the same Ortho113
  mapping ``add_phonology.py`` uses, gated by the original-tier witness
  check (see ``_phon_regen.py``). This also repairs the PHON damage the
  symbols caused: the mapping renders unknown characters as ``*``, so
  e.g. ``ø-sitangah`` had standard PHON ``*-sitaŋaħ``; it becomes
  ``sitaŋaħ``. The repair logic is driven from the *original* tier, so
  re-running the script also heals elements whose FORM was cleaned by an
  earlier version that did not regenerate PHON.
- A file is rewritten only if its unmodified tree first re-serializes
  byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python remove_null_symbols.py            # corpus XML/ by default
    python remove_null_symbols.py --dry-run
"""

import argparse
import collections
import os
import re
import sys
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _phon_regen import language_of, load_mappings, regen_standard_phon  # noqa: E402

DEFAULT_CHARS = "∅øØ"


def strip_symbols(text, chars):
    """Remove null symbols token-wise, cleaning up orphaned boundary markers."""
    out = []
    for tok in text.split(" "):
        if any(c in tok for c in chars):
            for c in chars:
                tok = tok.replace(c, "")
            tok = re.sub(r"-{2,}", "-", tok)
            tok = re.sub(r"={2,}", "=", tok)
            tok = tok.strip("-=")
        out.append(tok)
    return " ".join(out)


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, chars, dry_run, stats):
    original_bytes = open(path, "rb").read()
    if not any(c.encode("utf-8") in original_bytes for c in chars):
        return False
    tree = etree.parse(path)
    if serialize(tree) != original_bytes:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    mp = load_mappings(language_of(root))
    modified = False
    for level in ("S", "W"):
        for el in root.iter(level):
            # Drive from the original tier so elements cleaned by earlier
            # runs (FORM done, PHON stale) are still healed.
            orig = next((c.text for c in el.findall("FORM")
                         if c.get("kindOf") == "original"), None)
            if not orig or not any(c in orig for c in chars):
                continue
            std_el = next((c for c in el.findall("FORM")
                           if c.get("kindOf") == "standard"), None)
            if std_el is None or not (std_el.text or "").strip():
                continue
            desired = strip_symbols(std_el.text, chars)
            if not desired.strip():
                stats["skipped (would empty element)"] += 1
                print(f"  NOT emptied: {level} id={el.get('id')!r} "
                      f"text={std_el.text!r}")
                continue
            if std_el.text != desired:
                std_el.text = desired
                stats[f"FORM cleaned ({level})"] += 1
                modified = True
            if regen_standard_phon(el, mp, stats):
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
    ap.add_argument("--chars", default=DEFAULT_CHARS,
                    help=f"Null symbols to remove (default: {DEFAULT_CHARS}).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    stats = collections.Counter()
    files = 0
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            if process_file(os.path.join(dirpath, fn), list(args.chars),
                            args.dry_run, stats):
                files += 1
                print(f"  modified: {fn}")
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
