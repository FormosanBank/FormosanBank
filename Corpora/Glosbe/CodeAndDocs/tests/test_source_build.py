"""Source-derived boundaries for the canonical Glosbe build."""

import importlib.util
import json
import os
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


def final_sentences():
    from lxml import etree

    return {s.get("id"): s for f in (HERE.parent / "XML").rglob("*.xml")
            for s in etree.parse(f).findall("S")}


def withdrawn():
    import csv

    with (HERE / "withdrawn_ids.csv").open(encoding="utf-8", newline="") as stream:
        return {row["withdrawn_id"]: row for row in csv.DictReader(stream)}


def resolve(sid):
    """A published id, or the id it was withdrawn to (withdrawn_ids.csv)."""
    return withdrawn().get(sid, {}).get("kept_id", sid)


def test_source_quotes_keep_the_adjacent_glottal_letter():
    final = final_sentences()
    for sid, phrase in [
        ("GLOSBE_ami_eng_TMEM_U000271", '"\'acaaw to toki"'),
        ("GLOSBE_ami_zho_TMEM_U001790", '"\'odingaray a pasalat"'),
        ("GLOSBE_ami_zho_TMEM_U000293", '"Itini'),
    ]:
        assert phrase in final[resolve(sid)].findtext('FORM[@kindOf="original"]')


def test_final_ids_and_approved_tiers():
    from lxml import etree

    published = {s.get("id") for f in (HERE / "pre_correction_snapshot").rglob("*.xml")
                 for s in etree.parse(f).findall("S")}
    final = final_sentences()
    ledger = withdrawn()
    assert published - final.keys() == {k for k, v in ledger.items() if v["action"] != "text merged"}
    assert all(v["kept_id"] in final for k, v in ledger.items() if v["action"] != "text merged")
    assert "GLOSBE_ami_zho_TMEM_U000046" in final  # keep_published_ids.csv
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
    (415, 425, ["sílung", "silung"], ["sea", "ocean"]),
])
def test_standard_collisions_preserve_distinct_source_entries(first, second, spellings, translations):
    from lxml import etree

    tree = etree.parse(HERE.parent / "XML/Atayal/Glosbe_tay_eng_lexical.xml")
    entries = [tree.find(f'S[@id="GLOSBE_tay_eng_LEXICAL_U{n:06}"]')
               for n in (first, second)]
    assert [s.findtext('FORM[@kindOf="original"]') for s in entries] == spellings
    assert [s.findtext('TRANSL') for s in entries] == translations
    assert len({s.findtext('FORM[@kindOf="standard"]') for s in entries}) == 1


def test_ruled_duplicates_are_withdrawn():
    final, ledger = final_sentences(), withdrawn()
    for old, keep in [("GLOSBE_tay_eng_LEXICAL_U000030", "GLOSBE_tay_eng_LEXICAL_U000029"),
                      ("GLOSBE_tay_eng_LEXICAL_U000104", "GLOSBE_tay_eng_LEXICAL_U000093"),
                      ("GLOSBE_trv_eng_LEXICAL_U000111", "GLOSBE_xsy_eng_LEXICAL_U000475")]:
        assert old not in final and keep in final
        assert ledger[old]["kept_id"] == keep and ledger[old]["action"] == "deleted"


def test_one_amis_file_joins_identical_sentences():
    from lxml import etree

    assert not (HERE.parent / "XML/Amis/Glosbe_ami_zho_tmem.xml").exists()
    root = etree.parse(HERE.parent / "XML/Amis/Glosbe_ami_eng_tmem.xml").getroot()
    assert root.get("id") == "GLOSBE_ami_eng_TMEM"
    assert withdrawn()["GLOSBE_ami_zho_TMEM"]["kept_id"] == "GLOSBE_ami_eng_TMEM"
    s = root.find('S[@id="GLOSBE_ami_eng_TMEM_U000012"]')
    assert resolve("GLOSBE_ami_zho_TMEM_U000143") == "GLOSBE_ami_eng_TMEM_U000012"
    assert [t.get(SOURCE.XML_LANG) for t in s.findall("TRANSL")] == ["eng", "zho"]
    kept = root.find('S[@id="GLOSBE_ami_zho_TMEM_U000046"]')
    assert [t.get(SOURCE.XML_LANG) for t in kept.findall("TRANSL")] == ["zho"]
    joined = {k for k, v in withdrawn().items() if v["action"] == "merged"}
    assert len(joined) == 1821


