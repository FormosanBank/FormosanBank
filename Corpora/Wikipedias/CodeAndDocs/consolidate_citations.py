"""Consolidate per-article citation/BibTeX_citation attributes into per-language form.

The default pipeline (clean_articles.py) emits a unique citation and BibTeX_citation
on every XML — one per Wikipedia article. That's useless to a corpus user: nobody
puts ten thousand citations in a paper. This script rewrites both attributes so
that every XML in a given language directory shares one canonical citation for
the whole Wikipedia (e.g. "Amis Wikipedia", "Sakizaya Wikipedia").

Output formats:
  citation         — APA-style, citing the language Wikipedia as a whole, with
                     retrieval date
  BibTeX_citation  — @misc entry keyed on Wiki_<lang_code> with title, author,
                     publisher, url, and urldate

The script is idempotent: re-running it with the same --date produces no diff.

Usage:
    python consolidate_citations.py --corpora_path path/to/XML
    python consolidate_citations.py --corpora_path path/to/XML --date 2026-06-09
"""

import argparse
import os
import re
from datetime import date as date_cls

# ISO 639-3 → human-readable Wikipedia name. The five Formosan Wikipedias
# currently in the corpus. Extend if more are added.
LANG_NAMES = {
    "ami": "Amis",
    "tay": "Atayal",
    "trv": "Seediq",
    "szy": "Sakizaya",
    "pwn": "Paiwan",
}

# Match the xml:lang attribute on the root TEXT tag, and the two attributes
# we want to overwrite. Values do not contain '"' in the current corpus,
# so [^"]* is sufficient.
LANG_RE = re.compile(r'xml:lang="([^"]+)"')
CITATION_RE = re.compile(r'citation="[^"]*"')
BIBTEX_RE = re.compile(r'BibTeX_citation="[^"]*"')


def apa_citation(lang_code, name, retrieval_date, year):
    """APA-style citation for the whole language Wikipedia."""
    return (
        f"Wikipedia contributors. ({year}). {name} Wikipedia. "
        f"Wikimedia Foundation. Retrieved {retrieval_date}, "
        f"from https://{lang_code}.wikipedia.org/"
    )


def bibtex_citation(lang_code, name, retrieval_date, year):
    """BibTeX @misc entry keyed on Wiki_<code>."""
    return (
        f"@misc{{Wiki_{lang_code}, "
        f"title = {{{name} Wikipedia}}, "
        f"author = {{{{Wikipedia contributors}}}}, "
        f"year = {{{year}}}, "
        f"publisher = {{Wikimedia Foundation}}, "
        f"url = {{https://{lang_code}.wikipedia.org/}}, "
        f"urldate = {{{retrieval_date}}} }}"
    )


def rewrite_file(xml_path, retrieval_date):
    """Rewrite citation + BibTeX_citation on one file. Returns True if changed."""
    with open(xml_path, "r", encoding="utf-8") as f:
        text = f.read()

    m = LANG_RE.search(text)
    if not m:
        return False
    lang_code = m.group(1)
    name = LANG_NAMES.get(lang_code)
    if name is None:
        return False  # Unknown language; leave file alone

    year = retrieval_date.split("-")[0]
    new_citation = f'citation="{apa_citation(lang_code, name, retrieval_date, year)}"'
    new_bibtex = f'BibTeX_citation="{bibtex_citation(lang_code, name, retrieval_date, year)}"'

    new_text, n_cit = CITATION_RE.subn(new_citation, text, count=1)
    new_text, n_bib = BIBTEX_RE.subn(new_bibtex, new_text, count=1)
    if n_cit == 0 and n_bib == 0:
        return False
    if new_text == text:
        return False

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(new_text)
    return True


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--corpora_path", required=True,
                        help="Path to the XML directory (contains per-language subdirs)")
    parser.add_argument("--date", default=None,
                        help="Retrieval date in YYYY-MM-DD (default: today). "
                             "Pass a fixed date for reproducible re-runs.")
    args = parser.parse_args()

    if not os.path.isdir(args.corpora_path):
        parser.error(f"corpora_path does not exist or is not a directory: {args.corpora_path}")

    retrieval_date = args.date or date_cls.today().isoformat()

    n_changed = 0
    n_seen = 0
    for root, _, files in os.walk(args.corpora_path):
        for fname in files:
            if not fname.endswith(".xml"):
                continue
            n_seen += 1
            if rewrite_file(os.path.join(root, fname), retrieval_date):
                n_changed += 1

    print(f"Updated {n_changed} of {n_seen} XML files (retrieval date: {retrieval_date})")


if __name__ == "__main__":
    main()
