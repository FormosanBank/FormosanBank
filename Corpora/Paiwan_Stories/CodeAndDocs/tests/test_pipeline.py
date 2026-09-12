from __future__ import annotations

import copy
import csv
import importlib
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
build_xml = importlib.import_module("build_xml")
repair_records = importlib.import_module("repair_records")


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.records = build_xml.rows()
        self.trees = build_xml.build(self.records)
        self.maljialjian = self.trees["maljialjian_a_qaciljay.xml"].getroot()

    def test_published_ids_and_inserted_source_order(self):
        self.assertEqual(
            {tree.getroot().get("id") for tree in self.trees.values()},
            {"PS_dingding", "PS_kavatjes", "PS_maljialjian"},
        )
        expected = [f"S{i}" for i in range(1, 16)]
        for name, tree in self.trees.items():
            ids = [s.get("id") for s in tree.getroot().findall("S")]
            self.assertEqual(ids, expected[:6] + ["S6a"] + expected[6:]
                             if name == "maljialjian_a_qaciljay.xml" else expected)
        self.assertTrue(self.maljialjian.find("S[@id='S7']/FORM").text.startswith("djemavadjavac"))
        self.assertTrue(self.maljialjian.find("S[@id='S15']/FORM").text.startswith("maru emusilui"))

    def test_missing_source_unit_is_retained(self):
        sentence = self.maljialjian.find("S[@id='S6a']")
        self.assertEqual(sentence.findtext("FORM"),
            "tjaukaljia ti vuvu a uqaljay na kemadrangu, sa masi dramiya uri vaik a pasa vavua a kalakuda.")
        self.assertEqual(sentence.findtext("TRANSL"), "爺爺一大早就揹著簍筐，帶著鐮刀往山裡去工作。")

    def test_source_translation_repairs(self):
        root = self.trees["kavatjes_ni_vuvu.xml"].getroot()
        expected = {
            "S12": "他們還會用菸頭來處理嘴破皮的傷口。",
            "S13": "現在她無聊的時候，常常一個人抽菸。",
            "S14": "還有一台老人機，",
            "S15": "想念時就會打電話給在台北工作的我。",
        }
        for sid, text in expected.items():
            self.assertEqual(root.findtext(f"S[@id='{sid}']/TRANSL"), text)
        self.assertEqual(self.maljialjian.findtext("S[@id='S6']/TRANSL"), "有一年部落正舉辦五年祭，")

    def test_published_quotation_corrections_are_retained(self):
        self.assertEqual(self.maljialjian.findtext("S[@id='S4']/FORM"),
            'ti kapi kivadaq tjaivuvu "vuvu, aicu a qaciljay sikudakuda?"')
        self.assertEqual(self.maljialjian.findtext("S[@id='S4']/TRANSL"),
            "kapi問＂奶奶，這顆石頭是做什麼用的?＂")
        self.assertIn("kumakuma, pangac,", self.maljialjian.findtext("S[@id='S11']/FORM"))

    def test_word_locators_represent_physical_rows(self):
        expected = {"S4": "Word table row 4, first unit", "S5": "Word table row 4, second unit",
                    "S6": "Word table row 5", "S6a": "Word table row 6", "S15": "Word table row 15"}
        for sid, locator in expected.items():
            self.assertIn(locator, self.maljialjian.find(f"S[@id='{sid}']").get("source"))

    def test_builder_owns_only_original_and_translation_tiers(self):
        for tree in self.trees.values():
            self.assertFalse(tree.findall(".//PHON"))
            self.assertFalse(tree.findall('.//FORM[@kindOf="standard"]'))
            for translation in tree.findall(".//TRANSL"):
                self.assertEqual(translation.attrib, {build_xml.XML_LANG: "zho"})

    def test_correcting_text_does_not_change_ids_or_locations(self):
        changed = copy.deepcopy(self.records)
        changed[0]["original"] = "corrected source text."
        rebuilt = build_xml.build(changed)
        for name, tree in self.trees.items():
            self.assertEqual(tree.getroot().attrib, rebuilt[name].getroot().attrib)
            self.assertEqual([s.attrib for s in tree.findall("S")],
                             [s.attrib for s in rebuilt[name].findall("S")])

    def write_records(self, path, records):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, self.records[0], delimiter="\t")
            writer.writeheader()
            writer.writerows(records)

    def test_duplicate_or_renumbered_ids_and_empty_sources_fail(self):
        for issue in ("duplicate", "renumbered", "empty"):
            with self.subTest(issue=issue), tempfile.TemporaryDirectory() as folder:
                changed = copy.deepcopy(self.records)
                if issue == "duplicate":
                    changed.append(changed[0])
                elif issue == "renumbered":
                    changed[0]["s_id"] = "S99"
                else:
                    changed[0]["original"] = " "
                path = Path(folder) / "records.tsv"
                self.write_records(path, changed)
                with self.assertRaises(ValueError):
                    build_xml.rows(path)

    def test_migration_is_repeatable_without_changing_source_words(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "records.tsv"
            changed = copy.deepcopy(self.records)
            for row in changed:
                if row["story"] == "maljialjian":
                    row["s_id"] = f"S{row['sequence']}"
            self.write_records(path, changed)
            repair_records.repair(path)
            first = path.read_bytes()
            repair_records.repair(path)
            self.assertEqual(first, path.read_bytes())
            rebuilt = build_xml.rows(path)
            self.assertEqual([(r["original"], r["translation"]) for r in rebuilt],
                             [(r["original"], r["translation"]) for r in self.records])


if __name__ == "__main__":
    unittest.main()
