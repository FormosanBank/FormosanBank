"""Source and expert-review regressions, independent of the old OCR heuristics."""

import csv
import json
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from generate_xml import CODE, build


def form(node, kind="original"):
    return node.findtext(f"FORM[@kindOf='{kind}']")


class ReviewedSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roots = [ET.parse(path).getroot() for path in sorted((CODE.parent / "XML").rglob("*.xml"))]
        cls.nodes = {node.get("id"): node for root in cls.roots for node in root.iter() if node.get("id")}

    def test_null_prefix_matches_source_on_all_original_tiers(self):
        # Scan pp. 37–38, table 9 and example 17d; expert commit 45d58b0.
        sentence = self.nodes["AKIW_SZY_2012_EX_017D"]
        word = self.nodes["AKIW_SZY_2012_EX_017DW1"]
        self.assertEqual(form(sentence), "∅-imelang ci Taymu kiyu si-dinget.")
        self.assertEqual(form(sentence, "standard"), "imelang ci Taymu kiyu sidinget.")
        self.assertEqual(form(word), "∅-imelang")
        self.assertEqual([form(m) for m in word.findall("M")], ["∅", "imelang"])
        self.assertEqual(word.findall("M")[0].findall("TRANSL"), [])
        self.assertEqual(word.findall("M")[1].findtext("TRANSL"), "生病")
        self.assertEqual(sentence.findtext("TRANSL"), "Taymu 生病所以流鼻涕。")

    def test_corrected_chinese_and_genitive_survive(self):
        # Scan pp. 33, 37 and Joshua's August 10 OCR review.
        self.assertEqual(self.nodes["AKIW_SZY_2012_EX_003W4"].findtext("TRANSL"), "屬格")
        self.assertEqual(self.nodes["AKIW_SZY_2012_EX_015"].findtext("TRANSL"), "我的肩膀受傷了。")
        self.assertEqual(self.nodes["AKIW_SZY_2012_EX_015W3"].findtext("TRANSL"), "肩膀")

    def test_complete_table_columns_survive(self):
        # Scan p. 53, table 13: full form, meaning, affix/function, root/meaning.
        sentence = self.nodes["AKIW_SZY_2012_TABLE_ROW_001"]
        word = sentence.find("W")
        self.assertEqual(form(sentence), "a-mumul")
        self.assertEqual(sentence.findtext("TRANSL"), "即將出發")
        self.assertEqual([(form(m), m.findtext("TRANSL")) for m in word.findall("M")],
                         [("a-", "即將進行"), ("mumul", "出發")])
        self.assertEqual(word.findall("M")[1].findtext("TRANSL[@ver='alt']"), "走")

    def test_circumfix_original_and_standard_are_distinct(self):
        # Scan p. 145, row 365; Madeline's August 14 notation decision.
        morph = self.nodes["AKIW_SZY_2012_TABLE_ROW_365W1M1"]
        self.assertEqual(form(morph), "ma-...-ay")
        self.assertEqual(form(morph, "standard"), "ma--ay")
        self.assertEqual(form(self.nodes["AKIW_SZY_2012_TABLE_ROW_365W1M2"]), "limula'")

    def test_repeated_apostrophes_are_retained(self):
        # Scan p. 147, row 376. The two source apostrophes are meaningful.
        sentence = self.nodes["AKIW_SZY_2012_TABLE_ROW_376"]
        self.assertEqual(form(sentence), "mu'-'neng-ay")
        self.assertEqual(form(sentence, "standard"), "mu''nengay")

    def test_distinct_source_analysis_is_not_deduplicated(self):
        # Scan pp. 99 and 112, examples 69a and 82a.
        a, b = [self.nodes[f"AKIW_SZY_2012_EX_{key}"] for key in ("069A", "082A")]
        self.assertEqual(form(a), "mu-lusu' ku tanang nay zais.")
        self.assertEqual(form(b), "mulusu' ku tanang nay zais.")
        self.assertEqual(form(a, "standard"), form(b, "standard"))

    def test_missing_source_gloss_is_not_invented(self):
        # Madeline removed the inherited function gloss in table row 20.
        affix = self.nodes["AKIW_SZY_2012_TABLE_ROW_020W1M1"]
        self.assertEqual(form(affix), "ka-")
        self.assertEqual(affix.findall("TRANSL"), [])

    def test_expert_alternate_translation_survives_syntax_repair(self):
        # Expert row 133 had a malformed tag containing the second reading.
        root = self.nodes["AKIW_SZY_2012_TABLE_ROW_133W1M2"]
        self.assertEqual([(t.get("ver"), t.text) for t in root.findall("TRANSL")],
                         [(None, "歇一下"), ("alt", "休息一下")])

    def test_expert_summary_exclusion_and_original_phon_omission(self):
        # Madeline's August 13–14 review excludes the entire late dataset.
        self.assertFalse(any("SUMMARY_ROW" in sid for sid in self.nodes))
        self.assertEqual(sum(len(root.findall("S")) for root in self.roots), 670)
        self.assertFalse(any(root.findall(".//PHON[@kindOf='original']") for root in self.roots))
        for key in ("083C", "091E"):
            self.assertNotIn(f"AKIW_SZY_2012_EX_{key}", self.nodes)


class TranscriptionBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.code = Path(self.temp.name) / "CodeAndDocs"
        self.code.mkdir()
        for name in ("extraction_report.csv", "table_extraction_report.csv", "manual_edits.xml"):
            shutil.copyfile(CODE / name, self.code / name)
        (self.code / "source_data").mkdir()
        shutil.copyfile(CODE / "source_data/text_metadata.json", self.code / "source_data/text_metadata.json")
        self.output = Path(self.temp.name) / "XML"

    def test_build_needs_only_committed_transcription_inputs(self):
        build(self.code, self.output)
        roots = [ET.parse(path).getroot() for path in self.output.rglob("*.xml")]
        self.assertEqual(sorted(len(root.findall("S")) for root in roots), [238, 432])
        self.assertFalse(any(root.findall(".//PHON") for root in roots))
        self.assertFalse(any(root.findall(".//FORM[@kindOf='standard']") for root in roots))

    def test_corrected_source_text_keeps_its_identity(self):
        path = self.code / "extraction_report.csv"
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            rows, fields = list(reader), reader.fieldnames
        rows[0]["form"] = "a corrected reading"
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
        build(self.code, self.output)
        path = self.output / "szy/akiw_2012_sakizaya_affixes_examples.xml"
        sentence = ET.parse(path).getroot().find("S")
        self.assertEqual(sentence.get("id"), "AKIW_SZY_2012_EX_001")
        self.assertEqual(sentence.get("source"), "PDF page 33; example 1")
        self.assertEqual(form(sentence), "a corrected reading")

    def test_missing_reviewed_record_stops_before_writing(self):
        path = self.code / "manual_edits.xml"
        tree = ET.parse(path)
        group = tree.getroot().find("FILE")
        group.remove(group.find("S"))
        tree.write(path, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "inventory and expert transcription disagree"):
            build(self.code, self.output)
        self.assertFalse(self.output.exists())

    def test_baseline_metadata_preserves_source_identity(self):
        metadata = json.loads((self.code / "source_data/text_metadata.json").read_text())
        self.assertEqual({v["text_attributes"]["{http://www.w3.org/XML/1998/namespace}lang"]
                          for v in metadata.values()}, {"szy"})
        self.assertEqual({v["text_attributes"]["dialect"] for v in metadata.values()}, {"Sakizaya"})


if __name__ == "__main__":
    unittest.main()
