#!/usr/bin/env python3
"""
Script to remove hyphens from FORM elements with kindOf="standard" 
in S and W elements within RauDong XML files.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

def remove_hyphens_from_file(xml_path):
    """Process a single XML file to remove hyphens from standard forms."""
    try:
        # Parse the XML file
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Track changes made
        changes_made = 0
        
        # Find all S and W elements
        for element in root.findall('.//S') + root.findall('.//W'):
            # Find FORM elements with kindOf="standard" within S and W elements
            standard_forms = element.findall('.//FORM[@kindOf="standard"]')
            
            for form in standard_forms:
                if form.text and '-' in form.text:
                    original_text = form.text
                    form.text = form.text.replace('-', '')
                    changes_made += 1
                    print(f"  {original_text} → {form.text}")
        
        # Save the modified XML if changes were made
        if changes_made > 0:
            tree.write(xml_path, encoding='utf-8', xml_declaration=True)
            print(f"Removed hyphens from {changes_made} standard forms in {xml_path}")
        
        return changes_made
        
    except Exception as e:
        print(f"Error processing {xml_path}: {e}")
        return 0

def main():
    """Process all XML files in the RauDong directory."""
    base_dir = Path("Corpora/RauDong/XML")
    
    if not base_dir.exists():
        print(f"Directory {base_dir} does not exist")
        return
    
    total_changes = 0
    files_processed = 0
    
    # Process XML files in the main directory and all subdirectories
    for xml_file in base_dir.rglob("*.xml"):
        print(f"\nProcessing {xml_file}...")
        changes = remove_hyphens_from_file(xml_file)
        total_changes += changes
        files_processed += 1
    
    print(f"\nSummary:")
    print(f"Files processed: {files_processed}")
    print(f"Total hyphen removals: {total_changes}")

if __name__ == "__main__":
    main()