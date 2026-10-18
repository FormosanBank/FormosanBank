"""NTUFormosanCorpus: source notation the builders must parse, not publish.

Maintainer's rulings, 2026-10-18 (NTU follow-up review), one test group each:

* a malformed code-switch tag, '<T2mi.jioL2T>' (TsouConv-typhoon record 421):
  "fix that stripping." (scripts/utils.py, _L2M_RE);

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
