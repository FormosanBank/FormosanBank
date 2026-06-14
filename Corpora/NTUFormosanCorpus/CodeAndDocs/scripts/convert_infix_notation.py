#!/usr/bin/env python3
"""convert_infix_notation.py

Convert M-tier infix notation from ``<X>`` to the canonical ``-X-``.

Background
----------
FormosanBank reserves angle brackets for the W FORM (where ``<X>`` marks
the surface position of an infix inside its host) and for TRANSL glosses
(``<AF>``, ``<RED>``); at the M tier an infix morpheme must be written
``-X-`` (validate_glosses rule V067 HARD, with V062 as its counterpart).
The NTU parsers copy the source morpheme strings verbatim, and the
source writes M-level infixes with brackets (``<n>`` under
``m<n>nanang``), so the published corpus carried ~2,920 bracketed infix
Ms across all three subcorpora.

What converts (all conditions required)
---------------------------------------
1. The M's original FORM is exactly one bracket group ``<X>`` (no other
   characters).
2. That same ``<X>`` occurs literally inside the parent W's original
   FORM -- the brackets really are infix notation, not a word-level
   code-switch/noise marker (``<gonense>=ku``, ``<BREATH>``,
   ``<JgekiJ>``, or the echo-morpheme ``<jiuhaole>`` under a bracketless
   W FORM).
3. Removing all bracket groups from the W FORM leaves host letters
   beyond clitic chunks (``=ku``) -- an infix needs a host.

For a converting M, every direct-child FORM and PHON whose text is a
single bracket group becomes ``-X-`` (letters unchanged; PHON needs no
orthography mapping because the transformation is purely notational --
surveyed 2026-06: PHON is bracket-shaped wherever FORM is, both tiers).
W-level FORMs and all TRANSL glosses are never touched. Ms left
unconverted are reported with reasons; the residue is the handful of
word-level markers above plus bracket groups split across a morpheme
boundary by the parsers (``la<in`` / ``i>haib`` from ``la<in-i>haib-an``),
which need structural repair, not notation conversion.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python convert_infix_notation.py            # corpus XML/ by default
    python convert_infix_notation.py --dry-run
"""

import argparse
import collections
import os
import re
from pathlib import Path

import lxml.etree as etree

_PURE = re.compile(r"^<([^<>]+)>$")
_GROUP = re.compile(r"<[^<>]+>")
_LETTER = re.compile(r"[^\W\d_]", re.UNICODE)


def _original_form(elem):
    for f in elem.findall("FORM"):
        if f.get("kindOf") == "original":
            return f.text or ""
    return ""


def _is_infix_m(m, w_form):
    """Apply the three conversion conditions; return reason or None (=convert)."""
    mo = _PURE.match(_original_form(m))
    if not mo:
        return "M FORM not a single bracket group"
    if mo.group(0) not in w_form:
        return "bracket group absent from W FORM (word-level marker)"
    rest = _GROUP.sub("", w_form)
    host = re.sub(r"=[^=]*", "", rest)  # drop clitic chunks
    if not _LETTER.search(host):
        return "no host letters outside the bracket group(s)"
    return None


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, dry_run, stats, skips):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    modified = False
    for w in tree.getroot().iter("W"):
        w_form = _original_form(w)
        for m in w.findall("M"):
            if not any("<" in (c.text or "") or ">" in (c.text or "")
                       for c in m if c.tag in ("FORM", "PHON")):
                continue
            reason = _is_infix_m(m, w_form)
            if reason:
                skips.append((os.path.basename(path), m.get("id"),
                              _original_form(m), reason))
                continue
            for c in m:
                if c.tag not in ("FORM", "PHON"):
                    continue
                mo = _PURE.match(c.text or "")
                if mo:
                    c.text = f"-{mo.group(1)}-"
                    stats[f"{c.tag} converted ({c.get('kindOf')})"] += 1
                    modified = True
            stats["M converted"] += 1
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
    skips = []
    files = 0
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            if process_file(os.path.join(dirpath, fn), args.dry_run, stats, skips):
                files += 1
    print(f"\nfiles {'that would be ' if args.dry_run else ''}modified: {files}")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")
    if skips:
        print(f"\nbracketed Ms NOT converted ({len(skips)}):")
        for fn, mid, form, reason in skips:
            print(f"  {fn} {mid}: {form!r} -- {reason}")


if __name__ == "__main__":
    main()
