#!/usr/bin/env python3
"""Deterministically build the reviewed Li (2014) Thao example corpus."""

from __future__ import annotations

import csv
import re
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "CodeAndDocs" / "reviewed_examples.tsv"
DRAFT = ROOT / "XML" / "Thao" / "li_2014_conjunction_in_thao.xml"
FINAL = ROOT / "Final_XML" / "Thao" / "li_2014_conjunction_in_thao.xml"
LEDGER = ROOT / "CodeAndDocs" / "source_ledger.csv"
SOURCE_MAP = ROOT / "CodeAndDocs" / "xml_source_map.csv"
REVIEW = ROOT / "CodeAndDocs" / "rendered_xml_review.md"

CITATION = ("Li, P. J.-K. (2014). Conjunction in Thao. In I Wayan Arka & N. L. K. "
            "Mas Indrawati (Eds.), Papers from 12-ICAL, Volume 2: Argument realisations "
            "and related constructions in Austronesian languages (pp. 401-409). "
            "Asia-Pacific Linguistics.")
BIBTEX = ("@incollection{li2014conjunctionthao, author={Li, Paul Jen-Kuei}, "
          "title={Conjunction in Thao}, booktitle={Papers from 12-ICAL, Volume 2: "
          "Argument realisations and related constructions in Austronesian languages}, "
          "editor={Arka, I Wayan and Indrawati, N. L. K. Mas}, publisher={Asia-Pacific "
          "Linguistics}, year={2014}, pages={401--409}, url={https://openresearch-"
          "repository.anu.edu.au/items/8bfb8bf0-2f58-4eae-947c-bf9af50faf9f}}")
COPYRIGHT = "Creative Commons Attribution 4.0 International (CC BY 4.0)."
EDGE_PUNCTUATION = ".,!?;:…"


def standard_sentence(form: str) -> str:
    """Remove source segmentation notation from the sentence standard tier."""
    return re.sub(r"[-=<>]", "", form)


def word_tokens(text: str) -> list[str]:
    return [token.strip(EDGE_PUNCTUATION) for token in text.split()]


def _split_base_morphemes(text: str) -> tuple[list[str], list[str]]:
    parts = re.split(r"([-=])", text)
    values: list[str] = []
    boundaries: list[str] = []
    pending = ""
    for part in parts:
        if part in {"-", "="}:
            pending = part
        elif part:
            values.append(part)
            boundaries.append(pending)
            pending = ""
    return values, boundaries


def parse_morphemes(form: str, gloss: str) -> list[tuple[str, str]]:
    """Return source-supported M form/gloss pairs in canonical infix notation."""
    form_infixes = re.findall(r"<([^<>]+)>", form)
    gloss_infixes = re.findall(r"<([^<>]+)>", gloss)
    if len(form_infixes) != len(gloss_infixes):
        raise ValueError(f"infix mismatch: {form!r} / {gloss!r}")

    form_values, form_boundaries = _split_base_morphemes(
        re.sub(r"<[^<>]+>", "", form)
    )
    gloss_values, gloss_boundaries = _split_base_morphemes(
        re.sub(r"<[^<>]+>", "", gloss)
    )
    if len(form_values) != len(gloss_values):
        raise ValueError(f"morpheme mismatch: {form!r} / {gloss!r}")
    if len(form_values) + len(form_infixes) == 1:
        return []

    result: list[tuple[str, str]] = []
    for form_value, form_boundary, gloss_value, gloss_boundary in zip(
        form_values,
        form_boundaries,
        gloss_values,
        gloss_boundaries,
        strict=True,
    ):
        m_form = f"={form_value}" if form_boundary == "=" else form_value
        m_gloss = f"={gloss_value}" if gloss_boundary == "=" else gloss_value
        result.append((m_form, m_gloss))
    for form_infix, gloss_infix in zip(form_infixes, gloss_infixes, strict=True):
        result.append((f"-{form_infix}-", f"<{gloss_infix}>"))
    return result


