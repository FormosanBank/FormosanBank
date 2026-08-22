#!/usr/bin/env python3
"""Apply exact, source-reviewed direct-sentence surface decisions."""

from __future__ import annotations

import argparse
import csv
import json
import re
import string
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_XML_PATH = ROOT.parent / "XML"
DECISIONS_PATH = ROOT / "intermediate" / "standard_surface_decisions.tsv"
DICTIONARY_NAME = "Song_2018_Kanakanavu_Grammar_Dictionary.xml"
GRAMMAR_NAME = "Song_2018_Kanakanavu_Grammar.xml"
EXPECTED_DECISIONS = 128
EXPECTED_DICTIONARY_DECISIONS = 125
EXPECTED_GRAMMAR_DECISIONS = 3
EXPECTED_BOUND_EXCLUSIONS = 11
BOUND_EXCLUDED_CLASS = "bound_form_entry_excluded"
EXPECTED_DICTIONARY_EXTRA_ENTRIES = 140
EXPECTED_DICTIONARY_ENTRIES = 870
# Split variants whose (form, translation) duplicates another record's entry.
# The source prints these forms as their own records (e.g. the pronoun
# case-form lists in records 0070-0074 repeat the standalone pronoun entries,
# and record pairs such as 0209 manguru/umanguru and 0644 umanguru/manguru
# list each other's headword), so the owning record keeps the form and the
# duplicate variant entry is dropped at build. Reviewer decision 2026-08-07.
DUPLICATE_VARIANT_ENTRY_IDS = frozenset(
    f"song-2018-kanakanavu-dictionary-{suffix}"
    for suffix in (
        "0070a", "0070b", "0070c",
        "0071a", "0071b", "0071c",
        "0072a", "0072b", "0072c",
        "0073a", "0073b", "0073c",
        "0074a", "0074b", "0074c",
        "0209a", "0219a", "0288a",
        "0367a", "0392b", "0412a",
        "0456a", "0644a", "0645a",
        "0646a", "0667a",
    )
)
DICTIONARY_MARKER_RE = re.compile(r"[-=+<>/;()\[\]{}\u2205\u00d8]")
GRAMMAR_REVIEW_RE = re.compile(r"-")
GRAMMAR_RESIDUE_RE = re.compile(r"[-=+<>\[\]{}\u2205\u00d8]")
PAGE_RE = re.compile(r"page (\d+)")

def variant_entry_id(record_id: str, index: int) -> str:
    """S id for the index-th form of a split decision (0006, 0006a, 0006b...)."""
    if index == 0:
        return record_id
    return f"{record_id}{string.ascii_lowercase[index - 1]}"
BREAK_NOTE = (
    "Source typewriter double-hyphen break punctuation rendered as a single "
    "dash; exact decision recorded in intermediate/standard_surface_decisions.tsv."
)
LYRIC_NOTE = (
    "Source lyric layout resolved with independently attested word boundaries; "
    "exact decision recorded in intermediate/standard_surface_decisions.tsv."
)
ANALYSIS_TIER_NOTE = (
    "Source analysis spelling standardized to the documented Ortho113 surface; "
    "original tier preserves the printed form."
)

# Reader page 69 prints takananga in the sentence surface but takanaga in the
# aligned analysis. Preserve the latter in original W/M tiers and resolve its
# non-Ortho113 g only in the corresponding standard tiers.
ANALYSIS_TIER_CORRECTIONS = {
    "song-2018-kanakanavu-S0012-W004": ("takanaga=kasu", "takananga=kasu"),
    "song-2018-kanakanavu-S0012-W004-M01": ("takanaga", "takananga"),
}


@dataclass(frozen=True)
class Decision:
    scope: str
    record_id: str
    source_page: str
    expected_input: str
    decision_class: str
    output_forms: tuple[str, ...]
    evidence: str

    @property
    def excluded(self) -> bool:
        return self.decision_class == BOUND_EXCLUDED_CLASS

    @property
    def note(self) -> str:
        if self.decision_class == "source_break_punctuation_single_dash":
            return BREAK_NOTE
        if self.decision_class == "source_lyric_layout_with_attested_boundaries":
            return LYRIC_NOTE
        raise ValueError(
            f"Only grammar decisions carry an XML note; got {self.decision_class!r}"
        )


