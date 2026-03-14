#!/usr/bin/env python3
"""
validate_glosses.py - Validate XML gloss structure

Usage: python validate_glosses.py <xml_folder> [--check_morpho]

Checks XML files recursively for:
- Number of words in <S> text vs number of <W> elements  
- Optional: Whether each <W> contains at least one <M> element
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
    
    args = parser.parse_args()
    
    # Validate input folder
    xml_folder = Path(args.xml_folder)
    if not xml_folder.exists() or not xml_folder.is_dir():
        print(f"Error: Directory '{xml_folder}' does not exist")
        sys.exit(1)
    
    # Setup output CSV
    csv_file = Path('validation_results.csv')
    
    print(f"Validating XML files in: {xml_folder}")
    print(f"Check morphemes: {args.check_morpho}")
    print(f"Output file: {csv_file}")
    print()
    
    # Find all XML files recursively
    xml_files = list(xml_folder.rglob('*.xml'))
    
    if not xml_files:
        print(f"No XML files found in {xml_folder}")
        return
    
    all_errors = []
    
    # Process each XML file
    for xml_file in xml_files:
        print(f"Processing: {xml_file}")
        
        file_errors = validate_xml_file(xml_file, args.check_morpho, args.debug)
        
        if file_errors:
            print(f"  Found {len(file_errors)} validation error(s)")
            all_errors.extend(file_errors)
    
    # Write results to CSV
    if all_errors:
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            if args.check_morpho:
                writer.writerow(['filename', 's_id', 'word_count', 'w_element_count', 'has_morphemes'])
            else:
                writer.writerow(['filename', 's_id', 'word_count', 'w_element_count'])
            
            # Write error records
            for error in all_errors:
                if args.check_morpho:
                    writer.writerow(error)
                else:
                    writer.writerow(error[:-1])  # Exclude has_morphemes column
        
        print(f"\nValidation complete!")
        print(f"Files processed: {len(xml_files)}")
        print(f"Total errors found: {len(all_errors)}")
        print(f"Results saved to: {csv_file}")
        
        print(f"\nSummary of errors:")
        print(f"  Total error records: {len(all_errors)}")
        
    else:
        print(f"\nValidation complete!")
        print(f"Files processed: {len(xml_files)}")
        print(f"No validation errors found!")


if __name__ == '__main__':
    main()