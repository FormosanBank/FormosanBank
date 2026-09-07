from __future__ import annotations

import json
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from xml.etree import ElementTree as ET

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT))

import make_xml  # noqa: E402
import prepare_audio  # noqa: E402


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = make_xml.load_manifest()
        cls.metadata = make_xml.load_metadata()

    def test_manifest_covers_every_metadata_wav(self) -> None:
        make_xml.validate_manifest(self.manifest, self.metadata)
        names = {entry["file"] for entry in self.manifest["files"]}
        self.assertEqual(len(names), 30)

    def test_generated_text_preserves_public_identifiers(self) -> None:
        entry = self.manifest["files"][0]
        item = self.metadata[entry["paradisec_item"]]
        root = ET.fromstring(make_xml.serialize_text(make_xml.build_text(entry, item)))
        self.assertEqual(root.attrib["id"], "AIT1-001-1")
        self.assertEqual(
            root.attrib["{http://www.w3.org/XML/1998/namespace}lang"], "trv"
        )
        self.assertEqual(root.attrib["dialect"], "Truku")
        self.assertEqual(root.attrib["copyright"], "CC BY-NC")
        self.assertEqual(root.find("AUDIO").attrib["file"], "AIT1-001-1.wav")

    def test_citation_matches_josh_decision(self) -> None:
        credit = self.metadata["AIT1-001"]["creditText"]
        self.assertEqual(
            make_xml.format_citation(credit),
            "Tang, Apay. (1997). Traditional Truku stories. Paradisec. "
            "https://dx.doi.org/10.4225/72/56EC22110B85A",
        )

    def test_duplicate_manifest_name_is_rejected(self) -> None:
        manifest = json.loads(json.dumps(self.manifest))
        manifest["files"][1]["file"] = manifest["files"][0]["file"]
        with self.assertRaisesRegex(ValueError, "unique basenames"):
            make_xml.validate_manifest(manifest, self.metadata)

    def test_prepared_wave_properties_are_checked(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "sample.wav"
            with wave.open(str(output), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(16_000)
                audio.writeframes(b"\0\0" * 160)
            properties = prepare_audio.assert_format(
                output, self.manifest["prepared"]["format"], 160
            )
            self.assertEqual(properties["duration_seconds"], 0.01)


if __name__ == "__main__":
    unittest.main()
