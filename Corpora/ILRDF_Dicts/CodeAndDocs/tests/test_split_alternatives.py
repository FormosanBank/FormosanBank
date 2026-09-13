"""Source-side alternatives, resolved on the original tier.

Two treatments, per the maintainer's rulings of 2026-09-07: a spelling variant
is one record carrying FORM[@kindOf="alternate"]; a lexical alternative is
separate <S> records. Anything we cannot classify confidently is dropped and
logged rather than guessed at.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from split_alternatives import (  # noqa: E402
    classify_site,
    split_headword,
    split_record,
    stage_a,
    stage_b,
)


def texts(result):
    return None if result is None else [r.text for r in result]


def published(text):
    readings, _dropped = split_record(text)
    return [r.text for r in readings]


def dropped(text):
    _readings, drops = split_record(text)
    return drops


class TestClassifySite(unittest.TestCase):
    def test_word_count_difference_is_lexical(self):
        for options in (["tanux", "mnaw tay tanux"],
                        ["sinsiy", "sinsi pcbaq biruʼ"],
                        ["trang", "trang balay"],
                        ["qbaqi", "qbaq mhtuw"],
                        ["pqwasan", "pqwasan biruʼ"]):
            self.assertEqual(classify_site(options), "lexical", options)

    def test_close_same_length_options_are_spelling(self):
        for options in (["hiya", "hiyaʼ"], ["musa", "musaʼ"],
                        ["betunx", "baytunux"], ["ku", "kuʼ"],
                        ["taʼ", "ta"], ["turak", "turuy"],
                        ["mʼabiʼ", "mʼabi"], ["lga", "lrwa"]):
            self.assertEqual(classify_site(options), "spelling", options)

    def test_distant_same_length_options_are_not_confident(self):
        """'mʼzwi'/'mcisal' and 'tayal'/'squliq' are lexical, but nothing
        separates them from an unrecognised spelling pair, so we decline."""
        for options in (["mʼzwi", "mcisal"], ["tayal", "squliq"]):
            self.assertIsNone(classify_site(options), options)

    def test_an_unbalanced_option_is_declined(self):
        """A bracketed option is unwrapped by _options; anything still
        carrying a stray bracket is malformed and we decline it."""
        self.assertIsNone(classify_site(["qinlwaxan", "(qwalax qinlwaxan"]))
        self.assertIsNone(classify_site(["kinbahan", "laqi kneril na laqi）"]))


class TestStageA(unittest.TestCase):
    def test_numbered_multi_example(self):
        self.assertEqual(
            stage_a("1. cyux su maniq bway nanu? 2. cyux suʼ maniq bway nanuʼ?"),
            ["cyux su maniq bway nanu?", "cyux suʼ maniq bway nanuʼ?"])

    def test_numbered_without_spaces(self):
        self.assertEqual(
            stage_a("1.bengun nya qbaʼ ni yaki. 2.cyux meng qbaʼ na yaki hya."),
            ["bengun nya qbaʼ ni yaki.", "cyux meng qbaʼ na yaki hya."])

    def test_a_sentence_final_numeral_is_not_a_marker(self):
        text = "Gnblung mu phnang ptucing ka btunux o 3."
        self.assertEqual(stage_a(text), [text])

    def test_markers_must_run_from_one(self):
        text = "2.yutas ga nyux gmulaq lbit qhuniq tatak qasa."
        self.assertEqual(stage_a(text), [text])

    def test_stray_leading_marker_is_dropped_not_split(self):
        self.assertEqual(stage_a("1.cyux mxal tariʼ nya."),
                         ["cyux mxal tariʼ nya."])

    def test_sentence_final_slash(self):
        self.assertEqual(
            stage_a("Ini iyah na./Mnarig ka patas bgay mu laqi na"),
            ["Ini iyah na.", "Mnarig ka patas bgay mu laqi na"])

    def test_bracketed_phrase_substitutes_into_the_frame(self):
        self.assertEqual(
            stage_a("cyux szwi na (krahu bayhuy) / (hopa na behuy) qu qhuniq."),
            ["cyux szwi na krahu bayhuy qu qhuniq.",
             "cyux szwi na hopa na behuy qu qhuniq."])


class TestSpellingVariants(unittest.TestCase):
    def test_one_record_carrying_an_alternate(self):
        result = stage_b("cyux mʼabiʼ / mʼabi qu yutas.")
        self.assertEqual(texts(result), ["cyux mʼabiʼ qu yutas."])
        self.assertEqual(result[0].alternates, ["cyux mʼabi qu yutas."])

    def test_three_close_spellings_give_two_alternates(self):
        result = stage_b("cyux inuʼ qu lukus maku / makuʼ / makw?")
        self.assertEqual(texts(result), ["cyux inuʼ qu lukus maku?"])
        self.assertEqual(len(result[0].alternates), 2)

    def test_a_short_outlier_declines_the_whole_site(self):
        """'makuʼ / maku / mu' -- 'mu' is far from the others, so we are not
        confident the site is a single word spelled three ways."""
        self.assertIsNone(stage_b("cyux inuʼ qu lukus makuʼ / maku / mu?"))

    def test_several_spelling_sites_stay_one_record(self):
        """Co-varying spellings must not become a cartesian product."""
        result = stage_b("ana ku / kuʼ musa / musaʼ mzwi taʼ / ta tanux.")
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].alternates), 1)


class TestLexicalAlternatives(unittest.TestCase):
    def test_two_records(self):
        self.assertEqual(
            texts(stage_b("cyux trang / (trang balay) mʼabiʼ qu yutas.")),
            ["cyux trang mʼabiʼ qu yutas.",
             "cyux trang balay mʼabiʼ qu yutas."])

    def test_lexical_multiplies_records_and_spelling_does_not(self):
        result = stage_b("ana ku / kuʼ musa tanux / (mnaw tay tanux) la.")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(r.alternates for r in result))

    def test_too_many_lexical_combinations_is_declined(self):
        self.assertIsNone(stage_b(
            "a / (bb cc) dd / (ee ff) gg / (hh ii) jj / (kk ll)."))


class TestFragmentIndependence(unittest.TestCase):
    def test_an_unreadable_example_does_not_kill_its_sibling(self):
        """A fragment we cannot classify is dropped; its siblings publish."""
        text = ("1.cyux mʼzwi / mcisal qu yutas. "
                "2.kinbahan suʼ knayril qani ga?")
        self.assertEqual(published(text), ["kinbahan suʼ knayril qani ga?"])
        self.assertEqual(len(dropped(text)), 1)

    def test_an_unanchored_phrase_alternative_is_declined(self):
        """Maintainer ruling 3. 'laqi kneril na laqi' shares no word with
        'kinbahan', so the span it replaces is a guess -- it could be
        'kinbahan' or 'kinbahan suʼ'. Decline; the sibling still publishes."""
        text = ("1.qani qu kinbahan / （laqi kneril na laqi） suʼ ga? "
                "2.kinbahan suʼ knayril qani ga?")
        self.assertEqual(published(text), ["kinbahan suʼ knayril qani ga?"])
        self.assertEqual(len(dropped(text)), 1)

    def test_both_examples_publish_when_both_resolve(self):
        text = "1.bengun nya qbaʼ ni yaki. 2.cyux meng qbaʼ na yaki hya."
        self.assertEqual(len(published(text)), 2)
        self.assertEqual(dropped(text), [])


class TestHeadwords(unittest.TestCase):
    """A headword differs from a sentence in one way: the whole field is the
    item, so nothing is ambiguous about what an alternative substitutes for.
    A headword is therefore never deleted merely for carrying a slash."""

    def test_dissimilar_forms_become_separate_entries(self):
        readings, dropped = split_headword("kmut/smʼung")
        self.assertEqual([r.text for r in readings], ["kmut", "smʼung"])
        self.assertEqual(dropped, [])

    def test_similar_forms_become_one_entry_with_an_alternate(self):
        readings, _ = split_headword("matepa^/matama")
        self.assertEqual([r.text for r in readings], ["matepa^"])
        self.assertEqual(readings[0].alternates, ["matama"])

    def test_a_spaced_trailing_bracket_is_a_second_form(self):
        readings, _ = split_headword("masʉecʉ (tʼocngoyx)")
        self.assertEqual([r.text for r in readings], ["masʉecʉ", "tʼocngoyx"])

    def test_an_attached_bracket_is_the_append_idiom_and_is_declined(self):
        """'uculru(wa)' means uculru/uculruwa; 'wa' is not an entry."""
        readings, dropped = split_headword("uculru(wa)")
        self.assertEqual(readings, [])
        self.assertEqual(dropped, ["uculru(wa)"])

    def test_annotation_is_retained(self):
        readings, _ = split_headword("chaicxngpu (音譯)")
        self.assertEqual([r.text for r in readings], ["chaicxngpu (音譯)"])


class TestEquals(unittest.TestCase):
    def test_trailing_variant(self):
        self.assertEqual(
            published("ata tu kmaanasapunuqi! = ata tu kmasapunuqi!"),
            ["ata tu kmaanasapunuqi!", "ata tu kmasapunuqi!"])

    def test_inline_parenthetical_variant(self):
        self.assertEqual(
            published("lhmazawan mabrith, mingqarayza makitzangqaw (= katzangqaw)."),
            ["lhmazawan mabrith, mingqarayza makitzangqaw.",
             "lhmazawan mabrith, mingqarayza katzangqaw."])


class TestInvariants(unittest.TestCase):
    def test_no_delimiter_survives(self):
        for text in ("hatomi^/foliki^ han ako.",
                     "cyux szwi na (krahu bayhuy) / (hopa na behuy) qu qhuniq.",
                     "ata tu kmaanasapunuqi! = ata tu kmasapunuqi!"):
            for out in published(text):
                self.assertNotIn("/", out, text)
                self.assertNotIn("=", out, text)

    def test_bracketed_options_are_unwrapped_not_left_dangling(self):
        for text in ("tnaq balay qinlwaxan / (qwalax qinlwaxan) nya la.",
                     "cyux szwi na (krahu bayhuy) / (hopa na behuy) qu qhuniq.",
                     "1.aw, (ʼsay taʼ kya) / (ungat htyalan nya) 2.aw. baqun."):
            for out in published(text):
                self.assertEqual(out.count("("), out.count(")"),
                                 f"{text} -> {out}")

    def test_plain_record_passes_through_unchanged(self):
        self.assertEqual(published("maan cu ku tavarʉʼʉ."),
                         ["maan cu ku tavarʉʼʉ."])

    def test_idempotent(self):
        for reading in published("hatomi^/foliki^ han ako."):
            self.assertEqual(published(reading), [reading])


if __name__ == "__main__":
    unittest.main()
