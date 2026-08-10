#!/usr/bin/env python3
"""Temporary, exploratory classifier for single-quote ``'`` characters.

For each ``'`` occurrence in a sentence, decides whether it is a glottal stop,
a quotation mark, or ambiguous, following the verbatim spec in the task that
created this file. This is exploratory tooling, not part of the standard QC
pipeline.

Public API
----------
``classify(form_text, dictionary) -> list[(quote_index, outcome_label)]``

``dictionary`` is a case-folded (or to-be-case-folded) set of single-word
original FORMs for the language. ``attested(w)`` means ``w.casefold()`` is in
the dictionary.

Outcome labels
--------------
GLOTTAL_INTERNAL, GLOTTAL_BOUND_NO_MATCH, GLOTTAL_PAIR, STRANDED_GLOTTAL,
QUOTATION, AMBIGUOUS.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

QUOTE = "'"

# Punctuation set for follows_punct / precedes_punct. Note: the ASCII ' is NOT
# in here; the ASCII " IS treated as punctuation (per spec).
PUNCT = set('.,;:?!"()[]{}<>«»“”‘’—–…')


def _is_letter(ch: str) -> bool:
    return ch is not None and ch.isalpha()


def _casefold_dict(dictionary) -> set:
    return {w.casefold() for w in dictionary}


def _strip_flanking_punct(token: str) -> str:
    """Strip flanking PUNCT chars (not the ASCII ') from a token."""
    start = 0
    end = len(token)
    while start < end and token[start] in PUNCT:
        start += 1
    while end > start and token[end - 1] in PUNCT:
        end -= 1
    return token[start:end]


# ---------------------------------------------------------------------------
# Per-occurrence geometry
# ---------------------------------------------------------------------------


def _adjacency(text: str, i: int) -> str:
    """Return 'internal' | 'initial' | 'final' | 'floating' for the ' at i.

    internal: letter on both immediate sides.
    initial:  letter immediately right, non-letter immediately left.
    final:    letter immediately left, non-letter immediately right.
    floating: non-letter on both immediate sides.
    """
    left = text[i - 1] if i - 1 >= 0 else None
    right = text[i + 1] if i + 1 < len(text) else None
    left_letter = _is_letter(left)
    right_letter = _is_letter(right)
    if left_letter and right_letter:
        return "internal"
    if right_letter and not left_letter:
        return "initial"
    if left_letter and not right_letter:
        return "final"
    return "floating"


def _nearest_nonspace_left(text: str, i: int) -> str | None:
    j = i - 1
    while j >= 0:
        if not text[j].isspace():
            return text[j]
        j -= 1
    return None


def _nearest_nonspace_right(text: str, i: int) -> str | None:
    j = i + 1
    while j < len(text):
        if not text[j].isspace():
            return text[j]
        j += 1
    return None


def _follows_punct(text: str, i: int) -> bool:
    ch = _nearest_nonspace_left(text, i)
    return ch is not None and ch in PUNCT


def _precedes_punct(text: str, i: int) -> bool:
    ch = _nearest_nonspace_right(text, i)
    return ch is not None and ch in PUNCT


# ---------------------------------------------------------------------------
# Word-neighbour helpers (for floating quotes)
# ---------------------------------------------------------------------------


def _token_spans(text: str):
    """Yield (start, end, token) for whitespace-separated tokens."""
    for m in re.finditer(r"\S+", text):
        yield (m.start(), m.end(), m.group())


def _prev_word_core(text: str, i: int) -> str | None:
    """Core of the nearest whitespace token to the LEFT of i containing a letter."""
    best = None
    for start, end, tok in _token_spans(text):
        if end <= i and any(c.isalpha() for c in tok):
            best = tok  # keep advancing; last one before i wins
        if start >= i:
            break
    if best is None:
        return None
    return _strip_flanking_punct(best)


def _next_word_core(text: str, i: int) -> str | None:
    """Core of the nearest whitespace token to the RIGHT of i containing a letter."""
    for start, end, tok in _token_spans(text):
        if start > i and any(c.isalpha() for c in tok):
            return _strip_flanking_punct(tok)
    return None


def _token_core_containing(text: str, i: int) -> str:
    """Core of the whitespace token that contains index i."""
    for start, end, tok in _token_spans(text):
        if start <= i < end:
            return _strip_flanking_punct(tok)
    return ""


# ---------------------------------------------------------------------------
# Candidate word construction
# ---------------------------------------------------------------------------


def _opener_candidate(text: str, i: int, adjacency: str) -> str | None:
    """Candidate word for a ' acting as an opener (attaches to the word to its right).

    Bound word-initial 'word -> that token's core ('word).
    Floating opener -> "'" + next_word_core.
    """
    if adjacency == "initial":
        return _token_core_containing(text, i)
    nxt = _next_word_core(text, i)
    if nxt is None:
        return None
    return QUOTE + nxt


def _closer_candidate(text: str, i: int, adjacency: str) -> str | None:
    """Candidate word for a ' acting as a closer (attaches to the word to its left).

    Bound word-final word' -> that token's core (word').
    Floating closer -> prev_word_core + "'".
    """
    if adjacency == "final":
        return _token_core_containing(text, i)
    prev = _prev_word_core(text, i)
    if prev is None:
        return None
    return prev + QUOTE


# ---------------------------------------------------------------------------
# Pair evaluation
# ---------------------------------------------------------------------------


def _evaluate_pair(text, dict_cf, opener_idx, closer_idx):
    """Evaluate one (opener, closer) pair; return 'QUOTATION' | 'GLOTTAL' | 'AMBIGUOUS'."""
    opener_adj = _adjacency(text, opener_idx)
    closer_adj = _adjacency(text, closer_idx)
    opener_word = _opener_candidate(text, opener_idx, opener_adj)
    closer_word = _closer_candidate(text, closer_idx, closer_adj)

    opener_attested = opener_word is not None and opener_word.casefold() in dict_cf
    closer_attested = closer_word is not None and closer_word.casefold() in dict_cf

    opener_follows = _follows_punct(text, opener_idx)
    closer_precedes = _precedes_punct(text, closer_idx)

    if (not opener_attested and not closer_attested) and (
        opener_follows or closer_precedes
    ):
        return "QUOTATION"
    if (opener_attested and closer_attested) and (not opener_follows) and (
        not closer_precedes
    ):
        return "GLOTTAL"
    return "AMBIGUOUS"


def _combine_pair_verdicts(verdicts):
    """Combine per-pair verdicts. Same for all -> that verdict; conflict -> AMBIGUOUS."""
    unique = set(verdicts)
    if len(unique) == 1:
        return unique.pop()
    return "AMBIGUOUS"


# ---------------------------------------------------------------------------
# Main classification
# ---------------------------------------------------------------------------


def classify(form_text, dictionary):
    """Classify every ' occurrence in ``form_text``.

    Returns list of (quote_index, outcome_label).
    """
    text = " ".join(form_text.split())  # whitespace-normalize
    dict_cf = _casefold_dict(dictionary)

    quote_indices = [i for i, ch in enumerate(text) if ch == QUOTE]
    adjacencies = {i: _adjacency(text, i) for i in quote_indices}

    results = []
    for i in quote_indices:
        adj = adjacencies[i]
        if adj == "internal":
            results.append((i, "GLOTTAL_INTERNAL"))
        elif adj == "floating":
            results.append((i, _classify_floating(text, dict_cf, i, quote_indices, adjacencies)))
        else:  # initial or final (bound)
            results.append((i, _classify_bound(text, dict_cf, i, adj, quote_indices, adjacencies)))
    return results


def _classify_floating(text, dict_cf, i, quote_indices, adjacencies):
    follows = _follows_punct(text, i)
    precedes = _precedes_punct(text, i)

    # Search for potential matches.
    # If precedes_punct: this floating acts as a CLOSER; look for openers EARLIER
    #   that are word-initial OR floating.
    # If follows_punct: this floating acts as an OPENER; look for closers LATER
    #   that are word-final OR floating.
    pairs = []  # (opener_idx, closer_idx)
    if precedes:
        for j in quote_indices:
            if j < i and adjacencies[j] in ("initial", "floating"):
                pairs.append((j, i))
    if follows:
        for j in quote_indices:
            if j > i and adjacencies[j] in ("final", "floating"):
                pairs.append((i, j))

    if pairs:
        verdicts = [_evaluate_pair(text, dict_cf, o, c) for (o, c) in pairs]
        verdict = _combine_pair_verdicts(verdicts)
        return _pair_verdict_to_label(verdict)

    # No potential match -> assume glottal stop; determine attachment.
    prev = _prev_word_core(text, i)
    nxt = _next_word_core(text, i)

    candidates = []  # list of (label_word, is_attested)
    # cand_prev = prev_core + "'": ruled out if prev ends in ' (double glottal) or no prev.
    if prev is not None and not prev.endswith(QUOTE):
        cand = prev + QUOTE
        candidates.append(("prev", cand, cand.casefold() in dict_cf))
    # cand_next = "'" + next_core: ruled out if next starts with ' or no next.
    if nxt is not None and not nxt.startswith(QUOTE):
        cand = QUOTE + nxt
        candidates.append(("next", cand, cand.casefold() in dict_cf))

    attested = [c for c in candidates if c[2]]
    if len(attested) == 1:
        return "STRANDED_GLOTTAL"
    return "AMBIGUOUS"


def _classify_bound(text, dict_cf, i, adj, quote_indices, adjacencies):
    # BOUND match search: matches are primarily bound at the OPPOSITE edge.
    # word-initial ' (opener) matches a LATER word-final ' (closer).
    # word-final ' (closer) matches an EARLIER word-initial ' (opener).
    # A floating ' that is acting as the opposite-edge partner (a floating opener
    # that follows punctuation, or a floating closer that precedes punctuation)
    # is also a valid partner so bound/floating pairs classify consistently
    # (see spec test 10: "pasowal: ' cima tayni'").
    pairs = []
    if adj == "initial":
        for j in quote_indices:
            if j <= i:
                continue
            if adjacencies[j] == "final":
                pairs.append((i, j))
            elif adjacencies[j] == "floating" and _precedes_punct(text, j):
                pairs.append((i, j))
    else:  # final
        for j in quote_indices:
            if j >= i:
                continue
            if adjacencies[j] == "initial":
                pairs.append((j, i))
            elif adjacencies[j] == "floating" and _follows_punct(text, j):
                pairs.append((j, i))

    if not pairs:
        return "GLOTTAL_BOUND_NO_MATCH"

    verdicts = [_evaluate_pair(text, dict_cf, o, c) for (o, c) in pairs]
    verdict = _combine_pair_verdicts(verdicts)
    return _pair_verdict_to_label(verdict)


def _pair_verdict_to_label(verdict):
    if verdict == "GLOTTAL":
        return "GLOTTAL_PAIR"
    if verdict == "QUOTATION":
        return "QUOTATION"
    return "AMBIGUOUS"


# ---------------------------------------------------------------------------
# Corpus loading + CLI
# ---------------------------------------------------------------------------


def _find_lang_files(corpora_root, lang):
    """Return XML files whose TEXT has xml:lang == lang."""
    files = []
    pattern = os.path.join(corpora_root, "**", "*.xml")
    for path in glob.iglob(pattern, recursive=True):
        # Cheap pre-filter to avoid parsing every file fully first.
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                head = fh.read(4096)
        except OSError:
            continue
        if f'xml:lang="{lang}"' not in head:
            continue
        files.append(path)
    return files


_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def _iter_sentence_forms(path, lang):
    """Yield S-level original FORM text for sentences in a file of the given lang."""
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return
    root = tree.getroot()
    if root.tag != "TEXT" or root.get(_LANG_ATTR) != lang:
        return
    for s in root.findall("S"):
        for form in s.findall("FORM"):
            if form.get("kindOf") == "original" and form.text:
                yield " ".join(form.text.split())


def build_dictionary(files, lang):
    """Single-word S-FORM originals (whitespace-free FORM text, flanking PUNCT stripped)."""
    words = set()
    for path in files:
        for text in _iter_sentence_forms(path, lang):
            if text and not any(c.isspace() for c in text):
                core = _strip_flanking_punct(text)
                if core:
                    words.add(core.casefold())
    return words


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default="ami", help="ISO 639-3 language code (default: ami)")
    parser.add_argument(
        "--corpora-path",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "Corpora"),
        help="Path to the Corpora directory.",
    )
    args = parser.parse_args(argv)

    corpora_root = os.path.abspath(args.corpora_path)
    files = _find_lang_files(corpora_root, args.lang)
    print(f"Found {len(files)} files for lang={args.lang} under {corpora_root}")

    dictionary = build_dictionary(files, args.lang)
    print(f"Dictionary: {len(dictionary)} single-word original FORMs")

    counts = Counter()
    examples = defaultdict(list)
    n_sentences = 0
    n_with_quote = 0

    for path in files:
        for text in _iter_sentence_forms(path, args.lang):
            n_sentences += 1
            if QUOTE not in text:
                continue
            n_with_quote += 1
            for (_idx, label) in classify(text, dictionary):
                counts[label] += 1
                if len(examples[label]) < 3 and text not in examples[label]:
                    examples[label].append(text)

    print(f"\nSentences scanned: {n_sentences} ({n_with_quote} contain a ')")
    print("\nOutcome counts:")
    order = [
        "GLOTTAL_INTERNAL",
        "GLOTTAL_BOUND_NO_MATCH",
        "GLOTTAL_PAIR",
        "STRANDED_GLOTTAL",
        "QUOTATION",
        "AMBIGUOUS",
    ]
    total = sum(counts.values())
    for label in order:
        print(f"  {label:24s} {counts.get(label, 0)}")
    print(f"  {'TOTAL':24s} {total}")

    print("\nExamples per label:")
    for label in order:
        print(f"\n[{label}]")
        for ex in examples.get(label, []):
            print(f"  - {ex}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
