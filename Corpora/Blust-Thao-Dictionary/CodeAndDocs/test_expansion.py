"""Regression tests for policy-required source-notation expansion."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))

from expand_source import (  # noqa: E402
    expand_optional,
    payload,
    serialized,
    word_internal_variants,
)


DATA_PATH = ROOT / "CodeAndDocs" / "expanded-records.json"
RAW_PATH = ROOT / "CodeAndDocs" / "extracted-records.json"
SLASH_PATH = ROOT / "CodeAndDocs" / "slash-alternatives.json"

#: The source PDF is rights-restricted and is NOT published with the corpus
#: (POL-048 is satisfied by the committed records, not by the book). A check
#: that re-derives those records can therefore only run where someone has put
#: the PDF back, and skips everywhere else - the same rule test_source_lock.py
#: already follows.
SOURCE_PDF = ROOT / "Private" / "[OA] Thao Dictionary.pdf"


def requires_the_source(case) -> None:
    if not SOURCE_PDF.is_file():
        case.skipTest("source PDF not present; see CodeAndDocs/download_source.py")



class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
        cls.slash_map = json.loads(SLASH_PATH.read_text(encoding="utf-8"))
        cls.examples = cls.data["dictionary_examples"]

    def records_for(self, source_record_id: str) -> list[dict[str, object]]:
        return [
            record
            for record in self.examples
            if record["source_record_id"] == source_record_id
        ]

    def test_committed_expansion_is_reproducible(self) -> None:
        requires_the_source(self)
        self.assertEqual(DATA_PATH.read_text(encoding="utf-8"), serialized(payload()))

    def test_expanded_counts(self) -> None:
        self.assertEqual(
            self.data["statistics"],
            {
                "expanded_dictionary_sentences": 8630,
                "expanded_interlinear_words": 2542,
                "expanded_text_sentences": 167,
                "optional_dictionary_source_records": 179,
                "raw_dictionary_examples": 8368,
                "raw_text_sentences": 166,
                "slash_source_records": 93,
                "total_sentences": 8797,
            },
        )

    def test_slash_inventory_exactly_covers_raw_source(self) -> None:
        raw_ids = {
            record["id"]
            for record in self.raw["dictionary_examples"]
            if "/" in record["source"]
        }
        self.assertEqual(raw_ids, set(self.slash_map))
        self.assertTrue(
            all(
                "/" not in variant
                for variants in self.slash_map.values()
                for variant in variants
            )
        )

    def test_expanded_source_ids_and_forms_are_valid(self) -> None:
        ids = [record["id"] for record in self.examples]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(
            any(
                marker in record["source"]
                for record in self.examples
                for marker in "()/"
            )
        )

    def test_a_bracket_inside_a_word_is_not_an_expansion(self) -> None:
        """It is one lexeme spelt two ways, so it stays one sentence.

        `(manu)-manu` and `ihu-(n)` used to become two S each. They are now one
        S with a ver="alt" FORM (POL-028), and the boundary marker goes with
        the material it belonged to: `(k)-m-alhus` gives `m-alhus`, not
        `-m-alhus` (maintainer, 2026-09-11).
        """
        for printed in ("(manu)–manu", "ihu–(n)", "(k)–m–alhus"):
            self.assertEqual(
                [form for form, _labels in expand_optional(printed)], [printed]
            )
        self.assertEqual(word_internal_variants("(manu)–manu"), ("manu", "manu–manu"))
        self.assertEqual(word_internal_variants("ihu–(n)"), ("ihu", "ihu–n"))
        self.assertEqual(word_internal_variants("(k)–m–alhus"), ("m–alhus", "k–m–alhus"))

    def test_optional_boundary_normalization(self) -> None:
        self.assertEqual(
            [form for form, _labels in expand_optional("ata (tu) m–asay cicu")],
            ["ata m–asay cicu", "ata tu m–asay cicu"],
        )
        self.assertEqual(
            [form for form, _labels in expand_optional("ata (sa) apiq")],
            ["ata apiq", "ata sa apiq"],
        )

    def test_text_optional_word_preserves_alignment(self) -> None:
        variants = self.data["texts"][4]["sentences"][:2]
        self.assertEqual(
            [variant["variant_suffix"] for variant in variants],
            ["opt01out", "opt01in"],
        )
        self.assertNotIn("tu", [word["form"] for word in variants[0]["words"]])
        included = [
            word for word in variants[1]["words"] if word["form"] == "tu"
        ]
        self.assertEqual(included, [{"form": "tu", "gloss": "TU"}])
        self.assertEqual(
            variants[1]["form"],
            " ".join(word["form"] for word in variants[1]["words"]),
        )

    def test_mixed_slash_and_optional_expansion(self) -> None:
        records = self.records_for("blust-dict-p0321-e008")
        self.assertEqual(
            [(record["id"], record["source"]) for record in records],
            [
                (
                    "blust-dict-p0321-e008-alt01-opt01out",
                    "t–m–u–barumbun qali",
                ),
                (
                    "blust-dict-p0321-e008-alt01-opt01in",
                    "t–m–u–barumbun iza sa qali",
                ),
                ("blust-dict-p0321-e008-alt02", "qali t–m–u–barumbun"),
            ],
        )

    def test_multiple_optional_expansion(self) -> None:
        records = self.records_for("blust-dict-p0635-e003")
        self.assertEqual(len(records), 4)
        self.assertEqual(
            {record["source"] for record in records},
            {
                "ma–cuaw ma–nasha tuali",
                "ma–cuaw ma–nasha a tuali",
                "ma–cuaw a ma–nasha tuali",
                "ma–cuaw a ma–nasha a tuali",
            },
        )

    def test_maintainer_ruled_slash_scopes(self) -> None:
        """The eight scopes the maintainer ruled on, 2026-09-10.

        Seven were mis-split the same way: the alternation is one word and the
        material around it is shared, but the curation cut the sentence at the
        slash and left the trailing words with only one reading. The eighth,
        blust-dict-p0881-e009, is the maintainer correcting the auditor rather
        than the curation - the alternation is `taun` / `mapa-ki-bariz` with
        `nam a` shared.

        This replaces test_visually_reviewed_slash_scopes, which enshrined two
        of these as reviewed and correct. The same eight are covered on the
        FormosanBank side by tests/utilities/test_slash_alternative_rulings.py,
        which asserts that QC/utilities/slash_alternatives.py reproduces each
        ruling from the printed source without the curation file.
        """
        expected = {
            "blust-dict-p0446-e019": {
                "kukulay i–say bukhaz kan qca–i ihu",
                "kukulay i–say bukhaz kan p–acay–i ihu",
            },
            "blust-dict-p0727-e001": {
                "ma–pitu–'un iza nak a qamishan",
                "ma–pitu–'un iza yaku a qamishan",
            },
            "blust-dict-p0822-e005": {
                "yaku m–rucu sa lhparishan, t–m–ali–raput",
                "yaku panaq sa lhparishan, t–m–ali–raput",
            },
            "blust-dict-p0848-e005": {
                "yaku a ma–kan fizfiz m–ruqit shapa",
                "yaku a ma–kan bailu m–ruqit shapa",
            },
            "blust-dict-p0881-e009": {
                "tilha mu–nay a shput kahiwan m–in–ia–sun nam a taun",
                "tilha mu–nay a shput kahiwan m–in–ia–sun nam a mapa–ki–bariz",
            },
            "blust-dict-p0924-e006": {
                "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw "
                "cicu a punuq, numa ya pin–shkash–in ita kun–na–tmaz cicu a punuq",
                "balinuqaz ya q–in–usaz iza i–say ma–braq muqay mu–apaw "
                "cicu a punuq, numa ya pin–shkash–in ita pish–na–tmaz cicu a punuq",
            },
            "blust-dict-p0925-e005": {
                "nak a kuskus lh–m–im–bakbak, shlaup iza",
                "nak a kuskus lh–m–im–bakbak, pish–qitan iza",
            },
            "blust-dict-p0996-e003": {
                "fukish ya ma–pulha–pulhash tiuz–an maní",
                "fukish ya ma–pulha–pulhash tiuz–i maní",
            },
            "blust-dict-p1027-e009": {
                "pin–tusha sa i–nay ma–dahun, lhay tata wa magkaci suma",
                "pin–tusha sa i–nay ma–dahun, lhay tata wa qbit suma",
            },
        }
        for record_id, forms in expected.items():
            with self.subTest(record_id=record_id):
                self.assertEqual(
                    {record["source"] for record in self.records_for(record_id)},
                    forms,
                )

    def test_source_note_is_not_expanded_as_form(self) -> None:
        records = self.records_for("blust-dict-p0431-e003")
        self.assertEqual(len(records), 1)
        self.assertEqual(
            records[0]["source_note"],
            "(itia may also precede p–in–a–kacu)",
        )


if __name__ == "__main__":
    unittest.main()
