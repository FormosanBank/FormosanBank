#!/usr/bin/env python3
"""Delete articles with no Formosan-language content (maintainer ruling 2026-08-12).

A handful of scraped pages contain no Formosan text at all: their FORMs hold
only punctuation, leftover wiki heading markup (``== ... ==``), Chinese
editorial remarks, or Chinese headings/glosses. They are not language data
and are deleted outright.

Criterion (deliberately mechanical): an article is deleted when **no FORM in
it contains a single Latin letter**. All five languages are written in Latin
orthographies, so a Latin letter is the minimal signature of Formosan
content; CJK characters, digits, and punctuation are not. Digits alone do
not save an article (``聯合國 : 193個國``).

This subsumes the earlier ``drop_empty_phon.py`` case: the punctuation-only
articles that produced empty PHON elements are now removed before
``add_phonology`` ever sees them.

Runs on the restored snapshot, before any text cleaning: cleaning
canonicalizes punctuation and Unicode but never adds or removes Latin
letters, so the verdict is the same either way. Idempotent.
"""

import argparse
import unicodedata
from pathlib import Path
from xml.etree import ElementTree as ET


def is_latin_letter(ch: str) -> bool:
    if not ch.isalpha():
        return False
    try:
        return "LATIN" in unicodedata.name(ch)
    except ValueError:
        return False


def has_formosan_content(path: Path) -> bool:
    root = ET.parse(path).getroot()
    return any(is_latin_letter(ch)
               for e in root.iter("FORM")
               for ch in (e.text or ""))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corpora_path", type=Path,
                    default=Path(__file__).resolve().parent.parent / "XML",
                    help="Wikipedias XML root (default: sibling XML/)")
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would be deleted without deleting")
    args = ap.parse_args()

    deleted = 0
    for f in sorted(args.corpora_path.rglob("*.xml")):
        if has_formosan_content(f):
            continue
        root = ET.parse(f).getroot()
        texts = {(e.text or "").strip() for e in root.iter("FORM")}
        summary = " | ".join(sorted(t for t in texts if t))
        print(f"delete {f}  [{summary[:120]}]")
        if not args.dry_run:
            f.unlink()
        deleted += 1

    verb = "would delete" if args.dry_run else "deleted"
    print(f"{verb} {deleted} articles with no Latin-letter content")


if __name__ == "__main__":
    main()
