"""utils.py – Shared utilities for the Formosan Bank XML parse scripts.

Functions
---------
strip_prosodic_markers(text)
    Strip prosodic and annotation markers (``^``, ``\\``, ``(H)``, etc.)
    from a raw form or ori token.  Call before any other processing.

clean_punctuation(text)
    Normalise full-width / curly punctuation to ASCII equivalents.

extract_notes(text)
    Remove parenthetical commentary from a translation string and
    return it separately as a notes string.

add_transl_element(parent, lang, text)
    Create a <TRANSL> child element, hoisting any parenthetical
    commentary into a ``notes`` attribute.

expand_infixes(form, en_gloss, zh_gloss)
    If *form* contains infix notation ``<xyz>``, split it into a list
    of ``(form, en, zh)`` sub-morpheme tuples — one per infix plus one
    for the remaining base — so each can become its own ``<M>`` element.
"""

import re
import xml.etree.ElementTree as ET

# Matches a whitespace-delimited token that is entirely uppercase X's,
# used to normalize unintelligible-speech markers (X, XX, XXXX…) to XXXX.
_XXXX_TOKEN_RE = re.compile(r'(?<!\S)X+(?!\S)')

# Matches code-switching bracket markers used in the NTU corpus:
#   <L2M  – opening tag (sometimes <L2E, <L2J, etc.)
#   L2M>  – closing tag
_L2M_RE = re.compile(r'<L2[A-Za-z]|L2[A-Za-z]>')

# Matches infix morpheme notation: <n>, <m>, <PF.PFV>, etc.
# Angle-bracket spans whose content is NOT an L2 code-switch marker.
_INFIX_RE = re.compile(r'<([^>]+)>')

# Matches prosodic and annotation markers that must be stripped from form
# strings and ori tokens before any other processing.  Longer / more-specific
# patterns must precede the single-character fallbacks in the alternation.
_PROSODIC_MARKER_RE = re.compile(
    r'\(H(?:x)?\)'          # (H) or (Hx)  aspiration / breath group
    r'|\(\d+(?:\.\d+)?\)'   # (N) or (N.M) pause duration in seconds
    r'|/\\'                  # /\  prosodic boundary
    r'|\\/'                  # \/  prosodic boundary
    r'|<[@Y|X]'              # <@  <Y  <|  <X   annotation span openers
    r'|[@Y|X]>'              # @>  Y>  |>  X>   annotation span closers
    r'|<WH'                  # <WH  whisper span opener
    r'|WH>'                  # WH>  whisper span closer
    r'|--'                   # --  double-dash break marker
    r'|[\\^@`;_|&:\[\]]'    # single-char markers: \ ^ @ ` ; _ | & : [ ]
    r'|…'                   # U+2026 HORIZONTAL ELLIPSIS
    r'|\((?:CAUGH(?:ING)?|COUGH(?:ING|S)?|THROAT|THRAOT|TSK|IHI|HICCUPING)\)'  # vocal noises
)


def strip_prosodic_markers(text):
    """Strip prosodic and annotation markers from a raw form or ori token.

    These markers are transcription conventions, not part of the language
    form itself.  Call this before any other processing — parenthesis
    handlers, L2-tag strippers, etc. — so that paren-wrapped markers such
    as ``(H)`` or ``(0.8)`` are never mis-identified as editorial insertions.

    Markers stripped
    ----------------
    ``(H)`` ``(Hx)``                aspiration / breath group
    ``(N)`` ``(N.M)``               pause duration, e.g. ``(0.8)``, ``(1.1)``
    ``/\\`` ``\\/``                 prosodic boundary sequences
    ``<@`` ``@>``                   annotation span
    ``<Y`` ``Y>``                   annotation span
    ``<|`` ``|>``                   annotation span
    ``<X`` ``X>``                   uncertain-text span (content is kept)
    ``<WH`` ``WH>``                 whisper span (content is kept)
    ``(COUGH)`` ``(THROAT)`` etc.   vocal-noise tokens (whole token removed)
    ``--``                          double-dash break marker
    ``\\ ^ @ ` ; _ | & : [ ]``     individual annotation characters
    """
    return _PROSODIC_MARKER_RE.sub('', text)