def test_highlight_spaces_and_editorial_notes():
    final = final_sentences()
    form = lambda sid: final[resolve(sid)].find('FORM[@kindOf="original"]')
    assert '"o wacay' in form("GLOSBE_ami_zho_TMEM_U000012").text
    assert "sa'opo i, oya" in form("GLOSBE_ami_zho_TMEM_U000233").text
    assert "'Olic 118 ," in form("GLOSBE_ami_zho_TMEM_U000393").text  # in both captures
    note = form("GLOSBE_ami_eng_TMEM_U000811")
    assert note.get("notes") == "(Nengnengen ko saka 12 fatac)"
    assert note.text.endswith("so'linay kimad")
    assert "private research" not in final["GLOSBE_ami_eng_LEXICAL_U000001"].getparent().get("BibTeX_citation")


def test_language_homographs_survive():
    from lxml import etree

    for language, folder, number, meaning in [("ami", "Amis", 23, "father"), ("tay", "Atayal", 149, "uncle")]:
        tree = etree.parse(HERE.parent / f"XML/{folder}/Glosbe_{language}_eng_lexical.xml")
        s = tree.find(f'S[@id="GLOSBE_{language}_eng_LEXICAL_U{number:06}"]')
        assert s.findtext('FORM[@kindOf="original"]') == "mama"
        assert s.findtext('TRANSL') == meaning


@pytest.mark.parametrize("number,reading", [
    (900, "How would Jehovah's counsel benefit Job long after his trials?"),
    (2543, "What goals might you set for yourself?"),
    (2597, "How can you plan to be a full-time Christian minister?"),
    (2829, 'Give Success to All Your Plans"'),
    (3376, "What will we consider?"),
    (4033, "How can baptized brothers be courageous?"),
])
def test_reviewed_alias_readings_survive_current_dedup(number, reading):
    from lxml import etree

    tree = etree.parse(HERE.parent / "XML/Amis/Glosbe_ami_eng_tmem.xml")
    sentence = tree.find(f'S[@id="GLOSBE_ami_eng_TMEM_U{number:06}"]')
    assert reading in [t.text for t in sentence.findall('TRANSL[@ver="alt"]')]


def test_alias_replay_does_not_merge_unreviewed_homographs(tmp_path, monkeypatch):
    from lxml import etree

    docs = tmp_path / "CodeAndDocs"
    docs.mkdir()
    (tmp_path / "XML").mkdir()
    (docs / "source_aliases.csv").write_text("omitted_id,retained_id,reason\nb,a,reviewed\n")
    path = tmp_path / "XML/test.xml"
    tree = SOURCE.render([row("word", "one", "a"), row("word", "two", "b"),
                          row("word", "three", "c")], {"id": "test"})
    etree.ElementTree(tree).write(path)
    monkeypatch.setattr(SOURCE, "HERE", docs)
    bank = Path(os.environ.get("FORMOSANBANK_ROOT", HERE.parents[2]))
    SOURCE.apply_reviewed_aliases(bank)
    result = etree.parse(path)
    assert [s.get("id") for s in result.findall("S")] == ["a", "c"]
    assert result.findtext('S[@id="a"]/TRANSL[@ver="alt"]') == "two"
    assert result.findtext('S[@id="c"]/TRANSL') == "three"

    tree.find('S[@id="b"]/FORM').text = "different word"
    etree.ElementTree(tree).write(path)
    with pytest.raises(ValueError, match="Reviewed alias no longer matches"):
        SOURCE.apply_reviewed_aliases(bank)
