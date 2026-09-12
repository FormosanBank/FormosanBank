#!/usr/bin/env python3
"""identify_unglossed_options.py — flag examples with an unglossed parenthesized option.

Audit/draft tool (added 2026-06-09 during the FormosanBank dev-repo audit).

Pattern: an example whose Truku form contains a parenthesized span of *word*
material (Latin letters), e.g. `M-gay =ku pila sunan (ka yaku).`, where the
source interlinear gloss covers only the NON-parenthesized core. The gloss
aligner therefore could not align the full form and fell back to `words_only`
(W/M FORMs emitted, but no per-morpheme gloss TRANSL).

Per maintainer direction (2026-06-09), each such example should become TWO <S>:
  1. glossed:   the glossed part only — the parenthesized option REMOVED.
  2. unglossed: all words, with the PARENTHESES deleted but their content kept.

This script does NOT modify anything. It writes a review list for hand-checking
before the rule is incorporated into the pipeline.

Inputs (relative to repo root):
  data/processed/examples_clean.jsonl       (truku_line_clean keeps parentheses)
  data/processed/gloss_alignment_audit.csv  (alignment_status, sentence_id, counts)
Output:
  data/processed/unglossed_option_candidates.csv
  + a printed summary.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data/processed/examples_clean.jsonl"
AUDIT = ROOT / "data/processed/gloss_alignment_audit.csv"
OUT = ROOT / "data/processed/unglossed_option_candidates.csv"

PAREN = re.compile(r"[（(]([^()（）]*)[)）]")
LATIN = re.compile(r"[A-Za-z]")
WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return WS.sub(" ", text).strip()


def _strip_paren_spans(text: str) -> str:
    """Remove parenthesized spans AND their content (the 'glossed part only')."""
    return _norm(PAREN.sub(" ", text))


def _delete_paren_marks(text: str) -> str:
    """Delete only the parenthesis characters, keep the content (the 'all words' form)."""
    return _norm(text.replace("(", "").replace(")", "").replace("（", "").replace("）", ""))


def _latin_paren_spans(text: str) -> list[str]:
    return [m.group(1).strip() for m in PAREN.finditer(text) if LATIN.search(m.group(1))]


TRANSLATION_ALT = re.compile(r"[（(/／]")


def _classify(form: str, spans: list[str], gloss_tok: int) -> str:
    """Heuristic guess at WHICH pattern this is (verify by hand).

    - 'variant_clause': the parenthetical is a whole ALTERNATIVE SENTENCE, often
      flagged by an '=' equivalence marker right before '(' (`X. = (Y.)`), or a
      parenthetical nearly as long as the main clause. The two are equivalent
      word orders / morphological variants -> SEPARATE variant <S> elements (the
      gloss belongs to the first; same translation), not one concatenated form.
    - 'optional_glossed': a short parenthesized argument that the source gloss
      DOES cover (gloss length ~ the with-option form). Split into with-option
      <S> + without-option <S>, both glossable. Translation may or may not
      differ (see translation_has_alternative).
    - 'optional_unglossed': a short parenthesized argument the gloss SKIPPED
      (gloss length ~ the without-option form), e.g. `(ka yaku)`. Split into
      glossed-core <S> + all-words(no-gloss) <S>.
    """
    if re.search(r"=\s*[（(]", form):
        return "variant_clause"
    without_tok = len(_strip_paren_spans(form).split())
    with_tok = len(_delete_paren_marks(form).split())
    paren_tok = max((len(s.split()) for s in spans), default=0)
    # The parenthetical is a whole CLAUSE (-> variant), not an optional argument,
    # when it ends in sentence-final ?/! (interrogative/exclamative) or is as long
    # as a clause (>= 4 tokens). A short NP like "(ka yaku)" stays an argument.
    if any(s.rstrip().endswith(("?", "!", "？", "！")) for s in spans) or paren_tok >= 4:
        return "variant_clause"
    if gloss_tok and abs(gloss_tok - with_tok) <= abs(gloss_tok - without_tok):
        return "optional_glossed"
    return "optional_unglossed"


def main() -> int:
    clean = {}
    with CLEAN.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rec = json.loads(line)
                clean[rec["example_record_id"]] = rec
    audit = list(csv.DictReader(AUDIT.open(encoding="utf-8")))

    candidates: list[dict] = []
    words_only_no_paren = 0
    for a in audit:
        if a["alignment_status"] == "morpheme_aligned":
            continue
        rec = clean.get(a["example_record_id"])
        if rec is None:
            continue
        form = rec.get("truku_line_clean", "")
        spans = _latin_paren_spans(form)
        if not spans:
            words_only_no_paren += 1
            continue
        try:
            gloss_tok = int(a["gloss_token_count"])
        except (KeyError, ValueError):
            gloss_tok = 0
        translation = rec.get("chinese_translation_clean", "")
        candidates.append({
            "sentence_id": a["sentence_id"],
            "page": a["page_number_one_based"],
            "label": a["example_label_clean"],
            "pattern_guess": _classify(form, spans, gloss_tok),
            "alignment_status": a["alignment_status"],
            "form_token_count": a["form_token_count"],
            "gloss_token_count": a["gloss_token_count"],
            "original_form": form,
            "parenthetical_options": " | ".join(spans),
            "form_without_option": _strip_paren_spans(form),      # option removed (core)
            "form_all_words": _delete_paren_marks(form),          # parens deleted, words kept
            "gloss_line": rec.get("gloss_line_clean", ""),
            "chinese_translation": translation,
            # Does the SOURCE translation itself encode the alternative (parens or
            # slash)? If so the two <S> likely need DIFFERENT translations; if not
            # they probably share one. Flagged for the by-hand decision.
            "translation_has_alternative": "yes" if TRANSLATION_ALT.search(translation) else "no",
        })

    fields = [
        "sentence_id", "page", "label", "pattern_guess", "alignment_status",
        "form_token_count", "gloss_token_count",
        "original_form", "parenthetical_options",
        "form_without_option", "form_all_words",
        "gloss_line", "chinese_translation", "translation_has_alternative",
    ]
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(candidates)

    order = ["optional_unglossed", "optional_glossed", "variant_clause"]
    by_pattern: dict[str, list[dict]] = {p: [] for p in order}
    for c in candidates:
        by_pattern.setdefault(c["pattern_guess"], []).append(c)

    print(f"candidates (parenthesized material): {len(candidates)}")
    for p in order:
        print(f"  {p:20s} {len(by_pattern.get(p, []))}")
    print(f"other words_only (no parenthetical — different problem): {words_only_no_paren}")
    print(f"written: {OUT}\n")

    for p in order:
        group = by_pattern.get(p, [])
        if not group:
            continue
        print(f"================ {p}  ({len(group)}) ================")
        for c in group:
            print(f"{c['sentence_id']}  (p{c['page']} {c['label']})  translation_alt={c['translation_has_alternative']}")
            print(f"    form:    {c['original_form']}")
            print(f"    option:  {c['parenthetical_options']}")
            print(f"    gloss:   {c['gloss_line']}")
            print(f"    transl:  {c['chinese_translation']}")
            print(f"    -> S without option: {c['form_without_option']}")
            print(f"    -> S all words:      {c['form_all_words']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
