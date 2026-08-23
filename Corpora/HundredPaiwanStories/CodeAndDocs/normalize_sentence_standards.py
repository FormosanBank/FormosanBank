#!/usr/bin/env python3
"""Apply exact source-reviewed decisions to direct sentence surface tiers."""

from __future__ import annotations

import argparse
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_DECISIONS = ROOT / "standard_surface_decisions.tsv"
DEFAULT_OPTIONAL_VARIANTS = ROOT / "data" / "optional_variants.tsv"
FIELDS = (
    "file",
    "sentence_id",
    "original_form",
    "source_standard_form",
    "legacy_blanket_form",
    "corrected_standard_form",
    "alternate_standard_form",
    "source_standard_phon",
    "legacy_blanket_phon",
    "corrected_standard_phon",
    "decision",
    "evidence",
    "review_status",
)
ALLOWED_DECISIONS = {
    "retain_plain_text_hyphen",
    "remove_parenthesized_uncertainty",
    "retain_plain_text_hyphen+remove_parenthesized_uncertainty",
    "published_parenthetical_token_with_omitted_alternate",
}


def load_optional_variants(
    path: Path = DEFAULT_OPTIONAL_VARIANTS,
) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    if len(rows) != 5:
        raise ValueError(f"expected five optional variants, found {len(rows)}")
    result = {row["sentence_id"]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate optional sentence ID")
    return result


def load_decisions(path: Path = DEFAULT_DECISIONS) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != FIELDS:
            raise ValueError("unexpected standard-surface manifest columns")
        rows = list(reader)

    if len(rows) != 166:
        raise ValueError(f"expected 166 exact decisions, found {len(rows)}")

    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row["file"], row["sentence_id"])
        if key in seen:
            raise ValueError(f"duplicate standard-surface decision: {key}")
        seen.add(key)
        if row["review_status"] != "source_checked":
            raise ValueError(f"unreviewed standard-surface decision: {key}")
        if row["decision"] not in ALLOWED_DECISIONS:
            raise ValueError(f"unknown standard-surface decision for {key}")
        required = (
            "file",
            "sentence_id",
            "original_form",
            "source_standard_form",
            "legacy_blanket_form",
            "corrected_standard_form",
            "decision",
            "evidence",
        )
        if any(not row[field] for field in required):
            raise ValueError(f"incomplete standard-surface decision: {key}")
        phon_presence = {
            bool(row["source_standard_phon"]),
            bool(row["legacy_blanket_phon"]),
            bool(row["corrected_standard_phon"]),
        }
        if len(phon_presence) != 1:
            raise ValueError(f"inconsistent PHON decision for {key}")
        if (
            "(" in row["corrected_standard_form"]
            or ")" in row["corrected_standard_form"]
        ):
            raise ValueError(f"unresolved parenthesis in corrected form for {key}")

        decision = row["decision"]
        if "retain_plain_text_hyphen" in decision:
            if "-" not in row["source_standard_form"]:
                raise ValueError(f"hyphen retention without source hyphen for {key}")
            if row["source_standard_form"].count("-") != row[
                "corrected_standard_form"
            ].count("-"):
                raise ValueError(f"source hyphen loss in corrected form for {key}")
        if decision == "published_parenthetical_token_with_omitted_alternate":
            if not row["alternate_standard_form"]:
                raise ValueError(f"missing omitted-token alternate for {key}")
        elif row["alternate_standard_form"]:
            raise ValueError(f"unexpected alternate standard for {key}")

    if sum("-" in row["source_standard_form"] for row in rows) != 153:
        raise ValueError("expected 153 exact source-hyphen sentence decisions")
    if sum("(" in row["source_standard_form"] for row in rows) != 16:
        raise ValueError("expected 16 exact parenthetical sentence decisions")
    if sum(bool(row["alternate_standard_form"]) for row in rows) != 5:
        raise ValueError("expected five published parenthetical-token alternates")
    return rows


