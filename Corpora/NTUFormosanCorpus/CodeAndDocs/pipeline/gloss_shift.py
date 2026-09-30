#!/usr/bin/env python3
"""Gloss-shift repair: operations, invariants, and the evidence that judges them.

A *gloss shift* is a sentence in which a whole run of cells on one tier sits one
slot away from the words it belongs to -- every word in the run carries its
neighbour's gloss, and the run ends at a word with no gloss at all. The source
JSONs hold each intonation unit as a list of rows, ``[form, gloss, gloss]``; the
shift lives there, in NTU's own data, and it is corrected there -- in memory, at
load time, never by writing the JSON back.

What a repair may do
--------------------
A repair *moves* cells. It never writes new text (``fill`` excepted, and only
with a named reviewer). Each operation acts on one tier of a bounded window of
rows ``[i, j]`` and only on the window's *word* rows -- transcription apparatus
such as ``...(1.4)``, a speaker label ``F:`` or a lone ``<L2J`` is stepped
over, and must carry no gloss:

``shift_right``  a cell is MISSING at i: insert a blank at i, and every cell in
                 (i, j] moves one word right. The cell at j must be blank; it is
                 the one the missing entry pushed off the end.
``shift_left``   a SPURIOUS blank sits at i: remove it, every cell in (i, j]
                 moves one word left, and j is left blank.
``split``        two cells were FUSED into i (``take-LF=1EPL.GEN`` holding the
                 host's gloss and a separately written clitic's): cut it at its
                 last ``sep``, the second half goes to the next word, the rest
                 moves right, and the blank at j is consumed. A ``=`` stays
                 with the clitic it marks (``=1EPL.GEN``; maintainer,
                 2026-09-30: "please don't lose the clitic marker!"); a ``-``
                 is the host's own boundary and is dropped.
``merge``        one cell was SPLIT across i and the next word (``take-LF`` /
                 ``=1EPL.GEN``): rejoin them at i, the rest moves left, j is
                 left blank. Only offered where a marker at the seam shows the
                 cut -- the join adds no boundary the source did not write.
``swap``         two whole tiers are exchanged across the window (``col1`` with
                 ``col2``: the English and Chinese glosses in each other's slot).
``fill``         put ``value`` in the blank cell at i. The one operation that
                 writes text; refused unless the table names a reviewer.

``check_moved_not_edited`` states the guarantee mechanically: for every
operation except ``fill``, the tier's non-blank content, read in order and with
the ``sep`` seams of a split/merge ignored, is identical before and after.

Tiers are named by source column -- ``form`` (0), ``col1`` (1), ``col2`` (2) --
or ``gloss``, both gloss columns moving together, which is how the shift in the
source has always presented.

What counts as better
---------------------
``score`` measures a run of rows against the rest of the language's source:

``attested``      (word, gloss) pairs seen elsewhere in the same language. A word
                  glossed the way it is glossed nowhere else is the shift's
                  signature, so a real repair raises this. Placeholder glosses
                  (XX, ??, FIL, FS, BC, ...) do not count: they mark no meaning.
``contradicted``  a word seen >= CONTRADICT_MIN times elsewhere, never with this
                  gloss.
``morph_match``   cells whose gloss has as many morphemes as the word's form
                  (``rakiyas-an=mu`` / ``climb-LF=1SG.GEN``: 3 = 3). Gated per
                  gloss language, so a good Chinese cell cannot hide a bad
                  English one.
``unglossed``     word rows with no gloss in any column. Reported, not gated:
                  a repair may leave a word bare (a gloss really was lost),
                  and the report suggests a same-language gloss for it.
``reconstruct``   words whose form, with its segmentation removed, is the
                  corresponding token of the plain-text sentence (the ``ori``
                  field), where the source has one.
``paired``        words whose English and Chinese glosses occur together on
                  some other word: the two gloss tiers agree with each other.
                  Guards single-column repairs, which can otherwise raise
                  attestation by tearing a correct pair apart.

Evidence is leave-one-out: the sentence under test is subtracted from the
lexicon, so a word never vouches for its own gloss.
"""
from __future__ import annotations

