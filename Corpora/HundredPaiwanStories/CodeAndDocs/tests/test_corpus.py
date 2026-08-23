from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import tempfile
import unittest
import xml.etree.ElementTree as ET
from copy import deepcopy
from pathlib import Path

from normalize_sentence_standards import (
    DEFAULT_DECISIONS,
    apply_decision,
    current_punctuation,
    load_decisions,
    load_optional_variants,
    normalize,
    optional_original_forms,
)
from scripts.paiwan_source import normalized_letters, parse_docx


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = Path(os.environ.get("PAIWAN_XML_ROOT", ROOT / "XML")).resolve()
REPORTS_ROOT = Path(os.environ.get("PAIWAN_REPORTS_ROOT", ROOT / "reports")).resolve()
SOURCE_ROOT = Path(
    os.environ.get("PAIWAN_SOURCE_ROOT", ROOT / "Private" / "source")
).resolve()
COPYRIGHT = (
    "Author permission allows attributed, non-profit derivative use. "
    "For-profit republication of the source as-is is not permitted."
)
MARKERS = "-=<>~()"


def direct(element: ET.Element, tag: str, kind: str) -> str:
    values = element.findall(f"{tag}[@kindOf='{kind}']")
    if len(values) != 1 or values[0].text is None:
        raise AssertionError(f"missing direct {kind} {tag} in {element.get('id')}")
    return values[0].text


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def xml_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.xml"))
    }


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.paths = sorted(XML_ROOT.rglob("*.xml"))
        cls.roots = {path.name: ET.parse(path).getroot() for path in cls.paths}
        cls.sentences = {
            (filename, sentence.get("id", "")): sentence
            for filename, root in cls.roots.items()
            for sentence in root.findall("S")
        }
        cls.decisions = load_decisions(DEFAULT_DECISIONS)
        cls.decisions_by_id = {row["sentence_id"]: row for row in cls.decisions}
        cls.optional = load_optional_variants()

    def test_inventory_and_global_ids(self) -> None:
        self.assertEqual(len(self.paths), 100)
        counts = {"TEXT": 0, "S": 0, "W": 0, "M": 0}
        identifiers: list[str] = []
        for root in self.roots.values():
            for element in root.iter():
                if element.tag in counts:
                    counts[element.tag] += 1
                if element.get("id"):
                    identifiers.append(element.get("id", ""))
        self.assertEqual(counts, {"TEXT": 100, "S": 2921, "W": 24556, "M": 36938})
        self.assertEqual(len(identifiers), 64515)
        self.assertEqual(len(set(identifiers)), len(identifiers))

    def test_root_metadata_and_rights_are_complete(self) -> None:
        xml_lang = "{http://www.w3.org/XML/1998/namespace}lang"
        for root in self.roots.values():
            self.assertEqual(root.get(xml_lang), "pwn")
            self.assertEqual(root.get("copyright"), COPYRIGHT)
            for attribute in ("id", "citation", "BibTeX_citation", "source", "dialect"):
                self.assertTrue(root.get(attribute), (root.get("id"), attribute))

    def test_every_exact_surface_decision_is_applied(self) -> None:
        self.assertEqual(len(self.decisions), 166)
        for row in self.decisions:
            sentence = self.sentences[(row["file"], row["sentence_id"])]
            expected_original = row["original_form"]
            optional = self.optional.get(row["sentence_id"])
            if optional is not None:
                expected_original, _omitted = optional_original_forms(row, optional)
            actual_original = direct(sentence, "FORM", "original")
            self.assertIn(
                actual_original,
                {expected_original, current_punctuation(expected_original)},
            )
            corrected_standard = row["corrected_standard_form"]
            if current_punctuation(
                expected_original
            ) != expected_original and actual_original == current_punctuation(
                expected_original
            ):
                corrected_standard = current_punctuation(corrected_standard)
            self.assertEqual(direct(sentence, "FORM", "standard"), corrected_standard)
            standard_phon = direct(sentence, "PHON", "standard")
            self.assertFalse(any(marker in standard_phon for marker in MARKERS))
        self.assertFalse(
            any(
                root.findall(".//FORM[@kindOf='alternate']")
                for root in self.roots.values()
            )
        )

    def test_source_hyphens_and_uncertainty_decisions(self) -> None:
        marked = [
            direct(sentence, "FORM", "standard")
            for sentence in self.sentences.values()
            if "-" in direct(sentence, "FORM", "standard")
        ]
        self.assertEqual(len(marked), 153)
        self.assertTrue(any("Yisu-sama" in value for value in marked))
        self.assertTrue(any("Kulje-Pulelelelengan" in value for value in marked))
        self.assertTrue(any("pakazua-u" in value for value in marked))
        for sentence in self.sentences.values():
            standard = direct(sentence, "FORM", "standard")
            self.assertNotIn("(", standard)
            self.assertNotIn(")", standard)

    def test_optional_tokens_are_complete_sentence_variants(self) -> None:
        self.assertEqual(len(self.optional), 5)
        for sentence_id, optional in self.optional.items():
            row = self.decisions_by_id[sentence_id]
            primary = self.sentences[(row["file"], sentence_id)]
            omitted_id = optional["omitted_sentence_id"]
            omitted = self.sentences[(row["file"], omitted_id)]
            included_original, omitted_original = optional_original_forms(row, optional)
            primary_original = direct(primary, "FORM", "original")
            punctuation_cleaned = current_punctuation(
                included_original
            ) != included_original and primary_original == current_punctuation(
                included_original
            )
            self.assertIn(
                primary_original,
                {included_original, current_punctuation(included_original)},
            )
            expected_omitted = (
                current_punctuation(omitted_original)
                if punctuation_cleaned
                else omitted_original
            )
            expected_alternate = (
                current_punctuation(row["alternate_standard_form"])
                if punctuation_cleaned
                else row["alternate_standard_form"]
            )
            self.assertEqual(direct(omitted, "FORM", "original"), expected_omitted)
            self.assertEqual(direct(omitted, "FORM", "standard"), expected_alternate)
            primary_translation = primary.find("TRANSL")
            omitted_translation = omitted.find("TRANSL")
            self.assertIsNotNone(primary_translation)
            self.assertIsNotNone(omitted_translation)
            self.assertEqual(
                (primary_translation.text, primary_translation.attrib),
                (omitted_translation.text, omitted_translation.attrib),
            )
            for element in omitted.iter():
                if element.tag in {"S", "W", "M"}:
                    self.assertTrue(element.get("id", "").startswith(omitted_id))

    def test_direct_text_and_analysis_tiers_remain_distinct(self) -> None:
        sentence = self.sentences[("PaiwanCh2_001.xml", "001S9")]
        word = sentence.findall("W")[1]
        self.assertEqual(direct(sentence, "FORM", "original").split()[1], "pakazua-u")
        self.assertEqual(direct(word, "FORM", "original"), "pa-maka-zua-u")
        self.assertEqual(
            [direct(morpheme, "FORM", "standard") for morpheme in word.findall("M")],
            ["pa", "maka", "zua", "u"],
        )

    def test_uppercase_ferrell_retroflex_preserves_case(self) -> None:
        sentence = self.sentences[("PaiwanCh2_033.xml", "033S11")]
        self.assertIn("Draqadraqa", direct(sentence, "FORM", "standard"))
        word = sentence.findall("W")[-1]
        self.assertEqual(direct(word, "FORM", "standard"), "Draqadraqa")
        self.assertEqual(
            direct(word.findall("M")[0], "FORM", "standard"), "Draqadraqa"
        )

    def test_added_and_recovered_source_material(self) -> None:
        self.assertIn(("PaiwanCh2_091.xml", "091S0"), self.sentences)
        for row in read_tsv(ROOT / "data" / "recovered_final_words.tsv"):
            filename = f"PaiwanCh2_{row['sentence_id'][:3]}.xml"
            sentence = self.sentences[(filename, row["sentence_id"])]
            word = sentence.findall("W")[-1]
            self.assertEqual(word.get("id"), row["word_id"])
            self.assertTrue(direct(word, "FORM", "original"))
            self.assertEqual(
                normalized_letters(direct(sentence, "FORM", "original").split()[-1]),
                normalized_letters(row["word"]),
            )

    def test_reviewed_translation_repairs(self) -> None:
        for row in read_tsv(ROOT / "data" / "translation_note_extractions.tsv"):
            sentence = next(
                value
                for (filename, sentence_id), value in self.sentences.items()
                if sentence_id == row["sentence_id"]
            )
            translation = sentence.find("TRANSL")
            self.assertIsNotNone(translation)
            self.assertFalse(
                (translation.text or "").endswith(row["source_translation_suffix"])
            )
            self.assertIn(row["note_attribute"], translation.get("notes", ""))

        correction = read_tsv(
            ROOT / "data" / "translation_punctuation_corrections.tsv"
        )[0]
        sentence = self.sentences[("PaiwanCh2_057.xml", correction["sentence_id"])]
        self.assertEqual(
            sentence.findtext("TRANSL"), correction["corrected_translation"]
        )
        self.assertEqual(
            correction["corrected_translation"].count("("),
            correction["corrected_translation"].count(")"),
        )

    def test_missing_source_gloss_is_explicit_and_not_invented(self) -> None:
        sentence = self.sentences[("PaiwanCh2_078.xml", "078S4")]
        word = next(
            item for item in sentence.findall("W") if item.get("id") == "078S4W19"
        )
        word_translation = word.find("TRANSL")
        final_morpheme = word.findall("M")[-1]
        final_translation = final_morpheme.find("TRANSL")
        self.assertEqual(word_translation.text, "do<qal>-plant-?")
        self.assertEqual(word_translation.get("kindOf"), "standard")
        self.assertEqual(final_translation.text, "?")
        self.assertEqual(final_translation.get("kindOf"), "standard")
        self.assertEqual(
            final_translation.get("notes"),
            "No source gloss was supplied for final -i.",
        )

    def test_source_files_and_parser_inventory_are_pinned(self) -> None:
        expected = {}
        for line in (
            (ROOT / "data" / "source_checksums.sha256")
            .read_text(encoding="utf-8")
            .splitlines()
        ):
            digest, path = line.split(maxsplit=1)
            expected[path] = digest
        for relative, digest in expected.items():
            actual = hashlib.sha256((SOURCE_ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(actual, digest)

        stories = parse_docx(SOURCE_ROOT / "Paiwan Ch2 Preprocessed.docx")
        self.assertEqual(len(stories), 100)
        self.assertEqual(sum(len(story.sentences) for story in stories), 2916)

    def test_rebuild_reports_pin_inventory_and_id_reconciliation(self) -> None:
        summary = json.loads(
            (REPORTS_ROOT / "rebuild" / "rebuild_summary.json").read_text(
                encoding="utf-8"
            )
        )
        expected = {
            "stories": 100,
            "source_sentences": 2916,
            "optional_variant_sentences": 5,
            "sentences": 2921,
            "words": 24556,
            "morphemes": 36938,
            "published_ids_preserved": 64198,
            "rebuilt_ids": 64515,
            "explicit_unknown_morphemes": 1,
            "recovered_final_words": 9,
        }
        for key, value in expected.items():
            self.assertEqual(summary[key], value, key)
        self.assertEqual(
            len(read_tsv(REPORTS_ROOT / "rebuild" / "gap_inference.tsv")), 228
        )
        self.assertEqual(
            len(read_tsv(REPORTS_ROOT / "rebuild" / "id_reconciliation.tsv")),
            109,
        )

    def test_source_drift_is_rejected(self) -> None:
        row = next(row for row in self.decisions if row["sentence_id"] == "001S9")
        sentence = deepcopy(self.sentences[(row["file"], row["sentence_id"])])
        sentence.find("FORM[@kindOf='original']").text = "changed source"
        with self.assertRaisesRegex(ValueError, "original FORM differs"):
            apply_decision(sentence, row)

    def test_normalization_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir) / "XML"
            shutil.copytree(XML_ROOT, temp_root)
            first = normalize(temp_root, DEFAULT_DECISIONS)
            first_hashes = xml_hashes(temp_root)
            second = normalize(temp_root, DEFAULT_DECISIONS)
            self.assertEqual(first, (166, 0, 0, 0))
            self.assertEqual(second, (166, 0, 0, 0))
            self.assertEqual(xml_hashes(temp_root), first_hashes)


if __name__ == "__main__":
    unittest.main()
