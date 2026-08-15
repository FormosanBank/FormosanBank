#!/usr/bin/env python3
"""Audit Lin 2015 source coverage and the fully generated corpus XML."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

import build_xml as builder


ROOT = Path(__file__).resolve().parents[1]
XML_ROOT = ROOT / "XML"
EXAMPLES_TSV = ROOT / "CodeAndDocs" / "extracted_examples.tsv"
EXCLUDED_TSV = ROOT / "CodeAndDocs" / "excluded_source_units.tsv"
REVIEW_TSV = ROOT / "CodeAndDocs" / "manual_source_review.tsv"
DIRECT_CHECKS_TSV = ROOT / "CodeAndDocs" / "direct_source_checks.tsv"
ALIGNMENT_OMISSIONS_TSV = ROOT / "CodeAndDocs" / "alignment_omissions.tsv"
AUDIT_REPORT = ROOT / "CodeAndDocs" / "source_alignment_audit.md"
PDF_PATH = (
    ROOT
    / "Private/source/basecamp/card-8262349071"
    / "lin_2015_amis_kavalan_interrogative_verbs.pdf"
)
LICENSE_PATH = (
    ROOT
    / "Private/source/basecamp/card-8262349071"
    / "source_license_screenshot_2025-01-28.png"
)
CACHE_PATH = (
    ROOT
    / "Private/cache"
    / "lin_2015_amis_kavalan_interrogative_verbs.layout.txt"
)
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

EXPECTED_FILES = {
    PDF_PATH: (
        "fb39fca379012a953ed21bc82d39c2545adc0227aa870a009841ed318aece28d",
        "source PDF",
    ),
    LICENSE_PATH: (
        "ccfc4711296bd5a1c60d72d8967542cea2428d99111df48ddfe585a88093748c",
        "CC BY 4.0 license screenshot",
    ),
    CACHE_PATH: (
        "64d6b9503bf8325aed09e9b3f55f1bfe873fed1dbe1768e86268fb589880ad82",
        "pdftotext -layout cache",
    ),
}
EXPECTED_XML = {
    "Amis": {
        "path": XML_ROOT / "Amis/lin_2015_amis_interrogative_verbs.xml",
        "xml_lang": "ami",
        "dialect": "Xiuguluan",
        "glottocode": "nat1254",
        "sentences": 38,
        "words": 179,
        "morphemes": 254,
        "forms": 942,
        "phon": 942,
        "translations": 482,
    },
    "Kavalan": {
        "path": XML_ROOT / "Kavalan/lin_2015_kavalan_interrogative_verbs.xml",
        "xml_lang": "ckv",
        "dialect": "Kavalan",
        "glottocode": "kava1241",
        "sentences": 38,
        "words": 168,
        "morphemes": 252,
        "forms": 916,
        "phon": 916,
        "translations": 462,
    },
}
EXPECTED_MISSING_GLOSS = {("Amis", "18a"), ("Amis", "18b")}
EXPECTED_MISSING_TRANSLATION = {
    ("Amis", "14b"),
    ("Amis", "18a"),
    ("Amis", "18b"),
    ("Amis", "55b"),
    ("Amis", "55d"),
    ("Amis", "57a"),
    ("Kavalan", "21b"),
    ("Kavalan", "54b"),
    ("Kavalan", "54d"),
}
EXPECTED_DIRECT_CHECKS = {
    ("Kavalan", "2a"), ("Kavalan", "3b"), ("Amis", "6a"),
    ("Amis", "10a"), ("Amis", "14a"), ("Amis", "14b"),
    ("Amis", "18a"), ("Amis", "19a"), ("Kavalan", "23a"),
    ("Kavalan", "23d"), ("Kavalan", "24a"), ("Amis", "25b"),
    ("Kavalan", "27b"), ("Amis", "28b"), ("Amis", "30a"),
    ("Kavalan", "39"), ("Kavalan", "41a"), ("Kavalan", "41b"),
    ("Amis", "42a"), ("Kavalan", "46"), ("Kavalan", "48a"),
    ("Kavalan", "50"), ("Amis", "51"), ("Kavalan", "54b"),
    ("Amis", "55b"), ("Kavalan", "56b"), ("Amis", "57b"),
    ("Kavalan", "59a"), ("Amis", "60a"), ("Amis", "60b"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def split_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if not unicodedata.category(char).startswith("M")
    )


def expected_standard(text: str, language: str, *, sentence_has_m: bool) -> str:
    """Reproduce the pinned shared standardization decisions used by build_all."""
    standard = strip_accents(text)
    if language == "Amis":
        for original, replacement in (("'", "^"), ("q", "'"), ("u", "o"), ("o", "o")):
            standard = standard.replace(original, replacement)
            standard = standard.replace(original.upper(), replacement.upper())
    if sentence_has_m:
        standard = standard.replace("-", "").replace("=", "")
    return standard


def expected_sentence_rows(language: str) -> list[tuple[int, builder.Example, builder.FormVariant]]:
    admitted = [
        example
        for example in builder.admitted_examples()
        if example.language == language
        and (example.language, example.source_id) not in builder.REPEAT_TARGETS
    ]
    rows: list[tuple[int, builder.Example, builder.FormVariant]] = []
    for index, example in enumerate(sorted(admitted, key=builder.source_order), start=1):
        rows.extend((index, example, variant) for variant in builder.form_variants(example))
    return rows


def verify_generated_tier(
    element: ET.Element,
    language: str,
    original: str,
    *,
    sentence_has_m: bool = False,
) -> list[str]:
    problems: list[str] = []
    forms = element.findall("FORM")
    if [(item.get("kindOf"), item.text or "") for item in forms] != [
        ("original", original),
        ("standard", expected_standard(original, language, sentence_has_m=sentence_has_m)),
    ]:
        problems.append("original/standard FORM pair")
    phon = element.findall("PHON")
    if [item.get("kindOf") for item in phon] != ["original", "standard"]:
        problems.append("original/standard PHON pair")
    elif any(not (item.text or "").strip() or "*" in (item.text or "") for item in phon):
        problems.append("nonempty resolved PHON")
    return problems


def verify_xml_language(language: str, errors: list[str], lines: list[str]) -> None:
    expected = EXPECTED_XML[language]
    path = expected["path"]
    root = ET.parse(path).getroot()
    status = "ok"
    metadata = (root.get(XML_LANG), root.get("dialect"), root.get("glottocode"))
    if metadata != (expected["xml_lang"], expected["dialect"], expected["glottocode"]):
        errors.append(f"Metadata mismatch in `{path.relative_to(ROOT)}`: {metadata}")
        status = "ERROR"
    if "CC BY 4.0" not in (root.get("copyright") or ""):
        errors.append(f"Missing CC BY 4.0 metadata in `{path.relative_to(ROOT)}`.")
        status = "ERROR"

    sentences = root.findall("./S")
    expected_rows = expected_sentence_rows(language)
    if len(sentences) != len(expected_rows):
        errors.append(
            f"Sentence inventory mismatch for {language}: expected {len(expected_rows)}, "
            f"found {len(sentences)}."
        )
        status = "ERROR"

    for sentence, (index, example, variant) in zip(sentences, expected_rows, strict=False):
        expected_id = f"S_{language.lower()}_{index:03d}{variant.id_suffix}"
        label = f"{language} {example.source_id}{variant.id_suffix}"
        if sentence.get("id") != expected_id:
            errors.append(f"Sentence ID mismatch for {label}: {sentence.get('id')!r}.")
            status = "ERROR"
        source_attr = sentence.get("source") or ""
        occurrences = [
            item
            for item in builder.admitted_examples()
            if item.language == language
            and (
                item.source_id == example.source_id
                or builder.REPEAT_TARGETS.get((item.language, item.source_id))
                == example.source_id
            )
        ]
        for occurrence in occurrences:
            marker = (
                f"{occurrence.source_id} (printed p. {occurrence.printed_page}; "
                f"PDF page {occurrence.pdf_page})"
            )
            if marker not in source_attr:
                errors.append(f"Missing occurrence provenance for {label}: {marker}.")
                status = "ERROR"

        sentence_has_m = sentence.find(".//M") is not None
        tier_problems = verify_generated_tier(
            sentence,
            language,
            variant.form,
            sentence_has_m=sentence_has_m,
        )
        if tier_problems:
            errors.append(f"Generated S tier mismatch for {label}: {', '.join(tier_problems)}.")
            status = "ERROR"

        translations = sentence.findall("TRANSL")
        readings = builder.translation_readings(example)
        translation_pairs = [
            (item.text or "", item.get(XML_LANG), item.get("ver"), item.get("kindOf"))
            for item in translations
        ]
        expected_pairs = [
            (reading, "eng", "alt" if index else None, None)
            for index, reading in enumerate(readings)
        ]
        if translation_pairs != expected_pairs:
            errors.append(f"S translation readings mismatch for {label}.")
            status = "ERROR"

        word_pairs, omission = builder.alignment_words(variant)
        if omission:
            errors.append(f"Unexpected W/M omission for {label}: {omission}.")
            status = "ERROR"
            continue
        analyses = [builder.aligned_morphemes(form, gloss) for form, gloss in word_pairs]
        parsed_sentence = any(len(forms) >= 2 for forms, _ in analyses)
        words = sentence.findall("W")
        if len(words) != len(word_pairs):
            errors.append(
                f"W inventory mismatch for {label}: expected {len(word_pairs)}, found {len(words)}."
            )
            status = "ERROR"
            continue
        for word_index, (word, (word_form, word_gloss), analysis) in enumerate(
            zip(words, word_pairs, analyses, strict=True), start=1
        ):
            expected_word_id = f"{expected_id}_W{word_index:02d}"
            if word.get("id") != expected_word_id:
                errors.append(f"W ID mismatch for {label} word {word_index}.")
                status = "ERROR"
            problems = verify_generated_tier(word, language, word_form)
            gloss = word.find("TRANSL[@kindOf='original']")
            if (
                problems
                or gloss is None
                or (gloss.text or "") != word_gloss
                or gloss.get(XML_LANG) != "eng"
                or len(word.findall("TRANSL")) != 1
            ):
                errors.append(f"W tier mismatch for {label} word {word_index}.")
                status = "ERROR"

            morph_forms, morph_glosses = analysis
            if parsed_sentence and len(morph_forms) < 2:
                morph_forms, morph_glosses = [word_form], [word_gloss]
            if not parsed_sentence:
                morph_forms, morph_glosses = [], []
            morphs = word.findall("M")
            if len(morphs) != len(morph_forms):
                errors.append(f"M inventory mismatch for {label} word {word_index}.")
                status = "ERROR"
                continue
            for morph_index, (morph, morph_form, morph_gloss) in enumerate(
                zip(morphs, morph_forms, morph_glosses, strict=True), start=1
            ):
                expected_morph_id = f"{expected_word_id}_M{morph_index:02d}"
                problems = verify_generated_tier(morph, language, morph_form)
                gloss = morph.find("TRANSL[@kindOf='original']")
                if (
                    morph.get("id") != expected_morph_id
                    or problems
                    or gloss is None
                    or (gloss.text or "") != morph_gloss
                    or gloss.get(XML_LANG) != "eng"
                    or len(morph.findall("TRANSL")) != 1
                ):
                    errors.append(
                        f"M tier mismatch for {label} word {word_index} morph {morph_index}."
                    )
                    status = "ERROR"

    counts = {
        "sentences": len(sentences),
        "words": len(root.findall(".//W")),
        "morphemes": len(root.findall(".//M")),
        "forms": len(root.findall(".//FORM")),
        "phon": len(root.findall(".//PHON")),
        "translations": len(root.findall(".//TRANSL")),
    }
    expected_counts = {key: expected[key] for key in counts}
    if counts != expected_counts:
        errors.append(
            f"Tier inventory mismatch in `{path.relative_to(ROOT)}`: "
            f"expected {expected_counts}, found {counts}."
        )
        status = "ERROR"
    lines.append(
        f"| `{path.relative_to(ROOT)}` | {counts['sentences']} | {counts['words']} | "
        f"{counts['morphemes']} | {counts['forms']} | {counts['phon']} | "
        f"{counts['translations']} | {status} |"
    )


def audit() -> tuple[list[str], list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    notices: list[str] = []
    lines = ["# Source Alignment Audit", ""]
    required = [
        EXAMPLES_TSV,
        EXCLUDED_TSV,
        REVIEW_TSV,
        DIRECT_CHECKS_TSV,
        ALIGNMENT_OMISSIONS_TSV,
        *[item["path"] for item in EXPECTED_XML.values()],
    ]
    for path in required:
        if not path.exists():
            errors.append(f"Missing required artifact: `{path.relative_to(ROOT)}`")
    expected_paths = {item["path"] for item in EXPECTED_XML.values()}
    actual_paths = set(XML_ROOT.rglob("*.xml")) if XML_ROOT.exists() else set()
    if actual_paths != expected_paths:
        errors.append("XML file inventory does not match the two expected corpus files.")
    if errors:
        return lines, errors, warnings

    lines.extend(
        [
            "## Source Integrity",
            "",
            "| File | Role | SHA-256 | Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    present = [path for path in EXPECTED_FILES if path.exists()]
    full_source_audit = len(present) == len(EXPECTED_FILES)
    if present and not full_source_audit:
        errors.append("Provide all three expected private source files or none.")
    for path, (expected_hash, role) in EXPECTED_FILES.items():
        if path.exists() and sha256(path) != expected_hash:
            errors.append(f"Source hash changed for `{path.relative_to(ROOT)}`.")
        lines.append(
            f"| `{path.relative_to(ROOT)}` | {role} | `{expected_hash}` | "
            f"{'verified' if path.exists() else 'recorded'} |"
        )
    if full_source_audit:
        try:
            info = subprocess.run(
                ["pdfinfo", str(PDF_PATH)], check=True, capture_output=True, text=True
            ).stdout
            pages = next(
                int(line.split(":", 1)[1])
                for line in info.splitlines()
                if line.startswith("Pages:")
            )
        except (OSError, subprocess.CalledProcessError, StopIteration, ValueError):
            pages = None
        if pages != 38:
            errors.append(f"Expected a 38-page source PDF, found {pages!r}.")
        try:
            fresh_cache = subprocess.run(
                ["pdftotext", "-layout", str(PDF_PATH), "-"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
        except (OSError, subprocess.CalledProcessError):
            fresh_cache = ""
            warnings.append("Could not reproduce the PDF text cache with pdftotext.")
        if fresh_cache and fresh_cache != CACHE_PATH.read_text(encoding="utf-8"):
            errors.append("The PDF text cache differs from a fresh pdftotext -layout extraction.")

    examples = read_tsv(EXAMPLES_TSV)
    excluded = read_tsv(EXCLUDED_TSV)
    reviews = read_tsv(REVIEW_TSV)
    direct_checks = read_tsv(DIRECT_CHECKS_TSV)
    omissions = read_tsv(ALIGNMENT_OMISSIONS_TSV)
    keys = [(row["language"], row["source_id"]) for row in examples]
    language_counts = Counter(row["language"] for row in examples)
    if len(examples) != 95 or language_counts != Counter({"Amis": 48, "Kavalan": 47}):
        errors.append(f"Expected 95 Formosan source rows, found {dict(language_counts)}.")
    if len(set(keys)) != len(keys):
        errors.append("Formosan source keys are not unique.")
    if any(int(row["pdf_page"]) != int(row["printed_page"]) - 252 for row in examples):
        errors.append("A source row has an invalid printed-page to PDF-page mapping.")
    missing_gloss = {key for key, row in zip(keys, examples, strict=True) if not row["gloss"]}
    missing_translation = {
        key
        for key, row in zip(keys, examples, strict=True)
        if not row["source_translation_eng"]
    }
    if missing_gloss != EXPECTED_MISSING_GLOSS:
        errors.append(f"Unexpected missing-gloss rows: {sorted(missing_gloss)}.")
    if missing_translation != EXPECTED_MISSING_TRANSLATION:
        errors.append(f"Unexpected missing-translation rows: {sorted(missing_translation)}.")
    if sum(row["admission_status"] == "admitted" for row in examples) != 75:
        errors.append("Expected 75 admitted Formosan occurrences.")
    if sum(row["admission_status"] == "excluded" for row in examples) != 20:
        errors.append("Expected 20 source-marked excluded Formosan occurrences.")
    if sum(row["source_form"].startswith("* ") for row in examples) != 18:
        errors.append("Expected 18 source-starred Formosan occurrences.")
    if sum(row["source_form"].startswith("? ") for row in examples) != 2:
        errors.append("Expected two source-marginal Formosan occurrences.")
    if sum(row["source_form"] != row["xml_form"] for row in examples) != 51:
        errors.append("Expected 51 rows with source-faithful XML notation changes.")
    if any("*" in row["xml_form"] for row in examples):
        errors.append("A source grammaticality asterisk leaked into an XML FORM.")

    source_by_key = {(item.language, item.source_id): item for item in builder.EXAMPLES}
    for row in examples:
        example = source_by_key[(row["language"], row["source_id"])]
        expected_variants = [
            {
                "id_suffix": variant.id_suffix,
                "label": variant.label,
                "form": variant.form,
                "aligned_form": variant.aligned_form,
                "gloss": variant.gloss,
            }
            for variant in builder.form_variants(example)
        ]
        if json.loads(row["xml_variants_json"]) != expected_variants:
            errors.append(f"Variant ledger mismatch for {row['language']} {row['source_id']}.")
        if tuple(json.loads(row["translation_readings_eng_json"])) != builder.translation_readings(example):
            errors.append(f"Translation ledger mismatch for {row['language']} {row['source_id']}.")
    if sum(len(builder.form_variants(example)) == 2 for example in builder.admitted_examples()) != 8:
        errors.append("Expected eight admitted optional source records under POL-026.")
    if omissions:
        errors.append("Admitted XML records must not have unresolved W/M alignment omissions.")

    excluded_counts = Counter(row["source_label"] for row in excluded)
    expected_excluded = Counter(
        {"Theory": 16, "Amis": 10, "Kavalan": 10, "Tzotzil": 1, "English": 1}
    )
    if len(excluded) != 38 or excluded_counts != expected_excluded:
        errors.append(f"Expected 38 source exclusions, found {dict(excluded_counts)}.")

    direct_keys = {(row["language"], row["source_id"]) for row in direct_checks}
    if len(direct_checks) != 30 or direct_keys != EXPECTED_DIRECT_CHECKS:
        errors.append("Direct source checks do not match the fixed 30-record sample.")
    rows_by_key = {(row["language"], row["source_id"]): row for row in examples}
    for row in direct_checks:
        key = (row["language"], row["source_id"])
        source_row = rows_by_key.get(key)
        if source_row is None:
            errors.append(f"Direct source check has no extraction row: {key}.")
        elif (
            row["printed_page"] != source_row["printed_page"]
            or row["pdf_page"] != source_row["pdf_page"]
            or not row["focus"].strip()
            or not row["visual_result"].startswith("Confirmed")
        ):
            errors.append(f"Direct source check evidence mismatch for {key}.")

    examples_by_page: dict[int, list[str]] = defaultdict(list)
    excluded_by_page: dict[int, list[str]] = defaultdict(list)
    for row in examples:
        examples_by_page[int(row["pdf_page"])].append(row["source_id"])
    for row in excluded:
        if row["source_label"] not in {"Amis", "Kavalan"}:
            excluded_by_page[int(row["pdf_page"])].append(row["source_id"])
    if [int(row["pdf_page"]) for row in reviews] != list(range(1, 39)):
        errors.append("Manual source review must cover PDF pages 1 through 38 in order.")
    for row in reviews:
        page = int(row["pdf_page"])
        if (
            row["visual_status"] != "confirmed"
            or split_ids(row["corpus_ids"]) != examples_by_page[page]
            or split_ids(row["excluded_ids"]) != excluded_by_page[page]
        ):
            errors.append(f"Manual review ledger mismatch on PDF page {page}.")

    lines.extend(
        [
            "",
            "## Coverage",
            "",
            "- Source PDF pages: 38",
            f"- Visually reviewed pages: {len(reviews)}",
            f"- Difficult records directly checked against rendered pages: {len(direct_checks)}",
            f"- Formosan source occurrences accounted for: {len(examples)}",
            "- Admitted Formosan occurrences: 75",
            "- Source-starred or marginal Formosan occurrences excluded under POL-016: 20",
            "- Theory or non-Formosan source units excluded: 18",
            "- Optional source records expanded under POL-026: 8",
            "- Generated XML sentence records: 76",
            "",
            "## XML Alignment",
            "",
            "| File | S | W | M | FORM | PHON | TRANSL | Status |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for language in ("Amis", "Kavalan"):
        verify_xml_language(language, errors, lines)

    if full_source_audit:
        cache_text = CACHE_PATH.read_text(encoding="utf-8")
        for sample in ("q‹um›uni", "tuniq-en", "ka-k‹um›a’en-an", "q‹m›aRat", "mayni=ay"):
            if sample not in cache_text:
                warnings.append(
                    f"Representative source string is missing from the PDF text cache: `{sample}`"
                )

    notices.extend(
        [
            "The extraction and exclusion ledgers account for every identified source unit.",
            "POL-016 excludes all 18 starred and two marginal Formosan occurrences while preserving their evidence.",
            "POL-026 expands eight optional source records into included and omitted S variants.",
            "POL-024 and POL-025 retain source-backed alternative, analytic, and literal translations as `ver=alt` readings.",
            "Amis standard and PHON tiers use the validated Lin-specific source profile; Kavalan uses Ortho113 directly.",
            "W and M glosses remain source-owned `kindOf=original`; every parsed sentence gives every W an M under POL-023.",
            "Original and standard PHON tiers are generated by the pinned shared phonology utility.",
        ]
    )
    lines.extend(
        [
            "",
            "## Result",
            "",
            f"- Errors: {len(errors)}",
            f"- Warnings: {len(warnings)}",
            f"- Notices: {len(notices)}",
        ]
    )
    if errors:
        lines.extend(["", "### Errors", "", *[f"- {item}" for item in errors]])
    if warnings:
        lines.extend(["", "### Warnings", "", *[f"- {item}" for item in warnings]])
    lines.extend(["", "### Notices", "", *[f"- {item}" for item in notices], ""])
    return lines, errors, warnings


def main() -> int:
    lines, errors, warnings = audit()
    AUDIT_REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {AUDIT_REPORT}")
    print(f"errors={len(errors)} warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
