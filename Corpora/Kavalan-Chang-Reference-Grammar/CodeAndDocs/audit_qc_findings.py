#!/usr/bin/env python3
"""Enforce and document the exact expected canonical QC findings.

The validators are FormosanBank's, from the checkout validate.sh is given: normally main at HEAD (POL-052).
The counts below are main's at the commit recorded in provenance.json; when main's validators change, this list is
restated, not the corpus bent to fit it."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from xml.etree import ElementTree as ET

import build_xml


EXPECTED = {
    "validate_xml": Counter({("SOFT", "V144"): 1}),
    "validate_text": Counter({("SOFT", "V142"): 3}),
    "validate_glosses": Counter(
        {
            ("SOFT", "V061"): 10,
            ("SOFT", "V065"): 3,
            ("SOFT", "V153"): 1,
        }
    ),
}
# Findings reported once for the whole file, with a count instead of a sentence: their count and exact message.
EXPECTED_FILE_COUNTS = {"V144": "6", "V153": "13"}
EXPECTED_FILE_MESSAGES = {
    "V144": "V144 SOFT: 6 W elements in 5 of 405 morphologically parsed sentences have no M child — allowed (no M = "
            "segmentation unknown, POL-057); confirm each is deliberately unsegmented",
    "V153": "V153 SOFT: 13 words whose gloss claims a different number of morphemes than the form implies, e.g. "
            "'ti-buya' (2) vs '人名' (1)",
}
# Findings reported per sentence or word: exactly where they are, so a ledger never names the wrong words.
EXPECTED_LOCATIONS = {
    "V061": frozenset({
        "S=S-p048l-e002 W=S-p048l-e002W5", "S=S-p048l-e002 W=S-p048l-e002W7", "S=S-p070l-e007 W=S-p070l-e007W1",
        "S=S-p077l-e002 W=S-p077l-e002W4", "S=S-p100r-e002 W=S-p100r-e002W2", "S=S-p101l-e003 W=S-p101l-e003W4",
        "S=S-p101r-e001 W=S-p101r-e001W1", "S=S-p101r-e002 W=S-p101r-e002W2", "S=S-p101r-e006 W=S-p101r-e006W2",
        "S=S-p102r-e008 W=S-p102r-e008W2"}),
    "V065": frozenset({"W=S-p086r-e004W1", "W=S-p086r-e005W1", "W=S-p103l-e002W1"}),
    "V142": frozenset({"S=S-p080r-e003", "S=S-p091l-e001", "S=S-p091r-e001"}),
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def unit_id(location: str) -> str | None:
    match = re.search(r"S=S-(p\d{3}[lr]-e\d{3})", location)
    if match is None:
        match = re.search(r"[WM]=S-(p\d{3}[lr]-e\d{3})", location)
    return match.group(1) if match else None


def disposition(validator: str, row: dict[str, str]) -> tuple[str, str]:
    rule = row["rule_id"]
    if rule == "V153":
        return (
            "word_tier_infix_notation_and_alignment",
            "13 words: 7 without morphemes whose printed gloss's pieces do not line up with the form's (ti-buya, "
            "ti-utay, u-rima=pa, s<um>ulal, kay-kaying, sin-sinngut-an-ku, se-sumkir; ruled to have none); the two "
            "locative pronouns ti-maiku-an and ta-maiku, glossed 我（處所） as one piece and split as p. 80 glosses "
            "ti-maisu-an (ruled 2026-11-08); 3 ta-...-an circumfix words whose -an the book leaves unglossed (one "
            "morpheme, ruled 2026-11-07; the slot is the frame's second half, ruled 2026-11-08); 1 hyphen inside a "
            "parenthesis (知道=動貌（-他）).",
        )
    if rule == "V144":
        return (
            "source_alignment_limit",
            "Six W in sentences whose other words are analysed have no M: five because their printed gloss's pieces "
            "do not match the form's (ti-buya, ti-utay, kay-kaying glossed as one piece; u-rima=pa and "
            "sin-sinngut-an-ku with the first piece unglossed; the maintainer, 2026-11-08: \"These should have no "
            "Ms.\"), and paqenanum, the handwritten word whose gloss the book does not give (2026-11-08: "
            "\"paqenanum does not have an M.\").",
        )
    if rule == "V142":
        return (
            "false_lexical_trigger",
            "The word marginal appears in provenance notes about excluded handwritten material and is not an acceptability judgment on the sentence.",
        )
    if rule == "V061":
        return (
            "source_alignment_limit",
            "Seven words have no M because their printed gloss's pieces do not match the form's (five are glossed "
            "as one piece; u-rima=pa and sin-sinngut-an-ku leave the first piece unglossed), and in three ta-...-an "
            "words the circumfix is one morpheme, ta-an (POL-014; ruled 2026-11-07), where the validator counts its "
            "two halves as two.",
        )
    if rule == "V134":
        return (
            "infix_angle_brackets_in_sentence_line",
            "The sentence line writes an infix in angle brackets, as the word FORM does (maintainer, audit round 1, "
            "2026-11-09: \"the sentence line should change hyphens to <> for infixes\"); V134 reports each < and >. "
            "The standard tier drops them (C012).",
        )
    if rule == "V065":
        return (
            "source_has_no_word_gloss",
            "The book glosses no word of these sentences (ita; footnote 41's tama and tina), so their words carry "
            "no gloss (POL-061 as amended 2026-10-18).",
        )
    raise ValueError(f"no disposition for {validator} {rule}")


def audit_validator(
    validator: str,
    path: Path,
    source_units: set[str],
) -> list[dict[str, str]]:
    rows = read_rows(path)
    actual = Counter((row["severity"], row["rule_id"]) for row in rows)
    expected = Counter(EXPECTED[validator])
    v134 = {}
    if validator == "validate_text":
        # V134, one finding per < and > in a sentence line: expected exactly where the sentence lines have infixes.
        for sentence in ET.parse(build_xml.OUT_XML).getroot().findall("S"):
            line = sentence.findtext("FORM[@kindOf='original']") or ""
            if "<" in line or ">" in line:
                v134[f"S={sentence.get('id')}"] = line.count("<") + line.count(">")
        if v134:
            expected[("SOFT", "V134")] = sum(v134.values())
    if actual != expected:
        raise ValueError(f"unexpected {validator} findings: {dict(actual)!r}")
    found_v134 = Counter(row["location"] for row in rows if row["rule_id"] == "V134")
    if found_v134 != Counter(v134):
        raise ValueError(f"V134 is not exactly the sentence lines' infix brackets: {sorted(set(found_v134) ^ set(v134))}")
    for rule, expected in EXPECTED_LOCATIONS.items():
        found = {row["location"] for row in rows if row["rule_id"] == rule}
        if any(row["rule_id"] == rule for row in rows) and found != expected:
            raise ValueError(f"{rule} locations changed: {sorted(found ^ expected)}")
    reviewed = []
    for row in rows:
        if row["rule_id"] in EXPECTED_FILE_COUNTS:
            if row["message"] != EXPECTED_FILE_MESSAGES[row["rule_id"]]:
                raise ValueError(f"{row['rule_id']} message changed: {row['message']!r}")
            expected_count = EXPECTED_FILE_COUNTS[row["rule_id"]]
            if row["count"] != expected_count:
                raise ValueError(
                    f"{row['rule_id']} count changed: {row['count']} != {expected_count}"
                )
        else:
            source_unit = unit_id(row["location"])
            if source_unit is None or source_unit not in source_units:
                raise ValueError(
                    f"{validator} finding lacks a reviewed source unit: {row['location']}"
                )
        status, justification = disposition(validator, row)
        reviewed.append(
            {
                "validator": validator,
                "severity": row["severity"],
                "rule_id": row["rule_id"],
                "location": row["location"],
                "count": row["count"],
                "disposition": status,
                "justification": justification,
            }
        )
    return reviewed


def write_review(path: Path, rows: list[dict[str, str]]) -> None:
    fields = [
        "validator",
        "severity",
        "rule_id",
        "location",
        "count",
        "disposition",
        "justification",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validate-xml", type=Path, required=True)
    parser.add_argument("--validate-text", type=Path, required=True)
    parser.add_argument("--validate-glosses", type=Path, required=True)
    parser.add_argument("--duplicates-original", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    duplicates = read_rows(args.duplicates_original)
    if duplicates:
        raise ValueError(f"duplicate validator produced {len(duplicates)} finding(s)")
    source_units = {unit.unit_id for unit in build_xml.load_source_units()}
    reviewed = []
    reviewed.extend(audit_validator("validate_xml", args.validate_xml, source_units))
    reviewed.extend(audit_validator("validate_text", args.validate_text, source_units))
    reviewed.extend(
        audit_validator("validate_glosses", args.validate_glosses, source_units)
    )
    write_review(args.output, reviewed)

    counts = Counter(
        (row["severity"], row["rule_id"], row["disposition"]) for row in reviewed
    )
    print(f"reviewed_findings={len(reviewed)}")
    for (severity, rule, status), count in sorted(counts.items()):
        print(f"{severity} {rule} {status}: {count}")
    print("unresolved_unrecorded_findings=0")
    print("publication_blockers=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
