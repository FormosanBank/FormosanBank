#!/usr/bin/env python3
"""Write RauDong's unknown glosses as ``<UNCLEAR/>`` (POL-021, POL-061).

Rau & Dong gloss six morphemes ``?`` (Chinese and English) and give text 9
sentence 23 the sentence translations ``句意不詳`` / ``(Sentence meaning not
clear``. Under POL-021 and POL-061 as amended 2026-10-17:

* a word or morpheme gloss the source declares unknown (its ``?``) is
  ``<TRANSL ...><UNCLEAR/></TRANSL>`` (action ``unclear``);
* a sentence translation that is wholly unknown is not emitted (action
  ``omit``).

Glosses the source simply leaves empty (the five words above five of those
morphemes) are NOT converted and stay empty. Maintainer, 2026-10-18:
"`<UNCLEAR/>` is really for when the source declares it unclear, rather than
just fails to gloss."

Every change is a row of ``unclear_glosses.tsv`` next to this script (POL-038:
the table is the record, nothing is hand-edited). A row names the TEXT/@id,
the level (S, W or M), the element id, the TRANSL's xml:lang, the text the
snapshot gives that TRANSL, and the action. The script fails, writing nothing,
when

* a row's element or TRANSL is missing, or its text is not ``snapshot_text``
  (the snapshot changed under the table);
* after the table is applied, any W or M gloss or S translation is still
  exactly ``?``/``??``/``???`` (a case the table does not cover). Empty
  glosses are not checked: they are left as they are.

A source's doubt about a gloss it did give (text 2 M 8_22_1 ``糞(日語?)``) is
not a wholly unknown gloss and is left as written.

It runs last in generate_xml.sh, after add_phonology: the shared standardize
and add_phonology steps do not handle ``<UNCLEAR/>`` inside TRANSL. Files are
written back with their own XML declaration line and otherwise as lxml
serialises the parsed tree, which is byte-identical to the input outside the
changed elements. A file with no row is not rewritten.

Usage:
    python apply_unclear_glosses.py --corpora_path <XML dir> [--table <tsv>]
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
DEFAULT_TABLE = HERE / "unclear_glosses.tsv"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
COLUMNS = ["text", "level", "id", "lang", "snapshot_text", "action"]
ACTION_FOR_LEVEL = {"S": "omit", "W": "unclear", "M": "unclear"}
WHOLE_MARKER = re.compile(r"[?？]{1,3}")


def load_table(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t", quoting=csv.QUOTE_NONE)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"{path.name}: header must be {COLUMNS}, got {reader.fieldnames}")
        rows = list(reader)
    keys = [(r["text"], r["level"], r["id"], r["lang"]) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError(f"{path.name}: duplicate rows")
    for row in rows:
        expected = ACTION_FOR_LEVEL.get(row["level"])
        if expected is None:
            raise ValueError(f"{path.name}: level must be S, W or M: {row}")
        if row["action"] != expected:
            raise ValueError(
                f"{path.name}: a {row['level']} row's action must be {expected!r}: {row}")
    return rows


def leftovers(root: etree._Element) -> list[str]:
    """Wholly unknown glosses or translations the table did not cover."""
    found = []
    for transl in root.iter("TRANSL"):
        if len(transl):  # holds an UNCLEAR (or other markup): already handled
            continue
        parent = transl.getparent()
        text = (transl.text or "").strip()
        if parent.tag in ("S", "W", "M") and WHOLE_MARKER.fullmatch(text):
            found.append(f"{root.get('id')} {parent.tag} {parent.get('id')} "
                         f"{transl.get(XML_LANG)} {transl.text!r}")
    return found


def apply_rows(root: etree._Element, rows: list[dict[str, str]], stats: Counter) -> None:
    for row in rows:
        where = f"{row['text']} {row['level']} {row['id']} {row['lang']}"
        matches = [e for e in root.iter(row["level"]) if e.get("id") == row["id"]]
        if len(matches) != 1:
            raise ValueError(f"{where}: {len(matches)} elements with that id")
        element = matches[0]
        transls = [t for t in element.findall("TRANSL") if t.get(XML_LANG) == row["lang"]]
        if len(transls) != 1:
            raise ValueError(f"{where}: {len(transls)} TRANSL with that xml:lang")
        transl = transls[0]
        if len(transl) or (transl.text or "") != row["snapshot_text"]:
            raise ValueError(
                f"{where}: TRANSL is {etree.tostring(transl, encoding='unicode').strip()!r}, "
                f"table expects text {row['snapshot_text']!r}")
        if row["action"] == "omit":
            element.remove(transl)  # lxml removes the tail with it
            stats["omitted_sentence_translations"] += 1
        else:
            transl.text = None
            etree.SubElement(transl, "UNCLEAR")
            stats[f"unclear_{row['level'].lower()}_glosses"] += 1


def write_preserving_declaration(path: Path, tree: etree._ElementTree) -> None:
    raw = path.read_bytes()
    declaration = raw.split(b"\n", 1)[0] if raw.startswith(b"<?xml") else None
    body = etree.tostring(tree.getroot(), encoding="unicode").encode("utf-8")
    trailing = raw[len(raw.rstrip()):]
    path.write_bytes((declaration + b"\n" if declaration is not None else b"") + body + trailing)


def apply(corpora_path: Path, table_path: Path) -> Counter:
    rows = load_table(table_path)
    by_text: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_text.setdefault(row["text"], []).append(row)

    stats: Counter = Counter()
    trees = {}
    problems = []
    for path in sorted(corpora_path.rglob("*.xml")):
        tree = etree.parse(str(path))
        text_id = tree.getroot().get("id")
        if text_id in trees:
            raise ValueError(f"two files carry TEXT id {text_id!r}")
        trees[text_id] = (path, tree)
        if text_id in by_text:
            apply_rows(tree.getroot(), by_text[text_id], stats)
        problems.extend(leftovers(tree.getroot()))

    unknown = sorted(set(by_text) - set(trees))
    if unknown:
        raise ValueError(f"{table_path.name}: no file has TEXT id {unknown}")
    if problems:
        raise ValueError(
            "wholly unknown glosses/translations not in the table:\n  " + "\n  ".join(problems))

    # Nothing is written until every check above has passed.
    for text_id in by_text:
        path, tree = trees[text_id]
        write_preserving_declaration(path, tree)
        stats["files_changed"] += 1
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--corpora_path", type=Path, required=True)
    parser.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    args = parser.parse_args()
    try:
        stats = apply(args.corpora_path.resolve(), args.table)
    except ValueError as error:
        print(f"apply_unclear_glosses: {error}", file=sys.stderr)
        return 1
    for key in ("unclear_w_glosses", "unclear_m_glosses",
                "omitted_sentence_translations", "files_changed"):
        print(f"{key}={stats[key]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
