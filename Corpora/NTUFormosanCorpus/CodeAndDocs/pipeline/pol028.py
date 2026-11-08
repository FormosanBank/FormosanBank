"""POL-028 (amended 2026-10-15): a glossed optional morpheme makes two sentences.

NTU writes optional material in parentheses inside a word. Optional LETTERS
inside one morpheme ('ka(z)', '(s)aiv=ik') stay one sentence with a ver="alt"
FORM (step 14 of the builders). An optional MORPHEME or clitic that the source
glosses ('kangavas(=an)' 'mango(=MED.NOM)', '(na=)ma-hansiap') is different:
the two readings are glossed differently, so each becomes a sentence of its
own -- the base keeps the published id, the other reading takes '<id>-opt' --
with its own word and morpheme tiers. Maintainer: "differences in morphemes
necessitate different sentence blocks only if they are glossed and would
result in different glossing."

A source row is split when its form holds an inline parenthesis whose content
begins or ends with a morpheme boundary ('-' or '='), and at least one gloss
column also holds a parenthesis. Which reading is the base, and per-reading
sentence text, translations and notes, can be set per record in
pol028_readings.tsv (rulings 2026-10-15/16); by default the base is the reading
without the optional morpheme and both readings carry the record's
translations (ruling 2026-10-16, "same translation").
"""
from __future__ import annotations

import csv
import re
from pathlib import Path

_INLINE = re.compile(r"\(([^()*]*)\)")
WORDY = re.compile(r"[^\W\d_]")


def _inline(text: str) -> bool:
    t = (text or "").strip()
    return bool(_INLINE.search(t)) and not re.fullmatch(r"\([^()]*\)\W*", t)


def is_glossed_optional_morpheme(row) -> bool:
    form = str(row[0]) if row else ""
    if not _inline(form) or len([p for p in form.split("/") if p.strip()]) > 1:
        return False
    if not any(c[:1] in "-=" or c[-1:] in "-=" for c in _INLINE.findall(form)):
        return False
    return any("(" in str(c) for c in list(row)[1:3])


def _read(text: str, with_opt: bool) -> str:
    return _INLINE.sub(r"\1" if with_opt else "", str(text))


def reading_rows(rows, with_opt: bool):
    """The record's gloss rows for one reading: the split rows lose their
    parentheses (keeping or dropping the optional morpheme and its gloss);
    every other row is untouched (letters-only optionals stay for step 14)."""
    out = []
    for r in rows:
        if is_glossed_optional_morpheme(r):
            out.append([_read(r[0], with_opt)] + [_read(c, with_opt) for c in list(r)[1:]])
        else:
            out.append(r)
    return out


def reading_ori(ori, with_opt: bool):
    """NTU's sentence line for one reading: a token with an inline parenthesis
    is read like the gloss form; free-standing '(word)' tokens are left for
    POL-026."""
    return [_read(t, with_opt) if _inline(str(t)) else t for t in ori]


