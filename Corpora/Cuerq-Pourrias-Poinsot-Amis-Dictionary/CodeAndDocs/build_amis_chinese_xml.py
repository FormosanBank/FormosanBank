#!/usr/bin/env python3
"""Build FormosanBank XML from the Amis-Chinese volume (Cuerq & Pourrias 2002, "O Citig no Amis").

Sources (committed under CodeAndDocs/, pinned by commit and SHA-256; CodeAndDocs/refresh_source.sh re-pulls them):
  source/pourrias-poinsot.txt   one entry per line (wildjcrt/amis-chinese-poinsot-onefile, 2025)
  source/toufu.sq3              the 2020 proofreading database, printed page + line for every line
                                (miaoski/amis-chinese-poinsot, branch toufu)
  data/french_pages_1_4.json    French pages 1-4 (hand-checked upstream)

Rulings this build follows are quoted in FormosanBank/claudeplans/sweep-qa-decision-log.md
("Poinsot" entries of 2026-10-16/17). In short:
  * one file pair (headwords, examples) per source label S, N, F, T, Z and "unmarked";
    Z -> XML/Sakizaya (szy, dialect Sakizaya); the rest -> XML/Amis (ami);
    N, S -> dialect Southern; F, T, unmarked -> dialect Xiuguluan;
  * an item marked with several dialects goes to each of their files; a reading marked for one
    dialect gets its own entry in that file only;
  * one S per defined form (derived forms and equivalents); a root is never an entry, and is named
    in FORM notes as "root: X";
  * borrowings noted "<Language> borrowing"; cross-references and Bible references go to notes;
  * French pages 1-4 attach to the matching Chinese entries (<= 2 letters apart), or stay separate
    where ruled (data/french_decisions.tsv).
Hand decisions live in data/*.tsv; nothing is edited by hand in the XML.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sqlite3
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

CODE = Path(__file__).resolve().parent          # CodeAndDocs/
ROOT = CODE.parent                               # the corpus root
DATA = CODE / "data"
SOURCE_TXT = CODE / "source" / "pourrias-poinsot.txt"
SOURCE_DB = CODE / "source" / "toufu.sq3"
# The upstream commits the two files were taken from (fetch_sources.py pins the same ones), and their SHA-256.
SOURCE_TXT_COMMIT = "365cfceca84c0edbb6af08133ce4e05e5c5291c0"   # wildjcrt/amis-chinese-poinsot-onefile
SOURCE_DB_COMMIT = "a35e2cbfd48002e15ddca87f674045c0376ed2cc"    # miaoski/amis-chinese-poinsot, branch toufu
SOURCE_TXT_SHA256 = "a0c0e05fae9b820ba2e2b9fd1b5477cfcccf018c58ee513ee28f31cec9b4f7f5"
SOURCE_DB_SHA256 = "70a2b7e421729fee57d53cd57ef1cef4ece254b159b6015bbe97e7990683888b"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

DIALECT_CODES = ("S", "N", "F", "T", "Z")
# "Coastal": readings labelled with the places 豐濱 and Tingalaw, ruled 2026-10-17 (cards r5-coastal-373 and
# r5-coastal-13029, "New Coastal file pair (dialect=\"Coastal\") for these readings"); filled by card_rulings.json
LABELS = DIALECT_CODES + ("unmarked", "Coastal")
FILE_DIALECT = {"S": "Southern", "N": "Southern", "F": "Xiuguluan", "T": "Xiuguluan",
                "unmarked": "Xiuguluan", "Z": "Sakizaya", "Coastal": "Coastal"}
BORROWING = {"J": "Japanese", "Tw": "Hokkien", "Ch": "Mandarin", "英語": "English",
             "希臘文": "Greek", "希伯來語": "Hebrew"}
PLACE_LABELS = {"豐濱", "玉里", "光復鄉", "Tingalaw"}

CITATION = ("Cuerq, G. (顧向前, Ci Ka Ogto), & Pourrias, L. (博利亞) (2002). O Citig no Amis: 阿美語－漢語字典. "
            "French translations for pages 1-4: Poinsot, M., & Pourrias, L. (n.d.). Amis-French dictionary. "
            "Missions Etrangères de Paris.")
BIBTEX = ("@book{cuerq_pourrias_2002, author={Cuerq, G{\\'e}rard and Pourrias, Louis}, "
          "title={O Citig no Amis: 阿美語－漢語字典}, year={2002}, "
          "note={Compiler 顧向前 (Ci Ka Ogto); Amis text revised by 博利亞 Louis Pourrias. French translations "
          "for pages 1-4 from Poinsot, Maurice and Pourrias, Louis, Amis-French dictionary, n.d.}}")
COPYRIGHT = "CC BY-NC 4.0"  # upstream says "CC BY-NC" without a version; ruled 2026-10-17: "CC BY-NC 4.0, as we do elsewhere"

MARKER = re.compile(r"\{([^}]*)\}")
CJK = re.compile(r"[㐀-鿿豈-﫿]")
LATIN = re.compile(r"[A-Za-z]")
BIBLE_REF = re.compile(r"(?:[(（]\s*|(?<=[”\s]))((?:\d\s*)?[\u3400-\u9fff]{1,3}\s*[：:]?\s*\d+\s*[,，\-–]\s*[\d\-–]+(?:\s*[和,，]\s*[\u3400-\u9fff]{1,3}\s*[：:]?\s*\d+\s*[,，\-–]\s*[\d\-–]+)?)\s*[)）]")
PLACEHOLDER = re.compile(r"§(\d+)§")
CROSS_REF = re.compile(r"[(（]?\s*見\s*([A-Za-z'’][A-Za-z'’\-]*)\s*[)）]?")
LATIN_RUN = re.compile(r"[A-Za-z'’‘]*[A-Za-z][A-Za-z'’‘]*(?:[ \t\-]+[A-Za-z'’‘]*[A-Za-z][A-Za-z'’‘]*)+[’'‘]?")


# ------------------------------------------------------------------ data model

@dataclass
class Form:
    text: str
    labels: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


@dataclass
class Sense:
    zh: str
    labels: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)
    equivalents: list[Form] = field(default_factory=list)


@dataclass
class Example:
    amis: str
    zh: str
    labels: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)


@dataclass
class Entry:
    line: int
    part: int
    lines: list[int]
    text: str
    root: str | None = None
    groups: list[list[Form]] = field(default_factory=list)   # '='-groups of defined forms
    senses: list[Sense] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)
    entry_notes: list[str] = field(default_factory=list)
    no_chinese: list[str] = field(default_factory=list)     # glosses printed without Chinese
    subentries: list[tuple[str, str, list[str]]] = field(default_factory=list)  # (form, gloss, notes) inside a sense
    refs: list[str] = field(default_factory=list)


# ------------------------------------------------------------------ helpers

def norm(word: str) -> str:
    """Compare forms: case and apostrophe shape folded; the apostrophe itself is a letter."""
    return word.lower().replace("’", "'").replace("‘", "'").strip().strip("-").strip()


def letters(text: str) -> str:
    text = text.lower().replace("’", "'").replace("‘", "'")
    return "".join(ch for ch in text if (ch.isascii() and ch.isalpha()) or ch == "'")


def lev(a: str, b: str, cap: int = 9) -> int:
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def tidy(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def space_marks(form: str) -> str:
    """Safolu ruling adopted 2026-10-17 (round 3, "Add all three"): no space before ? or !, and a space between ?/!
    and a following letter. Applied to the full-width ？！ the source uses as well as to ASCII ?!."""
    form = re.sub(r"\s+([?!？！])", r"\1", form)
    return re.sub(r"([?!？！])(?=[A-Za-z'’“\"])", r"\1 ", form)


def take_markers(text: str) -> tuple[str, set[str], list[str]]:
    """Remove {X} markers; return text, dialect labels, notes (borrowings, place labels, others)."""
    labels: set[str] = set()
    notes: list[str] = []
    for m in MARKER.findall(text):
        code = m.strip()
        if code in DIALECT_CODES:
            labels.add(code)
        elif code in BORROWING:
            notes.append(f"{BORROWING[code]} borrowing")
        elif code in PLACE_LABELS:
            notes.append(f"source label: {code}")
        else:
            notes.append(f"source label: {code}")
    return tidy(MARKER.sub(" ", text)), labels, notes


def is_derivation(left: str, right: str) -> bool:
    """A bare hyphen (no spaces) separates root and derived form when the right side contains the
    left side's letters (acak-maacak); otherwise it is part of one word (haki-kakaen)."""
    return letters(left).strip("'") in letters(right)


