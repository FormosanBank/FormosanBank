"""
find_missing_last_word.py

Walks all Final_XML files (Grammar, Stories, Sentences) and finds every <S>
element whose last letter-bearing FORM token has no corresponding <W> element.

Output:
  sentences_missing_glosses.csv  — one row per offending sentence
  (also prints how many of those sentences overlap with empty_gloss_words.csv)
"""

import csv
import glob
import os
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HAS_LETTER = re.compile(r'[^\W\d_]', re.UNICODE)   # at least one Unicode letter
_STRIP_PUNCT = re.compile(r'^[\W_]+|[\W_]+$', re.UNICODE)  # leading/trailing non-word chars


def letter_tokens(text):
    """Return whitespace-split tokens that contain at least one letter."""
    return [t for t in text.split() if _HAS_LETTER.search(t)]


def bare(tok):
    """Strip leading/trailing punctuation and internal hyphens for comparison.

    W FORM values use hyphens as morpheme-boundary markers (e.g. ``ma-macai``)
    while the S FORM uses the natural orthographic form (``mamacai``).
    Removing hyphens before comparing lets them match.
    """
    t = re.sub(r'<[^>]*>', '', tok)   # remove infix markers like <n>, <m>
    t = _STRIP_PUNCT.sub('', t).lower()
    return t.replace('-', '')


def w_forms(s_elem):
    """Return the set of bare FORM texts from all <W> children of an <S>."""
    result = set()
    for w in s_elem.findall('W'):
        f = w.find('FORM')
        if f is not None and f.text:
            result.add(bare(f.text))
    return result


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def scan_xml_tree(final_xml_dir):
    """
    Walk all XML files under final_xml_dir and return a list of row dicts for
    sentences whose last letter-bearing token has no corresponding <W>.
    """
    rows = []
    xml_files = sorted(glob.glob(os.path.join(final_xml_dir, '**', '*.xml'),
                                 recursive=True))
    for fpath in xml_files:
        rel = os.path.relpath(fpath, final_xml_dir)
        # Derive a tidy language label from the path (first directory component)
        parts = rel.split(os.sep)
        category  = parts[0] if len(parts) >= 2 else ''   # Grammar / Stories / Sentences
        lang_part = parts[1] if len(parts) >= 3 else ''   # e.g. Seediq, Amis, ...

        try:
            tree = ET.parse(fpath)
        except ET.ParseError as e:
            print(f'  [WARN] Parse error in {rel}: {e}')
            continue

        root = tree.getroot()
        for s in root.findall('.//S'):
            s_id = s.get('id', '')
            form_elem = s.find('FORM')
            if form_elem is None or not form_elem.text:
                continue
            s_form = form_elem.text.strip()
            tokens = letter_tokens(s_form)
            if not tokens:
                continue
            last_tok = tokens[-1]

            # Check whether the bare form of the last token appears in any W.
            ws = w_forms(s)
            if not ws:
                continue   # sentence has no Ws at all — different problem
            if bare(last_tok) not in ws:
                rows.append({
                    'category':   category,
                    'language':   lang_part,
                    'xml_file':   rel,
                    'sentence_id': s_id,
                    's_form':     s_form,
                    'last_token': last_tok,
                    'num_tokens': len(tokens),
                    'num_W':      len(s.findall('W')),
                })
    return rows


def load_empty_gloss_sentence_ids(empty_csv):
    """
    Read empty_gloss_words.csv and return a set of
    (language_prefix, file_stem, sentence_id_str) tuples.
    """
    ids = set()
    if not os.path.exists(empty_csv):
        return ids
    with open(empty_csv, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            lang  = row.get('language', '').split('_')[0]   # e.g. Sakizaya
            fstem = os.path.splitext(row.get('file_name', ''))[0]  # e.g. A2
            sid   = str(row.get('Sentence_id', '')).strip()
            ids.add((lang, fstem, sid))
    return ids


def sentence_key_from_row(row):
    """
    Derive a (language, file_stem, sentence_id_str) key from a missing-last-word row
    so it can be matched against empty_gloss_sentence_ids.

    S id format examples:
      Grammar:   ap2_S_4           → lang from xml_file path, file_stem=ap2, sid=4
      Stories:   sdqNr-frog_lubi 2020s_S_3_W0  → skip (this is a W id, not S)
                 actually S ids look like:  sdqNr-frog_lubi 2020s_S_3
      Sentences: 10-5_S_1
    """
    s_id = row['sentence_id']
    lang = row['language']

    # Grammar pattern:  <filestem>_S_<n>  or  <filestem>_S_<n>[a-z]
    m = re.match(r'^(.+?)_S_(\d+)', s_id)
    if m:
        fstem = m.group(1)
        sid   = m.group(2)
        return (lang, fstem, sid)
    return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    project_dir   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    final_xml_dir = os.path.join(project_dir, 'Final_XML')
    output_csv    = os.path.join(project_dir, 'sentences_missing_glosses.csv')
    empty_csv     = os.path.join(project_dir, 'empty_gloss_words.csv')

    print('Scanning Final_XML for sentences missing a last-word W…')
    rows = scan_xml_tree(final_xml_dir)

    fieldnames = ['category', 'language', 'xml_file', 'sentence_id',
                  's_form', 'last_token', 'num_tokens', 'num_W']
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f'Wrote {len(rows)} rows to {output_csv}')

    # Cross-reference with empty_gloss_words.csv
    empty_ids = load_empty_gloss_sentence_ids(empty_csv)
    if empty_ids:
        overlap = 0
        for row in rows:
            key = sentence_key_from_row(row)
            if key and key in empty_ids:
                overlap += 1
        print(f'\nOf {len(rows)} sentences with a missing last-word W,')
        print(f'  {overlap} also have at least one entry in empty_gloss_words.csv.')
    else:
        print(f'\n(Could not load {empty_csv} for cross-reference.)')


if __name__ == '__main__':
    main()
