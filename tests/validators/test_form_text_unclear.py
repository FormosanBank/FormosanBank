"""Rules read a FORM whole, past an inline <UNCLEAR/> (rules/_form_text.py).

The text after <UNCLEAR/> is the marker's tail, so a plain ``form.text``
read stopped at the marker. Each example below is a real published shape
(NTUFormosanCorpus, WilangYutasVideos) that the old read got wrong.
"""
from io import BytesIO
from pathlib import Path

from lxml import etree

from QC.validation.rules import gloss as gloss_rules
from QC.validation.rules import text as text_rules
from QC.validation.rules._form_text import form_text, form_words_text

_TEXT = """<?xml version="1.0" encoding="utf-8"?>
<TEXT id="T1" citation="t" BibTeX_citation="@t{{t}}" copyright="t" xml:lang="dru">
{body}
</TEXT>
"""


def _findings(rule, body: str):
    tree = etree.parse(BytesIO(_TEXT.format(body=body).encode("utf-8")))
    return rule(tree, Path("test.xml"), None)


def _form(xml: str):
    return etree.fromstring(xml)


# Rukai, 20200529-FW-Lixing-1_S_18: the old read saw 'waecenge ka' only.
_RUKAI_S = """<S id="S1">
  <FORM kindOf="original">waecenge ka <UNCLEAR/>lalasu ki kidringi.</FORM>
  <W id="W1"><FORM kindOf="original">w-a-ecenge</FORM></W>
  <W id="W2"><FORM kindOf="original">ka</FORM></W>
  <W id="W3"><FORM kindOf="original">la-lasu</FORM></W>
  <W id="W4"><FORM kindOf="original">ki</FORM></W>
  <W id="W5"><FORM kindOf="original">kidringi</FORM></W>
</S>"""


def test_form_text_keeps_the_text_after_the_marker():
    form = _form('<FORM>waecenge ka <UNCLEAR/>lalasu ki kidringi.</FORM>')
    assert form_text(form) == "waecenge ka lalasu ki kidringi."
    assert form_words_text(form) == "waecenge ka ?lalasu ki kidringi."


def test_form_words_text_counts_a_standalone_marker_as_a_word():
    form = _form('<FORM>ini uda hii <UNCLEAR/> <UNCLEAR/></FORM>')
    assert form_words_text(form).split() == ["ini", "uda", "hii", "?", "?"]


def test_comments_add_no_text():
    form = _form('<FORM>ka<!-- note --> lalasu</FORM>')
    assert form_text(form) == "ka lalasu"


def test_v060_counts_the_words_after_the_marker():
    assert _findings(gloss_rules.v060_W_count_matches_word_count, _RUKAI_S) == []


def test_v060_counts_a_sentence_that_starts_with_the_marker():
    # Seediq S_134 shape: .text is None, so the old read counted 0 words.
    body = """<S id="S1">
      <FORM kindOf="original"><UNCLEAR/> ye kiya</FORM>
      <W id="W1"><FORM kindOf="original"><UNCLEAR/></FORM></W>
      <W id="W2"><FORM kindOf="original">ye</FORM></W>
      <W id="W3"><FORM kindOf="original">kiya</FORM></W>
    </S>"""
    assert _findings(gloss_rules.v060_W_count_matches_word_count, body) == []


def test_v141_spells_the_whole_sentence():
    assert _findings(text_rules.v141_W_reconstructs_S, _RUKAI_S) == []


def test_v061_counts_an_unclear_morpheme():
    # Kanakanavu kkvNr_dailylife_Angai_S_9_W1.
    body = """<S id="S1"><FORM kindOf="original">x</FORM>
      <W id="W1"><FORM kindOf="original"><UNCLEAR/>=maku</FORM>
        <M id="M1"><FORM kindOf="original">XX</FORM></M>
        <M id="M2"><FORM kindOf="original">=maku</FORM></M>
      </W></S>"""
    assert _findings(gloss_rules.v061_M_count_matches_form_segmentation, body) == []


def test_v122_sees_a_slash_after_the_marker():
    # WilangYutasVideos Atayal_133.
    body = '<S id="S1"><FORM kindOf="original">ruw...<UNCLEAR/> /</FORM></S>'
    findings = _findings(text_rules.v122_parens_slashes_anywhere, body)
    assert [f.rule_id for f in findings] == ["V122"]
