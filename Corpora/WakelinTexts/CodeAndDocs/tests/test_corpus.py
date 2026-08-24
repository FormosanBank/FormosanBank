from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

CORPUS_ROOT = Path(__file__).resolve().parents[2]
XML_ROOT = CORPUS_ROOT / "XML"
CODE_ROOT = CORPUS_ROOT / "CodeAndDocs"
LEDGER_PATH = CODE_ROOT / "source_records.json"
DECISIONS_PATH = CODE_ROOT / "alternative_expansions.json"
ID_LEDGER_PATH = CODE_ROOT / "public_id_ledger.json"
MANIFEST_PATH = CODE_ROOT / "source_manifest.json"
SOURCE_PATH = CODE_ROOT / "Original.pdf"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
PUBLICATION_NOTICE = "All rights reserved; FormosanBank has permission to publish."
PRIVATE_SOURCE_COMMIT = "e1f52f43ab9e17b1d9a99329964b2ab64fbe864a"

sys.path.insert(0, str(CODE_ROOT))
from expand_alternatives import load_expanded_ledger  # noqa: E402


def roots(xml_root: Path = XML_ROOT) -> dict[str, ET.Element]:
    return {
        str(path.relative_to(xml_root)): ET.parse(path).getroot()
        for path in sorted(xml_root.rglob("*.xml"))
    }


def node_counts(corpus: dict[str, ET.Element]) -> Counter[str]:
    return Counter(
        {
            tag: sum(len(list(root.iter(tag))) for root in corpus.values())
            for tag in ("S", "W", "M")
        }
    )


def test_source_and_emitted_inventories_are_complete() -> None:
    source = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    emitted = load_expanded_ledger(LEDGER_PATH, DECISIONS_PATH)
    assert len(source["texts"]) == len(emitted["texts"]) == 6
    assert sum(len(text["sentences"]) for text in source["texts"]) == 171
    assert sum(len(text["sentences"]) for text in emitted["texts"]) == 190
    assert len(json.loads(DECISIONS_PATH.read_text())["expansions"]) == 18

    for source_text, emitted_text in zip(
        source["texts"], emitted["texts"], strict=True
    ):
        source_ids = {record["id"] for record in source_text["sentences"]}
        emitted_ids = {record["id"] for record in emitted_text["sentences"]}
        assert source_ids <= emitted_ids
        extras = emitted_ids - source_ids
        if emitted_text["path"] == "Yami/Kwaway.xml":
            assert "S48b" in extras
            assert "S48v2" not in emitted_ids
        for record in emitted_text["sentences"]:
            original = next(
                form["text"] for form in record["forms"] if form["kind"] == "original"
            )
            assert "/" not in original
            assert all(form["kind"] != "alternate" for form in record["forms"])


def test_final_xml_matches_reviewed_counts_and_tiers() -> None:
    corpus = roots()
    assert set(corpus) == {
        "Yami/Kalaku1.xml",
        "Yami/Kalaku2.xml",
        "Yami/Kalaku3.xml",
        "Yami/Kalaku4.xml",
        "Yami/Kangkang.xml",
        "Yami/Kwaway.xml",
    }
    assert node_counts(corpus) == Counter({"M": 1183, "W": 926, "S": 190})
    for root in corpus.values():
        assert root.get(XML_LANG) == "tao"
        assert root.get("dialect") == "Yami"
        assert root.get("copyright") == PUBLICATION_NOTICE
        assert not list(root.iter("PHON"))
        for element in (*root.findall("S"), *root.iter("W"), *root.iter("M")):
            original = [
                item.text or ""
                for item in element.findall("FORM[@kindOf='original']")
            ]
            standard = [
                item.text or ""
                for item in element.findall("FORM[@kindOf='standard']")
            ]
            assert standard == original


