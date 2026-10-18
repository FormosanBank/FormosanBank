"""Tests for the Amis-Chinese volume build (Cuerq & Pourrias 2002, "O Citig no Amis").

These encode the maintainer's rulings of 2026-10-17 (quoted in
FormosanBank/claudeplans/sweep-qa-decision-log.md, "Poinsot round 2"):

- one file pair (head words, example sentences) per source label S, N, F, T, Z
  and "unmarked" (everything not marked S, N, F, T or Z);
- Z is Sakizaya (xml:lang="szy", dialect="Sakizaya") under XML/Sakizaya/;
  everything else is Amis under XML/Amis/;
- N and S -> dialect="Southern"; F, T and unmarked -> dialect="Xiuguluan";
- an item marked with several dialects goes into each of their files;
- a reading marked as specific to one dialect gets its own entry in that
  dialect's file and does not appear for other dialects;
- borrowings carry a note "<Language> borrowing".

The checks deliberately do NOT import the extraction code. They re-read the
pinned source text with their own small rules, so a bug in the extractor
cannot be repeated by the test that is meant to catch it.

Scope rule assumed here for where a source marker applies (not yet ruled;
see the Poinsot round-2 decision page): in the part before the first
full-width colon, a marker applies to the "="-separated group it is written
in; after the colon, a marker applies to the "；"-separated piece it sits in.
Pieces that mix a marker with Amis forms or examples must be listed in
data/marker_scope.tsv.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

CODE = Path(__file__).resolve().parents[1]      # CodeAndDocs/
REPO = CODE.parent                               # the corpus root
SOURCE = CODE / "source" / "pourrias-poinsot.txt"
SOURCE_DB = CODE / "source" / "toufu.sq3"
XML_DIR = Path(os.environ.get("POINSOT_XML_DIR", REPO / "XML"))  # override to test a scratch build
DATA = CODE / "data"
BUILD_SCRIPT = CODE / "build_amis_chinese_xml.py"

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

DIALECT_CODES = ("S", "N", "F", "T", "Z")
LABELS = DIALECT_CODES + ("unmarked", "Coastal")   # Coastal: ruled 2026-10-17, cards r5-coastal-373 / -13029
FILE_DIALECT = {
    "Coastal": "Coastal",
    "S": "Southern",
    "N": "Southern",
    "F": "Xiuguluan",
    "T": "Xiuguluan",
    "unmarked": "Xiuguluan",
    "Z": "Sakizaya",
}
BORROWING = {
    "J": "Japanese",
    "Tw": "Hokkien",
    "Ch": "Mandarin",
    "英語": "English",
    "希臘文": "Greek",
    "希伯來語": "Hebrew",
}
KINDS = ("headwords", "examples")
# Every file pair, except Coastal examples: the two Coastal readings are head words, so that file would be empty
FILES = [(l, k) for l in LABELS for k in KINDS if (l, k) != ("Coastal", "examples")]

# French pages 1-4 records the maintainer ruled "separate" (rounds 3-4). Placement follows the rulings: a French
# example goes where its French parent entry's markers send it (S003_0104's parent is "adidi' - {N.Z.} = mimig").
FRENCH_SEPARATE = {
    "S002_0031": ("headwords", {"unmarked"}),   # pa'acfelan
    "S002_0163": ("headwords", {"unmarked"}),   # adapagpag
    "S001_0018": ("examples", {"unmarked"}),    # Padagen cigra a mihinam to kolog.  (parent a)
    "S001_0072": ("examples", {"unmarked"}),    # maro' itini aca, itira aca.  (parent aca)
    "S002_0096": ("examples", {"unmarked"}),    # ci'ada  (parent 'ada)
    "S002_0150": ("examples", {"unmarked"}),    # maadah to ko adada  (parent adah - maadah)
    "S003_0042": ("examples", {"unmarked"}),    # sa mato 'adicaw ko faloco' iso  (parent 'adicaw)
    "S003_0084": ("examples", {"unmarked"}),    # ma'adi ko hmay  (parent 'adi = 'og'og)
    "S003_0104": ("examples", {"N", "Z"}),      # adidi'ay a wawa  (parent adidi' - {N.Z.})
}
# S002_0022 (tfod saan ko 'acfel … colonne de fumée) is COMBINED with line 48 once the wrapped "a 'acfel：煙柱" is rejoined.

MARKER = re.compile(r"\{([^}]*)\}")
CJK = re.compile(r"[㐀-鿿豈-﫿]")
CJK_RUN = re.compile(r"[㐀-鿿豈-﫿]+")
LATIN_WORD = r"[A-Za-z][A-Za-z'’]*"
LATIN_WORDS_IN_A_ROW = re.compile(LATIN_WORD + r"(?:[ \t\-]+" + LATIN_WORD + r")+")
ID_LINE = re.compile(r"-L(\d{5})(?:-s(\d+))?-")  # -L<line>- or -L<line>-s<part>- (entries split apart, line_splits.tsv)
ID_FRENCH = re.compile(r"-FR-(S\d{3}_\d{4})$")  # French-only entries kept separate (no Chinese line)


# ---------------------------------------------------------------- helpers

def file_path(label: str, kind: str) -> Path:
    folder = "Sakizaya" if label == "Z" else "Amis"
    return XML_DIR / folder / f"poinsot_chinese_{label}_{kind}.xml"


@functools.lru_cache(maxsize=None)
def source_lines() -> dict[int, str]:
    text = SOURCE.read_text(encoding="utf-8")
    return {n: line for n, line in enumerate(text.split("\n"), start=1) if line.strip()}


def head_part(line: str) -> str:
    """The head word: up to the first full-width colon, or the first Chinese character outside a {marker}
    if that comes earlier ("tka - 開始；起頭 - anini ko tka：…" has its gloss before the colon)."""
    head = line.split("：", 1)[0]
    masked = MARKER.sub(lambda m: " " * len(m.group(0)), head)
    m = CJK.search(masked)
    head = re.sub(r"[\s\-]+$", "", head[:m.start()]) if m else head
    # "dadinas (=lilit)", "paso’lin - (mipaso’lin = pakaso’lin)": parentheses that only enclose an '=' list
    head = re.sub(r"[(（]\s*[=＝]\s*([^()（）：\u3400-\u9fff]*?)\s*[)）]", r" = \1", head)
    return re.sub(r"[(（]([^()（）：\u3400-\u9fff]*[=＝][^()（）：\u3400-\u9fff]*)[)）]", r"\1", head)


def after_colon(line: str) -> str:
    return line[len(head_part(line)):].lstrip(" -：")


def markers(text: str) -> set[str]:
    return set(MARKER.findall(text))


def amis_words(text: str) -> list[str]:
    # A bare hyphen separates root and derived form in this book (acak-maacak), so it splits words.
    text = MARKER.sub(" ", text)
    return [w for w in re.findall(r"[A-Za-z'’]+", text) if re.search("[A-Za-z]", w)]


def head_groups(line: str) -> list[tuple[set[str], set[str]]]:
    """'='-separated groups of the head part: (dialect markers, Amis words)."""
    out: list[tuple[set[str], set[str]]] = []
    for group in re.split(r"[=＝]", head_part(line)):
        tags = markers(group) & set(DIALECT_CODES)
        words = {w.strip("-") for w in amis_words(re.sub(r"<\d+>|\([^)]*\)", " ", group))}
        if not words and out:
            out[-1][0].update(tags)   # "kapia = {S}：" - a marker alone in an '=' slot belongs to the word before
            continue
        out.append((tags, words))
    return out


def within(form: str, words: set[str]) -> bool:
    """All words of a (possibly multi-word) form belong to the given word set."""
    ws = set(amis_words(form))
    return bool(ws) and ws <= words


def clean_tagged_readings(line: str) -> list[tuple[set[str], str]]:
    """After-colon pieces that hold one dialect marker plus Chinese only.

    Returns (markers, Chinese reading). Pieces that also contain Amis forms
    or examples (" - " or "=") are not 'clean' and are handled by
    marker_scope.tsv instead.
    """
    out = []
    for piece in re.split(r"[；;]", after_colon(line)):
        tags = markers(piece) & set(DIALECT_CODES)
        if not tags or " - " in piece or "=" in piece or "＝" in piece:
            continue
        for reading in pieces(MARKER.sub("", piece)):   # compared sense by sense, as translations are
            out.append((tags, reading))
    return out


def after_colon_unmarked_forms(line: str) -> set[str]:
    """Amis words written after the colon in a piece that carries no dialect marker. Ruled 2026-10-17 ("I think we
    assume it is inherited"): such words take the head word's dialect, so they belong wherever the head goes."""
    out: set[str] = set()
    for piece in re.split(r"[；;]", after_colon(line)):
        if not (markers(piece) & set(DIALECT_CODES)):
            out |= set(amis_words(piece))
    return out


def mixed_marker_pieces(line: str) -> list[str]:
    return [
        piece for piece in re.split(r"[；;]", after_colon(line))
        if markers(piece) & set(DIALECT_CODES) and (" - " in piece or "=" in piece or "＝" in piece)
    ]


def pieces(text: str) -> set[str]:
    """A translation split into its senses, punctuation removed, for comparison."""
    return {"".join(CJK.findall(p)) for p in re.split(r"[；;，,、：]", text) if CJK.search(p)}


class Record:
    """One <S> as the tests see it."""

    def __init__(self, label: str, kind: str, s: ET.Element):
        self.label, self.kind = label, kind
        self.id = s.get("id")
        m = ID_LINE.search(self.id or "")
        self.line = int(m.group(1)) if m else None
        self.part = int(m.group(2)) if m and m.group(2) else 0
        f = ID_FRENCH.search(self.id or "")
        self.french_id = f.group(1) if f else None
        forms = s.findall("FORM")
        self.form = " ".join(f.text or "" for f in forms if f.get("kindOf") == "original" and f.get("ver") != "alt")
        self.alt_forms = [f.text or "" for f in forms if f.get("kindOf") == "original" and f.get("ver") == "alt"]
        self.zho = [t.text or "" for t in s.findall("TRANSL") if t.get(XML_LANG) == "zho"]
        # French TRANSLs from the French volume's pages 1-4; a French plant/animal name printed in the Chinese volume
        # (note "French name", ruled 2026-10-17 round 6) counts with the other-language names instead
        is_name = lambda t: t.get(XML_LANG) == "fra" and t.get("notes") == "French name"
        self.fra = [t.text or "" for t in s.findall("TRANSL") if t.get(XML_LANG) == "fra" and not is_name(t)]
        self.other = [t.text or "" for t in s.findall("TRANSL") if t.get(XML_LANG) not in ("zho", "fra") or is_name(t)]
        self.notes = " ".join(e.get("notes") or "" for e in list(s) if e.get("notes"))
        self.form_notes = " ".join(f.get("notes") or "" for f in forms if f.get("notes"))


_CACHE: dict = {}


def load_all() -> dict[tuple[str, str], tuple[ET.Element, list[Record]]]:
    if "all" not in _CACHE:
        out = {}
        for label, kind in FILES:
            root = ET.parse(file_path(label, kind)).getroot()
            out[(label, kind)] = (root, [Record(label, kind, s) for s in root.iter("S")])
        _CACHE["all"] = out
    return _CACHE["all"]


def records(kind: str | None = None) -> list[Record]:
    return [r for (lab, k), (_, rs) in load_all().items() for r in rs if kind in (None, k)]


def by_line(kind: str | None = None) -> dict[int, list[Record]]:
    out: dict[int, list[Record]] = defaultdict(list)
    for r in records(kind):
        if r.line is not None:
            out[r.line].append(r)
    return out


@functools.lru_cache(maxsize=None)
def joined_lines() -> dict[int, int]:
    """Line -> the line it was joined onto (printed-line wraps decided 'joined' in line_wraps.tsv)."""
    path = DATA / "line_wraps.tsv"
    joined = set()
    if path.exists():
        for row in path.read_text(encoding="utf-8").splitlines()[1:]:
            if row.strip() and row.split("\t")[1] == "joined":
                joined.add(int(row.split("\t")[0]))
    out, lines = {}, sorted(source_lines())
    for prev, cur in zip(lines, lines[1:]):
        if cur in joined:
            out[cur] = out.get(prev, prev)
    return out


def owner(n: int) -> int:
    return joined_lines().get(n, n)


def _keyed(text: str) -> tuple[str, list[int]]:
    chars, idx = [], []
    for i, ch in enumerate(text):
        c = ch.lower()
        if ("a" <= c <= "z") or ("0" <= c <= "9") or CJK.match(c):
            chars.append(c)
            idx.append(i)
    return "".join(chars), idx


@functools.lru_cache(maxsize=None)
def corrected_lines() -> dict[int, str]:
    """Source lines with the recorded typing corrections (text_corrections.tsv) applied."""
    lines = dict(source_lines())
    path = DATA / "text_corrections.tsv"
    if path.exists():
        for row in path.read_text(encoding="utf-8").splitlines()[1:]:
            if row.strip():
                n, old, new = row.split("\t")[:3]
                lines[int(n)] = lines[int(n)].replace(old, new)
    return lines


@functools.lru_cache(maxsize=None)
def source_entries() -> dict[tuple[int, int], str]:
    """Entries as the rulings define them: source lines, with printed-line wraps joined onto the line before
    (line_wraps.tsv), recorded typing corrections applied (text_corrections.tsv), and entries glued onto the
    line before split off again (line_splits.tsv). Keys are (line, part)."""
    lines = corrected_lines()
    joined: dict[int, str] = {}
    for n in sorted(lines):
        o = owner(n)
        joined[o] = (joined[o].rstrip() + " " + lines[n].lstrip()) if o != n else lines[n]
    fps: dict[int, list[str]] = defaultdict(list)
    path = DATA / "line_splits.tsv"
    if path.exists():
        for row in path.read_text(encoding="utf-8").splitlines()[1:]:
            cols = row.split("\t")
            if len(cols) > 2 and cols[2] == "split":
                fps[int(cols[0])].append(cols[1])
    out: dict[tuple[int, int], str] = {}
    for n, text in joined.items():
        k, idx = _keyed(text)
        cuts, last = [], len(head_part(text))
        for fp in fps.get(n, []):
            pos = next((i for i in range(len(k)) if idx[i] > last and k.startswith(fp, i)), None)
            assert pos is not None, f"line {n}: split fingerprint {fp} not found"
            off = idx[pos]
            while off > 0 and text[off - 1] in "’'‘":
                off -= 1
            cuts.append(off)
            last = off
        bounds = [0] + cuts + [len(text)]
        for j, (a, b) in enumerate(zip(bounds, bounds[1:])):
            out[(n, j)] = text[a:b].strip()
    # printed lines the 2020 DB marked blank, restored from the scan: part 90+k after a source line
    path = DATA / "restored_lines.tsv"
    if path.exists():
        for k, row in enumerate(path.read_text(encoding="utf-8").splitlines()[1:]):
            cols = row.split("\t")
            out[(int(cols[2]), 90 + k)] = cols[3]
    return out


def by_entry(kind: str | None = None) -> dict[tuple[int, int], list["Record"]]:
    out: dict[tuple[int, int], list[Record]] = defaultdict(list)
    for r in records(kind):
        if r.line is not None:
            out[(r.line, r.part)].append(r)
    return out


@functools.lru_cache(maxsize=None)
def excluded_lines() -> set[int]:
    """Lines the maintainer ruled out of the corpus (data/exclusions.tsv)."""
    path = DATA / "exclusions.tsv"
    rows = path.read_text(encoding="utf-8").splitlines()[1:] if path.exists() else []
    return {int(r.split("\t")[0]) for r in rows if r.strip()}


@functools.lru_cache(maxsize=None)
def card_ruled_lines() -> set[int]:
    """Lines whose result the maintainer ruled card by card (data/card_rulings.json)."""
    import json
    path = DATA / "card_rulings.json"
    return {x["line"] for x in json.loads(path.read_text(encoding="utf-8"))["lines"]} if path.exists() else set()


def scope_file_lines() -> set[int]:
    path = DATA / "marker_scope.tsv"
    if not path.exists():
        return set()
    out = set()
    for row in path.read_text(encoding="utf-8").splitlines()[1:]:
        if row.strip():
            line, decision = row.split("\t")[:2]
            if decision in {"accepted", "corrected"}:   # a proposal awaiting the maintainer does not count
                out.add(int(line))
    return out


# ---------------------------------------------------------------- tests

class SourceIsPinned(unittest.TestCase):
    def test_source_present_and_unchanged_shape(self) -> None:
        self.assertTrue(SOURCE.exists(), f"missing {SOURCE}: run CodeAndDocs/refresh_source.sh")
        lines = source_lines()
        self.assertEqual(len(lines), 17930, "pinned pourrias-poinsot.txt@365cfce has 17,930 entries")
        no_colon = [n for n, l in lines.items() if "：" not in l]
        self.assertEqual(no_colon, [], "every entry has a full-width colon")

    def test_source_files_match_their_pinned_hashes(self) -> None:
        sys.path.insert(0, str(CODE))
        import build_amis_chinese_xml as B
        for path, want in ((SOURCE, B.SOURCE_TXT_SHA256), (SOURCE_DB, B.SOURCE_DB_SHA256)):
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), want, f"{path.name} differs from the pinned copy")


