#!/usr/bin/env python3
"""Verify complete source coverage and final source-to-XML alignment."""

from __future__ import annotations

import csv
import json
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import build_xml
from normalize_standard_sentences import normalize as normalize_standard_sentence


CORPUS_ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = Path(__file__).resolve().parents[1]
DIRECT_CHECKS = CODE_ROOT / "evidence" / "direct_source_checks.csv"
SUMMARY = CODE_ROOT / "evidence" / "source_alignment_summary.json"
REVIEWER_FLAGGED_SENTENCE_IDS = {
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
STARRED_EXCLUDED_IDS = {
    "tsukida2014_seediq_S010",
    "tsukida2014_seediq_S012",
    "tsukida2014_seediq_S014",
    "tsukida2014_seediq_S030",
    "tsukida2014_seediq_S031",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def direct_forms(element: ET.Element) -> dict[str, str]:
    return {form.get("kindOf", ""): form.text or "" for form in element.findall("FORM")}


def conversion_table() -> list[tuple[str, str]]:
    return [
        (row["original"], row["standard"])
        for row in build_xml.read_tsv(CODE_ROOT / "raw_data" / "source_to_ortho113.tsv")
    ]


def expected_standard(text: str, *, sentence: bool) -> str:
    value = text
    for original, standard in conversion_table():
        value = value.replace(original, standard)
    return normalize_standard_sentence(value) if sentence else value


def check_word_structure(sentence: ET.Element, record: dict[str, str]) -> None:
    reviewed = build_xml.read_morpheme_alignments()
    expected_words, alignment_note = build_xml.word_alignment(record)
    words = sentence.findall("W")
    require(len(words) == len(expected_words), f"W count mismatch at {record['id']}")
    for word_index, (word, (original, gloss)) in enumerate(
        zip(words, expected_words), start=1
    ):
        require(word.get("id") == f"{record['id']}W{word_index}", "Unexpected W id")
        forms = direct_forms(word)
        require(
            forms.get("original") == original,
            f"W original mismatch at {word.get('id')}",
        )
        require(
            forms.get("standard") == expected_standard(original, sentence=False),
            f"W standard mismatch at {word.get('id')}",
        )
        morpheme_rows, canonical_gloss = build_xml.morpheme_alignment(
            record, word_index, original, gloss, reviewed
        )
        expected_word_glosses = [gloss]
        if canonical_gloss:
            expected_word_glosses.append(canonical_gloss)
        translations = word.findall("TRANSL")
        require(
            [translation.text or "" for translation in translations]
            == expected_word_glosses,
            f"W gloss mismatch at {word.get('id')}",
        )
        require(
            all(translation.get("kindOf") is None for translation in translations),
            f"Unexpected W TRANSL tier at {word.get('id')}",
        )
        if canonical_gloss:
            require(translations[1].get("ver") == "alt", "Canonical gloss not alt")

        morphemes = word.findall("M")
        require(
            len(morphemes) == len(morpheme_rows),
            f"M count mismatch at {word.get('id')}",
        )
        for morpheme_index, (morpheme, (m_original, m_gloss)) in enumerate(
            zip(morphemes, morpheme_rows), start=1
        ):
            require(
                morpheme.get("id") == f"{record['id']}W{word_index}M{morpheme_index}",
                "Unexpected M id",
            )
            forms = direct_forms(morpheme)
            require(forms.get("original") == m_original, "M original mismatch")
            require(
                forms.get("standard") == expected_standard(m_original, sentence=False),
                "M standard mismatch",
            )
            translations = morpheme.findall("TRANSL")
            require(
                len(translations) == 1
                and (translations[0].text or "") == m_gloss
                and translations[0].get("kindOf") is None,
                "M gloss mismatch",
            )
    require(record["word_structure"] == alignment_note, "Word audit drift")


def main() -> None:
    rows = build_xml.read_tsv()
    build_xml.validate_rows(rows)
    records = build_xml.included_records(rows)
    for record in records:
        _, record["word_structure"] = build_xml.word_alignment(record)
    source_by_id = {row["id"]: row for row in rows}
    record_by_id = {record["id"]: record for record in records}

    root = ET.parse(build_xml.FINAL_XML).getroot()
    sentences = root.findall("S")
    sentence_by_id = {sentence.get("id", ""): sentence for sentence in sentences}
    require(len(sentence_by_id) == len(sentences) == 26, "Expected 26 unique S records")
    require(set(sentence_by_id) == set(record_by_id), "XML and source IDs differ")
    require(build_xml.SOURCE_PDF_SHA256 in root.get("source", ""), "Missing PDF hash")

    no_word_ids = {
        sentence_id
        for sentence_id, sentence in sentence_by_id.items()
        if not sentence.findall("W")
    }
    require(not no_word_ids, f"Sentences without W structure: {sorted(no_word_ids)}")
    require(
        all(sentence_by_id[sentence_id].findall("W") for sentence_id in REVIEWER_FLAGGED_SENTENCE_IDS),
        "A reviewer-flagged sentence still lacks W structure",
    )
    require(
        STARRED_EXCLUDED_IDS.isdisjoint(sentence_by_id),
        "Starred source unit leaked into XML",
    )

    for sentence_id, record in record_by_id.items():
        sentence = sentence_by_id[sentence_id]
        forms = direct_forms(sentence)
        require(
            forms.get("original") == record["original"],
            f"S original mismatch at {sentence_id}",
        )
        require(
            forms.get("standard")
            == expected_standard(record["original"], sentence=True),
            f"S standard mismatch at {sentence_id}",
        )
        require(
            sentence.get("source") == record["source_locator"],
            f"Source locator mismatch at {sentence_id}",
        )
        expected_translations = [record["translation"]] if record["translation"] else []
        if record["translation_alt"] and record["translation_alt_in_xml"] == "yes":
            expected_translations.append(record["translation_alt"])
        require(
            [translation.text or "" for translation in sentence.findall("TRANSL")]
            == expected_translations,
            f"Translation mismatch at {sentence_id}",
        )
        require(
            not any(mark in forms["standard"] for mark in "-=()[]"),
            f"Analysis notation remains in S standard at {sentence_id}",
        )
        check_word_structure(sentence, record)

    require(len(root.findall(".//W")) == 188, "Expected 188 W elements")
    require(len(root.findall(".//M")) == 115, "Expected 115 M elements")

    ledger = read_csv(build_xml.SOURCE_LEDGER)
    require(len(ledger) == 39, "Expected 39 source-ledger rows")
    require(
        Counter(row["included_in_xml"] for row in ledger) == {"yes": 26, "no": 13},
        "Unexpected source-ledger totals",
    )
    require(
        {row["source_id"] for row in ledger} == set(source_by_id),
        "Source-ledger IDs differ",
    )

    pages = read_csv(build_xml.PAGE_INVENTORY)
    require(len(pages) == 11, "Expected 11 article pages")
    require(
        {int(row["pdf_page"]) for row in pages} == set(range(74, 85)),
        "Page coverage differs",
    )
    require(
        len(read_csv(build_xml.NOTATION_AUDIT)) == 39,
        "Notation audit must cover every unit",
    )

    direct_checks = read_csv(DIRECT_CHECKS)
    require(len(direct_checks) == 33, "Expected 33 rendered-page checks")
    require(
        set(record_by_id).issubset(
            {check["record_id"] for check in direct_checks}
        ),
        "Every included record must have a rendered-page check",
    )
    for check in direct_checks:
        source = source_by_id.get(check["record_id"])
        require(
            source is not None, f"Unknown direct-check record: {check['record_id']}"
        )
        for check_field, source_field in (
            ("stable_locator", "source_locator"),
            ("source_original", "original"),
            ("source_gloss", "gloss"),
            ("source_translation", "translation"),
        ):
            require(
                check[check_field] == source[source_field],
                f"Direct check drift at {check['record_id']}",
            )
        require(
            check["result"] == "pass",
            f"Unresolved direct check at {check['record_id']}",
        )

    standard_form_count = 0
    for parent in root.findall(".//FORM/.."):
        if parent.find("FORM[@kindOf='standard']") is None:
            continue
        standard_form_count += 1
        phonology = parent.findall("PHON[@kindOf='standard']")
        require(len(phonology) == 1, f"Expected one PHON at {parent.get('id')}")
        require((phonology[0].text or "").strip(), f"Empty PHON at {parent.get('id')}")
        require(
            "*" not in (phonology[0].text or ""),
            f"PHON placeholder at {parent.get('id')}",
        )
        phon_text = phonology[0].text or ""
        require("'" not in phon_text, f"ASCII apostrophe remains in PHON at {parent.get('id')}")
        require(
            not any(unicodedata.category(char).startswith("P") for char in phon_text),
            f"Punctuation remains in PHON at {parent.get('id')}",
        )
    require(standard_form_count == 329, "Expected 329 standard FORM/PHON parents")
    require(len(root.findall(".//PHON")) == 329, "Expected 329 PHON tiers")

    require((CORPUS_ROOT / "XML").is_dir(), "Published XML directory is missing")
    final_files = sorted(
        path.relative_to(CORPUS_ROOT).as_posix()
        for path in (CORPUS_ROOT / "XML").rglob("*.xml")
    )
    require(
        final_files
        == ["XML/Seediq/tsukida_2014_correlative_clauses_in_seediq.xml"],
        "Unexpected final XML layout",
    )

    build_xml.write_source_map(records, root)
    summary = {
        "article_pages_reviewed": 11,
        "excluded_source_units": 13,
        "final_morphemes": 115,
        "final_phonology_tiers": 329,
        "final_sentences": 26,
        "final_words": 188,
        "included_source_units": 26,
        "phonology_placeholders": 0,
        "source_units": 39,
        "reviewer_flagged_records_remediated": 12,
        "source_units_without_safe_word_alignment": 0,
        "unresolved_source_alignment_findings": 0,
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("Source alignment passed: 39 units, 11 pages, 26 S, 188 W, 115 M, 329 PHON.")


if __name__ == "__main__":
    main()
