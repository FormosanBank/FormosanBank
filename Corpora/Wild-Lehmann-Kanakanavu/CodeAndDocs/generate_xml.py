#!/usr/bin/env python3
"""generate_xml.py -- kanakanavu.info interlinear pages -> original-tier XML.

Step 1 of generate_xml.sh (POL-047). Reads only the committed scrape under
--source (the HTML bytes as served) and corpus_metadata.json beside this
script; writes one XML file per text page under <out>/<language_dir>/ and the
rejected-unit list.

Each page under html/language-documentation/ (except its index) is one TEXT.
Each inner table on a page is one source unit; its `rf` row is the unit's id.
Row labels are the site's own (defined at the top of every page):

  rf    -> S/@id  = <TEXT id>_<rf with apostrophes removed>
  NR    -> S  FORM kindOf="original"   (the NR cells joined by one space)
           and one W per NR cell, FORM = the cell
  GE    -> W  TRANSL kindOf="original" (the GE cell in the same column;
                                         every page has as many GE cells as NR)
  FTE   -> S  TRANSL xml:lang="eng"
  FTC   -> S  TRANSL xml:lang="zho"
  OFTE  -> S  TRANSL xml:lang="eng" ver="alt" notes=...  (Tsuchida 2003's own
                                         translation; POL-025)
  PT    -> not emitted here. Maintainer, round 1: PT "is actually an exact
           transcription, rather than a clean sentence ... have a separate XML
           that has the audio and just PT. Everything else goes in NR."
  OT/OG -> not emitted (Tsuchida 2003's transcription and gloss lines)

The page's recording (one per page) -> TEXT/AUDIO file=..., i.e. untranscribed
audio (no sentence timings). Maintainer, round 2: "Audio will be handled as
untranscribed audio. The PT transcriptions go in separate files but not the
XML folder." A video's audio track is named with corpus_metadata.json's
video_audio_ext (the extracted audio, not the .mp4).

Corrections, in this order, before any W or M is built:
  1. CodeAndDocs/source_corrections.tsv -- one row per changed cell, with the
     exact text it expects, the operation, and the maintainer's ruling it
     rests on. A row whose expected text is not found stops the build.
     Operations: replace (sentence and word text), w_only (word text only;
     the sentence keeps the printed cell), variant (to = "base|alt": the word
     gets the base and a ver="alt" FORM, the sentence the base), repeat (the
     word is written twice, both with the cell's gloss), optional (POL-026:
     the sentence is emitted without the cell, and again as <id>-opt with it),
     single_m (the word gets one M even though its gloss is unknown; a ruled
     exception), add_after (to = "word=pt word=pt ...": words the source's NR
     line lacks, transcribed from its PT line, inserted after the cell, each
     glossed ? (POL-061) with the row's note, where {pt} is that word's PT form).
     Rows on the GE line replace the gloss. Rows on a translation line (FTE,
     FTC, OFTE) take op split (to = "main|alt[|alt...]": the main translation
     plus one marked ver="alt" per further reading, POL-025), replace (to =
     the new text), note (to = "text|note": the text, with the note in
     TRANSL/@notes, added after Tsuchida's note on OFTE) or drop (no
     translation on that line).
  2. In NR text, the IPA tap U+027E is written r. Maintainer, round 1: correct
     it in the original tier (the transcriber writes r for the same words
     elsewhere); "This should be noted in the docs."

M tier (POL-057): an M exists where NR segments the word (a hyphen or an
<infix>) AND the GE cell splits into the same pieces in the same places; a
segmented word whose gloss does not split the same way keeps its W and W
gloss and gets no M (counted in the build report). A word NR does not
segment gets one M (FORM = the word, gloss = the W gloss) when its gloss is
one piece: no hyphen, no <infix>, no bracketed capital label such as (AV),
and not unknown (empty, ?, ??, ???). Maintainer, round 3: "For unsegmented
words with a gloss that is a single morpheme, they get that gloss. The
remaining 57 remain open for now." A cell holding several words
(`makasuen ia`) gets no M. Infixes follow POL-014: the root is one M with `-` at the
infixation point, followed by the infix as `-um-`; the infix gloss keeps the
source's brackets (`<AV>`), as in ILCAA-Kanakanavu-Texts.

Glosses (POL-021/POL-061 as amended 2026-10-17): a GE cell that is empty,
`?`, `??` or `???` becomes <UNCLEAR/>; inside a hyphen-split gloss, a piece
that is exactly one of those becomes <UNCLEAR/>. Any other `?` is the
source's mark of uncertainty about a gloss it did give: it is removed from the
gloss and the TRANSL gets notes="uncertain" (`COND(?)` -> `COND`; `go?` -> `go`).
Where a `?` run sits between two letters it separated alternatives and becomes
`/` (`father?uncle?` -> `father/uncle`). Maintainer (2026-11-11): "They mark
uncertainty. Remove them from the gloss and put "uncertain" in the note for
that TRANSL." The `/` reading was confirmed: "Yes, go ahead and use the
slash format." One gloss is dropped (GLOSS_DROPPED): `go-?/certain (TB)??` on
`mua` (2014_Moo_02_55_W01) gets no TRANSL and no M. Maintainer (2026-11-11):
"I think the gloss should just be deleted for that W and there should be no
child Ms."

A free translation that is empty is not emitted.

Final punctuation (POL-063; maintainer, QC review page 2026-11-09, chose "Apply it
now, in generate_xml.py"). The NR
line has none, so each sentence ends in the mark its main English translation
ends in (. ? ! : , ;), or in . when that ends in none or there is no English.
An English translation with no final mark gets a period. A Chinese translation
ends in its script's mark: a final Latin . ? ! becomes 。 ？ ！, and one with no
final mark gets the full-width form of the sentence's mark. A translation that
ends in : , or ; because the text goes on (POL-063, partial utterances) keeps it,
and its sentence ends the same way. A closing quotation mark or bracket after a
final mark counts as ending in that mark.

A unit with no NR row is rejected (written to --rejected with the reason).
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup
from lxml import etree

HERE = Path(__file__).resolve().parent
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SITE = "https://kanakanavu.info/language-documentation/"
UNKNOWN_GLOSS = {"", "?", "??", "???"}
# Glosses not emitted at all (no TRANSL, no M); see the docstring.
GLOSS_DROPPED = {"go-?/certain (TB)??"}
INFIX = re.compile(r"<([^<>]*)>")
LABEL = re.compile(r"[<(][A-Z][A-Za-z0-9.:]*[>)]")   # a bracketed capital label in a gloss, e.g. (AV)


TAP = "\u027e"
TRANSL_LINES = {"FTE", "FTC", "OFTE"}

# POL-063 final punctuation (see the docstring).
LATIN_END = ".?!"
CHINESE_END = "\u3002\uff1f\uff01"
GOES_ON = ":,;"
TO_CHINESE = {".": "\u3002", "?": "\uff1f", "!": "\uff01", ":": "\uff1a", ",": "\uff0c", ";": "\uff1b"}
CLOSERS = "\"'\u201d\u2019)\u300d"


def final_mark(text: str) -> str:
    """The text's last character before any closing quotation marks or brackets."""
    return text.rstrip().rstrip(CLOSERS)[-1:]


