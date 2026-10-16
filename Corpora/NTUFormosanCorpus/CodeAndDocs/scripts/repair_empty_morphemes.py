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

The script partitions these words into three source-safe repairs and also
completes partially parsed sentences:

* When every gloss tier has exactly as many non-empty glosses as the word has
  form-bearing M elements, the glosses are reassigned in document order and
  only the empty shells are deleted.
* When a W FORM contains an infix or null marker, existing form-bearing M
  elements already preserve the structural analysis. Empty shells are deleted
  without inventing an alignment for their glosses. The source-backed W
  translations remain the fidelity anchor.
* Other unresolved alignments are collapsed to one mirror M copied from the
  W-level FORM, PHON, and TRANSL tiers. This keeps every source-backed W tier
  intact while withdrawing an unsupported fine-grained alignment.
* After those repairs, an M-less W inside a sentence that still carries
  morphological parsing receives the same one-M mirror. This implements
  POL-023 without inventing finer segmentation, including when the source
  word is represented by ``UNCLEAR``.

Safety
------
* A mirror collapse is allowed only when the W has a non-empty id and
  original FORM and neither the W nor its M tier contains angle brackets.
  Angle-bracket words retain their existing form-bearing M analysis. An
  M-less word may still receive a whole-W mirror because that copies source
  tiers without interpreting the angle notation.
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
import copy
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom

ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"
_SENTINEL = chr(0xE000)  # private-use char to protect text quotes during serialization
_MIXED_SENTINEL = chr(0xE001)
_INFIX_RE = re.compile(r"<[^>]+>")


# --- helpers ---------------------------------------------------------------

def _empty(text):
    return not (text or "").strip()


def _form_original(elem):
    for c in elem.findall("FORM"):
        if c.get("kindOf") == "original":
            text = c.text or ""
            if c.find("UNCLEAR") is not None:
                return text + "?"
            return text
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


def _has_angle_m(w):
    return any(
        "<" in (_form_original(m) or "") or ">" in (_form_original(m) or "")
        for m in w.findall("M")
    )


def _drop_empty_shells(w):
    """Drop empty-form M shells without changing form-bearing siblings."""
    removed = 0
    for m in list(w.findall("M")):
        if _empty(_form_original(m)):
            w.remove(m)
            removed += 1
    return removed


def _collapse_to_w_mirror(w):
    """Replace an unsupported granular M tier with one W-level mirror M."""
    if not w.get("id") or _empty(_form_original(w)):
        return 0
    old_ms = list(w.findall("M"))
    if not old_ms:
        return 0
    for m in old_ms:
        w.remove(m)
    _append_w_mirror(w)
    return len(old_ms)


def _append_w_mirror(w):
    """Copy a source-backed W into one coarse M without guessing a split."""
    w_id = w.get("id")
    if not w_id or _empty(_form_original(w)):
        raise RuntimeError("cannot mirror W without an id and original FORM")
    if w.findall("M"):
        raise RuntimeError(f"cannot append mirror to M-bearing W {w_id}")
    mirror = ET.Element("M", {"id": f"{w_id}M1"})
    for child in w:
        if child.tag in ("FORM", "PHON", "TRANSL"):
            mirror.append(copy.deepcopy(child))
    w.append(mirror)
    return mirror


def _sentence_carries_parsing(sentence):
    """Match the shared V144 definition of a morphologically parsed S."""
    for w in sentence.findall("W"):
        ms = w.findall("M")
        if len(ms) >= 2:
            return True
        w_form = _form_original(w) or ""
        if any((_form_original(m) or "") != w_form for m in ms):
            return True
    return False


def _add_missing_w_mirrors(sentence):
    """Add POL-023 mirrors to M-less W elements in one parsed sentence."""
    if not _sentence_carries_parsing(sentence):
        return 0
    added = 0
    for w in sentence.findall("W"):
        if w.findall("M"):
            continue
        _append_w_mirror(w)
        added += 1
    return added


# --- serialization (byte-faithful to the corpus's minidom output) ----------

def _strip_ws(e, *, preserve_inline_tail=False):
    mixed_tier = e.tag in {"FORM", "TRANSL"} and bool(len(e))
    if e.text and not e.text.strip():
        if not (mixed_tier and "\n" not in e.text and "\r" not in e.text):
            e.text = None
    if e.tail and not e.tail.strip():
        if not (
            preserve_inline_tail
            and "\n" not in e.tail
            and "\r" not in e.tail
        ):
            e.tail = None
    for c in e:
        _strip_ws(c, preserve_inline_tail=mixed_tier)


