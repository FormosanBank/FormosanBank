#!/usr/bin/env python3
"""pipeline_sentences — the NTU *Sentences* pipeline, one measured step at a time.

Companion to pipeline_grammar.py (grammar). Shared steps are imported from it rather
than reimplemented; the steps numbered here are the ones the sentence sources
need and grammar did not.

    python pipeline_sentences.py --json <sentence dir> --out <dir> [--steps 0,1,...]
    python pipeline_sentences.py --list-steps

STEPS
  2  split a record that holds several sentences
     The source separates two sentences inside one record with a bare '/' --
     a ["/", "", ""] gloss row and a "/" ori token. Emitting one S per record
     puts both sentences' words under one sentence form, which no amount of
     later repair can align. Split into one S per group, suffixed a/b/c on the
     record id as main does.

  3  expand infix notation into its own morphemes
     Same as grammar's step 17, and the same ordering constraint: split on '-'
     and '=' FIRST, then expand infixes within each piece. Reuses
     expand_infixes from the corpus's own utils.py.

  4  drop sentences the source marks ungrammatical
     A bare leading '*' on an ori token or a gloss form marks the whole example
     ungrammatical (POL-016) -- distinct from the '*(X)' / '(*X)' parenthesis
     notation, which marks material obligatory or forbidden within an otherwise
     grammatical sentence. main drops these outright: "Skip sentences marked
     ungrammatical anywhere". All 35 in the corpus are in this subcorpus.

  5  strip transcription markup from forms
     The sources carry conventions that are not part of the language: prosodic
     and breath markers ((H), (0.8), slash-backslash), and code-switch tags naming the
     source language of a borrowed word (<L2JtukiL2J> = Japanese "tuki").
     Reuses strip_prosodic_markers and strip_l2m from the corpus's own utils.py.
     strip_l2m keeps the word and removes only the tag, because a code-switched
     word is real text; strip_prosodic_markers removes the marker entirely.
     The fact of the code-switch is kept as notes="code-switch" on the word
     form. parse_stories.py does this; parse_sentences.py strips the tag and
     drops the flag, losing the information -- the stories convention is the
     better of the two.

     Runs FIRST, on both the sentence form and every word form, as
     strip_prosodic_markers's own docstring requires: "Call this before any
     other processing ... so that paren-wrapped markers such as (H) or (0.8)
     are never mis-identified as editorial insertions." It also removes the
     <L2...> groups that would otherwise reach the infix expander in step 3.

  14 record word-internal optional material as an alternate form
     The sources mark optional material inside a word -- 'ka(z)', '(s)aiv=ik',
     'kangavas(=an)' -- which has no W of its own, so it cannot be treated as an
     optional word. main's resolve_inline_parentheticals.py materialises every
     combination as a separate sentence: 119 sentences gain variants, and one
     with five optional groups becomes 32 near-identical readings. That is not
     a useful corpus.

     Instead each affected word keeps ONE base FORM (kindOf="original", the
     reading WITHOUT the optional material) and one variant FORM of the same
     tier, kindOf="original" ver="alt" (WITH it) -- the POL-028 spelling as
     revised 2026-09-09. The sentence gets the same pair, built from the same
     choice, so the base forms agree across the two tiers and the variants
     agree too -- one extra form per word and per sentence, never 2^n
     sentences. standardize.py then derives the matching standard-tier
     variants, because a variant names the tier it varies from.

  15 drop rows that are transcription apparatus, not words
     ORDERING: runs AFTER step 5. A pause marker still carrying its timing
     ('...(1.6)') has digits in it, so it matches none of the six classes; only
     once step 5 has stripped the timing does it read as '...' and get dropped.
     With the wrong order 8505 such rows survived as glossless words.

     Six classes of gloss row carry no word and must not become a W: a speaker
     label with no gloss or glossed as a label, punctuation with no gloss or
     glossed as punctuation, a pause marker with no gloss, and a non-verbal
     annotation such as '(COUGH)'. Runs first, before the sentence form is
     rebuilt from the gloss forms, so the apparatus never reaches the sentence
     either. Rare in these sources (29 rows) and structural in the stories,
     where they are one gloss row in six.

     A seventh class -- CJK in the form column -- is deliberately NOT dropped:
     in the stories most of it is genuine Mandarin code-switching, where the
     Chinese IS the spoken word.

  1  put the gloss columns in the right language slots
     Assigning columns positionally tags Chinese as English and vice versa for
     any source that writes English first. Adapted from the published
     fix_swapped_gloss_langs.py, keeping its per-row gate. A no-op on grammar,
     which is why it was dropped there; on sentences it is essential.

  0  rebuild the sentence form from the gloss forms
     The source withholds the running sentence in 3319 of 4430 records: 'ori'
     is absent in 1039, and holds nothing but punctuation (usually a lone '.')
     in a further 2280. main rebuilds it by joining the
     gloss column-0 forms (parse_sentences.py: "Reconstruct from gloss if ori
     not available for this group"). Without it a quarter of sentences have no
     FORM at all, and tests 1, 3 and 5 measure that absence rather than
     anything about the pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import html
import re
import unicodedata
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
_REPO_ROOT = Path(__file__).resolve().parents[4]   # <bank>/Corpora/<C>/CodeAndDocs/pipeline/
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from pipeline_grammar import (SPLIT, XML_LANG, add_transl as _add_transl, step1_brackets,  # noqa: E402
                       step7_align_separator, drop_starred_alternatives, drop_starred_readings, free_entries,
                   load_free_repairs,
                   conform_sentence, build_attestation,
                       load_malformed_translations, unglossed_optional,
                       prune_unsupported, _OPTIONAL)
from QC.cleaning.clean_xml import swap_punctuation  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
# The gloss/word test helpers live in qa/, which is their single home;
# the builders reuse them rather than carrying a second copy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qa"))
from utils import (expand_infixes, strip_l2m, strip_prosodic_markers,  # noqa: E402
                   resolve_ungrammatical_parens)

ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")


def add_transl(parent, lang, text):
    return _add_transl(parent, lang, clean_text(text))

STEPS = {
    0: "rebuild the sentence form from the gloss forms",
    1: "put the gloss columns in the right language slots",
    2: "split a record that holds several sentences",
    3: "expand infix notation into its own morphemes",
    4: "drop sentences the source marks ungrammatical",
    5: "strip transcription markup from forms",
    7: "resolve POL-017 grammaticality parentheses (both tiers, before the form is rebuilt)",
    8: "canonicalize punctuation (POL-010/011/013) via clean_xml",
    9: "convert a gloss separator when it makes the morpheme counts match",
   10: "repair truncated free translations (MALFORMED_TRANSLATIONS)",
   11: "split an unglossed WHOLE-WORD optional parenthetical into a second sentence",
   12: "withdraw a word or morpheme analysis the tiers do not support",
   13: "give an unsegmented word a single mirror morpheme (POL-023)",
   14: "record word-internal optional material as an alternate form",
   15: "drop rows that are transcription apparatus, not words",
   18: "reassign glosses stranded on a form-less morpheme, then drop the shell",
}

# The six agreed classes of gloss row that carry no word. A "_" is the sources'
# placeholder for an absent gloss and counts as empty throughout. A seventh
# class -- CJK in the form column -- is deliberately NOT dropped: in the stories
# most of it is genuine Mandarin code-switching, where the Chinese IS the word.
_SPEAKER = re.compile(r"^\s*[A-Z]\s*[:.：]*\s*$")
_LABEL_ECHO = re.compile(r"^\s*([A-Z])\s*[:.…]*\s*(?:\([^)]*\))?\s*[.…]*\s*$")
_PUNCT_ONLY = re.compile(r"^[^\w’'ʉ]+$")
_PAUSE = re.compile(r"^\s*[（(]?\d+(?:\.\d+)?[）)]?\s*$|^\.{2,}$|^=+$")
_NONVERBAL = re.compile(r"^\s*[（(]\s*[A-Z]{2,}\s*[）)]\s*$")


def apparatus_class(row: list):
    """Which of the six apparatus classes this row is, or None if it is a word."""
    form = str(row[0]).strip()
    glosses = [str(c).strip() for c in row[1:]]
    blank = all(g in ("", "_") for g in glosses)
    if _SPEAKER.match(form):
        if blank:
            return "1 speaker label, no gloss"
        if any(_LABEL_ECHO.match(g) for g in glosses if g):
            return "2 speaker label glossed as a label"
    if _PUNCT_ONLY.match(form):
        if blank:
            return "3 punctuation, no gloss"
        if all(_PUNCT_ONLY.match(g) for g in glosses if g and g != "_"):
            return "4 punctuation glossed as punctuation"
    if _PAUSE.match(form) and blank:
        return "5 pause marker, no gloss"
    if _NONVERBAL.match(form):
        return "6 non-verbal annotation"
    return None

# Optional material written INSIDE a word: 'ka(z)', '(s)aiv=ik', 'kangavas(=an)',
# '(na=)ma-hansiap'. Distinguished from a free-standing optional word by having
# other characters outside the parentheses.
_INLINE_OPTIONAL = re.compile(r"\(([^()*]*)\)")


def has_inline_optional(form: str) -> bool:
    text = (form or "").strip()
    return bool(_INLINE_OPTIONAL.search(text)) and not re.fullmatch(
        r"\([^()]*\)", text)


def inline_readings(form: str) -> tuple:
    """(without the optional material, with it) -- both parenthesis-free."""
    return (_INLINE_OPTIONAL.sub("", form).strip(),
            _INLINE_OPTIONAL.sub(r"\1", form).strip())

SUFFIXES = "abcdefghijklmnopqrstuvwxyz"


# A speaker label opening a turn ('T:', 'D:...', 'P:..') and a bare intonation
# unit number, which marks where the next turn begins.
_TURN_LABEL = re.compile(r"^\s*[A-Z]\s*[:：]")
_IU_NUMBER = re.compile(r"^\s*\d+\s*$")


def split_groups(rows: list, ori: list) -> tuple:
    """Split gloss rows and ori tokens into per-sentence groups.

    A record can hold more than one sentence; the source separates them with a
    bare '/' -- a ["/", "", ""] gloss row, and a "/" ori token. main gives the
    resulting sentences 'a'/'b'/'c' suffixes on the record id.
    """
    gloss_groups, current = [], []
    for row in rows:
        form = str(row[0])
        if form == "/" and not any(str(c).strip() for c in row[1:]):
            if current:
                gloss_groups.append(current)
            current = []
            continue
        # A second speaker label starts a second turn: the record holds two
        # sentences by two speakers. The bare IU number that precedes it is the
        # boundary marker, not a word, so it is dropped with the split. Without
        # this the later turn is silently lost -- sdqCon-dialog2 rec 187's
        # answer ('m-uda icin ...') appeared nowhere in the built corpus.
        if _TURN_LABEL.match(form) and current:
            while current and _IU_NUMBER.match(str(current[-1][0])):
                current.pop()
            if current:
                gloss_groups.append(current)
            current = []
        current.append(row)
    if current:
        gloss_groups.append(current)

    ori_groups, current_ori = [], []
    for token in ori:
        if str(token) == "/":
            ori_groups.append(current_ori)
            current_ori = []
        else:
            current_ori.append(token)
    ori_groups.append(current_ori)
    return gloss_groups, ori_groups

HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")
WORDY = re.compile(r"[^\W\d_]")
# Characters XML forbids outright. Seven backspaces (0x08) occur in Sakizaya
# story glosses ('\x08PREP', '去\x08外面'); left in, they make the file
# unparseable, so they are removed wherever text is emitted rather than in an
# optional step.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def clean_text(text):
    return _CONTROL.sub("", text) if isinstance(text, str) else text


def step1_realign(zho: str, eng: str) -> tuple:
    """Swap when the English slot carries Han and the Chinese slot does not.

    The source's column order is not fixed: Kanakanavu writes Chinese first,
    Rukai English first, and Bunun is mixed WITHIN the language (6820 rows one
    way, 6450 the other), so the decision has to be per row rather than per
    file or per language. The gate is idempotent -- after a swap it no longer
    holds -- and it leaves alone both identical pairs (DM, TOP, PN) and rows
    where only one slot is filled.
    """
    if HAN.search(eng or "") and not HAN.search(zho or ""):
        return eng, zho
    return zho, eng


def gloss_rows(body: dict) -> list:
    return [r for r in (body.get("gloss") or []) if isinstance(r, list) and r]


# Two prosodic markers main's strip_prosodic_markers does not remove:
#   '=='/'==='  vowel lengthening. borrow_segmentation.py: "the NTU
#               transcriptions use ==/=== as a prosodic-lengthening marker,
#               which the parsers strip". Left in, the splitter reads it as two
#               clitic boundaries -- 6,660 of 6,822 test-6 failures.
#   trailing '/' the intonation-unit terminal, pairing with '\' which IS
#               stripped. 1,633 of 1,634 story cases are the last row of a
#               record, following sentence punctuation ('ru,/', 'ha?/').
_LENGTHENING = re.compile(r"={2,}")
_IU_TERMINAL = re.compile(r"/+\s*$")
_IU_LEADING = re.compile(r"^\s*/+")
# A run of two or more dots is a pause marker, not punctuation: strip_prosodic_
# markers removes the single-character ellipsis U+2026 and the "--" break, but
# never the ASCII run. Left in place it survives in the sentence FORM (which the
# word tier never carries), so the word tier cannot account for the sentence --
# 890 of the 925 stories test-3 failures. A single "." is real punctuation.
_PAUSE_DOTS = re.compile(r"\.{2,}")


_BRACKET_NOTE = re.compile(r"\[[^\]]*\]")


def step5_strip_markup(text: str, gloss: bool = False) -> tuple:
    """Return (cleaned text, whether a code-switch tag was removed).

    Entities are decoded FIRST. strip_prosodic_markers treats '&' and ';' as
    single-character annotation markers, so '&lt;RED&gt;swim' fed to it straight
    comes out as the literal text 'ltREDgtswim' -- 554 of the 558 entity-bearing
    glosses in Sentences were damaged this way.

    In a gloss, a bracketed annotation is dropped whole. The same marker class
    strips '[' and ']' but leaves their contents, turning '[TVH1][u2]talk' into
    'TVH1u2talk'. A form keeps its brackets' contents, because there they are
    constituent bracketing that other steps resolve.
    """
    text = html.unescape(text or "")
    if gloss:
        text = _BRACKET_NOTE.sub("", text)
    clean, is_code_switch = strip_l2m(strip_prosodic_markers(text))
    # Strip the IU terminal only when it sits against a word, at either end. A
    # form that is nothing but "/" is the sentence-split separator step 2 keys
    # on, and step 5 runs first -- removing it silently disabled splitting.
    if clean.strip().strip("/"):
        clean = _IU_TERMINAL.sub("", clean)
        clean = _IU_LEADING.sub("", clean)
    clean = _LENGTHENING.sub("", clean)
    clean = _PAUSE_DOTS.sub("", clean)
    clean = drop_starred_alternatives(clean)
    return clean.strip(), is_code_switch


# Only the MARKERS come off, never the material between them: an infix is
# part of the surface form, so 'h<in>ud-an' is 'hinudan', not 'hudan'.
_SEG_MARKERS = re.compile(r"[-=<>]")


def step0_form_from_gloss(rows: list) -> str:
    """Join the gloss forms into a sentence form, as main does when ori is empty.

    Segmentation markers come OFF. The sentence form is the running text; the
    analysis lives on W and M. Joining the word forms verbatim carried '-', '='
    and '<in>' up into the sentence, which the published corpus never does --
    894 sentences differed from main for this reason alone.
    """
    joined = " ".join(str(r[0]).strip() for r in rows if str(r[0]).strip())
    text = " ".join(_SEG_MARKERS.sub("", joined).split())
    # The word forms carry no sentence-final punctuation, so a rebuilt sentence
    # ends bare. The published corpus closes it; matching that keeps the two
    # builds comparable (894 sentences differed by this alone). Only ever added
    # to a REBUILT form -- a form taken from the source's own ori is left exactly
    # as the source wrote it.
    if text and text[-1] not in ".!?。！？,，":
        text += "."
    return text





def language_for(path) -> str:
    """Language of a source JSON file: the '<Language>_<Dialect>' directory."""
    return path.parent.name.split("_")[0]


def dialect_for(path) -> str:
    """Canonical dialect for a source JSON file, via dialects.csv.

    Source directories are '<Language>_<Dialect>' and the source's own dialect
    name is not always the registry's: 'Tgdaya' is registered as 'Tegudaya',
    'Isbukun' as 'Junqun', 'Mayrinax' as 'Wenshui'. Match on the Official name
    or any OtherNames alias and return the Official form. A name the registry
    does not know (Rukai 'Vedai') becomes 'unknown' -- V036 sanctions that, and
    guessing a mapping would be inventing data.
    """
    import csv
    raw = path.parent.name.split("_", 1)
    if len(raw) < 2 or not raw[1]:
        return "unknown"
    language, name = raw[0], raw[1]
    # FB_DIALECTS lets a build read a registry that is not yet merged --
    # the same escape hatch CTABLES gives the conversion tables.
    registry = Path(os.environ.get("FB_DIALECTS")
                    or Path(__file__).resolve().parents[4] / "dialects.csv")
    if not registry.exists():
        return "unknown"
    with open(registry, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["Language"] != language:
                continue
            official = (row.get("Official") or "").strip()
            if not official:
                # A single-variety language: the registry row exists with no
                # Official column, and the dialect label is the language name
                # (which is how the published corpus labels Kanakanavu and
                # Sakizaya).
                return language
            aliases = [a.strip() for a in (row.get("OtherNames") or "").split("/") if a.strip()]
            if name == official or name in aliases:
                return official
    return "unknown"


def language_code(name: str) -> str:
    """ISO 639-3 code for a language directory name, via the canonical map.

    languages.csv is the single source of truth (POL-039); every consumer goes
    through QC.corpus_counts.load_language_codes. The pipelines used to hardcode
    "ami" on every TEXT regardless of language, which mislabelled every
    non-Amis file in the build.
    """
    from QC.corpus_counts import load_language_codes
    for code, label in load_language_codes().items():
        if str(label).lower() == (name or "").lower():
            return code
    return "und"


FREE_REPAIRS = load_free_repairs()

def build(records: list, text_id: str, steps: set, stats: dict,
          attested: dict | None = None, malformed: dict | None = None, language: str = "", dialect: str = "unknown") -> ET.Element:
    root = ET.Element("TEXT")
    root.set("id", text_id)
    root.set("citation", "NTU Corpus of Formosan Languages")
    root.set("BibTeX_citation", "")
    root.set("copyright", "CC BY-NC 4.0")
    root.set(XML_LANG, language_code(language))
    # V036 requires @dialect; "unknown" is the sanctioned value when the
    # source does not record one. For trv that reads as Seediq, correctly.
    root.set("dialect", dialect)

    for rec in records:
        if not (isinstance(rec, list) and len(rec) > 1 and isinstance(rec[1], dict)):
            continue
        rid, body = str(rec[0]), rec[1]
        all_rows = gloss_rows(body)
        all_ori = list(body.get("ori") or [])

        code_switch = set()
        if 7 in steps:
            # BOTH tiers, and before step 0 rebuilds the sentence form from the
            # gloss forms -- otherwise the rebuilt sentence keeps '(*sua)' while
            # the word tier drops it, and the tiers disagree. main resolves
            # gloss_group and ori_tokens together for the same reason. A token
            # that resolves to nothing is dropped, taking its gloss with it.
            resolved_rows = []
            for r in all_rows:
                cells = [resolve_ungrammatical_parens(str(c)) for c in r]
                if cells[0].strip() != str(r[0]).strip():
                    stats["7 grammaticality parens resolved"] = stats.get(
                        "7 grammaticality parens resolved", 0) + 1
                if not cells[0].strip():
                    stats["7   rows dropped (forbidden material)"] = stats.get(
                        "7   rows dropped (forbidden material)", 0) + 1
                    continue
                resolved_rows.append(cells)
            all_rows = resolved_rows
            all_ori = [t for t in (resolve_ungrammatical_parens(str(t)) for t in all_ori)
                       if t.strip()]

        if 5 in steps:
            before = (list(all_ori), [list(r) for r in all_rows])
            all_ori = [t for t, _ in (step5_strip_markup(str(t)) for t in all_ori) if t]
            cleaned = []
            for r in all_rows:
                form, is_cs = step5_strip_markup(str(r[0]))
                if not form.strip():
                    continue
                if is_cs:
                    code_switch.add(form)
                    stats["5   code-switched words marked"] = stats.get(
                        "5   code-switched words marked", 0) + 1
                # The glosses carry the tags too -- repair_l2_markers notes that
                # "tags inside gloss strings (TRANSL) were never stripped at
                # all" -- so they get the same treatment.
                glosses = []
                for cell in r[1:]:
                    g, g_cs = step5_strip_markup(str(cell), gloss=True)
                    if g != str(cell):
                        stats["5   gloss cells cleaned"] = stats.get(
                            "5   gloss cells cleaned", 0) + 1
                    glosses.append(g)
                cleaned.append([form] + glosses)
            all_rows = cleaned
            if (all_ori, [list(r) for r in all_rows]) != before:
                stats["5 records with markup stripped"] = stats.get(
                    "5 records with markup stripped", 0) + 1

        if 15 in steps:
            kept = []
            dropped_labels = set()
            for r in all_rows:
                cls = apparatus_class(r)
                if cls:
                    stats[f"15 dropped: {cls}"] = stats.get(f"15 dropped: {cls}", 0) + 1
                    if cls.startswith(("1 speaker label", "2 speaker label")):
                        # Remember WHICH label, so only that one is taken out of
                        # the sentence form.
                        dropped_labels.add(str(r[0]).strip().rstrip(":.：").strip())
                    continue
                kept.append(r)
            all_rows = kept
            if dropped_labels:
                # A label dropped from the word tier must go from the sentence
                # form too, or the form carries a token no W will ever account
                # for. Step 5 has already taken the colon off, so the ori token
                # is a bare capital. 556 of the 705 stories test-3 failures were
                # exactly this.
                before_ori = len(all_ori)
                all_ori = [t for t in all_ori
                           if str(t).strip().rstrip(":.：").strip() not in dropped_labels]
                if len(all_ori) != before_ori:
                    stats["15   speaker labels removed from the sentence form"] = stats.get(
                        "15   speaker labels removed from the sentence form", 0) + (
                        before_ori - len(all_ori))

        if 2 in steps:
            groups, ori_groups = split_groups(all_rows, all_ori)
            if not groups:
                # A record with no gloss rows still has a sentence and its
                # translations; it must not vanish just because it has no words.
                groups, ori_groups = [[]], [all_ori]
            if len(groups) > 1:
                stats["2 records split into several sentences"] = stats.get(
                    "2 records split into several sentences", 0) + 1
                stats["2   extra sentences emitted"] = stats.get(
                    "2   extra sentences emitted", 0) + len(groups) - 1
        else:
            groups, ori_groups = [all_rows], [all_ori]

        for gi, rows in enumerate(groups):
            suffix = SUFFIXES[gi] if len(groups) > 1 else ""
            ori = ori_groups[gi] if gi < len(ori_groups) else []
            if 4 in steps and (any(str(t).startswith("*") for t in ori)
                               or any(str(r[0]).startswith("*") for r in rows)):
                stats["4 ungrammatical sentences dropped"] = stats.get(
                    "4 ungrammatical sentences dropped", 0) + 1
                continue
            emit_sentence(root, text_id, rid + suffix, body, rows, ori, steps, stats,
                          code_switch, attested, malformed)
    # POL-053: the closed attribute surface, plus V017/V085 conformance.
    conform_sentence(root, stats)
    return root


def reassign_glosses(sentence, stats: dict) -> None:
    """Recover glosses stranded on form-less M, then drop the empty shells.

    Ported from repair_empty_morphemes.py's guarded branch. A repair happens
    only when the glosses are recoverable by position: for EVERY gloss
    language, the number of non-empty glosses must equal the number of M that
    carry a form. The i-th gloss then goes to the i-th form-bearing M and the
    shells are removed.

    Where the word carries an infix, a form-M and the gloss assigned to it must
    agree on whether they are bracketed; otherwise the word is left alone,
    because there the mapping is not positional and redistributing would
    scramble it. A word that fails either guard keeps its shells for the later
    prune to judge.
    """
    def orig(el):
        node = el.find("FORM[@kindOf='original']")
        return "".join(node.itertext()) if node is not None else ""

    for w in sentence.findall("W"):
        ms = w.findall("M")
        if not ms or not any(not orig(m).strip() for m in ms):
            continue
        formed = [m for m in ms if orig(m).strip()]
        if not formed:
            continue
        tiers: dict = {}
        for m in ms:
            for t in m.findall("TRANSL"):
                text = (t.text or "").strip()
                if text and text != "_":
                    tiers.setdefault(t.get(XML_LANG), []).append(text)
        if not tiers or any(len(v) != len(formed) for v in tiers.values()):
            continue
        if "<" in orig(w):
            bad = False
            for glosses in tiers.values():
                for m, g in zip(formed, glosses):
                    if ("<" in orig(m)) != ("<" in g):
                        bad = True
            if bad:
                continue
        for lang, glosses in tiers.items():
            for i, m in enumerate(formed):
                el = next((t for t in m.findall("TRANSL")
                           if t.get(XML_LANG) == lang), None)
                if el is None:
                    el = ET.SubElement(m, "TRANSL")
                    el.set(XML_LANG, lang)
                el.text = glosses[i]
        for m in ms:
            if not orig(m).strip():
                w.remove(m)
                stats["18 stranded glosses reassigned, shell dropped"] = stats.get(
                    "18 stranded glosses reassigned, shell dropped", 0) + 1


def emit_sentence(root, text_id, sid, body, rows, ori, steps, stats,
                  code_switch=frozenset(), attested=None, malformed=None):
        attested = attested or {}
        malformed = malformed or {}
        s = ET.SubElement(root, "S")
        s.set("id", f"{text_id}_S_{sid}")
        form = ET.SubElement(s, "FORM")
        form.set("kindOf", "original")
        s_form = " ".join(str(t) for t in ori)
        # The source withholds the running sentence in two ways: 'ori' absent
        # (1039 records) and 'ori' holding nothing but punctuation, typically a
        # lone '.' (2280 records). Only 1111 of 4430 carry real words, so the
        # gate gets a word-character test rather than a truthiness test.

        if 0 in steps and not WORDY.search(s_form) and rows:
            s_form = step0_form_from_gloss(rows)
            stats["0 sentence forms rebuilt from the gloss"] = stats.get(
                "0 sentence forms rebuilt from the gloss", 0) + 1
        alt_s_form = None
        if 14 in steps and any(has_inline_optional(str(r[0])) for r in rows):
            main_words, alt_words = [], []
            for r in rows:
                f = str(r[0])
                if has_inline_optional(f):
                    a, b = inline_readings(f)
                    main_words.append(a)
                    alt_words.append(b)
                else:
                    main_words.append(f)
                    alt_words.append(f)
            s_form = " ".join(w for w in main_words if w)
            alt_s_form = " ".join(w for w in alt_words if w)
            stats["14 sentences given an alternate form"] = stats.get(
                "14 sentences given an alternate form", 0) + 1

        if 8 in steps:
            canon = swap_punctuation(s_form)
            if canon != s_form:
                stats["8 S FORMs canonicalized"] = stats.get(
                    "8 S FORMs canonicalized", 0) + 1
                s_form = canon
        form.text = clean_text(s_form)
        if alt_s_form and alt_s_form != s_form:
            alt = ET.SubElement(s, "FORM")
            alt.set("kindOf", "original")
            alt.set("ver", "alt")
            alt.text = swap_punctuation(alt_s_form) if 8 in steps else alt_s_form

        # emit_sentence sees the id with any split suffix ('12a'); the repair
        # table keys on the source record, so the suffix comes off first.
        base_rid = re.sub(r"[a-z]$", "", str(sid))
        entries, free_notes = free_entries(body.get("free") or [], text_id,
                                           base_rid, FREE_REPAIRS)
        for lang, text, ver, note in entries:
            el = add_transl(s, lang, text)
            if ver:
                el.set("ver", ver)
            if note:
                el.set("notes", note)
        for note in free_notes:
            s.set("notes", ((s.get("notes") or "") + " " + note).strip())

        if 11 in steps:
            # Only a WHOLE-word parenthetical counts here. The sentence sources
            # also mark optional material INSIDE a word -- 'ka(z)',
            # '(s)aiv=ik', 'kangavas(=an)' -- which has no W of its own and
            # must not be treated as an optional word; that is what main's
            # resolve_inline_parentheticals.py is for, run as a post-XML step.
            whole = any(re.fullmatch(r"\([^()]*\)", str(r[0]).strip()) for r in rows)
            optional = unglossed_optional(s_form, rows) if whole else None
            if optional:
                def _resolve(text, keep):
                    out = _OPTIONAL.sub(
                        lambda m: (m.group(1) if keep else "")
                        if m.group(1).strip() == optional else m.group(0), text)
                    return " ".join(out.split())
                source_form = s_form
                s_form = _resolve(source_form, keep=False)
                form.text = s_form
                variant = ET.SubElement(root, "S")
                variant.set("id", f"{text_id}_S_{sid}-alt")
                variant.set("notes", f"optional element '{optional}' present; the "
                                     "source gives it no gloss, so this reading "
                                     "carries no word tier")
                vform = ET.SubElement(variant, "FORM")
                vform.set("kindOf", "original")
                vform.text = _resolve(source_form, keep=True)
                for line in body.get("free") or []:
                    if line.startswith("#c"): add_transl(variant, "zho", drop_starred_readings(line[2:]))
                    elif line.startswith("#e"): add_transl(variant, "eng", drop_starred_readings(line[2:]))
                stats["11 unglossed optional parentheticals split"] = stats.get(
                    "11 unglossed optional parentheticals split", 0) + 1

        if 10 in steps and malformed:
            for transl in s.findall("TRANSL"):
                case = malformed.get((s.get("id"), transl.get(XML_LANG)))
                if case and (swap_punctuation((transl.text or "").strip())
                             == swap_punctuation(case[0].strip())):
                    transl.text = case[1]
                    stats["10 truncated translations repaired"] = stats.get(
                        "10 truncated translations repaired", 0) + 1

        for i, row in enumerate(rows):
            w_form = str(row[0])
            zho = str(row[1]) if len(row) > 1 else ""
            eng = str(row[2]) if len(row) > 2 else ""

            # ORDERING: after step 6. swap_punctuation maps "[" -> "(" and
            # "]" -> ")", so canonicalising first would hide the brackets from
            # step 6 and merge them with the POL-017 parentheses.
            if 8 in steps:
                for nm, val in (("f", w_form), ("z", zho), ("e", eng)):
                    canon = swap_punctuation(val)
                    if canon != val:
                        stats["8 word cells canonicalized"] = stats.get(
                            "8 word cells canonicalized", 0) + 1
                        if nm == "f": w_form = canon
                        elif nm == "z": zho = canon
                        else: eng = canon

            if 9 in steps and attested:
                for nm, val in (("z", zho), ("e", eng)):
                    new = step7_align_separator(w_form, val, attested)
                    if new != val:
                        stats["9 gloss separators converted"] = stats.get(
                            "9 gloss separators converted", 0) + 1
                        if nm == "z": zho = new
                        else: eng = new

            if 1 in steps:
                new_zho, new_eng = step1_realign(zho, eng)
                if (new_zho, new_eng) != (zho, eng):
                    stats["1 gloss columns realigned"] = stats.get(
                        "1 gloss columns realigned", 0) + 1
                zho, eng = new_zho, new_eng

            w = ET.SubElement(s, "W")
            w.set("id", f"{text_id}_S_{sid}_W{i}")
            w_alt = None
            if 14 in steps and has_inline_optional(w_form):
                base, alt = inline_readings(w_form)
                # POL-028/V150: an alternate is a SPELLING VARIANT of its
                # sibling. When removing the optional material leaves nothing
                # but punctuation, the whole WORD was optional -- the sentence's
                # word inventory changes, so POL-026 makes it a separate S
                # block, not an alternate. Writing one here produced pairs like
                # base ',' / alternate 'ia,'.
                if any(unicodedata.category(c)[0] in ("L", "N") for c in base):
                    w_form, w_alt = base, alt
                    stats["14   words given an alternate form"] = stats.get(
                        "14   words given an alternate form", 0) + 1
                else:
                    stats["14   whole-word optional left for POL-026"] = stats.get(
                        "14   whole-word optional left for POL-026", 0) + 1

            wf = ET.SubElement(w, "FORM")
            wf.set("kindOf", "original")
            wf.text = clean_text(w_form)
            if w_alt and w_alt != w_form:
                wa = ET.SubElement(w, "FORM")
                wa.set("kindOf", "original")
                wa.set("ver", "alt")
                wa.text = w_alt
            if w_form in code_switch:
                wf.set("notes", "code-switch")
            add_transl(w, "zho", zho)
            add_transl(w, "eng", eng)

            parts = [p for p in SPLIT.split(w_form) if p]
            zparts = [p for p in SPLIT.split(zho) if p]
            eparts = [p for p in SPLIT.split(eng) if p]
            # A bracket group is an infix only if the word has host letters
            # outside it. '<L2J...L2J>' and '<BREATH>' are code-switch and
            # non-verbal markers, and convert_infix_notation declines them for
            # exactly this reason; expanding them invents a form-less morpheme.
            has_infix = (3 in steps and bool(re.search(r"<[^>]+>", w_form))
                         and bool(WORDY.search(re.sub(r"<[^>]*>", "", w_form))))
            # A monomorphemic word is ANALYSED too: one morpheme, carrying the
            # word's gloss. Emitting the M records that, and withholding it
            # would make "analysed as monomorphemic" look identical to "never
            # analysed" -- the distinction POL-054 exists to protect. The M is
            # written whenever the word is glossed; an unglossed word gets
            # nothing, because there the M really would be invented.
            is_glossed = bool(zho.strip() or eng.strip())
            if (len(parts) > 1 or len(zparts) > len(parts) > 0 or has_infix
                    or (len(parts) == 1 and is_glossed)):
                for j in range(max(len(parts), len(zparts), len(eparts))):
                    piece = parts[j] if j < len(parts) else ""
                    mz = zparts[j] if j < len(zparts) else ""
                    me = eparts[j] if j < len(eparts) else ""
                    expandable = (3 in steps and bool(re.search(r"<[^>]+>", piece))
                                  and bool(WORDY.search(re.sub(r"<[^>]*>", "", piece))))
                    sub = expand_infixes(piece, me, mz) if expandable else []
                    if len(sub) > 1:
                        stats["3 infixes expanded"] = stats.get("3 infixes expanded", 0) + 1
                        for n, (sf_, se_, sc_) in enumerate(sub):
                            m = ET.SubElement(w, "M")
                            m.set("id", f"{text_id}_S_{sid}_W{i}M{j}_{n}")
                            mf = ET.SubElement(m, "FORM")
                            mf.set("kindOf", "original")
                            mf.text = clean_text(sf_)
                            add_transl(m, "zho", sc_)
                            add_transl(m, "eng", se_)
                        continue
                    m = ET.SubElement(w, "M")
                    m.set("id", f"{text_id}_S_{sid}_W{i}M{j}")
                    if piece:
                        mf = ET.SubElement(m, "FORM")
                        mf.set("kindOf", "original")
                        mf.text = clean_text(piece)
                    add_transl(m, "zho", mz)
                    add_transl(m, "eng", me)

        if 18 in steps:
            reassign_glosses(s, stats)

        if 12 in steps:
            prune_unsupported(s, stats)
        if 13 in steps and any(w.findall("M") for w in s.findall("W")):
            for w in s.findall("W"):
                if w.findall("M"):
                    continue
                node = w.find("FORM[@kindOf='original']")
                wf = "".join(node.itertext()) if node is not None else ""
                if not wf.strip():
                    continue
                m = ET.SubElement(w, "M")
                m.set("id", f"{w.get('id')}M0")
                mf = ET.SubElement(m, "FORM")
                mf.set("kindOf", "original")
                mf.text = wf
                for t in w.findall("TRANSL"):
                    add_transl(m, t.get(XML_LANG), t.text or "")
                stats["13 mirror morphemes added"] = stats.get(
                    "13 mirror morphemes added", 0) + 1



def _attestation_clean(cell: str) -> str:
    """Normalize a gloss cell exactly as the pipeline does before the flip."""
    text, _ = strip_l2m(strip_prosodic_markers(cell or ""))
    return swap_punctuation(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--steps", default="all")
    ap.add_argument("--list-steps", action="store_true")
    args = ap.parse_args()

    if args.list_steps:
        for n, desc in sorted(STEPS.items()):
            print(f"  {n}  {desc}")
        return 0
    if not args.json or not args.out:
        ap.error("--json and --out are required unless --list-steps")

    if args.steps == "all":
        steps = set(STEPS)
    elif args.steps == "none":
        steps = set()
    else:
        steps = {int(x) for x in args.steps.split(",") if x.strip()}

    attested = build_attestation(args.json, _attestation_clean) if 9 in steps else {}
    malformed = load_malformed_translations(args.json) if 10 in steps else {}
    stats: dict = {}
    # Clear the output first: a previous run's files would otherwise
    # survive alongside the new ones and be scored twice.
    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    by_language: dict = {}
    for path in sorted(args.json.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        recs = data if isinstance(data, list) else (list(data.values())[0] if data else [])
        if not isinstance(recs, list):
            continue
        root = build(recs, path.stem, steps, stats, attested, malformed, language=language_for(path), dialect=dialect_for(path))
        language = path.parent.name.split("_")[0]
        merged = by_language.get(language)
        if merged is None:
            merged = ET.Element("TEXT")
            for key, value in root.attrib.items():
                merged.set(key, value)
            # main publishes these as NTU_Sen_<Language> (not "Sent"); POL-037
            # wants the id stable across a rebuild, so we keep its spelling.
            merged.set("id", f"NTU_Sen_{language}")
            by_language[language] = merged
        merged.extend(list(root))

    count = 0
    for language, root in sorted(by_language.items()):
        dest = args.out / language
        dest.mkdir(parents=True, exist_ok=True)
        ET.ElementTree(root).write(dest / f"{language}.xml",
                                   encoding="utf-8", xml_declaration=True)
        count += 1
    print(f"wrote {count} files; steps applied: {sorted(steps) or 'none'}")
    for k in sorted(stats):
        print(f"  {k}: {stats[k]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
