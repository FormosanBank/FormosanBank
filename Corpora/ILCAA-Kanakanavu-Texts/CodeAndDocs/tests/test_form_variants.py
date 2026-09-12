"""Readings checked against printed examples, not inferred from string overlap."""
import os
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest


ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = Path(os.environ.get("KANAKANAVU_WORKSPACE", ROOT / "CodeAndDocs/.build"))


def sentence(text_number, number, suffix=""):
    path, = (WORKSPACE / "build/xml_drafts/Kanakanavu").glob(f"ILCAA_KanakanavuTexts_{text_number:03d}_*.xml")
    root = ET.parse(path).getroot()
    return root.find(f'./S[@id="{root.attrib["id"]}_S{number:04d}{suffix}"]')


def readings(parent):
    return [form.text for form in parent.findall('./FORM[@kindOf="original"]')]


@pytest.mark.parametrize("text,number,word,morph,word_forms,morph_forms,gloss", [
    (6, 4, 2, 1, ["makaasu", "makaasua"], ["makaasu", "makaasua"], "in.that.way"),  # p53
    (8, 1, 4, 1, ["tee=ku", "tia=ku"], ["tee", "tia"], "FUT"),  # p55, footnote 14
    (10, 14, 11, 2, ["cəpəŋ-in", "cəpəŋ-ini"], ["in", "ini"], "3.GEN"),  # p71
    (11, 88, 5, 4, ["tia=ma-ʔanivi-ni", "tia=ma-ʔanivi-ini"], ["ni", "ini"], "3.GEN"),  # p93
    (11, 102, 4, 1, ["va=ʔai", "ava=ʔai"], ["va", "ava"], "in.fact"),  # p95
    (40, 9, 1, 1, ["aan=ci", "haan=ci"], ["aan", "haan"], "Where.gone"),  # p231
])
def test_same_word_readings_share_sentence(text, number, word, morph, word_forms, morph_forms, gloss):
    source = sentence(text, number)
    assert source is not None
    assert sentence(text, number, "-opt") is None
    assert len(source.findall("FORM")) == 1
    w = source.findall("W")[word - 1]
    m = w.findall("M")[morph - 1]
    assert readings(w) == word_forms
    assert readings(m) == morph_forms
    assert m.findtext("TRANSL") == gloss
    for node in (w, m):
        assert [form.get("ver") for form in node.findall("FORM")] == [None, "alt"]


def test_optional_whole_words_keep_separate_aligned_sentences():
    # p74 example 29: the source places exist/LOC beneath optional (ʔaisi na).
    base, optional = sentence(10, 29), sentence(10, 29, "-opt")
    base_words, full_words = base.findall("W"), optional.findall("W")
    assert len(full_words) == len(base_words) + 2
    assert [(readings(w)[0], w.findtext("TRANSL")) for w in full_words[10:12]] == [("ʔaisi", "exist"), ("na", "LOC")]
    assert [readings(w) for w in base_words] == [readings(w) for w in full_words[:10] + full_words[12:]]
    assert base.findtext("TRANSL") == optional.findtext("TRANSL")


def test_different_source_glosses_do_not_collapse_to_form_variants():
    # p55 example 2 explicitly contrasts AV-go with AV-IRR-go.toward.
    base, alternate = sentence(8, 2), sentence(8, 2, "-opt")
    first, second = base.findall("W")[3], alternate.findall("W")[3]
    assert readings(first) == ["mu-usa"]
    assert readings(second) == ["mu-a-kusa"]
    assert first.findtext("TRANSL") == "AV-go"
    assert second.findtext("TRANSL") == "AV-IRR-go.toward"
    assert len(first.findall("M")) == 2
    assert len(second.findall("M")) == 3


