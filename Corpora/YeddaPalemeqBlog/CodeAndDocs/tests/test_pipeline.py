from __future__ import annotations

import csv
import hashlib
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/source_snapshot/Paiwan_Yedda_Blog.xml"
XML = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
AUDIT = ROOT / "data/formosanbank_audit"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class YeddaPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ET.parse(XML).getroot()
        cls.manifest = json.loads((AUDIT / "manifest.json").read_text(encoding="utf-8"))

    def sentence(self, sentence_id: str) -> ET.Element:
        sentence = self.root.find(f"S[@id='{sentence_id}']")
        self.assertIsNotNone(sentence)
        return sentence  # type: ignore[return-value]

    def test_frozen_source_and_manifest_hashes(self) -> None:
        self.assertEqual(
            sha256(SOURCE),
            "e18d0aa67893278cb7754e9725e68a81075760961391b3db941eca7d873ddba6",
        )
        self.assertEqual(sha256(XML), self.manifest["xml_sha256"])

    def test_source_coverage_is_complete(self) -> None:
        rows = read_tsv(AUDIT / "source_coverage.tsv")
        self.assertEqual(len(rows), 668)
        self.assertNotIn("omitted", {row["status"] for row in rows})
        self.assertEqual(
            sum(row["status"] == "expanded_source_alternatives" for row in rows), 3
        )

    def test_canonical_tier_shape(self) -> None:
        sentences = self.root.findall("S")
        self.assertEqual(len(sentences), 671)
        self.assertEqual(len({sentence.get("id") for sentence in sentences}), 671)
        for element in self.root.iter():
            if element.tag not in {"S", "W", "M"}:
                continue
            self.assertEqual(len(element.findall("FORM[@kindOf='original']")), 1)
            self.assertEqual(len(element.findall("FORM[@kindOf='standard']")), 1)
            self.assertEqual(len(element.findall("PHON[@kindOf='original']")), 1)
            self.assertEqual(len(element.findall("PHON[@kindOf='standard']")), 1)

    def test_source_alternatives_are_explicit(self) -> None:
        expected = {
            "S24_1": "a kipaparangez tua mareka qali maru tjalja semeljecan a tja kava nu kaljavuceleljan.",
            "S24_1b": "a kipaparangez tua mareka drava maru tjalja semeljecan a tja kava nu kaljavuceleljan.",
            "S483_1": "liyaw a talem ni kama a abar.",
            "S483_1b": "liyaw a talem ni kama a yasi.",
            "S535_1": "izua tucu a kinarupurupung, tjangtjang, asaw na vurasi 'ata runi.",
            "S535_1b": "izua tucu a kinarupurupung, siyak, asaw na vurasi 'ata runi.",
        }
        for sentence_id, text in expected.items():
            sentence = self.sentence(sentence_id)
            self.assertEqual(sentence.find("FORM[@kindOf='original']").text, text)
            self.assertNotIn("audio_url", sentence.attrib)
            self.assertIsNone(sentence.find("AUDIO"))

    def test_standard_segmentation_decision(self) -> None:
        """C012 drops the source segmentation from the standard tier.

        Nothing in the build edits the standard tier after standardize.py runs
        (POL-002). The reason the two tiers differ is recorded on the *original*
        FORM, which is source-owned and safe to annotate.
        """
        sentence = self.sentence("S652653654_2")
        original = sentence.find("FORM[@kindOf='original']")
        self.assertEqual(original.text, "pai, maya manu seman-neka-aravac tua zuma.")
        self.assertEqual(
            sentence.find("FORM[@kindOf='standard']").text,
            "pai, maya manu semannekaaravac tua zuma.",
        )
        self.assertIn("POL-014/015", original.get("notes", ""))
        self.assertIsNone(sentence.find("FORM[@kindOf='standard']").get("notes"))

    def test_issue_rows_are_repaired(self) -> None:
        expected = {
            "S493_1": "Where is the soup spoon? I use it to serve soup. Where is my pen?",
            "S491_1": "In the past herding cattles was considered a taboo.",
            "S481_1": "The kid is eating.",
            "S413_1": "I saw our elders.",
            "S412_1": "I saw you and your girlfriend.",
            "S305_1": "稲葉浩志いなばこうし is very handsome!",
            "S169_1": "What is nose-flute? That is something our ancestors create to make sound.",
            "S159_1": "We do not see horses in our place.",
            "S62_1": "Let's sing. Let all of us dance. Everybody, come play. Come, everybody, let's play swing.",
        }
        for sentence_id, text in expected.items():
            translation = self.sentence(sentence_id).find(f"TRANSL[@{XML_LANG}='eng']")
            self.assertIsNotNone(translation)
            self.assertEqual(translation.text, text)
            self.assertTrue(translation.get("notes"))

    def test_live_source_translation_repairs_are_applied(self) -> None:
        expected_ids = {
            "S664665_1",
            "S545_1",
            "S545_2",
            "S545_3",
            "S545_4",
            "S545_5",
            "S545_6",
            "S545_7",
            "S545_8",
            "S538_1",
            "S168_1",
            "S170_1",
            "S85_1",
            "S78_1",
            "S71_1",
            "S39_1",
            "S38_1",
            "S37_1",
            "S35_1",
            "S34_1",
            "S21_1",
            "S19_1",
            "S9_1",
            "Sunknown_1",
        }
        rows = read_tsv(AUDIT / "source_translation_review.tsv")
        self.assertEqual(len(rows), 24)
        self.assertEqual({row["s_id"] for row in rows}, expected_ids)
        for row in rows:
            translation = self.sentence(row["s_id"]).find(f"TRANSL[@{XML_LANG}='eng']")
            self.assertIsNotNone(translation)
            self.assertEqual(translation.text, row["translation"])
            self.assertTrue(translation.get("notes"))

    def test_live_source_word_gloss_repairs_are_applied(self) -> None:
        rows = read_tsv(AUDIT / "source_word_translation_review.tsv")
        self.assertEqual(len(rows), 41)
        self.assertEqual(len({row["w_id"] for row in rows}), 41)
        for row in rows:
            word = self.root.find(f".//W[@id='{row['w_id']}']")
            self.assertIsNotNone(word)
            translation = word.find(f"TRANSL[@{XML_LANG}='eng']")
            self.assertIsNotNone(translation)
            self.assertEqual(translation.text, row["translation"])
            self.assertEqual(
                translation.get("notes"),
                "Restored from the live source after frozen-scrape review.",
            )

    def test_m_tier_is_per_sentence_consistent(self) -> None:
        """POL-023, per-sentence: a sentence either analyses every W or none.

        The blog parses some sentences morphologically and leaves others
        unparsed. fix_m_tier.py drops the mirror M tier from the unparsed ones
        rather than letting it assert an analysis Yedda never made.
        """
        def form(element: ET.Element) -> str:
            child = element.find("FORM[@kindOf='original']")
            return child.text or "" if child is not None else ""

        stripped = 0
        for sentence in self.root.findall("S"):
            words = sentence.findall("W")
            if not words:
                continue
            parsed = any(
                len(word.findall("M")) >= 2
                or any(form(m) != form(word) for m in word.findall("M"))
                for word in words
            )
            if parsed:
                for word in words:
                    self.assertTrue(
                        word.findall("M"),
                        f"{word.get('id')} has no M in an analysed sentence",
                    )
            else:
                for word in words:
                    self.assertEqual(
                        word.findall("M"),
                        [],
                        f"{word.get('id')} keeps a mirror M in an unparsed sentence",
                    )
                stripped += 1
        self.assertEqual(stripped, 161)
        self.assertEqual(len(self.root.findall(".//M")), 6492)

    def test_standard_tier_strips_source_accents(self) -> None:
        """--remove_accents flattens the diacritics on two quoted Mandarin terms.

        Both the acute and the macron are stripped from the standard tier.
        Paiwan attests no accented letter, so the corpus passes no keep set
        letters here and nothing is protected. The original tier is untouched
        in every case.
        """
        expected = {"S303_1W9": ("yípó", "yipo"), "S303_1W14": ("āyí", "ayi")}
        for word_id, (original, standard) in expected.items():
            word = self.root.find(f".//W[@id='{word_id}']")
            self.assertIsNotNone(word)
            self.assertEqual(word.find("FORM[@kindOf='original']").text, original)
            self.assertEqual(word.find("FORM[@kindOf='standard']").text, standard)
        sentence = self.sentence("S303_1")
        self.assertIn("yípó", sentence.find("FORM[@kindOf='original']").text)
        self.assertIn("yipo", sentence.find("FORM[@kindOf='standard']").text)

    def test_no_legacy_final_xml(self) -> None:
        self.assertFalse((ROOT.parent / "Final_XML").exists())


if __name__ == "__main__":
    unittest.main()