import copy
import csv
import functools
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qa"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sentence_xml_tests import gloss_pieces, morpheme_count, substantive  # noqa: E402
from utils import strip_l2m, strip_prosodic_markers  # noqa: E402

TIERS = {"form": (0,), "col1": (1,), "col2": (2,), "gloss": (1, 2)}
OPS = ("shift_right", "shift_left", "split", "merge", "swap", "fill")
BLANK = {"", "_"}
CONTRADICT_MIN = 3
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
# Apparatus, not words. The first four patterns are pipeline_stories.py's own
# (its step 15 drops such rows), copied rather than imported because that module
# imports this one; tests/corpora/test_ntu_gloss_shift.py fails if they drift.
# A gloss moved onto a row the build then drops is simply lost, and a gloss
# moved onto a speaker label keeps the label as a word, which the sentence form
# does not contain -- so prune withdraws the sentence's whole word tier.
_SPEAKER = re.compile(r"^\s*[A-Z]\s*[:.：]*\s*$")
_PUNCT_ONLY = re.compile(r"^[^\w’'ʉ]+$")
_PAUSE = re.compile(r"^\s*[（(]?\d+(?:\.\d+)?[）)]?\s*$|^\.{2,}$|^=+$")
_NONVERBAL = re.compile(r"^\s*[（(]\s*[A-Z]{2,}\s*[）)]\s*$")
# And a bare '<L2J' / 'L2J>', a code-switch tag the source put on a row of its own.
_LONE_L2_TAG = re.compile(r"^(<L2[A-Z]?|L2[A-Z]?>)$")
# A speaker label names who is talking, with a colon: 'F:', 'D:..', and the
# multi-speaker 'S,G,W:' / 'Y,M:' of the Tsou conversations.
_COLON_LABEL = re.compile(r"^\s*[A-Z]\d?(\s*,\s*[A-Z]\d?)*\s*[:：]")
# Glosses that mark something other than a meaning -- a filler, a false start,
# unintelligible speech, backchannel -- are not evidence about a word: 'XX'
# glossed 'XX' is "attested" everywhere, and would reward moving it anywhere.
PLACEHOLDER_GLOSSES = {"XX", "XXX", "XXXX", "X", "??", "?", "FIL", "FS", "UH", "UU",
                       "AH", "BC", "@@", "@@@"}
# NTU_GLOSS_SHIFT_TABLE points a trial build at another table.
REPAIRS_TSV = Path(os.environ.get("NTU_GLOSS_SHIFT_TABLE")
                   or Path(__file__).with_name("gloss_shift_repairs.tsv"))
TABLE_FIELDS = ("source_file", "record_ids", "record_sha256", "tier", "op", "i", "j",
                "sep", "value", "status", "reviewer", "rationale")


# ------------------------------------------------------------------ cells

def blank(cell) -> bool:
    return (cell if isinstance(cell, str) else "").strip() in BLANK


def norm_form(form: str) -> str:
    """A word form as a lexicon key: markup, prosody and punctuation removed.

    Segmentation (``-``, ``=``, ``<>``) is kept -- ``rakiyas-an=mu`` and
    ``rakiyasanmu`` are different claims about the word.
    """
    text = strip_prosodic_markers(form or "")
    text, _ = strip_l2m(text)
    text = text.replace("’", "'").replace("^", "")
    text = re.sub(r"={2,}", "", text)
    text = text.strip().strip(".,;:!?/\\_\"“”()[] ")
    return unicodedata.normalize("NFC", text).lower()


@functools.lru_cache(maxsize=None)
def _builder_clean(raw: str) -> str:
    """The form as pipeline_stories step 5 leaves it (prosody, lengthening
    '==', IU '/', pause dots and code-switch tags stripped). Imported lazily:
    pipeline_stories imports this module."""
    from pipeline_stories import step5_strip_markup
    return step5_strip_markup(raw)[0]


