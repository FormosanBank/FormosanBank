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
import bisect
import glob
import os
import re
import sys
from collections import Counter, defaultdict
from xml.etree import ElementTree as ET

QUOTE = "'"

# Punctuation set for follows_punct / precedes_punct. Note: the ASCII ' is NOT
# in here; the ASCII " IS treated as punctuation (per spec).
PUNCT = set('.,;:?!"()[]{}<>«»“”‘’—–…')


def _is_letter(ch) -> bool:
    return ch is not None and ch.isalpha()


def _casefold_dict(dictionary) -> set:
    return {w.casefold() for w in dictionary}


def _strip_flanking_punct(token: str) -> str:
    """Strip flanking PUNCT chars (not the ASCII ') from a token."""
    start, end = 0, len(token)
    while start < end and token[start] in PUNCT:
        start += 1
    while end > start and token[end - 1] in PUNCT:
        end -= 1
    return token[start:end]


def _adjacency(text: str, i: int) -> str:
    """Return 'internal' | 'initial' | 'final' | 'floating' for the ' at i."""
    left = text[i - 1] if i - 1 >= 0 else None
    right = text[i + 1] if i + 1 < len(text) else None
    ll, rl = _is_letter(left), _is_letter(right)
    if ll and rl:
        return "internal"
    if rl and not ll:
        return "initial"
    if ll and not rl:
        return "final"
    return "floating"


def _nearest_nonspace_left(text: str, i: int):
    j = i - 1
    while j >= 0:
        if not text[j].isspace():
            return text[j]
        j -= 1
    return None


def _nearest_nonspace_right(text: str, i: int):
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


def _token_spans(text: str):
    """Yield (start, end, token) for whitespace-separated tokens."""
    for m in re.finditer(r"\S+", text):
        yield (m.start(), m.end(), m.group())


# ---------------------------------------------------------------------------
# Pair evaluation (uses precomputed per-' info)
# ---------------------------------------------------------------------------


def _evaluate_pair(dict_cf, opener_idx, closer_idx, info) -> str:
    """Evaluate one (opener, closer) pair; 'QUOTATION' | 'GLOTTAL' | 'AMBIGUOUS'."""
    ow = info[opener_idx]["opener"]
    cw = info[closer_idx]["closer"]
    oa = ow is not None and ow.casefold() in dict_cf
    ca = cw is not None and cw.casefold() in dict_cf
    of = info[opener_idx]["follows"]
    cp = info[closer_idx]["precedes"]
    if (not oa and not ca) and (of or cp):
        return "QUOTATION"
    if (oa and ca) and (not of) and (not cp):
        return "GLOTTAL"
    return "AMBIGUOUS"


def _combine_pair_verdicts(verdicts) -> str:
    unique = set(verdicts)
    return unique.pop() if len(unique) == 1 else "AMBIGUOUS"


def _pair_verdict_to_label(verdict) -> str:
    if verdict == "GLOTTAL":
        return "GLOTTAL_PAIR"
    if verdict == "QUOTATION":
        return "QUOTATION"
    return "AMBIGUOUS"


# ---------------------------------------------------------------------------
# Main classification (per-sentence precompute for O(T + Q^2), not O(Q^2 * T))
# ---------------------------------------------------------------------------


def classify(form_text, dictionary):
    """Classify every ' occurrence in ``form_text``.

    Returns list of (quote_index, outcome_label).
    """
    text = " ".join(form_text.split())  # whitespace-normalize
    dict_cf = _casefold_dict(dictionary)

    quote_indices = [i for i, ch in enumerate(text) if ch == QUOTE]
    if not quote_indices:
        return []

    # --- precompute token geometry ONCE ---
    spans = list(_token_spans(text))
    starts = [s for s, _, _ in spans]
    lspans = [(s, e, t) for (s, e, t) in spans if any(c.isalpha() for c in t)]
    lstarts = [s for s, _, _ in lspans]
    lends = [e for _, e, _ in lspans]

    def containing_core(i):
        k = bisect.bisect_right(starts, i) - 1
        if 0 <= k < len(spans) and spans[k][1] > i:
            return _strip_flanking_punct(spans[k][2])
        return ""

    def prev_core(i):
        k = bisect.bisect_right(lends, i)          # letter-tokens ending at/<= i
        return _strip_flanking_punct(lspans[k - 1][2]) if k > 0 else None

    def next_core(i):
        k = bisect.bisect_right(lstarts, i)        # first letter-token starting > i
        return _strip_flanking_punct(lspans[k][2]) if k < len(lspans) else None

    info = {}
    for i in quote_indices:
        a = _adjacency(text, i)
        pc, nc = prev_core(i), next_core(i)
        if a == "initial":
            opener = containing_core(i)
        else:
            opener = (QUOTE + nc) if nc is not None else None
        if a == "final":
            closer = containing_core(i)
        else:
            closer = (pc + QUOTE) if pc is not None else None
        info[i] = {
            "adj": a,
            "follows": _follows_punct(text, i),
            "precedes": _precedes_punct(text, i),
            "opener": opener,
            "closer": closer,
            "prev_core": pc,
            "next_core": nc,
        }

    results = []
    for i in quote_indices:
        a = info[i]["adj"]
        if a == "internal":
            results.append((i, "GLOTTAL_INTERNAL"))
        elif a == "floating":
            results.append((i, _classify_floating(dict_cf, i, quote_indices, info)))
        else:
            results.append((i, _classify_bound(dict_cf, i, quote_indices, info)))
    return results


