#!/usr/bin/env python3
"""
validate_glosses.py - Validate XML gloss structure

Usage: python validate_glosses.py <xml_folder> [--check_morpho]

Checks XML files recursively for:
- Number of words in <S> text vs number of <W> elements  
- Optional: Whether each <W> contains at least one <M> element
- Morpheme count mismatch: number of <M> elements vs morphemes implied by <W> FORM
  (logged to a separate CSV)
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET


def count_words(text):
    """Count words in text using whitespace splitting."""
    if not text:
        return 0
    # Clean up whitespace and split
    words = re.split(r'\s+', text.strip())
    # Filter out empty strings
    return len([w for w in words if w])


def extract_s_direct_text(s_element):
    """
    Extract the direct text content of an S element from its FORM element,
    preferring the original form.
    """
    # Look for the original form first
    original_form = s_element.find('./FORM[@kindOf="original"]')
    if original_form is not None and original_form.text:
        return original_form.text.strip()
    
    # Fallback to any FORM element
    any_form = s_element.find('./FORM')
    if any_form is not None and any_form.text:
        return any_form.text.strip()
    
    # Last resort: any direct text content (excluding child elements)
    text = s_element.text if s_element.text else ""
    return text.strip()


def count_morphemes_from_form(form_text):
    """
    Count the number of morphemes implied by a W FORM string.

    Rules:
    - Each <...> group is one infix morpheme.
    - After removing infix groups, split the remainder on '-' and '=' to get
      the remaining morpheme segments.
    - Total = number of infix groups + number of non-empty segments.

    Examples:
      'ka'        -> 1
      'ika-doa'   -> 2
      'k-anak-an' -> 3
      'ma=luhay'  -> 2
      'k<um>ita'  -> 2  (infix 'um' + root 'kita')
    """
    if not form_text:
        return 0

    # Count and remove infix groups <...>
    infixes = re.findall(r'<[^>]+>', form_text)
    n_infixes = len(infixes)
    remainder = re.sub(r'<[^>]+>', '', form_text)

    # Split remainder on morpheme boundary markers - and =
    segments = re.split(r'[-=]', remainder)
    n_segments = len([s for s in segments if s])  # ignore empty segments

    return n_infixes + n_segments


def get_w_form(w_element):
    """Return the original FORM text of a W element, or any FORM as fallback."""
    original = w_element.find('./FORM[@kindOf="original"]')
    if original is not None and original.text:
        return original.text.strip()
    any_form = w_element.find('./FORM')
    if any_form is not None and any_form.text:
        return any_form.text.strip()
    return ''


def validate_morpheme_counts_file(xml_file, debug=False):
    """
    Check that the number of <M> elements in each <W> matches the number of
    morphemes implied by the W's FORM (via '-', '=', and '<>' notation).

    Skipped cases (not an error):
    - W implies exactly 1 morpheme AND has 0 M elements  (monomorphemic, M optional)

    Returns list of tuples:
        (filename, s_id, w_id, w_form, expected_m_count, actual_m_count)
    """
    errors = []

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Warning: Could not parse {xml_file}: {e}")
        return errors

    for s_elem in root.findall('.//S[@id]'):
        s_id = s_elem.get('id')
        for w_elem in s_elem.findall('./W'):
            w_id = w_elem.get('id', '')
            form_text = get_w_form(w_elem)
            expected = count_morphemes_from_form(form_text)
            actual = len(w_elem.findall('./M'))

            if debug:
                print(f"  S[{s_id}] W[{w_id}] form='{form_text}' expected={expected} actual={actual}")

            # Monomorphemic word with no M tags is acceptable
            if expected == 1 and actual == 0:
                continue

            if expected != actual:
                errors.append((str(xml_file), s_id, w_id, form_text, expected, actual))

    return errors


def validate_xml_file(xml_file, check_morpho=False, debug=False):
    """
    Validate a single XML file and return a list of validation errors.
    
    Returns list of tuples: (filename, s_id, word_count, w_count, has_morphemes)
    """
    errors = []
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Warning: Could not parse {xml_file}: {e}")
        return errors
    
    # Find all S elements with id attributes
    s_elements = root.findall('.//S[@id]')
    
    for s_elem in s_elements:
        s_id = s_elem.get('id')
        
        # Extract direct text content from S element's FORM
        s_text = extract_s_direct_text(s_elem)
        word_count = count_words(s_text)
        
        # Count W elements within this S (direct children only)
        w_elements = s_elem.findall('./W')
        w_count = len(w_elements)
        
        # Debug: Also check for any nested W elements (which shouldn't exist)
        nested_w = s_elem.findall('.//W')  # All W descendants
        if len(nested_w) != w_count:
            print(f"  Warning: Found {len(nested_w)} total W elements but {w_count} direct children in S[@id='{s_id}']")
        
        if debug:
            print(f"  S[@id='{s_id}']: text='{s_text}' words={word_count}, W_elements={w_count}")
            if w_elements:
                for i, w in enumerate(w_elements):
                    w_text = ET.tostring(w, encoding='unicode', method='text').strip()
                    m_count = len(w.findall('./M'))
                    print(f"    W[{i}]: '{w_text}' (M elements: {m_count})")
        
        has_morphemes = None
        if check_morpho:
            # Check if any W element lacks M children
            w_without_m = any(len(w.findall('./M')) == 0 for w in w_elements)
            has_morphemes = 'F' if w_without_m else 'T'
        
        # Log if word count doesn't match W count, or if checking morphemes and found issues
        should_log = (word_count != w_count) or (check_morpho and has_morphemes == 'F')
        
        if should_log:
            errors.append((str(xml_file), s_id, word_count, w_count, has_morphemes))
    
    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate XML gloss structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_glosses.py /path/to/xml/files
  python validate_glosses.py /path/to/xml/files --check_morpho
        """
    )
    
    parser.add_argument('xml_folder', 
                       help='Folder containing XML files to validate (searches recursively)')
    parser.add_argument('--check_morpho', action='store_true',
                       help='Check if each W element has at least one M element')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output showing detailed parsing information')
    parser.add_argument('--output_dir',
                       help='Directory for validation CSV outputs. Defaults to the current working directory.')
    
    args = parser.parse_args()
    
    # Validate input folder
    xml_folder = Path(args.xml_folder)
    if not xml_folder.exists() or not xml_folder.is_dir():
        print(f"Error: Directory '{xml_folder}' does not exist")
        sys.exit(1)
    
    # Setup output CSVs
    output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)
    w_csv_file = output_dir / 'validation_results.csv'
    m_csv_file = output_dir / 'validation_m_mismatches.csv'

    print(f"Validating XML files in: {xml_folder}")
    print(f"Check morphemes (W missing M): {args.check_morpho}")
    print(f"W-mismatch output: {w_csv_file}")
    print(f"M-mismatch output: {m_csv_file}")
    print()

    # Find all XML files recursively
    xml_files = list(xml_folder.rglob('*.xml'))

    if not xml_files:
        print(f"No XML files found in {xml_folder}")
        return

    all_w_errors = []
    all_m_errors = []

    # Process each XML file
    for xml_file in xml_files:
        print(f"Processing: {xml_file}")

        file_w_errors = validate_xml_file(xml_file, args.check_morpho, args.debug)
        if file_w_errors:
            print(f"  Found {len(file_w_errors)} W-count mismatch(es)")
            all_w_errors.extend(file_w_errors)

        file_m_errors = validate_morpheme_counts_file(xml_file, args.debug)
        if file_m_errors:
            print(f"  Found {len(file_m_errors)} M-count mismatch(es)")
            all_m_errors.extend(file_m_errors)

    # Write W-mismatch CSV
    if all_w_errors:
        with open(w_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if args.check_morpho:
                writer.writerow(['filename', 's_id', 'word_count', 'w_element_count', 'has_morphemes'])
            else:
                writer.writerow(['filename', 's_id', 'word_count', 'w_element_count'])
            for error in all_w_errors:
                if args.check_morpho:
                    writer.writerow(error)
                else:
                    writer.writerow(error[:-1])
        print(f"\nW-mismatch results saved to: {w_csv_file} ({len(all_w_errors)} error(s))")
    else:
        print(f"\nNo W-count mismatches found.")

    # Write M-mismatch CSV
    if all_m_errors:
        with open(m_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 's_id', 'w_id', 'w_form', 'expected_m_count', 'actual_m_count'])
            writer.writerows(all_m_errors)
        print(f"M-mismatch results saved to: {m_csv_file} ({len(all_m_errors)} error(s))")
    else:
        print(f"No M-count mismatches found.")

    print(f"\nValidation complete! Files processed: {len(xml_files)}")


if __name__ == '__main__':
    main()