def clean_form(form: str) -> str:
    """Remove printing debris from a form: colons, a dangling dash, parentheses left unpaired by a split
    ("simi )", "dadinas (", "Lowak) -", "hawatid："). Paired parentheses are kept."""
    form = tidy(form).strip(" ：:")
    form = re.sub(r"\s+-$|^-(?=[A-Za-z'’])", "", form).strip()
    if form.count("(") != form.count(")"):
        form = tidy(form.replace("(", " ").replace(")", " "))
    if form.startswith("(") and form.endswith(")") and form.count("(") == 1:
        form = form[1:-1].strip()
    return form


def split_forms(text: str) -> list[str]:
    return [clean_form(p) for p in re.split(r"\s*,\s*", text) if LATIN.search(p) and not CJK.search(p) and clean_form(p)]


# ------------------------------------------------------------------ source loading

def load_source(path: Path) -> dict[int, str]:
    return {n: line for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1) if line.strip()}


def read_tsv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    rows = path.read_text(encoding="utf-8").splitlines()
    head = rows[0].split("\t")
    return [dict(zip(head, r.split("\t"))) for r in rows[1:] if r.strip()]


def apply_corrections(lines: dict[int, str]) -> dict[int, str]:
    """Recorded corrections of typing errors (data/text_corrections.tsv, each with scan evidence)."""
    out = dict(lines)
    for r in read_tsv(DATA / "text_corrections.tsv"):
        n = int(r["line"])
        if out[n].count(r["old"]) != 1:
            raise ValueError(f"text correction for line {n} no longer matches the source: {r['old']!r}")
        out[n] = out[n].replace(r["old"], r["new"])
    return out


def apply_wraps(lines: dict[int, str]) -> tuple[dict[int, str], dict[int, list[int]]]:
    """Join printed-line wraps recorded as 'joined' in line_wraps.tsv onto the line before."""
    joined = {int(r["line"]) for r in read_tsv(DATA / "line_wraps.tsv") if r["decision"] == "joined"}
    out: dict[int, str] = {}
    members: dict[int, list[int]] = {}
    last = None
    for n in sorted(lines):
        if n in joined and last is not None:
            out[last] = out[last].rstrip() + " " + lines[n].lstrip()
            members[last].append(n)
        else:
            out[n] = lines[n]
            members[n] = [n]
            last = n
    return out, members


def keyed(text: str) -> tuple[str, list[int]]:
    """Letters, digits and Chinese only (apostrophes, spaces, braces dropped), with original offsets."""
    chars, idx = [], []
    for i, ch in enumerate(text):
        c = ch.lower()
        if ("a" <= c <= "z") or ("0" <= c <= "9") or CJK.match(c):
            chars.append(c)
            idx.append(i)
    return "".join(chars), idx


def locate(host: str, fp: str, after: int) -> int | None:
    """Offset in host where the text with this fingerprint starts (backing up over a leading apostrophe)."""
    k, idx = keyed(host)
    for pos in range(len(k)):
        if idx[pos] > after and k.startswith(fp, pos):
            off = idx[pos]
            while off > 0 and host[off - 1] in "’'‘":
                off -= 1
            return off
    return None


def apply_splits(joined: dict[int, str]) -> dict[tuple[int, int], str]:
    """Split entries glued onto the line before (line_splits.tsv, decision 'split'); keys (line, part)."""
    rows: dict[int, list[str]] = defaultdict(list)
    for r in read_tsv(DATA / "line_splits.tsv"):
        if r["decision"] == "split":
            rows[int(r["line"])].append(r["fingerprint"])
    out: dict[tuple[int, int], str] = {}
    for n, text in joined.items():
        cuts, last = [], len(split_head_body(text)[0])
        for fp in rows.get(n, []):
            off = locate(text, fp, last)
            if off is None:
                raise ValueError(f"line {n}: split fingerprint {fp!r} no longer found")
            cuts.append(off)
            last = off
        bounds = [0] + cuts + [len(text)]
        for j, (a, b) in enumerate(zip(bounds, bounds[1:])):
            out[(n, j)] = text[a:b].strip()
    return out


# ------------------------------------------------------------------ printed page and line

def printed_locations(lines: dict[int, str], db: Path) -> dict[int, tuple[tuple[int, int], tuple[int, int]] | None]:
    """Locate every source line in the 2020 proofreading DB (letters and Chinese characters only)."""
    def key(s: str) -> str:
        return "".join(ch for ch in s.lower() if ("a" <= ch <= "z") or ("0" <= ch <= "9") or CJK.match(ch))

    con = sqlite3.connect(db)
    stream: list[str] = []
    owner: list[tuple[int, int]] = []
    for p, l, a in con.execute("select p, line, ans from toufu order by p, line"):
        if a is None or "這是空白" in a:
            continue
        k = key(a)
        stream.append(k)
        owner.extend([(p, l)] * len(k))
    s = "".join(stream)
    pos = 0
    out: dict[int, tuple[tuple[int, int], tuple[int, int]] | None] = {}
    for n in sorted(lines):
        e = key(lines[n])
        if not e:
            out[n] = None
            continue
        j = s.find(e, pos, pos + 20000 + len(e))
        if j >= 0:
            out[n] = (owner[j], owner[j + len(e) - 1])
            pos = j + len(e)
            continue
        win = s[pos:pos + len(e) * 2 + 400]
        blocks = [b for b in difflib.SequenceMatcher(None, e, win, autojunk=False).get_matching_blocks() if b.size]
        if blocks:
            a0, a1 = blocks[0].b, blocks[-1].b + blocks[-1].size
            if difflib.SequenceMatcher(None, e, win[a0:a1], autojunk=False).ratio() >= 0.85:
                out[n] = (owner[pos + a0], owner[pos + a1 - 1])
                pos += a1
                continue
        out[n] = None
    return out


def location_note(locs: list[tuple[tuple[int, int], tuple[int, int]] | None]) -> str:
    if any(loc is None for loc in locs):
        return "uncertain; need to check"
    (p0, l0), (p1, l1) = locs[0][0], locs[-1][1]
    start = f"printed p.{p0:03d} l.{l0:02d}"
    return start if (p0, l0) == (p1, l1) else f"{start}–p.{p1:03d} l.{l1:02d}"


# ------------------------------------------------------------------ parsing one entry

def split_head_body(text: str) -> tuple[str, str]:
    """Head = text before the first full-width colon; if Chinese appears earlier, the head ends there."""
    head, _, body = text.partition("：")
    m = CJK.search(MARKER.sub(lambda x: " " * len(x.group(0)), head))   # Chinese inside {英語} etc. is a marker
    if m:
        cut = m.start()
        return re.sub(r"[\s\-]+$", "", text[:cut]), text[cut:]
    return head, body


def parse_head(head: str, entry: Entry) -> None:
    sense_no = re.search(r"<(\d+)>", head)
    if sense_no:
        entry.entry_notes.append(f"sense {sense_no.group(1)}")
    head = re.sub(r"<\d+>", " ", head)
    # "dadinas (=lilit)", "sadigsinan - {N} (= sadigsigan？)", "paso’lin - (mipaso’lin = pakaso’lin)": the
    # parentheses only enclose an '=' list
    head = re.sub(r"[(（]\s*[=＝]\s*([^()（）：\u3400-\u9fff]*?)\s*[)）]", r" = \1", head)
    head = re.sub(r"[(（]([^()（）：\u3400-\u9fff]*[=＝][^()（）：\u3400-\u9fff]*)[)）]", r"\1", head)
    head = head.replace("；", ", ")          # "lawac；pakalawac" lists two forms
    for gi, group in enumerate(re.split(r"\s*[=＝]\s*", head)):
        text, labels, notes = take_markers(group)
        if not LATIN.search(re.sub(r"\([^)]*\)", " ", text)) and entry.groups:
            notes = notes + [f"printed in parentheses: ({p.strip()})" for p in re.findall(r"\(([^)]*)\)", text) if p.strip()]
            # a marker standing alone in an '=' slot ("kapia = {S}：") belongs to the word before it
            for f in entry.groups[-1]:
                f.labels |= labels
                f.notes += notes
            continue
        parens = re.findall(r"\(([^)]*)\)", text)
        text = tidy(re.sub(r"\([^)]*\)", " ", text))
        if parens:
            notes = notes + [f"printed in parentheses: ({p.strip()})" for p in parens if p.strip()]
        # spaced dashes always separate; a bare hyphen separates only a derivation (acak-maacak)
        parts: list[str] = []
        for chunk in re.split(r"\s+-\s*|\s*-\s+", text):
            pieces = chunk.split("-")
            if len(pieces) == 2 and all(LATIN.search(x) for x in pieces) and is_derivation(pieces[0], pieces[1]):
                parts.extend(pieces)
            else:
                parts.append(chunk)
        parts = [tidy(p) for p in parts if LATIN.search(p)]
        if not parts:
            continue
        forms: list[str]
        if gi == 0 and len(parts) >= 2:
            entry.root = split_forms(parts[0])[0] if split_forms(parts[0]) else parts[0]
            forms = [f for p in parts[1:] for f in split_forms(p)]
        else:
            forms = [f for p in parts for f in split_forms(p)]
        entry.groups.append([Form(f, set(labels), list(notes)) for f in forms])