def rows() -> list[dict[str, str]]:
    with RECORDS.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle, delimiter="\t"))
    if len(data) != 27 or any(r["included"] != "yes" for r in data):
        raise SystemExit("Expected exactly 27 reviewed included examples")

    expected_pages = {
        **{str(number): ("395", "402") for number in range(1, 6)},
        **{str(number): ("396", "403") for number in range(6, 9)},
        **{str(number): ("397", "404") for number in range(9, 15)},
        **{str(number): ("398", "405") for number in range(15, 21)},
        **{str(number): ("399", "406") for number in range(21, 25)},
        "fn7-1": ("399", "406"),
        "fn7-2": ("399", "406"),
        "fn7-3": ("399", "406"),
    }
    for r in data:
        expected_pdf, expected_printed = expected_pages[r["example_label"]]
        expected_locator = f"PDF p. {expected_pdf}; printed p. {expected_printed};"
        if (r["pdf_page"], r["printed_page"]) != (expected_pdf, expected_printed):
            raise SystemExit(
                f"Wrong reviewed page pair for {r['example_label']}: "
                f"{r['pdf_page']}/{r['printed_page']} != {expected_pdf}/{expected_printed}"
            )
        if not r["source_locator"].startswith(expected_locator):
            raise SystemExit(
                f"Wrong reviewed locator for {r['example_label']}: {r['source_locator']!r}"
            )
        forms = word_tokens(r["original"])
        glosses = r["gloss"].split()
        if r["gloss"] and len(forms) != len(glosses):
            raise SystemExit(
                f"Word/gloss mismatch for {r['example_label']}: "
                f"{len(forms)} forms != {len(glosses)} glosses"
            )
        if r["gloss"]:
            for form, gloss in zip(forms, glosses, strict=True):
                parse_morphemes(form, gloss)
    return data


def build(data: list[dict[str, str]]) -> ET.ElementTree:
    root = ET.Element("TEXT", {
        "id": "li_2014_conjunction_in_thao", "citation": CITATION,
        "BibTeX_citation": BIBTEX, "copyright": COPYRIGHT,
        "{http://www.w3.org/XML/1998/namespace}lang": "ssf", "dialect": "Thao",
        "glottocode": "thao1240",
        "source": "Li 2014 PDF pp. 394-402 (printed pp. 401-409)",
    })
    for r in data:
        sentence = ET.SubElement(root, "S", {"id": r["id"], "source": r["source_locator"]})
        original = ET.SubElement(sentence, "FORM", {"kindOf": "original"})
        original.text = r["original"]
        standard = ET.SubElement(sentence, "FORM", {"kindOf": "standard"})
        standard.text = standard_sentence(r["original"])
        translation = ET.SubElement(sentence, "TRANSL", {"xml:lang": "eng"})
        translation.text = r["translation"]
        word_pairs = (
            zip(word_tokens(r["original"]), r["gloss"].split(), strict=True)
            if r["gloss"]
            else ()
        )
        for word_number, (word_form, word_gloss) in enumerate(word_pairs, start=1):
            word = ET.SubElement(
                sentence, "W", {"id": f"{r['id']}_w{word_number:02d}"}
            )
            for kind in ("original", "standard"):
                form = ET.SubElement(word, "FORM", {"kindOf": kind})
                # Word-level analytical segmentation is source evidence required
                # for alignment with the gloss and child morphemes.
                form.text = word_form
            gloss = ET.SubElement(
                word, "TRANSL", {"xml:lang": "eng", "kindOf": "gloss"}
            )
            gloss.text = word_gloss
            for morpheme_number, (m_form, m_gloss) in enumerate(
                parse_morphemes(word_form, word_gloss), start=1
            ):
                morpheme = ET.SubElement(
                    word,
                    "M",
                    {"id": f"{r['id']}_w{word_number:02d}_m{morpheme_number:02d}"},
                )
                m_original = ET.SubElement(morpheme, "FORM", {"kindOf": "original"})
                m_original.text = m_form
                m_standard = ET.SubElement(morpheme, "FORM", {"kindOf": "standard"})
                m_standard.text = re.sub(r"[-=<>]", "", m_form)
                m_translation = ET.SubElement(
                    morpheme,
                    "TRANSL",
                    {"xml:lang": "eng", "kindOf": "original"},
                )
                m_translation.text = m_gloss
    ET.indent(root, space="    ")
    return ET.ElementTree(root)


