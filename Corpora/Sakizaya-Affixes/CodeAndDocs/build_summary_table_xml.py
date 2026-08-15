#!/usr/bin/env python3
"""Account for all Sakizaya examples in the late thesis tables."""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from xml_tiers import add_form_pair, add_translation


ROOT = Path(__file__).resolve().parents[1]
XML_DIR = ROOT / "XML/szy"
XML_PATH = XML_DIR / "akiw_2012_sakizaya_affixes_summary_rows.xml"
INVENTORY_REPORT = ROOT / "CodeAndDocs/table_extraction_report.csv"
VISION_OCR_DIR = ROOT / "Private/cache/vision_ocr_350"
REPORT_CSV = ROOT / "CodeAndDocs/summary_table_extraction_report.csv"
SOURCE_DATA_DIR = ROOT / "CodeAndDocs/source_data"

XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("xml", XML_NS)


@dataclass
class SummaryRow:
    seq: int
    page: int
    form: str
    meaning_zho: str
    source_table: str = ""
    affix_form: str = ""
    affix_function_zho: str = ""
    base_form: str = ""
    base_meaning_zho: str = ""
    source_context: str = ""
    raw_ocr: str = ""
    retained_xml_id: str = ""
    note: str = "Page-image reviewed late summary/comparison table row."
    status: str = "include"

    @property
    def xml_id(self) -> str:
        return f"AKIW_SZY_2012_SUMMARY_ROW_{self.seq:03d}"


def parse_source_rows() -> list[SummaryRow]:
    path = SOURCE_DATA_DIR / "late_table_rows.csv"
    rows: list[SummaryRow] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for source_row in csv.DictReader(handle):
            rows.append(
                SummaryRow(
                    seq=int(source_row["seq"]),
                    page=int(source_row["page"]),
                    form=source_row["form"],
                    meaning_zho=source_row["meaning_zho"],
                    source_table=source_row["source_table"],
                    affix_form=source_row["affix_form"],
                    affix_function_zho=source_row["affix_function_zho"],
                    base_form=source_row["base_form"],
                    base_meaning_zho=source_row["base_meaning_zho"],
                )
            )
    expected = set(range(435, 548))
    observed = {row.seq for row in rows}
    if observed != expected or len(rows) != len(expected):
        raise RuntimeError("late_table_rows.csv must cover rows 435-547 exactly once")
    return sorted(rows, key=lambda row: row.seq)
def read_inventory_rows() -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    with INVENTORY_REPORT.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["status"] == "include":
                indexed.setdefault(row["form"], row)
    return indexed


def ocr_items(page: int) -> list[tuple[float, float, str]]:
    path = VISION_OCR_DIR / f"page-{page:03d}.vision.tsv"
    items: list[tuple[float, float, str]] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            text = re.sub(r"\s+", " ", row["text"]).strip()
            if text:
                items.append((float(row["top"]), float(row["left"]), text))
    return sorted(items)


def add_raw_ocr(rows: list[SummaryRow]) -> None:
    by_page: dict[int, list[SummaryRow]] = defaultdict(list)
    for row in rows:
        by_page[row.page].append(row)
    for page, page_rows in by_page.items():
        items = ocr_items(page)
        anchors: dict[int, float] = {}
        for row in page_rows:
            candidates = [
                top
                for top, _left, text in items
                if re.match(rf"^{row.seq}(?:\D|$)", text)
            ]
            if not candidates:
                raise RuntimeError(f"No OCR row-number anchor for late row {row.seq}")
            anchors[row.seq] = min(candidates)
        ordered = sorted(page_rows, key=lambda row: anchors[row.seq])
        for index, row in enumerate(ordered):
            y = anchors[row.seq]
            lower = (anchors[ordered[index - 1].seq] + y) / 2 if index else y - 110
            upper = (y + anchors[ordered[index + 1].seq]) / 2 if index + 1 < len(ordered) else y + 110
            row.raw_ocr = " | ".join(
                text for top, _left, text in items if lower <= top <= upper
            )
            if not row.raw_ocr:
                raise RuntimeError(f"No OCR evidence captured for late row {row.seq}")


def add_linguistic_fields(rows: list[SummaryRow]) -> None:
    inventory = read_inventory_rows()
    for row in rows:
        prior = inventory.get(row.form)
        if prior:
            row.affix_form = prior["affix_form"]
            row.affix_function_zho = prior["affix_function_zho"]
            row.base_form = prior["base_form"]
            row.base_meaning_zho = prior["base_meaning_zho"]
        elif not all(
            (
                row.affix_form,
                row.affix_function_zho,
                row.base_form,
                row.base_meaning_zho,
            )
        ):
            raise RuntimeError(
                f"Late row {row.seq} ({row.form}) lacks source linguistic fields"
            )
        row.source_context = (
            f"{row.affix_form} | {row.base_form} | {row.base_meaning_zho} | "
            f"{row.affix_function_zho}"
        )


