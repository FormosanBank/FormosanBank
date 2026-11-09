from __future__ import annotations

import csv
import re
import sys
import unittest
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))

import build_xml  # noqa: E402


class ChangLedgerAndBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.units = build_xml.load_source_units()
        cls.included = [unit for unit in cls.units if unit.decision == "include"]
        cls.by_id = {unit.unit_id: unit for unit in cls.units}
        cls.groups = build_xml.group_source_units(cls.units)
        cls.decisions = build_xml.load_variant_decisions(cls.units)
        with build_xml.SOURCE_COVERAGE.open(encoding="utf-8", newline="") as handle:
            cls.coverage = list(csv.DictReader(handle, delimiter="\t"))
        cls.root = ET.parse(build_xml.OUT_XML).getroot()
        cls.sentences = cls.root.findall("S")
        cls.primary_sentences = [
            sentence for sentence in cls.sentences if "accepted source alternative" not in sentence.get("source", "")
        ]
        cls.variant_sentences = [
            sentence for sentence in cls.sentences if "accepted source alternative" in sentence.get("source", "")
        ]

    def test_source_inventory_and_grouping(self) -> None:
        # 755 transcribed units + 14 examples added after review: 30b, footnotes 31-i and 13 (2026-11-06); nine
        # from the phonology chapter and footnote 41's two answers (2026-11-07).
        self.assertEqual(len(self.units), 769)
        self.assertEqual(sum(unit.added for unit in self.units), 14)
        self.assertEqual(
            Counter(unit.decision for unit in self.units),
            {"include": 492, "exclude": 277},
        )
        self.assertEqual(
            sum(unit.unit_type == "vocabulary_entry" for unit in self.units), 277
        )
        self.assertEqual(len({unit.unit_id for unit in self.units}), 769)
        self.assertEqual(len({unit.source_order for unit in self.units}), 769)
        self.assertEqual(len(self.groups), 450)
        self.assertEqual(sum(len(group) > 1 for group in self.groups), 36)
        self.assertEqual(sum(len(group) - 1 for group in self.groups), 42)

    def test_all_pdf_pages_have_verified_coverage(self) -> None:
        self.assertEqual(
            [row["pdf_page"] for row in self.coverage],
            [f"{page:03d}" for page in range(1, 123)],
        )
        self.assertTrue(
            all(
                row["coverage_status"] == "verified_against_rendered_scan"
                for row in self.coverage
            )
        )
        included = sum(
            int(row["included_left"]) + int(row["included_right"])
            for row in self.coverage
        )
        vocabulary = sum(
            int(row["vocabulary_left"]) + int(row["vocabulary_right"])
            for row in self.coverage
        )
        self.assertEqual((included, vocabulary), (478, 277))

    def test_variant_ledger_covers_every_printed_alternative(self) -> None:
        self.assertEqual(len(self.decisions), 22)
        self.assertEqual(
            Counter(row.decision for row in self.decisions.values()),
            {
                "include": 12,
                "word_variant": 8,
                "exclude_analysis_notation": 1,
                "exclude_unacceptable": 1,
            },
        )

    def test_output_inventory_and_tier_ownership(self) -> None:
        self.assertEqual(len(self.sentences), 461)
        self.assertEqual(len(self.primary_sentences), 450)
        self.assertEqual(len(self.variant_sentences), 11)
        self.assertEqual(len(self.root.findall(".//W")), 1661)
        self.assertEqual(len(self.root.findall(".//M")), 2502)
        # 8 of the FORMs are a word's second FORM (ver="alt"); the schema gives PHON no ver, so it has no PHON.
        self.assertEqual(len(self.root.findall(".//FORM[@kindOf='original']")), 4632)
        self.assertEqual(len(self.root.findall(".//PHON[@kindOf='original']")), 4624)
        # The standard tier (standardize.py, Kavalan_TaiwanNandao_113.tsv): one standard FORM per original FORM, and
        # standard PHON wherever there is original PHON.
        self.assertEqual(len(self.root.findall(".//FORM[@kindOf='standard']")), 4632)
        self.assertEqual(len(self.root.findall(".//PHON[@kindOf='standard']")), 4624)
        self.assertEqual(self.root.findall(".//FORM[@kindOf='alternate']"), [])
        self.assertFalse(
            any("*" in (phon.text or "") for phon in self.root.findall(".//PHON[@kindOf='original']"))
        )
        # Ortho113 Kavalan has no o, so the o of miaori(q) is '*' in standard PHON: 3 sentences x S, W and M.
        self.assertEqual(
            sum("*" in (phon.text or "") for phon in self.root.findall(".//PHON[@kindOf='standard']")), 9
        )

    def test_translation_kind_is_owned_by_level(self) -> None:
        for sentence in self.sentences:
            for translation in sentence.findall("TRANSL"):
                self.assertIsNone(translation.get("kindOf"), sentence.get("id"))
        for tag in ("W", "M"):
            for element in self.root.findall(f".//{tag}"):
                for translation in element.findall("TRANSL"):
                    self.assertEqual(
                        translation.get("kindOf"), "original", element.get("id")
                    )

    def test_primary_sentences_match_reviewed_groups(self) -> None:
        self.assertEqual(len(self.primary_sentences), len(self.groups))
        for sentence, group in zip(self.primary_sentences, self.groups, strict=True):
            unit = group[0]
            self.assertEqual(sentence.get("id"), build_xml.sentence_id(unit))
            chinese = sentence.findtext("TRANSL[@xml:lang='zho']", default="", namespaces={"xml": build_xml.XML_NS})
            self.assertEqual(
                sentence.findtext("FORM[@kindOf='original']"),
                # Infixes in angle brackets in the sentence line too (maintainer, audit round 1, 2026-11-09).
                build_xml.end_sentence(build_xml.sentence_line(build_xml.normalize_surface_form(unit)),
                                       chinese).translate(build_xml.TO_ASCII),
            )
            source = sentence.get("source", "")
            for occurrence in group:
                self.assertIn(occurrence.unit_id, source)

    def test_accepted_alternatives_are_sibling_sentences_or_word_variants(self) -> None:
        variants = {
            sentence.findtext("FORM[@kindOf='original']"): sentence
            for sentence in self.variant_sentences
        }
        self.assertIn("turu ay wasu.", variants)
        self.assertIn("tani tasaw.", variants)
        for sentence in variants.values():
            self.assertIn("accepted source alternative", sentence.get("source", ""))
        # Eight alternative sentences have words, from their example's printed gloss line (maintainer, round 5,
        # 2026-11-08; build_xml.ALTERNATIVE_WORD_GLOSSES); 28's =b. and =c. have none yet.
        def words(sentence):
            return [(w.findtext("FORM"), w.findtext("TRANSL"),
                     " · ".join(f"{m.findtext('FORM')} {m.findtext('TRANSL')}" for m in w.findall("M")))
                    for w in sentence.findall("W")]
        self.assertEqual({form: words(s) for form, s in variants.items()}, {
            "turu ay wasu.": [("turu", "三", "turu 三"), ("ay", "關係詞", "ay 關係詞"), ("wasu", "狗", "wasu 狗")],
            "tani tasaw.": [("tani", "多少", "tani 多少"), ("tasaw", "年", "tasaw 年")],
            "saku zau, wasu wi'u.": [("saku", "貓", "saku 貓"), ("zau,", "這", "zau 這"), ("wasu", "狗", "wasu 狗"),
                                     ("wi'u", "那", "wi'u 那")],
            "razat 'nay.": [("razat", "人", "razat 人"), ("'nay", "那", "'nay 那")],
            "'nay ay razat.": [("'nay", "那", "'nay 那"), ("ay", "關係詞", "ay 關係詞"), ("razat", "人", "razat 人")],
            "zaku ay bawa'.": [("zaku", "我的", "zaku 我的"), ("ay", "關係詞", "ay 關係詞"), ("bawa'", "船", "bawa' 船")],
            "bawa' zaku.": [("bawa'", "船", "bawa' 船"), ("zaku", "我的", "zaku 我的")],
            "Ramar-an na ti-tama ti-tina ya tamun.": [
                ("Ramar-an", "煮-PF", "Ramar 煮 · an PF"), ("na", "屬格", "na 屬格"),
                ("ti-tama", "類別詞-父親", "ti 類別詞 · tama 父親"), ("ti-tina", "類別詞-母親", "ti 類別詞 · tina 母親"),
                ("ya", "主格", "ya 主格"), ("tamun", "菜", "tamun 菜")],
            "qan-ika Raaq!": [("qan-ika", "吃-祈使詞（PF）", "qan 吃 · ika 祈使詞（PF）"), ("Raaq", "酒", "Raaq 酒")],
            "'etung-ika tenayan!": [("'etung-ika", "殺-祈使詞（PF）", "'etung 殺 · ika 祈使詞（PF）"),
                                    ("tenayan", "竹子", "tenayan 竹子")],
            "mana tengen a irip-su?": [("mana", "為什麼", "mana 為什麼"), ("tengen", "髒兮兮", "tengen 髒兮兮"),
                                       ("a", "主格", "a 主格"), ("irip-su", "身體-你的", "irip 身體 · su 你的")],
        })
        # The alternatives the maintainer named (round 4, 2026-11-07) are a second FORM on the word that varies, not
        # sentences: ya/a x5, Ranaw/Rakana x2, timayku/an.
        self.assertNotIn("me-tawa a sunis.", variants)
        self.assertNotIn("naquni a ranas-na kiya, Rakana mai m-utu.", variants)
        variant_forms = {}
        for word in self.root.iter("W"):
            for form in word.findall("FORM"):
                if form.get("ver") is not None:
                    kind = form.get("kindOf")
                    self.assertEqual(form.get("ver"), "alt")
                    self.assertIn(kind, ("original", "standard"))
                    self.assertEqual(
                        len([f for f in word.findall("FORM") if f.get("ver") is None and f.get("kindOf") == kind]), 1
                    )
                    if kind == "original":
                        variant_forms[word.get("id")] = (word.findtext("FORM"), form.text, form.get("notes"))
        # No note: ver="alt" says it (maintainer, round 5, 2026-11-08).
        self.assertEqual(variant_forms, {
            "S-p041r-e001W2": ("ya", "a", None), "S-p044l-e001W2": ("ya", "a", None),
            "S-p044l-e002W4": ("ya", "a", None), "S-p044r-e001W4": ("ya", "a", None),
            "S-p044r-e002W4": ("ya", "a", None),
            "S-p096r-e004W5": ("Ranaw", "Rakana", None), "S-p097l-e001W5": ("Ranaw", "Rakana", None),
            "S-p097r-e003W6": ("timayku", "timaykuan", None),
        })
        # The base keeps its pronunciation; the variant has none.
        self.assertEqual(self.root.find(".//W[@id='S-p044l-e001W2']/PHON").text, "ja")

    @staticmethod
    def words_sentence(*forms: str) -> ET.Element:
        sentence = ET.Element("S", {"id": "S-test"})
        for text in forms:
            ET.SubElement(ET.SubElement(sentence, "W"), "FORM", {"kindOf": "original"}).text = text
        return sentence

    def word_variant(self, unit_id: str, alternative: str, decision: str = build_xml.WORD_VARIANT, reason: str = "r"):
        from dataclasses import replace
        unit = replace(self.by_id[unit_id], alternate_forms=alternative)
        normalized = build_xml.normalize_surface_form(unit, alternative)
        return unit, {(unit.unit_id, normalized): build_xml.VariantDecision(unit.unit_id, normalized, decision, "", reason, "", "", "")}

    def test_word_variant_must_differ_in_one_word(self) -> None:
        """A word_variant alternative must differ from the published words in exactly one word: two differing
        words, or an extra word, stop the build; one differing word gives one second FORM."""
        published = ("me-tawa", "ya", "sunis")
        for alternative in ("me-tawi a sunis", "me-tawa a sunis zau"):
            unit, decisions = self.word_variant("p044l-e001", alternative)
            with self.assertRaises(ValueError, msg=alternative):
                build_xml.add_word_variants(self.words_sentence(*published), [unit], decisions)
        unit, decisions = self.word_variant("p044l-e001", "me-tawa a sunis")
        sentence = self.words_sentence(*published)
        self.assertEqual(build_xml.add_word_variants(sentence, [unit], decisions), set(decisions))
        self.assertEqual([f.text for f in sentence.find("W[2]").findall("FORM")], ["ya", "a"])

    def test_word_variant_reprinted_is_written_once(self) -> None:
        """An alternative both printings of an example carry (saraq/tengen, pp. 161 and 185) is one second FORM;
        one printing may not make it a word variant and the other a sentence."""
        published = ("mana", "saraq", "a", "irip-su")
        first, d1 = self.word_variant("p090r-e003", "mana tengen a irip-su", reason="p. 161")
        second, d2 = self.word_variant("p102r-e007", "mana tengen a irip-su", reason="p. 185")
        sentence = self.words_sentence(*published)
        self.assertEqual(build_xml.add_word_variants(sentence, [first, second], d1 | d2), set(d1) | set(d2))
        forms = sentence.find("W[2]").findall("FORM")
        self.assertEqual([(f.text, f.get("notes")) for f in forms], [("saraq", None), ("tengen", None)])
        second, d2 = self.word_variant("p102r-e007", "mana tengen a irip-su", decision="include")
        with self.assertRaises(ValueError):
            build_xml.add_word_variants(self.words_sentence(*published), [first, second], d1 | d2)

    def test_non_surface_and_unresolved_alternatives_are_not_emitted(self) -> None:
        forms = {
            sentence.findtext("FORM[@kindOf='original']") for sentence in self.sentences
        }
        self.assertNotIn("nia-niana qan=pa=iku", forms)
        self.assertNotIn("iku", forms)
        self.assertNotIn("Ramar-an na ti-tama ti-tina ya tamun", forms)

    def test_repeated_occurrences_are_consolidated_without_data_loss(self) -> None:
        group = next(group for group in self.groups if len(group) == 5)
        sentence = self.root.find(f"S[@id='S-{group[0].xml_unit_id}']")
        self.assertIsNotNone(sentence)
        self.assertEqual(sentence.get("source", "").count("source unit "), 5)
        gender = self.root.find("S[@id='S-p056r-e001']")
        translations = {
            element.text
            for element in gender.findall(
                "TRANSL[@xml:lang='zho']", namespaces={"xml": build_xml.XML_NS}
            )
        }
        self.assertEqual(translations, {"那菜 upa 她煮了。", "那菜 upa 他煮了。"})

    def test_primary_sentences_have_reviewed_word_tiers(self) -> None:
        for sentence in self.primary_sentences:
            source_words = sentence.findtext(
                "FORM[@kindOf='original']", default=""
            ).split()
            self.assertEqual(len(sentence.findall("W")), len(source_words))
        # Only the three sentences the book does not gloss at all keep unglossed words (ita; footnote 41's
        # tama and tina; POL-061, 2026-10-18); a word left unglossed in a glossed sentence is <UNCLEAR/>.
        self.assertEqual(
            [word.get("id") for word in self.root.findall(".//W") if word.find("TRANSL") is None],
            ["S-p086r-e004W1", "S-p086r-e005W1", "S-p103l-e002W1"],
        )

    def test_morpheme_forms_follow_source_segmentation(self) -> None:
        infix_words, circumfix_words = [], []
        for word in self.root.findall(".//W"):
            form = word.findtext("FORM[@kindOf='original']", default="")
            morphs = word.findall("M")
            morph_forms = [
                morph.findtext("FORM[@kindOf='original']", default="")
                for morph in morphs
            ]
            infixes = [part for part in morph_forms if re.fullmatch(r"-[^-]+-", part)]
            root_gaps = [
                part for part in morph_forms if re.fullmatch(r"[^-=]+-[^-=]+", part)
            ]
            if infixes:
                infix_words.append(word)
                self.assertEqual((len(infixes), len(root_gaps)), (1, 1))
                # The word FORM writes the infix in angle brackets (POL-014; maintainer, round 5): p<um>ukun.
                bracketed = "<" + infixes[0][1:-1] + ">"
                self.assertIn(bracketed, form, word.get("id"))
                self.assertNotIn(infixes[0], form, word.get("id"))
                self.assertTrue(form.replace(bracketed, "-", 1).startswith(root_gaps[0]), word.get("id"))
            elif root_gaps:
                # A ruled circumfix (ta-an, sa-an) is the only other morpheme written around a gap.
                circumfix_words.append(word.get("id"))
                self.assertIn(root_gaps, (["ta-an"], ["sa-an"]), word.get("id"))
                self.assertEqual(morph_forms.index(root_gaps[0]), 0, word.get("id"))
        self.assertEqual(len(infix_words), 81)
        self.assertEqual(sorted(circumfix_words),
                         sorted(f"S-{unit}W{index}" for unit, index in build_xml.CIRCUMFIX_WORDS))

    def test_reviewer_examples_have_source_backed_morphemes(self) -> None:
        eat = self.root.find("S[@id='S-p040r-e001']/W[@id='S-p040r-e001W1']")
        self.assertEqual(
            [m.findtext("FORM[@kindOf='original']") for m in eat.findall("M")],
            ["q-an", "-em-"],
        )
        self.assertEqual(
            [m.findtext("TRANSL") for m in eat.findall("M")], ["吃", "AF"]
        )
        completed = self.root.find(
            "S[@id='S-p076l-e001']/W[@id='S-p076l-e001W2']"
        )
        self.assertEqual(
            [m.findtext("FORM[@kindOf='original']") for m in completed.findall("M")],
            ["t-ayta", "-n-", "ku"],
        )

    def test_optional_and_constituent_notation_is_not_a_fake_word(self) -> None:
        constituent = self.root.find("S[@id='S-p045r-e002']")
        self.assertEqual(
            constituent.findtext("FORM[@kindOf='original']"),
            "spaR-an-na tu babar-an-ku=ti=isu.",
        )
        self.assertEqual(
            [word.findtext("FORM[@kindOf='original']") for word in constituent.findall("W")],
            ["spaR-an-na", "tu", "babar-an-ku=ti=isu"],
        )
        for sentence in self.primary_sentences:
            form = sentence.findtext("FORM[@kindOf='original']", default="")
            self.assertFalse(any(mark in form for mark in "()[]"))

    def test_alternate_glosses_do_not_create_duplicate_original_translations(self) -> None:
        translated = [
            element
            for tag in ("W", "M")
            for parent in self.root.findall(f".//{tag}")
            for element in parent.findall("TRANSL")
        ]
        self.assertTrue(any("Alternative printed glosses" in (t.get("notes") or "") for t in translated))
        for tag in ("W", "M"):
            for parent in self.root.findall(f".//{tag}"):
                languages = [t.get(build_xml.XML_LANG) for t in parent.findall("TRANSL")]
                self.assertEqual(len(languages), len(set(languages)), parent.get("id"))

    def test_student_review_rulings_are_published(self) -> None:
        """The maintainer's 2026-11-06 rulings on the student review, as published."""
        def gloss(element):
            return "".join(
                [element.text or ""] + [f"<UNCLEAR/>{child.tail or ''}" for child in element]
            ).strip()

        def word(sid, index):
            w = self.root.find(f"S[@id='{sid}']/W[@id='{sid}W{index}']")
            return (gloss(w.find("TRANSL")),
                    [(m.findtext("FORM[@kindOf='original']"), gloss(m.find("TRANSL"))) for m in w.findall("M")])

        # p098r-e003: the book prints a blank, then -你 ("Leave it as ` -你`").
        self.assertEqual(word("S-p098r-e003", 1), ("<UNCLEAR/>-你", [("qeniqian", "<UNCLEAR/>"), ("su", "你")]))
        # Trailing hyphen after AF: the word keeps its root and infix morphemes; the trailing hyphen itself is
        # deleted (ruled 2026-11-07), since 打<AF> names both morphemes.
        self.assertEqual(word("S-p058l-e002", 1), ("打<AF>", [("p-ukun", "打"), ("-um-", "AF")]))
        # p049l-e001: the reviewer's recommendation, with the printed gloss in a note.
        self.assertEqual(word("S-p049l-e001", 1)[0], "處所格-豐濱-處所格=動貌=我")
        self.assertIn("處所格-豐濱=動貌=我", self.root.find("S[@id='S-p049l-e001']/W/TRANSL").get("notes"))
        # Morphemes carry no punctuation (su? -> su); words keep it.
        self.assertEqual(word("S-p075l-e003", 3)[1], [("tasaw", "年"), ("su", "你的")])
        self.assertEqual(self.root.findtext("S[@id='S-p075l-e003']/W[@id='S-p075l-e003W3']/FORM"), "tasaw-su?")
        # The #-marked translation of p041l-e001 is gone; the = mark is removed.
        p041 = self.root.find("S[@id='S-p041l-e001']")
        self.assertEqual([gloss(t) for t in p041.findall("TRANSL")], ["utay 在打 tuyaw。"])
        # Every one of the student's 125 notes is published on its sentence.
        published = sum((s.find("FORM").get("notes") or "").count(build_xml.REVIEW_NOTE_PREFIX)
                        for s in self.sentences)
        self.assertEqual(published, 125)
        # The three examples added from the scan.
        thirty_b = self.root.find("S[@id='S-p059r-e002']")
        self.assertEqual([gloss(t) for t in thirty_b.findall("TRANSL")], ["我的東西我知道。", "我認得出我的東西。"])
        self.assertEqual(self.root.find("S[@id='S-p059r-e003']").findall("TRANSL"), [])
        self.assertEqual(self.root.findtext("S[@id='S-p042l-e005']/FORM"), "kin-turu a sunis.")
        # Sentences and translations end in the script's period; parentheses by script.
        song = {f"S-{u}" for u in build_xml.SONG_LINE_COMMA_UNITS}
        for sentence in self.sentences:
            in_song = sentence.get("id") in song
            self.assertIn(sentence.findtext("FORM")[-1], "," if in_song else ".?!", sentence.get("id"))
            for t in sentence.findall("TRANSL"):
                self.assertIn(gloss(t)[-1], "，" if in_song else "。？！", sentence.get("id"))
        self.assertFalse(any(ch in "()" for t in self.root.iter("TRANSL") for ch in gloss(t)))
        for form in self.root.iter("FORM"):
            self.assertFalse(any(ch in "（）【】[]ₛᵢⱼₖ" for ch in form.text or ""), form.text)
        # Brackets and subscripts are deleted from the Kavalan line, and the old notes saying they are
        # preserved are gone; a note saying what was bracketed is written only with PRINT_NOTES.
        bracketed = ["S-p045r-e002", "S-p094l-e002", "S-p094l-e003", "S-p095l-e001", "S-p095l-e002",
                     "S-p095l-e003", "S-p095l-e004"]
        for sid in bracketed:
            notes = self.root.find(f"S[@id='{sid}']/FORM").get("notes") or ""
            self.assertNotIn("are preserved", notes, sid)
            self.assertEqual("in square brackets" in notes or "in bold brackets" in notes, build_xml.PRINT_NOTES, sid)
        # 6b's true transcription note stays unless the fuller note replaces it.
        self.assertEqual("Brackets are printed constituent notation." in
                         (self.root.find("S[@id='S-p045r-e002']/FORM").get("notes") or ""), not build_xml.PRINT_NOTES)

    def test_fixes_from_the_implementation_review(self) -> None:
        """Defects an independent review of the 2026-11-06 changes found, as fixed."""
        # Where the corpus follows the handwriting, no note says the handwriting is excluded.
        for unit in self.included:
            if unit.form != unit.transcribed_form:
                notes = self.root.find(f"S[@id='S-{unit.xml_unit_id}']/FORM").get("notes") or ""
                self.assertNotIn("handwritten correction is excluded", notes, unit.unit_id)
        p099 = self.root.find("S[@id='S-p099l-e003']/FORM").get("notes")
        self.assertNotIn("pun=ta while", p099)
        self.assertEqual(p099.startswith("The book prints pun-ta, glossed 完-咱們;"), build_xml.PRINT_NOTES)
        # An alternative gloss that comes from her correction says so, not "retained in source_units.tsv".
        notes = self.root.find(".//W[@id='S-p091r-e003W3']/TRANSL").get("notes")
        self.assertIn("as corrected in the 2026-10 review (review_corrections.tsv)", notes)
        # Two of these take their words from the printing she corrected (round 6), so the note gives the first
        # printing's gloss, from the transcription.
        for wid, first in (("S-p039r-e002W1", "一直講"), ("S-p069r-e003W1", "去哪裡=未來式=你")):
            notes = self.root.find(f".//W[@id='{wid}']/TRANSL").get("notes")
            self.assertIn("retained in source_units.tsv: " + first, notes, wid)
        # The fourth, her 打-AF- on p091l-e002, is 打<AF> once its trailing hyphen is deleted: the same gloss as
        # the published one, so no note.
        self.assertIsNone(self.root.find(".//W[@id='S-p055l-e003W2']/TRANSL").get("notes"))
        # Glosses quoted in notes have the same parenthesis width as the glosses.
        labels = ("Alternative printed glosses retained in source_units.tsv: ",
                  "Alternative printed glosses as corrected in the 2026-10 review (review_corrections.tsv): ")
        for tag in ("W", "M"):
            for t in self.root.iter(tag):
                notes = (t.find("TRANSL").get("notes") or "") if t.find("TRANSL") is not None else ""
                listed = notes[notes.find("Alternative printed glosses"):] if "Alternative printed glosses" in notes else ""
                for label in labels:
                    listed = listed.replace(label, "")
                self.assertFalse(any(ch in "()" for ch in listed), t.get("id"))
        # The six song lines keep their final comma, and their Kavalan line ends in one (round 6, 2026-11-08).
        for unit in build_xml.SONG_LINE_COMMA_UNITS:
            sentence = self.root.find(f"S[@id='S-{unit}']")
            self.assertTrue(sentence.findtext("TRANSL").endswith("，"), unit)
            self.assertNotIn("，。", sentence.findtext("TRANSL"), unit)

    def test_guards_for_cases_not_in_todays_data(self) -> None:
        from dataclasses import replace
        # p075r-e005: restoring the printed double hyphen publishes the same word and morphemes.
        unit = self.by_id["p075r-e005"]
        one = build_xml.split_morphemes(unit, 2, "s-n-angi-an-na", "蓋-完成貌-PF-他")
        two = build_xml.split_morphemes(unit, 2, "s-n-angi-an-na", "蓋-完成貌--PF-他")
        self.assertEqual(one, two)
        self.assertEqual(one, [("s-angi", "蓋"), ("-n-", "完成貌"), ("an", "PF"), ("na", "他")])
        self.assertEqual(build_xml.canonical_word_gloss("蓋-完成貌--PF-他", two), "蓋<完成貌>-PF-他")
        # A trailing = after an infix's gloss is kept on the word gloss.
        hit = build_xml.split_morphemes(self.by_id["p058l-e002"], 99, "p-um-ukun", "打-AF=")
        self.assertEqual(build_xml.canonical_word_gloss("打-AF=", hit), "打<AF>=")
        # A trailing empty slot on a longer infixed word is the rest of the root too (as in round 2).
        longer = build_xml.split_morphemes(self.by_id["p058l-e002"], 99, "p-um-ukun=iku", "打-AF=我-")
        self.assertEqual(longer, [("p-ukun", "打"), ("-um-", "AF"), ("=iku", "我")])
        # The trailing-hyphen ruling (2026-11-07) deletes that hyphen first, so the word gloss is 打<AF>=我; a trailing
        # hyphen the ruling keeps would stay on the word gloss.
        self.assertEqual(build_xml.without_redundant_trailing_hyphen("p058l-e002", 99, "p-um-ukun=iku", "打-AF=我-"),
                         "打-AF=我")
        self.assertEqual(build_xml.canonical_word_gloss("打-AF=我", longer), "打<AF>=我")
        self.assertEqual(build_xml.canonical_word_gloss("打-AF=我-", longer), "打<AF>=我-")
        # A translation ending in a comma that is not held stops the build instead of becoming "，。".
        for mark in "，,；;：:、.?!…":
            with self.assertRaises(ValueError):
                build_xml.end_translation("我追" + mark)
        self.assertEqual(build_xml.end_translation(""), "")
        # A handwriting note listed for a unit whose handwriting is not followed stops the build.
        listed = build_xml.HANDWRITING_NOTE_REPLACEMENTS
        saved = dict(listed)
        try:
            listed["p101r-e02"] = listed.pop("p101r-e002")   # a mistyped key
            with self.assertRaises(ValueError):
                build_xml.build_tree(self.units)
        finally:
            listed.clear()
            listed.update(saved)
        self.assertEqual(listed, saved)

        # A ruling applies only to the edit it was made about.
        corrections = build_xml.load_review_corrections()
        changed = {u: dict(f) for u, f in corrections.items()}
        changed["p098r-e003"]["glosses"] = (changed["p098r-e003"]["glosses"][0],
                                            '["小時候-你的", "SI", "AF-坐", "受格", "飛機", "疑問助詞"]')
        with self.assertRaises(ValueError):
            build_xml.adjudicate_corrections(changed, build_xml.load_review_adjudication())
        # A printing with no translation, grouped with one that has one, in either order.
        thirty_b, footnote = self.by_id["p059r-e002"], self.by_id["p059r-e003"]
        for first, second in ((thirty_b, footnote), (footnote, thirty_b)):
            anchor = first.unit_id
            units = [u for u in self.units if u.unit_id not in {thirty_b.unit_id, footnote.unit_id}]
            units += [replace(first, xml_unit_id=anchor, form="supaR-an zaku", gloss=thirty_b.gloss,
                              source_order=595001),
                      replace(second, xml_unit_id=anchor, form="supaR-an zaku", gloss=thirty_b.gloss,
                              source_order=595002)]
            units.sort(key=lambda u: (u.source_order, u.unit_id))
            sentence = build_xml.build_tree(units).getroot().find(f"S[@id='S-{anchor}']")
            texts = [(t.text, t.get("ver")) for t in sentence.findall("TRANSL")]
            self.assertEqual(texts, [("我的東西我知道。", None), ("我認得出我的東西。", "alt")], anchor)
            self.assertNotIn(build_xml.NO_PRINTED_TRANSLATION, sentence.find("FORM").get("notes") or "")
        # A space between two <UNCLEAR/> survives serialization; indentation does not.
        root = ET.Element("TEXT")
        build_xml.set_text(ET.SubElement(root, "FORM"), f"qan {build_xml.UNCLEAR} {build_xml.UNCLEAR} sunis")
        self.assertIn("<FORM>qan <UNCLEAR /> <UNCLEAR /> sunis</FORM>", build_xml.serialize(ET.ElementTree(root)))
        padded = ET.fromstring("<TEXT><TRANSL>\n    <UNCLEAR/>\n  </TRANSL></TEXT>")
        self.assertIn("<TRANSL><UNCLEAR /></TRANSL>", build_xml.serialize(ET.ElementTree(padded)))
        # A song line keeps its final comma (round 6); a parenthesis gets 。 after it.
        self.assertEqual(build_xml.end_translation("我今天晚上要去你家玩，", song_line=True), "我今天晚上要去你家玩，")
        self.assertEqual(build_xml.end_sentence("tantanuz-an-ku", "我追，"), "tantanuz-an-ku,")
        self.assertEqual(build_xml.end_translation("我（受格）"), "我（受格）。")
        # Bracket notes: the kind is per span, and a misquoted span stops the build.
        spans = replace(self.by_id["p095l-e001"], form="a [s b c] [d e]", transcribed_form="a [s b c] [d e]")
        self.assertEqual(build_xml.bracket_note(spans),
                         "The book prints b c in square brackets with a subscript s, [ₛ ]. "
                         "The book prints d e in square brackets [ ].")
        with self.assertRaises(ValueError):
            build_xml.bracket_note(replace(spans, form="a b c", transcribed_form="a [b d]"))
        # The transcription alone, rebuilt with no review data, carries no review notes.
        raw = build_xml.build_tree(build_xml.load_source_units(corrections={}, additions=None),
                                   review=False).getroot()
        self.assertFalse(any(build_xml.REVIEW_NOTE_PREFIX in (f.get("notes") or "") for f in raw.iter("FORM")))
        self.assertEqual((len(raw.findall(".//W")), len(raw.findall(".//M"))), (1636, 2465))

    def test_round3_rulings(self) -> None:
        """The maintainer's round-3 answers (2026-11-07), as published, and the guards that keep them true."""
        def gloss(element):
            if element is None:
                return None
            return "".join([element.text or ""] + [f"<UNCLEAR/>{child.tail or ''}" for child in element]).strip()

        def morphemes(wid):
            w = self.root.find(f".//W[@id='{wid}']")
            return [(m.findtext("FORM[@kindOf='original']"), gloss(m.find("TRANSL"))) for m in w.findall("M")]

        zho = {"xml": build_xml.XML_NS}
        # A Kavalan line ends as its Chinese does: ? after ？, ! after ！, else a period; a printed mark stays.
        ends = Counter()
        for sentence in self.sentences:
            chinese = sentence.findtext("TRANSL[@xml:lang='zho']", default="", namespaces=zho)
            form = sentence.findtext("FORM[@kindOf='original']")
            self.assertEqual(form[-1], build_xml.KAVALAN_END_OF.get(chinese[-1:], "."), sentence.get("id"))
            ends[form[-1]] += 1
        self.assertEqual(ends, {".": 358, "?": 83, "!": 14, ",": 6})
        self.assertEqual(build_xml.end_sentence("niana zau", "這是什麼？"), "niana zau?")
        self.assertEqual(build_xml.end_sentence("tani=ti a tasaw-su?", "幾歲。"), "tani=ti a tasaw-su?")
        # Circumfixes: one morpheme, ta-an or sa-an, then the root, as the circumfix option showed.
        self.assertEqual(morphemes("S-p101r-e006W2"), [("ta-an", "處所格"), ("miaoriq", "苗栗")])
        self.assertEqual(morphemes("S-p100r-e002W2"), [("ta-an", "處所格"), ("paw", "家"), ("su", "你")])
        # The other ta-/sa-...-an words keep two morphemes: those whose -an the book glosses (POL-014's exception),
        # and 18a, which the circumfix answer did not name.
        self.assertEqual(morphemes("S-p048r-e002W2"), [("ta", "處所格"), ("miaori", "苗栗"), ("an", "處所格")])
        self.assertEqual([f for f, _ in morphemes("S-p049l-e001W1")], ["ta", "bakung", "an", "=ti", "=iku"])
        # Trailing hyphens: none is left on a published gloss; one that is not redundant would stay.
        self.assertEqual([t for t in self.root.iter("TRANSL") if (gloss(t) or "").endswith("-")], [])
        self.assertEqual(gloss(self.root.find(".//W[@id='S-p101r-e006W2']/TRANSL")), "處所格-苗栗")
        self.assertEqual(build_xml.without_redundant_trailing_hyphen("x", 1, "pukun-an", "打-PF-"), "打-PF")
        self.assertEqual(build_xml.without_redundant_trailing_hyphen("x", 1, "ta-bakung-an", "處所格-豐濱-"),
                         "處所格-豐濱-")
        self.assertEqual(build_xml.split_morphemes(self.by_id["p049l-e001"], 9, "ta-bakung-an", "處所格-豐濱-"), [])
        # The transcription's note that the gloss keeps the printed trailing hyphen is gone with the hyphen.
        self.assertNotIn("including the trailing hyphen",
                         self.root.find("S[@id='S-p066l-e002']/FORM").get("notes") or "")
        # Book notes: footnote 30 on 20a, example 1's pronunciation.
        self.assertIn(build_xml.BOOK_NOTES["p057l-e001"], self.root.find("S[@id='S-p057l-e001']/FORM").get("notes"))
        self.assertTrue(self.root.find("S[@id='S-p034r-e001']/FORM").get("notes").startswith(
            "Pronunciation given by the book: [puku nanku tia sunis]."))
        # The eleven added examples.
        added = {"S-p035l-e001": "razat a yau.", "S-p035l-e002": "wasu a yau.", "S-p036l-e001": "sunis-su.",
                 "S-p036l-e002": "pukun-an-na.", "S-p036l-e003": "bura-an.", "S-p036l-e004": "kin-tani sunis-su.",
                 "S-p036l-e005": "pukun-an-ku=pa sunis.", "S-p036r-e001": "sum=pa.", "S-p036r-e002": "qmaynep.",
                 "S-p086r-e004": "tama.", "S-p086r-e005": "tina."}
        for sid, form in added.items():
            self.assertEqual(self.root.findtext(f"S[@id='{sid}']/FORM"), form, sid)
        for sid in list(added)[:9]:
            notes = self.root.find(f"S[@id='{sid}']/FORM").get("notes")
            self.assertTrue(notes.startswith("Pronunciation given by the book: ["), sid)
            self.assertTrue(notes.endswith(build_xml.NO_PRINTED_TRANSLATION), sid)
            self.assertEqual(self.root.find(f"S[@id='{sid}']").findall("TRANSL"), [], sid)
        self.assertEqual(morphemes("S-p035l-e001W2"), [("a", "<UNCLEAR/>")])
        for sid, meaning in (("S-p086r-e004", "公的。"), ("S-p086r-e005", "母的。")):
            sentence = self.root.find(f"S[@id='{sid}']")
            self.assertEqual([gloss(t) for t in sentence.findall("TRANSL")], [meaning])
            self.assertEqual(sentence.find("FORM").get("notes"), "Footnote 41: an answer to 10b.")
            self.assertIsNone(sentence.find("W/TRANSL"))
        # Each list a ruling added stops the build when it no longer matches the data.
        for name, stale in (("BOOK_NOTES", {"p999l-e001": "x"}), ("CIRCUMFIX_WORDS", {("p101r-e006", 1)}),
                            ("CIRCUMFIX_WORDS", {("p103l-e002", 1)}),
                            ("UNGLOSSED_LAST_PIECE", {("p101r-e006", 1)}), ("NO_MORPHEME_WORDS", {("p099l-e003", 1)}),
                            ("PROCLITIC_WORDS", {"S-p999l-e001W1"}), ("WORDS_FROM_PRINTING", {"S-p042l-e005": "x"}),
                            ("DROPPED_TRANSCRIPTION_NOTES", {"p099l-e003": ("not a note", "not a note")}),
                            ("SONG_LINE_COMMA_UNITS", {"p042r-e003"}), ("TRAILING_HYPHEN_NOTES", ("Not a note.",)),
                            # decisions_word_glosses.tsv / decisions_morphemes.tsv: a row for an example that does not
                            # exist, and one the build never uses (the student corrected p039l-e002's glosses).
                            ("WORD_GLOSS_OVERRIDES", {"p999l-e001": ("x",)}),
                            ("WORD_GLOSS_OVERRIDES", {"p039l-e002": ("在", "浴室", "洗澡")}),
                            ("MORPHEME_OVERRIDES", {("p999l-e001", 1): (("x", "y"),)}),
                            ("MORPHEME_OVERRIDES", {("p039l-e002", 9): (("x", "y"),)})):
            saved = getattr(build_xml, name)
            if isinstance(saved, dict):
                setattr(build_xml, name, {**saved, **stale})
            elif isinstance(saved, tuple):
                setattr(build_xml, name, saved + stale)
            else:
                setattr(build_xml, name, saved | stale)
            try:
                with self.assertRaises(ValueError, msg=name):
                    build_xml.build_tree(self.units)
            finally:
                setattr(build_xml, name, saved)

    def test_ruled_form_edit_must_apply(self) -> None:
        saved = build_xml.RULED_FORM_EDITS
        build_xml.RULED_FORM_EDITS = {**saved, "p099l-e003": (("not printed", "x"),)}
        try:
            with self.assertRaises(ValueError):
                build_xml.load_source_units()
        finally:
            build_xml.RULED_FORM_EDITS = saved

    def test_round6_rulings(self) -> None:
        """The maintainer's round-6 answers (2026-11-08), as published."""
        def gloss(t):
            return None if t is None else "".join([t.text or ""] + ["<UNCLEAR/>" + (c.tail or "") for c in t]).strip()
        def word(wid):
            return self.root.find(f".//W[@id='{wid}']")
        def morphemes(wid):
            return [(m.findtext("FORM"), gloss(m.find("TRANSL"))) for m in word(wid).findall("M")]
        # sa-kasaw-an: sa 終點 · kasaw 長濱 · an <UNCLEAR/>, word gloss 終點-長濱-<UNCLEAR/>.
        for wid in ("S-p101r-e004W2", "S-p102r-e005W3"):
            self.assertEqual(morphemes(wid), [("sa", "終點"), ("kasaw", "長濱"), ("an", "<UNCLEAR/>")])
            self.assertEqual(gloss(word(wid).find("TRANSL")), "終點-長濱-<UNCLEAR/>")
        # The two locative pronouns, split as p. 80 glosses ti-maisu-an; word glosses as printed.
        self.assertEqual(morphemes("S-p058l-e003W3"), [("ti", "類別詞"), ("maiku", "我"), ("an", "處所格")])
        self.assertEqual(morphemes("S-p058l-e004W3"), [("ta", "處所格"), ("maiku", "我")])
        self.assertEqual(gloss(word("S-p058l-e004W3").find("TRANSL")), "我（處所）")
        # ta-paw-an-su, written with a hyphen in word and sentence, glossed 處所格-家-你.
        self.assertEqual(word("S-p100r-e002W2").findtext("FORM"), "ta-paw-an-su")
        self.assertEqual(self.root.findtext("S[@id='S-p100r-e002']/FORM"), "sasaqay=pa=iku ta-paw-an-su anuqaRabi,")
        self.assertEqual(gloss(word("S-p100r-e002W2").find("TRANSL")), "處所格-家-你")
        # Unglossed words keep one <UNCLEAR/> morpheme, except paqenanum.
        self.assertEqual(morphemes("S-p050l-e001W2"), [])
        self.assertEqual(morphemes("S-p054l-e001W4"), [("a", "<UNCLEAR/>")])
        # A clitic before its word keeps the =.
        self.assertEqual(morphemes("S-p070r-e003W1"), [("qa=", "大概快要"), ("patay", "死")])
        self.assertEqual(morphemes("S-p100r-e003W3"), [("ta=", "處所格"), ("pawan", "家"), ("su", "你")])
        self.assertEqual(sum(1 for m in self.root.iter("M") if (m.findtext("FORM") or "").endswith("=")), 11)
        # Two examples printed twice take their words from the printing she corrected.
        self.assertEqual(morphemes("S-p039r-e002W1"), [("si", "<UNCLEAR/>"), ("kaw", "持續貌"), ("kawma", "說")])
        self.assertEqual(self.root.findtext("S[@id='S-p069r-e003']/FORM"), "quni-pa=isu?")
        self.assertEqual(morphemes("S-p069r-e003W1"), [("quni", "去哪裡"), ("pa", "未來式"), ("=isu", "你")])
        self.assertEqual(word("S-p091r-e003W3").findtext("FORM"), "sunis-su")
        # Alternative sentences: ids, notes, footnote 19.
        ids = sorted(s.get("id") for s in self.variant_sentences)
        self.assertEqual(ids, ["S-p043l-e004-opt", "S-p043r-e001-opt", "S-p047l-e005-ia", "S-p050r-e001-opt",
                               "S-p050r-e002-opt", "S-p050r-e003-opt", "S-p059l-e002-b", "S-p059l-e002-c",
                               "S-p080l-e002-opt", "S-p080l-e003-opt", "S-p090r-e003-opt"])
        # No alternative sentence carries a note (round 6 for 28's; round 7, 2026-11-08: "Drop all eight").
        for sentence in self.variant_sentences:
            self.assertIsNone(sentence.find("FORM").get("notes"), sentence.get("id"))
        # t-n-ayta-ku without the printed (PF) (round 7).
        self.assertEqual(gloss(word("S-p076l-e001W2").find("TRANSL")), "看到<完成貌>-我")
        self.assertEqual(morphemes("S-p076l-e001W2"), [("t-ayta", "看到"), ("-n-", "完成貌"), ("ku", "我")])
        fn19 = self.root.find("S[@id='S-p047l-e005']")
        self.assertNotIn("paired a form", fn19.find("FORM").get("notes"))
        self.assertTrue(fn19.find("FORM").get("notes").startswith("Review (2026-10): "))
        self.assertIsNone(fn19.find("TRANSL").get("notes"))
        # Song lines end in a comma, Kavalan and Chinese alike.
        for unit in build_xml.SONG_LINE_COMMA_UNITS:
            sentence = self.root.find(f"S[@id='S-{unit}']")
            self.assertEqual((sentence.findtext("FORM")[-1], gloss(sentence.find("TRANSL"))[-1]), (",", "，"), unit)

    def test_generated_source_stage_matches_final_xml_without_phon(self) -> None:
        self.assertEqual(build_xml.source_stage_from_generated(), build_xml.render())


if __name__ == "__main__":
    unittest.main()
