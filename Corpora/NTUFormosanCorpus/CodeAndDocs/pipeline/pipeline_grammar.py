#!/usr/bin/env python3
"""pipeline_grammar — builds the Grammar subcorpus XML from the source JSONs.

Starts from the naive JSON -> XML conversion (no corrections) and applies the
enumerated steps below. Each step is added only once its effect on
grammar_xml_tests.py has been measured, so the test table is the record of what
each step buys.

pipeline2.py is kept unchanged at its seven-step state so the table has a fixed
reference point: a p3 column that moves relative to p2 shows what the newest
steps bought, rather than everything being re-measured against a moving target.

    python pipeline_grammar.py --json <grammar dir> --out <dir> [--steps 1,2,...]
    python pipeline_grammar.py --list-steps

STEPS
  1  strip trailing Chinese grammatical-role labels from word forms
     Some form-column cells carry a Chinese role label appended to the word
     ('seto]謂語' -> 'seto]'). The published pipeline strips *all* CJK from the
     form column of non-wordlist entries; this step instead strips only a closed
     vocabulary of 30 attested role labels, anchored at the end of the cell, so
     a form-column cell that is genuinely Chinese is left alone to be handled on
     its own terms rather than silently emptied.

     A2 wordlist files are exempt: there column 0 legitimately holds Chinese.

  3  apply pinned source-record repairs
     Some source records are scrambled in ways no rule should generalise -- a
     free translation sitting in the gloss column, a note in the translation
     slot. Those are repaired one record at a time from p2_source_repairs.xml,
     each pinned by a SHA-256 of the pre-repair record so the build fails rather
     than misapplies if the source changes. pipeline2 keeps its own repair list
     rather than inheriting the published one, and adds to it as cases are found.

  4  strip footnote markers from the sentence form
     The grammar books print footnote references against the end of an example
     ('’esi tapininga sua cina.25', '’akuni arapipiningi soni!15'). Only the
     digits are the reference: the punctuation before them belongs to the
     sentence, as 'soni!15' shows -- its free translation is '今天不要出去！',
     an imperative -- so the mark is kept and only the digits removed.

  5  emit no word tier for unglossed sentences
     Some records carry a real sentence but no word-level annotation at all,
     encoded as a single placeholder gloss row: [["_", "", ""]]. That is an
     absence of glossing, not a word, so the S gets no W tier rather than one W
     whose FORM is "_".

  6  join fixed English compound glosses with '.'
     'sister-in-law' is one gloss, not three morphemes. A closed list of these
     compounds is written with '.' so the separator logic below sees them as the
     single unit they are. Runs before step 7 for that reason.

  7  convert a gloss separator when it makes the morpheme counts match
     '-' divides morphemes; '.' joins words inside one morpheme's gloss. Where
     they are confused, the gloss splits into the wrong number of pieces. This
     flips one separator, and ONLY when the result matches the segmentation's
     morpheme count exactly. The competing spelling must be attested somewhere
     in the corpus, but one attestation is enough: the exact-match requirement,
     not the frequency, is what makes the change safe.

 11  canonicalize punctuation (POL-010/011/013) via clean_xml
     Reuses QC.cleaning.clean_xml.swap_punctuation, the repo's single
     implementation: curly singles, modifier apostrophes, backtick and the
     stress mark all become ASCII "'" (the glottal stop's canonical spelling,
     POL-010); every dash look-alike becomes "-" (POL-011); tilde look-alikes
     become "~" (POL-013); fullwidth punctuation becomes ASCII.

     ORDERING: this must run AFTER step 1, not before. swap_punctuation maps
     "[" -> "(" and "]" -> ")", so normalising first would both hide the
     constituent brackets from step 1 and make them indistinguishable from the
     POL-017 optional/forbidden parentheses "*(X)" / "(*X)".

  12 resolve POL-017 grammaticality parentheses in the sentence form
     '*(X)' marks X obligatory (keep X, unstarred); '(*X)' marks X forbidden
     (drop it). The word tier already resolves these, but the sentence form
     kept them, leaving a word in the sentence with no counterpart. Reuses
     resolve_ungrammatical_parens from the corpus's own utils.py rather than
     reimplementing the notation.

  13 close the space before sentence-final punctuation
     Some sentence forms end 'a wacu .', with the final mark detached as its
     own token. Closing the space is a whitespace fix, not a punctuation edit.

  14 suppress sentence blocks recorded as irreconcilable
     Runs last. See IRRECONCILABLE above.

  15 rebuild the sentence form from the word tier for cited excerpts
     Three grammar records quote an excerpt from another corpus, so the sentence
     form holds the citation -- '(NTU Formosan Corpus: skzyNr-moving_kulang
     IU100-101)' -- while the fully glossed word tier holds the transcript. The
     sentence is rebuilt from those word forms, with the conversational
     apparatus removed (IU numbers, pause timings, prominence, unit-final
     backslash), and the citation kept as a note.

  16 split an unglossed optional parenthetical into a second sentence
     The source marks an optional word by wrapping it in parentheses. Where the
     word tier carries that word -- with its own parenthesised gloss, or with
     the parentheses lost -- the corpus's own split_optional_parentheticals.py
     and the INDEXED_OPTIONAL_WORDS table in source_repairs.xml already
     materialise both readings, and p3 defers to them.

     This step covers only the remaining case, which those deliberately
     decline: the parenthetical has NO gloss anywhere in the word tier
     (e.g. '’esi kara marivura’ʉ (kara) ’uva …', whose word tier runs
     '’esi=kara | m-arivura’ʉ | ’uva | …'). Two sentences are emitted, neither
     containing parentheses: the reading WITHOUT the optional word keeps the
     word tier, which is what that tier actually glosses; the reading WITH it
     carries no W elements at all, because its segmentation and glossing are
     unknown and must not be guessed.

  17 expand infix notation into its own morphemes
     An infix is written inside angle brackets in the form and bracketed in the
     gloss ('t<um>a-tang' / 'Ca重疊<主事焦點>'), so splitting on '-' and '='
     alone leaves it buried in its host and the morpheme count comes up short.
     Reuses expand_infixes from the corpus's own utils.py, applied in main's
     order: split on '-' and '=' FIRST, then expand infixes within each piece.
     The order matters -- expanding first yields a single base whose '-' marks
     the embedding point, which cannot then be re-split ('k<um>a-kʉnʉ' would
     give base 'k-a-kʉnʉ', three pieces against a two-piece gloss).

  18 give an unsegmented word a single mirror morpheme (POL-023)
     Within a sentence that still carries morphological parsing -- some words
     analysed, some not -- an unanalysed word gets one M mirroring its FORM and
     glosses, which is what repair_empty_morphemes.py does. A sentence with no
     M at all gets none: it is either unanalysed in the source, or step 20
     withdrew its morpheme tier, and a flat mirror must not stand in for an
     analysis that was found unsupportable.

     Caveat for the table: tests 7, 10 and 12 are scored per M, so mirrors
     enlarge the denominator with morphemes that pass trivially. Movement in
     those three rows after this step is dilution, not improvement.

  19 repair truncated free translations (MALFORMED_TRANSLATIONS)
     The scrape cut some Chinese free translations off mid-parenthetical,
     leaving an unclosed '(' and a sentence fragment ('她的小孩正在哭.(說話者看
     到/知道,也可能只聽到小孩的哭聲而沒'). The reviewed replacement keeps the
     translation and drops the truncated remainder. Applied only when the
     current text matches the recorded EXPECTED exactly, so it fails closed if
     the upstream text changes.

  21 strip transcription markup from forms
     ORDERING: must run AFTER step 1, for the same reason step 11 must.
     strip_prosodic_markers removes square brackets, which are grammar's
     constituent brackets; stripping them first leaves step 1 unable to pair a
     label with its closing bracket, so '[tarukuka]中心語=musu' becomes
     'tarukuka中心語=musu' -- a label the end-anchored role regex cannot reach
     because the cell ends in a clitic. Step 20 then withdraws the whole word
     tier, hiding the damage as a coverage loss.

     Prosodic and breath markers, and code-switch tags naming the source
     language of a borrowed word. Reuses strip_prosodic_markers and strip_l2m
     from the corpus's own utils.py, keeping the word and dropping only the
     tag, with the fact of the switch recorded as notes="code-switch" on the
     form (parse_stories.py's convention). Grammar carries only one such tag,
     but it is the last V067 finding -- an M FORM of '<L2JsansiciguL2J>' that
     convert_infix_notation rightly refuses to treat as an infix.

  8  strip prompt prefixes from the sentence form
     Question-and-answer examples print a prompt in front of the sentence
     ('問：tayza i taypey kisu haw?'). The prompt is apparatus, not the sentence.

  9  strip role labels from the sentence form
     The same role labels step 1 removes from word forms also appear appended to
     words in the sentence form ('a wacu中心語 .'), where step 1 never looked.

 10  move parenthesised source annotations out of the sentence form
     A2 headwords carry annotations such as '（日語）' marking a Japanese loan.
     Unlike a role label this is lexicographic content, so it is moved to the
     sentence's notes rather than deleted.

  2  render A2 vocabulary lists as sentences with no word tier
     An A2 record is a dictionary entry, not a sentence: 'ori' is the indigenous
     headword and the single gloss row's first column is its Chinese meaning,
     not a word gloss. Treating that column positionally as a word form (as the
     naive conversion does) puts Chinese in a FORM, leaves the TRANSL empty and
     loses the sentence-level translation. So the headword becomes the S FORM,
     the Chinese becomes the sentence-level TRANSL, and no W is emitted.

     A2 is identified by filename, which is the convention the published
     pipeline also relies on (is_wordlist="A2" in source.name).
"""
from __future__ import annotations