def strip_l2m(form):
    """Strip NTU code-switching markers from a word FORM string.

    Markers look like ``<L2Mword`` (opening) or ``wordL2M>`` (closing) or
    the fully wrapped ``<L2MwordL2M>``.  The letter after ``L2`` varies
    (M for Mandarin, E for English, J for Japanese, etc.).

    Parameters
    ----------
    form : str
        The raw word form string, possibly containing L2M markers.

    Returns
    -------
    clean : str
        The form with all L2M markers removed.
    is_code_switch : bool
        True if any marker was found and stripped.
    """
    if _L2M_RE.search(form):
        return _L2M_RE.sub('', form), True
    return form, False

# W FORM values that are known to be omitted from the sentence surface string
# and must be inserted when a count mismatch is detected.
#   XXXX – unintelligible speech marker
#   ye   – Seediq discourse particle
#   ay   – Saisiyat sentence-final particle
#   a    – common Formosan linker/particle
_INSERTABLE_TOKENS = frozenset({'XXXX', 'ye', 'ay', 'a'})


def insert_xxxx_tokens(ori, words):
    """Insert missing particle/marker tokens into the sentence FORM string
    wherever a W element has a known-omissible FORM but no corresponding
    token exists in the surface text.

    Known-omissible tokens: XXXX (unintelligible speech), ye (Seediq),
    ay (Saisiyat), a (common linker/particle).

    Only acts when the number of whitespace-delimited tokens in *ori* is
    strictly less than len(*words*), and only when at least one W FORM is
    in ``_INSERTABLE_TOKENS``.

    Parameters
    ----------
    ori : str
        The sentence surface-form string (already cleaned/joined).
    words : list
        The list of word entries for this sentence (each entry is a list
        whose first element is the W FORM string).

    Returns
    -------
    str
        The (possibly modified) sentence FORM string.
    """
    tokens = ori.split()
    n_s = len(tokens)
    n_w = len(words)

    if n_s >= n_w:
        return ori  # counts match (or more surface tokens) — nothing to do

    # Count how many times each insertable token appears in the W list and
    # in the surface.  Only token types where the W list has a surplus over
    # the surface are candidates for insertion — if the surface already
    # contains as many 'ye's (etc.) as the Ws do, that token is not missing.
    w_type_counts: dict = {}
    for w in words:
        if w[0] in _INSERTABLE_TOKENS:
            w_type_counts[w[0]] = w_type_counts.get(w[0], 0) + 1

    surface_type_counts: dict = {}
    for tok in tokens:
        if tok in _INSERTABLE_TOKENS:
            surface_type_counts[tok] = surface_type_counts.get(tok, 0) + 1

    # Collect (w_index, form) only for token types that are genuinely under-
    # represented in the surface relative to the W list.
    insertable = [
        (i, w[0]) for i, w in enumerate(words)
        if w[0] in _INSERTABLE_TOKENS
        and surface_type_counts.get(w[0], 0) < w_type_counts.get(w[0], 0)
    ]
    if not insertable:
        return ori  # mismatch but no deficit of known-omissible tokens

    # Insert each token at its W index position.
    # Insertion math: for each prior insertion the list grows by 1 and the
    # target index also grows by 1 — they cancel, so w_idx is always correct.
    for w_idx, form in insertable:
        pos = min(w_idx, len(tokens))
        if pos < len(tokens) and tokens[pos] == form:
            continue  # token already present at this position — skip
        tokens.insert(pos, form)
        if len(tokens) >= n_w:
            break  # stop once counts are balanced

    return ' '.join(tokens)

# Regex that identifies speaker-role labels (Q&A labels, conversation participants).
# Pattern: one or two uppercase letters followed by a colon, e.g. A:, B:, Q:, R:, M:, SP:.
# These tokens always have empty glosses; lowercase colon-tokens (o:, i:, so:) are
# genuine discourse markers with glosses and must NOT be suppressed.
_SPEAKER_TOKEN_RE = re.compile(r'^[A-Z]{1,2}:$')

