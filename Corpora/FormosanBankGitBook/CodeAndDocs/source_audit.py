#!/usr/bin/env python3
"""Read-only PDF, source-key, and final source-tier consistency checks."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

import pdfplumber
import process_raw

PDF_SHA256 = "5f7b960a9105f46a3216de6220664334b7d32763e8fc95d1519daadb4b84dd84"


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def audit(bank: Path, source_only: bool = False) -> dict[str, int]:
    code = Path(__file__).resolve().parent
    source = code / "raw_data" / "Paiwan"
    pdf = source / "Website PWN-v1.2.pdf"
    if hashlib.sha256(pdf.read_bytes()).hexdigest() != PDF_SHA256:
        raise ValueError("The reviewed source PDF has changed")
    columns: list[list[str]] = [[], [], []]
    with pdfplumber.open(pdf) as document:
        if len(document.pages) != 9:
            raise ValueError("The source must contain nine pages")
        for page in document.pages:
            for index, (left, right) in enumerate([(88, 223), (230, 365), (372, 507)]):
                text = page.crop((left, 70, right, 765)).extract_text(
                    x_tolerance=1, y_tolerance=3
                )
                if not text:
                    raise ValueError("Unreadable source column")
                columns[index].append(text)
    streams = [compact("\n".join(pages)) for pages in columns]
    cursors = [0, 0, 0]
    inventory = process_raw.source_inventory(source)
    matched = 0
    for stem, records in inventory.items():
        manifest = process_raw.SECTIONS[stem]
        if hashlib.sha256((source / f"{stem}.txt").read_bytes()).hexdigest() != manifest["sha256"]:
            raise ValueError(f"{stem}: reviewed source ledger changed")
        if len(records) != int(manifest["records"]):
            raise ValueError(f"{stem}: source coverage changed")
        for key, record in zip(process_raw.record_keys(stem, len(records)), records, strict=True):
            for index, value in enumerate((record.english, record.chinese, record.paiwan)):
                needle = compact(value)
                position = streams[index].find(needle, cursors[index])
                if position < 0:
                    raise ValueError(f"{stem}/{key['s_id']}: source field {index} absent or out of order")
                cursors[index] = position + len(needle)
                matched += 1
    if source_only:
        return {"pdf_pages": 9, "ordered_source_fields": matched, "records": matched // 3}

    sys.path.insert(0, str(bank))
    from QC.cleaning.clean_xml import clean_text, clean_trans

    count = 0
    for stem, records in inventory.items():
        root = ET.parse(code.parent / "XML" / "Paiwan" / f"{stem}.xml").getroot()
        sentences = root.findall("S")
        keys = process_raw.record_keys(stem, len(records))
        if [s.get("id") for s in sentences] != [row["s_id"] for row in keys]:
            raise ValueError(f"{stem}: source associations or order changed")
        if root.findall(".//W") or root.findall(".//M") or root.findall(".//AUDIO"):
            raise ValueError(f"{stem}: unsupported source tiers")
        for sentence, record in zip(sentences, records, strict=True):
            expected = (
                ("FORM[@kindOf='original']", clean_text(html.unescape(unicodedata.normalize("NFC", record.paiwan)), "pwn")),
                (f"TRANSL[@{process_raw.XML_LANG}='eng']", clean_trans(record.english, "eng")),
                (f"TRANSL[@{process_raw.XML_LANG}='zho']", clean_trans(record.chinese, "zho")),
            )
            for query, value in expected:
                if sentence.findtext(query) != value:
                    raise ValueError(f"{stem}/{sentence.get('id')}: {query} differs from cleaned source")
            for query in ["FORM[@kindOf='standard']", "PHON[@kindOf='original']", "PHON[@kindOf='standard']"]:
                if len(sentence.findall(query)) != 1:
                    raise ValueError(f"{stem}/{sentence.get('id')}: missing or duplicate derived tier")
            count += 1
    return {"pdf_pages": 9, "ordered_source_fields": matched, "records": count, "final_source_fields": 3 * count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formosanbank", type=Path, default=os.environ.get("FORMOSANBANK_ROOT"))
    parser.add_argument("--source-only", action="store_true")
    args = parser.parse_args()
    if not args.source_only and not args.formosanbank:
        parser.error("Set FORMOSANBANK_ROOT or --formosanbank for final-tier checks")
    print(json.dumps(audit(args.formosanbank, args.source_only), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
