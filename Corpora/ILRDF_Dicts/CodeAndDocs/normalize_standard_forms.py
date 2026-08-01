#!/usr/bin/env python3
"""Derive clean sentence-level standard forms from ILRDF source forms.

The source API mixes surface text with morphological boundaries, spelling
alternatives, parenthetical alternatives, and occasional Chinese editor notes.
Those strings remain unchanged in FORM[@kindOf="original"].  This script only
updates direct S/FORM[@kindOf="standard"] elements.

Run without --apply for a dry run.  A successful second dry run after applying
must report zero changes.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from lxml import etree


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
PAREN_RE = re.compile(r"\([^()]*\)")
SPACE_RE = re.compile(r"\s+")
FULL_CLAUSE_ALT_RE = re.compile(r"(?<=[.!?])\s*/\s*")
TOKEN_ALT_RE = re.compile(r"(?P<left>\S+?)\s*/\s*(?P<right>\S+)")
TRAILING_PUNCT_RE = re.compile(r"([.!?,;:]+)$")


def strip_parenthetical_alternatives(text: str) -> str:
    """Keep the source-preferred outer reading and remove parenthetical ones."""
    previous = None
    while text != previous:
        previous = text
        text = PAREN_RE.sub("", text)
    return text


def choose_first_slash_alternatives(text: str) -> str:
    """Choose the source's first slash-ordered surface alternative.

    A slash after sentence punctuation separates complete clause variants.  A
    slash inside a clause separates neighboring lexical variants.  In the
    latter case punctuation carried by the rejected token is retained.
    """
    while match := FULL_CLAUSE_ALT_RE.search(text):
        boundary = re.search(r"[.!?]", text[match.end() :])
        if boundary is None:
            text = text[: match.start()]
            break
        rejected_end = match.end() + boundary.end()
        text = text[: match.start()] + text[rejected_end:]

    def keep_left(match: re.Match[str]) -> str:
        left = match.group("left")
        right = match.group("right")
        punctuation = TRAILING_PUNCT_RE.search(right)
        if punctuation and not TRAILING_PUNCT_RE.search(left):
            return left + punctuation.group(1)
        return left

    previous = None
    while text != previous and "/" in text:
        previous = text
        text = TOKEN_ALT_RE.sub(keep_left, text)
    return text.replace("/", "")


def normalize_standard(text: str) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    normalized = text

    if "=" in normalized:
        normalized = normalized.split("=", 1)[0]
        reasons.append("equals-alternative")
    if "(" in normalized or ")" in normalized:
        normalized = strip_parenthetical_alternatives(normalized)
        reasons.append("parenthetical-alternative")
    if "/" in normalized:
        normalized = choose_first_slash_alternatives(normalized)
        reasons.append("slash-alternative")
    if "-" in normalized:
        normalized = normalized.replace("-", "")
        reasons.append("morpheme-boundary")
    if "_" in normalized:
        normalized = normalized.replace("_", "")
        reasons.append("infix-placeholder")
    if CJK_RE.search(normalized):
        normalized = CJK_RE.sub("", normalized)
        reasons.append("inline-editor-note")

    normalized = SPACE_RE.sub(" ", normalized).strip()
    normalized = re.sub(r"\s+([,.!?;:])", r"\1", normalized)
    normalized = re.sub(r"([.!?])\1+", r"\1", normalized)
    return normalized, tuple(reasons)


def iter_xml_files(xml_dir: Path) -> list[Path]:
    return sorted(path for path in xml_dir.rglob("*.xml") if path.is_file())


def process(xml_dir: Path, apply: bool) -> tuple[int, Counter[str]]:
    parser = etree.XMLParser(remove_blank_text=False)
    changed_forms = 0
    reasons: Counter[str] = Counter()

    for path in iter_xml_files(xml_dir):
        tree = etree.parse(str(path), parser)
        changed_file = False
        for sentence in tree.iter("S"):
            standard = sentence.find('./FORM[@kindOf="standard"]')
            if standard is None or standard.text is None:
                continue
            normalized, form_reasons = normalize_standard(standard.text)
            if normalized == standard.text:
                continue
            if not normalized:
                raise ValueError(
                    f"normalization emptied {path}: S id={sentence.get('id')!r}"
                )
            standard.text = normalized
            changed_forms += 1
            reasons.update(form_reasons)
            changed_file = True

        if apply and changed_file:
            tree.write(
                str(path),
                encoding="UTF-8",
                xml_declaration=True,
                pretty_print=False,
            )

    return changed_forms, reasons


def find_residuals(xml_dir: Path) -> Counter[str]:
    parser = etree.XMLParser(remove_blank_text=False)
    residuals: Counter[str] = Counter()
    markers = {"-": "dash", "_": "underscore", "/": "slash", "=": "equals"}
    for path in iter_xml_files(xml_dir):
        tree = etree.parse(str(path), parser)
        for sentence in tree.iter("S"):
            standard = sentence.find('./FORM[@kindOf="standard"]')
            text = standard.text if standard is not None else None
            if not text:
                continue
            for marker, label in markers.items():
                if marker in text:
                    residuals[label] += 1
            if CJK_RE.search(text):
                residuals["CJK"] += 1
    return residuals


def main() -> int:
    default_xml = Path(__file__).resolve().parents[1] / "XML"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path, default=default_xml)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    changed, reasons = process(args.xml_dir.resolve(), args.apply)
    mode = "applied" if args.apply else "would change"
    print(f"{mode}: {changed} direct S-standard forms")
    for reason, count in sorted(reasons.items()):
        print(f"  {reason}: {count}")

    if args.apply:
        residuals = find_residuals(args.xml_dir.resolve())
        print("residual direct S-standard markers:")
        if residuals:
            for marker, count in sorted(residuals.items()):
                print(f"  {marker}: {count}")
            return 1
        print("  none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
