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
        self.assertEqual(len(sentences), 674)
        self.assertEqual(len({sentence.get("id") for sentence in sentences}), 674)
        for element in self.root.iter():
            if element.tag not in {"S", "W", "M"}:
                continue
            # one base per tier (POL-028); ver="alt" variants come from word_alternates.tsv
            for tier in ("original", "standard"):
                forms = element.findall(f"FORM[@kindOf='{tier}']")
                self.assertEqual(sum(f.get("ver") is None for f in forms), 1)
                self.assertTrue(all(f.get("ver") in (None, "alt") for f in forms))
            self.assertEqual(len(element.findall("PHON[@kindOf='original']")), 1)
            self.assertEqual(len(element.findall("PHON[@kindOf='standard']")), 1)

    def test_x_or_y_headword_spellings_are_variants(self) -> None:
        rows = read_tsv(ROOT / "word_alternates.tsv")
        self.assertEqual(len(rows), 72)
        variants = 0
        for element in self.root.iter():
            if element.tag in {"S", "W", "M"}:
                variants += sum(
                    f.get("ver") == "alt" for f in element.findall("FORM[@kindOf='original']")
                )
        self.assertEqual(variants, 72 + 63)  # 72 words; 63 of them also on their single morpheme
        for row in rows:
            word = self.root.find(f".//W[@id='{row['w_id']}']")
            alts = [
                (f.get("kindOf"), f.text) for f in word.findall("FORM") if f.get("ver") == "alt"
            ]
            self.assertEqual(alts, [("original", row["alternate"]), ("standard", row["alternate"])])
            self.assertEqual(len(word.findall("PHON[@kindOf='original']")), 1)

    def test_sentences_written_out_from_a_word_gloss(self) -> None:
        expected = {
            "S507_2": "nu mevulung a caucau, madjeleanga a malim tua ngadan nua caucau.",
            "S507_3": "nu mevulung a caucau, madjeleanga a madraudraw tua ngadan nua caucau.",
        }
        ids = [s.get("id") for s in self.root.findall("S")]
        self.assertEqual(ids[ids.index("S507_1") + 1 : ids.index("S507_1") + 3], ["S507_2", "S507_3"])
        for sentence_id, text in expected.items():
            sentence = self.sentence(sentence_id)
            self.assertEqual(sentence.find("FORM[@kindOf='original']").text, text)
            self.assertEqual(sentence.findall("W") + sentence.findall("TRANSL") + sentence.findall("AUDIO"), [])

    def test_post_502_is_two_sentences(self) -> None:
        expected = {"S502_1": ("saladji a kemim.", ["sa", "ladji"]), "S502_2": ("pasaladji a kemim.", ["pa", "sa", "ladji"])}
        for sentence_id, (text, pieces) in expected.items():
            sentence = self.sentence(sentence_id)
            self.assertEqual(sentence.find("FORM[@kindOf='original']").text, text)
            self.assertEqual(sentence.find("TRANSL").text,
                             "No, I don't want to. No, I don't want to. Forget it, don't bother trying to find it.")
            words = sentence.findall("W")
            self.assertEqual([w.find("FORM[@kindOf='original']").text for w in words][1:], ["a", "k<em>im"])
            self.assertEqual(words[0].find("FORM[@kindOf='original']").text, "-".join(pieces))
            self.assertEqual(words[0].find("TRANSL").text, "I don't want to.")
            self.assertEqual([m.find("FORM[@kindOf='original']").text for m in words[0].findall("M")], pieces)
        for sentence_id in ("S502_1", "S502_2"):  # the recording pronounces all three lines
            self.assertIsNone(self.sentence(sentence_id).find("AUDIO"))
            self.assertIsNone(self.sentence(sentence_id).get("audio_url"))

    def test_prose_dictionary(self) -> None:
        table = read_tsv(ROOT / "prose_dictionary.tsv")
        built = [row for row in table if not row["hold"]]
        self.assertEqual((len(table), len(built)), (26, 26))
        root = ET.parse(XML.parent / "Paiwan_Yedda_Blog_Dictionary.xml").getroot()
        entries = {s.get("id"): s for s in root.findall("S")}
        self.assertEqual(sorted(entries), sorted(row["entry_id"] for row in built))
        meqaca = entries["YD0001"]
        self.assertEqual(meqaca.find("FORM[@kindOf='original']").text, "meqaca")
        self.assertEqual(
            [(m.find("FORM[@kindOf='original']").text, m.findtext("TRANSL")) for m in meqaca.iter("M")],
            [("me", "AV"), ("qaca", "grow up")],
        )
        for row in table:
            self.assertNotIn("(", row["form"] + row["word_form"] + row["morphemes"])
        garden = entries["YD0018"]
        self.assertEqual([(f.get("ver"), f.text) for f in garden.findall("FORM[@kindOf='original']")],
                         [(None, "puhanaan"), ("alt", "puhanan")])

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
        self.assertEqual(len(rows), 49)
        self.assertEqual(len({row["w_id"] for row in rows}), 49)
        moved = {"S502_1W2": "S502_2W1"}  # pasaladji, moved when post 502 was split in two
        for row in rows:
            word = self.root.find(f".//W[@id='{moved.get(row['w_id'], row['w_id'])}']")
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
        self.assertEqual(len(self.root.findall(".//M")), 6497)  # 6492 + 5 from splitting post 502

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
