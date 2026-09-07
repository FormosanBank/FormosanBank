"""Per-language headword dictionaries.

One <S> per headword, one <TRANSL> per sense, no W or M tier. The entries go
through the same cleaning, standardization and phonology pipeline as the
sentences; generate_dictionary.py emits source tiers only.
"""
import gzip
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate_dictionary  # noqa: E402
from ilrdf_source import LANGUAGES, XML_LANG, entry_id, extract_entries  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
SNAPSHOTS = BASE / "source_data" / "snapshots"
G = "20a69646-e70a-f011-bd65-00155db40116"


def _load(language):
    with gzip.open(SNAPSHOTS / f"{language}.json.gz", "rt", encoding="utf-8") as fh:
        return json.load(fh)


class TestEntryId(unittest.TestCase):
    def test_carries_the_guid_with_a_d_prefix(self):
        self.assertEqual(entry_id("Amis", G), f"Amis_d{G}")

    def test_a_raw_guid_still_greps_to_the_entry(self):
        self.assertIn(G, entry_id("Amis", G))

    def test_malformed_guid_is_rejected(self):
        with self.assertRaises(ValueError):
            entry_id("Amis", "not-a-guid")


class TestExtractEntries(unittest.TestCase):
    def test_entry_ids_unique_per_language(self):
        for language in LANGUAGES:
            ids = [e.identifier for e in extract_entries(language, _load(language))]
            self.assertEqual(
                [i for i, n in Counter(ids).items() if n > 1], [], language)

    def test_every_entry_has_a_headword_and_a_sense(self):
        for e in extract_entries("Saaroa", _load("Saaroa")):
            self.assertTrue(e.headword.strip())
            self.assertTrue(e.senses)
            for sense in e.senses:
                self.assertTrue(sense.gloss.strip())

    def test_headwords_are_not_sentences(self):
        """A dictionary entry is a lexical item, not an example."""
        entries = extract_entries("Saaroa", _load("Saaroa"))
        long_ones = [e for e in entries if len(e.headword.split()) > 6]
        self.assertLess(len(long_ones) / len(entries), 0.02)

    def test_part_of_speech_is_carried_per_sense(self):
        entries = extract_entries("Saaroa", _load("Saaroa"))
        self.assertTrue(any(s.part_of_speech for e in entries for s in e.senses))


class TestTree(unittest.TestCase):
    def setUp(self):
        entries = extract_entries("Saaroa", _load("Saaroa"))
        # Take a sample that is guaranteed to include a multi-sense entry,
        # otherwise the ver="alt" test silently skips.
        multi = [e for e in entries if len(e.senses) > 1][:5]
        self.entries = multi + entries[:20]
        self.root = generate_dictionary._build_tree(
            "Saaroa", self.entries, "2026-08-21")

    def test_source_tiers_only(self):
        for s in self.root.findall("S"):
            self.assertEqual(
                [f.get("kindOf") for f in s.findall("FORM")], ["original"])
            self.assertIsNone(s.find("PHON"))
            self.assertIsNone(s.find("W"))

    def test_every_sentence_has_at_least_one_translation(self):
        for s in self.root.findall("S"):
            self.assertTrue(s.findall("TRANSL"))

    def test_second_and_later_senses_are_marked_alt(self):
        for s in self.root.findall("S"):
            translations = s.findall("TRANSL")
            if len(translations) > 1:
                self.assertIsNone(translations[0].get("ver"))
                for extra in translations[1:]:
                    self.assertEqual(extra.get("ver"), "alt")
                break
        else:
            self.skipTest("no multi-sense entry in this sample")

    def test_part_of_speech_rides_on_the_sense(self):
        notes = [t.get("notes") for s in self.root.findall("S")
                 for t in s.findall("TRANSL")]
        self.assertTrue(any(notes))

    def test_root_id_is_distinct_from_the_sentence_file(self):
        self.assertEqual(self.root.get("id"), "ILRDF_Dicts_Saaroa_dictionary")

    def test_root_declares_the_language_and_rights(self):
        self.assertEqual(self.root.get(XML_LANG), "sxr")
        self.assertEqual(self.root.get("copyright"), "CC BY-NC")


if __name__ == "__main__":
    unittest.main()
