from __future__ import annotations

import math
from collections import Counter


def orthography_score(
    grapheme_counts: Counter[str],
    candidate_inventory: frozenset[str],
    support_count: dict[str, int],
    n_candidates: int,
) -> tuple[float, int, int]:
    """Average per-informative-grapheme orthography fit for one candidate.

    Returns (score, support_tokens, penalty_tokens). Graphemes attested in no
    candidate (support 0) are neutral. Rarer graphemes weigh more.
    """
    total = 0.0
    support = 0
    penalty = 0
    informative = 0
    for g, c in grapheme_counts.items():
        s = support_count.get(g, 0)
        if s <= 0:
            continue
        informative += c
        weight = 1.0 + math.log(n_candidates / s)  # s in [1, n]; s=n -> 1.0
        if g in candidate_inventory:
            total += weight * c
            support += c
        else:
            total -= weight * c
            penalty += c
    if informative == 0:
        return 0.0, 0, 0
    return total / informative, support, penalty
