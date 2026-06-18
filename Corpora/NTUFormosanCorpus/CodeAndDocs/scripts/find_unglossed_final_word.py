"""
find_unglossed_final_word.py

Walks all Final_XML files and finds sentences where the last <W> element
has neither an English nor a Mandarin W-level TRANSL (or both are empty/"_").

Output:
  unglossed_final_word.csv  — one row per offending sentence

Also cross-references with:
  sentences_missing_glosses.csv  (last S-FORM token has no W)
  empty_gloss_words.csv          (grammar JSON words with both glosses empty)
"""

import csv
import glob
import os
import re
import xml.etree.ElementTree as ET

XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'

# ---------------------------------------------------------------------------

def has_real_text(elem):
    """True if elem.text is non-empty and not a bare underscore."""
    t = (elem.text or '').strip()
    return bool(t) and t != '_'


def last_w_is_unglossed(s_elem):
    """
    Return the last <W> child of *s_elem* if it has no non-empty W-level
    TRANSL in either 'en' or 'zho'.  Return None otherwise.
    """
    ws = s_elem.findall('W')
    if not ws:
        return None
    last_w = ws[-1]
    for tr in last_w.findall('TRANSL'):
        lang = tr.get(XML_LANG, '')
        if lang in ('en', 'zho') and has_real_text(tr):
            return None          # at least one gloss found — not unglossed
    return last_w


def last_w_form(w_elem):
    f = w_elem.find('FORM')
    return (f.text or '').strip() if f is not None else ''


# ---------------------------------------------------------------------------

def scan(final_xml_dir):
    rows = []
    for fpath in sorted(glob.glob(os.path.join(final_xml_dir, '**', '*.xml'),
                                  recursive=True)):
        rel   = os.path.relpath(fpath, final_xml_dir)
        parts = rel.split(os.sep)
        category = parts[0] if len(parts) >= 2 else ''
        language = parts[1] if len(parts) >= 3 else ''

        try:
            tree = ET.parse(fpath)
        except ET.ParseError as e:
            print(f'  [WARN] {rel}: {e}')
            continue

        for s in tree.getroot().findall('.//S'):
            bad_w = last_w_is_unglossed(s)
            if bad_w is None:
                continue
            rows.append({
                'category':    category,
                'language':    language,
                'xml_file':    rel,
                'sentence_id': s.get('id', ''),
                'last_W_form': last_w_form(bad_w),
                'last_W_id':   bad_w.get('id', ''),
            })
    return rows


# ---------------------------------------------------------------------------

def load_sentence_ids(csv_path, id_col):
    ids = set()
    if not os.path.exists(csv_path):
        return ids
    with open(csv_path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            ids.add(row.get(id_col, '').strip())
    return ids


# ---------------------------------------------------------------------------

def main():
    project_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    final_xml_dir = os.path.join(project_dir, 'Final_XML')
    output_csv    = os.path.join(project_dir, 'unglossed_final_word.csv')
    missing_csv   = os.path.join(project_dir, 'sentences_missing_glosses.csv')
    empty_csv     = os.path.join(project_dir, 'empty_gloss_words.csv')

    print('Scanning Final_XML for sentences whose last W has no gloss…')
    rows = scan(final_xml_dir)

    fieldnames = ['category', 'language', 'xml_file', 'sentence_id',
                  'last_W_form', 'last_W_id']
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        csv.DictWriter(f, fieldnames=fieldnames).writeheader()
        csv.DictWriter(f, fieldnames=fieldnames).writerows(rows)
    print(f'Wrote {len(rows)} rows to {output_csv}')

    # Cross-reference
    this_ids    = {r['sentence_id'] for r in rows}
    missing_ids = load_sentence_ids(missing_csv, 'sentence_id')
    empty_ids   = load_sentence_ids(empty_csv,   'Sentence_id')

    overlap_missing = len(this_ids & missing_ids)
    overlap_empty   = len(this_ids & empty_ids)

    print(f'\nOf {len(rows)} sentences with an unglossed final W:')
    print(f'  {overlap_missing} also appear in sentences_missing_glosses.csv '
          f'(last S-FORM token has no W)')
    print(f'  {overlap_empty} also appear in empty_gloss_words.csv '
          f'(grammar JSON words with both glosses empty)')


if __name__ == '__main__':
    main()
