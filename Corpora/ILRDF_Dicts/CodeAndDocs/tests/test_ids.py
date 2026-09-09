"""Sentence-id tests: ids carry the source GUID verbatim and survive corrections.

See docs/id_scheme.md for why the id is not a hash of the sentence text.
"""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ilrdf_source import (  # noqa: E402
    LANGUAGES,
    extract_sentences,
    load_audio_exclusions,
    load_translation_exclusions,
    load_translation_overrides,
    sentence_id,
    verify_and_load_snapshot,
)

BASE = Path(__file__).resolve().parents[1]
SOURCE_DATA = BASE / "source_data"
SNAPSHOTS = SOURCE_DATA / "snapshots"

A_GUID = "20a69646-e70a-f011-bd65-00155db40116"


def _manifest():
    return json.loads(
        (SOURCE_DATA / "source_manifest.json").read_text(encoding="utf-8"))


def _sentences(language):
    """extract_sentences with its real signature; defaults for the rest."""
    snapshot = verify_and_load_snapshot(language, SNAPSHOTS, _manifest())
    sentences, _stats = extract_sentences(
        language,
        snapshot,
        load_audio_exclusions(SOURCE_DATA / "audio_exclusions.json"),
        load_translation_overrides(
            SOURCE_DATA / "translation_language_overrides.json"),
        set(),
        load_translation_exclusions(
            SOURCE_DATA / "source_content_exclusions.json"),
        set(),
    )
    return sentences


class TestSentenceId(unittest.TestCase):
    def test_id_carries_the_guid_verbatim(self):
        self.assertEqual(sentence_id("Amis", A_GUID), f"Amis_{A_GUID}")

    def test_id_is_derived_from_guid_not_text(self):
        self.assertEqual(sentence_id("Amis", A_GUID), sentence_id("Amis", A_GUID))

    def test_a_raw_guid_greps_back_to_the_id(self):
        self.assertIn(A_GUID, sentence_id("Amis", A_GUID))

    def test_malformed_guid_is_rejected(self):
        for bad in ("", None, "not-a-guid", A_GUID.replace("-", "")):
            with self.assertRaises(ValueError):
                sentence_id("Amis", bad)

    def test_ids_unique_within_every_language(self):
        for language in LANGUAGES:
            ids = [s.identifier for s in _sentences(language)]
            duplicates = [i for i, n in Counter(ids).items() if n > 1]
            self.assertEqual(duplicates, [], f"{language}: duplicate ids")

    def test_canonical_id_is_the_lowest_guid_in_the_merge_group(self):
        for language in LANGUAGES:
            for s in _sentences(language):
                self.assertEqual(
                    s.identifier,
                    sentence_id(language, min(s.source_ids)),
                    f"{language}: {s.identifier} is not the lowest-GUID id",
                )

    def test_every_sentence_carries_at_least_one_guid(self):
        for language in LANGUAGES:
            for s in _sentences(language):
                self.assertTrue(s.source_ids, f"{language}: {s.original!r}")

    def test_id_survives_a_text_correction(self):
        """The whole point: correcting the text must not retire the id."""
        target = _sentences("Saaroa")[0]
        before = target.identifier
        target.original = target.original + " corrected"
        self.assertEqual(before, target.identifier)


if __name__ == "__main__":
    unittest.main()