import argparse
import copy
import sys
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from xml.etree import ElementTree as ET

_REPO_ROOT = Path(__file__).resolve().parents[4]   # <bank>/Corpora/<C>/CodeAndDocs/pipeline/
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.cleaning.clean_xml import swap_punctuation

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
# The gloss/word test helpers live in qa/, which is their single home;
# the builders reuse them rather than carrying a second copy.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "qa"))
from utils import (resolve_ungrammatical_parens, expand_infixes,
                   strip_l2m, strip_prosodic_markers)
from grammar_xml_tests import clitic_alignment, morpheme_count, MARKERS

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
ET.register_namespace("xml", "http://www.w3.org/XML/1998/namespace")
SPLIT = re.compile(r"[-=]")
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿]")

# Grammatical role labels attested as trailing annotations in the form column.
# Compositional: an optional case prefix plus a role, which covers all 30
# attested surface forms including 主格處所, which occurs only as a whole cell.
# If this step is promoted into the real pipeline the vocabulary belongs in a
# data file (POL-039).
CASE_PREFIXES = ["主格", "屬格", "斜格"]
ROLES = [
    "主事者", "受事者", "使動者", "被使動者", "受動者", "受惠者", "受役物",
    "經驗者", "擁有者", "擁有物", "謂語", "名詞謂語", "中心語", "關係子句",
    "延伸名詞組", "主語", "主體", "基準體", "工具", "處所", "時間", "目標",
    "接受者",
]
_ROLES_ALT = ("(?:(?:" + "|".join(CASE_PREFIXES) + ")?"
              "(?:" + "|".join(sorted(ROLES, key=len, reverse=True)) + "))+")
# A role label sitting immediately inside or outside a closing bracket.
_LABEL_AT_CLOSE = re.compile(rf"(?:{_ROLES_ALT}\]|\]{_ROLES_ALT})")
# A coindexation subscript on a bracketed constituent: '[aku]i'.
_COINDEX = re.compile(r"\]i(?=\s*$)")
# A role label appended to a bare word, no bracket involved.
_ROLE_RE = re.compile(rf"{_ROLES_ALT}\s*$")


def step1_brackets(form: str) -> str:
    """Remove constituent bracketing: brackets, their labels, coindex subscripts.

    Bracket content is kept, including a clitic that trails the label
    ('[tarukuka]中心語=musu' -> 'tarukuka=musu'). A cell that was nothing but a
    labelled closing bracket (']基準體') reduces to empty and its row is dropped
    by the caller.
    """
    s = _COINDEX.sub("]", form or "")
    s = _LABEL_AT_CLOSE.sub("]", s)
    s = s.replace("[", "").replace("]", "")
    return _ROLE_RE.sub("", s)


STEPS = {
    1: "remove constituent bracketing, role labels and coindex subscripts",
    2: "render A2 vocabulary lists as sentences with no word tier",
    3: "apply pinned source-record repairs",
    4: "strip footnote markers from the sentence form",
    5: "emit no word tier for unglossed sentences",
    6: "join fixed English compound glosses with '.'",
    7: "convert a gloss separator when it makes the morpheme counts match",
    8: "strip prompt prefixes from the sentence form",
    9: "strip role labels from the sentence form",
   10: "move parenthesised source annotations out of the sentence form",
   11: "canonicalize punctuation (POL-010/011/013) via clean_xml",
   12: "resolve POL-017 grammaticality parentheses in the sentence form",
   13: "close the space before sentence-final punctuation",
   14: "suppress sentence blocks recorded as irreconcilable",
   15: "rebuild the sentence form from the word tier for cited excerpts",
   16: "split an unglossed optional parenthetical into a second sentence",
   17: "expand infix notation into its own morphemes",
   18: "give an unsegmented word a single mirror morpheme (POL-023)",
   19: "repair truncated free translations (MALFORMED_TRANSLATIONS)",
   20: "withdraw a word or morpheme analysis the tiers do not support",
   21: "strip transcription markup from forms",
   22: "reassign glosses stranded on a form-less morpheme, then drop the shell",
}

