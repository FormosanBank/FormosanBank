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
from QC.utilities.classify_quotes import apply_quote_corrections as aqc


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


# --- Gap 2: closing quote after terminal punctuation -> QUOTATION ---
def test_closer_after_period_pairs_as_quotation():
    # 'zzq (opener) ... wqx.' (closer follows '.') -> QUOTATION pair.
    assert _labels("'zzq wqx.'") == ["QUOTATION", "QUOTATION"]


def test_closer_after_period_space_pairs_as_quotation():
    assert _labels("'zzq wqx. '") == ["QUOTATION", "QUOTATION"]


def test_word_final_glottal_not_treated_as_closer_after_punct():
    # faloco' 's ' follows a letter, not punct -> stays a glottal pair.
    assert _labels("o 'ayam ko faloco' iso") == ["GLOTTAL_PAIR", "GLOTTAL_PAIR"]


# --- apply_quote_corrections: the high-confidence 4-rule policy -------------
# Zero false positives by design; anything not matching is assumed glottal.


def test_rule2_closing_quote_after_period_no_transl_needed():
    # one word-initial ' + one ' after a period -> Rule 2 (.' is unambiguous).
    text = "'zzq wqx.'"
    new_text, corrected, stranded, ambiguous = aqc(text, [], DICT)
    assert new_text == '"zzq wqx."'
    assert len(corrected) == 2 and stranded == [] and ambiguous == []


def test_rule1_transl_count_matches_start_end_quotes():
    text = "o 'zzq mid wqx' ko"          # 'zzq (initial) + wqx' (final)
    new_text, corrected, stranded, ambiguous = aqc(text, ['he said "x"'], DICT)
    assert new_text == 'o "zzq mid wqx" ko'
    assert len(corrected) == 2 and ambiguous == []


def test_rule1_blocked_when_a_boundary_word_is_attested():
    # 'ayam and faloco' are attested glottal words -> Rule 1 must not fire.
    text = "'ayam mid faloco'"
    new_text, corrected, stranded, ambiguous = aqc(text, ['a "bird"'], DICT)
    assert new_text == text and corrected == []
    assert len(ambiguous) == 2            # flagged for review, not edited


def test_rule3_requires_transl_corroboration():
    # word-final closer before '.' is ambiguous with a real glottal -> needs TRANSL.
    text = "x 'zzq mid wqx'."
    with_transl = aqc(text, ['said "y"'], DICT)
    assert with_transl[0] == 'x "zzq mid wqx".' and len(with_transl[1]) == 2
    # no TRANSL quote -> must NOT fire (this is the Wikipedia false-positive guard)
    assert aqc(text, [], DICT) == (text, [], [], [])


def test_rule4_requires_transl_corroboration():
    text = "x: 'zzq mid wqx'"             # opener after ':', word-final closer
    with_transl = aqc(text, ['said "z"'], DICT)
    assert with_transl[0] == 'x: "zzq mid wqx"' and len(with_transl[1]) == 2
    assert aqc(text, [], DICT) == (text, [], [], [])


def test_no_false_positive_on_real_glottal_words_with_quoting_transl():
    # Genuine glottal-boundary sentence + a quoting TRANSL -> left glottal, flagged.
    text = "'ayam ako a faloco'"
    new_text, corrected, stranded, ambiguous = aqc(text, ['my "bird"'], DICT)
    assert new_text == text and corrected == [] and len(ambiguous) == 2


def test_transl_without_quotes_suppresses_conversion():
    # Rule 2 would fire, but the TRANSL has no quotation -> assume glottal.
    text = "'zzq wqx.'"
    assert aqc(text, ["he spoke plainly"], DICT) == (text, [], [], [])


def test_empty_quotation_guard_blocks_back_to_back():
    # Adjacent quote marks would make an empty "" -> nothing is converted.
    text = "a: '' b"
    new_text, corrected, stranded, ambiguous = aqc(text, ['x "y"'], DICT)
    assert new_text == text and corrected == []


def test_destrand_removes_whitespace_to_let_a_rule_fire():
    # floating ' -> remove the space so 'zzq is word-initial and Rule 2 fires.
    text = "x ' zzq wqx.'"
    new_text, corrected, stranded, ambiguous = aqc(text, [], DICT)
    assert new_text == 'x "zzq wqx."'
    assert len(corrected) == 2 and stranded == [2]


def test_apply_internal_glottal_ignored():
    text = "romi'ad ko 'ayam"
    assert aqc(text, [], DICT) == (text, [], [], [])


def test_apply_no_quote_is_noop():
    text = "o wawa no tao"
    assert aqc(text, [], DICT) == (text, [], [], [])
