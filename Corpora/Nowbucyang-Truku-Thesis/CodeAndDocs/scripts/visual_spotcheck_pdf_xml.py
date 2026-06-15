#!/usr/bin/env python3
"""Create a source-screenshot to XML spotcheck report for high-risk examples."""

from __future__ import annotations

import csv
from pathlib import Path
import xml.etree.ElementTree as ET

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
XML_PATH = ROOT / "Final_XML/Truku/Hsu_Lowking_Truku_WordFormation_2008.xml"
OUT_DIR = ROOT / "data/processed/spotcheck_images"
REPORT_PATH = ROOT / "data/processed/pdf_xml_visual_spotcheck.md"


CASES = [
    {
        "name": "Slash options: example 6a",
        "page": 28,
        "crop": (110, 690, 760, 1015),
        "ids": [
            "HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E006A1",
        ],
        "expectation": "Source `hiya/laqi` and segmentation are preserved in original sentence/word FORM; sentence standard FORM is de-segmented and the source Mandarin free translation with slash is retained for manual QC.",
    },
    {
        "name": "Parentheses and Ch1 Ex11a",
        "page": 32,
        "crop": (120, 105, 770, 675),
        "ids": [
            "HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E011A",
            "HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E011E",
        ],
        "expectation": "Ch1 Ex11a is included. Parenthetical source text is not a blanket rejection reason; standard forms conservatively remove parenthetical material.",
    },
    {
        "name": "Page-break translation: example 26c source page",
        "page": 42,
        "crop": (120, 520, 760, 785),
        "ids": ["HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E026C"],
        "expectation": "The Truku/gloss lines appear at the bottom of page 42 and the free translation continues at the top of page 43.",
    },
    {
        "name": "Page-break translation: example 26c continuation",
        "page": 43,
        "crop": (150, 70, 680, 300),
        "ids": ["HSU_LOWKING_TRUKU_WORDFORMATION_2008_C01_E026C"],
        "expectation": "The top-of-page Mandarin line is used as the source free translation for example 26c.",
    },
    {
        "name": "Parenthesized affix: Ch4 Ex4c",
        "page": 127,
        "crop": (120, 500, 760, 760),
        "ids": ["HSU_LOWKING_TRUKU_WORDFORMATION_2008_C04_E004C"],
        "expectation": "Original sentence and word FORM values keep source morphology/segmentation; sentence standard FORM removes parenthetical morphology conservatively.",
    },
]


def xml_lang_attr(name: str) -> str:
    return f"{{http://www.w3.org/XML/1998/namespace}}{name}"


def element_texts(parent: ET.Element, tag: str) -> list[tuple[str, str]]:
    out = []
    for child in parent.findall(tag):
        lang = child.attrib.get(xml_lang_attr("lang"), "")
        kind = child.attrib.get("kindOf", "")
        label = lang or kind
        out.append((label, (child.text or "").strip()))
    return out


def crop_image(page: int, box: tuple[int, int, int, int], name: str) -> str:
    src = ROOT / f"data/raw/page_images/page_{page:04d}.png"
    img = Image.open(src)
    crop = img.crop(box)
    out = OUT_DIR / f"{name}.png"
    crop.save(out)
    return str(out.relative_to(ROOT))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    root = ET.parse(XML_PATH).getroot()
    by_id = {s.attrib["id"]: s for s in root.findall("S")}
    index = {}
    with (ROOT / "data/processed/xml_index.csv").open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            index[row["sentence_id"]] = row

    lines = [
        "# PDF/XML Visual Spotcheck",
        "",
        "This report compares cropped PDF page images against the final FormosanBank XML for high-risk examples raised during QC.",
        "",
    ]

    all_ok = True
    for idx, case in enumerate(CASES, start=1):
        image_path = crop_image(case["page"], case["crop"], f"spotcheck_{idx:02d}_page_{case['page']:04d}")
        lines.extend([
            f"## {case['name']}",
            "",
            f"- PDF page image crop: `{image_path}`",
            f"- Expected XML handling: {case['expectation']}",
            "",
        ])
        for sid in case["ids"]:
            s = by_id.get(sid)
            if s is None:
                all_ok = False
                lines.append(f"- `{sid}`: MISSING")
                continue
            forms = element_texts(s, "FORM")
            trans = element_texts(s, "TRANSL")
            ix = index.get(sid, {})
            lines.append(f"- `{sid}` page={ix.get('page_number_one_based', '')} ex={ix.get('example_number', '')}{ix.get('subexample_letter', '')}")
            for label, text in forms:
                lines.append(f"  - FORM {label}: `{text}`")
            for label, text in trans:
                lines.append(f"  - TRANSL {label}: `{text}`")
        lines.append("")

    lines.extend([
        "## Result",
        "",
        f"- Spotcheck status: {'PASS' if all_ok else 'FAIL'}",
        "- No OCR was used for these comparisons; page images are audit renderings of the source PDF.",
        "- Final XML remains under `Final_XML/Truku/`; screenshot crops and this report stay outside `Final_XML/`.",
        "",
    ])
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
