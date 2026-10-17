#!/usr/bin/env python3
"""Put back original-tier text the shared quote cleaner mistook for a quotation.

QC/cleaning/clean_xml.py (#262) rewrites a pair of ' as " when it judges them to
be quotation marks. In a few NTU sentences the ' are glottal letters, and the
rewrite deletes them. quote_cleaner_exemptions.tsv lists each such sentence with
the text the cleaner produces ('cleaned') and the source's text ('restored').
Runs right after clean_xml. A row applies where its language directory holds its
sentence id; a sentence that is found but whose original FORM does not contain
'cleaned' exactly once exits 1, so a change in the source or the cleaner is
reviewed rather than silently skipped. Ruling 2026-10-16.

usage: restore_quote_exemptions.py --xml_dir <dir> [--table <tsv>]
"""
import argparse
import csv
import sys
from pathlib import Path

from lxml import etree


def load(path):
    rows = [line for line in Path(path).read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")]
    # The text columns hold literal " characters: no CSV quoting.
    return list(csv.DictReader(rows, delimiter="\t", quoting=csv.QUOTE_NONE))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True, type=Path)
    ap.add_argument("--table", type=Path, default=Path(__file__).with_name("quote_cleaner_exemptions.tsv"))
    args = ap.parse_args(argv)
    rows = load(args.table)
    restored = 0
    for language in sorted({r["language"] for r in rows}):
        lang_dir = args.xml_dir / language
        for path in sorted(lang_dir.glob("*.xml")) if lang_dir.is_dir() else []:
            tree = etree.parse(str(path))
            by_id = {s.get("id"): s for s in tree.getroot().iter("S")}
            changed = False
            for r in (r for r in rows if r["language"] == language):
                s = by_id.get(r["s_id"])
                if s is None:
                    continue
                form = s.find("FORM[@kindOf='original']")
                text = form.text if form is not None else None
                if text is None or text.count(r["cleaned"]) != 1:
                    print(f"restore_quote_exemptions: {r['s_id']}: original FORM {text!r} does not "
                          f"contain {r['cleaned']!r} exactly once", file=sys.stderr)
                    return 1
                form.text = text.replace(r["cleaned"], r["restored"])
                restored += 1
                changed = True
            if changed:
                tree.write(str(path), encoding="utf-8", xml_declaration=True)
    print(f"sentences restored: {restored}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
