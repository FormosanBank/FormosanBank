#!/usr/bin/env python3
"""Export every source record as the baseline for the student review page.

    python CodeAndDocs/export_review.py      # -> review_baseline.json + review_page.html
    ...review_page.html is published as a web page; the student works there...
    python CodeAndDocs/apply_review.py <reviewed.json>   # -> review_corrections.tsv
    FORMOSANBANK_PATH=... CodeAndDocs/generate_xml.sh    # publishes them

The review covers everything a transcription pass can get wrong: the Seediq
words, their glosses, and the free translation. One entry per **source record**,
not per published sentence. A record with optional material or a slash
alternation expands into two or four sentences that all share one word list, so
reviewing sentences would show the same material several times and invite
inconsistent corrections -- and the word positions differ between the variants,
because an optional `(ka)` shifts everything after it.

So a few cells carry the source's own notation rather than a finished word:
`(ka)` for optional material, `laqi/heya` for an alternation, `{laqi` /
`gaga/temi}` for an alternation whose scope spans words, and ` = ` in a
translation separating the source's alternative renderings. The reviewer keeps
that notation; the build expands it.

Each record carries triage `flags`, hints for a reviewer with limited time, not
verdicts:

  latin_gloss   a gloss in Latin script that is not a known proper name -- the
                signature of a gloss column shifted by one (`ka` glossed `w`,
                `walis` glossed `alis`)
  unbalanced    a gloss with an unmatched ( ) （ ）, a bracket that drifted in
                from a neighbour's gloss
  substring     a rare gloss that is a substring of the gloss the same word
                usually gets -- a two-character Chinese word split across two
                Seediq words (老人 over `naq rudan`)
  adjacent      two neighbouring glosses that join into a word the corpus uses
                elsewhere -- 然 + 後 over `bobo na`, w + alis over `ka walis`
  count         the gloss claims a different number of morphemes than the word

`translation_fixed_in_build` marks the records whose published translations are
written out by hand in build_xml.translations_for(), not taken from the
inventory. A translation correction there cannot be applied mechanically; the
build refuses one, and the page tells the reviewer to use the note instead.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CodeAndDocs"))
from build_xml import HAND_WRITTEN_TRANSLATIONS  # noqa: E402

ACCEPTED = ROOT / "CodeAndDocs" / "extracted_examples.tsv"
INVENTORY = ROOT / "CodeAndDocs" / "source_inventory.tsv"
CHAPTER5 = ROOT / "CodeAndDocs" / "chapter5_inventory.tsv"
DEDUP = ROOT / "CodeAndDocs" / "deduplicated_variants.tsv"
OUT = ROOT / "CodeAndDocs" / "review_baseline.json"
# The student works in a web page built from this same baseline, so the page can
# never show different text from what apply_review.py compares against.
PAGE_TEMPLATE = ROOT / "CodeAndDocs" / "review_page.template.html"
PAGE = ROOT / "CodeAndDocs" / "review_page.html"
FORMAT = "chang-seediq-review/1"

NULL = "∅"
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
LATIN = re.compile(r"[A-Za-z]")
# Names the source itself glosses as themselves, plus the Leipzig-style codes.
KNOWN_LATIN = {
    "pawan", "walis", "temi", "awe", "buni", "awi", "tone", "udun", "paras",
    "baso", "KA", NULL,
}


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def morphemes_claimed(text: str) -> int:
    infixes = len(re.findall(r"<[^>]+>", text or ""))
    rest = re.sub(r"<[^>]+>", "", text or "")
    return len([p for p in re.split(r"[-=]", rest) if p.strip()]) + infixes


def record_hash(record: dict) -> str:
    """Fingerprint of what the reviewer was shown, to refuse stale reviews."""
    shown = [record["words"], record["glosses"], record["translation"]]
    blob = json.dumps(shown, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def load_records() -> list[dict]:
    # Which published sentences each record became: context for the reviewer.
    published: dict[str, list[str]] = defaultdict(list)
    for row in read_tsv(ACCEPTED):
        published[row["source_id"]].append(row["s_id"])

    # Chapter 5 is its own file, numbered in narrative order by build_long_texts.
    chapter5 = [row for row in read_tsv(CHAPTER5) if row["decision"] == "include"]
    for row in chapter5:
        published[row["record_id"]].append(f"long-texts {row['record_id']}")

    # A record every one of whose readings was merged into another record's is
    # not published at all; the page tells the reviewer to skip it.
    merged_into = {row["dropped_source_id"]: row["merged_into_source_id"]
                   for row in read_tsv(DEDUP)}

    records = []
    for path, chapter in ((INVENTORY, "3-4"), (CHAPTER5, "5")):
        for row in read_tsv(path):
            if row["decision"] != "include":
                continue
            pairs = json.loads(row["word_gloss_json"])
            record = {
                "record": row["record_id"],
                "chapter": chapter,
                "locator": row["source_locator"],
                "published_as": published.get(row["record_id"], []),
                "merged_into": "" if row["record_id"] in published
                               else merged_into.get(row["record_id"], ""),
                "words": [word for word, _ in pairs],
                "glosses": [gloss for _, gloss in pairs],
                "translation": row["translation"],
                "translation_fixed_in_build":
                    row["record_id"] in HAND_WRITTEN_TRANSLATIONS,
            }
            record["hash"] = record_hash(record)
            records.append(record)
    return records


def flag(records: list[dict]) -> None:
    # A word's usual gloss, for the substring test.
    usual: dict[str, Counter] = defaultdict(Counter)
    # Every gloss the corpus uses anywhere, for the adjacent-split test.
    vocabulary: set[str] = set()
    for record in records:
        for form, gloss in zip(record["words"], record["glosses"]):
            usual[form.strip(".,;:!?\"")][gloss] += 1
            if gloss:
                vocabulary.add(gloss)

    for record in records:
        reasons = []
        pairs = list(zip(record["words"], record["glosses"]))
        for form, gloss in pairs:
            bare = form.strip(".,;:!?\"")
            if gloss and LATIN.search(gloss) and not HAN.search(gloss) \
                    and gloss not in KNOWN_LATIN:
                reasons.append("latin_gloss")
            if gloss.count("（") != gloss.count("）") or \
                    gloss.count("(") != gloss.count(")"):
                reasons.append("unbalanced")
            common = usual[bare].most_common(1)
            if common and gloss != common[0][0] and len(gloss) == 1 \
                    and gloss in common[0][0]:
                reasons.append("substring")
            if re.search(r"[-=<]", form) and \
                    morphemes_claimed(form) != morphemes_claimed(gloss):
                reasons.append("count")
        for (_, left), (_, right) in zip(pairs, pairs[1:]):
            if not left or not right or NULL in (left, right):
                continue
            if min(len(left), len(right)) > 2:
                continue
            if left + right in vocabulary:
                reasons.append("adjacent")
        record["flags"] = sorted(set(reasons))


def main() -> None:
    records = load_records()
    flag(records)
    payload = {"format": FORMAT, "records": records}
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    template = PAGE_TEMPLATE.read_text(encoding="utf-8")
    placeholder = "/*__BASELINE__*/"
    if template.count(placeholder) != 1:
        raise SystemExit(f"{PAGE_TEMPLATE} must contain {placeholder} exactly once")
    # Inside <script type="application/json">, only "</" can end the block early.
    embedded = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    PAGE.write_text(template.replace(placeholder, embedded), encoding="utf-8")
    flagged = sum(1 for r in records if r["flags"])
    fixed = sum(1 for r in records if r["translation_fixed_in_build"])
    print(f"Wrote {OUT}: {len(records)} source records, {flagged} flagged, "
          f"{fixed} with translations written out in build_xml.py")
    print(f"Wrote {PAGE}")


if __name__ == "__main__":
    main()