class FileLayout(unittest.TestCase):
    """Ruling: two folders, one file pair per label, language and dialect per label."""

    def test_exactly_the_expected_files(self) -> None:
        expected = {file_path(l, k).relative_to(XML_DIR) for l, k in FILES}
        found = {p.relative_to(XML_DIR) for p in XML_DIR.rglob("*.xml")}
        self.assertEqual(found, expected)

    def test_language_and_dialect(self) -> None:
        for (label, kind), (root, _) in load_all().items():
            with self.subTest(label=label, kind=kind):
                self.assertEqual(root.get(XML_LANG), "szy" if label == "Z" else "ami")
                self.assertEqual(root.get("dialect"), FILE_DIALECT[label])

    def test_citation_names_both_volumes(self) -> None:
        for (label, kind), (root, _) in load_all().items():
            with self.subTest(label=label, kind=kind):
                cit = root.get("citation") or ""
                for name in ("Cuerq", "Pourrias", "2002", "Poinsot"):
                    self.assertIn(name, cit)

    def test_ids_unique_and_point_at_a_source_line(self) -> None:
        lines = source_lines()
        for (label, kind), (_, rs) in load_all().items():
            with self.subTest(label=label, kind=kind):
                ids = [r.id for r in rs]
                self.assertEqual(len(ids), len(set(ids)), "duplicate S ids")
                bad = [r.id for r in rs if r.line not in lines and r.french_id not in FRENCH_SEPARATE]
                self.assertEqual(bad, [], "ids must carry -L<source line>- or name a ruled-separate French record")

    def test_no_file_is_empty(self) -> None:
        for (label, kind), (_, rs) in load_all().items():
            with self.subTest(label=label, kind=kind):
                self.assertGreater(len(rs), 0)


