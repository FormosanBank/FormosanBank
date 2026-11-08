"""Printed columns on physical PDF pages 72 and 90, checked 2026-09-12."""
import json
import sys
from pathlib import Path

import pytest
from lxml import etree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import pipeline


CASES = json.loads((Path(__file__).parent / "fixtures/gloss_columns.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda case: f"PDF-page-{case['physical_page']}")
def test_gloss_columns(case):
    def entries(values):
        return [
            {"text": text, "raw_text": text, "bbox": [left, 0, right, 1], "refs": []}
            for text, left, right in values
        ]

    actual = pipeline.align_gloss_entries_by_source_position(
        entries(case["source"]), entries(case["gloss"])
    )
    assert [None if item is None else item["text"] for item in actual] == case["expected"]


def test_absent_source_gloss_is_not_unclear_text():
    morph = etree.Element("M")
    etree.SubElement(morph, "FORM", kindOf="original").text = "kai"
    assert pipeline.add_translation(morph, "", kind_of="original") is None
    assert morph.findtext("FORM") == "kai"
    assert morph.find("TRANSL") is None
    assert not morph.findall(".//UNCLEAR")
