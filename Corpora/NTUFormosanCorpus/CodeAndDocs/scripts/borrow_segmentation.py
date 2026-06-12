#!/usr/bin/env python3
"""borrow_segmentation.py

Recover morpheme segmentation for under-segmented words by borrowing it
from a duplicate instance elsewhere in the source data.

Background
----------
Many of the empty-form <M> shells left after ``repair_empty_morphemes.py``
exist because the source gloss table writes a wordform unsegmented
(e.g. ``matineng``) while glossing it as several morphemes
(``主事焦點-知道``). The segmentation needed to fix this is not guessable
mechanically -- but in many cases the *same corpus* contains the same
word, properly segmented (``ma-tineng``), in another sentence. This
script finds those duplicates in the source JSONs
(``CodeAndDocs/{grammar,sentence,story}``) and applies the borrowed
segmentation: the word-level FORM gains its boundary markers, each
morpheme slot gets its form piece (with PHON regenerated through the
same Ortho113 mapping used by ``add_phonology.py``), and the empty
shells are eliminated by becoming real morphemes.

A note on ``==``: the NTU transcriptions use ``==``/``===`` as a
prosodic-lengthening marker, which the parsers strip. In a handful of
words the stripped run also contained a real boundary (e.g.
``izaw===tu`` = ``izaw==`` + clitic ``=tu``), fusing two morphemes.
Where a cleanly segmented duplicate exists, this script recovers those
too; candidate spellings containing ``==`` are never used as the
borrowed form.

Safety guards (a word is repaired only if ALL hold)
---------------------------------------------------
1. The word has >=1 empty-form <M>.
2. Exactly one piece-sequence is found among same-language source
   duplicates whose piece count equals the word's <M> count (candidates
   containing ``<`` infix notation are ignored; spellings containing
   ``==`` may corroborate the pieces but are never used as the spelling).
3. Letter fidelity: the borrowed form with boundary markers removed is
   byte-identical to the current word FORM (only boundaries are added,
   letters never change).
4. Every gloss tier present on the word's <M>s has exactly as many
   non-empty glosses as there are pieces (gloss positions unambiguous;
   gloss text is never moved between tiers or invented).
5. PHON reproducibility: converting the *current* word FORM through the
   Ortho113 mapping reproduces the word's *current* PHON exactly (both
   kindOf tiers). This proves the mapping is the one that generated this
   file's PHON, so regenerated per-morpheme PHONs are style-consistent.
   Words failing this are skipped, not guessed.
6. File round-trip: a file is rewritten only if its unmodified tree
   first re-serializes byte-identically (lxml, xml_declaration, UTF-8 --
   the corpus convention after the id-normalization pass). Files in any
   other serialization style are skipped, never rewritten.

The script is idempotent: re-running it makes no further changes.

Usage
-----
    python borrow_segmentation.py            # corpus defaults relative to script
    python borrow_segmentation.py --dry-run  # report only, write nothing
"""

import argparse
import collections
import csv
import json
import os
import re
import sys
from pathlib import Path

import lxml.etree as etree

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.utilities.add_phonology import apply_phonology_mappings  # noqa: E402
from QC.validation._dialect_inventory import is_multi_dialect_language  # noqa: E402

_XLANG = "{http://www.w3.org/XML/1998/namespace}lang"

_LANG_MAP = {
    'ami': 'Amis', 'tay': 'Atayal', 'bnn': 'Bunun', 'ckv': 'Kavalan',
    'pwn': 'Paiwan', 'pyu': 'Puyuma', 'dru': 'Rukai', 'sxr': 'Saaroa',
    'xsy': 'Saisiyat', 'szy': 'Sakizaya', 'trv': 'Seediq', 'ssf': 'Thao',
    'tsu': 'Tsou', 'tao': 'Yami', 'xnb': 'Kanakanavu',
}


def _empty(text):
    return not (text or "").strip()


def _get_tier(elem, tag, kind):
    for c in elem.findall(tag):
        if c.get("kindOf") == kind:
            return c
    return None


def _pieces(form):
    """Boundary-split pieces of a source form ('-', '=', and '==' runs)."""
    return [p for p in re.split(r"[-=]+", form) if p.strip()]


def _letters(form):
    """Form with all boundary markers removed (letter-fidelity key)."""
    return re.sub(r"[-=]+", "", form)


# --- source index -----------------------------------------------------------

def build_source_index(codedocs_dir):
    """Map (language, letters) -> Counter of segmented source spellings."""
    index = collections.defaultdict(collections.Counter)
    for sub in ("grammar", "sentence", "story"):
        root = os.path.join(codedocs_dir, sub)
        if not os.path.isdir(root):
            continue
        for lang_dir in os.listdir(root):
            full = os.path.join(root, lang_dir)
            if not os.path.isdir(full):
                continue
            language = lang_dir.split("_")[0]
            for fn in os.listdir(full):
                if not fn.endswith(".json"):
                    continue
                try:
                    data = json.load(open(os.path.join(full, fn)))
                except Exception:
                    continue
                for item in data.get("glosses", []):
                    for trip in item[1].get("gloss", []):
                        if not (isinstance(trip, list) and trip and trip[0]):
                            continue
                        form = trip[0]
                        if "<" in form or not re.search(r"[-=]", form):
                            continue
                        index[(language, _letters(form))][form] += 1
    return index


