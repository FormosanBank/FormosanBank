"""The frozen main-id ledger (POL-037; maintainer ruling 2026-10-15).

"Keep main's ids for the 96,988 (frozen in the ledger); GUID ids only for new
records." These are static checks on source_data/main_id_ledger.csv and the
rulings table; they do not rebuild anything.
"""
import csv
import json
import re
import unittest
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
LEDGER = BASE / "source_data" / "main_id_ledger.csv"
RULINGS = BASE / "source_data" / "alternative_rulings.json"
MAIN_MANIFEST = BASE / "source_data" / "main_2024" / "manifest.json"


def _rows():
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _number(main_id):
    return int(main_id.rsplit("_", 1)[1])


class TestMainIdLedger(unittest.TestCase):
    def test_every_main_id_appears_exactly_once(self):
        ids = [r["main_id"] for r in _rows()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 98837)

    def test_statuses_are_the_ruled_ones(self):
        self.assertLessEqual(
            {r["status"] for r in _rows()},
            {"kept", "merged-kept", "merged-retired", "withdrawn"})

    def test_kept_ids_publish_under_themselves(self):
        for row in _rows():
            if row["status"] in ("kept", "merged-kept", "withdrawn"):
                self.assertEqual(row["published_id"], row["main_id"])

    def test_a_merged_group_keeps_its_lowest_id(self):
        groups = defaultdict(list)
        for row in _rows():
            if row["status"].startswith("merged"):
                groups[row["record_id"]].append(row)
        self.assertTrue(groups)
        for rows in groups.values():
            lowest = min(rows, key=lambda r: _number(r["main_id"]))
            self.assertEqual(lowest["status"], "merged-kept")
            self.assertTrue(all(r["published_id"] == lowest["main_id"] for r in rows))
            self.assertEqual(sum(r["status"] == "merged-kept" for r in rows), 1)

    def test_no_2026_record_is_claimed_twice(self):
        claims = Counter(r["record_id"] for r in _rows()
                         if r["status"] in ("kept", "merged-kept"))
        self.assertEqual([k for k, v in claims.items() if v > 1], [])

    def test_saisiyat_5666_and_5667_merge_into_5666(self):
        rows = {r["main_id"]: r for r in _rows()}
        self.assertEqual(rows["Saisiyat_5666"]["status"], "merged-kept")
        self.assertEqual(rows["Saisiyat_5667"]["status"], "merged-retired")
        self.assertEqual(rows["Saisiyat_5667"]["published_id"], "Saisiyat_5666")


class TestAlternativeRulings(unittest.TestCase):
    def test_counts_match_the_rulings(self):
        records = json.loads(RULINGS.read_text(encoding="utf-8"))["records"]
        self.assertEqual(Counter(r["ruling"] for r in records), Counter({
            "remove": 35, "retain": 9, "b": 7, "thao-one-form": 7,
            "thao-alt-variant": 5, "delete": 4, "c": 3, "notransl": 2, "a": 1}))

    def test_every_ruling_targets_a_kept_main_id(self):
        rows = {r["main_id"]: r for r in _rows()}
        for record in json.loads(RULINGS.read_text(encoding="utf-8"))["records"]:
            self.assertEqual(rows[record["main_id"]]["status"], "kept", record["main_id"])

    def test_split_ids_follow_pol_028(self):
        for record in json.loads(RULINGS.read_text(encoding="utf-8"))["records"]:
            ids = [p["id"] for p in record["publish"]]
            expected = [record["main_id"], f"{record['main_id']}-opt"][: len(ids)]
            self.assertEqual(ids, expected)
            for item in record["publish"]:
                for form in item["forms"]:
                    if record["ruling"] != "retain":
                        self.assertIsNone(re.search(r"[()（）/]", form), form)

    def test_only_the_untranslated_rulings_keep_audio_on_the_sentence(self):
        for record in json.loads(RULINGS.read_text(encoding="utf-8"))["records"]:
            expected = "on_S" if record["ruling"] == "notransl" else "untranscribed"
            self.assertEqual(record["audio"], expected, record["main_id"])


class TestMainSnapshot(unittest.TestCase):
    def test_snapshot_covers_sixteen_languages(self):
        manifest = json.loads(MAIN_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["files"]), 16)
        self.assertRegex(manifest["formosanbank_commit"], r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