class DialectAssignment(unittest.TestCase):
    """Ruling: every item in a dialect file was marked with that dialect."""

    def test_every_item_in_a_dialect_file_was_marked_with_that_dialect(self) -> None:
        entries, scope = source_entries(), scope_file_lines()
        problems = []
        for r in records("headwords"):
            if r.line is None:
                continue  # French-only entries: checked in FrenchSeparate
            line = entries[(r.line, r.part)]
            groups = head_groups(line)
            clean = clean_tagged_readings(line)
            if r.label == "unmarked":
                untagged_words = set().union(*[w for t, w in groups if not t])
                head_tagged = any(t for t, _ in groups)
                ok = within(r.form, untagged_words) or not head_tagged
                tagged_readings = {rd for _, rd in clean}
                ok = ok and not (pieces("；".join(r.zho)) & tagged_readings)
            else:
                tagged_words = set().union(*[w for t, w in groups if r.label in t]) if groups else set()
                readings = {rd for t, rd in clean if r.label in t}
                first_tags = groups[0][0] if groups else set()
                inherited = r.label in first_tags and within(r.form, after_colon_unmarked_forms(line))
                ok = within(r.form, tagged_words) or inherited or (bool(r.zho) and pieces("；".join(r.zho)) <= readings)
            if not ok and r.line not in scope:
                problems.append(f"{r.label} {r.id} {r.form!r} {r.zho} <- line {r.line}: {line[:90]}")
        self.assertEqual(problems[:20], [], f"{len(problems)} items not justified by a source marker")

    def test_examples_follow_their_entry(self) -> None:
        heads = by_entry("headwords")
        problems = [
            f"{r.id} in {r.label}" for r in records("examples")
            if r.line is not None and r.label not in {h.label for h in heads.get((r.line, r.part), [])}
            and r.line not in card_ruled_lines()
        ]
        self.assertEqual(problems[:20], [], f"{len(problems)} examples sit in a file their entry is not in")

    def test_dialect_specific_reading_not_in_other_dialects(self) -> None:
        heads = by_entry("headwords")
        problems = []
        scope = scope_file_lines()
        for n, line in source_entries().items():
            if n[0] in scope or n[0] in excluded_lines():
                continue      # the maintainer ruled this line's reading card by card
            # Chinese readings marked after the colon
            for tags, reading in clean_tagged_readings(line):
                for r in heads.get(n, []):
                    if r.label not in tags and reading in pieces("；".join(r.zho)):
                        problems.append(f"line {n}: {reading} ({tags}) also in {r.label} {r.id}")
            # Amis forms marked in the head part
            groups = head_groups(line)
            if sum(1 for t, _ in groups if t) and len({frozenset(t) for t, _ in groups}) > 1:
                for tags, words in groups:
                    for r in heads.get(n, []):
                        if within(r.form, words) and r.label not in (tags or {"unmarked"}):
                            problems.append(f"line {n}: {r.form} ({tags or 'unmarked'}) also in {r.label} {r.id}")
        self.assertEqual(problems[:20], [], f"{len(problems)} dialect-specific readings leaked")

    def test_head_marker_counts_match_headword_files(self) -> None:
        """Every head-marked line is in that dialect's head-word file; extra lines only
        come from markers after the colon (so the count is bounded on both sides)."""
        lines = source_entries()
        heads = by_entry("headwords")
        for code in DIALECT_CODES:
            with self.subTest(code=code):
                head_marked = {n for n, l in lines.items() if code in markers(head_part(l))}
                anywhere = {n for n, l in lines.items() if code in markers(l)}
                in_file = {n for n, rs in heads.items() if any(r.label == code for r in rs)}
                missing = sorted(n for n in head_marked - in_file if n[0] not in card_ruled_lines() | excluded_lines())
                self.assertEqual(missing[:20], [], f"{len(missing)} head-marked {code} lines missing")
                self.assertLessEqual(in_file, anywhere, f"{code} file holds lines never marked {code}")

    def test_mixed_marker_pieces_are_accounted_for(self) -> None:
        """Markers sharing a piece with Amis forms/examples need a recorded scope decision."""
        scope = scope_file_lines()
        missing = sorted({n for (n, j), l in source_entries().items() if mixed_marker_pieces(l) and n not in scope and n not in excluded_lines()})
        self.assertEqual(missing[:20], [], f"{len(missing)} lines with mixed-piece markers not in marker_scope.tsv")


