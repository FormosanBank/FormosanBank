"""Source-derived boundaries for the canonical Glosbe build."""

import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("glosbe_source", HERE / "process_source.py")
SOURCE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SOURCE)


def row(source, target="definition", sid="test", **extra):
    return dict(source=source, target=target, sid=sid, record="new-source",
                kind="lexical", file="xsy/Glosbe_xsy_eng_lexical.xml",
                asterisks="", sha256="test", **extra)


@pytest.mark.parametrize("form", ["hongu' utux", "baq ske' 'tayal su ka?",
                                 "ka'inae:aewan ka 'ima 'ayaeh", "katikama’an ’ilibita’"])
def test_lexical_word_spaces_survive(form):
    result = SOURCE.render([row(form)], {"id": "test"})
    assert result.findtext("S/FORM") == form


def test_valid_definitions_are_not_filtered():
    result = SOURCE.render([row("psalu' tuqiy", "see (the road)", "road"),
                            row("usb", "usb", "usb")], {"id": "test"})
    assert [e.text for e in result.findall("S/TRANSL")] == ["see (the road)", "usb"]


def test_unreviewed_markers_are_not_removed():
    with pytest.raises(ValueError, match="Unreviewed asterisk"):
        SOURCE.render([row("*bad")], {"id": "test"})


def test_new_numerals_are_not_editorial_labels():
    example = row("8 cudad", "8 books")
    example.update(kind="tmem", file="ami/Glosbe_ami_eng_tmem.xml")
    assert SOURCE.content_fields(example) == ("8 cudad", "8 books")


def test_reviewed_journal_citations_are_notes():
    records = map(json.loads, (HERE / "source_records.jsonl").read_text().splitlines())
    example = next(r for r in records if r["sid"] == "GLOSBE_ami_eng_TMEM_U000041")
    sentence = SOURCE.render([example], {"id": "test"}).find("S")
    assert sentence.find('FORM').get('notes') == "w17.01, p."
    assert sentence.find('TRANSL').get('notes') == "w17.01, p."
    assert sentence.findtext('FORM').endswith("aka a misaidahidahi.")
    assert sentence.findtext('TRANSL').endswith("not take ourselves too seriously.")
    assert SOURCE.content_fields(row("w17.01, p.", "a source word"))[0] == "w17.01, p."


def test_saisiyat_case_is_not_merged():
    with pytest.raises(ValueError, match="Different source forms"):
        SOURCE.render([row("S"), row("s")], {"id": "test"})


def test_correction_keeps_id_and_alternate_translations():
    examples = [row("word", "one", "stable"), row("word", "two", "stable")]
    before = SOURCE.render(examples, {"id": "test"})
    for example in examples:
        example["source"] = "corrected word"
    after = SOURCE.render(examples, {"id": "test"})
    assert before.find("S").get("id") == after.find("S").get("id") == "stable"
    assert [e.get("ver") for e in after.findall("S/TRANSL")] == [None, "alt"]


def test_recorded_quote_repairs_preserve_glottal_letters():
    from lxml import etree

    root = etree.parse(HERE / "manual_edits.xml")
    for sid, phrase in [("GLOSBE_ami_eng_TMEM_U001294", "ilaloma' ningra.\""),
                        ("GLOSBE_ami_eng_TMEM_U001286", "mipaino' cangranan,\""),
                        ("GLOSBE_ami_zho_TMEM_U001536", "ilaloma' ningra.\""),
                        ("GLOSBE_ami_zho_TMEM_U001930", "mipaino' cangranan,\"")]:
        assert phrase in root.findtext(f'.//S[@id="{sid}"]/FORM')


def test_source_quotes_keep_the_adjacent_glottal_letter():
    from lxml import etree

    for file, sid, phrase in [
        ("ami/Glosbe_ami_eng_tmem.xml", "GLOSBE_ami_eng_TMEM_U000271", '"\'acaaw to toki"'),
        ("ami/Glosbe_ami_zho_tmem.xml", "GLOSBE_ami_zho_TMEM_U001790", '"\'odingaray a pasalat"'),
        ("ami/Glosbe_ami_zho_tmem.xml", "GLOSBE_ami_zho_TMEM_U000293", '3 "Itini'),
    ]:
        tree = etree.parse(HERE.parent / "XML" / file)
        assert phrase in tree.findtext(f'S[@id="{sid}"]/FORM[@kindOf="original"]')


