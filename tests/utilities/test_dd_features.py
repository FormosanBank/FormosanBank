import math
from collections import Counter
from QC.utilities.dialect_detector_pkg.features import orthography_score, log_prob_score, extract_counts
from QC.utilities.dialect_detector_pkg.graphemes import UNK

def test_orthography_prefers_dialect_with_exclusive_letter():
    # 2 candidates; 'v' only in Alpha (support 1), 'a' in both (support 2)
    support = {"v": 1, "a": 2}
    counts = Counter({"v": 2, "a": 2})
    alpha_inv = frozenset({"v", "a"})
    beta_inv = frozenset({"a"})
    s_alpha, sup_a, pen_a = orthography_score(counts, alpha_inv, support, n_candidates=2)
    s_beta, sup_b, pen_b = orthography_score(counts, beta_inv, support, n_candidates=2)
    assert s_alpha > s_beta
    assert pen_a == 0 and pen_b == 2   # Beta penalized for the two 'v'

def test_out_of_language_letters_are_neutral():
    support = {"a": 2}
    counts = Counter({"zzz": 5})       # not in support map -> support 0 -> ignored
    s, sup, pen = orthography_score(counts, frozenset({"a"}), support, n_candidates=2)
    assert (s, sup, pen) == (0.0, 0, 0)

def test_log_prob_prefers_matching_profile():
    obs = Counter({"a": 3})
    near = log_prob_score(obs, Counter({"a": 30, "b": 1}), 31, vocab_size=2)
    far = log_prob_score(obs, Counter({"a": 1, "b": 30}), 31, vocab_size=2)
    assert near > far
    assert log_prob_score(Counter(), Counter({"a": 1}), 1, 1) == 0.0

def test_extract_counts_unigram_bigram_word():
    graphemes = ["a", "b", "a"]
    uni, bi, words = extract_counts(graphemes, "ab a")
    assert uni == Counter({"a": 2, "b": 1})
    assert bi == Counter({"a b": 1, "b a": 1})
    assert words == Counter({"ab": 1, "a": 1})

def test_extract_counts_ignores_unk_in_bigrams_boundaries():
    # UNK still counts as a unigram token but bigrams are over the sequence as-is
    uni, bi, words = extract_counts(["a", UNK, "b"], "a? b")
    assert uni[UNK] == 1
