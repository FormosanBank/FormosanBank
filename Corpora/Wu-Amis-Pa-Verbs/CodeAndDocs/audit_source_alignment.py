#!/usr/bin/env python3
"""Verify final XML against the reviewed Wu source inventory."""

from __future__ import annotations

import copy
import csv
import importlib.util
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "XML/Amis/pa-verbs.xml"
SOURCE_PDF_SHA256 = "9ba94321d9c8e926cf8cca3b0b81814400d2bb7194ba48574d77ad54490308f5"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SPEC = importlib.util.spec_from_file_location(
    "build_xml", ROOT / "CodeAndDocs/build_xml.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Unable to load build_xml.py")
BUILD_XML = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD_XML)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def node_text(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text


def strip_machine_tiers(sentence: ET.Element) -> ET.Element:
    stripped = copy.deepcopy(sentence)
    for parent in stripped.iter():
        for child in list(parent):
            if child.tag == "PHON" or (
                child.tag == "FORM" and child.get("kindOf") == "standard"
            ):
                parent.remove(child)
    return stripped


def semantic_element(node: ET.Element) -> tuple:
    return (
        node.tag,
        tuple(sorted(node.attrib.items())),
        (node.text or "").strip(),
        tuple(semantic_element(child) for child in node),
    )


def tier_is_complete(node: ET.Element) -> bool:
    for kind_of in ("original", "standard"):
        forms = node.findall(f"FORM[@kindOf='{kind_of}']")
        phons = node.findall(f"PHON[@kindOf='{kind_of}']")
        if len(forms) != 1 or len(phons) != 1:
            return False
    return True


def main() -> None:
    errors: list[str] = []
    accepted = read_tsv(ROOT / "CodeAndDocs/source_examples.tsv")
    direct = read_tsv(ROOT / "CodeAndDocs/direct_source_checks.tsv")
    rejected = read_tsv(ROOT / "CodeAndDocs/rejected_source_examples.tsv")
    coverage = read_tsv(ROOT / "CodeAndDocs/source_coverage.tsv")
    manifest = read_tsv(ROOT / "CodeAndDocs/source_manifest.tsv")
    root = ET.parse(XML_PATH).getroot()

    expected_manifest = {
        "source_id": "wu-2006-pa-verbs",
        "filename": "pa-verbs.pdf",
        "sha256": SOURCE_PDF_SHA256,
        "pages": "13",
        "tracking": "ignored-private-source",
    }
    if manifest != [expected_manifest]:
        errors.append("source manifest does not match the development evidence")

    expected_root = {
        XML_LANG: "ami",
        "dialect": "Coastal",
        "id": "wu-2006-amis-pa-verbs",
        "copyright": BUILD_XML.COPYRIGHT,
    }
    for key, expected in expected_root.items():
        if root.get(key) != expected:
            errors.append(
                f"TEXT {key!r}: expected {expected!r}, found {root.get(key)!r}"
            )
    if not root.get("citation") or not root.get("BibTeX_citation"):
        errors.append("TEXT citation metadata is incomplete")

    expected_sentences = BUILD_XML.build_tree(accepted).getroot().findall("S")
    actual_sentences = root.findall("S")
    if len(accepted) != 29 or len(actual_sentences) != 29:
        errors.append(
            f"expected 29 source-adjudicated sentence variants, found "
            f"{len(accepted)}/{len(actual_sentences)}"
        )
    if len(direct) != 30 or any(row["result"] != "match" for row in direct):
        errors.append("expected 30 passing direct visual checks")
    if len(coverage) != 13 or [row["pdf_page"] for row in coverage] != [
        str(page) for page in range(1, 14)
    ]:
        errors.append("source coverage ledger must account for PDF pages 1 through 13")
    if any(row["review_status"] != "reviewed" for row in coverage):
        errors.append("one or more source pages lack reviewed status")

    expected_rejected = {
        "duplicate_source_occurrence": 2,
        "source_marked_ungrammatical": 7,
        "starred_alternative": 4,
        "starred_reading": 1,
        "source_marked_questionable": 2,
    }
    rejected_reasons = Counter(row["reason"] for row in rejected)
    if rejected_reasons != expected_rejected:
        errors.append(f"unexpected rejection inventory: {dict(rejected_reasons)}")

    expected_ids = [item.get("id", "") for item in expected_sentences]
    actual_ids = [item.get("id", "") for item in actual_sentences]
    if actual_ids != expected_ids:
        errors.append("final sentence IDs/order do not match the reviewed source table")
    for expected_sentence, actual_sentence in zip(
        expected_sentences, actual_sentences, strict=False
    ):
        if semantic_element(expected_sentence) != semantic_element(
            strip_machine_tiers(actual_sentence)
        ):
            errors.append(
                f"{expected_sentence.get('id', '')} differs from the reviewed source table"
            )

    all_ids = [node.get("id", "") for node in root.iter() if node.get("id")]
    if len(all_ids) != len(set(all_ids)):
        errors.append("XML IDs are not unique")
    if any(not identifier.isascii() or "'" in identifier for identifier in all_ids):
        errors.append("XML IDs are not ASCII-safe")
    if any(not sentence.findall("W") for sentence in actual_sentences):
        errors.append("one or more sentences lack word glossing")
    if any(not word.findall("M") for word in root.findall(".//W")):
        errors.append("one or more words lack M under POL-023")
    if any(
        (translation := word.find("TRANSL")) is None
        or translation.get("kindOf") is not None
        for word in root.findall(".//W")
    ):
        errors.append("one or more words lack an untiered source gloss")
    if any(
        (translation := morph.find("TRANSL")) is None
        or translation.get("kindOf") is not None
        for morph in root.findall(".//M")
    ):
        errors.append("one or more morphemes lack an untiered source gloss")
    if root.findall(".//TRANSL[@kindOf='original']"):
        errors.append("one or more TRANSL tiers use forbidden kindOf=original")
    if any(
        not tier_is_complete(node)
        for node in root.findall(".//S") + root.findall(".//W") + root.findall(".//M")
    ):
        errors.append(
            "one or more S/W/M nodes lack complete original and standard FORM/PHON tiers"
        )
    if any(
        marker in node_text(form)
        for form in root.findall(".//FORM")
        for marker in ("*", "?")
    ):
        errors.append("acceptability punctuation was lexicalized in FORM")
    if any(
        marker in node_text(form)
        for form in root.findall(".//FORM")
        for marker in ("ø", "Ø")
    ):
        errors.append("a noncanonical null symbol remains in FORM")

    null_words = [
        word
        for word in root.findall(".//W")
        if "∅" in node_text(word.find("FORM[@kindOf='original']"))
    ]
    null_morphs = [
        morph
        for morph in root.findall(".//M")
        if node_text(morph.find("FORM[@kindOf='original']")) == "∅"
    ]
    null_sentences = [
        sentence
        for sentence in root.findall("S")
        if "∅" in node_text(sentence.find("FORM[@kindOf='original']"))
    ]
    if len(null_sentences) != 7 or len(null_words) != 7 or len(null_morphs) != 7:
        errors.append(
            "expected seven source nulls at S/W/M, found "
            f"{len(null_sentences)}/{len(null_words)}/{len(null_morphs)}"
        )
    if any(
        "∅" in node_text(sentence.find("FORM[@kindOf='standard']"))
        for sentence in null_sentences
    ):
        errors.append("a null unit remains in S standard FORM")
    if any(
        node_text(word.find("PHON[@kindOf='original']")) != "ʦi"
        or node_text(word.find("PHON[@kindOf='standard']")) != "ʦi"
        for word in null_words
    ):
        errors.append("a null-plus-ci word has non-silent null phonology")
    if any(
        node_text(morph.find("PHON[@kindOf='original']")) != "∅"
        or node_text(morph.find("PHON[@kindOf='standard']")) != "∅"
        for morph in null_morphs
    ):
        errors.append("a null-only morpheme does not retain PHON ∅")
    if any("~" in node_text(phon) for phon in root.findall(".//PHON")):
        errors.append("one or more PHON tiers contain a legacy tilde alternative")

    pa_fli = root.find("S[@id='s32a']/W[@id='s32aw0']")
    if pa_fli is None or len(pa_fli.findall("M")) != 1:
        errors.append("source-underanalyzed Pa-fli does not have exactly one M")
    elif (
        node_text(pa_fli.find("M/FORM[@kindOf='original']")) != "Pa-fli"
        or node_text(pa_fli.find("M/TRANSL")) != "give"
    ):
        errors.append("Pa-fli whole-word M does not preserve the source analysis")

    cau_word = root.find("S[@id='s32b']/W[@id='s32bw0']")
    cau_morph = root.find("S[@id='s32b']/W[@id='s32bw0']/M[@id='s32bw0m1']")
    if (
        cau_word is None
        or node_text(cau_word.find("TRANSL")) != "UV-CaU-give"
        or node_text(cau_word.find("TRANSL[@kindOf='standard']")) != "UV-CAU-give"
        or cau_morph is None
        or node_text(cau_morph.find("TRANSL")) != "CaU"
        or node_text(cau_morph.find("TRANSL[@kindOf='standard']")) != "CAU"
    ):
        errors.append("source CaU and additive standard CAU glosses are incomplete")

    print(f"errors={len(errors)} warnings=0 notices=0")
    if errors:
        raise SystemExit("Source alignment failed: " + "; ".join(errors))


if __name__ == "__main__":
    main()
