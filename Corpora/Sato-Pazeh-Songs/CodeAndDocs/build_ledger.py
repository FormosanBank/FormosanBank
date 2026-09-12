#!/usr/bin/env python3
"""Build the complete source ledger from reviewed rows and excluded blocks."""

from __future__ import annotations

import csv
from collections import defaultdict

from corpus_config import (
    BLOCKS_CSV,
    LEDGER_CSV,
    REVIEWED_CSV,
    relative_final_path,
    sentence_id,
    source_locator,
)


PRINTED_TO_PDF = {str(page): page - 115 for page in range(116, 127)}
FIELDS = [
    "pdf_page",
    "printed_page",
    "source_locator",
    "page_entry_record",
    "target_text",
    "translation_gloss_segmentation",
    "method",
    "confidence_review_note",
    "included",
    "exclusion_reason",
    "final_xml_path",
    "final_s_id",
]


def read_csv(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    by_pdf_page: dict[int, list[dict[str, str]]] = defaultdict(list)

    for block in read_csv(BLOCKS_CSV):
        pdf_page = int(block["pdf_page"])
        by_pdf_page[pdf_page].append(
            {
                "pdf_page": str(pdf_page),
                "printed_page": block["printed_page"],
                "source_locator": block["source_locator"],
                "page_entry_record": block["block_type"],
                "target_text": "",
                "translation_gloss_segmentation": block["content_summary"],
                "method": "manual visual inventory of rendered scan",
                "confidence_review_note": f"high; {block['review_note']}",
                "included": "false",
                "exclusion_reason": block["exclusion_reason"],
                "final_xml_path": "",
                "final_s_id": "",
            }
        )

    for row in read_csv(REVIEWED_CSV):
        sequence = int(row["sequence"])
        pdf_page = PRINTED_TO_PDF[row["page"]]
        text_key = row["text_key"]
        by_pdf_page[pdf_page].append(
            {
                "pdf_page": str(pdf_page),
                "printed_page": row["page"],
                "source_locator": source_locator(row),
                "page_entry_record": f"{text_key} sentence {sequence}",
                "target_text": row["form_original"],
                "translation_gloss_segmentation": row["translation_jpn"],
                "method": "manual transcription from scan; OCR used only as a diagnostic",
                "confidence_review_note": f"high; {row['review_note']}",
                "included": "true",
                "exclusion_reason": "",
                "final_xml_path": relative_final_path(text_key),
                "final_s_id": sentence_id(text_key, sequence),
            }
        )

    rows = [row for page in range(1, 15) for row in by_pdf_page[page]]
    LEDGER_CSV.parent.mkdir(parents=True, exist_ok=True)
    with LEDGER_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    included = sum(row["included"] == "true" for row in rows)
    excluded = sum(row["included"] == "false" for row in rows)
    covered = sorted({int(row["pdf_page"]) for row in rows})
    print(f"ledger={LEDGER_CSV}")
    print(f"included={included} excluded_blocks={excluded} pdf_pages={covered}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
