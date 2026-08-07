#!/usr/bin/env python3
"""Reconcile sentence vowels against the source's duplicate basic lexicon."""

from __future__ import annotations

import argparse
import csv
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_LEDGER = ROOT / "intermediate" / "source_ledger.csv"
DICTIONARY_LEDGER = ROOT / "intermediate" / "dictionary_ledger.csv"
WORD_RE = re.compile(r"[A-Za-zʉɄáíúÁÍÚ’']+")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def skeleton(text: str) -> str:
    text = text.lower().replace("’", "'").replace("ʉ", "u").replace("Ʉ", "u")
    return "".join(
        character
        for character in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(character)
    )


def dictionary_forms(rows: list[dict[str, str]]) -> dict[str, set[str]]:
    forms: dict[str, set[str]] = {}
    for row in rows:
        for variant in re.split(r"\s+[/;]\s+|[/;]\s*", row["form"]):
            variant = variant.strip()
            if not variant or " " in variant or any(mark in variant for mark in "()"):
                continue
            forms.setdefault(skeleton(variant), set()).add(variant)
    return forms


def corrected_word(word: str, forms: dict[str, set[str]]) -> str:
    candidates = forms.get(skeleton(word), set())
    if not candidates or any(len(candidate) != len(word) for candidate in candidates):
        return word

    result = list(word)
    for index, character in enumerate(word):
        if character.lower() != "u":
            continue
        candidate_characters = {candidate[index].lower() for candidate in candidates}
        if candidate_characters == {"ʉ"}:
            result[index] = "Ʉ" if character.isupper() else "ʉ"
    return "".join(result)


def corrected_text(text: str, forms: dict[str, set[str]]) -> str:
    return WORD_RE.sub(lambda match: corrected_word(match.group(), forms), text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    rows = read_csv(SOURCE_LEDGER)
    forms = dictionary_forms(read_csv(DICTIONARY_LEDGER))
    changes: list[tuple[str, str, str]] = []
    for row in rows:
        corrected = corrected_text(row["target_text"], forms)
        if corrected != row["target_text"]:
            changes.append((row["final_s_id"] or row["example_label"], row["target_text"], corrected))
            row["target_text"] = corrected

    for identifier, before, after in changes:
        print(f"{identifier}: {before} -> {after}")
    print(f"{len(changes)} sentence rows require barred-vowel reconciliation.")

    if args.apply and changes:
        with SOURCE_LEDGER.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {SOURCE_LEDGER}")
    if args.check and changes:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
