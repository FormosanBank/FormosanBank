#!/usr/bin/env python3
"""Turn a student's review into the corrections overlay the build applies.

    python CodeAndDocs/apply_review.py reviewed.json     # a downloaded file
    python CodeAndDocs/apply_review.py dump/edits/       # the page's server store

`reviewed.json` is what the review page's "Download corrections" button saves.
A directory is the page's server-side `edits` collection dumped one document per
file (`<record>.json`, the document body alone), as Claude's ArtifactData
`list` with `out_dir` writes it. Either way the content is:

    {"format": "chang-seediq-review/1",
     "edits": {"R312": {"base": "<hash>", "words": [...], "glosses": [...],
                        "translation": "...", "note": "...", "reviewed": true}}}

Writes two files, both keyed on source record ids (stable; sentence ids are not):

  review_corrections.tsv  one row per changed field -- `words`, `glosses` or
                          `translation` -- with `was` and `now`. build_xml.py
                          applies it over the inventories; a `was` that no longer
                          matches fails the build as a stale review.
  review_log.tsv          one row per record the student touched: whether they
                          marked it reviewed, what changed, and their note. Notes
                          on unchanged records are questions for the maintainer.

The comparison is against `review_baseline.json`, the file the page was built
from. An edit made against a different baseline (its `base` hash differs) is
refused rather than guessed at. Re-running with the same file is a no-op.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "CodeAndDocs" / "review_baseline.json"
CORRECTIONS = ROOT / "CodeAndDocs" / "review_corrections.tsv"
LOG = ROOT / "CodeAndDocs" / "review_log.tsv"
FORMAT = "chang-seediq-review/1"
NULL = "∅"


def clean_tokens(record_id: str, field: str, tokens: list) -> list[str]:
    out = []
    for token in tokens:
        token = str(token).strip()
        if any(ch.isspace() for ch in token):
            raise SystemExit(f"{record_id} {field}: {token!r} contains a space; "
                             "one word per box")
        out.append(token)
    return out


ADJUDICATION = ROOT / "CodeAndDocs" / "review_adjudication.tsv"


def load_adjudication() -> dict[str, dict[str, tuple[str, str, str]]]:
    """The maintainer's rulings on individual review edits: record -> field ->
    (action, value, reason). `keep` restores the baseline value of a field,
    `set` replaces the reviewer's value (words/glosses as a JSON array), and
    `supersede` (field `all`) skips the record because the build now does the
    same thing structurally. Kept in a committed table so every departure from
    what the reviewer typed is visible and reasoned."""
    if not ADJUDICATION.exists():
        return {}
    out: dict[str, dict[str, tuple[str, str, str]]] = {}
    with ADJUDICATION.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            if row["action"] not in {"keep", "set", "supersede"}:
                raise SystemExit(f"Unknown adjudication action {row['action']!r}")
            out.setdefault(row["record_id"], {})[row["field"]] = (
                row["action"], row["value"], row["reason"])
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reviewed", type=Path, help="a downloaded review file, or a directory of dumped store documents")
    args = parser.parse_args()

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if args.reviewed.is_dir():
        reviewed = {"format": FORMAT, "edits": {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(args.reviewed.glob("*.json"))
        }}
        if not reviewed["edits"]:
            raise SystemExit(f"No <record>.json documents in {args.reviewed}")
    else:
        reviewed = json.loads(args.reviewed.read_text(encoding="utf-8"))
    for name, payload in (("baseline", baseline), ("reviewed file", reviewed)):
        if payload.get("format") != FORMAT:
            raise SystemExit(f"The {name} is not {FORMAT}: {payload.get('format')!r}")
    base = {record["record"]: record for record in baseline["records"]}

    unknown = sorted(set(reviewed["edits"]) - set(base))
    if unknown:
        raise SystemExit(f"{len(unknown)} reviewed records are not in the baseline: "
                         f"{unknown[:5]}")

    rulings = load_adjudication()
    stale = sorted(set(rulings) - set(reviewed["edits"]))
    if stale:
        raise SystemExit(f"Adjudications for records the reviewer did not edit: {stale}")
    changes, log = [], []
    for record_id in sorted(reviewed["edits"]):
        edit, record = reviewed["edits"][record_id], base[record_id]
        if edit.get("base") != record["hash"]:
            raise SystemExit(
                f"{record_id} was reviewed against a different baseline "
                f"({edit.get('base')!r}, now {record['hash']!r}). Refusing to guess."
            )
        edit = dict(edit)
        ruled = rulings.get(record_id, {})
        if "all" in ruled:
            action, _, reason = ruled["all"]
            if action != "supersede":
                raise SystemExit(f"{record_id}: field 'all' only takes 'supersede'")
            log.append({"record_id": record_id,
                        "reviewed": "yes" if edit.get("reviewed") else "no",
                        "changed": f"superseded: {reason}",
                        "note": str(edit.get("note", "")).strip()})
            continue
        for field, (action, value, reason) in ruled.items():
            if field not in {"words", "glosses", "translation"} or action == "supersede":
                raise SystemExit(f"{record_id}: bad adjudication {field}/{action}")
            if action == "keep":
                edit[field] = record[field]
            else:
                edit[field] = json.loads(value) if field != "translation" else value
        words = clean_tokens(record_id, "words", edit.get("words", record["words"]))
        glosses = clean_tokens(record_id, "glosses",
                               edit.get("glosses", record["glosses"]))
        # An empty box is an unfinished edit, not a deliberate blank: the corpus
        # writes a missing gloss as ∅, so a dropped box would shift the row.
        if not words:
            # An emptied card is ignored: the record stays as it was and nothing
            # empty is published. Removing a record is an inventory decision.
            print(f"WARNING {record_id}: the reviewer emptied this card; ignored, "
                  "the record is unchanged. Remove it in the inventory if intended.")
            log.append({"record_id": record_id,
                        "reviewed": "yes" if edit.get("reviewed") else "no",
                        "changed": "ignored: card emptied",
                        "note": str(edit.get("note", "")).strip()})
            continue
        if "" in words or "" in glosses:
            raise SystemExit(f"{record_id}: an empty box remains (words {words}, "
                             f"glosses {glosses}); delete it or write {NULL}")
        if len(words) != len(glosses):
            raise SystemExit(f"{record_id}: {len(words)} words but {len(glosses)} "
                             "glosses")
        translation = str(edit.get("translation", record["translation"])).strip()
        note = str(edit.get("note", "")).strip()

        changed = []
        for field, was, now in (
            ("words", " ".join(record["words"]), " ".join(words)),
            ("glosses", " ".join(record["glosses"]), " ".join(glosses)),
            ("translation", record["translation"], translation),
        ):
            if was != now:
                changed.append(field)
                changes.append({"record_id": record_id, "field": field,
                                "was": was, "now": now, "reviewer_note": note})
        if "translation" in changed and record["translation_fixed_in_build"]:
            print(f"NOTE {record_id}: translation changed, but this record's "
                  "translations are written out in build_xml.translations_for(); "
                  "the build will refuse it until that table is edited by hand.")
        log.append({"record_id": record_id,
                    "reviewed": "yes" if edit.get("reviewed") else "no",
                    "changed": ",".join(changed), "note": note})

    with CORRECTIONS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, ["record_id", "field", "was", "now",
                                         "reviewer_note"],
                                delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(changes)
    with LOG.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, ["record_id", "reviewed", "changed", "note"],
                                delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(log)

    reviewed_count = sum(1 for row in log if row["reviewed"] == "yes")
    questions = [row for row in log if row["note"] and not row["changed"]]
    print(f"Wrote {CORRECTIONS}: {len(changes)} changed fields across "
          f"{len({c['record_id'] for c in changes})} records")
    print(f"Wrote {LOG}: {len(log)} records touched, {reviewed_count} marked "
          f"reviewed (of {len(base)}), {len(questions)} notes without a change")
    for change in changes[:20]:
        print(f"  {change['record_id']} {change['field']}: "
              f"{change['was']!r} -> {change['now']!r}")
    if len(changes) > 20:
        print(f"  ... and {len(changes) - 20} more")
    if changes:
        print("\nRebuild to publish them: CodeAndDocs/generate_xml.sh")


if __name__ == "__main__":
    sys.exit(main())
