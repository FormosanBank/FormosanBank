#!/usr/bin/env python3
"""Turn a student's review into the corrections overlay the build applies.

    python CodeAndDocs/apply_review.py reviewed.json     # a downloaded file
    python CodeAndDocs/apply_review.py dump/edits/       # the page's server store

`reviewed.json` is what the review page's "Download corrections" button saves. A
directory is the page's server-side `edits` collection dumped one document per
file (`<unit_id>.json`, the document body alone), as Claude's ArtifactData `list`
with `out_dir` writes it. Either way each edit is
`{base, words, glosses, translation, note, reviewed, updatedAt}`.

Writes two files, keyed on source unit ids:

  review_corrections.tsv  one row per changed field -- `words` or `glosses` (JSON
                          arrays) or `translation` -- with `was` and `now`.
                          build_xml.py applies it; a `was` that no longer matches
                          fails the build as a stale review.
  review_log.tsv          one row per unit the student touched: reviewed or not,
                          what changed, and their note. Notes on unchanged units
                          are questions for the maintainer.

Edits made against a different baseline (their `base` hash differs) are refused.
After writing, the whole corpus is built in memory with the corrections, so a
conflict -- two printings of one example that no longer agree, a word whose
morphemes are written out by hand -- is reported now rather than at rebuild.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import build_xml

ROOT = build_xml.ROOT
BASELINE = ROOT / "CodeAndDocs" / "review_baseline.json"
CORRECTIONS = build_xml.REVIEW_CORRECTIONS
LOG = ROOT / "CodeAndDocs" / "review_log.tsv"
FORMAT = "chang-kavalan-review/1"


def dumps(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def tokens(unit_id: str, field: str, values: list) -> list[str]:
    out = [str(v).strip() for v in values]
    for value in out:
        if any(ch.isspace() for ch in value):
            raise SystemExit(f"{unit_id} {field}: {value!r} contains a space; one per box")
    if field == "words" and "" in out:
        raise SystemExit(f"{unit_id}: an empty word box remains; delete it or fill it in")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reviewed", type=Path,
                        help="a downloaded review file, or a directory of dumped store documents")
    args = parser.parse_args()

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    if args.reviewed.is_dir():
        reviewed = {"format": FORMAT, "edits": {
            path.stem: json.loads(path.read_text(encoding="utf-8"))
            for path in sorted(args.reviewed.glob("*.json"))
        }}
        if not reviewed["edits"]:
            raise SystemExit(f"No <unit_id>.json documents in {args.reviewed}")
    else:
        reviewed = json.loads(args.reviewed.read_text(encoding="utf-8"))
    for name, payload in (("baseline", baseline), ("reviewed file", reviewed)):
        if payload.get("format") != FORMAT:
            raise SystemExit(f"The {name} is not {FORMAT}: {payload.get('format')!r}")
    base = {record["record"]: record for record in baseline["records"]}
    unknown = sorted(set(reviewed["edits"]) - set(base))
    if unknown:
        raise SystemExit(f"{len(unknown)} reviewed units are not in the baseline: {unknown[:5]}")

    changes, log = [], []
    for unit_id in sorted(reviewed["edits"]):
        edit, record = reviewed["edits"][unit_id], base[unit_id]
        if edit.get("base") != record["hash"]:
            raise SystemExit(f"{unit_id} was reviewed against a different baseline "
                             f"({edit.get('base')!r}, now {record['hash']!r}). Refusing to guess.")
        words = tokens(unit_id, "words", edit.get("words", record["words"]))
        glosses = tokens(unit_id, "glosses", edit.get("glosses", record["glosses"]))
        if len(words) != len(glosses):
            raise SystemExit(f"{unit_id}: {len(words)} words but {len(glosses)} glosses")
        translation = str(edit.get("translation", record["translation"])).strip()
        note = str(edit.get("note", "")).strip()
        changed = []
        for field, was, now in (
            ("words", dumps(record["words"]), dumps(words)),
            ("glosses", dumps(record["glosses"]), dumps(glosses)),
            ("translation", record["translation"], translation),
        ):
            if was != now:
                changed.append(field)
                changes.append({"unit_id": unit_id, "field": field, "was": was, "now": now,
                                "reviewer_note": note})
        log.append({"unit_id": unit_id, "reviewed": "yes" if edit.get("reviewed") else "no",
                    "changed": ",".join(changed), "note": note})

    with CORRECTIONS.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, ["unit_id", "field", "was", "now", "reviewer_note"],
                                delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(changes)
    with LOG.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, ["unit_id", "reviewed", "changed", "note"],
                                delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(log)

    reviewed_count = sum(1 for row in log if row["reviewed"] == "yes")
    questions = [row for row in log if row["note"] and not row["changed"]]
    print(f"Wrote {CORRECTIONS}: {len(changes)} changed fields across "
          f"{len({c['unit_id'] for c in changes})} units")
    print(f"Wrote {LOG}: {len(log)} units touched, {reviewed_count} marked reviewed "
          f"(of {len(base)}), {len(questions)} notes without a change")
    for change in changes[:20]:
        print(f"  {change['unit_id']} {change['field']}: {change['was']} -> {change['now']}")
    if len(changes) > 20:
        print(f"  ... and {len(changes) - 20} more")

    try:
        build_xml.build_tree(build_xml.load_source_units())
    except (ValueError, IndexError) as error:
        hint = (" The example is printed more than once; make the same change on every "
                "printing's card." if "non-equivalent" in str(error) else "")
        raise SystemExit(f"\nThe corrections were written, but the corpus does not build "
                         f"with them:\n  {error}\n{hint}\nResolve this, then re-run.")
    if changes:
        print("\nThe corpus builds with these corrections. Publish them: CodeAndDocs/generate_xml.sh")


if __name__ == "__main__":
    main()
