#!/usr/bin/env python3
"""Corpus files from translations collected on the documentation site.

Maintainer, 2026-10-18: "when we consume these, they become part of the
FormosanBank GitBook corpus itself ... Old translations are not removed from
the corpus ... new translations may reflect new sentence; they are out of date
for the documentation, but they are still data." Mandarin enters only as a
translation attached to a Formosan sentence of the same English sentence (R3).

Reads the approved rows of FormosanBank's docs/translations/{pwn,ami,bnn}.tsv
and writes one TEXT per translator x dialect x date under
XML/<Language>/doc_translations/: each S has the translation as its original
FORM, the English sentence as TRANSL eng and, when one is approved, the
Mandarin translation of the same English sentence as TRANSL zho. The store is
append-only, so every earlier file is regenerated identically and nothing is
ever removed. It also refreshes the counts block in ../README.md, including
how many of the attached Mandarin translations began as machine translation
(R4: "Yes, say so in the corpus README with counts").
"""

from __future__ import annotations

import csv
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = HERE.parent
FORMOSANBANK = HERE.parents[2]
sys.path.insert(0, str(HERE))
import citation  # noqa: E402

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
LANGUAGES = {"pwn": "Paiwan", "ami": "Amis", "bnn": "Bunun"}
SOURCE = "translation of the FormosanBank documentation (site translation pages)"
COUNTS_START = "<!-- SITE TRANSLATION COUNTS START (written by CodeAndDocs/build_translations.py) -->"
COUNTS_END = "<!-- SITE TRANSLATION COUNTS END -->"


def read_store(store_dir: Path, code: str) -> list[dict[str, str]]:
    path = store_dir / f"{code}.tsv"
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def newest_approved(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    best: dict[str, dict[str, str]] = {}
    for row in rows:
        if row["approved"] == "yes" and row["translation"].strip():
            if row["english"] not in best or row["date"] >= best[row["english"]]["date"]:
                best[row["english"]] = row
    return best


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.casefold()).strip("-") or "unknown"


def build(store_dir: Path, xml_root: Path) -> list[dict]:
    """Write the files; return one summary dict per file."""
    apa, bibtex = citation.citation(store_dir)
    mandarin = newest_approved(read_store(store_dir, "zho"))
    summaries = []
    for code, language in LANGUAGES.items():
        batches: dict[tuple, list[dict]] = defaultdict(list)
        for row in read_store(store_dir, code):
            if row["approved"] == "yes" and row["translation"].strip():
                batches[(row["translator"], row["dialect"], row["date"])].append(row)
        out_dir = xml_root / language / "doc_translations"
        for (translator, dialect, date), rows in sorted(batches.items()):
            text_id = f"doc_translation_{code}_{slug(translator)}_{slug(dialect)}_{date}"
            attrs = {"id": text_id, XML_LANG: code, "source": SOURCE, "copyright": "CC BY-NC 4.0",
                     "citation": apa, "BibTeX_citation": bibtex}
            if dialect:
                attrs["dialect"] = dialect
            root = ET.Element("TEXT", attrs)
            zho = mt = 0
            for n, row in enumerate(sorted(rows, key=lambda r: (r["english"], r["translation"])), start=1):
                sentence = ET.SubElement(root, "S", {"id": f"{text_id}_{n}"})
                ET.SubElement(sentence, "FORM", {"kindOf": "original"}).text = row["translation"]
                ET.SubElement(sentence, "TRANSL", {XML_LANG: "eng"}).text = row["english"]
                zh = mandarin.get(row["english"])
                if zh:
                    ET.SubElement(sentence, "TRANSL", {XML_LANG: "zho"}).text = zh["translation"]
                    zho += 1
                    mt += zh["origin"] == "mt"
            ET.indent(root, space="  ")
            out_dir.mkdir(parents=True, exist_ok=True)
            path = out_dir / f"{text_id}.xml"
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
            with path.open("ab") as handle:
                handle.write(b"\n")
            summaries.append({"file": str(Path("XML") / path.relative_to(xml_root)), "sentences": len(rows),
                              "mandarin": zho, "mandarin_mt": mt, "translator": translator,
                              "dialect": dialect or "unknown"})
    return summaries


def counts_block(summaries: list[dict]) -> str:
    if not summaries:
        body = ("No translations collected through the site's translation pages yet. When there are, "
                "each file is listed here with its sentence count and how many of its attached Mandarin "
                "translations began as machine translation and were then approved by a person.")
    else:
        lines = ["| File | Translator | Dialect | Sentences | Mandarin attached | of which began as machine translation |",
                 "| --- | --- | --- | ---: | ---: | ---: |"]
        lines += [f"| `{s['file']}` | {s['translator']} | {s['dialect']} | {s['sentences']} | {s['mandarin']} | {s['mandarin_mt']} |"
                  for s in summaries]
        body = "\n".join(lines)
    return f"{COUNTS_START}\n{body}\n{COUNTS_END}"


def update_readme(readme: Path, summaries: list[dict]) -> None:
    text = readme.read_text(encoding="utf-8")
    start, end = text.find(COUNTS_START), text.find(COUNTS_END)
    if start == -1 or end == -1:
        raise ValueError(f"{readme} has no site-translation counts block")
    readme.write_text(text[:start] + counts_block(summaries) + text[end + len(COUNTS_END):], encoding="utf-8")


def main() -> int:
    summaries = build(FORMOSANBANK / "docs" / "translations", CORPUS / "XML")
    update_readme(CORPUS / "README.md", summaries)
    print(f"Wrote {len(summaries)} site-translation file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
