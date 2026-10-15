#!/usr/bin/env python3
"""Author manual_edits.xml from the reviewed table in source_repairs.json.

The repairs are source-fidelity fixes: the ILRDF API emitted material that is
not Formosan text -- a part-of-speech category label standing in for a word, or
Chinese editorial matter welded onto the end of a sentence. Under POL-030 and
POL-002 those belong in the ORIGINAL tier, applied through the repo's own
manual-edits mechanism rather than patched into the standard tier afterwards.

This only works because sentence ids come from the source GUID (see
docs/id_scheme.md). apply_manual_edits.py matches records by S/@id, so a record
whose id were a hash of its own text would be orphaned by the very edit it
describes.

Run after generate_xml.py and split_alternatives.py, before the pipeline's
apply_manual_edits.py step. Re-running is safe: the output is regenerated from
the table, and a repair whose 'before' text is no longer present is reported
rather than silently dropped.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lxml import etree

BASE = Path(__file__).resolve().parent
REPAIRS = BASE / "source_data" / "source_repairs.json"
XML_DIR = BASE.parent / "XML"
MANUAL_EDITS = BASE / "manual_edits.xml"


def load_repairs(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["repairs"]


def build(xml_dir: Path, repairs: list[dict]) -> tuple[etree._Element, list[str]]:
    """Return the MANUAL_EDITS tree and a list of repairs that found no target."""
    wanted = {r["before"]: r for r in repairs}
    root = etree.Element("MANUAL_EDITS")
    matched: set[str] = set()

    for path in sorted(xml_dir.rglob("*.xml")):
        relative = path.relative_to(xml_dir).as_posix()
        group: etree._Element | None = None
        for sentence in etree.parse(str(path)).getroot().findall("S"):
            form = sentence.find('FORM[@kindOf="original"]')
            if form is None or form.text not in wanted:
                continue
            repair = wanted[form.text]
            matched.add(repair["before"])
            if group is None:
                group = etree.SubElement(root, "FILE", {"path": relative})
            record = etree.fromstring(etree.tostring(sentence))
            record.find('FORM[@kindOf="original"]').text = repair["after"]
            group.append(record)

    missing = [r["before"] for r in repairs if r["before"] not in matched]
    return root, missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, default=XML_DIR)
    parser.add_argument("--out", type=Path, default=MANUAL_EDITS)
    parser.add_argument("--repairs", type=Path, default=REPAIRS)
    args = parser.parse_args()

    repairs = load_repairs(args.repairs)
    root, missing = build(args.xml_dir.resolve(), repairs)
    count = len(root.findall(".//S"))

    etree.indent(root, space="    ")
    args.out.write_bytes(
        etree.tostring(root, encoding="UTF-8", xml_declaration=True,
                       pretty_print=True))
    print(f"wrote {args.out}: {count} of {len(repairs)} repairs")
    for before in missing:
        print(f"  NO TARGET: {before[:70]!r}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
