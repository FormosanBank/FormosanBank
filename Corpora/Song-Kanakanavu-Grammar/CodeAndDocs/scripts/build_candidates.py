#!/usr/bin/env python3
"""Build page inventory and conservative labeled-example candidates from official text XML."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


LABEL_RE = re.compile(r"^[（(](\d+(?:[-�]\d+[a-z]?)?)[）)]\s*(.*)$", re.IGNORECASE)
CJK_RE = re.compile(r"[\u3400-\u9fff]")
TRANSL_END_RE = re.compile(r"[。！？?]$")
LATIN_RE = re.compile(r"[A-Za-zʉáíú’']")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-jsonl", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    parser.add_argument("--pages", type=Path, required=True)
    args = parser.parse_args()

    pages = [json.loads(line) for line in args.text_jsonl.read_text(encoding="utf-8").splitlines()]
    candidates: list[dict[str, object]] = []
    inventory: list[dict[str, object]] = []
    for page in pages:
        ordered = sorted(enumerate(page["rows"]), key=lambda item: (item[1]["y"], item[0]))
        rows = [row for _, row in ordered]
        page_candidates = []
        for index, row in enumerate(rows):
            text = " ".join(row["text"].split())
            match = LABEL_RE.match(text)
            if not match:
                continue
            label = match.group(1).replace("�", "-")
            if "-" not in label and not (187 <= page["page"] <= 192 or page["page"] >= 221):
                continue
            if "-" not in label and text.startswith("("):
                # Narrative overview paragraphs repeat many sentences in a
                # compact ASCII-numbered stream; use the fullwidth-numbered
                # interlinear presentation below them instead.
                continue
            target = match.group(2).rstrip("� ")
            if re.search(r"[（(]\d+[）)]", target):
                # Narrative overview lines concatenate many numbered sentences;
                # retain the later interlinear occurrence of each sentence instead.
                continue
            if not target or "-" not in label:
                target_parts = [target] if target else []
                for later in rows[index + 1 :]:
                    later_text = " ".join(later["text"].split())
                    if LABEL_RE.match(later_text):
                        break
                    if CJK_RE.search(later_text):
                        if TRANSL_END_RE.search(later_text):
                            break
                        continue
                    if LATIN_RE.search(later_text):
                        target_parts.append(later_text.rstrip("� "))
                target = " ".join(target_parts)
            translation = ""
            for later in rows[index + 1 :]:
                later_text = " ".join(later["text"].split())
                if LABEL_RE.match(later_text):
                    break
                if CJK_RE.search(later_text) and TRANSL_END_RE.search(later_text):
                    translation = later_text
                    break
            page_candidates.append(
                {
                    "source_locator": f"page-{page['page']:03d}",
                    "reader_page": page["page"],
                    "example_label": label,
                    "target_candidate": target,
                    "translation_candidate": translation,
                    "method": "Official positioned text XML; must be checked against page image",
                    "review_status": "UNREVIEWED",
                    "review_note": "",
                }
            )
        candidates.extend(page_candidates)
        inventory.append(
            {
                "source_locator": f"page-{page['page']:03d}",
                "reader_page": page["page"],
                "candidate_count": len(page_candidates),
                "coverage_status": "UNREVIEWED",
                "review_note": "Inspect official page image and reconcile all examples and non-numbered sentence tables",
            }
        )

    args.candidates.parent.mkdir(parents=True, exist_ok=True)
    with args.candidates.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidates[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(candidates)
    with args.pages.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(inventory[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(inventory)
    print(f"Wrote {len(candidates)} labeled candidates across {len(inventory)} pages.")


if __name__ == "__main__":
    main()
