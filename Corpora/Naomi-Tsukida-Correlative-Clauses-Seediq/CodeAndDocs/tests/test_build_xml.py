from __future__ import annotations

import csv
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
sys.path.insert(0, str(CODE))

import build_xml  # noqa: E402
import restore_source_notation  # noqa: E402


REVIEWER_FLAGGED_IDS = {
    "tsukida2014_seediq_S005",
    "tsukida2014_seediq_S006",
    "tsukida2014_seediq_S008",
    "tsukida2014_seediq_S009",
    "tsukida2014_seediq_S011",
    "tsukida2014_seediq_S018",
    "tsukida2014_seediq_S019",
    "tsukida2014_seediq_S020",
    "tsukida2014_seediq_S021",
    "tsukida2014_seediq_S024",
    "tsukida2014_seediq_S026",
    "tsukida2014_seediq_S029",
}


def corpus_model():
    rows = build_xml.read_tsv()
    build_xml.validate_rows(rows)
    records = build_xml.included_records(rows)
    tree = build_xml.build_tree(records)
    return rows, records, tree


def test_development_output_path_is_canonical_xml():
    assert build_xml.XML_PATH == (
        ROOT / "XML/Seediq/tsukida_2014_correlative_clauses_in_seediq.xml"
    )
    assert not (ROOT / "Final_XML").exists()


def test_source_inventory_is_complete():
    rows, records, _ = corpus_model()
    assert len(rows) == len({row["id"] for row in rows}) == 39
    assert Counter(row["included"] for row in rows) == {"yes": 26, "no": 13}
    assert len(records) == 28
    assert set(range(74, 84)) == {int(row["pdf_page"].split("-")[0]) for row in rows}
    assert {page for page, _, _, _ in build_xml.PAGE_ROWS} == set(range(74, 85))


def test_comparison_examples_11_and_20_are_separate_source_units():
    rows, _, _ = corpus_model()
    by_id = {row["id"]: row for row in rows}
    assert by_id["excluded_003a"]["example_label"] == "11a"
    assert by_id["excluded_003b"]["example_label"] == "11b"
    assert by_id["excluded_003a"]["original"].endswith("nyuntulu-rlu].")
    assert "pantu-rnu]" in by_id["excluded_003b"]["original"]
    assert by_id["excluded_005a"]["example_label"] == "20a"
    assert by_id["excluded_005b"]["example_label"] == "20b"


def test_every_included_sentence_has_source_aligned_words():
    _, records, tree = corpus_model()
    no_words = {
        sentence.get("id")
        for sentence in tree.getroot().findall("S")
        if not sentence.findall("W")
    }
    assert no_words == set()
    assert len(tree.getroot().findall(".//W")) == 201
    assert len(tree.getroot().findall(".//M")) == 254
    unparsed = {"tsukida2014_seediq_S002", "tsukida2014_seediq_S005", "tsukida2014_seediq_S005v2"}
    assert {s.get("id") for s in tree.getroot().findall("S") if not s.findall("W/M")} == unparsed
    assert all(w.findall("M") for s in tree.getroot().findall("S")
               if s.get("id") not in unparsed for w in s.findall("W"))
    for record in records:
        words, note = build_xml.word_alignment(record)
        assert len(words) == len(record["gloss"].split())
        assert "source word/gloss alignment retained" in note
    by_id = {
        sentence.get("id"): sentence for sentence in tree.getroot().findall("S")
    }
    assert all(by_id[sentence_id].findall("W") for sentence_id in REVIEWER_FLAGGED_IDS)


def test_reviewed_infixes_have_reconstructable_morphemes():
    _, _, tree = corpus_model()
    root = tree.getroot()
    word = root.find("S[@id='tsukida2014_seediq_S006']/W[@id='tsukida2014_seediq_S006W3']")
    assert word is not None
    assert [form.text for form in word.findall("M/FORM[@kindOf='original']")] == [
        "b-arig",
        "-en-",
        "=na",
    ]
    assert [translation.text for translation in word.findall("TRANSL")] == [
        "CV.PRF-buy=3SG.GEN",
        "<CV.PRF>buy=3SG.GEN",
    ]
    assert [item.get("kindOf") for item in word.findall("TRANSL")] == [
        "original",
        "standard",
    ]
    assert word.findall("TRANSL")[1].get("ver") == "alt"
    double_infix = root.find(
        "S[@id='tsukida2014_seediq_S020']/W[@id='tsukida2014_seediq_S020W1']"
    )
    assert double_infix is not None
    assert [form.text for form in double_infix.findall("M/FORM[@kindOf='original']")] == [
        "S-teruŋ",
        "-em-",
        "-en-",
        "=ku",
    ]


