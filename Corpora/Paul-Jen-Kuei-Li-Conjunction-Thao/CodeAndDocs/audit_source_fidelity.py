#!/usr/bin/env python3
"""Audit fixed source examples and structural invariants in the generated XML."""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "CodeAndDocs" / "reviewed_examples.tsv"
FINAL = ROOT / "Final_XML" / "Thao" / "li_2014_conjunction_in_thao.xml"
EDGE_PUNCTUATION = ".,!?;:…"

# Five independent checks transcribed from printed pp. 402, 404, 405, and 406.
FIXED_CHECKS = {
    "li2014_thao_S001": {
        "original": "ma-faðaq m-apa buna masa kawi.",
        "standard": "mafaðaq mapa buna masa kawi.",
        "w_count": 5,
        "word": ("ma-faðaq", "AF-know", (("ma", "AF"), ("faðaq", "know"))),
    },
    "li2014_thao_S003": {
        "original": "ma-faðaq ma-didir paðay masa q<m>aʃiʃi ðaʃuq.",
        "standard": "mafaðaq madidir paðay masa qmaʃiʃi ðaʃuq.",
        "w_count": 6,
        "word": ("q<m>aʃiʃi", "sift<AF>", (("qaʃiʃi", "sift"), ("-m-", "<AF>"))),
    },
    "li2014_thao_S005": {
        "original": "numa maniun ya miku-ki-náy, u-tusi-wan maniun mita a taun, m-ara sa fa-finʃiq a paðay, buna, ɬari, suksuk, makamun pu-náy maɬuyða.",
        "standard": "numa maniun ya mikukináy, utusiwan maniun mita a taun, mara sa fafinʃiq a paðay, buna, ɬari, suksuk, makamun punáy maɬuyða.",
        "w_count": 20,
        "word": ("miku-ki-náy", "want-stay-here", (("miku", "want"), ("ki", "stay"), ("náy", "here"))),
    },
    "li2014_thao_S017": {
        "original": "numa iðáy ɬa-ɬawʃin a fafaw quθquθ-an minabút, maqa antu a-m-utun, maqa a-ma-daqri ya iðáy a fa ɬawʃin-an.",
        "standard": "numa iðáy ɬaɬawʃin a fafaw quθquθan minabút, maqa antu amutun, maqa amadaqri ya iðáy a fa ɬawʃinan.",
        "w_count": 17,
        "word": ("a-ma-daqri", "IRR-STA-smooth", (("a", "IRR"), ("ma", "STA"), ("daqri", "smooth"))),
    },
    "li2014_thao_S024": {
        "original": "numa mataŋ-kaktun-iða, parʃian ya ma-qa-quyaʃ ʃa-ʃayla wa quyaʃ.",
        "standard": "numa mataŋkaktuniða, parʃian ya maqaquyaʃ ʃaʃayla wa quyaʃ.",
        "w_count": 8,
        "word": ("ma-qa-quyaʃ", "AF-RED-sing", (("ma", "AF"), ("qa", "RED"), ("quyaʃ", "sing"))),
    },
}


def forms(parent: ET.Element) -> dict[str, str]:
    return {node.attrib["kindOf"]: node.text or "" for node in parent.findall("FORM")}


def transl(parent: ET.Element, kind: str | None = None) -> str:
    for node in parent.findall("TRANSL"):
        if node.attrib.get("kindOf") == kind:
            return node.text or ""
    raise AssertionError(f"missing translation kind={kind!r}")


def main() -> None:
    with RECORDS.open(encoding="utf-8", newline="") as handle:
        records = {row["id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    root = ET.parse(FINAL).getroot()
    sentences = {node.attrib["id"]: node for node in root.findall("S")}
    assert len(records) == len(sentences) == 27

    for sentence_id, expected in FIXED_CHECKS.items():
        row = records[sentence_id]
        sentence = sentences[sentence_id]
        sentence_forms = forms(sentence)
        assert row["original"] == expected["original"] == sentence_forms["original"]
        assert expected["standard"] == sentence_forms["standard"]
        assert re.sub(r"[-=<>]", "", row["original"]) == sentence_forms["standard"]
        words = sentence.findall("W")
        assert len(words) == expected["w_count"]
        expected_form, expected_gloss, expected_morphemes = expected["word"]
        word = next(node for node in words if forms(node)["original"] == expected_form)
        assert forms(word)["standard"] == expected_form
        assert transl(word, "gloss") == expected_gloss
        actual_morphemes = tuple(
            (forms(node)["original"], transl(node, "original"))
            for node in word.findall("M")
        )
        assert actual_morphemes == expected_morphemes
        print(f"PASS {sentence_id}: {row['source_locator']}")

    for number, sentence_id in enumerate(records, start=1):
        row = records[sentence_id]
        sentence = sentences[sentence_id]
        words = sentence.findall("W")
        if row["gloss"]:
            source_words = [token.strip(EDGE_PUNCTUATION) for token in row["original"].split()]
            source_glosses = row["gloss"].split()
            assert len(words) == len(source_words) == len(source_glosses)
            assert [forms(word)["original"] for word in words] == source_words
            assert [transl(word, "gloss") for word in words] == source_glosses
        else:
            assert number >= 25 and not words and not sentence.findall(".//M")

    print("PASS all 24 glossed examples align; S025-S027 remain sentence-only")
    print("Source-fidelity audit complete: 5 fixed checks, 27 structural checks")


if __name__ == "__main__":
    main()