@functools.lru_cache(maxsize=None)
def is_word(form: str) -> bool:
    """True for a row that can carry a gloss, rather than transcription apparatus.

    Tested on the form as written and as the builder sees it after step 5, so a
    row the builder empties ('(Hx)') or reads as a pause is apparatus.

    Speaker labels need care. The builder's pattern matches any lone capital,
    but drops such a row only when its gloss is blank or merely echoes the
    letter (step 15, classes 1 and 2); glossed, it is kept as a word. A label
    with a colon ('F:', 'D:..', 'P:...(0.9)') is a real speaker label, and a
    gloss moved onto it would be kept as a word the sentence form does not
    contain -- prune then withdraws the whole word tier -- so it is apparatus.
    A lone capital without one is a word slot: Sakizaya 'E==' is a lengthened
    filler glossed FIL, and 'X' marks an unintelligible word; if the gloss that
    lands on it is only an echo, the builder drops the row, as it should.
    An unintelligible stretch ('XX', 'XX--') is always a word slot.
    """
    raw = (form or "").strip()
    if raw and not _builder_clean(raw).strip():
        return False                      # the builder drops the row
    shapes = {raw, strip_prosodic_markers(raw).strip(), _builder_clean(raw)}
    if any(p.match(x) for p in (_PUNCT_ONLY, _PAUSE, _NONVERBAL, _LONE_L2_TAG)
           for x in shapes):
        return False
    if any(_COLON_LABEL.match(x) for x in shapes):
        return False
    text = norm_form(raw)
    return bool(text) and substantive(text)


def norm_gloss(gloss: str) -> str:
    return (gloss or "").strip()


def gloss_lang(gloss: str) -> str:
    """'zho' or 'eng', by script: Chinese when at least half its pieces are.
    Columns are not trusted to be in order ('IRR=go-處格' is English)."""
    from pipeline_grammar import han_share
    return "zho" if han_share(gloss) >= 0.5 else "eng"


def bare(text: str) -> str:
    return re.sub(r"[-=<>\s]", "", text or "")


# ------------------------------------------------------------------ operations

@dataclass
class Op:
    tier: str
    op: str
    i: int
    j: int
    sep: str = "="
    value: str = ""
    reviewer: str = ""

    def label(self) -> str:
        extra = f" sep={self.sep!r}" if self.op in ("split", "merge") else ""
        extra += f" value={self.value!r}" if self.op == "fill" else ""
        return f"{self.op}({self.tier}, {self.i}..{self.j}){extra}"


class RepairError(ValueError):
    """An operation whose preconditions do not hold. Never applied partially."""


def _cols(tier: str) -> tuple:
    if tier not in TIERS:
        raise RepairError(f"unknown tier {tier!r}")
    return TIERS[tier]


def _cell(rows: list, k: int, c: int) -> str:
    row = rows[k]
    return row[c] if c < len(row) and isinstance(row[c], str) else ""


def _set(rows: list, k: int, c: int, value: str) -> None:
    row = rows[k]
    while len(row) <= c:
        row.append("")
    row[c] = value


def word_slots(rows: list, i: int, j: int) -> list:
    """Row indices in [i, j] that hold words."""
    return [k for k in range(i, j + 1) if is_word(_cell(rows, k, 0))]


