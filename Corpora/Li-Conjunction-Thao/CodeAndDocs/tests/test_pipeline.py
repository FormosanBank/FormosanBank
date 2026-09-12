from __future__ import annotations

import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DOCS / "scripts"))

import audit_source_fidelity as audit
import build_xml
from flatten_standard_segmentation import flatten_file


def original(parent: ET.Element) -> str:
    return parent.findtext("FORM[@kindOf='original']")


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.records = audit._read_records()
        self.root = build_xml.build(build_xml.rows()).getroot()

    def test_printed_records_remain_separate_from_corrections(self) -> None:
        audit._audit_literal_fixtures(self.records)
        raw = self.records["li2014_thao_S021"]
        fixed = build_xml.corrected_record(raw)
        self.assertIn("ɬpaðiSan", raw["original"])
        self.assertIn("ɬpaðiʃan", fixed["original"])
        self.assertEqual(raw["gloss"], fixed["gloss"])
        self.assertEqual(raw["source_locator"], fixed["source_locator"])

    def test_changed_correction_input_fails(self) -> None:
        row = self.records["li2014_thao_S021"].copy()
        row["original"] = "unexpected transcription"
        with self.assertRaisesRegex(ValueError, "Correction source changed"):
            build_xml.corrected_record(row)

    def test_reviewed_readings_propagate_to_word_tiers(self) -> None:
        sentence = self.root.find("S[@id='li2014_thao_S021']")
        self.assertEqual(original(sentence.findall("W")[-1]), "ɬpaðiʃan")
        for label, expected in {
            "S025": "a muʃa iða yaku ya saqaði.",
            "S026": "ya ʃaʃanu maθuaw waðaqan maharbuk.",
            "S027": "hadana ita iða ya aðaðak.",
        }.items():
            self.assertEqual(original(self.root.find(f"S[@id='li2014_thao_{label}']")), expected)
        self.assertEqual(self.root.findtext("S[@id='li2014_thao_S001']/TRANSL"),
                         "I know how to carry sweet potatoes and firewood on my back.")
        self.assertEqual(self.root.findtext("S[@id='li2014_thao_S009']/W[5]/TRANSL"), "person")

    def test_footnote_five_is_retained_without_invented_analysis(self) -> None:
        sentence = self.root.find("S[@id='li2014_thao_fn5_1']")
        self.assertEqual(original(sentence), "tu sa suma wa anyamin")
        self.assertEqual(sentence.findtext("TRANSL"), "It's the other people's stuff")
        self.assertFalse(sentence.findall("W"))
        self.assertIn("printed p. 403; footnote 5", sentence.get("source"))

    def test_pending_morphology_does_not_expand(self) -> None:
        self.assertEqual(len(self.root.findall(".//W")), 211)
        self.assertEqual(len(self.root.findall(".//M")), 169)
        self.assertEqual(sum(not word.findall("M") for word in self.root.findall(".//W")), 140)
        self.assertEqual(build_xml.parse_morphemes("masa", "and"), [])
        self.assertEqual(build_xml.parse_morphemes("q<m>aʃiʃi", "catch<AF>"),
                         [("q-aʃiʃi", "catch"), ("-m-", "<AF>")])
        with self.assertRaisesRegex(ValueError, "infix mismatch"):
            build_xml.parse_morphemes("q<m>aʃiʃi", "catch")

    def test_published_sentence_ids_and_order_survive(self) -> None:
        ids = [sentence.get("id") for sentence in self.root.findall("S")]
        expected = [f"li2014_thao_S{number:03d}" for number in range(1, 28)]
        expected.insert(8, "li2014_thao_fn5_1")
        self.assertEqual(ids, expected)
        self.assertEqual(self.root.get("id"), "li_2014_conjunction_in_thao")

    def test_raw_build_is_deterministic_and_has_no_derived_tiers(self) -> None:
        second = build_xml.build(build_xml.rows()).getroot()
        self.assertEqual(ET.tostring(self.root), ET.tostring(second))
        self.assertFalse(self.root.findall(".//FORM[@kindOf='standard']"))
        self.assertFalse(self.root.findall(".//PHON"))

    def test_source_audit_detects_output_corruption(self) -> None:
        audit._audit_source_anchors(self.root, self.records)
        self.root.find("S[@id='li2014_thao_S025']/FORM").text = "a muʃa iDa yaku ya saqaDi."
        with self.assertRaises(AssertionError):
            audit._audit_source_anchors(self.root, self.records)

    def test_flatten_only_removes_sentence_standard_infix_brackets(self) -> None:
        xml = '''<TEXT><S><FORM kindOf="original">q&lt;m&gt;a-ʃiʃi</FORM>
        <FORM kindOf="standard">q&lt;m&gt;a-shishi</FORM><W>
        <FORM kindOf="standard">q&lt;m&gt;a-shishi</FORM></W></S></TEXT>'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.xml"
            path.write_text(xml)
            flatten_file(path)
            result = ET.parse(path)
        self.assertEqual(result.findtext("S/FORM[@kindOf='standard']"), "qma-shishi")
        self.assertEqual(result.findtext("S/FORM[@kindOf='original']"), "q<m>a-ʃiʃi")
        self.assertEqual(result.findtext("S/W/FORM"), "q<m>a-shishi")

    def test_final_output_has_current_utility_tiers(self) -> None:
        root = ET.parse(build_xml.XML).getroot()
        audit._audit_final(root)
        audit._audit_source_anchors(root, self.records)
        self.assertFalse(any("*" in (node.text or "") for node in root.findall(".//PHON")))
        self.assertTrue(all(node.get("kindOf") is None for node in root.findall(".//TRANSL")))


if __name__ == "__main__":
    unittest.main()
