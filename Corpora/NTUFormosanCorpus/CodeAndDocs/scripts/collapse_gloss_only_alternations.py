#!/usr/bin/env python3
"""collapse_gloss_only_alternations.py

Collapse a word whose slash alternation exists only in the lexical gloss,
not in the uttered sentence.

Background
----------
For a few words the source's running sentence (the JSON ``ori`` field, and
hence the XML S-level FORM) uses a single form, while the word's lexical
gloss row records an alternative separated by ``/``. Example
(Rukai ``20200531-FW-Yongfu-2_S_9``)::

    S FORM : kay Tanebake wa-lrumay si papacay-nga ki Kui.   (uses 'si')
    W FORM : si/la        gloss and/then / 和/然後

Here the speaker said ``si``; ``la`` is merely a noted alternative. Unlike
``expand_*`` (steps 16, 18), these must NOT be expanded into separate
sentences -- the alternative utterance was never made. Slashes are
forbidden in W/M FORMs (validate_text V121), so this step collapses the
word to the alternative that actually appears in the sentence and records
the dropped alternative(s) in a ``notes`` attribute on the word's original
FORM.

Scope (a word is collapsed only if ALL hold)
--------------------------------------------
1. Exactly one word in the sentence has ``/`` in its FORM, it has
   ``<M>`` segmentation, and it contains no parenthesis (slash+paren
   mixes are left for manual review).
2. Every morpheme tier/gloss splits into 1 (shared) or the same N>=2.
3. The free (S-level) translation contains no ``/``.
4. Exactly one alternative index, when its surface (dashes/clitics
   removed) is reconstructed, matches a whitespace token of the S-level
   FORM -- that is the uttered form. (0 or >1 matches => ambiguous,
   left for manual review.)

The uttered alternative is kept across all tiers; the dropped
alternative word-form(s) and their glosses are written to a ``notes``
attribute. The sentence-level FORM/PHON are already collapsed and are
left untouched. PHON needs no orthography mapping.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python collapse_gloss_only_alternations.py            # corpus XML/ by default
    python collapse_gloss_only_alternations.py --dry-run
"""

import argparse
import collections
import os
import re
from pathlib import Path

import lxml.etree as etree

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"


def _lang(t):
    return t.get(_XLANG) or t.get("lang")


def _ftext(el, kind):
    f = next((f for f in el.findall("FORM") if f.get("kindOf") == kind), None)
    return f.text if f is not None else None


def _capture(el):
    d = {}
    for f in el.findall("FORM"):
        d[("FORM", f.get("kindOf"))] = f.text
    for p in el.findall("PHON"):
        d[("PHON", p.get("kindOf"))] = p.text
    for t in el.findall("TRANSL"):
        d[("TRANSL", _lang(t))] = t.text
    return d


def _piece(text, i, N):
    parts = text.split("/")
    return parts[i] if len(parts) == N else parts[0]


def _group_replace(text, caps, key, i, N):
    for cap in caps:
        g = cap.get(key)
        if g:
            text = text.replace(g, _piece(g, i, N), 1)
    return text


def analyze(s):
    ws = s.findall("W")
    slash = [(i, w) for i, w in enumerate(ws) if "/" in (_ftext(w, "original") or "")]
    if len(slash) != 1:
        return None
    w_index, w = slash[0]
    wf = _ftext(w, "original") or ""
    if "(" in wf or ")" in wf:
        return None
    ms = w.findall("M")
    if not ms:
        return None
    if any("/" in (t.text or "") for t in s.findall("TRANSL")):
        return None
    caps = [_capture(m) for m in ms]
    counts = set()
    for cap in caps:
        for v in cap.values():
            if v is not None:
                counts.add(len(v.split("/")))
    counts.discard(1)
    if len(counts) != 1:
        return None
    N = counts.pop()
    if N < 2:
        return None
    sform = _ftext(s, "original") or ""
    toks = {t.strip(".,!?;:。，！？") for t in sform.split()}
    uttered = []
    for idx in range(N):
        surf = re.sub(r"[-=]", "", _group_replace(wf, caps, ("FORM", "original"), idx, N))
        if surf in toks:
            uttered.append(idx)
    if len(uttered) != 1:
        return None
    return w_index, w, caps, N, uttered[0]


def _dropped_note(w, caps, N, kept):
    parts = []
    for idx in range(N):
        if idx == kept:
            continue
        form = _group_replace(_ftext(w, "original") or "", caps,
                              ("FORM", "original"), idx, N)
        eng = _group_replace(
            next((t.text for t in w.findall("TRANSL") if _lang(t) == "eng"), "") or "",
            caps, ("TRANSL", "eng"), idx, N)
        zho = _group_replace(
            next((t.text for t in w.findall("TRANSL") if _lang(t) == "zho"), "") or "",
            caps, ("TRANSL", "zho"), idx, N)
        glosses = " / ".join(g for g in (eng, zho) if g)
        parts.append(f"{form} ({glosses})" if glosses else form)
    return ("source lexical gloss also lists alternative form(s) not used in "
            "this sentence: " + "; ".join(parts))


def collapse(s, w_index, w, caps, N, kept):
    for m, cap in zip(w.findall("M"), caps):
        for child in m:
            if child.tag in ("FORM", "PHON"):
                key = (child.tag, child.get("kindOf"))
            elif child.tag == "TRANSL":
                key = ("TRANSL", _lang(child))
            else:
                continue
            if cap.get(key) is not None:
                child.text = _piece(cap[key], kept, N)
    note = _dropped_note(w, caps, N, kept)
    for child in w:
        if child.tag in ("FORM", "PHON"):
            key = (child.tag, child.get("kindOf"))
        elif child.tag == "TRANSL":
            key = ("TRANSL", _lang(child))
        else:
            continue
        if child.text:
            child.text = _group_replace(child.text, caps, key, kept, N)
    fo = next((f for f in w.findall("FORM") if f.get("kindOf") == "original"), None)
    if fo is not None:
        fo.set("notes", note)


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _slash_in_forms(elem):
    return any(c.tag in ("FORM", "PHON") and c.text and "/" in c.text
               for c in elem.iter())


def process_file(path, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    modified = False
    for s in tree.getroot().iter("S"):
        info = analyze(s)
        if not info:
            continue
        w_index, w, caps, N, kept = info
        collapse(s, w_index, w, caps, N, kept)
        if _slash_in_forms(w):
            raise AssertionError(f"residual slash after collapse in {s.get('id')} ({path})")
        stats["words collapsed"] += 1
        stats[f"alternatives dropped (N-1={N - 1})"] += N - 1
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
