"""The entry schema's classification rules, as the maintainer ruled them.

The question that produced this file (2026-09-10): are there unambiguous bound
roots -- ones followed by numbered sub-entries starting at 2 -- that are neither
surrounded by bars nor followed by a (PAN *...) etymology?  There are.  Blust
writes a root header three ways and the bars are the least common denominator,
not the marker:

    |acay| (PAN *aCay `die, dead'):        bars + etymology       8
    |ailhi| (PAN *wiRi `left side'):       bars                 519
    kuza (PAN *kuja `how?'):               etymology only         4
    antua:                                 neither               30

What all four share is a header that ends in a colon and defines nothing.  That
is the test.  "Numbering starts at 2" is not: Matansún: runs 1a, 1b.
"""

import json
import re
import unittest
from pathlib import Path

RECORDS = Path(__file__).resolve().parent / "entry-records.json"


class TestRootHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        entries = json.loads(RECORDS.read_text(encoding="utf-8"))["entries"]
        cls.by_key = {(e["headword"], e["printed_page"]): e for e in entries}
        cls.entries = entries

    def entry(self, headword, page):
        if (headword, page) not in self.by_key:
            near = sorted(h for h, p in self.by_key if h.startswith(headword[:4]))
            self.fail(f"{headword} p.{page} is gone; nearby headwords: {near[:6]}")
        return self.by_key[(headword, page)]

    def test_bars_are_a_root(self):
        for headword, page in [("acay", 280), ("ailhi", 286)]:
            e = self.entry(headword, page)
            self.assertEqual(e["format"], "B")
            self.assertEqual(e["root_marker"], "bars")

    def test_colon_with_an_etymology_and_no_bars_is_a_root(self):
        for headword, page in [("kuza", 504), ("pshiq", 731), ("tutu", 1029),
                               ("ziwan", 1065)]:
            e = self.entry(headword, page)
            self.assertEqual(e["format"], "B", headword)
            self.assertEqual(e["root_marker"], "colon", headword)
            self.assertTrue(e["etymology"], headword)

    def test_a_bare_colon_is_a_root(self):
        # The maintainer's question exactly: neither bars nor (PAN *...).
        for headword, page in [("antua", 296), ("qtit", 806), ("dishlum", 364),
                               ("palhaza", 661), ("untikuy", 1041)]:
            e = self.entry(headword, page)
            self.assertEqual(e["format"], "B", headword)
            self.assertEqual(e["root_marker"], "colon", headword)
            self.assertIsNone(e["etymology"], headword)

    def test_no_root_keeps_the_colon_as_a_sense(self):
        # The colon leaves behind a sense whose definition is punctuation and
        # nothing else.  Every root drops it, however its header was marked.
        # (A root whose first definition is *empty* is a different defect -
        # all barred, all already carrying S03 and S04.)
        kept = []
        for e in self.entries:
            if e["root_marker"] is None or not e["senses"]:
                continue
            definition = e["senses"][0]["definition"].strip()
            if definition and not re.search(r"\w", definition):
                kept.append((e["headword"], e["printed_page"]))
        # None survives. puqnur p.748 and tilhush p.989 used to, because Blust
        # prints an example directly under their header and the drop required
        # the whole sense to be empty - so the colon stood as the definition and
        # the entry read as a bound root with a sense of its own (maintainer,
        # 2026-09-11). The root test now looks at the definition alone, and a
        # header sense that carries only an example keeps its example and loses
        # the colon.
        self.assertEqual(kept, [], kept)

    def test_a_root_header_may_carry_an_example(self):
        """Blust prints an illustration directly under a bound-root header:

            |puqnur|:
              cicu a punuq itia tusha wa puqnur  He has two bumps on his head
            2 lhum-puqnur  swelling or bump ...

        The sense has no definition, which is what makes it a root header, but
        it does have a sentence - and that sentence is Thao with a translation
        whatever the line above it is. Ten of them in eight entries were being
        dropped from the XML in silence.
        """
        carried = [
            (e["headword"], e["printed_page"], len(e["senses"][0]["examples"]))
            for e in self.entries
            if e["root_marker"] and e["senses"]
            and e["senses"][0]["number"] is None
            and e["senses"][0]["examples"]
        ]
        self.assertEqual(sum(n for _h, _p, n in carried), 10, carried)
        self.assertEqual(len(carried), 8, carried)
        for _head, _page, n in carried:
            self.assertGreater(n, 0)

    def test_starting_at_two_is_not_the_marker(self):
        # Matansún: is marked exactly like the others and runs 1a, 1b.
        e = self.entry("Matansún", 595)
        self.assertEqual(e["root_marker"], "colon")
        self.assertEqual(e["senses"][0]["number"], 1)
        self.assertEqual(e["senses"][0]["subsense"], "a")

    def test_a_form_at_the_margin_opens_its_own_entry(self):
        """The third block opener (maintainer, 2026-09-10).

        A derived form set in the sub-entry face and sitting AT the column
        margin, with no sense number in front of it, is an index entry
        pointing at the entry that treats it - not a sub-entry of whatever
        entry happens to be open.  Reading them as sub-entries absorbed 148
        forms into klhiw, 137 into manu and 77 into mismis.
        """
        for headword, page, definition, target in [
            ("an–sun–in", 294, "be gathered in a place", "sun:2"),
            ("an–suriz–in", 294, "be spilled", "suriz:2"),
            ("a–ntua–k", 296, "I will take it somewhere", "ntua:3"),
        ]:
            entry = self.entry(headword, page)
            self.assertEqual(entry["senses"][0]["definition"], definition)
            self.assertEqual(entry["senses"][0]["cross_references"], [target])

    def test_the_entries_that_had_swallowed_their_neighbours(self):
        for headword, page, most in [("klhiw", 478, 4), ("manu", 577, 4),
                                     ("mismis", 621, 4), ("ansinis", 294, 6)]:
            entry = self.entry(headword, page)
            self.assertLessEqual(len(entry["senses"]), most, headword)

    def test_no_entry_absorbs_a_long_run_of_unnumbered_senses(self):
        # S09's invariant, asserted directly on the records.
        for e in self.entries:
            run = worst = 0
            for sense in e["senses"]:
                run = 0 if sense["number"] is not None else run + 1
                worst = max(worst, run)
            self.assertLessEqual(
                worst, 3, f"{e['headword']} p.{e['printed_page']} has a run of {worst}")

    def test_the_stress_acute_stays_on_its_vowel(self):
        """PyMuPDF draws Blust's acute as its own span, sitting ON its vowel.

        The overlay's x-range falls INSIDE the base span's, which defeats every
        gap measurement downstream: the headword closed early and the accent
        was routed into the definition.  139 fields lost it and 59 headwords
        were truncated at it.  Reordering is not enough - `Alis` is one span,
        so the overlay has to go INSIDE it, at the character its x0 lands on.
        """
        for headword, page in [("Matansún", 595), ("Alisán", 288), ("Anáy", 293),
                               ("baksán", 315), ("falhán", 372), ("ananá", 292)]:
            self.entry(headword, page)

    def test_no_field_keeps_a_homeless_accent(self):
        stray = [
            (e["headword"], e["printed_page"], field)
            for e in self.entries
            for field, value in
            [("headword", e["headword"]), ("etymology", e["etymology"])]
            + [(f, v) for s in e["senses"]
               for f, v in [("definition", s["definition"]), ("form", s["form"])]]
            if value and "\x13" in value
        ]
        # None may remain. 0x13 is not a legal XML character, so one surviving
        # here stops the whole build at clean_xml with a parse error.
        self.assertEqual(stray, [], stray[:5])

    def test_the_linnean_authority_is_gone(self):
        for e in self.entries:
            for sense in e["senses"]:
                self.assertNotRegex(sense["definition"] or "", r"\((?:Linn\.|L\.)\)")

    def test_a_free_word_is_not_a_root(self):
        for headword, page in [("a", 280), ("hala", 395)]:
            self.assertIn((headword, page), self.by_key)
        self.assertIsNone(self.entry("a", 280)["root_marker"])


if __name__ == "__main__":
    unittest.main()
