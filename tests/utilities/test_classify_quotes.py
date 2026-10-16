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


def test_rule1_requires_balanced_quotes():
    # lone word-final glottal + a single (spanning) TRANSL quote must NOT convert.
    text = "o toki nga', mikalic to kasoling"     # nga' is a real word-final glottal
    new_text, corrected, stranded, ambiguous = aqc(text, ['"a spanning quote opens here'], DICT)
    assert new_text == text and corrected == []


def test_rules34_require_complete_transl_pair():
    # Rule 4 shape, but the TRANSL has only ONE quote (spanning) -> must NOT fire.
    text = "x: 'zzq mid wqx'"
    new_text, corrected, _, _ = aqc(text, ['said "y just an opener'], DICT)
    assert new_text == text and corrected == []
    # two quotes (a complete pair) -> fires
    assert aqc(text, ['said "y done"'], DICT)[0] == 'x: "zzq mid wqx"'


# ---------------------------------------------------------------------------
# POL-028: quote classification reads the tier's base, not a variant
# ---------------------------------------------------------------------------

def test_sentence_records_read_the_original_base_not_a_variant(tmp_path):
    """`for form in s.findall("FORM"): ... break` took the first
    kindOf="original" in document order, which is a ver="alt" variant
    whenever one is written first."""
    import xml.etree.ElementTree as ET
    from QC.utilities.classify_quotes import _sentence_records

    path = tmp_path / "a.xml"
    path.write_text(
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1">'
        '<FORM kindOf="original" ver="alt">variant reading</FORM>'
        '<FORM kindOf="original">base reading</FORM>'
        "</S></TEXT>",
        encoding="utf-8",
    )
    records = _sentence_records(str(path), "ami")
    assert [text for text, _transls in records] == ["base reading"]


def test_sentence_records_skip_a_variant_only_sentence(tmp_path):
    from QC.utilities.classify_quotes import _sentence_records

    path = tmp_path / "a.xml"
    path.write_text(
        '<TEXT xml:lang="ami" dialect="Coastal">'
        '<S id="1"><FORM kindOf="original" ver="alt">variant reading</FORM></S>'
        "</TEXT>",
        encoding="utf-8",
    )
    assert _sentence_records(str(path), "ami") == []


# --- wrap rules and whole-word lookup (maintainer, 2026-10-14) ---------------

def test_wrapped_translation_and_single_quoted_utterance_become_double():
    # Rule 1: both wrapped; the closing quote may sit before or after the period.
    for text in ("'o wawa no tao.'", "'o wawa no tao'."):
        new, corrected, _, _ = aqc(text, ['" the child of the person ."'], set())
        assert new.startswith('"') and '"' in new[-2:] and "'" not in new
        assert len(corrected) == 2


def test_consumed_wrapping_quotes_license_nothing_else():
    # Rule 2: utterance already in double quotes; the translation's wrap is
    # consumed, no other quote is left, so the inner ' stay glottal.
    text = "\"'ayam ko tao'.\""
    new, corrected, _, _ = aqc(text, ['" the bird of the person ."'], set())
    assert new == text and corrected == []


def test_a_wrapped_translation_is_consumed_even_when_the_utterance_is_not():
    # Addendum (2026-10-14): the translation-wrapping quotes are consumed anyway
    # and are not evidence of a quote; nothing else quotes, so nothing changes.
    text = "'aehoe' mwai' ila kita' oyae'."
    assert aqc("o wawa 'ayam tao'.", ['" a child said bird ."'], set())[0] == "o wawa 'ayam tao'."
    # ... but a quotation inside the translation still licenses the old rules.
    assert aqc("o wawa 'ayam tao'.", ['" a child said “bird” ."'], set())[0] == 'o wawa "ayam tao".'


def test_a_word_with_a_glottal_at_both_edges_is_found_whole():
    # 'aehoe' (Saisiyat, dog): the old lookup tried only 'aehoe and aehoe'.
    text = "kas'oehaz ka 'aehoe' sahae' ila 'i'izo'."
    lst = {"'aehoe'", "'i'izo'"}
    new, corrected, _, _ = aqc(text, ['he said "x" there', "他說「x」"], lst)
    assert corrected == [] and new == text


def test_transl_wrap_needs_one_pair_around_the_whole_translation():
    tw = classify_quotes.transl_wrap
    assert tw('" dog also came to see ."') == (0, 24)
    assert tw('"dog came".') is not None
    assert tw('"A" and "B"') is None                 # two quotations
    assert tw("「他說『走』」") is not None             # corner quotes nest
    assert tw("he said \"go\"") is None


