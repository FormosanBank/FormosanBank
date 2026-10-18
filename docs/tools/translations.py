"""Sentence-level translation of the documentation site.

Maintainer, 2026-10-18 (decision page LrT9Ktvda8YGLf2rqprFsC): collaborators
translate the site sentence by sentence, without Claude accounts; a translation
someone typed counts as approved unless they untick it; machine-translated or
earlier drafts start unapproved; "The translated part appears. The untranslated
part does not."; standard headings and table/figure labels are translated once;
corpus "Reproduction and processing" sections are not translated into Formosan
languages; every translation is kept as data (old ones are not removed).

Pieces:

* ``parse_blocks`` / ``segments`` split a page into translatable units
  (headings, sentences, list items, table cells), each keyed by its English
  text, so an edited sentence becomes a new unit and its old translation stays
  in the store as data.
* The store: ``docs/translations/<code>.tsv``, one row per translation
  (english, translation, approved, origin, translator, dialect, date). The
  shared labels (headings, table and figure labels, language and dialect
  names) are listed by site_labels.py and translated in the same stores.
* ``render_translated_page`` rebuilds a page from approved units only.
* ``merge_import`` folds a translator's saved work into a store.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRANSLATIONS_DIR = REPO_ROOT / "docs" / "translations"
STORE_FIELDS = ("english", "translation", "approved", "origin", "translator", "dialect", "date")
ORIGINS = ("human", "mt", "previous-website", "corpus-match")
PAYLOAD_FORMAT = "formosanbank-translation/1"


@dataclass(frozen=True)
class TargetLanguage:
    code: str  # ISO 639-3, the store's file name
    edition: str  # prepare_site edition key
    name: str
    formosan: bool  # Formosan editions skip corpus "Reproduction and processing"


TARGETS = (
    TargetLanguage("zho", "zh", "Mandarin", False),
    TargetLanguage("pwn", "paiwan", "Paiwan", True),
    TargetLanguage("ami", "amis", "Amis", True),
    TargetLanguage("bnn", "bunun", "Bunun", True),
)
TARGETS_BY_CODE = {t.code: t for t in TARGETS}
TARGETS_BY_EDITION = {t.edition: t for t in TARGETS}

REPRODUCTION_HEADING = "Reproduction and processing"


# --------------------------------------------------------------------------
# Splitting a page into units
# --------------------------------------------------------------------------

FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.S)
FENCE_OPEN = re.compile(r"^(\s*)(`{3,}|~{3,})")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
LIST_ITEM = re.compile(r"^(\s*)(?:[*+-]|\d+[.)])\s+(.*)$")
TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
TABLE_SEPARATOR = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")
ADMONITION = re.compile(r'^!!!\s+\w+(?:\s+"([^"]*)")?\s*$')
GITBOOK_DIRECTIVE = re.compile(r"^\s*{%.*%}\s*$")
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
HTML_TAG = re.compile(r"<[^>]+>")
EMPHASIS = re.compile(r"(\*\*|\*)(?=\S)(.+?)(?<=\S)\1")
ABBREVIATIONS = re.compile(
    r"\b(?:e\.g|i\.e|cf|vs|etc|et al|pp|p|no|vol|ed|eds|ca|fig|Dr|Mr|Ms|Prof|St|[A-Z])\.(?=\s)"
)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[\"“'(\[`*A-Z0-9])")


INLINE_CODE = re.compile(r"`[^`\n]+`")


def plain_text(markdown: str) -> str:
    """Inline Markdown flattened to what a reader sees; inline code is kept as written.

    Code spans are masked first, so `<UNCLEAR/>` or `*` inside backticks is
    not mistaken for an HTML tag or emphasis.
    """
    saved: list[str] = []

    def mask(match: re.Match[str]) -> str:
        saved.append(match.group(0))
        return f"\x00{len(saved) - 1}\x00"

    text = INLINE_CODE.sub(mask, markdown)
    text = IMAGE.sub("", text)
    text = LINK.sub(lambda m: m.group(1), text)
    text = HTML_TAG.sub("", text)
    text = EMPHASIS.sub(lambda m: m.group(2), text)
    text = text.replace("&nbsp;", " ").replace("\\#", "#")
    text = re.sub("\x00(\\d+)\x00", lambda m: saved[int(m.group(1))], text)
    return " ".join(text.split())


def split_sentences(text: str) -> list[str]:
    protected = ABBREVIATIONS.sub(lambda m: m.group(0)[:-1] + "\x01", text)
    return [s.replace("\x01", ".").strip() for s in SENTENCE_END.split(protected) if s.strip()]


def translatable(text: str) -> bool:
    """A unit worth translating: has letters, and is not only code or a number."""
    stripped = re.sub(r"`[^`]*`", "", text)
    return any(ch.isalpha() for ch in stripped)


def key_of(text: str) -> str:
    return " ".join(text.split())


@dataclass
class Block:
    kind: str  # heading, paragraph, list, table, code, admonition
    level: int = 0  # heading level / list indent
    units: list[str] = field(default_factory=list)  # paragraph sentences, list items, heading
    rows: list[list[str]] = field(default_factory=list)  # table cells (plain text)
    raw: str = ""  # code
    title: str = ""  # admonition title
    section: str = ""  # nearest level-2 heading above


def parse_blocks(markdown: str) -> list[Block]:
    text = HTML_COMMENT.sub("", FRONT_MATTER.sub("", markdown))
    lines = text.split("\n")
    blocks: list[Block] = []
    section = ""
    paragraph: list[str] = []
    i = 0

    def flush():
        if paragraph:
            sentences = [s for s in split_sentences(plain_text(" ".join(paragraph))) if translatable(s)]
            if sentences:
                blocks.append(Block("paragraph", units=sentences, section=section))
            paragraph.clear()

    while i < len(lines):
        line = lines[i]
        fence = FENCE_OPEN.match(line)
        if fence:
            flush()
            marker = fence.group(2)
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith(marker):
                j += 1
            blocks.append(Block("code", raw="\n".join(lines[i:j + 1]), section=section))
            i = j + 1
            continue
        if not line.strip() or GITBOOK_DIRECTIVE.match(line):
            flush()
            i += 1
            continue
        heading = HEADING.match(line)
        if heading:
            flush()
            level = len(heading.group(1))
            title = plain_text(heading.group(2))
            if level == 2:
                section = title
            if translatable(title):
                blocks.append(Block("heading", level=level, units=[title], section=section))
            i += 1
            continue
        if TABLE_ROW.match(line):
            flush()
            rows = []
            while i < len(lines) and TABLE_ROW.match(lines[i]):
                if not TABLE_SEPARATOR.match(lines[i]):
                    cells = [plain_text(c) for c in lines[i].strip().strip("|").split("|")]
                    rows.append(cells)
                i += 1
            blocks.append(Block("table", rows=rows, section=section))
            continue
        admonition = ADMONITION.match(line)
        if admonition:
            flush()
            j = i + 1
            body = []
            while j < len(lines) and (lines[j].startswith("    ") or not lines[j].strip()):
                if lines[j].strip():
                    body.append(lines[j].strip())
                elif body and j + 1 < len(lines) and not lines[j + 1].startswith("    "):
                    break
                j += 1
            sentences = [s for s in split_sentences(plain_text(" ".join(body))) if translatable(s)]
            blocks.append(Block("admonition", title=plain_text(admonition.group(1) or ""),
                                units=sentences, section=section))
            i = j
            continue
        item = LIST_ITEM.match(line)
        if item:
            flush()
            items: list[tuple[int, str]] = []
            while i < len(lines):
                m = LIST_ITEM.match(lines[i])
                if m:
                    items.append((len(m.group(1)), m.group(2)))
                elif lines[i].strip() and lines[i].startswith(" ") and items and not FENCE_OPEN.match(lines[i]):
                    indent, prev = items[-1]
                    items[-1] = (indent, prev + " " + lines[i].strip())
                else:
                    break
                i += 1
            for indent, body in items:
                units = [s for s in split_sentences(plain_text(body)) if translatable(s)]
                if units:
                    blocks.append(Block("list", level=indent, units=units, section=section))
            continue
        paragraph.append(line.strip())
        i += 1
    flush()
    return blocks


def block_units(block: Block) -> list[str]:
    if block.kind == "table":
        return [cell for row in block.rows for cell in row if translatable(cell)]
    units = list(block.units)
    if block.kind == "admonition" and block.title and translatable(block.title):
        units.insert(0, block.title)
    return units


def segments(markdown: str, *, skip_reproduction: bool = False, exclude: set[str] | None = None) -> list[str]:
    """The page's translatable units, in order, without repeats."""
    exclude = exclude or set()
    seen: set[str] = set()
    out: list[str] = []
    for block in parse_blocks(markdown):
        if skip_reproduction and block.section == REPRODUCTION_HEADING:
            continue
        for unit in block_units(block):
            key = key_of(unit)
            if key not in seen and key not in exclude:
                seen.add(key)
                out.append(key)
    return out