# The corpus's own repair table is the single source of truth; p3 reads it
# rather than copying the cases. main applies it via repair_source_fields.py,
# which is fail-closed on the whole-corpus file layout and so cannot run
# against a grammar-only tree.
def prune_unsupported(sentence, stats: dict) -> None:
    """Withdraw an analysis the sentence's own tiers do not support.

    Two levels, applied in order:

    * A sentence whose word tier does not account for its sentence form
      (test 3) loses its W elements entirely. The word tier claims an
      alignment with the sentence that does not hold, so it is not published.
    * A sentence that does account for its words, but whose morphemes fail
      test 6, 7 or 12 -- a morpheme missing, unglossed, or form-less -- loses
      its M elements only. The word tier stands; the finer analysis does not.

    Run before the mirror step, so a sentence stripped of morphemes is given
    flat one-M-per-word mirrors rather than left bare. That is the same
    withdrawal repair_empty_morphemes.py performs in its third branch.
    """
    def orig(el):
        node = el.find("FORM[@kindOf='original']")
        return "".join(node.itertext()) if node is not None else ""

    words = sentence.findall("W")
    if not words:
        return
    s_form = orig(sentence)
    forms = [orig(w) for w in words]

    if not clitic_alignment(s_form, forms):
        for w in words:
            sentence.remove(w)
        stats["20 sentences whose W tier was withdrawn"] = stats.get(
            "20 sentences whose W tier was withdrawn", 0) + 1
        stats["20   W elements deleted"] = stats.get("20   W elements deleted", 0) + len(words)
        return

    bad = False
    for w, w_form in zip(words, forms):
        ms = w.findall("M")
        formed = [m for m in ms if orig(m).strip()]
        if MARKERS.search(w_form) and len(formed) != morpheme_count(w_form):
            bad = True                                    # test 6
        formed_ms = [m for m in ms if orig(m).strip()]
        unglossed = [m for m in formed_ms
                     if not any((t.text or "").strip() for t in m.findall("TRANSL"))]
        for m in ms:
            if not orig(m).strip():
                bad = True                                # test 12
                # Only a PARTIAL gap counts. A word whose morphemes are
                # uniformly unglossed is segmentation published without
                # morpheme glosses -- YeddaPalemeqBlog does this for 3,906
                # glossed words -- and withdrawing it would delete valid
                # analysis. A gap in an otherwise glossed word is the
                # misalignment this rule is for.
        if unglossed and len(unglossed) != len(formed_ms):
            bad = True                                    # test 7
    if bad:
        n = 0
        for w in words:
            for m in w.findall("M"):
                w.remove(m); n += 1
        stats["20 sentences whose M tier was withdrawn"] = stats.get(
            "20 sentences whose M tier was withdrawn", 0) + 1
        stats["20   M elements deleted"] = stats.get("20   M elements deleted", 0) + n


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


def load_malformed_translations(json_dir: Path) -> dict:
    """{(sentence id, lang): (expected, replacement)} for every subcorpus."""
    # Sits beside the source JSONs, in the corpus's CodeAndDocs. Introduced by
    # PR #161, so it is absent from a plain main checkout.
    path = json_dir.parent / "source_repairs.xml"
    if not path.exists():
        return {}
    root = ET.parse(str(path)).getroot()
    section = root.find("MALFORMED_TRANSLATIONS")
    out = {}
    for case in [] if section is None else section.findall("CASE"):
        # No subcorpus filter: the table holds 10 grammar, 4 sentence and 7
        # story cases, and each pipeline should apply the ones whose sentence id
        # it actually emits. Filtering to Grammar meant sentences and stories
        # loaded nothing at all.
        out[(case.get("sentenceId"), case.get(XML_LANG))] = (
            case.findtext("EXPECTED") or "", case.findtext("REPLACEMENT") or "")
    return out

# An optional word the source wraps in parentheses: '(kara)', '(sua)'.
_OPTIONAL = re.compile(r"\(([^()*]+)\)")

# A citation standing where the sentence text should be: the grammar quotes an
# excerpt from another corpus, so the sentence form holds the reference while
# the word tier carries the actual transcript.
_CITATION = re.compile(r"^\s*\(\s*NTU Formosan Corpus\b[^)]*\)\s*$")
# Conversational transcription apparatus carried on the quoted word forms:
# an intonation-unit number, a pause timing, a prominence mark, and the
# unit-final backslash.
_IU_NUMBER = re.compile(r"^\d+\.{2,}")
_PAUSE = re.compile(r"[（(]\d+\.\d+[）)]")
_IU_TRAILING = re.compile(r"\\+$")


def unglossed_optional(s_form: str, rows: list) -> str | None:
    """The optional word in *s_form* that the word tier does not gloss."""
    # Strip parentheses AND trailing punctuation: the word tier may render the
    # optional word as 'mesa,' where the sentence writes '(mesa)', and treating
    # those as different would wrongly call the word unglossed.
    glossed = {re.sub(r"[()]", "", str(r[0])).strip(" .,;:!?\u3001\uff0c").lower()
               for r in rows if r}
    for match in _OPTIONAL.finditer(s_form):
        word = match.group(1).strip()
        if not word or HAN.search(word) or " " in word:
            continue
        if word.lower() not in glossed:
            return word
    return None


def step15_sentence_from_words(forms: list) -> str:
    """Reconstruct the sentence text from quoted word forms."""
    words = []
    for form in forms:
        text = _IU_TRAILING.sub("", _PAUSE.sub("", _IU_NUMBER.sub("", form)))
        text = text.replace("^", "").strip()
        if text:
            words.append(text)
    return " ".join(words)

# Sentence blocks whose two tiers cannot be reconciled: the word tier carries
# words with no counterpart in the sentence, or vice versa, and no rule
# explains the difference. Suppressed at the end of the pipeline rather than
# published half-aligned. Each entry records why.
IRRECONCILABLE = {
    # key: "<language dir>/<file stem>_S_<record id>"
    "Kanakanavu_Kanakanavu/07_S_4":
        "word tier has 'sua' with no counterpart in the sentence",
    "Kanakanavu_Kanakanavu/06_S_55":
        "word tier has 'sua' with no counterpart in the sentence",
    "Kanakanavu_Kanakanavu/12_S_16":
        "word tier has 'sinatʉ isi' with no counterpart in the sentence",
    "Kanakanavu_Kanakanavu/14_S_17":
        "word tier has 'ísua' with no counterpart in the sentence",
    "Kanakanavu_Kanakanavu/15_S_29":
        "word tier reads 'Vanau=kara'; the sentence has bare 'Vanau'",
    "Kanakanavu_Kanakanavu/13_S_41":
        "sentence has 'esi' with no word-tier counterpart",
    "Sakizaya_Sakizaya/14_S_16":
        "sentence has a second 'tu' with no word-tier counterpart",
}