def sentence_mark(english: str) -> str:
    m = final_mark(english) if english else ""
    return m if m and m in LATIN_END + GOES_ON else "."


def end_english(text: str) -> str:
    m = final_mark(text)
    return text if m and m in LATIN_END + GOES_ON else text.rstrip() + "."


def end_chinese(text: str, smark: str, sid: str) -> str:
    t = text.rstrip()
    core = t.rstrip(CLOSERS)
    m = core[-1:]
    if m and m in CHINESE_END + "\uff1a\uff0c\uff1b":
        return t
    if m and m in LATIN_END:
        i = len(core) - 1
        return t[:i] + TO_CHINESE[m] + t[i + 1:]
    if m and m in GOES_ON:
        raise SystemExit(f"{sid}: Chinese translation ends in the Latin {m!r}, which POL-063's rule here does not cover: {t!r}")
    return t + TO_CHINESE[smark]


def load_corrections(path: Path) -> dict:
    """(page, rf) -> list of correction rows (dicts), in file order."""
    out: dict = {}
    with path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            row["cell"] = int(row["cell"])
            out.setdefault((row["page"], row["rf"]), []).append(row)
    return out


def clean(s: str) -> str:
    """Cell text: non-breaking spaces to spaces, whitespace runs collapsed."""
    return re.sub(r"\s+", " ", s.replace("\xa0", " ")).strip()


