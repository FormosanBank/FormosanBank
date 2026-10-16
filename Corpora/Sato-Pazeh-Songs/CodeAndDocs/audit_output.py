#!/usr/bin/env python3
"""Audit final XML and source coverage independently of FormosanBank QC."""

from __future__ import annotations

import csv
import sys
import xml.etree.ElementTree as ET

from corpus_config import (
    COPYRIGHT,
    LEDGER_CSV,
    REVIEWED_CSV,
    SOURCE_PAGES,
    TEXTS,
    final_path,
    sentence_id,
    source_locator,
)


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SOURCE_BACKED_EXPECTATIONS = {
    ("kaiki", "12"): {
        "page": "116",
        "translation_jpn": "是蚋望在東、故號名",
    },
    ("flood", "3"): {
        "page": "119",
        "form_original": "Tap-ba-nan nu mat-taro",
    },
    ("dispersion", "8"): {
        "page": "123",
        "translation_jpn": "乃是要爲蕃人、蕃乃是東蕃也",
    },
    ("dispersion", "14"): {
        "page": "123",
        "translation_jpn": "我等要去我所、乃是爲生蕃是生蕃沙漏毛（サラウモー蕃號也）",
    },
    ("dispersion", "17"): {
        "page": "124",
        "translation_jpn": "橋號マビダピ、乃是タトゥマウマウワン",
    },
    ("dispersion", "18"): {
        "page": "124",
        "translation_jpn": "投茅々灣滑落于橋下",
    },
    ("dispersion", "20"): {
        "page": "124",
        "translation_jpn": "答曰汝自囘去、我要去",
    },
    ("dispersion", "21"): {
        "page": "124",
        "translation_jpn": "變爲鹿乃是麞鹿也",
    },
    ("dispersion", "22"): {
        "page": "124",
        "form_original": "Tatumaumauwan, kahah mausai mahah dakho",
        "translation_jpn": "不得已自去爲生蕃也",
    },
    ("dispersion", "23"): {
        "page": "124",
        "form_original": "Aiyan nu aiyan, saisaiya wilan.",
        "translation_jpn": "",
    },
}


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    errors: list[str] = []
    reviewed_rows = read_csv(REVIEWED_CSV)
    grouped = {key: [] for key in TEXTS}
    for row in reviewed_rows:
        grouped.setdefault(row["text_key"], []).append(row)

    reviewed_by_key = {
        (row["text_key"], row["sequence"]): row for row in reviewed_rows
    }
    for row_key, expected_fields in SOURCE_BACKED_EXPECTATIONS.items():
        row = reviewed_by_key.get(row_key)
        require(row is not None, f"Missing source-backed row: {row_key}", errors)
        if row is None:
            continue
        for field, expected in expected_fields.items():
            require(
                row[field] == expected,
                f"{row_key}: {field} is {row[field]!r}; expected {expected!r}",
                errors,
            )

    seen_ids: set[str] = set()
    xml_sentence_count = 0
    translation_count = 0
    for text_key, config in TEXTS.items():
        path = final_path(text_key)
        require(path.is_file(), f"Missing final XML: {path}", errors)
        if not path.is_file():
            continue
        root = ET.parse(path).getroot()
        require(root.tag == "TEXT", f"{path}: root is not TEXT", errors)
        require(root.get(XML_LANG) == "pzh", f"{path}: xml:lang must be pzh", errors)
        require(root.get("glottocode") == "paze1234", f"{path}: wrong glottocode", errors)
        require(root.get("dialect") == "unknown", f"{path}: dialect must be unknown", errors)
        require(root.get("copyright") == COPYRIGHT, f"{path}: copyright must be {COPYRIGHT}", errors)
        require(root.get("id") == config["text_id"], f"{path}: unexpected TEXT id", errors)
        require("1931" in root.get("citation", ""), f"{path}: citation must use the source date 1931", errors)
        require(not root.findall(".//PHON"), f"{path}: unsupported PHON tier present", errors)
        require(not root.findall(".//W"), f"{path}: unsupported W tier present", errors)
        require(not root.findall(".//M"), f"{path}: unsupported M tier present", errors)
        require(not root.findall(".//AUDIO"), f"{path}: unsupported AUDIO tier present", errors)

        xml_rows = root.findall("S")
        source_rows = sorted(grouped[text_key], key=lambda row: int(row["sequence"]))
        require(
            len(xml_rows) == int(config["expected_count"]),
            f"{path}: {len(xml_rows)} S elements; expected {config['expected_count']}",
            errors,
        )
        require(
            len(xml_rows) == len(source_rows),
            f"{path}: XML/reviewed row count mismatch",
            errors,
        )

        for xml_row, source_row in zip(xml_rows, source_rows):
            sequence = int(source_row["sequence"])
            expected_id = sentence_id(text_key, sequence)
            actual_id = xml_row.get("id", "")
            require(actual_id == expected_id, f"{path}: expected id {expected_id}, got {actual_id}", errors)
            require(actual_id not in seen_ids, f"Duplicate S id: {actual_id}", errors)
            seen_ids.add(actual_id)

            forms = xml_row.findall("FORM")
            translations = xml_row.findall("TRANSL")
            originals = xml_row.findall("FORM[@kindOf='original']")
            standards = xml_row.findall("FORM[@kindOf='standard']")
            require(len(forms) == 1, f"{actual_id}: expected one source FORM tier", errors)
            require(len(originals) == 1, f"{actual_id}: expected exactly one original FORM", errors)
            require(not standards, f"{actual_id}: unsupported standard FORM present", errors)
            expected_translations = 1 if source_row["translation_jpn"] else 0
            require(
                len(translations) == expected_translations,
                f"{actual_id}: expected {expected_translations} TRANSL tiers",
                errors,
            )
            require(
                xml_row.get("source") == source_locator(source_row),
                f"{actual_id}: source locator differs from reviewed CSV",
                errors,
            )
            if originals:
                require(originals[0].text == source_row["form_original"], f"{actual_id}: original FORM differs from reviewed CSV", errors)
            if translations:
                require(translations[0].get(XML_LANG) == "jpn", f"{actual_id}: TRANSL is not jpn", errors)
                require(
                    translations[0].text == source_row["translation_jpn"],
                    f"{actual_id}: TRANSL differs from reviewed source",
                    errors,
                )
                translation_count += 1
        xml_sentence_count += len(xml_rows)

    ledger_rows = read_csv(LEDGER_CSV)
    included = [row for row in ledger_rows if row["included"] == "true"]
    excluded = [row for row in ledger_rows if row["included"] == "false"]
    ledger_ids = {row["final_s_id"] for row in included}
    covered_pages = {int(row["pdf_page"]) for row in ledger_rows}
    require(len(reviewed_rows) == 83, f"Reviewed row count is {len(reviewed_rows)}, expected 83", errors)
    require(xml_sentence_count == 83, f"XML sentence count is {xml_sentence_count}, expected 83", errors)
    require(translation_count == 82, f"Translation count is {translation_count}, expected 82", errors)
    require(len(included) == 83, f"Ledger included count is {len(included)}, expected 83", errors)
    require(ledger_ids == seen_ids, "Ledger/XML S id sets differ", errors)
    require(covered_pages == set(range(1, SOURCE_PAGES + 1)), f"Ledger PDF page coverage is {sorted(covered_pages)}", errors)
    require(all(row["exclusion_reason"] for row in excluded), "Excluded ledger row lacks a reason", errors)
    require(len(excluded) == 16, f"Ledger excluded block count is {len(excluded)}, expected 16", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"audit_errors={len(errors)}", file=sys.stderr)
        return 1

    print(f"xml_files={len(TEXTS)}")
    print(f"sentences={xml_sentence_count}")
    print(f"unique_s_ids={len(seen_ids)}")
    print(f"translations={translation_count}")
    print("standard_forms=0 (Pazeh has no designated standard orthography)")
    print(f"ledger_included={len(included)}")
    print(f"ledger_excluded_blocks={len(excluded)}")
    print(f"ledger_pdf_pages={len(covered_pages)}/{SOURCE_PAGES}")
    print("unsupported_tiers=0")
    print("audit_errors=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