EXAMPLE_START = re.compile(r"(?:(?<=[\s\u3000-\u9fff\uff00-\uffef。，；：、)）\]」”.!?])|^)-\s*(?=(?:\{[^}]*\}\s*)*[“\"‘'’]?[A-Za-z])|\s+-\s*(?=(?:\{[^}]*\}\s*)*[“\"‘'’]?[A-Za-z])")


def first_chinese(seg: str) -> int | None:
    depth = 0
    for i, ch in enumerate(seg):
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
        elif depth == 0 and CJK.match(ch):
            return i
    return None


def split_example(seg: str) -> tuple[str, str]:
    """Amis part and Chinese part of an example segment: cut at the colon or the first Chinese character
    (outside parentheses), whichever comes first."""
    colon, cjk = seg.find("："), first_chinese(seg)
    if colon >= 0 and (cjk is None or colon < cjk):
        amis, _, zh = seg.partition("：")
        return amis, zh
    # Bible style: “Amis”(ref)“Chinese”  or  Amis (ref) Chinese
    depth = 0
    for i, ch in enumerate(seg):
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
        elif depth == 0 and CJK.match(ch):
            j = i
            while j > 0 and seg[j - 1] in "“\" ":
                j -= 1
            return seg[:j], seg[j:]
    m = re.search(r"[(（]([^)）]*[\u3400-\u9fff][^)）]*)[)）]\s*$", seg)
    if m:
        return seg[:m.start()], m.group(1)
    return seg, ""


# Every Latin-letter text found where a translation belongs, decided one by one (latin_runs.tsv): scientific -> a
# Latin TRANSL, english -> an English TRANSL (both ruled 2026-10-17), keep -> stays inside the Chinese (ruled for
# "mama no kapah" and "’Na Taolan’"), amis -> Amis text, review -> a decision card; meanwhile a "source text:" note.
LATIN_RUNS = {r["text"]: r["class"] for r in read_tsv(DATA / "latin_runs.tsv")}
FOREIGN_CLASSES = {"scientific": "§lat§", "english": "§eng§", "french": "§fra§", "review": "source text: ",
                   "note": "source text: ", "drop": "§drop§"}   # not Amis (french/note/drop ruled 2026-10-17, round 6)
PARKED = {"amis-in-chinese": "source text: "}   # Amis text inside a Chinese translation, awaiting a card
_foreign = sorted((x for x, c in LATIN_RUNS.items() if c in FOREIGN_CLASSES or c in PARKED), key=len, reverse=True)
FOREIGN_RUN = re.compile(r"(?<![A-Za-z'’])(?:" + "|".join(re.escape(x) for x in _foreign) + r")(?![A-Za-z'’])")
KEEP_RUN = re.compile("|".join(re.escape(x) for x, c in LATIN_RUNS.items() if c == "keep"))


def foreign_note(text: str) -> str:
    """The note that carries a listed non-Amis text: "§lat§X", "§eng§X" or "source text: X"."""
    return {**FOREIGN_CLASSES, **PARKED}[LATIN_RUNS[text]] + text


def foreign(text: str) -> list[str] | None:
    """If text (whole, or every comma- or '/'-separated part) is a listed non-Amis text, its notes; else None.
    Amis text parked from inside a Chinese translation ("amis-in-chinese") is Amis, so it is not foreign here."""
    for cand in (tidy(text), tidy(text).strip("：:；; “”\"()（）-")):
        if LATIN_RUNS.get(cand) in FOREIGN_CLASSES:
            return [foreign_note(cand)]
    text = tidy(text).strip("：:；; “”\"()（）-")
    parts = [tidy(x).strip("：: ") for x in re.split(r"[,/，=＝：]", text) if x.strip()]   # "Hairtail：trichiurus haumela"
    if len(parts) > 1 and all(LATIN_RUNS.get(x) in FOREIGN_CLASSES for x in parts):
        return [foreign_note(x) for x in parts]
    return None


UNCERTAIN = re.compile(r"[(（]\s*[?？]\s*[)）]")


def clean_chinese(text: str) -> tuple[str, list[str]]:
    """Clean a Chinese translation. Latin-letter runs inside it are decided per run (ruled 2026-10-17):
    scientific names -> a Latin TRANSL ("§lat§" note), English names -> an English TRANSL ("§eng§"), runs ruled to stay
    -> left in the text (latin_runs.tsv), anything else -> FORM/TRANSL notes "source text:" for review.
    A printed "(?)" is removed and noted "translation uncertain" (ruled 2026-10-17)."""
    notes: list[str] = []
    if UNCERTAIN.search(text):
        notes.append("translation uncertain")
        text = UNCERTAIN.sub(" ", text)
    for m in CROSS_REF.finditer(text):
        notes.append(f"cross-reference: 見 {m.group(1)}")
    text = CROSS_REF.sub(" ", text)
    text = re.sub(r"“\s*”|\(\s*\)|（\s*）", " ", text)

    def listed(m: re.Match) -> str:
        notes.append(foreign_note(m.group(0)))
        return " "
    text = FOREIGN_RUN.sub(listed, text)
    kept: list[str] = []

    def keep(m: re.Match) -> str:
        kept.append(m.group(0))
        return f"\x01{len(kept) - 1}\x01"
    text = KEEP_RUN.sub(keep, text)

    def unlisted(m: re.Match) -> str:
        notes.append(f"source text: {m.group(0).strip()}")
        return " "
    text = LATIN_RUN.sub(unlisted, text)
    text = re.sub(r"\x01(\d+)\x01", lambda m: kept[int(m.group(1))], text)
    text = re.sub(r"\s*[=＝]\s*$|^\s*[=＝]\s*", "", text)     # "一種菜 =" left when a name after "=" moved out
    text = text.replace("[宗]", " ")   # domain label "religion": dropped everywhere (ruled 2026-10-17, card r6-zong-6599 "Drop [宗] everywhere")
    text = re.sub(r"\(\s*\)|（\s*）", " ", text)
    text = re.sub(r"(?:\s*：\s*)+(?=：|$)", "", text)          # trailing / doubled colons left behind
    text = re.sub(r"^\s*：\s*", "", text)
    text = re.sub(r"：\s*：", "：", text)
    return tidy(text), notes


def take_refs(text: str, refs: list[str]) -> tuple[str, list[str]]:
    """Replace §n§ placeholders by nothing and return the Bible references they stood for, as notes."""
    found = [f"source: {refs[int(m.group(1))]}" for m in PLACEHOLDER.finditer(text)]
    return tidy(PLACEHOLDER.sub(" ", text)), found


QUOTED_EXAMPLE = re.compile(r"“([^”“]*[A-Za-z][^”“]*)”\s*((?:§\d+§\s*)*)[：:]?\s*“([^”“]*[\u3400-\u9fff][^”“]*)”")
def word_pair(amis: str) -> bool:
    """'sasoalen = sasowalen', 'tood han = salimood': forms joined by '=' that are not all sentences (POL-027)."""
    opts = re.split(r"\s+[=＝]\s+", amis)
    return (len(opts) > 1 and all(LATIN.search(o) for o in opts)
            and not all(len(re.findall(r"[A-Za-z'’]+", o)) >= 2 for o in opts))


def pair_definition(zh: str) -> tuple[str, str]:
    """Split the Chinese after a word pair into the pair's own definition and the rest. The pair's definition runs
    over every '；' piece that has no Amis in it ("Ido = rdo：滿的；連續的；無空的；一致性，一慣性": all four are the
    pair's; ruled 2026-10-18, decision page card r2-m5: "Please try reparsing assuming the mandarin is a
    translation/definition"); a piece with Amis in it starts the rest."""
    pieces = re.split(r"[；;]", zh)
    k = 1
    while k < len(pieces) and not LATIN.search(MARKER.sub(" ", pieces[k])):
        k += 1
    return "；".join(pieces[:k]), "；".join(pieces[k:])


