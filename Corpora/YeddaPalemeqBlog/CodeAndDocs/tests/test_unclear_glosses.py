"""Unknown-gloss markers and the ruled gloss-to-notes moves (maintainer, 2026-10-17).

- A W/M gloss that is exactly `?`, `??` or `???` (half- or full-width) is the
  source's own unknown-gloss marker and becomes <TRANSL ...><UNCLEAR/></TRANSL>.
- CodeAndDocs/gloss_to_notes.tsv lists eight word glosses ruled one by one:
  the whole old gloss goes to TRANSL/@notes and the gloss becomes <UNCLEAR/>
  (seven words) or "to find" (S313_1 k<ar>im, whose morphemes stay unglossed).
- A `?` standing as a whole piece inside a longer gloss becomes <UNCLEAR/> only
  in glosses listed in CodeAndDocs/unclear_gloss_placeholders.tsv, which ships
  with no rows.
"""

from __future__ import annotations

import csv
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
XML = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
AUDIT = ROOT / "data/formosanbank_audit"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

sys.path.insert(0, str(ROOT / "scripts"))
import build_xml  # noqa: E402

FIND_GLOSS = (
    "to find. I do not know what -ar-means, but it seems to denote agency like "
    "-em- or -en-? The root iskim'find people, find object'."
)
RULED_UNCLEAR = {
    "S419_1W20": ("siayang", "? I can't make this word."),
    "S425_1W4": ("i", "? I am not sure."),
    "S425_1W27": ("paseketj", "? I cannot find this word."),
    "S427_1W7": ("mavesuang", "? I don't know this word."),
    "S430_1W7": (
        "djumaken",
        "? I cannot find this word. sinsi kalekes's translation is like to be "
        "found out or give away.",
    ),
    "S617_1W4": (
        "an",
        "? As far as the syntax goes, I think it should be the oblique "
        "casetaortua. However, the recording sounds likean. Could it "
        "bema-djadjas-anwith the LOC marker? I am not sure. I don't know how "
        "to explain this.",
    ),
    "S640_1W6": (
        "nu",
        "? Usuallynuis your (2nd personal plural GEN). Here why the elder "
        "saysnuis unknown to me.",
    ),
}


def gloss_parts(translation: ET.Element) -> list[str]:
    """Text and UNCLEAR markers in document order, whitespace-only text dropped."""
    parts = []
    if translation.text and translation.text.strip():
        parts.append(translation.text)
    for child in translation:
        parts.append(f"<{child.tag}/>")
        if child.tail and child.tail.strip():
            parts.append(child.tail)
    return parts


class PublishedUnclearGlossTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = ET.parse(XML).getroot()

    def word(self, word_id: str) -> ET.Element:
        word = self.root.find(f".//W[@id='{word_id}']")
        self.assertIsNotNone(word)
        return word  # type: ignore[return-value]

    def test_whole_question_mark_gloss_is_unclear(self) -> None:
        word = self.word("S77_1W5")
        self.assertEqual(word.find("FORM[@kindOf='original']").text, "nu")
        translations = word.findall("TRANSL")
        self.assertEqual(len(translations), 1)
        self.assertEqual(translations[0].attrib, {XML_LANG: "eng"})
        self.assertEqual(gloss_parts(translations[0]), ["<UNCLEAR/>"])

    def test_ruled_glosses_become_unclear_with_notes(self) -> None:
        for word_id, (form, old_gloss) in RULED_UNCLEAR.items():
            word = self.word(word_id)
            self.assertEqual(word.find("FORM[@kindOf='original']").text, form)
            translations = word.findall("TRANSL")
            self.assertEqual(len(translations), 1, word_id)
            self.assertEqual(
                translations[0].attrib, {XML_LANG: "eng", "notes": old_gloss}
            )
            self.assertEqual(gloss_parts(translations[0]), ["<UNCLEAR/>"], word_id)

    def test_find_gloss_shortened_and_morphemes_unglossed(self) -> None:
        word = self.word("S313_1W3")
        self.assertEqual(word.find("FORM[@kindOf='original']").text, "k<ar>im")
        translations = word.findall("TRANSL")
        self.assertEqual(len(translations), 1)
        self.assertEqual(translations[0].text, "to find")
        self.assertEqual(len(translations[0]), 0)
        self.assertEqual(translations[0].get("notes"), FIND_GLOSS)
        morphemes = word.findall("M")
        self.assertEqual(
            [m.find("FORM[@kindOf='original']").text for m in morphemes],
            ["k-im", "-ar-"],
        )
        for morpheme in morphemes:
            self.assertEqual(morpheme.findall("TRANSL"), [])

    def test_no_marker_gloss_or_bounded_piece_remains(self) -> None:
        for element in [*self.root.iter("W"), *self.root.iter("M")]:
            for translation in element.findall("TRANSL"):
                text = "".join(translation.itertext())
                self.assertIsNone(
                    build_xml.WHOLE_UNKNOWN_GLOSS.fullmatch(text.strip()),
                    f"{element.get('id')} keeps the gloss {text!r}",
                )
                self.assertIsNone(
                    build_xml.PLACEHOLDER_PIECE.search(text),
                    f"{element.get('id')} keeps a bounded ? in {text!r}",
                )

    def test_unclear_only_where_ruled(self) -> None:
        holders = sorted(
            element.get("id")
            for element in [*self.root.iter("W"), *self.root.iter("M")]
            for translation in element.findall("TRANSL")
            if translation.find("UNCLEAR") is not None
        )
        self.assertEqual(holders, sorted(["S77_1W5", *RULED_UNCLEAR]))
        self.assertEqual(len(list(self.root.iter("UNCLEAR"))), 8)
        for sentence in self.root.findall("S"):
            for child in sentence:
                if child.tag in {"FORM", "PHON", "TRANSL"}:
                    self.assertIsNone(child.find("UNCLEAR"))

    def test_attached_question_marks_are_kept(self) -> None:
        expected = {"S652653654_1W5": "LIG?", "S644645_2W4": "right?"}
        for word_id, gloss in expected.items():
            self.assertEqual(self.word(word_id).find("TRANSL").text, gloss)

    def test_audit_lists_every_change(self) -> None:
        with (AUDIT / "unclear_gloss_review.tsv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        got = {(r["id"], r["source_gloss"], r["unclear_count"], r["resolution"]) for r in rows}
        expected = {("S77_1W5", "?", "1", "whole_unknown_gloss_marker")}
        expected |= {
            (word_id, old, "1", "ruled_gloss_to_notes")
            for word_id, (_, old) in RULED_UNCLEAR.items()
        }
        expected.add(("S313_1W3", FIND_GLOSS, "0", "ruled_gloss_to_notes"))
        self.assertEqual(len(rows), 9)
        self.assertEqual(got, expected)

    def test_shipped_placeholder_table_has_no_rows(self) -> None:
        self.assertEqual(
            build_xml.UNCLEAR_PLACEHOLDER_TABLE.read_text(encoding="utf-8"),
            "gloss\tlang\n",
        )
        self.assertEqual(
            build_xml.read_placeholder_table(build_xml.UNCLEAR_PLACEHOLDER_TABLE),
            set(),
        )


SYNTHETIC = """<TEXT>
  <S id="S1">
    <W id="S1W1"><TRANSL xml:lang="eng">to go-? there</TRANSL></W>
    <W id="S1W2"><TRANSL xml:lang="eng">? I am not sure.</TRANSL></W>
    <W id="S1W3"><TRANSL xml:lang="eng">LIG?</TRANSL></W>
    <W id="S1W4"><TRANSL xml:lang="eng">??</TRANSL>
      <M id="S1W4M1"><TRANSL xml:lang="eng" notes="kept">？</TRANSL></M>
    </W>
  </S>
</TEXT>"""


class PlaceholderTableTests(unittest.TestCase):
    """A temporary one-row placeholder table applied to a small synthetic tree."""

    def setUp(self) -> None:
        self.root = ET.fromstring(SYNTHETIC)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def table(self, *rows: str) -> Path:
        path = Path(self.tmp.name) / "unclear_gloss_placeholders.tsv"
        path.write_text("gloss\tlang\n" + "".join(r + "\n" for r in rows), encoding="utf-8")
        return path

    def gloss(self, element_id: str) -> ET.Element:
        return self.root.find(f".//*[@id='{element_id}']/TRANSL")

    def test_one_row_table(self) -> None:
        placeholders = build_xml.read_placeholder_table(self.table("to go-? there\teng"))
        rows = build_xml.mark_unclear_glosses(self.root, placeholders)
        self.assertEqual(gloss_parts(self.gloss("S1W1")), ["to go-", "<UNCLEAR/>", " there"])
        self.assertEqual(self.gloss("S1W1").attrib, {XML_LANG: "eng"})
        # Unlisted longer gloss and attached `?` are left as written.
        self.assertEqual(self.gloss("S1W2").text, "? I am not sure.")
        self.assertEqual(len(self.gloss("S1W2")), 0)
        self.assertEqual(self.gloss("S1W3").text, "LIG?")
        # Whole markers convert without a row, keeping attributes.
        self.assertEqual(gloss_parts(self.gloss("S1W4")), ["<UNCLEAR/>"])
        self.assertEqual(gloss_parts(self.gloss("S1W4M1")), ["<UNCLEAR/>"])
        self.assertEqual(self.gloss("S1W4M1").get("notes"), "kept")
        self.assertEqual(
            sorted((r["id"], r["unclear_count"], r["resolution"]) for r in rows),
            [
                ("S1W1", "1", "listed_placeholder_pieces"),
                ("S1W4", "1", "whole_unknown_gloss_marker"),
                ("S1W4M1", "1", "whole_unknown_gloss_marker"),
            ],
        )

    def test_empty_table_changes_no_longer_gloss(self) -> None:
        build_xml.mark_unclear_glosses(self.root, set())
        self.assertEqual(self.gloss("S1W1").text, "to go-? there")
        self.assertEqual(self.gloss("S1W2").text, "? I am not sure.")

    def test_piece_boundaries(self) -> None:
        split = build_xml.PLACEHOLDER_PIECE.split
        self.assertEqual(split("a-?-b"), ["a-", "-b"])
        self.assertEqual(split("a=?.b ?"), ["a=", ".b ", ""])
        self.assertEqual(split("LIG?"), ["LIG?"])
        self.assertEqual(split("right?"), ["right?"])
        self.assertEqual(split("dja- '?'"), ["dja- '?'"])

    def test_unmatched_or_invalid_rows_fail(self) -> None:
        with self.assertRaises(SystemExit):
            build_xml.mark_unclear_glosses(
                self.root,
                build_xml.read_placeholder_table(self.table("? not in corpus\teng")),
            )
        for bad in ("?\teng", "LIG?\teng", "? I am not sure."):
            with self.assertRaises(SystemExit):
                build_xml.read_placeholder_table(self.table(bad))


if __name__ == "__main__":
    unittest.main()