# --------------------------------------------------------------------------
# The store
# --------------------------------------------------------------------------


def store_path(code: str, directory: Path = TRANSLATIONS_DIR) -> Path:
    return directory / f"{code}.tsv"


def load_store(code: str, directory: Path = TRANSLATIONS_DIR) -> list[dict]:
    path = store_path(code, directory)
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def save_store(code: str, rows: list[dict], directory: Path = TRANSLATIONS_DIR) -> None:
    path = store_path(code, directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["english"], r["date"], r["translator"], r["translation"]))
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=STORE_FIELDS, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({f: _clean(row.get(f, "")) for f in STORE_FIELDS})


def _clean(value: str) -> str:
    return " ".join(str(value).replace("\t", " ").split())


def approved_map(rows: list[dict]) -> dict[str, str]:
    """English -> the newest approved translation."""
    best: dict[str, tuple[str, str]] = {}
    for row in rows:
        if row["approved"] != "yes" or not row["translation"].strip():
            continue
        current = best.get(row["english"])
        if current is None or row["date"] >= current[0]:
            best[row["english"]] = (row["date"], row["translation"])
    return {english: translation for english, (_date, translation) in best.items()}


# --------------------------------------------------------------------------
# Importing a translator's saved work
# --------------------------------------------------------------------------


