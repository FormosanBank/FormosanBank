#!/usr/bin/env python3
"""
Helper function to standardize punctuation spacing in FORM and PHON elements across all XML files.

Rules:
1. Remove whitespace before "?", "!", ",", and "."
2. Add whitespace after "?", "!", ",", and "." (unless it's the final character or followed by punctuation)

"!" is handled here, parallel to "?", so that ePark1/2 outputs (whose generator
ePark1and2.py does no text cleaning) receive the same sentence-punctuation
spacing as ePark3 outputs (whose ePark3.py clean_text() already splits
run-together sentences on "!"). This pass runs over all of Final_XML, so it is
the single authoritative, uniform punctuation-spacing step. By the time it runs,
clean_xml.py has already mapped full-width "！" and other typographic punctuation
to ASCII, so only ASCII forms need to be matched here.
"""

import os
import xml.etree.ElementTree as ET
import re
from pathlib import Path

def fix_punctuation_spacing(text):
    """
    Fix punctuation spacing according to the rules:
    1. Remove whitespace at the beginning of text
    2. Remove whitespace at the end of text
    3. Remove whitespace before "?", "!", ",", "."
    4. Replace " : " with ": " (remove space before colon)
    5. Add whitespace after "?", "!", ",", and "." (unless it's the final character or followed by punctuation)
    """
    if not text:
        return text

    # Remove whitespace at the beginning and end of text
    text = text.strip()

    # Remove whitespace before "?", "!", ",", and "."
    text = re.sub(r'\s+([?!,.])(?!\d)', r'\1', text)  # Don't remove space before . in numbers

    # Replace " : " with ": " (remove space before colon)
    text = re.sub(r'\s+:\s*"', ': "', text)

    # Replace ",:" with ":" (remove comma before colon)
    text = re.sub(r',:(?=\s*")', ':', text)

    # Add whitespace after "?" if not already present and not at end of string
    # and not followed by common punctuation marks
    text = re.sub(r'\?(?!\s|$|["\')\]\},.;:])', '? ', text)

    # Add whitespace after "!" (parallel to "?") if not already present and not
    # at end of string and not followed by common punctuation marks
    text = re.sub(r'!(?!\s|$|["\')\]\},.;:])', '! ', text)

    # Add whitespace after "," if not already present and not at end of string
    # and not followed by common punctuation marks
    text = re.sub(r',(?!\s|$|["\')\]\}?,.;:])', ', ', text)
    
    # Add whitespace after "." if not already present and not at end of string
    # and not followed by common punctuation marks or digits (for decimals)
    text = re.sub(r'\.(?!\s|$|["\')\]\}?,.;:]|\d)', '. ', text)

    # In Formosan orthographies the apostrophe (and IPA ʔ/ʡ in PHON) is a
    # glottal-stop LETTER that can begin a word, not a closing quote. The rules
    # above exclude it as closing punctuation, so a sentence mark running
    # straight into a glottal-initial word (e.g. source "akən!'aijaŋa") is left
    # merged. Add the missing space when a glottal stop directly follows ? ! , .
    # and itself begins a word.
    text = re.sub(r"([?!,.])(?=['’ʔʡ][^\W\d_])", r'\1 ', text)
    
    return text

def process_xml_file(file_path):
    """Process a single XML file and fix punctuation spacing in FORM and PHON elements."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Track if any changes were made
        changes_made = False
        
        # Find all FORM and PHON elements
        for element in root.iter():
            if element.tag in ['FORM', 'PHON'] and element.text:
                original_text = element.text
                fixed_text = fix_punctuation_spacing(original_text)
                
                if original_text != fixed_text:
                    element.text = fixed_text
                    changes_made = True
                    print(f"  Fixed {element.tag}: '{original_text}' -> '{fixed_text}'")
        
        # Save the file if changes were made
        if changes_made:
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            print(f"Updated: {file_path}")
            return True
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def process_all_xml_files(final_xml_dir):
    """Process all XML files in the Final_XML directory."""
    final_xml_path = Path(final_xml_dir)
    
    if not final_xml_path.exists():
        print(f"Error: Directory {final_xml_dir} does not exist")
        return
    
    print(f"Processing XML files in {final_xml_dir}...")
    
    # Find all XML files
    xml_files = list(final_xml_path.rglob('*.xml'))
    
    if not xml_files:
        print("No XML files found")
        return
    
    print(f"Found {len(xml_files)} XML files")
    
    files_changed = 0
    files_processed = 0
    
    for xml_file in xml_files:
        files_processed += 1
        if files_processed % 50 == 0:
            print(f"Processed {files_processed}/{len(xml_files)} files...")
        
        print(f"Processing: {xml_file.relative_to(final_xml_path)}")
        if process_xml_file(xml_file):
            files_changed += 1
    
    print(f"\nSummary:")
    print(f"  Files processed: {files_processed}")
    print(f"  Files changed: {files_changed}")
    print(f"  Files unchanged: {files_processed - files_changed}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix punctuation spacing in FORM and PHON elements')
    parser.add_argument('--final_xml_dir', default='Final_XML', 
                       help='Path to the Final_XML directory (default: Final_XML)')
    parser.add_argument('--test', action='store_true',
                       help='Test mode - show what would be changed without making changes')
    
    args = parser.parse_args()
    
    if args.test:
        print("TEST MODE: No files will be modified")
        # You could add a dry-run mode here if needed
    
    process_all_xml_files(args.final_xml_dir)

if __name__ == "__main__":
    main()