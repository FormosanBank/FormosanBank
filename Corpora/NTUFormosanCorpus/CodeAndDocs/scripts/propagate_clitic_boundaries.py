#!/usr/bin/env python3
"""Propagate W-level clitic boundaries to the corresponding M elements.

The NTU parsers split W forms on ``=`` and then discard the separator from
the generated M forms. FormosanBank requires the cliticized M to retain that
boundary as a leading ``=``. This script maps each W boundary to its source
surface unit, finds the matching M in document order, and prefixes both M
FORM tiers. A trailing source ``=`` is retained on the last non-infix M.

Infix hosts are handled without treating the infix itself as a clitic. For
example, ``na=k<ua>upa`` maps the boundary to the root M ``k-upa``, not to
the infix M ``-ua-``. Repeated forms are resolved by their source occurrence
number. The script fails on an unresolved boundary, rewrites only files that
round-trip byte-identically, and is idempotent.
"""

import argparse
import collections
import os
import re
from pathlib import Path

import lxml.etree as etree

_ANGLE = re.compile(r"<[^<>]+>")
_INFIX_M = re.compile(r"^-.+-$")
_EDGE_PUNCT = ".,!?;:\\_"


def _original_form(elem):
    form = elem.find('./FORM[@kindOf="original"]')
    return "" if form is None else (form.text or "")


def _match_key(text):
    return re.sub(r"[-=<>]", "", text or "").strip().strip(_EDGE_PUNCT).casefold()


def _is_infix_m(text):
    return bool(_INFIX_M.fullmatch((text or "").strip()))


def split_units(text):
    """Return marker-delimited units and ``(next_unit_index, marker)`` pairs."""
    units = []
    markers = []
    current = []
    angle_depth = 0
    for char in text:
        if char == "<":
            angle_depth += 1
            current.append(char)
        elif char == ">":
            angle_depth = max(0, angle_depth - 1)
            current.append(char)
        elif angle_depth == 0 and char in "-=":
            if current:
                units.append("".join(current))
                current = []
            markers.append((len(units), char))
        else:
            current.append(char)
    if current:
        units.append("".join(current))
    return units, markers


def _candidate_indices(ms, key):
    return [
        index
        for index, m in enumerate(ms)
        if not _is_infix_m(_original_form(m))
        and _match_key(_original_form(m)) == key
    ]


def _select_candidate(units, unit_index, ms):
    target = units[unit_index]
    target_key = _match_key(target)
    candidates = _candidate_indices(ms, target_key)
    occurrence_key = target_key

    if not candidates and _ANGLE.search(target):
        root_key = _match_key(_ANGLE.sub("", target))
        candidates = _candidate_indices(ms, root_key)
        occurrence_key = root_key

    if not candidates:
        return None

    occurrence = 0
    for unit in units[: unit_index + 1]:
        unit_key = _match_key(_ANGLE.sub("", unit)) if occurrence_key != target_key else _match_key(unit)
        if unit_key == occurrence_key:
            occurrence += 1
    position = max(0, occurrence - 1)
    return candidates[min(position, len(candidates) - 1)]


def boundary_targets(w):
    """Return M indices to prefix and M indices to suffix for one W."""
    w_form = _original_form(w)
    ms = w.findall("M")
    if "=" not in w_form or not ms:
        return set(), set(), []
    if len(ms) == 1 and _original_form(ms[0]) == w_form:
        return set(), set(), []

    units, markers = split_units(w_form)
    prefix = set()
    suffix = set()
    unresolved = []
    for unit_index, marker in markers:
        if marker != "=":
            continue
        if unit_index >= len(units):
            candidates = [
                index
                for index, m in enumerate(ms)
                if _original_form(m).strip() and not _is_infix_m(_original_form(m))
            ]
            if not candidates:
                candidates = [
                    index for index, m in enumerate(ms) if _original_form(m).strip()
                ]
            if candidates:
                suffix.add(candidates[-1])
            else:
                unresolved.append((unit_index, "trailing"))
            continue
        if _match_key(units[unit_index]) == "∅":
            # A zero clitic must remain a whole-null M so add_phonology emits
            # PHON ∅ under POL-012. Retain its boundary on the preceding host
            # M edge, a convention already used in published FormosanBank XML.
            if unit_index == 0:
                unresolved.append((unit_index, "null clitic without host"))
                continue
            selected = _select_candidate(units, unit_index - 1, ms)
            if selected is None:
                unresolved.append((unit_index, "null clitic host"))
            else:
                suffix.add(selected)
            continue
        selected = _select_candidate(units, unit_index, ms)
        if selected is None:
            unresolved.append((unit_index, units[unit_index]))
        else:
            prefix.add(selected)
    return prefix, suffix, unresolved


def repair_w(w):
    prefix, suffix, unresolved = boundary_targets(w)
    if unresolved:
        return 0, unresolved
    changed = 0
    for index, m in enumerate(w.findall("M")):
        if index not in prefix and index not in suffix:
            continue
        for form in m.findall("FORM"):
            text = form.text or ""
            new = text
            if index in prefix and not new.startswith("="):
                new = "=" + new
            if index in suffix and not new.endswith("="):
                new += "="
            if new != text:
                form.text = new
                changed += 1
    return changed, []


def serialize(tree):
    return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")


def repair_corpus(xml_dir, dry_run=False):
    stats = collections.Counter()
    unresolved = []
    for dirpath, _, filenames in os.walk(xml_dir):
        for filename in sorted(filenames):
            if not filename.endswith(".xml"):
                continue
            path = os.path.join(dirpath, filename)
            original = open(path, "rb").read()
            tree = etree.parse(path)
            if serialize(tree) != original:
                raise RuntimeError(f"clitic repair round-trip guard failed: {path}")
            file_changed = False
            for w in tree.getroot().iter("W"):
                if "=" not in _original_form(w):
                    continue
                stats["W with clitic boundary"] += 1
                changed, problems = repair_w(w)
                if problems:
                    unresolved.append((path, w.get("id"), _original_form(w), problems))
                    continue
                if changed:
                    stats["W repaired"] += 1
                    stats["FORM tiers changed"] += changed
                    file_changed = True
            if file_changed:
                stats["files modified"] += 1
                if not dry_run:
                    with open(path, "wb") as handle:
                        handle.write(serialize(tree))
    if unresolved:
        lines = "\n".join(repr(item) for item in unresolved[:20])
        raise RuntimeError(
            f"unresolved clitic boundaries ({len(unresolved)}):\n{lines}"
        )
    for label in ("W with clitic boundary", "W repaired", "FORM tiers changed", "files modified"):
        print(f"{label}: {stats[label]}")
    return stats


def main():
    default_xml = Path(__file__).resolve().parents[2] / "XML"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml_dir", default=str(default_xml))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repair_corpus(args.xml_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
