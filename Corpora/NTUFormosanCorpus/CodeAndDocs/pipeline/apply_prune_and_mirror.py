#!/usr/bin/env python3
"""Withdraw unsupported analyses, then mirror morphemes -- as a final pass.

These were pipeline steps 12 and 13. They belong at the very end, after every
repair has run: a sentence pruned before `resolve_residual_optional_parens` or
`propagate_clitic_boundaries` is judged on data those repairs would have fixed,
and any sentence they *add* afterwards escapes the prune entirely.

Withdrawal (was step 12)
    A sentence whose word tier does not account for its sentence form loses its
    W elements; one that passes that but whose morphemes fail -- a morpheme
    implied by the word form has no M, an M carries no gloss, or an M carries no
    form -- loses its M elements. The word tier stands in the second case.

Mirroring (was step 13)
    Within a sentence that still carries morphological parsing -- some words
    analysed, some not -- an unanalysed word gets one M mirroring its FORM and
    glosses. A sentence with no M at all gets none: it is either unanalysed in
    the source or had its morpheme tier withdrawn just now, and a flat mirror
    must not stand in for an analysis found unsupportable.

    python apply_prune_and_mirror.py --xml_dir <dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import copy
import re
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
# The gloss/word test helpers live in qa/, their single home.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qa"))
from borrow_missing_morphemes import bare, collect_donors  # noqa: E402
from sentence_xml_tests import (substantive as _substantive,  # noqa: E402
                                clitic_alignment, form_text,
                                morpheme_count, MARKERS)

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"



def segment_from_form(form: str) -> list:
    """The morpheme forms a W FORM's own markers imply.

    Mirrors morpheme_count exactly -- each <X> infix is its own morpheme,
    written '-X-' (V067 forbids angle brackets in an M FORM), and what remains
    after removing the infixes splits on '-' and '='. So 'h<m>uwa' -> ['-m-',
    'huwa'] and 'ka-kaun-un' -> ['ka', 'kaun', 'un'].
    """
    stripped = (form or "").strip()
    if not stripped:
        return []
    infixes = re.findall(r"<[^>]+>", stripped)
    rest = re.sub(r"<[^>]+>", "", stripped)
    # Same filter morpheme_count uses: a punctuation-only piece is not a
    # morpheme, so it never becomes an M (which would fail V017/test 14).
    pieces = [p for p in re.split(r"[-=]", rest) if p and _substantive(p)]
    return [f"-{i.strip('<>')}-" for i in infixes] + pieces


def regenerate_morphemes(w, stats: Counter, donors: dict | None = None) -> None:
    """Rebuild a word's M tier from its own segmentation, without glosses.

    POL-054: when the morphemes cannot be reconciled with the glosses, the
    segmentation is still known -- it is written in the W FORM -- but the
    morpheme-level glossing is not trustworthy. Withdrawing the tier would
    throw away the segmentation too; inventing glosses would assert an
    analysis nobody made. So the Ms are regenerated from the form and left
    unglossed, which is exactly what "no confirmed morphosyntactic glossing"
    looks like.
    """
    # A corpus-attested, fully glossed analysis of this very word form IS a
    # reconciliation -- better than falling back to an unglossed rebuild, which
    # would throw away glosses the corpus already has. Only if no such donor
    # exists do we regenerate from the form alone.
    if donors:
        cands = donors.get(form_text(w))
        if cands and len(cands) == 1:
            key, template = next(iter(cands.items()))
            if bare("".join(key)) == bare(form_text(w)):
                for m in w.findall("M"):
                    w.remove(m)
                for j, m in enumerate(template):
                    clone = copy.deepcopy(m)
                    clone.set("id", f"{w.get('id')}M{j}")
                    w.append(clone)
                stats["  words reconciled from a glossed donor"] += 1
                return
    for m in w.findall("M"):
        w.remove(m)
    forms = segment_from_form(form_text(w))
    if len(forms) < 2:
        # One morpheme is not a segmentation; asserting "monomorphemic" here
        # would be the same manufactured claim POL-054 forbids.
        stats["  words left with no M (no segmentation to record)"] += 1
        return
    for i, piece in enumerate(forms):
        m = etree.SubElement(w, "M")
        m.set("id", f"{w.get('id')}M{i}")
        f = etree.SubElement(m, "FORM")
        f.set("kindOf", "original")
        f.text = piece
    stats["  words whose M tier was regenerated unglossed"] += 1


def prune(sentence, stats: Counter, donors: dict | None = None) -> bool:
    words = sentence.findall("W")
    if not words:
        return False
    s_form = form_text(sentence)
    forms = [form_text(w) for w in words]

    if not clitic_alignment(s_form, forms):
        for w in words:
            sentence.remove(w)
        stats["sentences whose W tier was withdrawn"] += 1
        stats["  W elements deleted"] += len(words)
        return True

    bad = False
    for w, w_form in zip(words, forms):
        ms = w.findall("M")
        formed = [m for m in ms if form_text(m).strip()]
        if MARKERS.search(w_form) and len(formed) != morpheme_count(w_form):
            bad = True
        formed_ms = [m for m in ms if form_text(m).strip()]
        unglossed = [m for m in formed_ms
                     if not any((t.text or "").strip() for t in m.findall("TRANSL"))]
        for m in ms:
            if not form_text(m).strip():
                bad = True
                # Only a PARTIAL gap counts. A word whose morphemes are
                # uniformly unglossed is segmentation published without
                # morpheme glosses -- YeddaPalemeqBlog does this for 3,906
                # glossed words -- and withdrawing it would delete valid
                # analysis. A gap in an otherwise glossed word is the
                # misalignment this rule is for.
        if unglossed and len(unglossed) != len(formed_ms):
            bad = True
    if bad:
        n = 0
        for w in words:
            n += len(w.findall("M"))
            regenerate_morphemes(w, stats, donors)
        stats["sentences whose M tier was regenerated from the form"] += 1
        stats["  glossed M elements replaced"] += n
        return True
    return False


def mirror(sentence, stats: Counter) -> bool:
    """Give a KNOWN monomorphemic word its single M.

    POL-054 forbids manufacturing an analysis, not recording one. A word with a
    form, a gloss and no segmentation markers HAS been analysed: as one
    morpheme, carrying that gloss. Writing the M states what the source says.
    Withholding it would lose the distinction POL-054 exists to protect, in the
    other direction -- "analysed as monomorphemic" would become
    indistinguishable from "not analysed".

    So the M is written only where the word is glossed. An UNGLOSSED word gets
    nothing: there the M really would be invented (4 such words in the published
    Sentences, against 15,699 properly glossed ones).
    """
    words = sentence.findall("W")
    changed = False
    for w in words:
        if w.findall("M"):
            continue
        w_form = form_text(w)
        if not w_form.strip():
            continue
        if MARKERS.search(w_form):
            # Segmented but M-less: the segmentation is known and the morphemes
            # are not. Regeneration handles that; a single mirror would assert
            # the word is monomorphemic, which its own form denies.
            stats["  left alone (segmented, so not monomorphemic)"] += 1
            continue
        if not any((t.text or "").strip() for t in w.findall("TRANSL")):
            stats["  left alone (unglossed: no analysis to record)"] += 1
            continue
        m = etree.SubElement(w, "M")
        m.set("id", f"{w.get('id')}M0")
        f = etree.SubElement(m, "FORM")
        f.set("kindOf", "original")
        f.text = w_form
        for t in w.findall("TRANSL"):
            nt = etree.SubElement(m, "TRANSL")
            nt.set(XML_LANG, t.get(XML_LANG))
            nt.text = t.text
        stats["mirror morphemes added"] += 1
        changed = True
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=("prune", "mirror", "both"),
                    default="both",
                    help="run one phase, so a borrow pass can sit between them")
    args = ap.parse_args()

    stats, files = Counter(), 0
    paths = sorted(args.xml_dir.rglob("*.xml"))
    # Collected before anything is rewritten, so the donors are the analyses the
    # corpus had going in -- not ones this pass just regenerated.
    donors = collect_donors(paths) if args.only in ("prune", "both") else {}
    for path in paths:
        tree = etree.parse(str(path))
        changed = False
        for s in tree.getroot().iter("S"):
            if args.only in ("prune", "both") and prune(s, stats, donors):
                changed = True
            if args.only in ("mirror", "both") and mirror(s, stats):
                changed = True
        if changed and not args.dry_run:
            tree.write(str(path), xml_declaration=True, encoding="UTF-8")
            files += 1
    print(f"files modified: {files}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
