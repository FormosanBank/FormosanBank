#!/usr/bin/env python3
"""Generate canonical Utrecht Manuscript XML from the pinned source ledger.

The source is a ten-column comparative table. Five columns are published:

    1  um_formosana   Joby's corrected reading  -> FORM kindOf="original"
    2  um_belgica     the manuscript's Dutch    -> TRANSL nld ver="alt", where it
                                                   differs from column 3
    3  vdv_dutch      van der Vlis's Dutch      -> TRANSL nld
    4  vdv_siraya     van der Vlis 1842         -> FORM kindOf="alternate"
    5  english        Joby's own English        -> TRANSL eng

Columns 6 to 10 are not published; see `xml.columns.reason` in
`source_decisions.json`.
"""

from __future__ import annotations

import argparse
import json
import re
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


# --------------------------------------------------------------------------
# text handling
# --------------------------------------------------------------------------

def outermost_brackets(text: str) -> tuple[str, list[str]]:
    """Split `text` into what is outside square brackets and what is inside.

    Matching runs to the *outermost* closing bracket, because the apparatus
    nests: `jeest [recte ie[e]ts]` is one note, and a non-greedy match would
    stop at the inner `]` and leave `ts]` behind in the published text.
    """
    kept: list[str] = []
    inner: list[str] = []
    depth = 0
    start = 0
    for index, char in enumerate(text):
        if char == "[":
            if depth == 0:
                kept.append(text[start:index])
                start = index + 1
            depth += 1
        elif char == "]" and depth:
            depth -= 1
            if depth == 0:
                inner.append(text[start:index])
                start = index + 1
    if depth:  # unbalanced; leave the text alone rather than guess
        return text, []
    kept.append(text[start:])
    return re.sub(r"\s{2,}", " ", "".join(kept)).strip(), inner


