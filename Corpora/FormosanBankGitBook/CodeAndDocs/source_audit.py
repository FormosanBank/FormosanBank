#!/usr/bin/env python3
"""Verify canonical Paiwan GitBook XML against the reviewed source ledger."""

from __future__ import annotations

import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import process_raw

EXPECTED_PDF_SHA256 = "5f7b960a9105f46a3216de6220664334b7d32763e8fc95d1519daadb4b84dd84"
EXPECTED_PDF_PAGES = 9
EXPECTED_RECORD_COUNTS = {
    "Welcome": 10,
    "FormosanBank": 29,
    "Formosan_Languages": 16,
    "Contributors": 9,
    "Terms_of_Use": 13,
    "Contributing_to_FormosanBank": 28,
}
EXPECTED_SOURCE_HASHES = {
    "Contributing_to_FormosanBank.txt": "aa4d0fdcfec0bc96ce60bbdb70bcaa54f25ee2480a6cc8406c033239d2dbca53",
    "Contributors.txt": "6e469f76634831d5617a9562c48f2374f022b5f3a223d744ae08ad7a43f21cfd",
    "FormosanBank.txt": "b9126f021be7f0c5b2295e9116ee404b80414c60b5a92623fd96ee7c4036ba17",
    "Formosan_Languages.txt": "74bd5f9a75e0e6155220f487e0832755f855588e40db63fdd52ac535f9855a58",
    "Terms_of_Use.txt": "60c0a9aaa2ff47b83a19be2b6e8ee34a52d92bcc563e9290abf60727182517b9",
    "Welcome.txt": "f4b2b025953d88f99475714d7bbc489129546872d1b0dbe1cef2be96b2a87e0f",
}
FORM_QUOTE_NORMALIZATION = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def direct(element: ET.Element, tag: str, attribute: str, value: str) -> list[ET.Element]:
    return [child for child in element.findall(tag) if child.get(attribute) == value]


def canonical_form(source_form: str) -> str:
    """Apply the current validator's required FORM-only quote normalization."""
    return source_form.translate(FORM_QUOTE_NORMALIZATION)


def display_path(path: Path, repo: Path) -> str:
    try:
        return str(path.relative_to(repo))
    except ValueError:
        return str(path)


def root_findings(root: ET.Element, stem: str) -> list[str]:
    expected = {
        "id": f"gitbook_{process_raw.LANGUAGE}_{stem}",
        process_raw.XML_LANG: process_raw.LANGUAGE_CODE,
        "source": process_raw.SOURCE_URLS[stem],
        "copyright": "CC-BY-NC",
        "citation": process_raw.CITATION,
        "BibTeX_citation": process_raw.BIBTEX,
        "dialect": process_raw.DIALECT,
    }
    return [
        f"root {attribute}={root.get(attribute)!r}; expected {value!r}"
        for attribute, value in expected.items()
        if root.get(attribute) != value
    ]


