from __future__ import annotations

import csv
import hashlib
import os
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(os.environ.get("CORPUS_ROOT", Path(__file__).resolve().parents[2]))
CODE = ROOT / "CodeAndDocs"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with (CODE / "intermediate" / "reviewed_sentences.csv").open(
            encoding="utf-8", newline=""
        ) as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.sentences = {
            sentence.get("id"): sentence
            for path in sorted((ROOT / "XML").rglob("*.xml"))
            for sentence in ET.parse(path).getroot().findall("S")
        }

    def test_reviewed_source_count_and_ids(self) -> None:
        self.assertEqual(len(self.rows), 83)
        self.assertEqual(len(self.sentences), 83)
        self.assertIn("nanpo1931_dispersion_s021b", self.sentences)
        self.assertEqual(
            self.sentences["nanpo1931_dispersion_s022"]
            .find("FORM[@kindOf='original']")
            .text,
            "Aiyan nu aiyan, saisaiya wilan.",
        )

    def test_source_tiers_only(self) -> None:
        standards = [
            form
            for sentence in self.sentences.values()
            for form in sentence.findall("FORM[@kindOf='standard']")
        ]
        translations = [
            translation
            for sentence in self.sentences.values()
            for translation in sentence.findall("TRANSL")
        ]
        self.assertEqual(standards, [])
        self.assertEqual(len(translations), 82)
        self.assertTrue(all(t.get(XML_LANG) == "jpn" for t in translations))

    def test_source_backed_regressions(self) -> None:
        row14 = self.sentences["nanpo1931_dispersion_s014"].find("TRANSL")
        self.assertEqual(
            row14.text,
            "我等要去我所、乃是爲生蕃是生蕃沙漏毛（サラウモー蕃號也）",
        )
        split = self.sentences["nanpo1931_dispersion_s021b"]
        self.assertEqual(
            split.find("FORM[@kindOf='original']").text,
            "Tatumaumauwan, kahah mausai mahah dakho",
        )
        self.assertEqual(split.find("TRANSL").text, "不得已自去爲生蕃也")
        self.assertEqual(
            self.sentences["nanpo1931_dispersion_s022"].findall("TRANSL"), []
        )

    def test_private_source_identity_when_available(self) -> None:
        source = Path(
            os.environ.get(
                "SOURCE_PDF",
                ROOT
                / "Private"
                / "source"
                / "nanpo_dozoku_v3n1_taisha_songs_1931.pdf",
            )
        )
        if not source.is_file():
            self.skipTest("private source is supplied outside the Git tree")
        self.assertEqual(source.stat().st_size, 16_508_391)
        self.assertEqual(
            hashlib.sha256(source.read_bytes()).hexdigest(),
            "094658186d845c0fd1fae2da6a8c41870734742a08e86fcfa97815710e1f485e",
        )


if __name__ == "__main__":
    unittest.main()