# Matches inline speaker labels inside free-translation strings, e.g. "A: " or "B: ".
# These appear at the start of a string or after a sentence boundary punctuation + space.
_INLINE_SPEAKER_LABEL_RE = re.compile(r'(?:^|(?<=\s))([A-Z]{1,2}):\s*')


def strip_speaker_labels_from_translation(text: str) -> str:
    """Remove inline speaker-role labels (e.g. ``A:``, ``B:``, ``Q:``) from a
    free-translation string, preserving the actual content.

    For example::

        "A: Have you been to Namasia? B: No."
        → "Have you been to Namasia? No."

        "A: 你去過那瑪夏嗎？ B: 沒有。"
        → "你去過那瑪夏嗎？ 沒有。"

    Only strips labels that are one or two uppercase letters followed by a
    colon and a space, so abbreviations mid-sentence are not affected.
    """
    return _INLINE_SPEAKER_LABEL_RE.sub('', text).strip()


def is_speaker_token(form: str, zh: str = '', en: str = '') -> bool:
    """Return True when *form* is a speaker-role label that should be suppressed.

    A token is a speaker label when it matches the pattern ``[A-Z]{1,2}:`` AND
    both gloss columns are empty (or absent).  Passing zh/en is optional – when
    they are supplied the empty-gloss guard is applied here as well.
    """
    if not _SPEAKER_TOKEN_RE.match(form):
        return False
    if zh or en:
        return False   # has a gloss → not a bare speaker label
    return True

# Legacy set kept for any callers that still use ``t in SPEAKER_TOKENS``.
# Prefer is_speaker_token() for new code.
SPEAKER_TOKENS = {'Q:', 'A:', 'B:', 'R:', 'C:', 'D:', 'F:', 'G:', 'H:', 'I:', 'K:',
                  'M:', 'N:', 'O:', 'P:', 'S:', 'T:', 'U:', 'W:', 'Y:'}

# Matches a token that is entirely wrapped in parentheses, e.g. '(So)', '(i)', '(mesa),'.
# Used to detect annotation insertions that have no corresponding gloss entry (pattern 1).
PAREN_TOKEN_RE = re.compile(r'^\([^)]+\)[,!?.]?$')

# Matches a form or token that contains an ungrammatical parenthetical:
#   *(text)  – asterisk before a parenthesised word
#   (*text)  – parenthesised word beginning with asterisk
# These mark material that should be silently removed from the FORM and from
# the word list (no <W> element is emitted).  The match is done anywhere in
# the string so that combined forms like '(na)(*sua)' are also caught.
UNGRAMMATICAL_PAREN_RE = re.compile(r'\*\([^)]*\)|\(\*[^)]*\)')


def _drop_starred_slash(tok):
    """If *tok* contains slash-separated alternatives and any start with ``*``,
    drop those alternatives and return the remaining non-starred one.

    Returns the original token unchanged when it contains no slash, or when
    none of the slash-parts start with ``*``.  Returns ``None`` when ALL
    alternatives start with ``*`` (the whole token is ungrammatical and the
    caller should drop it entirely).

    Examples
    --------
    ``'patuelre/*makanaelre'`` → ``'patuelre'``
    ``'*tu-a-/ma-auvagavagay'`` → ``'ma-auvagavagay'``
    ``'*bad/*alsoBad'``         → ``None``
    """
    if not tok or '/' not in tok:
        return tok
    parts = tok.split('/')
    good = [p for p in parts if not p.startswith('*')]
    if len(good) == len(parts):
        return tok          # no starred alternatives — nothing to do
    return good[0] if good else None   # None → whole token is ungrammatical


# Matched quote-pair groups.  All characters in a group are treated as the
# same "quote type" for parity counting purposes, so that e.g. a curly open
# quote " and curly close quote " are counted together.  The nth standalone
# quote-only token of a given group (0-based) is an opener if n is even, a
# closer if n is odd — regardless of which character was actually used.
# This means that even mis-typed curly quotes are handled correctly by
# context (is there already an open quote earlier in the sentence?) rather
# than by blindly trusting the visual direction of the glyph.
_QUOTE_GROUPS = [
    frozenset('"\u201c\u201d'),   # straight " + curly " "
    # Note: single quotes (' \u2018 \u2019) are intentionally absent —
    # they are script characters in Formosan languages (glottal stops etc.)
    # and are exempt from punct-only classification entirely, so they never
    # reach the quote-direction logic in join_ori_tokens.
    frozenset('\u300c\u300d'),    # 「 」
    frozenset('\u300e\u300f'),    # 『 』
    frozenset('\u00ab\u00bb'),    # « »
]


