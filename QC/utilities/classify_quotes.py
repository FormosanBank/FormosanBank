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


def stranded_side(form_text, i, dictionary):
    """For a STRANDED_GLOTTAL ' at index ``i`` (into the whitespace-normalized
    text), return 'prev' or 'next' -- the side whose word becomes attested when
    the ' reattaches -- or None if not uniquely resolvable.
    """
    text = " ".join(form_text.split())
    dict_cf = _casefold_dict(dictionary)
    prev = nxt = None
    for s, e, tok in _token_spans(text):
        core = _strip_flanking_punct(tok)
        if not any(c.isalpha() for c in core):
            continue
        if e <= i:
            prev = core
        elif s > i and nxt is None:
            nxt = core
    cand = []
    if prev is not None and not prev.endswith(QUOTE) \
            and (prev + QUOTE).casefold() in dict_cf:
        cand.append("prev")
    if nxt is not None and not nxt.startswith(QUOTE) \
            and (QUOTE + nxt).casefold() in dict_cf:
        cand.append("next")
    return cand[0] if len(cand) == 1 else None


def _transl_quotation_targets(text, transls, dict_cf):
    """Guarded complementary rule: TRANSL quote marks matched by outermost FORM '.

    Returns the sorted list of ' indices to rewrite to " (empty if the rule does
    not fire). Fires only when: the S has TRANSL(s); (TRANSL quote-mark count −
    FORM " count) = need > 0 and even; there are >= need non-internal '
    candidates; and the outermost ``need`` of them do NOT sit in an attested
    token (the guard against genuine glottal-boundary words, e.g. 'ayam …
    faloco'). The outermost ``need`` candidates — the first need/2 and the last
    need/2 — are the quotation marks; middle candidates (word-final/initial
    glottals inside the quoted span) stay glottal.
    """
    if not transls:
        return []
    tq = sum(ch in TRANSL_QUOTES for t in transls for ch in t)
    fq = sum(ch in FORM_DQUOTES for ch in text)
    need = tq - fq
    if need <= 0 or need % 2:
        return []
    cands = [i for i, ch in enumerate(text)
             if ch == QUOTE and _adjacency(text, i) != "internal"]
    if len(cands) < need:
        return []
    k = need // 2
    chosen = cands[:k] + cands[-k:]
    spans = list(_token_spans(text))

    def token_at(i):
        for s, e, t in spans:
            if s <= i < e:
                return _strip_flanking_punct(t)
        return ""

    if any(token_at(i).casefold() in dict_cf for i in chosen):
        return []
    return sorted(chosen)


def apply_quote_corrections(form_text, transls, dictionary):
    """Decide each ' in an original-tier FORM and apply corrections.

    Whitespace is normalized (as ``classify`` does) first, so the returned text
    is single-spaced. Returns ``(new_text, corrected, stranded, ambiguous)``
    where the three lists hold indices into the NORMALIZED pre-correction text:
      - corrected: ' rewritten to " (QUOTATION)
      - stranded:  ' whose neighbouring space was removed to reattach a glottal
      - ambiguous: ' left in place, needs human review
    Glottal (internal / bound / pair) outcomes are left untouched and not
    reported. A TRANSL that confirms all-glottal short-circuits to no changes.

    Order of precedence:
      1. TRANSL confirms all-glottal -> no changes.
      2. Guarded TRANSL-count quotation rule -> when it fires, the outermost
         matched ' become ", every other ' is left glottal (this OVERRIDES the
         per-' classifier, whose pairing can misfire when the quoted span's
         boundary words themselves end in glottals).
      3. Otherwise, the per-' classifier (canonical `: '…'.` pairing etc.).
    """
    text = " ".join(form_text.split())
    if QUOTE not in text:
        return text, [], [], []
    if translation_confirms_glottal(text, transls):
        return text, [], [], []

    dict_cf = _casefold_dict(dictionary)
    transl_targets = _transl_quotation_targets(text, transls, dict_cf)
    if transl_targets:
        chars = list(text)
        for i in transl_targets:
            chars[i] = '"'
        return "".join(chars), transl_targets, [], []

    corrected, stranded, ambiguous = [], [], []
    delete = set()                      # space indices to drop (stranded repair)
    chars = list(text)
    for idx, label in classify(text, dictionary):
        if label == "QUOTATION":
            corrected.append(idx)
            chars[idx] = '"'
        elif label == "STRANDED_GLOTTAL":
            side = stranded_side(text, idx, dictionary)
            if side == "prev" and idx - 1 >= 0 and chars[idx - 1] == " ":
                delete.add(idx - 1)
                stranded.append(idx)
            elif side == "next" and idx + 1 < len(chars) and chars[idx + 1] == " ":
                delete.add(idx + 1)
                stranded.append(idx)
            else:
                ambiguous.append(idx)   # direction unresolved -> flag for review
        elif label == "AMBIGUOUS":
            ambiguous.append(idx)
    new_text = "".join(c for k, c in enumerate(chars) if k not in delete)
    return new_text, corrected, stranded, ambiguous


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
