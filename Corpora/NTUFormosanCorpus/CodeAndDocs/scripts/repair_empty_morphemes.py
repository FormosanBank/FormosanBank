#!/usr/bin/env python3
"""repair_empty_morphemes.py

Repair empty-form <M> shells produced upstream by the parsers.

Background
----------
When a word's surface form and its gloss split into a different number of
segments, ``parse_sentences.py`` / ``parse_grammar.py`` align them with
``itertools.zip_longest(..., fillvalue='')`` and emit one <M> per slot.
Where the gloss has more segments than the form, the extra slots become
<M> elements with an empty FORM (and PHON) but a non-empty gloss -- a
gloss with no corresponding wordform morpheme. The mirror case (a form
morpheme whose gloss slot is empty) also occurs.

This script repairs the subset of those words where the misalignment is
purely a slot-ordering artifact: for a word where every gloss tier has
exactly as many non-empty glosses as the word has form-bearing <M>s, the
glosses are reassigned to the form-bearing <M>s in document order and the
empty-form shells are deleted. No gloss text is ever re-derived or
invented -- existing <M>-level gloss text is only relocated -- so FORM,
PHON, and gloss content are all preserved exactly (only empty shells go
away).

Safety
------
* A word is repaired only if (a) it has >=1 empty-form <M>, (b) each
  present gloss tier (zho/eng) has a non-empty-gloss count equal to the
  number of form-bearing <M>s, and (c) for words containing infix
  notation (``<...>``) the bracketed forms align with bracketed glosses
  after reassignment. Words failing any of these are left untouched for
  manual / source review (see empty_M_repair_partition.csv).
* Each file is re-serialized only if its *unmodified* tree round-trips
  byte-identically through this script's serializer (which matches the
  corpus's minidom output, including ``&quot;`` escaping of text quotes).
  A file that does not round-trip is skipped, never rewritten.
* The script is idempotent: re-running it makes no further changes.

Usage
-----
    python repair_empty_morphemes.py            # defaults to ../../XML
    python repair_empty_morphemes.py --xml_dir <dir>
    python repair_empty_morphemes.py --dry-run  # report only, write nothing
"""

import argparse
import collections
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"
_SENTINEL = chr(0xE000)  # private-use char to protect text quotes during serialization
_INFIX_RE = re.compile(r"<[^>]+>")


# --- helpers ---------------------------------------------------------------

def _empty(text):
    return not (text or "").strip()


def _form_original(elem):
    for c in elem.findall("FORM"):
        if c.get("kindOf") == "original":
            return c.text
    return None


def _has_bracket(text):
    return bool(_INFIX_RE.search(text or ""))


def _ordered_tiers(w):
    """Map gloss-language -> list of non-empty <M>-level glosses, in document order."""
    tiers = collections.defaultdict(list)
    for m in w.findall("M"):
        for t in m.findall("TRANSL"):
            if not _empty(t.text):
                tiers[t.get(_XLANG) or t.get("lang")].append(t.text)
    return tiers


def _is_guarded(w):
    """Return True if W is safe to auto-repair."""
    ms = w.findall("M")
    if not ms or not any(_empty(_form_original(m)) for m in ms):
        return False
    form_ms = [m for m in ms if not _empty(_form_original(m))]
    if not form_ms:
        return False
    tiers = _ordered_tiers(w)
    if not tiers or any(len(g) != len(form_ms) for g in tiers.values()):
        return False
    if "<" in (_form_original(w) or ""):
        # infix safety: bracketed form must pair with bracketed gloss
        for glosses in tiers.values():
            for m, g in zip(form_ms, glosses):
                if _has_bracket(_form_original(m)) != _has_bracket(g):
                    return False
    return True


def _repair_w(w):
    """Reassign existing glosses to form-bearing <M>s and drop empty-form shells."""
    ms = w.findall("M")
    form_ms = [m for m in ms if not _empty(_form_original(m))]
    for lang, glosses in _ordered_tiers(w).items():
        for i, m in enumerate(form_ms):
            tel = next((t for t in m.findall("TRANSL")
                        if (t.get(_XLANG) or t.get("lang")) == lang), None)
            if tel is None:
                tel = ET.SubElement(m, "TRANSL")
                tel.set(_XLANG, lang)
            tel.text = glosses[i]
    removed = 0
    for m in list(ms):
        if _empty(_form_original(m)):
            w.remove(m)
            removed += 1
    return removed


# --- serialization (byte-faithful to the corpus's minidom output) ----------

def _strip_ws(e):
    if e.text and not e.text.strip():
        e.text = None
    if e.tail and not e.tail.strip():
        e.tail = None
    for c in e:
        _strip_ws(c)


def _protect_quotes(e):
    if e.text and '"' in e.text:
        e.text = e.text.replace('"', _SENTINEL)
    if e.tail and '"' in e.tail:
        e.tail = e.tail.replace('"', _SENTINEL)
    for c in e:
        _protect_quotes(c)


def _serialize(root):
    _strip_ws(root)
    _protect_quotes(root)
    out = minidom.parseString(ET.tostring(root, "utf-8")).toprettyxml(indent="    ")
    if out.endswith("\n"):
        out = out[:-1]
    return out.replace(_SENTINEL, "&quot;")


# --- driver ----------------------------------------------------------------

def repair_corpus(xml_dir, dry_run=False):
    files_modified = w_repaired = m_removed = skipped = 0
    for dirpath, _, filenames in os.walk(xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            path = os.path.join(dirpath, fn)
            original = open(path, encoding="utf-8").read()
            # round-trip guard: never rewrite a file we can't reproduce byte-for-byte
            if _serialize(ET.parse(path).getroot()) != original:
                print(f"  SKIP (does not round-trip): {path}")
                skipped += 1
                continue
            root = ET.parse(path).getroot()
            nw = nrm = 0
            for w in root.iter("W"):
                if _is_guarded(w):
                    nrm += _repair_w(w)
                    nw += 1
            if nw:
                files_modified += 1
                w_repaired += nw
                m_removed += nrm
                if not dry_run:
                    open(path, "w", encoding="utf-8").write(_serialize(root))
    verb = "would repair" if dry_run else "repaired"
    print(f"\nfiles {'to modify' if dry_run else 'modified'}: {files_modified}")
    print(f"W's {verb}: {w_repaired}")
    print(f"empty-form M's {'to remove' if dry_run else 'removed'}: {m_removed}")
    if skipped:
        print(f"files skipped (round-trip guard): {skipped}")
    return files_modified, w_repaired, m_removed


def main():
    default_xml = os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "XML"))
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=default_xml,
                    help="Directory of XML files to repair (default: the corpus XML/).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing.")
    args = ap.parse_args()
    repair_corpus(args.xml_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