# --------------------------------------------------------------------------
# Reading one page
# --------------------------------------------------------------------------

def read_page(path: Path) -> dict:
    soup = BeautifulSoup(path.read_bytes(), "lxml", from_encoding="iso-8859-1")
    title = clean(soup.title.get_text()).removesuffix(" | Kanakanavu")
    outer = soup.find("table", class_="out")
    if outer is None:
        raise SystemExit(f"{path}: no <table class='out'>")
    units = []
    for k, table in enumerate(outer.find_all("table")):
        rows = []
        for tr in table.find_all("tr", recursive=False):
            label = tr.find("td", class_="label")
            if label is None:
                continue
            cells = [clean(td.get_text()) for td in tr.find_all("td")
                     if "label" not in (td.get("class") or [])]
            rows.append((clean(label.get_text()), cells))
        units.append({"k": k, "rows": rows})
    # Prose outside the table: who recorded it, when, where, and the speaker.
    for t in soup.find_all("table", class_="out"):
        t.decompose()
    prose = clean(soup.get_text(" "))
    rec = re.search(r"(This (?:story|narration) was (?:originally )?recorded by [^.]+\.)", prose)
    spk = re.search(r"(The speaker is [^.]+\.)", prose)
    media = [el.get("href") or el.get("src") for el in soup.find_all(["a", "source", "embed", "param", "video", "audio"])
             if (el.get("href") or el.get("src") or "").lower().endswith((".mp3", ".mp4"))]
    media = sorted({m.rsplit("/", 1)[-1] for m in media})
    return {"title": title, "units": units, "recorded": rec.group(1) if rec else "",
            "speaker": spk.group(1) if spk else "", "media": media}


# --------------------------------------------------------------------------
# Morpheme splitting (only where NR and GE agree)
# --------------------------------------------------------------------------

def form_pieces(word: str):
    """NR word -> M FORMs; None if unsegmented; 'bad' if not splittable."""
    if "-" not in word and "<" not in word and ">" not in word:
        return None
    out = []
    for p in word.split("-"):
        m = INFIX.search(p)
        if m:
            if INFIX.search(p, m.end()) or not p[:m.start()] or not p[m.end():]:
                return "bad"
            out += [p[:m.start()] + "-" + p[m.end():], "-" + m.group(1) + "-"]
        elif "<" in p or ">" in p or p == "":
            return "bad"
        else:
            out.append(p)
    return out


def gloss_pieces(gloss: str):
    out = []
    for p in (x.strip() for x in gloss.split("-")):     # site writes e.g. "shoot -UV1"
        m = INFIX.search(p)
        if m:
            if INFIX.search(p, m.end()):
                return "bad"
            out += [(p[:m.start()] + p[m.end():]).strip(), "<" + m.group(1) + ">"]
        elif "<" in p or ">" in p or p == "":
            return "bad"
        else:
            out.append(p)
    return out


def aligned(fp, gp) -> bool:
    if fp in (None, "bad") or gp == "bad" or len(fp) != len(gp):
        return False
    return all((f.startswith("-") and f.endswith("-")) == g.startswith("<") for f, g in zip(fp, gp))


def strip_uncertain(piece: str) -> tuple[str, bool]:
    """Remove the source's uncertainty marks from a gloss (or gloss piece) it did give.

    -> (the gloss without them, whether any were removed). `(?)` and `?` are dropped;
    a `?` run between two letters separated alternatives (`father?uncle?`) and becomes
    `/`, the site's own separator for alternative glosses (`CONT/please?`).
    """
    if "?" not in piece or piece in UNKNOWN_GLOSS:
        return piece, False
    out = piece.replace("(?)", "")
    out = re.sub(r"(?<=[^\W\d_])\?+(?=[^\W\d_])", "/", out)
    return out.replace("?", "").strip(), True


