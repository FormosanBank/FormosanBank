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
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.xml_forms import find_base_form  # noqa: E402

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


# A source whose quotation marks are a backtick/apostrophe pair (Blust's Thao
# Dictionary is the worked case) prints the same quotation in the Thao and in
# its English translation, so the translation is a witness for the FORM. Two
# things follow, and both are evidence the per-apostrophe classifier does not
# otherwise have.
OPENING_MARKS = "`\u2018\u201c"
CLOSING_MARKS = "\u2019\u201d"


def _closing_apostrophes(text: str, dict_cf: set | None = None) -> int:
    """Apostrophes used as a closing quotation mark, not as a letter.

    A closing mark follows a letter, digit or sentence punctuation and is not
    followed by a letter. A glottal-stop apostrophe can look identical at the
    end of a word, so when a dictionary is available the word is checked
    against it first: an attested `qriu'` is a glottal, not a closing mark.
    """
    total = 0
    for match in re.finditer(r"(?<=[\w.,;:?!])'(?![\w])", text):
        if dict_cf:
            start = match.start()
            while start > 0 and text[start - 1].isalpha():
                start -= 1
            word = text[start : match.start() + 1]
            if word and word.casefold() in dict_cf:
                continue
        total += 1
    return total


def quote_parity(form_text, transl_texts, dictionary=None):
    """Compare the quotation marks in a FORM with those in its translations.

    Returns a dict with the opener and closer counts on each side and a verdict:

    ``balanced``        both sides agree and each side's own marks pair up;
    ``form_unclosed``   the FORM opens a quotation it never closes -- the usual
                        cause is a quotation that runs past the sentence the
                        text was split at;
    ``form_unopened``   the FORM closes a quotation it never opened -- the same
                        cause, seen from the other end, or an apostrophe that is
                        really a glottal stop;
    ``transl_unopened`` the translation closes a quotation it never opened,
                        which in a scraped source usually means the opening
                        glyph is missing from the PDF's text layer;
    ``transl_unclosed`` the mirror of that;
    ``count_mismatch``  both sides are internally balanced but disagree on how
                        many quotations there are -- often a translator
                        splitting one quotation in two, so the weakest signal
                        of the six.

    ``dictionary`` is the language's attested single words, as ``classify``
    takes it; without one, a word-final glottal stop counts as a closing mark.

    It is deliberately a report and not a repair: which side is wrong is a
    judgement about the source, and the counts are what make it decidable.
    """
    transl_texts = list(transl_texts or [])
    # The dictionary applies to the FORM only: it is the Formosan language's
    # word list, and a translation is English.
    dict_cf = _casefold_dict(dictionary) if dictionary else None
    form_open = sum(ch in OPENING_MARKS for ch in form_text)
    form_close = sum(ch in CLOSING_MARKS for ch in form_text) + _closing_apostrophes(
        form_text, dict_cf
    )
    transl_open = sum(ch in OPENING_MARKS for t in transl_texts for ch in t)
    transl_close = sum(
        ch in CLOSING_MARKS for t in transl_texts for ch in t
    ) + sum(_closing_apostrophes(t) for t in transl_texts)

    if form_open == form_close == transl_open == transl_close:
        verdict = "balanced"
    elif form_open > form_close:
        verdict = "form_unclosed"
    elif form_close > form_open:
        verdict = "form_unopened"
    elif transl_open > transl_close:
        verdict = "transl_unclosed"
    elif transl_close > transl_open:
        verdict = "transl_unopened"
    else:
        verdict = "count_mismatch"
    return {
        "form_open": form_open,
        "form_close": form_close,
        "transl_open": transl_open,
        "transl_close": transl_close,
        "verdict": verdict,
    }


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

# A glottal stop stands next to a vowel in these languages: there a ' right
# before a consonant at the start of a word, or right after one at the end, is
# a prime candidate for a quotation mark -- unless the word is attested with
# that spelling (maintainer, 2026-10-14). Used only to choose among several
# candidates; the wrap rules ignore it.
CONSONANT_QUOTE_LANGUAGES = {"Saisiyat", "Saaroa", "Bunun", "Kanakanavu", "Paiwan", "Puyuma", "Rukai"}
VOWELS = set("aeiouəɨʉɘɜœæø")


