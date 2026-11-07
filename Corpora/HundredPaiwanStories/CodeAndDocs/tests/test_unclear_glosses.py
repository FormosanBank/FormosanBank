"""The source's unknown-gloss marker "?" is published as <UNCLEAR/>.

Maintainer's rulings, 2026-10-17: "B. A, plus ? used as a placeholder inside
a gloss", where A = "Convert glosses that are exactly ? or ??"; "B. Glosses
UNCLEAR; sentence translations omitted"; "if the S FORM is simply
<UNCLEAR/>, no Ws. If the W FORM is <UNCLEAR />, no Ms under it."
"""
from __future__ import annotations

import csv
import hashlib
import os
import re
import shutil
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from lxml import etree

from scripts.apply_unclear_glosses import DEFAULT_PLACEHOLDERS, PIECE, apply


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = Path(os.environ.get("PAIWAN_XML_ROOT", ROOT.parent / "XML")).resolve()
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
WHOLE_MARKER = re.compile(r"[?？]{1,3}")


def write_table(path: Path, rows: list[tuple[str, str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["gloss", "lang"])
        writer.writerows(rows)
    return path


def hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*.xml"))
    }


FIXTURE = """<?xml version='1.0' encoding='utf-8'?>
<TEXT id="t" xml:lang="pwn">
    <S id="s1">
        <FORM kindOf="original">a b c d</FORM>
        <TRANSL xml:lang="eng">?</TRANSL>
        <W id="s1W1">
            <FORM kindOf="original">a</FORM>
            <TRANSL xml:lang="eng" kindOf="original">if-main-?-outsider-nom</TRANSL>
            <M id="s1W1M0">
                <FORM kindOf="original">a</FORM>
                <TRANSL xml:lang="eng" kindOf="original">？</TRANSL>
            </M>
        </W>
        <W id="s1W2">
            <FORM kindOf="original">b</FORM>
            <TRANSL xml:lang="eng" kindOf="original">?-what</TRANSL>
        </W>
        <W id="s1W3">
            <FORM kindOf="original">c</FORM>
            <TRANSL xml:lang="eng" kindOf="original">LIG?</TRANSL>
        </W>
        <W id="s1W4">
            <FORM kindOf="original">d</FORM>
            <TRANSL xml:lang="eng" kindOf="original" notes="kept">??</TRANSL>
        </W>
    </S>
</TEXT>
"""


class PublishedUnclearGlossTests(unittest.TestCase):
    """What the published XML must look like after the conversion."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.trees = {
            path.name: etree.parse(str(path)) for path in sorted(XML_ROOT.rglob("*.xml"))
        }

    def test_no_bare_question_mark_gloss_remains(self) -> None:
        leftovers = [
            transl.getparent().get("id")
            for tree in self.trees.values()
            for transl in tree.iter("TRANSL")
            if len(transl) == 0 and WHOLE_MARKER.fullmatch((transl.text or "").strip())
        ]
        self.assertEqual(leftovers, [])

    def test_unclear_glosses_are_counted_and_keep_their_attributes(self) -> None:
        whole: Counter = Counter()
        placeholder: Counter = Counter()
        for tree in self.trees.values():
            for transl in tree.iter("TRANSL"):
                if transl.find("UNCLEAR") is None:
                    continue
                level = transl.getparent().tag
                self.assertIn(level, {"W", "M"})
                self.assertEqual(
                    dict(transl.attrib), {XML_LANG: "eng", "kindOf": "original"}
                )
                self.assertTrue(all(child.tag == "UNCLEAR" for child in transl))
                if transl.text is None and len(transl) == 1 and transl[0].tail is None:
                    whole[level] += 1
                else:
                    placeholder[level] += 1
        self.assertEqual(whole, {"M": 338, "W": 18})
        self.assertEqual(placeholder, {"W": 291})
        for tree in self.trees.values():
            for unclear in tree.iter("UNCLEAR"):
                self.assertEqual(unclear.getparent().tag, "TRANSL")

    def test_example_morpheme(self) -> None:
        morpheme = self.trees["PaiwanCh2_001.xml"].find(".//M[@id='001S7W3M2']")
        self.assertEqual(morpheme.findtext("FORM[@kindOf='original']"), "ta")
        transl = morpheme.find("TRANSL")
        self.assertEqual(
            etree.tostring(transl, encoding="unicode", with_tail=False),
            '<TRANSL xml:lang="eng" kindOf="original"><UNCLEAR/></TRANSL>',
        )

    def test_placeholder_glosses_are_converted(self) -> None:
        published = Counter(
            etree.tostring(transl, encoding="unicode", with_tail=False)
            for tree in self.trees.values()
            for transl in tree.iter("TRANSL")
            if transl.getparent().tag == "W"
        )
        head = '<TRANSL xml:lang="eng" kindOf="original">'
        self.assertEqual(published[head + "if-main-<UNCLEAR/>-outsider-nom</TRANSL>"], 19)
        self.assertEqual(published[head + "<UNCLEAR/>-what</TRANSL>"], 42)
        self.assertEqual(published[head + "stat-exact-<UNCLEAR/></TRANSL>"], 24)
        self.assertEqual(published[head + "?-what</TRANSL>"], 0)

    def test_remaining_question_marks_are_not_whole_pieces(self) -> None:
        remaining: Counter = Counter()
        for tree in self.trees.values():
            for transl in tree.iter("TRANSL"):
                if transl.getparent().tag not in {"W", "M"}:
                    continue
                pieces = [transl.text or ""] + [child.tail or "" for child in transl]
                for piece in pieces:
                    self.assertIsNone(PIECE.search(piece), transl.getparent().get("id"))
                text = "".join(transl.itertext())
                if "?" in text:
                    remaining[text] += 1
        # A ? next to an infix marker or attached to a word stays as written.
        self.assertEqual(sum(remaining.values()), 28)
        self.assertEqual(remaining["?<af>-complete"], 2)
        self.assertEqual(remaining["decide?"], 2)

    def test_no_sentence_translation_or_form_is_unclear(self) -> None:
        for tree in self.trees.values():
            for sentence in tree.iter("S"):
                for transl in sentence.findall("TRANSL"):
                    self.assertFalse(
                        WHOLE_MARKER.fullmatch("".join(transl.itertext()).strip())
                    )
            for form in tree.iter("FORM"):
                self.assertIsNone(form.find("UNCLEAR"))

    def test_committed_placeholder_table(self) -> None:
        with DEFAULT_PLACEHOLDERS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle, delimiter="\t"))
        self.assertEqual(rows[0], ["gloss", "lang"])
        self.assertEqual(len(rows) - 1, 104)
        self.assertEqual({row[1] for row in rows[1:]}, {"eng"})
        self.assertIn(["if-main-?-outsider-nom", "eng"], rows)


class ConversionTests(unittest.TestCase):
    """The conversion step itself, on a fixture and on a published file."""

    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.temp)
        self.xml = self.temp / "XML"
        self.xml.mkdir()

    def test_fixture_with_one_row_table(self) -> None:
        (self.xml / "f.xml").write_text(FIXTURE, encoding="utf-8")
        table = write_table(self.temp / "t.tsv", [("if-main-?-outsider-nom", "eng")])
        stats = apply(self.xml, table)
        self.assertEqual(stats["unclear_w_glosses"], 1)
        self.assertEqual(stats["unclear_m_glosses"], 1)
        self.assertEqual(stats["placeholder_w_glosses"], 1)
        self.assertEqual(stats["omitted_sentence_translations"], 1)
        out = (self.xml / "f.xml").read_text(encoding="utf-8")
        self.assertTrue(out.startswith("<?xml version='1.0' encoding='utf-8'?>\n"))
        root = etree.fromstring(out.encode("utf-8"))

        def gloss(word_id: str) -> str:
            node = root.find(f".//*[@id='{word_id}']/TRANSL")
            return etree.tostring(node, encoding="unicode", with_tail=False)

        self.assertEqual(root.find("S/TRANSL"), None)
        self.assertIn(">if-main-<UNCLEAR/>-outsider-nom<", gloss("s1W1"))
        self.assertIn("><UNCLEAR/><", gloss("s1W1M0"))
        self.assertIn(">?-what<", gloss("s1W2"))  # not listed: kept
        self.assertIn(">LIG?<", gloss("s1W3"))  # attached to a word: kept
        self.assertEqual(
            gloss("s1W4"),
            '<TRANSL xml:lang="eng" kindOf="original" notes="kept"><UNCLEAR/></TRANSL>',
        )
        # Idempotent.
        before = hashes(self.xml)
        again = apply(self.xml, table)
        self.assertEqual(sum(again.values()), 0)
        self.assertEqual(hashes(self.xml), before)

    def test_committed_table_is_a_no_op_on_published_xml(self) -> None:
        shutil.copytree(XML_ROOT, self.xml, dirs_exist_ok=True)
        before = hashes(self.xml)
        stats = apply(self.xml, DEFAULT_PLACEHOLDERS)
        self.assertEqual(sum(stats.values()), 0)
        self.assertEqual(hashes(self.xml), before)

    def test_one_row_table_on_source_question_marks(self) -> None:
        # Put the source's "?" back in a copy of the published XML, then
        # convert with a one-row table: every whole "?" gloss converts, and
        # of the placeholder glosses only the listed one does.
        shutil.copytree(XML_ROOT, self.xml, dirs_exist_ok=True)
        for path in self.xml.rglob("*.xml"):
            path.write_bytes(path.read_bytes().replace(b"<UNCLEAR/>", b"?"))
        table = write_table(self.temp / "t.tsv", [("if-main-?-outsider-nom", "eng")])
        stats = apply(self.xml, table)
        self.assertEqual(stats["unclear_w_glosses"], 18)
        self.assertEqual(stats["unclear_m_glosses"], 338)
        self.assertEqual(stats["placeholder_w_glosses"], 19)
        converted = []
        unlisted = 0
        for path in sorted(self.xml.rglob("*.xml")):
            for transl in etree.parse(str(path)).iter("TRANSL"):
                if transl.text == "if-main-" and len(transl) == 1:
                    self.assertEqual(transl[0].tag, "UNCLEAR")
                    self.assertEqual(transl[0].tail, "-outsider-nom")
                    converted.append(transl.getparent().get("id"))
                if transl.text == "?-what":
                    unlisted += 1
        self.assertEqual(len(converted), 19)
        self.assertEqual(unlisted, 42)

    def test_bad_tables_are_rejected(self) -> None:
        (self.xml / "f.xml").write_text(FIXTURE, encoding="utf-8")
        attached = write_table(self.temp / "a.tsv", [("LIG?", "eng")])
        with self.assertRaisesRegex(ValueError, "no \\? standing as a gloss piece"):
            apply(self.xml, attached)
        unused = write_table(self.temp / "u.tsv", [("never-?-seen", "eng")])
        with self.assertRaisesRegex(ValueError, "match no gloss"):
            apply(self.xml, unused)

    def test_form_that_is_only_unclear_fails(self) -> None:
        fixture = FIXTURE.replace(
            '<FORM kindOf="original">b</FORM>', '<FORM kindOf="original"><UNCLEAR/></FORM>'
        )
        (self.xml / "f.xml").write_text(fixture, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "FORM is only <UNCLEAR/>"):
            apply(self.xml, DEFAULT_PLACEHOLDERS)


if __name__ == "__main__":
    unittest.main()
