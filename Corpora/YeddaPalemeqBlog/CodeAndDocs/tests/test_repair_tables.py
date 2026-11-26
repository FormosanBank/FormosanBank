"""The build's repair tables check the text they expect before applying.

Per row: expected text present -> apply; repaired text already present -> skip
and report; neither -> stop the build naming the row. Each case is provoked on
the real frozen snapshot, so a check that never fires would fail here.
"""

from __future__ import annotations

import csv
import importlib.util
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_xml", ROOT / "scripts/build_xml.py")
bx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bx)  # type: ignore[union-attr]


def fresh_root() -> ET.Element:
    root = ET.parse(bx.SOURCE).getroot()
    bx.strip_derived_tiers(root)
    return root


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE))


def write(path: Path, rows: list[dict[str, str]], header: list[str]) -> None:
    lines = ["\t".join(header)] + ["\t".join(row[h] for h in header) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class RepairTableTests(unittest.TestCase):
    def setUp(self) -> None:
        bx.SKIPPED.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = {
            name: getattr(bx, name)
            for name in (
                "ISSUE_REPAIRS_TABLE", "VARIANTS_TABLE", "SOURCE_TRANSLATION_TABLE",
                "SOURCE_WORD_TRANSLATION_TABLE",
            )
        }

    def tearDown(self) -> None:
        for name, value in self.saved.items():
            setattr(bx, name, value)
        bx.SKIPPED.clear()
        self.tmp.cleanup()

    def altered(self, attr: str, header: list[str], column: str) -> str:
        """Point `attr` at a copy whose first row expects text that is not there."""
        rows = read(getattr(bx, attr))
        rows[0][column] = "NOT THE SNAPSHOT TEXT"
        path = Path(self.tmp.name) / getattr(bx, attr).name
        write(path, rows, header)
        setattr(bx, attr, path)
        return rows[0][header[0]]

    def build_to_repairs(self) -> ET.Element:
        root = fresh_root()
        bx.check_variant_sources(root)
        bx.split_alternatives(root)
        bx.annotate_source_segmentation(root)
        return root

    def test_every_row_applies_on_the_snapshot(self) -> None:
        root = self.build_to_repairs()
        self.assertEqual(len(bx.repair_issue_rows(root)), 9)
        self.assertEqual(len(bx.restore_source_translations(root)), 24)
        self.assertEqual(len(bx.restore_source_word_translations(root)), 49)
        self.assertEqual(bx.SKIPPED, [])

    def test_second_pass_skips_every_row(self) -> None:
        root = self.build_to_repairs()
        bx.repair_issue_rows(root)
        bx.restore_source_translations(root)
        bx.restore_source_word_translations(root)
        before = ET.tostring(root)
        bx.repair_issue_rows(root)
        bx.restore_source_translations(root)
        bx.restore_source_word_translations(root)
        self.assertEqual(len(bx.SKIPPED), 9 + 24 + 49)
        self.assertEqual(ET.tostring(root), before)

    def test_issue_repair_stops_on_unexpected_text(self) -> None:
        row_id = self.altered("ISSUE_REPAIRS_TABLE", bx.ISSUE_REPAIRS_HEADER, "expected_translation")
        root = self.build_to_repairs()
        with self.assertRaisesRegex(SystemExit, f"issue_repairs.tsv: row {row_id} "):
            bx.repair_issue_rows(root)

    def test_source_translation_stops_on_unexpected_text(self) -> None:
        row_id = self.altered(
            "SOURCE_TRANSLATION_TABLE", bx.SOURCE_TRANSLATION_HEADER, "expected_translation"
        )
        root = self.build_to_repairs()
        bx.repair_issue_rows(root)
        with self.assertRaisesRegex(SystemExit, f"source_translation_repairs.tsv: row {row_id} "):
            bx.restore_source_translations(root)

    def test_word_translation_stops_when_the_word_has_another_gloss(self) -> None:
        root = self.build_to_repairs()
        bx.repair_issue_rows(root)
        bx.restore_source_translations(root)
        first = read(bx.SOURCE_WORD_TRANSLATION_TABLE)[0]["w_id"]
        word = bx.find_word(bx.find_sentence(root, first.rsplit("W", 1)[0]), first)
        bx.add_word_translation(word, "SOME OTHER GLOSS")
        with self.assertRaisesRegex(SystemExit, f"source_word_translation_repairs.tsv: row {first} "):
            bx.restore_source_word_translations(root)

    def test_variant_stops_on_unexpected_source_text(self) -> None:
        row_id = self.altered("VARIANTS_TABLE", bx.VARIANTS_HEADER, "source_form")
        with self.assertRaisesRegex(SystemExit, f"source_variants.tsv: row {row_id} "):
            bx.check_variant_sources(fresh_root())


class GlossWhitespaceTests(unittest.TestCase):
    def setUp(self) -> None:
        bx.SKIPPED.clear()
        self.tmp = tempfile.TemporaryDirectory()
        self.saved = bx.GLOSS_WHITESPACE_TABLE
        self.rows = read(bx.GLOSS_WHITESPACE_TABLE)

    def tearDown(self) -> None:
        bx.GLOSS_WHITESPACE_TABLE = self.saved
        bx.SKIPPED.clear()
        self.tmp.cleanup()

    def use(self, rows: list[dict[str, str]]) -> None:
        path = Path(self.tmp.name) / "gloss_whitespace_repairs.tsv"
        write(path, rows, bx.GLOSS_WHITESPACE_HEADER)
        bx.GLOSS_WHITESPACE_TABLE = path

    def test_every_row_changes_whitespace_only_and_applies(self) -> None:
        self.assertEqual(len(self.rows), 1127)
        for row in self.rows:
            self.assertNotEqual(row["snapshot_gloss"], row["repaired_gloss"])
            self.assertEqual(
                bx.WHITESPACE.sub("", row["snapshot_gloss"]),
                bx.WHITESPACE.sub("", row["repaired_gloss"]),
            )
        self.assertEqual(bx.repair_gloss_whitespace(fresh_root()), 1127)
        self.assertEqual(bx.SKIPPED, [])

    def test_example_the_root_is_kan(self) -> None:
        root = fresh_root()
        bx.repair_gloss_whitespace(root)
        word = bx.find_word(bx.find_sentence(root, "S375_1"), "S375_1W5")
        self.assertEqual(
            word.find("TRANSL").text,
            "make or prepare food, actor voice (AV). san- 'construct, work on'; "
            "kakanen 'food' with the root kan.",
        )

    def test_second_pass_skips_every_row(self) -> None:
        root = fresh_root()
        bx.repair_gloss_whitespace(root)
        self.assertEqual(bx.repair_gloss_whitespace(root), 0)
        self.assertEqual(len(bx.SKIPPED), 1127)

    def test_row_that_changes_letters_is_refused(self) -> None:
        rows = [dict(self.rows[0])]
        rows[0]["repaired_gloss"] = rows[0]["repaired_gloss"] + "x"
        self.use(rows)
        with self.assertRaisesRegex(SystemExit, "changes more than whitespace"):
            bx.repair_gloss_whitespace(fresh_root())

    def test_unexpected_gloss_stops(self) -> None:
        root = fresh_root()
        row = self.rows[0]
        word = bx.find_word(bx.find_sentence(root, row["w_id"].rsplit("W", 1)[0]), row["w_id"])
        word.find("TRANSL").text = "SOME OTHER GLOSS"
        with self.assertRaisesRegex(SystemExit, f"gloss_whitespace_repairs.tsv: row {row['w_id']} "):
            bx.repair_gloss_whitespace(root)


if __name__ == "__main__":
    unittest.main()


class XorYHeadwordTests(unittest.TestCase):
    """word_alternates / word_gloss_corrections / sentence_translation_notes: apply, skip, stop."""

    def setUp(self) -> None:
        bx.SKIPPED.clear()

    def tearDown(self) -> None:
        bx.SKIPPED.clear()

    def built(self) -> ET.Element:
        root = fresh_root()
        bx.check_variant_sources(root)
        bx.split_alternatives(root)
        bx.annotate_source_segmentation(root)
        bx.repair_issue_rows(root)
        bx.restore_source_translations(root)
        bx.restore_source_word_translations(root)
        return root

    def test_apply_then_second_pass_skips(self) -> None:
        root = self.built()
        bx.correct_word_glosses(root)
        self.assertEqual(bx.add_word_alternates(root), 72)
        bx.add_sentence_translation_notes(root)
        self.assertEqual(bx.SKIPPED, [])
        before = ET.tostring(root)
        bx.correct_word_glosses(root)
        self.assertEqual(bx.add_word_alternates(root), 0)
        bx.add_sentence_translation_notes(root)
        self.assertEqual(len(bx.SKIPPED), 1 + 72 + 1)
        self.assertEqual(ET.tostring(root), before)

    def test_unexpected_text_stops(self) -> None:
        root = self.built()
        word = bx.find_word(bx.find_sentence(root, "S618619_2"), "S618619_2W4")
        word.find("TRANSL").text = "SOMETHING ELSE"
        with self.assertRaisesRegex(SystemExit, "word_gloss_corrections.tsv: row S618619_2W4 "):
            bx.correct_word_glosses(root)
        bx.add_variant_form(bx.find_word(bx.find_sentence(root, "S631_1"), "S631_1W4"), "OTHER")
        with self.assertRaisesRegex(SystemExit, "word_alternates.tsv: row S631_1W4 "):
            bx.add_word_alternates(root)
        bx.find_sentence(root, "S237_1").find("TRANSL").set("notes", "another note")
        with self.assertRaisesRegex(SystemExit, "sentence_translation_notes.tsv: row S237_1 "):
            bx.add_sentence_translation_notes(root)