def test_source_gloss_is_tiered_only_when_paired_with_standard():
    _, _, tree = corpus_model()
    root = tree.getroot()
    paired_words = [
        word
        for word in root.findall(".//W")
        if word.find("TRANSL[@kindOf='standard']") is not None
    ]
    assert len(paired_words) == 11
    assert all(
        len(word.findall("TRANSL[@kindOf='original']")) == 1
        for word in paired_words
    )
    assert all(
        translation.get("kindOf") is None
        for word in root.findall(".//W")
        if word.find("TRANSL[@kindOf='standard']") is None
        for translation in word.findall("TRANSL")
    )
    assert root.findall(".//M/TRANSL[@kindOf='original']") == []


def test_analytical_wrappers_are_removed_only_at_word_edges():
    assert build_xml.lexical_word("(ka") == "ka"
    assert build_xml.lexical_word("hiya).") == "hiya"
    assert build_xml.lexical_word("[p-en-huqil") == "p-en-huqil"
    assert build_xml.lexical_word("se'diq].") == "se'diq"


def test_original_forms_and_translations_are_preserved():
    _, _, tree = corpus_model()
    root = tree.getroot()
    by_id = {sentence.get("id"): sentence for sentence in root.findall("S")}
    assert by_id["tsukida2014_seediq_S018"].find("FORM").text == (
        "Wada qeduriq ka se'diq [p-en-huqil rebiq-an]."
    )
    assert [
        item.text for item in by_id["tsukida2014_seediq_S016"].findall("TRANSL")
    ] == [
        "When the child is likely to stumble, he supports the child.",
        "He supported the child who was likely to stumble.",
    ]
    assert [
        item.text for item in by_id["tsukida2014_seediq_S020"].findall("TRANSL")
    ] == ["I met [the man who gave Rubiq a book]."]
    assert [
        item.text for item in by_id["tsukida2014_seediq_S009"].findall("TRANSL")
    ] == ["Yudaw who is speaking to a/the guest is from America."]


def test_optional_constituents_are_expanded_with_aligned_glosses():
    _, _, tree = corpus_model()
    by_id = {
        sentence.get("id"): sentence for sentence in tree.getroot().findall("S")
    }
    assert by_id["tsukida2014_seediq_S005"].find("FORM").text == (
        "Laqi gaga 'u, malu."
    )
    assert by_id["tsukida2014_seediq_S005v2"].find("FORM").text == (
        "Laqi gaga 'u, malu ka hiya."
    )
    assert len(by_id["tsukida2014_seediq_S005"].findall("W")) == 4
    assert len(by_id["tsukida2014_seediq_S005v2"].findall("W")) == 6
    assert len(by_id["tsukida2014_seediq_S008"].findall("W")) == 9
    assert len(by_id["tsukida2014_seediq_S008v2"].findall("W")) == 12
    assert not any(
        marker in (sentence.find("FORM").text or "")
        for sentence in by_id.values()
        for marker in ("(", ")")
    )


def test_starred_and_duplicate_source_units_stay_excluded():
    rows, records, _ = corpus_model()
    output_ids = {record["id"] for record in records}
    excluded = {row["id"]: row for row in rows if row["included"] == "no"}
    starred = {
        row_id for row_id, row in excluded.items() if row["original"].startswith("*")
    }
    assert starred == {
        "tsukida2014_seediq_S010",
        "tsukida2014_seediq_S012",
        "tsukida2014_seediq_S014",
        "tsukida2014_seediq_S030",
        "tsukida2014_seediq_S031",
    }
    assert output_ids.isdisjoint(excluded)
    assert excluded["excluded_006"]["original"].startswith("Kumuᵢ")
    source_interpretation = next(
        row for row in rows if row["id"] == "tsukida2014_seediq_S009"
    )
    assert source_interpretation["translation_alt"].startswith("*")
    assert source_interpretation["translation_alt_in_xml"] == "no"


