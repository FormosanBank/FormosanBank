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
from QC.utilities.classify_quotes import (PUNCT, CONSONANT_QUOTE_LANGUAGES, _is_letter,
                                         _strip_flanking_punct, is_vowel)


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


# A glottal stop stands next to a vowel: a word that begins with ' + consonant
# or ends with consonant + ' is a quotation mark glued to a word, not a glottal.


def glottal_next_to_consonant(word: str) -> bool:
    """True iff `word` begins with ' + consonant or ends with consonant + '
    (maintainer, 2026-10-14: such words are removed from the list)."""
    if len(word) >= 2 and word[0] == "'" and _is_letter(word[1]) and not is_vowel(word[1]):
        return True
    if len(word) >= 2 and word[-1] == "'" and _is_letter(word[-2]) and not is_vowel(word[-2]):
        return True
    return False


def build_attestation_set(forms_by_sentence, min_freq=3, include_interior=False):
    """Edge-apostrophe words from single-word S-FORMs (± frequent interiors),
    plus every word anywhere in running text that begins AND ends with ',
    minus every word whose ' stands next to a consonant.

    forms_by_sentence: list of token lists (each = one S-FORM, whitespace-split).
    include_interior=False (default) draws the one-edge words from single-word
    S-FORMs only. Words with ' at BOTH edges are taken from every position
    (maintainer, 2026-10-14: "our allow-list should include words that begin
    *and* end in single quotes"); then any word that starts with ' + consonant
    or ends with consonant + ' is removed ("After adding those, we should remove
    from the allow-list any words that start with a ' followed by a consonant or
    end with a consonant followed by a '"). Only entries passing
    `is_edge_apostrophe_word` are kept -- anything else can never match a
    classifier lookup.
    """
    singleword = set()
    interior = Counter()
    both_edges = set()
    for toks in forms_by_sentence:
        if len(toks) == 1:
            core = _strip_flanking_punct(toks[0]).casefold()
            if core:
                singleword.add(core)
        for t in toks:
            core = _strip_flanking_punct(t).casefold()
            if len(core) >= 3 and core[0] == "'" and core[-1] == "'":
                both_edges.add(core)
        if include_interior:
            for t in toks[1:-1]:                   # exclude initial + final
                core = _strip_flanking_punct(t).casefold()
                if core and _has_letter_or_digit(core):
                    interior[core] += 1
    result = singleword | both_edges
    if include_interior:
        result = result | {w for w, n in interior.items() if n >= min_freq}
    return {w for w in result if is_edge_apostrophe_word(w) and not glottal_next_to_consonant(w)}


def consonant_headwords(forms_by_sentence):
    """One-word S-FORMs (dictionary headwords) whose ' stands next to a
    consonant: the words the consonant filter takes off the list, kept apart as
    the "attested with that spelling" exceptions for CONSONANT_QUOTE_LANGUAGES."""
    out = set()
    for toks in forms_by_sentence:
        if len(toks) == 1:
            core = _strip_flanking_punct(toks[0]).casefold()
            if core and is_edge_apostrophe_word(core) and glottal_next_to_consonant(core):
                out.add(core)
    return out


def frequent_both_edge_words(original_forms, min_count=50, min_ratio=10):
    """Words written with ' at both edges at least `min_count` times in the
    language's original tier, whose variants missing one or both 's are together
    at least `min_ratio` times rarer (maintainer, 2026-10-14: "Add to the allow
    lists words that appear at least 50 times in the corpus with opening and
    ending 's, and the word missing one or both 's is at least 10x less frequent
    as with both")."""
    counts = Counter()
    for toks in original_forms:
        for t in toks:
            core = _strip_flanking_punct(t).casefold()
            if core:
                counts[core] += 1
    out = set()
    for w, n in counts.items():
        if n < min_count or len(w) < 3 or w[0] != "'" or w[-1] != "'":
            continue
        missing = counts[w[1:]] + counts[w[:-1]] + counts[w[1:-1]]
        if n >= min_ratio * missing and is_edge_apostrophe_word(w):
            out.add(w)
    return out


def _iter_language_forms(corpora_path, language, kinds=("original", "standard")):
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
                if form.get("kindOf") in kinds:
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
    words |= frequent_both_edge_words(
        list(_iter_language_forms(args.corpora_path, args.language, kinds=("original",))))
    words = {w for w in words if not glottal_next_to_consonant(w)}
    out_dir = Path(args.reference_dir) / args.language
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "attestation.txt"
    out_path.write_text("\n".join(sorted(words)) + "\n", encoding="utf-8")
    if args.language in CONSONANT_QUOTE_LANGUAGES:
        (out_dir / "attestation_consonant.txt").write_text(
            "\n".join(sorted(consonant_headwords(forms))) + "\n", encoding="utf-8")
    print(f"{args.language}: {len(forms)} S-FORMs scanned -> "
          f"{len(words)} words -> {out_path}")


if __name__ == "__main__":
    main()
