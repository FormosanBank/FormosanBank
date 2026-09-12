"""Printed table columns, lexical examples and protected grammatical context."""

import csv
import json
import os
import shutil
import sys
from pathlib import Path

import pytest
from lxml import etree

CODE = Path(__file__).resolve().parents[1]
WORKSPACE = Path(os.environ.get("KANAKANAVU_WORKSPACE", CODE / ".build"))
sys.path.insert(0, str(CODE / "scripts"))
import introduction_lexemes as intro


def sentence(profile, key, language="Kanakanavu"):
    file = WORKSPACE / f"build/xml_drafts/{language}/ILCAA_KanakanavuTexts_intro_{profile}.xml"
    root = etree.parse(str(file)).getroot()
    return root, root.find(f"S[@id='ILCAA_KANAKANAVU_TEXTS_INTRO_{profile.upper()}_{key}']")


def test_historical_columns_are_separate_and_glyphs_follow_print():
    for profile, form in (("Tsuchida1969", "tarikúuka"), ("Szakos1999", "tarikuka"), ("BasicVocabulary2007", "tarakuka")):
        _, s = sentence(profile, f"T1_{profile}_R01")
        assert s.findtext("FORM") == form
    assert sentence("Tsuchida1969", "T1_Tsuchida1969_R05")[1].findtext("FORM") == "ta’ɨ́lɨmɨ"
    assert sentence("Tsuchida1969", "T1_Tsuchida1969_R09")[1].findtext("FORM") == "ranɨ́ngɨ"


def test_explicit_echo_vowel_and_comma_variants():
    root, s = sentence("Tsuchida1969", "T1_Tsuchida1969_R03")
    assert [(f.text, f.get("ver")) for f in s.findall("FORM")] == [("kumakaɨn", None), ("kumakaɨnɨ", "alt")]
    assert len(root.findall("S")) == 10  # Prose reuses this exact example.
    _, s = sentence("Szakos1999", "T1_Szakos1999_R08")
    assert [f.text for f in s.findall("FORM")] == ["meecun", "me’ecun"]


def test_free_pronouns_preserve_stress_and_row_context():
    root, _ = sentence("Tsuchida1976", "T2_01")
    assert len(root.findall("S")) == 16
    assert not root.findall(".//TRANSL")  # Row headings are not free translations.
    forms = [s.findtext("FORM") for s in root.findall("S")]
    assert "íiku" in forms and "ʔisua" in forms
    assert not any(f.startswith(("=", "-")) or f == "ø" for f in forms)
    iikia = next(s for s in root.findall("S") if s.findtext("FORM") == "íikia")
    assert "1EXCL" in iikia.find("FORM").get("notes")


def test_saaroa_comparison_keeps_its_language():
    root, s = sentence("SaaroaComparison", "P020_SAAROA", "Saaroa")
    assert root.get(intro.XML_LANG) == "xsr" and root.get("dialect") == "Saaroa"
    assert s.findtext("FORM") == "iɫakia"


def test_title_and_footnote_supply_the_same_lexeme():
    _, s = sentence("Asai2026", "TITLE_FN029")
    assert s.findtext("FORM") == "ʔənnaŋ"
    assert [(t.get(intro.XML_LANG), t.text) for t in s.findall("TRANSL")] == [
        ("eng", "Fruit of the bird lime plant"), ("zho", "破布子")]


def test_printed_analysis_keeps_infix_gap_and_source_gloss():
    _, s = sentence("Asai2026", "P024_03")
    assert s.find("TRANSL") is None
    assert s.findtext("W/TRANSL") == "RED<AV>-tie"
    assert [m.findtext("FORM") for m in s.findall("W/M")] == ["k-a", "-um-", "kili"]
    with (WORKSPACE / "data/processed/xml_token_index.csv").open() as f:
        indexed = {r["element_id"] for r in csv.DictReader(f)}
    assert {x.get("id") for x in s.xpath(".//W | .//M")} <= indexed


def test_templates_and_unresolved_phonetic_strings_are_not_sentences():
    records = intro.load_records(CODE / "introduction_lexemes.json", WORKSPACE)
    assert len(records) == 100
    assert not any("STEM" in r["form"] or r["form"] in ("M-type", "kɔ:", "kɅɨnɨ") for r in records)
    data = json.loads((CODE / "introduction_lexemes.json").read_text())
    assert len(data["pending"]) == 3 and len(data["profile_review_required"]) == 5


def test_changed_source_page_requires_review(tmp_path):
    target = tmp_path / "data/raw/text/pages"
    shutil.copytree(WORKSPACE / "data/raw/text/pages", target)
    with (target / "page_0016.txt").open("a") as f:
        f.write("changed")
    with pytest.raises(ValueError, match="Changed introduction source page: 16"):
        intro.load_records(CODE / "introduction_lexemes.json", tmp_path)
