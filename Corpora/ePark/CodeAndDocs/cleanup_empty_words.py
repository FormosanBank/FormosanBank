#!/usr/bin/env python3
"""
Cleanup script for jiu_jie_jiao_cai_nine_level_materials XML files.
Removes <W /> elements where:
1. The text contains no alphanumeric characters
2. There is no value for the 'file' attribute in the corresponding <AUDIO /> element

This script preserves original formatting to maintain git tracking.
"""

import os
import re
import xml.etree.ElementTree as ET
from pathlib import Path

def has_alphanumeric(text):
    """Check if text contains any alphanumeric characters."""
    if not text:
        return False
    return bool(re.search(r'[a-zA-Z0-9]', text))

def should_remove_word_element(w_element):
    """
    Determine if a <W> element should be removed based on criteria:
    1. Text contains no alphanumeric characters
    2. No 'file' attribute value in corresponding <AUDIO> element
    """
    # Check if the <FORM> text contains alphanumeric characters
    form_element = w_element.find('FORM')
    if form_element is not None and form_element.text:
        if has_alphanumeric(form_element.text):
            return False  # Has alphanumeric text, keep it
    
    # Check if there's an <AUDIO> element with a 'file' attribute
    audio_element = w_element.find('AUDIO')
    if audio_element is not None:
        file_attr = audio_element.get('file')
        if file_attr and file_attr.strip():
            return False  # Has audio file, keep it
    
    # If we get here, it has no alphanumeric text AND no audio file
    return True

def cleanup_xml_file(xml_path):
    """
    Clean up a single XML file by removing empty word elements.
    Preserves original formatting by only removing specific elements.
    Returns the number of elements removed.
    """
    try:
        # Read the original content
        with open(xml_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the XML to find elements to remove
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        w_ids_to_remove = []
        
        # Find all <W> elements that should be removed
        for w_element in root.findall('.//W'):
            if should_remove_word_element(w_element):
                w_id = w_element.get('id')
                if w_id:
                    w_ids_to_remove.append(w_id)
        
        if not w_ids_to_remove:
            return 0
        
        # Remove each element by finding its complete block in the content
        modified_content = content
        removed_count = 0
        
        for w_id in w_ids_to_remove:
            # Find the start of the W element with this ID
            # Look for pattern like: <W id="0-1"> or <W id="0-1" ...>
            start_pattern = rf'<W[^>]*\bid="{re.escape(w_id)}"[^>]*>'
            start_match = re.search(start_pattern, modified_content)
            
            if start_match:
                start_pos = start_match.start()
                
                # Find the matching closing </W> tag
                # We need to handle nested elements properly
                search_pos = start_match.end()
                tag_depth = 1
                
                while search_pos < len(modified_content) and tag_depth > 0:
                    # Find next < character
                    next_tag = modified_content.find('<', search_pos)
                    if next_tag == -1:
                        break
                    
                    # Check if it's an opening or closing W tag
                    if modified_content[next_tag:next_tag+3] == '<W ':
                        tag_depth += 1
                        search_pos = next_tag + 3
                    elif modified_content[next_tag:next_tag+4] == '</W>':
                        tag_depth -= 1
                        if tag_depth == 0:
                            end_pos = next_tag + 4
                            # Remove the entire W element including surrounding whitespace
                            element_text = modified_content[start_pos:end_pos]
                            
                            # Find the beginning of the line for proper indentation removal
                            line_start = modified_content.rfind('\n', 0, start_pos)
                            if line_start == -1:
                                line_start = 0
                            else:
                                line_start += 1
                            
                            # Check if the line only contains whitespace before our element
                            line_before_element = modified_content[line_start:start_pos]
                            if line_before_element.strip() == '':
                                # Remove from start of line to include indentation
                                start_pos = line_start
                                # Also check if there's a newline after to remove it
                                if end_pos < len(modified_content) and modified_content[end_pos] == '\n':
                                    end_pos += 1
                            
                            # Remove the element
                            modified_content = modified_content[:start_pos] + modified_content[end_pos:]
                            removed_count += 1
                            break
                        else:
                            search_pos = next_tag + 4
                    else:
                        search_pos = next_tag + 1
        
        if removed_count > 0:
            # Write back the modified content
            with open(xml_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"  Removed {removed_count} empty word elements from {xml_path.name}")
        
        return removed_count
        
    except ET.ParseError as e:
        print(f"  Error parsing {xml_path}: {e}")
        return 0
    except Exception as e:
        print(f"  Error processing {xml_path}: {e}")
        return 0

def main():
    """
    Main function to process all XML files in jiu_jie_jiao_cai_nine_level_materials.
    """
    # Define the target directory
    target_dir = Path('./Final_XML/jiu_jie_jiao_cai_nine_level_materials')
    
    if not target_dir.exists():
        print(f"Target directory does not exist: {target_dir}")
        return
    
    print(f"Starting cleanup of XML files in {target_dir}...")
    
    # Find all XML files in the target directory
    xml_files = list(target_dir.glob('**/*.xml'))
    
    if not xml_files:
        print("No XML files found in the target directory.")
        return
    
    print(f"Found {len(xml_files)} XML files to process.")
    
    total_removed = 0
    processed_files = 0
    
    # Process each XML file
    for xml_file in xml_files:
        print(f"Processing: {xml_file.relative_to(target_dir)}")
        removed_count = cleanup_xml_file(xml_file)
        total_removed += removed_count
        processed_files += 1
        
        if processed_files % 10 == 0:
            print(f"  Progress: {processed_files}/{len(xml_files)} files processed")
    
    print(f"\nCleanup complete!")
    print(f"Processed {processed_files} XML files")
    print(f"Removed {total_removed} empty word elements total")
    
    if total_removed > 0:
        print(f"\nNote: {total_removed} <W> elements were removed because they contained")
        print("only non-alphanumeric text and had no corresponding audio files.")

if __name__ == "__main__":
    main()