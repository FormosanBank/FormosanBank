#!/usr/bin/env python3
"""Withdraw word tiers the sentence does not support; rebuild morphemes that
cannot be reconciled with their glosses -- as a final pass.

This runs at the very end, after every repair: a sentence judged before
``resolve_residual_optional_parens`` or ``propagate_clitic_boundaries`` would be
judged on data those repairs fix.

Word tier (maintainer ruling 2026-09-08, decision log "Step 20")
    A sentence whose word tier does not account for its sentence form
    (``clitic_alignment``) loses its W elements.

Morpheme tier (maintainer ruling 2026-09-09, re-affirmed 2026-09-28)
    "if we cannot reconcile the segmentation to the glosses, we regenerate the
    Ms from the W's segmentation and do not include glosses in the Ms."
    Judged per word. A word's morphemes are unreconcilable when it is segmented
    but has a different number of form-bearing Ms from the pieces its form
    implies, when an M has no form (a shell left by a gloss with more pieces
    than the form), or when only some of its Ms are glossed. Such a word gets
    one M per piece of its own FORM, with no glosses: the segmentation is real
    data, but no confirmed morphosyntactic glossing exists for it. A segmented
    word with no Ms at all gets the same. A form of one piece gets no M --
    "A lack of Ms indicates no clear segmentation" -- and nothing else is
    touched: a glossed one-morpheme word keeps its own single M.

    No morpheme is ever copied from another word. (Until 2026-09-28 this step
    replaced every word's Ms in a flagged sentence with the glossed Ms of the
    first occurrence of the same form anywhere in the subcorpus, in any
    language. That was never ruled; see the decision log.)

The policy this implements is "the M tier is evidence, never manufactured":
POL-057 on the unmerged ``policy/m-tier-is-evidence`` branch (numbered POL-054
before 2026-09-10; POL-054 on main is now the waivers policy).

    python apply_prune_and_mirror.py --xml_dir <dir> [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parent))
# The gloss/word test helpers live in qa/, their single home.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qa"))
from sentence_xml_tests import (substantive as _substantive,  # noqa: E402
                                clitic_alignment, form_text,
                                morpheme_count, MARKERS)


def segment_from_form(form: str) -> list:
    """The morpheme forms a W FORM's own markers imply.

    Mirrors morpheme_count exactly -- each <X> infix is its own morpheme,
    written '-X-' (V067 forbids angle brackets in an M FORM), and what remains
    after removing the infixes splits on '-' and '='. So 'h<m>uwa' -> ['-m-',
    'huwa'], 'ka-kaun-un' -> ['ka', 'kaun', 'un'], 'kai=ta' -> ['kai', '=ta'].
    """
    stripped = (form or "").strip()
    if not stripped:
        return []
    infixes = re.findall(r"<[^>]+>", stripped)
    rest = re.sub(r"<[^>]+>", "", stripped)
    # Same filter morpheme_count uses: a punctuation-only piece is not a
    # morpheme, so it never becomes an M (which would fail V017/test 14).
    # A piece after '=' is a clitic and keeps its '=' ('rakiyas-an=mu' ->
    # 'rakiyas', 'an', '=mu'): the corpus writes clitic Ms that way, and V066
    # (HARD) requires a W's '=' to reach one of its Ms.
    parts = re.split(r"([-=])", rest)
    pieces, sep = [], ""
    for part in parts:
        if part in ("-", "="):
            sep = part
            continue
        if part and _substantive(part):
            pieces.append(("=" if sep == "=" else "") + part)
        sep = ""
    return [f"-{i.strip('<>')}-" for i in infixes] + pieces


def _glossed(m) -> bool:
    return any((t.text or "").strip() for t in m.findall("TRANSL"))


def unreconcilable(w) -> str | None:
    """Why this word's morphemes cannot stand, or None if they can."""
    w_form = form_text(w)
    ms = w.findall("M")
    if not ms:
        return "segmented word with no M" if MARKERS.search(w_form) else None
    formed = [m for m in ms if form_text(m).strip()]
    if len(formed) != len(ms):
        return "an M with no form"
    if MARKERS.search(w_form) and len(formed) != morpheme_count(w_form):
        return "M count differs from the form's segmentation"
    unglossed = [m for m in formed if not _glossed(m)]
    # A PARTIAL gap is the misalignment; uniformly unglossed Ms are
    # segmentation published without morpheme glosses, and stand.
    if unglossed and len(unglossed) != len(formed):
        return "only some Ms are glossed"
    return None


def regenerate_morphemes(w, stats: Counter) -> None:
    """Rebuild a word's M tier from its own segmentation, without glosses."""
    for m in w.findall("M"):
        w.remove(m)
    forms = segment_from_form(form_text(w))
    if len(forms) < 2:
        # One piece is not a segmentation; asserting "monomorphemic" here would
        # be the manufactured claim the M-tier policy forbids.
        stats["  words left with no M (one piece: no clear segmentation)"] += 1
        return
    for i, piece in enumerate(forms):
        m = etree.SubElement(w, "M")
        m.set("id", f"{w.get('id')}M{i}")
        f = etree.SubElement(m, "FORM")
        f.set("kindOf", "original")
        f.text = piece
    stats["  words whose Ms were rebuilt from their own segmentation, unglossed"] += 1


def prune(sentence, stats: Counter) -> bool:
    words = sentence.findall("W")
    if not words:
        return False
    if not clitic_alignment(form_text(sentence), [form_text(w) for w in words]):
        for w in words:
            sentence.remove(w)
        stats["sentences whose W tier was withdrawn"] += 1
        stats["  W elements deleted"] += len(words)
        return True
    changed = False
    for w in words:
        why = unreconcilable(w)
        if why:
            stats[f"  reason: {why}"] += 1
            stats["  glossed M elements removed"] += sum(1 for m in w.findall("M") if _glossed(m))
            regenerate_morphemes(w, stats)
            changed = True
    if changed:
        stats["sentences with at least one word's Ms rebuilt"] += 1
    return changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", choices=("prune",), default="prune",
                    help="kept for compatibility; mirroring was removed (ruling 2026-09-09)")
    args = ap.parse_args()

    stats, files = Counter(), 0
    for path in sorted(args.xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        changed = False
        for s in tree.getroot().iter("S"):
            if prune(s, stats):
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