def test_single_quoted_quotations_inside_a_consumed_translation_still_count():
    # Formosan-Kanakanavu-Texts S_SPIRIT_S0020: utterance and translation are both
    # wrapped in "; the translation's own quotation 'Yes,' licenses the nested
    # 'əəʔə,' -> "əəʔə," (POL-018: nested quotations use double quotes too).
    text = "\"nuu ʔusu misa=kan kasua Suŋau ia, 'əəʔə,' kisa-u-i=ʔai.\""
    tr = ["\"When the Sungau says 'Usu to you, say 'Yes,' in reply.\""]
    assert aqc(text, tr, set())[0] == "\"nuu ʔusu misa=kan kasua Suŋau ia, \"əəʔə,\" kisa-u-i=ʔai.\""
    # contractions and possessives are not quotation marks
    assert classify_quotes._single_quote_pairs_as_double("it's the dogs' bone") == "it's the dogs' bone"


def test_rule_3_needs_the_opener_first_and_checks_it_against_the_list():
    # NTU SaiNr-kathethel2 S_173: kamamwai' (closer-shaped) comes BEFORE the
    # opener 'iniya'om, which is on the Saisiyat list; nothing may be converted.
    text = "saen ay So'o ay hini kamamwai', talek, 'iniya'om."
    tr = ['They said: "Is it you who come to cook for us?"']
    assert aqc(text, tr, {"'iniya'om"})[0] == text
    assert aqc(text, tr, set())[0] == text            # order alone blocks it


# --- consonant preference (maintainer, 2026-10-14) ---------------------------
# "for Saisiyat, Saaroa, Bunun, Kanakanavu, Paiwan, Puyuma, and Rukai, a ' next
# to a consonant should be considered as a prime candidate for a quotation mark
# UNLESS that is a word attested in that language with that spelling."

def test_a_consonant_adjacent_quote_wins_among_several_openers():
    # Two word-initial ', so rule 2 cannot choose; 'tatini (' + t) is the prime
    # one, 'oya (' + o) stays a glottal.
    text = "'oya ka 'tatini sahae.' ila"
    assert aqc(text, [], set())[0] == text                       # no preference: nothing
    assert aqc(text, [], set(), set())[0] == "'oya ka \"tatini sahae.\" ila"


def test_a_consonant_adjacent_word_attested_with_that_spelling_is_not_prime():
    text = "'oya ka 'tatini sahae.' ila"
    assert aqc(text, [], set(), {"'tatini"})[0] == text           # exception list
    assert aqc(text, [], {"'tatini"}, set())[0] == text           # the main list


def test_more_quote_shaped_apostrophes_than_translation_quotes():
    # Rule 1 needs as many start/end ' as TRANSL quotes; with one too many, the
    # two consonant-adjacent ones match the count and are taken.
    text = "'aehoe ma 'tatini sahaek'."
    tr = ['the dog said "come here".']
    assert aqc(text, tr, set())[0] == text
    assert aqc(text, tr, set(), set())[0] == "'aehoe ma \"tatini sahaek\"."


def test_the_preference_never_overrides_rule_1_when_the_counts_already_match():
    # Two openers and two closers, four TRANSL quotes: rule 1 takes all four,
    # prime or not.
    text = "'ima ka', 'tatini sahaek'."
    tr = ['"this", "that".']
    assert aqc(text, tr, set(), set())[0] == aqc(text, tr, set())[0] == '"ima ka", "tatini sahaek".'


# --- '' pairs (maintainer, 2026-10-14) ----------------------------------------
# "If there is a `''` and a matching `''` in the same utterance, they can be
# converted to "s."

def test_a_matching_pair_of_double_apostrophes_becomes_double_quotes():
    # ePark Atayal: '' typed for a double quote; previously half-converted.
    text = "''tlubuw'' ga, mha ''rgyax.''"
    new, corrected, _, _ = aqc(text, [], set())
    assert new == '"tlubuw" ga, mha "rgyax."' and len(corrected) == 4


def test_double_apostrophes_need_a_match_and_a_word_edge():
    assert aqc("''tlubuw ga", [], set())[0] == "''tlubuw ga"                   # no match
    assert aqc("kamatortoroe''omaling' ka", [], set())[0] == "kamatortoroe''omaling' ka"  # inside a word
    assert aqc("'''Amis''' ka", [], set())[0] == "'''Amis''' ka"               # three: not one
    # the glottals inside a converted pair stay glottals
    assert aqc("''s'uli'' ka", [], set())[0] == '"s\'uli" ka'


def test_a_double_apostrophe_matches_only_the_next_one():
    # Amis Wikipedia U_parik_a_lutuk: each mark glued to a neighbouring word;
    # the first opening must not pair with the last closing a paragraph later.
    text = "tu ''maylunsan''han nu hulam, a lutuk''maylunsan''… Tuna"
    assert aqc(text, [], set())[0] == text
    # Sakizaya Wikipedia Daren: '' followed by a comma does not open.
    text = "niyadu' '', pacumud tu ta-zen a kenis'' ka"
    assert aqc(text, [], set())[0] == text
