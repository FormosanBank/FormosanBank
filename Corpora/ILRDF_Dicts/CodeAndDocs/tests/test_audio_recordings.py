"""Recording choice and file names (audio_recordings.py), and the built XML.

Rulings (2026-10-17): one S per distinct recording, identical copies kept
once; ids -opt, -opt3; Yami village in the file name, 朗島 first; files named
by their real type; broken/unreachable recordings dropped, main's recording
used when no working 2026 copy exists.
"""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from audio_recordings import (AudioTable, Fingerprint, audio_elements, choose,
                              split_id, EXTENSIONS, BROKEN_TYPES, UNREACHABLE)

XML_DIR = Path(__file__).resolve().parents[2] / "XML"


class FakeTable(AudioTable):
    def __init__(self, recordings, mains):
        self.by_url = {url: Fingerprint("2026", "L", url, f"{url}.mp3", "1", sha, kind, "")
                       for url, sha, kind in recordings}
        self.main = {("Bunun", name): Fingerprint("main", "Bunun", f"Bunun/Bunun/{name}",
                                                  name, "1", sha, "", "")
                     for name, sha in mains}


def run(language, identifier, recordings, mains=(), main_audio=(), village=None,
        second_s=()):
    table = FakeTable(recordings, mains)
    log = []
    chosen = choose(language, identifier, [u for u, _, _ in recordings], village or {},
                    [dict(a) for a in main_audio], table, set(second_s), log)
    return audio_elements(language, identifier, chosen, table), log


class TestChoice(unittest.TestCase):
    def test_identical_copies_kept_once(self):
        out, log = run("Bunun", "Bunun_1", [("u1", "A", "mp3"), ("u2", "A", "mp3")])
        self.assertEqual(out, [{"url": "u1", "file": "Bunun_1.mp3"}])
        self.assertEqual([r["outcome"] for r in log], ["identical copy: kept once"])

    def test_distinct_recordings_named_opt_opt3_by_real_type(self):
        out, _ = run("Bunun", "Bunun_1", [("u1", "A", "mp3"), ("u2", "B", "webm"),
                                          ("u3", "C", "wav")])
        self.assertEqual([a["file"] for a in out],
                         ["Bunun_1.mp3", "Bunun_1-opt.webm", "Bunun_1-opt3.wav"])

    def test_identical_to_main_keeps_mains_file(self):
        main = {"url": "old", "file": "Bunun_1.mp3", "start": "0", "end": "3"}
        out, _ = run("Bunun", "Bunun_1", [("u1", "M", "same-as-main"), ("u2", "B", "mp3")],
                     mains=[("Bunun_1.mp3", "M")], main_audio=[main])
        self.assertEqual(out, [main, {"url": "u2", "file": "Bunun_1-opt.mp3"}])

    def test_different_2026_recording_replaces_mains(self):
        main = {"url": "old", "file": "Bunun_1.mp3"}
        out, log = run("Bunun", "Bunun_1", [("u1", "B", "mp3")],
                       mains=[("Bunun_1.mp3", "M")], main_audio=[main])
        self.assertEqual(out, [{"url": "u1", "file": "Bunun_1.mp3"}])
        self.assertIn("main's recording not used", log[0]["outcome"])

    def test_second_s_ruling_keeps_main_first(self):
        main = {"url": "old", "file": "Bunun_1.mp3"}
        out, _ = run("Bunun", "Bunun_1", [("u1", "B", "mp3")], mains=[("Bunun_1.mp3", "M")],
                     main_audio=[main], second_s=["Bunun_1"])
        self.assertEqual(out, [main, {"url": "u1", "file": "Bunun_1-opt.mp3"}])

    def test_broken_dropped_and_main_used_instead(self):
        main = {"url": "old", "file": "Bunun_1.mp3"}
        out, log = run("Bunun", "Bunun_1", [("u1", "", "all-zero"), ("u2", "", "unreachable")],
                       mains=[("Bunun_1.mp3", "M")], main_audio=[main])
        self.assertEqual(out, [main])
        outcomes = [r["outcome"] for r in log]
        self.assertIn("dropped: broken", outcomes)
        self.assertIn("dropped: unreachable", outcomes)

    def test_broken_with_no_main_leaves_no_audio(self):
        out, _ = run("Bunun", "Bunun_9", [("u1", "", "unknown:0000000000000000")])
        self.assertEqual(out, [])

    def test_yami_village_order_and_names(self):
        recs = [("u1", "A", "mp3"), ("u2", "B", "mp3"), ("u3", "C", "webm"), ("u4", "A", "mp3")]
        village = {"u1": "漁人", "u2": "朗島", "u3": "野銀", "u4": "漁人"}
        out, _ = run("Yami", "Yami_4596", recs, village=village)
        self.assertEqual([a["file"] for a in out],
                         ["Yami_4596_朗島.mp3", "Yami_4596_野銀.webm", "Yami_4596_漁人.mp3"])

    def test_yami_two_different_recordings_of_one_village(self):
        # Not ruled: the second distinct recording of a village takes _2.
        recs = [("u1", "A", "mp3"), ("u2", "B", "mp3")]
        out, _ = run("Yami", "Yami_1", recs, village={"u1": "野銀", "u2": "野銀"})
        self.assertEqual([a["file"] for a in out], ["Yami_1_野銀.mp3", "Yami_1_野銀_2.mp3"])

    def test_split_id(self):
        self.assertEqual([split_id("X", k) for k in range(4)],
                         ["X", "X-opt", "X-opt3", "X-opt4"])


@unittest.skipUnless((XML_DIR / "Bunun" / "Bunun.xml").exists(), "built XML not present")
class TestBuiltXml(unittest.TestCase):
    """Every S carries at most one AUDIO, and every 2026 file is named by type."""

    @classmethod
    def setUpClass(cls):
        cls.table = AudioTable()

    def test_published_audio(self):
        problems = []
        for path in sorted(XML_DIR.glob("*/*.xml")):
            if path.name.endswith("_dictionary.xml"):
                continue
            root = ET.parse(path).getroot()
            for s in root.findall("S"):
                if len(s.findall("AUDIO")) > 1:
                    problems.append(f"{s.get('id')}: more than one AUDIO")
            for audio in root.iter("AUDIO"):
                fp = self.table.by_url.get(audio.get("url", ""))
                if fp is None:
                    continue
                if fp.type in BROKEN_TYPES or fp.type == UNREACHABLE:
                    problems.append(f"{audio.get('file')}: broken/unreachable published")
                elif fp.type in EXTENSIONS and not audio.get("file").endswith(
                        "." + EXTENSIONS[fp.type]):
                    problems.append(f"{audio.get('file')}: real type {fp.type}")
        self.assertEqual(problems[:20], [])


if __name__ == "__main__":
    unittest.main()