def is_vowel(ch: str) -> bool:
    base = unicodedata.normalize("NFD", (ch or "").casefold())[:1]
    return base in VOWELS


def _quotation_targets(text, transls, dict_cf, fq_consumed=0, consonant_quotes=None):
    """High-confidence quotation rules over a whitespace-normalized ``text``.

    Returns the set of ' indices to rewrite to " (empty set if no rule fires).
    Designed for ZERO false positives: every rule is a narrow, guarded pattern,
    and anything not matching is assumed to be a glottal stop. It deliberately
    leaves genuine-but-unproven quotations as glottal (false negatives are fine
    and shrink as the dictionary grows).

    A ' "starts a word" = adjacency 'initial'; "ends a word" = adjacency 'final'.
    A word is "attested" if the glottal word the ' belongs to is in the dict,
    looked up whole and by its one-sided forms (``word_forms``). First rule that
    fires wins, subject to the no-empty-quote guard. In every rule the opening
    quote must come before the closing one.

      1. #TRANSL quotation marks (incl. Chinese) minus existing FORM " (less any
         a wrap rule consumed) equals the count of word-initial + word-final ',
         they alternate opening/closing, and NONE of those words is attested ->
         all those ' are quotes. With ``consonant_quotes`` set and MORE such '
         than the count, the consonant-adjacent unattested ones are taken when
         they alone match it.
      2. exactly one word-initial ' AND exactly one ' immediately following
         closing punctuation (. , ! ? ;).
      3. exactly one word-initial ' AND exactly one word-final ' immediately
         preceding closing punctuation, neither word attested.
      4. exactly one word-initial ' that follows punctuation AND exactly one
         word-final ', and neither word is attested.
    Rules 2-4 need exactly one candidate on each side; with ``consonant_quotes``
    set (CONSONANT_QUOTE_LANGUAGES), several candidates of which exactly one is
    consonant-adjacent and unattested narrow to that one.
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

    def word_forms(i):
        """The spellings under which the glottal WORD this ' belongs to is looked up.

        The word is the run of letters, apostrophes and word-internal marks
        around the ' (``WORD_MARKS``). Looked up whole, and also without the
        apostrophe at its far edge -- so an opening quote glued to a word that
        ends in a real glottal ('Mafana') doesn't hide that ``mafana'`` is
        attested, and a word with a glottal at both edges (``'aehoe'``) or
        inside (``'a'aynaa'``) is found as itself (maintainer, 2026-10-14: the
        list includes words that begin and end in a single quote; the old
        one-sided lookup could never match them).
        """
        if adj[i] not in ("initial", "final"):
            return set()
        a = i
        while a > 0 and (text[a - 1].isalpha() or text[a - 1] in WORD_MARKS):
            a -= 1
        b = i + 1
        while b < len(text) and (text[b].isalpha() or text[b] in WORD_MARKS):
            b += 1
        word = text[a:b].strip(":-~^")
        cands = {word}
        if adj[i] == "initial" and word.endswith(QUOTE):
            cands.add(word[:-1])
        if adj[i] == "final" and word.startswith(QUOTE):
            cands.add(word[1:])
        # The letters on the apostrophe's own side, as before: kept so the
        # lookup only ever finds MORE words than it used to ('ta'enengan still
        # matches 'ta, k'yaba' still matches yaba').
        if adj[i] == "initial":
            j = i + 1
            while j < len(text) and text[j].isalpha():
                j += 1
            cands.add(text[i:j])
        else:
            j = i - 1
            while j >= 0 and text[j].isalpha():
                j -= 1
            cands.add(text[j + 1:i + 1])
        return cands

    def attested(i):
        cands = word_forms(i)
        return bool(cands) and any(c.casefold() in dict_cf for c in cands)

    def prime(i):
        """' next to a consonant (initial: before one; final: after one), the
        word not attested with that spelling."""
        if adj[i] == "initial":
            nb = text[i + 1] if i + 1 < len(text) else ""
        elif adj[i] == "final":
            nb = text[i - 1] if i else ""
        else:
            return False
        if not (_is_letter(nb) and not is_vowel(nb)):
            return False
        cands = {c.casefold() for c in word_forms(i)}
        return not (cands & dict_cf) and not (cands & consonant_quotes)

    def narrowed(cands):
        """Several candidates, exactly one of them prime -> that one. Otherwise
        the candidates are left as they are (maintainer, 2026-10-14: the
        consonant preference only decides between candidates)."""
        if consonant_quotes is None or len(cands) <= 1:
            return cands
        p = [i for i in cands if prime(i)]
        return p if len(p) == 1 else cands

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
    # FORM double quotes that a wrap rule has already paired with consumed
    # translation quotes are not counted again.
    fq = sum(ch in FORM_DQUOTES for ch in text) - fq_consumed
    # Rules 3-4 have ambiguous closers (word'. / word' are real word-final-glottal
    # patterns), so they only fire when the TRANSL carries at least one complete
    # quotation PAIR. A lone TRANSL quote (a quotation that spans sentence
    # boundaries) must not corroborate a same-sentence pair.
    transl_has_pair = (tq - fq) >= 2

    # Rule 1 -- TRANSL count matches start/end ', none attested. The ' must be
    # BALANCED (equal openers and closers): a real quotation has matched marks,
    # so a lone word-final glottal matching a single spanning TRANSL quote (odd
    # count) is not a quotation.
    # ... and in order: opening, closing, opening, closing (2026-10-14).
    alternates = all(adj[i] == ("initial" if n % 2 == 0 else "final") for n, i in enumerate(se))
    if se and (tq - fq) == len(se) and len(word_initial) == len(word_final) and alternates \
            and all(not attested(i) for i in se):
        conv = guarded(set(se))
        if conv:
            return conv
    # ... and when there are more start/end ' than TRANSL quotes, the prime ones
    # (consonant-adjacent, unattested), if they alone match the count.
    if consonant_quotes is not None and se and len(se) > (tq - fq) > 0:
        pse = [i for i in se if prime(i)]
        if len(pse) == (tq - fq) \
                and all(adj[i] == ("initial" if n % 2 == 0 else "final") for n, i in enumerate(pse)):
            conv = guarded(set(pse))
            if conv:
                return conv
    word_initial = narrowed(word_initial)
    word_final = narrowed(word_final)
    wf_before_closing = narrowed(wf_before_closing)
    # Rule 2 -- one word-initial ' + one ' after closing punct (.' is unambiguous).
    if len(word_initial) == 1 and len(after_closing) == 1 \
            and word_initial[0] < after_closing[0]:
        conv = guarded({word_initial[0], after_closing[0]})
        if conv:
            return conv
    # Rule 3 -- one word-initial ' + one word-final ' before closing punct
    # (unattested); TRANSL-corroborated.
    # The opening quote must come before the closing one, and the opening word
    # is checked against the list too (2026-10-14: rule 3 paired kamamwai' with
    # a LATER 'iniya'om, which is on the Saisiyat list, and never looked it up).
    if transl_has_pair and len(word_initial) == 1 and len(wf_before_closing) == 1 \
            and word_initial[0] < wf_before_closing[0] \
            and not attested(word_initial[0]) and not attested(wf_before_closing[0]):
        conv = guarded({word_initial[0], wf_before_closing[0]})
        if conv:
            return conv
    # Rule 4 -- one word-initial ' after punct + one word-final ', neither
    # attested; TRANSL-corroborated.
    if transl_has_pair and len(word_initial) == 1 and _follows_punct(text, word_initial[0]) \
            and len(word_final) == 1 and word_initial[0] < word_final[0] \
            and not attested(word_initial[0]) and not attested(word_final[0]):
        conv = guarded({word_initial[0], word_final[0]})
        if conv:
            return conv
    return set()


def _destrand_for_quotation(text, transls, dict_cf, fq_consumed=0, consonant_quotes=None):
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
            conv = _quotation_targets(variant, transls, dict_cf, fq_consumed, consonant_quotes)
            if conv:
                return variant, conv, [i]
    return text, set(), []


# Word-internal marks a Formosan word may carry besides letters and the
# apostrophe (Saisiyat's length colon, the Bunun/Thao hyphen, the reduplication
# tilde, Sakizaya's circumflex); mirrors build_attestation_dict.ALLOWED_MARKS.
WORD_MARKS = set("':-~^")
# Sentence-final punctuation a wrapping quote may stand before or after.
SENTENCE_FINAL = set(".!?。！？…")
_QUOTE_FAMILIES = ({'"', "“", "”", "＂"}, {"「", "」"}, {"『", "』"})
_OPENERS = {'"', "“", "＂", "「", "『"}
_CLOSERS = {'"', "”", "＂", "」", "』"}


def _wrapping_close(s, open_set, close_set):
    """Index of the quote that closes a quote at s[0], when that pair wraps the
    whole string -- the closing quote may stand before or after sentence-final
    punctuation. None otherwise."""
    if len(s) < 2 or s[0] not in open_set:
        return None
    k = len(s) - 1
    while k > 0 and s[k] in SENTENCE_FINAL:
        k -= 1
    if k <= 0 or s[k] not in close_set:
        return None
    return k


def transl_wrap(t):
    """(open, close) indices of quotation marks that wrap a translation whole, or
    None. The pair must belong together: no quote of the same family between
    them that would close the first one early ("A" and "B" is two quotations).
    A straight quote cannot nest, so any straight quote inside disqualifies it;
    curly and corner quotes are matched as brackets."""
    s = t.strip()
    k = _wrapping_close(s, _OPENERS, _CLOSERS)
    if k is None:
        return None
    lead = len(t) - len(t.lstrip())
    fam = next(f for f in _QUOTE_FAMILIES if s[0] in f)
    if s[k] not in fam:
        return None
    if s[0] in ('"', "＂"):
        if any(ch in ('"', "＂") for ch in s[1:k]):
            return None
    else:
        depth = 0
        for j, ch in enumerate(s[:k + 1]):
            if ch in fam and ch in _OPENERS:
                depth += 1
            elif ch in fam and ch in _CLOSERS:
                depth -= 1
                if depth == 0 and j != k:
                    return None
    return lead, lead + k


def wrap_rules(text, transls):
    """The two wrap rules (maintainer, 2026-10-14), applied before every other
    rule except the '' pairs. Returns (indices of ' to rewrite to ",
    consumed-quote-stripped translations, FORM double quotes consumed, stop).

    1. A translation wrapped whole in quotation marks, and an utterance wrapped
       whole in single quotes (each closing quote before or after
       sentence-final punctuation): the two single quotes become double quotes.
    2. The same, with the utterance wrapped in double quotes: nothing changes in
       the utterance.
    3. (Addendum) The translation wrapped, the utterance not: nothing changes in
       the utterance.
    In every case the translation-wrapping quotes are consumed: they no longer
    count as evidence for any further ' -> ". If no other quotation mark is left
    in the translations, the sentence is finished.
    """
    wraps = [transl_wrap(t) for t in transls]
    if not any(wraps):
        return set(), transls, 0, False
    conv, fq_consumed = set(), 0
    k = _wrapping_close(text, {QUOTE}, {QUOTE})
    if k is not None:
        conv = {0, k}
        fq_consumed = 2
    else:
        k = _wrapping_close(text, FORM_DQUOTES, FORM_DQUOTES)
        # Addendum (maintainer, 2026-10-14): "If the translation is wrapped by
        # quotes and the utterance is not, the translation-wrapping quotes are
        # consumed anyway. They are not considered evidence of a quote."
        fq_consumed = 2 if k is not None else 0
    stripped = []
    for t, w in zip(transls, wraps):
        if w:
            a, b = w
            t = t[:a] + t[a + 1:b] + t[b + 1:]
        stripped.append(_single_quote_pairs_as_double(t))
    left = sum(ch in TRANSL_QUOTES for t in stripped for ch in t)
    return conv, stripped, fq_consumed, left == 0


def _single_quote_pairs_as_double(t):
    """A translation's own quotations written in single quotes ('Yes,' inside
    "... say 'Yes,' in reply.") count as translation-internal quotes once the
    wrapping pair is consumed. Elsewhere the cleaner never reads ' in a
    translation as a quotation mark (it's, dogs'), so only a pair counts: an
    opening ' or ‘ at the start of a word, closed by a later ' or ’ that ends a
    word or follows punctuation. Returns a copy with those pairs written as ",
    used for counting only -- the translation itself is never rewritten."""
    chars, opener = list(t), None
    for i, ch in enumerate(t):
        left = t[i - 1] if i else " "
        right = t[i + 1] if i + 1 < len(t) else " "
        if ch in ("'", "‘") and (left.isspace() or left in '(["“') and right.isalnum():
            opener = i
        elif ch in ("'", "’") and opener is not None and not (left.isalnum() and right.isalnum()) \
                and (right.isspace() or right in '.,;:!?)]"”' or i + 1 == len(t)):
            chars[opener] = chars[i] = '"'
            opener = None
    return "".join(chars)


_DQ_OPEN_BEFORE = set("([{“「『\"")
_DQ_CLOSE_AFTER = set(".,;:!?)]}”」』\"…")


def _double_apostrophe_pairs(text):
    """Two apostrophes typed for a double quotation mark (ePark Atayal
    ``''tlubuw ... rgyax''``). Maintainer, 2026-10-14: "If there is a `''` and a
    matching `''` in the same utterance, they can be converted to "s."

    Only a run of exactly two apostrophes counts; a run of three is not one. An
    opening '' starts a word (start of text, a space or an opening bracket/quote
    before it, a letter or digit after it); a closing '' ends one (a non-space
    before it, the end of text, a space or closing punctuation after it). The
    match of an opening '' is the NEXT '' in the utterance, whatever its shape:
    it must be a closing one, or nothing is converted -- so ''maylunsan''han ...
    lutuk''maylunsan'' (each mark glued to a neighbouring word) never pairs the
    first opening with the last closing across a paragraph. '' between two
    letters (Saisiyat ``kamatortoroe''omaling'``) neither opens nor closes.
    Returns the rewritten text and the indices of the new " in it."""
    runs, i = [], 0
    while i < len(text):
        if text[i] == QUOTE:
            j = i
            while j < len(text) and text[j] == QUOTE:
                j += 1
            if j - i == 2:
                before = text[i - 1] if i else " "
                after = text[j] if j < len(text) else " "
                opens = (before.isspace() or before in _DQ_OPEN_BEFORE) and after.isalnum()
                closes = (after.isspace() or after in _DQ_CLOSE_AFTER) and not before.isspace()
                runs.append((i, "open" if opens and not closes else "close" if closes and not opens else None))
            i = j
        else:
            i += 1
    pairs, k = [], 0
    while k + 1 < len(runs):
        if runs[k][1] == "open" and runs[k + 1][1] == "close":
            pairs.append((runs[k][0], runs[k + 1][0]))
            k += 2
        else:
            k += 1
    if not pairs:
        return text, set()
    starts = {i for pair in pairs for i in pair}
    out, new_idx, i = [], set(), 0
    while i < len(text):
        if i in starts:
            new_idx.add(len(out))
            out.append('"')
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out), new_idx


