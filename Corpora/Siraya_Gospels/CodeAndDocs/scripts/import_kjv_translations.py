#!/usr/bin/env python3
"""Refresh aligned English translations from the checked-in KJV extract."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTERMEDIATE = ROOT / "data" / "verses.jsonl"
REFERENCE = ROOT / "reference_translations" / "eng-kjv-nltk-gutenberg.tsv"


def load_reference() -> dict[tuple[str, int, int], str]:
    with REFERENCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    reference = {
        (row["book"], int(row["chapter"]), int(row["verse"])): row["text"]
        for row in rows
    }
    if len(rows) != 1_950 or len(reference) != len(rows):
        raise SystemExit("expected 1,950 unique Matthew and John KJV reference rows")
    return reference


def mapped_verse(book: str, chapter: int, verse: int) -> int:
    return verse - 1 if book == "John" and chapter == 1 and verse >= 39 else verse


def aligned_text(book: str, chapter: int, verse: int, source: str) -> str:
    """Partition KJV John 1:38 across the source's two printed verse units."""

    if (book, chapter, verse) not in {("John", 1, 38), ("John", 1, 39)}:
        return source
    marker = "What seek ye?"
    if marker not in source:
        raise SystemExit("KJV John 1:38 no longer contains the reviewed split marker")
    prefix, suffix = source.split(marker, 1)
    return prefix.strip() if verse == 38 else f"{marker}{suffix}"


def main() -> None:
    reference = load_reference()
    rows = [
        json.loads(line)
        for line in INTERMEDIATE.read_text(encoding="utf-8").splitlines()
    ]
    changed = 0
    for row in rows:
        book, file_name = Path(row["path"]).parts
        chapter = int(Path(file_name).stem.removeprefix("chapter"))
        verse = int(str(row["sentence_id"]).removeprefix("verse"))
        source = reference[(book, chapter, mapped_verse(book, chapter, verse))]
        expected = aligned_text(book, chapter, verse, source)
        field = next(
            field
            for field in row["fields"]
            if field["tag"] == "TRANSL" and field["xml_lang"] == "eng"
        )
        changed += field["text"] != expected
        field["text"] = expected
    with INTERMEDIATE.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Refreshed 1,951 English tiers; changed {changed} aligned records.")


if __name__ == "__main__":
    main()
