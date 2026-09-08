#!/usr/bin/env python3
"""Apply the reviewed source-annotation corrections to the ORIGINAL tier.

The source marks a reading it is unsure of by appending ``(?)`` to the word
on its plain-text line -- ``paqeteleng(?)`` -- and leaves the mark off the
morpheme line. That is an editorial annotation about the text, not part of
the text, so it must not reach the standard tier: ``?`` is the glottal
letter in Ferrell's orthography, so standardize.py converts it and the
standard form gains a glottal stop the language does not have
(``paqeteleng(')``).

The corpus used to fix that *after* standardize.py by overwriting the
generated standard FORM. This script fixes it at the source instead: it
removes the annotation from the S-level original FORM before standardize.py
runs, and records what it removed in that FORM's ``notes`` attribute, so
the standard and phonology tiers are simply derived and never edited.

Each correction is witness-gated: the sentence's original FORM must still
match the reviewed ``original_form`` in standard_surface_decisions.tsv, or
the run fails rather than silently correcting drifted text. Idempotent --
an already-corrected sentence is recognised by its notes attribute.

Usage
-----
    python scripts/apply_manual_corrections.py --corpora-path <XML dir>
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from normalize_sentence_standards import (  # noqa: E402
    DEFAULT_DECISIONS,
    SOURCE_ANNOTATION as ANNOTATION,
    current_punctuation,
    load_decisions,
    strip_source_annotation as strip_annotation,
)

DECISION = "remove_parenthesized_uncertainty"
NOTE = (
    "Source reading marked uncertain: the plain-text line prints {tokens}. "
    "The annotation is recorded here rather than left in the text, where "
    "standardize.py would read its ? as the glottal letter."
)


def annotated_tokens(text: str) -> list[str]:
    """The annotated whitespace tokens of ``text``, as the source prints them.

    Trailing sentence punctuation is trimmed so the note quotes the word and
    its annotation (``paqeteleng(?)``) rather than the whole token.
    """
    return [
        token.rstrip(".,;:!?\"'")
        for token in text.split()
        if ANNOTATION.search(token)
    ]


def correct_sentence(sentence: etree._Element, row: dict[str, str]) -> bool:
    """Strip the annotation from one S's original FORM. True if changed."""
    sentence_id = sentence.get("id")
    forms = [
        form
        for form in sentence.findall("FORM")
        if form.get("kindOf") == "original"
    ]
    if len(forms) != 1:
        raise ValueError(f"{sentence_id}: expected exactly one original FORM")
    form = forms[0]
    text = form.text or ""

    expected = row["original_form"]
    allowed = {expected, current_punctuation(expected)}
    if text in {strip_annotation(value) for value in allowed}:
        if not form.get("notes"):
            raise ValueError(
                f"{sentence_id}: annotation already stripped but not recorded"
            )
        return False
    if text not in allowed:
        raise ValueError(
            f"{sentence_id}: original FORM differs from the reviewed source"
        )

    tokens = annotated_tokens(text)
    if not tokens:
        raise ValueError(f"{sentence_id}: reviewed sentence carries no (?)")
    form.text = strip_annotation(text)
    form.set("notes", NOTE.format(tokens=" and ".join(tokens)))
    return True


def apply(corpora_path: Path, decisions_path: Path) -> int:
    rows = [row for row in load_decisions(decisions_path) if row["decision"] == DECISION]
    if not rows:
        raise ValueError("no source-annotation corrections found")

    by_file: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_file.setdefault(row["file"], []).append(row)

    corrected = 0
    for filename, file_rows in sorted(by_file.items()):
        path = corpora_path / filename
        if not path.exists():
            raise ValueError(f"{filename} not found under {corpora_path}")
        tree = etree.parse(str(path))
        sentences = {s.get("id"): s for s in tree.getroot().findall("S")}
        changed = False
        for row in file_rows:
            sentence = sentences.get(row["sentence_id"])
            if sentence is None:
                raise ValueError(f"{row['sentence_id']} is missing from {filename}")
            if correct_sentence(sentence, row):
                corrected += 1
                changed = True
        if changed:
            etree.indent(tree, space="    ")
            tree.write(
                str(path), xml_declaration=True, pretty_print=True, encoding="utf-8"
            )
    print(f"reviewed_corrections={len(rows)}")
    print(f"corrected_originals={corrected}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpora-path", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    args = parser.parse_args()
    raise SystemExit(apply(args.corpora_path.resolve(), args.decisions))


if __name__ == "__main__":
    main()