def apply_quote_corrections(form_text, transls, dictionary, consonant_quotes=None):
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
    if consonant_quotes is not None:
        consonant_quotes = _casefold_dict(consonant_quotes)

    # '' ... '' pairs come first: they are double quotation marks already.
    text, dq_conv = _double_apostrophe_pairs(text)

    # Then the wrap rules; they may rewrite the utterance's wrapping
    # single quotes and consume the translations' wrapping quotes.
    wrap_conv, transls, fq_consumed, stop = wrap_rules(text, list(transls))
    if wrap_conv:
        chars = list(text)
        for i in wrap_conv:
            chars[i] = '"'
        text = "".join(chars)
    if stop or QUOTE not in text:
        return text, sorted(dq_conv | wrap_conv), [], []

    tq = sum(ch in TRANSL_QUOTES for t in transls for ch in t)
    # A TRANSL that carries no quotation confirms the sentence has none.
    quotation_allowed = not (transls and tq == 0)

    corrected, stranded, work = dq_conv | set(wrap_conv), [], text
    if quotation_allowed:
        conv = _quotation_targets(text, transls, dict_cf, fq_consumed, consonant_quotes)
        if conv:
            work = text
        else:
            work, conv, stranded = _destrand_for_quotation(text, transls, dict_cf, fq_consumed,
                                                           consonant_quotes)
        if conv:
            chars = list(work)
            for i in conv:
                chars[i] = '"'
            work = "".join(chars)
            corrected |= conv

    ambiguous = []
    if not (corrected - set(wrap_conv) - dq_conv) and tq > 0:
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
        # The original tier's BASE: a POL-028 ver="alt" variant is a second
        # reading, and classifying its quotes would attribute them to the
        # sentence as though the base had said them.
        form = find_base_form(s, "original")
        if form is None or not form.text:
            continue
        form_text = " ".join("".join(form.itertext()).split())
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