class KnownEntries(unittest.TestCase):
    """Real entries whose correct placement is known; line numbers in pourrias-poinsot.txt@365cfce."""

    def where(self, line: int, kind: str = "headwords") -> dict[str, list[Record]]:
        out: dict[str, list[Record]] = defaultdict(list)
        for r in by_line(kind).get(line, []):
            out[r.label].append(r)
        return out

    def test_form_specific_markers_amrakay(self) -> None:
        # 497: amrakay - {N} = 'amrek {S}：弱的
        w = self.where(497)
        self.assertEqual({r.form for r in w["N"]}, {"amrakay"})
        self.assertEqual({r.form for r in w["S"]}, {"'amrek"})
        self.assertNotIn("unmarked", w)

    def test_sense_specific_markers_ciyak(self) -> None:
        # 1949: ciyak - {N}：西瓜：cak, lidaw, kacawas, sinar；南瓜{S}
        w = self.where(1949)
        self.assertTrue(any("西瓜" in " ".join(r.zho) for r in w["N"]))
        self.assertFalse(any("南瓜" in " ".join(r.zho) for r in w["N"]))
        self.assertTrue(w["S"] and all(pieces("；".join(r.zho)) == {"南瓜"} for r in w["S"]))

    def test_sense_marker_in_untagged_entry_afilid(self) -> None:
        # 190: 'afilid：提起；抱起來 {N}；用一個臂抓重物
        w = self.where(190)
        unmarked = pieces("；".join(t for r in w["unmarked"] for t in r.zho))
        self.assertEqual(unmarked, {"提起", "用一個臂抓重物"})
        self.assertEqual(pieces("；".join(t for r in w["N"] for t in r.zho)), {"抱起來"})

    def test_two_dialects_one_word_adidi(self) -> None:
        # 119: adidi' - {N}{Z} = mimig：矮瘦子；小；不大  -> N file and Sakizaya file
        w = self.where(119)
        self.assertIn("adidi'", {r.form for r in w["N"]})
        self.assertIn("adidi'", {r.form for r in w["Z"]})
        self.assertNotIn("adidi'", {r.form for r in w["unmarked"]})

    def test_homographs_stay_apart_alet(self) -> None:
        # 341 'alet = sa'et = 'alat：柵欄 | 342 'alet - {F} = taker = tna'：禁止… | 343 'alet - {Z} = misawad：放棄
        self.assertIn("柵欄", " ".join(t for r in self.where(341)["unmarked"] for t in r.zho))
        self.assertIn("禁止", " ".join(t for r in self.where(342)["F"] for t in r.zho))
        self.assertIn("放棄", " ".join(t for r in self.where(343)["Z"] for t in r.zho))
        self.assertNotIn("Z", self.where(341))
        self.assertNotIn("F", self.where(343))

    def test_sakizaya_only_acawa(self) -> None:
        # 37: acawa {Z}：丈夫或妻子
        self.assertEqual(set(self.where(37)), {"Z"})

    def test_borrowing_notes(self) -> None:
        # 269: ainoko {J}：混血兒 ; 6587: kansiya {J} {Tw} = aray = ahowid：…
        notes = " ".join(r.notes for rs in self.where(269).values() for r in rs)
        self.assertIn("Japanese borrowing", notes)
        notes = " ".join(r.notes for rs in self.where(6587).values() for r in rs)
        self.assertIn("Japanese borrowing", notes)
        self.assertIn("Hokkien borrowing", notes)
        self.assertEqual(set(self.where(269)), {"unmarked"})

    def test_printed_text_is_not_corrected(self) -> None:
        # 17237: the print says 感官經 (checked on the scan strip), not 神經
        zho = " ".join(t for rs in self.where(17237).values() for r in rs for t in r.zho)
        self.assertIn("感官經", zho)
        self.assertNotIn("神經", zho)

    def test_printed_page_and_line(self) -> None:
        cases = {497: "p.019 l.40", 5: "p.005 l.15", 2578: "p.085 l.08"}
        for line, loc in cases.items():
            with self.subTest(line=line):
                notes = " ".join(r.form_notes for rs in self.where(line).values() for r in rs)
                self.assertIn(loc, notes)

    def test_unmatched_entries_are_flagged(self) -> None:
        for line in (11425, 11427, 11450):  # otoy, otrak, oyas: not in the 2020 proofreading DB
            with self.subTest(line=line):
                notes = " ".join(r.form_notes for rs in self.where(line).values() for r in rs)
                self.assertIn("uncertain; need to check", notes)


class TextShape(unittest.TestCase):
    """Ruling: what Chinese translations and Amis/Sakizaya forms may contain."""

    def test_chinese_translations_have_chinese_and_no_latin_word_runs(self) -> None:
        problems = []
        for r in records():
            for t in r.zho:
                if not CJK.search(t):
                    problems.append(f"{r.id}: no Chinese: {t!r}")
                m = LATIN_WORDS_IN_A_ROW.search(KEEP_IN_CHINESE.sub(" ", t))
                if m:
                    problems.append(f"{r.id}: Latin words {m.group(0)!r} in {t!r}")
        self.assertEqual(problems[:20], [], f"{len(problems)} bad Chinese translations")

    def test_amis_and_sakizaya_forms(self) -> None:
        """At most 3 Chinese characters in a row; at least 80% of the letters Latin.

        Letters = Latin letters, the apostrophe letters ' and ’, and CJK characters.
        Spaces, punctuation and digits are not counted either way.
        """
        problems = []
        for r in records():
            run = max((len(m) for m in CJK_RUN.findall(r.form)), default=0)
            latin = len(re.findall(r"[A-Za-z'’]", r.form))
            letters = latin + len(CJK.findall(r.form))
            if run > 3 or not letters or latin / letters < 0.8:
                problems.append(f"{r.id}: {r.form!r}")
        self.assertEqual(problems[:20], [], f"{len(problems)} bad Amis/Sakizaya forms")

    def test_no_source_markup_left_in_text(self) -> None:
        """No {marker} or <n> anywhere; no colon in an Amis form; in a Chinese translation a colon is ordinary
        punctuation ("雷聲：低沉的聲…") unless it dangles at either end or is doubled (left over from moving text out)."""
        problems = [
            f"{r.id}: {txt!r}" for r in records()
            for txt, is_zh in [(r.form, False)] + [(z, True) for z in r.zho] + [(f, False) for f in r.fra]
            if re.search(r"[{}]|<\d+>", txt)
            or (not is_zh and "：" in txt)
            or (is_zh and re.search(r"^\s*：|：\s*$|：\s*：", txt))
        ]
        self.assertEqual(problems[:20], [], f"{len(problems)} texts still carry markers or colons")


