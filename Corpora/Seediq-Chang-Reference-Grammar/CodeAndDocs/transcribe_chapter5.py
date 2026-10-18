#!/usr/bin/env python3
"""Transcription of chapter 5, 賽德克語的長篇語料 (printed pp. 151-159).

Chapter 5 is the book's only connected narrative: the `sumuladuc` 祭祀 ritual
account, narrated by 傅景賢 (walis wadan) and retold by 錢成鏡 (pawan torih).
Each sentence is printed as three lines -- Seediq, a word-by-word Chinese gloss
in [...] or {...}, and a free translation in '...'.

**Transcribed by reading the page images at 300 dpi, not the text layer.** The
scan's text layer is far more garbled here than in chapters 3-4 (`m “ usa
s叫m.圖umalu`, `A孔阻止風`, `祭把` for 祭祀) and, more dangerously, it collapses
the spacing that carries the gloss alignment -- which is exactly what produced
the shifted-gloss defects in chapters 3-4. Alignment below was read off the
printed column positions.

Unlike chapters 3-4, whose inventory came from an Apple Vision pass that is not
in this repository, this transcription **is** the source layer: the data is in
chapter5_transcription.tsv beside this file, so the chapter-5 chain reproduces
from a clean clone with no untracked input. The transcription was made by a
Claude session (commit cbcffea, 2026-09-11) and checked against the book in the
2026-10 student review.

Conventions, matching the rest of the corpus:
  - A word the source leaves unglossed takes ∅ (mostly the case marker `ka`).
  - Proper names gloss as themselves (`awi`, `tone`, `walis`, `buni`, `udun`,
    `paras`), which is what chapters 3-4 do with `pawan`/`walis`/`temi`/`awe`.
  - Footnote superscripts (15 on `sa-an-daha`, 16 on `pizu`) are not part of the
    word and do not appear in the FORM -- the V137-V139 leak this corpus is
    otherwise clean of.
  - Punctuation stays attached to its word, as in chapters 3-4.

One record per bracketed example (see bracketed_examples): where the book's
gloss bracket spans several printed blocks, they become one record and the
later blocks stay in the inventory as `merged_into_<record>` exclusions.

Idempotent. Run:  python CodeAndDocs/transcribe_chapter5.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "CodeAndDocs" / "chapter5_inventory.tsv"

PRINTED_TO_PDF = 16

# The transcription itself is data (POL-039): chapter5_transcription.tsv, one row
# per printed block, read off the page images at 300 dpi. `seediq` and `gloss`
# are the two printed lines, one gloss per word, so they split on spaces into
# aligned [word, gloss] pairs; ∅ marks a word the book leaves unglossed.
#
# `gloss_bracket` records the gloss brackets as printed. The book wraps each
# example's gloss in [ ... ], however many lines it runs to, so the brackets --
# not the translation lines -- say where one example ends (ruled 2026-10-14,
# option B): opens_and_closes, opens_only (prints "[" but no "]"), closes_only
# (prints "]" but no "["), or none (the title and section headings).
TRANSCRIPTION = ROOT / "CodeAndDocs" / "chapter5_transcription.tsv"


def load_transcription():
    blocks: list[tuple[str, int, list[list[str]], str, str]] = []
    brackets: dict[str, str] = {}
    with TRANSCRIPTION.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            words, glosses = row["seediq"].split(), row["gloss"].split()
            if len(words) != len(glosses):
                raise SystemExit(f"{row['record_id']}: {len(words)} words but "
                                 f"{len(glosses)} glosses")
            blocks.append((row["record_id"], int(row["printed_page"]),
                           [list(pair) for pair in zip(words, glosses)],
                           row["translation"], row["note"]))
            brackets[row["record_id"]] = row["gloss_bracket"]
    return blocks, brackets


BLOCKS, _BRACKETS = load_transcription()
GLOSS_UNCLOSED = {r for r, b in _BRACKETS.items() if b == "opens_only"}
GLOSS_UNOPENED = {r for r, b in _BRACKETS.items() if b == "closes_only"}
GLOSS_NONE = {r for r, b in _BRACKETS.items() if b == "none"}
if set(_BRACKETS.values()) - {"opens_and_closes", "opens_only", "closes_only", "none"}:
    raise SystemExit(f"Unknown gloss_bracket value in {TRANSCRIPTION.name}")
SENTENCE_FINAL = tuple(".!?。！？")


def bracketed_examples(blocks: list[tuple]) -> list[list[tuple]]:
    """Group consecutive blocks that share one gloss bracket.

    A block that opens a bracket while the previous block's bracket is still
    open is a printing slip one way or the other. Ruled 2026-10-15: if the
    previous block's Seediq ends with sentence-final punctuation, its "]" was
    dropped and the new "[" starts a new example; otherwise the new "[" is the
    slip and the block continues the open example. Blocks with no brackets at
    all (the title and the section headings) stand alone.
    """
    groups: list[list[tuple]] = []
    open_group: list[tuple] | None = None
    for block in blocks:
        record = block[0]
        if record in GLOSS_NONE:
            if open_group is not None:
                raise SystemExit(f"{record} has no gloss bracket inside an open one")
            groups.append([block])
            continue
        opens = record not in GLOSS_UNOPENED
        closes = record not in GLOSS_UNCLOSED
        if opens and open_group is not None:
            previous_form = " ".join(word for word, _ in open_group[-1][2])
            if previous_form.endswith(SENTENCE_FINAL):
                open_group = None          # infer the dropped "]"
        if open_group is None:
            if not opens:
                raise SystemExit(f"{record} closes a gloss bracket that is not open")
            open_group = []
            groups.append(open_group)
        open_group.append(block)
        if closes:
            open_group = None
    if open_group is not None:
        raise SystemExit("A chapter 5 gloss bracket is never closed")
    return groups


FIELDS = [
    "record_id", "pdf_page", "printed_page", "source_locator", "form", "gloss",
    "translation", "word_gloss_json", "decision", "exclusion_reason",
    "review_notes", "provenance",
]


def main() -> None:
    rows = []
    merged_into: dict[str, str] = {}
    examples = []
    for group in bracketed_examples(BLOCKS):
        first = group[0]
        if len(group) == 1:
            examples.append(first)
            continue
        for later in group[1:]:
            merged_into[later[0]] = first[0]
        note = "; ".join(filter(None, [b[4] for b in group] + [
            "one bracketed example printed over "
            + ", ".join(b[0] for b in group) + "; Seediq and translations joined"]))
        examples.append((first[0], first[1], [pair for b in group for pair in b[2]],
                         "".join(b[3] for b in group), note))
        examples.extend((b[0], b[1], b[2], b[3], b[4]) for b in group[1:])
    for record_id, printed, pairs, translation, note in examples:
        decision = "include" if translation else "exclude"
        reason = "" if translation else "missing_source_translation"
        if record_id in merged_into:
            decision, reason = "exclude", f"merged_into_{merged_into[record_id]}"
        rows.append({
            "record_id": record_id,
            "pdf_page": printed + PRINTED_TO_PDF,
            "printed_page": printed,
            "source_locator": (
                f"printed p. {printed} / PDF p. {printed + PRINTED_TO_PDF} / "
                "chapter 5 narrative"
            ),
            "form": " ".join(word for word, _ in pairs),
            "gloss": " ".join(gloss for _, gloss in pairs),
            "translation": translation,
            "word_gloss_json": json.dumps(pairs, ensure_ascii=False),
            "decision": decision,
            "exclusion_reason": reason,
            "review_notes": note,
            "provenance": "direct review of the 300 dpi page images",
        })

    ids = [row["record_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise SystemExit("Duplicate record ids in the chapter 5 transcription")
    for row in rows:
        if len(json.loads(row["word_gloss_json"])) != len(row["form"].split()):
            raise SystemExit(f"Word/gloss misalignment at {row['record_id']}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    included = sum(row["decision"] == "include" for row in rows)
    print(f"Wrote {OUT}: {len(rows)} blocks, {included} included, "
          f"{len(rows) - included} excluded")


if __name__ == "__main__":
    main()
