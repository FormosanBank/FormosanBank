"""Source and expert-review regressions, independent of the old OCR heuristics."""

import csv
import json
import os
import re
import shutil
import sys
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
        self.assertEqual(sum(len(root.findall("S")) for root in self.roots), 677)
        self.assertFalse(any(root.findall(".//PHON[@kindOf='original']") for root in self.roots))
        for key in ("083C", "091E"):
            self.assertNotIn(f"AKIW_SZY_2012_EX_{key}", self.nodes)

    def test_source_optional_object_has_two_aligned_readings(self):
        # Scan p. 55, 23c: ha-min han mu-kan (kiya hemay); Chinese has optional 飯.
        full = self.nodes["AKIW_SZY_2012_EX_023C"]
        short = self.nodes["AKIW_SZY_2012_EX_023C-opt"]
        self.assertEqual(form(full), "ha-min han mu-kan kiya hemay.")
        self.assertEqual(form(short), "ha-min han mu-kan.")
        self.assertEqual(full.findtext("TRANSL"), "飯全部都吃掉。")
        self.assertEqual(short.findtext("TRANSL"), "全部都吃掉。")
        self.assertEqual([form(w) for w in short.findall("W")], ["ha-min", "han", "mu-kan"])
        self.assertEqual([w.findtext("TRANSL") for w in short.findall("W")],
                         ["HA-全部的", "助詞", "主焦-吃"])
        self.assertEqual([len(w.findall("M")) for w in short.findall("W")], [2, 1, 2])
        self.assertEqual(form(short, "standard"), "hamin han mukan.")
        self.assertEqual([w.get("id") for w in full.findall("W")],
                         [f"AKIW_SZY_2012_EX_023CW{n}" for n in range(1, 6)])

    def test_footnote_examples_keep_their_actual_source_analysis(self):
        # Scan pp. 33, 37: four unglossed sentences, including separate i niyazu'.
        for suffix in ("009A", "009B", "010", "014"):
            self.assertEqual(self.nodes[f"AKIW_SZY_2012_FN_{suffix}"].findall("W"), [])
        self.assertEqual(form(self.nodes["AKIW_SZY_2012_FN_010"]),
                         "kaku kusa balakiy-ay i niyazu'")
        self.assertEqual(form(self.nodes["AKIW_SZY_2012_FN_010"], "standard"),
                         "kaku kusa balakiyay i niyazu'")
        # Scan p. 39, footnote 15: sa-pa- is the single glossed 工焦 complex.
        sentence = self.nodes["AKIW_SZY_2012_FN_015"]
        self.assertEqual(form(sentence), "sa-pa-lamel ni ina tu buting ku banlay.")
        self.assertEqual(sentence.findtext("TRANSL"), "九層塔是媽媽配魚用的。")
        self.assertEqual([(form(m), m.findtext("TRANSL")) for m in sentence.find("W").findall("M")],
                         [("sa-pa-", "工焦"), ("lamel", "混")])

    def test_page_spanning_prose_example_keeps_all_four_glosses(self):
        sentence = self.nodes["AKIW_SZY_2012_P130_PROSE"]
        self.assertEqual(form(sentence), "tayza kaku i Taypak")
        self.assertEqual(sentence.findtext("TRANSL"), "我去臺北")
        self.assertEqual([w.findtext("TRANSL") for w in sentence.findall("W")],
                         ["去", "我", "處所格", "臺北"])
        self.assertEqual(sentence.findall(".//M"), [])

    def test_author_translation_alternatives_do_not_replace_expert_readings(self):
        # Scan pp. 130-131: footnotes 98-100 and the full 100a prose paraphrase.
        readings = {
            "099A": ("春天的天氣很好。", "春天天氣好"),
            "099B": ("樹在春天開花。", "樹的花在春天的時候開"),
            "100A": ("我每天清晨運動。", "我每天清晨會運動身體"),
            "100B": ("我都在清晨時刻起床。", "我清晨的時候起床得很早"),
        }
        for suffix, (primary, alternative) in readings.items():
            sentence = self.nodes[f"AKIW_SZY_2012_EX_{suffix}"]
            self.assertEqual([(t.get("ver"), t.text) for t in sentence.findall("TRANSL")],
                             [(None, primary), ("alt", alternative)])

    def test_unusual_gloss_labels_are_printed_in_the_source(self):
        cases = [
            ("023BW1M1", "HA"), ("023CW1M1", "HA"),  # p. 55
            ("033BW5M1", "PAY"), ("043BW1M2", "A"),  # pp. 66, 75
            ("100AW1M1", "PAY"), ("107BW3M1", "NA"),  # pp. 130, 137
            ("120BW5M1", "NA"), ("121BW1M1", "NU"),  # pp. 148–149
            ("123BW1M3", "HEN"), ("124BW5M2", "AW"),  # pp. 152–153
        ]
        for suffix, gloss in cases:
            with self.subTest(morpheme=suffix):
                morph = self.nodes[f"AKIW_SZY_2012_EX_{suffix}"]
                self.assertEqual(form(morph), gloss.lower())
                self.assertEqual(morph.findtext("TRANSL"), gloss)

    def test_scoped_source_gloss_exceptions(self):
        # Joshua's August 10 ruling; fixture readings come from expert commit 45d58b0.
        from lxml import etree

        tools = Path(os.environ.get("FORMOSANBANK_ROOT", CODE.parents[2]))
        self.assertTrue((tools / "QC/validation/rules/gloss_scrape.py").is_file(),
                        "Set FORMOSANBANK_ROOT to the current shared tools")
        sys.path.insert(0, str(tools))
        from QC.validation.rules.gloss_scrape import g001_marker_skeleton_parity

        with (CODE / "source_data/gloss_exceptions.csv").open(newline="", encoding="utf-8") as handle:
            cases = list(csv.DictReader(handle))
        expected = {case["word_id"] for case in cases}
        self.assertEqual(len(cases), 450)
        self.assertEqual(len(expected), 450)
        self.assertEqual(sum("TABLE_ROW" in wid for wid in expected), 403)
        for case in cases:
            with self.subTest(word=case["word_id"]):
                word = self.nodes[case["word_id"]]
                self.assertEqual(form(word), case["form"])
                self.assertEqual(word.findtext("TRANSL"), case["gloss"])
        actual = []
        for path in (CODE.parent / "XML").rglob("*.xml"):
            for finding in g001_marker_skeleton_parity(etree.parse(path), path):
                self.assertEqual(finding.rule_id, "G001")
                actual.append(re.search(r"W=([^\s]+)", finding.location).group(1))
        # Footnote 15 (scan p. 39) also glosses a composite prefix as one 工焦.
        self.assertEqual(len(actual), 451)
        self.assertEqual(set(actual), expected | {"AKIW_SZY_2012_FN_015W1"})

    def test_table_meanings_are_not_split_into_fictitious_glosses(self):
        # Each reviewed six-column row has one whole-word meaning and two source analyses.
        sentences = [s for root in self.roots for s in root.findall("S")
                     if "TABLE_ROW" in s.get("id", "")]
        self.assertEqual(len(sentences), 432)
        for sentence in sentences:
            with self.subTest(row=sentence.get("id")):
                self.assertEqual(len(sentence.findall("W")), 1)
                word = sentence.find("W")
                self.assertEqual(word.findtext("TRANSL"), sentence.findtext("TRANSL"))
                self.assertEqual(len(word.findall("M")), 2)


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
        path = self.output / "Sakizaya/akiw_2012_sakizaya_affixes_examples.xml"
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