def test_final_ids_and_approved_tiers():
    from lxml import etree

    published = {s.get("id") for f in (HERE / "pre_correction_snapshot").rglob("*.xml")
                 for s in etree.parse(f).findall("S")}
    final = {s.get("id"): s for f in (HERE.parent / "XML").rglob("*.xml")
             for s in etree.parse(f).findall("S")}
    assert published - final.keys() == {"GLOSBE_ami_zho_TMEM_U000046"}
    assert final.keys() - published == {"GLOSBE_tay_eng_LEXICAL_T5674367316521196016",
                                        "GLOSBE_xsy_eng_LEXICAL_T5403228964499116686"}
    for sentence in final.values():
        assert {e.get("kindOf") for e in sentence.findall("PHON")} == {"original", "standard"}
    book = final["GLOSBE_ami_eng_LEXICAL_U000001"]
    assert book.findtext('FORM[@kindOf="original"]') == "Cudad"
    assert book.findtext('FORM[@kindOf="standard"]') == "Codad"


def test_source_labels_and_date_are_retained_in_the_snapshot():
    records = {r["record"]: r for r in map(json.loads, (HERE / "source_records.jsonl").read_text().splitlines())}
    title = records["GLOSBE_STATIC_67d813451f0b5c7ed8a4"]
    assert title["source"].startswith("3 Palahad")
    assert title["target"] == "3 Cultivate Self-Control"
    date = records["GLOSBE_REVIEWED_ZHO_58019b201df8cb0f"]
    assert "2002/8/15" in SOURCE.content_fields(date)[0]


@pytest.mark.parametrize("first,second,spellings,translations", [
    (29, 30, ["btúnux", "btunux"], ["stone", "stone"]),
    (93, 104, ["kāyal", "kayal"], ["sky", "sky"]),
    (415, 425, ["sílung", "silung"], ["sea", "ocean"]),
])
def test_standard_collisions_preserve_distinct_source_entries(first, second, spellings, translations):
    from lxml import etree

    tree = etree.parse(HERE.parent / "XML/tay/Glosbe_tay_eng_lexical.xml")
    entries = [tree.find(f'S[@id="GLOSBE_tay_eng_LEXICAL_U{n:06}"]')
               for n in (first, second)]
    assert [s.findtext('FORM[@kindOf="original"]') for s in entries] == spellings
    assert [s.findtext('TRANSL') for s in entries] == translations
    assert len({s.findtext('FORM[@kindOf="standard"]') for s in entries}) == 1


def test_parallel_translation_witnesses_and_language_homographs_survive():
    from lxml import etree

    pairs = [
        ("ami/Glosbe_ami_eng_tmem.xml", "GLOSBE_ami_eng_TMEM_U000012", "eng"),
        ("ami/Glosbe_ami_zho_tmem.xml", "GLOSBE_ami_zho_TMEM_U000143", "zho"),
    ]
    forms = []
    for file, sid, language in pairs:
        s = etree.parse(HERE.parent / "XML" / file).find(f'S[@id="{sid}"]')
        assert s.find('TRANSL').get(SOURCE.XML_LANG) == language
        forms.append(s.findtext('FORM[@kindOf="original"]'))
    assert forms[0] == forms[1]
    for language, number, meaning in [("ami", 23, "father"), ("tay", 149, "uncle")]:
        tree = etree.parse(HERE.parent / f"XML/{language}/Glosbe_{language}_eng_lexical.xml")
        s = tree.find(f'S[@id="GLOSBE_{language}_eng_LEXICAL_U{number:06}"]')
        assert s.findtext('FORM[@kindOf="original"]') == "mama"
        assert s.findtext('TRANSL') == meaning
