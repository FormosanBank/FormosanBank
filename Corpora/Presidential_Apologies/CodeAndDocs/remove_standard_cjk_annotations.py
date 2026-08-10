#!/usr/bin/env python3
"""Remove Mandarin parenthetical annotations from the standard tier.

The Tsou and Kavalan translations gloss many terms with a Mandarin
parenthetical — 'zipun( 日 本 )', 'senfa(憲法)', '"cungtungfuan
weiyeanhuy" ( 總統府委員會 )'. Per the corpus README these annotations are
not part of the utterance and are not in the free translation, so they are
kept on the original tier (source fidelity) and removed from the standard
tier. This script IS that removal, as a re-runnable pipeline step: it was
originally done by hand, which a rerun of `standardize.py --copy` silently
undid (the standard tier is re-copied from the original).

What counts as an annotation: an ASCII-parenthesized group whose content
contains at least one CJK ideograph and no Latin letter (whitespace and CJK
punctuation allowed). Everything else is untouched — in particular:

* bare inline CJK terms ('e 行政院 ho, ne hooin 法 院 ho, "原住民族基本法")
  are code-switched utterance content, not annotations, and stay in both
  tiers;
* Latin-content parentheticals (taa'uzva(taa'uiva), esmiza(esmia)) are
  source alternates and stay in both tiers;
* the original FORM and all TRANSL are never modified.

Removal replaces the group (with adjacent spaces) by one space, then drops
the space again before trailing punctuation or a closing quote — this
reproduces the original hand cleanup byte-for-byte on every sentence it
had covered (verified against the published tier).

PHON is regenerated with add_phonology's own phonologize: the standard
PHON from the cleaned standard FORM, and the original PHON from the
original FORM with the annotation groups masked out — the annotation is
not speech, so it contributes no '*' runs to the IPA. (Bare inline CJK
remains in FORM and still surfaces as '*' in PHON: it is utterance content
that our orthography tables cannot transcribe.)

Run AFTER standardize.py --copy and add_phonology.py (see README).
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from QC.utilities.add_phonology import load_profile, phonologize, prettify
from QC.validation._dialect_inventory import ISO_TO_LANGUAGE, standard_orthography

_IDEOGRAPH = re.compile(r'[㐀-鿿豈-﫿]')
_LATIN = re.compile(r'[A-Za-z]')
_GROUP = re.compile(r'\([^()]*\)')


def is_annotation(group: str) -> bool:
    inner = group[1:-1]
    return bool(_IDEOGRAPH.search(inner)) and not _LATIN.search(inner)


def remove_annotations(text: str) -> tuple[str, int]:
    """Strip annotation groups; returns (cleaned text, groups removed).

    Each group is removed together with its adjacent spaces and replaced
    by a single space — except when it abuts trailing punctuation, a
    closing parenthesis (nested annotation), or a closing double quote
    (odd number of '"' to the left), where no space is left behind. The
    decision is purely local, so text outside the removed spans is
    untouched (bare inline CJK keeps its source spacing).
    """
    out = []
    pos = 0
    n = 0
    for m in _GROUP.finditer(text):
        if not is_annotation(m.group(0)):
            continue
        start, end = m.start(), m.end()
        while start > pos and text[start - 1] == ' ':
            start -= 1
        while end < len(text) and text[end] == ' ':
            end += 1
        start = max(start, pos)
        left = text[start - 1] if start > 0 else ''
        right = text[end] if end < len(text) else ''
        if right in '.,;:!?)':
            sep = ''
        elif right == '"' and text[:start].count('"') % 2 == 1:
            sep = ''
        elif left in ('(', '') or right == '':
            sep = ''
        else:
            sep = ' '
        out.append(text[pos:start])
        out.append(sep)
        pos = end
        n += 1
    out.append(text[pos:])
    if not n:
        return text, 0
    return ''.join(out).strip(), n


def process_file(path: Path, dry_run: bool) -> tuple[int, int]:
    tree = ET.parse(path)
    root = tree.getroot()
    text_el = root if root.tag == 'TEXT' else root.find('.//TEXT')
    language_code = (
        text_el.get('xml:lang', '')
        or text_el.get('{http://www.w3.org/XML/1998/namespace}lang', '')
        or text_el.get('lang', '')
    ).strip()
    language = ISO_TO_LANGUAGE.get(language_code, language_code)
    dialect = text_el.get('dialect', '').strip() or 'default'
    standard_profile = load_profile(standard_orthography(language), language, dialect)
    original_profile = load_profile('Ortho113', language, dialect)

    removed = changed = 0
    for s in root.iter('S'):
        orig = s.find('FORM[@kindOf="original"]')
        std = s.find('FORM[@kindOf="standard"]')
        if orig is None or not orig.text or std is None or not std.text:
            continue
        new_std, n_std = remove_annotations(std.text)
        if n_std:
            std.text = new_std
            removed += n_std
            changed += 1
        masked_orig, n_orig = remove_annotations(orig.text)
        if standard_profile is not None:
            phon = s.find('PHON[@kindOf="standard"]')
            if phon is not None:
                new_phon = phonologize(std.text, standard_profile)
                if phon.text != new_phon:
                    phon.text = new_phon
                    changed += 1
        if original_profile is not None and n_orig:
            phon = s.find('PHON[@kindOf="original"]')
            if phon is not None:
                new_phon = phonologize(masked_orig, original_profile)
                if phon.text != new_phon:
                    phon.text = new_phon
                    changed += 1

    if changed and not dry_run:
        xml_string = prettify(root)
        xml_string = '\n'.join(l for l in xml_string.split('\n') if l.strip())
        path.write_text(xml_string, encoding='utf-8')
    return removed, changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--xml_dir', type=Path,
                    default=Path(__file__).resolve().parent.parent / 'XML')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    files = sorted(args.xml_dir.glob('*/*.xml')) or sorted(args.xml_dir.glob('*.xml'))
    if not files:
        print(f'No .xml in {args.xml_dir}', file=sys.stderr)
        return 1
    total_removed = total_changed = 0
    for path in files:
        removed, changed = process_file(path, args.dry_run)
        if removed or changed:
            print(f'  {path.parent.name}: {removed} annotation(s) removed, '
                  f'{changed} element(s) updated')
        total_removed += removed
        total_changed += changed
    verb = 'would remove' if args.dry_run else 'removed'
    print(f'{verb} {total_removed} CJK parenthetical annotation(s); '
          f'{total_changed} elements updated')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
