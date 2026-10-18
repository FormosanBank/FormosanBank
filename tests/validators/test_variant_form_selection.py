"""A ver="alt" variant must never stand in for its tier's base FORM.

POL-028 (revised 2026-09-09) gave every tier a base FORM plus zero or
more ``ver="alt"`` variants. The rules and helpers here all reach for
"the node's original text", and each of them used
``find('./FORM[@kindOf="original"]')``, which returns the first match in
*document order* — a variant whenever one is written first. The XSD does
not order FORM siblings, so which one you get is luck.

Each test builds a node whose variant and base disagree in a way the
rule can see, and asserts the rule follows the base. Every one of them
fails if the selection reverts to first-match.
"""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from lxml import etree

from QC.validation import _source_align
from QC.validation.rules import gloss as gloss_rules
from QC.validation.rules import gloss_scrape
from QC.validation.rules import text as text_rules

_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="pwn">'
)


def _tree(body: str) -> etree._ElementTree:
    return etree.parse(BytesIO((_HEAD + body + "</TEXT>").encode("utf-8")))


def _first(body: str, tag: str) -> etree._Element:
    return _tree(body).find(f".//{tag}")


# --------------------------------------------------------------------------
# V060 — word count of the S base, not of a shorter variant
# --------------------------------------------------------------------------

def test_v060_counts_the_base_not_a_preceding_variant():
    """Base has 3 words and 3 W children: clean. The variant has 2."""
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">ina kaen</FORM>'
        '<FORM kindOf="original">ina kaen wawa</FORM>'
        '<W id="S1W1"><FORM kindOf="original">ina</FORM></W>'
        '<W id="S1W2"><FORM kindOf="original">kaen</FORM></W>'
        '<W id="S1W3"><FORM kindOf="original">wawa</FORM></W>'
        "</S>"
    )
    assert gloss_rules.v060_W_count_matches_word_count(
        tree, Path("test.xml"), None
    ) == []


def test_v060_does_not_pile_onto_a_variant_only_sentence():
    """No base FORM means nothing to compare, so V060 must stay silent and
    leave the shape to V149 (HARD). Without the guard, strict selection
    turns the missing base into a bogus "word-count (0)" finding."""
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">ina kaen wawa</FORM>'
        '<W id="S1W1"><FORM kindOf="original">ina</FORM></W>'
        '<W id="S1W2"><FORM kindOf="original">kaen</FORM></W>'
        '<W id="S1W3"><FORM kindOf="original">wawa</FORM></W>'
        "</S>"
    )
    assert gloss_rules.v060_W_count_matches_word_count(
        tree, Path("test.xml"), None
    ) == []


def test_get_w_form_prefers_the_base():
    w = _first(
        '<S id="S1"><W id="S1W1">'
        '<FORM kindOf="original" ver="alt">kan</FORM>'
        '<FORM kindOf="original">kaen</FORM>'
        "</W></S>",
        "W",
    )
    assert gloss_rules._get_w_form(w) == "kaen"


def test_extract_s_direct_text_prefers_the_base():
    s = _first(
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">ina kaen</FORM>'
        '<FORM kindOf="original">ina kaen wawa</FORM>'
        "</S>",
        "S",
    )
    assert gloss_rules._extract_s_direct_text(s) == "ina kaen wawa"


def test_extract_s_direct_text_ignores_a_variant_only_tier():
    """Strict (maintainer ruling 2026-09-10): a variant is not a base, so
    the S falls through to its own direct text rather than the variant."""
    s = _first(
        '<S id="S1"><FORM kindOf="original" ver="alt">ina kaen</FORM></S>',
        "S",
    )
    assert gloss_rules._extract_s_direct_text(s) == ""


# --------------------------------------------------------------------------
# V068 / V141 — letter-skeleton reconstruction reads bases
# --------------------------------------------------------------------------

def test_v068_reconstructs_from_the_w_base_not_a_variant():
    """M tier spells the W base exactly; the variant is unrelated letters."""
    tree = _tree(
        '<S id="S1"><W id="S1W1">'
        '<FORM kindOf="original" ver="alt">qqqqzzzz</FORM>'
        '<FORM kindOf="original">ka-kaun-un</FORM>'
        '<M id="S1W1M1"><FORM kindOf="original">ka</FORM></M>'
        '<M id="S1W1M2"><FORM kindOf="original">kaun</FORM></M>'
        '<M id="S1W1M3"><FORM kindOf="original">un</FORM></M>'
        "</W></S>"
    )
    assert gloss_rules.v068_M_reconstructs_W(tree, Path("test.xml"), None) == []


