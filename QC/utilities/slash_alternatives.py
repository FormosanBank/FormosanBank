#!/usr/bin/env python3
"""Slash alternatives: resolve their scope, and audit a resolution.

A source that offers alternatives inside one printed example -- ``Sally likes
x / y`` -- becomes one ``<S>`` per option (POL-027), and the hard part is not
the split but the **scope**: how much of the sentence alternates, and how much
is shared. Getting it wrong produces a reading that is missing a word, or a
fragment with no verb, and nothing downstream notices.

Two entry points, deliberately separate:

``resolve_scope(raw, morphemes=None, translation=None)``
    Propose the readings, with the evidence used and a confidence.

``audit(raw, options, translation=None)``
    Check a resolution somebody else produced. This is the one that scales: a
    corpus that curated its scopes by hand can be re-checked at merge instead
    of by eye.

Where the scope evidence comes from, in order of strength:

1. **The morpheme tier.** ``NTUFormosanCorpus`` resolves the scope from it and
   this module reuses that reading: in ``pua/mua/mu-lebe`` with M1 =
   ``pua/mua/mu`` and M2 = ``lebe``, only M1 alternates, so the readings are
   ``pua-lebe`` / ``mua-lebe`` / ``mu-lebe`` and NOT the naive string split.
   Corpora with an M tier should pass it.
2. **The translation's own slash.** ``I called the dog/pig/chicken`` says there
   are three readings and that they differ in one noun. A slash count in the
   translation that disagrees with the option count is a finding on its own,
   and a translation that keeps its slash after expansion means the readings
   were never given their own (POL-026/POL-027).
3. **Shared prefix and suffix.** With neither of the above, the longest shared
   material on each side of the slash bounds the alternation.

Nothing here rewrites data. ``audit`` returns findings; the caller decides.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Sequence
from xml.etree import ElementTree as ET

SLASH = "/"
_STRIP = ".,;:?!`'\"()"
_DASHES = "-‐‑‒–—"


def tokens(text: str) -> list[str]:
    return [piece for piece in re.split(r"\s+", text.strip()) if piece]


def _bare(token: str) -> str:
    return token.strip(_STRIP).casefold()


def _bag(option: str) -> Counter:
    return Counter(_bare(piece) for piece in tokens(option) if _bare(piece))


@dataclass
class Finding:
    """One problem with a resolution. ``severity`` is the caller's to act on."""

    rule: str
    severity: str
    message: str
    detail: str = ""

    def __str__(self) -> str:
        tail = f" ({self.detail})" if self.detail else ""
        return f"{self.rule} {self.severity}: {self.message}{tail}"


@dataclass
class Scope:
    """A proposed reading of one slash-bearing source string."""

    options: list[str]
    prefix: str = ""
    suffix: str = ""
    alternants: list[str] = field(default_factory=list)
    evidence: str = ""
    confidence: str = "low"
    rejected: list[list[str]] = field(default_factory=list)


# --------------------------------------------------------------------------
# resolution


def _morpheme_scope(raw: str, morphemes: Sequence[Sequence[str]]) -> Scope | None:
    """NTU's reading: the slash scope is the morpheme, not the word.

    ``morphemes`` is one sequence of morpheme FORMs per word of the sentence.
    A morpheme either alternates N ways or is shared; a single consistent N
    across the word is the option count, and anything else is left alone.
    """
    counts = {
        len(form.split(SLASH))
        for word in morphemes
        for form in word
        if SLASH in form
    }
    if len(counts) != 1:
        return None
    (count,) = counts
    if count < 2:
        return None
    readings = []
    for index in range(count):
        words = []
        for word in morphemes:
            pieces = [
                form.split(SLASH)[index] if SLASH in form else form for form in word
            ]
            words.append("-".join(pieces))
        readings.append(" ".join(words))
    if len(set(readings)) != count:
        return None
    return Scope(
        options=readings,
        alternants=[
            form for word in morphemes for form in word if SLASH in form
        ],
        evidence="morpheme tier",
        confidence="high",
    )


def _permutation(left: Sequence[str], right: Sequence[str]) -> bool:
    return Counter(_bare(x) for x in left) == Counter(_bare(x) for x in right)


def _common_prefix(left: Sequence[str], right: Sequence[str]) -> int:
    n = 0
    while n < min(len(left), len(right)) and _bare(left[n]) == _bare(right[n]):
        n += 1
    return n