class NothingLost(unittest.TestCase):
    """Every source entry, Amis word and Chinese character ends up somewhere."""

    def test_every_source_line_has_a_head_word_entry(self) -> None:
        excluded = {}
        path = DATA / "exclusions.tsv"
        if path.exists():
            for row in path.read_text(encoding="utf-8").splitlines()[1:]:
                n, reason = row.split("\t", 1)
                self.assertTrue(reason.strip(), f"exclusion {n} has no reason")
                excluded[int(n)] = reason
        heads = by_line("headwords")
        joined = joined_lines()
        no_heads = {x for x in card_ruled_lines()}   # e.g. 13550: ruled to have an example and no head word
        missing = [n for n in source_lines() if owner(n) not in heads and n not in excluded and owner(n) not in no_heads]
        self.assertEqual(missing[:20], [], f"{len(missing)} source lines produced no head-word entry")
        self.assertLessEqual(len(excluded), 90, "more than 0.5% of entries excluded")

    def test_no_amis_letters_lost(self) -> None:
        lines = corrected_lines()
        text_by_line: dict[int, str] = defaultdict(str)
        for r in records():
            text_by_line[r.line] += " ".join([r.form, r.notes, *r.zho, *r.fra, *r.other, *r.alt_forms]) + " "
        problems = []
        for n, line in lines.items():
            if owner(n) in excluded_lines() or owner(n) in card_ruled_lines():
                continue     # ruled out, or the maintainer specified the result word by word (card_rulings.json)
            have = text_by_line.get(owner(n), "").replace("’", "'")
            line = re.sub("|".join(re.escape(x) for x, c in latin_runs().items() if c == "drop"), " ", line)
            for w in amis_words(line):
                if w.replace("’", "'") not in have:
                    problems.append(f"line {n}: {w!r}")
        self.assertEqual(problems[:20], [], f"{len(problems)} Amis/Latin words from the source appear nowhere")

    def test_no_chinese_lost(self) -> None:
        lines = source_lines()
        text_by_line: dict[int, str] = defaultdict(str)
        for r in records():
            text_by_line[r.line] += " ".join([r.notes, *r.zho]) + " "
        problems = []
        for n, line in lines.items():
            if owner(n) in excluded_lines() or owner(n) in card_ruled_lines():
                continue
            # "[宗]" (religion label) is dropped everywhere: ruled 2026-10-17, card r6-zong-6599 "Drop [宗] everywhere"
            for run in CJK_RUN.findall(MARKER.sub(" ", line.replace("[宗]", " "))):
                if run not in text_by_line.get(owner(n), ""):
                    problems.append(f"line {n}: {run}")
        self.assertEqual(problems[:20], [], f"{len(problems)} Chinese runs from the source appear nowhere")

    def test_borrowing_notes_match_source_markers(self) -> None:
        lines = {n: l for n, l in corrected_lines().items() if owner(n) not in card_ruled_lines()}
        notes_by_line: dict[int, str] = defaultdict(str)
        for r in records():
            notes_by_line[r.line] += r.notes + " "
        problems = []
        group_markers: dict[int, set[str]] = defaultdict(set)
        for n, line in lines.items():
            group_markers[owner(n)] |= markers(line)
        for n, line in lines.items():
            for code, lang in BORROWING.items():
                marked = code in group_markers[owner(n)]
                noted = f"{lang} borrowing" in notes_by_line.get(owner(n), "")
                if marked != noted:
                    problems.append(f"line {n}: {code} marked={marked} noted={noted}")
        self.assertEqual(problems[:20], [], f"{len(problems)} borrowing notes missing or unjustified")

    def test_place_labels_kept_in_notes(self) -> None:
        """{豐濱} {玉里} {光復鄉} {Tingalaw} are not dialect codes; the label must survive in notes."""
        notes_by_line: dict[int, str] = defaultdict(str)
        for r in records():
            notes_by_line[r.line] += r.notes + " "
        problems = [
            f"line {n}: {label}"
            for n, line in source_lines().items()
            for label in markers(line) & {"豐濱", "玉里", "光復鄉", "Tingalaw"}
            if label not in notes_by_line.get(owner(n), "")
        ]
        self.assertEqual(problems, [])

    def test_every_head_word_entry_has_a_printed_location(self) -> None:
        bad = [
            r.id for r in records("headwords")
            if not re.search(r"printed p\.\d{3} l\.\d{2}|uncertain; need to check|French volume p\.\d{3}", r.form_notes)
        ]
        self.assertEqual(bad[:20], [], f"{len(bad)} entries without page/line or the uncertain flag")


class FrenchPagesOneToFour(unittest.TestCase):
    """Ruling d4: French from pages 1-4 attaches to the matching Chinese entries."""

    LAST_ALIGNED_LINE = 199  # afsa'：淡而無味的食物 = S004_0169 afsa' (fade, doux), the last French page-4 entry

    def test_french_only_where_the_french_pages_reach(self) -> None:
        late = [r.id for r in records() if r.fra and r.line is not None and r.line > self.LAST_ALIGNED_LINE]
        self.assertEqual(late, [])

    def test_known_attachments(self) -> None:
        heads = by_line("headwords")
        cases = {5: "gibier", 6: "donner des cadeaux"}  # 'a'adopen, aag
        for line, fra in cases.items():
            with self.subTest(line=line):
                self.assertIn(fra, " ".join(t for r in heads.get(line, []) for t in r.fra))


def _norm_form(w: str) -> str:
    # The apostrophe is a letter (glottal stop): keep it; only fold its shape and case.
    return w.lower().replace("’", "'").replace("‘", "'").strip().strip("-").strip()


def root_and_defined(line: str) -> tuple[str | None, list[str]]:
    """Root and the forms an entry defines.

    The head word is first split on '=' (equivalents). Only the first '=' group can hold a root: a word
    followed by ' - ' and at least one further Amis word ("aag - mapaag"). "acoho - {S} = X" and
    "a - <1>" have nothing after the dash but a marker or a sense number, so their first word is defined,
    not a root. A bare hyphen counts as a root boundary only when the right side contains the left side
    ("acak-maacak"); otherwise it is part of one word.
    """
    head = re.sub(r"\{[^}]*\}|<\d+>|\([^)]*\)", " ", head_part(line))
    groups = re.split(r"\s*[=＝]\s*", head)

    def parts_of(group: str) -> list[str]:
        out = []
        for chunk in re.split(r"\s+-\s*|\s*-\s+", group):
            bits = chunk.split("-")
            ln = lambda s: re.sub(r"[^a-z']", "", _norm_form(s))
            if len(bits) == 2 and all(re.search("[A-Za-z]", b) for b in bits) and ln(bits[0]).strip("'") in ln(bits[1]):
                out += bits
            else:
                out.append(chunk)
        return [p.strip() for p in out if re.search("[A-Za-z]", p) and not CJK.search(p)]

    first = parts_of(groups[0])
    rest = [x for g in groups[1:] for p in parts_of(g) for x in re.split(r"\s*,\s*", p)]
    if len(first) >= 2:
        root = first[0]
        defined = [x for p in first[1:] for x in re.split(r"\s*,\s*", p)] + rest
        return _norm_form(root), [_norm_form(d) for d in defined if _norm_form(d)]
    defined = [x for p in first for x in re.split(r"\s*,\s*", p)] + rest
    return None, [_norm_form(d) for d in defined if _norm_form(d)]


