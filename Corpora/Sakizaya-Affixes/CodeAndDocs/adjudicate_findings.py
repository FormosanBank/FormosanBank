#!/usr/bin/env python3
"""Adjudicate every finding from the guarded Sakizaya QC run."""

from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "XML/szy"
XML_NS = "http://www.w3.org/XML/1998/namespace"
EXPECTED_COMMANDS = {
    "build_all",
    "build_all_repeat",
    "validate_xml",
    "validate_dialect",
    "validate_text",
    "validate_glosses",
    "validate_duplicates_original",
    "validate_duplicates_standard",
    "orthography_extract_original",
    "validate_orthography_original",
    "validate_vocabulary_original",
    "orthography_extract_standard",
    "validate_orthography_standard",
    "validate_vocabulary_standard",
    "validate_registries",
    "orthography_detector_original",
    "orthography_detector_standard",
    "apply_manual_edits_scratch",
    "clean_xml_scratch",
    "standardize_source_profile_scratch",
    "add_phonology_scratch",
    "validate_port_readiness",
}
SOURCE_DISTINCT_STANDARD_DUPLICATE_IDS = {
    "AKIW_SZY_2012_EX_069A",
    "AKIW_SZY_2012_EX_082A",
}


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def direct_text(parent: ET.Element, tag: str, kind: str = "") -> str:
    for child in parent.findall(tag):
        if not kind or child.attrib.get("kindOf") == kind:
            return child.text or ""
    return ""


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qc-dir", required=True, type=Path)
    args = parser.parse_args()
    qc_dir = args.qc_dir.resolve()

    schema = read_csv(qc_dir / "validate_xml_findings.csv")
    text_rows = read_csv(qc_dir / "validate_text_findings.csv")
    gloss_rows = read_csv(qc_dir / "validate_glosses_findings.csv")
    duplicate_original = read_csv(qc_dir / "duplicate_original_findings.csv")
    duplicate_standard = read_csv(qc_dir / "duplicate_standard_findings.csv")
    registry_rows = read_csv(qc_dir / "validate_registries_findings.csv")

    require(
        len(schema) == 1
        and schema[0]["severity"] == "SOFT"
        and schema[0]["rule_id"] == "V144"
        and schema[0]["count"] == "37",
        f"Unexpected XML validator findings: {schema}",
    )
    require(
        len(text_rows) == 2
        and Counter((row["severity"], row["rule_id"], row["character"]) for row in text_rows)
        == {("SOFT", "V116", "∅"): 2},
        f"Unexpected text validator findings: {text_rows}",
    )
    require(
        Counter((row["severity"], row["rule_id"]) for row in gloss_rows)
        == {("SOFT", "V061"): 97, ("SOFT", "V064"): 1},
        "Gloss finding inventory changed",
    )
    require(not duplicate_original, "Unexpected original-tier duplicate findings")
    require(
        len(duplicate_standard) == 2
        and {row["s_id"] for row in duplicate_standard}
        == SOURCE_DISTINCT_STANDARD_DUPLICATE_IDS
        and {row["severity"] for row in duplicate_standard} == {"SOFT"}
        and {row["normalized_text"] for row in duplicate_standard}
        == {"mulusu' ku tanang nay zais."},
        f"Unexpected standard-tier duplicate findings: {duplicate_standard}",
    )
    require(
        not any(row.get("severity") == "HARD" for row in registry_rows),
        f"Registry validator produced HARD findings: {registry_rows}",
    )

    run_rows = read_csv(qc_dir / "run_summary.tsv", delimiter="\t")
    prior = [row for row in run_rows if row["name"] != "adjudicate_findings"]
    require(
        {row["name"] for row in prior} == EXPECTED_COMMANDS
        and len(prior) == len(EXPECTED_COMMANDS)
        and all(row["exit_code"] == "0" for row in prior),
        "A guarded QC command failed or the command inventory changed",
    )
    dependency = json.loads((qc_dir / "public_dependency.json").read_text())
    require(
        dependency["before_clean"] is True
        and dependency["after_clean"] is True
        and dependency["modified"] is False
        and dependency["before_commit"] == dependency["after_commit"]
        and dependency["tool_tree_matches_origin_main"] is True
        and re.fullmatch(r"[0-9a-f]{40}", dependency["origin_main"]),
        "Public FormosanBank dependency guard failed",
    )
    require(
        not (qc_dir / "determinism_diff.txt").read_text().strip(),
        "Repeat build changed generated outputs",
    )
    require(
        not (qc_dir / "clean_xml_diff.txt").read_text().strip(),
        "Canonical cleaner changes final XML",
    )
    require(
        not (qc_dir / "standard_phon_diff.txt").read_text().strip(),
        "Shared standardization or phonology differs from final XML",
    )
    port_log = (qc_dir / "validate_port_readiness.log").read_text()
    require(
        "port-readiness: 0 HARD, 0 WARN" in port_log,
        f"Port-readiness layout, privacy, pin, or freshness checks failed:\n{port_log}",
    )

    roots = {path.name: ET.parse(path).getroot() for path in sorted(FINAL.glob("*.xml"))}
    by_id = {
        element.attrib["id"]: element
        for root in roots.values()
        for element in root.iter()
        if element.attrib.get("id")
    }
    totals = {
        tag: sum(len(root.findall(f".//{tag}")) for root in roots.values())
        for tag in ("S", "W", "M", "FORM", "PHON", "TRANSL", "AUDIO")
    }
    require(
        totals
        == {
            "S": 681,
            "W": 1768,
            "M": 2571,
            "FORM": 10040,
            "PHON": 10040,
            "TRANSL": 5038,
            "AUDIO": 0,
        },
        f"Unexpected final corpus shape: {totals}",
    )
    translation_topology = Counter(
        (
            element.tag,
            translation.attrib.get("kindOf", "untiered"),
        )
        for root in roots.values()
        for element in root.iter()
        if element.tag in {"S", "W", "M"}
        for translation in element.findall("TRANSL")
    )
    require(
        translation_topology
        == {
            ("S", "untiered"): 700,
            ("W", "original"): 1768,
            ("M", "original"): 2570,
        },
        f"Unexpected translation tier ownership: {translation_topology}",
    )
    require(
        {name: len(root.findall("S")) for name, root in roots.items()}
        == {
            "akiw_2012_sakizaya_affixes_examples.xml": 240,
            "akiw_2012_sakizaya_affixes_summary_rows.xml": 9,
            "akiw_2012_sakizaya_affixes_table_rows.xml": 432,
        },
        "Final per-source XML counts changed",
    )

    zero_sentence = by_id["AKIW_SZY_2012_EX_017D"]
    zero_word = by_id["AKIW_SZY_2012_EX_017DW1"]
    zero_null = by_id["AKIW_SZY_2012_EX_017DW1M1"]
    require(
        direct_text(zero_sentence, "FORM", "original")
        == "∅-imelang ci Taymu kiyu si-dinget."
        and direct_text(zero_sentence, "FORM", "standard")
        == "imelang ci Taymu kiyu sidinget."
        and direct_text(zero_word, "FORM", "original") == "∅-imelang"
        and direct_text(zero_word, "FORM", "standard") == "∅-imelang"
        and direct_text(zero_null, "FORM", "original") == "∅"
        and not zero_null.findall("TRANSL"),
        "Source-backed null-prefix representation changed",
    )

    extraction_rows = read_csv(ROOT / "CodeAndDocs/extraction_report.csv")
    table_rows = read_csv(ROOT / "CodeAndDocs/table_extraction_report.csv")
    summary_rows = read_csv(ROOT / "CodeAndDocs/summary_table_extraction_report.csv")
    require(
        Counter(row["status"] for row in extraction_rows)
        == {"include": 240, "excluded_exact_repeat": 12, "excluded_ungrammatical": 9},
        "Numbered source disposition inventory changed",
    )
    require(
        Counter(row["status"] for row in [*table_rows, *summary_rows])
        == {"include": 441, "excluded_exact_repeat": 106},
        "Table source disposition inventory changed",
    )

    source_audit = read_csv(ROOT / "CodeAndDocs/source_alignment_audit.csv")
    table_audit = read_csv(ROOT / "CodeAndDocs/table_output_audit.csv")
    format_audit = read_csv(ROOT / "CodeAndDocs/xml_format_audit.csv")
    spot_audit = read_csv(ROOT / "CodeAndDocs/source_spot_checks.csv")
    random_audit = read_csv(ROOT / "CodeAndDocs/random_source_checks.csv")
    complete_audit = read_csv(ROOT / "CodeAndDocs/complete_source_review.csv")
    coverage = read_csv(ROOT / "CodeAndDocs/page_coverage.csv")
    require(
        len(source_audit) == 261 and all(row["audit_status"] == "pass" for row in source_audit),
        "Source alignment audit failed",
    )
    require(
        len(table_audit) == 547 and all(row["audit_status"] == "pass" for row in table_audit),
        "Table output audit failed",
    )
    require(format_audit and all(row["status"] == "pass" for row in format_audit), "XML format audit failed")
    require(
        len(spot_audit) == 57 and all(row["status"] == "pass" for row in spot_audit),
        "Independent source spot checks failed",
    )
    require(
        len(random_audit) == 36 and all(row["status"] == "pass" for row in random_audit),
        "Seeded random source checks failed",
    )
    require(
        len(complete_audit) == 808 and all(row["result"] == "pass" for row in complete_audit),
        "Complete source review failed",
    )
    require(
        len(coverage) == 174
        and sum(int(row["source_report_rows"]) for row in coverage) == 808
        and sum(int(row["expected_xml_rows"]) for row in coverage) == 681,
        "Complete source coverage totals changed",
    )

    adjudicated: list[dict[str, str]] = [
        {
            "validator": "validate_xml",
            "severity": "SOFT",
            "rule_id": "V144",
            "location": "AKIW_SZY_2012_SAKIZAYA_AFFIXES_EXAMPLES",
            "count": "37",
            "status": "source_confirmed_non_actionable",
            "reason": (
                "The thesis supplies aligned M analysis only for some words. "
                "Missing M tiers are not synthesized where source segmentation or glosses are absent."
            ),
        }
    ]
    for row in text_rows:
        adjudicated.append(
            {
                "validator": "validate_text",
                "severity": row["severity"],
                "rule_id": row["rule_id"],
                "location": row["location"],
                "count": row.get("count", "1"),
                "status": "source_confirmed_non_actionable",
                "reason": (
                    "The canonical ∅ marker is source-backed by pages 17 and 18 and required "
                    "at W and M under POL-012; V116 is an expected inventory notice."
                ),
            }
        )
    for row in gloss_rows:
        if row["rule_id"] == "V064":
            reason = (
                "The source identifies a null prefix but supplies only the root/whole-word gloss 生病. "
                "The null M is preserved without inventing a gloss."
            )
        elif "_examples.xml" in row["file"]:
            reason = (
                "The source glosses the printed composite affix as one unit. "
                "No unattested morpheme gloss split is added."
            )
        else:
            reason = (
                "The source table pairs one complete affix analysis with one root analysis. "
                "Those two M tiers are preserved even when surface hyphen count differs."
            )
        adjudicated.append(
            {
                "validator": "validate_glosses",
                "severity": row["severity"],
                "rule_id": row["rule_id"],
                "location": row["location"],
                "count": row.get("count", "1"),
                "status": "source_confirmed_non_actionable",
                "reason": reason,
            }
        )
    for row in duplicate_standard:
        adjudicated.append(
            {
                "validator": "validate_duplicate_sentences",
                "severity": "SOFT",
                "rule_id": "source_distinct_standard_convergence",
                "location": f"S={row['s_id']} FORM=standard",
                "count": "1",
                "status": "source_confirmed_non_actionable",
                "reason": (
                    "Pages 99 and 112 print distinct original forms mu-lusu' and mulusu'. "
                    "Shared standardization correctly converges while both source occurrences retain stable IDs."
                ),
            }
        )

    cleaner_rows = read_csv(qc_dir / "cleaner_warnings.csv")
    require(
        len(cleaner_rows) == 1
        and cleaner_rows[0]["rule_id"] == "c002"
        and cleaner_rows[0]["s_id"] == "AKIW_SZY_2012_EX_046B"
        and cleaner_rows[0]["character"] == "'",
        f"Unexpected cleaner warning inventory: {cleaner_rows}",
    )
    adjudicated.append(
        {
            "validator": "clean_xml",
            "severity": "SOFT",
            "rule_id": "c002",
            "location": "S=AKIW_SZY_2012_EX_046B TRANSL=zho",
            "count": "1",
            "status": "source_confirmed_non_actionable",
            "reason": "The apostrophe is the source-confirmed name-final mark in Edi', not Chinese quotation punctuation.",
        }
    )

    excluded_rows: list[dict[str, str]] = []
    for dataset, rows in (
        ("numbered", extraction_rows),
        ("table", table_rows),
        ("summary", summary_rows),
    ):
        for row in rows:
            if row["status"] == "include":
                continue
            retained_id = row.get("retained_xml_id", "")
            if row["status"] == "excluded_exact_repeat":
                retained = by_id.get(retained_id)
                require(retained is not None, f"Exact repeat lacks retained XML: {dataset} {row}")
                require(
                    direct_text(retained, "FORM", "original") == row["form"],
                    f"Exact repeat link mismatch: {dataset} {row}",
                )
            else:
                unit_id = (
                    f"AKIW_SZY_2012_EX_{int(row['example']):03d}{row['subexample'].upper()}"
                )
                require(unit_id not in by_id and not retained_id, f"Ungrammatical exclusion leaked into XML: {row}")
            excluded_rows.append(
                {
                    "dataset": dataset,
                    "source_unit": (
                        f"{row['example']}{row['subexample']}" if dataset == "numbered" else row["seq"]
                    ),
                    "status": row["status"],
                    "source_form": row["form"],
                    "source_translation_or_meaning": row.get("translation_zho", row.get("meaning_zho", "")),
                    "source_gloss_or_context": row.get("source_gloss", row.get("source_context", "")),
                    "retained_xml_id": retained_id,
                }
            )
    require(
        Counter(row["status"] for row in excluded_rows)
        == {"excluded_exact_repeat": 118, "excluded_ungrammatical": 9},
        "Source exclusion inventory changed",
    )

    write_csv(
        qc_dir / "findings_adjudication.csv",
        adjudicated,
        ["validator", "severity", "rule_id", "location", "count", "status", "reason"],
    )
    write_csv(
        qc_dir / "source_exclusion_audit.csv",
        excluded_rows,
        [
            "dataset",
            "source_unit",
            "status",
            "source_form",
            "source_translation_or_meaning",
            "source_gloss_or_context",
            "retained_xml_id",
        ],
    )
    summary = {
        "audit_date": "2026-08-13",
        "basecamp_card_id": "8176965975",
        "build_deterministic": True,
        "complete_source_review_rows": 808,
        "final": {
            "files": 3,
            "sentences": totals["S"],
            "words": totals["W"],
            "morphemes": totals["M"],
            "original_forms": totals["FORM"] // 2,
            "standard_forms": totals["FORM"] // 2,
            "original_phonology": totals["PHON"] // 2,
            "standard_phonology": totals["PHON"] // 2,
            "translations": totals["TRANSL"],
            "sentence_translations_untiered": translation_topology[("S", "untiered")],
            "word_morpheme_translations_original": (
                translation_topology[("W", "original")]
                + translation_topology[("M", "original")]
            ),
            "word_morpheme_translations_untiered": 0,
            "word_morpheme_translations_standard": 0,
            "audio_references": totals["AUDIO"],
            "hard_findings": 0,
            "soft_finding_rows": len(adjudicated),
            "unresolved_findings": 0,
        },
        "source_units_accounted_for": 808,
        "source_exclusions": dict(Counter(row["status"] for row in excluded_rows)),
        "independent_source_spot_checks": 57,
        "seeded_random_source_checks": 36,
        "public_dependency": {
            "modified": False,
            "origin_main": dependency["origin_main"],
            "tool_tree_matches_origin_main": True,
        },
        "publication_status": "private development repository; ready to port but not published",
        "verdict": "ready to port",
    }
    (qc_dir / "qc_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"Adjudicated {len(adjudicated)} SOFT finding rows; "
        "0 HARD findings and 0 unresolved findings remain."
    )


if __name__ == "__main__":
    main()