def add_gloss(parent, text: str) -> None:
    """W/M gloss with the POL-061 <UNCLEAR/> rule and the uncertainty note."""
    t = etree.SubElement(parent, "TRANSL", {XML_LANG: "eng", "kindOf": "original"})
    if text in UNKNOWN_GLOSS:
        etree.SubElement(t, "UNCLEAR")
        return
    pieces = [p if p in UNKNOWN_GLOSS else strip_uncertain(p) for p in text.split("-")]
    if any(isinstance(p, tuple) and p[1] for p in pieces):
        t.set("notes", "uncertain")
    text = "-".join(p if isinstance(p, str) else p[0] for p in pieces)
    parts = text.split("-")
    if len(parts) > 1 and any(p in UNKNOWN_GLOSS for p in parts):
        last = None
        for i, p in enumerate(parts):
            sep = "-" if i else ""
            if p in UNKNOWN_GLOSS:
                if last is None:
                    t.text = (t.text or "") + sep
                else:
                    last.tail = (last.tail or "") + sep
                last = etree.SubElement(t, "UNCLEAR")
            elif last is None:
                t.text = (t.text or "") + sep + p
            else:
                last.tail = (last.tail or "") + sep + p
        return
    t.text = text


# --------------------------------------------------------------------------
# Building one TEXT
# --------------------------------------------------------------------------

