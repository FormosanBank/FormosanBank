#!/usr/bin/env python3
"""Turn a student's proofreading into a corrections table, ready for adjudication.

    python apply_review.py --repo ../Formosan-<Name> <downloaded.json | dumped edits/ directory>

The input is either the file the page's "Download corrections" button saves (what the
student emails), or the page's server-side `edits` collection dumped one document per
file (`<record>.json`, the body alone), as ArtifactData `list` with `out_dir` writes it.
Each edit is {base, sentence, words, glosses, translations, note, reviewed, updatedAt}.

Writes, next to the baseline in <repo>/review/:

  review_corrections.tsv  one row per changed field: record, file, field (sentence |
                          words | glosses | translation.N), what the XML has (`was`),
                          what the student typed (`now`), and the student's note.
                          words/glosses are JSON arrays.
  review_log.tsv          one row per record the student touched: reviewed or not,
                          which fields changed, the note, and any problem found here.

Nothing here edits XML. Which corrections are applied, and how, is decided with the
maintainer and then built by the dev repo's own pipeline (see SKILL.md, part 2).

Refused per record, and listed as problems (exit status 1 if there are any):
  - an edit made against a different baseline (its `base` hash differs);
  - a record id the baseline does not have;
  - a word row and gloss row of different lengths, or an empty word box.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


def dumps(value: list[str]) -> str:
    return json.dumps(value, ensure_ascii=False)


def clean(values) -> list[str]:
    return [" ".join(str(v).split()) for v in (values or [])]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("reviewed", type=Path, help="a downloaded review file, or a directory of dumped store documents")
    args = ap.parse_args()
    out_dir = args.repo.resolve() / "review"
    baseline = json.loads((out_dir / "review_baseline.json").read_text(encoding="utf-8"))
    fmt = baseline["format"]

    if args.reviewed.is_dir():
        edits = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted(args.reviewed.glob("*.json"))}
        if not edits:
            sys.exit(f"No <record>.json documents in {args.reviewed}")
    else:
        payload = json.loads(args.reviewed.read_text(encoding="utf-8"))
        if payload.get("format") != fmt:
            sys.exit(f"The reviewed file is {payload.get('format')!r}, but this baseline is {fmt!r}. Wrong corpus or an older page.")
        edits = payload.get("edits") or {}

    base = {r["record"]: r for r in baseline["records"]}
    changes, log, problems = [], [], []
    for rid in sorted(edits):
        edit, rec = edits[rid], base.get(rid)
        note = str(edit.get("note", "")).strip()
        if rec is None:
            problems.append(f"{rid}: not in the baseline")
            continue
        if edit.get("base") != rec["hash"]:
            problems.append(f"{rid}: made against baseline {edit.get('base')!r}, current is {rec['hash']!r}; refused")
            log.append({"record": rid, "reviewed": "?", "changed": "", "note": note, "problem": "stale baseline"})
            continue
        sentence = " ".join(str(edit.get("sentence", rec["sentence"])).split())
        words = clean(edit.get("words", rec["words"]))
        glosses = clean(edit.get("glosses", rec["glosses"]))
        was_tr = [t["text"] for t in rec["translations"]]
        now_tr = clean(edit.get("translations", was_tr))
        problem = ""
        if len(words) != len(glosses):
            problem = f"{len(words)} words but {len(glosses)} glosses"
        elif "" in words:
            problem = "an empty word box"
        elif len(now_tr) != len(was_tr):
            problem = f"{len(now_tr)} translations but the baseline has {len(was_tr)}"
        if problem:
            problems.append(f"{rid}: {problem}")
        fields = [("sentence", rec["sentence"], sentence),
                  ("words", dumps(rec["words"]), dumps(words)),
                  ("glosses", dumps(rec["glosses"]), dumps(glosses))]
        fields += [(f"translation.{i + 1}", w, n) for i, (w, n) in enumerate(zip(was_tr, now_tr))]
        changed = []
        for field, was, now in fields:
            if was != now:
                changed.append(field)
                changes.append({"record": rid, "file": rec["file"], "locator": rec["locator"], "field": field,
                                "was": was, "now": now, "reviewer_note": note})
        log.append({"record": rid, "reviewed": "yes" if edit.get("reviewed") else "no",
                    "changed": ",".join(changed), "note": note, "problem": problem})

    for name, rows, cols in (("review_corrections.tsv", changes, ["record", "file", "locator", "field", "was", "now", "reviewer_note"]),
                             ("review_log.tsv", log, ["record", "reviewed", "changed", "note", "problem"])):
        with (out_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, cols, delimiter="\t", lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    reviewed = sum(1 for row in log if row["reviewed"] == "yes")
    questions = [row for row in log if row["note"] and not row["changed"]]
    print(f"Wrote {out_dir / 'review_corrections.tsv'}: {len(changes)} changed fields in "
          f"{len({c['record'] for c in changes})} records")
    print(f"Wrote {out_dir / 'review_log.tsv'}: {len(log)} records touched, {reviewed} of {len(base)} marked reviewed, "
          f"{len(questions)} notes on unchanged records")
    by_field: dict[str, int] = {}
    for c in changes:
        key = c["field"].split(".")[0]
        by_field[key] = by_field.get(key, 0) + 1
    print(f"  changes by field: {by_field}")
    if problems:
        print(f"\n{len(problems)} problem(s); these records need a decision before anything is applied:")
        for p in problems:
            print(f"  {p}")
        sys.exit(1)


if __name__ == "__main__":
    main()
