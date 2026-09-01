#!/usr/bin/env python3
"""Generate canonical Utrecht Manuscript XML from the pinned source ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from lxml import etree

from reconcile_predecessor import (
    build_reconciliation,
    load_predecessor,
    load_source,
    reconciliation_csv,
)


XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"


def load_inputs(
    code_docs: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    decisions = json.loads(
        (code_docs / "source_decisions.json").read_text(encoding="utf-8")
    )
    source = load_source(code_docs / decisions["source"]["path"], decisions)
    predecessor = load_predecessor(
        code_docs / decisions["predecessor"]["path"], decisions
    )
    reconciliation = build_reconciliation(source, predecessor, decisions)
    committed_mapping = code_docs / "source" / "source_reconciliation.csv"
    if committed_mapping.read_text(encoding="utf-8") != reconciliation_csv(
        reconciliation
    ):
        raise ValueError("committed source reconciliation does not match its inputs")
    return decisions, source, reconciliation


def form_decisions_by_row(
    decisions: dict[str, Any], source: dict[str, Any]
) -> dict[int, dict[str, Any]]:
    source_by_row = {row["source_row"]: row for row in source["rows"]}
    result: dict[int, dict[str, Any]] = {}
    for item in decisions["form_decisions"]:
        source_row = item["source_row"]
        if source_row in result:
            raise ValueError(f"duplicate form decision for source row {source_row}")
        if source_row not in source_by_row:
            raise ValueError(f"form decision targets absent source row {source_row}")
        if source_by_row[source_row]["um_formosana"] != item["raw_form"]:
            raise ValueError(f"form decision raw text drifted at source row {source_row}")
        if not item["output_form"].strip():
            raise ValueError(f"form decision empties source row {source_row}")
        result[source_row] = item
    return result


def canonical_translation(
    text: str, decisions: dict[str, Any]
) -> tuple[str, str | None]:
    cleanup = decisions["xml"]["translation_cleanup"]
    output = text
    if cleanup["square_brackets_to_parentheses"]:
        output = output.translate(str.maketrans({"[": "(", "]": ")"}))
    notes = text if cleanup["preserve_raw_in_notes"] and output != text else None
    return output, notes


def translation_decisions_by_key(
    decisions: dict[str, Any], source: dict[str, Any]
) -> dict[tuple[int, str], dict[str, Any]]:
    source_by_row = {row["source_row"]: row for row in source["rows"]}
    allowed_fields = {
        item["source_field"] for item in decisions["xml"]["translations"]
    }
    result: dict[tuple[int, str], dict[str, Any]] = {}
    for item in decisions["translation_decisions"]:
        key = (item["source_row"], item["source_field"])
        if key in result:
            raise ValueError(f"duplicate translation decision for {key}")
        if item["source_field"] not in allowed_fields:
            raise ValueError(f"translation decision uses unconfigured field {key}")
        row = source_by_row.get(item["source_row"])
        if row is None:
            raise ValueError(f"translation decision targets absent source row {key}")
        if row[item["source_field"]].strip() != item["raw_text"]:
            raise ValueError(f"translation decision raw text drifted at {key}")
        outputs = item["outputs"]
        if len(outputs) < 2 or any(not value.strip() for value in outputs):
            raise ValueError(f"translation decision must have two or more values at {key}")
        if len(outputs) != len(set(outputs)):
            raise ValueError(f"translation decision repeats an output at {key}")
        result[key] = item
    return result


def expected_translation_nodes(
    row: dict[str, Any],
    decisions: dict[str, Any],
    translation_decisions: dict[tuple[int, str], dict[str, Any]],
) -> list[dict[str, str]]:
    expected: list[dict[str, str]] = []
    for translation in decisions["xml"]["translations"]:
        source_field = translation["source_field"]
        raw_text = row[source_field].strip()
        if not raw_text:
            continue
        decision = translation_decisions.get((row["source_row"], source_field))
        values = decision["outputs"] if decision is not None else [raw_text]
        for index, value in enumerate(values):
            output, cleanup_notes = canonical_translation(value, decisions)
            node = {"xml_lang": translation["xml_lang"], "text": output}
            if index > 0:
                node["ver"] = "alt"
            if decision is not None and index == 0:
                node["notes"] = raw_text
            elif cleanup_notes is not None:
                node["notes"] = cleanup_notes
            expected.append(node)
    return expected


def build_tree(
    decisions: dict[str, Any],
    source: dict[str, Any],
    reconciliation: dict[str, Any],
) -> etree._ElementTree:
    attributes = decisions["xml"]["attributes"]
    root_attributes = {
        (XML_LANG if name == "xml:lang" else name): value
        for name, value in attributes.items()
    }
    root = etree.Element("TEXT", root_attributes)
    decisions_by_row = form_decisions_by_row(decisions, source)
    translation_decisions = translation_decisions_by_key(decisions, source)
    mapping_by_row = {
        record["source_row"]: record for record in reconciliation["records"]
    }

    for row in source["rows"]:
        source_row = row["source_row"]
        sentence = etree.SubElement(root, "S", id=mapping_by_row[source_row]["output_id"])
        form_decision = decisions_by_row.get(source_row)
        if form_decision is None:
            form = etree.SubElement(sentence, "FORM", kindOf="original")
            form.text = row["um_formosana"]
        else:
            form = etree.SubElement(
                sentence,
                "FORM",
                kindOf="original",
                notes=form_decision["notes"],
            )
            form.text = form_decision["output_form"]

        for expected in expected_translation_nodes(
            row, decisions, translation_decisions
        ):
            translation_attributes = {XML_LANG: expected["xml_lang"]}
            if "ver" in expected:
                translation_attributes["ver"] = expected["ver"]
            if "notes" in expected:
                translation_attributes["notes"] = expected["notes"]
            node = etree.SubElement(sentence, "TRANSL", translation_attributes)
            node.text = expected["text"]

    etree.indent(root, space="    ")
    return etree.ElementTree(root)


def write_tree(tree: etree._ElementTree, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(
        str(path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def parse_args() -> argparse.Namespace:
    code_docs = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-docs", type=Path, default=code_docs)
    parser.add_argument(
        "--output",
        type=Path,
        default=code_docs.parent / "XML" / "Siraya" / "Utrecht_Manuscript.xml",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions, source, reconciliation = load_inputs(args.code_docs)
    tree = build_tree(decisions, source, reconciliation)
    write_tree(tree, args.output)
    print(f"Generated {len(source['rows'])} S records at {args.output}")


if __name__ == "__main__":
    main()
