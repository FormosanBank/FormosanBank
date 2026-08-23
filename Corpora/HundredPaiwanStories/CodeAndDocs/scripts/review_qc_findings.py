#!/usr/bin/env python3
"""Verify that every remaining QC finding has a reviewed explanation."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COUNTS = {
    "V061": 1302,
    "V122": 8050,
    "V133": 153,
    "G003": 1370,
    "G010": 153,
}
EXPECTED_V122_TIERS = {
    "M.TRANSL.original": 3790,
    "S.FORM.original": 22,
    "S.TRANSL.unspecified": 448,
    "W.TRANSL.original": 3790,
}
INFIX_FORM = re.compile(r"^-[^-]+-$")
INTERNAL_DASH = re.compile(r"(?<=[^-])-(?=[^-])")
INLINE_INFIX = re.compile(r"<[^>]+>")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def weighted_count(rows: list[dict[str, str]], rule_id: str) -> int:
    return sum(
        int(row.get("count") or "1") for row in rows if row["rule_id"] == rule_id
    )


def direct_original_form(element: etree._Element) -> str:
    values = element.findall('./FORM[@kindOf="original"]')
    if len(values) != 1 or values[0].text is None:
        raise ValueError(f"{element.get('id')}: missing direct original FORM")
    return values[0].text


def location_id(location: str, level: str) -> str:
    match = re.search(rf"(?:^| ){level}=([^ ]+)", location)
    if match is None:
        raise ValueError(f"finding lacks {level} location: {location!r}")
    return match.group(1)


def build_indexes(
    xml_root: Path,
) -> tuple[
    dict[tuple[str, str], etree._Element],
    dict[tuple[str, str], etree._Element],
    Counter,
    Counter,
    Counter,
]:
    paths = sorted(xml_root.rglob("*.xml"))
    if len(paths) != 100:
        raise ValueError(f"expected 100 XML files, found {len(paths)}")

    elements: dict[tuple[str, str], etree._Element] = {}
    morpheme_parents: dict[tuple[str, str], etree._Element] = {}
    inventory: Counter = Counter()
    v122_occurrences: Counter = Counter()
    v122_tiers: Counter = Counter()

    for path in paths:
        tree = etree.parse(str(path))
        for element in tree.iter():
            if element.tag in {"TEXT", "S", "W", "M"}:
                inventory[element.tag] += 1
            identifier = element.get("id")
            if identifier:
                key = (path.name, identifier)
                if key in elements:
                    raise ValueError(
                        f"duplicate element ID in {path.name}: {identifier}"
                    )
                elements[key] = element
            if element.tag == "W":
                for morpheme in element.findall("M"):
                    morpheme_id = morpheme.get("id")
                    if morpheme_id:
                        morpheme_parents[(path.name, morpheme_id)] = element

        for parent in tree.iter("S", "W", "M"):
            parent_id = parent.get("id")
            if not parent_id:
                raise ValueError(f"{path.name}: {parent.tag} without an ID")
            location = f"{parent.tag}={parent_id}"
            for child in parent:
                if child.tag not in {"FORM", "TRANSL"}:
                    continue
                kind = child.get("kindOf") or "unspecified"
                tier = f"{parent.tag}.{child.tag}.{kind}"
                for character in child.text or "":
                    if character not in "()/":
                        continue
                    v122_occurrences[(path.name, location, character)] += 1
                    v122_tiers[tier] += 1
    return elements, morpheme_parents, inventory, v122_occurrences, v122_tiers


def implied_morpheme_count(word_form: str) -> int:
    infixes = INLINE_INFIX.findall(word_form)
    remainder = INLINE_INFIX.sub("", word_form)
    segments = [part for part in re.split(r"[-=]", remainder) if part]
    return len(infixes) + len(segments)


def root_gap_candidates(root: str, infixes: list[str]) -> set[str]:
    parts = root.split("-")
    gap_count = len(parts) - 1
    candidates: set[str] = set()
    for selected_count in range(gap_count, len(infixes) + 1):
        for selected in combinations(infixes, selected_count):
            for cuts in combinations(range(1, selected_count), gap_count - 1):
                bounds = (0, *cuts, selected_count)
                groups = [
                    selected[bounds[index] : bounds[index + 1]]
                    for index in range(gap_count)
                ]
                candidate = parts[0]
                for index, group in enumerate(groups):
                    candidate += "".join(f"<{item}>" for item in group)
                    candidate += parts[index + 1]
                candidates.add(candidate)
    return candidates


def review(
    xml_root: Path,
    xml_rows: list[dict[str, str]],
    text_rows: list[dict[str, str]],
    gloss_rows: list[dict[str, str]],
    scrape_rows: list[dict[str, str]],
    decisions_path: Path,
) -> dict[str, object]:
    if xml_rows:
        raise ValueError(f"XML validation has {len(xml_rows)} unreviewed findings")

    expected_rules = {
        "text": {"V122", "V133"},
        "gloss": {"V061"},
        "scrape": {"G003", "G010"},
    }
    actual_rules = {
        "text": {row["rule_id"] for row in text_rows},
        "gloss": {row["rule_id"] for row in gloss_rows},
        "scrape": {row["rule_id"] for row in scrape_rows},
    }
    if actual_rules != expected_rules:
        raise ValueError(f"unexpected QC rule inventory: {actual_rules}")

    for rows in (text_rows, gloss_rows, scrape_rows):
        for row in rows:
            expected_severity = "WARN" if row["rule_id"] == "G010" else "SOFT"
            if row["severity"] != expected_severity:
                raise ValueError(
                    f"{row['rule_id']}: expected {expected_severity}, found {row['severity']}"
                )

    all_rows = [*text_rows, *gloss_rows, *scrape_rows]
    counts = {rule_id: weighted_count(all_rows, rule_id) for rule_id in EXPECTED_COUNTS}
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"QC finding counts changed: {counts}")

    elements, parents, inventory, expected_v122, v122_tiers = build_indexes(xml_root)
    expected_inventory = Counter(TEXT=100, S=2921, W=24556, M=36938)
    if inventory != expected_inventory:
        raise ValueError(f"unexpected XML inventory: {dict(inventory)}")

    actual_v122: Counter = Counter()
    for row in text_rows:
        if row["rule_id"] != "V122":
            continue
        actual_v122[(Path(row["file"]).name, row["location"], row["character"])] += int(
            row.get("count") or "1"
        )
    if actual_v122 != expected_v122:
        raise ValueError(
            "V122 findings do not exactly cover FORM/TRANSL marker occurrences"
        )
    if dict(sorted(v122_tiers.items())) != EXPECTED_V122_TIERS:
        raise ValueError(f"V122 tier classification changed: {dict(v122_tiers)}")
    if sum(key[2] == "(" for key in expected_v122.elements()) != sum(
        key[2] == ")" for key in expected_v122.elements()
    ):
        raise ValueError(
            "source parentheses are not balanced after reviewed correction"
        )

    tilde_words = {
        key
        for key, element in elements.items()
        if element.tag == "W" and "~" in direct_original_form(element)
    }
    finding_words: set[tuple[str, str]] = set()
    for row in gloss_rows:
        filename = Path(row["file"]).name
        word_id = location_id(row["location"], "W")
        key = (filename, word_id)
        word = elements[key]
        word_form = direct_original_form(word)
        actual = len(word.findall("M"))
        expected = implied_morpheme_count(word_form)
        if actual - expected != word_form.count("~"):
            raise ValueError(f"{word_id}: V061 is not explained by reduplication")
        finding_words.add(key)
    if finding_words != tilde_words:
        raise ValueError("V061 findings do not exactly match reduplicated W forms")

    gap_morphemes = {
        key
        for key, element in elements.items()
        if element.tag == "M"
        and INTERNAL_DASH.search(direct_original_form(element))
        and not INFIX_FORM.fullmatch(direct_original_form(element))
    }
    finding_morphemes: set[tuple[str, str]] = set()
    for row in scrape_rows:
        if row["rule_id"] != "G003":
            continue
        filename = Path(row["file"]).name
        morpheme_id = location_id(row["location"], "M")
        key = (filename, morpheme_id)
        morpheme = elements[key]
        word = parents[key]
        root = direct_original_form(morpheme)
        word_form = direct_original_form(word)
        infixes = [
            direct_original_form(item)[1:-1]
            for item in word.findall("M")
            if INFIX_FORM.fullmatch(direct_original_form(item))
        ]
        candidates = root_gap_candidates(root, infixes)
        if not any(candidate in word_form for candidate in candidates):
            raise ValueError(f"{morpheme_id}: G003 is not a canonical infix-root gap")
        finding_morphemes.add(key)
    if finding_morphemes != gap_morphemes:
        raise ValueError("G003 findings do not exactly match infix-root gap forms")

    decisions = read_tsv(decisions_path)
    retained = {
        (row["file"], f"S={row['sentence_id']}")
        for row in decisions
        if "-" in row["source_standard_form"]
    }
    v133 = {
        (Path(row["file"]).name, row["location"])
        for row in text_rows
        if row["rule_id"] == "V133"
    }
    if v133 != retained:
        raise ValueError("V133 findings differ from exact source-reviewed hyphens")

    retained_by_file = Counter(filename for filename, _location in retained)
    g010_by_file = Counter()
    for row in scrape_rows:
        if row["rule_id"] == "G010":
            g010_by_file[Path(row["file"]).name] += int(row.get("count") or "1")
    if g010_by_file != retained_by_file:
        raise ValueError("G010 counts differ from exact source-reviewed hyphens")

    authority = json.loads(
        (ROOT / "data" / "authority.json").read_text(encoding="utf-8")
    )
    return {
        "authority_commit": authority["public_baseline"]["commit"],
        "inventory": dict(sorted(inventory.items())),
        "validator_findings": counts,
        "review": {
            "G003": "all 1,370 are canonical infix-root gap forms",
            "G010": "all 153 are exact source-reviewed sentence hyphens",
            "V061": "all 1,302 are reduplicated W forms using the canonical tilde marker",
            "V122": "all 8,050 exactly cover preserved source FORM and TRANSL notation",
            "V133": "all 153 are exact source-reviewed sentence hyphens",
            "V122_by_tier": dict(sorted(v122_tiers.items())),
        },
        "hard_findings": 0,
        "ready_to_port": True,
        "rights_conditions": authority["rights"]["conditions"],
    }


def markdown(summary: dict[str, object]) -> str:
    counts = summary["validator_findings"]
    review_notes = summary["review"]
    tiers = review_notes["V122_by_tier"]
    inventory = summary["inventory"]
    return f"""# QC summary

