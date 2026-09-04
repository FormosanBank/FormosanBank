#!/usr/bin/env python3
"""Verify that all nine issue findings have exact source-backed dispositions."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "data/formosanbank_audit/issue_1_review.tsv"
EXPECTED = {
    "S493_1": "separated_free_translation_from_word_gloss",
    "S491_1": "separated_free_translation_from_word_gloss",
    "S481_1": "separated_free_translation_from_word_gloss",
    "S413_1": "separated_free_translation_from_word_gloss",
    "S412_1": "separated_free_translation_from_word_gloss",
    "S305_1": "retained_source_code_switching",
    "S169_1": "restored_omitted_translation_line",
    "S159_1": "moved_source_analysis_to_notes",
    "S62_1": "restored_omitted_translation_lines",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    with REVIEW.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    observed = {row["s_id"]: row["resolution"] for row in rows}
    if len(rows) != 9 or observed != EXPECTED:
        raise SystemExit(f"Issue review changed: {observed}")
    if any(not row["source_url"] or not row["evidence"] for row in rows):
        raise SystemExit("Issue review contains a row without source evidence")
    print("PASS: 9/9 issue findings have source-backed dispositions; 0 unresolved")


if __name__ == "__main__":
    main()
