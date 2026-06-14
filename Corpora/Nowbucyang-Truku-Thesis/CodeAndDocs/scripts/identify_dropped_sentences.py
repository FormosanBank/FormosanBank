#!/usr/bin/env python3
"""identify_dropped_sentences.py — flag numbered examples that lost a 2nd sentence.

Audit/draft tool (added 2026-06-09 during the FormosanBank dev-repo audit).

`_parse_example_block` keeps exactly ONE form+gloss+translation per numbered
block; a SECOND Truku sentence in the same block (typically a Q&A answer, e.g.
`Q: ...` / `A: ...`) falls into `commentary_raw`, which is never emitted to the
XML. This finds those genuine dropped sentences.

It deliberately EXCLUDES the noise the broad scan picks up: compound-word
morphology tables (`村長 bukung alang 統治者+部落`, Chinese-first / `+`-bearing)
and `->` derivation chains / Chinese prose. A genuine dropped Truku sentence is
either marked with a `Q:`/`A:` dialogue label, or is a pure-Latin clause (no CJK).

Proposed pipeline fix (maintainer-approved direction 2026-06-09): split such a
block into multiple records — mirror the existing chapter-2 compound parser,
which already emits several records from one block — and drop any `* ...`
ungrammatical alternative in the recovered sentence.

Writes a review list; modifies nothing.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/processed/examples_raw.jsonl"
OUT = ROOT / "data/processed/dropped_sentence_candidates.csv"

CJK = re.compile(r"[㐀-鿿]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z='’ʔ.\-]*")
QA_LABEL = re.compile(r"^\s*[A-Za-z]\s*[:：]")


def _is_dropped_truku_sentence(piece: str) -> bool:
    core = QA_LABEL.sub("", piece).strip()
    if len(LATIN_WORD.findall(core)) < 2:
        return False
    has_qa = bool(QA_LABEL.match(piece))
    # genuine = a dialogue-labelled line, OR a pure-Latin clause (no CJK gloss/table)
    return has_qa or not CJK.search(core)


def main() -> int:
    rows = [json.loads(l) for l in RAW.open(encoding="utf-8") if l.strip()]
    out_rows: list[dict] = []
    for r in rows:
        pieces = [p.strip() for p in (r.get("commentary_raw", "") or "").split("|") if p.strip()]
        dropped_forms = [p for p in pieces if _is_dropped_truku_sentence(p)]
        if not dropped_forms:
            continue
        # a CJK-only piece following the form is its translation
        dropped_transl = [p for p in pieces if CJK.search(p) and not LATIN_WORD.search(p)]
        out_rows.append({
            "parent_example_record_id": r["example_record_id"],
            "page": r.get("page_number_one_based", ""),
            "label": r.get("example_label_raw", ""),
            "kept_form_Q": r.get("truku_line_raw", ""),
            "kept_translation": r.get("chinese_translation_raw", ""),
            "dropped_form_A_raw": " | ".join(dropped_forms),
            "dropped_translation_A": " | ".join(dropped_transl),
            "notes": "drop any '* ...' ungrammatical alternative when recovering",
        })

    fields = [
        "parent_example_record_id", "page", "label",
        "kept_form_Q", "kept_translation",
        "dropped_form_A_raw", "dropped_translation_A", "notes",
    ]
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    print(f"genuine dropped-sentence examples: {len(out_rows)}")
    print(f"written: {OUT}\n")
    for r in out_rows:
        print(f"{r['parent_example_record_id']}  (p{r['page']} {r['label']})")
        print(f"    kept (Q):      {r['kept_form_Q']!r}  /  {r['kept_translation']!r}")
        print(f"    dropped (A):   {r['dropped_form_A_raw']!r}  /  {r['dropped_translation_A']!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
