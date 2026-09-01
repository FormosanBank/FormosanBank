#!/usr/bin/env python3
"""Verify published source-review evidence and generated tier invariants."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from apply_review_corrections import FULL_ORIGINAL_FORMS
from build_source_ledger import JOHN_PAGES, MATTHEW_PAGES


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "verses.jsonl"
FINAL = ROOT.parent / "XML" / "Siraya"
CHECKS = ROOT / "data" / "source_checks.json"
LEDGER = ROOT / "data" / "source_ledger.csv"
SOURCE_SCOPE = ROOT / "data" / "source_scope.json"
TRANSLATION_MANIFEST = ROOT / "data" / "reference_translation_manifest.json"
SOURCE_REVIEW_MANIFEST = ROOT / "data" / "source_review_manifest.json"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

SOURCES = {
    "Gospels of St. Matthew and St. John.pdf": {
        "bytes": 17_870_622,
        "pages": 149,
        "sha256": "bb382f8157b1b2359b7a47d7ec4ad1cfcf396ae8754cfe52a6e01c0ebcc23ca6",
    },
    "Matthew.pdf": {
        "bytes": 11_259_279,
        "pages": 190,
        "sha256": "2c197bf35d4c7affd7d9ccaa5d3743622bfdae8d959e332abd17b5fa7cf1ff80",
    },
}


def sha256_bytes(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_reference(path: Path) -> str:
    """Hash the exact reference bytes, decompressing checked-in gzip files."""

    if path.suffix != ".gz":
        return sha256_file(path)
    digest = hashlib.sha256()
    with gzip.open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_intermediate() -> dict[tuple[str, str], dict[str, object]]:
    rows = [
        json.loads(line)
        for line in INTERMEDIATE.read_text(encoding="utf-8").splitlines()
    ]
    indexed = {(row["path"], row["sentence_id"]): row for row in rows}
    if len(rows) != 1_951 or len(indexed) != len(rows):
        raise SystemExit("expected 1,951 unique intermediate verse records")
    return indexed


def form_fields(row: dict[str, object]) -> dict[str, str]:
    return {
        field["kindOf"]: field["text"]
        for field in row["fields"]
        if field["tag"] == "FORM"
    }


def verify_tiers(rows: dict[tuple[str, str], dict[str, object]]) -> None:
    original_imbalances = []
    for key, row in rows.items():
        forms = form_fields(row)
        if set(forms) != {"original"}:
            raise SystemExit(f"unexpected FORM tiers for {key}: {sorted(forms)}")
        original = forms["original"]
        if (
            original.count("(") != original.count(")")
            or original.count("[") != original.count("]")
        ):
            original_imbalances.append(key)

    expected_imbalances = [
        ("John/chapter12.xml", "verse28"),
        ("John/chapter12.xml", "verse33"),
    ]
    if original_imbalances != expected_imbalances:
        raise SystemExit(
            f"unexpected original-tier punctuation imbalance: {original_imbalances}"
        )


def verify_stable_ids(rows: dict[tuple[str, str], dict[str, object]]) -> None:
    expected_paths = sorted({path for path, _sentence_id in rows})
    actual_paths = sorted(str(path.relative_to(FINAL)) for path in FINAL.rglob("*.xml"))
    if actual_paths != expected_paths:
        raise SystemExit("generated XML paths diverge from the reviewed source inventory")

    for relative in expected_paths:
        book, chapter_file = Path(relative).parts
        chapter = Path(chapter_file).stem.removeprefix("chapter")
        expected_text_id = f"Siraya_Dutch_{book}_Chapter{chapter}"
        root = ET.parse(FINAL / relative).getroot()
        if root.attrib.get("id") != expected_text_id:
            raise SystemExit(f"published TEXT id changed: {relative}")
        actual_sentence_ids = [sentence.attrib["id"] for sentence in root.findall("S")]
        expected_sentence_ids = [
            sentence_id for path, sentence_id in rows if path == relative
        ]
        if actual_sentence_ids != expected_sentence_ids:
            raise SystemExit(f"published sentence ids changed: {relative}")


def verify_checks(rows: dict[tuple[str, str], dict[str, object]]) -> None:
    manifest = json.loads(CHECKS.read_text(encoding="utf-8"))
    checks = manifest["checks"]
    rare_checks = manifest.get("rare_form_checks", [])
    followup_ids = manifest.get("followup_sample_ids", [])
    phases = Counter(check["phase"] for check in checks)
    if phases["core"] < 5 or phases["regression"] < 3:
        raise SystemExit(f"insufficient source checks: {dict(phases)}")
    check_ids = {check["id"] for check in checks}
    if (
        manifest.get("followup_review_date") != "2026-07-28"
        or len(followup_ids) < 5
        or len(followup_ids) != len(set(followup_ids))
        or not set(followup_ids) <= check_ids
    ):
        raise SystemExit("invalid follow-up source-check record")
    checked_keys = {(check["path"], check["sentence_id"]) for check in checks}
    expected_keys = set(FULL_ORIGINAL_FORMS) - {("John/chapter5.xml", "verse42")}
    if checked_keys != expected_keys:
        raise SystemExit("source-check manifest does not cover every reviewed full form")

    for check in checks:
        key = (check["path"], check["sentence_id"])
        row = rows[key]
        forms = form_fields(row)
        if sha256_bytes(forms["original"]) != check["original_sha256"]:
            raise SystemExit(f"original source-check mismatch: {check['id']}")
        if FULL_ORIGINAL_FORMS.get(key) != forms["original"]:
            raise SystemExit(f"source correction and manifest diverged: {check['id']}")
        if not 1 <= check["pdf_page"] <= SOURCES[check["source_file"]]["pages"]:
            raise SystemExit(f"invalid PDF page in source check: {check['id']}")

        xml_path = FINAL / check["path"]
        sentence = next(
            sentence
            for sentence in ET.parse(xml_path).getroot().findall("S")
            if sentence.attrib["id"] == check["sentence_id"]
        )
        xml_forms = {
            field.attrib["kindOf"]: field.text or ""
            for field in sentence.findall("FORM")
        }
        if xml_forms != {"original": forms["original"]}:
            raise SystemExit(f"final XML differs from reviewed intermediate: {check['id']}")

    if manifest.get("rare_form_review_date") != "2026-08-20" or len(rare_checks) != 2:
        raise SystemExit("invalid rare-form source-check record")
    for check in rare_checks:
        key = (check["path"], check["sentence_id"])
        forms = form_fields(rows[key])
        original = forms["original"]
        if (
            check["checked_text"] not in original
            or sha256_bytes(original) != check["original_sha256"]
            or not 1 <= check["pdf_page"] <= SOURCES[check["source_file"]]["pages"]
        ):
            raise SystemExit(f"rare-form source-check mismatch: {check['id']}")
        xml_path = FINAL / check["path"]
        sentence = next(
            sentence
            for sentence in ET.parse(xml_path).getroot().findall("S")
            if sentence.attrib["id"] == check["sentence_id"]
        )
        xml_original = sentence.find("FORM[@kindOf='original']")
        if xml_original is None or (xml_original.text or "") != original:
            raise SystemExit(f"rare-form XML mismatch: {check['id']}")

    print(
        f"Source checks: {phases['core']} core and "
        f"{phases['regression']} regression examples verified; "
        f"{len(followup_ids)} independently rechecked; "
        f"{len(rare_checks)} rare forms confirmed."
    )


def verify_full_review(rows: dict[tuple[str, str], dict[str, object]]) -> None:
    manifest = json.loads(SOURCE_REVIEW_MANIFEST.read_text(encoding="utf-8"))
    scope = manifest.get("review_scope", {})
    if (
        manifest.get("schema_version") != 1
        or manifest.get("review_date") != "2026-08-21"
        or manifest.get("canonical_input") != "intermediate/verses.jsonl"
        or scope
        != {
            "reviewed_units": 1_951,
            "rendered_scan_pages": 314,
            "book_units": {"John": 880, "Matthew": 1_071},
            "chapter_files": 49,
        }
    ):
        raise SystemExit("invalid full source-review scope")

    expected_witnesses = [
        {
            "book": "Matthew",
            "url": "https://storage.googleapis.com/siraya/20230218/matt.js",
            "bytes": 876_703,
            "sha256": "90254b8b39f732008722ae0fe3210b76b1dc88896886903b15a409c6608e7f14",
            "last_modified": "2023-02-18",
        },
        {
            "book": "John",
            "url": "https://storage.googleapis.com/siraya/20230218/john.js",
            "bytes": 702_869,
            "sha256": "d7a495a8ce90ddbd8d994aab9a20ea2cf0484ffbbd90f808a3ed7d3c8df9359b",
            "last_modified": "2023-02-18",
        },
    ]
    if manifest.get("transcription_witnesses") != expected_witnesses:
        raise SystemExit("unexpected transcription-witness identity")
    scan_control = {
        item["name"]: item["sha256"] for item in manifest.get("scan_control", [])
    }
    if scan_control != {name: item["sha256"] for name, item in SOURCES.items()}:
        raise SystemExit("source-review scan identities diverge from private sources")
    if manifest.get("adjudication") != {
        "rare_character_crops_checked": 36,
        "additional_low_confidence_verses_checked": 7,
        "invariant_followup_verses_checked": 2,
        "apostrophe_policy": "Represent printed apostrophe variants as ASCII U+0027.",
        "confusable_policy": (
            "Replace witness-only Greek, Cyrillic, and small-cap OCR confusables "
            "with the Latin characters visible in the scans."
        ),
        "punctuation_policy": (
            "Preserve printed square brackets, round parentheses, punctuation "
            "imbalance, spacing, diacritics, and hyphenation."
        ),
    }:
        raise SystemExit("unexpected source-review adjudication policy")

    reviewed = []
    for (path, sentence_id), row in rows.items():
        reviewed.append(
            {
                "path": path,
                "sentence_id": sentence_id,
                "original": form_fields(row)["original"],
            }
        )
    if canonical_digest(reviewed) != manifest.get("original_tiers_sha256"):
        raise SystemExit("full reviewed original-tier hash mismatch")

    expected_chapters = []
    for book, page_map in (("Matthew", MATTHEW_PAGES), ("John", JOHN_PAGES)):
        for chapter, pdf_pages in page_map.items():
            path = f"{book}/chapter{chapter}.xml"
            chapter_rows = [item for item in reviewed if item["path"] == path]
            expected_chapters.append(
                {
                    "path": path,
                    "pdf_pages": pdf_pages,
                    "reviewed_units": len(chapter_rows),
                    "original_tiers_sha256": canonical_digest(chapter_rows),
                }
            )
            xml_originals = {
                sentence.attrib["id"]: (
                    sentence.find("FORM[@kindOf='original']").text or ""
                )
                for sentence in ET.parse(FINAL / path).getroot().findall("S")
            }
            expected_originals = {
                item["sentence_id"]: item["original"] for item in chapter_rows
            }
            if xml_originals != expected_originals:
                raise SystemExit(f"final XML differs from full review: {path}")
    if manifest.get("chapters") != expected_chapters:
        raise SystemExit("chapter-level source-review hashes or page spans changed")
    print("Full source review: 1,951 units across 314 rendered pages verified.")


def verify_ledger(rows: dict[tuple[str, str], dict[str, object]]) -> None:
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        ledger = list(csv.DictReader(handle))
    if len(ledger) != len(rows):
        raise SystemExit("source ledger does not cover every intermediate record")
    counts = Counter(row["source_file"] for row in ledger)
    if counts != Counter(
        {
            "Matthew.pdf": 1_071,
            "Gospels of St. Matthew and St. John.pdf": 880,
        }
    ):
        raise SystemExit(f"unexpected ledger source split: {dict(counts)}")

    for row in ledger:
        book = "John" if row["source_file"].startswith("Gospels") else "Matthew"
        chapter = int(row["source_locator"].split()[-1].split(":")[0])
        expected_pages = (JOHN_PAGES if book == "John" else MATTHEW_PAGES)[chapter]
        if row["pdf_pages"] != expected_pages:
            raise SystemExit(f"unexpected PDF pages for {row['source_locator']}")
        if not row["final_xml_path"].startswith(f"XML/Siraya/{book}/"):
            raise SystemExit(f"non-canonical XML path in ledger: {row['final_xml_path']}")
        path = row["final_xml_path"].removeprefix("XML/Siraya/")
        key = (path, row["final_s_id"])
        if row["original_form"] != form_fields(rows[key])["original"]:
            raise SystemExit(f"ledger original differs from reviewed input: {key}")
        if row["method"] != (
            "full rendered-scan review aided by a public raw transcription "
            "witness and independent OCR"
        ):
            raise SystemExit(f"unexpected review method in ledger: {key}")
        if row["review_note"] != (
            "Reviewed against the printed Siraya column; the rendered scan "
            "controls punctuation, diacritics, spacing, and hyphenation"
        ):
            raise SystemExit(f"incomplete review note in ledger: {key}")


def verify_scope_and_references() -> None:
    scope = json.loads(SOURCE_SCOPE.read_text(encoding="utf-8"))
    if [item["included_page_range"] for item in scope["source_files"]] != [
        "13-186",
        "6-145",
    ]:
        raise SystemExit("unexpected source page scope")
    decisions = {item["component"]: item["included"] for item in scope["component_decisions"]}
    expected_exclusions = {
        "Dutch parallel columns",
        "Book and chapter headings",
        "Embedded OCR text",
        "PHON tiers",
        "W and M tiers",
    }
    if set(decisions) != expected_exclusions or any(decisions.values()):
        raise SystemExit("source component decisions are incomplete")

    manifest = json.loads(TRANSLATION_MANIFEST.read_text(encoding="utf-8"))
    paths = [
        (manifest["english"]["checked_in_extract"], manifest["english"]["checked_in_extract_sha256"]),
        (manifest["mandarin"]["matthew"]["path"], manifest["mandarin"]["matthew"]["sha256"]),
        (manifest["mandarin"]["john"]["path"], manifest["mandarin"]["john"]["sha256"]),
    ]
    for relative, expected in paths:
        reference_path = Path(relative)
        if reference_path.parts[0] == "CodeAndDocs":
            reference_path = Path(*reference_path.parts[1:])
        if sha256_reference(ROOT / reference_path) != expected:
            raise SystemExit(f"reference translation identity mismatch: {relative}")


def main() -> None:
    rows = load_intermediate()
    verify_tiers(rows)
    verify_stable_ids(rows)
    verify_checks(rows)
    verify_full_review(rows)
    verify_ledger(rows)
    verify_scope_and_references()
    print(
        "Published reference identities, original-tier invariants, stable IDs, "
        "full source-review evidence, source scope, and ledger passed."
    )


if __name__ == "__main__":
    main()
