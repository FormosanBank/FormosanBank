"""Source-side alternatives become separate <S> records.

The ILRDF source packs alternative wordings into one record three ways: '='
("same as"), parentheses, and slashes. Each distinct option becomes its own
record, resolved on the ORIGINAL tier before clean_xml and standardize.
Anything the cascade cannot interpret is deleted rather than guessed at.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from split_alternatives import (  # noqa: E402
    split_record,
    stage_a,
    stage_b,
)


class TestStageA(unittest.TestCase):
    """Sentence-level: one record holding more than one sentence."""

    def test_numbered_multi_example(self):
        self.assertEqual(
            stage_a("1. cyux su maniq bway nanu? 2. cyux suʼ maniq bway nanuʼ?"),
            ["cyux su maniq bway nanu?", "cyux suʼ maniq bway nanuʼ?"])

    def test_numbered_without_spaces(self):
        self.assertEqual(
            stage_a("1.bengun nya qbaʼ ni yaki. 2.cyux meng qbaʼ na yaki hya."),
            ["bengun nya qbaʼ ni yaki.", "cyux meng qbaʼ na yaki hya."])

    def test_three_numbered_parts(self):
        self.assertEqual(
            stage_a("1.musa ku maniq mami la. 2.mosa ku maniq mami la. "
                    "3.musaʼ sakuʼ maniq mamiʼ la."),
            ["musa ku maniq mami la.", "mosa ku maniq mami la.",
             "musaʼ sakuʼ maniq mamiʼ la."])

    def test_a_sentence_final_numeral_is_not_a_marker(self):
        """'... o 3.' is the number three, not example marker 3."""
        for text in ("Gnblung mu phnang ptucing ka btunux o 3.",
                     "Hnhdhik dha ga, qbhangan o mn 2.",
                     "Pphungul na plpax knan ka pdahik o 7."):
            self.assertEqual(stage_a(text), [text])

    def test_markers_must_run_from_one(self):
        """A record starting at '2.' is irregular -- leave it for a human."""
        text = "2.yutas ga nyux gmulaq lbit qhuniq tatak qasa."
        self.assertEqual(stage_a(text), [text])

    def test_stray_leading_marker_is_not_a_split(self):
        """A lone '1.' with no '2.' is a marker to drop, not a boundary."""
        self.assertEqual(stage_a("1.cyux mxal tariʼ nya."), ["cyux mxal tariʼ nya."])

    def test_sentence_final_slash(self):
        self.assertEqual(
            stage_a("Ini iyah na./Mnarig ka patas bgay mu laqi na"),
            ["Ini iyah na.", "Mnarig ka patas bgay mu laqi na"])

    def test_bracketed_phrase_substitutes_into_the_frame(self):
        self.assertEqual(
            stage_a("cyux szwi na (krahu bayhuy) / (hopa na behuy) qu qhuniq."),
            ["cyux szwi na krahu bayhuy qu qhuniq.",
             "cyux szwi na hopa na behuy qu qhuniq."])

    def test_three_bracketed_options(self):
        self.assertEqual(len(stage_a(
            "(nanu zywaw su soni) / (kmnswa su ryax) / (mswaʼ suʼ sawniʼ) ga.")), 3)

    def test_plain_sentence_is_one_fragment(self):
        self.assertEqual(stage_a("hatomi^ han ako."), ["hatomi^ han ako."])


class TestStageB(unittest.TestCase):
    """Word-level: one record holding one sentence with lexical options."""

    def test_two_options(self):
        self.assertEqual(
            stage_b("hatomi^/foliki^ han ako ko paliding."),
            ["hatomi^ han ako ko paliding.", "foliki^ han ako ko paliding."])

    def test_spaced_slash(self):
        self.assertEqual(
            stage_b("bleqi balay tblaq mitaʼ / mangay."),
            ["bleqi balay tblaq mitaʼ.", "bleqi balay tblaq mangay."])

    def test_three_similar_options(self):
        self.assertEqual(
            stage_b("cyux inuʼ qu lukus makuʼ / maku / mu?"),
            ["cyux inuʼ qu lukus makuʼ?", "cyux inuʼ qu lukus maku?",
             "cyux inuʼ qu lukus mu?"])

    def test_two_sites_is_uninterpretable(self):
        self.assertIsNone(stage_b(
            "ana cipuq/cipoq pila gitan lga, musa pzyux/piyux nanak la."))

    def test_n_way_dissimilar_is_uninterpretable(self):
        self.assertIsNone(stage_b("mutux klayun snyu / snyuw / gasil ru rmugan."))

    def test_two_dissimilar_options_still_split(self):
        """Two options need no similarity evidence; three or more do."""
        self.assertEqual(
            stage_b("ani saku magal kagaw/sapuh ha."),
            ["ani saku magal kagaw ha.", "ani saku magal sapuh ha."])

    def test_dangling_slash_is_uninterpretable(self):
        self.assertIsNone(stage_b("Kadrua ku abaadhane ku kazilu ki pangudaane/"))

    def test_no_slash_is_a_single_reading(self):
        self.assertEqual(stage_b("hatomi^ han ako."), ["hatomi^ han ako."])


class TestEquals(unittest.TestCase):
    """'=' is the source's 'same as' notation, not a null marker."""

    def test_trailing_variant(self):
        self.assertEqual(
            split_record("ata tu kmaanasapunuqi! = ata tu kmasapunuqi!"),
            ["ata tu kmaanasapunuqi!", "ata tu kmasapunuqi!"])

    def test_inline_parenthetical_variant(self):
        self.assertEqual(
            split_record("lhmazawan mabrith, mingqarayza makitzangqaw (= katzangqaw)."),
            ["lhmazawan mabrith, mingqarayza makitzangqaw.",
             "lhmazawan mabrith, mingqarayza katzangqaw."])


class TestInvariants(unittest.TestCase):
    def test_no_delimiter_survives_a_split(self):
        for text in ("hatomi^/foliki^ han ako.",
                     "cyux szwi na (krahu bayhuy) / (hopa na behuy) qu qhuniq.",
                     "ata tu kmaanasapunuqi! = ata tu kmasapunuqi!"):
            for out in split_record(text) or []:
                self.assertNotIn("/", out, text)
                self.assertNotIn("=", out, text)

    def test_readings_are_distinct(self):
        out = split_record("hatomi^/foliki^ han ako.")
        self.assertEqual(len(out), len(set(out)))

    def test_idempotent(self):
        once = split_record("hatomi^/foliki^ han ako.")
        for reading in once:
            self.assertEqual(split_record(reading), [reading])

    def test_never_returns_an_empty_reading(self):
        for text in ("hatomi^/foliki^ han ako.",
                     "1. a bcd. 2. e fgh."):
            for out in split_record(text) or []:
                self.assertTrue(out.strip())

    def test_plain_record_passes_through_unchanged(self):
        self.assertEqual(split_record("maan cu ku tavarʉʼʉ."),
                         ["maan cu ku tavarʉʼʉ."])


if __name__ == "__main__":
    unittest.main()