def split_on_commas(text: str) -> list[str]:
    """Split on commas that sit outside brackets and parentheses."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for char in text:
        if char in "[(":
            depth += 1
        elif char in "])":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def strip_alternate_form(raw: str, headword: str, decisions: dict[str, Any],
                         source_row: int) -> str:
    """Column 4 as a publishable alternate form, or "" when there is none."""
    rules = decisions["alternate_form_rules"]
    if any(item["source_row"] == source_row for item in rules["drop_entirely"]):
        return ""
    value = raw.strip()
    if rules["strip_bracketed"]:
        value, _ = outermost_brackets(value)
    keep_tail = any(item["source_row"] == source_row for item in rules["keep_tail"])
    if rules["drop_text_after_headword"] and not keep_tail:
        if value.startswith(headword + " "):
            value = headword
    return "" if value == headword else value


# --------------------------------------------------------------------------
# inputs
# --------------------------------------------------------------------------

def apply_reversed_columns(source: dict[str, Any], decisions: dict[str, Any]) -> None:
    """Undo runs where the source fills two columns in the opposite order."""
    for entry in decisions.get("reversed_column_pairs", []):
        first, last = entry["source_rows"]
        left, right = entry["swap"]
        for row in source["rows"]:
            if first <= row["source_row"] <= last:
                row[left], row[right] = row[right], row[left]


def load_inputs(code_docs: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    decisions = json.loads((code_docs / "source_decisions.json").read_text(encoding="utf-8"))
    source = load_source(code_docs / decisions["source"]["path"], decisions)
    predecessor = load_predecessor(code_docs / decisions["predecessor"]["path"], decisions)
    reconciliation = build_reconciliation(source, predecessor, decisions)
    committed = code_docs / "source" / "source_reconciliation.csv"
    if committed.read_text(encoding="utf-8") != reconciliation_csv(reconciliation):
        raise ValueError("committed source reconciliation does not match its inputs")
    apply_reversed_columns(source, decisions)
    return decisions, source, reconciliation


def form_decisions_by_row(decisions: dict[str, Any], source: dict[str, Any]) -> dict[int, dict[str, Any]]:
    by_row = {row["source_row"]: row for row in source["rows"]}
    result: dict[int, dict[str, Any]] = {}
    for item in decisions["form_decisions"]:
        source_row = item["source_row"]
        if source_row in result:
            raise ValueError(f"duplicate form decision for source row {source_row}")
        if source_row not in by_row:
            raise ValueError(f"form decision targets absent source row {source_row}")
        if by_row[source_row]["um_formosana"] != item["raw_form"]:
            raise ValueError(f"form decision raw text drifted at source row {source_row}")
        if not item["output_form"].strip():
            raise ValueError(f"form decision empties source row {source_row}")
        result[source_row] = item
    return result


def translation_decisions_by_key(decisions: dict[str, Any],
                                 source: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    by_row = {row["source_row"]: row for row in source["rows"]}
    allowed = {item["source_field"] for item in decisions["xml"]["columns"]["translations"]}
    result: dict[tuple[int, str], dict[str, Any]] = {}
    for item in decisions["translation_decisions"]:
        key = (item["source_row"], item["source_field"])
        if key in result:
            raise ValueError(f"duplicate translation decision for {key}")
        if item["source_field"] not in allowed:
            raise ValueError(f"translation decision uses unconfigured field {key}")
        row = by_row.get(item["source_row"])
        if row is None:
            raise ValueError(f"translation decision targets absent source row {key}")
        if row[item["source_field"]].strip() != item["raw_text"]:
            raise ValueError(f"translation decision raw text drifted at {key}")
        if len(item["outputs"]) != len(set(item["outputs"])):
            raise ValueError(f"translation decision repeats an output at {key}")
        result[key] = item
    return result


# --------------------------------------------------------------------------
# building
# --------------------------------------------------------------------------

def render_translation(raw: str, field: str, source_row: int,
                       siraya: str, decisions: dict[str, Any],
                       overrides: dict[tuple[int, str], dict[str, Any]]) -> tuple[list[str], str | None]:
    """One source cell as (readings, note). readings[0] is primary."""
    override = overrides.get((source_row, field))
    if override is not None:
        return list(override["outputs"]), override.get("notes")

    brackets = decisions["bracket_rules"]
    note: str | None = None
    text = raw.strip()
    if field in brackets["apparatus_columns"]:
        # every bracket in the historical Dutch is apparatus about the manuscript
        text, inner = outermost_brackets(text)
        if inner:
            note = "; ".join(part.strip() for part in inner)
    elif field in brackets["authorial_columns"]:
        # Joby's own elaboration; POL-024 lets it stay inline
        text = text.replace("[", "(").replace("]", ")")

    if not text:
        return [], note

    split = decisions["comma_split"]
    if (source_row not in split["do_not_split"]
            and not (split["skip_when_siraya_has_comma"] and "," in siraya)):
        readings = split_on_commas(text)
    else:
        readings = [text]
    return readings, note


def build_tree(decisions: dict[str, Any], source: dict[str, Any],
               reconciliation: dict[str, Any]) -> etree._ElementTree:
    attributes = decisions["xml"]["attributes"]
    root = etree.Element("TEXT", {(XML_LANG if name == "xml:lang" else name): value
                                  for name, value in attributes.items()})
    forms = form_decisions_by_row(decisions, source)
    overrides = translation_decisions_by_key(decisions, source)
    columns = decisions["xml"]["columns"]
    mapping = {record["source_row"]: record for record in reconciliation["records"]}

    for row in source["rows"]:
        source_row = row["source_row"]
        sentence_id = mapping[source_row]["output_id"]
        sentence = etree.SubElement(root, "S", id=sentence_id)

        decision = forms.get(source_row)
        headword = decision["output_form"] if decision else row["um_formosana"]
        form = etree.SubElement(sentence, "FORM", kindOf="original")
        form.text = headword
        if decision is not None:
            form.set("notes", decision["notes"])

        for extra in (decision or {}).get("alternate_forms", []):
            node = etree.SubElement(sentence, "FORM", kindOf="alternate")
            node.text = extra["form"]
            node.set("notes", extra["notes"])

        # A parsed headword carries markers van der Vlis does not write, so compare
        # his reading against the unparsed form or every parse looks like a variant.
        plain = headword
        if (decision or {}).get("parse") is not None:
            plain = re.sub(r"[<>-]", "", headword)
        alternate = strip_alternate_form(row[columns["alternate_form"]], plain,
                                         decisions, source_row)
        if alternate:
            node = etree.SubElement(sentence, "FORM", kindOf="alternate")
            node.text = alternate
            node.set("notes", "van der Vlis 1842.")

        emitted: dict[str, list[str]] = {}
        for spec in columns["translations"]:
            field = spec["source_field"]
            raw = row[field].strip()
            if not raw:
                continue
            if spec["role"] == "alt_when_different" and raw == row[spec["different_from"]].strip():
                continue
            readings, note = render_translation(raw, field, source_row,
                                                row["um_formosana"], decisions, overrides)
            language = spec["xml_lang"]
            for index, reading in enumerate(readings):
                if reading in emitted.setdefault(language, []):
                    continue
                emitted[language].append(reading)
                node = etree.SubElement(sentence, "TRANSL", {XML_LANG: language})
                if spec["role"] == "alt_when_different" or index > 0 or len(emitted[language]) > 1:
                    node.set("ver", "alt")
                if index == 0 and note:
                    node.set("notes", note)
                node.text = reading

        parse = (decision or {}).get("parse")
        if parse is not None:
            word = etree.SubElement(sentence, "W", id=f"{sentence_id}_W1")
            word_form = etree.SubElement(word, "FORM", kindOf="original")
            word_form.text = parse["word"]
            for index, morpheme in enumerate(parse["morphemes"], start=1):
                unit = etree.SubElement(word, "M", id=f"{sentence_id}_W1_M{index}")
                unit_form = etree.SubElement(unit, "FORM", kindOf="original")
                unit_form.text = morpheme

    etree.indent(root, space="    ")
    return etree.ElementTree(root)


def write_tree(tree: etree._ElementTree, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(str(path), encoding="UTF-8", xml_declaration=True, pretty_print=True)


def parse_args() -> argparse.Namespace:
    code_docs = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-docs", type=Path, default=code_docs)
    parser.add_argument("--output", type=Path,
                        default=code_docs.parent / "XML" / "Siraya" / "Utrecht_Manuscript.xml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    decisions, source, reconciliation = load_inputs(args.code_docs)
    tree = build_tree(decisions, source, reconciliation)
    write_tree(tree, args.output)
    print(f"Generated {len(source['rows'])} S records at {args.output}")


if __name__ == "__main__":
    main()