PLAIN_EXAMPLE = re.compile(r"(?:(?<=[\u3400-\u9fff，。；：！？)）\s])|^)([A-Za-z'’‘][A-Za-z'’‘]*(?:[ ,]+[A-Za-z'’‘][A-Za-z'’‘!?]*)+[!?！？]?)\s*((?:§\d+§\s*)*)：\s*([^A-Za-z：；§]*[\u3400-\u9fff][^A-Za-z：；§]*)")


def embedded_examples(piece: str, entry: Entry) -> str:
    """Take examples written inside a sense (no dash) out of it, as Example records; return what is left."""
    def quoted(m: re.Match) -> str:
        amis, refs, zh = m.group(1), m.group(2), m.group(3)
        _, notes = take_refs(refs, entry.refs)
        entry.examples.append(Example(tidy(amis), tidy(zh), set(), notes))
        return " "
    piece = QUOTED_EXAMPLE.sub(quoted, piece)

    def plain(m: re.Match) -> str:
        amis, refs, zh = m.group(1), m.group(2), m.group(3)
        if len(re.findall(r"[A-Za-z'’]+", amis)) < 2 or foreign(amis):
            return m.group(0)      # a listed Latin/English name with its Chinese is a sense, not an example
        _, notes = take_refs(refs, entry.refs)
        zh_c, zh_n = clean_chinese(zh)
        entry.examples.append(Example(tidy(amis), zh_c, set(), notes + zh_n))
        return " "
    return PLAIN_EXAMPLE.sub(plain, piece)


