#!/usr/bin/env python3
"""
run_parsers.py

Wrapper that:
  1. Runs parse_stories.py, parse_grammar.py, parse_sentences.py in sequence.
  2. Scans every generated Final_XML file for sentences whose final <W> has
     no non-empty <TRANSL> elements (i.e., the last word is unglossed).
  3. For each such sentence, strips all <TRANSL> and <M> children from every
     <W> in that sentence, leaving bare <W><FORM>…</FORM></W> shells.
  4. Rewrites the affected XML files in-place and logs every stripped sentence
     to sentences_with_bad_glosses_removed.csv.
"""

import csv
import os
import subprocess
import sys
from xml.dom import minidom
from xml.etree import ElementTree as ET

# ── Paths ──────────────────────────────────────────────────────────────────────
HERE      = os.path.dirname(os.path.abspath(__file__))  # scripts/
ROOT      = os.path.dirname(HERE)                        # project root
FINAL_XML = os.path.join(ROOT, 'Final_XML')
LOG_PATH  = os.path.join(ROOT, 'sentences_with_bad_glosses_removed.csv')

# ── Namespace ──────────────────────────────────────────────────────────────────
# The 'xml' prefix is pre-registered in ElementTree, but be explicit so
# round-tripping xml:lang attributes writes 'xml:lang' not a Clark-notation key.
ET.register_namespace('xml', 'http://www.w3.org/XML/1998/namespace')


# ── Helpers ────────────────────────────────────────────────────────────────────
def _strip_whitespace_nodes(elem):
    """Recursively remove whitespace-only text/tail from a parsed element tree.

    When ElementTree reads a prettified XML file it preserves the existing
    indentation in .text/.tail.  If we then run toprettyxml it adds another
    layer, producing double blank lines.  Clearing whitespace-only strings
    before serialising avoids this.
    """
    if elem.text and not elem.text.strip():
        elem.text = None
    if elem.tail and not elem.tail.strip():
        elem.tail = None
    for child in elem:
        _strip_whitespace_nodes(child)


def prettify(elem):
    """Return a pretty-printed XML string matching the parsers' output style."""
    _strip_whitespace_nodes(elem)
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='    ')


def w_has_nonempty_transl(w_elem):
    """Return True if w_elem has at least one non-empty <TRANSL> child."""
    for t in w_elem.findall('TRANSL'):
        if (t.text or '').strip():
            return True
    return False


# ── Parser runner ──────────────────────────────────────────────────────────────
def run_parsers():
    for script in ('parse_stories.py', 'parse_grammar.py', 'parse_sentences.py'):
        path = os.path.join(HERE, script)
        print(f'\n=== Running {script} ===')
        sys.stdout.flush()
        result = subprocess.run([sys.executable, path], cwd=ROOT)
        if result.returncode != 0:
            print(f'ERROR: {script} exited with code {result.returncode}',
                  file=sys.stderr)
            sys.exit(result.returncode)


# ── Clean-up pass ──────────────────────────────────────────────────────────────
def cleanup_xml_file(xml_path, category, language, log_rows):
    """Strip W-level glosses and M elements from sentences with an unglossed
    final word.  Returns True if the file was modified."""
    try:
        tree = ET.parse(xml_path)
    except ET.ParseError as e:
        print(f'  WARNING: cannot parse {xml_path}: {e}', file=sys.stderr)
        return False

    root = tree.getroot()
    modified = False

    for s_elem in root.iter('S'):
        ws = list(s_elem.findall('W'))
        if not ws:
            continue
        # If the last W already has at least one non-empty TRANSL, skip.
        if w_has_nonempty_transl(ws[-1]):
            continue

        # Last W is unglossed → strip all TRANSL and M from every W in sentence.
        s_id      = s_elem.get('id', '')
        last_form = (ws[-1].findtext('FORM') or '').strip()
        n_words   = len(ws)

        for w in ws:
            for tag in ('TRANSL', 'M'):
                for child in list(w.findall(tag)):
                    w.remove(child)

        log_rows.append({
            'category':    category,
            'language':    language,
            'file':        os.path.basename(xml_path),
            'sentence_id': s_id,
            'n_words':     n_words,
            'last_w_form': last_form,
        })
        modified = True

    if modified:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(prettify(root))

    return modified


def run_cleanup():
    print('\n=== Clean-up pass: stripping sentences with unglossed final word ===')
    log_rows = []
    files_modified = 0

    for category in ('Grammar', 'Sentences', 'Stories'):
        cat_dir = os.path.join(FINAL_XML, category)
        if not os.path.isdir(cat_dir):
            continue
        for lang_dir in sorted(os.listdir(cat_dir)):
            full_dir = os.path.join(cat_dir, lang_dir)
            if not os.path.isdir(full_dir):
                continue
            for fname in sorted(os.listdir(full_dir)):
                if not fname.endswith('.xml'):
                    continue
                path = os.path.join(full_dir, fname)
                if cleanup_xml_file(path, category, lang_dir, log_rows):
                    files_modified += 1

    fieldnames = ['category', 'language', 'file', 'sentence_id',
                  'n_words', 'last_w_form']
    with open(LOG_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(log_rows)

    from collections import Counter
    print(f'Stripped {len(log_rows)} sentences across {files_modified} files '
          f'→ {LOG_PATH}')
    for cat, n in sorted(Counter(r['category'] for r in log_rows).items()):
        print(f'  {cat}: {n}')


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    run_parsers()
    run_cleanup()