def test_source_notation_restoration_is_fail_closed_and_idempotent(tmp_path):
    _, _, tree = corpus_model()
    path = tmp_path / "corpus.xml"
    root = tree.getroot()
    for sentence_id, (
        cleaned,
        _,
    ) in restore_source_notation.ORIGINAL_RESTORATIONS.items():
        root.find(f"S[@id='{sentence_id}']/FORM[@kindOf='original']").text = cleaned
    for sentence_id, (
        cleaned,
        _,
    ) in restore_source_notation.TRANSLATION_RESTORATIONS.items():
        root.find(f"S[@id='{sentence_id}']/TRANSL").text = cleaned
    tree.write(path, encoding="utf-8", xml_declaration=True)
    assert restore_source_notation.process(path) == (7, 7)
    assert restore_source_notation.process(path) == (7, 0)
    restored = ET.parse(path).getroot()
    assert restored.find("S[@id='tsukida2014_seediq_S029']/FORM").text.startswith("[")


def test_build_outputs_are_deterministic(tmp_path):
    rows, records, tree = corpus_model()
    other = build_xml.build_tree(build_xml.included_records(rows))
    assert ET.tostring(tree.getroot()) == ET.tostring(other.getroot())
    output = tmp_path / "corpus.xml"
    build_xml.write_xml(tree, output)
    assert output.is_file()
    assert not hasattr(build_xml, "DRAFT_XML")


def test_direct_checks_cover_difficult_cases():
    with (CODE / "intermediate" / "direct_source_checks.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 33
    included_ids = {
        row["id"]
        for row in build_xml.read_tsv()
        if row["included"] == "yes"
    }
    assert included_ids <= {row["record_id"] for row in rows}
    assert {row["record_id"] for row in rows} >= {
        "excluded_003a",
        "excluded_003b",
        "tsukida2014_seediq_S025",
        "excluded_006",
        "tsukida2014_seediq_S031",
    }


def test_approved_source_infix_findings_have_exact_scope():
    from lxml import etree

    bank = Path(os.environ["FORMOSANBANK_ROOT"])
    sys.path.insert(0, str(bank))
    from QC.validation.rules.gloss_scrape import g001_marker_skeleton_parity

    findings = g001_marker_skeleton_parity(etree.parse(str(build_xml.XML_PATH)), build_xml.XML_PATH)
    expected = [("006", 3), ("009", 2), ("011", 6), ("018", 5), ("019", 4),
                ("020", 1), ("021", 1), ("024", 2), ("026", 1), ("026", 7), ("029", 1)]
    assert [(f.rule_id, f.location, f.count) for f in findings] == [
        ("G001", f"S=tsukida2014_seediq_S{n} W=tsukida2014_seediq_S{n}W{w}", 1)
        for n, w in expected
    ]


def test_original_phon_uses_the_documented_tsukida_profile():
    root = ET.parse(build_xml.XML_PATH).getroot()
    words = root.find("S[@id='tsukida2014_seediq_S002']").findall("W")
    assert words[3].findtext("FORM[@kindOf='original']") == "gaga"
    assert words[3].findtext("PHON[@kindOf='original']") == "ɣaɣa"
    assert words[1].findtext("FORM[@kindOf='original']") == "huliŋ"
    assert words[1].findtext("PHON[@kindOf='original']") == "ħuɮiŋ"
    assert root.find("S[@id='tsukida2014_seediq_S018']/W[@id='tsukida2014_seediq_S018W2']/TRANSL").text == "AC.escape"


def test_text_correction_retains_all_source_ids():
    rows = build_xml.read_tsv()
    before = build_xml.build_tree(build_xml.included_records(rows)).getroot()
    row = next(r for r in rows if r["id"] == "tsukida2014_seediq_S002")
    row["original"] = "Deha huliŋ kumu gaga"
    after = build_xml.build_tree(build_xml.included_records(rows)).getroot()
    assert [e.get("id") for e in before.iter() if e.get("id")] == [
        e.get("id") for e in after.iter() if e.get("id")
    ]
