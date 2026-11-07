#!/usr/bin/env python3
"""'' -> " in the Amis, Atayal, Paiwan and Sakizaya Wikipedias (maintainer ruling 2026-10-14).

The articles were downloaded as Wikipedia's plain-text extracts: download.py
calls ``wikipediaapi.Wikipedia(USER_AGENT, lang_code)``, whose default
ExtractFormat.WIKI requests ``explaintext=1`` from the TextExtracts API -- the
rendered page as plain text, MediaWiki's ``''italic''`` markup already applied
and removed. A ``''`` that survives is therefore a character the page shows:
two apostrophes typed for a double quotation mark, as the README already
records for Seediq (``normalize_seediq_quotes.py``, op 1). Their shapes say the
same: of 380 runs of two in these four languages, only 90 form tidy
``''word''`` pairs; the rest are quotation marks with stray spacing
(``nu'' kuwangrung''``, ``'' babaungan a wina ''``) or mixed with ``"``
(``'' 8.19 Lolol"``).

One operation over ``FORM kindOf="original"`` in ``XML/{Amis,Atayal,Paiwan,
Sakizaya}/`` only (run EARLY in the pipeline, before ``clean_xml``): every run
of exactly two apostrophes becomes ``"``. A run of three or more is left
alone -- it can hold a glottal letter (Sakizaya Luxembourg
``''a puyuay nubuyu'''`` is ``buyu'`` + a closing ``''``; that one is
corrected by a CodeAndDocs/manual_edits.xml record, per the ruling).

Seediq is not touched here (its own step already converts its ``''``).
Standard FORMs and PHON are machine-derived and regenerate downstream
(POL-002/POL-003), so only the original tier is edited. Idempotent.
"""

import argparse
import re
import sys
from pathlib import Path

LANGUAGES = ("Amis", "Atayal", "Paiwan", "Sakizaya")
FORM_RE = re.compile(r'(<FORM kindOf="original">)(.*?)(</FORM>)', re.DOTALL)
TWO = re.compile(r"(?<!')''(?!')")


def normalize_text(text: str) -> str:
    return TWO.sub('"', text)


def process_file(path: Path, apply: bool) -> int:
    raw = path.read_text(encoding='utf-8')
    changed = 0

    def repl(m):
        nonlocal changed
        new = normalize_text(m.group(2))
        if new != m.group(2):
            changed += 1
        return m.group(1) + new + m.group(3)

    new_raw = FORM_RE.sub(repl, raw)
    if apply and new_raw != raw:
        path.write_text(new_raw, encoding='utf-8')
    return changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--corpora_path', type=Path,
                    default=Path(__file__).resolve().parent.parent / 'XML',
                    help='Wikipedias XML root (default: sibling XML/)')
    ap.add_argument('--dry-run', action='store_true',
                    help='report what would change without writing')
    args = ap.parse_args()

    total_files = total_forms = 0
    for lang in LANGUAGES:
        d = args.corpora_path / lang
        if not d.is_dir():
            sys.exit(f'not found: {d}')
        for f in sorted(d.glob('*.xml')):
            n = process_file(f, apply=not args.dry_run)
            if n:
                total_files += 1
                total_forms += n
    verb = 'would change' if args.dry_run else 'changed'
    print(f'{verb} {total_forms} original FORMs in {total_files} files')


if __name__ == '__main__':
    main()