def parse_body(body: str, entry: Entry) -> None:
    refs: list[str] = []

    def stash(m: re.Match) -> str:
        refs.append(re.sub(r"\s+", " ", m.group(1)))
        return f" §{len(refs) - 1}§ "
    body = BIBLE_REF.sub(stash, body)
    entry.refs = refs
    starts = [m.start() for m in EXAMPLE_START.finditer(body)]
    bounds = [0] + starts + [len(body)]
    segments = [body[a:b] for a, b in zip(bounds, bounds[1:])]
    sense_texts: list[tuple[str, set[str], list[str]]] = []
    for k, seg in enumerate(segments):
        seg = re.sub(r"^\s*-\s*", "", seg) if k else seg
        if not seg.strip():
            continue
        before_colon = seg.split("：", 1)[0]
        stripped, seg_labels, seg_notes = take_markers(before_colon)
        if k == 0 or not LATIN.search(stripped):
            sense_texts.append((seg, set(), []))
            continue
        semi = seg.find("；")
        if semi > 0 and "：" not in seg[:semi] and not CJK.search(seg[:semi]):
            sense_texts.append((seg[semi + 1:], set(), []))
            seg = seg[:semi]
        amis, zh = split_example(seg)
        if foreign(take_markers(amis)[0]) or all(foreign(x) for x in re.split(r"\s*[=＝]\s*", take_markers(amis)[0]) if x.strip()):
            sense_texts.append((seg, set(), []))   # "- Cassia fistula", "- Citrus aurientium：酸橙": a name, not Amis
            continue
        amis, labels, notes = take_markers(amis)
        # (e) parenthesised text inside the Amis goes to notes: "o pipatorodan to kowag (豐年祭的第八天)"
        for par in re.findall(r"[(（]([^)）]*)[)）]", amis):
            notes.append(f"printed in parentheses: ({par.strip()})")
        amis = tidy(re.sub(r"[(（][^)）]*[)）]", " ", amis))
        amis, ref_notes = take_refs(amis, refs)
        amis = re.sub(r"[\s\-]+$", "", amis)
        # a dash + marker + colon inside the translation starts a new marked sense ("這是你的枕頭 - {N} ：針眼")
        zh = re.sub(r"\s*-\s*((?:\{[^}]*\}\s*)+)(?=[：=＝])", r"；\1", zh)
        glued = re.search(r"(?<=[\u3400-\u9fff，。！？])\s*[A-Za-z'’][A-Za-z'’ ,]*?\s*：\s*[\u3400-\u9fff]", zh)
        if glued and (zh.find("；") < 0 or glued.start() < zh.find("；")):
            sense_texts.append((zh[glued.start():], set(), []))
            zh = zh[:glued.start()]
        eq = re.search(r"(?<=[\u3400-\u9fff，。！？”）)])\s*(?=(?:[A-Za-z'’][A-Za-z'’ ]*?\s*)?[=＝]\s*[A-Za-z'’][^：；]*：\s*[\u3400-\u9fff])", zh)
        if eq and (zh.find("；") < 0 or eq.start() < zh.find("；")):
            # "他的氏族是那一個？ mahagagatoway = mahagagatoay：懷孕的開始": the translation ends at the Chinese
            sense_texts.append((zh[eq.start():].lstrip("=＝ "), set(), []))
            zh = zh[:eq.start()]
        if "；" in zh and word_pair(amis):
            zh, more = pair_definition(zh)
            if more.strip():
                sense_texts.append((more, set(), []))
        elif "；" in zh:
            # "…“他留在門外”；短留，呼住": the example's translation ends at the first '；'
            zh, _, more = zh.partition("；")
            sense_texts.append((more, set(), []))
        # references are read only from this example's own translation (not from senses cut off above)
        zh, zh_ref_notes = take_refs(zh, refs)
        refs_here = ref_notes + zh_ref_notes
        notes += refs_here
        if not zh.strip() or not CJK.search(zh):
            if len(re.findall(r"[A-Za-z'’]+", amis)) >= 2 and "," not in amis:
                # an example printed without a translation ("- ma'adapaway a fafahiyan")
                entry.examples.append(Example(amis, "", labels, notes + ["no translation in the source"]))
            else:
                # single Amis words listed in the definition ("- tafiras {N} - padaka"): equivalents
                for f in split_forms(amis):
                    entry.groups.append([Form(f, labels, notes + ["listed in the definition"])])
            if zh.strip():
                sense_texts.append((zh, set(), []))
            continue
        zh, zh_labels, zh_marker_notes = take_markers(zh)   # "…：鋤稻子 {Z}" marks the example
        labels |= zh_labels
        notes += zh_marker_notes
        zh_clean, zh_notes = clean_chinese(zh)
        if len(re.findall(r"[A-Za-z'’]+", amis)) == 1 and "," not in amis and not refs_here:
            # "- dodohay：…", "- kawkagle {Tw} (…)": a single word with its own gloss is a sub-entry
            entry.subentries.append((amis, zh_clean, notes + zh_notes + (["marker: " + ",".join(sorted(labels))] if labels else [])))
            continue
        entry.examples.append(Example(amis, zh_clean, labels, notes + zh_notes))
    pieces: list[str] = []
    for text, _, _ in sense_texts:
        # "鹹的 - {S}：辣的": a dash + marker + colon starts a new sense carrying that marker
        text = re.sub(r"\s*-\s*((?:\{[^}]*\}\s*)+)(?=[：=＝])", r"；\1", text)
        split = re.split(r"[；;]", text)
        while split:
            piece = split.pop(0)
            left, colon, right = piece.partition("：")
            # "睡在別人旁邊 Ido = rdo：滿的": the Amis is what follows the last Chinese character
            left_amis = take_markers(re.sub(r"^\s*[(（]", "", re.sub(r"^.*[㐀-鿿]", "", left)))[0]
            # "大甕 = ciokeg = talafinan = flalonan：水缸" (forms listed after a gloss, leading '=') is not a pair
            if colon and CJK.search(right) and not tidy(left_amis).startswith(("=", "＝")) and word_pair(tidy(left_amis)):
                # a word pair's definition keeps its Chinese-only pieces (see pair_definition)
                zh, more = pair_definition(right + "".join("；" + p for p in split))
                split = re.split(r"[；;]", more) if more else []
                piece = left + colon + zh
                if re.match(r"^\s*[(（]", piece) and re.search(r"[)）]\s*$", piece) and piece.count("(") + piece.count("（") == 1 and piece.count(")") + piece.count("）") == 1:
                    # "(fokosi = bokasi：牧師；和尚)": the parentheses enclose the whole pair and its definition
                    piece = re.sub(r"[)）]\s*$", "", re.sub(r"^\s*[(（]", "", piece))
            pieces.append(piece)
    for piece in pieces:
            if not piece.strip():
                continue
            equivalents: list[Form] = []
            # Bible quotations and plain examples written inside a sense, without a dash:
            #   "躬身；俯身：“Mico'koy cagra a minegneg to sra”§0§“他們凝視地面”"   (quotation, reference, translation)
            #   "(mipalo：打)，aka pipalo to wawa：不要打孩子們"                    (two or more Amis words, colon, Chinese)
            piece = embedded_examples(piece, entry)
            piece, piece_refs = take_refs(piece, entry.refs)
            # "擦布 (= simi {J})", "(=cikil =cipim)": the parentheses only enclose an '=' list
            piece = re.sub(r"[(（]\s*[=＝]\s*([^()（）：\u3400-\u9fff]*?)\s*[)）](?=[\s\-]*$)", r" = \1 ", piece)
            # "(看：lnaf)", "(也許：kodid no paga？)", "(如同飛的鳥：mafaharay a 'ayam)": a Chinese remark that quotes Amis
            # stays with the translation, as a note
            for m in list(re.finditer(r"[(（]([^()（）]*[\u3400-\u9fff][^()（）]*：\s*[A-Za-z'’][^()（）\u3400-\u9fff]*)[)）]", piece)):
                if not foreign(m.group(1).rsplit("：", 1)[1]):
                    piece = piece.replace(m.group(0), " ")
                    note = f"printed in parentheses: ({tidy(m.group(1))})"
                    (piece_refs if CJK.search(MARKER.sub(" ", piece)) else entry.entry_notes).append(note)
            # "( = Fagcaiay a 'Adigo[基督教]：聖靈)": a parenthesised sub-entry with its own gloss
            for m in list(re.finditer(r"[(（]\s*=?\s*([A-Za-z'’][^：()（）]*?)\s*(\[[^\]]*\])?\s*：\s*([^()（）]+)[)）]", piece)):
                sub_notes = [f"domain label: {m.group(2)}"] if m.group(2) else []
                # "(Figus superba = t'iaw：對葉榕)": a listed name before '=' is a translation of the Amis after it
                sub_parts = [x for x in re.split(r"\s*[=＝]\s*", tidy(m.group(1))) if x.strip()]
                sub_notes += [n for x in sub_parts if foreign(x) for n in foreign(x)]
                sub_form = " = ".join(x for x in sub_parts if not foreign(x))
                if LATIN.search(sub_form):
                    entry.subentries.append((sub_form, tidy(m.group(3)), sub_notes))
                else:
                    entry.senses.append(Sense(clean_chinese(m.group(3))[0], set(), sub_notes))
                piece = piece.replace(m.group(0), " ")
            # "kaadayayan：慈悲的", "{F} = micokar：踢打" or "(感嘆) ada', tayra：妤巴！你去巴": Amis before a colon,
            # Chinese after. Markers are blanked first so the letters inside {F} never count as Amis.
            handled = False
            while True:
                masked = MARKER.sub(lambda x: "\x00" * len(x.group(0)), piece)
                m = re.match(r"^\s*((?:[(（][^)）]*[)）]|[^A-Za-z'’=＝])*?)\s*([=＝]?)\s*([A-Za-z'’][^：\u3400-\u9fff\x00]*?)\s*((?:\x00+\s*)*)：\s*(.*[\u3400-\u9fff].*)$", masked)
                if not m:
                    break
                lead = piece[:m.start(2)]
                amis_part = piece[m.start(3):m.end(4)]
                zh_part = piece[m.start(5):]
                lead_text, lead_labels, lead_notes = take_markers(lead)
                a_text, a_labels, a_notes = take_markers(amis_part)
                a_labels |= lead_labels
                a_notes = lead_notes + a_notes
                a_parts = [x for x in re.split(r"\s*[=＝]\s*", a_text) if x.strip()]
                f_notes = [n for x in a_parts if foreign(x) for n in foreign(x)]
                if f_notes:
                    a_text = " = ".join(x for x in a_parts if not foreign(x))
                    if not LATIN.search(a_text):
                        # "一種鳥：Common kingfisher：翠鳥 = pidoegay：…": the name translates the head words; the
                        # Chinese before it is a sense and the rest is read again
                        if CJK.search(lead_text):
                            entry.senses.append(Sense(clean_chinese(lead_text.rstrip("：: "))[0], set(), []))
                        entry.entry_notes += f_notes
                        piece = zh_part
                        continue
                    a_notes = a_notes + f_notes      # "Figus superba = t'iaw：對葉榕": the name goes with t'iaw
                if LATIN.search(a_text):
                    if CJK.search(lead_text):
                        entry.senses.append(Sense(clean_chinese(lead_text.rstrip("：: "))[0], set(), []))
                    zh_c, zh_n = clean_chinese(zh_part)
                    if m.group(2) or (len(re.findall(r"[A-Za-z'’]+", a_text)) == 1 and "," not in a_text):
                        entry.subentries.append((a_text, zh_c, a_notes + zh_n + piece_refs + (["marker: " + ",".join(sorted(a_labels))] if a_labels else [])))
                    else:
                        entry.examples.append(Example(a_text, zh_c, a_labels, a_notes + zh_n + piece_refs))
                    handled = True
                break
            if handled:
                continue
            parts = re.split(r"\s*[=＝]\s*", piece)
            keep = [parts[0]]
            for p in parts[1:]:
                p_text, p_labels, p_notes = take_markers(p)
                sci = re.match(r"^\s*([A-Za-z'’][A-Za-z'’ ]*?)\s*：\s*([A-Za-z][A-Za-z .]+)$", p_text)
                if sci and foreign(sci.group(2)):
                    p_text, p_notes = sci.group(1), p_notes + foreign(sci.group(2))
                if LATIN.search(p_text) and not CJK.search(p_text) and not foreign(p_text):
                    equivalents += [Form(f, set(p_labels), list(p_notes)) for f in split_forms(p_text)]
                elif not p_text and keep:
                    keep[-1] = keep[-1] + " " + p      # a marker alone after '=' stays with the text before
                else:
                    keep.append(p)
            piece_text, labels, notes = take_markers(" = ".join(keep))
            # "gloss：amis, amis" (equivalents listed after a gloss); scientific names are not Amis
            if "：" in piece_text:
                gloss, _, tail = piece_text.partition("：")
                if LATIN.search(tail) and not CJK.search(tail) and not foreign(tail):
                    equivalents += [Form(f, set(), []) for f in split_forms(tail)]
                    piece_text = gloss
            zh, zh_notes = clean_chinese(piece_text)
            if not CJK.search(zh):
                # no Chinese in this sense: a scientific name, a German gloss, "？？？", an untranslated phrase ...
                gloss = tidy(MARKER.sub(" ", piece)).strip("；; ")
                if gloss and not equivalents:
                    words = re.findall(r"[A-Za-z'’]+", gloss)
                    if entry.line in NON_CHINESE:   # ruled glosses in another language (non_chinese_glosses.tsv)
                        entry.no_chinese.append(gloss)
                    elif foreign(gloss) or all(foreign(x) for x in re.split(r"\s+-\s+", gloss)):
                        entry.entry_notes += foreign(gloss) or [n for x in re.split(r"\s+-\s+", gloss) for n in foreign(x)]
                    elif len(words) >= 2 and not re.search(r"[^\sA-Za-z'’,.!?-]", gloss) and entry.line not in NON_CHINESE:
                        entry.examples.append(Example(gloss, "", labels, notes + ["no translation in the source"]))
                    else:
                        entry.no_chinese.append(gloss)
                    entry.entry_notes += notes
                    continue
                zh = ""
            entry.senses.append(Sense(zh, labels, notes + zh_notes + piece_refs, equivalents))


def parse_entry(n: int, part: int, members: list[int], text: str) -> Entry:
    entry = Entry(line=n, part=part, lines=members, text=text)
    # "'el'el： - ma'el'elay = …：gloss": the head word continues past a misplaced colon
    text = re.sub(r"^([^：]*[A-Za-z'’][^：]*)：\s*-\s*(?=[A-Za-z'’])", r"\1 - ", text, count=1)
    # "ma’deg - (夠了！：ma’deg to！)：適當，足夠": a (Chinese：Amis) example printed between the head word and its colon is
    # an example of the head word; the gloss after the colon is the head word's own
    m = re.match(r"^([^：]*?)\s-\s*[(（]([^()（）]*[\u3400-\u9fff][^()（）]*)：([^()（）]*[A-Za-z][^()（）]*)[)）]\s*：(.*)$", text)
    if m:
        text = f"{m.group(1)}：{m.group(4)} - {m.group(3).strip()}：{m.group(2).strip()}"
    head, body = split_head_body(text)
    parse_head(head, entry)
    parse_body(body, entry)
    return entry