def existing_rows_by_form() -> dict[str, list[tuple[str, str]]]:
    indexed: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for path in sorted(XML_DIR.glob("*.xml")):
        if path == XML_PATH:
            continue
        for sentence in ET.parse(path).getroot().findall("S"):
            original = sentence.find('./FORM[@kindOf="original"]')
            if original is None or not original.text:
                continue
            indexed[original.text].append((sentence.attrib["id"], path.name))
    return indexed


def classify_rows(rows: list[SummaryRow]) -> list[SummaryRow]:
    existing = existing_rows_by_form()
    for row in rows:
        matches = existing.get(row.form, [])
        if not matches:
            continue
        row.status = "excluded_exact_repeat"
        row.retained_xml_id, retained_file = matches[0]
        row.note = (
            "Page-image reviewed exact FORM repeat; the retained XML record receives "
            "this row's source meaning as a source-located alternate translation when distinct. "
            f"Retained in {retained_file}."
        )
    return rows


def add_alternate_translations(rows: list[SummaryRow]) -> None:
    trees = {
        path: ET.parse(path)
        for path in sorted(XML_DIR.glob("*.xml"))
        if path != XML_PATH
    }
    by_id: dict[str, tuple[Path, ET.Element]] = {}
    for path, tree in trees.items():
        for sentence in tree.getroot().findall("S"):
            by_id[sentence.attrib["id"]] = (path, sentence)

    changed: set[Path] = set()
    for row in rows:
        if row.status != "excluded_exact_repeat":
            continue
        retained = by_id.get(row.retained_xml_id)
        if retained is None:
            raise RuntimeError(f"Late row {row.seq} lacks retained XML {row.retained_xml_id}")
        path, sentence = retained
        existing_meanings = {
            transl.text or ""
            for transl in sentence.findall("TRANSL")
            if transl.attrib.get(f"{{{XML_NS}}}lang") == "zho"
        }
        if row.meaning_zho in existing_meanings:
            continue
        add_translation(
            sentence,
            row.meaning_zho,
            ver="alt",
            notes=f"Source: PDF page {row.page}; {row.source_table} row {row.seq}",
        )
        changed.add(path)

    for path in changed:
        tree = trees[path]
        ET.indent(tree.getroot(), space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)


def write_report(rows: list[SummaryRow]) -> None:
    fieldnames = [field for field in SummaryRow.__dataclass_fields__]
    with REPORT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, lineterminator="\n", fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.__dict__)


def write_xml(rows: list[SummaryRow]) -> None:
    root = ET.Element(
        "TEXT",
        {
            "id": "AKIW_SZY_2012_SAKIZAYA_AFFIXES_SUMMARY_ROWS",
            "citation": (
                "Akiw, Chung-Wen Hsu. 2012. The Study of Affixes in Sakizaya. "
                "Master's thesis, National Dong Hwa University."
            ),
            "BibTeX_citation": (
                "@mastersthesis{Akiw_2012_Sakizaya_Affixes, "
                "author = {Akiw, Chung-Wen Hsu}, "
                "title = {The Study of Affixes in Sakizaya}, "
                "school = {National Dong Hwa University}, "
                "year = {2012}}"
            ),
            "copyright": (
                "Author permission recorded on Basecamp card 8176965975; "
                "private development corpus pending maintainer port-in approval."
            ),
            f"{{{XML_NS}}}lang": "szy",
            "source": (
                "akiw_2012_sakizaya_affixes_scan.pdf; late summary/comparison table "
                "rows 435-547; SHA-256 "
                "fab787faf0e32cd087ba3dc222734132ad4213ca0804b8d5b32a318e66fbbbee"
            ),
            "glottocode": "saki1247",
            "dialect": "Sakizaya",
        },
    )
    for row in rows:
        if row.status != "include":
            continue
        sentence = ET.SubElement(
            root,
            "S",
            {
                "id": row.xml_id,
                "source": f"PDF page {row.page}; {row.source_table} row {row.seq}",
            },
        )
        add_form_pair(sentence, row.form)
        add_translation(sentence, row.meaning_zho)
        word = ET.SubElement(sentence, "W", {"id": f"{row.xml_id}W1"})
        add_form_pair(word, row.form)
        add_translation(word, row.meaning_zho, kind_of="original")

        affix = ET.SubElement(word, "M", {"id": f"{row.xml_id}W1M1"})
        add_form_pair(affix, row.affix_form)
        add_translation(affix, row.affix_function_zho, kind_of="original")

        root_morpheme = ET.SubElement(word, "M", {"id": f"{row.xml_id}W1M2"})
        add_form_pair(root_morpheme, row.base_form)
        add_translation(root_morpheme, row.base_meaning_zho, kind_of="original")

    XML_PATH.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root, space="    ")
    ET.ElementTree(root).write(XML_PATH, encoding="utf-8", xml_declaration=True)


def main() -> None:
    rows = parse_source_rows()
    add_linguistic_fields(rows)
    add_raw_ocr(rows)
    rows = classify_rows(rows)
    write_xml(rows)
    add_alternate_translations(rows)
    write_report(rows)
    print(f"Wrote {XML_PATH}")
    print(f"Wrote {REPORT_CSV}")
    print(f"Included {sum(row.status == 'include' for row in rows)} summary table rows")


if __name__ == "__main__":
    main()
