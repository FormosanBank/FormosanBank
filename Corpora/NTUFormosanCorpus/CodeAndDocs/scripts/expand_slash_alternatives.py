#!/usr/bin/env python3
"""expand_slash_alternatives.py

Expand a sentence whose word offers slash-separated *alternative* forms
into one sentence per alternative, with no slash left anywhere.

Background
----------
In elicitation the NTU source sometimes records several acceptable forms
of a word separated by ``/`` -- in the word/morpheme FORM and in the
matching (also slash-separated) gloss -- while the free translation lists
no alternatives. The slash scope is the *morpheme*: in

    W FORM : pua/mua/mu-lebe         (M1 = pua/mua/mu, M2 = lebe)
    gloss  : 放/去/去-下 / put/go/go-down
    TRANSL : 貓咪被丟樓梯下             (no slash)

only M1 alternates (3 ways); M2 (``lebe``) is shared. The three readings
are therefore ``pua-lebe`` / ``mua-lebe`` / ``mu-lebe`` -- NOT the naive
string split ``pua`` / ``mua`` / ``mu-lebe``. Slashes are forbidden in
W/M FORMs (validate_text V121 HARD).

Scope (a sentence is expanded only if ALL hold)
-----------------------------------------------
1. Exactly one word in the sentence has ``/`` in its FORM, and it has
   morpheme (<M>) segmentation.
2. For every morpheme, each FORM/PHON tier and each gloss splits into
   either 1 piece (shared) or the same N>=2 pieces (alternation) -- a
   single consistent N across the word.
3. The word-level FORM split on ``/`` yields exactly N pieces. This
   rejects word-level alternation that the parser mis-segmented at the
   morpheme tier (where the per-morpheme count disagrees with N), which
   cannot be expanded mechanically and is left for manual review.
4. Every morpheme's FORM/PHON group string occurs verbatim in the
   word-level and sentence-level FORM/PHON (so each alternative can be
   reconstructed by replacing the group in place, preserving the word's
   own ``-``/``=`` separators).
5. The free (S-level) translation contains no ``/``.

Output
------
The original element becomes alternative 1; alternatives 2..N are copies
inserted immediately after it, with id suffix ``-alt2`` .. ``-altN``
(descendant ids rewritten to match, as in dedupe_sentence_ids.py). In
each reading every morpheme takes its alternative's piece (or the shared
piece), and the word- and sentence-level FORM/PHON/gloss are rebuilt by
replacing each morpheme group with that piece -- so no slash remains.
PHON needs no orthography mapping: choosing an alternative changes no
letter within a piece. AUDIO (if any) stays on alternative 1 and is
removed from the rest (a recording captures one uttered form); no clean
slash sentence currently carries audio.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python expand_slash_alternatives.py            # corpus XML/ by default
    python expand_slash_alternatives.py --dry-run
"""

import argparse
import collections
import copy
import os
from pathlib import Path

import lxml.etree as etree

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _ftext(el, kind):
    f = next((f for f in el.findall("FORM") if f.get("kindOf") == kind), None)
    return f.text if f is not None else None


def _lang(t):
    return t.get(_XLANG) or t.get("lang")


# capture keys: ("FORM","original"), ("PHON","standard"), ("TRANSL","eng"), ...
def _capture(el):
    d = {}
    for f in el.findall("FORM"):
        d[("FORM", f.get("kindOf"))] = f.text
    for p in el.findall("PHON"):
        d[("PHON", p.get("kindOf"))] = p.text
    for t in el.findall("TRANSL"):
        d[("TRANSL", _lang(t))] = t.text
    return d


