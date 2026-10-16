#!/usr/bin/env python3
"""Generate QC/validation/ATTRIBUTES.md — every attribute the XML may carry.

POL-053: the XML attribute set is closed and documented. The XSD declares
no `anyAttribute`, so an undeclared attribute already fails validate_xml —
that is the whitelist. This builds the human-readable half from the same
schema, so the documentation cannot drift from what actually validates
(POL-039: the table is derived, not retyped).

    python QC/validation/attributes_catalogue.py            # write ATTRIBUTES.md
    python QC/validation/attributes_catalogue.py --check    # exit 1 if stale

`tests/validators/test_attributes_catalogue.py` runs --check, so a new
attribute fails CI until it is annotated and the catalogue regenerated.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

SCHEMA = Path(__file__).resolve().parent / "xml_template.xsd"
OUTPUT = Path(__file__).resolve().parent / "ATTRIBUTES.md"

XS = "{http://www.w3.org/2001/XMLSchema}"

# Document order, so the catalogue reads top-down like the XML does rather
# than alphabetically.
ELEMENT_ORDER = ["TEXT", "S", "W", "M", "FORM", "PHON", "TRANSL", "AUDIO"]


def _element_name(complex_type: etree._Element) -> str | None:
    """The element a complexType describes.

    Named types follow the `<ELEMENT>_Type` convention; an inline type is
    named by the xs:element that contains it (TEXT).
    """
    name = complex_type.get("name")
    if name:
        return name[:-5] if name.endswith("_Type") else name
    parent = complex_type.getparent()
    if parent is not None and parent.tag == f"{XS}element":
        return parent.get("name")
    return None


def _enumerations(schema: etree._ElementTree) -> dict[str, str]:
    """simpleType name -> 'a | b | c' for every *named* enumerated type."""
    out: dict[str, str] = {}
    for simple in schema.iter(f"{XS}simpleType"):
        name = simple.get("name")
        if not name:
            continue
        values = [e.get("value") for e in simple.iter(f"{XS}enumeration")]
        if values:
            out[name] = " | ".join(values)
    return out


def _inline_enum(attribute: etree._Element) -> str:
    """'a | b | c' for an attribute whose enumeration is declared inline

    (an `<xs:simpleType>` child under the attribute itself, rather than a
    `type="SomeName"` reference to a named simpleType). Legal XSD, and
    without this an attribute shaped this way would silently render '—'
    despite having real enumerated values.
    """
    simple = attribute.find(f"{XS}simpleType")
    if simple is None:
        return ""
    values = [e.get("value") for e in simple.iter(f"{XS}enumeration")]
    return " | ".join(values)


def _documentation(attribute: etree._Element) -> str:
    node = attribute.find(f"{XS}annotation/{XS}documentation")
    if node is None or not node.text:
        return ""
    # xs:documentation is indented block text; collapse to one line.
    return re.sub(r"\s+", " ", node.text).strip()


def collect() -> list[tuple[str, str, str, str, str]]:
    """(element, attribute, use, allowed_values, documentation).

    Sorted by the element's position in the XML, then attribute name.
    """
    schema = etree.parse(str(SCHEMA))
    enums = _enumerations(schema)
    rows: list[tuple[str, str, str, str, str]] = []
    for complex_type in schema.iter(f"{XS}complexType"):
        element = _element_name(complex_type)
        if element is None:
            continue
        for attribute in complex_type.findall(f"{XS}attribute"):
            name = attribute.get("name") or attribute.get("ref") or "?"
            use = attribute.get("use") or "optional"
            type_name = attribute.get("type") or ""
            values = enums.get(type_name, "") or _inline_enum(attribute)
            if not values and type_name.startswith("xs:"):
                values = type_name
            rows.append((element, name, use, values, _documentation(attribute)))

    def sort_key(row):
        element, attribute = row[0], row[1]
        rank = (ELEMENT_ORDER.index(element)
                if element in ELEMENT_ORDER else len(ELEMENT_ORDER))
        return (rank, element, attribute)

    return sorted(rows, key=sort_key)


def _table_cell(text: str) -> str:
    """Escape a value for use inside a Markdown table cell.

    Any free-form text placed in a cell — documentation prose, or an
    enum-values list rendered as `a | b | c` — can contain a literal
    `|`. GFM tables split on unescaped `|` regardless of surrounding
    backticks, so every such cell must go through this before being
    written into a row, or the pipe is read as an extra column
    delimiter and misaligns or splits the row.
    """
    return text.replace("|", "\\|")


def render() -> str:
    rows = collect()
    out = [
        "# XML attributes",
        "",
        "Every attribute a FormosanBank XML file may carry, generated from",
        "`QC/validation/xml_template.xsd` by",
        "`QC/validation/attributes_catalogue.py`. **Do not edit by hand** —",
        "annotate the attribute in the XSD and regenerate.",
        "",
        "The schema declares no `anyAttribute`, so this list is exhaustive:",
        "an attribute not named here fails `validate_xml.py`. Adding one",
        "requires an XSD declaration, an `xs:documentation` annotation, a",
        "regenerated catalogue, and a policy entry (POL-053).",
        "",
    ]
    current = None
    for element, attribute, use, values, doc in rows:
        if element != current:
            if current is not None:
                out.append("")
            current = element
            out += [
                f"## `<{element}>`",
                "",
                "| Attribute | Use | Allowed values | Meaning |",
                "| --- | --- | --- | --- |",
            ]
        shown = f"`{_table_cell(values)}`" if values else "—"
        out.append(f"| `{attribute}` | {use} | {shown} | {_table_cell(doc)} |")
    out += ["", f"{len(rows)} attributes across {len(set(r[0] for r in rows))} elements.", ""]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="exit 1 if ATTRIBUTES.md is not what this would write")
    args = parser.parse_args()

    undocumented = [
        f"{element}/@{attribute}"
        for element, attribute, _use, _values, doc in collect()
        if not doc.strip()
    ]
    if undocumented:
        print("POL-053: these attributes have no xs:documentation in the XSD:",
              file=sys.stderr)
        for name in undocumented:
            print(f"  {name}", file=sys.stderr)
        return 1

    rendered = render()
    if args.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
        if current != rendered:
            print(f"{OUTPUT} is stale; run: python {Path(__file__).name}",
                  file=sys.stderr)
            return 1
        print(f"{OUTPUT} is current.")
        return 0
    OUTPUT.write_text(rendered, encoding="utf-8")
    rows = collect()
    print(f"Wrote {OUTPUT} ({len(rows)} attributes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
