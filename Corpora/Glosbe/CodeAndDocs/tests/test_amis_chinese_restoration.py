from collections import Counter
import xml.etree.ElementTree as ET

from scripts.glosbe_pipeline import (
    PROCESSED,
    XML_NS,
    dedupe_key,
    form_group_key,
    load_config,
    merge_reviewed_amis_chinese,
    read_csv,
    validate_xml_file,
)


def restored_rows():
    config = load_config("scripts/config.yaml")
    current = [
        {
            "record_id": row["record_id"],
            "source_sentence_clean": row["source_sentence_clean"],
            "target_sentence_clean": row["target_sentence_clean"],
            "source_url": row["source_url"],
            "raw_html_path": row["raw_path"],
        }
        for row in read_csv(PROCESSED / "amis_chinese_restoration_audit.csv")
        if row["origin"] == "current_scrape_reviewed_match"
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
        "output_rows": 2321,
        "output_forms": 2296,
    }
    assert [row["record_id"] for row in merged[:25]] == [row["record_id"] for row in current]
    assert Counter(row["origin"] for row in audit) == {
        "current_scrape_reviewed_match": 25,
        "joseph_reviewed_traditional": 2296,
    }


def test_restoration_keeps_distinct_translations_without_exact_duplicates():
    _, (merged, _, _) = restored_rows()
    pairs = [
        (dedupe_key(row["source_sentence_clean"]), dedupe_key(row["target_sentence_clean"]))
        for row in merged
    ]

    assert len(pairs) == len(set(pairs))
    assert len({source for source, _ in pairs}) == 2311
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
