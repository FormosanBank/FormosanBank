#!/usr/bin/env python3
"""Normalize apostrophes in the Seediq Wikipedia (maintainer ruling 2026-08-11).

Seediq orthography does not use the apostrophe as a letter (no `'` row in
Orthographies/Ortho113/Seediq.tsv), and source inspection of the trv wikitext
showed the corpus's apostrophes are quotation usage: literal ``''`` pairs the
article authors typed as double-quote substitutes (<nowiki>-protected in the
wikitext so MediaWiki would not italicize them), single-quoted titles of laws
and documents, and the Atayal-vocabulary boilerplate words ``knita'`` and
``brbiru'`` ("cinkhulan sa knita' sa brbiru'" ~ "source: seen in the
writings"), which keep a genuine glottal ``'``.

Two ordered operations over ``FORM kindOf="original"`` in ``XML/Seediq/`` only
(run EARLY in the pipeline, before ``clean_xml``):

1. Literal ``''`` pairs -> ``"``.
2. Every remaining ``'`` -> ``"``, EXCEPT apostrophes inside the whitelisted
   words ``knita'`` / ``brbiru'`` (case-insensitive, punctuation-tolerant).

Other Wikipedias languages are untouched: their ``'`` is assumed glottal by
the documented fiat (see README, "Apostrophe handling").

Standard FORMs and PHON are machine-derived and regenerate downstream
(POL-002/POL-003), so only the original tier is edited here. Idempotent.
"""

import argparse
import re
import sys
from pathlib import Path

WHITELIST = {"knita'", "brbiru'"}
# Punctuation strippable around a token when matching the whitelist — the
# apostrophe itself is deliberately NOT in this set.
EDGE_PUNCT = '.,;:?!"()[]{}<>«»“”‘’—–…~'

FORM_RE = re.compile(r'(<FORM kindOf="original">)(.*?)(</FORM>)', re.DOTALL)


def normalize_text(text: str) -> str:
    text = text.replace("''", '"')                       # op 1
    out = []
    for tok in text.split(' '):                          # op 2
        if "'" in tok and tok.strip(EDGE_PUNCT).casefold() in WHITELIST:
            out.append(tok)
        else:
            out.append(tok.replace("'", '"'))
    return ' '.join(out)


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

    seediq = args.corpora_path / 'Seediq'
    if not seediq.is_dir():
        sys.exit(f'not found: {seediq} (this script is Seediq-only by ruling)')

    total_files = total_forms = 0
    for f in sorted(seediq.glob('*.xml')):
        n = process_file(f, apply=not args.dry_run)
        if n:
            total_files += 1
            total_forms += n
    verb = 'would change' if args.dry_run else 'changed'
    print(f'{verb} {total_forms} original FORMs in {total_files} files')


if __name__ == '__main__':
    main()