def _quote_group(token):
    """Return the group index for a quote-only token, or -1 if not a quote."""
    chars = set(token)
    for i, grp in enumerate(_QUOTE_GROUPS):
        if chars <= grp:          # every char in the token belongs to this group
            return i
    return -1


def join_ori_tokens(tokens):
    """Join ori tokens into a FORM string, attaching punct-only tokens
    directly to an adjacent word token without an intervening space.

    Attachment direction for standalone quote-only tokens is determined by
    **parity of prior occurrences** of the same quote group within the same
    sentence:
    - Even count seen so far (0, 2, …) → opener → attach FORWARD to the
      following word token.
    - Odd count (1, 3, …) → closer → attach BACKWARD to the preceding token.

    This correctly handles both well-formed curly pairs (``" … "``) and
    mis-typed ones (e.g. two open curly quotes used as a pair), because the
    decision is based on whether a matching opener has already been seen rather
    than on the visual direction of the glyph.

    All other punct-only tokens (commas, periods, ``??``, etc.) attach
    backward to the preceding token unconditionally.

    This keeps the whitespace-separated word count in <FORM> in sync with
    the number of <W> elements (which also omit punct-only entries).
    """
    # Pre-scan: decide forward/backward for every token in one pass.
    quote_group_counts = {}   # group_index → number of quote tokens seen so far
    directions = []           # 'forward', 'backward', or None (non-punct word)

    for t in tokens:
        if not is_punct_only(t):
            directions.append(None)
            continue
        grp = _quote_group(t)
        if grp >= 0:
            # Quote-only punct: use parity to decide direction.
            count = quote_group_counts.get(grp, 0)
            directions.append('forward' if count % 2 == 0 else 'backward')
            quote_group_counts[grp] = count + 1
        else:
            # Non-quote punct (comma, period, ??, …): always attach backward.
            directions.append('backward')

    # Second pass: build the joined string using the pre-computed directions.
    parts = []
    pending_prefix = ''   # quote opener waiting to prepend to the next word

    for t, direction in zip(tokens, directions):
        if direction == 'forward':
            pending_prefix += t
        elif direction == 'backward':
            if parts:
                parts[-1] += t
            else:
                # Nothing precedes yet — defer to the next word as a prefix.
                pending_prefix += t
        else:
            parts.append(pending_prefix + t)
            pending_prefix = ''

    # Flush any trailing prefix (e.g. an opener with no following word).
    if pending_prefix:
        if parts:
            parts[-1] += pending_prefix
        else:
            parts.append(pending_prefix)

    return ' '.join(parts)


def _norm_paren(s):
    """Normalise a paren-wrapped token or gloss form for membership comparison.

    Strips trailing punctuation, outer parentheses, and morpheme-boundary
    hyphens so that ori token ``(ngipalay).`` correctly matches gloss form
    ``(ngi-palay).``, and ori token ``(i)`` matches gloss form ``i``.
    """
    s = re.sub(r'[,!?.]$', '', s)   # strip trailing punct
    s = re.sub(r'^\(|\)$', '', s)   # strip outer parens
    s = s.replace('-', '')           # strip morpheme boundaries
    return s

# Matches a string that contains at least one letter or digit (i.e. is not purely punctuation).
_HAS_ALNUM_RE = re.compile(r'[^\W_]', re.UNICODE)

