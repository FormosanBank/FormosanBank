"""NTUFormosanCorpus: source notation the builders must parse, not publish.

Maintainer's rulings, 2026-10-18 (NTU follow-up review), one test group each:

* a malformed code-switch tag, '<T2mi.jioL2T>' (TsouConv-typhoon record 421):
  "fix that stripping." (scripts/utils.py, _L2M_RE);
* a Sakizaya grammar example quoted from a conversation, '100....（2.2）^yah'
  (intonation-unit number, pause, then the word): the unit number and the pause
  must not be glued onto the word (pipeline_grammar.py, step 15);

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
