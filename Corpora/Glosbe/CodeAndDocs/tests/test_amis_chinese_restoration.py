from collections import Counter
import xml.etree.ElementTree as ET

from scripts.glosbe_pipeline import (
    PROCESSED,
    XML_NS,
    dedupe_key,
    form_group_key,
    load_config,
    merge_reviewed_amis_chinese,
    read_jsonl,
    validate_xml_file,
)


def restored_rows():
    config = load_config("scripts/config.yaml")
    current = [
        row
        for row in read_jsonl(PROCESSED / "quality_filtered_examples.jsonl")
        if (row["l1"], row["l2"]) == ("ami", "zh")
    ]
    return current, merge_reviewed_amis_chinese(config, current)


def test_restoration_recovers_reviewed_unique_pairs():
    current, (merged, stats, audit) = restored_rows()

    assert stats == {
        "legacy_input_rows": 5860,
        "legacy_unique_pairs": 2321,
        "legacy_duplicate_rows": 3539,
        "current_rows": 25,
        "current_reviewed_matches": 25,
        "current_converted_new": 0,
        "normalization_duplicate_rows": 15,
        "output_rows": 2306,
        "output_forms": 2296,
    }
    assert [row["record_id"] for row in merged[:25]] == [row["record_id"] for row in current]
    assert Counter(row["origin"] for row in audit) == {
        "current_scrape_reviewed_match": 25,
        "joseph_reviewed_traditional": 2281,
        "joseph_reviewed_traditional;normalization_duplicate_omitted": 15,
    }


def test_restoration_keeps_distinct_translations_without_exact_duplicates():
    _, (merged, _, _) = restored_rows()
    pairs = [
        (dedupe_key(row["source_sentence_clean"]), dedupe_key(row["target_sentence_clean"]))
        for row in merged
    ]

    assert len(pairs) == len(set(pairs))
    assert len({source for source, _ in pairs}) == 2296
    assert len({form_group_key(row["source_sentence_clean"]) for row in merged}) == 2296
    assert all("*" not in row["source_sentence_clean"] for row in merged)
    assert all("*" not in row["target_sentence_clean"] for row in merged)


def test_local_validator_accepts_standard_form_and_alternate_translation(tmp_path):
    root = ET.Element(
        "TEXT",
        {
            "id": "test",
            "citation": "citation",
            "BibTeX_citation": "bibtex",
            "copyright": "copyright",
            f"{{{XML_NS}}}lang": "ami",
        },
    )
    sentence = ET.SubElement(root, "S", {"id": "test-S1"})
    ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = "Formosan text"
    ET.SubElement(sentence, "FORM", {"kindOf": "standard"}).text = "Formosan text"
    ET.SubElement(sentence, "TRANSL", {f"{{{XML_NS}}}lang": "zho"}).text = "主要翻譯"
    ET.SubElement(
        sentence,
        "TRANSL",
        {f"{{{XML_NS}}}lang": "zho", "ver": "alt"},
    ).text = "另一個翻譯"
    path = tmp_path / "test.xml"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    assert validate_xml_file(path, load_config("scripts/config.yaml")) == []