# Single-quote-like characters that function as script markers (glottal stops,
# laryngeals, etc.) in Formosan and other languages.  A token composed entirely
# of these characters must NOT be classified as punctuation-only, because it may
# carry phonological content that cannot be resolved automatically.
_SINGLE_QUOTE_CHARS = frozenset(
    "'"        # U+0027 ASCII apostrophe
    '`'        # U+0060 grave accent / backtick
    '\u2018'   # U+2018 LEFT SINGLE QUOTATION MARK  '
    '\u2019'   # U+2019 RIGHT SINGLE QUOTATION MARK '
    '\u02bc'   # U+02BC MODIFIER LETTER APOSTROPHE  ʼ
    '\u02bb'   # U+02BB MODIFIER LETTER TURNED COMMA ʻ
    '\u00b4'   # U+00B4 ACUTE ACCENT                ´
    '\u02be'   # U+02BE MODIFIER LETTER RIGHT HALF RING ʾ
    '\u02bf'   # U+02BF MODIFIER LETTER LEFT HALF RING  ʿ
    '\u2032'   # U+2032 PRIME                        ′
)


def is_punct_only(form):
    """Return True if *form* consists entirely of punctuation / whitespace.

    Exception: tokens composed *entirely* of single-quote-like characters
    (apostrophe, modifier-letter apostrophe, grave accent, etc.) are NOT
    treated as punctuation.  These characters function as glottal-stop or
    laryngeal markers in Formosan scripts and cannot be handled automatically.

    Mixed tokens such as ``?'`` (question mark + apostrophe) still count as
    punctuation-only and will be attached to an adjacent word by
    ``join_ori_tokens``.
    """
    s = form or ""
    if not s:
        return True
    if _HAS_ALNUM_RE.search(s):
        return False  # contains a letter or digit — definitely not punct-only
    # No alnum: exempt only if EVERY character is a single-quote script marker.
    if all(c in _SINGLE_QUOTE_CHARS for c in s):
        return False
    return True


_PN_GLOSS_VALUES = {'人名', 'PN'}


def fill_propername_gloss(words: list, col_zh: int, col_en: int) -> None:
    """In-place: if a word has empty glosses, starts with a capital letter,
    and its immediate predecessor also starts with a capital letter whose
    gloss is '人名' or 'PN', fill the empty gloss with '人名' (zh) and 'PN' (en).

    This handles consecutive proper-name tokens where the second token was
    left unglossed in the source (e.g. "Pani Kanapaniana." or "Ka'angena Paicʉ.").
    """
    max_col = max(col_zh, col_en)
    for i in range(1, len(words)):
        w = words[i]
        w_prev = words[i - 1]
        if len(w) <= max_col or len(w_prev) <= max_col:
            continue
        zh = w[col_zh]
        en = w[col_en]
        # Current word must have empty glosses in both columns
        if (zh and zh.strip() not in ('', '_')) or (en and en.strip() not in ('', '_')):
            continue
        # Current form must start with a capital letter
        form = (w[0] or '').lstrip('^')  # strip leading ^ (asterisk variants)
        if not form or not form[0].isupper():
            continue
        # Previous form must start with a capital letter
        form_prev = (w_prev[0] or '').lstrip('^')
        if not form_prev or not form_prev[0].isupper():
            continue
        # Previous gloss must be a proper-name value
        zh_prev = (w_prev[col_zh] or '').strip()
        en_prev = (w_prev[col_en] or '').strip()
        if zh_prev in _PN_GLOSS_VALUES or en_prev in _PN_GLOSS_VALUES:
            w[col_zh] = '人名'
            w[col_en] = 'PN'