# Prompts printed in front of an example in a question-and-answer pair. Both
# the Han form '問：' and the Latin 'Q:'/'A:' occur; an 'A:' may appear mid-form
# where a question and its answer share one record, so these are stripped
# wherever they fall, not only at the start.
PROMPT_PREFIXES = ["問：", "問:", "Q:", "Q：", "A:", "A："]

# Parenthesised annotations the source prints against a headword. These are
# content, not druff -- '（日語）' records that the entry is a Japanese loan --
# so they move to the sentence's notes rather than being deleted. Two are
# etymological, two are editorial.
SOURCE_ANNOTATIONS = {
    "日語": "Japanese loanword",
    "借詞": "loanword",
    "已發生": "已發生",
    "需再確認": "需再確認",
}
_ANNOTATION_RE = re.compile(
    r"\s*[（(]\s*(" + "|".join(SOURCE_ANNOTATIONS) + r")\s*[）)]")
# In the sentence form a role label may be followed by punctuation
# ('Panayan中心語,'), so it cannot be matched at end-of-token alone.
_ROLE_IN_SENTENCE = re.compile(_ROLES_ALT + r"(?=[.,;:!?\u3001\uff0c\u3002]*\s*$)")

# English compounds whose internal hyphens are orthography, not morpheme
# boundaries. Written with '.' so they count as the single gloss they are.
COMPOUND_GLOSSES = [
    "sister-in-law", "brother-in-law", "son-in-law", "daughter-in-law",
    "bride-to-be",
]


def step6_compounds(gloss: str) -> str:
    for compound in COMPOUND_GLOSSES:
        if compound in gloss:
            gloss = gloss.replace(compound, compound.replace("-", "."))
    return gloss


def gloss_bigrams(gloss: str):
    """Adjacent gloss atoms and the separator between them."""
    parts = re.split(r"([-.])", gloss)
    for i in range(1, len(parts) - 1, 2):
        if parts[i - 1] and parts[i + 1]:
            yield parts[i - 1], parts[i], parts[i + 1]


def build_attestation(json_dir: Path, clean=None) -> dict:
    """{(A, B, separator): count} over every gloss in the corpus.

    Built from the whole corpus -- grammar, sentence and story -- when they sit
    alongside each other, because a spelling attested only in the story files is
    still evidence about the convention.

    `clean` is the same normalization the pipeline applies to a gloss cell
    before the flip is attempted (markup stripping, punctuation canonicalization).
    Without it the pool is built from raw JSON while the lookup is done on
    cleaned text, so a bigram whose separator or neighbours were changed by the
    cleanup can never match its own evidence.
    """
    root = json_dir.parent if (json_dir.parent / "sentence").exists() else json_dir
    dirs = [d for d in (root / "grammar", root / "sentence", root / "story") if d.exists()] or [json_dir]
    counts: dict = {}
    for d in dirs:
        for path in d.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            recs = data if isinstance(data, list) else (list(data.values())[0] if data else [])
            if not isinstance(recs, list):
                continue
            for rec in recs:
                if not (isinstance(rec, list) and len(rec) > 1 and isinstance(rec[1], dict)):
                    continue
                for row in rec[1].get("gloss") or []:
                    if not isinstance(row, list):
                        continue
                    for cell in row[1:]:
                        text = clean(str(cell)) if clean else str(cell)
                        for a, sep, b in gloss_bigrams(text):
                            counts[(a, b, sep)] = counts.get((a, b, sep), 0) + 1
    return counts


_INFIX_GLOSS = re.compile(r"<[^>]+>")


def _gloss_pieces(gloss: str) -> int:
    """Morphemes a gloss claims: [-=] pieces plus one per infix gloss."""
    return (len([x for x in SPLIT.split(gloss) if x])
            + len(_INFIX_GLOSS.findall(gloss or "")))


def step7_align_separator(form: str, gloss: str, attested: dict) -> str:
    """Flip one gloss separator, but only for an exact morpheme-count match.

    A flip is allowed only if the competing spelling is attested somewhere in the
    corpus; a single attestation is enough, because the evidence that matters is
    that the flip makes the gloss agree exactly with the segmentation.
    """
    # Count morphemes the way the test and the withdrawal step do. Splitting on
    # [-=] alone counts "<um>" in the form but not "<主事焦點>" in the gloss, so
    # for every infixed word this step aimed at a target the test would still
    # reject -- and disagreed with the prune, which decides M-suppression on
    # morpheme_count.
    n_form = morpheme_count(form) if form.strip() else 0
    if not n_form or _gloss_pieces(gloss) == n_form:
        return gloss
    for a, sep, b in gloss_bigrams(gloss):
        other = "." if sep == "-" else "-"
        if not attested.get((a, b, other)):
            continue
        candidate = gloss.replace(f"{a}{sep}{b}", f"{a}{other}{b}", 1)
        if _gloss_pieces(candidate) == n_form:
            return candidate
    return gloss

# A footnote reference printed against the end of a sentence: 'sua cina.25',
# 'soni!15'. The punctuation before the digits is the sentence's own -- '!15'
# sits on an imperative whose free translation ends in '！' -- so only the
# digits are removed.
_FOOTNOTE = re.compile(r"(?<=[^\W\d_])([.!?])?\d+\s*$")


def load_record_repairs(path: Path) -> dict:
    """{(source file suffix, record id): {digest, replacement}} from the XML."""
    if not path.exists():
        return {}
    root = ET.parse(str(path)).getroot()
    out = {}
    for case in root.iter("CASE"):
        key = (case.get("sourceFile"), int(case.get("recordId")))
        replacement = json.loads(case.findtext("REPLACEMENT_JSON") or "")
        out[key] = {"digest": case.get("sourceDigest"), "replacement": replacement}
    return out


