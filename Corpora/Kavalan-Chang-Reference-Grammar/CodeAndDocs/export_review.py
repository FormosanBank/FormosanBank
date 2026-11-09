#!/usr/bin/env python3
"""Export every included source unit as the baseline for the student review page.

    python CodeAndDocs/export_review.py     # -> review_baseline.json + review_page.html
    ...review_page.html is published as a claude.ai artifact; the student works there...
    python CodeAndDocs/apply_review.py <downloaded.json | dumped edits/ directory>
                                            # -> review_corrections.tsv + review_log.tsv
    CodeAndDocs/generate_xml.sh             # publishes them

One card per printed example (source unit): the Kavalan words in one row, the gloss
under each word, then the Chinese free translation. An example the book prints
more than once is one card per printing, because each printing is checked
against its own page; the build publishes them as one sentence and requires
their words to agree.

The words and glosses shown are exactly what the build aligns and publishes
(build_xml.review_words / review_glosses), including the eight units whose
glosses are written out in WORD_GLOSS_OVERRIDES. A review correction replaces
those. The baseline is the transcription alone, so the export refuses to run
while review_corrections.tsv holds corrections.

Triage flags (hints, not verdicts):
  count        a segmented word whose gloss has a different number of parts, so
               it publishes without a morpheme tier
  unbalanced   an unmatched bracket in a word or gloss
  substring    a one-character gloss that is part of the gloss this word usually
               gets -- a two-character word split across two words
  adjacent     two neighbouring glosses that join into a gloss used elsewhere
  empty_gloss  a word with no gloss
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import build_xml

ROOT = build_xml.ROOT
OUT = ROOT / "CodeAndDocs" / "review_baseline.json"
PAGE_TEMPLATE = ROOT / "CodeAndDocs" / "review_page.template.html"
PAGE = ROOT / "CodeAndDocs" / "review_page.html"
FORMAT = "chang-kavalan-review/1"


def unbalanced(value: str) -> bool:
    return any(value.count(a) != value.count(b) for a, b in ("()", "（）", "[]"))


def record_hash(record: dict) -> str:
    shown = [record["words"], record["glosses"], record["translation"]]
    blob = json.dumps(shown, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    if build_xml.load_review_corrections():
        raise SystemExit(f"{build_xml.REVIEW_CORRECTIONS} holds corrections; the review "
                         "baseline is the transcription alone. Move it aside to re-export.")
    units = build_xml.load_source_units(corrections={})
    decisions = build_xml.load_variant_decisions(units)
    groups = build_xml.group_source_units(units)
    group_of = {unit.unit_id: group for group in groups for unit in group}
    pinned = {uid for uid, _ in build_xml.MORPHEME_OVERRIDES}

    records = []
    for unit in units:
        if unit.decision != "include":
            continue
        group = group_of[unit.unit_id]
        sid = build_xml.sentence_id(group[0])
        variants = len(build_xml.accepted_variants(group, decisions))
        words = build_xml.review_words(unit)
        glosses = build_xml.review_glosses(unit)
        aligned = build_xml.normalize_surface_form(unit).split()
        segmented = [
            bool(re.search(r"[-=]", form)) and bool(gloss)
            and not build_xml.split_morphemes(unit, index, form, gloss)
            for index, (form, gloss) in enumerate(zip(aligned, glosses), start=1)
        ]
        record = {
            "record": unit.unit_id,
            "label": unit.printed_label,
            "locator": f"book p. {unit.book_page} (PDF p. {unit.pdf_page}, {unit.side} half), "
                       f"example {unit.printed_label}",
            "published_as": [sid] + [f"{sid}-alt{n:02d}" for n in range(1, variants + 1)],
            "repeats": [u.unit_id for u in group if u.unit_id != unit.unit_id],
            "words": words,
            "glosses": glosses,
            "translation": unit.translation_zho,
            "also_printed": [a for a in build_xml.split_alternates(unit.alternate_forms)]
                            + [a for a in build_xml.split_alternates(unit.alternate_translations_zho)],
            "glosses_locked": unit.gloss_alignment == "unavailable",
            "morphemes_pinned": unit.unit_id in pinned,
            "bracket_words": words != unit.form.split(),
            "count_columns": [i + 1 for i, bad in enumerate(segmented) if bad],
        }
        record["hash"] = record_hash(record)
        records.append(record)

    usual: dict[str, Counter] = defaultdict(Counter)
    vocabulary: set[str] = set()
    for record in records:
        for form, gloss in zip(record["words"], record["glosses"]):
            usual[form.strip(".,;:!?\"")][gloss] += 1
            if gloss:
                vocabulary.add(gloss)
    for record in records:
        pairs = list(zip(record["words"], record["glosses"]))
        flags = []
        if record["count_columns"]:
            flags.append("count")
        if any(unbalanced(v) for pair in pairs for v in pair):
            flags.append("unbalanced")
        for form, gloss in pairs:
            common = usual[form.strip(".,;:!?\"")].most_common(1)
            if common and gloss != common[0][0] and len(gloss) == 1 and gloss in common[0][0]:
                flags.append("substring")
        for (_, left), (_, right) in zip(pairs, pairs[1:]):
            if left and right and min(len(left), len(right)) <= 2 and left + right in vocabulary:
                flags.append("adjacent")
        if not record["glosses_locked"] and any(not g for _, g in pairs):
            flags.append("empty_gloss")
        record["flags"] = sorted(set(flags))

    payload = {"format": FORMAT, "records": records}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    template = PAGE_TEMPLATE.read_text(encoding="utf-8")
    placeholder = "/*__BASELINE__*/"
    if template.count(placeholder) != 1:
        raise SystemExit(f"{PAGE_TEMPLATE} must contain {placeholder} exactly once")
    # Inside <script type="application/json">, only "</" can end the block early.
    embedded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    PAGE.write_text(template.replace(placeholder, embedded), encoding="utf-8")
    counts = Counter(f for r in records for f in r["flags"])
    print(f"Wrote {OUT}: {len(records)} printed examples, "
          f"{sum(1 for r in records if r['flags'])} flagged {dict(counts)}")
    print(f"Wrote {PAGE}")


if __name__ == "__main__":
    main()
