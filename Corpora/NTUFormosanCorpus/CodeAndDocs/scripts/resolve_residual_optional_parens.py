#!/usr/bin/env python3
"""resolve_residual_optional_parens.py

Resolve the whole-word parentheticals left after
``split_optional_parentheticals.py`` (step 15).

Step 15 split only the optional words whose *gloss* was also parenthesized
(the maintainer-approved signal). This step handles the remaining
whole-word parentheticals -- where the gloss is a plain gloss, or the word
is absent from the running sentence -- by routing each on whether its
surface form actually appears in the sentence-level FORM:

* **split** -- the parenthesized surface (``(sua)``, ``(kumakʉʉn)``) is a
  token of the S FORM: the word is optional *within* the sentence. Produce
  a without-optional reading (the original) and a with-optional reading
  (id ``-opt``), exactly as step 15 (its ``make_without`` / ``make_with``
  are reused).
* **strip** -- the *bare* surface (``la``, ``kavay``) is a token of the S
  FORM: the word is already in the sentence without parentheses; just
  remove the parens from the word's FORM/PHON/gloss.
* **delete** -- the surface is absent from the S FORM: the word is an
  optional addition the speaker did not utter (e.g. Seediq ``(so)`` glossed
  ``(如此)``). Remove the word and record it in a ``notes`` attribute on the
  sentence's original FORM.

Surface matching strips infix/segmentation markers (``< > - =``) from the
word FORM first, so a word like ``(k<um>a-kʉʉn)`` is correctly matched
against the S-FORM token ``(kumakʉʉn)``.

Parenthetical material that is not a whole word (embedded ``k(a)-u``, split
asides ``bi(n``…``ma)s``, slash+paren mixes) is out of scope and left for
manual review.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent.

Usage
-----
    python resolve_residual_optional_parens.py            # corpus XML/ by default
    python resolve_residual_optional_parens.py --dry-run
"""

import argparse
import collections
import os
import re
import sys
from pathlib import Path

import lxml.etree as etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from split_optional_parentheticals import make_with, make_without  # noqa: E402

_WHOLE = re.compile(r"^\([^()]*\)$")
_MARKERS = re.compile(r"[<>\-=]")


def _ftext(el, kind):
    f = next((f for f in el.findall("FORM") if f.get("kindOf") == kind), None)
    return f.text if f is not None else None


def _surface(form):
    return _MARKERS.sub("", form)


def _route(w, toks):
    surf = _surface(_ftext(w, "original") or "")
    if surf in toks:
        return "split"
    if surf[1:-1] in toks:
        return "strip"
    return "delete"


def _strip_parens_subtree(w):
    for el in w.iter():
        if el.tag in ("FORM", "PHON", "TRANSL") and el.text and (
                "(" in el.text or ")" in el.text):
            el.text = el.text.replace("(", "").replace(")", "")
        notes = el.get("notes")
        if notes and ("(" in notes or ")" in notes):
            el.set("notes", notes.replace("(", "").replace(")", ""))


def _delete_note(w):
    bare = _surface(_ftext(w, "original") or "")[1:-1]
    glosses = " / ".join(
        (t.text or "").replace("(", "").replace(")", "")
        for t in w.findall("TRANSL") if t.text)
    return f"{bare} ({glosses})" if glosses else bare


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def process_file(path, dry_run, stats):
    original = open(path, "rb").read()
    tree = etree.parse(path)
    if serialize(tree) != original:
        stats["file skipped: round-trip guard"] += 1
        return False
    root = tree.getroot()
    modified = False
    for s in list(root.iter("S")):
        toks = [t.strip(".,!?;:。，！？") for t in (_ftext(s, "original") or "").split()]
        pw = [w for w in s.findall("W") if _WHOLE.match(_ftext(w, "original") or "")]
        if not pw:
            continue
        routes = {id(w): _route(w, toks) for w in pw}
        rset = set(routes.values())
        if len(rset) > 1:
            stats[f"SKIPPED mixed-route sentence: {s.get('id')}"] += 1
            continue
        route = rset.pop()
        if route == "split":
            sid = s.get("id")
            clone = make_with(s, sid, pw)
            make_without(s, pw)
            s.getparent().insert(s.getparent().index(s) + 1, clone)
            stats["split (with/without)"] += 1
        elif route == "strip":
            for w in pw:
                _strip_parens_subtree(w)
            stats["stripped (word already in sentence)"] += 1
        else:  # delete
            notes = "; ".join(_delete_note(w) for w in pw)
            for w in pw:
                s.remove(w)
            fo = next((f for f in s.findall("FORM") if f.get("kindOf") == "original"), None)
            if fo is not None:
                prefix = ("source lists optional word(s) not in this sentence: ")
                existing = fo.get("notes")
                fo.set("notes", f"{existing}; {prefix}{notes}" if existing else prefix + notes)
            stats["deleted (optional word absent from sentence)"] += 1
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