def record_digest(record) -> str:
    raw = json.dumps(record, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def apply_record_repairs(records: list, src_key: str, repairs: dict, stats: dict) -> list:
    """Replace pinned records. Fails closed if the source has drifted."""
    applicable = [(k, v) for k, v in repairs.items() if src_key.endswith(k[0])]
    if not applicable:
        return records
    out = list(records)
    for (source_file, record_id), repair in applicable:
        matches = [(i, r) for i, r in enumerate(out) if r and r[0] == record_id]
        if len(matches) != 1:
            raise RuntimeError(
                f"expected one record {record_id} in {source_file}, got {len(matches)}")
        i, record = matches[0]
        found = record_digest(record)
        if found != repair["digest"]:
            raise RuntimeError(
                f"source drifted for {source_file}:{record_id}; "
                f"expected {repair['digest']}, found {found}")
        out[i] = copy.deepcopy(repair["replacement"])
        stats["3 pinned records repaired"] = stats.get("3 pinned records repaired", 0) + 1
    return out


def has_han(text: str | None) -> bool:
    return bool(HAN.search(text or ""))


def add_transl(parent, lang: str, text: str):
    el = ET.SubElement(parent, "TRANSL")
    el.set(XML_LANG, lang)
    el.text = text
    return el




# A slash alternative whose alternant is starred is an ungrammatical variant the
# source offers for contrast: 'patuelre/*makanaelre'. POL-016 keeps ungrammatical
# material out of the published form, and the expander cannot resolve it (it
# raises "residual slash after expand"). Deleting the starred alternant leaves
# the grammatical word. Only slash-adjacent stars are touched: '*(X)' and '(*X)'
# are POL-017 obligatory/forbidden marking and are handled elsewhere.
_STARRED_ALT = re.compile(r"/\*[^\s/()]+|(?<![\w)])\*[^\s/()]+/")



# A free translation sometimes carries two readings, one starred as unavailable:
#   "All the boys ate two fish each. / *All the boys ate the fish two by two."
#   "All the children took fish. (*Children took all the fish.)"
# The star marks a reading the sentence CANNOT have, so the starred half is not
# a translation of this sentence and is deleted.
_STARRED_PAREN = re.compile(r"\s*[(（]\s*\*[^)）]*[)）]")


def drop_starred_readings(text: str) -> str:
    text = _STARRED_PAREN.sub("", text or "")
    if "/" in text and "*" in text:
        parts = [p for p in text.split("/")]
        kept = [p for p in parts if not p.strip().startswith("*")]
        if kept and len(kept) != len(parts):
            text = "/".join(kept)
    return " ".join(text.split()).strip()



_FINAL_PUNCT = re.compile(r"[.!?。！？]\s*$")
_LIT = re.compile(r"^\s*[(（]\s*lit\.?\s*[)）]\s*", re.I)


def load_free_repairs(path=None) -> dict:
    """{(file_stem, record, lang): action} from free_translation_repairs.tsv."""
    p = Path(path) if path else Path(__file__).with_name("free_translation_repairs.tsv")
    out: dict = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = [c.strip() for c in line.split("\t") if c.strip() != ""]
        if len(parts) == 4:
            stem, rec, lang, action = parts
            out[(stem, rec, lang)] = action
    return out


def free_entries(free: list, stem: str, rid: str, repairs: dict) -> list:
    """Resolve a record's free-translation lines into (lang, text, ver, note).

    Four shapes the source uses, none of them a second translation of the same
    sentence except the last:

    * a line-WRAP -- one translation broken across two lines, recognised by the
      earlier line not ending in sentence-final punctuation. Joined.
    * a metalinguistic NOTE ('usa "where" usually is "isa"'), pinned in the
      repair table because no shape distinguishes it. Moves to @notes.
    * a MIS-SLOTTED language: a Latin-script line sitting in the zho slot while
      a Han line waits in the same slot. Re-slotted.
    * a genuine literal ALTERNATIVE, marked '(lit.)'. Kept, with ver='alt' and
      the marker moved to @notes -- it labels the translation, it is not part
      of it.
    """
    by_lang: dict = {"zho": [], "eng": []}
    notes: list = []
    for line in free or []:
        if line.startswith("#c"):
            by_lang["zho"].append(line[2:].strip())
        elif line.startswith("#e"):
            by_lang["eng"].append(line[2:].strip())
        elif line.startswith("#n"):
            notes.append(line[2:].strip())

    if repairs.get((stem, rid, "*")) == "drop_all":
        return [], notes

    # Mis-slotted: a Latin-only line in the zho slot beside a Han line.
    zho = by_lang["zho"]
    if len(zho) > 1 and HAN.search(zho[-1]) and not HAN.search(zho[0]):
        by_lang["eng"] = [zho[0]] + by_lang["eng"]
        by_lang["zho"] = zho[1:]

    out = []
    for lang in ("zho", "eng"):
        lines = [t for t in by_lang[lang] if t]
        if not lines:
            continue
        if repairs.get((stem, rid, lang)) == "note":
            notes.extend(lines[1:])
            lines = lines[:1]
        # Join wraps: the earlier line does not close a sentence.
        joined = [lines[0]]
        for nxt in lines[1:]:
            if not _FINAL_PUNCT.search(joined[-1]) and not _LIT.match(nxt):
                joined[-1] = (joined[-1] + " " + nxt).strip()
            else:
                joined.append(nxt)
        for i, text in enumerate(joined):
            note = ""
            if _LIT.match(text):
                text, note = _LIT.sub("", text).strip(), "lit."
            out.append((lang, drop_starred_readings(text), "alt" if i else "", note))
    return out, notes


def drop_starred_alternatives(text: str) -> str:
    return _STARRED_ALT.sub("", text or "")


def conform_sentence(root, stats: dict) -> None:
    """Bring every S into line with the closed attribute surface (POL-053).

    Three defects the repo's validators catch that the pipeline used to emit:

    * ``S/@notes`` -- the XSD allows @notes on FORM and TRANSL only (V000).
      A sentence-level note moves onto the sentence's original FORM.
    * two TRANSL children in the same language with no @ver to tell them
      apart (V085) -- they are numbered in document order.
    * an S whose original FORM has no content (V017). It is rebuilt from the
      word tier if that has anything; a sentence that is nothing but
      transcription apparatus is dropped rather than published empty.
    """
    XL = "{http://www.w3.org/XML/1998/namespace}lang"
    for s in list(root.findall("S")):
        # The attribute is forbidden on S whatever its value, so it is always
        # removed; only a note with content is worth carrying over. An empty
        # notes="" still fails the XSD.
        note = s.get("notes")
        if note is not None:
            del s.attrib["notes"]
        if note and note.strip():
            form = s.find("FORM[@kindOf='original']")
            if form is None:
                form = s.find("FORM")
            if form is not None:
                merged = ((form.get("notes") or "") + " " + note).strip()
                form.set("notes", merged)
                stats["conform: S notes moved to FORM"] = stats.get(
                    "conform: S notes moved to FORM", 0) + 1

        by_lang: dict = {}
        for t in s.findall("TRANSL"):
            by_lang.setdefault(t.get(XL), []).append(t)
        for lang, group in by_lang.items():
            if len(group) < 2:
                continue
            # V084 allows exactly one @ver value, "alt" (the 2026-06-01 Bril
            # convention). The first translation is the primary and carries
            # nothing; every later one in the same language is the alternate.
            for t in group[1:]:
                if not t.get("ver"):
                    t.set("ver", "alt")
            stats["conform: same-language TRANSLs given @ver"] = stats.get(
                "conform: same-language TRANSLs given @ver", 0) + 1

        form = s.find("FORM[@kindOf='original']")
        if form is None:
            form = s.find("FORM")
        if form is not None and not (form.text or "").strip():
            rebuilt = " ".join(
                "".join(w.find("FORM").itertext()).strip()
                for w in s.findall("W")
                if w.find("FORM") is not None
            ).strip()
            if rebuilt:
                form.text = rebuilt
                stats["conform: empty S FORM rebuilt from the word tier"] = stats.get(
                    "conform: empty S FORM rebuilt from the word tier", 0) + 1
            else:
                root.remove(s)
                stats["conform: S dropped (nothing but transcription apparatus)"] = stats.get(
                    "conform: S dropped (nothing but transcription apparatus)", 0) + 1





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

# The NTU backend's "no audio file" sentinel, decoded and URL-encoded.
_AUDIO_SENTINELS = ("\u6c92\u6709\u97f3\u6a94",
                    "%E6%B2%92%E6%9C%89%E9%9F%B3%E6%AA%94")


def load_audio_overrides(path=None) -> dict:
    """{source url: (action, replacement url, file attribute)} from the TSV.

    Taken verbatim from the PR's parse_grammar.py, which the published corpus
    follows: one url is renamed (and its file attribute written decoded), and
    eleven name sources that are unavailable and must not be published at all.
    Kept as data rather than python (POL-039).
    """
    p = Path(path) if path else Path(__file__).with_name("audio_overrides.tsv")
    out: dict = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        cells = (line.split("\t") + ["", "", ""])[:4]
        out[cells[0].strip()] = (cells[1].strip(), cells[2].strip(), cells[3].strip())
    return out


AUDIO_OVERRIDES = load_audio_overrides()

def build(records: list, text_id: str, steps: set[int], stats: dict,
          src_key: str = "", repairs: dict | None = None,
          attested: dict | None = None,
          malformed: dict | None = None, language: str = "", dialect: str = "unknown") -> ET.Element:
    is_wordlist = "A2" in text_id
    lang_dir = src_key.split("/")[-2] if "/" in src_key else ""
    if 3 in steps and repairs:
        records = apply_record_repairs(records, src_key, repairs, stats)
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
        # RETIRED. Step 14 used to delete the whole S when its word tier could
        # not be reconciled with the sentence -- discarding the sentence, its
        # translation and its audio to avoid publishing one bad analysis. The
        # prune already withdraws just the W tier in exactly this case, which
        # keeps everything that was good. Six Kanakanavu sentences and their
        # recordings were being lost this way; the published corpus keeps them.
        if False and f"{lang_dir}/{text_id}_S_{rid}" in IRRECONCILABLE:
            stats["14 irreconcilable blocks suppressed"] = stats.get(
                "14 irreconcilable blocks suppressed", 0) + 1
            continue
        s = ET.SubElement(root, "S")
        s.set("id", f"{text_id}_S_{rid}")
        form = ET.SubElement(s, "FORM")
        form.set("kindOf", "original")
        s_form = " ".join(str(t) for t in (body.get("ori") or []))
        if 21 in steps:
            # The sentence form needs the same markup stripping the word forms
            # get. Step 21 only ever ran per word, so a grammar sentence kept
            # its code-switch tags and lengthening: 13_S_48 published
            # '<L2JsansiciguL2J>' and 'cali==w' in the S FORM.
            cleaned, _ = strip_l2m(strip_prosodic_markers(s_form))
            cleaned = re.sub(r"={2,}", "", cleaned)
            if cleaned.strip() != s_form:
                stats["21 sentence forms cleaned of markup"] = stats.get(
                    "21 sentence forms cleaned of markup", 0) + 1
                s_form = " ".join(cleaned.split())

        if 15 in steps and _CITATION.match(s_form):
            rebuilt = step15_sentence_from_words(
                [str(r[0]) for r in (body.get("gloss") or [])
                 if isinstance(r, list) and r])
            if rebuilt:
                s.set("notes", (s_form.strip() + " " + (s.get("notes") or "")).strip())
                # The rebuild comes from raw word cells, which still carry their
                # code-switch tags and lengthening, so it needs the same
                # stripping the ori path got a few lines above.
                if 21 in steps:
                    rebuilt, _ = strip_l2m(strip_prosodic_markers(rebuilt))
                    rebuilt = " ".join(re.sub(r"={2,}", "", rebuilt).split())
                s_form = rebuilt
                stats["15 sentence forms rebuilt from the word tier"] = stats.get(
                    "15 sentence forms rebuilt from the word tier", 0) + 1

        if 8 in steps:
            for prefix in PROMPT_PREFIXES:
                if prefix in s_form:
                    s_form = s_form.replace(prefix, " ")
                    stats["8 prompt prefixes stripped"] = stats.get(
                        "8 prompt prefixes stripped", 0) + 1
            s_form = " ".join(s_form.split())

        if 12 in steps:
            # Canonicalize ONLY the bracket characters first. Step 12 runs 5th
            # and full punctuation canonicalization (step 11) 9th, so without
            # this the POL-017 handler cannot see the fullwidth parentheses in
            # 16 grammar records. A reorder is not an option: swap_punctuation
            # also maps "[" -> "(", which would hide constituent brackets from
            # step 1 and merge them with the POL-017 parentheses.
            for wide, ascii_ in (("（", "("), ("）", ")"), ("【", "("), ("】", ")"),
                                 ("〔", "("), ("〕", ")")):
                s_form = s_form.replace(wide, ascii_)
            resolved = resolve_ungrammatical_parens(s_form)
            if resolved != s_form:
                stats["12 grammaticality parens resolved"] = stats.get(
                    "12 grammaticality parens resolved", 0) + 1
                s_form = " ".join(resolved.split())

        if 9 in steps:
            cleaned = " ".join(_ROLE_IN_SENTENCE.sub("", tok) for tok in s_form.split())
            if cleaned != s_form:
                stats["9 role labels stripped from S FORM"] = stats.get(
                    "9 role labels stripped from S FORM", 0) + 1
                s_form = cleaned

        if 10 in steps:
            found = _ANNOTATION_RE.findall(s_form)
            if found:
                s_form = _ANNOTATION_RE.sub("", s_form).strip()
                note = "; ".join(SOURCE_ANNOTATIONS[f] for f in found)
                s.set("notes", ((s.get("notes") or "") + " " + note).strip())
                stats["10 source annotations moved to notes"] = stats.get(
                    "10 source annotations moved to notes", 0) + len(found)

        if 4 in steps and _FOOTNOTE.search(s_form):
            s_form = _FOOTNOTE.sub(lambda m: m.group(1) or "", s_form)
            stats["4 footnote markers stripped"] = stats.get(
                "4 footnote markers stripped", 0) + 1
        if 11 in steps:
            canon = swap_punctuation(s_form)
            if canon != s_form:
                stats["11 S FORMs canonicalized"] = stats.get(
                    "11 S FORMs canonicalized", 0) + 1
                s_form = canon
        if 13 in steps:
            closed = re.sub(r"\s+([.,;:!?])(\s*)$", r"\1\2", s_form)
            if closed != s_form:
                stats["13 detached final punctuation closed"] = stats.get(
                    "13 detached final punctuation closed", 0) + 1
                s_form = closed
        form.text = s_form

        entries, free_notes = free_entries(body.get("free") or [], text_id, rid,
                                           FREE_REPAIRS)
        # AUDIO: the grammar source gives a public url per record. The NTU
        # backend marks a missing recording with the sentinel filename
        # 沒有音檔 ("no audio file"), URL-encoded in older parses and decoded
        # since 2026-07-29; both forms are suppressed rather than published.
        audio_url = str(body.get("audio_url") or "").strip()
        action, replacement, file_attr = AUDIO_OVERRIDES.get(audio_url, ("", "", ""))
        if action == "suppress":
            audio_url = ""
            stats["AUDIO suppressed (source unavailable)"] = stats.get(
                "AUDIO suppressed (source unavailable)", 0) + 1
        elif action == "url":
            audio_url = replacement
        if audio_url and not any(t in audio_url for t in _AUDIO_SENTINELS):
            audio = ET.SubElement(s, "AUDIO")
            audio.set("file", file_attr or audio_url.rsplit("/", 1)[-1])
            audio.set("url", audio_url)
            stats["AUDIO elements written"] = stats.get("AUDIO elements written", 0) + 1
        elif audio_url:
            stats["AUDIO suppressed (no-audio sentinel)"] = stats.get(
                "AUDIO suppressed (no-audio sentinel)", 0) + 1
        for lang, text, ver, note in entries:
            el = add_transl(s, lang, text)
            if ver:
                el.set("ver", ver)
            if note:
                el.set("notes", note)
        for note in free_notes:
            s.set("notes", ((s.get("notes") or "") + " " + note).strip())

        if 19 in steps and malformed:
            for transl in s.findall("TRANSL"):
                key = (s.get("id"), transl.get(XML_LANG))
                case = malformed.get(key)
                # The recorded EXPECTED is in main's canonicalized punctuation
                # (ASCII '.', '('), while p3 has not canonicalized the
                # sentence-level TRANSL. Compare through swap_punctuation so the
                # reviewed decision applies without settling that separately.
                if case and (swap_punctuation((transl.text or "").strip())
                             == swap_punctuation(case[0].strip())):
                    transl.text = case[1]
                    stats["19 truncated translations repaired"] = stats.get(
                        "19 truncated translations repaired", 0) + 1

        rows = [r for r in (body.get("gloss") or []) if isinstance(r, list) and r]

        if 5 in steps and rows and all(
                str(r[0]).strip() == "_" and not any(str(c).strip() for c in r[1:])
                for r in rows):
            stats["5 unglossed sentences given no W tier"] = stats.get(
                "5 unglossed sentences given no W tier", 0) + 1
            continue

        if 2 in steps and is_wordlist:
            # The entry's Chinese meaning, not a word gloss.
            meaning = str(rows[0][0]).strip() if rows else ""
            if meaning:
                add_transl(s, "zho", meaning)
                stats["2 A2 entries routed to sentence TRANSL"] = stats.get(
                    "2 A2 entries routed to sentence TRANSL", 0) + 1
            continue

        optional = unglossed_optional(s_form, rows) if 16 in steps else None
        if optional:
            def _resolve(text, keep):
                """Drop or unwrap the optional parenthetical; leave others alone."""
                out = _OPTIONAL.sub(
                    lambda m: (m.group(1) if keep else "")
                    if m.group(1).strip() == optional else m.group(0), text)
                return " ".join(out.split())

            source_form = s_form
            # This block becomes the reading WITHOUT the optional word: that is
            # what the word tier below actually glosses.
            s_form = _resolve(source_form, keep=False)
            form.text = s_form

            variant = ET.SubElement(root, "S")
            variant.set("id", f"{text_id}_S_{rid}-alt")
            variant.set("notes", f"optional element '{optional}' present; the "
                                 "source gives it no gloss, so this reading "
                                 "carries no word tier")
            vform = ET.SubElement(variant, "FORM")
            vform.set("kindOf", "original")
            vform.text = _resolve(source_form, keep=True)
            for line in body.get("free") or []:
                if line.startswith("#c"):
                    add_transl(variant, "zho", drop_starred_readings(line[2:]))
                elif line.startswith("#e"):
                    add_transl(variant, "eng", drop_starred_readings(line[2:]))
            stats["16 unglossed optional parentheticals split"] = stats.get(
                "16 unglossed optional parentheticals split", 0) + 1

        for i, row in enumerate(rows):
            w_form = str(row[0])
            zho = str(row[1]) if len(row) > 1 else ""
            eng = str(row[2]) if len(row) > 2 else ""

            code_switch = False

            if 6 in steps:
                for name, val in (("zho", zho), ("eng", eng)):
                    new = step6_compounds(val)
                    if new != val:
                        stats["6 compound glosses joined"] = stats.get(
                            "6 compound glosses joined", 0) + 1
                        if name == "zho": zho = new
                        else: eng = new

            if 1 in steps and not is_wordlist:
                stripped = step1_brackets(w_form)
                if stripped != w_form:
                    stats["1 cells debracketed / delabelled"] = stats.get(
                        "1 cells debracketed / delabelled", 0) + 1
                    w_form = stripped
            if (1 in steps and not (zho.strip() or eng.strip())
                    and w_form.strip() in ("", "ø", "\u2205")):
                # Nothing but a labelled closing bracket, or a bare null marker
                # left behind by one: a trace, and traces are not published.
                stats["1 rows dropped (bracket only)"] = stats.get(
                    "1 rows dropped (bracket only)", 0) + 1
                continue

            if 21 in steps:
                cleaned, is_cs = strip_l2m(strip_prosodic_markers(w_form))
                if cleaned.strip() != w_form:
                    stats["21 word forms cleaned of markup"] = stats.get(
                        "21 word forms cleaned of markup", 0) + 1
                    w_form = cleaned.strip()
                code_switch = is_cs
            else:
                code_switch = False

            if 11 in steps:
                for name, val in (("form", w_form), ("zho", zho), ("eng", eng)):
                    canon = swap_punctuation(val)
                    if canon != val:
                        stats["11 word cells canonicalized"] = stats.get(
                            "11 word cells canonicalized", 0) + 1
                        if name == "form": w_form = canon
                        elif name == "zho": zho = canon
                        else: eng = canon

            w = ET.SubElement(s, "W")
            w.set("id", f"{text_id}_S_{rid}_W{i}")
            wf = ET.SubElement(w, "FORM")
            wf.set("kindOf", "original")
            wf.text = w_form
            if code_switch:
                wf.set("notes", "code-switch")
            add_transl(w, "zho", zho)
            add_transl(w, "eng", eng)

            if 7 in steps and attested:
                for name, val in (("zho", zho), ("eng", eng)):
                    new = step7_align_separator(w_form, val, attested)
                    if new != val:
                        stats["7 gloss separators converted"] = stats.get(
                            "7 gloss separators converted", 0) + 1
                        if name == "zho": zho = new
                        else: eng = new

            parts = [p for p in SPLIT.split(w_form) if p]
            zparts = [p for p in SPLIT.split(zho) if p]
            eparts = [p for p in SPLIT.split(eng) if p]
            # An infixed word has at least two morphemes even when it carries
            # no '-' or '=' at all ('t<um>ʉpʉ'), so it must enter this loop too.
            has_infix = 17 in steps and bool(re.search(r"<[^>]+>", w_form))
            # A monomorphemic word is ANALYSED too: one morpheme carrying the
            # word's gloss. Recording the M states that; withholding it makes
            # "analysed as monomorphemic" indistinguishable from "never
            # analysed", which is the distinction POL-054 protects. An
            # unglossed word still gets nothing -- there the M would be invented.
            is_glossed = bool(zho.strip() or eng.strip())
            if (len(parts) > 1 or len(zparts) > len(parts) > 0 or has_infix
                    or (len(parts) == 1 and is_glossed)):
                for j in range(max(len(parts), len(zparts), len(eparts))):
                    piece = parts[j] if j < len(parts) else ""
                    mz = zparts[j] if j < len(zparts) else ""
                    me = eparts[j] if j < len(eparts) else ""
                    sub = expand_infixes(piece, me, mz) if 17 in steps else []
                    if len(sub) > 1:
                        stats["17 infixes expanded"] = stats.get(
                            "17 infixes expanded", 0) + 1
                        for n, (sf, se, sc) in enumerate(sub):
                            m = ET.SubElement(w, "M")
                            m.set("id", f"{text_id}_S_{rid}_W{i}M{j}_{n}")
                            mf = ET.SubElement(m, "FORM")
                            mf.set("kindOf", "original")
                            mf.text = sf
                            add_transl(m, "zho", sc)
                            add_transl(m, "eng", se)
                        continue
                    m = ET.SubElement(w, "M")
                    m.set("id", f"{text_id}_S_{rid}_W{i}M{j}")
                    if piece:
                        mf = ET.SubElement(m, "FORM")
                        mf.set("kindOf", "original")
                        mf.text = piece
                    else:
                        stats["surplus gloss pieces (form-less M)"] = stats.get(
                            "surplus gloss pieces (form-less M)", 0) + 1
                    add_transl(m, "zho", mz)
                    add_transl(m, "eng", me)

        if 22 in steps:
            reassign_glosses(s, stats)

        if 20 in steps:
            prune_unsupported(s, stats)

        if 18 in steps and any(w.findall("M") for w in s.findall("W")):
            # Only where the sentence still carries morphological parsing --
            # some words analysed, some not. A sentence with no M at all is
            # either unanalysed in the source or had its morpheme tier
            # withdrawn by step 20; in neither case should a flat mirror be
            # invented to stand in for an analysis that is not there.
            for i, w in enumerate(s.findall("W")):
                if w.findall("M"):
                    continue
                node = w.find("FORM[@kindOf='original']")
                w_form = "".join(node.itertext()) if node is not None else ""
                if not w_form.strip():
                    continue
                m = ET.SubElement(w, "M")
                m.set("id", f"{w.get('id')}M0")
                mf = ET.SubElement(m, "FORM")
                mf.set("kindOf", "original")
                mf.text = w_form
                for t in w.findall("TRANSL"):
                    add_transl(m, t.get(XML_LANG), t.text or "")
                stats["18 mirror morphemes added"] = stats.get(
                    "18 mirror morphemes added", 0) + 1
    # POL-053: the closed attribute surface, plus V017/V085 conformance.
    conform_sentence(root, stats)
    return root



def _attestation_clean(cell: str) -> str:
    """Normalize a gloss cell exactly as the pipeline does before the flip."""
    text, _ = strip_l2m(strip_prosodic_markers(cell or ""))
    return swap_punctuation(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--steps", default="all",
                    help="comma-separated step numbers, or 'all' / 'none'")
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

    repairs = load_record_repairs(Path(__file__).with_name("p2_source_repairs.xml"))
    attested = build_attestation(args.json, _attestation_clean) if 7 in steps else {}
    malformed = load_malformed_translations(args.json) if 19 in steps else {}
    stats: dict = {}
    # Clear the output first: a previous run's files would otherwise
    # survive alongside the new ones and be scored twice.
    if args.out.exists():
        shutil.rmtree(args.out)
    args.out.mkdir(parents=True, exist_ok=True)
    count = 0
    # One XML per language, matching the published layout
    # (XML/Grammar/<Language>/<Language>.xml), so that repair scripts keyed by
    # that path resolve, and sentence ids sit in the same file main puts them in.
    by_language: dict = {}
    for path in sorted(args.json.rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        recs = data if isinstance(data, list) else (list(data.values())[0] if data else [])
        if not isinstance(recs, list):
            continue
        src_key = "/".join(path.parts[-3:])
        root = build(recs, path.stem, steps, stats, src_key, repairs, attested,
                     malformed, language=language_for(path), dialect=dialect_for(path))
        language = path.parent.name.split("_")[0]
        merged = by_language.get(language)
        if merged is None:
            merged = ET.Element("TEXT")
            for key, value in root.attrib.items():
                merged.set(key, value)
            merged.set("id", f"NTU_Gram_{language}")
            by_language[language] = merged
        merged.extend(list(root))

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
