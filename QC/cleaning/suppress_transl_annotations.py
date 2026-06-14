#!/usr/bin/env python3
"""
Suppress annotator-note parentheticals from SENTENCE-level <TRANSL> text.

Some FormosanBank translations carry parenthetical annotator notes that are not
part of the translation itself — grammatical labels and editorial markers such
as "(人名)" (= "[this is a] personal name"), "(祈使)" (imperative),
"(各族用語)", or the English "(imperatives)" / "(collectively)". This script
strips a CURATED, EXACT-MATCH list of such notes.

CRITICAL SCOPE: only S-level <TRANSL> (a TRANSL that is a *direct child* of an
<S>) is touched. W-level and M-level <TRANSL> are never modified — there these
same strings are legitimate word/morpheme glosses, and suppressing them would
destroy real data. FORM/PHON are never touched either.

The suppression list lives in a sidecar data file (default
transl_annotation_suppress_list.txt next to this script), one exact
parenthetical content per line, '#'-comments allowed — edit that file to extend
the list; no code change needed.

Whitespace is cleaned only AT each removal site (a note between two spaces
collapses to one space; an edge note's adjacent space is consumed). Text with no
suppressed note is left byte-for-byte untouched.

When stripping a note leaves a TRANSL empty (the "translation" was only the
note, e.g. the whole text was "(男子全名)"), --empty-policy decides:
  remove (default) — delete the now-empty <TRANSL> element
  empty            — keep an empty <TRANSL></TRANSL>
  keep             — do not suppress when the note is the entire translation

Dry run by default (prints a preview + summary); pass --apply to write. Uses
lxml exactly like clean_xml.py so the diff shows only the text/element changes.
"""

import argparse
import re
from pathlib import Path

from lxml import etree

# One parenthetical pair (half- or full-width), capturing inner content.
_PAREN = re.compile(r'[（(]([^（(）)]*)[）)]')
_SENT = '\x00'  # transient marker for a removal site


def load_suppress_list(path):
    """Read the sidecar list: one exact content per line, '#' starts a comment."""
    items = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            items.append(line)
    return set(items)


def suppress_in_text(text, sup):
    """Return (new_text, n_removed). new_text is text unchanged if n_removed == 0."""
    if not text:
        return text, 0
    n = [0]

    def repl(m):
        if m.group(1).strip() in sup:
            n[0] += 1
            return _SENT
        return m.group(0)

    out = _PAREN.sub(repl, text)
    if n[0] == 0:
        return text, 0
    out = out.replace(' ' + _SENT + ' ', ' ')        # note between spaces -> one space
    out = re.sub(r' ?' + _SENT + r' ?', '', out)      # remaining sites -> drop + <=1 adjacent space
    return out.strip(), n[0]


def process_file(path, sup, empty_policy, apply_changes):
    """Process one XML file. Returns (n_notes_removed, n_emptied, changes[])."""
    try:
        tree = etree.parse(str(path))
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing {path}: {e}")
        return 0, 0, []

    n_removed = n_emptied = 0
    changes = []
    for s in root.findall('S'):
        for t in s.findall('TRANSL'):          # S-level only — never W/M
            before = t.text
            new, k = suppress_in_text(before, sup)
            if k == 0:
                continue
            if new == '':
                n_emptied += 1
                if empty_policy == 'keep':
                    continue                    # leave the note in place
                n_removed += k
                changes.append((before, '‹EMPTY› (TRANSL removed)' if empty_policy == 'remove' else ''))
                if apply_changes:
                    if empty_policy == 'remove':
                        s.remove(t)
                    else:
                        t.text = ''
            else:
                n_removed += k
                changes.append((before, new))
                if apply_changes:
                    t.text = new

    if changes and apply_changes:
        tree.write(str(path), xml_declaration=True, pretty_print=True, encoding='utf-8')
    return n_removed, n_emptied, changes


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--corpora_path', required=True,
                    help='Directory of XML files to process (recursive).')
    ap.add_argument('--list', default=str(here / 'transl_annotation_suppress_list.txt'),
                    help='Suppression list file (default: sidecar next to this script).')
    ap.add_argument('--empty-policy', choices=['remove', 'empty', 'keep'], default='remove',
                    help="What to do when a note was the entire translation (default: remove the TRANSL element).")
    ap.add_argument('--apply', action='store_true', help='Write changes. Without this, preview only.')
    ap.add_argument('--show', type=int, default=25, help='Max before/after examples to print.')
    args = ap.parse_args()

    sup = load_suppress_list(args.list)
    root_dir = Path(args.corpora_path)
    if not root_dir.exists():
        raise SystemExit(f"Error: {root_dir} does not exist")
    files = sorted(root_dir.rglob('*.xml'))
    print(f"{'APPLY' if args.apply else 'DRY RUN'}: {len(files)} files; "
          f"{len(sup)} suppression strings; empty-policy={args.empty_policy}")

    total_removed = total_emptied = files_changed = shown = 0
    for f in files:
        nr, ne, changes = process_file(f, sup, args.empty_policy, args.apply)
        if changes:
            files_changed += 1
            total_removed += nr
            total_emptied += ne
            for before, after in changes:
                if shown < args.show:
                    print(f"  [{f.name}]\n    - {before!r}\n    + {after!r}")
                    shown += 1

    print("\nSummary:")
    print(f"  files changed:        {files_changed}/{len(files)}")
    print(f"  notes removed:        {total_removed}")
    print(f"  TRANSL left empty:    {total_emptied} "
          f"({'removed' if args.empty_policy=='remove' else args.empty_policy})")
    if not args.apply:
        print("  (dry run — no files written; re-run with --apply)")


if __name__ == '__main__':
    main()
