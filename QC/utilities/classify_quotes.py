#!/usr/bin/env python3
"""Classifier for single-quote ``'`` characters in FORM text.

For each ``'`` occurrence in a sentence, decides whether it is a glottal stop,
a quotation mark, or ambiguous, following the verbatim spec in the task that
created this file. This module is production code: `QC/cleaning/clean_xml.py`
imports it to drive the original-tier ``'``-as-quotation correction (via
`apply_quote_corrections`). It also provides a standalone CLI (`main`) for
corpus-wide audits.

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

# Quotation marks as they appear in a TRANSL (double-quote + bracket families).
TRANSL_QUOTES = set('"“”＂「」『』')
# Double-quote family as it appears in a FORM.
FORM_DQUOTES = set('"“”＂')


def translation_confirms_glottal(form_text, transl_texts):
    """First-pass test: given the S has >=1 TRANSL, is every ' in the FORM a glottal?

    - no quotation marks in any TRANSL  -> yes (the sentence carries no quotation);
    - TRANSL quotation-mark count == FORM double-quote count -> yes (the FORM's
      quotations are all carried by ", so the remaining ' are glottal stops).
    Returns False when there is NO TRANSL (no information) or the counts differ.
    """
    if not transl_texts:
        return False
    tq = sum(ch in TRANSL_QUOTES for t in transl_texts for ch in t)
    if tq == 0:
        return True
    fq = sum(ch in FORM_DQUOTES for ch in form_text)
    return tq == fq


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


# Punctuation that a CLOSING quotation mark can follow (e.g. word.' or word. ').
TERMINAL_PUNCT = set(".,;:?!")


def _follows_terminal(text: str, i: int) -> bool:
    ch = _nearest_nonspace_left(text, i)
    return ch is not None and ch in TERMINAL_PUNCT


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
    # cf: the closer follows terminal punctuation (word.' / word. ') — a closing
    # quotation-mark signal, since a glottal letter never sits after a period.
    cf = info[closer_idx]["follows_terminal"]
    if (not oa and not ca) and (of or cp or cf):
        return "QUOTATION"
    if (oa and ca) and (not of) and (not cp) and (not cf):
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
        follows_terminal = _follows_terminal(text, i)
        info[i] = {
            "adj": a,
            "follows": _follows_punct(text, i),
            "precedes": _precedes_punct(text, i),
            "follows_terminal": follows_terminal,
            # A ' that follows terminal punctuation and opens nothing after it
            # (no following letter-word) is a closing quotation mark.
            "end_closer": a == "floating" and follows_terminal and nc is None,
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
    # end_closer (word.' / word. ') -> acts as CLOSER; match = earlier opener.
    pairs = []
    if precedes:
        for j in quote_indices:
            if j < i and info[j]["adj"] in ("initial", "floating"):
                pairs.append((j, i))
    if info[i]["end_closer"]:
        for j in quote_indices:
            if j < i and (
                info[j]["adj"] == "initial"
                or (info[j]["adj"] == "floating" and info[j]["follows"])
            ):
                pairs.append((j, i))
    if follows and not info[i]["end_closer"]:
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
            elif info[j]["adj"] == "floating" and info[j]["end_closer"]:
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


# Punctuation a CLOSING quotation mark can sit against (word.' / word'. / word',).
CLOSING_PUNCT = set(".,!?;")


def _quotation_targets(text, transls, dict_cf):
    """High-confidence quotation rules over a whitespace-normalized ``text``.

    Returns the set of ' indices to rewrite to " (empty set if no rule fires).
    Designed for ZERO false positives: every rule is a narrow, guarded pattern,
    and anything not matching is assumed to be a glottal stop. It deliberately
    leaves genuine-but-unproven quotations as glottal (false negatives are fine
    and shrink as the dictionary grows).

    A ' "starts a word" = adjacency 'initial'; "ends a word" = adjacency 'final'.
    A word is "attested" if the whitespace token holding the ' is in the dict.
    First rule that fires wins, subject to the no-empty-quote guard.

      1. #TRANSL quotation marks (incl. Chinese) minus existing FORM " equals the
         count of word-initial + word-final ', and NONE of those words is
         attested -> all those ' are quotes.
      2. exactly one word-initial ' AND exactly one ' immediately following
         closing punctuation (. , ! ? ;).
      3. exactly one word-initial ' AND exactly one word-final ' immediately
         preceding closing punctuation, and that word-final word is not attested.
      4. exactly one word-initial ' that follows punctuation AND exactly one
         word-final ', and neither word is attested.
    """
    idx = [i for i, ch in enumerate(text) if ch == QUOTE]
    if not idx:
        return set()
    adj = {i: _adjacency(text, i) for i in idx}
    word_initial = [i for i in idx if adj[i] == "initial"]
    word_final = [i for i in idx if adj[i] == "final"]
    after_closing = [i for i in idx if i > 0 and text[i - 1] in CLOSING_PUNCT]
    wf_before_closing = [i for i in word_final
                         if i + 1 < len(text) and text[i + 1] in CLOSING_PUNCT]

    def attested(i):
        """Is the glottal WORD this ' belongs to attested? Uses the letter-run
        adjacent to the ' (initial: '+letters; final: letters+'), NOT the whole
        whitespace token -- so an opening quote glued to a word that ends in a
        real glottal (e.g. 'Mafana') doesn't hide that ``mafana'`` is attested.
        """
        if adj[i] == "initial":
            j = i + 1
            while j < len(text) and text[j].isalpha():
                j += 1
            word = text[i:j]
        elif adj[i] == "final":
            j = i - 1
            while j >= 0 and text[j].isalpha():
                j -= 1
            word = text[j + 1:i + 1]
        else:
            return False
        return word.casefold() in dict_cf

    def guarded(conv):
        """Return conv unless the rewrite would create an empty quotation -- two
        " back to back, separated only by whitespace, or abutting an existing "."""
        s = sorted(conv)
        for a, b in zip(s, s[1:]):
            if text[a + 1:b].strip() == "":
                return set()
        for i in conv:
            j = i + 1
            while j < len(text) and text[j] == " ":
                j += 1
            if j < len(text) and text[j] in FORM_DQUOTES:
                return set()
            j = i - 1
            while j >= 0 and text[j] == " ":
                j -= 1
            if j >= 0 and text[j] in FORM_DQUOTES:
                return set()
        return set(conv)

    se = sorted(set(word_initial) | set(word_final))
    tq = sum(ch in TRANSL_QUOTES for t in transls for ch in t)
    fq = sum(ch in FORM_DQUOTES for ch in text)
    # Rules 3-4 have ambiguous closers (word'. / word' are real word-final-glottal
    # patterns), so they only fire when the TRANSL carries at least one complete
    # quotation PAIR. A lone TRANSL quote (a quotation that spans sentence
    # boundaries) must not corroborate a same-sentence pair.
    transl_has_pair = (tq - fq) >= 2

    # Rule 1 -- TRANSL count matches start/end ', none attested. The ' must be
    # BALANCED (equal openers and closers): a real quotation has matched marks,
    # so a lone word-final glottal matching a single spanning TRANSL quote (odd
    # count) is not a quotation.
    if se and (tq - fq) == len(se) and len(word_initial) == len(word_final) \
            and all(not attested(i) for i in se):
        conv = guarded(set(se))
        if conv:
            return conv
    # Rule 2 -- one word-initial ' + one ' after closing punct (.' is unambiguous).
    if len(word_initial) == 1 and len(after_closing) == 1 \
            and word_initial[0] != after_closing[0]:
        conv = guarded({word_initial[0], after_closing[0]})
        if conv:
            return conv
    # Rule 3 -- one word-initial ' + one word-final ' before closing punct
    # (unattested); TRANSL-corroborated.
    if transl_has_pair and len(word_initial) == 1 and len(wf_before_closing) == 1 \
            and word_initial[0] != wf_before_closing[0] \
            and not attested(wf_before_closing[0]):
        conv = guarded({word_initial[0], wf_before_closing[0]})
        if conv:
            return conv
    # Rule 4 -- one word-initial ' after punct + one word-final ', neither
    # attested; TRANSL-corroborated.
    if transl_has_pair and len(word_initial) == 1 and _follows_punct(text, word_initial[0]) \
            and len(word_final) == 1 and word_initial[0] != word_final[0] \
            and not attested(word_initial[0]) and not attested(word_final[0]):
        conv = guarded({word_initial[0], word_final[0]})
        if conv:
            return conv
    return set()


def _destrand_for_quotation(text, transls, dict_cf):
    """If removing the whitespace on one side of a STRANDED ' lets a quotation
    rule fire, return (variant_text, converted_indices, [orig ' index]).
    Otherwise (text, empty set, []).

    A ' is stranded only when it has whitespace on BOTH sides -- a lone ',
    not one already attached to a word or to punctuation. This matters: a '
    glued to a comma (``tamdaw,' padamaay``) has whitespace on just one side;
    removing it would wrongly glue a closing quote to the next word.
    """
    for i, ch in enumerate(text):
        if ch != QUOTE:
            continue
        if not (0 < i < len(text) - 1 and text[i - 1] == " " and text[i + 1] == " "):
            continue
        for sp in (i - 1, i + 1):
            variant = text[:sp] + text[sp + 1:]
            conv = _quotation_targets(variant, transls, dict_cf)
            if conv:
                return variant, conv, [i]
    return text, set(), []


def apply_quote_corrections(form_text, transls, dictionary):
    """Rewrite ' -> " on the ORIGINAL tier only under the high-confidence
    quotation rules in ``_quotation_targets``; assume glottal otherwise.

    Whitespace is normalized first. Returns ``(new_text, corrected, stranded,
    ambiguous)`` (index lists into the normalized text):
      - corrected: ' rewritten to "
      - stranded:  a floating ' whose surrounding whitespace was removed so a
        rule could fire
      - ambiguous: ' left unchanged in a sentence whose TRANSL carries quotation
        marks we could not confidently place -- an audit flag, NOT an edit.

    Zero false positives by design: a TRANSL with no quotation marks suppresses
    all conversion, and every rule is narrowly guarded. Genuine but unproven
    quotations are deliberately left as glottal.
    """
    text = " ".join(form_text.split())
    if QUOTE not in text:
        return text, [], [], []
    dict_cf = _casefold_dict(dictionary)
    tq = sum(ch in TRANSL_QUOTES for t in transls for ch in t)
    # A TRANSL that carries no quotation confirms the sentence has none.
    quotation_allowed = not (transls and tq == 0)

    corrected, stranded, work = set(), [], text
    if quotation_allowed:
        conv = _quotation_targets(text, transls, dict_cf)
        if conv:
            work = text
        else:
            work, conv, stranded = _destrand_for_quotation(text, transls, dict_cf)
        if conv:
            chars = list(work)
            for i in conv:
                chars[i] = '"'
            work = "".join(chars)
            corrected = conv

    ambiguous = []
    if not corrected and tq > 0:
        ambiguous = [i for i, ch in enumerate(text) if ch == QUOTE]
    return work, sorted(corrected), stranded, ambiguous


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


def _sentence_records(path, lang):
    """Return [(original_form_text, [transl_texts])] for each S in a file of ``lang``."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return []
    if root.tag != "TEXT" or root.get(_LANG_ATTR) != lang:
        return []
    out = []
    for s in root.findall("S"):
        form_text = None
        for form in s.findall("FORM"):
            if form.get("kindOf") == "original" and form.text:
                form_text = " ".join("".join(form.itertext()).split())
                break
        if form_text is None:
            continue
        transls = []
        for tr in s.findall("TRANSL"):
            txt = "".join(tr.itertext())
            if txt and txt.strip():
                transls.append(txt)
        out.append((form_text, transls))
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
    parser.add_argument(
        "--dictionary", default=None,
        help="newline-delimited attestation word list; overrides the built-in "
             "single-word S-FORM dictionary",
    )
    args = parser.parse_args(argv)

    root = os.path.abspath(args.corpora_path)
    files = _find_lang_files(root, args.lang)
    print(f"Found {len(files)} files for lang={args.lang}", flush=True)

    # Parse each file ONCE; reuse for dictionary + classification.
    records = []  # (original_form_text, [transl_texts])
    for n, path in enumerate(files, 1):
        records.extend(_sentence_records(path, args.lang))
        if n % 500 == 0:
            print(f"  parsed {n}/{len(files)} files…", flush=True)
    all_forms = [f for (f, _tr) in records]

    if args.dictionary:
        with open(args.dictionary, encoding="utf-8") as fh:
            dictionary = {w.strip().casefold() for w in fh if w.strip()}
        print(f"Dictionary (from {args.dictionary}): {len(dictionary)} words", flush=True)
    else:
        dictionary = build_dictionary(all_forms)
        print(f"Dictionary: {len(dictionary)} single-word original FORMs", flush=True)

    counts = Counter()
    examples = defaultdict(list)
    n_sent = n_quote_sent = n_transl_pass = 0
    for form_text, transls in records:
        n_sent += 1
        if QUOTE not in form_text:
            continue
        n_quote_sent += 1
        # FIRST PASS: the translation confirms every ' is a glottal.
        if translation_confirms_glottal(form_text, transls):
            n_transl_pass += 1
            counts["GLOTTAL_TRANSL"] += form_text.count(QUOTE)
            if len(examples["GLOTTAL_TRANSL"]) < args.examples:
                examples["GLOTTAL_TRANSL"].append(form_text)
            continue
        # SECOND PASS: per-' pairing / dictionary classification.
        for _idx, label in classify(form_text, dictionary):
            counts[label] += 1
            if len(examples[label]) < args.examples and form_text not in examples[label]:
                examples[label].append(form_text)

    order = [
        "GLOTTAL_TRANSL", "GLOTTAL_INTERNAL", "GLOTTAL_BOUND_NO_MATCH",
        "GLOTTAL_PAIR", "STRANDED_GLOTTAL", "QUOTATION", "AMBIGUOUS",
    ]
    total = sum(counts.values())
    print(f"\nSentences: {n_sent} ({n_quote_sent} contain a '; "
          f"{n_transl_pass} resolved all-glottal by TRANSL first pass)")
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
