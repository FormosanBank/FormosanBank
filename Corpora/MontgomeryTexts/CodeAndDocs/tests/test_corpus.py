from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

CORPUS_ROOT = Path(__file__).resolve().parents[2]
XML_ROOT = CORPUS_ROOT / "XML"
LEDGER_PATH = CORPUS_ROOT / "CodeAndDocs/source_records.json"
SOURCE_PATH = CORPUS_ROOT / "CodeAndDocs/Original.pdf"
MANIFEST_PATH = CORPUS_ROOT / "CodeAndDocs/source_manifest.json"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
PUBLICATION_NOTICE = "All rights reserved; FormosanBank has permission to publish."
PRIVATE_SOURCE_COMMIT = "e1f52f43ab9e17b1d9a99329964b2ab64fbe864a"

EXPECTED_TEXT_IDS = {
    "Amis/Day_I_Now.xml": "Montgomery_Amis_Day_I_Now",
    "Amis/Fire_and_Water.xml": "Montgomery_Amis_Fire_and_Water",
    "Amis/Silo.xml": "Montgomery_Amis_Silo",
}
EXPECTED_SENTENCE_IDS = {
    "Amis/Day_I_Now.xml": [f"S{number}" for number in range(2, 19)],
    "Amis/Fire_and_Water.xml": [f"S{number}" for number in range(2, 12)],
    "Amis/Silo.xml": [f"S{number}" for number in range(2, 12)],
}


def roots() -> dict[str, ET.Element]:
    return {
        str(path.relative_to(XML_ROOT)): ET.parse(path).getroot()
        for path in sorted(XML_ROOT.rglob("*.xml"))
    }


def tier_values(element: ET.Element, tag: str) -> list[tuple[str, str]]:
    values = []
    for item in element.findall(tag):
        key = item.get("kindOf") if tag == "FORM" else item.get(XML_LANG)
        values.append((key or "", item.text or ""))
    return values


def test_inventory_is_the_three_existing_public_texts() -> None:
    corpus = roots()
    assert set(corpus) == set(EXPECTED_TEXT_IDS)
    counts = {
        tag: sum(sum(1 for _ in root.iter(tag)) for root in corpus.values())
        for tag in ("S", "W", "M")
    }
    assert counts == {"S": 37, "W": 351, "M": 0}


def test_surviving_public_ids_are_preserved() -> None:
    for path, root in roots().items():
        assert root.get("id") == EXPECTED_TEXT_IDS[path]
        sentence_ids = [sentence.get("id") for sentence in root.findall("S")]
        assert sentence_ids == EXPECTED_SENTENCE_IDS[path]
        assert "S1" not in sentence_ids
        for sentence in root.findall("S"):
            sentence_id = sentence.get("id")
            for number, word in enumerate(sentence.findall("W"), start=1):
                assert word.get("id") == f"{sentence_id}W{number}"


def test_xml_matches_the_public_source_ledger() -> None:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    corpus = roots()
    assert len(ledger["texts"]) == 3
    for text in ledger["texts"]:
        root = corpus[text["path"]]
        assert root.get("{http://www.w3.org/XML/1998/namespace}lang") == "ami"
        assert root.get("citation") == text["citation"]
        assert root.get("copyright") == text["copyright"] == PUBLICATION_NOTICE
        sentences = root.findall("S")
        assert len(sentences) == len(text["sentences"])
        for record, sentence in zip(text["sentences"], sentences, strict=True):
            assert int(sentence.get("id", "S0")[1:]) == record["source_number"] + 1
            assert tier_values(sentence, "FORM")[0] == (
                "original",
                record["forms"][0]["text"],
            )
            assert tier_values(sentence, "TRANSL") == [
                (item["lang"], item["text"]) for item in record["translations"]
            ]
            words = sentence.findall("W")
            assert len(words) == len(record["words"])
            for word_record, word in zip(record["words"], words, strict=True):
                assert tier_values(word, "FORM")[0] == (
                    "original",
                    word_record["forms"][0]["text"],
                )
                assert tier_values(word, "TRANSL") == [
                    (item["lang"], item["text"])
                    for item in word_record.get("translations", [])
                ]


def test_derived_tiers_are_conservative() -> None:
    for root in roots().values():
        assert not list(root.iter("PHON"))
        assert not list(root.iter("M"))
        for element in (*root.findall("S"), *root.iter("W")):
            original = element.find("FORM[@kindOf='original']")
            standard = element.find("FORM[@kindOf='standard']")
            assert original is not None
            assert standard is not None
            assert standard.text == original.text


def test_source_pdf_matches_the_reviewed_manifest() -> None:
    assert SOURCE_PATH.stat().st_size == 874535
    assert hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest() == (
        "7a9ad6482f4d1c38a45e2ba50b4a037155d4e771ce4586d64f06852e8bf8e2bd"
    )


def test_manifest_records_rights_and_private_source_commit() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source = manifest["source"]
    assert source["rights"] == (
        "Publication rights confirmed by the FormosanBank maintainer on 2026-08-23; "
        "no open license is asserted."
    )
    assert source["private_source_repo"] == "FormosanBank/Formosan-Old_Texts"
    assert source["private_source_commit"] == PRIVATE_SOURCE_COMMIT
