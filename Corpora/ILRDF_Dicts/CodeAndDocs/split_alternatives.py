#!/usr/bin/env python3
"""Resolve source-side alternatives on the ORIGINAL tier.

The ILRDF source packs alternative wordings into one record three ways:

    =   "same as"        ata tu kmaanasapunuqi! = ata tu kmasapunuqi!
    ( ) bracketed         cyux szwi na (krahu bayhuy) / (hopa na behuy) qu …
    /   inline options    hatomi^/foliki^ han ako ko paliding.

Two different things hide under "alternative", and they get different
treatments (maintainer ruling 2026-09-07):

    spelling variant    the same utterance written differently --
                        'hiya' / 'hiyaʼ', 'musa' / 'musaʼ', 'betunx' /
                        'baytunux'. One record; the other spellings ride
                        along as FORM[@kindOf="alternate"].

    lexical alternative different wording -- 'mʼzwi' / 'mcisal',
                        'tanux' / 'mnaw tay tanux', 'sinsiy' /
                        'sinsi pcbaq biruʼ'. Separate <S> records.

Collapsing spelling variants into alternate FORMs is what keeps this
tractable. Expanding every site cartesianly produced up to 768 combinations of
a single Atayal sentence, most of them ungrammatical, because dialectal
spellings co-vary rather than combining freely.

Classification, in order of confidence:

    1. options differ in word count         -> lexical    (high confidence)
    2. same word count, similarity >= 0.50  -> spelling
    3. anything else                        -> NOT CONFIDENT

Rule 3 drops the fragment and logs it. The threshold is calibrated against the
maintainer's own rulings: spellings ran 0.83 0.80 0.80 0.67 0.67 0.62 0.60
0.50 0.33, lexical 0.17 and 0.00. At 0.50, eight of the nine spelling rulings
are captured and both lexical ones excluded. 'tay' / 'te' at 0.33 is lost —
the accepted cost of publishing only what we are confident of.

A record split by numbering resolves each example INDEPENDENTLY: an example
the cascade cannot read no longer takes its siblings with it.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import re
from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree
from rapidfuzz.distance import Levenshtein

# --- stage A: one record holding more than one sentence ----------------------

_NUMBERED = re.compile(r"(?:(?<=^)|(?<=[\s.!?]))([1-9])\s*[.．]\s*")
_SENTENCE_SLASH = re.compile(r"(?<=[.!?])\s*/\s*")
_BRACKET_ALT = re.compile(r"[（(]([^（()）]*)[）)](?:\s*/\s*[（(]([^（()）]*)[）)])+")
_BRACKET_OPTION = re.compile(r"[（(]([^（()）]*)[）)]")

# --- stage B: one sentence holding lexical or spelling options ---------------

#: An option is a bare token or a bracketed group. The source writes a
#: multi-word alternative in brackets -- 'trang / (trang balay)',
#: 'hakasi /(sikacuganan nua kipalengleng)' -- so without the bracketed form
#: here a site would match only the bare tokens either side of the slash and
#: silently lose the rest of the phrase.
_OPTION = r"(?:[（(][^（()）]*[）)]|[^\s/（()）]+)"
_SITE = re.compile(rf"{_OPTION}(?:\s*/\s*{_OPTION})+")
_OUTER_BRACKET = re.compile(r"^[（(]\s*(.*?)\s*[）)]$", re.S)
_TAIL = re.compile(r"^(.*?)([.,!?;:]*)$", re.S)
_CORE = "().,!?;:"
_BRACKETS = (("(", ")"), ("（", "）"), ("〔", "〕"))

#: Same-word-count options at or above this similarity are one word spelled
#: two ways. See the module docstring for the calibration.
SPELLING_SIMILARITY = 0.50

#: A fragment whose lexical sites would yield more records than this is not
#: something we can resolve with confidence either.
MAX_READINGS = 4

_EQUALS_INLINE = re.compile(r"\s*[（(]\s*=\s*([^）)]*)[）)]")
_EQUALS_TRAILING = re.compile(r"\s*=\s*(.+)$", re.S)


@dataclass
class Reading:
    """One published record: its text, plus other spellings of that text."""
    text: str
    alternates: list[str] = field(default_factory=list)


def _tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([,.!?;:])", r"\1", text)


def _balanced(text: str) -> bool:
    return all(text.count(a) == text.count(b) for a, b in _BRACKETS)


def _norm(word: str) -> str:
    return word.strip(_CORE).casefold()


def classify_site(options: list[str]) -> str | None:
    """'lexical', 'spelling', or None when neither reading is confident."""
    if len(options) < 2 or not all(o.strip(_CORE) for o in options):
        return None
    if any(not _balanced(o) for o in options):
        return None                    # a site may not straddle a bracket
    if len({len(o.split()) for o in options}) > 1:
        return "lexical"
    similarity = min(
        Levenshtein.normalized_similarity(_norm(options[0]), _norm(other))
        for other in options[1:]
    )
    return "spelling" if similarity >= SPELLING_SIMILARITY else None


def stage_a(text: str) -> list[str]:
    """Split a record that holds more than one sentence into fragments."""
    markers = list(_NUMBERED.finditer(text))
    digits = [m.group(1) for m in markers]
    if len(markers) > 1 and digits == [str(i + 1) for i in range(len(digits))]:
        parts = [p.strip() for p in _NUMBERED.split(text)
                 if p and not p.isdigit() and p.strip()]
        if len(parts) > 1:
            return parts
    if len(markers) == 1 and digits == ["1"] and markers[0].start() == 0:
        stripped = text[markers[0].end():].strip()
        if stripped:
            return [stripped]

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


def _options(site: str) -> tuple[list[str], str]:
    """Options at a site, with sentence punctuation lifted out of the last.

    A bracketed option is unwrapped: the brackets delimit a multi-word
    alternative, they are not part of it.
    """
    raw = [p for p in re.split(r"\s*/\s*", site) if p]
    tail = _TAIL.match(raw[-1]).group(2) if raw else ""
    options = []
    for part in raw:
        body = _TAIL.match(part).group(1)
        unwrapped = _OUTER_BRACKET.match(body)
        options.append(unwrapped.group(1) if unwrapped else body)
    return options, tail


def stage_b(text: str) -> list[Reading] | None:
    """Resolve one sentence's options, or None when not confident."""
    sites = _SITE.findall(text)
    if not sites:
        return None if "/" in text else [Reading(text)]

    spans, kinds, opts, tails = [], [], [], []
    cursor = 0
    for site in sites:
        start = text.index(site, cursor)
        cursor = start + len(site)
        options, tail = _options(site)
        kind = classify_site(options)
        if kind is None:
            return None
        spans.append((start, cursor))
        kinds.append(kind)
        opts.append(options)
        tails.append(tail)

    lexical = [i for i, k in enumerate(kinds) if k == "lexical"]
    spelling = [i for i, k in enumerate(kinds) if k == "spelling"]
    combinations = (
        list(itertools.product(*(range(len(opts[i])) for i in lexical)))
        if lexical else [()]
    )
    if len(combinations) > MAX_READINGS:
        return None
    depth = max((len(opts[i]) for i in spelling), default=1)

    def render(choice: dict[int, int]) -> str:
        out, last = [], 0
        for index, (start, end) in enumerate(spans):
            out.append(text[last:start])
            pick = min(choice.get(index, 0), len(opts[index]) - 1)
            out.append(opts[index][pick] + tails[index])
            last = end
        out.append(text[last:])
        return _tidy("".join(out))

    readings: list[Reading] = []
    for combo in combinations:
        base = dict(zip(lexical, combo))
        primary = render(base)
        if not primary.strip() or "/" in primary or not _balanced(primary):
            return None
        alternates: list[str] = []
        for level in range(1, depth):
            variant = render({**base, **{i: level for i in spelling}})
            if variant != primary and variant not in alternates:
                alternates.append(variant)
        if primary not in [r.text for r in readings]:
            readings.append(Reading(primary, alternates))
    return readings or None


