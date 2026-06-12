from __future__ import annotations

import math
import re
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


_WORD_RE = re.compile(r"\w+", re.UNICODE)


def log_prob_score(
    counts: Counter[str],
    profile_counts: Counter[str],
    profile_total: int,
    vocab_size: int,
    smoothing: float = 1.0,
) -> float:
    """Average add-`smoothing`-smoothed log-prob of `counts` under a profile."""
    n = sum(counts.values())
    if n == 0:
        return 0.0
    denom = profile_total + smoothing * max(vocab_size, 1)
    score = 0.0
    for item, c in counts.items():
        p = (profile_counts.get(item, 0) + smoothing) / denom
        score += c * math.log(p)
    return score / n


def extract_counts(
    graphemes: list[str], text: str
) -> tuple[Counter[str], Counter[str], Counter[str]]:
    """Return (unigram, bigram, word) count bags. Bigrams are space-joined
    grapheme pairs; words are casefolded \\w+ runs of the raw text."""
    uni = Counter(graphemes)
    bi = Counter(
        f"{graphemes[i]} {graphemes[i + 1]}" for i in range(len(graphemes) - 1)
    )
    words = Counter(_WORD_RE.findall(text.casefold()))
    return uni, bi, words
