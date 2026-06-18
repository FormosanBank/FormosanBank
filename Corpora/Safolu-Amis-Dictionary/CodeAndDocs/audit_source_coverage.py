#!/usr/bin/env python3
"""Prove source-example coverage for the finalized Safolu XML package."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from build_formosanbank_xml import LANGUAGE_SUBDIR, SAFOLU_TEXT_ID
from moedict_formosanbank import ROOT, iter_moedict_json_files, parse_marked_example


DEFAULT_SOURCES_DIR = ROOT / "_sources"
DEFAULT_FINAL_DIR = ROOT / "Final_XML"
DEFAULT_AUDIT_DIR = ROOT / "data" / "formosanbank_audit"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def count_xml_sentences(path: Path) -> int:
    return sum(1 for child in ET.parse(path).getroot() if child.tag == "S")


def count_generated_examples(source_dir: Path) -> tuple[int, int, int]:
    total = valid = malformed = 0
    for source_file in iter_moedict_json_files(source_dir):
        entry = load_json(source_file)
        if not isinstance(entry, dict):
            continue
        for heteronym in entry.get("h", []):
            for definition in heteronym.get("d", []):
                for raw_example in definition.get("e", []):
                    total += 1
                    try:
                        parse_marked_example(raw_example)
                    except ValueError:
                        malformed += 1
                    else:
                        valid += 1
    return total, valid, malformed


def reject_reason_counts(rejected: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for example in rejected["examples"]:
        key = "+".join(example["reject_reasons"])
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def audit(sources_dir: Path, final_dir: Path, audit_dir: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    safolu_dir = final_dir / LANGUAGE_SUBDIR / "Safolu"
    safolu_audit_dir = audit_dir / "Safolu"

    safolu_xml = safolu_dir / f"{SAFOLU_TEXT_ID}.xml"
    safolu_metadata = load_json(safolu_audit_dir / f"{SAFOLU_TEXT_ID}.metadata.json")
    safolu_rejected = load_json(safolu_audit_dir / f"{SAFOLU_TEXT_ID}.rejected.json")

    source_total, source_valid_markers, source_malformed_markers = count_generated_examples(
        sources_dir / "amis-moedict" / "docs" / "s"
    )
    xml_count = count_xml_sentences(safolu_xml)
    rejected_count = safolu_rejected["rejected_example_count"]
    # A source example field can expand into several sentences (a glued list is
    # split into one S per pair), so coverage is tracked at the source-FIELD
    # level via each record's source_ordinal -- not by sentence counts.
    accepted_fields = {e["notes"].get("source_ordinal") for e in safolu_metadata["examples"]}
    accepted_fields.discard(None)
    rejected_fields = {e["source_ordinal"] for e in safolu_rejected["examples"]}
    accounted = len(accepted_fields | rejected_fields)
    split_fields = sum(1 for e in safolu_metadata["examples"] if e["notes"].get("split_from_cjk_form"))
    recovered = sum(
        1 for example in safolu_metadata["examples"] if example["notes"].get("recovered_form_from_translation")
    )
    recovered_from_note = sum(
        1 for example in safolu_metadata["examples"] if example["notes"].get("recovered_form_from_note")
    )
    form_only = sum(1 for example in safolu_metadata["examples"] if not example["translations"])
    discarded_middle = sum(
        1 for example in safolu_metadata["examples"] if "discarded_middle_translation" in example["notes"]
    )

    checks = {
        "safolu_source_markers_are_well_formed": source_malformed_markers == 0,
        "safolu_source_examples_accounted": source_total == accounted,
        "safolu_accepted_rejected_disjoint": accepted_fields.isdisjoint(rejected_fields),
        "safolu_xml_matches_metadata": xml_count == safolu_metadata["example_count"],
        "safolu_rejected_matches_metadata": rejected_count == safolu_metadata["rejected_example_count"],
    }
    for name, passed in checks.items():
        if not passed:
            errors.append(name)

    report = {
        "description": (
            "Coverage audit for Final_XML. Every Safolu docs/s example field is either represented in "
            "valid FormosanBank XML or explicitly present in the rejected-record audit."
        ),
        "excluded": [
            {"source": "g0v/amis-moedict/docs/p", "reason": "Virginia Fey dictionary already processed separately."},
            {"source": "g0v/amis-moedict/docs/m", "reason": "Poinsot dictionary lives in the Formosan-Poinsot-Amis-Dictionary repository."},
        ],
        "safolu": {
            "final_xml": str(safolu_xml.relative_to(ROOT)),
            "xml_sentence_count": xml_count,
            "metadata_example_count": safolu_metadata["example_count"],
            "source_example_fields": source_total,
            "source_fields_with_valid_markers": source_valid_markers,
            "source_fields_with_malformed_markers": source_malformed_markers,
            "rejected_count": rejected_count,
            "accounted_source_fields": accounted,
            "sentences_split_from_cjk_form": split_fields,
            "recovered_empty_form_rows": recovered,
            "recovered_form_from_note_rows": recovered_from_note,
            "form_only_no_translation_rows": form_only,
            "discarded_middle_translation_artifacts": discarded_middle,
            "reject_reason_counts": reject_reason_counts(safolu_rejected),
        },
        "checks": checks,
    }
    return report, errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources-dir", type=Path, default=DEFAULT_SOURCES_DIR)
    parser.add_argument("--final-dir", type=Path, default=DEFAULT_FINAL_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_AUDIT_DIR / "coverage_audit.json")
    args = parser.parse_args()

    report, errors = audit(args.sources_dir.resolve(), args.final_dir.resolve(), args.audit_dir.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        for error in errors:
            print(f"Coverage check failed: {error}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Wrote coverage audit to {args.out}")


if __name__ == "__main__":
    main()
