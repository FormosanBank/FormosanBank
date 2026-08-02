#!/usr/bin/env python3
"""Build Formosan lexical XML from the visually reviewed source ledger."""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "CodeAndDocs" / "source_ledger.tsv"
REPORT_PATH = ROOT / "CodeAndDocs" / "extraction_report.csv"
SUMMARY_PATH = ROOT / "CodeAndDocs" / "extraction_summary.md"
XML_ROOT = ROOT / "Final_XML"
SOURCE_URL = "https://archive.org/details/elementsofcompar00lathrich"
BASECAMP_URL = (
    "https://app.basecamp.com/3340659/buckets/31258415/"
    "card_tables/cards/9999151808"
)

TEXT_CITATION = (
    "Latham, R. G. (1862). Elements of comparative philology. "
    "London: Walton and Maberly."
)
TEXT_BIBTEX = (
    "@book{latham1862comparativephilology, author = {Latham, Robert Gordon}, "
    "title = {Elements of comparative philology}, "
    "publisher = {Walton and Maberly}, address = {London}, year = {1862}}"
)
VALID_STATUSES = {"included", "omitted_blank_or_dash"}


@dataclass(frozen=True)
class LexicalEntry:
    printed_page: str
    pdf_page: str
    table: str
    language_code: str
    language_label: str
    dialect: str
    source_variety: str
    english: str
    form: str
    alternate_forms: tuple[str, ...]
    status: str
    note: str

    @property
    def s_id(self) -> str:
        return f"S_{slug(self.source_variety)}_{slug(self.english)}"

    @property
    def source_attr(self) -> str:
        return (
            f"Latham 1862 printed p. {self.printed_page}; "
            f"PDF p. {self.pdf_page}; {self.table}; "
            f"source variety: {self.source_variety}; "
            f"English gloss: {self.english}"
        )


def slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "entry"


def load_ledger(path: Path = LEDGER_PATH) -> list[LexicalEntry]:
    with path.open(encoding="utf-8", newline="") as handle:
        raw_rows = list(csv.DictReader(handle, delimiter="\t"))

    entries = [
        LexicalEntry(
            printed_page=row["printed_page"],
            pdf_page=row["pdf_page"],
            table=row["table"],
            language_code=row["language_code"],
            language_label=row["language_label"],
            dialect=row["dialect"],
            source_variety=row["source_variety"],
            english=row["english"],
            form=row["form"],
            alternate_forms=tuple(
                form
                for form in row["alternate_forms"].split(" | ")
                if form
            ),
            status=row["status"],
            note=row["note"],
        )
        for row in raw_rows
    ]

    if len(entries) != 64:
        raise ValueError(f"Expected 64 reviewed source cells, got {len(entries)}")
    if {entry.status for entry in entries} - VALID_STATUSES:
        raise ValueError("Source ledger contains an unsupported status")
    included = [entry for entry in entries if entry.status == "included"]
    omitted = [
        entry for entry in entries
        if entry.status == "omitted_blank_or_dash"
    ]
    if len(included) != 62 or len(omitted) != 2:
        raise ValueError("Source ledger must contain 62 included and 2 omitted cells")
    if any(not entry.form for entry in included):
        raise ValueError("Included source cells must have a FORM")
    if any(entry.form or entry.alternate_forms for entry in omitted):
        raise ValueError("Omitted source cells cannot contain FORM data")
    if len({entry.s_id for entry in included}) != len(included):
        raise ValueError("Included source cells produce duplicate XML IDs")
    if Counter(entry.printed_page for entry in entries) != Counter(
        {"315": 16, "316": 16, "317": 16, "318": 16}
    ):
        raise ValueError("Source ledger does not cover 16 target cells per page")
    return entries


def included_entries(entries: list[LexicalEntry]) -> list[LexicalEntry]:
    return [entry for entry in entries if entry.status == "included"]