def _common_suffix(left: Sequence[str], right: Sequence[str]) -> int:
    n = 0
    while (
        n < min(len(left), len(right))
        and _bare(left[-1 - n]) == _bare(right[-1 - n])
    ):
        n += 1
    return n


def _repeats_a_token(words: Sequence[str]) -> bool:
    """A reading that says the same word twice in a row is a mis-split.

    `kan qca-i / kan p-acay-i ihu` prints the shared `kan` on both sides of the
    slash. Splitting one word off each side glues the two copies together
    (`... kan kan p-acay-i ihu`), and that doubled word is the tell.
    """
    return any(_bare(a) == _bare(b) for a, b in zip(words, words[1:]))


#: Sentence-final marks that close a frame rather than an alternant.
CLOSERS = "?!.\u2019'\u201d\"\u00bb"


def _closed(scope: Scope, closing: str) -> Scope:
    """Re-attach the frame's closing punctuation to every reading."""
    if not closing:
        return scope
    scope.options = [option + closing for option in scope.options]
    if scope.suffix:
        scope.suffix += closing
    return scope


def _affix_scope(raw: str) -> Scope:
    """Bound the alternation without a morpheme tier.

    The printed string is ``PREFIX A / B SUFFIX``, and the shared material is
    printed once, so the string alone cannot say where PREFIX stops and A
    starts. What it can do is rank the candidates.

    Two shapes have to be handled before ranking, because both make the naive
    reading produce a reading that repeats a word:

    * **Shared material printed on both sides.** `ma-pitu-'un iza nak a
      qamishan / yaku a qamishan` prints `a qamishan` twice. It is stripped from
      both sides first and re-attached to every reading.
    * **An alternant that starts with a shared word.** `kan qca-i / kan
      p-acay-i ihu` prints `kan` at the head of both alternants. Nothing
      identifies it in advance, so candidates that glue two copies of a word
      together are rejected instead.

    Ranking then prefers the *balanced* candidate — an alternation is between
    comparable things, so alternants of equal length beat a lopsided pair — and
    only then the shortest. Every candidate considered is kept on the Scope so
    a reviewer sees what was rejected.
    """
    # Sentence-final punctuation belongs to the FRAME, not to the last
    # alternant. `Why do you hate me/us?` splits into `... me` and `us?`, and
    # the reading that lost the question mark is not a sentence. Held aside and
    # re-attached to every reading (maintainer, 2026-09-11).
    closing = ""
    while raw and raw[-1] in CLOSERS:
        closing = raw[-1] + closing
        raw = raw[:-1]
    raw = raw.rstrip()

    parts = [part.strip() for part in raw.split(SLASH)]
    if len(parts) != 2:
        # Three or more readings are a bare list of alternants inside one
        # shared frame: `I called the dog/pig/chicken` prints the frame once,
        # on the first part only. The alternants are the trailing run of the
        # first part as long as the longest of the rest, and everything before
        # it is shared.
        rest = [tokens(part) for part in parts[1:]]
        first = tokens(parts[0])
        width = max((len(option) for option in rest), default=0)
        if width and len(first) > width:
            shared = first[: len(first) - width]
            alternants = [first[len(first) - width :]] + rest
            return _closed(
                Scope(
                    options=[" ".join(shared + option) for option in alternants],
                    prefix=" ".join(shared),
                    alternants=[" ".join(option) for option in alternants],
                    evidence=(
                        f"{len(parts)} readings; the frame is printed once and "
                        f"the alternants are {width} token(s) each"
                    ),
                    confidence="medium",
                ),
                closing,
            )
        return _closed(
            Scope(
                options=parts,
                alternants=parts,
                evidence="more than two readings; printed split kept",
                confidence="low",
            ),
            closing,
        )
    left, right = tokens(parts[0]), tokens(parts[1])
    if _permutation(left, right):
        return _closed(Scope(
            options=[" ".join(left), " ".join(right)],
            alternants=[" ".join(left), " ".join(right)],
            evidence="the two sides are the same words in a different order",
            confidence="high",
        ), closing)

    # Shared material the source printed on both sides of the slash.
    tail = _common_suffix(left, right)
    shared_tail = left[len(left) - tail :] if tail else []
    if tail:
        left, right = left[: len(left) - tail], right[: len(right) - tail]
    head = _common_prefix(left, right)
    shared_head = left[:head]
    left, right = left[head:], right[head:]
    doubled = bool(shared_head or shared_tail)

    candidates: list[Scope] = []
    for take_left in range(1, len(left) + 1):
        for take_right in range(1, len(right) + 1):
            prefix = left[: len(left) - take_left]
            suffix = right[take_right:]
            alt_left = left[len(left) - take_left :]
            alt_right = right[:take_right]
            first = shared_head + prefix + alt_left + suffix + shared_tail
            second = shared_head + prefix + alt_right + suffix + shared_tail
            if first == second:
                continue
            if _repeats_a_token(first) or _repeats_a_token(second):
                continue
            candidates.append(
                Scope(
                    options=[" ".join(first), " ".join(second)],
                    prefix=" ".join(shared_head + prefix),
                    suffix=" ".join(suffix + shared_tail),
                    alternants=[" ".join(alt_left), " ".join(alt_right)],
                    evidence=(
                        "shared prefix/suffix, some of it printed on both sides"
                        if doubled
                        else "shared prefix/suffix"
                    ),
                    confidence="medium",
                )
            )
    if not candidates:
        return Scope(
            options=[" ".join(shared_head + left + shared_tail),
                     " ".join(shared_head + right + shared_tail)],
            alternants=[" ".join(left), " ".join(right)],
            evidence="no sub-sentential split gives distinct readings",
            confidence="low",
        )
    candidates.sort(
        key=lambda scope: (
            abs(
                len(tokens(scope.alternants[0]))
                - len(tokens(scope.alternants[1]))
            ),
            sum(len(tokens(alt)) for alt in scope.alternants),
        )
    )
    best = candidates[0]
    best.rejected = [
        [option + closing for option in c.options] for c in candidates[1:6]
    ]
    return _closed(best, closing)


