"""Recording choice and file names (audio_recordings.py), and the built XML.

Rulings (2026-10-17): one S per distinct recording, identical copies kept
once; ids -opt, -opt3; Yami village in the file name, 朗島 first; files named
by their real type; broken/unreachable recordings dropped, main's recording
used when no working 2026 copy exists.
"""
import csv
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from audio_recordings import (AudioTable, Fingerprint, audio_elements, choose,
                              load_no_audio, split_id, EXTENSIONS, BROKEN_TYPES,
                              UNREACHABLE)

XML_DIR = Path(__file__).resolve().parents[2] / "XML"
AUDIO_LOG = Path(__file__).resolve().parents[1] / "docs" / "audio_not_published.csv"


class FakeTable(AudioTable):
    def __init__(self, recordings, mains):
        self.by_url = {url: Fingerprint("2026", "L", url, f"{url}.mp3", "1", sha, kind, "")
                       for url, sha, kind in recordings}
        self.main = {("Bunun", name): Fingerprint("main", "Bunun", f"Bunun/Bunun/{name}",
                                                  name, "1", sha, "", "")
                     for name, sha in mains}


def run(language, identifier, recordings, mains=(), main_audio=(), village=None,
        second_s=(), no_audio=()):
    table = FakeTable(recordings, mains)
    log = []
    chosen, replaced = choose(language, identifier, [u for u, _, _ in recordings],
                              village or {}, [dict(a) for a in main_audio], table,
                              set(second_s), log, set(no_audio))
    run.replaced = replaced
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
        # Ruling 2026-10-18 "Use the 2026 URL": main's file, the 2026 URL.
        self.assertEqual(out, [{**main, "url": "u1"}, {"url": "u2", "file": "Bunun_1-opt.mp3"}])

    def test_different_2026_recording_replaces_mains(self):
        # Ruling 2026-10-18 "Give replacements new names" + "add the recordings
        # as untranscribed audio".
        main = {"url": "old", "file": "Bunun_1.mp3", "start": "0", "end": "3"}
        out, log = run("Bunun", "Bunun_1", [("u1", "B", "mp3")],
                       mains=[("Bunun_1.mp3", "M")], main_audio=[main])
        self.assertEqual(out, [{"url": "u1", "file": "Bunun_1_2.mp3"}])
        self.assertEqual(run.replaced, [main])
        self.assertIn("published as untranscribed audio", log[0]["outcome"])

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

    def test_no_audio_ruling_drops_every_recording(self):
        main = {"url": "old", "file": "Bunun_1.mp3"}
        out, log = run("Bunun", "Bunun_1", [("u1", "M", "same-as-main"), ("u2", "B", "mp3")],
                       mains=[("Bunun_1.mp3", "M")], main_audio=[main], no_audio=["Bunun_1"])
        self.assertEqual(out, [])
        self.assertEqual(len(log), 3)
        self.assertTrue(all("Drop the audio" in r["outcome"] for r in log))

    def test_split_id(self):
        self.assertEqual([split_id("X", k) for k in range(4)],
                         ["X", "X-opt", "X-opt3", "X-opt4"])


@unittest.skipUnless((XML_DIR / "Bunun" / "Bunun.xml").exists(), "built XML not present")
class TestBuiltXml(unittest.TestCase):
    """Every S carries at most one AUDIO, and every 2026 file is named by type."""

    @classmethod
    def setUpClass(cls):
        cls.table = AudioTable()

    def test_no_audio_rulings_hold(self):
        # Maintainer, round 3 (2026-10-16): "Use only 2026 version. Drop the audio."
        found = {}
        for identifier in sorted(load_no_audio()):
            language = identifier.rsplit("_", 1)[0]
            root = ET.parse(XML_DIR / language / f"{language}.xml").getroot()
            family = [s for s in root.findall("S")
                      if s.get("id") == identifier or s.get("id", "").startswith(identifier + "-opt")]
            found[identifier] = (len(family), sum(len(s.findall("AUDIO")) for s in family))
        self.assertEqual(found, {i: (1, 0) for i in found})
        self.assertEqual(len(found), 5)

    def test_no_published_name_reuses_a_main_file_with_other_bytes(self):
        # Ruling 2026-10-18: "Give replacements new names".
        problems = []
        for path in sorted(XML_DIR.glob("*/*.xml")):
            if path.name.endswith("_dictionary.xml"):
                continue
            language = path.parent.name
            for audio in ET.parse(path).getroot().iter("AUDIO"):
                fp = self.table.by_url.get(audio.get("url", ""))
                main = self.table.main_file(language, audio.get("file"))
                if fp is not None and main is not None and fp.sha256 != main.sha256:
                    problems.append(audio.get("file"))
        self.assertEqual(problems[:20], [])

    def test_identical_main_recordings_carry_the_2026_url(self):
        # Ruling 2026-10-18: "Use the 2026 URL". Where a sentence's own 2026
        # recording was kept once because main's file is byte-identical
        # (audio_not_published.csv, same_as = main's file), main's AUDIO
        # carries a 2026 source URL.
        wanted = {}
        for r in csv.DictReader(open(AUDIO_LOG, encoding="utf-8")):
            if (r["origin"] == "2026" and r["outcome"] == "identical copy: kept once"
                    and self.table.main_file(r["language"], r["same_as"]) is not None):
                wanted.setdefault(r["language"], set()).add(r["same_as"])
        self.assertGreater(sum(map(len, wanted.values())), 0)
        stale = []
        for language, files in sorted(wanted.items()):
            root = ET.parse(XML_DIR / language / f"{language}.xml").getroot()
            for audio in root.iter("AUDIO"):
                if audio.get("file") in files and audio.get("url", "") not in self.table.by_url:
                    stale.append(audio.get("file"))
        self.assertEqual(stale[:20], [])

    def test_replaced_main_recordings_are_untranscribed(self):
        # Ruling 2026-10-18: "add the recordings as untranscribed audio".
        rows = [r for r in csv.DictReader(open(AUDIO_LOG, encoding="utf-8"))
                if r["outcome"].startswith("main's recording replaced")]
        self.assertGreater(len(rows), 0)
        missing = []
        for r in rows:
            root = ET.parse(XML_DIR / r["language"] / f"{r['language']}.xml").getroot()
            if r["file"] not in {a.get("file") for a in root.findall("AUDIO")}:
                missing.append(r["file"])
        self.assertEqual(missing[:20], [])

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