def filter_punct_words(words, s_id="", issues_writer=None, src=""):
    """Filter gloss triples whose form is purely punctuation.

    Parameters
    ----------
    words : list of [form, zh, en]
        The raw gloss triples for a sentence.
    s_id : str
        Sentence identifier, used in error messages.
    issues_writer : csv.writer or None
        If provided, rows are written here for punct-form entries that have
        non-empty translations (which indicates a data problem).
    src : str
        Source file path or name, used in error messages.

    Returns
    -------
    list of [form, zh, en]
        Only entries whose form contains at least one alphanumeric character.
    """
    result = []
    for w in words:
        if w[0]:
            # If ===+ appears and either gloss column contains '=' (indicating
            # a clitic boundary), collapse the run to a single '=' so the
            # clitic is preserved in the FORM.  Otherwise strip the whole run
            # (it is just a discourse / prosodic marker with no clitic).
            has_clitic = any(
                '=' in (w[j] if j < len(w) and w[j] else '')
                for j in (1, 2)
            )
            form = w[0]
            if has_clitic and re.search(r'={3,}', form):
                form = re.sub(r'={3,}', '=', form)
            form = re.sub(r'={2,}', '', form)
            form = re.sub(r'^X+$', 'XXXX', form)  # normalise unintelligible markers (X, XX, …) → XXXX
        else:
            form = w[0]
        if form != w[0]:
            w = list(w)
            w[0] = form
        if not is_punct_only(form):
            result.append(w)
            continue
        # Form is punct-only — check whether the translations are also empty/punct.
        zh = w[1] if len(w) > 1 else ""
        en = w[2] if len(w) > 2 else ""
        if is_punct_only(zh or "") and is_punct_only(en or ""):
            # Benign: trailing punctuation entry — silently drop it.
            pass
        else:
            # Translations have content: something is wrong in the source data.
            msg = (f"punct-only FORM '{form}' has non-empty TRANSL "
                   f"zh='{zh}' en='{en}' in {s_id}"
                   + (f" ({src})" if src else ""))
            print(f"  WARNING: {msg}")
            if issues_writer is not None:
                issues_writer.writerow([s_id, "punct_form_with_transl", form, zh, en])
    return result


def clean_punctuation(text):
    """
    Replace full-width punctuation and curly quotes with ASCII equivalents.

    Args:
        text (str): The input text to be cleaned.

    Returns:
        str: The cleaned text.
    """
    cleaned_text = text.replace("，", ",")
    cleaned_text = cleaned_text.replace("。", ".")
    cleaned_text = cleaned_text.replace("！", "!")
    cleaned_text = cleaned_text.replace("？", "?")
    cleaned_text = cleaned_text.replace("；", ";")
    cleaned_text = cleaned_text.replace("：", ":")
    cleaned_text = cleaned_text.replace("（", "(")
    cleaned_text = cleaned_text.replace("）", ")")
    cleaned_text = cleaned_text.replace("【", "[")
    cleaned_text = cleaned_text.replace("】", "]")
    cleaned_text = cleaned_text.replace("《", '"')
    cleaned_text = cleaned_text.replace("》", '"')
    cleaned_text = cleaned_text.replace("\u201c", '"')
    cleaned_text = cleaned_text.replace("\u201d", '"')
    cleaned_text = cleaned_text.replace("\u2018", "'")
    cleaned_text = cleaned_text.replace("\u2019", "'")
    cleaned_text = re.sub(r'={2,}', '', cleaned_text)  # prosodic/filler marker (==, ===, …)
    cleaned_text = cleaned_text.replace("「這是真的中文翻譯」", "")  # placeholder translation
    cleaned_text = _XXXX_TOKEN_RE.sub('XXXX', cleaned_text)  # unintelligible markers

    return cleaned_text.strip()


