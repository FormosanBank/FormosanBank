from __future__ import annotations

import csv
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))

import build_lexical_xml as build  # noqa: E402

_BANK = ROOT.parents[1]
if str(_BANK) not in sys.path:
    sys.path.insert(0, str(_BANK))
from QC.xml_forms import base_form_text  # noqa: E402


SOURCE_CHECKS = ROOT / "CodeAndDocs" / "source_checks.tsv"
REVIEWER_FEEDBACK = ROOT / "CodeAndDocs" / "reviewer_feedback.tsv"


class SourceLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = build.load_ledger()
        cls.included = build.included_entries(cls.ledger)
        cls.sentences: dict[str, ET.Element] = {}
        for path in sorted((ROOT / "XML").rglob("*.xml")):
            root = ET.parse(path).getroot()
            for sentence in root.findall("S"):
                record_id = sentence.get("id", "")
                if not record_id or record_id in cls.sentences:
                    raise AssertionError(f"Duplicate or empty S ID: {record_id}")
                cls.sentences[record_id] = sentence

    def test_source_ledger_has_complete_target_grid(self) -> None:
        self.assertEqual(len(self.ledger), 64)
        # The Gabelentz "Sida" column -- 22 occupied cells and 2 dashes --
        # is excluded rather than deleted: the ledger still records every
        # cell of the printed grid, and says why each is not published.
        self.assertEqual(len(self.included), 40)
        self.assertEqual(
            Counter(entry.status for entry in self.ledger),
            Counter({"included": 40, "excluded_unidentified_variety": 24}),
        )
        self.assertEqual(
            Counter(entry.printed_page for entry in self.ledger),
            Counter({"315": 16, "316": 16, "317": 16, "318": 16}),
        )
        self.assertEqual(
            Counter(entry.pdf_page for entry in self.ledger),
            Counter({"2": 16, "3": 16, "4": 16, "5": 16}),
        )

    def test_every_included_source_cell_matches_xml_exactly(self) -> None:
        records = build.xml_entries(self.included)
        self.assertEqual(
            {entry.s_id for entry in records},
            set(self.sentences),
        )
        for entry in records:
            sentence = self.sentences[entry.s_id]
            self.assertEqual(
                base_form_text(sentence, "original"),
                entry.form,
            )
            self.assertIsNone(sentence.find("FORM[@kindOf='standard']"))
            self.assertEqual(
                tuple(
                    form.text or ""
                    for form in sentence.findall("FORM[@kindOf='original'][@ver='alt']")
                ),
                entry.alternate_forms,
            )
            self.assertEqual(
                sentence.findtext("TRANSL"),
                entry.english.lower(),
            )
            self.assertEqual(
                sentence.find("TRANSL").get(
                    "{http://www.w3.org/XML/1998/namespace}lang"
                ),
                "eng",
            )
            self.assertEqual(sentence.get("source"), entry.source_attr)

    def test_the_sida_column_is_excluded_whole(self) -> None:
        """Gabelentz prints the column as "Sida"; identifying it with the
        "Sideia" of the Klaproth/Vander Vlis table is an assumption
        FormosanBank does not make, so none of it is published under
        fos. The two dash cells are inside that column."""
        excluded = {
            entry.s_id
            for entry in self.ledger
            if entry.status == "excluded_unidentified_variety"
        }
        self.assertEqual(len(excluded), 24)
        self.assertTrue(all(e.startswith("S_sida_") for e in excluded))
        self.assertIn("S_sida_forehead", excluded)
        self.assertIn("S_sida_beard", excluded)
        self.assertTrue(excluded.isdisjoint(self.sentences))
        self.assertFalse(
            [s for s in self.sentences if s.startswith("S_sida_")]
        )

    def test_source_spelling_variants_keep_their_tier(self) -> None:
        alternates = [
            form
            for sentence in self.sentences.values()
            for form in sentence.findall("FORM[@kindOf='original'][@ver='alt']")
        ]
        self.assertEqual(len(alternates), 2)
        self.assertEqual({form.text for form in alternates}, {"soa", "tutta"})
        self.assertEqual(
            sum(1 + len(entry.alternate_forms) for entry in self.included),
            47,
        )
        for sentence in self.sentences.values():
            self.assertIsNone(sentence.find("FORM[@kindOf='alternate']"))
            for form in sentence.findall("FORM"):
                self.assertNotIn(",", form.text or "")

    def test_no_unlicensed_phonology_or_gloss_structure_is_inferred(self) -> None:
        for sentence in self.sentences.values():
            self.assertIsNone(sentence.find("PHON"))
            self.assertIsNone(sentence.find("W"))
            self.assertIsNone(sentence.find("M"))

    def test_independent_source_checks_match_xml(self) -> None:
        """The twelve spot checks stay in the file as transcription
        evidence even where their cell is no longer published -- three
        are Sida. XML is asserted for the nine that are."""
        with SOURCE_CHECKS.open(encoding="utf-8", newline="") as handle:
            checks = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(checks), 12)
        self.assertEqual(
            {check["printed_page"] for check in checks},
            {"315", "316", "317", "318"},
        )
        published = [c for c in checks if not c["xml_id"].startswith("S_sida_")]
        self.assertEqual(len(published), 9)
        for check in published:
            sentence = self.sentences[check["xml_id"]]
            alternates = " | ".join(
                form.text or ""
                for form in sentence.findall("FORM[@kindOf='original'][@ver='alt']")
            )
            self.assertEqual(
                base_form_text(sentence, "original"),
                check["expected_original_form"],
            )
            self.assertEqual(
                alternates,
                check["expected_alternate_forms"],
            )
            lexeme = self.sentences.get(check["xml_id"] + "-opt")
            self.assertEqual(
                lexeme.findtext("FORM") if lexeme is not None else "",
                check["expected_lexeme_forms"],
            )
            self.assertEqual(
                sentence.findtext("TRANSL"),
                check["expected_translation_eng"],
            )

    def test_review_feedback_regressions(self) -> None:
        expected = {
            "S_vander_vlis_sideia_two": ("so", ("soa",)),
            "S_favorlang_man": ("bahosa", ("sjam",)),
            "S_favorlang_hair": ("tâu", ("ratta",)),
            "S_favorlang_ear": ("chárrina", ()),
            "S_favorlang_mouth": ("ranied", ("sabbacha",)),
            "S_favorlang_neck": ("bokkir", ("arribórribon",)),
            "S_favorlang_breast": ("arrabis", ("zido",)),
            "S_favorlang_belly": ("cháan", ()),
            "S_favorlang_heart": ("totto", ("tutta",)),
        }
        for record_id, (original, alternates) in expected.items():
            sentence = self.sentences[record_id]
            self.assertEqual(
                base_form_text(sentence, "original"),
                original,
            )
            readings = [form.text for form in sentence.findall("FORM[@ver='alt']")]
            lexeme = self.sentences.get(record_id + "-opt")
            if lexeme is not None:
                readings.append(lexeme.findtext("FORM"))
            self.assertEqual(tuple(readings), alternates)

    def test_five_source_lexemes_have_separate_records(self) -> None:
        # Printed pp. 316-318. POL-028: a competing lexeme is its own S
        # block, the second taking the first's id plus "-opt". The sixth
        # case, Sida Foot, left with the Sida column.
        expected = {
            "S_favorlang_man": ("bahosa", "sjam", "man"),
            "S_favorlang_hair": ("tâu", "ratta", "hair"),
            "S_favorlang_mouth": ("ranied", "sabbacha", "mouth"),
            "S_favorlang_neck": ("bokkir", "arribórribon", "neck"),
            "S_favorlang_breast": ("arrabis", "zido", "breast"),
        }
        self.assertEqual(len(self.sentences), 45)
        self.assertEqual(
            {key for key in self.sentences if "-opt" in key},
            {key + "-opt" for key in expected},
        )
        self.assertFalse([k for k in self.sentences if "-lex" in k])
        for record_id, (base, second, translation) in expected.items():
            for suffix, form in [("", base), ("-opt", second)]:
                sentence = self.sentences[record_id + suffix]
                self.assertEqual(len(sentence.findall("FORM")), 1)
                self.assertEqual(sentence.find("FORM").attrib, {"kindOf": "original"})
                self.assertEqual(base_form_text(sentence, "original"), form)
                self.assertEqual(sentence.findtext("TRANSL"), translation)
                self.assertEqual(sentence.get("source"), self.sentences[record_id].get("source"))

    def test_correcting_a_reading_does_not_change_its_identifier(self) -> None:
        entry = next(row for row in self.included if row.s_id == "S_favorlang_ear")
        self.assertEqual(
            replace(entry, form="corrected reading").s_id,
            "S_favorlang_ear",
        )
        entry = next(row for row in self.included if row.s_id == "S_favorlang_neck")
        corrected = replace(entry, alternate_forms=("corrected reading",))
        self.assertEqual(
            [row.s_id for row in build.xml_entries([corrected])],
            ["S_favorlang_neck", "S_favorlang_neck-opt"],
        )

    def test_generator_does_not_restore_prohibited_derived_tiers(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.xml"
            build.write_xml_file(path, "test", self.included[:1], "sira1267")
            root = ET.parse(path).getroot()
            self.assertEqual(root.get("copyright"), "public domain")
            self.assertEqual(root.findtext("S/FORM[@kindOf='original']"), "rama")
            self.assertIsNone(root.find(".//FORM[@kindOf='standard']"))
            self.assertIsNone(root.find(".//PHON"))

    def test_every_reviewer_attachment_row_has_a_resolution(self) -> None:
        with REVIEWER_FEEDBACK.open(
            encoding="utf-8",
            newline="",
        ) as handle:
            feedback = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(feedback), 13)
        self.assertEqual(
            Counter(row["source_attachment"] for row in feedback),
            Counter(
                {
                    "errorsFavorlang.csv": 9,
                    "errorsSida.csv": 3,
                    "OCR Review 2": 1,
                }
            ),
        )
        # Boese's review covered cells that are no longer published --
        # the Sida column left under a later ruling. The rows stay: they
        # record what a reviewer found in the source, which does not stop
        # being true when a column is withdrawn. Only published records
        # are asserted against the XML.
        for row in feedback:
            self.assertTrue(row["resolution"].startswith("Resolved:"))
            if row["xml_id"].startswith("S_sida_"):
                self.assertNotIn(row["xml_id"], self.sentences)
                continue
            self.assertIn(row["xml_id"], self.sentences)


if __name__ == "__main__":
    unittest.main()
