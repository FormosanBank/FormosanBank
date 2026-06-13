#!/usr/bin/env python3
"""split_optional_parentheticals.py

Split a sentence that records an *optional* word into two paren-free
sentences: one without the optional word and one with it.

Background
----------
In elicitation, the NTU source sometimes notes that a word is optional by
wrapping it in parentheses -- in the running sentence FORM, in the
word/morpheme FORM, and in the matching gloss (also parenthesized) -- while
the free translation contains no parentheses (the optional material is a
linguist's note, not part of the uttered sentence). Example:

    S FORM : wavutha (nakuane) pangipalay.
    W1     : FORM "(nakuane)"  gloss "(1S.FO)" / "(第一人稱單數.自由斜格)"
    TRANSL : "He forced me to fly."          (no parentheses)

Parentheses are forbidden in W/M FORMs (validate_text V121 HARD). Rather
than guess whether the optional word belongs in the form, this step
materializes both readings as real sentences, with no parentheses left
anywhere in either.

Scope (a sentence is split only if ALL hold)
--------------------------------------------
1. The sentence FORM contains a parenthesis.
2. The free (S-level) translation contains no parenthesis.
3. Every parenthesis-bearing word is a *whole* parenthetical: its original
   FORM matches ``^\\([^()]*\\)$`` (so all parens are confined to such
   words; none are split across or embedded inside other words).
4. Each such word carries a gloss and every one of its TRANSLs is itself
   fully parenthesized (``^\\(.*\\)$``) -- the "matching gloss in
   parentheses" signal.

Sentences with embedded / split / unbalanced parentheses, or whose
parenthetical word lacks a parenthesized gloss, are left untouched for
manual review.

Output
------
For each matching sentence ``S_N``:
* The original element becomes the **without-optional** reading: the
  parenthetical word(s) and their morphemes are deleted, and the optional
  token is removed from the S-level FORM/PHON (both tiers) with whitespace
  and space-before-punctuation tidied. It keeps its id and any AUDIO.
* A **with-optional** reading is inserted immediately after it: a copy in
  which only the parenthesis characters are stripped (content kept) from
  every FORM/PHON/TRANSL text and ``notes`` attribute. Its id gains a
  ``-opt`` suffix (descendant ids rewritten to match, as in
  dedupe_sentence_ids.py). AUDIO is removed from this reading -- the
  recording is of the shorter, actually-uttered sentence.

PHON needs no orthography mapping: removing parentheses is purely
notational and never changes a letter.

A file is rewritten only if its unmodified tree first re-serializes
byte-identically (lxml, xml declaration, UTF-8). Idempotent: a re-run
finds no parenthesized sentences (the outputs have none).

Usage
-----
    python split_optional_parentheticals.py            # corpus XML/ by default
    python split_optional_parentheticals.py --dry-run
"""

import argparse
import collections
import copy
import os
import re
from pathlib import Path

import lxml.etree as etree

_WHOLE_PAREN = re.compile(r"^\([^()]*\)$")
_PAREN_GLOSS = re.compile(r"^\(.*\)$")


def _form(el, kind):
    return next((f for f in el.findall("FORM") if f.get("kindOf") == kind), None)


def _phon(el, kind):
    return next((p for p in el.findall("PHON") if p.get("kindOf") == kind), None)


def _form_text(el, kind):
    f = _form(el, kind)
    return f.text if f is not None else None


def _transls(el):
    return el.findall("TRANSL")


def is_match(s):
    """Return the list of whole-parenthetical W elements, or None."""
    sform = _form_text(s, "original") or ""
    if "(" not in sform and ")" not in sform:
        return None
    if any("(" in (t.text or "") or ")" in (t.text or "") for t in _transls(s)):
        return None  # parenthesis in the free translation
    ws = s.findall("W")
    paren_ws = [w for w in ws
                if "(" in (_form_text(w, "original") or "")
                or ")" in (_form_text(w, "original") or "")]
    if not paren_ws:
        return None
    whole = [w for w in paren_ws if _WHOLE_PAREN.match(_form_text(w, "original") or "")]
    if len(whole) != len(paren_ws):
        return None  # some paren is embedded / split across words
    for w in whole:
        ts = _transls(w)
        if not ts or not all(_PAREN_GLOSS.match(t.text or "") for t in ts):
            return None  # no matching parenthesized gloss
    return whole


