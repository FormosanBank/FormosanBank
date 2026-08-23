from __future__ import annotations

import csv
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import build_xml
import source_audit


class LanguageRoutingTests(unittest.TestCase):
    def test_resolves_suffixed_and_unsuffixed_dialects(self) -> None:
        self.assertEqual(build_xml.language_for_dialect("Southern_Amis"), "Amis")
        self.assertEqual(build_xml.language_for_dialect("Truku"), "Truku")


class AudioManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        record = source_audit.SourceRecord(
            slug="topic",
            dialect="Southern_Amis",
            level="S",
            record_id="1",
            form="form",
            translations=(("zho", "translation"),),
            source_file="source.csv",
            source_locator="row 1",
            audio_file="audio.wav",
            audio_url="https://example.test/audio.wav",
        )
        self.inventory = source_audit.Inventory({record.key: record}, Counter(), [])

    def test_loads_complete_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audio.tsv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=build_xml.AUDIO_MANIFEST_FIELDS,
                    dialect="excel-tab",
                    lineterminator="\n",
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "topic": "topic",
                        "dialect": "Southern_Amis",
                        "s_id": "1",
                        "status": "retained",
                        "end": "1.25",
                    }
                )
            self.assertEqual(
                build_xml.load_audio_manifest(path, self.inventory),
                {("topic", "Southern_Amis", "S", "1"): ("retained", "1.25")},
            )

    def test_rejects_incomplete_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "audio.tsv"
            path.write_text("topic\tdialect\ts_id\tstatus\tend\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "coverage mismatch"):
                build_xml.load_audio_manifest(path, self.inventory)


if __name__ == "__main__":
    unittest.main()
