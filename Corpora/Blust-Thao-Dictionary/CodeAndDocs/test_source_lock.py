from __future__ import annotations

import json
import unittest
from datetime import date
from pathlib import Path

from CodeAndDocs.download_source import sha256


ROOT = Path(__file__).resolve().parents[1]


class SourceLockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = json.loads(
            (ROOT / "CodeAndDocs" / "source-lock.json").read_text()
        )
        cls.rights = json.loads(
            (ROOT / "CodeAndDocs" / "rights-evidence.json").read_text()
        )

    def test_source_identity(self) -> None:
        self.assertEqual(self.lock["isbn"], "9789570147858")
        self.assertEqual(self.lock["printed_pages"], 1106)
        self.assertEqual(self.lock["pdf_pages"], 1117)
        self.assertEqual(self.lock["pdf_bytes"], 6_046_093)

    def test_local_source_when_present(self) -> None:
        source = ROOT / "Private" / self.lock["pdf_filename"]
        if not source.exists():
            self.skipTest("source not downloaded")
        self.assertEqual(source.stat().st_size, self.lock["pdf_bytes"])
        self.assertEqual(sha256(source), self.lock["pdf_sha256"])

    def test_authorized_scope_and_term(self) -> None:
        # Widened on the maintainer's ruling of 2026-09-11: the grant covers
        # the book's linguistic material, not a named list of sections, so the
        # dictionary's headwords and definitions are in scope too.
        self.assertEqual(
            self.rights["authorized_material"], "the linguistic material in the book"
        )
        # POL-042: the recorded licence is the exact rights_vocabulary.csv value
        # that ships in @copyright, and the grant carries no expiry.
        self.assertEqual(self.rights["license"], "CC BY-NC 4.0")
        self.assertEqual(
            date.fromisoformat(self.rights["granted"]), date(2024, 1, 30)
        )
        self.assertNotIn("valid_through", self.rights)


if __name__ == "__main__":
    unittest.main()