def _one_direct(sentence: ET.Element, tag: str, kind: str) -> ET.Element:
    elements = sentence.findall(f"{tag}[@kindOf='{kind}']")
    if len(elements) != 1 or elements[0].text is None:
        raise ValueError(
            f"{sentence.get('id')}: expected one nonempty direct {kind} {tag}"
        )
    return elements[0]


def optional_original_forms(
    row: dict[str, str], optional: dict[str, str]
) -> tuple[str, str]:
    token = optional["included_token"]
    marker = f"({token})"
    original = row["original_form"]
    if original.count(marker) != 1:
        raise ValueError(f"{row['sentence_id']}: optional source marker changed")
    included = original.replace(marker, token)
    if original.startswith(f"{marker} "):
        omitted = original[len(marker) + 1 :]
    elif f" {marker}" in original:
        omitted = original.replace(f" {marker}", "", 1)
    else:
        raise ValueError(
            f"{row['sentence_id']}: optional marker is not token-delimited"
        )
    return included, omitted


def current_punctuation(value: str) -> str:
    """Apply the current clean_xml quote canonicalization to reviewed text."""

    return value.replace("'", '"')


def apply_decision(
    sentence: ET.Element,
    row: dict[str, str],
    *,
    omitted_sentence: ET.Element | None = None,
    optional: dict[str, str] | None = None,
) -> tuple[int, int, int]:
    sentence_id = sentence.get("id")
    if sentence_id != row["sentence_id"]:
        raise ValueError(f"decision ID mismatch: {sentence_id} != {row['sentence_id']}")

    original = _one_direct(sentence, "FORM", "original")
    expected_original = row["original_form"]
    if optional is not None:
        expected_original, _omitted_original = optional_original_forms(row, optional)
    cleaned_original = current_punctuation(expected_original)
    if original.text not in {expected_original, cleaned_original}:
        raise ValueError(f"{sentence_id}: original FORM differs from reviewed source")
    punctuation_cleaned = (
        cleaned_original != expected_original and original.text == cleaned_original
    )

    standard = _one_direct(sentence, "FORM", "standard")
    blanket_source = row["source_standard_form"].replace("-", "")
    allowed_forms = {
        row["source_standard_form"],
        row["legacy_blanket_form"],
        row["corrected_standard_form"],
        blanket_source,
        current_punctuation(row["source_standard_form"]),
        current_punctuation(row["legacy_blanket_form"]),
        current_punctuation(row["corrected_standard_form"]),
        current_punctuation(blanket_source),
    }
    if standard.text not in allowed_forms:
        raise ValueError(f"{sentence_id}: standard FORM differs from exact decision")
    corrected_standard = row["corrected_standard_form"]
    if punctuation_cleaned:
        corrected_standard = current_punctuation(corrected_standard)
    form_changes = int(standard.text != corrected_standard)
    standard.text = corrected_standard

    phon_changes = 0
    standard_phon = sentence.findall("PHON[@kindOf='standard']")
    if len(standard_phon) > 1 or any(element.text is None for element in standard_phon):
        raise ValueError(f"{sentence_id}: invalid regenerated standard PHON inventory")
    if standard_phon:
        phon = standard_phon[0]
        if any(marker in phon.text for marker in "-=<>~()"):
            raise ValueError(f"{sentence_id}: regenerated standard PHON has markers")

    if sentence.findall("FORM[@kindOf='alternate']"):
        raise ValueError(f"{sentence_id}: alternate FORM must be a complete S variant")

    variant_changes = 0
    if optional is None:
        if omitted_sentence is not None or row["alternate_standard_form"]:
            raise ValueError(f"{sentence_id}: incomplete optional-variant routing")
    else:
        if omitted_sentence is None:
            raise ValueError(f"{sentence_id}: missing complete omitted-token S variant")
        if omitted_sentence.get("id") != optional["omitted_sentence_id"]:
            raise ValueError(f"{sentence_id}: omitted sentence ID differs from review")
        if omitted_sentence.findall("FORM[@kindOf='alternate']"):
            raise ValueError(f"{sentence_id}: omitted S contains an alternate FORM")
        _included_original, expected_omitted_original = optional_original_forms(
            row, optional
        )
        omitted_original = _one_direct(omitted_sentence, "FORM", "original")
        if punctuation_cleaned:
            expected_omitted_original = current_punctuation(expected_omitted_original)
        if omitted_original.text != expected_omitted_original:
            raise ValueError(
                f"{sentence_id}: omitted original FORM differs from review"
            )
        omitted_standard = _one_direct(omitted_sentence, "FORM", "standard")
        desired_omitted = row["alternate_standard_form"]
        if punctuation_cleaned:
            desired_omitted = current_punctuation(desired_omitted)
        if omitted_standard.text != desired_omitted:
            raise ValueError(
                f"{sentence_id}: omitted standard FORM differs from review"
            )
        if "(" in omitted_standard.text or ")" in omitted_standard.text:
            raise ValueError(
                f"{sentence_id}: unresolved marker in omitted standard FORM"
            )
        omitted_phon = omitted_sentence.findall("PHON[@kindOf='standard']")
        if bool(standard_phon) != bool(omitted_phon):
            raise ValueError(f"{sentence_id}: omitted standard PHON presence differs")

    return form_changes, phon_changes, variant_changes


