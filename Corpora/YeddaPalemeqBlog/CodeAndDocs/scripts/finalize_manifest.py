#!/usr/bin/env python3
"""Write a deterministic handoff manifest for the canonical corpus."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/source_snapshot/Paiwan_Yedda_Blog.xml"
XML = ROOT.parent / "XML/Paiwan/Paiwan_Yedda_Blog.xml"
AUDIT = ROOT / "data/formosanbank_audit"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    root = ET.parse(XML).getroot()
    counts = {
        tag: len(root.findall(f".//{tag}"))
        for tag in ("S", "W", "M", "FORM", "PHON", "TRANSL", "AUDIO")
    }
    audit_hashes = {
        path.name: sha256(path)
        for path in sorted(AUDIT.iterdir())
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "validator_commit": "7c2e0b692abed413bd9234d866cf9f0435c9651e",
        "source_snapshot_sha256": sha256(SOURCE),
        "xml_sha256": sha256(XML),
        "counts": counts,
        "source_records": 668,
        "source_records_omitted": 0,
        "alternative_expansions": 3,
        "issue_findings_reviewed": 9,
        "source_sentence_translations_repaired": 24,
        "source_word_translations_repaired": 41,
        "unresolved_findings": 0,
        "audit_sha256": audit_hashes,
    }
    (AUDIT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
