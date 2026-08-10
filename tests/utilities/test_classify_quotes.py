"""Tests for the temporary quote/glottal classifier.

The classifier decides, for each single-quote ' in a sentence, whether it is a
glottal stop, a quotation mark, or ambiguous. See QC/utilities/classify_quotes.py
and the verbatim spec that accompanies it.
"""

import importlib.util
from pathlib import Path

# Load the module by path so the test does not depend on package layout.
_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "QC" / "utilities" / "classify_quotes.py"
)
_spec = importlib.util.spec_from_file_location("classify_quotes", _MODULE_PATH)
classify_quotes = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(classify_quotes)

classify = classify_quotes.classify

DICT = {"faloco'", "loma'", "'ayam", "ma'orip", "romi'ad", "cima"}


def _labels(form_text, dictionary=DICT):
    """Return just the ordered list of outcome labels for the ' occurrences."""
    return [label for (_idx, label) in classify(form_text, dictionary)]


# --- Required tests from the spec -------------------------------------------


def test_1_internal_glottal():
    result = classify("romi'ad", DICT)
    assert len(result) == 1
    assert result[0][1] == "GLOTTAL_INTERNAL"


def test_2_bound_final_no_match():
    result = classify("faloco' no tao", DICT)
    assert len(result) == 1
    assert result[0][1] == "GLOTTAL_BOUND_NO_MATCH"


def test_3_bound_initial_no_match():
    result = classify("o 'ayam iso", DICT)
    assert len(result) == 1
    assert result[0][1] == "GLOTTAL_BOUND_NO_MATCH"


def test_4_quotation_pair():
    # opener 'cima (not attested, follows ':'), closer tayni' (not attested)
    assert _labels("pasowal: 'cima tayni'") == ["QUOTATION", "QUOTATION"]


def test_5_glottal_pair():
    # opener 'ayam (attested, not after punct), closer faloco' (attested, not before punct)
    assert _labels("o 'ayam ko faloco' iso") == ["GLOTTAL_PAIR", "GLOTTAL_PAIR"]


def test_6_pair_before_punct_ambiguous():
    # closer faloco' precedes ',' -> both-attested-no-punct rule fails -> AMBIGUOUS
    assert _labels("'ayam faloco',") == ["AMBIGUOUS", "AMBIGUOUS"]


def test_7_floating_stranded_glottal():
    result = classify("faloco ' no tao", DICT)
    assert len(result) == 1
    assert result[0][1] == "STRANDED_GLOTTAL"


def test_8_floating_stranded_ambiguous_zero_attested():
    result = classify("xyz ' abc", DICT)
    assert len(result) == 1
    assert result[0][1] == "AMBIGUOUS"


def test_9_floating_double_glottal_ambiguous():
    # floating ' after faloco'; cand_prev faloco'' ruled out; cand_next 'no not attested
    result = classify("faloco' ' no", DICT)
    # two ' occurrences: the bound word-final one on faloco', and the floating one.
    labels = [lab for (_i, lab) in result]
    # The floating one resolves to AMBIGUOUS (0 remaining attested).
    assert "AMBIGUOUS" in labels
    # The bound faloco' ' -- word-final ' with no opener -> GLOTTAL_BOUND_NO_MATCH
    # (the floating ' is not a valid bound opener).
    assert labels[0] == "GLOTTAL_BOUND_NO_MATCH"
    assert labels[1] == "AMBIGUOUS"


def test_10_floating_opener_quotation():
    # floating ' follows ':' -> opener, matches later word-final tayni'
    # opener_candidate 'cima (not attested), closer_candidate tayni' (not attested),
    # opener follows punct -> QUOTATION for floating ' and the bound tayni'
    assert _labels("pasowal: ' cima tayni'") == ["QUOTATION", "QUOTATION"]


# --- Additional coverage tests ----------------------------------------------


def test_internal_plus_quotation_same_sentence():
    # romi'ad has an internal glottal; the 'cima ... tayni' pair is a quotation.
    result = classify("romi'ad pasowal: 'cima tayni'", DICT)
    labels = [lab for (_i, lab) in result]
    assert labels == ["GLOTTAL_INTERNAL", "QUOTATION", "QUOTATION"]


def test_floating_two_attested_ambiguous():
    # Local dict where BOTH xyz' and 'abc are attested -> 2 attested -> AMBIGUOUS.
    local = {"xyz'", "'abc"}
    result = classify("xyz ' abc", local)
    assert len(result) == 1
    assert result[0][1] == "AMBIGUOUS"


def test_floating_prev_only_attested_stranded():
    # Only xyz' attested -> STRANDED_GLOTTAL attaching to xyz.
    local = {"xyz'"}
    result = classify("xyz ' abc", local)
    assert result[0][1] == "STRANDED_GLOTTAL"


def test_bound_pair_glottal():
    # word-initial 'ayam (attested) ... word-final loma' (attested), no punct -> GLOTTAL
    assert _labels("o 'ayam a loma' iso") == ["GLOTTAL_PAIR", "GLOTTAL_PAIR"]


# --- TRANSL first-pass tests (temporary) ---
from QC.utilities.classify_quotes import translation_confirms_glottal as tcg


def test_transl_no_transl_returns_false():
    assert tcg("o faloco'", []) is False           # no info


def test_transl_no_quotes_all_glottal():
    assert tcg("o faloco' 'ayam", ["the heart bird"]) is True


def test_transl_quotes_match_form_dquotes_glottal():
    # FORM quotation carried by " (2 of them); the ' in faloco' is a glottal.
    form = 'cika "faloco\'" saan'   # -> cika "faloco'" saan  (2 ", 1 ')
    assert tcg(form, ['he said "heart"']) is True


def test_transl_quotes_mismatch_not_resolved():
    # TRANSL has a quotation but FORM has no " -> single-quote may be a quote.
    assert tcg("'faloco' saan", ['he said "heart"']) is False