def load_decisions(path: Path = DECISIONS_PATH) -> dict[tuple[str, str], Decision]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected_fields = [
            "scope",
            "record_id",
            "source_page",
            "expected_input",
            "decision_class",
            "output_forms_json",
            "evidence",
        ]
        if reader.fieldnames != expected_fields:
            raise ValueError(f"Unexpected decision manifest columns: {reader.fieldnames}")
        rows = list(reader)

    decisions: dict[tuple[str, str], Decision] = {}
    for row in rows:
        try:
            outputs = json.loads(row["output_forms_json"])
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid output JSON for {row['record_id']}: {error}"
            ) from error
        if not isinstance(outputs, list) or any(
            not isinstance(output, str) or not output for output in outputs
        ):
            raise ValueError(f"Invalid output forms for {row['record_id']}: {outputs!r}")
        if len(outputs) != len(set(outputs)):
            raise ValueError(f"Duplicate output forms for {row['record_id']}")
        if row["scope"] not in {"dictionary", "grammar"}:
            raise ValueError(f"Unexpected decision scope: {row['scope']!r}")
        if not row["evidence"]:
            raise ValueError(f"Missing evidence for {row['record_id']}")
        decision = Decision(
            scope=row["scope"],
            record_id=row["record_id"],
            source_page=row["source_page"],
            expected_input=row["expected_input"],
            decision_class=row["decision_class"],
            output_forms=tuple(outputs),
            evidence=row["evidence"],
        )
        key = (decision.scope, decision.record_id)
        if key in decisions:
            raise ValueError(f"Duplicate decision key: {key}")
        decisions[key] = decision

    dictionary = [decision for decision in decisions.values() if decision.scope == "dictionary"]
    grammar = [decision for decision in decisions.values() if decision.scope == "grammar"]
    excluded = [decision for decision in dictionary if decision.excluded]
    if any(decision.output_forms for decision in excluded) or any(
        not decision.excluded and not decision.output_forms
        for decision in decisions.values()
    ):
        raise ValueError(
            "Empty outputs and the bound-exclusion class must coincide exactly"
        )
    extra = sum(max(0, len(decision.output_forms) - 1) for decision in dictionary)
    actual = (len(decisions), len(dictionary), len(grammar), len(excluded), extra)
    expected = (
        EXPECTED_DECISIONS,
        EXPECTED_DICTIONARY_DECISIONS,
        EXPECTED_GRAMMAR_DECISIONS,
        EXPECTED_BOUND_EXCLUSIONS,
        EXPECTED_DICTIONARY_EXTRA_ENTRIES,
    )
    if actual != expected:
        raise ValueError(f"Decision manifest coverage changed: {actual}; expected {expected}")
    return decisions


def one_form(sentence: ET.Element, kind: str) -> ET.Element:
    forms = sentence.findall(f"./FORM[@kindOf='{kind}']")
    if len(forms) != 1:
        raise ValueError(
            f"{sentence.get('id', '<unknown>')} has {len(forms)} direct {kind} forms"
        )
    return forms[0]


def assert_source_alignment(sentence: ET.Element, decision: Decision) -> ET.Element:
    original = one_form(sentence, "original")
    if (original.text or "") != decision.expected_input:
        raise ValueError(
            f"Source input changed for {decision.record_id}: "
            f"{original.text!r}; expected {decision.expected_input!r}"
        )
    match = PAGE_RE.search(sentence.get("source", ""))
    actual_page = match.group(1) if match else ""
    if actual_page != decision.source_page:
        raise ValueError(
            f"Source page changed for {decision.record_id}: "
            f"{actual_page!r}; expected {decision.source_page!r}"
        )
    return original