def resolve_equals(text: str) -> list[str]:
    """The readings a '=' offers, or the text unchanged when it has none."""
    match = _EQUALS_INLINE.search(text)
    if match is not None:
        head, tail = text[: match.start()], text[match.end():]
        word = re.search(r"(\S+)\s*$", head)
        if word is None:
            return [_tidy(head + tail)]
        return [_tidy(head + tail),
                _tidy(head[: word.start(1)] + match.group(1) + tail)]
    match = _EQUALS_TRAILING.search(text)
    if match is not None:
        return [_tidy(text[: match.start()]), _tidy(match.group(1))]
    return [text]


def split_record(text: str) -> tuple[list[Reading], list[str]]:
    """Return (published readings, fragments dropped as unresolvable).

    Fragments are independent: an example the cascade cannot read does not
    take its siblings with it.
    """
    readings: list[Reading] = []
    dropped: list[str] = []
    for after_equals in resolve_equals(text):
        for fragment in stage_a(after_equals):
            resolved = stage_b(fragment)
            if resolved is None:
                dropped.append(fragment)
                continue
            for reading in resolved:
                if reading.text and reading.text not in [r.text for r in readings]:
                    readings.append(reading)
    return readings, dropped


_SUFFIX = "abcdefghijklmnopqrstuvwxyz"


