from __future__ import annotations

import csv
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_translations
import citation

FIELDS = ("english", "translation", "approved", "origin", "translator", "dialect", "date")
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def write_store(directory: Path, code: str, rows: list[tuple]) -> None:
    with open(directory / f"{code}.tsv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(FIELDS)
        writer.writerows(rows)


class BuildTranslationsTests(unittest.TestCase):
    def test_no_store_means_no_files_and_v1_citation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store, xml = Path(tmp) / "store", Path(tmp) / "XML"
            store.mkdir()
            self.assertEqual(build_translations.build(store, xml), [])
            self.assertEqual(
                citation.citation(store)[0],
                "Ruan, X. (2025). Translations of the FormosanBank documentation v1.",
            )

    def test_approved_rows_become_one_text_with_english_and_mandarin(self) -> None:
        contributors = {
            "Xuan Ruan": {"name": "Xuan Ruan", "surname": "Ruan", "given": "Xuan", "initials": "X."},
            "Ana Test": {"name": "Ana Test", "surname": "Test", "given": "Ana", "initials": "A."},
            "Bo Zh": {"name": "Bo Zh", "surname": "Zh", "given": "Bo", "initials": "B."},
        }
        with tempfile.TemporaryDirectory() as tmp:
            store, xml = Path(tmp) / "store", Path(tmp) / "XML"
            store.mkdir()
            write_store(store, "pwn", [
                ("Hello.", "PWN-1", "yes", "human", "Ana Test", "Eastern", "2026-11-01"),
                ("Bye.", "PWN-2", "yes", "mt", "Ana Test", "Eastern", "2026-11-01"),
                ("Draft.", "PWN-3", "no", "human", "Ana Test", "Eastern", "2026-11-01"),
            ])
            write_store(store, "zho", [
                ("Hello.", "你好。", "yes", "mt", "Bo Zh", "", "2026-11-02"),
            ])
            original = citation.read_contributors
            citation.read_contributors = lambda path=None: contributors
            try:
                summaries = build_translations.build(store, xml)
                apa, bib = citation.citation(store, contributors)
            finally:
                citation.read_contributors = original
            self.assertEqual(len(summaries), 1)
            self.assertEqual((summaries[0]["sentences"], summaries[0]["mandarin"], summaries[0]["mandarin_mt"]), (2, 1, 1))
            root = ET.parse(xml / summaries[0]["file"].removeprefix("XML/")).getroot()
            self.assertEqual(root.get(XML_LANG), "pwn")
            self.assertEqual(root.get("dialect"), "Eastern")
            sentences = root.findall("S")
            self.assertEqual([s.find("FORM").text for s in sentences], ["PWN-2", "PWN-1"])
            hello = sentences[1]
            self.assertEqual({t.get(XML_LANG): t.text for t in hello.findall("TRANSL")}, {"eng": "Hello.", "zho": "你好。"})
            self.assertEqual(apa, "Ruan, X., Test, A., & Zh, B. (2026). Translations of the FormosanBank documentation v3.")
            self.assertIn("author={Ruan, Xuan and Test, Ana and Zh, Bo}", bib)

    def test_unregistered_translator_stops_the_build(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Path(tmp)
            write_store(store, "ami", [("Hi.", "AMI-1", "yes", "human", "Nobody Known", "", "2026-11-01")])
            with self.assertRaises(KeyError):
                citation.citation(store)


if __name__ == "__main__":
    unittest.main()