def resolve_scope(
    raw: str,
    morphemes: Sequence[Sequence[str]] | None = None,
    translation: str | None = None,
) -> Scope:
    """Propose the readings of ``raw``, best available evidence first."""
    if morphemes:
        scope = _morpheme_scope(raw, morphemes)
        if scope is not None:
            return scope
    scope = _affix_scope(raw)
    if translation and SLASH in translation:
        expected = translation.count(SLASH) + 1
        if expected == len(scope.options):
            scope.evidence += "; translation slash count agrees"
            if scope.confidence == "medium":
                scope.confidence = "high"
        else:
            scope.evidence += (
                f"; translation implies {expected} readings, not {len(scope.options)}"
            )
            scope.confidence = "low"
    return scope


# --------------------------------------------------------------------------
# audit


def audit(
    raw: str, options: Sequence[str], translation: str | None = None
) -> list[Finding]:
    """Check a resolution of ``raw`` into ``options``. Findings, not fixes."""
    findings: list[Finding] = []
    if len(options) < 2:
        findings.append(
            Finding("SA001", "HARD", "fewer than two readings for a slash source")
        )
        return findings
    unresolved = [option for option in options if SLASH in option]
    for option in unresolved:
        findings.append(
            Finding("SA002", "HARD", "a reading still contains a slash", option)
        )
    if len(set(options)) != len(options):
        findings.append(Finding("SA003", "HARD", "two readings are identical"))

    # Every distinct token of the source has to survive into some reading.
    # Deliberately a set and not a multiset: the source prints shared material
    # once per side, so the counts legitimately differ from the readings'.
    union = set()
    for option in options:
        union |= set(_bag(option))
    source = {
        _bare(piece) for piece in tokens(raw.replace(SLASH, " ")) if _bare(piece)
    }
    lost = sorted(source - union) if not unresolved else []
    if lost:
        findings.append(
            Finding(
                "SA004",
                "HARD",
                "source material appears in no reading",
                " ".join(lost),
            )
        )

    # The shape of the readings tells you which check applies.
    bags = [_bag(option) for option in options]
    permutation = any(
        bags[i] == bags[j] for i in range(len(bags)) for j in range(i + 1, len(bags))
    )
    # A word-order variant that also gains or loses a particle -- `ruza
    # pia-biskaw` / `pia-biskaw sa ruza` -- legitimately differs in length, and
    # its signature is containment: every word of the shorter reading is in the
    # longer one. A substitution never has that, because its alternants differ.
    sets = [set(bag) for bag in bags]
    contained = any(
        sets[i] <= sets[j] or sets[j] <= sets[i]
        for i in range(len(sets))
        for j in range(i + 1, len(sets))
    )
    lengths = {len(tokens(option)) for option in options}
    if not permutation and not contained and len(lengths) > 1:
        shortest = min(options, key=lambda option: len(tokens(option)))
        longest = max(options, key=lambda option: len(tokens(option)))
        extra = sorted((_bag(longest) - _bag(shortest)).elements())
        findings.append(
            Finding(
                "SA005",
                "SOFT",
                "a lexical substitution whose readings differ in length: shared "
                "material may have been given to only one of them",
                f"only in one reading: {' '.join(extra)}" if extra else "",
            )
        )

    if translation:
        if SLASH in translation:
            findings.append(
                Finding(
                    "SA006",
                    "SOFT",
                    "the readings share one translation that still contains a "
                    "slash; each reading needs its own (POL-026/POL-027)",
                    translation.strip()[:80],
                )
            )
        elif translation.count(SLASH) + 1 not in (1, len(options)):
            findings.append(
                Finding("SA007", "SOFT", "translation slash count disagrees")
            )
    return findings


