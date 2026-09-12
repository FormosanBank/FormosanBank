#!/usr/bin/env python3
"""Fail closed unless the Yedda handoff matches its source and manifest."""

from __future__ import annotations

import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/source_snapshot/Paiwan_Yedda_Blog.xml"
XML = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
AUDIT = ROOT / "data/formosanbank_audit"
EXPECTED_SOURCE_SHA256 = (
    "e18d0aa67893278cb7754e9725e68a81075760961391b3db941eca7d873ddba6"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def main() -> None:
    manifest = json.loads((AUDIT / "manifest.json").read_text(encoding="utf-8"))
    root = ET.parse(XML).getroot()
    sentences = root.findall("S")
    sentence_ids = [sentence.get("id", "") for sentence in sentences]
    coverage = read_tsv(AUDIT / "source_coverage.tsv")
    issue_rows = read_tsv(AUDIT / "issue_1_review.tsv")
    variants = read_tsv(AUDIT / "source_variant_review.tsv")
    translations = read_tsv(AUDIT / "source_translation_review.tsv")
    word_translations = read_tsv(AUDIT / "source_word_translation_review.tsv")
    current_counts = {
        tag: len(root.findall(f".//{tag}"))
        for tag in ("S", "W", "M", "FORM", "PHON", "TRANSL", "AUDIO")
    }
    checks = {
        "source_hash": sha256(SOURCE) == EXPECTED_SOURCE_SHA256,
        "xml_hash": sha256(XML) == manifest["xml_sha256"],
        "counts": current_counts == manifest["counts"],
        "sentence_count": len(sentences) == 671,
        "unique_sentence_ids": len(set(sentence_ids)) == 671 and "" not in sentence_ids,
        "source_coverage": len(coverage) == 668,
        "no_source_omissions": all(row["status"] != "omitted" for row in coverage),
        "three_expansions": sum(
            row["status"] == "expanded_source_alternatives" for row in coverage
        )
        == 3,
        "issue_review": len(issue_rows) == 9,
        "variant_review": len(variants) == 3,
        "translation_review": len(translations) == 24,
        "word_translation_review": len(word_translations) == 41,
        "tier_shape": current_counts["FORM"] == current_counts["PHON"],
        "no_final_xml": not (ROOT.parent / "Final_XML").exists(),
    }
    errors = [name for name, passed in checks.items() if not passed]
    result = {"checks": checks, "counts": current_counts, "errors": errors}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