def write_xml(tree: ET.ElementTree) -> None:
    DRAFT.parent.mkdir(parents=True, exist_ok=True)
    FINAL.parent.mkdir(parents=True, exist_ok=True)
    tree.write(DRAFT, encoding="utf-8", xml_declaration=True)
    text = DRAFT.read_text(encoding="utf-8")
    text = re.sub(r" ns0:lang=", " xml:lang=", text)
    text = text.replace(' xmlns:ns0="http://www.w3.org/XML/1998/namespace"', "")
    DRAFT.write_text(text, encoding="utf-8")
    shutil.copyfile(DRAFT, FINAL)


def write_evidence(data: list[dict[str, str]]) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source_locator", "page", "entry_or_record", "target_language_text",
              "translation", "gloss", "extraction_method", "review_note",
              "included_in_xml", "exclusion_reason", "final_xml_filename", "final_s_id"]
    with LEDGER.open("w", encoding="utf-8", newline="") as handle:
        out = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        out.writeheader()
        for r in data:
            out.writerow({"source_locator": r["source_locator"], "page": r["pdf_page"],
                "entry_or_record": r["example_label"], "target_language_text": r["original"],
                "translation": r["translation"], "gloss": r["gloss"],
                "extraction_method": "embedded text plus rendered-page manual review",
                "review_note": r["notes"] or "visually reviewed", "included_in_xml": "yes",
                "exclusion_reason": "", "final_xml_filename": FINAL.name, "final_s_id": r["id"]})
        exclusions = {
            394: ("printed p. 401", "title, introduction, rights notice; no example utterances"),
            400: ("printed p. 407", "summary prose only; no quoted Thao utterances"),
            401: ("printed p. 408", "frequency table contains counts, not utterances"),
            402: ("printed p. 409", "references only; no Thao utterances"),
        }
        for page, (entry, reason) in exclusions.items():
            out.writerow({"source_locator": f"PDF p. {page}; {entry}", "page": page,
                "entry_or_record": "page coverage", "target_language_text": "",
                "translation": "", "gloss": "", "extraction_method": "rendered-page review",
                "review_note": "whole page inventoried", "included_in_xml": "no",
                "exclusion_reason": reason, "final_xml_filename": "", "final_s_id": ""})

    map_fields = ["xml_id", "source_locator", "pdf_page", "printed_page", "example_label",
                  "source_ref", "source_original", "standard_form", "translation", "gloss", "notes"]
    with SOURCE_MAP.open("w", encoding="utf-8", newline="") as handle:
        out = csv.DictWriter(handle, fieldnames=map_fields, lineterminator="\n")
        out.writeheader()
        for r in data:
            out.writerow({"xml_id": r["id"], "source_locator": r["source_locator"],
                "pdf_page": r["pdf_page"], "printed_page": r["printed_page"],
                "example_label": r["example_label"], "source_ref": r["source_ref"],
                "source_original": r["original"],
                "standard_form": standard_sentence(r["original"]),
                "translation": r["translation"], "gloss": r["gloss"], "notes": r["notes"]})

    lines = ["# Rendered XML Review", "", "All 27 included examples were visually checked.", "",
             "Sentence-level standard forms remove source segmentation markers (`-`, `=`,",
             "`<`, and `>`). Word-level forms retain source segmentation so their aligned",
             "glosses and source-supported morphemes remain auditable. The final three",
             "footnote examples have no source gloss and therefore no W/M analysis.", ""]
    for r in data:
        lines += [f"## {r['id']} / {r['source_locator']}", "", f"- Original: {r['original']}",
                  f"- Standard: {standard_sentence(r['original'])}",
                  f"- W count: {len(r['gloss'].split()) if r['gloss'] else 0}",
                  f"- Source gloss: {r['gloss'] or 'not supplied'}",
                  f"- Translation: {r['translation']}", f"- Review: {r['notes'] or 'matched rendered source'}", ""]
    REVIEW.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = rows()
    write_xml(build(data))
    write_evidence(data)
    print(f"Wrote {FINAL} ({len(data)} sentences)")


if __name__ == "__main__":
    main()