def build(page: str, data: dict, meta: dict, corrections: dict, report: dict, rejected: list):
    slug = page.replace("-", "_")
    text_id = f"{meta['text_id_prefix']}_{slug}"
    url = f"{SITE}{page}.html"
    source = " ".join(x for x in [f'kanakanavu.info, "{data["title"]}", {url}.', data["recorded"], data["speaker"]] if x)
    if page.startswith("s-tsuchida-2003"):
        source += " " + meta["source_tsuchida_suffix"]
    attrs = {"id": text_id, XML_LANG: meta["xml_lang"], "dialect": meta["dialect"],
             "citation": meta["citation"], "BibTeX_citation": meta["bibtex"],
             "copyright": meta["copyright"], "source": source}
    root = etree.Element("TEXT", attrs)
    for m in data["media"]:                         # untranscribed audio (see the docstring)
        name = m if m.lower().endswith(".mp3") else m.rsplit(".", 1)[0] + meta["video_audio_ext"]
        etree.SubElement(root, "AUDIO", {"file": name})
        report["TEXT AUDIO"] += 1

    for unit in data["units"]:
        rows = {}
        for label, cells in unit["rows"]:
            rows.setdefault(label, list(cells))
        rf = (rows.get("rf") or [""])[0]
        sid = f"{text_id}_{rf.replace(chr(39), '')}" if rf else f"{text_id}_table{unit['k']:03d}"
        nr, ge = rows.get("NR"), rows.get("GE")
        if not nr:
            rejected.append((sid, f"table {unit['k']} on {page}.html has rows {[l for l, _ in unit['rows']]} and no NR (normalized text) row"))
            continue
        if ge is None or len(ge) != len(nr):
            raise SystemExit(f"{sid}: {len(nr)} NR cells but {0 if ge is None else len(ge)} GE cells")

        # cells: [sentence text, word text, gloss, variant or None, FORM note or ""]
        cells = [[w, w, g, None, ""] for w, g in zip(nr, ge)]
        optional = None
        force_m, inserts = set(), {}                # single_m cells; add_after: cell -> new cells
        tfix = {}                                   # translation line -> (texts, note); texts[1:] are ver="alt"
        for c in corrections.get((page, rf), []):
            if c["line"] in TRANSL_LINES:
                have = (rows.get(c["line"]) or [""])[0]
                if have != c["from"]:
                    raise SystemExit(f"{sid}: correction expects {c['line']} = {c['from']!r}, found {have!r}")
                if c["line"] in tfix:
                    raise SystemExit(f"{sid}: two corrections for {c['line']}; combine them into one row")
                if c["op"] == "split":
                    tfix[c["line"]] = (c["to"].split("|"), "")
                elif c["op"] == "replace":
                    tfix[c["line"]] = ([c["to"]], "")
                elif c["op"] == "note":
                    text, note = c["to"].split("|", 1)
                    tfix[c["line"]] = ([text], note)
                elif c["op"] == "drop":
                    tfix[c["line"]] = ([], "")
                else:
                    raise SystemExit(f"{sid}: unknown translation op {c['op']!r}")
                report["corrections applied"] += 1
                report[f"translations: {c['op']}"] += 1
                continue
            i = c["cell"] - 1
            line = nr if c["line"] == "NR" else ge
            if i >= len(line) or line[i] != c["from"]:
                raise SystemExit(f"{sid}: correction expects {c['line']} cell {c['cell']} = {c['from']!r}, "
                                 f"found {line[i] if i < len(line) else None!r}")
            report["corrections applied"] += 1
            cell = cells[i]
            if c["line"] == "GE":
                cell[2] = c["to"]
            elif c["op"] == "replace":
                cell[0] = cell[1] = c["to"]
            elif c["op"] == "w_only":
                cell[1] = c["to"]
            elif c["op"] == "variant":
                base, alt = c["to"].split("|")
                cell[0] = cell[1] = base
                cell[3] = alt
            elif c["op"] == "repeat":
                cell[0] = cell[1] = c["to"]
                cell.append("repeat")
            elif c["op"] == "optional":
                cell[0] = cell[1] = c["to"]
                optional = i
            elif c["op"] == "single_m":
                force_m.add(i)
                continue
            elif c["op"] == "add_after":
                new = []
                for pair in c["to"].split():
                    word, pt = pair.split("=", 1)
                    new.append([word, word, "?", None, c["note"].format(pt=pt)])
                inserts[i] = new
                report["words added from PT"] += len(new)
                continue
            else:
                raise SystemExit(f"{sid}: unknown correction op {c['op']!r}")
            if c["note"]:
                cell[4] = c["note"]
        expanded = []
        for k, cell in enumerate(cells):
            expanded.append(cell[:5] + [k in force_m])
            if len(cell) > 5:                       # repeat
                expanded.append(cell[:5] + [k in force_m])
            expanded += [extra + [False] for extra in inserts.get(k, [])]
        for cell in expanded:                       # rule 2: the IPA tap
            for j in (0, 1, 3):
                if cell[j] and TAP in cell[j]:
                    report["tap -> r (cells)"] += 1 if j == 1 else 0
                    cell[j] = cell[j].replace(TAP, "r")
        variants = [(sid, expanded)]
        if optional is not None:
            opt_index = sum(1 + (len(c) > 5) + len(inserts.get(k, [])) for k, c in enumerate(cells[:optional]))
            without = [c for k, c in enumerate(expanded) if k != opt_index]
            variants = [(sid, without), (f"{sid}-opt", expanded)]
        for this_id, these in variants:
            emit_sentence(root, this_id, these, rows, meta, report, tfix)
    return f"{meta['file_prefix']}_{slug}.xml", root


