"""NTUFormosanCorpus: source notation the builders must parse, not publish.

Maintainer's rulings, 2026-10-18 (NTU follow-up review), one test group each:

* a malformed code-switch tag, '<T2mi.jioL2T>' (TsouConv-typhoon record 421):
  "fix that stripping." (scripts/utils.py, _L2M_RE);
* a Sakizaya grammar example quoted from a conversation, '100....（2.2）^yah'
  (intonation-unit number, pause, then the word): the unit number and the pause
  must not be glued onto the word (pipeline_grammar.py, step 15);
* multi-speaker labels, 'Y,M:', 'W,G,S:': "Any number of single capital letters
  followed by a colon, ignore intervening commas => speaker label."
  (pipeline_stories.py, step 15).

The second group holds the published XML to the rulings; NTU_XML_DIR points it
at another tree (e.g. the pre-change XML, on which these tests fail).
"""
from __future__ import annotations

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CODEDOCS = ROOT / "Corpora" / "NTUFormosanCorpus" / "CodeAndDocs"
NTU_XML = Path(os.environ.get("NTU_XML_DIR") or ROOT / "Corpora" / "NTUFormosanCorpus" / "XML")
sys.path.insert(0, str(CODEDOCS / "scripts"))

from utils import strip_l2m, strip_prosodic_markers  # noqa: E402

sys.path.insert(0, str(CODEDOCS / "pipeline"))
import pipeline_stories as ps  # noqa: E402


def _inner(el):
    return (el.text or "") + "".join(ET.tostring(c, encoding="unicode") for c in el)


# ------------------------------------------------------------ the parsers


@pytest.mark.parametrize("raw, clean", [
    ("<T2mi.jioL2T>].\\\\", "mi.jio."),     # the malformed tag, opening with no L
    ("<L2haiyaL2>", "haiya"),               # a bare <L2 still keeps the word's h
    ("<L2JjidenshaL2J>", "jidensha"),
    ("k<um>an", "k<um>an"),                 # infix notation untouched
    ("<PF.PFV>", "<PF.PFV>"),
])
def test_code_switch_tags_stripped(raw, clean):
    assert strip_l2m(strip_prosodic_markers(raw))[0] == clean


@pytest.mark.parametrize("raw, label", [
    ("Y,M:", True), ("W,G,S:", True), ("S, G ,W：", True),
    ("Y,M", False),            # no colon: not a label
    ("ma,", False), ("Lao.Jia:", False), ("T:", False),   # T: is the single-label rule's
])
def test_multi_speaker_label_pattern(raw, label):
    assert bool(ps.multi_speaker_labels([[raw, "_", "_"]])) is label


def test_multi_speaker_label_row_is_apparatus():
    labels = ps.multi_speaker_labels([["S,G,W:", "_", "_"]])
    assert ps.apparatus_class(["S,G,W", "", ""], labels).startswith("1 speaker label")
    assert ps.apparatus_class(["S,G,W", "", ""]) is None    # without the raw cell's colon


# ------------------------------------------------------- the published XML


@pytest.fixture(scope="module")
def sentences():
    files = sorted(NTU_XML.rglob("*.xml"))
    assert files, f"no XML under {NTU_XML}"
    return {s.get("id"): s for f in files for s in ET.parse(f).getroot().iter("S")}


def test_malformed_code_switch_tag_stripped(sentences):
    s = sentences["TsouConv-typhoon_S_420"]
    w = next(w for w in s.findall("W") if w.get("id") == "TsouConv-typhoon_S_420_W11")
    assert [_inner(f) for f in w.iter("FORM")] == ["mi.jio"] * 4
    assert [f.text for f in s.findall("FORM")] == ["'a lasi no 'so aiti honga 'o, 'o 'o ping.zhuang to mi.jio."] * 2
    leftovers = [(sid, "".join(f.itertext())) for sid, s in sentences.items() for f in s.iter("FORM")
                 if "T2mi" in "".join(f.itertext())]
    assert leftovers == []


def test_cited_excerpt_words_carry_no_transcription_apparatus():
    """Grammar 13.json records 38, 39, 48 quote skzyNr-moving_kulang IU100-101,
    IU105-107 and IU309-312; '100....（2.2）^yah' is the word 'yah'."""
    root = ET.parse(NTU_XML / "Grammar" / "Sakizaya" / "Sakizaya.xml").getroot()
    sakizaya = {s.get("id"): s for s in root.iter("S")}
    words = {sid: [w.find("FORM").text for w in sakizaya[sid].findall("W")]
             for sid in ("13_S_38", "13_S_39", "13_S_48")}
    assert words["13_S_38"] == ["yah", "ta-luma'", "kina", "adiwawa", "sa", "ku", "babalaki"]
    assert words["13_S_39"][0] == "sa-ka-ta-luma'" and words["13_S_39"][6] == "sa"
    assert words["13_S_48"][0] == "ya" and "caliw" in words["13_S_48"]
    for sid, forms in words.items():
        for form in forms:
            assert not any(ch.isdigit() for ch in form) and "==" not in form, (sid, form)


MULTI_LABEL_SENTENCES = {   # S id -> its sentence FORM after the labels went (22 sentences, 23 labels)
    "None-1_S_21": "te'o i'vaha mia 'ia, mi mimu i'vaho novei to, atuhcumu emoo.",
    "TsouConv-typhoon_S_289": "zou ba'e mameoi.",
    "TsouConv-typhoon_S_503": "ea zou mo nana, <UNCLEAR /> <UNCLEAR /> oh mo nana nʉthʉ na s, seito ne kosiuso.",
}


def test_multi_speaker_labels_removed(sentences):
    import re
    label = re.compile(r"(?<!\S)[A-Z](?:,[A-Z])+(?!\S)")
    left = [(sid, "".join(f.itertext())) for sid, s in sentences.items() for f in s.iter("FORM")
            if label.search("".join(f.itertext()))]
    assert left == [], f"{len(left)} FORM(s) still hold a multi-speaker label, e.g. {left[:3]}"
    for sid, form in MULTI_LABEL_SENTENCES.items():
        assert [_inner(f) for f in sentences[sid].findall("FORM")] == [form] * 2, sid
