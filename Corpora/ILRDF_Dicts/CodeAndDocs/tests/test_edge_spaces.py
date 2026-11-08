"""Maintainer ruling 2026-10-18: no ILRDF PHON has an outer space; the
original tier loses the space next to punctuation at its start/end."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tidy_edge_spaces import tidy

XML_DIR = Path(__file__).resolve().parents[2] / "XML"


class TestTidy(unittest.TestCase):
    def test_ruled_examples(self):
        cases = {
            "fafahiyan ako .": ("fafahiyan ako.", ["final"]),
            "Ini huya wah ! .": ("Ini huya wah!.", ["final"]),
            ". Aiza bunun masuaz.": ("Aiza bunun masuaz.", ["leading_dot"]),
            ".Ansahanava tapaa": ("Ansahanava tapaa", ["leading_dot"]),
            '" Dopohen a matayal!" saan.': ('"Dopohen a matayal!" saan.', ["open"]),
            "a zaljum ( vava ).": ("a zaljum (vava).", ["bracket"]),
            "Pistus huma'an mas ismut ,": ("Pistus huma'an mas ismut,", ["close"]),
            "caca -": ("caca-", ["close"]),
            "teyrahem no …": ("teyrahem no…", ["close"]),
            'kaa-in cinhuz-a. "': ('kaa-in cinhuz-a."', ["close"]),
        }
        for before, expected in cases.items():
            self.assertEqual(tidy(before), (expected[0], expected[1]), before)

    def test_inner_text_untouched(self):
        for text in ['"mekan mu lra? " " aiwa', "sa mihu? ( minu qa sa mihu?)",
                     "ira ko cecay , a tamohong.", "'una pa"]:
            self.assertEqual(tidy(text)[1], [], text)


@unittest.skipUnless((XML_DIR / "Amis" / "Amis.xml").exists(), "built XML not present")
class TestBuiltPhon(unittest.TestCase):
    def test_no_phon_has_an_outer_space(self):
        bad = []
        for path in sorted(XML_DIR.glob("*/*.xml")):
            for phon in ET.parse(path).getroot().iter("PHON"):
                text = phon.text or ""
                if text != text.strip():
                    bad.append(f"{path.name}: {text!r}")
        self.assertEqual(bad[:20], [])
        self.assertEqual(len(bad), 0)