def borrowed_spelling(index, language, letters, n_pieces):
    """Return the unique borrowed segmented spelling, or None."""
    cands = index.get((language, letters))
    if not cands:
        return None
    valid = {f: n for f, n in cands.items() if len(_pieces(f)) == n_pieces}
    if not valid:
        return None
    piece_seqs = {tuple(_pieces(f)) for f in valid}
    if len(piece_seqs) != 1:
        return None
    clean = {f: n for f, n in valid.items() if "==" not in f}
    if not clean:
        return None
    return max(clean, key=lambda f: clean[f])


# --- phonology --------------------------------------------------------------

def load_mappings(language):
    tsv = _REPO_ROOT / "Orthographies" / "Ortho113" / f"{language}.tsv"
    if not tsv.exists():
        return None
    with open(tsv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    cols = [c for c in (rows[0].keys() if rows else []) if c != "letter"]
    if not cols:
        return None
    column = cols[0] if not is_multi_dialect_language(language) else (
        "default" if "default" in cols else cols[0])
    mappings = [(r["letter"], r[column]) for r in rows
                if r.get("letter") and r.get(column) is not None]
    return mappings, dict(mappings)


def convert(text, mp):
    mappings, cdict = mp
    return apply_phonology_mappings(text, mappings, cdict)


# --- serialization ----------------------------------------------------------

def serialize(tree):
    """Corpus convention: lxml with xml declaration, UTF-8, no reformat."""
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


# --- repair -----------------------------------------------------------------

def gloss_tier_counts(w):
    counts = collections.Counter()
    for m in w.findall("M"):
        for t in m.findall("TRANSL"):
            if not _empty(t.text):
                counts[t.get(_XLANG) or t.get("lang")] += 1
    return counts


def try_repair_w(w, language, index, mp, stats):
    ms = w.findall("M")
    if not ms:
        return False
    empty_ms = [m for m in ms
                if (lambda fe: fe is None or _empty(fe.text))(_get_tier(m, "FORM", "original"))]
    if not empty_ms:
        return False
    wform_el = _get_tier(w, "FORM", "original")
    if wform_el is None or _empty(wform_el.text):
        return False
    wform = wform_el.text
    if "<" in wform:
        stats["skip: infix form"] += 1
        return False
    borrowed = borrowed_spelling(index, language, _letters(wform), len(ms))
    if not borrowed:
        stats["skip: no unique duplicate"] += 1
        return False
    if _letters(borrowed) != _letters(wform):
        stats["skip: letter mismatch"] += 1
        return False
    pieces = _pieces(borrowed)
    counts = gloss_tier_counts(w)
    if not counts or any(n != len(pieces) for n in counts.values()):
        stats["skip: gloss count mismatch"] += 1
        return False
    if mp is None:
        stats["skip: no orthography TSV"] += 1
        return False
    # all M's must carry their four tiers (parser always emits them)
    for m in ms:
        for tag in ("FORM", "PHON"):
            for kind in ("original", "standard"):
                if _get_tier(m, tag, kind) is None:
                    stats["skip: M missing FORM/PHON tier"] += 1
                    return False
    # PHON reproducibility guard on the *current* word form
    w_tiers = {}
    for kind in ("original", "standard"):
        fe = _get_tier(w, "FORM", kind)
        pe = _get_tier(w, "PHON", kind)
        if fe is None or pe is None or _empty(fe.text) or _empty(pe.text):
            stats["skip: missing W FORM/PHON tier"] += 1
            return False
        if convert(fe.text, mp) != pe.text:
            stats["skip: PHON not reproducible"] += 1
            return False
        w_tiers[kind] = (fe, pe)
    # apply: W-level FORM/PHON get the segmented spelling
    for kind, (fe, pe) in w_tiers.items():
        fe.text = borrowed
        pe.text = convert(borrowed, mp)
    # M-level: assign pieces in document order
    for m, piece in zip(ms, pieces):
        for kind in ("original", "standard"):
            mfe = _get_tier(m, "FORM", kind)
            mpe = _get_tier(m, "PHON", kind)
            if mfe is not None:
                mfe.text = piece
            if mpe is not None:
                mpe.text = convert(piece, mp)
    return True


def main():
    here = Path(__file__).resolve()
    corpus = here.parents[2]
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", default=str(corpus / "XML"))
    ap.add_argument("--source_dir", default=str(corpus / "CodeAndDocs"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    index = build_source_index(args.source_dir)
    stats = collections.Counter()
    files_mod = w_rep = 0
    mp_cache = {}
    for dirpath, _, filenames in os.walk(args.xml_dir):
        for fn in sorted(filenames):
            if not fn.endswith(".xml"):
                continue
            path = os.path.join(dirpath, fn)
            original = open(path, "rb").read()
            tree = etree.parse(path)
            if serialize(tree) != original:
                stats["file skipped: round-trip guard"] += 1
                continue
            root = tree.getroot()
            text_el = root if root.tag == "TEXT" else root.find(".//TEXT")
            if text_el is None:
                continue
            code = (text_el.get(_XLANG) or text_el.get("xml:lang") or "").strip()
            language = _LANG_MAP.get(code, code)
            if language not in mp_cache:
                mp_cache[language] = load_mappings(language)
            n = 0
            for w in root.iter("W"):
                if try_repair_w(w, language, index, mp_cache[language], stats):
                    n += 1
            if n:
                files_mod += 1
                w_rep += n
                if not args.dry_run:
                    with open(path, "wb") as f:
                        f.write(serialize(tree))
    verb = "would be " if args.dry_run else ""
    print(f"\nfiles {verb}modified: {files_mod}")
    print(f"W's {verb}repaired (segmentation borrowed): {w_rep}")
    print("skip reasons among empty-M words:")
    for k, v in stats.most_common():
        print(f"  {v:5d}  {k}")


if __name__ == "__main__":
    main()
