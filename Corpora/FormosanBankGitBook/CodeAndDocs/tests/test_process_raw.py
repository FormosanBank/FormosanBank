from __future__ import annotations

import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

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
                for index, sentence in enumerate(root.findall("S")):
                    self.assertEqual(sentence.get("id"), str(index))
                    self.assertEqual(len(sentence.findall("FORM[@kindOf='original']")), 1)
                    self.assertFalse(sentence.findall("FORM[@kindOf='standard']"))
                    self.assertFalse(sentence.findall("PHON"))
                    self.assertEqual(len(sentence.findall("TRANSL")), 2)


if __name__ == "__main__":
    unittest.main()
