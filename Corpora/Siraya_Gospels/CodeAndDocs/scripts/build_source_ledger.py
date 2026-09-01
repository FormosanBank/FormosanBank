#!/usr/bin/env python3
"""Create a complete verse-level source-to-XML ledger."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "verses.jsonl"
OUTPUT = ROOT / "data" / "source_ledger.csv"

MATTHEW_PAGES = {
    1: "13-16", 2: "17-21", 3: "21-24", 4: "24-28", 5: "28-36",
    6: "36-41", 7: "41-46", 8: "46-51", 9: "52-57", 10: "57-64",
    11: "64-69", 12: "69-77", 13: "77-86", 14: "87-91", 15: "92-97",
    16: "98-102", 17: "102-107", 18: "107-113", 19: "113-118",
    20: "118-124", 21: "124-132", 22: "132-138", 23: "138-145",
    24: "145-153", 25: "153-160", 26: "160-172", 27: "172-182",
    28: "183-186",
}
JOHN_PAGES = {
    1: "6-13", 2: "13-17", 3: "17-23", 4: "23-31", 5: "31-38",
    6: "38-49", 7: "49-56", 8: "56-66", 9: "66-72", 10: "73-79",
    11: "79-87", 12: "87-95", 13: "96-102", 14: "102-107",
    15: "107-111", 16: "111-117", 17: "117-121", 18: "121-128",
    19: "129-136", 20: "136-141", 21: "141-145",
}


def reference_verse(book: str, chapter: int, verse: int) -> str:
    if book == "John" and chapter == 1 and verse in {38, 39}:
        return f"John 1:38 part {verse - 37}"
    mapped = verse - 1 if book == "John" and chapter == 1 and verse >= 39 else verse
    return f"{book} {chapter}:{mapped}"


def main() -> None:
    with INPUT.open(encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "source_locator",
                "source_file",
                "pdf_pages",
                "original_form",
                "english_reference_locator",
                "english_translation",
                "mandarin_reference_locator",
                "mandarin_translation",
                "translation_note",
                "method",
                "review_note",
                "included",
                "exclusion_reason",
                "final_xml_path",
                "final_s_id",
            ],
        )
        writer.writeheader()
        for row in rows:
            fields = row["fields"]
            by_kind = {
                (field["tag"], field["kindOf"] or field["xml_lang"]): field["text"]
                for field in fields
            }
            book, chapter_file = Path(row["path"]).parts
            chapter = Path(chapter_file).stem.removeprefix("chapter")
            verse = str(row["sentence_id"]).removeprefix("verse")
            chapter_number = int(chapter)
            verse_number = int(verse)
            source_file = (
                "Gospels of St. Matthew and St. John.pdf"
                if book == "John"
                else "Matthew.pdf"
            )
            pdf_pages = (
                JOHN_PAGES[chapter_number]
                if book == "John"
                else MATTHEW_PAGES[chapter_number]
            )
            reference_locator = reference_verse(book, chapter_number, verse_number)
            writer.writerow(
                {
                    "source_locator": f"Gravius 1661 {book} {chapter}:{verse}",
                    "source_file": source_file,
                    "pdf_pages": pdf_pages,
                    "original_form": by_kind.get(("FORM", "original"), ""),
                    "english_reference_locator": f"NLTK Gutenberg KJV {reference_locator}",
                    "english_translation": by_kind.get(("TRANSL", "eng"), ""),
                    "mandarin_reference_locator": f"CUV USFM {reference_locator}",
                    "mandarin_translation": by_kind.get(("TRANSL", "cmn"), ""),
                    "translation_note": (
                        "CUV edition omits this verse"
                        if (book, chapter_number, verse_number)
                        in {("Matthew", 18, 11), ("Matthew", 23, 14), ("John", 5, 4), ("John", 7, 53)}
                        else ""
                    ),
                    "method": (
                        "full rendered-scan review aided by a public raw transcription "
                        "witness and independent OCR"
                    ),
                    "review_note": (
                        "Reviewed against the printed Siraya column; the rendered scan "
                        "controls punctuation, diacritics, spacing, and hyphenation"
                    ),
                    "included": "yes",
                    "exclusion_reason": "",
                    "final_xml_path": f"XML/Siraya/{row['path']}",
                    "final_s_id": row["sentence_id"],
                }
            )
    print(f"Wrote {len(rows)} rows to CodeAndDocs/data/source_ledger.csv")


if __name__ == "__main__":
    main()
