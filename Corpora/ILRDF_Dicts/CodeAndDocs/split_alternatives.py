#!/usr/bin/env python3
"""Split source-side alternatives into separate <S> records.

The ILRDF source packs alternative wordings into one record three ways:

    =   "same as"        ata tu kmaanasapunuqi! = ata tu kmasapunuqi!
    ( ) bracketed phrase  cyux szwi na (krahu bayhuy) / (hopa na behuy) qu …
    /   lexical options   hatomi^/foliki^ han ako ko paliding.

Each distinct option becomes its own record. This runs on the ORIGINAL tier,
before clean_xml and standardize, so no published FORM ever carries a
delimiter; the source string is preserved in FORM/@notes and split ids take a
letter suffix (…_a, …_b, …_c).

The cascade runs in two stages, because a numbered record often also contains
word alternations and a flat pass conflates them.

    Stage A, sentence-level  — a record holding more than one sentence
      1. numbered multi-example, '1. … 2. …'
      2. sentence alternation, a slash after '.', '!' or '?'
      3. bracketed phrase alternation, '(A) / (B)', substituted into the frame

    Stage B, word-level      — a record holding one sentence with options
      4. exactly one alternation site with exactly two options
      5. exactly one site with N mutually similar options
      6. ANYTHING ELSE -> delete

Rule 6 is the important one. With two or more independent alternation sites
you cannot know which combinations the source licenses: the variants are
dialectal and co-vary, so a cartesian split would manufacture ungrammatical
sentences. One Atayal record reaches 768 combinations. Such records are
deleted, and the count is published in the README rather than buried.

Attestation plays no part: the cascade decides by structure alone.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import re
from pathlib import Path

from lxml import etree

# --- Stage A -----------------------------------------------------------------

#: '1.' / '2.' at the start, or after whitespace or sentence punctuation.
_NUMBERED = re.compile(r"(?:(?<=^)|(?<=[\s.!?]))([1-9])\s*\.\s*")
#: A slash directly after sentence punctuation separates whole clauses.
_SENTENCE_SLASH = re.compile(r"(?<=[.!?])\s*/\s*")
#: '(A) / (B)' — two or more bracketed phrases offered as alternatives.
_BRACKET_ALT = re.compile(r"\(([^()]*)\)(?:\s*/\s*\(([^()]*)\))+")
_BRACKET_OPTION = re.compile(r"\(([^()]*)\)")

# --- Stage B -----------------------------------------------------------------

#: One alternation site: tokens joined by slashes, no whitespace inside a token.
_SITE = re.compile(r"[^\s/]+(?:\s*/\s*[^\s/]+)+")
#: Trailing sentence punctuation carried by an option.
_TAIL = re.compile(r"^(.*?)([.,!?;:]*)$", re.S)
#: Options are compared on their letters, not their punctuation.
_CORE = "().,!?;:"
#: Three or more options must look like variants of each other.
_SIMILARITY = 0.5

# --- '=' ---------------------------------------------------------------------

_EQUALS_INLINE = re.compile(r"\s*\(\s*=\s*([^)]*)\)")
_EQUALS_TRAILING = re.compile(r"\s*=\s*(.+)$", re.S)


def _tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    return text


def resolve_equals(text: str) -> list[str]:
    """Return the readings a '=' offers, or a single reading if it has none.

    Inline '(= x)' replaces the preceding word; a trailing '= …' is a whole
    second phrasing of the sentence.
    """
    match = _EQUALS_INLINE.search(text)
    if match is not None:
        head, tail = text[: match.start()], text[match.end():]
        word = re.search(r"(\S+)\s*$", head)
        if word is None:
            return [_tidy(head + tail)]
        replaced = head[: word.start(1)] + match.group(1) + tail
        return [_tidy(head + tail), _tidy(replaced)]
    match = _EQUALS_TRAILING.search(text)
    if match is not None:
        return [_tidy(text[: match.start()]), _tidy(match.group(1))]
    # No '=': pass the source through untouched. Tidying here would silently
    # edit the original tier of records this task has no business changing --
    # whitespace and punctuation spacing belong to clean_xml.
    return [text]


def stage_a(text: str) -> list[str]:
    """Sentence-level split: a record holding more than one sentence."""
    # A marker sequence must run 1, 2, 3 …  Without that test a sentence-final
    # numeral is read as a marker and the sentence is silently truncated:
    # "… ka btunux o 3." would lose its last two characters.
    markers = list(_NUMBERED.finditer(text))
    digits = [m.group(1) for m in markers]
    consecutive = digits == [str(i + 1) for i in range(len(digits))]
    if len(markers) > 1 and consecutive:
        parts = [p.strip() for p in _NUMBERED.split(text)
                 if p and not p.isdigit() and p.strip()]
        if len(parts) > 1:
            return parts
    if len(markers) == 1 and digits == ["1"] and markers[0].start() == 0:
        stripped = text[markers[0].end():].strip()
        if stripped:
            return [stripped]          # a lone leading '1.' is a marker to drop

    if _SENTENCE_SLASH.search(text):
        parts = [p.strip() for p in _SENTENCE_SLASH.split(text) if p.strip()]
        if len(parts) > 1:
            return parts

    match = _BRACKET_ALT.search(text)
    if match is not None:
        options = _BRACKET_OPTION.findall(match.group(0))
        return [_tidy(text[: match.start()] + option + text[match.end():])
                for option in options]

    return [text]


def _options(site: str) -> tuple[list[str], list[str], str]:
    """Split one site into (substitutable options, comparable cores, tail).

    Trailing sentence punctuation belongs to the sentence, not to the option
    that happens to sit last, so it is lifted out and re-attached to every
    reading. Without this, 'mitaʼ / mangay.' would yield 'mitaʼ' unpunctuated.
    """
    raw = [p for p in re.split(r"\s*/\s*", site) if p]
    tail = _TAIL.match(raw[-1]).group(2) if raw else ""
    options = [_TAIL.match(p).group(1) for p in raw]
    cores = [p.strip(_CORE) for p in options]
    return options, cores, tail


def stage_b(text: str) -> list[str] | None:
    """Word-level split, or None when the record cannot be interpreted."""
    sites = _SITE.findall(text)
    if not sites:
        return None if "/" in text else [text]
    if len(sites) > 1:
        return None                        # cannot know which combinations hold

    options, cores, tail = _options(sites[0])
    if len(options) < 2 or not all(cores):
        return None
    if len(options) > 2:
        similarity = [
            difflib.SequenceMatcher(None, cores[0].lower(), core.lower()).ratio()
            for core in cores[1:]
        ]
        if not all(ratio >= _SIMILARITY for ratio in similarity):
            return None

    start = text.index(sites[0])
    head, rest = text[:start], text[start + len(sites[0]):]
    readings = [_tidy(head + option + tail + rest) for option in options]
    if any("/" in r or not r.strip() for r in readings):
        return None
    seen: list[str] = []
    for reading in readings:
        if reading not in seen:
            seen.append(reading)
    return seen


def split_record(text: str) -> list[str] | None:
    """The whole cascade. None means the record is uninterpretable — delete it."""
    readings: list[str] = []
    for after_equals in resolve_equals(text):
        for fragment in stage_a(after_equals):
            resolved = stage_b(fragment)
            if resolved is None:
                return None
            readings.extend(resolved)
    out: list[str] = []
    for reading in readings:
        if reading and reading not in out:
            out.append(reading)
    return out or None


# --- corpus application ------------------------------------------------------

_SUFFIX = "abcdefghijklmnopqrstuvwxyz"


def process(xml_dir: Path, apply: bool, report: Path | None) -> dict[str, int]:
    counts = {"records": 0, "split": 0, "deleted": 0, "produced": 0, "unchanged": 0}
    rows: list[dict[str, object]] = []
    for path in sorted(xml_dir.rglob("*.xml")):
        tree = etree.parse(str(path))
        root = tree.getroot()
        changed = False
        for sentence in list(root.findall("S")):
            form = sentence.find('FORM[@kindOf="original"]')
            if form is None or not form.text:
                continue
            counts["records"] += 1
            source = form.text
            readings = split_record(source)
            if readings is None:
                rows.append({"id": sentence.get("id"), "verdict": "deleted",
                             "sites": len(_SITE.findall(source)), "source": source})
                counts["deleted"] += 1
                root.remove(sentence)
                changed = True
                continue
            if readings == [source]:
                counts["unchanged"] += 1
                continue
            if len(readings) > len(_SUFFIX):
                raise ValueError(f"{sentence.get('id')}: {len(readings)} readings")
            counts["split"] += 1
            counts["produced"] += len(readings)
            rows.append({"id": sentence.get("id"), "verdict": "split",
                         "sites": len(_SITE.findall(source)), "source": source})
            index = list(root).index(sentence)
            for offset, reading in enumerate(readings):
                clone = etree.fromstring(etree.tostring(sentence))
                clone.set("id", f"{sentence.get('id')}_{_SUFFIX[offset]}")
                clone_form = clone.find('FORM[@kindOf="original"]')
                clone_form.text = reading
                clone_form.set("notes", f"source: {source}")
                root.insert(index + offset, clone)
            root.remove(sentence)
            changed = True
        if apply and changed:
            tree.write(str(path), encoding="UTF-8", xml_declaration=True)
    if report is not None and rows:
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["id", "verdict", "sites", "source"])
            writer.writeheader()
            writer.writerows(rows)
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--xml-dir", type=Path,
                        default=Path(__file__).resolve().parents[1] / "XML")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path,
                        default=Path(__file__).resolve().parent / "docs" / "split_report.csv")
    args = parser.parse_args()
    counts = process(args.xml_dir.resolve(), args.apply,
                     args.report if args.apply else None)
    mode = "applied" if args.apply else "would change"
    print(f"{mode}: {counts['split']} records split into {counts['produced']}, "
          f"{counts['deleted']} deleted, {counts['unchanged']} unchanged "
          f"({counts['records']} examined)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