def normalize(
    xml_root: Path,
    decisions_path: Path = DEFAULT_DECISIONS,
    optional_path: Path = DEFAULT_OPTIONAL_VARIANTS,
) -> tuple[int, int, int, int]:
    decisions = load_decisions(decisions_path)
    optional_variants = load_optional_variants(optional_path)
    by_file: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decisions:
        by_file[row["file"]].append(row)

    files = {path.name: path for path in sorted(xml_root.rglob("*.xml"))}
    missing_files = sorted(set(by_file) - set(files))
    if missing_files:
        raise ValueError(f"missing reviewed XML files: {missing_files}")

    applied = form_changes = phon_changes = variant_changes = 0
    for filename, rows in sorted(by_file.items()):
        path = files[filename]
        tree = ET.parse(path)
        root = tree.getroot()
        sentences = {sentence.get("id"): sentence for sentence in root.findall(".//S")}
        for row in rows:
            sentence = sentences.get(row["sentence_id"])
            if sentence is None:
                raise ValueError(f"{filename}: missing sentence {row['sentence_id']}")
            optional = optional_variants.get(row["sentence_id"])
            omitted_sentence = None
            if optional is not None:
                omitted_sentence = sentences.get(optional["omitted_sentence_id"])
            form_delta, phon_delta, variant_delta = apply_decision(
                sentence,
                row,
                omitted_sentence=omitted_sentence,
                optional=optional,
            )
            applied += 1
            form_changes += form_delta
            phon_changes += phon_delta
            variant_changes += variant_delta

        ET.indent(root, space="    ")
        tree.write(path, encoding="utf-8", xml_declaration=True)

    if applied != len(decisions):
        raise ValueError(f"applied {applied} of {len(decisions)} exact decisions")
    if set(optional_variants) != {
        row["sentence_id"] for row in decisions if row["alternate_standard_form"]
    }:
        raise ValueError("optional-variant manifest differs from surface decisions")
    return applied, form_changes, phon_changes, variant_changes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora-path", type=Path, default=Path("XML"))
    parser.add_argument(
        "--decisions",
        type=Path,
        default=DEFAULT_DECISIONS,
    )
    parser.add_argument(
        "--optional-variants",
        type=Path,
        default=DEFAULT_OPTIONAL_VARIANTS,
    )
    args = parser.parse_args()
    applied, forms, phon, variants = normalize(
        args.corpora_path.resolve(),
        args.decisions.resolve(),
        args.optional_variants.resolve(),
    )
    print(f"exact_decisions={applied}")
    print(f"corrected_forms={forms}")
    print(f"corrected_phon={phon}")
    print(f"normalized_complete_variants={variants}")


if __name__ == "__main__":
    main()
