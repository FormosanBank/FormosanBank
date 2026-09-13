from __future__ import annotations

import copy
import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))
sys.path.insert(0, os.environ["FORMOSANBANK_ROOT"])

pipeline = importlib.import_module("generate_xml")
helpers = importlib.import_module("moedict_formosanbank")
snapshot = importlib.import_module("source_snapshot")
dedup = importlib.import_module("QC.cleaning.remove_duplicate_sentences")


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.corpus, cls.records, cls.rejected = pipeline.safolu_corpus()
        cls.by_id = {row.sentence_id: row for row in cls.records}

    def test_every_source_field_is_accounted_for(self):
        represented = {row.notes["source_ordinal"] for row in self.records}
        excluded = {row["source_ordinal"] for row in self.rejected}
        self.assertFalse(represented & excluded)
        self.assertEqual(represented | excluded, set(range(1, 49420)))
        self.assertEqual(len(self.by_id), len(self.records))

    def test_same_spelling_different_meanings_survive(self):
        first, second = self.by_id["S00110"], self.by_id["S00112"]
        self.assertEqual(first.form, "O 'a'atalen ko felac.")
        self.assertEqual(first.form, second.form)
        self.assertNotEqual(first.translations, second.translations)
        tree = helpers.build_text_tree(self.corpus, [first, second])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.xml"
            tree.write(path, encoding="utf-8")
            self.assertEqual(dedup.plan_removals(str(path), tier="original"), [])

    def test_true_repeated_reference_example_uses_shared_dedup(self):
        tree = helpers.build_text_tree(self.corpus, [self.by_id["S00058"], self.by_id["S00060"]])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.xml"
            tree.write(path, encoding="utf-8")
            plan = dedup.plan_removals(str(path), tier="original")
            self.assertEqual([(row[1], row[3]) for row in plan], [("S00060", "S00058")])

    def test_quoted_japanese_is_source_content(self):
        row = self.by_id["S35031"]
        self.assertEqual(row.form, "O nani 番人 a sowal no Dipon ko Pangcah hananay.")
        self.assertEqual(row.translations[0].text, "Pangcah 是由日語番人諧音的借詞。")

    def test_panay_remains_the_chinese_subject(self):
        row = self.by_id["S14824"]
        self.assertEqual(row.form, "Mangalay ci Panay a malakangkofo.")
        self.assertEqual(row.translations[0].text, "Panay.想當護士。")

    def test_attested_pronunciations_are_same_tier_variants(self):
        expected = {
            "S04848": ("'efa", "'fa", "馬"),
            "S04848-opt": ("enem", "'nem", "六"),
            "S07063": ("sapihpih", "sapiehpieh", "扇子。"),
            "S07064": ("tefi'", "tefie'h", "肩豆。"),
        }
        for sid, (base, variant, translation) in expected.items():
            row = self.by_id[sid]
            self.assertEqual((row.form, row.variants, row.translations[0].text), (base, (variant,), translation))
            sentence = helpers.build_text_tree(self.corpus, [row]).getroot().find("S")
            self.assertEqual([f.attrib for f in sentence.findall("FORM")], [
                {"kindOf": "original"}, {"kindOf": "original", "ver": "alt"},
            ])

    def test_word_alternatives_keep_the_published_base(self):
        for ordinal in (41674, 42031):
            base = f"S{ordinal}"
            self.assertIn(base, self.by_id)
            self.assertIn(base + "-opt", self.by_id)
            self.assertIn(base + "-opt3", self.by_id)
            self.assertNotIn(base + "_1", self.by_id)
        self.assertEqual(self.by_id["S32641-opt"].form, "Malecad a nengnengen ko samado ato panay.")

    def test_existing_published_expansion_ids_do_not_move(self):
        mapping = json.loads((ROOT / "CodeAndDocs/legacy_expansion_ids.json").read_text())
        for ordinal, ids in mapping.items():
            self.assertEqual([row.sentence_id for row in self.records if row.notes["source_ordinal"] == int(ordinal)], ids)

    def test_explicit_lexical_alternatives_keep_both_source_readings(self):
        expected = {
            "S07828": [("O Kafalan a finacadan ko fai ako.", "我的舅媽是噶瑪蘭族人。"), ("O Kafalan a tamdaw ko fai ako.", "我的舅媽是噶瑪蘭族人。")],
            "S29374": [("Misafadasan a misanga' ko cokowi.", "桌子做成四方形。"), ("Misafadasan a misanga' ko parad.", "桌子做成四方形。")],
            "S39092": [("Rakis ko 'irang.", "流血。"), ("Rakis ko remes.", "流血。")],
            "S01889": [("O 'Arikaya ko 'ada no 'Amis.", "'Arikaya是阿美族人的敵人。"), ("O 'Arikaya ko 'ada no Pangcah.", "'Arikaya是阿美族人的敵人。")],
            "S29086": [("Misa'osi to tilid.", "讀書。"), ("Misa'osi to cudad.", "讀書。")],
            "S42869": [("Sapikilidongaw ako to fail i aikor no 'ongcoy.", "我想在岩石後面避一避風。"), ("Sapikilidongaw ako to orad i aikor no 'ongcoy.", "我想在岩石後面避一避雨。")],
            "S42957": [("Sapikonis a faktaw.", "劃線的墨汁具。"), ("Sapikonis a saditek.", "劃線的墨汁具。")],
        }
        for sid, readings in expected.items():
            with self.subTest(source=sid):
                records = [self.by_id[sid], self.by_id[sid + "-opt"]]
                self.assertEqual([(r.form, r.translations[0].text) for r in records], readings)
                self.assertEqual([r.variants for r in records], [(), ()])
                self.assertEqual(records[0].raw_example, records[1].raw_example)

    def test_optional_words_change_the_sentence_inventory(self):
        self.assertEqual(self.by_id["S11242"].form, "Limaay a lefot ko pitilidan niyam.")
        self.assertEqual(self.by_id["S11242-opt"].form, "Limaay a lefot ko tamdaw no pitilidan niyam.")
        self.assertEqual(self.by_id["S11242"].variants, ())

    def test_override_rejects_changed_source(self):
        row = copy.deepcopy(next(row for row in snapshot.load_rows() if row["source_ordinal"] == 14824))
        row["raw_example"] = row["raw_example"].replace("想當護士", "有改動")
        with self.assertRaisesRegex(ValueError, "no longer matches upstream"):
            pipeline.extract_generated_moedict_examples([row], self.corpus.text_id, "zho", "eng", {"14824": pipeline.load_source_overrides()["14824"]})

    def test_unresolved_readings_and_prior_corrections_are_preserved(self):
        self.assertEqual(self.by_id["S00006"].form, "Ini ko 'a'acawen a nanom (nanum).")
        self.assertEqual(self.by_id["S37193"].translations[0].text, "銀行是提款的地方。")
        self.assertIn(35128, {row["source_ordinal"] for row in self.rejected})


if __name__ == "__main__":
    unittest.main()
