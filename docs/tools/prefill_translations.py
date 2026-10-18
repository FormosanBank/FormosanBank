#!/usr/bin/env python3
"""Fill the translation stores with starting text that a person then checks.

Maintainer, 2026-10-18: "For Mandarin, we can prepopulate using MT (basically,
you translate it), but we don't *use* anything for an actual GitHub Page until
it's been approved by someone." and "The ticking is mostly for approving prior
work (MT-based, guesstimated translation from a previous version of the
website, etc)." Every row written here is therefore approved = no.

    python docs/tools/prefill_translations.py inventory --out units.json
        Every unit the translation pages ask for, per language (input for drafting).
    python docs/tools/prefill_translations.py corpus-match
        Exact English matches with the FormosanBank GitBook corpus (each Paiwan
        sentence there carries its English and Mandarin): Paiwan and Mandarin rows,
        origin corpus-match.
    python docs/tools/prefill_translations.py add <code> <origin> <file.tsv> [--translator NAME]
        Add drafted rows (TSV with columns english, translation) with the given
        origin (mt or previous-website). Units not on the site are refused.

Existing rows are never changed; a row identical to one already stored is skipped.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import translations as tr  # noqa: E402

XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
CORPUS_XML = tr.REPO_ROOT / "Corpora" / "FormosanBankGitBook" / "XML" / "Paiwan"


def inventory(repository_root: Path) -> dict[str, list[str]]:
    import prepare_site
    import site_labels
    import translated_editions

    out: dict[str, list[str]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "en"
        prepare_site.stage_edition(repository_root, staging, prepare_site.EDITIONS_BY_KEY["en"])
        for target in tr.TARGETS:
            data = translated_editions.tool_data(staging, target, [], [])
            units = list(site_labels.labels())
            for page in data["pages"]:
                units += [u for u in page["units"] if u not in units]
            out[target.code] = list(dict.fromkeys(units))
    return out


def add_rows(code: str, new: list[dict]) -> tuple[int, int]:
    store = tr.load_store(code)
    seen = {(r["english"], r["translation"], r["origin"]) for r in store}
    added = [r for r in new if (r["english"], r["translation"], r["origin"]) not in seen]
    tr.save_store(code, store + added)
    return len(added), len(new) - len(added)


def corpus_rows(units: set[str], today: str) -> dict[str, list[dict]]:
    rows: dict[str, list[dict]] = {"pwn": [], "zho": []}
    for path in sorted(CORPUS_XML.glob("*.xml")):
        root = ET.parse(path).getroot()
        for sentence in root.iter("S"):
            english = next((t.text for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "eng"), None)
            chinese = next((t.text for t in sentence.findall("TRANSL") if t.get(XML_LANG) == "zho"), None)
            form = next((f.text for f in sentence.findall("FORM") if f.get("kindOf") == "original" and not f.get("ver")), None)
            if not english or tr.key_of(english) not in units:
                continue
            key = tr.key_of(english)
            if form:
                rows["pwn"].append({"english": key, "translation": form, "approved": "no", "origin": "corpus-match",
                                    "translator": "Xuan Ruan", "dialect": root.get("dialect", ""), "date": today})
            if chinese:
                rows["zho"].append({"english": key, "translation": chinese, "approved": "no", "origin": "corpus-match",
                                    "translator": "", "dialect": "", "date": today})
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory")
    inv.add_argument("--out", type=Path, required=True)
    sub.add_parser("corpus-match")
    add = sub.add_parser("add")
    add.add_argument("code", choices=sorted(tr.TARGETS_BY_CODE))
    add.add_argument("origin", choices=("mt", "previous-website"))
    add.add_argument("file", type=Path)
    add.add_argument("--translator", default="")
    args = parser.parse_args(argv)
    today = dt.date.today().isoformat()

    if args.command == "inventory":
        units = inventory(tr.REPO_ROOT)
        args.out.write_text(json.dumps(units, ensure_ascii=False, indent=0), encoding="utf-8")
        print({code: len(u) for code, u in units.items()})
        return 0
    if args.command == "corpus-match":
        units = set(inventory(tr.REPO_ROOT)["zho"])
        for code, rows in corpus_rows(units, today).items():
            added, skipped = add_rows(code, rows)
            print(f"{code}: {added} corpus-match rows added, {skipped} already present")
        return 0
    units = set(inventory(tr.REPO_ROOT)[args.code])
    with open(args.file, newline="", encoding="utf-8") as handle:
        drafted = list(csv.DictReader(handle, delimiter="\t"))
    rows, refused = [], []
    for row in drafted:
        english, translation = tr.key_of(row.get("english", "")), " ".join((row.get("translation") or "").split())
        if not english or not translation:
            continue
        if english not in units:
            refused.append(english)
            continue
        rows.append({"english": english, "translation": translation, "approved": "no", "origin": args.origin,
                     "translator": args.translator, "dialect": "", "date": today})
    added, skipped = add_rows(args.code, rows)
    print(f"{args.code}: {added} {args.origin} rows added, {skipped} already present, {len(refused)} refused (not on the site)")
    for english in refused[:10]:
        print(f"  refused: {english}")
    return 1 if refused else 0


if __name__ == "__main__":
    raise SystemExit(main())
