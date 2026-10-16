#!/usr/bin/env python3
"""Build the explicit source-to-predecessor identifier reconciliation ledger."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from lxml import etree


VALID_XML_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9._-]*$")
RECONCILIATION_FIELDS = (
    "source_row",
    "output_id",
    "mapping_status",
    "predecessor_index",
    "predecessor_id",
    "predecessor_form",
    "id_reason",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_predecessor(path: Path, decisions: dict[str, Any]) -> list[dict[str, Any]]:
    expected = decisions["predecessor"]
    if path.stat().st_size != expected["bytes"]:
        raise ValueError("public predecessor byte size drifted")
    if sha256_file(path) != expected["sha256"]:
        raise ValueError("public predecessor SHA-256 drifted")

    payload = path.read_bytes()
    if b"</TEXT>" in payload:
        raise ValueError("pinned predecessor unexpectedly contains a closing TEXT tag")
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    root = etree.fromstring(payload + b"\n</TEXT>\n", parser=parser)
    entries: list[dict[str, Any]] = []
    for index, word in enumerate(root.findall("W"), start=1):
        entries.append(
            {
                "predecessor_index": index,
                "id": word.get("id"),
                "original_form": word.findtext('./FORM[@kindOf="original"]') or "",
            }
        )
    if len(entries) != expected["entry_count"]:
        raise ValueError(
            f"expected {expected['entry_count']} predecessor entries, "
            f"found {len(entries)}"
        )
    return entries


def load_source(path: Path, decisions: dict[str, Any]) -> dict[str, Any]:
    ledger = json.loads(path.read_text(encoding="utf-8"))
    expected = decisions["source"]
    if ledger["row_count"] != expected["row_count"]:
        raise ValueError("source row count drifted")
    if ledger["rows_sha256"] != expected["rows_sha256"]:
        raise ValueError("source row payload SHA-256 drifted")
    return ledger


def _validate_retirements(
    entries: list[dict[str, Any]], decisions: dict[str, Any]
) -> set[int]:
    retired: set[int] = set()
    for item in decisions["predecessor"]["retired_entries"]:
        index = item["predecessor_index"]
        if index in retired:
            raise ValueError(f"duplicate retirement for predecessor entry {index}")
        actual = entries[index - 1]
        for field in ("id", "original_form"):
            if actual[field] != item[field]:
                raise ValueError(
                    f"retirement entry {index} {field} drifted: "
                    f"{actual[field]!r} != {item[field]!r}"
                )
        retired.add(index)
    return retired


def build_reconciliation(
    source: dict[str, Any],
    entries: list[dict[str, Any]],
    decisions: dict[str, Any],
) -> dict[str, Any]:
    retired = _validate_retirements(entries, decisions)
    new_rows = set(decisions["new_source_rows"])
    source_rows = source["rows"]
    source_numbers = {row["source_row"] for row in source_rows}
    if not new_rows <= source_numbers:
        raise ValueError("new-source row decision is outside the source inventory")

    retained_entries = [
        entry for entry in entries if entry["predecessor_index"] not in retired
    ]
    inherited_rows = [
        row for row in source_rows if row["source_row"] not in new_rows
    ]
    if len(retained_entries) != len(inherited_rows):
        raise ValueError(
            "retained predecessor and inherited source inventories have different sizes"
        )

    predecessor_by_row = {
        row["source_row"]: entry
        for row, entry in zip(inherited_rows, retained_entries, strict=True)
    }
    overrides = {
        item["source_row"]: item["predecessor_index"]
        for item in decisions["mapping_overrides"]
    }
    overridden_rows = set(overrides)
    default_entries = {
        predecessor_by_row[row]["predecessor_index"] for row in overridden_rows
    }
    requested_entries = set(overrides.values())
    if default_entries != requested_entries:
        raise ValueError("mapping overrides must permute, not add, predecessor entries")
    entries_by_index = {entry["predecessor_index"]: entry for entry in entries}
    for source_row, predecessor_index in overrides.items():
        predecessor_by_row[source_row] = entries_by_index[predecessor_index]

    used_predecessors = [
        entry["predecessor_index"] for entry in predecessor_by_row.values()
    ]
    if len(used_predecessors) != len(set(used_predecessors)):
        raise ValueError("a predecessor entry maps to more than one source row")
    expected_predecessors = {
        entry["predecessor_index"] for entry in retained_entries
    }
    if set(used_predecessors) != expected_predecessors:
        raise ValueError("retained predecessor coverage is incomplete")

    id_overrides = {
        item["source_row"]: item for item in decisions["output_id_overrides"]
    }
    records: list[dict[str, Any]] = []
    for row in source_rows:
        source_row = row["source_row"]
        predecessor = predecessor_by_row.get(source_row)
        override = id_overrides.get(source_row)
        if override is not None:
            output_id = override["output_id"]
            id_reason = override["reason"]
        elif predecessor is not None:
            output_id = predecessor["id"]
            id_reason = None
        else:
            output_id = f"Utrecht_Manuscript-S-r{source_row:04d}"
            id_reason = "Source row is absent from the public predecessor."

        if predecessor is None:
            status = "new_source"
        elif override is not None:
            status = "repaired_predecessor_id"
        elif predecessor["original_form"] == row["um_formosana"]:
            status = "retained_exact"
        else:
            status = "retained_source_corrected"
        records.append(
            {
                "source_row": source_row,
                "pdf_page": row["pdf_page"],
                "pdf_top": row["pdf_top"],
                "output_id": output_id,
                "mapping_status": status,
                "id_reason": id_reason,
                "predecessor": predecessor,
            }
        )

    output_ids = [record["output_id"] for record in records]
    duplicates = [value for value, count in Counter(output_ids).items() if count > 1]
    if duplicates:
        raise ValueError(f"duplicate output ids remain: {duplicates}")
    invalid = [value for value in output_ids if not VALID_XML_ID.fullmatch(value)]
    if invalid:
        raise ValueError(f"invalid XML ids remain: {invalid}")
    unused_overrides = set(id_overrides) - source_numbers
    if unused_overrides:
        raise ValueError(f"output-id overrides target absent rows: {unused_overrides}")

    statuses = Counter(record["mapping_status"] for record in records)
    mapping_payload = json.dumps(
        records, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    return {
        "schema": 1,
        "source_rows_sha256": source["rows_sha256"],
        "predecessor_sha256": decisions["predecessor"]["sha256"],
        "record_count": len(records),
        "records_sha256": hashlib.sha256(mapping_payload.encode("utf-8")).hexdigest(),
        "counts": {
            "source_rows": len(source_rows),
            "predecessor_entries": len(entries),
            "retained_predecessor_entries": len(retained_entries),
            "retired_predecessor_entries": len(retired),
            **dict(sorted(statuses.items())),
        },
        "retired_predecessor_entries": [
            {
                **entries[item["predecessor_index"] - 1],
                "reason": item["reason"],
            }
            for item in decisions["predecessor"]["retired_entries"]
        ],
        "records": records,
    }


def reconciliation_csv(result: dict[str, Any]) -> str:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer, fieldnames=RECONCILIATION_FIELDS, lineterminator="\n"
    )
    writer.writeheader()
    for record in result["records"]:
        predecessor = record["predecessor"]
        writer.writerow(
            {
                "source_row": record["source_row"],
                "output_id": record["output_id"],
                "mapping_status": record["mapping_status"],
                "predecessor_index": (
                    predecessor["predecessor_index"] if predecessor else ""
                ),
                "predecessor_id": predecessor["id"] if predecessor else "",
                "predecessor_form": (
                    predecessor["original_form"] if predecessor else ""
                ),
                "id_reason": record["id_reason"] or "",
            }
        )
    return buffer.getvalue()


def parse_args() -> argparse.Namespace:
    code_docs = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source", type=Path, default=code_docs / "source" / "source_records.json"
    )
    parser.add_argument(
        "--predecessor",
        type=Path,
        default=code_docs / "source" / "public_predecessor.xml",
    )
    parser.add_argument(
        "--decisions", type=Path, default=code_docs / "source_decisions.json"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=code_docs / "source" / "source_reconciliation.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    source = load_source(args.source, decisions)
    entries = load_predecessor(args.predecessor, decisions)
    result = build_reconciliation(source, entries, decisions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(reconciliation_csv(result), encoding="utf-8")
    print(
        f"Mapped {result['counts']['retained_predecessor_entries']} predecessor "
        f"entries and {result['counts']['new_source']} new source rows."
    )
    print(
        f"Retired {result['counts']['retired_predecessor_entries']} predecessor "
        "artifacts."
    )
    print(f"Records SHA-256: {result['records_sha256']}")


if __name__ == "__main__":
    main()
