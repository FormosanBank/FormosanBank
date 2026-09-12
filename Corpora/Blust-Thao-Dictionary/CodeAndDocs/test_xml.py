"""Structural and source-fidelity tests for the canonical Thao XML."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unicodedata
import unittest
import xml.etree.ElementTree as ET

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))

from build_xml import (  # noqa: E402
    DICTIONARY_PARTS,
    attested_unquoted_tokens,
    normalize_blust_quotes,
)


DATA_PATH = ROOT / "CodeAndDocs" / "expanded-records.json"
XML_DIR = ROOT / "XML" / "Thao"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
EXPECTED_FILES = {
    *(f"blust_2003_thao_text_{number:02d}.xml" for number in range(1, 6)),
    *(
        f"blust_2003_thao_dictionary_{start:04d}_{end:04d}.xml"
        for start, end in DICTIONARY_PARTS
    ),
}


def authority_path() -> Path:
    """The FormosanBank checkout to validate against — never a pinned one (POL-048)."""
    for parent in ROOT.parents:
        if (parent / "QC" / "validation" / "xml_template.xsd").is_file():
            return parent
    configured = os.environ.get("FORMOSANBANK_PATH")
    if configured:
        return Path(configured).resolve()
    return ROOT.parent / "FormosanBank"


def canonical_original(value: str, attested: set[str]) -> str:
    value = normalize_blust_quotes(value, attested)
    return value.translate(
        str.maketrans(
            {
                "–": "-",
                "—": "-",
                "‘": "'",
                "’": "'",
                "“": '"',
                "”": '"',
                "`": "'",
            }
        )
    )


# standardize.py removes ACCENTS_TO_STRIP - acute, breve, macron - and only
# from VOWELS: a diacritic on a consonant is part of the letter. It is NOT a
# blanket "drop every combining mark". Blust's nasalised onomatopoeia
# (makin-ĩhĩh) therefore keeps its tilde in the standard tier: the tilde marks
# nasalisation, which is a segment, not the source prosody an accent records
# (maintainer's ruling, 2026-09-11).
_STRIP = {"\u0301", "\u0306", "\u0304"}
_VOWELS = set("aeiouAEIOU")


def _clusters(value: str):
    """Each base character with the combining marks that follow it."""
    decomposed = unicodedata.normalize("NFD", value)
    out = []
    for character in decomposed:
        if unicodedata.category(character).startswith("M") and out:
            out[-1][1].append(character)
        else:
            out.append((character, []))
    return out


def expected_standard(value: str) -> str:
    unaccented = []
    for cluster_base, marks in _clusters(value):
        if cluster_base in _VOWELS:
            marks = [m for m in marks if m not in _STRIP]
        unaccented.append(
            unicodedata.normalize("NFC", cluster_base + "".join(marks))
        )
    unaccented = "".join(unaccented)
    return (
        unaccented.replace("c", "th")
        .replace("C", "Th")
        .replace("g", "ng")
        .replace("G", "Ng")
    )


class XMLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        cls.attested = attested_unquoted_tokens(cls.data)
        # The published tree takes its dictionary from the schema parse, so
        # this file no longer reads it. What it checks is build_xml.py's own
        # output, run through the same four shared steps and thrown away: that
        # pipeline still produces the five interlinear texts, and it remains the
        # independent reading of the source that caught the accent bug and the
        # printed-page bug (maintainer, 2026-09-11).
        import tempfile
        import build_xml
        from regenerate import find_formosanbank, shared_pipeline
        cls._staging = tempfile.TemporaryDirectory()
        staging = Path(cls._staging.name)
        xml_root = staging / "corpus" / "XML"
        tree_dir = xml_root / "Thao"
        build_xml.write_all(tree_dir)
        shared_pipeline(find_formosanbank(None), Path(sys.executable),
                        staging, xml_root)
        cls.files = sorted(tree_dir.glob("*.xml"))
        cls.roots = [ET.parse(path).getroot() for path in cls.files]
        cls.sentences = [sentence for root in cls.roots for sentence in root.findall("S")]
        cls.sentence_by_id = {sentence.get("id"): sentence for sentence in cls.sentences}

    @classmethod
    def tearDownClass(cls) -> None:
        cls._staging.cleanup()

    def test_provenance_and_schema(self) -> None:
        # POL-052: provenance is recorded, never a gate. The schema check runs
        # against whatever checkout is available.
        provenance = json.loads(
            (ROOT / "CodeAndDocs" / "provenance.json").read_text(encoding="utf-8")
        )
        self.assertRegex(provenance["formosanbank_commit"], r"^[0-9a-f]{40}$")
        authority = authority_path()
        schema = etree.XMLSchema(
            etree.parse(str(authority / "QC" / "validation" / "xml_template.xsd"))
        )
        for path in self.files:
            with self.subTest(path=path.name):
                self.assertTrue(schema.validate(etree.parse(str(path))), schema.error_log)

    def test_file_and_tier_counts(self) -> None:
        self.assertEqual({path.name for path in self.files}, EXPECTED_FILES)
        words = [word for root in self.roots for word in root.findall(".//W")]
        morphemes = [morpheme for root in self.roots for morpheme in root.findall(".//M")]
        self.assertEqual(len(self.roots), 13)
        self.assertEqual(len(self.sentences), 8797)
        # 2,542 interlinear words plus 53,124 dictionary-example words.
        self.assertEqual(len(words), 55678)
        # Only the dictionary examples are morphologically segmented in print,
        # so only they carry an M tier (POL-023, per sentence).
        self.assertEqual(len(morphemes), 74221)
        text_words = [
            word
            for root in self.roots
            if root.get("id", "").startswith("blust_2003_thao_text_")
            for word in root.findall(".//W")
        ]
        self.assertEqual(len(text_words), 2542)
        self.assertEqual(
            sum(len(word.findall("M")) for word in text_words), 0
        )
        self.assertEqual(
            sum(len(root.findall('.//TRANSL[@ver="alt"]')) for root in self.roots),
            2,
        )
        # 25 after the T10 italic gloss face was admitted (was 29). Counted
        # over the interlinear words: the dictionary examples are glossed as
        # wholes, so none of their W or M carries a TRANSL at all.
        self.assertEqual(sum(word.find("TRANSL") is None for word in text_words), 25)
        self.assertEqual(
            sum(1 for word in words if word.find("TRANSL") is not None), 2517
        )

    def test_metadata_and_canonical_routing(self) -> None:
        for root in self.roots:
            self.assertEqual(root.tag, "TEXT")
            self.assertEqual(root.get(XML_LANG), "ssf")
            self.assertEqual(root.get("dialect"), "Thao")
            self.assertEqual(root.get("glottocode"), "thao1240")
            # POL-042: exactly one rights_vocabulary.csv value, no free text.
            self.assertEqual(root.get("copyright"), "CC BY-NC 4.0")
        self.assertFalse((ROOT / "Final_XML").exists())
        self.assertNotIn("xml", {path.name for path in ROOT.iterdir()})

    def test_all_ids_are_globally_unique(self) -> None:
        ids = [
            element.get("id")
            for root in self.roots
            for element in root.iter()
            if element.tag in {"TEXT", "S", "W", "M"}
        ]
        self.assertTrue(all(ids))
        self.assertEqual(len(ids), len(set(ids)))

    def test_source_and_derived_tier_ownership(self) -> None:
        for element in [
            child
            for root in self.roots
            for child in root.iter()
            if child.tag in {"S", "W"}
        ]:
            with self.subTest(element_id=element.get("id")):
                # POL-028: a tier carries exactly one FORM without @ver - the
                # reading the variants vary from - plus any number with one.
                # PHON has no @ver, so there is one per tier and it belongs to
                # the base (21 sentences carry a ver="alt" FORM: Blust brackets
                # material inside a word to give two spellings of one lexeme).
                original = [
                    f for f in element.findall('FORM[@kindOf="original"]')
                    if not f.get("ver")
                ]
                standard = [
                    f for f in element.findall('FORM[@kindOf="standard"]')
                    if not f.get("ver")
                ]
                original_phon = element.findall('PHON[@kindOf="original"]')
                standard_phon = element.findall('PHON[@kindOf="standard"]')
                self.assertEqual(len(original), 1)
                self.assertEqual(len(standard), 1)
                for kind in ("original", "standard"):
                    variants = [
                        f for f in element.findall(f'FORM[@kindOf="{kind}"]')
                        if f.get("ver")
                    ]
                    for variant in variants:
                        self.assertTrue(variant.text, element.get("id"))
                self.assertEqual(len(original_phon), 1)
                self.assertEqual(len(standard_phon), 1)
                self.assertTrue(original[0].text)
                self.assertTrue(standard[0].text)
                self.assertTrue(original_phon[0].text)
                self.assertTrue(standard_phon[0].text)
                self.assertEqual(standard[0].text, expected_standard(original[0].text))

    def test_every_expanded_dictionary_source_is_preserved(self) -> None:
        for record in self.data["dictionary_examples"]:
            with self.subTest(record_id=record["id"]):
                sentence = self.sentence_by_id[record["id"]]
                original = sentence.find('FORM[@kindOf="original"]')
                self.assertEqual(
                    original.text,
                    canonical_original(record["source"], self.attested),
                )
                # The W tier is the sentence retokenized, and the M tier its
                # printed morpheme boundaries (POL-023): the W FORMs must spell
                # the sentence back, and the M FORMs their word.
                words = sentence.findall("W")
                self.assertEqual(
                    [w.find('FORM[@kindOf="original"]').text for w in words],
                    original.text.split(),
                )
                for word in words:
                    morphemes = word.findall("M")
                    if not morphemes:
                        continue
                    self.assertEqual(
                        "-".join(
                            m.find('FORM[@kindOf="original"]').text
                            for m in morphemes
                        ),
                        word.find('FORM[@kindOf="original"]').text,
                    )

    def test_every_expanded_text_word_is_preserved(self) -> None:
        expected_word_count = 0
        for text in self.data["texts"]:
            for record in text["sentences"]:
                suffix = (
                    f"-{record['variant_suffix']}"
                    if record.get("variant_suffix")
                    else ""
                )
                sentence_id = (
                    f"blust-text-t{int(text['number']):02d}-"
                    f"s{int(record['number']):03d}{suffix}"
                )
                sentence = self.sentence_by_id[sentence_id]
                self.assertEqual(
                    sentence.find('FORM[@kindOf="original"]').text,
                    canonical_original(record["form"], self.attested),
                )
                words = sentence.findall("W")
                self.assertEqual(len(words), len(record["words"]))
                expected_word_count += len(words)
                normalized_words = canonical_original(
                    " ".join(source_word["form"] for source_word in record["words"]),
                    self.attested,
                ).split(" ")
                for expected, word in zip(normalized_words, words, strict=True):
                    self.assertEqual(word.find('FORM[@kindOf="original"]').text, expected)
        self.assertEqual(expected_word_count, 2542)

    def test_literal_notes_and_translation_alternatives(self) -> None:
        literal = self.sentence_by_id["blust-dict-p0431-e003"]
        translations = literal.findall("TRANSL")
        self.assertEqual(len(translations), 1)
        self.assertEqual(translations[0].text, "I have received your letter")
        self.assertEqual(
            translations[0].get("notes"),
            "Literal translation: Your letter was sent, has reached me",
        )
        alternatives = self.sentence_by_id["blust-dict-p0348-e009"].findall(
            "TRANSL"
        )
        self.assertEqual(len(alternatives), 2)
        self.assertIsNone(alternatives[0].get("ver"))
        self.assertEqual(alternatives[1].get("ver"), "alt")

    def test_quotes_are_not_phonologized_as_glottal_stops(self) -> None:
        quoted = self.sentence_by_id["blust-text-t01-s006"]
        form = quoted.find('FORM[@kindOf="original"]').text
        phon = quoted.find('PHON[@kindOf="original"]').text
        self.assertIn('"Maniun', form)
        self.assertIn('palhaushin"', form)
        self.assertNotIn("ʔmaniun", phon)
        lexical = self.sentence_by_id["blust-dict-p0804-e019"]
        self.assertIn("qriu'", lexical.find('FORM[@kindOf="original"]').text)
        self.assertIn("qriuʔ", lexical.find('PHON[@kindOf="original"]').text)


if __name__ == "__main__":
    unittest.main()