@dataclass
class ImportReport:
    new: list[dict] = field(default_factory=list)
    unchanged: int = 0
    unknown: list[str] = field(default_factory=list)  # English not in the current inventory
    blocked: list[str] = field(default_factory=list)  # cross-dialect approved clashes
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.blocked


def parse_payload(text: str) -> dict:
    payload = json.loads(text)
    if payload.get("format") != PAYLOAD_FORMAT:
        raise ValueError(f"not a FormosanBank translation file (format {payload.get('format')!r})")
    for key in ("language", "translator", "items"):
        if key not in payload:
            raise ValueError(f"translation file has no {key!r}")
    if payload["language"] not in TARGETS_BY_CODE:
        raise ValueError(f"unknown language {payload['language']!r}")
    return payload


def merge_import(
    store: list[dict], payload: dict, inventory_keys: set[str], *, today: str | None = None
) -> tuple[list[dict], ImportReport]:
    """Add a translator's items to ``store``; returns (new store, report).

    Nothing is overwritten: every changed translation is a new row. An item
    whose English is no longer in the site's inventory is still kept (it is
    data) and listed. A newly approved translation for a sentence that already
    has an approved translation in a *different dialect* blocks the import
    (maintainer, S2: "We will worry about that if it ever happens!"), so a
    person decides.
    """
    today = today or dt.date.today().isoformat()
    report = ImportReport()
    translator = _clean(payload.get("translator", ""))
    dialect = _clean(payload.get("dialect", ""))
    if not translator:
        report.errors.append("the file does not name its translator")
        return store, report
    existing: dict[tuple[str, str], dict] = {}
    approved_dialects: dict[str, set[str]] = {}
    for row in store:
        existing[(row["english"], row["translation"])] = row
        if row["approved"] == "yes":
            approved_dialects.setdefault(row["english"], set()).add(row["dialect"])
    added: list[dict] = []
    for item in payload["items"]:
        english = key_of(item.get("english", ""))
        translation = _clean(item.get("translation", ""))
        if not english or not translation:
            continue
        approved = "yes" if item.get("approved", True) else "no"
        if english not in inventory_keys:
            report.unknown.append(english)
        previous = existing.get((english, translation))
        if previous and previous["approved"] == approved and previous["dialect"] == dialect:
            report.unchanged += 1
            continue
        others = approved_dialects.get(english, set()) - {dialect}
        if approved == "yes" and others and TARGETS_BY_CODE[payload["language"]].formosan:
            report.blocked.append(f"{english!r}: approved in dialect {sorted(others)}, now also in {dialect!r}")
            continue
        origin = item.get("origin") if item.get("origin") in ORIGINS else "human"
        if previous and previous["translation"] == translation:
            origin = previous["origin"]  # approving prior work keeps its origin
        added.append({
            "english": english, "translation": translation, "approved": approved,
            "origin": origin, "translator": translator, "dialect": dialect, "date": today,
        })
    report.new = added
    if not report.ok:
        return store, report
    return store + added, report


