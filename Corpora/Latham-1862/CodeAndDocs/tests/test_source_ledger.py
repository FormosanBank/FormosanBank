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
        self.assertEqual(len(self.included), 62)
        self.assertEqual(
            Counter(entry.status for entry in self.ledger),
            Counter({"included": 62, "omitted_blank_or_dash": 2}),
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
                sentence.findtext("FORM[@kindOf='original']"),
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

    def test_dash_cells_are_terminally_omitted(self) -> None:
        omitted = {
            entry.s_id
            for entry in self.ledger
            if entry.status == "omitted_blank_or_dash"
        }
        self.assertEqual(omitted, {"S_sida_forehead", "S_sida_beard"})
        self.assertTrue(omitted.isdisjoint(self.sentences))

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
            70,
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

    def test_twelve_independent_source_checks_match_xml(self) -> None:
        with SOURCE_CHECKS.open(encoding="utf-8", newline="") as handle:
            checks = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(checks), 12)
        self.assertEqual(
            {check["printed_page"] for check in checks},
            {"315", "316", "317", "318"},
        )
        for check in checks:
            sentence = self.sentences[check["xml_id"]]
            alternates = " | ".join(
                form.text or ""
                for form in sentence.findall("FORM[@kindOf='original'][@ver='alt']")
            )
            self.assertEqual(
                sentence.findtext("FORM[@kindOf='original']"),
                check["expected_original_form"],
            )
            self.assertEqual(
                alternates,
                check["expected_alternate_forms"],
            )
            lexeme = self.sentences.get(check["xml_id"] + "-lex2")
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
            "S_sida_mouth": ("motaus", ()),
            "S_favorlang_neck": ("bokkir", ("arribórribon",)),
            "S_favorlang_breast": ("arrabis", ("zido",)),
            "S_favorlang_belly": ("cháan", ()),
            "S_favorlang_heart": ("totto", ("tutta",)),
            "S_sida_foot": ("rahpal", ("tiltil",)),
        }
        for record_id, (original, alternates) in expected.items():
            sentence = self.sentences[record_id]
            self.assertEqual(
                sentence.findtext("FORM[@kindOf='original']"),
                original,
            )
            readings = [form.text for form in sentence.findall("FORM[@ver='alt']")]
            lexeme = self.sentences.get(record_id + "-lex2")
            if lexeme is not None:
                readings.append(lexeme.findtext("FORM"))
            self.assertEqual(tuple(readings), alternates)

    def test_six_source_lexemes_have_separate_records(self) -> None:
        # Printed pp. 316-318; revised POL-028 supersedes the old FORM grouping.
        expected = {
            "S_favorlang_man": ("bahosa", "sjam", "man"),
            "S_favorlang_hair": ("tâu", "ratta", "hair"),
            "S_favorlang_mouth": ("ranied", "sabbacha", "mouth"),
            "S_favorlang_neck": ("bokkir", "arribórribon", "neck"),
            "S_favorlang_breast": ("arrabis", "zido", "breast"),
            "S_sida_foot": ("rahpal", "tiltil", "foot"),
        }
        self.assertEqual(len(self.sentences), 68)
        self.assertEqual(
            {key for key in self.sentences if "-lex" in key},
            {key + "-lex2" for key in expected},
        )
        for record_id, (base, second, translation) in expected.items():
            for suffix, form in [("", base), ("-lex2", second)]:
                sentence = self.sentences[record_id + suffix]
                self.assertEqual(len(sentence.findall("FORM")), 1)
                self.assertEqual(sentence.find("FORM").attrib, {"kindOf": "original"})
                self.assertEqual(sentence.findtext("FORM"), form)
                self.assertEqual(sentence.findtext("TRANSL"), translation)
                self.assertEqual(sentence.get("source"), self.sentences[record_id].get("source"))

    def test_correcting_a_reading_does_not_change_its_identifier(self) -> None:
        entry = next(row for row in self.included if row.s_id == "S_sida_mouth")
        self.assertEqual(
            replace(entry, form="corrected reading").s_id,
            "S_sida_mouth",
        )
        entry = next(row for row in self.included if row.s_id == "S_favorlang_neck")
        corrected = replace(entry, alternate_forms=("corrected reading",))
        self.assertEqual(
            [row.s_id for row in build.xml_entries([corrected])],
            ["S_favorlang_neck", "S_favorlang_neck-lex2"],
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
        for row in feedback:
            self.assertIn(row["xml_id"], self.sentences)
            self.assertTrue(row["resolution"].startswith("Resolved:"))


if __name__ == "__main__":
    unittest.main()
