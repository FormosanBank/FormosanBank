#!/usr/bin/env python3
"""List sentences of old corpus documentation that a rewritten README no longer contains.

    python docs/tools/check_readme_coverage.py <new README> <old text file> [<old text file> ...]

Used when each corpus's README and GitBook page were merged into one README
(2026-10): nothing either source said may be lost. A sentence counts as
present when its letters and digits appear, in order, in the new README
(case, spacing, punctuation and Markdown markup are ignored), so moving a
sentence or re-punctuating it is fine; rewording it is flagged for a person to
check. Prints one flagged sentence per line; exits 1 if any.

Parts of the old GitBook page that the new layout replaces by design are not
checked, and are listed separately: the generated statistics block, the
"Access Details" link to the repository, and the Terms-of-Use citation
boilerplate (the README's "How to cite" section carries the citation).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

STATS_BLOCK = re.compile(r"<!-- CORPUS STATS START -->.*?<!-- CORPUS STATS END -->", re.S)
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
LINK = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")
SENTENCE_END = re.compile(r"(?<=[.!?;:])\s+")
ABBREVIATION = re.compile(r"\b(?:pp|p|e\.g|i\.e|cf|vs|al|no|vol|ed|eds|ca|fig|[A-Z])\.(?=\s)", re.I)
# Section headings the 2026-10 layout renames or merges (POL-044/052/055 as
# amended); their content is checked, the heading words are not.
OLD_SECTION_HEADING = re.compile(
    r"(?i)^#+\s*\**\s*(?:corpus statistics|corpus processing|copyright|citation|"
    r"notes(?: and issues)?|corpus notes|minor notes|access details|rights|reproduction|"
    r"validation|audio|publication packaging|source(?: and [a-z ]+)?|license|"
    r"how to cite|notes and caveats|languages and dialects|statistics)\s*\**\s*$"
)
REPLACED_BY_DESIGN = (
    OLD_SECTION_HEADING,
    re.compile(r"(?is)^#+\s*\**access details\**.*"),
    re.compile(r"(?i)the repo containing this corpus in formosanbank"),
    re.compile(r"(?i)in accordance with (?:our|the) \[?terms of use"),
)


def normalize(text: str) -> str:
    """Letters and digits only, casefolded."""
    return "".join(ch for ch in text.casefold() if ch.isalnum())


def plain(markdown: str) -> str:
    text = FRONT_MATTER.sub("", markdown)
    text = STATS_BLOCK.sub("", text)
    text = LINK.sub(lambda m: m.group(1), text)
    return HTML_TAG.sub(" ", text)


def sentences(markdown: str) -> list[str]:
    """Sentences, list items, headings, table rows and code lines of a document."""
    units: list[str] = []
    for block in re.split(r"\n\s*\n", plain(markdown)):
        lines = block.splitlines()
        if any(line.lstrip().startswith(("*", "-", "|", "#", "```", "    ")) for line in lines) or (
            lines and re.match(r"^\s*\d+[.)]\s", lines[0])
        ):
            pieces = lines  # structured block: one unit per line
        else:
            joined = ABBREVIATION.sub(lambda m: m.group(0)[:-1] + "\x01", " ".join(line.strip() for line in lines))
            pieces = [piece.replace("\x01", ".") for piece in SENTENCE_END.split(joined)]
        for piece in pieces:
            piece = piece.strip().strip("*").strip()
            if piece.startswith("```") or set(piece) <= set("|-: "):
                continue
            if len(normalize(piece)) >= 4:
                units.append(piece)
    return units


def replaced_by_design(sentence: str) -> bool:
    return any(pattern.search(sentence) for pattern in REPLACED_BY_DESIGN)


def uncovered(old_texts: list[str], new_text: str) -> tuple[list[str], list[str]]:
    """(flagged sentences, sentences skipped as replaced by design)."""
    target = normalize(plain(new_text))
    flagged: list[str] = []
    skipped: list[str] = []
    seen: set[str] = set()
    for old in old_texts:
        for sentence in sentences(old):
            key = normalize(sentence)
            if key in seen:
                continue
            seen.add(key)
            if replaced_by_design(sentence):
                skipped.append(sentence)
            elif key not in target:
                flagged.append(sentence)
    return flagged, skipped


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__.splitlines()[2].strip(), file=sys.stderr)
        return 2
    new = Path(argv[0]).read_text(encoding="utf-8")
    olds = [Path(p).read_text(encoding="utf-8") for p in argv[1:]]
    flagged, skipped = uncovered(olds, new)
    for sentence in skipped:
        print(f"SKIPPED (replaced by design): {sentence}")
    for sentence in flagged:
        print(f"MISSING: {sentence}")
    print(f"{len(flagged)} missing, {len(skipped)} skipped by design", file=sys.stderr)
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
