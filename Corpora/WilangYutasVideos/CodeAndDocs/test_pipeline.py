from __future__ import annotations

import csv
import importlib.util
import sys
import unittest
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
BUILDER_PATH = ROOT / "CodeAndDocs" / "make_xml.py"
SPEC = importlib.util.spec_from_file_location("wilang_make_xml_tests", BUILDER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load {BUILDER_PATH}")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class WilangPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = builder.load_manifest()
        cls.xml: dict[str, etree._Element] = {}
        for row in cls.manifest:
            relative = str(row.output_path.relative_to(ROOT))
            cls.xml[relative] = etree.parse(str(row.output_path)).getroot()

    def test_manifest_covers_exact_canonical_tree(self) -> None:
        expected = {str(row.output_path.relative_to(ROOT)) for row in self.manifest}
        actual = {
            str(path.relative_to(ROOT)) for path in sorted((ROOT / "XML").rglob("*.xml"))
        }
        self.assertEqual(expected, actual)
        self.assertEqual(len(expected), 82)
        self.assertEqual(sum(row.source_path is not None for row in self.manifest), 34)
        self.assertEqual(sum(bool(row.audio_only_file) for row in self.manifest), 48)

    def test_all_pinned_sources_match_manifest(self) -> None:
        for row in self.manifest:
            if row.source_path is not None:
                builder.verify_source(row)

    def test_every_source_line_has_an_explicit_role(self) -> None:
        totals = builder.SourceStats(0, 0, 0, 0, 0)
        for row in self.manifest:
            if row.source_path is None:
                continue
            _, stats = builder.parse_source(row.source_path)
            totals = builder.SourceStats(
                totals.timestamp_lines + stats.timestamp_lines,
                totals.included_entries + stats.included_entries,
                totals.blank_entries + stats.blank_entries,
                totals.translation_lines + stats.translation_lines,
                totals.continuation_lines + stats.continuation_lines,
            )
        self.assertEqual(totals, builder.SourceStats(6455, 3014, 3441, 237, 5))

    def test_sentence_and_audio_mapping_matches_pinned_sources(self) -> None:
        total_sentences = 0
        for row in self.manifest:
            root = self.xml[str(row.output_path.relative_to(ROOT))]
            self.assertEqual(root.get("id"), row.output_path.stem)
            self.assertEqual(root.get("audio"), f"https://www.youtube.com/watch?v={row.video_id}")
            if row.source_path is None:
                self.assertEqual(len(root.findall("S")), 0)
                self.assertEqual(
                    [audio.get("file") for audio in root.findall("AUDIO")],
                    [row.audio_only_file],
                )
                continue
            entries, _ = builder.parse_source(row.source_path)
            included = [(index, entry) for index, entry in enumerate(entries) if entry.text]
            sentences = root.findall("S")
            self.assertEqual(len(sentences), len(included))
            total_sentences += len(sentences)
            for number, (sentence, (raw_index, entry)) in enumerate(
                zip(sentences, included, strict=True), start=1
            ):
                sentence_id = f"Atayal_{number}"
                self.assertEqual(sentence.get("id"), sentence_id)
                audio = sentence.find("AUDIO")
                self.assertIsNotNone(audio)
                self.assertEqual(audio.get("start"), entry.start)
                expected_end = entries[raw_index + 1].start if raw_index + 1 < len(entries) else None
                self.assertEqual(audio.get("end"), expected_end)
                self.assertEqual(
                    audio.get("file"), f"{row.output_path.stem}_{sentence_id}.wav"
                )
        self.assertEqual(total_sentences, 3014)

    def test_original_and_standard_forms_are_parallel(self) -> None:
        for root in self.xml.values():
            for sentence in root.findall("S"):
                original = sentence.find("FORM[@kindOf='original']")
                standard = sentence.find("FORM[@kindOf='standard']")
                self.assertIsNotNone(original)
                self.assertIsNotNone(standard)
                self.assertEqual(etree.tostring(original), etree.tostring(standard).replace(b'standard', b'original', 1))
                self.assertEqual(len(sentence.findall("PHON")), 2)
                self.assertIsNone(sentence.find("W"))

    def test_wrapped_source_continuations_are_retained(self) -> None:
        retained = (
            "llyung qutux nha qalang Truku",
            "raral ga. aw ay.",
            "yasa gluw naga i sazing..magal hi ga",
            "lasa hiya. syogun syogu ga Rato gun sami hiya",
            "hazi tunux mamu kya uzi pi",
        )
        corpus_text = "\n".join(
            "".join(root.itertext()) for root in self.xml.values()
        )
        for text in retained:
            self.assertIn(text, corpus_text)

    def test_source_bopomofo_is_preserved(self) -> None:
        path = (
            "XML/Atayal/"
            "20190407_Yutas_Wilang_di4duan_Lowsing_Watan_MVI_1702_yiwancheng.xml"
        )
        sentence = self.xml[path].find("S[@id='Atayal_28']")
        self.assertIsNotNone(sentence)
        original = sentence.find("FORM[@kindOf='original']")
        standard = sentence.find("FORM[@kindOf='standard']")
        self.assertIn("摸ㄇ", original.text or "")
        self.assertIn("摸ㄇ", standard.text or "")

    def test_issue_one_has_exact_complete_disposition(self) -> None:
        with (ROOT / "CodeAndDocs" / "issue_1_review.tsv").open(
            encoding="utf-8", newline=""
        ) as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        self.assertEqual([int(row["finding"]) for row in rows], list(range(1, 22)))
        for row in rows[:20]:
            root = self.xml[row["output_path"]]
            sentence = root.find(f"S[@id='{row['s_id']}']")
            self.assertIsNotNone(sentence)
            form_text = "".join(sentence.find("FORM[@kindOf='original']").itertext())
            self.assertTrue(any(ord(character) > 127 for character in form_text))
        fixed = self.xml[rows[20]["output_path"]].find("S[@id='Atayal_110']")
        self.assertIsNotNone(fixed)
        self.assertIsNone(fixed.find("TRANSL"))
        self.assertIn("(再確認)", fixed.find("FORM[@kindOf='original']").get("notes", ""))

    def test_editorial_rechecks_are_not_free_translation_text(self) -> None:
        path = (
            "XML/Atayal/"
            "muqianxianzuozhepian_20160525_binkafeifangtan_Yutas_Wilang_"
            "muqianxianzuozhepian.xml"
        )
        root = self.xml[path]
        translations = root.findall(".//TRANSL")
        self.assertFalse(any((transl.text or "").strip() == "(再確認)" for transl in translations))
        noted = [transl for transl in translations if "再確認" in transl.get("notes", "")]
        self.assertEqual(len(noted), 2)


if __name__ == "__main__":
    unittest.main()
