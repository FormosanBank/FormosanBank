#!/usr/bin/env python3
"""
Script to update XML file id attributes to follow the pattern:
{folder_two_levels_up}_{filename}

For example:
Final_XML/hui_ben_ping_tai_picture_book_platform/Amis/Coastal_Amis.xml
-> id="hui_ben_ping_tai_picture_book_platform_Coastal_Amis"
"""

import os
from pathlib import Path
from lxml import etree

def update_xml_id(file_path):
    """Update the id attribute in the TEXT element of an XML file."""
    try:
        # Parse the file path to get components
        path = Path(file_path)
        filename_without_ext = path.stem
        
        # Get the folder two levels up from the file
        # file_path structure: Final_XML/folder_two_levels_up/language_folder/filename.xml
        parts = path.parts
        if len(parts) >= 4 and parts[0] == 'Final_XML':
            folder_two_levels_up = parts[1]
        else:
            print(f"Warning: Unexpected path structure for {file_path}")
            return False
        
        # Construct the new id
        new_id = f"{folder_two_levels_up}_{filename_without_ext}"
        
        # Parse the XML file
        parser = etree.XMLParser(strip_cdata=False)
        tree = etree.parse(file_path, parser)
        root = tree.getroot()
        
        # Find the TEXT element (should be the root)
        if root.tag == 'TEXT':
            current_id = root.get('id')
            if current_id != new_id:
                print(f"Updating {file_path}")
                print(f"  Old id: {current_id}")
                print(f"  New id: {new_id}")
                
                # Update the id attribute
                root.set('id', new_id)
                
                # Write the file back with proper formatting
                tree.write(file_path, encoding='UTF-8', xml_declaration=True, pretty_print=True)
                return True
            else:
                print(f"Already correct: {file_path}")
                return False
        else:
            print(f"Warning: No TEXT root element found in {file_path}")
            return False
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Update all XML files in the Final_XML directory."""
    xml_files = list(Path('Final_XML').glob('**/*.xml'))
    
    print(f"Found {len(xml_files)} XML files to process")
    print("=" * 50)
    
    updated_count = 0
    for xml_file in sorted(xml_files):
        if update_xml_id(xml_file):
            updated_count += 1
    
    print("=" * 50)
    print(f"Updated {updated_count} out of {len(xml_files)} files")

if __name__ == '__main__':
    main()