def audit(
    repo: Path,
    xml_dir: Path,
    *,
    apply: bool,
    require_generated: bool,
) -> dict[str, object]:
    source_dir = repo / "raw_data" / "Paiwan"
    inventory = process_raw.source_inventory(source_dir)
    findings: dict[str, list[str]] = {}
    counts: Counter[str] = Counter()

    if EXPECTED_SOURCE_HASHES:
        for filename, expected_hash in EXPECTED_SOURCE_HASHES.items():
            actual_hash = sha256(source_dir / filename)
            if actual_hash != expected_hash:
                findings.setdefault(filename, []).append(
                    f"source ledger hash {actual_hash}; expected {expected_hash}"
                )

    actual_xml = {path.name for path in xml_dir.glob("*.xml")}
    expected_xml = {f"{stem}.xml" for stem in inventory}
    if actual_xml != expected_xml:
        findings["XML inventory"] = [
            f"missing={sorted(expected_xml - actual_xml)}",
            f"unexpected={sorted(actual_xml - expected_xml)}",
        ]

    for stem, records in inventory.items():
        expected_count = EXPECTED_RECORD_COUNTS[stem]
        if len(records) != expected_count:
            findings.setdefault(f"{stem}.txt", []).append(
                f"source records={len(records)}; expected={expected_count}"
            )

        xml_path = xml_dir / f"{stem}.xml"
        if not xml_path.exists():
            continue
        tree = ET.parse(xml_path)
        root = tree.getroot()
        file_findings = root_findings(root, stem)
        sentences = root.findall("S")
        if len(sentences) != len(records):
            file_findings.append(f"sentences={len(sentences)}; source={len(records)}")
            findings[display_path(xml_path, repo)] = file_findings
            continue

        for index, (sentence, record) in enumerate(zip(sentences, records, strict=True)):
            locator = f"S={index}"
            expected_form = canonical_form(record.paiwan)
            if sentence.get("id") != str(index):
                file_findings.append(f"{locator} id={sentence.get('id')!r}")

            originals = direct(sentence, "FORM", "kindOf", "original")
            chinese = direct(sentence, "TRANSL", process_raw.XML_LANG, "zho")
            english = direct(sentence, "TRANSL", process_raw.XML_LANG, "eng")
            if len(originals) != 1 or len(chinese) != 1 or len(english) != 1:
                file_findings.append(
                    f"{locator} source tier counts FORM={len(originals)} "
                    f"zho={len(chinese)} eng={len(english)}"
                )
                continue

            if apply:
                originals[0].text = expected_form
                chinese[0].text = record.chinese
                english[0].text = record.english

            expected_tiers = (
                ("original FORM", originals[0].text or "", expected_form),
                ("zho TRANSL", chinese[0].text or "", record.chinese),
                ("eng TRANSL", english[0].text or "", record.english),
            )
            for label, actual, expected in expected_tiers:
                if actual != expected:
                    file_findings.append(f"{locator} {label} differs from source")

            if sentence.findall("W") or sentence.findall("M") or sentence.findall("AUDIO"):
                file_findings.append(f"{locator} has unsupported W, M, or AUDIO tiers")

            if require_generated:
                standards = direct(sentence, "FORM", "kindOf", "standard")
                original_phon = direct(sentence, "PHON", "kindOf", "original")
                standard_phon = direct(sentence, "PHON", "kindOf", "standard")
                if not all(len(tier) == 1 for tier in (standards, original_phon, standard_phon)):
                    file_findings.append(
                        f"{locator} generated tiers standard={len(standards)} "
                        f"original-PHON={len(original_phon)} standard-PHON={len(standard_phon)}"
                    )
                elif standards[0].text != expected_form:
                    file_findings.append(f"{locator} copied standard FORM differs from source")

            counts["sentences"] += 1
            counts["translations"] += 2

        if apply and not file_findings:
            ET.indent(root, space="  ")
            tree.write(xml_path, encoding="utf-8", xml_declaration=True)
            with xml_path.open("ab") as handle:
                handle.write(b"\n")
        if file_findings:
            findings[display_path(xml_path, repo)] = file_findings

    return {
        "applied": apply,
        "canonical_findings": findings,
        "counts": dict(sorted(counts.items())),
        "source": {
            "files": len(inventory),
            "included_records": sum(len(records) for records in inventory.values()),
            "excluded_unaligned_headings": 2,
            "reviewed_pdf_pages": EXPECTED_PDF_PAGES,
            "reviewed_pdf_sha256": EXPECTED_PDF_SHA256,
        },
    }


def main() -> int:
    repo = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=repo)
    parser.add_argument("--xml", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--require-generated", action="store_true")
    args = parser.parse_args()

    resolved_repo = args.repo.resolve()
    xml_dir = (
        args.xml.resolve()
        if args.xml
        else resolved_repo.parent / "XML" / "Paiwan"
    )
    result = audit(
        resolved_repo,
        xml_dir,
        apply=args.apply,
        require_generated=args.require_generated,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if result["canonical_findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
