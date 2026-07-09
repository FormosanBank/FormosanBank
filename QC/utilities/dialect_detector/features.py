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
) -> tuple[Counter[str], Counter[str], Counter[str], Counter[str]]:
    """Return (unigram, bigram, word, word_bigram) count bags. Bigrams are space-joined
    grapheme pairs; words are casefolded \\w+ runs of the raw text; word_bigrams are
    space-joined adjacent word pairs."""
    uni = Counter(graphemes)
    bi = Counter(
        f"{graphemes[i]} {graphemes[i + 1]}" for i in range(len(graphemes) - 1)
    )
    word_list = _WORD_RE.findall(text.casefold())
    words = Counter(word_list)
    word_bi = Counter(
        f"{word_list[i]} {word_list[i + 1]}" for i in range(len(word_list) - 1)
    )
    return uni, bi, words, word_bi

def kl_divergence(
    counts: Counter[str],
    profile_counts: Counter[str],
    profile_total: int,
    vocab_size: int,
    smoothing: float = 1.0,
) -> float:
    """Average KL divergence of `counts` from a profile."""
    n = sum(counts.values())
    if n == 0:
        return 0.0
    denom = profile_total + smoothing * max(vocab_size, 1)
    kl = 0.0
    for item, c in counts.items():
        p = (profile_counts.get(item, 0) + smoothing) / denom
        q = c / n
        kl += p * math.log(p / q)
    return kl

def overlap_coefficient(set1: frozenset[str], set2: frozenset[str]) -> float:
    """Overlap coefficient of two sets: |intersection| / min(|set1|, |set2|).
    Returns at least 1.0 to avoid division by zero when used as a divisor.
    """
    if not set1 or not set2:
        return 1.0
    intersection = len(set1 & set2)
    coeff = intersection / min(len(set1), len(set2))
    if coeff < 1e-10:
        print(f"Warning: Overlap coefficient is very small, first elements: {list(set1)[0]}, {list(set2)[0]}. Returning 1e-10 to avoid division by zero.")
    return max(coeff, 1e-10)
