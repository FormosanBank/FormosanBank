"""Shared helpers for tier-reconstruction rules (V068 M->W, V141 W->S).

A "reconstruction" check asks whether a coarser tier's FORM is spelled by
its finer-tier children's FORMs — used to catch *misalignment* (the
children belong to a different parent), NOT to prove exact equality.

We compare letter-only character multisets so that:
  - infixes/circumfixes (which only reorder characters) score a perfect
    match — the infix morpheme's letters are present either way;
  - segmentation markers ('-', '=', '<', '>'), punctuation, and whitespace
    are ignored for free (none are letters);
  - small genuine differences (reduplication placeholders like ``RED``,
    null morphemes ``ø``, and the few orthographic letters dropped as
    punctuation, e.g. the apostrophe glottal stop) only nudge the
    similarity ratio down rather than producing a false mismatch.

Callers flag when ``similarity`` falls below DEFAULT_SIMILARITY_THRESHOLD.
"""
from __future__ import annotations

import unicodedata
from collections import Counter

# Default cutoff for "these don't reconstruct each other". A guess pending
# calibration against Corpora/: correct decompositions cluster near 1.0,
# genuine misalignments near 0.0, so the exact cut is not delicate.
DEFAULT_SIMILARITY_THRESHOLD = 0.6


def letter_skeleton(text: str | None) -> Counter:
    """Return a multiset (Counter) of the casefolded Unicode-letter
    characters in ``text``.

    Everything that is not a Unicode letter (category ``L*``) is dropped:
    whitespace, digits, punctuation, and the segmentation markers
    ``- = < >``. Order is not preserved (it's a multiset), which is what
    makes infix/circumfix decompositions compare equal.
    """
    skeleton: Counter = Counter()
    for ch in text or "":
        if unicodedata.category(ch).startswith("L"):
            skeleton[ch.casefold()] += 1
    return skeleton


def similarity(a: Counter, b: Counter) -> float:
    """Overlap ratio of two letter-skeletons: ``sum(min) / max(|a|, |b|)``.

    Range [0.0, 1.0]. 1.0 means one multiset's letters are fully contained
    in the other and of equal size (a perfect reconstruction). Two empty
    skeletons return 1.0 (nothing to disprove); one empty and one non-empty
    return 0.0.
    """
    len_a = sum(a.values())
    len_b = sum(b.values())
    if len_a == 0 and len_b == 0:
        return 1.0
    overlap = sum((a & b).values())  # Counter '&' = elementwise min
    return overlap / max(len_a, len_b)