def _protect_quotes(e):
    if e.text and '"' in e.text:
        e.text = e.text.replace('"', _SENTINEL)
    if e.tail and '"' in e.tail:
        e.tail = e.tail.replace('"', _SENTINEL)
    for c in e:
        _protect_quotes(c)


def _protect_mixed_tiers(root):
    """Replace structured FORM/TRANSL contents with inline placeholders.

    ``minidom.toprettyxml`` inserts indentation into mixed-content elements
    on every pass. That whitespace becomes tier content and makes the next
    round-trip differ. Structural ``UNCLEAR`` tiers are the only nested
    FORM/TRANSL content in this corpus, so serialize their inner XML compactly
    and restore it after pretty-printing.
    """
    replacements = {}
    for index, element in enumerate(root.iter()):
        if element.tag not in {"FORM", "TRANSL"} or not len(element):
            continue
        marker = f"{_MIXED_SENTINEL}{index}{_MIXED_SENTINEL}"
        if marker in (element.text or ""):
            raise AssertionError("mixed-content serialization marker collision")
        tail = element.tail
        element.tail = None
        compact = minidom.parseString(
            ET.tostring(element, "utf-8")
        ).documentElement.toxml()
        element.tail = tail
        inner = compact.split(">", 1)[1].rsplit(f"</{element.tag}>", 1)[0]
        for child in list(element):
            element.remove(child)
        element.text = marker
        replacements[marker] = inner
    return replacements


def _serialize(root):
    root = copy.deepcopy(root)
    _strip_ws(root)
    _protect_quotes(root)
    mixed = _protect_mixed_tiers(root)
    out = minidom.parseString(ET.tostring(root, "utf-8")).toprettyxml(indent="    ")
    if out.endswith("\n"):
        out = out[:-1]
    for marker, inner in mixed.items():
        if out.count(marker) != 1:
            raise AssertionError("mixed-content serialization marker drift")
        out = out.replace(marker, inner)
    return out.replace(_SENTINEL, "&quot;")


# --- driver ----------------------------------------------------------------

def repair_corpus(xml_dir, dry_run=False):
    files_modified = guarded = structural_shells = collapsed = 0
    missing_mirrors = m_removed = skipped = 0
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
                ms = w.findall("M")
                if not ms or not any(_empty(_form_original(m)) for m in ms):
                    continue
                if _is_guarded(w):
                    nrm += _repair_w(w)
                    guarded += 1
                    nw += 1
                    continue
                w_form = _form_original(w) or ""
                if "<" in w_form or ">" in w_form or "∅" in w_form:
                    removed = _drop_empty_shells(w)
                    if removed:
                        nrm += removed
                        structural_shells += 1
                        nw += 1
                    continue
                if _has_angle_m(w):
                    raise RuntimeError(
                        f"unresolved angle residue in M tier: {path} {w.get('id')}"
                    )
                removed = _collapse_to_w_mirror(w)
                if removed:
                    nrm += removed
                    collapsed += 1
                    nw += 1
            for sentence in root.iter("S"):
                added = _add_missing_w_mirrors(sentence)
                if added:
                    missing_mirrors += added
                    nw += added
            if nw:
                files_modified += 1
                m_removed += nrm
                if not dry_run:
                    open(path, "w", encoding="utf-8").write(_serialize(root))
    verb = "would repair" if dry_run else "repaired"
    print(f"\nfiles {'to modify' if dry_run else 'modified'}: {files_modified}")
    print(f"W's {verb} by guarded reassignment: {guarded}")
    print(f"infix/null W's {verb} by empty-shell deletion: {structural_shells}")
    print(f"W's {verb} by mirror collapse: {collapsed}")
    print(f"M-less W's {verb} by POL-023 mirror addition: {missing_mirrors}")
    print(f"empty-form M's {'to remove' if dry_run else 'removed'}: {m_removed}")
    if skipped:
        print(f"files skipped (round-trip guard): {skipped}")
    return (
        files_modified,
        guarded + structural_shells + collapsed + missing_mirrors,
        m_removed,
    )


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
