import math
from collections import Counter
from QC.utilities.dialect_detector_pkg.features import orthography_score

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
