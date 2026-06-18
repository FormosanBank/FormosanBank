"""
filter_validation.py

Filters a validation results CSV produced by validate_glosses.py,
removing rows that are uninteresting for manual review.

Currently removes:
  - w_element_count == 0
    (Sentences with no <W> elements have nothing to compare against.
     Grammar A2 sections are vocabulary wordlists — no <W> by design.
     Stories: L2 code-switched utterances have a correct <FORM> but no
     morphological breakdown, which is linguistically appropriate.)

Also separates into clitics.csv:
  - word_count > w_element_count AND the difference equals the total number of
    '=' characters across all <W><FORM> values in the sentence.
    These are cases where a host word and its clitic are written as two separate
    tokens in the <S><FORM> string but combined with '=' in the gloss <W> element.
    These are not errors; they are passed to the corpus maintainer separately.

Usage:
    python scripts/filter_validation.py validation_results.csv
    python scripts/filter_validation.py validation_results.csv --output filtered.csv
    python scripts/filter_validation.py validation_results.csv --clitics clitics.csv
"""

import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET


def _count_equals_in_sentence(filename, s_id, base_dir, xml_cache):
    """
    Return the total number of '=' characters across all <W><FORM> texts in the
    given sentence, loading and caching the XML tree as needed.
    Returns None if the sentence cannot be found.
    """
    if filename not in xml_cache:
        xml_path = os.path.join(base_dir, filename)
        try:
            xml_cache[filename] = ET.parse(xml_path).getroot()
        except (FileNotFoundError, ET.ParseError):
            xml_cache[filename] = None

    root = xml_cache[filename]
    if root is None:
        return None

    s_elem = next((s for s in root.iter('S') if s.get('id') == s_id), None)
    if s_elem is None:
        return None

    return sum(
        (w.find('FORM').text or '').count('=')
        for w in s_elem.findall('W')
        if w.find('FORM') is not None
    )


def filter_rows(rows, base_dir):
    """
    Return (kept, removed_trivial, clitics).

    kept            – rows that need manual review
    removed_trivial – rows silently dropped (no <W> elements)
    clitics         – rows whose mismatch is entirely explained by host=clitic
                      joining in the gloss <W> forms
    """
    kept = []
    removed_trivial = []
    clitics = []
    xml_cache = {}

    for r in rows:
        word_count = int(r['word_count'])
        w_count    = int(r['w_element_count'])

        # Sentences with no <W> elements are uninteresting: Grammar A2 sections
        # are vocabulary wordlists (no <W> by design); Stories L2 utterances
        # have a correct <FORM> but no morphological breakdown (appropriate);
        # Sentences entries simply had no gloss data.
        if w_count == 0:
            removed_trivial.append(r)
            continue

        # Clitic mismatch: S FORM splits host+clitic as two tokens, but the gloss
        # <W> joins them with '='.  The count of '=' in all W FORMs exactly
        # accounts for the word/W discrepancy.
        diff = word_count - w_count
        if diff > 0:
            eq_count = _count_equals_in_sentence(
                r['filename'], r['s_id'], base_dir, xml_cache
            )
            if eq_count is not None and diff == eq_count:
                clitics.append(r)
                continue

        kept.append(r)

    return kept, removed_trivial, clitics


def main():
    parser = argparse.ArgumentParser(description="Filter a validation results CSV.")
    parser.add_argument("input", help="Input CSV file (e.g. validation_results.csv)")
    parser.add_argument("--output", "-o", help="Output CSV file (default: overwrite input)")
    parser.add_argument(
        "--clitics", "-c",
        help="Output CSV for clitic-mismatch rows (default: clitics.csv next to input)"
    )
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.abspath(args.input))

    with open(args.input, newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    kept, removed_trivial, clitics = filter_rows(rows, base_dir)

    output_path  = args.output  or args.input
    clitics_path = args.clitics or os.path.join(base_dir, "clitics.csv")

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    with open(clitics_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(clitics)

    print(f"Removed {len(removed_trivial)} trivially uninteresting rows.")
    print(f"Moved   {len(clitics)} clitic-mismatch rows → {clitics_path}")
    print(f"Kept    {len(kept)} rows → {output_path}")


if __name__ == "__main__":
    main()