def analyze(s):
    """Return (w_index, captured_ms, N) if s is a clean slash-alternation, else None."""
    ws = s.findall("W")
    slash_ws = [(i, w) for i, w in enumerate(ws) if "/" in (_ftext(w, "original") or "")]
    if len(slash_ws) != 1:
        return None
    w_index, w = slash_ws[0]
    ms = w.findall("M")
    if not ms:
        return None
    if any("/" in (t.text or "") for t in s.findall("TRANSL")):
        return None
    captured_ms = [_capture(m) for m in ms]
    counts = set()
    for cap in captured_ms:
        for v in cap.values():
            if v is not None:
                counts.add(len(v.split("/")))
    counts.discard(1)
    if len(counts) != 1:
        return None
    N = counts.pop()
    if N < 2:
        return None
    if len((_ftext(w, "original") or "").split("/")) != N:
        return None  # word-level alternation mis-segmented at the morpheme tier
    wcap = _capture(w)
    scap = _capture(s)
    for tag, kind in (("FORM", "original"), ("FORM", "standard"),
                      ("PHON", "original"), ("PHON", "standard")):
        wtext, stext = wcap.get((tag, kind)), scap.get((tag, kind))
        for cap in captured_ms:
            g = cap.get((tag, kind))
            if g and "/" in g:
                if wtext is None or g not in wtext or stext is None or g not in stext:
                    return None
    return w_index, captured_ms, N


def _piece(text, i, N):
    parts = text.split("/")
    return parts[i] if len(parts) == N else parts[0]


def _group_replace(text, captured_ms, key, i, N):
    """Replace each morpheme's group string (for `key`) with its alt-i piece."""
    for cap in captured_ms:
        g = cap.get(key)
        if g:
            text = text.replace(g, _piece(g, i, N), 1)
    return text


def _apply(elem, w_index, captured_ms, N, i):
    """Rewrite elem (a sentence) to alternative i in place."""
    w = elem.findall("W")[w_index]
    # morpheme tier: each child takes its piece
    for m, cap in zip(w.findall("M"), captured_ms):
        for child in m:
            if child.tag in ("FORM", "PHON"):
                key = (child.tag, child.get("kindOf"))
            elif child.tag == "TRANSL":
                key = ("TRANSL", _lang(child))
            else:
                continue
            if cap.get(key) is not None:
                child.text = _piece(cap[key], i, N)
    # word tier: rebuild by replacing morpheme groups in place
    for child in w:
        if child.tag in ("FORM", "PHON"):
            key = (child.tag, child.get("kindOf"))
        elif child.tag == "TRANSL":
            key = ("TRANSL", _lang(child))
        else:
            continue
        if child.text:
            child.text = _group_replace(child.text, captured_ms, key, i, N)
    # sentence tier: only FORM/PHON carry the surface form
    for child in elem:
        if child.tag in ("FORM", "PHON") and child.text:
            key = (child.tag, child.get("kindOf"))
            child.text = _group_replace(child.text, captured_ms, key, i, N)


def _retarget_ids(elem, old, new):
    for el in elem.iter():
        cid = el.get("id")
        if cid and cid.startswith(old):
            el.set("id", new + cid[len(old):])


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _slash_in_forms(elem):
    for el in elem.iter():
        if el.tag in ("FORM", "PHON") and el.text and "/" in el.text:
            return True
    return False


def process_file(path, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    modified = False
    for s in list(root.iter("S")):
        info = analyze(s)
        if not info:
            continue
        w_index, captured_ms, N = info
        sid = s.get("id")
        parent = s.getparent()
        # alternatives 2..N: copies of the pristine sentence, then transformed
        clones = []
        for i in range(1, N):
            clone = copy.deepcopy(s)
            for au in clone.findall(".//AUDIO"):
                au.getparent().remove(au)
            _apply(clone, w_index, captured_ms, N, i)
            _retarget_ids(clone, sid, f"{sid}-alt{i + 1}")
            clones.append(clone)
        _apply(s, w_index, captured_ms, N, 0)  # original becomes alternative 1
        for off, clone in enumerate(clones, start=1):
            parent.insert(parent.index(s) + off, clone)
        if _slash_in_forms(s) or any(_slash_in_forms(c) for c in clones):
            raise AssertionError(f"residual slash after expand in {sid} ({path})")
        stats["sentences expanded"] += 1
        stats[f"readings produced (N={N})"] += N
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
