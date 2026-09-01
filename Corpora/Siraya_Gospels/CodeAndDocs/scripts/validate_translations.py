#!/usr/bin/env python3
"""Validate aligned English and Mandarin reference translation coverage."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from import_cuv_translations import OMITTED, aligned_text as aligned_cuv
from import_cuv_translations import mapped_verse, parse
from import_kjv_translations import aligned_text as aligned_kjv
from import_kjv_translations import load_reference


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT.parent / "XML" / "Siraya"
USFM = ROOT / "reference_translations" / "cmn-cu89t_usfm"
XML_NS = "{http://www.w3.org/XML/1998/namespace}lang"


def translations(sentence: ET.Element) -> dict[str, str]:
    return {
        element.attrib[XML_NS]: element.text or ""
        for element in sentence.findall("TRANSL")
    }


def main() -> None:
    kjv = load_reference()
    cuv = {
        "Matthew": parse(USFM / "70-MATcmn-cu89t.usfm.gz"),
        "John": parse(USFM / "73-JHNcmn-cu89t.usfm.gz"),
    }
    english_checked = mandarin_checked = omitted = 0
    for path in sorted(FINAL.rglob("*.xml")):
        book, file_name = path.relative_to(FINAL).parts
        chapter = int(Path(file_name).stem.removeprefix("chapter"))
        for sentence in ET.parse(path).getroot().findall("S"):
            verse = int(sentence.attrib["id"].removeprefix("verse"))
            mapped = mapped_verse(book, chapter, verse)
            actual = translations(sentence)

            expected_english = aligned_kjv(
                book, chapter, verse, kjv[(book, chapter, mapped)]
            )
            if actual.get("eng") != expected_english:
                raise SystemExit(f"KJV mismatch for {book} {chapter}:{verse}")
            english_checked += 1

            key = (book, chapter, verse)
            if key in OMITTED:
                if "cmn" in actual:
                    raise SystemExit(f"Unexpected CUV translation for omitted verse {key}")
                omitted += 1
                continue
            expected_mandarin = aligned_cuv(
                book, chapter, verse, cuv[book][(chapter, mapped)]
            )
            if actual.get("cmn") != expected_mandarin:
                raise SystemExit(f"CUV mismatch for {book} {chapter}:{verse}")
            mandarin_checked += 1

    print(
        f"English coverage: {english_checked} aligned KJV tiers from "
        "1,950 reference units."
    )
    print(
        f"Mandarin coverage: {mandarin_checked} aligned CUV tiers; "
        f"{omitted} documented edition omissions."
    )


if __name__ == "__main__":
    main()
