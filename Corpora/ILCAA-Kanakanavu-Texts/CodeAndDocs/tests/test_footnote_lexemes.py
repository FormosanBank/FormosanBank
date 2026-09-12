"""Footnote readings and exclusions checked against the printed source."""

import json
import os
import sys
from pathlib import Path

import pytest
from lxml import etree

CODE = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("KANAKANAVU_WORKSPACE", CODE / ".build"))
sys.path.insert(0, str(CODE / "scripts"))
import footnote_lexemes


@pytest.fixture
def root():
    return etree.parse(str(WORKSPACE / "build/xml_drafts/Kanakanavu" / footnote_lexemes.FILENAME)).getroot()


def sentence(root, key):
    return root.find(f"S[@id='{footnote_lexemes.TEXT_ID}_{key}']")


def test_printed_variant_and_distinct_archaic_word(root):
    # Notes 21 and 52 distinguish a variant pair from an archaic snake term.
    assert [f.text for f in sentence(root, "FN021_01").findall("FORM")] == ["ləəʔə", "ləʔəvə"]
    assert [f.get("ver") for f in sentence(root, "FN021_01").findall("FORM")] == [None, "alt"]
    assert [f.text for f in sentence(root, "FN052_01").findall("FORM")] == ["vunai", "vənai"]
    assert sentence(root, "FN052_01-opt").findtext("FORM") == "vaəsə"


def test_meanings_and_languages_are_preserved(root):
    assert [(t.text, t.get("ver")) for t in sentence(root, "FN056_01").findall("TRANSL")] == [
        ("worm", None), ("snake", "alt")]
    assert [(t.text, t.get("ver")) for t in sentence(root, "FN053_01-opt").findall("TRANSL")] == [
        ("bite snake", None), ("bitten by a snake", "alt")]
    translation = sentence(root, "FN077_01").find("TRANSL")
    assert translation.text == "後埔" and translation.get(footnote_lexemes.XML_LANG) == "zho"


def test_unglossed_lexeme_does_not_get_an_invented_translation(root):
    source = sentence(root, "FN011_01")
    assert source.findtext("FORM") == "kurakurakurai"
    assert source.find("TRANSL") is None
    assert "synonym" in source.find("FORM").get("notes")
    assert root.find(".//W") is None and root.find(".//M") is None


def test_bound_forms_and_rejected_erratum_are_not_extra_utterances(root):
    ids = [s.get("id") for s in root]
    assert not any("_FN037_" in sid or "_FN072_" in sid or "_FN025_" in sid for sid in ids)


def test_audit_detects_lost_original_form(root, tmp_path):
    source = sentence(root, "FN003_01")
    source.remove(source.find("FORM"))
    etree.ElementTree(root).write(str(tmp_path / footnote_lexemes.FILENAME), encoding="utf-8")
    notes = [json.loads(line) for line in (WORKSPACE / "data/processed/footnotes.jsonl").read_text().splitlines()]
    findings = footnote_lexemes.audit_xml(tmp_path, CODE / "footnote_lexemes.jsonl", notes)
    assert any("FN003_01: source FORM differs" in message for message in findings)


def test_changed_footnote_requires_new_source_review():
    notes = [json.loads(line) for line in (WORKSPACE / "data/processed/footnotes.jsonl").read_text().splitlines()]
    notes[2]["footnote_raw"] = notes[2]["footnote_raw"].replace("professor", "teacher")
    with pytest.raises(ValueError, match="Changed source footnote"):
        footnote_lexemes.load_records(CODE / "footnote_lexemes.jsonl", notes)