def expand_infixes(form, en_gloss, zh_gloss):
    """Expand a morpheme that carries infix notation into sub-morpheme tuples.

    In the NTU corpus, infixes are written inside angle brackets within the
    surface form (e.g. ``q<n>qda``) and their glosses are likewise bracketed
    in the English and Chinese gloss strings (e.g. ``<PF.PFV>throw``).

    If *form* contains one or more ``<xyz>`` spans this function returns a
    list of ``(form, en, zh)`` tuples:

    * One tuple per infix: form = ``'<xyz>'``, en/zh = the bracketed portion
      of the corresponding gloss string.
    * One trailing tuple for the base: the base form uses ``-`` to mark
      the embedding point(s) (e.g. ``q<n>qda`` → ``q-qda``); leading/trailing
      hyphens are stripped for word-initial/final infixes (``<n>apa`` → ``apa``).
      Annotator-error hyphens immediately after ``>`` in gloss strings are
      also stripped (``<AF>-eat`` → base gloss ``eat``).

    If *form* contains no angle-bracket spans the function returns the
    unchanged triple wrapped in a one-element list.

    Examples
    --------
    >>> expand_infixes('q<n>qda', '<PF.PFV>throw', '<受焦.完成>投下')
    [('<n>', '<PF.PFV>', '<受焦.完成>'), ('q-qda', 'throw', '投下')]

    >>> expand_infixes('s<m>iling', '<AF>-ask', '<主焦>-問')
    [('<m>', '<AF>', '<主焦>'), ('s-iling', 'ask', '問')]

    >>> expand_infixes('m<n>ddengu', 'AF<PFV>dry', '主焦<完成>乾')
    [('<n>', '<PFV>', '<完成>'), ('m-ddengu', 'AFdry', '主焦乾')]
    """
    form_infixes = _INFIX_RE.findall(form)
    if not form_infixes:
        return [(form, en_gloss, zh_gloss)]

    en_infixes = _INFIX_RE.findall(en_gloss)
    zh_infixes = _INFIX_RE.findall(zh_gloss)

    # Replace each run of consecutive infix spans with '-' to mark the
    # embedding point, then strip leading/trailing '-' for word-initial/final
    # infixes (e.g. '<n>apa' → 'apa', 'q<n>qda' → 'q-qda').
    root_form = re.sub(r'(?:<[^>]+>)+', '-', form).strip('-')

    # Remove the infix gloss spans.  Some annotators write "<AF>-eat" with a
    # spurious leading hyphen; strip that artefact with lstrip.
    root_en = _INFIX_RE.sub('', en_gloss).lstrip('-')
    root_zh = _INFIX_RE.sub('', zh_gloss).lstrip('-')

    result = []
    for i, fi in enumerate(form_infixes):
        ei = en_infixes[i] if i < len(en_infixes) else fi
        zi = zh_infixes[i] if i < len(zh_infixes) else fi
        result.append((f'<{fi}>', f'<{ei}>', f'<{zi}>'))

    result.append((root_form, root_en, root_zh))
    return result


def extract_notes(text):
    """
    Extract parenthetical commentary from a translation string.

    Recognises both ASCII parentheses ``()`` and full-width ``（）``.

    Parameters
    ----------
    text : str
        The translation string, possibly containing ``(commentary)`` or
        ``（commentary）`` spans.

    Returns
    -------
    cleaned : str
        The translation with all parenthetical spans removed and
        surrounding whitespace normalised.
    notes : str or None
        A ``'; '``-joined string of every captured group (stripped), or
        ``None`` when no parenthetical content was found.
    """
    pattern = r'[(\uff08]([^)\uff09]+)[)\uff09]'
    notes = [m.group(1).strip() for m in re.finditer(pattern, text)
             if m.group(1).strip()]
    cleaned = re.sub(r'\s*[(\uff08][^)\uff09]+[)\uff09]\s*', ' ', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned, (text if notes else None)


def strip_form_parens(text):
    """
    Remove parenthetical spans ``(...)`` from a sentence FORM string.

    Parenthetical words in the original text (e.g. optional elements,
    annotator insertions) have no corresponding ``<W>`` element and
    inflate the surface word count.  This function strips them so that
    the ``<FORM>`` text matches the glossed word sequence.

    Parameters
    ----------
    text : str
        The sentence form string.

    Returns
    -------
    cleaned : str
        The form string with every ``(...)`` span and its surrounding
        whitespace removed, collapsed to a single space between words.
    notes : str or None
        The original unmodified *text* if any parenthetical content was
        removed; ``None`` otherwise.
    """
    cleaned = re.sub(r'\s*\([^)]*\)\s*', ' ', text).strip()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    if cleaned != text:
        return cleaned, text
    return text, None


def add_transl_element(parent, lang, text):
    """
    Create a ``<TRANSL>`` child element on *parent*.

    Any parenthetical commentary found in *text* is removed from the
    element's text content and stored in a ``notes`` attribute instead.

    Parameters
    ----------
    parent : xml.etree.ElementTree.Element
        The parent XML element.
    lang : str
        BCP-47 language tag written to ``xml:lang``  (e.g. ``"zh"``).
    text : str
        The translation string.

    Returns
    -------
    xml.etree.ElementTree.Element
        The newly created ``<TRANSL>`` element.
    """
    elem = ET.SubElement(parent, "TRANSL")
    elem.set("xml:lang", lang)
    cleaned, notes = extract_notes(text or "")
    elem.text = cleaned if cleaned else (text or "")
    if notes:
        elem.set("notes", notes)
    return elem
