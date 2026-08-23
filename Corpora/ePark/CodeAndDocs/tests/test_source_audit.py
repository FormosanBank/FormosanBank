from __future__ import annotations

import unittest

import source_audit


class CanonicalFormTextTests(unittest.TestCase):
    def test_normalizes_current_policy_quotes_and_annotations(self) -> None:
        self.assertEqual(
            source_audit.canonical_form_text("  *‘族語’「例句」  "),
            "'族語'\"例句\"",
        )

    def test_preserves_lexical_apostrophes(self) -> None:
        self.assertEqual(source_audit.canonical_form_text("nga'ay"), "nga'ay")


class MalformedCsvTests(unittest.TestCase):
    def test_recovers_source_commas_from_three_column_export(self) -> None:
        self.assertEqual(
            source_audit.parse_malformed_three_column_row(
                ["source", "with", "commas", "中文", "https://example.test/audio.mp3"]
            ),
            ("source,with,commas", "中文", "https://example.test/audio.mp3"),
        )

    def test_recovers_two_column_export(self) -> None:
        self.assertEqual(
            source_audit.parse_malformed_three_column_row(
                ["source,中文", "https://example.test/audio.mp3"]
            ),
            ("source", "中文", "https://example.test/audio.mp3"),
        )


if __name__ == "__main__":
    unittest.main()
