from __future__ import annotations

import tempfile
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import process_raw


class ProcessRawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo = Path(__file__).resolve().parents[1]
        cls.source_dir = cls.repo / "raw_data" / "Paiwan"
        cls.inventory = process_raw.source_inventory(cls.source_dir)

    def test_reviewed_inventory(self) -> None:
        self.assertEqual(
            {stem: len(records) for stem, records in self.inventory.items()},
            {
                "Welcome": 10,
                "FormosanBank": 29,
                "Formosan_Languages": 16,
                "Contributors": 9,
                "Terms_of_Use": 13,
                "Contributing_to_FormosanBank": 28,
            },
        )
        self.assertEqual(sum(map(len, self.inventory.values())), 105)

    def test_reviewed_source_repairs_are_retained(self) -> None:
        welcome = self.inventory["Welcome"]
        terms = self.inventory["Terms_of_Use"]
        contributing = self.inventory["Contributing_to_FormosanBank"]
        languages = self.inventory["Formosan_Languages"]

        self.assertTrue(any("Principal Investigators" in row.english for row in welcome))
        self.assertEqual(sum("Mohamed, W." in row.english for row in terms), 2)
        self.assertTrue(any("FormosanBank will" in row.english for row in contributing))
        self.assertTrue(any("You decide how" in row.english for row in contributing))
        self.assertTrue(any("(amilikan|ciniukukan)" in row.paiwan for row in contributing))
        self.assertTrue(
            any(row.english.startswith("The most striking") for row in languages)
        )

    def test_generation_is_deterministic_and_source_owned(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_dir = Path(first)
            second_dir = Path(second)
            self.assertEqual(process_raw.generate(self.source_dir, first_dir), (6, 105))
            self.assertEqual(process_raw.generate(self.source_dir, second_dir), (6, 105))

            first_files = sorted(first_dir.glob("*.xml"))
            second_files = sorted(second_dir.glob("*.xml"))
            self.assertEqual([path.name for path in first_files], [path.name for path in second_files])
            for first_path, second_path in zip(first_files, second_files, strict=True):
                self.assertEqual(first_path.read_bytes(), second_path.read_bytes())

                root = ET.parse(first_path).getroot()
                for sentence in root.findall("S"):
                    self.assertEqual(len(sentence.findall("FORM[@kindOf='original']")), 1)
                    self.assertFalse(sentence.findall("FORM[@kindOf='standard']"))
                    self.assertFalse(sentence.findall("PHON"))
                    self.assertEqual(len(sentence.findall("TRANSL")), 2)

    def test_published_ids_keep_their_passages(self) -> None:
        for stem, sid, translation in (
            ("Welcome", "8", "And our many contributors."),
            ("Contributors", "6", "Funding"),
            ("Formosan_Languages", "9", "A Legacy of Suppression and Revitalization"),
        ):
            root = process_raw.build_tree(stem, self.inventory[stem]).getroot()
            self.assertEqual(root.findtext(f"S[@id='{sid}']/TRANSL[@{process_raw.XML_LANG}='eng']"), translation)

    def test_new_source_lists_have_separate_keys(self) -> None:
        for stem, sid, phrase in (
            ("Welcome", "p1_people", "Principal Investigators Joshua Hartshorne"),
            ("Formosan_Languages", "p5_languages", "Amis (Ami) Atayal (Tayal)"),
            ("Contributors", "p6_contributors", "Li-May Sung Indigenous Languages"),
        ):
            root = process_raw.build_tree(stem, self.inventory[stem]).getroot()
            self.assertTrue(root.findtext(f"S[@id='{sid}']/TRANSL[@{process_raw.XML_LANG}='eng']").startswith(phrase))

    def test_text_corrections_do_not_change_identity(self) -> None:
        records = list(self.inventory["Welcome"])
        before = process_raw.build_tree("Welcome", records).getroot()
        records[2] = process_raw.SourceRecord("Corrected translation", records[2].chinese, records[2].paiwan)
        after = process_raw.build_tree("Welcome", records).getroot()
        self.assertEqual([s.get("id") for s in before], [s.get("id") for s in after])

    def test_missing_source_record_fails_before_renumbering(self) -> None:
        with self.assertRaises(ValueError):
            process_raw.build_tree("Welcome", self.inventory["Welcome"][:-1])

    def test_page_continuation_and_source_punctuation(self) -> None:
        self.assertEqual(self.inventory["Welcome"][-1].paiwan, "izuanan tjuruvu a caucau nakipusaladj tjanuamen.")
        self.assertIn("(amilikan|ciniukukan)", self.inventory["Contributing_to_FormosanBank"][1].paiwan)
        self.assertIn("open-source", self.inventory["Contributing_to_FormosanBank"][2].paiwan)
        self.assertIn("pu’ui", self.inventory["Contributing_to_FormosanBank"][25].paiwan)

    def test_malformed_or_empty_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.txt"
            for value in ("", "English\nChinese\n", "English\n\nPaiwan"):
                path.write_text(value)
                with self.assertRaises(ValueError):
                    process_raw.parse_source(path)


if __name__ == "__main__":
    unittest.main()