# ------------------------------------------------------------------ assignment

@dataclass
class Record:
    label: str
    kind: str
    sid: str
    form: str
    form_notes: list[str]
    zho: list[tuple[str, list[str]]]
    fra: list[tuple[str, str | None]] = field(default_factory=list)
    alt_forms: list[str] = field(default_factory=list)
    other: list[tuple[str, str, list[str]]] = field(default_factory=list)   # (xml:lang, text, notes): German, Latin


def defined_form_set(entries: list[Entry]) -> set[str]:
    out = set()
    for e in entries:
        if any(CJK.search(s.zh) for s in e.senses) or e.examples:
            out |= {norm(f.text) for g in e.groups for f in g}
            out |= {norm(q.text) for s in e.senses for q in s.equivalents}
    return out


def build_records(entries: list[Entry], locs: dict[int, str]) -> list[Record]:
    out: list[Record] = []
    for e in entries:
        loc = locs[(e.line, e.part)]
        tag = f"L{e.line:05d}" + (f"-s{e.part}" if e.part else "")
        root_note = [f"root: {e.root}"] if e.root else []
        general = [s for s in e.senses if not s.labels and s.zh]
        specific = [s for s in e.senses if s.labels and s.zh]
        per_file: dict[tuple[str, str], Record] = {}

        def add(label: str, form: Form, senses: list[Sense], extra: list[str]) -> None:
            key = (label, form.text.replace("’", "'"))
            if key not in per_file:
                notes = [loc] + root_note + e.entry_notes + form.notes + extra
                per_file[key] = Record(label, "headwords", "", form.text, notes, [])
            rec = per_file[key]
            for s in senses:
                if s.zh and (s.zh, s.notes) not in rec.zho:
                    rec.zho.append((s.zh, s.notes))
                elif not s.zh:
                    rec.form_notes += [n for n in s.notes if n.startswith(("§lat§", "§eng§", "§fra§", "§drop§"))]

        head_labels_first = (e.groups[0][0].labels if e.groups and e.groups[0] else set()) or {"unmarked"}
        for group in e.groups:
            for form in group:
                for label in sorted(form.labels or {"unmarked"}):
                    add(label, form, general, [])
        main_forms = e.groups[0] if e.groups else []
        for s in specific:
            for label in sorted(s.labels):
                # a sense marker reaches the head forms that carry no dialect marker of their own
                own = [f for g in e.groups for f in g if not f.labels]
                for form in (own or main_forms):
                    add(label, Form(form.text, set(), form.notes), [s], [])
        for s in e.senses:
            for q in s.equivalents:
                labels = q.labels or s.labels or head_labels_first   # inherited (ruled 2026-10-17)
                for label in sorted(labels):
                    add(label, q, [s] if s.zh else general, [f"listed under {main_forms[0].text}"] if main_forms else [])
        for form_text, gloss, notes in e.subentries:
            inherit = True
            pars = re.findall(r"[(（]([^)）]*)[)）]", form_text)
            if pars:
                notes = notes + [f"printed in parentheses: ({x.strip()})" for x in pars]
                form_text = tidy(re.sub(r"[(（][^)）]*[)）]", " ", form_text))
            labels = {x for n in notes if n.startswith("marker: ") for x in n[8:].split(",")} or head_labels_first
            # "sfi = taloan：廚房" lists two forms: one S each (round-4 ruling, option C)
            for one in [clean_form(x) for x in re.split(r"\s*[=＝]\s*", form_text) if clean_form(x)]:
                for label in sorted(labels):
                    add(label, Form(one, set(), [n for n in notes if not n.startswith("marker: ")]),
                        [Sense(gloss, set(), [])] if gloss else [], [f"listed under {main_forms[0].text}"] if main_forms else [])
        if any(s.zh for s in e.senses) or e.subentries:
            extra_gloss = [f"gloss in source: {g}" for g in e.no_chinese]
            for rec in per_file.values():
                rec.form_notes += extra_gloss
        if not any(s.zh for s in e.senses) and not e.subentries:
            # nothing in Chinese: keep the head words, with the printed gloss (German -> TRANSL deu, ruled data)
            for group in e.groups:
                for form in group:
                    for label in sorted(form.labels or {"unmarked"}):
                        add(label, form, [], [])
            for rec in per_file.values():
                for g in e.no_chinese:
                    lang = NON_CHINESE.get(e.line)
                    if lang:
                        # ruled 2026-10-17: the gloss is the translation, in its own language; a printed (?) becomes a note
                        uncertain = bool(re.search(r"[(（]\s*[?？]\s*[)）]", g))
                        text = tidy(re.sub(r"[(（]\s*[?？]\s*[)）]", " ", g))
                        tnotes = (["scientific name"] if lang == "lat" else []) + (["translation uncertain"] if uncertain else [])
                        rec.other.append((lang, text, tnotes))
                    else:
                        rec.form_notes.append(f"gloss in source: {g}")
        # An "example" printed as a pair of words or a phrase and a word ("sasoalen = sasowalen：話，要講的話") is a set
        # of equivalent head words, one S per form (ruled 2026-10-17, decision page card m5: "Turn the word pairs into
        # head-word entries now"). Sentence alternatives stay examples (POL-027, below); "ccay a pawti = 26" stays an
        # example because "26" is not a form, and a pair printed without a translation stays an untranslated example.
        # "ccay a pawti = 26 斗" (one sack = 26 dou): the number goes with its unit in the translation (ruled
        # 2026-10-18, decision page card r3-12604: "Option B: ccay a pawti = \"26 斗\"")
        for ex in e.examples:
            m = re.fullmatch(r"(.+?)\s+[=＝]\s+(\d+)", ex.amis)
            if m and ex.zh:
                ex.notes.append(f"printed: {ex.amis} {ex.zh}")
                ex.amis, ex.zh = m.group(1), f"{m.group(2)} {ex.zh}"
        pairs = [ex for ex in e.examples if ex.zh and word_pair(ex.amis)]
        pair_heads = {r.label for r in per_file.values()} or {"unmarked"}
        for ex in pairs:
            labels = (ex.labels & pair_heads) or pair_heads
            for one in [clean_form(o) for o in re.split(r"\s+[=＝]\s+", ex.amis)]:
                for label in sorted(labels):
                    add(label, Form(one, set(), [n for n in ex.notes if not n.startswith("marker: ")]),
                        [Sense(z.strip(), set(), []) for z in re.split(r"[；;]", ex.zh) if z.strip()],
                        [f"listed under {main_forms[0].text}"] if main_forms else [])
        e.examples = [ex for ex in e.examples if ex not in pairs]
        k = 0
        for rec in per_file.values():
            if not rec.zho and not (not any(s.zh for s in e.senses) and rec.label):
                continue
            k += 1
            rec.sid = f"{rec.label}-{tag}-{k:02d}"
            out.append(rec)
        heads = {r.label for r in per_file.values() if r.sid}
        for i, ex in enumerate(e.examples, start=1):
            labels = (ex.labels & heads) or heads or {"unmarked"}
            # POL-027: a sentence printed with alternatives ("dada kiso = tanam kiso", "A / B") is one S per option
            options = [tidy(x) for x in re.split(r"\s+[=＝/]\s+", ex.amis) if tidy(x)]
            # only sentences are alternatives: "ccay a pawti = 26" is an equation and "sodiget = sogidet" a pair of
            # words (a sub-entry), so both stay one S
            if not all(len(re.findall(r"[A-Za-z'’]+", o)) >= 2 for o in options):
                options = [ex.amis]
            for j, option in enumerate(options):
                suffix = "" if len(options) == 1 else f"-{j + 1}"
                note = [] if len(options) == 1 else [f"alternative {j + 1} of {len(options)} in the source: {ex.amis}"]
                for label in sorted(labels):
                    out.append(Record(label, "examples", f"{label}-{tag}-e{i:02d}{suffix}", option,
                                      [loc] + ex.notes + note, [(ex.zh, [])] if ex.zh else []))
    for rec in out:
        lift_foreign(rec)
        rec.form = space_marks(rec.form)
        rec.alt_forms = [space_marks(a) for a in rec.alt_forms]
    return out


