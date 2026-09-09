from __future__ import annotations

import csv
import os
import sys
import unittest
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))
import audit_source_alignment as audit  # noqa: E402
import build_xml as build  # noqa: E402

# Independently transcribed from the analyzed rows on PDF pages 39, 40, 42-44.
PARSED = {
    "S_maga_003": ("traɖo", "ŋa"),
    "S_maga_004": ("sakroɖu", "ŋa"),
    "S_maga_007": ("ko", "sa", "tepruu"),
    "S_maga_008": ("i", "sierkɨ"),
    "S_maga_009": ("u", "rgu"),
    "S_maga_010": ("astita", "li"),
    "S_maga_014": ("n", "udu"),
    "S_tona_003": ("siakiaoɖo", "ŋa"),
    "S_tona_004": ("valak", "ili"),
    "S_tona_006": ("ko", "sya", "tiapoy"),
    "S_tona_007": ("i", "siaəkə"),
    "S_tona_008": ("w", "a", "igoʔo"),
    "S_tona_009": ("a", "kakə"),
    "S_tona_011": ("i", "kaʔacə"),
    "S_tona_015": ("ʔaokay", "a"),
}


class CorpusRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.roots = [ET.parse(path).getroot() for path in sorted((ROOT / "XML").rglob("*.xml"))]
        cls.sentences = {s.get("id"): s for r in cls.roots for s in r.findall("S")}

    def test_complete_source_alignment(self):
        self.assertEqual(audit.audit(), [])

    def test_identity_counts_and_languages(self):
        self.assertEqual([(r.get("dialect"), len(r.findall("S"))) for r in self.roots],
                         [("Maolin", 14), ("Dona", 15)])
        self.assertEqual(sum(len(s.findall("W")) for s in self.sentences.values()), 102)
        self.assertEqual(sum(len(s.findall("W/M")) for s in self.sentences.values()), 69)
        self.assertEqual(sum(len(s.findall("TRANSL")) for s in self.sentences.values()), 34)
        for r in self.roots:
            self.assertEqual(r.get("{http://www.w3.org/XML/1998/namespace}lang"), "dru")
            self.assertEqual(r.get("copyright"), "CC BY-NC-SA 4.0")

    def test_exact_source_parsing_and_mirror_omissions(self):
        for sid, s in self.sentences.items():
            if sid not in PARSED:
                self.assertEqual(s.findall("W/M"), [], sid)
                continue
            self.assertTrue(all(w.findall("M") for w in s.findall("W")), sid)
            parsed = [w for w in s.findall("W") if len(w.findall("M")) > 1]
            self.assertEqual(len(parsed), 1, sid)
            self.assertEqual(tuple(m.findtext("FORM[@kindOf='original']") for m in parsed[0].findall("M")), PARSED[sid])

    def test_source_blank_words_have_no_invented_gloss(self):
        words = {w.get("id"): w for s in self.sentences.values() for w in s.findall("W")}
        self.assertEqual({wid for wid, w in words.items() if not w.findall("TRANSL")}, audit.BLANKS)
        for wid in audit.BLANKS:
            self.assertFalse(words[wid].findall("M/TRANSL"))
        self.assertFalse(any(t.text == "?" for r in self.roots for t in r.iter("TRANSL")))

    def test_tona_nine_preserves_boundary_without_guessing_morpheme_meanings(self):
        s = self.sentences["S_tona_009"]
        self.assertEqual(s.findtext("FORM[@kindOf='original']"), "akakə ka wakanə na bələbələ.")
        w = s.find("W")
        self.assertEqual(w.findtext("FORM[@kindOf='original']"), "a-kakə")
        self.assertEqual(w.findtext("TRANSL"), "1S.TOP")
        self.assertEqual([m.findtext("FORM[@kindOf='original']") for m in w.findall("M")], ["a", "kakə"])
        self.assertFalse(w.findall("M/TRANSL"))

    def test_tona_four_keeps_expert_join_and_multiword_gloss(self):
        s = self.sentences["S_tona_004"]
        self.assertEqual(s.findtext("FORM[@kindOf='original']"), "saokwamamitə valakili.")
        self.assertEqual([w.get("id") for w in s.findall("W")], ["S_tona_004_W_001", "S_tona_004_W_003"])
        w = s.find("W")
        self.assertEqual(w.findtext("FORM[@kindOf='original']"), "saokwamamitə")
        for node in (w, w.find("M")):
            self.assertEqual([(t.get("kindOf"), t.text) for t in node.findall("TRANSL")],
                             [("original", "very fat"), ("standard", "very.fat")])

    def test_expert_retroflex_and_literal_translation_survive(self):
        forms = [s.findtext("FORM[@kindOf='original']") for s in self.sentences.values()]
        self.assertEqual(sum(f.count("ɖ") for f in forms), 9)
        self.assertFalse(any("ḍ" in f for f in forms))
        s = self.sentences["S_tona_015"]
        self.assertEqual([(t.text, t.get("ver"), t.get("notes")) for t in s.findall("TRANSL")],
                         [("I asked him to come tomorrow.", None, None),
                          ('"Come tomorrow," I said to him.', "alt", "literal translation")])

    def test_source_notation_and_word_glosses_remain(self):
        self.assertEqual(self.sentences["S_maga_009"].findtext("W/TRANSL"), "ACT/REAL-know")
        self.assertEqual(self.sentences["S_maga_009"].findtext("TRANSL"), "Kanaw knows (how to) swim.")
        self.assertEqual(self.sentences["S_maga_013"].findtext("TRANSL"), "He forgot (his) keys at home.")
        self.assertEqual(self.sentences["S_tona_014"].findtext("TRANSL"), "Takanao went to eat the banana.")
        self.assertEqual(self.sentences["S_tona_014"].findall("W")[2].findtext("FORM[@kindOf='original']"), "takanaw")

    def test_derived_tiers_are_complete_and_have_no_failure_markers(self):
        for r in self.roots:
            for node in r.iter():
                if node.tag not in {"S", "W", "M"}:
                    continue
                for tag in ("FORM", "PHON"):
                    self.assertEqual({x.get("kindOf") for x in node.findall(tag)}, {"original", "standard"})
                self.assertTrue(all("*" not in (p.text or "") for p in node.findall("PHON")))
            self.assertFalse(r.findall("S/TRANSL[@kindOf]"))
        self.assertFalse((ROOT / "Final_XML").exists())

    def test_text_correction_does_not_change_source_identity(self):
        original = build.make_text(build.MAGA)
        example = replace(build.MAGA.examples[2], form="traɖo-ŋa musu!")
        changed = build.make_text(replace(build.MAGA, examples=(example,)))
        before = original.find("S[@id='S_maga_003']")
        after = changed.find("S")
        self.assertEqual([n.get("id") for n in before.iter() if n.get("id")],
                         [n.get("id") for n in after.iter() if n.get("id")])

    def test_scoped_source_scrape_exception(self):
        from lxml import etree

        fb = Path(os.environ["FORMOSANBANK_ROOT"])
        sys.path.insert(0, str(fb))
        from QC.validation.rules.gloss_scrape import g001_marker_skeleton_parity

        findings = []
        for path in sorted((ROOT / "XML").rglob("*.xml")):
            findings.extend(g001_marker_skeleton_parity(etree.parse(str(path)), path))
        self.assertEqual([(f.rule_id, f.location, f.count) for f in findings],
                         [("G001", "S=S_tona_009 W=S_tona_009_W_001", 1)])

    def test_all_pdf_pages_have_explicit_scope(self):
        with (ROOT / "CodeAndDocs/source_page_coverage.tsv").open(newline="") as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        pages = []
        for row in rows:
            limits = [int(x) for x in row["page_range"].split("-")]
            pages.extend(range(limits[0], limits[-1] + 1))
        self.assertEqual(pages, list(range(1, 47)))
        self.assertEqual(sum(int(r["corpus_units"]) for r in rows), 29)


if __name__ == "__main__":
    unittest.main()