def _classify_floating(dict_cf, i, quote_indices, info):
    follows = info[i]["follows"]
    precedes = info[i]["precedes"]

    # precedes_punct -> acts as CLOSER; match = earlier opener (initial|floating).
    # follows_punct  -> acts as OPENER; match = later   closer (final|floating).
    pairs = []
    if precedes:
        for j in quote_indices:
            if j < i and info[j]["adj"] in ("initial", "floating"):
                pairs.append((j, i))
    if follows:
        for j in quote_indices:
            if j > i and info[j]["adj"] in ("final", "floating"):
                pairs.append((i, j))

    if pairs:
        verdicts = [_evaluate_pair(dict_cf, o, c, info) for (o, c) in pairs]
        return _pair_verdict_to_label(_combine_pair_verdicts(verdicts))

    # No match -> glottal stop; decide what it attaches to.
    prev, nxt = info[i]["prev_core"], info[i]["next_core"]
    attested = 0
    if prev is not None and not prev.endswith(QUOTE):   # attach as word-final
        if (prev + QUOTE).casefold() in dict_cf:
            attested += 1
    if nxt is not None and not nxt.startswith(QUOTE):   # attach as word-initial
        if (QUOTE + nxt).casefold() in dict_cf:
            attested += 1
    return "STRANDED_GLOTTAL" if attested == 1 else "AMBIGUOUS"


def _classify_bound(dict_cf, i, quote_indices, info):
    a = info[i]["adj"]
    pairs = []
    if a == "initial":
        for j in quote_indices:
            if j <= i:
                continue
            if info[j]["adj"] == "final":
                pairs.append((i, j))
            elif info[j]["adj"] == "floating" and info[j]["precedes"]:
                pairs.append((i, j))
    else:  # final
        for j in quote_indices:
            if j >= i:
                continue
            if info[j]["adj"] == "initial":
                pairs.append((j, i))
            elif info[j]["adj"] == "floating" and info[j]["follows"]:
                pairs.append((j, i))

    if not pairs:
        return "GLOTTAL_BOUND_NO_MATCH"
    verdicts = [_evaluate_pair(dict_cf, o, c, info) for (o, c) in pairs]
    return _pair_verdict_to_label(_combine_pair_verdicts(verdicts))


# ---------------------------------------------------------------------------
# Corpus loading + CLI
# ---------------------------------------------------------------------------

_LANG_ATTR = "{http://www.w3.org/XML/1998/namespace}lang"


def _find_lang_files(corpora_root, lang):
    """XML files whose TEXT root declares xml:lang == lang (cheap head pre-filter)."""
    files = []
    for path in glob.iglob(os.path.join(corpora_root, "**", "*.xml"), recursive=True):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                head = fh.read(4096)
        except OSError:
            continue
        if f'xml:lang="{lang}"' in head:
            files.append(path)
    return files


def _sentence_forms(path, lang):
    """Return the S-level original FORM texts for a file of the given lang."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []
    if root.tag != "TEXT" or root.get(_LANG_ATTR) != lang:
        return []
    out = []
    for s in root.findall("S"):
        for form in s.findall("FORM"):
            if form.get("kindOf") == "original" and form.text:
                out.append(" ".join(form.text.split()))
    return out


def build_dictionary(all_forms):
    """Single-word original FORMs (whitespace-free), flanking PUNCT stripped, casefold."""
    words = set()
    for text in all_forms:
        if text and not any(c.isspace() for c in text):
            core = _strip_flanking_punct(text)
            if core:
                words.add(core.casefold())
    return words


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lang", default="ami", help="ISO 639-3 code (default: ami)")
    parser.add_argument(
        "--corpora-path",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "Corpora"),
    )
    parser.add_argument("--examples", type=int, default=4, help="examples per label")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.corpora_path)
    files = _find_lang_files(root, args.lang)
    print(f"Found {len(files)} files for lang={args.lang}", flush=True)

    # Parse each file ONCE; reuse for dictionary + classification.
    per_file_forms = []
    for n, path in enumerate(files, 1):
        per_file_forms.append(_sentence_forms(path, args.lang))
        if n % 500 == 0:
            print(f"  parsed {n}/{len(files)} files…", flush=True)
    all_forms = [f for forms in per_file_forms for f in forms]

    dictionary = build_dictionary(all_forms)
    print(f"Dictionary: {len(dictionary)} single-word original FORMs", flush=True)

    counts = Counter()
    examples = defaultdict(list)
    n_sent = n_quote_sent = 0
    for text in all_forms:
        n_sent += 1
        if QUOTE not in text:
            continue
        n_quote_sent += 1
        for _idx, label in classify(text, dictionary):
            counts[label] += 1
            if len(examples[label]) < args.examples and text not in examples[label]:
                examples[label].append(text)

    order = [
        "GLOTTAL_INTERNAL", "GLOTTAL_BOUND_NO_MATCH", "GLOTTAL_PAIR",
        "STRANDED_GLOTTAL", "QUOTATION", "AMBIGUOUS",
    ]
    total = sum(counts.values())
    print(f"\nSentences: {n_sent} ({n_quote_sent} contain a ')")
    print("\nOutcome counts:")
    for label in order:
        print(f"  {label:24s} {counts.get(label, 0)}")
    print(f"  {'TOTAL':24s} {total}")

    print("\nExamples per label:")
    for label in order:
        print(f"\n[{label}]")
        for ex in examples.get(label, []):
            print(f"  - {ex[:200]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