def process(xml_dir: Path, apply: bool, report: Path | None) -> dict[str, int]:
    counts = {"records": 0, "unchanged": 0, "rewritten": 0, "published": 0,
              "deleted": 0, "fragments_dropped": 0, "alternates": 0}
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
            readings, dropped = split_record(source)
            for fragment in dropped:
                counts["fragments_dropped"] += 1
                rows.append({"id": sentence.get("id"), "verdict": "dropped",
                             "fragment": fragment, "source": source})
            if not readings:
                counts["deleted"] += 1
                root.remove(sentence)
                changed = True
                continue
            if (len(readings) == 1 and readings[0].text == source
                    and not readings[0].alternates):
                counts["unchanged"] += 1
                continue
            counts["rewritten"] += 1
            counts["published"] += len(readings)
            rows.append({"id": sentence.get("id"), "verdict": "resolved",
                         "fragment": "", "source": source})
            index = list(root).index(sentence)
            for offset, reading in enumerate(readings):
                clone = etree.fromstring(etree.tostring(sentence))
                if len(readings) > 1:
                    clone.set("id", f"{sentence.get('id')}_{_SUFFIX[offset]}")
                original = clone.find('FORM[@kindOf="original"]')
                original.text = reading.text
                original.set("notes", f"source: {source}")
                for position, spelling in enumerate(reading.alternates, start=1):
                    node = etree.Element("FORM", kindOf="alternate")
                    node.text = spelling
                    clone.insert(position, node)
                    counts["alternates"] += 1
                root.insert(index + offset, clone)
            root.remove(sentence)
            changed = True
        if apply and changed:
            tree.write(str(path), encoding="UTF-8", xml_declaration=True)
    if report is not None and rows:
        report.parent.mkdir(parents=True, exist_ok=True)
        with report.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["id", "verdict", "fragment", "source"])
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
    c = process(args.xml_dir.resolve(), args.apply,
                args.report if args.apply else None)
    print(f"{'applied' if args.apply else 'would change'}: "
          f"{c['rewritten']} records rewritten into {c['published']} "
          f"({c['alternates']} alternate spellings), {c['deleted']} deleted, "
          f"{c['fragments_dropped']} fragments dropped, "
          f"{c['unchanged']} unchanged ({c['records']} examined)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
