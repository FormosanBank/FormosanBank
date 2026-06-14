#!/usr/bin/env python3
"""identify_alternative_translations.py — flag translations carrying an alternative.

Audit/draft tool (added 2026-06-09 during the FormosanBank dev-repo audit).

Pattern: the Truku form has NO parenthetical, but the Chinese translation does,
e.g. `我要打那個小孩。(那個小孩要被我打)`. Three sub-cases (maintainer decision
2026-06-09):
  - 'alt_translation'    -> the parenthetical is a genuine alternative rendering.
                            Emit TWO <TRANSL>: primary + the alternative with
                            ver="alt" (per the FormosanBank XML schema).
  - 'explanatory_note'   -> the parenthetical clarifies a word, not an alternative.
                            DO NOTHING (leave the translation as-is).
  - 'inline_slash_option'-> '/'-separated inline alternatives. DEFER (handle separately).

This script does NOT modify anything; it writes a review list for hand-checking
before the rule is incorporated into the pipeline.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data/processed/examples_clean.jsonl"
OUT = ROOT / "data/processed/alternative_translation_candidates.csv"

CJK = re.compile(r"[㐀-鿿]")
CJK_PAREN = re.compile(r"[（(]\s*=?\s*([^()（）]*[㐀-鿿][^()（）]*?)\s*[)）]")
WS = re.compile(r"\s+")

DISPOSITION = {
    "alt_translation": "split_two_TRANSL_primary_plus_ver_alt",
    "explanatory_note": "do_nothing",
    "inline_slash_option": "defer_handle_separately",
}


def _norm(text: str) -> str:
    return WS.sub(" ", text).strip()


def _classify(translation: str, inside: str, main: str) -> str:
    if "/" in translation or "／" in translation:
        return "inline_slash_option"
    if len(CJK.findall(main)) >= 4 and len(CJK.findall(inside)) >= 3 and \
            len(CJK.findall(inside)) >= 0.5 * len(CJK.findall(main)):
        return "alt_translation"
    return "explanatory_note"


def main() -> int:
    rows = [json.loads(l) for l in CLEAN.open(encoding="utf-8") if l.strip()]
    out_rows: list[dict] = []
    for r in rows:
        form = r.get("truku_line_clean", "")
        transl = r.get("chinese_translation_clean", "")
        if not form or "(" in form or "（" in form:
            continue  # only translations whose alternative is NOT in the Formosan
        m = CJK_PAREN.search(transl)
        if not m:
            continue
        inside = m.group(1).strip()
        main = _norm(CJK_PAREN.sub("", transl).replace("=", " "))
        pattern = _classify(transl, inside, main)
        out_rows.append({
            "example_record_id": r["example_record_id"],
            "page": r.get("page_number_one_based", ""),
            "pattern_guess": pattern,
            "disposition": DISPOSITION[pattern],
            "original_translation": transl,
            "proposed_primary_TRANSL": main if pattern == "alt_translation" else "",
            "proposed_alt_TRANSL_ver_alt": inside if pattern == "alt_translation" else "",
            "truku_form": form,
        })

    fields = [
        "example_record_id", "page", "pattern_guess", "disposition",
        "original_translation", "proposed_primary_TRANSL",
        "proposed_alt_TRANSL_ver_alt", "truku_form",
    ]
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(out_rows)

    import collections
    counts = collections.Counter(r["pattern_guess"] for r in out_rows)
    print(f"alternative-translation candidates: {len(out_rows)}")
    for p in ("alt_translation", "explanatory_note", "inline_slash_option"):
        print(f"  {p:20s} {counts.get(p, 0):3d}  -> {DISPOSITION[p]}")
    print(f"written: {OUT}\n")
    for r in out_rows:
        if r["pattern_guess"] != "alt_translation":
            continue
        print(f"{r['example_record_id']}  (p{r['page']})")
        print(f"    transl:      {r['original_translation']}")
        print(f"    -> primary:  {r['proposed_primary_TRANSL']}")
        print(f"    -> ver=alt:  {r['proposed_alt_TRANSL_ver_alt']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