def apply_decision(sentence: ET.Element, decision: Decision) -> int:
    assert_source_alignment(sentence, decision)
    standards = sentence.findall("./FORM[@kindOf='standard']")
    if len(standards) != 1:
        raise ValueError(
            f"{decision.record_id} has {len(standards)} direct standard forms before review"
        )
    standard = standards[0]
    for alternate in sentence.findall("./FORM[@kindOf='alternate']"):
        sentence.remove(alternate)

    if not decision.output_forms:
        raise ValueError(
            f"{decision.record_id} has no output forms; excluded entries must "
            "never reach the XML"
        )

    standard.text = decision.output_forms[0]
    standard.set("notes", decision.note)
    insert_at = list(sentence).index(standard) + 1
    for output in decision.output_forms[1:]:
        alternate = ET.Element(
            "FORM", {"kindOf": "alternate", "notes": decision.note}
        )
        alternate.text = output
        sentence.insert(insert_at, alternate)
        insert_at += 1
    return len(decision.output_forms) - 1


def decisions_for_scope(
    decisions: dict[tuple[str, str], Decision], scope: str
) -> dict[str, Decision]:
    return {
        record_id: decision
        for (decision_scope, record_id), decision in decisions.items()
        if decision_scope == scope
    }


def normalize_dictionary(
    root: ET.Element, decisions: dict[str, Decision]
) -> tuple[int, int, int]:
    """Verify the build-time entry split; the dictionary needs no rewriting.

    Variant forms are emitted as separate S entries by build_xml before the
    standard tier is copied from the original tier, so every published entry
    already carries one clean surface. This pass only enforces that state.
    """
    sentences = {sentence.get("id", ""): sentence for sentence in root.findall("./S")}
    excluded = {
        record_id
        for record_id, decision in decisions.items()
        if decision.excluded
    }
    split = {
        record_id: decision
        for record_id, decision in decisions.items()
        if not decision.excluded
    }
    present_excluded = excluded & set(sentences)
    if present_excluded:
        raise ValueError(
            "Bound citation entries must be excluded upstream but are present "
            f"in the XML: {sorted(present_excluded)}"
        )
    marked_ids = {
        record_id
        for record_id, sentence in sentences.items()
        if DICTIONARY_MARKER_RE.search(one_form(sentence, "original").text or "")
    }
    if marked_ids:
        raise ValueError(
            "Dictionary originals must be apparatus-free after the build-time "
            f"split; markers remain in: {sorted(marked_ids)}"
        )
    if len(sentences) != EXPECTED_DICTIONARY_ENTRIES:
        raise ValueError(
            f"Dictionary entry count changed: {len(sentences)}; "
            f"expected {EXPECTED_DICTIONARY_ENTRIES}"
        )

    present_duplicates = DUPLICATE_VARIANT_ENTRY_IDS & set(sentences)
    if present_duplicates:
        raise ValueError(
            "Duplicate variant entries must be dropped at build but are "
            f"present: {sorted(present_duplicates)}"
        )

    verified_entries = 0
    for record_id, decision in split.items():
        for index, output in enumerate(decision.output_forms):
            entry_id = variant_entry_id(record_id, index)
            if entry_id in DUPLICATE_VARIANT_ENTRY_IDS:
                continue
            sentence = sentences.get(entry_id)
            if sentence is None:
                raise ValueError(f"Missing split variant entry: {entry_id}")
            original = one_form(sentence, "original")
            if (original.text or "") != output:
                raise ValueError(
                    f"{entry_id} original drifted from the reviewed output: "
                    f"{original.text!r}; expected {output!r}"
                )
            if decision.expected_input not in (original.get("notes") or ""):
                raise ValueError(
                    f"{entry_id} original lost its source-apparatus note"
                )
            standard = one_form(sentence, "standard")
            if (standard.text or "") != output:
                raise ValueError(
                    f"{entry_id} standard drifted from the reviewed output: "
                    f"{standard.text!r}; expected {output!r}"
                )
            verified_entries += 1
    return len(split), verified_entries, len(excluded)