def roots_without_own_entry() -> dict[str, list[int]]:
    translated: set[str] = set()
    roots: dict[str, list[int]] = defaultdict(list)
    glossed_word = re.compile(r"(?:^|[\s\-；;=(（])([A-Za-z'’][A-Za-z'’]*)\s*(?:\{[^}]*\}\s*)*(?:[(（][^)）]*[)）]\s*)?：\s*[^：]*?[\u3400-\u9fff]")
    after_eq = re.compile(r"[=＝]\s*(?:\{[^}]*\}\s*)*([A-Za-z'’][A-Za-z'’ ]*[A-Za-z'’])")
    pair_first = re.compile(r"(?:^|[\s\-；;(（])([A-Za-z'’][A-Za-z'’]*)\s+[=＝]\s+[A-Za-z'’][A-Za-z'’ ]*：\s*[^：]*?[㐀-鿿]")
    for n, line in source_entries().items():
        root, defined = root_and_defined(line)
        body = after_colon(line)
        if CJK.search(body):
            translated.update(defined)
        # words that carry their own gloss or are '=' equivalents after the colon also have a translated entry
        translated.update(_norm_form(m.group(1)) for m in glossed_word.finditer(body))
        if CJK.search(body):
            translated.update(_norm_form(m.group(1)) for m in after_eq.finditer(body))
        # the first form of a word pair with its own translation ("{T} sodiget = sogidet：鼻涕") is a head word too
        # (ruled 2026-10-18, decision page card r2-m5-sodiget: "Convert it: the book translates sodiget, so it has
        # its own entry")
        translated.update(_norm_form(m.group(1)) for m in pair_first.finditer(body))
        if root:
            roots[root].append(n)
    return {r: ns for r, ns in roots.items() if r not in translated}


class BoundRoots(unittest.TestCase):
    """Ruling 2026-10-17: "Roots that do not have their own translated entry are not to be included. We don't
    know if they are bound roots or not, and bound roots should not have entries in FormosanBank corpora."
    A root has its own translated entry when it is a defined form (alone, after '=' or as a derived form)
    of some entry whose text after the colon has Chinese."""

    def test_source_counts(self) -> None:
        excluded = roots_without_own_entry()
        self.assertEqual(len(excluded), 2231, "pinned source: 2,231 roots lack their own translated entry (corrected 2026-10-17; the first count, 3,174, misread \"X - {S} = Y\" heads and ignored glossed words after the colon; 2,232 -> 2,231 when \"dadinas (=lilit)：女子待頭飾\" was read as an '=' list, giving lilit a translation; 2,231 -> 2,233 when the ruled dashes were restored (2026-10-17, cards r5-separators-*), making caa' and htof roots; 2,233 -> 2,232 when \"mayo - J\" was read as \"mayo - {J}\" (card r6-structure-10236), giving mayo its own entry; 2,232 -> 2,231 when the first form of a translated word pair counted as a head word (card r2-m5-sodiget), giving sodiget its own entry)")

    def test_roots_without_their_own_entry_never_get_an_entry(self) -> None:
        excluded = roots_without_own_entry()
        bad = [
            f"{r.label} {r.id}: {f!r}"
            for r in records()
            for f in [r.form, *r.alt_forms]
            if _norm_form(f) in excluded
        ]
        self.assertEqual(bad[:20], [], f"{len(bad)} entries for roots that have no translated entry of their own")

    def test_roots_with_their_own_entry_keep_it(self) -> None:
        # positive control: cakay (own entry line 1240 'cakay：買，購'; root of line 1241 'cakay - micakay：購買')
        forms_1240 = {_norm_form(r.form) for r in by_line("headwords").get(1240, [])}
        self.assertIn("cakay", forms_1240)
        forms_1241 = {_norm_form(r.form) for r in by_line("headwords").get(1241, [])}
        self.assertEqual(forms_1241, {"micakay"}, "the root is not repeated as an entry in the derived line")

    def test_known_excluded_root_acak(self) -> None:
        # acak-maacak{Z}：乾旱的;口乾 -> maacak (Sakizaya file) only, never acak
        line = next(n for n, l in source_lines().items() if l.startswith("acak-maacak"))
        forms = {_norm_form(r.form) for r in by_line("headwords").get(line, [])}
        self.assertEqual(forms, {"maacak"})


class FrenchSeparate(unittest.TestCase):
    """The French records ruled 'separate' are their own S: French Amis as printed, French translation, no Chinese."""

    def test_placement_and_content(self) -> None:
        french = {sid: (form, trs) for sid, form, trs in FrenchCarriedOver().french_pages_1_to_4()}
        found: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for r in records():
            if r.french_id:
                found[r.french_id].add((r.kind, r.label))
                form, trs = french[r.french_id]
                self.assertEqual(r.form, form, r.id)
                self.assertEqual(r.zho, [], r.id)
                self.assertEqual(sorted(r.fra), sorted(trs), r.id)
                self.assertRegex(r.form_notes, r"French volume p\.\d{3}", r.id)
        expected = {sid: {(kind, lab) for lab in labels} for sid, (kind, labels) in FRENCH_SEPARATE.items()}
        self.assertEqual(dict(found), expected)


class FormsOptionC(unittest.TestCase):
    """Ruled (round 4, option C): one S per defined form; the root is not an entry but is named in notes
    ("May an excluded root still be named in the notes of its derived word" -> "yes")."""

    def line_starting(self, prefix: str) -> int:
        return next(n for n, l in source_lines().items() if l.startswith(prefix))

    def forms_on(self, line: int, label: str | None = None) -> dict[str, Record]:
        """Every form on the line, main or ver="alt" (alt forms: ruled 2026-10-17, card r6-altrule-0)."""
        return {f: r for r in by_line("headwords").get(line, []) if label in (None, r.label) for f in [r.form, *r.alt_forms]}

    def test_derived_and_equivalent_each_get_an_entry(self) -> None:
        n = self.line_starting("posot - miposot = porot")
        got = self.forms_on(n)
        self.assertEqual(set(got), {"miposot", "porot"})
        for r in got.values():
            self.assertIn("截斷", " ".join(r.zho))
        self.assertIn("root: posot", got["miposot"].form_notes)

    def test_several_derived_forms(self) -> None:
        n = self.line_starting("ga'ay - misaga'ay, masaga'ay, pasaga'ay")
        got = self.forms_on(n)
        self.assertEqual(set(got), {"misaga'ay", "masaga'ay", "pasaga'ay"})
        for r in got.values():
            self.assertIn("root: ga'ay", r.form_notes)
        # ruled 2026-10-17 (card r6-altrule-0): forms 1-2 characters apart with the same translations, same file -> one S
        self.assertEqual(len({id(r) for r in got.values()}), 1)

    def test_equivalents_listed_after_the_gloss(self) -> None:
        # 1949 ciyak - {N}：西瓜：cak, lidaw, kacawas, sinar；南瓜{S}  (French p.35: "pastèque: cak, lidaw, kacawas, sinar")
        # Ruled 2026-10-17 ("I think we assume it is inherited"): words written after the colon with no marker of
        # their own take the head word's dialect, so cak, lidaw, kacawas, sinar go with ciyak {N}.
        self.assertLessEqual({"ciyak", "cak", "lidaw", "kacawas", "sinar"}, set(self.forms_on(1949, "N")))
        self.assertNotIn("unmarked", {r.label for r in by_line("headwords").get(1949, [])})
        self.assertEqual(set(self.forms_on(1949, "S")), {"ciyak"})

    def test_excluded_root_named_in_notes(self) -> None:
        n = self.line_starting("acak-maacak")
        got = self.forms_on(n)
        self.assertEqual(set(got), {"maacak"})
        self.assertIn("root: acak", got["maacak"].form_notes)


def _alpha_key(line: str) -> str:
    word = re.split(r"[\s：=\-{(<]", line.strip(), 1)[0]
    return re.sub(r"[^a-z]", "", word.lower())


