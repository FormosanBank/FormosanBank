#!/usr/bin/env python3
"""Export a dev repo's XML as the baseline for a student proofreading page.

    python export_review.py --repo ../Formosan-<Name>          # reads <repo>/review/review_config.json
        -> <repo>/review/review_baseline.json   what the student starts from; apply_review.py checks against it
        -> <repo>/review/review_page.html       publish this file as the artifact

One card per <S>, showing what the XML publishes: the sentence (S FORM original),
the word-by-word line (W FORM original) with one gloss per word (the W's first
non-alternative TRANSL), and every S-level TRANSL. Each record carries a hash of
what it shows; an edit made against a different hash is refused at apply time.

Config keys (review/review_config.json):
  format            "<slug>-review/1"; changes whenever the baseline is regenerated
  title             page name, e.g. "Teng Puyuma Proofreading"
  language          "Puyuma"
  source_html       how the guide names the book (trusted HTML, written by us)
  pdf_note          which PDF to open and what the page numbers on the cards mean
  download_prefix   file name stem for the student's download
  gloss_script      "latin" or "han" (font, and the two Chinese-only triage flags)
  word_tier         "edit" (default) or "none" (sentence + translation only)
  check_words_against_sentence   default true; false where the word line is an
                    analysis line that is not spelled like the sentence
  gloss_line        optional {"ver": "alt", "notes_contains": "...", "empty_token": "$"}:
                    the glosses live in one S-level TRANSL; spread them over the words
  record_info       optional TSV (record, locator, include) for corpora whose <S>
                    carry no page locator, or to leave records out
  locators          optional [[regex, format], ...]: rewrite S/@source into something a
                    student can read; first match wins; {0}.. = groups, {source} = raw
  flags_off         triage flags that are noise for this source (e.g. ["parts"]
                    where the book glosses whole words)
  guide_items       corpus-specific <li> items for the guide (trusted HTML)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from lxml import etree

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "review_page.template.html"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
SAFE_ID = re.compile(r"^[A-Za-z0-9_\-.~:@+]{1,200}$")   # artifact db document-id grammar
APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "‘": "'", "`": "'", "ʻ": "'"})
LANG_NAMES = {"eng": "English", "zho": "Chinese", "jpn": "Japanese"}


def inner(el) -> str:
    """Element text with child elements written out (<UNCLEAR/>), so nothing is silently dropped."""
    if el is None:
        return ""
    out = [el.text or ""]
    for child in el:
        tag = etree.QName(child).localname
        body = inner(child)
        out.append(f"<{tag}>{body}</{tag}>" if body else f"<{tag}/>")
        out.append(child.tail or "")
    return re.sub(r"\s+", " ", "".join(out)).strip()


def original_form(el):
    form = el.find("FORM[@kindOf='original']")
    return form if form is not None else el.find("FORM")


def letters(s: str) -> str:
    s = unicodedata.normalize("NFC", s.translate(APOSTROPHES)).lower()
    s = re.sub(r"<[A-Z]+/>", "", s)
    return "".join(ch for ch in s if unicodedata.category(ch)[0] in "LMN" or ch == "'")


def parts(t: str) -> int:
    infixes = len(re.findall(r"<[^<>]+>", t))
    rest = re.sub(r"<[^<>]+>", "", t)
    return len([p for p in re.split(r"[-=]", rest) if p.strip()]) + infixes


def unbalanced(value: str) -> bool:
    return any(value.count(a) != value.count(b) for a, b in ("()", "（）", "[]", "【】"))


def record_hash(r: dict) -> str:
    shown = [r["sentence"], r["words"], r["glosses"], [t["text"] for t in r["translations"]]]
    blob = json.dumps(shown, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def readable(source: str, cfg: dict) -> str:
    """First matching [regex, format] pair wins; {0}.. are the groups, {source} the raw string."""
    for pattern, fmt in cfg.get("locators", []):
        m = re.search(pattern, source)
        if m:
            return fmt.format(*m.groups(), source=source)
    return source


def load_record_info(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    return {row["record"]: row for row in rows}


def guide_html(cfg: dict, example: tuple[str, str] | None, has_words: bool, edge_punct: bool) -> str:
    lang = html.escape(cfg["language"])
    items = [
        f"<p>Each card is one sentence from {cfg['source_html']} as it appears in FormosanBank's data. "
        f"Open the book at the page shown on the card and make the card match the book. {cfg.get('pdf_note', '')}</p>",
        "<h3>What to fix</h3><ul>",
        f"<li><strong>Misread letters.</strong> Fix any {lang} letter, character or punctuation mark that differs "
        "from the book. Type the book's spelling even where it looks unusual. Don't correct the author's spelling or grammar.</li>",
        "<li><strong>Translations.</strong> Make each free translation match the book. Where the book gives more than one "
        "translation, each has its own box. If the book prints a translation the card lacks, copy it into the note.</li>",
    ]
    if has_words:
        items += [
            "<li><strong>The sentence and the word line.</strong> The first box is the sentence as the book prints it. "
            "The boxes under it are the word-by-word line: one word per box, with its gloss underneath.</li>",
            "<li><strong>Misaligned glosses.</strong> Each gloss must sit under the word it belongs to. Click a box, then use the "
            "buttons under the table: <em>Insert box</em> and <em>Delete box</em> shift only that row; <em>Insert column</em> and "
            "<em>Delete column</em> change both rows.</li>",
            "<li><strong>One gloss under two words.</strong> When the book prints a single gloss under two or more words together, "
            "put those words in one box with a space between them, and type the gloss once.</li>",
            "<li><strong>No gloss printed.</strong> If the book prints no gloss under a word, leave that gloss box empty. "
            "Don't type <code>∅</code>, <code>?</code> or anything else there. Type <code>∅</code> or <code>?</code> only where the book itself prints that symbol.</li>",
        ]
        if edge_punct:
            items.append("<li><strong>Punctuation in the word boxes.</strong> Some word boxes carry the comma, full stop or quotation mark "
                         "that stands next to the word in the sentence. Leave it there; punctuation is sorted out when the corpus is built. "
                         "Fix it only where it is the wrong mark.</li>")
        if example:
            items.append(
                "<li><strong>Morphemes.</strong> A word split by hyphens should have a gloss with the same number of parts, "
                f"for example <code>{html.escape(example[0])}</code> over <code>{html.escape(example[1])}</code>. "
                "Keep infixes in angle brackets and clitic <code>=</code> signs as the book prints them.</li>")
    items += [
        "</ul><h3>What to leave alone</h3><ul>",
        "<li><strong>Ungrammatical examples.</strong> FormosanBank leaves out examples the book marks with <code>*</code> or <code>?</code>. "
        "If a card holds one the book stars, write \"starred in the book\" in the note. Don't add the star.</li>",
        "<li><strong>One printed example, several cards.</strong> Where the book offers alternatives (<code>a / b</code>) or optional "
        "words in parentheses, FormosanBank keeps each reading as its own sentence, so one printed example can appear as several cards. "
        "Check that each card's words, glosses and translation belong to its own reading. Don't add the slashes or parentheses back.</li>",
        "<li><strong>Quotation marks.</strong> Where the book uses single quotes as quotation marks, FormosanBank writes straight double "
        "quotes (<code>\"</code>) instead, because <code>'</code> is a letter in many Formosan spellings. Leave those double quotes as they are.</li>",
        "<li><strong><code>&lt;UNCLEAR/&gt;</code></strong> marks a spot the scrape could not read. If the book is legible there, "
        "replace <code>&lt;UNCLEAR/&gt;</code> with what it prints; otherwise leave it.</li>",
    ]
    items += cfg.get("guide_items", [])
    items += [
        "</ul><h3>Finishing a card</h3><ul>",
        "<li><strong>Notes.</strong> If you are unsure, or something cannot be fixed in the boxes, write it in the note. Notes go to the maintainer.</li>",
        "<li><strong>Mark reviewed</strong> when a card matches the book, even if you changed nothing. That is how we know it was checked.</li>",
        "<li>Cards with a yellow tag were flagged by an automatic check as likely problems. The tag is only a hint about where to start; hover over it to see what it means.</li>",
        "</ul>",
    ]
    return "\n".join(items)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--config", type=Path, help="default: <repo>/review/review_config.json")
    args = ap.parse_args()
    repo = args.repo.resolve()
    cfg_path = args.config or repo / "review" / "review_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    out_dir = cfg_path.parent
    corrections = out_dir / "review_corrections.tsv"
    if corrections.exists() and corrections.read_text(encoding="utf-8").count("\n") > 1:
        sys.exit(f"{corrections} holds corrections. Re-exporting would change the baseline under them; "
                 "incorporate or move them aside first.")

    word_tier = cfg.get("word_tier", "edit")
    gline = cfg.get("gloss_line")
    info = load_record_info(repo / cfg["record_info"]) if cfg.get("record_info") else {}
    xml_files = sorted((repo / "XML").rglob("*.xml"))
    if not xml_files:
        sys.exit(f"No XML under {repo / 'XML'}")

    records, seen = [], set()
    for path in xml_files:
        rel = path.relative_to(repo).as_posix()
        label = path.relative_to(repo / "XML").with_suffix("").as_posix()
        for s in etree.parse(str(path)).getroot().iter("S"):
            rid = s.get("id") or ""
            if not SAFE_ID.match(rid) or rid in (".", ".."):
                sys.exit(f"{rel}: S id {rid!r} is not usable as a store document id; map ids first")
            if rid in seen:
                sys.exit(f"S id {rid!r} occurs twice; the page needs unique ids")
            seen.add(rid)
            row = info.get(rid, {})
            if row.get("include", "yes").strip().lower() in ("no", "false", "0"):
                continue
            sform = original_form(s)
            ws = s.findall("W") if word_tier != "none" else []
            words = [inner(original_form(w)) for w in ws]
            glosses, more = [], []
            for w in ws:
                prim = [t for t in w.findall("TRANSL") if t.get("ver") != "alt"]
                glosses.append(inner(prim[0]) if prim else "")
                for t in w.findall("TRANSL"):
                    if not prim or t is not prim[0]:
                        more.append(f"{inner(original_form(w))} = {inner(t)}")
            line_el = None
            if gline and ws and not any(glosses):
                for t in s.findall("TRANSL"):
                    if t.get("ver") == gline.get("ver") and gline.get("notes_contains", "") in (t.get("notes") or ""):
                        line_el = t
                        break
            line_count_off = False
            if line_el is not None:
                toks = ["" if tok == gline.get("empty_token") else tok for tok in inner(line_el).split()]
                line_count_off = len(toks) != len(words)
                glosses = (toks + [""] * len(words))[:len(words)] if len(toks) <= len(words) else \
                    toks[:len(words) - 1] + [" ".join(toks[len(words) - 1:])]
            translations = [{"lang": t.get(XML_LANG), "ver": t.get("ver"), "text": inner(t)}
                            for t in s.findall("TRANSL") if t is not line_el]
            notes = [n for n in [sform.get("notes") if sform is not None else None]
                     + [t.get("notes") for t in s.findall("TRANSL") if t is not line_el] if n]
            rec = {
                "record": rid,
                "file": rel,
                "file_label": label,
                "locator": row.get("locator") or readable(s.get("source") or "", cfg),
                "sentence": inner(sform),
                "words": words,
                "glosses": glosses,
                "gloss_source": "line" if line_el is not None else ("words" if ws else "none"),
                "translations": translations,
                "alternates": [inner(f) for f in s.findall("FORM[@kindOf='alternate']")],
                "more_glosses": "; ".join(more),
                "scrape_notes": list(dict.fromkeys(notes)),
                "_line_count_off": line_count_off,
            }
            rec["hash"] = record_hash(rec)
            records.append(rec)

    # ---- triage flags (hints for the student, not verdicts) ----
    usual: dict[str, Counter] = defaultdict(Counter)
    vocabulary: set[str] = set()
    for r in records:
        for w, g in zip(r["words"], r["glosses"]):
            usual[w.strip(".,;:!?\"")][g] += 1
            if g:
                vocabulary.add(g)
    has_translations = sum(1 for r in records if r["translations"]) > len(records) / 2
    han = cfg.get("gloss_script") == "han"
    for r in records:
        flags = []
        pairs = list(zip(r["words"], r["glosses"]))
        if r["words"]:
            if any(re.search(r"[-=<]", w) and g and " " not in w and parts(w) != parts(g) for w, g in pairs):
                flags.append("parts")
            if any(g for _, g in pairs):
                if any(not g for _, g in pairs):
                    flags.append("no_gloss")
            else:
                flags.append("no_glosses")
            if cfg.get("check_words_against_sentence", True) and \
                    letters(" ".join(r["words"])) != letters(r["sentence"]):
                flags.append("words_sentence")
            if han:
                for w, g in pairs:
                    common = usual[w.strip(".,;:!?\"")].most_common(1)
                    if common and g != common[0][0] and len(g) == 1 and g in common[0][0]:
                        flags.append("split_word")
                for (_, left), (_, right) in zip(pairs, pairs[1:]):
                    if left and right and min(len(left), len(right)) <= 2 and left + right in vocabulary:
                        flags.append("split_gloss")
        if any(unbalanced(v) for v in [r["sentence"], *r["words"], *r["glosses"]]):
            flags.append("bracket")
        if r.pop("_line_count_off"):
            flags.append("line_count")
        if "<UNCLEAR" in json.dumps([r["sentence"], r["words"], r["glosses"]], ensure_ascii=False):
            flags.append("unclear")
        if has_translations and not r["translations"]:
            flags.append("no_translation")
        r["flags"] = sorted(set(flags) - set(cfg.get("flags_off", [])))

    # A note the scrape put on most cards says something about the whole corpus: it belongs in
    # the guide (written by hand into guide_items), not repeated on every card.
    note_counts = Counter(n for r in records for n in r["scrape_notes"])
    corpus_wide = {n for n, c in note_counts.items() if c > len(records) / 2}
    for r in records:
        r["scrape_notes"] = [n for n in r["scrape_notes"] if n not in corpus_wide]
    all_words = [w for r in records for w in r["words"]]
    edge_punct = sum(1 for w in all_words if re.search(r'^["“‘(]|[,.;:!?"”’)]$', w)) > len(all_words) / 100

    example = None
    for r in records:
        for w, g in zip(r["words"], r["glosses"]):
            if re.search(r'[^\w\-=<>]', w):
                continue
            if parts(w) >= 3 and parts(w) == parts(g) and "<" not in w and " " not in w and len(w) <= 24:
                example = (w, g)
                break
        if example:
            break

    files = Counter(r["file"] for r in records)
    labels = {r["file"]: r["file_label"] for r in records}
    payload = {
        "format": cfg["format"],
        "page": {
            "language": cfg["language"],
            "gloss_script": cfg.get("gloss_script", "latin"),
            "word_tier": word_tier,
            "download_prefix": cfg["download_prefix"],
            "files": [{"file": f, "label": labels[f], "count": n} for f, n in sorted(files.items())],
        },
        "records": records,
    }
    (out_dir / "review_baseline.json").write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    template = TEMPLATE.read_text(encoding="utf-8")
    for marker in ("/*__BASELINE__*/", "<!--__GUIDE__-->"):
        if template.count(marker) != 1:
            sys.exit(f"{TEMPLATE} must contain {marker} exactly once")
    has_words = any(r["words"] for r in records)
    page = (template.replace("__TITLE__", html.escape(cfg["title"]))
            .replace("<!--__GUIDE__-->", guide_html(cfg, example, has_words, edge_punct))
            # Inside <script type="application/json">, only "</" can end the block early.
            .replace("/*__BASELINE__*/", json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")))
    (out_dir / "review_page.html").write_text(page, encoding="utf-8")

    flag_counts = Counter(f for r in records for f in r["flags"])
    print(f"Wrote {out_dir / 'review_baseline.json'} and review_page.html ({len(page) / 1e6:.2f} MB)")
    print(f"  {len(records)} cards from {len(files)} XML file(s); {sum(1 for r in records if r['words'])} with a word line "
          f"({sum(1 for r in records if r['gloss_source'] == 'line')} spread from a gloss line); "
          f"{sum(1 for r in records if not r['translations'])} without a translation")
    print(f"  flagged: {sum(1 for r in records if r['flags'])} cards  {dict(sorted(flag_counts.items()))}")
    print(f"  morpheme example in guide: {example}")
    for n in sorted(corpus_wide):
        print(f"  NOT shown on cards (on {note_counts[n]} of {len(records)}); say it in guide_items if it matters: {n}")
    print(f"  punctuation-in-word-boxes guide item: {'included' if edge_punct else 'not needed'}")
    notes = Counter(n for r in records for n in r["scrape_notes"])
    if notes:
        print(f"  scrape notes shown on cards ({len(notes)} distinct; most common):")
        for n, c in notes.most_common(6):
            print(f"    {c:5d}  {n[:150]}")


if __name__ == "__main__":
    main()