def load_overrides(path=None) -> dict:
    """{(source file suffix, record id, 'base'|'opt'): row dict}."""
    p = Path(path) if path else Path(__file__).with_name("pol028_readings.tsv")
    lines = [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    out = {}
    for r in csv.DictReader(lines, delimiter="\t", quoting=csv.QUOTE_NONE):
        out[(r["source_file"], str(r["record"]), r["reading"])] = r
    return out


OVERRIDES = load_overrides()


def overrides_for(language: str, stem: str, rid) -> dict:
    """Override rows for one record, matched on the source file's language
    directory ('Bunun_Isbukun' -> Bunun) and stem, which together are unique."""
    out = {}
    for (f, rec, reading), row in OVERRIDES.items():
        parts = Path(f).parts
        if (len(parts) >= 2 and parts[-2].split("_")[0] == language
                and Path(f).stem == stem and rec == str(rid)):
            out[reading] = row
    return out


def free_for(body: dict, row) -> list:
    """The record's free lines with any per-reading translation substituted.
    An override that names a translation replaces that language entirely; an
    explicit '-' publishes none in that language. Notes are kept."""
    free = list(body.get("free") or [])
    if not row:
        return free
    for tag, col in (("#c", "zho"), ("#e", "eng")):
        val = (row.get(col) or "").strip()
        if val:
            free = [l for l in free if not str(l).startswith(tag)]
            if val != "-":
                free.append(f"{tag} {val}")
    return free


# --------------------------------------------------------------------------
# Optional phrases (POL-026): a parenthesis that opens on one word and closes
# on a later one, e.g. '(nau tu)' (source note: "nau tu可以省略") or
# '(kane ku butulu)?'. Each reading is a sentence of its own. Transcriber
# labels written the same way ('(CLEAR THROAT)', '(PHONE RINGS)') are not
# optional speech and are left alone. POL-026 (whole optional words) applied to
# phrases: item D10 on the 2026-10-16 follow-ups page (Kanakanavu 3_S_1), a fix
# under existing policy, not a separate ruling; five more records have the same case.
_LABEL = re.compile(r"[A-Z][A-Z .]*")


def phrase_span(tokens):
    """(start, end) of the one multi-token '( … )' span, or None."""
    start = None
    for i, t in enumerate(str(x) for x in tokens):
        if start is None:
            if t.startswith("(") and ")" not in t:
                start = i
        elif "(" in t:
            return None
        elif ")" in t:
            inner = " ".join(str(x) for x in tokens[start:i + 1])
            if not re.fullmatch(r"\(([^()]*)\)[^\w()]*", inner) or _LABEL.fullmatch(inner.strip("().,?!/\\_ ")):
                return None
            return (start, i)
    return None


def _strip_parens(text):
    return str(text).replace("(", "").replace(")", "")


def phrase_reading(tokens, span, with_phrase, cells=False):
    """Tokens (or gloss rows when cells=True) for one reading. Without the
    phrase, the punctuation after its closing parenthesis moves onto the
    preceding token so the sentence keeps it."""
    s, e = span
    if with_phrase:
        out = list(tokens)
        for i in (s, e):
            out[i] = [_strip_parens(c) for c in out[i]] if cells else _strip_parens(out[i])
        return out
    tail = re.sub(r"^.*\)", "", str(tokens[e][0] if cells else tokens[e]))
    out = list(tokens[:s]) + list(tokens[e + 1:])
    if tail.strip() and s > 0:
        prev = out[s - 1]
        if cells:
            out[s - 1] = [str(prev[0]) + tail] + list(prev[1:])
        else:
            out[s - 1] = str(prev) + tail
    return out


_TRANSL_GROUP = re.compile(r"\s*[（(][^()（）]*[)）]")


def phrase_free(free, with_phrase):
    """Translation lines for one reading: without the phrase, parenthesized
    groups come out; with it, only the parenthesis characters do. Lines with
    no parentheses are unchanged. This applies the 2026-10-16 ruling on #13/#18
    (each reading its own wording when the text and translation both mark the
    option) to optional phrases; the phrase cases were not ruled on separately."""
    out = []
    for line in free:
        l = str(line)
        if l[:2] in ("#c", "#e") and _TRANSL_GROUP.search(l):
            body = l[2:]
            body = (re.sub(r"[()（）]", "", body) if with_phrase
                    else re.sub(r"\s+([,.;:!?。，！？])", r"\1", _TRANSL_GROUP.sub("", body)))
            l = l[:2] + body
        out.append(l)
    return out


def readings(rows, ori, body, ovr):
    """Every reading of a record as (id suffix, rows, ori, free, notes, keep_audio),
    or None when the record has neither a glossed optional morpheme nor an
    optional phrase. The base (no optional material) keeps the id; one
    optional kind gives '-opt'; with both, the phrase alone is '-opt3' and
    both together '-opt4' (POL-028 never uses '-opt2')."""
    morph = any(is_glossed_optional_morpheme(r) for r in rows)
    rspan = phrase_span([r[0] for r in rows]) if rows else None
    if not morph and not rspan:
        return None
    ospan = phrase_span(ori) if ori else None
    combos = [(False, False)]
    if morph:
        combos.append((True, False))
    if rspan:
        combos.append((False, True))
    if morph and rspan:
        combos.append((True, True))
    suffix = {(False, False): "", (True, False): "-opt", (False, True): "-opt3" if morph else "-opt",
              (True, True): "-opt4"}
    out = []
    for m_with, p_with in combos:
        key = "base" if not m_with else "opt"
        row = (ovr.get(key) or {}) if not p_with else {}
        takes_with = (row.get("takes") or ("with" if m_with else "without")) == "with"
        r_rows = reading_rows(rows, takes_with) if morph else list(rows)
        r_ori = [row["sentence_text"]] if row.get("sentence_text") else (reading_ori(ori, takes_with) if morph else list(ori))
        free = free_for(body, row)
        if rspan:
            r_rows = phrase_reading(r_rows, rspan, p_with, cells=True)
            free = phrase_free(free, p_with)
            if ospan:
                r_ori = phrase_reading(r_ori, ospan, p_with)
        out.append((suffix[(m_with, p_with)], r_rows, r_ori, free, row.get("notes"), not (m_with or p_with)))
    return out