def _ends_in_untranslated_example(line: str) -> bool:
    segs = re.split(r"\s-\s|\s=\s|＝", after_colon(line))
    last = segs[-1].strip() if segs else ""
    return len(segs) > 1 and bool(re.search("[a-z]", last)) and not CJK.search(last) and "：" not in last


def suspected_wrap_lines() -> list[int]:
    """Lines that look like the second half of a printed line wrap: the entry before ends in an Amis example
    with no translation, and this line's head word breaks alphabetical order (e.g. 49 a'acfel：煙柱)."""
    lines = source_lines()
    ns = sorted(lines)
    out = []
    for prev, cur, nxt in zip(ns, ns[1:], ns[2:]):
        a, b, c = _alpha_key(lines[prev]), _alpha_key(lines[cur]), _alpha_key(lines[nxt])
        if _ends_in_untranslated_example(lines[prev]) and a and b and c and not (a <= b <= c) and a <= c:
            out.append(cur)
    return out


class WrappedLines(unittest.TestCase):
    """A printed line wrap starting with Amis words became a fake entry in pourrias-poinsot.txt (wildjcrt's
    joining rule only joined lines starting with Chinese or a quote). Found by the maintainer via S002_0022."""

    def test_acfel_smoke_column_is_rejoined(self) -> None:
        # scan p.6 l.26-27: "… = masatrocay" / "a 'acfel : 煙柱."  -> one example; no entry "a'acfel"
        self.assertEqual([r.id for r in records() if _norm_form(r.form) in {"a'acfel", "aacfel"}], [])
        ex = [r for r in by_line("examples").get(48, []) if "masatrocay" in r.form]
        self.assertTrue(ex, "line 48 example missing")
        self.assertIn("a 'acfel", ex[0].form.replace("’", "'"))
        self.assertIn("煙柱", " ".join(ex[0].zho))
        self.assertIn("colonne de fumée", " ".join(ex[0].fra))  # French S002_0022, ruled combine

    def test_every_suspected_wrap_is_resolved(self) -> None:
        """Each suspected wrap is either joined to the line before or recorded as checked and not a wrap."""
        path = DATA / "line_wraps.tsv"   # columns: line, decision (joined|not-a-wrap), evidence
        decided = {}
        if path.exists():
            for row in path.read_text(encoding="utf-8").splitlines()[1:]:
                n, decision, evidence = row.split("\t", 2)
                self.assertIn(decision, {"joined", "not-a-wrap"})
                self.assertTrue(evidence.strip(), f"line {n}: no evidence recorded")
                decided[int(n)] = decision
        suspects = suspected_wrap_lines()
        self.assertEqual(len(suspects), 36, "pinned source: 36 strongly suspected wraps")
        self.assertEqual([n for n in suspects if n not in decided][:20], [], "suspected wraps without a decision")
        heads = by_line("headwords")
        joined_but_entry = [n for n, d in decided.items() if d == "joined" and n in heads]
        self.assertEqual(joined_but_entry, [], "a joined continuation still produced its own entry")


class GlossesWithoutChinese(unittest.TestCase):
    """Ruled 2026-10-17 on the review cards: "The scientific name is a translation. Mark language as latin for the
    TRANSL. Note can say it's a scientific name." German glosses: TRANSL xml:lang="deu"; "The (?) should result in the
    note saying translation is uncertain." Lines: pourrias-poinsot.txt@365cfce."""

    LATIN = {5185: "Stellaria aquatica", 5187: "Nasturtium sunlyratum", 5371: "Denathe stronifera",
             6842: "Biden bipinnata", 9485: "Erythrina variegata", 9647: "Solanum nigrum",
             15738: "Carnavalia microcarpea", 16511: "Abelmoschus moschatus"}
    GERMAN = {3099: "beim jagen erfolgos bleibleu", 5482: "feld des bosen traumes"}

    def transls(self, line: int) -> list[tuple[str, str, str]]:
        out = []
        for (label, kind), (root, _) in load_all().items():
            for s in root.iter("S"):
                m = ID_LINE.search(s.get("id"))
                if m and int(m.group(1)) == line:
                    out += [(t.get(XML_LANG), t.text or "", t.get("notes") or "") for t in s.findall("TRANSL")]
        return out

    def test_scientific_names_are_latin_translations(self) -> None:
        for line, name in self.LATIN.items():
            with self.subTest(line=line):
                got = self.transls(line)
                self.assertIn(name, [t for lang, t, _ in got if lang == "lat"])
                self.assertTrue(all("scientific name" in n for lang, _, n in got if lang == "lat"))
                self.assertFalse(any("?" in t or "？" in t for _, t, _ in got))
        self.assertIn("translation uncertain", " ".join(n for _, _, n in self.transls(6842)))

    def test_german_glosses(self) -> None:
        for line, text in self.GERMAN.items():
            with self.subTest(line=line):
                got = self.transls(line)
                self.assertIn(text, [t for lang, t, _ in got if lang == "deu"])
                self.assertFalse(any("?" in t or "？" in t for _, t, _ in got))
        self.assertIn("translation uncertain", " ".join(n for _, _, n in self.transls(3099)))


def latin_runs() -> dict[str, str]:
    """data/latin_runs.tsv: every Latin-letter text found where a translation belongs -> its class."""
    rows = (DATA / "latin_runs.tsv").read_text(encoding="utf-8").splitlines()[1:]
    return {r.split("\t")[1]: r.split("\t")[2] for r in rows if r.strip()}


KEEP_IN_CHINESE = re.compile("|".join(re.escape(x) for x, c in latin_runs().items() if c == "keep"))