@pytest.mark.parametrize("number,words,glosses,analyzed_morphs", [
    (24, ["naini", "sua", "k<um>a-kaən", "uuru"], ["who", "NOM", "RED<AV>-eat", "cooked.rice"], [("k-a", "RED"), ("-um-", "<AV>"), ("kaən", "eat")]),
    (25, ["naini", "sua", "kaən-a"], ["what", "NOM", "eat-NMLZ.UV"], [("kaən", "eat"), ("a", "NMLZ.UV")]),
    (26, ["naini", "sua", "si-pa-Ɂucip-in", "uuru"], ["what", "NOM", "CV-PA-cook-3.GEN", "cooked.rice"], [("si", "CV"), ("pa", "PA"), ("Ɂucip", "cook"), ("in", "3.GEN")]),
    (27, ["naini", "sua", "si-ara-kulacə=musu", "ia"], ["what", "NOM", "CV-get-angry=2SG.GEN", "TOP"], [("si", "CV"), ("ara", "get"), ("kulacə", "angry"), ("=musu", "2SG.GEN")]),
])
def test_pseudocleft_clause_brackets_preserve_source_alignment(number, words, glosses, analyzed_morphs):
    # Physical page 24, examples 23a-d. Brackets delimit the clause, not a word.
    source = sentence(0, number)
    assert "[" in source.findtext("FORM") and "]" in source.findtext("FORM")
    assert "*" not in source.findtext("FORM")
    parsed = source.findall("W")
    assert [readings(w)[0] for w in parsed] == words
    assert [w.findtext("TRANSL") for w in parsed] == glosses
    assert [(readings(m)[0], m.findtext("TRANSL")) for m in parsed[2].findall("M")] == analyzed_morphs
    assert all(w.findall("M") for w in parsed)


@pytest.mark.parametrize("text,number,word,form,gloss,morphs", [
    (9, 47, 2, "t<in-um>upuru", "sit<PFV-AV>", [("t-upuru", "sit"), ("-in-", "<PFV>"), ("-um-", "<AV>")]),  # p66
    (21, 62, 5, "c<in-əm>əʔrə-a=kara=kamu", "see<PFV-AV>-LOC=Q=2PL.NOM", [("c-əʔrə", "see"), ("-in-", "<PFV>"), ("-əm-", "<AV>"), ("a", "LOC"), ("=kara", "Q"), ("=kamu", "2PL.NOM")]),  # p138
    (22, 12, 1, "t<in-um>mana", "hear<PFV-AV>", [("t-mana", "hear"), ("-in-", "<PFV>"), ("-um-", "<AV>")]),  # p142
    (29, 17, 5, "t<in-m>mana=ku", "hear<PFV-AV>=1SG.NOM", [("t-mana", "hear"), ("-in-", "<PFV>"), ("-m-", "<AV>"), ("=ku", "1SG.NOM")]),  # p176
    (31, 34, 1, "s<in-m>ərəcə", "check.trap<PFV-AV>", [("s-ərəcə", "check.trap"), ("-in-", "<PFV>"), ("-m-", "<AV>")]),  # p193
    (39, 22, 1, "c<in-m>aʔivi=cu", "pass<PFV-AV>=COS", [("c-aʔivi", "pass"), ("-in-", "<PFV>"), ("-m-", "<AV>"), ("=cu", "COS")]),  # p229
    (42, 20, 5, "c<in-m>əʔəra", "see<PFV-AV>", [("c-əʔəra", "see"), ("-in-", "<PFV>"), ("-m-", "<AV>")]),  # p242
    (42, 27, 4, "c<in-m>əʔəra", "see<PFV-AV>", [("c-əʔəra", "see"), ("-in-", "<PFV>"), ("-m-", "<AV>")]),  # p242
    (29, 17, 2, "c<um>əʔəra", "see<AV>", [("c-əʔəra", "see"), ("-um-", "<AV>")]),  # p176, single infix
    (40, 20, 3, "ʔələvə", "priest-shaman", [("ʔələvə", "priest-shaman")]),  # accepted single lexical gloss
])
def test_source_infixes_and_following_clitics(text, number, word, form, gloss, morphs):
    # Introduction pp18-19 identifies separate PFV and AV infixes, in that order.
    w = sentence(text, number).findall("W")[word - 1]
    assert readings(w) == [form]
    assert w.findtext("TRANSL") == gloss
    parsed = w.findall("M")
    assert [(readings(m)[0], m.findtext("TRANSL")) for m in parsed] == morphs
    assert [m.get("id") for m in parsed] == [f'{w.get("id")}_M{i:02d}' for i in range(1, len(morphs) + 1)]
