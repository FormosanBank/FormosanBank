#!/usr/bin/env python3
"""Build source-faithful Tsukida (2014) Seediq XML and audit ledgers."""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
CORPUS_ROOT = Path(__file__).resolve().parents[2]
ROOT = CODE_ROOT
INPUT = ROOT / "raw_data" / "reviewed_examples.tsv"
MORPHEME_INPUT = ROOT / "raw_data" / "reviewed_morpheme_alignments.tsv"
VARIANT_INPUT = ROOT / "raw_data" / "reviewed_variants.tsv"
XML_NAME = "tsukida_2014_correlative_clauses_in_seediq.xml"
FINAL_XML = CORPUS_ROOT / "XML" / "Seediq" / XML_NAME
SOURCE_LEDGER = ROOT / "evidence" / "source_ledger.csv"
PAGE_INVENTORY = ROOT / "evidence" / "page_inventory.csv"
NOTATION_AUDIT = ROOT / "evidence" / "source_notation_audit.csv"
SOURCE_MAP = ROOT / "evidence" / "xml_source_map.csv"

SOURCE_PDF_SHA256 = "fab9b60ce52e47530805204c1d5beed02e52e63972e8315d9a1996c8e79248f1"
TEXT_ID = "tsukida_2014_correlative_clauses_in_seediq"
CITATION = (
    "Tsukida, N. (2014). Correlative clauses in Seediq. In I Wayan Arka & "
    "N. L. K. Mas Indrawati (Eds.), Papers from 12-ICAL, Volume 2: Argument "
    "realisations and related constructions in Austronesian languages "
    "(pp. 69-79). Asia-Pacific Linguistics."
)
BIBTEX = (
    "@incollection{tsukida2014correlativeseediq, author = {Tsukida, Naomi}, "
    "title = {Correlative clauses in Seediq}, booktitle = {Papers from 12-ICAL, "
    "Volume 2: Argument realisations and related constructions in Austronesian "
    "languages}, editor = {Arka, I Wayan and Indrawati, N. L. K. Mas}, "
    "publisher = {Asia-Pacific Linguistics}, year = {2014}, pages = {69--79}, "
    "url = {https://openresearch-repository.anu.edu.au/items/"
    "8bfb8bf0-2f58-4eae-947c-bf9af50faf9f}}"
)
COPYRIGHT = (
    "Copyright held by the authors, released under Creative Commons Attribution "
    "Licence (CC BY 4.0)."
)
PAGE_ROWS = [
    (74, 69, "examples 1-2", "Hindi excluded; Seediq example 2 included"),
    (75, 70, "examples 3-8", "six Seediq examples included"),
    (76, 71, "examples 9-10 (start)", "Seediq 9 included; Hindi 10 begins"),
    (77, 72, "examples 10-12", "Hindi and two Australian-language groups excluded"),
    (78, 73, "examples 13-14", "13 and 14b included; starred 14a excluded"),
    (79, 74, "examples 15-17", "15b, 16b, 17a-b included; 15a/16a excluded"),
    (80, 75, "examples 18-19", "four Seediq examples included"),
    (81, 76, "examples 20-24 (start)", "English 20a-b excluded; Seediq 21-24 included"),
    (82, 77, "examples 24-27", "continuation of 24 and examples 25-27 included"),
    (83, 78, "examples 27-29", "27 included; 28a-b and 29 excluded"),
    (84, 79, "summary and references", "no target-language examples"),
]


def read_tsv(path: Path = INPUT) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    for row in rows:
        for key, value in row.items():
            row[key] = value or ""
    return rows


