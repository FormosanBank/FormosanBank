#!/usr/bin/env python3
"""Audit source identity, reviewed records, and generated Thao tiers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

from build_xml import parse_morphemes, word_tokens

CODE_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = Path(__file__).resolve().parents[2]
RECORDS = CODE_ROOT / "data" / "reviewed_examples.tsv"
LEDGER = CODE_ROOT / "data" / "source_ledger.csv"
MANIFEST = CODE_ROOT / "data" / "source_manifest.json"
XML = CORPUS_ROOT / "XML" / "Thao" / "li_2014_conjunction_in_thao.xml"

EXPECTED_SHA256 = "fab9b60ce52e47530805204c1d5beed02e52e63972e8315d9a1996c8e79248f1"
EXPECTED_BYTES = 8_566_297
EXPECTED_PAGES = 402

SOURCE_SNIPPETS = (
    "Copyright held by the authors, released under Creative Commons Attribution Licence (CC BY 4.0).",
    "firewoodon my back.",
    "LIG erson and/then",
    "catching wildanimals",
    "ɬpaðiSan.",
    "a muʃa iDa yaku ya saqaDi.",
    "ya ʃaʃanu maθuaw waDaqan maharbuk.",
    "hadana ita iDa ya aDaDak.",
)

SOURCE_LITERAL_FIXTURES = {
    "li2014_thao_S001": {
        "translation": "I know how to carry sweet potatoes and firewoodon my back.",
    },
    "li2014_thao_S004": {
        "translation": "Having no mother or father, then (one is) sad listening (to the songs)",
    },
    "li2014_thao_S009": {
        "gloss": "there DET some LIG erson and/then some LIG person fear<AF>",
    },
    "li2014_thao_S015": {
        "translation": "Because (he) was very capable when (he) was catching wildanimals",
    },
    "li2014_thao_S021": {
        "original": (
            "myaðáy a malan-ta-tnur t<m>aðam ya tima sa ma-ʔania panaq "
            "sa iðáy ɬpaðiSan."
        ),
    },
    "li2014_thao_S025": {
        "original": "a muʃa iDa yaku ya saqaDi.",
        "translation": "I'll leave this noon",
    },
    "li2014_thao_S026": {
        "original": "ya ʃaʃanu maθuaw waDaqan maharbuk.",
        "translation": "In the morning the lake is very foggy",
    },
    "li2014_thao_S027": {
        "original": "hadana ita iDa ya aDaDak.",
        "translation": "Let's adopt a child",
    },
}


def _read_records() -> dict[str, dict[str, str]]:
    with RECORDS.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    assert len(rows) == 27
    return {row["id"]: row for row in rows}


def _forms(parent: ET.Element) -> dict[str, str]:
    return {
        node.attrib["kindOf"]: "".join(node.itertext())
        for node in parent.findall("FORM")
    }


def _translation(parent: ET.Element, kind: str | None = None) -> str:
    for node in parent.findall("TRANSL"):
        if node.attrib.get("kindOf") == kind:
            return node.text or ""
    raise AssertionError(f"missing translation kind={kind!r}")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


def _source_text(source: Path) -> str:
    assert source.is_file(), source
    assert source.stat().st_size == EXPECTED_BYTES
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == EXPECTED_SHA256

    info = subprocess.run(
        ["pdfinfo", str(source)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert re.search(rf"^Pages:\s+{EXPECTED_PAGES}$", info, re.MULTILINE)

    with tempfile.TemporaryDirectory(prefix="thao-source-audit-") as tmp:
        text_path = Path(tmp) / "article.txt"
        subprocess.run(
            [
                "pdftotext",
                "-f",
                "394",
                "-l",
                "402",
                "-layout",
                str(source),
                str(text_path),
            ],
            check=True,
        )
        extracted = text_path.read_text(encoding="utf-8")

    compact_source = _compact(extracted)
    for snippet in SOURCE_SNIPPETS:
        assert _compact(snippet) in compact_source, snippet
    return extracted


def _audit_manifest() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["sha256"] == EXPECTED_SHA256
    assert manifest["bytes"] == EXPECTED_BYTES
    assert manifest["pages"] == EXPECTED_PAGES
    assert manifest["article_pdf_pages"] == "394-402"


def _audit_ledger(records: dict[str, dict[str, str]]) -> None:
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    retained = [row for row in rows if row["included_in_xml"] == "yes"]
    excluded = [row for row in rows if row["included_in_xml"] == "no"]
    assert len(rows) == 31
    assert len(retained) == len(records) == 27
    assert len(excluded) == 4
    assert {row["final_s_id"] for row in retained} == set(records)
    assert {row["page"] for row in excluded} == {"394", "400", "401", "402"}


def _audit_source_anchors(
    root: ET.Element,
    records: dict[str, dict[str, str]],
) -> None:
    sentences = {sentence.attrib["id"]: sentence for sentence in root.findall("S")}
    assert set(sentences) == set(records)

    for sentence_id, row in records.items():
        sentence = sentences[sentence_id]
        assert _forms(sentence)["original"] == row["original"]
        assert _translation(sentence) == row["translation"]
        expected_words = word_tokens(row["original"]) if row["gloss"] else []
        expected_glosses = row["gloss"].split() if row["gloss"] else []
        words = sentence.findall("W")
        assert len(words) == len(expected_words) == len(expected_glosses)
        for word_number, (word, word_form, word_gloss) in enumerate(
            zip(words, expected_words, expected_glosses, strict=True),
            start=1,
        ):
            assert _forms(word)["original"] == word_form
            assert _translation(word, "original") == word_gloss
            expected_morphemes = parse_morphemes(word_form, word_gloss)
            morphemes = word.findall("M")
            assert len(morphemes) == len(expected_morphemes) >= 1
            for morpheme_number, (morpheme, expected) in enumerate(
                zip(morphemes, expected_morphemes, strict=True),
                start=1,
            ):
                expected_form, expected_gloss = expected
                assert morpheme.attrib["id"] == (
                    f"{sentence_id}_w{word_number:02d}_m{morpheme_number:02d}"
                )
                assert _forms(morpheme)["original"] == expected_form
                assert _translation(morpheme, "original") == expected_gloss


def _audit_literal_fixtures(records: dict[str, dict[str, str]]) -> None:
    for sentence_id, expected in SOURCE_LITERAL_FIXTURES.items():
        row = records[sentence_id]
        for field, value in expected.items():
            assert row[field] == value, (sentence_id, field, row[field], value)


def _audit_raw(root: ET.Element) -> None:
    assert not root.findall('.//FORM[@kindOf="standard"]')
    assert not root.findall(".//PHON")


def _audit_final(root: ET.Element) -> None:
    originals = root.findall('.//FORM[@kindOf="original"]')
    standards = root.findall('.//FORM[@kindOf="standard"]')
    standard_phon = root.findall('.//PHON[@kindOf="standard"]')
    assert len(originals) == len(standards) == len(standard_phon) == 547
    assert not root.findall('.//PHON[@kindOf="original"]')
    assert all("*" not in (node.text or "") for node in standard_phon)

    sentences = {sentence.attrib["id"]: sentence for sentence in root.findall("S")}
    expected_standards = {
        "li2014_thao_S001": "mafazaq mapa buna masa kawi.",
        "li2014_thao_S003": "mafazaq madidir pazay masa q<m>ashishi zashuq.",
        "li2014_thao_S021": (
            "myazay a malantatnur t<m>azam ya tima sa ma'ania panaq sa "
            "izay lhpazishan."
        ),
        "li2014_thao_S025": "a musha iza yaku ya saqazi.",
    }
    for sentence_id, expected in expected_standards.items():
        assert _forms(sentences[sentence_id])["standard"] == expected

    for sentence in sentences.values():
        standard = _forms(sentence)["standard"]
        assert "-" not in standard and "=" not in standard


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--stage", required=True, choices=("raw", "final"))
    args = parser.parse_args()

    records = _read_records()
    _source_text(args.source)
    _audit_manifest()
    _audit_ledger(records)
    _audit_literal_fixtures(records)

    root = ET.parse(XML).getroot()
    assert len(root.findall("S")) == 27
    assert len(root.findall(".//W")) == 211
    assert len(root.findall(".//M")) == 309
    _audit_source_anchors(root, records)
    if args.stage == "raw":
        _audit_raw(root)
    else:
        _audit_final(root)

    print(
        f"Source audit passed ({args.stage}): 9 article pages, 27 records, "
        "4 exclusions, 211 W, 309 M"
    )


if __name__ == "__main__":
    main()