class ForeignNamesAndUncertainty(unittest.TestCase):
    """Ruled 2026-10-17: "1. Yes, latin ruling applies to those [scientific names beside Chinese glosses]. 2. Yes
    [English names -> TRANSL eng]. 3. I either said or meant to say that runs needed to be looked at. Those two are
    examples that should stay [’Na Taolan’, mama no kapah stay in the Chinese]. 4. Yes [a printed (?) -> note
    "translation uncertain", for all entries]." Which class each text belongs to is listed in latin_runs.tsv."""

    def test_every_class_is_known(self) -> None:
        self.assertEqual(set(latin_runs().values()) - {"scientific", "english", "french", "keep", "amis", "review",
                                                       "amis-in-chinese", "german", "note", "drop"}, set())
        self.assertEqual(sorted(x for x, c in latin_runs().items() if c == "keep"), ["mama no kapah", "’Na Taolan’"])

    def test_listed_names_are_never_amis_forms(self) -> None:
        names = [x for x, c in latin_runs().items() if c in ("scientific", "english", "french", "review", "note", "drop")]
        pat = re.compile(r"(?<![A-Za-z'’])(?:" + "|".join(re.escape(x) for x in names) + r")(?![A-Za-z'’])")
        problems = [f"{r.id}: {r.form!r}" for r in records() if pat.search(r.form)]
        self.maxDiff = None
        self.assertEqual(problems[:60], [], f"{len(problems)} Amis forms hold a listed Latin/English/other name")

    def test_scientific_and_english_names_are_translations(self) -> None:
        lines = source_lines()
        have: dict[int, set[tuple[str, str]]] = defaultdict(set)
        for (label, kind), (root, _) in load_all().items():
            for s in root.iter("S"):
                m = ID_LINE.search(s.get("id"))
                for tr in s.findall("TRANSL"):
                    if m and tr.get(XML_LANG) in ("lat", "eng") or (m and tr.get(XML_LANG) == "fra" and tr.get("notes") == "French name"):
                        have[int(m.group(1))].add((tr.get(XML_LANG), tr.text or ""))
                        want_note = {"lat": "scientific name", "eng": "English name", "fra": "French name"}[tr.get(XML_LANG)]
                        self.assertTrue((tr.get("notes") or "").startswith(want_note))
        problems = []
        for name, cls in latin_runs().items():
            if cls not in ("scientific", "english", "french"):
                continue
            lang = {"scientific": "lat", "english": "eng", "french": "fra"}[cls]
            for n, line in lines.items():
                if re.search(r"(?<![A-Za-z'’])" + re.escape(name) + r"(?![A-Za-z'’])", line):
                    if (lang, name) not in have.get(owner(n), set()):
                        problems.append(f"line {n}: {name!r} is not a TRANSL {lang}")
        self.maxDiff = None
        self.assertEqual(problems[:60], [], f"{len(problems)} listed names are not translations")

    def test_kept_runs_stay_in_the_chinese(self) -> None:
        zh = " ".join(z for r in records() for z in r.zho)
        self.assertGreaterEqual(zh.count("mama no kapah"), 2)   # lines 6986 and 11887
        self.assertIn("田埔村’Na Taolan’的名字", zh)

    def test_runs_left_in_notes_are_listed_for_review(self) -> None:
        """Every Latin-letter run still parked in a "source text:" note is one that awaits a decision card."""
        listed = {x for x, c in latin_runs().items() if c in ("review", "amis-in-chinese", "note")}
        problems = []
        for (label, kind), (root, _) in load_all().items():
            for s in root.iter("S"):
                for el in s:
                    for note in (el.get("notes") or "").split("; "):
                        if note.startswith("source text: ") and note[13:] not in listed:
                            problems.append(f"{s.get('id')}: {note[13:]!r}")
        self.assertEqual(problems[:20], [], f"{len(problems)} runs not classified in latin_runs.tsv")

    def test_printed_question_mark_becomes_a_note(self) -> None:
        q = re.compile(r"[(（]\s*[?？]\s*[)）]")
        lines = source_lines()
        notes: dict[int, str] = defaultdict(str)
        for (label, kind), (root, _) in load_all().items():
            for s in root.iter("S"):
                m = ID_LINE.search(s.get("id"))
                for el in s:
                    if m:
                        notes[int(m.group(1))] += " " + (el.get("notes") or "")
                        if el.tag == "TRANSL":
                            self.assertIsNone(q.search(el.text or ""), s.get("id"))
        problems = [f"line {n}" for n, line in lines.items() if q.search(line) and owner(n) not in card_ruled_lines()
                    and owner(n) not in excluded_lines() and "translation uncertain" not in notes.get(owner(n), "")]
        # card-ruled instead: 4309 "form uncertain", 2695 "Japanese borrowing (uncertain)", 9592 "Arabic borrowing (uncertain)"
        self.assertEqual(problems, [], f"{len(problems)} entries with a printed (?) lack the note")

    def test_no_internal_placeholders(self) -> None:
        bad = [r.id for r in records() if "§" in r.notes or any("§" in z for z in r.zho + r.other)]
        self.assertEqual(bad[:20], [], f"{len(bad)} records still carry a § placeholder")


class SafoluLessons(unittest.TestCase):
    """Rules first made for Safolu, adopted here by the maintainer on 2026-10-17 (round 3, "Add all three")."""

    BIBLE_REF = re.compile(r"[(（][\u3400-\u9fff]{1,3}\s*\d+\s*[,，]\s*\d+")

    def test_question_and_exclamation_spacing(self) -> None:
        """No space before ? or !, and a space between ?/! and a following letter (Safolu ruling)."""
        bad = [f"{r.id}: {r.form!r}" for r in records() if re.search(r"\s[?!？！]|[?!？！][A-Za-z'’]", r.form)]
        self.assertEqual(bad[:20], [], f"{len(bad)} forms with ?/! spacing errors")

    def test_cross_references_not_in_translations(self) -> None:
        """(見 sarocod) / (見 taog) move from the translation to notes."""
        bad = [f"{r.id}: {t!r}" for r in records() for t in r.zho if re.search(r"見\s*[A-Za-z'’]", t)]
        self.assertEqual(bad[:20], [], f"{len(bad)} translations still hold a cross-reference")

    def test_bible_references_not_in_amis_text(self) -> None:
        """(可 5,25) leaves the Amis sentence and is kept in notes."""
        bad = [f"{r.id}: {r.form!r}" for r in records() if self.BIBLE_REF.search(r.form)]
        self.assertEqual(bad[:20], [], f"{len(bad)} forms still hold a Bible reference")
        lines = source_lines()
        notes_by_line: dict[int, str] = defaultdict(str)
        for r in records():
            notes_by_line[r.line] += r.notes + " "
        lost = []
        for n, line in lines.items():
            for m in self.BIBLE_REF.finditer(line):
                ref = re.sub(r"\s", "", m.group(0)[1:])
                if ref not in re.sub(r"\s", "", notes_by_line.get(owner(n), "")):
                    lost.append(f"line {n}: {m.group(0)}")
        self.assertEqual(lost[:20], [], f"{len(lost)} Bible references not kept in notes")


class FrenchCarriedOver(unittest.TestCase):
    """Maintainer, round 3: "Please confirm that the French translations from those 4 pages are getting
    incorporated into the new XMLs." Every French translation from pages 1-4, as the existing French
    builder reads them, must appear on some S in the new files."""

    def french_pages_1_to_4(self) -> list[tuple[str, str, list[str]]]:
        # the old French build's pages 1-4 (dev repo commit 30140ba), frozen by snapshot_french_reference.py
        data = json.loads((DATA / "french_reference_pages_1_4.json").read_text(encoding="utf-8"))
        return [(r["id"], r["form"], r["transl"]) for r in data["records"]]

    def test_every_french_translation_from_pages_1_to_4_is_present(self) -> None:
        french = self.french_pages_1_to_4()
        self.assertEqual(len(french), 189 + 36, "French pages 1-4 hold 189 entries and 36 examples")
        have = " | ".join(t for r in records() for t in r.fra)
        missing = [f"{sid} {form!r}: {tr!r}" for sid, form, trs in french for tr in trs if tr and tr not in have]
        self.assertEqual(missing[:20], [], f"{len(missing)} French translations from pages 1-4 not carried over")

    def test_adidiw_has_its_own_restored_entry(self) -> None:
        # The maintainer read the scan (card r5-adidiw-118): "adidiw - {N} = tandaca - sans force - 弱". p.8 l.30 prints
        # "adidiw – {N} = tadanca : 弱." but the 2020 DB marked it blank; restored (restored_lines.tsv), and the French
        # S003_0109 "sans force" attaches to it, not to line 118.
        alts = [a for r in by_line("headwords").get(118, []) for a in r.alt_forms]
        self.assertNotIn("adidiw", alts)
        got = {(r.label, r.form): (r.zho, r.fra) for r in records("headwords") if r.line == 119 and r.part == 90}
        self.assertEqual(got, {("N", "adidiw"): (["弱"], ["sans force"]), ("unmarked", "tadanca"): (["弱"], ["sans force"])})


class Reproducible(unittest.TestCase):
    def test_two_builds_are_identical(self) -> None:
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            for out in (a, b):
                subprocess.run([sys.executable, str(BUILD_SCRIPT), "--xml-out-dir", out], check=True, cwd=REPO)
            fa = sorted(p.relative_to(a) for p in Path(a).rglob("*.xml"))
            fb = sorted(p.relative_to(b) for p in Path(b).rglob("*.xml"))
            self.assertEqual(fa, fb)
            for rel in fa:
                self.assertEqual((Path(a) / rel).read_bytes(), (Path(b) / rel).read_bytes(), str(rel))


if __name__ == "__main__":
    unittest.main()
