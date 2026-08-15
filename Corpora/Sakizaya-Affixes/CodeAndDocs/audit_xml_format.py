#!/usr/bin/env python3
"""Audit XML tier shape for Sakizaya affix corpus output."""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = ROOT / "XML/szy"
AUDIT_CSV = ROOT / "CodeAndDocs/xml_format_audit.csv"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def form_text(parent: ET.Element, kind: str) -> str:
    for form in parent.findall("FORM"):
        if form.attrib.get("kindOf") == kind:
            return form.text or ""
    return ""


def add_check(
    rows: list[dict[str, str]],
    xml_path: Path,
    element: ET.Element,
    check: str,
    passed: bool,
    note: str,
) -> None:
    rows.append(
        {
            "file": str(xml_path.relative_to(ROOT)),
            "element": element.tag,
            "id": element.attrib.get("id", ""),
            "check": check,
            "status": "pass" if passed else "fail",
            "note": note,
        }
    )


def audit_file(xml_path: Path) -> list[dict[str, str]]:
    root = ET.parse(xml_path).getroot()
    rows: list[dict[str, str]] = []
    is_inventory = xml_path.name.endswith("_table_rows.xml")
    for sentence in root.findall("S"):
        add_check(
            rows,
            xml_path,
            sentence,
            "s_has_id_and_source_attributes",
            set(sentence.attrib) == {"id", "source"}
            and bool(sentence.attrib.get("source")),
            ",".join(sorted(sentence.attrib)),
        )

        s_standard = form_text(sentence, "standard")
        original = sentence.find('./FORM[@kindOf="original"]')
        source_judged_without_m = bool(
            original is not None
            and original.attrib.get("notes", "").startswith("source judgement:")
            and sentence.find(".//M") is None
        )
        add_check(
            rows,
            xml_path,
            sentence,
            "s_standard_has_no_source_hyphens",
            "-" not in s_standard or source_judged_without_m,
            s_standard,
        )

        word_count = len(sentence.findall("W"))
        add_check(
            rows,
            xml_path,
            sentence,
            "s_has_word_tiers",
            word_count > 0,
            str(word_count),
        )

        words = sentence.findall("W")
        if is_inventory:
            notes = [
                form.attrib["notes"]
                for tier in [sentence, *sentence.findall(".//W"), *sentence.findall(".//M")]
                for form in tier.findall("FORM")
                if form.attrib.get("notes")
            ]
            inventory_m_count = sum(len(word.findall("M")) for word in words)
            add_check(
                rows,
                xml_path,
                sentence,
                "inventory_columns_use_m_tiers_not_notes",
                not notes and inventory_m_count == 2,
                f"M={inventory_m_count}; notes={' | '.join(notes)}",
            )
        if words:
            last_word = words[-1]
            last_word_values = [
                element.text or ""
                for element in [*last_word.findall("FORM"), *last_word.findall("PHON")]
            ]
            add_check(
                rows,
                xml_path,
                last_word,
                "sentence_final_w_has_no_sentence_punctuation",
                all(not re.search(r"[.,!?;:。！？；：]+$", text) for text in last_word_values),
                " | ".join(last_word_values),
            )

        for tier in [sentence, *sentence.findall(".//W"), *sentence.findall(".//M")]:
            standard = form_text(tier, "standard")
            phons = tier.findall("PHON")
            add_check(
                rows,
                xml_path,
                tier,
                "tier_has_shared_original_and_standard_phonology",
                {phon.attrib.get("kindOf") for phon in phons} == {"original", "standard"}
                and len(phons) == 2
                and all(bool(phon.text) for phon in phons),
                " | ".join(phon.text or "" for phon in phons),
            )
            for transl in tier.findall("TRANSL"):
                kind = transl.attrib.get("kindOf", "")
                expected_kind = "" if tier.tag == "S" else "original"
                add_check(
                    rows,
                    xml_path,
                    transl,
                    "transl_kind_matches_tier_ownership",
                    kind == expected_kind,
                    f"actual={kind or '<untiered>'}; expected={expected_kind or '<untiered>'}",
                )
                add_check(
                    rows,
                    xml_path,
                    transl,
                    "transl_has_xml_lang",
                    bool(transl.attrib.get(f"{{{XML_NS}}}lang")),
                    transl.attrib.get(f"{{{XML_NS}}}lang", ""),
                )

            if tier.tag == "M":
                morph_values = [
                    element.text or ""
                    for element in [*tier.findall("FORM"), *tier.findall("PHON")]
                ]
                add_check(
                    rows,
                    xml_path,
                    tier,
                    "m_has_no_sentence_punctuation",
                    all(
                        not re.search(r"[.,!?;:。！？；：]+$", text)
                        for text in morph_values
                    ),
                    " | ".join(morph_values),
                )

        for word in sentence.findall(".//W"):
            original = form_text(word, "original")
            standard = form_text(word, "standard")
            morphemes = word.findall("M")
            if "'" in original and "-" not in original and "=" not in original and len(morphemes) == 1:
                morph = morphemes[0]
                expected_original = re.sub(r"[.,!?;:。！？；：]+$", "", original)
                expected_standard = re.sub(r"[.,!?;:。！？；：]+$", "", standard)
                add_check(
                    rows,
                    xml_path,
                    morph,
                    "single_m_preserves_word_apostrophes",
                    form_text(morph, "original") == expected_original
                    and form_text(morph, "standard") == expected_standard,
                    " | ".join(
                        (
                            original,
                            form_text(morph, "original"),
                            standard,
                            form_text(morph, "standard"),
                        )
                    ),
                )
            if "-" in original and not original.startswith(("ø-", "Ø-", "∅-")):
                add_check(
                    rows,
                    xml_path,
                    word,
                    "w_standard_retains_segmentation",
                    "-" in standard,
                    standard,
                )
    return rows


def write_csv(rows: list[dict[str, str]]) -> None:
    fieldnames = ["file", "element", "id", "check", "status", "note"]
    with AUDIT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    rows: list[dict[str, str]] = []
    for xml_path in sorted(XML_ROOT.glob("*.xml")):
        rows.extend(audit_file(xml_path))
    write_csv(rows)
    failures = sum(1 for row in rows if row["status"] != "pass")
    print(f"xml format checks: {len(rows)}")
    print(f"xml format failures: {failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