def lift_foreign(rec: Record) -> None:
    """Notes "§lat§X" / "§eng§X" (listed scientific / English names, latin_runs.tsv) become TRANSL lat / eng."""
    def pull(notes: list[str]) -> list[str]:
        for n in notes:
            if n.startswith(("§lat§", "§eng§", "§fra§")):
                lang = {"§lat§": "lat", "§eng§": "eng", "§fra§": "fra"}[n[:5]]
                item = (lang, n[5:], [{"lat": "scientific name", "eng": "English name", "fra": "French name"}[lang]])
                if item not in rec.other:
                    rec.other.append(item)
        # "§drop§": a text the maintainer ruled out (e.g. "amilax", card r6-names-3138)
        return [n for n in notes if not n.startswith(("§lat§", "§eng§", "§fra§", "§drop§"))]
    rec.form_notes = pull(rec.form_notes)
    rec.zho = [(z, pull(list(n))) for z, n in rec.zho]


# ------------------------------------------------------------------ dangling parentheses, alt forms

def close_dangling(text: str) -> str:
    """Ruled 2026-10-17 (card r5-unbalanced-3833): "Assume that if a new entry or example sentence starts while
    there's a dangling parentheses, it should close right before the new entry or example." Only entries with more
    opening than closing parentheses are touched; the missing ")" goes before the next example, else at the end."""
    missing = text.count("(") + text.count("（") - text.count(")") - text.count("）")
    if missing <= 0:
        return text
    starts = {m.start() for m in EXAMPLE_START.finditer(text)}
    out, stack = [], []
    for i, ch in enumerate(text):
        if i in starts and stack and missing > 0:
            while stack and missing > 0:
                closer = ")" if stack.pop() == "(" else "）"
                while out and out[-1] == " ":
                    out.pop()
                out.append(closer + " ")
                missing -= 1
        if ch in "(（":
            stack.append(ch)
        elif ch in ")）" and stack:
            stack.pop()
        out.append(ch)
    text = "".join(out).rstrip()
    while stack and missing > 0:
        text += ")" if stack.pop() == "(" else "）"
        missing -= 1
    return text


def edit_distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def own_notes(r: Record) -> set[str]:
    """A form's notes other than where it is printed, its root and "listed under …" (shared by an entry's forms).
    A form with notes of its own (a borrowing, a printed parenthesis) is not merged into another form."""
    return {n for n in r.form_notes if n and not n.startswith(("printed p.", "root: ", "listed under ", "uncertain; need"))}


