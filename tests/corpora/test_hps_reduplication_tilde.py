"""HundredPaiwanStories: '~' separates a reduplicated syllable from its stem in the standard gloss tier, so the source's
red~stem converts like red elsewhere (maintainer 2026-11-27, HPS gloss abbreviations page JmCfWcQZsGwM2UE9KXM1dL,
card b1: "Apply, tests first"; Leipzig Rule 10 writes reduplication with '~'). Written before the change."""
import re
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
XL = "{http://www.w3.org/XML/1998/namespace}lang"


def glosses():
    out = []
    for f in sorted((REPO / "Corpora/HundredPaiwanStories/XML").rglob("*.xml")):
        for el in ET.parse(f).getroot().iter():
            if el.tag in ("W", "M"):
                std = [t for t in el.findall("TRANSL") if t.get("kindOf") == "standard"]
                orig = {t.get(XL): "".join(t.itertext()) for t in el.findall("TRANSL") if t.get("kindOf") == "original"}
                for t in std:
                    s = "".join(t.itertext())
                    out.append((s, s == orig.get(t.get(XL)) and bool(re.search(r"[()]", s))))
    return out


def test_no_lowercase_red_joined_by_tilde_is_left():
    left = [s for s, residue in glosses() if not residue and re.search(r"(?:^|[.\-=<>\s~])red~", s)]
    assert left == [], f"{len(left)} standard glosses keep red~, e.g. {left[:5]}"


def test_tilde_stays_in_the_standard_tier():
    assert any("RED~" in s for s, _ in glosses())          # Leipzig Rule 10: the ~ is kept, only the code converts
