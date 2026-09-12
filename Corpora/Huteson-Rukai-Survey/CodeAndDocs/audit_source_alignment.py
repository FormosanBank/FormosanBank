#!/usr/bin/env python3
"""Compare generated source tiers with the reviewed Appendix B transcription."""
from __future__ import annotations

import argparse
import csv
import hashlib
import re
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "CodeAndDocs/manual_source_review.tsv"
MANIFEST = ROOT / "CodeAndDocs/source_manifest.md"


def manifest_pdf_sha256() -> str:
    """The source PDF's SHA-256, read from source_manifest.md.

    Kept in one place rather than hardcoded here as well (POL-039): the manifest
    is the human-readable record, this is its only consumer.
    """
    text = MANIFEST.read_text(encoding="utf-8")
    match = re.search(r"Source PDF:.*?SHA-256\s*`([0-9a-f]{64})`", text, re.S)
    if match is None:
        raise ValueError(f"no source PDF SHA-256 found in {MANIFEST}")
    return match.group(1)
# W ids whose source gloss column is blank. Such a W carries either no TRANSL at
# all, or an inferred gloss that MUST be marked with @notes (see build_xml.py
# INFERRED_GLOSSES) — an unmarked gloss here would be an invented one.
BLANKS = {
    "S_maga_007_W_002", "S_maga_011_W_004", "S_maga_013_W_004",
    "S_maga_014_W_004", "S_tona_009_W_004", "S_tona_010_W_004",
    "S_tona_014_W_002", "S_tona_014_W_005",
}
ALTERNATES = {
    ("Maolin", "4"): ["He started to cry.", "She started to cry."],
    ("Maolin", "6"): ["This person ran.", "This person is running."],
    ("Dona", "3"): ["He started to cry.", "She started to cry."],
    ("Dona", "5"): ["That old person ran.", "That old person is running."],
}


def audit() -> list[str]:
    errors = []
    with REVIEW.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    roots = [ET.parse(path).getroot() for path in sorted((ROOT / "XML").rglob("*.xml"))]
    sentences = {s.get("id"): s for root in roots for s in root.findall("S")}
    expected_ids = set()
    for row in rows:
        key = "maga" if row["dialect"] == "Maolin" else "tona"
        sid = f"S_{key}_{int(row['example_number']):03d}"
        expected_ids.add(sid)
        s = sentences.get(sid)
        if s is None:
            errors.append(f"Missing {sid}")
            continue
        if s.findtext("FORM[@kindOf='original']") != row["source_natural_form"]:
            errors.append(f"{sid}: natural FORM differs from reviewed source")
        expected_translations = list(ALTERNATES.get(
            (row["dialect"], row["example_number"]), [row["source_translation"]]
        ))
        if row["source_alternate_translation"]:
            expected_translations.append(row["source_alternate_translation"])
        translations = s.findall("TRANSL")
        if [t.text for t in translations] != expected_translations:
            errors.append(f"{sid}: free translations differ from source")
        if any(t.get("ver") != ("alt" if i else None) for i, t in enumerate(translations)):
            errors.append(f"{sid}: translation alternate metadata differs")
        expected_words = [w.strip('.,!?"“”') for w in row["source_form"].split()]
        words = s.findall("W")
        if [w.findtext("FORM[@kindOf='original']") for w in words] != expected_words:
            errors.append(f"{sid}: analyzed words differ from source")
        remaining = iter(row["source_gloss"].split())
        for w in words:
            original = w.find("TRANSL[@kindOf='original']")
            if original is None:
                original = w.find("TRANSL")
            if w.get("id") in BLANKS:
                if original is not None and not original.get("notes"):
                    errors.append(f"{w.get('id')}: blank source column carries an unmarked gloss")
                continue
            expected = next(remaining, None)
            if (original.text if original is not None else None) != expected:
                errors.append(f"{w.get('id')}: source gloss column differs")
        if next(remaining, None) is not None:
            errors.append(f"{sid}: unrepresented source gloss")
    if len(rows) != 29 or len(expected_ids) != 29 or set(sentences) != expected_ids:
        errors.append("Expected exactly the 29 reviewed Appendix B identities")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Optional original PDF identity check")
    args = parser.parse_args()
    errors = audit()
    if args.source and hashlib.sha256(args.source.read_bytes()).hexdigest() != manifest_pdf_sha256():
        errors.append("Source PDF does not match the reviewed 46-page edition")
    for error in errors:
        print(error)
    print(f"29 source records checked; {len(errors)} discrepancies. This is not a QC verdict.")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
