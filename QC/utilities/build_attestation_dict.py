"""Build a per-language attestation dictionary for the quote/glottal classifier.

By default the set is **single-word sentence-level S-FORMs only** (whitespace-free
tokens) — i.e. dictionary entries. This keeps the set clean: interior tokens
harvested from running text can be polluted by unresolved quote-`'` (e.g. a
quote-wrapped 'madimadiay leaking in as if it were a word), which then defeats
the classifier's attestation guard. Single-word S-FORMs are far less prone to
this, and coverage grows naturally as more dictionary entries are added.

With --include-interior, the set additionally unions in interior tokens (neither
sentence-initial nor sentence-final), punctuation-stripped, containing >=1
letter/digit, with frequency >= --min-freq. Use with care (pollution risk).

Scans all Corpora/*/XML files whose TEXT xml:lang resolves to <Language>, using
both original and standard S-FORM tiers. Output: newline-delimited, sorted,
casefolded, to <reference_dir>/<Language>/attestation.txt.

Regenerate whenever a corpus is ported (the port-corpus-in skill runs this),
or standalone at any time.
"""
import argparse
import glob
import os
import sys
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from QC.corpus_counts import resolve_language, XML_LANG
from QC.utilities.classify_quotes import PUNCT, _strip_flanking_punct, _is_letter


def _has_letter_or_digit(word: str) -> bool:
    return any(_is_letter(ch) or ch.isdigit() for ch in word)


# Interior marks a Formosan word may carry besides letters (the apostrophe
# itself, Saisiyat's vowel-length colon, the Bunun/Thao hyphen letter, the
# reduplication tilde, Sakizaya's circumflex).
ALLOWED_MARKS = set("':-~^")


def is_edge_apostrophe_word(word: str) -> bool:
    """True iff `word` can ever matter to the quote classifier.

    Every dictionary lookup in classify_quotes/clean_xml tests a form that
    starts or ends with the apostrophe (`'word` / `word'`), so only plausible
    Formosan words carrying a word-initial or word-final `'` belong in an
    attestation dictionary (maintainer ruling 2026-08-11).
    """
    if not word or not (word.startswith("'") or word.endswith("'")):
        return False
    if not any(_is_letter(ch) for ch in word):
        return False
    return all(_is_letter(ch) or ch in ALLOWED_MARKS for ch in word)


def build_attestation_set(forms_by_sentence, min_freq=3, include_interior=False):
    """Edge-apostrophe words from single-word S-FORMs (± frequent interiors).

    forms_by_sentence: list of token lists (each = one S-FORM, whitespace-split).
    include_interior=False (default) draws from single-word S-FORMs only.
    Regardless of source, only entries passing `is_edge_apostrophe_word`
    are kept — anything else can never match a classifier lookup.
    """
    singleword = set()
    interior = Counter()
    for toks in forms_by_sentence:
        if len(toks) == 1:
            core = _strip_flanking_punct(toks[0]).casefold()
            if core:
                singleword.add(core)
        if include_interior:
            for t in toks[1:-1]:                   # exclude initial + final
                core = _strip_flanking_punct(t).casefold()
                if core and _has_letter_or_digit(core):
                    interior[core] += 1
    result = singleword
    if include_interior:
        result = result | {w for w, n in interior.items() if n >= min_freq}
    return {w for w in result if is_edge_apostrophe_word(w)}


def _iter_language_forms(corpora_path, language):
    """Yield token lists for every original/standard S-FORM in `language`."""
    for path in glob.iglob(os.path.join(corpora_path, "**", "*.xml"),
                           recursive=True):
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError:
            continue
        if root.tag != "TEXT":
            continue
        code = root.get(XML_LANG)
        dialect = root.get("dialect")
        if resolve_language(code, dialect) != language:
            continue
        for s in root.findall("S"):
            for form in s.findall("FORM"):
                if form.get("kindOf") in ("original", "standard"):
                    text = " ".join("".join(form.itertext()).split())
                    if text:
                        yield text.split()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--language", required=True, help="Display name, e.g. Amis")
    ap.add_argument("--include-interior", action="store_true",
                    help="also union in >=min-freq interior tokens (pollution risk)")
    ap.add_argument("--min-freq", type=int, default=3)
    ap.add_argument("--corpora_path", default=str(_REPO_ROOT / "Corpora"))
    ap.add_argument("--reference_dir",
                    default=str(_REPO_ROOT / "QC" / "validation" / "reference"))
    args = ap.parse_args(argv)

    forms = list(_iter_language_forms(args.corpora_path, args.language))
    words = build_attestation_set(forms, args.min_freq,
                                  include_interior=args.include_interior)
    out_dir = Path(args.reference_dir) / args.language
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "attestation.txt"
    out_path.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    print(f"{args.language}: {len(forms)} S-FORMs scanned -> "
          f"{len(words)} words -> {out_path}")


if __name__ == "__main__":
    main()
