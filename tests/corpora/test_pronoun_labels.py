"""Pronoun person-number labels in the standard gloss tier (maintainer 2026-11-27, pronoun glosses page
NSfDfqWnj1j6R3vhD2ei3x: "I prefer 2SG and 2PL to you.SG and you.PL. Same for 1SG and 1PL and 3SG and 3PL. Can we apply
anywhere we've standardized differently so far?"; round 2: "Periods: 1PL.INCL / 1PL.EXCL").

Two kinds of check, per corpus, on the published XML:
  converted  -- no old spelling the rulings convert is left, outside glosses the tool copies whole (residue: a
                parenthesis it does not handle, e.g. "(spend.the.night)-we", "=一下(客氣)=你.主格");
  kept       -- what was ruled to stay is still there: possessives (card p5 "These all go on undecided list, keep their
                original forms."), bare "you" (card p4 "you (number not stated) -> undecided"), self-glosses that only
                look like English pronouns (NTU "HE" = Tsou -he, "ME" = Kanakanavu me-, "US" = 美國; "I" glossing a
                morpheme i), and 其他 'other'.
Written before the conversion was applied (the maintainer: "When applying to things already standardized (if any),
please write some tests first to make sure the splash radius is exactly as expected.").
"""
import re
import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
XL = "{http://www.w3.org/XML/1998/namespace}lang"
SEP = r"(?:^|(?<=[.\-=<>~\s]))"          # start of an atom
END = r"(?=$|[.\-=<>~\s])"               # end of an atom


def atom(*xs):
    return re.compile(SEP + "(?:" + "|".join(re.escape(x) for x in xs) + ")" + END)


ZH_OLD = atom("我", "你", "他", "她", "我們", "你們", "他們", "她們", "咱們")
OLD = {
    "NTUFormosanCorpus": [atom("1S", "2S", "3S", "1P", "2P", "3P", "1PI"), re.compile(r"\b1P\((?:IN|EX|INCL|EXCL)\)"), ZH_OLD],
    "Amis-Pa-Verbs": [atom("1S", "2S", "3S", "1P", "2P", "3P")],
    "Huteson-Rukai-Survey": [atom("1S", "2S", "3S", "1P", "2P", "3P")],
    "RauDong": [re.compile(SEP + r"[123]\.[SP]" + END), ZH_OLD, atom("含", "除")],
    "ILCAA-Kanakanavu-Texts": [atom("1INCL", "1EXCL", "1.EXCL")],
    "Wild-Lehmann-Kanakanavu": [atom("1PI", "1PE")],
    "Naomi-Tsukida-Correlative-Clauses-Seediq": [atom("1PLIN", "1PLEX")],
    "HundredPaiwanStories": [atom("I", "3rd.pers"), re.compile(r"\bwe\((?:INCL|EXCL|inc|exc)\)|\byou\((?:s|p)\)")],
    "WakelinTexts": [atom("I", "i", "me", "he", "him", "she", "they", "them", "we", "us")],
    "Li-Conjunction-Thao": [atom("I", "we", "you.pl")],
    "Song-Kanakanavu-Grammar": [ZH_OLD, atom("排除", "排除式", "包含式")],
    "Kavalan-Chang-Reference-Grammar": [ZH_OLD],
    "Seediq-Chang-Reference-Grammar": [ZH_OLD],
    "Nowbucyang-Truku-Thesis": [ZH_OLD],
    "Sakizaya-Affixes": [ZH_OLD, atom("包含式")],
}
KEPT = {   # (pattern, why) -- each must still occur in the standard tier
    "HundredPaiwanStories": [(atom("my"), "possessive (p5)"), (re.compile(r"\byour\((?:s|p)\)"), "possessive (p5)"),
                             (atom("you"), "bare you (p4)"), (re.compile(r"\bour\((?:INCL|EXCL)\)"), "possessive (p5)")],
    "WakelinTexts": [(atom("his", "my", "their"), "possessive (p5)"), (atom("her"), "her: object or possessive"),
                     (atom("you"), "bare you (p4)")],
    "NTUFormosanCorpus": [(atom("HE", "ME", "US"), "self-glosses, not pronouns"), (atom("I"), "I glossing a morpheme i"),
                          (re.compile("其他"), "其他 'other'"), (re.compile("我的|他的"), "possessive (p5)")],
    "ILCAA-Kanakanavu-Texts": [(atom("I"), "I glossing a morpheme i")],
    "Kavalan-Chang-Reference-Grammar": [(re.compile("我的|你的"), "possessive (p5)")],
}


@lru_cache(maxsize=None)
def standard_glosses(corpus):
    """(standard text, is residue) for every W/M standard gloss; residue = copied verbatim from the original and
    holding a parenthesis (the tool converts nothing in such a gloss)."""
    out = []
    for f in sorted((REPO / "Corpora" / corpus / "XML").rglob("*.xml")):
        for el in ET.parse(f).getroot().iter():
            if el.tag not in ("W", "M"):
                continue
            for t in el.findall("TRANSL"):
                if t.get("kindOf") != "standard":
                    continue
                s = "".join(t.itertext())
                orig = next(("".join(o.itertext()) for o in el.findall("TRANSL") if o.get("kindOf") == "original"
                             and o.get(XL) == t.get(XL) and o.get("ver") == t.get("ver")), None)
                out.append((s, s == orig and bool(re.search(r"[()（）]", s))))
    return out


@pytest.mark.parametrize("corpus", sorted(OLD))
def test_no_old_pronoun_spelling_is_left(corpus):
    left = [s for s, residue in standard_glosses(corpus) if not residue and any(p.search(s) for p in OLD[corpus])]
    assert left == [], f"{corpus}: {len(left)} standard glosses keep an old pronoun spelling, e.g. {left[:5]}"


@pytest.mark.parametrize("corpus", sorted(KEPT))
def test_ruled_exceptions_are_still_there(corpus):
    gl = [s for s, _ in standard_glosses(corpus)]
    for pat, why in KEPT[corpus]:
        assert any(pat.search(s) for s in gl), f"{corpus}: nothing left matching {pat.pattern} ({why})"