def _tidy(text):
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\s+([,.;:!?。，！？])", r"\1", text)
    return text.strip()


_PAREN_GROUP = re.compile(r"\([^()]*\)")


def _drop_groups(text):
    """Remove whole ``(...)`` groups and tidy (for the S-level running form)."""
    return _tidy(_PAREN_GROUP.sub("", text)) if text else text


def _strip_parens(text):
    return text.replace("(", "").replace(")", "") if text else text


def make_without(s, whole):
    """Modify s in place: drop the parenthetical word(s) and their groups
    from the S-level running FORM/PHON. Only optional-word parens appear at
    the S level (gloss parens live in TRANSL), so dropping every group is
    safe and sidesteps the S-FORM(no dashes)/W-FORM(dashes) mismatch."""
    for kind in ("original", "standard"):
        f, p = _form(s, kind), _phon(s, kind)
        if f is not None:
            f.text = _drop_groups(f.text)
        if p is not None:
            p.text = _drop_groups(p.text)
    for w in whole:
        s.remove(w)


def make_with(s, sid, whole):
    """Return a copy with the optional word's parens stripped (content kept).

    Only the parenthetical-word subtrees and the S-level FORM/PHON tokens
    are touched; unrelated gloss parentheticals elsewhere in the sentence
    (e.g. an optional gloss particle ``去(了)`` on another word) are
    preserved verbatim. AUDIO is removed; the id gains a ``-opt`` suffix.
    """
    clone = copy.deepcopy(s)
    clone_ws = clone.findall("W")
    whole_idx = [s.findall("W").index(w) for w in whole]
    for au in clone.findall(".//AUDIO"):
        au.getparent().remove(au)
    # S-level FORM/PHON carry only optional-word parens -> strip them all
    for kind in ("original", "standard"):
        f, p = _form(clone, kind), _phon(clone, kind)
        if f is not None:
            f.text = _strip_parens(f.text)
        if p is not None:
            p.text = _strip_parens(p.text)
    # strip parens only within the parenthetical-word subtrees
    for i in whole_idx:
        for el in clone_ws[i].iter():
            if el.text and ("(" in el.text or ")" in el.text):
                el.text = _strip_parens(el.text)
            notes = el.get("notes")
            if notes and ("(" in notes or ")" in notes):
                el.set("notes", _strip_parens(notes))
    new = sid + "-opt"
    for el in clone.iter():
        cid = el.get("id")
        if cid and cid.startswith(sid):
            el.set("id", new + cid[len(sid):])
    return clone


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def _form_phon_paren(s):
    """True if any FORM/PHON under s still contains a parenthesis (the V121
    invariant). Parens in TRANSL/notes elsewhere are legitimate gloss
    annotation and not this step's concern."""
    for el in s.iter():
        if el.tag in ("FORM", "PHON") and el.text and (
                "(" in el.text or ")" in el.text):
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
        whole = is_match(s)
        if not whole:
            continue
        sid = s.get("id")
        had_audio = s.find(".//AUDIO") is not None
        clone = make_with(s, sid, whole)      # build longer first (from pristine S)
        make_without(s, whole)                # then collapse s to the shorter reading
        parent = s.getparent()
        parent.insert(parent.index(s) + 1, clone)
        # guard: no FORM/PHON in either reading may contain a parenthesis
        if _form_phon_paren(s) or _form_phon_paren(clone):
            raise AssertionError(f"residual FORM/PHON paren after split in {sid} ({path})")
        stats["sentences split"] += 1
        stats[f"parenthetical words removed (={len(whole)})"] += len(whole)
        if had_audio:
            stats["audio kept on shorter / dropped on longer"] += 1
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
