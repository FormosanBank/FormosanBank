#!/usr/bin/env python3
"""Finalize the scan-reviewed chapter 3-4 source inventory.

The input is the 353-row geometry inventory produced from the private scan with
Apple Vision OCR.  This script records the direct scan corrections and the
include/exclude decision for every marked block.  The generated TSV is the
earliest redistributable authoritative layer used by ``build_xml.py``.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "CodeAndDocs" / "source_inventory.tsv"


# The scan-review decisions are data, kept in CodeAndDocs/ beside this script
# (POL-039).  Each table is keyed by the 0-based row of the 353-row geometry
# inventory; ``record_id`` is the R-number that row becomes (row + 1).
#
# inventory_not_examples.tsv: rows that are headings, affix inventories,
#   tables, OCR page artifacts, or incomplete records rather than translated
#   interlinear examples.
# inventory_overrides.tsv: one row per replaced field.  A few real examples
#   cross page boundaries or share an explicitly stated translation with
#   another source example; they are restored from direct scan review rather
#   than inferred from surrounding prose.
# ocr_form_fixes.tsv: OCR misreadings in example lines, applied in file order.
NOT_EXAMPLES_TSV = ROOT / "CodeAndDocs" / "inventory_not_examples.tsv"
OVERRIDES_TSV = ROOT / "CodeAndDocs" / "inventory_overrides.tsv"
OCR_FORM_FIXES_TSV = ROOT / "CodeAndDocs" / "ocr_form_fixes.tsv"


def _read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def load_not_examples() -> set[int]:
    return {int(row["geometry_row"]) for row in _read_tsv(NOT_EXAMPLES_TSV)}


def load_overrides() -> dict[int, dict[str, str]]:
    overrides: dict[int, dict[str, str]] = {}
    for row in _read_tsv(OVERRIDES_TSV):
        overrides.setdefault(int(row["geometry_row"]), {})[row["field"]] = row["value"]
    return overrides


def load_ocr_form_fixes() -> dict[str, str]:
    return {row["ocr"]: row["corrected"] for row in _read_tsv(OCR_FORM_FIXES_TSV)}


NOT_EXAMPLES = load_not_examples()
OVERRIDES = load_overrides()
OCR_FORM_FIXES = load_ocr_form_fixes()


def clean_form(text: str) -> str:
    for old, new in OCR_FORM_FIXES.items():
        text = text.replace(old, new)
    # The OCR wraps gloss lines in these, so they are artefacts in a form line.
    text = text.replace("【", "").replace("】", "").replace("[", "").replace("]", "")
    # Braces are NOT an artefact: Chang uses them to mark an alternation whose
    # scope spans more than one word ({laqi gaga/temi} = `laqi gaga` ~ `temi`).
    # Deleting them flattened the book's one such example into a single-word
    # alternation and published `laqi` in both readings. build_xml parses them.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_prose(text: str) -> str:
    text = text.strip().strip("'‘’\"“”『』「」 ")
    text = (
        text.replace(".", "。").replace(",", "，").replace("(", "（").replace(")", "）")
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_unacceptable(form: str) -> bool:
    return bool(re.match(r"^\s*[?*]", form))


def exclusion_reason(index: int, row: dict[str, str]) -> str:
    if index in NOT_EXAMPLES:
        return "not_interlinear_example"
    if is_unacceptable(row["form"]):
        if row["form"].lstrip().startswith("*"):
            return "ungrammatical_source"
        return "marginal_source"
    if not row["form"] or not row["gloss"]:
        return "incomplete_source_block"
    if not row["translation"]:
        return "missing_source_translation"
    return ""


def normalize_pairs(row: dict[str, str]) -> list[list[str]]:
    try:
        pairs = json.loads(row.get("word_gloss_json", "") or "[]")
    except json.JSONDecodeError:
        pairs = []
    form_words = row["form"].split()
    glosses = row["gloss"].split()
    if len(form_words) == len(glosses):
        return [[word, gloss] for word, gloss in zip(form_words, glosses, strict=True)]
    if len(pairs) == len(form_words):
        return [
            [word, str(pair[1])] for word, pair in zip(form_words, pairs, strict=True)
        ]
    return []


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("geometry_inventory", type=Path)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    with args.geometry_inventory.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 353:
        raise SystemExit(f"Expected 353 geometry rows, found {len(rows)}")

    output: list[dict[str, str]] = []
    alignment_errors: list[str] = []
    for index, source in enumerate(rows):
        row = dict(source)
        row.update(OVERRIDES.get(index, {}))
        row["form"] = clean_form(row["form"])
        row["gloss"] = re.sub(r"\s+", " ", row["gloss"].strip())
        row["translation"] = clean_prose(row["translation"])
        reason = exclusion_reason(index, row)
        decision = "exclude" if reason else "include"
        pairs = normalize_pairs(row)
        if decision == "include" and len(pairs) != len(row["form"].split()):
            alignment_errors.append(
                f"row {index} PDF {row['pdf_page']} {row['marker']}: "
                f"{len(row['form'].split())} words / {len(pairs)} aligned glosses"
            )
        output.append(
            {
                "record_id": f"R{index + 1:03d}",
                "pdf_page": row["pdf_page"],
                "printed_page": row["printed_page"],
                "marker": row["marker"],
                "source_locator": (
                    f"printed p. {row['printed_page']} / PDF p. {row['pdf_page']} / example {row['marker']}"
                ),
                "form": row["form"],
                "gloss": row["gloss"],
                "translation": row["translation"],
                "word_gloss_json": json.dumps(pairs, ensure_ascii=False),
                "decision": decision,
                "exclusion_reason": reason,
                "review_notes": row.get("review_notes", ""),
                "provenance": "Apple Vision OCR plus direct scan review",
            }
        )

    if alignment_errors:
        raise SystemExit("\n".join(alignment_errors))

    fields = list(output[0])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)

    included = sum(row["decision"] == "include" for row in output)
    excluded = len(output) - included
    print(f"Wrote {args.output}: {included} included, {excluded} excluded")


if __name__ == "__main__":
    main()
