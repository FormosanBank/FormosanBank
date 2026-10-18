"""Regression tests for the locked Thao Dictionary extraction."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))

from extract_source import payload, serialized  # noqa: E402
from pdf_text import standardize_blust  # noqa: E402


DATA_PATH = ROOT / "CodeAndDocs" / "extracted-records.json"

#: The source PDF is rights-restricted and is NOT published with the corpus
#: (POL-048 is satisfied by the committed records, not by the book). A check
#: that re-derives those records can therefore only run where someone has put
#: the PDF back, and skips everywhere else - the same rule test_source_lock.py
#: already follows.
SOURCE_PDF = ROOT / "Private" / "[OA] Thao Dictionary.pdf"


def requires_the_source(case) -> None:
    if not SOURCE_PDF.is_file():
        case.skipTest("source PDF not present; see CodeAndDocs/download_source.py")



class ExtractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.examples = {
            record["id"]: record for record in cls.data["dictionary_examples"]
        }

    def test_committed_extraction_is_reproducible(self) -> None:
        requires_the_source(self)
        self.assertEqual(DATA_PATH.read_text(encoding="utf-8"), serialized(payload()))

    def test_counts_cover_all_authorized_sections(self) -> None:
        self.assertEqual(
            self.data["statistics"],
            {
                "dictionary_examples": 8368,
                "discarded_runs": 0,
                "interlinear_words": 2531,
                "text_sentences": 166,
                "texts": 5,
                "total_sentences": 8534,
            },
        )
        self.assertEqual(
            [len(text["sentences"]) for text in self.data["texts"]],
            [8, 32, 7, 14, 105],
        )

    def test_dictionary_ids_are_unique(self) -> None:
        records = self.data["dictionary_examples"]
        self.assertEqual(len(records), len({record["id"] for record in records}))
        self.assertTrue(all(record["source"] for record in records))
        self.assertTrue(all(record["translation"] for record in records))

    def test_decoded_text_has_no_pdf_control_codes(self) -> None:
        values: list[str] = []

        def collect(value: object) -> None:
            if isinstance(value, str):
                values.append(value)
            elif isinstance(value, dict):
                for child in value.values():
                    collect(child)
            elif isinstance(value, list):
                for child in value:
                    collect(child)

        collect(self.data)
        self.assertFalse(
            any(ord(character) < 32 for value in values for character in value)
        )
        self.assertFalse(any("{" in value for value in values))
        self.assertFalse(any("\x13" in value for value in values))
        self.assertFalse(any("|" in value for value in values))
        self.assertFalse(any("\\" in value for value in values))

    def test_visual_dictionary_samples(self) -> None:
        expected = {
            "blust-dict-p0280-e002": (
                "yaku q–m–aras sa buna antu a kan–in qnuan",
                "I am fencing in the sweet potatoes so that they won't be "
                "eaten by the buffaloes",
            ),
            "blust-dict-p0280-e024": (
                "i–nay a ranaw ka–ma–p–acay–ak",
                "I killed this chicken",
            ),
            "blust-dict-p0458-e005": (
                "ya t–m–ala sa kawi pasahay–in kaul t–m–ala, ya k–un–lhit "
                "sa lhimza pasahay–in ma–bazay a kaul k–un–lhit",
                "If you cut trees use the kaul to cut, (but) if you are "
                "cutting slender miscanthus use the ma–bazay a kaul",
            ),
            "blust-dict-p0952-e004": (
                "uka sa tahamish pasay–in rukul pin–tahamish",
                "If there was no tahamish we used a rukul to serve as a "
                "tahamish",
            ),
        }
        for record_id, (source, translation) in expected.items():
            with self.subTest(record_id=record_id):
                self.assertEqual(self.examples[record_id]["source"], source)
                self.assertEqual(
                    self.examples[record_id]["translation"], translation
                )

    def test_visual_interlinear_samples(self) -> None:
        first = self.data["texts"][0]["sentences"][0]
        self.assertEqual(
            first["form"],
            "Numa ya pinudaqu iza kmalawa sa lhalhaushin, marutaw a "
            "lhalhaushin.",
        )
        self.assertEqual(
            [word["gloss"] for word in first["words"]],
            [
                "Then",
                "when",
                "finished-Pudaqu",
                "already",
                "make",
                "SA",
                "swings,",
                "tall",
                "LIG",
                "swings.",
            ],
        )
        new_year = self.data["texts"][2]["sentences"][0]
        self.assertEqual(new_year["words"][4]["gloss"], "month")
        self.assertEqual(new_year["words"][5]["gloss"], "our")

    def test_unaligned_gloss_slots_are_preserved_as_source_gaps(self) -> None:
        missing = [
            word
            for text in self.data["texts"]
            for sentence in text["sentences"]
            for word in sentence["words"]
            if word["gloss"] is None
        ]
        # 23 after the T10 italic gloss face was admitted; four of the
        # original 27 were `funfun` glossed as itself in italics.
        self.assertEqual(len(missing), 23)

    def test_printed_footnotes_reach_the_word_they_mark(self) -> None:
        notes = {
            (text["number"], sentence["number"], word["form"]): word["note"]
            for text in self.data["texts"]
            for sentence in text["sentences"]
            for word in sentence["words"]
            if "note" in word
        }
        self.assertEqual(len(notes), 5)
        self.assertEqual(
            notes[(2, 25, "funfun,")],
            "the fruit of the tree Castanopsis indica.",
        )
        self.assertEqual(notes[(4, 1, "Zintun")], "Sun-Moon Lake.")

    def test_italic_glosses_are_not_dropped(self) -> None:
        monkeys = self.data["texts"][1]
        sentence = next(s for s in monkeys["sentences"] if s["number"] == 28)
        word = next(w for w in sentence["words"] if w["form"] == "funfun.")
        self.assertEqual(word["gloss"], "funfun.")

    def test_the_replacement_page_is_read(self) -> None:
        """Printed p. 291 is typeset in Book Antiqua, not the Type 3 faces.

        Every classification in the extractor is by font name, so before
        FONT_ALIASES the page was invisible: none of its fourteen examples was
        extracted, and the record open when it began survived across it and
        absorbed the first translation on printed p. 292.
        """
        page = [
            record
            for record in self.data["dictionary_examples"]
            if record["source_printed_page"] == 291
        ]
        self.assertEqual(len(page), 14)
        self.assertEqual(page[0]["source"], "ana–i iza sa m–ihu shapa wa hulus")
        self.assertEqual(page[0]["translation"], "Give me your leather jacket")
        # The record it used to swallow into.
        self.assertEqual(
            self.examples["blust-dict-p0290-e012"]["translation"], "Give me money"
        )

    def test_nothing_is_discarded(self) -> None:
        # Both former discards are now kept: printed p. 835's translation is
        # set in the definition face and is read there, and printed p. 905's
        # "(recorded ...)" parenthetical moves to the record's source note.
        self.assertEqual(self.data["discards"], [])

    def test_a_definition_face_translation_is_read(self) -> None:
        record = self.examples["blust-dict-p0835-e006"]
        self.assertEqual(record["source"], "ani yaku ma–min–riqaz atu")
        self.assertEqual(record["translation"], "I never see the dog")

    def test_a_transcription_note_leaves_the_translation(self) -> None:
        record = self.examples["blust-dict-p0905-e019"]
        self.assertEqual(
            record["translation"],
            "Clothes lice are easy to catch (lit. Clothes lice are easy to be caught)",
        )
        self.assertEqual(
            record["source_note"],
            "(recorded with [duwan] for what I take to be shdu uan)",
        )

    def test_rendered_text_restores_three_dropped_a_words(self) -> None:
        text = self.data["texts"][4]
        expected = {66: 4, 69: 3, 95: 15}
        for sentence_number, word_index in expected.items():
            with self.subTest(sentence=sentence_number):
                sentence = next(
                    item
                    for item in text["sentences"]
                    if item["number"] == sentence_number
                )
                self.assertEqual(
                    sentence["words"][word_index],
                    {
                        "form": "`A",
                        "gloss": "`FUT" if sentence_number != 95 else "`A",
                    },
                )

    def test_source_orthography_mapping(self) -> None:
        self.assertEqual(
            standardize_blust("caw musaháy m–acay g"),
            "thaw musahay m-athay ng",
        )

    def test_source_note_is_not_admitted_as_thao(self) -> None:
        expected = {
            "blust-dict-p0431-e003": (
                "m–ihu a patash–an p–in–a–kacu itia shau–na–nay yakin",
                "(itia may also precede p–in–a–kacu)",
            ),
            "blust-dict-p0460-e009": (
                "nak a kawi pa–kawi–n suma tilha",
                "(alternatively /tilha/ may precede the rest)",
            ),
        }
        for record_id, (source, source_note) in expected.items():
            with self.subTest(record_id=record_id):
                record = self.examples[record_id]
                self.assertEqual(record["source"], source)
                self.assertEqual(record["source_note"], source_note)

    def test_source_parentheses_are_balanced(self) -> None:
        for record in self.data["dictionary_examples"]:
            with self.subTest(record_id=record["id"]):
                self.assertEqual(
                    record["source"].count("("),
                    record["source"].count(")"),
                )

    def test_custom_quote_and_dash_glyphs_match_print(self) -> None:
        quoted = self.examples["blust-dict-p0631-e008"]
        self.assertIn("“kumish”", quoted["source"])
        self.assertIn("“pubic hair”", quoted["translation"])
        dashed = self.examples["blust-dict-p0293-e015"]
        self.assertEqual(
            dashed["source"],
            "ita lhuan malh–ka–kakca a mu–tusi Qariwan—minu ihu qa min–ani",
        )


if __name__ == "__main__":
    unittest.main()
