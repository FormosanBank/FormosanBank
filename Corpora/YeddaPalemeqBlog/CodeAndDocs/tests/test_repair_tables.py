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
        self.assertEqual(len(bx.restore_source_word_translations(root)), 41)
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
        self.assertEqual(len(bx.SKIPPED), 9 + 24 + 41)
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


if __name__ == "__main__":
    unittest.main()