def write_xml_file(
    path: Path,
    text_id: str,
    entries: list[LexicalEntry],
    glottocode: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    first = entries[0]
    root = etree.Element(
        "TEXT",
        id=text_id,
        citation=TEXT_CITATION,
        BibTeX_citation=TEXT_BIBTEX,
        copyright="Public domain.",
        glottocode=glottocode,
        dialect=first.dialect,
        source=(
            f"Basecamp card {BASECAMP_URL}; Latham 1862 Formosan lexical "
            f"tables; manual transcription; public scan: {SOURCE_URL}"
        ),
    )
    root.set(
        "{http://www.w3.org/XML/1998/namespace}lang",
        first.language_code,
    )
    for entry in entries:
        sentence = etree.SubElement(
            root,
            "S",
            id=entry.s_id,
            source=entry.source_attr,
        )
        original = etree.SubElement(sentence, "FORM", kindOf="original")
        original.text = entry.form
        standard = etree.SubElement(sentence, "FORM", kindOf="standard")
        standard.text = entry.form
        for alternate_form in entry.alternate_forms:
            alternate = etree.SubElement(
                sentence,
                "FORM",
                kindOf="alternate",
            )
            alternate.text = alternate_form
        translation = etree.SubElement(sentence, "TRANSL")
        translation.set(
            "{http://www.w3.org/XML/1998/namespace}lang",
            "eng",
        )
        translation.text = entry.english.lower()
    etree.ElementTree(root).write(
        str(path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def write_xml(entries: list[LexicalEntry]) -> None:
    siraya_entries = [
        entry for entry in entries if entry.language_code == "fos"
    ]
    babuza_entries = [
        entry for entry in entries if entry.language_code == "bzg"
    ]
    if len(siraya_entries) != 38 or len(babuza_entries) != 24:
        raise ValueError("Unexpected language split in included source ledger")
    write_xml_file(
        XML_ROOT / "Siraya/latham_1862_sideia_sida.xml",
        "latham_1862_sideia_sida",
        siraya_entries,
        "sira1267",
    )
    write_xml_file(
        XML_ROOT / "Babuza-Favorlang/latham_1862_favorlang.xml",
        "latham_1862_favorlang",
        babuza_entries,
        "favo1235",
    )


def write_report(entries: list[LexicalEntry]) -> None:
    fieldnames = [
        "s_id",
        "language_code",
        "language_label",
        "dialect",
        "source_variety",
        "english",
        "form",
        "alternate_forms",
        "printed_page",
        "pdf_page",
        "table",
        "review_note",
    ]
    with REPORT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        writer.writeheader()
        for entry in entries:
            writer.writerow(
                {
                    "s_id": entry.s_id,
                    "language_code": entry.language_code,
                    "language_label": entry.language_label,
                    "dialect": entry.dialect,
                    "source_variety": entry.source_variety,
                    "english": entry.english,
                    "form": entry.form,
                    "alternate_forms": " | ".join(entry.alternate_forms),
                    "printed_page": entry.printed_page,
                    "pdf_page": entry.pdf_page,
                    "table": entry.table,
                    "review_note": entry.note,
                }
            )


def write_summary(entries: list[LexicalEntry]) -> None:
    by_variety = Counter(entry.source_variety for entry in entries)
    by_language = Counter(entry.language_label for entry in entries)
    source_form_count = sum(
        1 + len(entry.alternate_forms) for entry in entries
    )
    rows = ["| Variety | Records |", "| --- | --- |"]
    for variety, count in sorted(by_variety.items()):
        rows.append(f"| {variety} | {count} |")
    language_rows = ["| Language | Records |", "| --- | --- |"]
    for language, count in sorted(by_language.items()):
        language_rows.append(f"| {language} | {count} |")
    lines = [
        "# Extraction Summary",
        "",
        "The 64 target cells on printed pages 315–318 were visually",
        "transcribed into `CodeAndDocs/source_ledger.tsv`. Sixty-two cells",
        "contain Formosan data and two source dash cells are terminally",
        "omitted.",
        "",
        "## Outputs",
        "",
        "- XML: `Final_XML/Siraya/latham_1862_sideia_sida.xml`",
        "- XML: `Final_XML/Babuza-Favorlang/latham_1862_favorlang.xml`",
        "- Row report: `CodeAndDocs/extraction_report.csv`",
        "- Exact source checks: `CodeAndDocs/source_checks.tsv`",
        "",
        "## Counts",
        "",
        f"- Lexical records emitted: {len(entries)}",
        f"- Source FORM variants emitted: {source_form_count}",
        f"- Source varieties represented: {len(by_variety)}",
        "",
        "## Counts By Source Variety",
        "",
        *rows,
        "",
        "## Counts By Language",
        "",
        *language_rows,
        "",
        "## Representation Decisions",
        "",
        "- Every source cell is one lexical `S` record.",
        "- Comma-separated source variants are separate `FORM` elements;",
        "  punctuation is not embedded in a FORM value.",
        "- Historical spelling is preserved in original and standard FORM",
        "  because the source supplies no supported modern normalization.",
        "- No W/M segmentation or PHON is inferred from this comparative table.",
        "- Sideia/Sida maps to Siraya (`fos`); Favorlang maps to Babuza-Favorlang (`bzg`).",
    ]
    SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ledger = load_ledger()
    entries = included_entries(ledger)
    write_xml(entries)
    write_report(entries)
    write_summary(entries)
    print("Wrote Final_XML/Siraya/latham_1862_sideia_sida.xml")
    print("Wrote Final_XML/Babuza-Favorlang/latham_1862_favorlang.xml")
    print(f"Records: {len(entries)}; source FORM variants: 70")


if __name__ == "__main__":
    main()