def test_v141_reconstructs_from_the_s_base_not_a_variant():
    tree = _tree(
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">qqqq zzzz</FORM>'
        '<FORM kindOf="original">ina kaen</FORM>'
        '<W id="S1W1"><FORM kindOf="original">ina</FORM></W>'
        '<W id="S1W2"><FORM kindOf="original">kaen</FORM></W>'
        "</S>"
    )
    assert text_rules.v141_W_reconstructs_S(tree, Path("test.xml"), None) == []


# --------------------------------------------------------------------------
# V153 — _pref_form_text
# --------------------------------------------------------------------------

def test_pref_form_text_prefers_the_base():
    w = _first(
        '<S id="S1"><W id="S1W1">'
        '<FORM kindOf="original" ver="alt">kan</FORM>'
        '<FORM kindOf="original">ka-kaun-un</FORM>'
        "</W></S>",
        "W",
    )
    assert gloss_rules._pref_form_text(w) == "ka-kaun-un"


# --------------------------------------------------------------------------
# gloss_scrape._form_text
# --------------------------------------------------------------------------

def test_gloss_scrape_form_text_prefers_the_base():
    w = _first(
        '<S id="S1"><W id="S1W1">'
        '<FORM kindOf="original" ver="alt">kan</FORM>'
        '<FORM kindOf="original">kaen</FORM>'
        "</W></S>",
        "W",
    )
    assert gloss_scrape._form_text(w, "original") == "kaen"


# --------------------------------------------------------------------------
# _source_align._s_text_for_matching
# --------------------------------------------------------------------------

def test_source_align_matches_on_the_s_base():
    s = _first(
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">ina kaen</FORM>'
        '<FORM kindOf="original">ina kaen wawa</FORM>'
        "</S>",
        "S",
    )
    assert _source_align._s_text_for_matching(s) == "ina kaen wawa"


def test_source_align_w_fallback_uses_the_original_tier():
    """Separate defect in the same expression: `a or b` on lxml elements
    is False for a childless element, so the kindOf filter was discarded
    and the first FORM of any tier won."""
    s = _first(
        '<S id="S1">'
        '<W id="S1W1">'
        '<FORM kindOf="standard">kaen</FORM>'
        '<FORM kindOf="original">ka2en</FORM>'
        "</W></S>",
        "S",
    )
    assert _source_align._s_text_for_matching(s) == "ka2en"


def test_source_align_w_fallback_prefers_the_base_over_a_variant():
    s = _first(
        '<S id="S1">'
        '<W id="S1W1">'
        '<FORM kindOf="original" ver="alt">kan</FORM>'
        '<FORM kindOf="original">kaen</FORM>'
        "</W></S>",
        "S",
    )
    assert _source_align._s_text_for_matching(s) == "kaen"


# --------------------------------------------------------------------------
# Audio collectors — the text paired with an audio span must be the base
# --------------------------------------------------------------------------

_AUDIO_HEAD = (
    '<?xml version="1.0" encoding="utf-8"?>'
    '<TEXT id="T1" citation="t" BibTeX_citation="@t{t}" '
    'copyright="t" xml:lang="ami">'
)


def _audio_corpus(tmp_path, body: str):
    """Write <tmp>/XML/test.xml plus the .wav its AUDIO refers to."""
    xml_dir = tmp_path / "XML"
    xml_dir.mkdir(parents=True, exist_ok=True)
    (tmp_path / "Audio").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Audio" / "a.wav").write_bytes(b"FAKE_WAV")
    (xml_dir / "test.xml").write_text(_AUDIO_HEAD + body + "</TEXT>", encoding="utf-8")
    return xml_dir


def test_collect_sentence_refs_pairs_audio_with_the_base(tmp_path):
    """A variant is a second reading; the audio was cut against the base,
    so density checks must measure the base's text."""
    from QC.validation import validate_audio

    xml_dir = _audio_corpus(
        tmp_path,
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">short</FORM>'
        '<FORM kindOf="original">a much longer spoken sentence</FORM>'
        '<AUDIO file="a.wav" start="0" end="3"/>'
        "</S>",
    )
    refs = validate_audio.collect_sentence_refs(str(xml_dir))
    assert [r.form_text for r in refs] == ["a much longer spoken sentence"]


def test_collect_entries_uses_the_base_as_the_asr_reference(tmp_path):
    from QC.validation import validate_audio_quality

    xml_dir = _audio_corpus(
        tmp_path,
        '<S id="S1">'
        '<FORM kindOf="original" ver="alt">variant reading</FORM>'
        '<FORM kindOf="original">base reading</FORM>'
        '<AUDIO file="a.wav"/>'
        "</S>",
    )
    entries = validate_audio_quality.collect_entries(
        xml_dir / "test.xml", tmp_path / "Audio", "ami"
    )
    assert [e["transcript"] for e in entries] == ["base reading"]
