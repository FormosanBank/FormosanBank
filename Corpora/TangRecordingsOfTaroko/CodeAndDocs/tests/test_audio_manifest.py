"""The manifest checks must actually fail when the manifest is wrong.

Every case below corrupts one thing and asserts the specific complaint, so a
check cannot quietly degrade into a no-op.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT))

import make_xml  # noqa: E402
import verify_sources  # noqa: E402


class ManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = verify_sources.load_manifest()
        cls.metadata = make_xml.load_metadata()

    def copy(self) -> dict:
        return json.loads(json.dumps(self.manifest))

    def test_committed_manifest_is_valid(self) -> None:
        verify_sources.validate_manifest(self.manifest, self.metadata)
        verify_sources.validate_pin(self.manifest)
        self.assertEqual(len(self.manifest["files"]), 30)

    def test_it_covers_every_recording_the_metadata_enumerates(self) -> None:
        listed = {entry["file"] for entry in self.manifest["files"]}
        enumerated = {
            name
            for item in self.metadata.values()
            for name in make_xml.item_recordings(item)
        }
        self.assertEqual(listed, enumerated)

    def test_a_dropped_recording_is_rejected(self) -> None:
        manifest = self.copy()
        dropped = manifest["files"].pop()["file"]
        with self.assertRaisesRegex(ValueError, "missing from the manifest"):
            verify_sources.validate_manifest(manifest, self.metadata)
        self.assertNotIn(dropped, {e["file"] for e in manifest["files"]})

    def test_a_duplicate_filename_is_rejected(self) -> None:
        manifest = self.copy()
        manifest["files"][1]["file"] = manifest["files"][0]["file"]
        with self.assertRaisesRegex(ValueError, "unique basenames"):
            verify_sources.validate_manifest(manifest, self.metadata)

    def test_an_unknown_item_is_rejected(self) -> None:
        manifest = self.copy()
        manifest["files"][0]["paradisec_item"] = "AIT1-999"
        with self.assertRaisesRegex(ValueError, "unknown Paradisec item"):
            verify_sources.validate_manifest(manifest, self.metadata)

    def test_source_url_drift_is_rejected(self) -> None:
        manifest = self.copy()
        manifest["files"][0]["source_url"] = "https://example.invalid/AIT1/001"
        with self.assertRaisesRegex(ValueError, "source URL drift"):
            verify_sources.validate_manifest(manifest, self.metadata)

    def test_a_malformed_hash_is_rejected(self) -> None:
        manifest = self.copy()
        manifest["files"][0]["sha256"] = "not-a-hash"
        with self.assertRaisesRegex(ValueError, "malformed SHA-256"):
            verify_sources.validate_manifest(manifest, self.metadata)

    def test_a_truncated_revision_is_rejected(self) -> None:
        manifest = self.copy()
        manifest["source"]["revision"] = manifest["source"]["revision"][:12]
        with self.assertRaisesRegex(ValueError, "not a full commit"):
            verify_sources.validate_manifest(manifest, self.metadata)

    def test_drift_from_the_downloader_pin_is_rejected(self) -> None:
        """The revision users download and the one --live checks must agree."""
        manifest = self.copy()
        manifest["source"]["revision"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "revision"):
            verify_sources.validate_pin(manifest)

    def test_local_audio_is_checked_by_content_not_name(self) -> None:
        genuine = b"the real bytes"
        entry = {
            **self.manifest["files"][0],
            "bytes": len(genuine),
            "sha256": hashlib.sha256(genuine).hexdigest(),
        }
        with tempfile.TemporaryDirectory() as temporary:
            audio_dir = Path(temporary)
            one = {"source": self.manifest["source"], "files": [entry]}

            with self.assertRaisesRegex(SystemExit, "missing="):
                verify_sources.verify_local(one, audio_dir)

            impostor = audio_dir / entry["file"]
            impostor.write_bytes(b"\0" * entry["bytes"])
            with self.assertRaisesRegex(SystemExit, "Move differing local copies aside"):
                verify_sources.verify_local(one, audio_dir)

            impostor.write_bytes(genuine)
            verify_sources.verify_local(one, audio_dir)

    def live_rows(self) -> list[dict]:
        return [
            {"type": "file", "path": e["hf_path"], "size": e["bytes"], "lfs": {"oid": e["sha256"]}}
            for e in self.manifest["files"]
        ]

    def test_matching_live_inventory_passes_without_downloading_audio(self) -> None:
        rows = self.live_rows() + [{"type": "file", "path": "README.md", "size": 20}]
        with patch.object(verify_sources, "live_inventory", return_value=rows):
            verify_sources.verify_live(self.manifest)

    def test_missing_live_recording_is_rejected(self) -> None:
        with patch.object(verify_sources, "live_inventory", return_value=self.live_rows()[1:]):
            with self.assertRaisesRegex(SystemExit, "missing=\\['Truku/AIT1-001-1.wav'"):
                verify_sources.verify_live(self.manifest)

    def test_extra_live_recording_is_rejected(self) -> None:
        rows = self.live_rows() + [{"type": "file", "path": "Truku/extra.wav", "size": 10}]
        with patch.object(verify_sources, "live_inventory", return_value=rows):
            with self.assertRaisesRegex(SystemExit, "extra=\\['Truku/extra.wav'"):
                verify_sources.verify_live(self.manifest)

    def test_wrong_live_size_is_rejected(self) -> None:
        rows = self.live_rows()
        rows[0]["size"] -= 1
        with patch.object(verify_sources, "live_inventory", return_value=rows):
            with self.assertRaisesRegex(SystemExit, "changed=\\['Truku/AIT1-001-1.wav'"):
                verify_sources.verify_live(self.manifest)

    def test_wrong_live_hash_is_rejected(self) -> None:
        rows = self.live_rows()
        rows[0]["lfs"]["oid"] = "0" * 64
        with patch.object(verify_sources, "live_inventory", return_value=rows):
            with self.assertRaisesRegex(SystemExit, "changed=\\['Truku/AIT1-001-1.wav'"):
                verify_sources.verify_live(self.manifest)

    def test_live_file_without_lfs_identity_is_rejected(self) -> None:
        rows = self.live_rows()
        del rows[0]["lfs"]
        with patch.object(verify_sources, "live_inventory", return_value=rows):
            with self.assertRaisesRegex(SystemExit, "changed=\\['Truku/AIT1-001-1.wav'"):
                verify_sources.verify_live(self.manifest)


if __name__ == "__main__":
    unittest.main()
