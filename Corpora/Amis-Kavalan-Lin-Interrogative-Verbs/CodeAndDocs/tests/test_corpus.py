from __future__ import annotations

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_build_module():
    spec = importlib.util.spec_from_file_location("build_xml", ROOT / "CodeAndDocs" / "build_xml.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load CodeAndDocs/build_xml.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_tsv(name: str) -> list[dict[str, str]]:
    with (ROOT / "CodeAndDocs" / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class CorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.build = load_build_module()
        cls.examples = read_tsv("extracted_examples.tsv")
        cls.excluded = read_tsv("excluded_source_units.tsv")
        cls.review = read_tsv("manual_source_review.tsv")
        cls.direct_checks = read_tsv("direct_source_checks.tsv")
        cls.alignment_omissions = read_tsv("alignment_omissions.tsv")

    def test_inventory_counts_and_language_balance(self) -> None:
        self.assertEqual(len(self.build.EXAMPLES), 95)
        self.assertEqual(len(self.build.excluded_units()), 38)
        self.assertEqual(
            Counter(example.language for example in self.build.EXAMPLES),
            Counter({"Amis": 48, "Kavalan": 47}),
        )
        self.assertEqual(
            Counter(item.source_label for item in self.build.excluded_units()),
            Counter({"Theory": 16, "Amis": 10, "Kavalan": 10, "Tzotzil": 1, "English": 1}),
        )

    def test_source_ids_are_unique_and_pages_are_consistent(self) -> None:
        example_keys = {(example.language, example.source_id) for example in self.build.EXAMPLES}
        excluded_keys = {(item.source_label, item.source_id) for item in self.build.EXCLUDED}
        self.assertEqual(len(example_keys), 95)
        self.assertEqual(len(excluded_keys), 18)
        self.assertTrue(example_keys.isdisjoint(excluded_keys))
        for item in [*self.build.EXAMPLES, *self.build.EXCLUDED]:
            self.assertEqual(item.pdf_page, item.printed_page - 252)
            self.assertIn(item.pdf_page, range(1, 39))

    def test_checked_in_ledgers_match_builder(self) -> None:
        expected_examples = [
            (
                example.language,
                example.source_id,
                str(example.printed_page),
                str(example.pdf_page),
                "excluded" if self.build.exclusion_reason(example) else "admitted",
                self.build.exclusion_reason(example),
                example.printed,
                self.build.xml_form(example),
                (
                    ""
                    if self.build.exclusion_reason(example)
                    else self.build.REPEAT_TARGETS.get(
                        (example.language, example.source_id), example.source_id
                    )
                ),
                example.gloss,
                self.build.source_note(example),
                example.published_translation,
                (
                    self.build.translation_readings(example)[1]
                    if len(self.build.translation_readings(example)) > 1
                    else ""
                ),
                self.build.translation_readings(example),
                self.build.form_variants(example),
            )
            for example in sorted(self.build.EXAMPLES, key=self.build.source_order)
        ]
        actual_examples = [
            (
                row["language"],
                row["source_id"],
                row["printed_page"],
                row["pdf_page"],
                row["admission_status"],
                row["exclusion_reason"],
                row["source_form"],
                row["xml_form"],
                row["xml_record_source_id"],
                row["gloss"],
                row["source_note"],
                row["source_translation_eng"],
                row["alternate_translation_eng"],
                tuple(json.loads(row["translation_readings_eng_json"])),
                tuple(
                    self.build.FormVariant(
                        item["id_suffix"],
                        item["label"],
                        item["form"],
                        item["aligned_form"],
                        item["gloss"],
                    )
                    for item in json.loads(row["xml_variants_json"])
                ),
            )
            for row in self.examples
        ]
        self.assertEqual(actual_examples, expected_examples)
        expected_excluded = [
            (item.source_label, item.source_id, str(item.printed_page), item.raw_form, item.reason)
            for item in sorted(self.build.excluded_units(), key=self.build.source_order)
        ]
        actual_excluded = [
            (row["source_label"], row["source_id"], row["printed_page"], row["raw_form"], row["reason"])
            for row in self.excluded
        ]
        self.assertEqual(actual_excluded, expected_excluded)

    def test_visual_review_covers_every_page_and_source_unit(self) -> None:
        self.assertEqual([int(row["pdf_page"]) for row in self.review], list(range(1, 39)))
        self.assertTrue(all(row["visual_status"] == "confirmed" for row in self.review))
        corpus_by_page: dict[int, list[str]] = defaultdict(list)
        excluded_by_page: dict[int, list[str]] = defaultdict(list)
        for row in self.examples:
            corpus_by_page[int(row["pdf_page"])].append(row["source_id"])
        for row in self.excluded:
            if row["source_label"] in {"Amis", "Kavalan"}:
                continue
            excluded_by_page[int(row["pdf_page"])].append(row["source_id"])
        for row in self.review:
            page = int(row["pdf_page"])
            corpus_ids = [item for item in row["corpus_ids"].split(",") if item]
            excluded_ids = [item for item in row["excluded_ids"].split(",") if item]
            self.assertEqual(corpus_ids, corpus_by_page[page])
            self.assertEqual(excluded_ids, excluded_by_page[page])

    def test_difficult_record_sample_has_direct_visual_evidence(self) -> None:
        self.assertEqual(len(self.direct_checks), 30)
        checked_keys = {(row["language"], row["source_id"]) for row in self.direct_checks}
        self.assertEqual(len(checked_keys), 30)
        source_rows = {(row["language"], row["source_id"]): row for row in self.examples}
        for row in self.direct_checks:
            key = (row["language"], row["source_id"])
            self.assertIn(key, source_rows)
            self.assertEqual(row["printed_page"], source_rows[key]["printed_page"])
            self.assertEqual(row["pdf_page"], source_rows[key]["pdf_page"])
            self.assertTrue(row["focus"])
            self.assertTrue(row["visual_result"].startswith("Confirmed"))

    def test_source_status_and_repetition_evidence_is_preserved(self) -> None:
        forms = [row["source_form"] for row in self.examples]
        self.assertEqual(sum(form.startswith("* ") for form in forms), 18)
        self.assertEqual(sum(form.startswith("? ") for form in forms), 2)
        self.assertEqual(
            sum(row["source_note"].startswith("Independently printed repetition") for row in self.examples),
            7,
        )
        self.assertTrue(any("‹m›" in form for form in forms))
        self.assertTrue(any("(na)" in form for form in forms))
        self.assertTrue(any(form.startswith("[") for form in forms))
        self.assertEqual(sum(row["source_form"] != row["xml_form"] for row in self.examples), 51)
        self.assertTrue(all("*" not in row["xml_form"] for row in self.examples))
        self.assertTrue(all(not any(mark in row["xml_form"] for mark in "‘’“”") for row in self.examples))
        self.assertEqual(sum(row["admission_status"] == "admitted" for row in self.examples), 75)
        self.assertEqual(sum(row["admission_status"] == "excluded" for row in self.examples), 20)
        self.assertEqual(
            sum(
                row["admission_status"] == "admitted"
                and row["source_id"] != row["xml_record_source_id"]
                for row in self.examples
            ),
            7,
        )
        self.assertTrue(
            all(
                not row["xml_record_source_id"] and row["exclusion_reason"]
                for row in self.examples
                if row["admission_status"] == "excluded"
            )
        )

    def test_source_corrections_and_anomalies_are_explicit(self) -> None:
        example_14a = next(
            row for row in self.examples if row["language"] == "Amis" and row["source_id"] == "14a"
        )
        self.assertIn("tuniq-en", example_14a["source_form"])
        self.assertEqual(example_14a["source_translation_eng"], "I will tenderise the meat a little.")
        self.assertEqual(example_14a["alternate_translation_eng"], "I will tenderise only the meat.")
        example_41b = next(
            row for row in self.examples if row["language"] == "Kavalan" and row["source_id"] == "41b"
        )
        self.assertIn("<AV>take", example_41b["gloss"])
        optional_glosses = {
            ("Kavalan", "48a"): "here-PV-1SG.ERG put ABS money-1SG.GEN",
            ("Kavalan", "48b"): "there-PV-1SG.ERG put ABS money-1SG.GEN",
            ("Amis", "49a"): "here-PV ERG PN put ABS-CN money",
            ("Amis", "49b"): "there-PV ERG PN put ABS-CN money",
        }
        rows = {(row["language"], row["source_id"]): row for row in self.examples}
        for key, gloss in optional_glosses.items():
            self.assertEqual(rows[key]["gloss"], gloss)
            self.assertIn("Optional secondary verb", rows[key]["source_note"])

    def test_builder_emits_source_preserving_tiers(self) -> None:
        for language, expected_count, expected_words, expected_morphemes in (
            ("Amis", 38, 179, 254),
            ("Kavalan", 38, 168, 252),
        ):
            examples = [
                item
                for item in self.build.admitted_examples()
                if item.language == language
            ]
            root = self.build.make_text(language, examples)
            sentences = root.findall("./S")
            canonical = [
                item
                for item in examples
                if (item.language, item.source_id) not in self.build.REPEAT_TARGETS
            ]
            expected_variants = [
                (item, variant)
                for item in sorted(canonical, key=self.build.source_order)
                for variant in self.build.form_variants(item)
            ]
            self.assertEqual(len(sentences), expected_count)
            self.assertEqual(
                [item.text or "" for item in root.findall("./S/FORM[@kindOf='original']")],
                [variant.form for _, variant in expected_variants],
            )
            self.assertEqual(root.findall(".//FORM[@kindOf='standard']"), [])
            self.assertEqual(len(root.findall(".//PHON")), 0)
            self.assertEqual(len(root.findall(".//W")), expected_words)
            self.assertEqual(len(root.findall(".//M")), expected_morphemes)
            self.assertIn("CC BY 4.0", root.get("copyright", ""))
            for translation in root.findall("./S/TRANSL"):
                self.assertNotIn("kindOf", translation.attrib)
                self.assertEqual(translation.get("{http://www.w3.org/XML/1998/namespace}lang"), "eng")
            for sentence, (item, variant) in zip(sentences, expected_variants, strict=True):
                self.assertIn(
                    f"{item.source_id} (printed p. {item.printed_page};",
                    sentence.get("source", ""),
                )
                expected_pairs, reason = self.build.alignment_words(variant)
                words = sentence.findall("W")
                if reason:
                    self.assertEqual(words, [])
                    continue
                self.assertEqual(len(words), len(expected_pairs))
                for word, (form_word, gloss_word) in zip(words, expected_pairs, strict=True):
                    self.assertEqual(word.findtext("FORM[@kindOf='original']"), form_word)
                    self.assertIsNone(word.find("FORM[@kindOf='standard']"))
                    self.assertEqual(word.findtext("TRANSL[@kindOf='original']"), gloss_word)
                    morph_forms, morph_glosses = self.build.aligned_morphemes(form_word, gloss_word)
                    morphs = word.findall("M")
                    parsed_sentence = any(
                        len(self.build.aligned_morphemes(form, gloss)[0]) >= 2
                        for form, gloss in expected_pairs
                    )
                    expected_morph_count = (
                        len(morph_forms) if len(morph_forms) >= 2 else int(parsed_sentence)
                    )
                    self.assertEqual(len(morphs), expected_morph_count)
                    if expected_morph_count:
                        if len(morph_forms) < 2:
                            morph_forms = [form_word]
                            morph_glosses = [gloss_word]
                        self.assertEqual(
                            [morph.findtext("FORM[@kindOf='original']") for morph in morphs],
                            morph_forms,
                        )
                        self.assertEqual(
                            [morph.findtext("TRANSL[@kindOf='original']") for morph in morphs],
                            morph_glosses,
                        )

    def test_optional_variants_and_translation_readings_follow_policy(self) -> None:
        optional = [
            example
            for example in self.build.admitted_examples()
            if len(self.build.form_variants(example)) == 2
        ]
        self.assertEqual(len(optional), 8)
        for example in optional:
            included, omitted = self.build.form_variants(example)
            self.assertEqual(included.id_suffix, "")
            self.assertEqual(omitted.id_suffix, "_OPT0")
            self.assertNotIn("(", included.form + omitted.form)
            self.assertNotIn(")", included.form + omitted.form)
            self.assertLessEqual(
                len(self.build.lexical_tokens(omitted.gloss)),
                len(self.build.lexical_tokens(included.gloss)),
            )

        example_19b = next(
            item
            for item in self.build.EXAMPLES
            if (item.language, item.source_id) == ("Amis", "19b")
        )
        self.assertEqual(len(self.build.translation_readings(example_19b)), 3)

    def test_infix_analysis_preserves_insertion_point(self) -> None:
        self.assertEqual(
            self.build.aligned_morphemes("q<um>uni", "<AV>do.what"),
            (["q-uni", "-um-"], ["do.what", "AV"]),
        )

    def test_alignment_omissions_are_source_required(self) -> None:
        actual = {
            (row["language"], row["source_id"], row["tier"], row["word_index"])
            for row in self.alignment_omissions
        }
        self.assertEqual(actual, set())
        self.assertEqual(len(self.alignment_omissions), 0)

    def test_base_xml_generation_is_deterministic(self) -> None:
        first = {}
        second = {}
        for language in ("Amis", "Kavalan"):
            examples = [
                item
                for item in self.build.admitted_examples()
                if item.language == language
            ]
            first[language] = self.build.prettify(self.build.make_text(language, examples))
            second[language] = self.build.prettify(self.build.make_text(language, examples))
        self.assertEqual(second, first)

    def test_gloss_audit_reconciliation_resolves_reviewed_finding_types(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "reconcile_gloss_audit", ROOT / "CodeAndDocs" / "reconcile_gloss_audit.py"
        )
        if spec is None or spec.loader is None:
            self.fail("Could not load CodeAndDocs/reconcile_gloss_audit.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = [
            {
                "severity": "HARD",
                "rule_id": "G021",
                "location": "line=1",
                "message": "source example (47) has no matching sentence",
            },
            {
                "severity": "HARD",
                "rule_id": "G021",
                "location": "line=2",
                "message": "source example (30) has no matching sentence",
            },
            {
                "severity": "SOFT",
                "rule_id": "G012",
                "location": "S=S_amis_001",
                "message": "parenthetical translation",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            findings = Path(directory) / "findings.csv"
            with findings.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
            reconciled = module.reconcile(
                findings,
                ROOT / "CodeAndDocs" / "extracted_examples.tsv",
                ROOT / "CodeAndDocs" / "excluded_source_units.tsv",
            )
        self.assertEqual(
            [row["disposition"] for row in reconciled],
            [
                "source-excluded",
                "false-positive-source-reference",
                "retain-source-translation",
            ],
        )


if __name__ == "__main__":
    unittest.main()