def apply_op(rows: list, op: Op) -> list:
    """Return a copy of *rows* with *op* applied. Raises RepairError if it cannot."""
    if op.op not in OPS:
        raise RepairError(f"unknown op {op.op!r}")
    if not (0 <= op.i <= op.j < len(rows)):
        raise RepairError(f"window {op.i}..{op.j} outside {len(rows)} rows")
    out = [list(r) for r in rows]
    cols = _cols(op.tier)

    if op.op == "swap":
        if op.tier != "gloss":
            raise RepairError("swap exchanges col1 and col2; give tier 'gloss'")
        for k in range(op.i, op.j + 1):
            a, b = _cell(out, k, 1), _cell(out, k, 2)
            _set(out, k, 1, b)
            _set(out, k, 2, a)
        return out

    if op.op == "fill":
        if not op.reviewer.strip():
            raise RepairError("fill writes text; it needs a named reviewer")
        if op.i != op.j:
            raise RepairError("fill takes a single row (i == j)")
        if len(cols) != 1:
            raise RepairError("fill writes one column; give col1, col2 or form")
        if not blank(_cell(out, op.i, cols[0])):
            raise RepairError(f"fill target row {op.i} is not blank")
        _set(out, op.i, cols[0], op.value)
        return out

    slots = word_slots(out, op.i, op.j)
    # A right shift may START at a transcription mark that carries a gloss --
    # a speaker label 'H:', a breath '(H)' -- when that gloss is the first one
    # displaced (maintainer, 2026-09-30: "(H) shouldn't be glossed. Shift starts
    # there."). The mark is left bare; the build drops it anyway.
    if (op.op == "shift_right" and op.tier != "form" and slots and slots[0] != op.i
            and any(not blank(_cell(out, op.i, c)) for c in cols)):
        slots = [op.i] + slots
    if len(slots) < 2 or slots[0] != op.i or slots[-1] != op.j:
        raise RepairError(f"window {op.i}..{op.j} must start and end on a word")
    # Apparatus rows inside the window are stepped over; they must not be
    # carrying anything that would be stranded.
    for k in range(op.i, op.j + 1):
        if k not in slots and op.tier != "form" and any(not blank(_cell(out, k, c)) for c in cols):
            raise RepairError(f"row {k} is apparatus but carries a gloss")

    for c in cols:
        cells = [_cell(out, k, c) for k in slots]
        if op.op == "shift_right":
            if not blank(cells[-1]):
                raise RepairError(f"shift_right needs a blank at {op.j} (col {c})")
            new = [""] + cells[:-1]
        elif op.op == "shift_left":
            if not blank(cells[0]):
                raise RepairError(f"shift_left needs a blank at {op.i} (col {c})")
            new = cells[1:] + [""]
        elif op.op == "split":
            if not blank(cells[-1]):
                raise RepairError(f"split needs a blank at {op.j} (col {c})")
            head = cells[0]
            cut = head.rfind(op.sep)
            if cut <= 0 or cut + len(op.sep) >= len(head):
                raise RepairError(f"row {op.i} col {c}: {head!r} has no inner {op.sep!r}")
            tail = head[cut:] if op.sep == "=" else head[cut + len(op.sep):]
            new = [head[:cut], tail] + cells[1:-1]
        elif op.op == "merge":
            a, b = cells[0], cells[1]
            if blank(a) or blank(b):
                raise RepairError("merge joins two non-blank cells")
            if not (a.endswith(op.sep) or b.startswith(op.sep)):
                raise RepairError(f"merge: no {op.sep!r} at the seam of {a!r}|{b!r}")
            new = [a + b] + cells[2:] + [""]
        else:  # pragma: no cover - guarded above
            raise RepairError(op.op)
        for k, v in zip(slots, new):
            _set(out, k, c, v)
    return out


def _content_stream(rows: list, c: int) -> list:
    """The non-blank cells of column *c*, in order."""
    return [_cell(rows, k, c).strip() for k in range(len(rows))
            if not blank(_cell(rows, k, c))]


def check_moved_not_edited(before: list, after: list, op: Op) -> None:
    """Raise unless *op* only moved content (see module docstring)."""
    if len(before) != len(after):
        raise RepairError("row count changed")
    if op.op == "fill":
        return
    moved = set(_cols(op.tier)) if op.op != "swap" else {1, 2}
    for c in range(3):
        if c in moved:
            continue
        if [_cell(before, k, c) for k in range(len(before))] != \
           [_cell(after, k, c) for k in range(len(after))]:
            raise RepairError(f"column {c} changed but the op does not touch it")
    if op.op == "swap":
        return
    for c in moved:
        a, b = _content_stream(before, c), _content_stream(after, c)
        if op.op in ("split", "merge"):
            # Only the cell boundary at the seam may move: the text, read
            # without the separator that marked the seam, is unchanged.
            a = "".join(a).replace(op.sep, "")
            b = "".join(b).replace(op.sep, "")
        if a != b:
            raise RepairError(f"column {c}: content changed, not merely moved")


# ------------------------------------------------------------------ lexicon

def bilingual_pair(row: list):
    """(English, Chinese) gloss of one row, if it has one of each."""
    cells = [norm_gloss(_cell([row], 0, c)) for c in (1, 2)]
    by = {gloss_lang(g): g for g in cells if g not in BLANK}
    return (by["eng"], by["zho"]) if len(by) == 2 else None


