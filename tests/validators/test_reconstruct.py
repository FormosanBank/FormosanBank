"""Tests for QC/validation/rules/_reconstruct.py.

Shared helpers for the tier-reconstruction rules V068 (M->W) and V141
(W->S): a letter-only character multiset and an overlap-similarity ratio.
Multiset comparison is order-independent, so infixes/circumfixes (which
only reorder characters) score a perfect match; the similarity ratio +
threshold is what tolerates reduplication placeholders and null morphemes
while still catching gross misalignment.
"""
from collections import Counter

from QC.validation.rules._reconstruct import letter_skeleton, similarity


# --- letter_skeleton ---------------------------------------------------------

def test_letter_skeleton_keeps_only_letters():
    # digits, whitespace, ASCII punctuation all dropped
    assert letter_skeleton("ab1 c!?") == Counter({"a": 1, "b": 1, "c": 1})


def test_letter_skeleton_drops_segmentation_markers():
    # '-', '=', '<', '>' are not letters -> dropped, so "ka-en" and "kaen"
    # produce the same skeleton.
    assert letter_skeleton("ka-en") == letter_skeleton("kaen")
    assert letter_skeleton("s<um>ulat") == letter_skeleton("sumulat")


def test_letter_skeleton_is_casefolded():
    assert letter_skeleton("AbC") == letter_skeleton("abc") == Counter(
        {"a": 1, "b": 1, "c": 1}
    )


def test_letter_skeleton_counts_multiplicity():
    assert letter_skeleton("aaab") == Counter({"a": 3, "b": 1})


def test_letter_skeleton_keeps_non_ascii_letters():
    # Non-ASCII orthographic letters (e.g. ŋ, ə) are category L -> kept.
    assert letter_skeleton("ŋaə") == Counter({"ŋ": 1, "a": 1, "ə": 1})


def test_letter_skeleton_empty_or_none():
    assert letter_skeleton("") == Counter()
    assert letter_skeleton(None) == Counter()


# --- similarity --------------------------------------------------------------

def test_similarity_identical_is_one():
    assert similarity(letter_skeleton("sumulat"), letter_skeleton("sumulat")) == 1.0


def test_similarity_infix_concatenation_is_one():
    # W "sumulat" vs Ms "s" + "-um-" + "ulat": multiset is identical despite
    # the infix being inserted rather than appended.
    w = letter_skeleton("sumulat")
    m = letter_skeleton("s") + letter_skeleton("-um-") + letter_skeleton("ulat")
    assert similarity(w, m) == 1.0


def test_similarity_disjoint_is_zero():
    assert similarity(letter_skeleton("abc"), letter_skeleton("xyz")) == 0.0


def test_similarity_partial_overlap_ratio():
    # overlap 3 ("abc"), larger side has 4 chars -> 0.75
    assert similarity(letter_skeleton("abc"), letter_skeleton("abcd")) == 0.75


def test_similarity_both_empty_is_one():
    # Nothing to disprove -> treat as a match (callers skip these anyway).
    assert similarity(Counter(), Counter()) == 1.0


def test_similarity_one_empty_is_zero():
    assert similarity(letter_skeleton("abc"), Counter()) == 0.0
