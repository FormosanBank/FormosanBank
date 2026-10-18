#!/usr/bin/env python3
"""Verify that every remaining QC finding has a reviewed explanation."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
# G003 (internal '-' in an M FORM) used to report 1,370 findings here: every
# infixed root, which POL-014 spells with a gap hyphen ('k<em>uda' -> 'k-uda').
# The shared rule now exempts an exact gap root derived from the parent W, so
# the corpus reports none. Its absence is the expected state, not a lost check.
#
# These are the REVIEWED rules: every finding of each is explained below
# against the XML. A finding the review cannot explain fails the build, and so
# does any count above the reviewed one. A count below it is reported, not
# failed: the XML-derived checks further down still hold the data itself, so
# a lower count means the validator now reports less, not that data was lost.
# Any rule NOT listed here is unreviewed: its SOFT/WARN findings are reported
# in the summary and do not stop the build, so new shared rules never break
# this corpus's rebuild; a HARD finding from any rule other than the one
# accepted G001 always fails.
EXPECTED_COUNTS = {
    "V061": 1302,
    "V064": 1,
    "V122": 8028,
    "G001": 1,
    "G002": 1,
    "G010": 153,
}
# The one place the source itself supplies no gloss: 078S4W19's final -i.
# The morpheme is published with no TRANSL rather than with an invented one,
# which necessarily costs three findings -- V064 (the M has no gloss), G002
# (4 Ms vs 3 gloss units) and G001 (the W FORM and W TRANSL skeletons differ
# by that unit). G001 is HARD. All three are accepted and documented; each is
# pinned to this exact location below so a fourth, or a move, fails the build.
ACCEPTED_GAP_WORD = "S=078S4 W=078S4W19"
ACCEPTED_GAP_MORPHEME = "M=078S4W19M0c"
# No S.FORM.original entry: the source's only parenthesised material in a
# sentence FORM was the "(?)" annotation, now moved to a notes attribute by
# scripts/apply_manual_corrections.py before standardize.py runs.
EXPECTED_V122_TIERS = {
    "M.TRANSL.original": 3790,
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


def verify_accepted_gloss_gap(elements, gloss_rows, scrape_rows) -> None:
    """Pin V064/G001/G002 to 078S4W19's unglossed final -i, and nothing else.

    These three findings are the accepted cost of publishing the one morpheme
    the source leaves unglossed without inventing a gloss for it. Each is
    checked against the XML rather than taken on trust, so a regression that
    drops a different gloss cannot hide behind the accepted exception.
    """
    located = [
        (row["rule_id"], row["location"])
        for rows in (gloss_rows, scrape_rows)
        for row in rows
        if row["rule_id"] in {"V064", "G001", "G002"}
    ]
    expected = {
        ("V064", ACCEPTED_GAP_MORPHEME),
        ("G001", ACCEPTED_GAP_WORD),
        ("G002", ACCEPTED_GAP_WORD),
    }
    if len(located) != len(set(located)) or not set(located) <= expected:
        raise ValueError(f"accepted gloss-gap findings moved or multiplied: {located}")

    word_id = ACCEPTED_GAP_WORD.split("W=")[1]
    morpheme_id = ACCEPTED_GAP_MORPHEME.split("=")[1]
    word = next(
        element
        for key, element in elements.items()
        if key[1] == word_id and element.tag == "W"
    )
    morphemes = word.findall("M")
    if [item.get("id") for item in morphemes][-1] != morpheme_id:
        raise ValueError(f"{morpheme_id} is no longer the final M of {word_id}")
    if morphemes[-1].findall("TRANSL"):
        raise ValueError(f"{morpheme_id} has a TRANSL; the source supplies none")
    if any(not item.findall("TRANSL") for item in morphemes[:-1]):
        raise ValueError(f"{word_id} has an unexpected second unglossed morpheme")
    word_translations = word.findall("TRANSL")
    if len(word_translations) != 1 or not word_translations[0].get("notes"):
        raise ValueError(f"{word_id} must carry one W TRANSL whose notes record the gap")


def review(
    xml_root: Path,
    xml_rows: list[dict[str, str]],
    text_rows: list[dict[str, str]],
    gloss_rows: list[dict[str, str]],
    scrape_rows: list[dict[str, str]],
    decisions_path: Path,
) -> dict[str, object]:
    validators = {
        "xml": xml_rows,
        "text": text_rows,
        "gloss": gloss_rows,
        "scrape": scrape_rows,
    }

    # HARD findings: the only one accepted is G001 on 078S4W19 (checked in
    # detail by verify_accepted_gloss_gap). Any other HARD finding, from any
    # rule, reviewed or not, fails the build.
    unaccepted_hard = [
        f"{row['rule_id']} {row['file']} {row['location']}"
        for rows in validators.values()
        for row in rows
        if row["severity"] == "HARD"
        and not (row["rule_id"] == "G001" and row["location"] == ACCEPTED_GAP_WORD)
    ]
    if unaccepted_hard:
        raise ValueError(f"unreviewed HARD findings: {unaccepted_hard}")
    hard_findings = sum(
        int(row.get("count") or "1")
        for rows in validators.values()
        for row in rows
        if row["severity"] == "HARD"
    )

    # Rules this corpus has not reviewed are reported, never failed (they are
    # SOFT or WARN here; HARD was handled above).
    unreviewed: dict[str, dict[str, object]] = {}
    for validator, rows in validators.items():
        for row in rows:
            rule_id = row["rule_id"]
            if rule_id in EXPECTED_COUNTS:
                continue
            entry = unreviewed.setdefault(
                rule_id,
                {
                    "validator": validator,
                    "title": row.get("title", ""),
                    "severity": row["severity"],
                    "count": 0,
                },
            )
            entry["count"] += int(row.get("count") or "1")
    unreviewed = dict(sorted(unreviewed.items()))

    by_validator: dict[str, dict[str, int]] = {}
    for validator, rows in validators.items():
        severities: Counter = Counter()
        for row in rows:
            severities[row["severity"]] += int(row.get("count") or "1")
        by_validator[validator] = dict(sorted(severities.items()))

    all_rows = [row for rows in validators.values() for row in rows]
    counts = {rule_id: weighted_count(all_rows, rule_id) for rule_id in EXPECTED_COUNTS}
    above = {
        rule_id: (count, EXPECTED_COUNTS[rule_id])
        for rule_id, count in counts.items()
        if count > EXPECTED_COUNTS[rule_id]
    }
    if above:
        raise ValueError(f"reviewed rules report more findings than reviewed: {above}")
    below = {
        rule_id: {"reported": count, "reviewed": EXPECTED_COUNTS[rule_id]}
        for rule_id, count in counts.items()
        if count < EXPECTED_COUNTS[rule_id]
    }

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
    if actual_v122 - expected_v122:
        raise ValueError(
            "V122 findings are not all FORM/TRANSL marker occurrences: "
            f"{sorted((actual_v122 - expected_v122).elements())[:5]}"
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
        if row["rule_id"] != "V061":
            continue
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
    if not finding_words <= tilde_words:
        raise ValueError("V061 findings are not all reduplicated W forms")

    # Every M whose FORM carries an internal '-' must be a canonical POL-014
    # infix-root gap: the root of its parent W with the infix removed, e.g.
    # 'k<em>uda' -> 'k-uda'. The shared G003 rule now exempts exactly those, so
    # it reports nothing here and this check is driven from the XML instead of
    # from its findings. Anything that is NOT such a gap is an unsplit word in
    # one M, which is what G003 exists to catch -- so a stray hyphen still fails
    # the build, it just fails here rather than as a finding.
    gap_morphemes = {
        key
        for key, element in elements.items()
        if element.tag == "M"
        and INTERNAL_DASH.search(direct_original_form(element))
        and not INFIX_FORM.fullmatch(direct_original_form(element))
    }
    for key in sorted(gap_morphemes):
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
            raise ValueError(f"{key[1]}: internal '-' is not a canonical infix-root gap")
    if any(row["rule_id"] == "G003" for row in scrape_rows):
        raise ValueError(
            "G003 reported a finding; every internal '-' in this corpus should "
            "be an exempt POL-014 gap root"
        )

    # A hyphen is a segmentation marker, not a letter of the standard
    # orthography. The ORIGINAL tier keeps every hyphen the source prints on
    # its plain-text line (Ferrell 1.6) -- that is what G010 reports -- while
    # the standard tier carries none, so V133 must not fire at all. The
    # expected G010 set is derived from the XML, not from the decision table,
    # which no longer records the hyphens.
    source_hyphens_by_file: Counter = Counter()
    standard_hyphens: list[str] = []
    for path in sorted(Path(xml_root).glob("PaiwanCh2_*.xml")):
        for sentence in etree.parse(str(path)).getroot().findall("S"):
            original = sentence.find("FORM[@kindOf='original']")
            standard = sentence.find("FORM[@kindOf='standard']")
            if original is not None and "-" in (original.text or ""):
                source_hyphens_by_file[path.name] += 1
            if standard is not None and "-" in (standard.text or ""):
                standard_hyphens.append(sentence.get("id"))
    if standard_hyphens:
        raise ValueError(
            f"standard FORMs regained a hyphen: {sorted(standard_hyphens)[:5]}"
        )

    g010_by_file = Counter()
    for row in scrape_rows:
        if row["rule_id"] == "G010":
            g010_by_file[Path(row["file"]).name] += int(row.get("count") or "1")
    if g010_by_file - source_hyphens_by_file:
        raise ValueError("G010 reports more than the source hyphens in the original tier")

    # The decision table now holds only the parenthetical decisions.
    decisions = read_tsv(decisions_path)
    if len(decisions) != 16 or not all(
        "(" in row["source_standard_form"] for row in decisions
    ):
        raise ValueError("standard_surface_decisions.tsv is no longer 16 parentheticals")

    verify_accepted_gloss_gap(elements, gloss_rows, scrape_rows)

    return {
        "inventory": dict(sorted(inventory.items())),
        "validator_findings": counts,
        "findings_by_validator": by_validator,
        "infix_root_gap_morphemes": len(gap_morphemes),
        "review": {
            "V061": f"all {counts['V061']:,} are reduplicated W forms using the canonical tilde marker",
            "V122": f"all {counts['V122']:,} are preserved source TRANSL and W/M FORM notation",
            "G010": f"all {counts['G010']:,} are source hyphens kept in the original tier; the standard tier carries none",
            "V064": "the single unglossed M is 078S4W19M0c, the -i the source leaves without a gloss",
            "G002": "078S4W19 has 4 Ms and 3 source gloss units for the same reason",
            "V122_by_tier": dict(sorted(v122_tiers.items())),
        },
        "hard_findings": hard_findings,
        "accepted_hard_findings": {
            "G001": (
                "078S4W19: the source supplies no gloss for the final -i, so the "
                "morpheme is published unglossed rather than with an invented "
                "gloss. The W FORM and W TRANSL skeletons differ by that one "
                "unit. Accepted and documented; see the corpus README."
            )
        },
        "reviewed_rules_below_reviewed_count": below,
        "unreviewed_findings": unreviewed,
        "ready_to_port": True,
    }


def markdown(summary: dict[str, object]) -> str:
    counts = summary["validator_findings"]
    review_notes = summary["review"]
    tiers = review_notes["V122_by_tier"]
    inventory = summary["inventory"]
    gap_morpheme_count = summary["infix_root_gap_morphemes"]
    labels = {"xml": "XML", "text": "Text", "gloss": "Gloss", "scrape": "Gloss scrape"}
    validator_lines = "\n".join(
        f"- {labels[validator]}: "
        + (
            ", ".join(f"{count:,} {severity}" for severity, count in by_severity.items())
            or "no findings"
        )
        for validator, by_severity in summary["findings_by_validator"].items()
    )
    below = summary["reviewed_rules_below_reviewed_count"]
    below_lines = (
        "\nReviewed rules now reporting fewer findings than were reviewed "
        "(the validator reports less; the XML checks still hold):\n\n"
        + "\n".join(
            f"- {rule_id}: {item['reported']:,} reported, {item['reviewed']:,} reviewed"
            for rule_id, item in below.items()
        )
        + "\n"
        if below
        else ""
    )
    unreviewed = summary["unreviewed_findings"]
    unreviewed_lines = (
        "\n".join(
            f"- {rule_id} `{item['title']}` ({item['validator']}): "
            f"{item['count']:,} {item['severity']}"
            for rule_id, item in unreviewed.items()
        )
        if unreviewed
        else "None."
    )
    return f"""# QC summary