def normalize_grammar(root: ET.Element, decisions: dict[str, Decision]) -> int:
    sentences = {sentence.get("id", ""): sentence for sentence in root.findall("./S")}
    review_ids = {
        record_id
        for record_id, sentence in sentences.items()
        if GRAMMAR_REVIEW_RE.search(one_form(sentence, "original").text or "")
    }
    if review_ids != set(decisions):
        raise ValueError(
            "Grammar decision coverage does not match hyphen-bearing source records: "
            f"missing={sorted(review_ids - set(decisions))}, "
            f"extra={sorted(set(decisions) - review_ids)}"
        )
    for record_id, decision in decisions.items():
        if len(decision.output_forms) != 1:
            raise ValueError(f"Grammar decision must have one output: {record_id}")
        apply_decision(sentences[record_id], decision)
    return len(decisions)


def normalize_analysis_tiers(root: ET.Element) -> int:
    by_id = {
        element.get("id", ""): element
        for element in root.iter()
        if element.tag in {"W", "M"}
    }
    for record_id, (expected_original, output_standard) in (
        ANALYSIS_TIER_CORRECTIONS.items()
    ):
        element = by_id.get(record_id)
        if element is None:
            raise ValueError(f"Missing analysis-tier correction target: {record_id}")
        original = one_form(element, "original")
        standard = one_form(element, "standard")
        if (original.text or "") != expected_original:
            raise ValueError(
                f"Analysis-tier source changed for {record_id}: {original.text!r}; "
                f"expected {expected_original!r}"
            )
        if (standard.text or "") != expected_original:
            raise ValueError(
                f"Analysis-tier standard changed before review for {record_id}: "
                f"{standard.text!r}; expected {expected_original!r}"
            )
        standard.text = output_standard
        standard.set("notes", ANALYSIS_TIER_NOTE)
    return len(ANALYSIS_TIER_CORRECTIONS)


def assert_marker_free(
    root: ET.Element, dictionary: bool, allowed: frozenset[str] = frozenset()
) -> None:
    """Reject residual analysis markers in surface tiers.

    `allowed` holds exact reviewed decision outputs (currently the two
    break-dash sentences, whose single dash is punctuation, not a marker).
    """
    kinds = {"standard", "alternate"} if dictionary else {"standard"}
    marker_re = DICTIONARY_MARKER_RE if dictionary else GRAMMAR_RESIDUE_RE
    for sentence in root.findall("./S"):
        for form in sentence.findall("./FORM"):
            if form.get("kindOf") not in kinds:
                continue
            text = form.text or ""
            if text in allowed:
                continue
            if marker_re.search(text):
                raise ValueError(
                    f"{sentence.get('id')} {form.get('kindOf')} retains analysis marker: "
                    f"{text!r}"
                )


def process_file(path: Path) -> tuple[int, int, int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    decisions = load_decisions()
    if path.name == DICTIONARY_NAME:
        count, split_entries, omissions = normalize_dictionary(
            root, decisions_for_scope(decisions, "dictionary")
        )
        assert_marker_free(root, dictionary=True)
        tier_corrections = 0
    elif path.name == GRAMMAR_NAME:
        count = normalize_grammar(root, decisions_for_scope(decisions, "grammar"))
        tier_corrections = normalize_analysis_tiers(root)
        split_entries = 0
        omissions = 0
        reviewed_dash_surfaces = frozenset(
            decision.output_forms[0]
            for decision in decisions.values()
            if decision.decision_class == "source_break_punctuation_single_dash"
        )
        assert_marker_free(root, dictionary=False, allowed=reviewed_dash_surfaces)
    else:
        raise ValueError(f"Unexpected Kanakanavu corpus XML: {path}")
    ET.indent(root, space="  ")
    tree.write(path, encoding="UTF-8", xml_declaration=True)
    return count, split_entries, omissions, tier_corrections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora_path", type=Path, default=DEFAULT_XML_PATH)
    args = parser.parse_args()
    files = (
        [args.corpora_path]
        if args.corpora_path.is_file()
        else sorted(args.corpora_path.rglob("*.xml"))
    )
    for path in files:
        count, split_entries, omissions, tier_corrections = process_file(path)
        print(
            f"Processed {count} exact decisions; verified {split_entries} "
            f"split variant entries and {omissions} bound entries excluded "
            f"upstream; applied {tier_corrections} analysis-tier corrections "
            f"in {path}"
        )


if __name__ == "__main__":
    main()
