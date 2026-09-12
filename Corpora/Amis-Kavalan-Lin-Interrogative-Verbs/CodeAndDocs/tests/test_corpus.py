from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from collections import Counter
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_xml", ROOT / "CodeAndDocs/build_xml.py")
assert spec is not None and spec.loader is not None
build = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build
spec.loader.exec_module(build)


def example(language, source_id):
    return next(e for e in build.EXAMPLES if (e.language, e.source_id) == (language, source_id))


def generated(language):
    return build.make_text(language, [e for e in build.admitted_examples() if e.language == language])


class SourceTests(unittest.TestCase):
    def test_complete_numbered_inventory(self):
        self.assertEqual(Counter(e.language for e in build.EXAMPLES), {"Amis": 49, "Kavalan": 47})
        self.assertEqual(sum(e.printed.startswith("* ") for e in build.EXAMPLES), 19)
        self.assertEqual(sum(e.printed.startswith("? ") for e in build.EXAMPLES), 2)
        self.assertEqual(len(build.admitted_examples()), 75)
        with (ROOT / "CodeAndDocs/excluded_source_units.tsv").open(newline="") as handle:
            excluded = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual(len(excluded), 39)
        self.assertEqual({(e.language, e.source_id) for e in build.EXAMPLES if build.exclusion_reason(e)},
                         {(e["source_label"], e["source_id"]) for e in excluded if e["source_label"] in build.LANGUAGES})

    def test_previously_missing_starred_5b_is_evidence_only(self):
        # Printed p.255; distinct occurrence, repeated on p.267 as 28b.
        item = example("Amis", "5b")
        self.assertEqual(item.printed, "* icuwa-en isu mi-saosi k-u cudad?")
        self.assertEqual(item.gloss, "where-PV 2SG.ERG AV-read ABS-CN book")
        self.assertEqual((item.printed_page, item.pdf_page, item.xml_id), (255, 3, ""))
        self.assertNotIn(item, build.admitted_examples())

    def test_translation_parentheses_match_print(self):
        # Printed pp.256 and 277, independently checked in the PDF.
        self.assertEqual(example("Amis", "6a").readings, ("(Somebody) pours water into the cup.",))
        self.assertEqual(example("Kavalan", "52a").readings, ("I do (it) in that way.",))

    def test_footnote_erratum_supersedes_the_body_reading(self):
        item = example("Amis", "14a")
        self.assertEqual(item.translation, "I will tenderise the meat a little.")
        self.assertEqual(item.readings, ("I will tenderise only the meat.",))
        sentence = generated("Amis").find("S[@id='S_amis_011']")
        self.assertEqual([t.text for t in sentence.findall("TRANSL")], list(item.readings))
        self.assertIn("Footnote 6", sentence.get("source"))
        self.assertIn("tuniq-en", item.printed)

    def test_reference_repetitions_keep_locators_and_printed_variants(self):
        self.assertEqual(len(build.REPEAT_TARGETS), 7)
        self.assertEqual(example("Kavalan", "7a").gloss, "<AV>do.what=2SG.ABS just now")
        self.assertEqual(example("Kavalan", "2a").gloss, "<AV>do.what=2SG.ABS just.now")
        sentence = generated("Kavalan").find("S[@id='S_kavalan_001']")
        self.assertIn("2a (printed p. 254", sentence.get("source"))
        self.assertIn("7a (printed p. 257", sentence.get("source"))
        self.assertEqual(sentence.findall("W")[-1].findtext("TRANSL"), "just.now")

    def test_source_spelling_and_gloss_anomalies_are_protected(self):
        self.assertIn("<AV>take", example("Kavalan", "41b").gloss)
        self.assertIn("bite", example("Kavalan", "41b").readings[0])
        self.assertIn("IA-KA-<UM>eat", example("Amis", "19c").gloss)
        self.assertIn("k-u-ra wacu", example("Amis", "25a").printed)

    def test_optional_constituents_have_aligned_variants(self):
        keys = {("Kavalan", "48a"), ("Kavalan", "48b"),
                ("Amis", "49a"), ("Amis", "49b"), ("Amis", "57b"), ("Amis", "57d")}
        actual = {(e.language, e.source_id) for e in build.admitted_examples() if len(build.form_variants(e)) == 2}
        self.assertEqual(actual, keys)
        for key in keys:
            variants = build.form_variants(example(*key))
            self.assertEqual([v.id_suffix for v in variants], ["", "-opt"])
            for variant in variants:
                self.assertEqual(build.alignment_words(variant)[1], "")
        included, omitted = build.form_variants(example("Amis", "49a"))
        self.assertIn("pateli", included.form)
        self.assertNotIn("pateli", omitted.form)
        self.assertIn("put", included.gloss)
        self.assertNotIn("put", omitted.gloss)

    def test_optional_prefix_varies_only_the_word_and_root(self):
        # Printed p.266: (na)quni-an-su has one word and one unchanged gloss.
        for label, meaning in (("24a", "do.what"), ("24b", "do.how")):
            item = example("Kavalan", label)
            self.assertEqual(len(build.form_variants(item)), 1)
            root = build.make_text("Kavalan", [item])
            self.assertEqual(len(root.findall("S")), 1)
            word = root.find("S/W")
            self.assertEqual([(f.text, f.get("ver")) for f in word.findall("FORM")],
                             [("naquni-an-su", None), ("quni-an-su", "alt")])
            morphemes = word.findall("M")
            self.assertEqual([(f.text, f.get("ver")) for f in morphemes[0].findall("FORM")],
                             [("naquni", None), ("quni", "alt")])
            self.assertEqual([m.findtext("FORM") for m in morphemes[1:]], ["an", "su"])
            self.assertEqual([m.findtext("TRANSL") for m in morphemes],
                             [meaning, "PV", "2SG.ERG"])
            self.assertEqual(len(root.findall("S/TRANSL")), 1)
            self.assertEqual(root.find("S").get("id"), item.xml_id)

    def test_source_infix_gap_and_clitic_are_preserved(self):
        self.assertEqual(build.aligned_morphemes("q<um>uni", "<AV>do.what"),
                         (["q-uni", "-um-"], ["do.what", "AV"]))
        self.assertEqual(build.aligned_morphemes("quni=isu", "do.what=2SG.ABS"),
                         (["quni", "=isu"], ["do.what", "2SG.ABS"]))

    def test_unknown_segmentation_does_not_create_a_whole_word_morpheme(self):
        variant = build.FormVariant("", "test", "mi-kalat", "mi-kalat", "bite")
        with self.assertRaisesRegex(ValueError, "Unresolved segmented alignment"):
            build.add_word_tiers(ET.Element("S", id="test"), variant)

    def test_word_alignment_failure_is_not_silently_omitted(self):
        variant = build.FormVariant("", "test", "word second", "word second", "gloss")
        with self.assertRaisesRegex(ValueError, "Unresolved source alignment"):
            build.add_word_tiers(ET.Element("S", id="test"), variant)

    def test_correction_and_input_order_do_not_renumber_ids(self):
        original = example("Amis", "1a")
        changed = replace(original, form="mi-maan ci sawmah?")
        one = build.make_text("Amis", [original]).find("S")
        two = build.make_text("Amis", [changed]).find("S")
        self.assertEqual(one.get("id"), "S_amis_001")
        self.assertEqual(two.get("id"), one.get("id"))
        self.assertEqual([n.get("id") for n in one.iter() if n.get("id")],
                         [n.get("id") for n in two.iter() if n.get("id")])
        items = [e for e in build.admitted_examples() if e.language == "Amis"]
        self.assertEqual(build.prettify(build.make_text("Amis", items)),
                         build.prettify(build.make_text("Amis", list(reversed(items)))))

    def test_protected_corpus_inventory_and_machine_tier_ownership(self):
        # Kavalan's two redundant 24a/b spellings now share their existing W/M.
        for language, sentences, words, morphemes in (("Amis", 38, 179, 254), ("Kavalan", 36, 157, 236)):
            root = generated(language)
            self.assertEqual(len(root.findall("S")), sentences)
            self.assertEqual(len(root.findall(".//W")), words)
            self.assertEqual(len(root.findall(".//M")), morphemes)
            self.assertEqual(root.get("copyright"), "CC BY 4.0")
            self.assertEqual(root.get("glottocode"), {"Amis": "cent2104", "Kavalan": "kava1241"}[language])
            self.assertEqual(root.findall(".//FORM[@kindOf='standard']"), [])
            self.assertEqual(root.findall(".//PHON"), [])

    def test_final_constituent_brackets_are_original_only(self):
        # Four constituent analyses on printed p.281; standard surfaces omit them.
        for language in ("Amis", "Kavalan"):
            root = ET.parse(ROOT / "XML" / language / f"lin_2015_{language.lower()}_interrogative_verbs.xml").getroot()
            for index in (33, 34):
                sentence = root.find(f"S[@id='S_{language.lower()}_{index:03d}']")
                original = sentence.findtext("FORM[@kindOf='original']")
                standard = sentence.findtext("FORM[@kindOf='standard']")
                self.assertTrue(original.startswith("["))
                self.assertIn("]", original)
                self.assertNotIn("[", standard)
                self.assertNotIn("]", standard)
                phon = sentence.findtext("PHON[@kindOf='original']")
                self.assertNotIn("]]", phon)
                self.assertNotIn("[[", phon)


if __name__ == "__main__":
    unittest.main()
