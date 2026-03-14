#!/usr/bin/env python3
"""
Replace Chinese prefixes in AUDIO file attributes with English folder names
"""

import os
import re
from pathlib import Path
from lxml import etree

def get_folder_two_levels_up(xml_file_path):
    """Get the folder name that is two levels up from the XML file"""
    # Convert to Path object for easier manipulation
    path = Path(xml_file_path)
    
    # Go up two levels: XML file -> language folder -> category folder
    if len(path.parts) >= 3:
        return path.parts[-3]  # Third from the end
    return None

def extract_chinese_prefix(filename):
    """Extract only the Chinese characters from the beginning of a filename"""
    # Find the first non-Chinese character (or underscore after Chinese chars)
    chinese_match = re.match(r'[\u4e00-\u9fff]+', filename)
    if chinese_match:
        return chinese_match.group()
    return ""

def clean_audio_file_attributes(xml_file):
    """Clean the file attributes in AUDIO tags for a single XML file"""
    try:
        # Get the category folder name (2 levels up)
        category_folder = get_folder_two_levels_up(xml_file)
        if not category_folder:
            print(f"Cannot determine category folder for {xml_file}")
            return False
        
        # Parse the XML file
        tree = etree.parse(xml_file)
        root = tree.getroot()
        
        # Find all AUDIO elements
        audio_elements = root.xpath('.//AUDIO[@file]')
        
        if not audio_elements:
            print(f"No AUDIO elements found in {xml_file}")
            return False
        
        updated = False
        
        for audio in audio_elements:
            original_file = audio.get('file')
            
            # Extract the Chinese prefix
            chinese_prefix = extract_chinese_prefix(original_file)
            
            # Handle two cases: 
            # 1. Files with Chinese prefix that need to be replaced
            # 2. Files that already have English folder name but with "/" instead of "_"
            
            if chinese_prefix and re.search(r'[\u4e00-\u9fff]', chinese_prefix):
                # Case 1: Replace Chinese prefix with English folder name
                remainder = original_file[len(chinese_prefix):]
                # Remove leading underscore if present to avoid double underscores
                if remainder.startswith('_'):
                    remainder = remainder[1:]
                new_file = f"{category_folder}_{remainder}"
            elif '/' in original_file and original_file.startswith(category_folder + '/'):
                # Case 2: Replace "/" with "_" in existing English folder names
                new_file = original_file.replace('/', '_')
            else:
                # No changes needed
                continue
            
            if new_file != original_file:
                audio.set('file', new_file)
                print(f"  Updated: {original_file} -> {new_file}")
                updated = True
        
        if updated:
            # Write back to file with proper XML formatting
            tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
            print(f"Updated {xml_file}")
            return True
        else:
            print(f"No changes needed: {xml_file}")
            return False
            
    except Exception as e:
        print(f"Error processing {xml_file}: {e}")
        return False

def main():
    final_xml_dir = Path("Final_XML")
    
    if not final_xml_dir.exists():
        print(f"Directory {final_xml_dir} not found!")
        return
    
    # Find all XML files
    xml_files = list(final_xml_dir.rglob("*.xml"))
    print(f"Found {len(xml_files)} XML files")
    
    updated_count = 0
    
    for xml_file in xml_files:
        print(f"\nProcessing: {xml_file}")
        if clean_audio_file_attributes(xml_file):
            updated_count += 1
    
    print(f"\nCompleted: Updated {updated_count} out of {len(xml_files)} files")

if __name__ == "__main__":
    main()