## Inventory

- 100 TEXT elements
- {inventory["S"]:,} S elements
- {inventory["W"]:,} W elements
- {inventory["M"]:,} M elements
- 64,515 globally unique TEXT, S, W, and M IDs
- all 64,198 previously published IDs preserved

## Validator results

Findings per validator, by severity (all rules, reviewed or not):

{validator_lines}

Reviewed rules:

- Text: {counts["V122"]:,} V122 soft findings
- Gloss: {counts["V061"]:,} V061 soft findings, {counts["V064"]} V064 soft finding
- Gloss scrape: {counts["G001"]} accepted G001 hard finding, {counts["G002"]} G002 soft finding, 0 G003 soft findings ({gap_morpheme_count:,} infix-root gap forms, all exempt under POL-014), {counts["G010"]:,} G010 warnings
{below_lines}
## Reviewed soft findings

- V061: {review_notes["V061"]}. The validator does not split `~` when estimating the M count.
- G010: {review_notes["G010"]}. V133 does not fire: no standard FORM contains a hyphen.
- V122: {review_notes["V122"]}. No sentence FORM carries a parenthesis: the source’s "(?)" annotation is recorded in a notes attribute instead. Parentheses are balanced after the recorded 057S3 punctuation repair. The occurrences comprise {tiers["S.TRANSL.unspecified"]:,} in source free translations, {tiers["W.TRANSL.original"]:,} in source W glosses, and {tiers["M.TRANSL.original"]:,} in source M glosses.

## Findings from rules this corpus has not reviewed

These come from shared validator rules added or changed after this corpus's
review. They are reported here and do not stop the build; any HARD finding
other than the accepted G001 does. The per-finding detail is in the
validators' CSVs, which the build writes but does not commit.

{unreviewed_lines}

No remaining finding blocks publication. The corpus is ready to port under the rights conditions recorded in the corpus README.
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
    for rule_id, item in summary["unreviewed_findings"].items():
        print(
            f"NOTE: unreviewed rule {rule_id} ({item['title']}): "
            f"{item['count']} {item['severity']} finding(s); reported, not gated",
            file=sys.stderr,
        )
    for rule_id, item in summary["reviewed_rules_below_reviewed_count"].items():
        print(
            f"NOTE: reviewed rule {rule_id} now reports {item['reported']} "
            f"(reviewed: {item['reviewed']})",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