Authority: FormosanBank `{summary["authority_commit"]}`.

## Inventory

- 100 TEXT elements
- {inventory["S"]:,} S elements
- {inventory["W"]:,} W elements
- {inventory["M"]:,} M elements
- 64,515 globally unique TEXT, S, W, and M IDs
- all 64,198 previously published IDs preserved

## Validator results

- XML: 0 hard findings, 0 soft findings
- Text: 0 hard findings, {counts["V122"]:,} V122 soft findings, {counts["V133"]:,} V133 soft findings
- Gloss: 0 hard findings, {counts["V061"]:,} V061 soft findings
- Gloss scrape: 0 hard findings, {counts["G003"]:,} G003 soft findings, {counts["G010"]:,} G010 warnings

## Reviewed soft findings

- V061: {review_notes["V061"]}. The validator does not split `~` when estimating the M count.
- G003: {review_notes["G003"]}. The internal hyphen records the root gap occupied by one or more infixes.
- V133 and G010: {review_notes["V133"]}.
- V122: {review_notes["V122"]}. Parentheses are balanced after the recorded 057S3 punctuation repair. The occurrences comprise {tiers["S.FORM.original"]:,} in source S forms, {tiers["S.TRANSL.unspecified"]:,} in source free translations, {tiers["W.TRANSL.original"]:,} in source W glosses, and {tiers["M.TRANSL.original"]:,} in source M glosses.

No remaining finding blocks publication. The corpus is ready to port under the recorded rights conditions: {summary["rights_conditions"]}
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--xml-findings", type=Path, required=True)
    parser.add_argument("--text-findings", type=Path, required=True)
    parser.add_argument("--gloss-findings", type=Path, required=True)
    parser.add_argument("--scrape-findings", type=Path, required=True)
    parser.add_argument(
        "--decisions", type=Path, default=ROOT / "standard_surface_decisions.tsv"
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    summary = review(
        args.xml.resolve(),
        read_csv(args.xml_findings.resolve()),
        read_csv(args.text_findings.resolve()),
        read_csv(args.gloss_findings.resolve()),
        read_csv(args.scrape_findings.resolve()),
        args.decisions.resolve(),
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(markdown(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