# --------------------------------------------------------------------------
# CLI


def _audit_curation(path: str, records: str | None) -> list[tuple[str, Finding]]:
    """Audit a {record_id: [options]} curation file against its source records."""
    curation = json.loads(open(path, encoding="utf-8").read())
    sources: dict[str, dict] = {}
    if records:
        data = json.loads(open(records, encoding="utf-8").read())
        for key in ("dictionary_examples", "records", "examples"):
            for record in data.get(key, []):
                sources[str(record["id"])] = record
    out = []
    for record_id, options in curation.items():
        record = sources.get(record_id, {})
        raw = str(record.get("source", " / ".join(options)))
        translation = record.get("translation")
        for finding in audit(raw, options, translation):
            out.append((record_id, finding))
    return out


def _audit_xml(path: str) -> list[tuple[str, Finding]]:
    """Report any published FORM that still carries an unresolved slash."""
    out = []
    pattern = os.path.join(path, "**", "*.xml")
    for filename in sorted(glob.glob(pattern, recursive=True)):
        try:
            root = ET.parse(filename).getroot()
        except ET.ParseError:
            continue
        for sentence in root.iter("S"):
            for form in sentence.findall("FORM"):
                if SLASH in (form.text or ""):
                    out.append(
                        (
                            sentence.get("id", "?"),
                            Finding(
                                "SA002",
                                "HARD",
                                "unresolved slash in a published FORM",
                                (form.text or "").strip()[:80],
                            ),
                        )
                    )
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    resolve = sub.add_parser("resolve", help="propose readings for one source string")
    resolve.add_argument("source")
    resolve.add_argument("--translation")

    curation = sub.add_parser("audit-curation", help="audit a curation JSON file")
    curation.add_argument("path")
    curation.add_argument("--records", help="the extraction the ids come from")

    published = sub.add_parser("audit-xml", help="find unresolved slashes in XML")
    published.add_argument("path")

    args = parser.parse_args(argv)
    if args.command == "resolve":
        scope = resolve_scope(args.source, translation=args.translation)
        print(f"evidence  : {scope.evidence}")
        print(f"confidence: {scope.confidence}")
        if scope.prefix:
            print(f"shared before: {scope.prefix}")
        if scope.suffix:
            print(f"shared after : {scope.suffix}")
        for option in scope.options:
            print(f"  reading: {option}")
        for other in scope.rejected:
            print(f"  also possible: {' || '.join(other)}")
        return 0

    findings = (
        _audit_curation(args.path, args.records)
        if args.command == "audit-curation"
        else _audit_xml(args.path)
    )
    for record_id, finding in findings:
        print(f"{record_id}\t{finding}")
    hard = sum(1 for _, finding in findings if finding.severity == "HARD")
    print(
        f"\n{len(findings)} findings ({hard} HARD) over "
        f"{args.path}",
        file=sys.stderr,
    )
    return 1 if hard else 0


if __name__ == "__main__":
    raise SystemExit(main())