def read_morpheme_alignments(
    path: Path = MORPHEME_INPUT,
) -> dict[tuple[str, int], dict[str, object]]:
    rows = read_tsv(path)
    alignments: dict[tuple[str, int], dict[str, object]] = {}
    for row in rows:
        key = (row["sentence_id"], int(row["word_index"]))
        if key in alignments:
            raise ValueError(f"Duplicate reviewed morpheme alignment: {key}")
        forms = row["m_forms"].split("|")
        glosses = row["m_glosses"].split("|")
        if len(forms) != len(glosses) or len(forms) < 2:
            raise ValueError(f"Invalid reviewed morpheme alignment: {key}")
        alignments[key] = {
            "word_form": row["word_form"],
            "source_word_gloss": row["source_word_gloss"],
            "canonical_word_gloss": row["canonical_word_gloss"],
            "morphemes": list(zip(forms, glosses)),
            "evidence": row["evidence"],
        }
    return alignments


def read_variants(path: Path = VARIANT_INPUT) -> dict[str, list[dict[str, str]]]:
    variants: dict[str, list[dict[str, str]]] = {}
    for row in read_tsv(path):
        variants.setdefault(row["source_id"], []).append(row)
    expected = {"tsukida2014_seediq_S005", "tsukida2014_seediq_S008"}
    if set(variants) != expected or any(len(rows) != 2 for rows in variants.values()):
        raise ValueError("Expected two reviewed variants for examples 6 and 9")
    ids = [row["variant_id"] for rows in variants.values() for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Reviewed variant ids must be unique")
    return variants


def validate_rows(rows: list[dict[str, str]]) -> None:
    ids = [row["id"] for row in rows]
    if len(rows) != 39 or len(set(ids)) != 39:
        raise ValueError("Expected 39 unique reviewed source units")
    if sum(row["included"] == "yes" for row in rows) != 26:
        raise ValueError("Expected 26 included Seediq source units")
    if sum(row["included"] == "no" for row in rows) != 13:
        raise ValueError("Expected 13 excluded comparison, duplicate, or starred units")
    if any(
        row["included"] == "yes"
        and (row["language"] != "Seediq" or row["grammaticality"] != "grammatical")
        for row in rows
    ):
        raise ValueError("Only grammatical Seediq source units may be included")
    if {page for page, _, _, _ in PAGE_ROWS} != set(range(74, 85)):
        raise ValueError("Page inventory must cover PDF pages 74-84")
    omitted_alternates = [
        row for row in rows if row["translation_alt_in_xml"] == "no"
    ]
    if [row["id"] for row in omitted_alternates] != ["tsukida2014_seediq_S009"]:
        raise ValueError("Expected only the starred interpretation of example 13 omitted")
    if not omitted_alternates[0]["translation_alt"].startswith("*"):
        raise ValueError("Omitted example 13 interpretation must remain source-attested")


def included_records(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    variants = read_variants()
    records: list[dict[str, str]] = []
    for source in rows:
        if source["included"] != "yes":
            continue
        source_variants = variants.get(source["id"])
        if not source_variants:
            record = dict(source)
            record["source_id"] = source["id"]
            record["variant_evidence"] = ""
            records.append(record)
            continue
        for variant in source_variants:
            record = dict(source)
            record.update(
                {
                    "id": variant["variant_id"],
                    "source_id": source["id"],
                    "original": variant["original"],
                    "gloss": variant["gloss"],
                    "translation": variant["translation"],
                    "translation_alt": "",
                    "translation_alt_in_xml": "n/a",
                    "variant_evidence": variant["evidence"],
                }
            )
            records.append(record)
    return records


def lexical_word(token: str) -> str:
    """Remove punctuation and analytical wrappers outside a lexical token."""
    word = token.strip()
    while word.startswith("*"):
        word = word[1:]
    while word and word[0] in '"“‘([':
        word = word[1:]
    while word and word[-1] in ',.;:!?"”’)]':
        word = word[:-1]
    return word


def word_alignment(record: dict[str, str]) -> tuple[list[tuple[str, str]], str]:
    source_words = [lexical_word(token) for token in record["original"].split()]
    source_words = [word for word in source_words if word]
    gloss_words = record["gloss"].split()
    if not gloss_words or len(source_words) != len(gloss_words):
        return [], (
            f"source word/gloss count mismatch ({len(source_words)} words, "
            f"{len(gloss_words)} glosses)"
        )
    return list(zip(source_words, gloss_words)), (
        "source word/gloss alignment retained; analytical wrappers removed at W edges"
    )


def split_gloss(gloss: str) -> list[str]:
    parts: list[str] = []
    for chunk in re.split(r"[-=]", gloss):
        position = 0
        for match in re.finditer(r"<([^>]+)>", chunk):
            if chunk[position : match.start()]:
                parts.append(chunk[position : match.start()])
            parts.append(match.group(1))
            position = match.end()
        if chunk[position:]:
            parts.append(chunk[position:])
    return [part for part in parts if part]


def split_form_part(part: str, clitic: bool) -> list[str]:
    prefix = "=" if clitic else ""
    match = re.fullmatch(r"([^<]*)<([^>]+)>(.*)", part)
    if not match:
        return [f"{prefix}{part}"] if part else []
    before, infix, after = match.groups()
    return [f"{prefix}{before}{after}", f"-{infix}-"]


def split_form(form: str) -> list[str]:
    output: list[str] = []
    current: list[str] = []
    pending = ""

    def flush() -> None:
        nonlocal current, pending
        if current:
            output.extend(split_form_part("".join(current), pending == "="))
        current = []
        pending = ""

    for character in form:
        if character in "-=":
            flush()
            pending = character
        else:
            current.append(character)
    flush()
    return [part for part in output if part]


def morpheme_alignment(
    record: dict[str, str],
    word_index: int,
    word: str,
    gloss: str,
    reviewed: dict[tuple[str, int], dict[str, object]],
) -> tuple[list[tuple[str, str]], str]:
    override = reviewed.get((record["id"], word_index))
    if override is not None:
        if override["word_form"] != word or override["source_word_gloss"] != gloss:
            raise ValueError(
                f"Reviewed morpheme alignment drift at {record['id']} W{word_index}"
            )
        return override["morphemes"], str(override["canonical_word_gloss"])

    form_parts = split_form(word)
    gloss_parts = split_gloss(gloss)
    if len(form_parts) <= 1:
        return [(word, gloss)], ""
    if len(form_parts) != len(gloss_parts):
        raise ValueError(
            f"Unreviewed morpheme mismatch at {record['id']} W{word_index}: "
            f"{word!r} versus {gloss!r}"
        )
    return list(zip(form_parts, gloss_parts)), ""


def add_word_structure(
    sentence: ET.Element,
    record: dict[str, str],
    reviewed: dict[tuple[str, int], dict[str, object]],
) -> str:
    aligned_words, alignment_note = word_alignment(record)
    if not aligned_words:
        return alignment_note
    for word_index, (word, gloss) in enumerate(aligned_words, start=1):
        word_element = ET.SubElement(
            sentence, "W", {"id": f"{record['id']}W{word_index}"}
        )
        ET.SubElement(word_element, "FORM", {"kindOf": "original"}).text = word
        ET.SubElement(
            word_element,
            "TRANSL",
            {"xml:lang": "eng", "kindOf": "original"},
        ).text = gloss
        morphemes, canonical_gloss = morpheme_alignment(
            record, word_index, word, gloss, reviewed
        )
        if canonical_gloss:
            ET.SubElement(
                word_element,
                "TRANSL",
                {"xml:lang": "eng", "kindOf": "standard", "ver": "alt"},
            ).text = canonical_gloss
        for morpheme_index, (form_part, gloss_part) in enumerate(
            morphemes, start=1
        ):
            morpheme = ET.SubElement(
                word_element,
                "M",
                {"id": f"{record['id']}W{word_index}M{morpheme_index}"},
            )
            ET.SubElement(morpheme, "FORM", {"kindOf": "original"}).text = form_part
            ET.SubElement(
                morpheme,
                "TRANSL",
                {"xml:lang": "eng", "kindOf": "original"},
            ).text = gloss_part
    return alignment_note


def build_tree(records: list[dict[str, str]]) -> ET.ElementTree:
    reviewed_morphemes = read_morpheme_alignments()
    root = ET.Element(
        "TEXT",
        {
            "id": TEXT_ID,
            "citation": CITATION,
            "BibTeX_citation": BIBTEX,
            "copyright": COPYRIGHT,
            "{http://www.w3.org/XML/1998/namespace}lang": "trv",
            "source": (
                "Tsukida 2014, Correlative clauses in Seediq, PDF pp. 74-84 / "
                f"printed pp. 69-79; source PDF SHA-256 {SOURCE_PDF_SHA256}"
            ),
            "dialect": "Truku",
        },
    )
    for record in records:
        sentence = ET.SubElement(
            root,
            "S",
            {"id": record["id"], "source": record["source_locator"]},
        )
        ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = record[
            "original"
        ]
        if record["translation"]:
            ET.SubElement(sentence, "TRANSL", {"xml:lang": "eng"}).text = record[
                "translation"
            ]
        if (
            record["translation_alt"]
            and record["translation_alt_in_xml"] == "yes"
        ):
            ET.SubElement(
                sentence, "TRANSL", {"xml:lang": "eng", "ver": "alt"}
            ).text = record["translation_alt"]
        record["word_structure"] = add_word_structure(
            sentence, record, reviewed_morphemes
        )
    used_alignments = {
        (record["id"], word_index)
        for record in records
        for word_index, (word, gloss) in enumerate(
            word_alignment(record)[0], start=1
        )
        if (record["id"], word_index) in reviewed_morphemes
    }
    if used_alignments != set(reviewed_morphemes):
        raise ValueError("Reviewed morpheme alignment table has unused rows")
    ET.indent(root, space="    ")
    return ET.ElementTree(root)


def write_xml(tree: ET.ElementTree, path: Path = FINAL_XML) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)
    text = path.read_text(encoding="utf-8")
    text = re.sub(r" ns0:lang=", " xml:lang=", text)
    text = text.replace(' xmlns:ns0="http://www.w3.org/XML/1998/namespace"', "")
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_source_ledger(rows: list[dict[str, str]]) -> None:
    variants = read_variants()
    fields = [
        "source_id",
        "source_locator",
        "page",
        "entry_block_record",
        "source_target_language_text",
        "translation",
        "translation_alt",
        "translation_alt_in_xml",
        "omitted_translation_reason",
        "gloss",
        "extraction_method",
        "confidence_review_note",
        "included_in_xml",
        "exclusion_reason",
        "final_xml_filename",
        "final_s_id",
    ]
    output = []
    for row in rows:
        included = row["included"] == "yes"
        output.append(
            {
                "source_id": row["id"],
                "source_locator": row["source_locator"],
                "page": row["pdf_page"],
                "entry_block_record": f"example {row['example_label']}",
                "source_target_language_text": row["original"],
                "translation": row["translation"],
                "translation_alt": row["translation_alt"],
                "translation_alt_in_xml": row["translation_alt_in_xml"],
                "omitted_translation_reason": (
                    row["notes"]
                    if row["translation_alt"]
                    and row["translation_alt_in_xml"] == "no"
                    else ""
                ),
                "gloss": row["gloss"],
                "extraction_method": "embedded text plus complete rendered-page review",
                "confidence_review_note": row["notes"],
                "included_in_xml": "yes" if included else "no",
                "exclusion_reason": "" if included else row["notes"],
                "final_xml_filename": XML_NAME if included else "",
                "final_s_id": (
                    ";".join(
                        variant["variant_id"] for variant in variants[row["id"]]
                    )
                    if included and row["id"] in variants
                    else row["id"] if included else ""
                ),
            }
        )
    write_csv(SOURCE_LEDGER, fields, output)


def write_page_inventory() -> None:
    fields = ["pdf_page", "printed_page", "source_content", "coverage_decision"]
    rows = [
        {
            "pdf_page": str(pdf_page),
            "printed_page": str(printed_page),
            "source_content": source_content,
            "coverage_decision": coverage_decision,
        }
        for pdf_page, printed_page, source_content, coverage_decision in PAGE_ROWS
    ]
    write_csv(PAGE_INVENTORY, fields, rows)


def write_notation_audit(rows: list[dict[str, str]]) -> None:
    fields = [
        "record_id",
        "source_locator",
        "included_in_xml",
        "source_original",
        "leading_star",
        "parenthesis_count",
        "square_bracket_count",
        "apostrophe_count",
        "hyphen_count",
        "equals_count",
        "terminal_punctuation",
        "translation",
        "alternate_translation",
        "review_status",
    ]
    output = []
    for row in rows:
        original = row["original"]
        output.append(
            {
                "record_id": row["id"],
                "source_locator": row["source_locator"],
                "included_in_xml": row["included"],
                "source_original": original,
                "leading_star": "yes" if original.startswith("*") else "no",
                "parenthesis_count": str(original.count("(") + original.count(")")),
                "square_bracket_count": str(original.count("[") + original.count("]")),
                "apostrophe_count": str(original.count("'")),
                "hyphen_count": str(original.count("-")),
                "equals_count": str(original.count("=")),
                "terminal_punctuation": (
                    original[-1:] if original[-1:] in ".?!" else ""
                ),
                "translation": row["translation"],
                "alternate_translation": row["translation_alt"],
                "review_status": "rendered source page rechecked 2026-08-08",
            }
        )
    write_csv(NOTATION_AUDIT, fields, output)


def source_map_rows(
    records: list[dict[str, str]], root: ET.Element | None = None
) -> list[dict[str, str]]:
    xml_by_id = (
        {sentence.get("id", ""): sentence for sentence in root.findall("S")}
        if root is not None
        else {}
    )
    output = []
    for record in records:
        sentence = xml_by_id.get(record["id"])
        standard = ""
        if sentence is not None:
            form = sentence.find("FORM[@kindOf='standard']")
            standard = (form.text or "") if form is not None else ""
        output.append(
            {
                "xml_id": record["id"],
                "source_locator": record["source_locator"],
                "pdf_page": record["pdf_page"],
                "printed_page": record["printed_page"],
                "example_label": record["example_label"],
                "source_ref": record["source_ref"],
                "source_original": record["original"],
                "xml_standard": standard,
                "source_gloss": record["gloss"],
                "translation": record["translation"],
                "translation_alt": record["translation_alt"],
                "translation_alt_in_xml": record["translation_alt_in_xml"],
                "word_structure": record["word_structure"],
                "review_notes": record["notes"],
                "source_id": record["source_id"],
                "variant_evidence": record["variant_evidence"],
            }
        )
    return output


def write_source_map(
    records: list[dict[str, str]], root: ET.Element | None = None
) -> None:
    fields = [
        "xml_id",
        "source_locator",
        "pdf_page",
        "printed_page",
        "example_label",
        "source_ref",
        "source_original",
        "xml_standard",
        "source_gloss",
        "translation",
        "translation_alt",
        "translation_alt_in_xml",
        "word_structure",
        "review_notes",
        "source_id",
        "variant_evidence",
    ]
    write_csv(SOURCE_MAP, fields, source_map_rows(records, root))


def main() -> None:
    rows = read_tsv()
    validate_rows(rows)
    records = included_records(rows)
    tree = build_tree(records)
    write_xml(tree)
    write_source_ledger(rows)
    write_page_inventory()
    write_notation_audit(rows)
    write_source_map(records)
    print("Generated 28 source-faithful Seediq sentences from 39 source units.")


if __name__ == "__main__":
    main()