def merge_alts(records: list[Record]) -> list[Record]:
    """Ruled 2026-10-17 (card r5-mixed-693: "If the two words differ in only 1 or 2 Amis characters and are same
    dialect, "alt" is appropriate."; card r6-altrule-0: apply to all pairs with identical translations, "But only if
    marked as being same dialect!"). Within one entry and one dialect file, head words whose forms differ by at most
    2 characters and whose translations are identical become one S: the first form, the others FORM ver="alt"."""
    groups: dict[tuple, list[Record]] = defaultdict(list)
    for r in records:
        m = re.search(r"-L(\d{5})(-s\d+)?-\d", r.sid)
        if r.kind == "headwords" and m:
            groups[(m.group(1), m.group(2), r.label)].append(r)
    drop: set[int] = set()
    for rs in groups.values():
        rs.sort(key=lambda r: r.sid)
        parent = list(range(len(rs)))

        def find(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i in range(len(rs)):
            for j in range(i + 1, len(rs)):
                a, b = rs[i], rs[j]
                if a.zho == b.zho and a.other == b.other and own_notes(b) <= own_notes(a) and \
                        edit_distance(a.form.replace("’", "'"), b.form.replace("’", "'")) <= 2:
                    parent[find(j)] = find(i)
        for j in range(len(rs)):
            i = find(j)
            if i != j:
                rs[i].alt_forms += [f for f in [rs[j].form, *rs[j].alt_forms] if f not in rs[i].alt_forms]
                drop.add(id(rs[j]))
    return [r for r in records if id(r) not in drop]


# ------------------------------------------------------------------ per-line card rulings

def apply_card_rulings(records: list[Record], locs: dict[tuple[int, int], str]) -> list[Record]:
    """Per-line results the maintainer ruled on the decision page (data/card_rulings.json)."""
    rulings = json.loads((DATA / "card_rulings.json").read_text(encoding="utf-8"))["lines"]
    line_of = lambda r: int(re.search(r"-L(\d{5})", r.sid).group(1))
    for ru in rulings:
        n, loc = ru["line"], locs[(ru["line"], 0)]
        mine = [r for r in records if line_of(r) == n]
        if not mine:
            raise ValueError(f"card ruling for line {n}: the build has no S for that line")
        if "headwords" in ru:
            records = [r for r in records if not (line_of(r) == n and r.kind == "headwords")]
            for k, h in enumerate(ru["headwords"], start=1):
                records.append(Record(h["label"], "headwords", f"{h['label']}-L{n:05d}-{k:02d}", h["form"],
                                      [loc] + h.get("notes", []), [(z, []) for z in h["zho"]],
                                      alt_forms=list(h.get("alt", [])), other=[tuple(o) for o in h.get("other", [])]))
        if "examples" in ru:
            records = [r for r in records if not (line_of(r) == n and r.kind == "examples")]
            for i, x in enumerate(ru["examples"], start=1):
                for label in x["labels"]:
                    records.append(Record(label, "examples", f"{label}-L{n:05d}-e{i:02d}", x["form"],
                                          [loc] + x.get("notes", []), [(z, []) for z in x["zho"]],
                                          alt_forms=list(x.get("alt", []))))
        for a in ru.get("add_alt_translation", []):
            hit = [r for r in records if line_of(r) == n and (r.label, r.kind, r.form) == (a["label"], a["kind"], a["form"])]
            if len(hit) != 1:
                raise ValueError(f"card ruling for line {n}: expected one S {a}, found {len(hit)}")
            hit[0].zho.append((a["zho"], []))
        for c in ru.get("replace_chinese", []):
            hits = 0
            for r in records:
                if line_of(r) == n:
                    if r.label in c["only_labels"]:
                        new = [(c["to"], zn + [c["note"]]) if z == c["from"] else (z, zn) for z, zn in r.zho]
                    else:
                        new = [(z, zn) for z, zn in r.zho if z != c["from"]]
                    hits += new != r.zho
                    r.zho = new
            if not hits:
                raise ValueError(f"card ruling for line {n}: Chinese {c['from']!r} not found")
        for a in ru.get("alt_forms", []):
            group = [r for r in records if line_of(r) == n and r.label == a["label"] and r.kind == "headwords"
                     and r.form in a["forms"]]
            if len(group) == 1 and set(a["forms"][1:]) <= set(group[0].alt_forms) and group[0].form == a["forms"][0]:
                continue        # already one S (merge_alts applied the general rule)
            if len(group) != len(a["forms"]):
                raise ValueError(f"card ruling for line {n}: alt forms {a['forms']} not all found")
            group.sort(key=lambda r: a["forms"].index(r.form))
            group[0].alt_forms += [r.form for r in group[1:]]
            records = [r for r in records if r not in group[1:]]
    return records


# ------------------------------------------------------------------ French pages 1-4

def attach_french(records: list[Record], entries: list[Entry], source_lines: dict[int, str]) -> list[Record]:
    data = json.loads((DATA / "french_pages_1_4.json").read_text(encoding="utf-8"))["records"]
    decisions = {r["fr_id"]: r["decision"] for r in read_tsv(DATA / "french_decisions.tsv")}
    by_line: dict[int, list[Record]] = defaultdict(list)
    for r in records:
        m = re.search(r"-L(\d{5})-", r.sid)
        by_line[int(m.group(1))].append(r)
    window = [e for e in entries if e.line <= 330]

    def head_forms(e: Entry) -> list[str]:
        return [f.text for g in e.groups for f in g] + [q.text for s in e.senses for q in s.equivalents]

    # head words: order kept between entries, any order within an entry; <= 2 letters
    fr_heads = [r for r in data if r["kind"] == "headword" and decisions.get(r["id"]) is None]
    weights = {0: 3, 1: 2, 2: 1}
    n, m = len(fr_heads), len(window)
    score = [[(9, "", 9)] * m for _ in range(n)]
    for i, fr in enumerate(fr_heads):
        for k, e in enumerate(window):
            forms = head_forms(e)
            if forms:
                d, z = min((lev(letters(fr["form"]), letters(f)), f) for f in forms)
                second = min([lev(letters(fr["form"]), letters(f)) for f in forms if f != z] or [9])
                score[i][k] = (d, z, second)
    D = [[0.0] * (m + 1) for _ in range(n + 1)]
    B = [[""] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for k in range(1, m + 1):
            best, b = D[i - 1][k], "skip"
            if D[i][k - 1] > best:
                best, b = D[i][k - 1], "left"
            d, _, second = score[i - 1][k - 1]
            if d <= 2:
                w = weights[d] + (0.5 if second <= 2 else 0)
                if D[i - 1][k] + w > best:
                    best, b = D[i - 1][k] + w, "match"
            D[i][k], B[i][k] = best, b
    matches: dict[str, tuple[int, str]] = {}
    i, k = n, m
    while i > 0 and k > 0:
        if B[i][k] == "left":
            k -= 1
        elif B[i][k] == "skip":
            i -= 1
        else:
            matches[fr_heads[i - 1]["id"]] = (window[k - 1].line, score[i - 1][k - 1][1])
            i -= 1
    out = list(records)
    for fr in data:
        fid, dec = fr["id"], decisions.get(fr["id"])
        trs = [(t["text"], t["ver"]) for t in fr["translations"] if t["text"]]
        if dec == "separate":
            # parent markers (S003_0104), see french_decisions.tsv
            labels = {"S003_0104": {"N", "Z"}}.get(fid, {"unmarked"})
            kind = "headwords" if fr["kind"] == "headword" else "examples"
            for label in sorted(labels):
                out.append(Record(label, kind, f"{label}-FR-{fid}", fr["form"],
                                  [f"French volume p.{fr['page']:03d}; Poinsot & Pourrias Amis-French {fid}"], [], trs))
            continue
        targets: list[Record] = []
        alt = None
        if dec and dec.startswith("alt-form:"):
            line = int(dec.split(":")[1])
            targets = [r for r in by_line[line] if r.kind == "headwords"]
            alt = fr["form"]
        elif dec and dec.startswith("combine:"):
            ref = dec.split(":")[1]
            line = int(ref.split(".")[0])
            targets = [r for r in by_line[line] if r.kind == ("examples" if fr["kind"] == "example" else "headwords")]
            if "." in ref:      # a restored printed line: "119.90" = part 90 after source line 119
                targets = [r for r in targets if f"-L{line:05d}-s{ref.split('.')[1]}-" in r.sid]
        elif fr["kind"] == "headword":
            if fid in matches:
                line, form = matches[fid]
                # the form may have become a ver="alt" FORM (merge_alts, ruled 2026-10-17)
                targets = [r for r in by_line[line] if r.kind == "headwords"
                           and norm(form) in {norm(f) for f in [r.form, *r.alt_forms]}]
        else:
            best = None
            for r in out:
                if "-FR-" in r.sid:
                    continue
                ln = int(re.search(r"-L(\d{5})-", r.sid).group(1))
                if ln > 330:
                    continue
                d = lev(letters(fr["form"]), letters(r.form), cap=40)
                if best is None or d < best[0]:
                    best = (d, ln, r.form)
            if best and best[0] <= 2:
                targets = [r for r in by_line[best[1]] if r.form == best[2]]
        for r in targets:
            for t in trs:
                if t not in r.fra:
                    r.fra.append(t)
            if alt and alt not in r.alt_forms:
                r.alt_forms.append(alt)
    return out


# ------------------------------------------------------------------ writing

def file_path(out_dir: Path, label: str, kind: str) -> Path:
    folder = "Sakizaya" if label == "Z" else "Amis"
    return out_dir / folder / f"poinsot_chinese_{label}_{kind}.xml"


def write_files(records: list[Record], out_dir: Path) -> dict[tuple[str, str], int]:
    src_commit = SOURCE_TXT_COMMIT
    db_commit = SOURCE_DB_COMMIT
    counts = {}
    for label in LABELS:
        for kind in ("headwords", "examples"):
            root = ET.Element("TEXT", {
                "id": f"poinsot_chinese_{label}_{kind}",
                "citation": CITATION,
                "BibTeX_citation": BIBTEX,
                "copyright": COPYRIGHT,
                XML_LANG: "szy" if label == "Z" else "ami",
                "source": (f"wildjcrt/amis-chinese-poinsot-onefile@{src_commit} pourrias-poinsot.txt; printed page/line "
                           f"from miaoski/amis-chinese-poinsot@{db_commit} toufu.sq3; source label {label}"),
                "glottocode": "saki1247" if label == "Z" else "amis1246",
                "dialect": FILE_DIALECT[label],
            })
            mine = [r for r in records if r.label == label and r.kind == kind]
            if not mine:
                continue        # no empty files (Coastal has head words only); the tests list the expected files
            mine.sort(key=lambda r: r.sid)
            for r in mine:
                s = ET.SubElement(root, "S", {"id": r.sid})
                f = ET.SubElement(s, "FORM", {"kindOf": "original"})
                f.text = r.form
                notes = "; ".join(dict.fromkeys(x for x in r.form_notes if x))
                if notes:
                    f.set("notes", notes)
                for alt in r.alt_forms:
                    a = ET.SubElement(s, "FORM", {"kindOf": "original", "ver": "alt"})
                    a.text = alt
                for i, (zh, zn) in enumerate(r.zho):
                    attrs = {XML_LANG: "zho"}
                    if i:
                        attrs["ver"] = "alt"
                    if zn:
                        attrs["notes"] = "; ".join(dict.fromkeys(zn))
                    t = ET.SubElement(s, "TRANSL", attrs)
                    t.text = zh
                # V085: several TRANSL in one language need ver on all but the first (two Latin names, a French
                # name beside the French volume's translation, ...)
                seen_langs: set[str] = set()
                for lang, txt, tnotes in r.other:
                    attrs = {XML_LANG: lang}
                    if lang in seen_langs:
                        attrs["ver"] = "alt"
                    seen_langs.add(lang)
                    if tnotes:
                        attrs["notes"] = "; ".join(tnotes)
                    t = ET.SubElement(s, "TRANSL", attrs)
                    t.text = txt
                for i, (fr, ver) in enumerate(r.fra):
                    attrs = {XML_LANG: "fra"}
                    if i or ver or "fra" in seen_langs:
                        attrs["ver"] = "alt"
                    t = ET.SubElement(s, "TRANSL", attrs)
                    t.text = fr
            path = file_path(out_dir, label, kind)
            path.parent.mkdir(parents=True, exist_ok=True)
            ET.indent(root, space="  ")
            path.write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True) + b"\n")
            counts[(label, kind)] = len(mine)
    return counts


NON_CHINESE = {int(r["line"]): r["lang"] for r in read_tsv(DATA / "non_chinese_glosses.tsv")}


def build(out_dir: Path) -> dict[tuple[str, str], int]:
    raw = load_source(SOURCE_TXT)
    joined, members = apply_wraps(apply_corrections(raw))
    locs_raw = printed_locations(raw, SOURCE_DB)
    parts = apply_splits(joined)
    excluded = {int(r["line"]) for r in read_tsv(DATA / "exclusions.tsv")}
    # printed lines the 2020 DB marked blank, restored from the scan (restored_lines.tsv); part 90+ after a line
    restored_loc = {}
    for k, r in enumerate(read_tsv(DATA / "restored_lines.tsv")):
        key = (int(r["after_source_line"]), 90 + k)
        parts[key] = r["text"]
        restored_loc[key] = f"printed p.{int(r['page']):03d} l.{int(r['line']):02d}; restored from the scan (marked blank in the 2020 proofreading DB)"
    parts = {k: close_dangling(v) for k, v in parts.items()}
    entries = [parse_entry(n, j, members[n], text) for (n, j), text in sorted(parts.items()) if n not in excluded]
    locs = {(e.line, e.part): restored_loc.get((e.line, e.part)) or location_note([locs_raw[n] for n in e.lines]) for e in entries}
    records = build_records(entries, locs)
    records = merge_alts(records)
    records = apply_card_rulings(records, locs)
    records = attach_french(records, entries, raw)
    return write_files(records, out_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--xml-out-dir", type=Path, default=ROOT / "XML")
    args = parser.parse_args()
    counts = build(args.xml_out_dir)
    for (label, kind), n in sorted(counts.items()):
        print(f"{label:9} {kind:9} {n:6} S")


if __name__ == "__main__":
    main()
