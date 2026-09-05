from collections import Counter
import unittest

from ilrdf_source import (
    extract_sentences,
    is_published,
    normalize_source_text,
    normalize_source_form,
    repair_question_token,
    sentence_id,
)


class SourceExtractionTests(unittest.TestCase):
    def test_source_normalization_is_nfc_and_layout_whitespace_only(self):
        self.assertEqual(
            normalize_source_text("  e\u0301\u00a0x  \nnext\t \n  "),
            "é\u00a0x\nnext",
        )

    def test_form_normalization_applies_current_spacing_and_quote_rules(self):
        self.assertEqual(
            normalize_source_form("  “a\u00a0  b”  "),
            '"a b"',
        )

    def test_publication_filter_matches_live_dictionary_flag(self):
        self.assertTrue(is_published({"frequency": 1, "sources": []}))
        self.assertTrue(is_published({"frequency": 0, "sources": ["線上辭典"]}))
        self.assertFalse(is_published({"frequency": 0, "sources": []}))

    def test_question_repair_requires_an_attested_clean_word(self):
        vocabulary = Counter({"cʉnʉ": 3})
        self.assertEqual(repair_question_token("c?nʉ.", vocabulary), ("cʉnʉ.", True))
        self.assertEqual(repair_question_token("x?y.", vocabulary), ("x?y.", False))
        self.assertEqual(repair_question_token("what?", vocabulary), ("what?", False))

    def test_duplicates_merge_translations_and_audio(self):
        audio_a = "https://example.test/Data/api/Storage/aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa/download"
        audio_b = "https://example.test/Data/api/Storage/bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb/download"
        sentence_a = {
            "id": "source-a",
            "originalSentence": "Form.",
            "chineseSentence": "翻譯一。",
            "audioItems": [{"audioUrl": audio_a}],
        }
        sentence_b = {
            "id": "source-b",
            "originalSentence": "Form.",
            "chineseSentence": "翻譯二。",
            "audioItems": [{"audioUrl": audio_b}],
        }
        snapshot = {
            "responses": [
                {
                    "query": "a",
                    "words": [
                        {
                            "frequency": 1,
                            "sources": [],
                            "explanationItems": [{"sentenceItems": [sentence_a, sentence_b]}],
                        }
                    ],
                },
                {
                    "query": "b",
                    "words": [
                        {
                            "frequency": 0,
                            "sources": ["線上辭典"],
                            "explanationItems": [{"sentenceItems": [sentence_a]}],
                        }
                    ],
                },
            ]
        }
        sentences, stats = extract_sentences(
            "Amis",
            snapshot,
            {"bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"},
            {},
            set(),
        )
        self.assertEqual(len(sentences), 1)
        self.assertEqual(
            sentences[0].translations,
            [("zho", "翻譯一。"), ("zho", "翻譯二。")],
        )
        self.assertEqual(sentences[0].audio_urls, [audio_a])
        self.assertEqual(sentences[0].source_ids, {"source-a", "source-b"})
        self.assertEqual(stats.excluded_audio, 1)

    def test_documented_bad_translation_is_excluded_without_losing_source(self):
        snapshot = {
            "responses": [
                {
                    "query": "x",
                    "words": [
                        {
                            "frequency": 1,
                            "explanationItems": [
                                {
                                    "sentenceItems": [
                                        {
                                            "originalSentence": "Source.",
                                            "chineseSentence": "10",
                                            "audioItems": [
                                                {"audioUrl": "https://example.test/a.mp3"}
                                            ],
                                        }
                                    ]
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        exclusion = {("Amis", "Source.", "10")}
        used: set[tuple[str, str, str]] = set()
        sentences, stats = extract_sentences(
            "Amis", snapshot, set(), {}, set(), exclusion, used
        )
        self.assertEqual(sentences[0].translations, [])
        self.assertEqual(sentences[0].audio_urls, ["https://example.test/a.mp3"])
        self.assertEqual(used, exclusion)
        self.assertEqual(stats.excluded_translation, 1)

    def test_punctuation_only_source_is_not_a_sentence(self):
        snapshot = {
            "responses": [
                {
                    "query": "x",
                    "words": [
                        {
                            "frequency": 1,
                            "explanationItems": [
                                {
                                    "sentenceItems": [
                                        {
                                            "originalSentence": ".",
                                            "chineseSentence": "句號",
                                        }
                                    ]
                                }
                            ],
                        }
                    ],
                }
            ]
        }
        sentences, stats = extract_sentences("Amis", snapshot, set(), {}, set())
        self.assertEqual(sentences, [])
        self.assertEqual(stats.skipped_source, 1)

    def test_sentence_id_is_stable_and_content_derived(self):
        self.assertEqual(sentence_id("Amis", "A."), sentence_id("Amis", "A."))
        self.assertNotEqual(sentence_id("Amis", "A."), sentence_id("Amis", "B."))


if __name__ == "__main__":
    unittest.main()