# --------------------------------------------------------------------------
# Rebuilding a page from approved units
# --------------------------------------------------------------------------


def render_translated_page(
    markdown: str,
    approved: dict[str, str],
    *,
    skip_reproduction: bool,
    english_url: str,
    english_title: str,
) -> str | None:
    """The page with only its approved units, or None if its title isn't approved.

    Untranslated units are left out (maintainer: "The translated part appears.
    The untranslated part does not."). Code blocks are kept as written. A table
    keeps the rows whose every text cell is translated, and only if its header
    row is. The page opens with a link to the complete English page.
    """
    blocks = parse_blocks(markdown)
    out: list[str] = []
    title_done = False
    for block in blocks:
        if skip_reproduction and block.section == REPRODUCTION_HEADING:
            continue
        if block.kind == "heading":
            text = approved.get(key_of(block.units[0]))
            if block.level == 1 and not title_done:
                if text is None:
                    return None
                out += [f"# {text}", "", f"[{english_title}]({english_url})", ""]
                title_done = True
            elif text is not None:
                out += [f"{'#' * block.level} {text}", ""]
        elif block.kind == "paragraph":
            texts = [approved[key_of(u)] for u in block.units if key_of(u) in approved]
            if texts:
                out += [" ".join(texts), ""]
        elif block.kind == "list":
            texts = [approved[key_of(u)] for u in block.units if key_of(u) in approved]
            if texts:
                out += [f"{' ' * block.level}- {' '.join(texts)}", ""]
        elif block.kind == "admonition":
            texts = [approved[key_of(u)] for u in block.units if key_of(u) in approved]
            title = approved.get(key_of(block.title)) if block.title else None
            if texts:
                header = f'!!! note "{title}"' if title else "!!! note"
                out += [header, f"    {' '.join(texts)}", ""]
        elif block.kind == "table":
            def row_text(row):
                cells = []
                for cell in row:
                    if not translatable(cell):
                        cells.append(cell)
                    elif key_of(cell) in approved:
                        cells.append(approved[key_of(cell)])
                    else:
                        return None
                return cells
            if not block.rows:
                continue
            header = row_text(block.rows[0])
            body = [r for r in (row_text(row) for row in block.rows[1:]) if r is not None]
            if header is not None and body:
                out.append("| " + " | ".join(header) + " |")
                out.append("|" + "---|" * len(header))
                out += ["| " + " | ".join(r) + " |" for r in body]
                out.append("")
        elif block.kind == "code":
            out += [block.raw, ""]
    if not title_done:
        return None
    return "\n".join(out).rstrip() + "\n"