@dataclass
class Lexicon:
    """Counts for one language: (word, gloss-language, gloss), (word,
    gloss-language), and (English gloss, Chinese gloss) seen on one word."""
    pairs: Counter = field(default_factory=Counter)
    words: Counter = field(default_factory=Counter)
    bilingual: Counter = field(default_factory=Counter)

    def add_rows(self, rows: list, sign: int = 1) -> None:
        for row in rows:
            if not row or not is_word(_cell([row], 0, 0)):
                continue
            w = norm_form(row[0])
            for c in (1, 2):
                g = norm_gloss(_cell([row], 0, c))
                if g in BLANK:
                    continue
                lang = gloss_lang(g)
                self.pairs[(w, lang, g)] += sign
                self.words[(w, lang)] += sign
            pair = bilingual_pair(row)
            if pair:
                self.bilingual[pair] += sign

    def without(self, rows: list) -> "Lexicon":
        lex = Lexicon(Counter(self.pairs), Counter(self.words), Counter(self.bilingual))
        lex.add_rows(rows, sign=-1)
        return lex


def records_of(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    recs = data if isinstance(data, list) else (data.get("glosses") or list(data.values())[0])
    return [r for r in recs if isinstance(r, list) and len(r) > 1 and isinstance(r[1], dict)]


def source_files(codedocs: Path, language: str | None = None) -> list:
    out = []
    for sub in ("grammar", "sentence", "story"):
        for p in sorted((codedocs / sub).rglob("*.json")):
            if language is None or p.parent.name.split("_")[0] == language:
                out.append(p)
    return out


def build_lexicon(paths: list) -> Lexicon:
    lex = Lexicon()
    for p in paths:
        for rec in records_of(p):
            lex.add_rows(rec[1].get("gloss") or [])
    return lex


# ------------------------------------------------------------------ scoring

def score(rows: list, lex: Lexicon, ori: list | None = None) -> dict:
    """Evidence for one alignment of *rows*. *lex* must already exclude them."""
    s = Counter(attested=0, contradicted=0, morph_match=0, morph_eng=0, morph_zho=0,
                unglossed=0, reconstruct=0, paired=0, support=0.0)
    words = [r for r in rows if r and is_word(_cell([r], 0, 0))]
    for row in words:
        w = norm_form(row[0])
        cells = [norm_gloss(_cell([row], 0, c)) for c in (1, 2)]
        if all(g in BLANK for g in cells):
            s["unglossed"] += 1
            continue
        pair = bilingual_pair(row)
        if pair and lex.bilingual.get(pair, 0) > 0:
            s["paired"] += 1
        for g in cells:
            if g in BLANK:
                continue
            lang = gloss_lang(g)
            if morpheme_count(w) == gloss_pieces(g):
                s["morph_match"] += 1
                s[f"morph_{lang}"] += 1
            if g.rstrip("=").upper() in PLACEHOLDER_GLOSSES:
                continue    # not evidence either way (see PLACEHOLDER_GLOSSES)
            n = lex.pairs.get((w, lang, g), 0)
            if n > 0:
                s["attested"] += 1
                s["support"] += math.log1p(n)
            elif lex.words.get((w, lang), 0) >= CONTRADICT_MIN:
                s["contradicted"] += 1
    if ori:
        tokens = [bare(norm_form(t)) for t in ori if is_word(t)]
        for tok, row in zip(tokens, words):
            s["reconstruct"] += int(tok == bare(norm_form(row[0])))
    s["support"] = round(s["support"], 3)
    return dict(s)


def improves(before: dict, after: dict) -> bool:
    """The acceptance rule: more attested, and nothing else gets worse.

    ``unglossed`` is reported, not gated. Inserting a blank is a legitimate
    repair -- a gloss really was lost -- and a repair that leaves a word bare
    but makes the rest of the sentence line up is worth seeing; the word left
    bare gets a same-language suggestion (``suggest``) for a reviewer to fill.
    """
    return (after["attested"] > before["attested"]
            and after["morph_eng"] >= before["morph_eng"]
            and after["morph_zho"] >= before["morph_zho"]
            and after["reconstruct"] >= before["reconstruct"]
            and after["contradicted"] <= before["contradicted"]
            and after["paired"] >= before["paired"])


def suggest(form: str, lex: "Lexicon", top: int = 2) -> str:
    """How the same word is glossed elsewhere in the same language.

    For a word a repair leaves bare. *lex* must be the leave-one-out lexicon of
    that language only -- never another language's. A suggestion, for a
    reviewer; nothing applies it.
    """
    w = norm_form(form)
    parts = []
    for lang in ("eng", "zho"):
        total = lex.words.get((w, lang), 0)
        if total <= 0:
            continue
        ranked = sorted(((n, g) for (ww, ll, g), n in lex.pairs.items()
                         if ww == w and ll == lang and n > 0), reverse=True)[:top]
        parts.append(", ".join(f"{g} ({n}/{total})" for n, g in ranked))
    return " | ".join(parts) or "no other occurrence"


# ------------------------------------------------------------------ the table

def record_digest(records: list) -> str:
    """SHA-256 over the targeted records, serialized as pipeline_grammar does."""
    payload = records[0] if len(records) == 1 else records
    raw = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def statuses_in_force() -> set:
    """Which table rows the build applies. Only 'accepted', unless overridden
    (NTU_GLOSS_SHIFT_STATUSES=accepted,proposed) to trial proposals."""
    raw = os.environ.get("NTU_GLOSS_SHIFT_STATUSES", "accepted")
    return {s.strip() for s in raw.split(",") if s.strip()}


def load_table(path: Path = REPAIRS_TSV, statuses: set | None = None) -> list:
    if not path.exists():
        return []
    statuses = statuses_in_force() if statuses is None else statuses
    out = []
    with path.open(encoding="utf-8", newline="") as fh:
        rows = [line for line in fh if not line.lstrip().startswith("#")]
    for row in csv.DictReader(rows, delimiter="\t"):
        if row.get("status", "").strip() not in statuses:
            continue
        missing = [f for f in TABLE_FIELDS if f not in row]
        if missing:
            raise RepairError(f"{path.name}: missing columns {missing}")
        out.append(row)
    return out


def op_from_row(row: dict) -> Op:
    return Op(tier=row["tier"], op=row["op"], i=int(row["i"]), j=int(row["j"]),
              sep=row.get("sep") or "=", value=row.get("value") or "",
              reviewer=row.get("reviewer") or "")


def apply_to_records(records: list, src_key: str, table: list, stats: dict) -> list:
    """Apply every table row for *src_key* to *records*; returns a new list.

    Each row is pinned: the records it targets must hash to ``record_sha256``
    *as they are in the source*, before any row is applied -- so two rows for
    one sentence, even over overlapping records, are both checked against the
    data they were written for, and a drifted source fails the build rather
    than have cells moved in data nobody has seen. Rows then apply in table
    order.
    """
    mine = [r for r in table if src_key.endswith(r["source_file"])]
    if not mine:
        return records
    out = list(records)
    index = {str(r[0]): k for k, r in enumerate(out) if isinstance(r, list) and r}

    def span(row):
        ids = row["record_ids"].split("+")
        try:
            ks = [index[i] for i in ids]
        except KeyError as exc:
            raise RepairError(f"{src_key}: no record {exc} for {row['record_ids']}") from None
        if ks != list(range(ks[0], ks[0] + len(ks))):
            raise RepairError(f"{src_key}: records {row['record_ids']} are not consecutive")
        return ks

    for row in mine:
        found = record_digest([records[k] for k in span(row)])
        if found != row["record_sha256"]:
            raise RepairError(f"source drifted for {src_key}:{row['record_ids']}; "
                              f"expected {row['record_sha256']}, found {found}")
    for row in mine:
        ks = span(row)
        lengths = [len(out[k][1].get("gloss") or []) for k in ks]
        glued = [list(g) for k in ks for g in (out[k][1].get("gloss") or [])]
        op = op_from_row(row)
        after = apply_op(glued, op)
        check_moved_not_edited(glued, after, op)
        stats["gloss-shift repairs applied"] = stats.get("gloss-shift repairs applied", 0) + 1
        pos = 0
        for k, n in zip(ks, lengths):
            rec = copy.deepcopy(out[k])
            rec[1]["gloss"] = after[pos:pos + n]
            pos += n
            out[k] = rec
    return out
