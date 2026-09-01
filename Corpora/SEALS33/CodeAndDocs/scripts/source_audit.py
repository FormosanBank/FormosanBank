#!/usr/bin/env python3
"""Audit generated SEALS 33 XML against the committed source snapshot."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from lxml import etree

if __package__:
    from .build_xml import (
        DEFAULT_OUTPUT,
        DEFAULT_SNAPSHOT,
        LANGUAGES,
        SOURCE_ROW_EXCLUSIONS,
        load_snapshot,
    )
else:
    from build_xml import (
        DEFAULT_OUTPUT,
        DEFAULT_SNAPSHOT,
        LANGUAGES,
        SOURCE_ROW_EXCLUSIONS,
        load_snapshot,
    )


APOSTROPHES = "\u2018\u2019\u02bc\u02bb`\u02c8"
DOUBLE_QUOTES = "\u201c\u201d"
DASHES = "\u2010\u2011\u2012\u2013\u2014\u2015\u2212\ufe58\ufe63\uff0d"


class AuditError(AssertionError):
    """Raised when generated XML is not source-aligned."""


def normalize_space(value: str) -> str:
    value = unicodedata.normalize("NFC", value.replace("\xa0", " "))
    return re.sub(r"\s+", " ", value).strip()


def canonical_form(value: str) -> str:
    table = {ord(char): "'" for char in APOSTROPHES}
    table.update({ord(char): '"' for char in DOUBLE_QUOTES})
    table.update({ord(char): "-" for char in DASHES})
    table.update({ord("["): "(", ord("]"): ")"})
    value = normalize_space(value.translate(table))
    return re.sub(r"--+", "-", value)


def canonical_translation(value: str, lang: str) -> str:
    value = normalize_space(value)
    if lang == "zho":
        value = value.translate(
            {ord(char): "＂" for char in "\u201c\u201d\u300c\u300d\u300e\u300f"}
        )
    elif lang == "eng":
        value = value.translate({ord(char): '"' for char in DOUBLE_QUOTES})
    return value


def audit(snapshot_path: Path = DEFAULT_SNAPSHOT, xml_dir: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    snapshot = load_snapshot(snapshot_path)
    rows = {row["source_row"]: row for row in snapshot["rows"]}
    expected_ids = [row for row in range(1, 30) if row not in SOURCE_ROW_EXCLUSIONS]
    files = sorted(xml_dir.rglob("*.xml"))
    if len(files) != 2:
        raise AuditError(f"expected two XML files; found {len(files)}")

    included_forms = 0
    included_translations = 0
    for lang_code, config in LANGUAGES.items():
        path = xml_dir / config["name"] / config["filename"]
        if not path.exists():
            raise AuditError(f"missing {path}")
        root = etree.parse(str(path)).getroot()
        if root.get("id") != config["text_id"]:
            raise AuditError(f"unexpected TEXT id in {path}")
        if root.get("{http://www.w3.org/XML/1998/namespace}lang") != lang_code:
            raise AuditError(f"unexpected xml:lang in {path}")
        if root.get("dialect") != config["dialect"]:
            raise AuditError(f"unexpected dialect in {path}")

        sentences = root.findall("S")
        actual_ids = [int(sentence.get("id")) for sentence in sentences]
        if actual_ids != expected_ids:
            raise AuditError(f"unexpected S ids in {path}: {actual_ids}")
        for sentence in sentences:
            source_row = int(sentence.get("id"))
            source = rows[source_row]
            original = sentence.findall('./FORM[@kindOf="original"]')
            if len(original) != 1:
                raise AuditError(f"row {source_row} in {path} must have one original FORM")
            if canonical_form(original[0].text or "") != canonical_form(source[lang_code]):
                raise AuditError(f"source FORM mismatch at {path}:S={source_row}")
            if "*" in (original[0].text or ""):
                raise AuditError(f"POL-016 asterisk retained at {path}:S={source_row}")

            expected_translations = [("zho", source["zho"])]
            if "eng" in source:
                expected_translations.append(("eng", source["eng"]))
            actual_translations = [
                (
                    item.get("{http://www.w3.org/XML/1998/namespace}lang"),
                    item.text or "",
                )
                for item in sentence.findall("TRANSL")
            ]
            if len(actual_translations) != len(expected_translations):
                raise AuditError(f"translation count mismatch at {path}:S={source_row}")
            for actual, expected in zip(actual_translations, expected_translations, strict=True):
                actual_lang, actual_text = actual
                expected_lang, expected_text = expected
                if actual_lang != expected_lang or canonical_translation(
                    actual_text, expected_lang
                ) != canonical_translation(expected_text, expected_lang):
                    raise AuditError(f"translation mismatch at {path}:S={source_row}")
            included_forms += 1
            included_translations += len(expected_translations)

        for forbidden in ("W", "M", "AUDIO"):
            if root.findall(f".//{forbidden}"):
                raise AuditError(f"unexpected {forbidden} tier in {path}")

    return {
        "status": "pass",
        "source_rows": 29,
        "included_rows_per_language": 28,
        "policy_excluded_rows": sorted(SOURCE_ROW_EXCLUSIONS),
        "included_original_forms": included_forms,
        "included_translations": included_translations,
        "excluded_presenter_blocks": len(snapshot["excluded_presenter_blocks"]),
        "rows_sha256": snapshot["rows_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--xml-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = audit(args.snapshot, args.xml_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            "source audit passed: "
            f"{result['source_rows']} rows accounted for, "
            f"{result['included_rows_per_language']} included per language, "
            "1 POL-016 exclusion"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