def emit_sentence(root, sid: str, cells: list, rows: dict, meta: dict, report: dict, tfix: dict) -> None:
    s = etree.SubElement(root, "S", {"id": sid})
    if "FTE" in tfix:
        english = (tfix["FTE"][0] or [""])[0]
    else:
        english = (rows.get("FTE") or [""])[0]
    smark = sentence_mark(english)
    text = " ".join(c[0] for c in cells)
    if final_mark(text) not in LATIN_END:
        text += smark
        report[f"POL-063: sentence ends in {smark!r}"] += 1
    etree.SubElement(s, "FORM", {"kindOf": "original"}).text = text

    def finish(lang: str, t: str) -> str:
        done = end_english(t) if lang == "eng" else end_chinese(t, smark, sid)
        if done != t:
            report[f"POL-063: {lang} translation given its final mark"] += 1
        return done

    for label, lang, extra in (("FTE", "eng", {}), ("FTC", "zho", {}),
                               ("OFTE", "eng", {"ver": "alt", "notes": meta["tsuchida_ofte_note"]})):
        if label in tfix:
            texts, note = tfix[label]
            attrs = dict(extra)
            if note:
                attrs["notes"] = f"{attrs['notes']}; {note}" if attrs.get("notes") else note
            for k, t in enumerate(texts):
                etree.SubElement(s, "TRANSL", {XML_LANG: lang, **attrs, **({"ver": "alt"} if k else {})}).text = finish(lang, t)
        elif rows.get(label) and rows[label][0]:
            etree.SubElement(s, "TRANSL", {XML_LANG: lang, **extra}).text = finish(lang, rows[label][0])
    for i, (_, word, gloss, alt, note, force_m) in enumerate(cells, start=1):
        report["W"] += 1
        w = etree.SubElement(s, "W", {"id": f"{sid}_W{i:02d}"})
        form = etree.SubElement(w, "FORM", {"kindOf": "original"})
        form.text = word
        if note:
            form.set("notes", note)
        if alt:
            etree.SubElement(w, "FORM", {"kindOf": "original", "ver": "alt"}).text = alt
        if gloss in GLOSS_DROPPED:
            report["W gloss dropped (no TRANSL, no M)"] += 1
            continue
        add_gloss(w, gloss)
        fp, gp = form_pieces(word), gloss_pieces(gloss)
        if fp is None:
            if force_m or (" " not in word and gloss not in UNKNOWN_GLOSS and gp != "bad" and len(gp) == 1
                    and not LABEL.search(gloss)):
                m = etree.SubElement(w, "M", {"id": f"{w.get('id')}_M01"})
                etree.SubElement(m, "FORM", {"kindOf": "original"}).text = word
                add_gloss(m, gloss)
                report["W unsegmented, one-piece gloss (one M)" if not force_m else "W unsegmented, one M by ruling"] += 1
                report["M"] += 1
            else:
                report["W unsegmented, gloss not one piece (no M)"] += 1
                report["unsegmented, no M"].append((sid, word, gloss))
            continue
        if not aligned(fp, gp):
            report["W segmented but gloss does not split the same way (no M)"] += 1
            report["unaligned"].append((sid, word, gloss))
            continue
        report["W segmented (M emitted)"] += 1
        for j, (f, g) in enumerate(zip(fp, gp), start=1):
            m = etree.SubElement(w, "M", {"id": f"{w.get('id')}_M{j:02d}"})
            etree.SubElement(m, "FORM", {"kindOf": "original"}).text = f
            add_gloss(m, g)
            report["M"] += 1
    report["S"] += 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", required=True, type=Path, help="CodeAndDocs/source")
    ap.add_argument("--out", required=True, type=Path, help="XML output root")
    ap.add_argument("--rejected", required=True, type=Path, help="rejected-unit TSV to write")
    args = ap.parse_args()

    meta = json.loads((HERE / "corpus_metadata.json").read_text(encoding="utf-8"))
    corrections = load_corrections(HERE / "source_corrections.tsv")
    n_corrections = sum(len(v) for v in corrections.values())
    pages = sorted(p for p in (args.source / "html" / "language-documentation").glob("*.html") if p.name != "index.html")
    outdir = args.out / meta["language_dir"]
    outdir.mkdir(parents=True, exist_ok=True)
    report = collections.Counter()
    report["unaligned"], report["unsegmented, no M"] = [], []
    rejected: list[tuple[str, str]] = []
    for p in pages:
        name, root = build(p.stem, read_page(p), meta, corrections, report, rejected)
        etree.ElementTree(root).write(str(outdir / name), encoding="UTF-8", xml_declaration=True, pretty_print=True)
    if report["corrections applied"] != n_corrections:
        raise SystemExit(f"{n_corrections} rows in source_corrections.tsv but {report['corrections applied']} applied")
    with args.rejected.open("w", encoding="utf-8", newline="") as fh:
        wr = csv.writer(fh, delimiter="\t", lineterminator="\n")
        wr.writerow(["unit", "reason"])
        wr.writerows(sorted(rejected))
    print(f"generate_xml.py: {len(pages)} pages -> {len(pages)} files; "
          + "; ".join(f"{k}={v}" for k, v in report.items() if k not in ("unaligned", "unsegmented, no M"))
          + f"; rejected={len(rejected)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