def test_published_ids_are_preserved() -> None:
    corpus = roots()
    ledger = json.loads(ID_LEDGER_PATH.read_text(encoding="utf-8"))
    assert ledger["private_source_commit"] == PRIVATE_SOURCE_COMMIT
    assert {item["public_text_id"] for item in ledger["text_id_mapping"]} == {
        root.get("id") for root in corpus.values()
    }

    kangkang = corpus["Yami/Kangkang.xml"].find("S[@id='S8']")
    assert kangkang is not None
    assert [word.get("id") for word in kangkang.findall("W")] == [
        "S8W1",
        "S8W2",
        "S8W3",
        "S8W4",
        "S8W6",
        "S8W7",
        "S8W8",
    ]
    assert kangkang.find("W[4]/M[2]").get("id") == "S8W5M1"
    kangkang_root = corpus["Yami/Kangkang.xml"]
    assert [
        morph.get("id")
        for morph in kangkang_root.find("S[@id='S33v2']/W").findall("M")
    ] == ["S33W1M2", "S33W1M3", "S33W1M4"]

    kwaway = corpus["Yami/Kwaway.xml"]
    assert kwaway.find("S[@id='S48b']") is not None
    assert kwaway.find("S[@id='S48v2']") is None
    assert kwaway.find("S[@id='S48b']/W[2]").get("id") == "S4bW2"

    kalaku4 = corpus["Yami/Kalaku4.xml"]
    assert [
        word.get("id") for word in kalaku4.find("S[@id='S2v2']").findall("W")[-2:]
    ] == ["S2W7", "S2W8"]
    assert [
        morph.get("id")
        for morph in kalaku4.find("S[@id='S2v2']/W[5]").findall("M")
    ] == ["S2W8M1", "S2W8M2"]
    assert {
        public_id
        for item in ledger["retired_structural_ids"]
        for public_id in item["public_ids"]
    } == {
        "S8W8",
        "S8W8M1",
        "S8W8M2",
        "S8W8M3",
        "S12W9M1",
        "S12W9M2",
        "S12W9M3",
    }


def test_complex_alternatives_are_independently_aligned() -> None:
    corpus = roots()
    kalaku1 = corpus["Yami/Kalaku1.xml"]
    assert [
        kalaku1.find(f"S[@id='{sid}']/FORM[@kindOf='original']").text
        for sid in ("S20", "S20v2", "S20v3")
    ] == ["pipangn-epen", "pipangungn-epen", "pipangengne-eben"]
    assert [
        kalaku1.find(f"S[@id='{sid}']/W[1]/M[2]/FORM[@kindOf='original']").text
        for sid in ("S17", "S17v2")
    ] == ["nem", "namen"]

    kalaku3 = corpus["Yami/Kalaku3.xml"]
    assert [
        len(kalaku3.find(f"S[@id='{sid}']").findall("W"))
        for sid in ("S8", "S8v2")
    ] == [7, 9]

    kwaway = corpus["Yami/Kwaway.xml"]
    assert [
        len(kwaway.find(f"S[@id='{sid}']").findall("W"))
        for sid in ("S48", "S48b")
    ] == [3, 5]
    assert not kwaway.find("S[@id='S51v2']/W").findall("M")


def test_builder_emits_only_source_owned_tiers() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = Path(directory) / "XML"
        subprocess.run(
            [
                os.environ.get("WAKELIN_PYTHON", "python3"),
                str(CODE_ROOT / "build_corpus.py"),
                "--source-ledger",
                str(LEDGER_PATH),
                "--alternative-decisions",
                str(DECISIONS_PATH),
                "--id-ledger",
                str(ID_LEDGER_PATH),
                "--xml-dir",
                str(target),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        built = roots(target)
        assert node_counts(built) == Counter({"M": 1183, "W": 926, "S": 190})
        for root in built.values():
            assert not list(root.iter("PHON"))
            assert not list(root.iter("FORM[@kindOf='standard']"))


def test_source_pdf_and_manifest_are_exact() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source = manifest["source"]
    assert SOURCE_PATH.stat().st_size == source["bytes"] == 1006822
    assert hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest() == source["sha256"]
    assert source["private_source_commit"] == PRIVATE_SOURCE_COMMIT
    assert source["rights"] == (
        "Publication rights confirmed by the FormosanBank maintainer on 2026-08-23; "
        "no open license is asserted."
    )


def test_historical_snapshot_is_retained_but_not_active() -> None:
    snapshot = CODE_ROOT / "pre_correction_snapshot/XML"
    assert len(list(snapshot.rglob("*.xml"))) == 6
    assert not (CODE_ROOT / "make_xml.sh").exists()
    assert not (CODE_ROOT / "drop_derived_tiers.py").exists()
    reproduce = (CODE_ROOT / "scripts/reproduce.sh").read_text(encoding="utf-8")
    assert "pre_correction_snapshot" not in reproduce
