#!/usr/bin/env python3
"""Extract the language-sorted basic lexicon from the reviewed source text."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "raw_data" / "official_text.jsonl"
OUTPUT = ROOT / "intermediate" / "dictionary_ledger.csv"
FIRST_PAGE = 193
LAST_PAGE = 206
REVERSE_FIRST_PAGE = 207
REVERSE_LAST_PAGE = 220
LATIN_RE = re.compile(r"[A-Za-zʉɄáíúÁÍÚ’']")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
SOURCE_LANGUAGE_NOTE_RE = re.compile(r"[（(](?:日語|借詞)[）)]")
BOUND_CITATION_REASON = (
    "Source prints a bound citation form with a trailing hyphen and supplies "
    "no unattached surface; entry excluded from the published XML."
)
FORM_CORRECTIONS = {
    ("aaka", "壞的；不好的"): "aka",
    ("iiávatu", "來"): "iávatu",
    ("kka-", "製作；做"): "ka-",
    ("makacap capʉ", "拍擊；擊掌"): "makacápacapʉ",
    ("mmaan", "十（數數）"): "maan",
    ("marikʉc kʉcʉ", "踩踏"): "marikʉcʉkʉcʉ",
    ("mavʉr vʉrʉ", "晃動；搖動（自然）"): "mavʉrʉvʉrʉ",
    ("nna-", "已故"): "na-",
    ("ngngaca’ʉ", "根部；根源"): "ngaca’ʉ",
    ("rramisi", "根（植物）"): "ramisi",
    ("sas patʉ", "四（數人）"): "sasápatʉ",
    ("s patʉ", "四（數數）"): "sápatʉ",
    ("ssaa", "或"): "saa",
    ("tangʉr ngʉrʉ", "木耳"): "tangʉrʉngʉrʉ",
    ("ttaa", "走（催促）"): "taa",
    ("tumatak takʉ", "砍除；砍草；鋤草"): "tumatakʉtakʉ",
    ("uuaru", "八（數物）"): "uaru",
    ("us patʉ", "四（數物）"): "usápatʉ",
    ("vʉr ngana", "深夜"): "vʉrʉngana",
    ("vvai", "手足"): "vai",
    ("’’acecu", "去了；走了"): "’acecu",
    ("ʉʉcʉ", "雲"): "ʉcʉ",
}


@dataclass
class Cell:
    fragments: list[dict[str, object]]

    @property
    def top(self) -> float:
        return min(float(row["y"]) for row in self.fragments)

    @property
    def bottom(self) -> float:
        return max(float(row["y"]) + float(row["h"]) for row in self.fragments)

    @property
    def center(self) -> float:
        return (self.top + self.bottom) / 2

    @property
    def text(self) -> str:
        return " ".join(str(row["text"]).strip() for row in self.fragments).strip()


def read_pages() -> dict[int, dict[str, object]]:
    records = [
        json.loads(line)
        for line in SOURCE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {int(record["page"]): record for record in records}


def group_form_cells(
    forms: list[dict[str, object]], translations: list[dict[str, object]]
) -> list[Cell]:
    cells: list[Cell] = []
    for row in sorted(forms, key=lambda item: (int(item["y"]), int(item["x"]))):
        if not cells:
            cells.append(Cell([row]))
            continue

        previous = cells[-1]
        previous_row = previous.fragments[-1]
        gap = int(row["y"]) - int(previous_row["y"])
        previous_text = str(previous_row["text"]).rstrip()
        previous_center = int(previous_row["y"]) + int(previous_row["h"]) / 2
        current_center = int(row["y"]) + int(row["h"]) / 2
        previous_matches = [
            item
            for item in translations
            if abs(int(item["y"]) + int(item["h"]) / 2 - previous_center) <= 5
        ]
        current_matches = [
            item
            for item in translations
            if abs(int(item["y"]) + int(item["h"]) / 2 - current_center) <= 5
        ]
        distinct_translation_lines = bool(previous_matches and current_matches) and not {
            int(item["y"]) for item in previous_matches
        }.intersection(int(item["y"]) for item in current_matches)

        continuation = (
            gap <= 9
            and (
                not distinct_translation_lines
                or previous_text.endswith(("/", ";"))
            )
            and (
                previous_text.endswith(("/", ";"))
                or not current_matches
                or previous.bottom >= int(row["y"])
            )
        )
        if continuation:
            previous.fragments.append(row)
        else:
            cells.append(Cell([row]))
    return cells


def assign_translations(
    cells: list[Cell], translations: list[dict[str, object]]
) -> list[str]:
    assigned: list[list[dict[str, object]]] = [[] for _ in cells]
    for row in translations:
        center = int(row["y"]) + int(row["h"]) / 2
        index = min(range(len(cells)), key=lambda item: abs(cells[item].center - center))
        assigned[index].append(row)
    return [
        "".join(
            str(row["text"]).strip()
            for row in sorted(group, key=lambda item: (int(item["y"]), int(item["x"])))
        )
        for group in assigned
    ]


def clean_form(text: str) -> str:
    text = SOURCE_LANGUAGE_NOTE_RE.sub("", text)
    return re.sub(r"\s+([/;])\s*", r" \1 ", " ".join(text.split())).strip()


def split_fused_rows(
    rows: list[dict[str, object]],
    form_left: int,
    translation_left: int,
) -> list[dict[str, object]]:
    """Recover form/translation pairs fused by the positioned-text layer."""
    normalized: list[dict[str, object]] = []
    for row in rows:
        text = str(row["text"]).strip()
        if not (form_left - 4 <= int(row["x"]) < form_left + 52):
            normalized.append(row)
            continue

        without_source_note = SOURCE_LANGUAGE_NOTE_RE.sub("", text).strip()
        if without_source_note == "minmana（已發生）何時":
            normalized.extend(
                [
                    {**row, "y": int(row["y"]) + 8, "text": "minmana"},
                    {
                        **row,
                        "x": translation_left,
                        "y": int(row["y"]) + 4,
                        "text": "何時（已發生）",
                    },
                ]
            )
            continue

        first_cjk = CJK_RE.search(without_source_note)
        if (
            translation_left > form_left
            and first_cjk
            and LATIN_RE.search(without_source_note[: first_cjk.start()])
        ):
            form = without_source_note[: first_cjk.start()].strip()
            translation = without_source_note[first_cjk.start() :].strip()
            normalized.extend(
                [
                    {**row, "text": form},
                    {**row, "x": translation_left, "text": translation},
                ]
            )
        else:
            normalized.append({**row, "text": without_source_note})
    return normalized


def extract_section(
    pages: dict[int, dict[str, object]],
    first_page: int,
    last_page: int,
    columns: tuple[tuple[int, int], tuple[int, int]],
) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for page_number in range(first_page, last_page + 1):
        rows = list(pages[page_number]["rows"])
        for column, (form_left, translation_left) in enumerate(columns, start=1):
            column_rows = split_fused_rows(rows, form_left, translation_left)
            forms = [
                row
                for row in column_rows
                if form_left - 4 <= int(row["x"]) < form_left + 52
                and int(row["y"]) < 397
                and bool(
                    LATIN_RE.search(
                        SOURCE_LANGUAGE_NOTE_RE.sub("", str(row["text"]).strip())
                    )
                )
                and not CJK_RE.search(
                    SOURCE_LANGUAGE_NOTE_RE.sub("", str(row["text"]).strip())
                )
                and str(row["text"]).strip() != "族語"
            ]
            translations = [
                row
                for row in column_rows
                if translation_left - 4 <= int(row["x"]) < translation_left + 48
                and int(row["y"]) < 397
                and bool(CJK_RE.search(str(row["text"]).strip()))
                and str(row["text"]).strip() != "中文"
            ]
            translation_centers = [
                int(row["y"]) + int(row["h"]) / 2 for row in translations
            ]
            forms = [
                row
                for row in forms
                if len(SOURCE_LANGUAGE_NOTE_RE.sub("", str(row["text"])).strip()) != 1
                or any(
                    abs(
                        int(row["y"])
                        + int(row["h"]) / 2
                        - translation_center
                    )
                    <= 5
                    for translation_center in translation_centers
                )
            ]
            cells = group_form_cells(forms, translations)
            glosses = assign_translations(cells, translations)
            for cell, gloss in zip(cells, glosses, strict=True):
                form = clean_form(cell.text)
                if form and gloss:
                    entries.append(
                        {
                            "reader_page": str(page_number),
                            "column": str(column),
                            "form": form,
                            "translation": gloss,
                        }
                    )
    return entries


def u_skeleton(text: str) -> str:
    return " ".join(text.lower().replace("ʉ", "u").replace("Ʉ", "u").split())


def merge_barred_vowels(primary: str, duplicate: str) -> str:
    if u_skeleton(primary) != u_skeleton(duplicate) or len(primary) != len(duplicate):
        return primary
    return "".join(
        "ʉ" if left.lower() in {"u", "ʉ"} and right.lower() == "ʉ" else left
        for left, right in zip(primary, duplicate, strict=True)
    )


def translations_overlap(primary: str, duplicate: str) -> bool:
    splitter = re.compile(r"[；、，。／/（）()]")
    primary_terms = {term for term in splitter.split(primary) if term}
    duplicate_terms = {term for term in splitter.split(duplicate) if term}
    return any(
        left in right or right in left
        for left in primary_terms
        for right in duplicate_terms
    )


def extract_entries() -> list[dict[str, str]]:
    pages = read_pages()
    primary = extract_section(
        pages,
        FIRST_PAGE,
        LAST_PAGE,
        ((48, 102), (166, 220)),
    )
    reverse = extract_section(
        pages,
        REVERSE_FIRST_PAGE,
        REVERSE_LAST_PAGE,
        ((102, 48), (219, 165)),
    )
    reverse_by_skeleton: dict[str, list[dict[str, str]]] = {}
    for entry in reverse:
        reverse_by_skeleton.setdefault(u_skeleton(entry["form"]), []).append(entry)

    entries: list[dict[str, str]] = []
    for index, entry in enumerate(primary, start=1):
        duplicates = [
            duplicate
            for duplicate in reverse_by_skeleton.get(u_skeleton(entry["form"]), [])
            if translations_overlap(entry["translation"], duplicate["translation"])
        ]
        corrected = entry["form"]
        for duplicate in duplicates:
            corrected = merge_barred_vowels(corrected, duplicate["form"])
        corrected = FORM_CORRECTIONS.get(
            (corrected, entry["translation"]),
            corrected,
        )
        bound_citation = corrected.endswith("-")
        entries.append(
            {
                "entry_id": f"song-2018-kanakanavu-dictionary-{index:04d}",
                **entry,
                "form": corrected,
                "method": (
                    "Official Appendix 2A positioned text; barred-vowel forms "
                    "cross-checked against duplicate Appendix 2B entry"
                    if duplicates
                    else "Official positioned text; language-sorted Appendix 2A"
                ),
                "included": "no" if bound_citation else "yes",
                "exclusion_reason": BOUND_CITATION_REASON if bound_citation else "",
            }
        )
    return entries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    entries = extract_entries()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(entries[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(entries)
    print(f"Wrote {len(entries)} dictionary entries to {args.output}")


if __name__ == "__main__":
    main()
