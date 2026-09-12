#!/usr/bin/env python3
"""Fail closed unless every validator finding matches reviewed source evidence."""

from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
_BANK = Path(__file__).resolve().parents[4]
if str(_BANK) not in sys.path:
    sys.path.insert(0, str(_BANK))
from build_lexical_xml import included_entries, load_ledger, xml_entries  # noqa: E402
from QC.xml_forms import base_form_text, iter_base_forms  # noqa: E402

EXPECTED_XML_PATHS = {
    "bzg": "Babuza-Favorlang/latham_1862_favorlang.xml",
    "fos": "Siraya/latham_1862_sideia_sida.xml",
}


def read_csv(path: Path, *, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def canonical_file(value: str, xml_root: Path) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path.resolve().relative_to(xml_root))
    if "XML" in path.parts:
        index = path.parts.index("XML")
        return str(Path(*path.parts[index + 1 :]))
    return str(path)


def source_locator(row: dict[str, str]) -> str:
    return (
        f"printed p. {row['printed_page']} / "
        f"{row['source_variety']} / {row['english']}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--source-ledger", type=Path, required=True)
    parser.add_argument("--duplicate-review", type=Path, required=True)
    parser.add_argument("--xml-root", type=Path, required=True)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    xml_root = args.xml_root.resolve()

    source_map: dict[str, dict[str, str]] = {}
    for entry in xml_entries(included_entries(load_ledger(args.source_ledger))):
        row = {key: str(value) for key, value in asdict(entry).items()}
        row["alternate_forms"] = " | ".join(entry.alternate_forms)
        record_id = entry.s_id
        if record_id in source_map:
            raise SystemExit(f"Duplicate source-ledger XML ID: {record_id}")
        source_map[record_id] = row

    xml: dict[str, dict[str, object]] = {}
    xml_paths = sorted(xml_root.rglob("*.xml"))
    actual_paths = {str(path.relative_to(xml_root)) for path in xml_paths}
    if actual_paths != set(EXPECTED_XML_PATHS.values()):
        raise SystemExit(f"Unexpected XML paths: {sorted(actual_paths)}")
    for path in xml_paths:
        root = ET.parse(path).getroot()
        language = root.get("{http://www.w3.org/XML/1998/namespace}lang", "")
        if str(path.relative_to(xml_root)) != EXPECTED_XML_PATHS.get(language):
            raise SystemExit(f"Unexpected language/path mapping: {path}")
        for sentence in root.findall("S"):
            record_id = sentence.get("id", "")
            # Base first, then its variants -- not document order. POL-020
            # does not order FORM siblings, so a positional comparison
            # against the ledger would depend on how the file happens to
            # be written.
            bases = [f.text or "" for f in iter_base_forms(sentence, "original")]
            variants = [f.text or "" for f in sentence.findall("FORM")
                        if f.get("ver") is not None]
            forms = bases + variants
            if not record_id or record_id in xml:
                raise SystemExit(f"Duplicate or empty XML ID: {record_id}")
            xml[record_id] = {
                "file": str(path.relative_to(xml_root)),
                "forms": forms,
                "original": base_form_text(sentence, "original"),
                "standard": base_form_text(sentence, "standard"),
                "has_w": sentence.find("W") is not None,
            }
    if set(xml) != set(source_map):
        raise SystemExit("XML and included source-ledger IDs do not match")
    for record_id, row in source_map.items():
        expected_forms = [row["form"]]
        expected_forms.extend(
            form for form in row["alternate_forms"].split(" | ") if form
        )
        if (
            xml[record_id]["original"] != row["form"]
            or xml[record_id]["standard"] != ""
            or xml[record_id]["forms"] != expected_forms
        ):
            raise SystemExit(f"XML/source-ledger form mismatch: {record_id}")

    review_rows: list[dict[str, str]] = []
    accepted = 0
    unresolved = 0

    expected_xml = Counter(value["file"] for value in xml.values())
    actual_xml: Counter[str] = Counter()
    for row in read_csv(run_dir / "validate_xml_findings.csv"):
        count = int(row.get("count") or 1)
        file = canonical_file(row["file"], xml_root)
        is_accepted = (
            row.get("severity", "").upper() == "SOFT"
            and row.get("rule_id") == "V014"
            and file in expected_xml
        )
        if is_accepted:
            actual_xml[file] += count
        accepted += count if is_accepted else 0
        unresolved += 0 if is_accepted else count
        review_rows.append({
            "validator": "validate_xml_findings.csv",
            "severity": row.get("severity", ""),
            "rule_or_tier": row.get("rule_id", ""),
            "evidence": file,
            "finding_count": str(count),
            "resolution": "accepted" if is_accepted else "unresolved",
            "rationale": "Standard FORM omitted under the merged August 12 corpus ruling."
                         if is_accepted else "Unexpected structural finding.",
        })
    if actual_xml != expected_xml:
        unresolved += sum((actual_xml - expected_xml).values())
        unresolved += sum((expected_xml - actual_xml).values())

    # With all source readings correctly tiered, neither validator has an
    # accepted finding. Keep any new result visible and require source review.
    for filename in ("validate_text_findings.csv", "validate_glosses_findings.csv"):
        for row in read_csv(run_dir / filename):
            count = int(row.get("count") or 1)
            unresolved += count
            review_rows.append({
                "validator": filename,
                "severity": row.get("severity", ""),
                "rule_or_tier": row.get("rule_id", ""),
                "evidence": row.get("location", ""),
                "finding_count": str(count),
                "resolution": "unresolved",
                "rationale": "Unexpected finding; inspect the XML and source.",
            })

    # However many groups the review file documents -- none, since the
    # Sida column left and both former groups needed a Sida record. The
    # count is not asserted: a corpus that gains or loses a duplicate
    # should update the review file, not trip a constant here.
    duplicate_review = read_csv(args.duplicate_review)
    for filename, tier, form_field in [
        ("duplicate_original_findings.csv", "original", "normalized_original"),
    ]:
        expected = {row[form_field]: row for row in duplicate_review}
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in read_csv(run_dir / filename):
            groups[row["normalized_text"]].append(row)
        for form, rows in sorted(groups.items()):
            reviewed = expected.get(form)
            ids = {row["s_id"] for row in rows}
            locators = {source_locator(source_map[record_id]) for record_id in ids}
            expected_ids = (
                set(reviewed["xml_ids"].split(" | ")) if reviewed else set()
            )
            expected_locators = (
                set(reviewed["source_locators"].split(" | "))
                if reviewed
                else set()
            )
            is_accepted = (
                reviewed is not None
                and ids == expected_ids
                and locators == expected_locators
                and len(rows) == len(expected_ids)
                and all(
                    row["severity"].upper() == reviewed["expected_severity"]
                    and canonical_file(row["file"], xml_root)
                    == xml[row["s_id"]]["file"]
                    and row["raw_text"] == form
                    and xml[row["s_id"]][tier] == form
                    for row in rows
                )
            )
            accepted += 1 if is_accepted else 0
            unresolved += 0 if is_accepted else 1
            review_rows.append(
                {
                    "validator": filename,
                    "severity": reviewed["expected_severity"] if reviewed else "",
                    "rule_or_tier": f"duplicate_{tier}",
                    "evidence": ";".join(sorted(ids)),
                    "finding_count": str(len(rows)),
                    "resolution": "accepted" if is_accepted else "unresolved",
                    "rationale": (
                        reviewed["rationale"]
                        if is_accepted
                        else "Duplicate group did not match the exact review."
                    ),
                }
            )
        if set(groups) != set(expected):
            unresolved += len(set(groups).symmetric_difference(expected))

    output = run_dir / "accepted_findings_review.csv"
    fields = [
        "validator",
        "severity",
        "rule_or_tier",
        "evidence",
        "finding_count",
        "resolution",
        "rationale",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(review_rows)
    print(
        f"Reviewed {accepted + unresolved} finding occurrences/groups: "
        f"{accepted} accepted, {unresolved} unresolved"
    )
    print(f"Wrote {output}")
    if unresolved:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
