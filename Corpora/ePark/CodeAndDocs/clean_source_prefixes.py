#!/usr/bin/env python3
"""
Remove ePark1/ePark2/ePark3 prefixes from source attributes in XML files
"""

import os
import re
from pathlib import Path
from lxml import etree

def clean_source_attribute(xml_file):
    """Clean the source attribute in a single XML file"""
    try:
        # Parse the XML file
        tree = etree.parse(xml_file)
        root = tree.getroot()
        
        # Find the TEXT element (should be root)
        if root.tag == 'TEXT' and 'source' in root.attrib:
            original_source = root.attrib['source']
            
            # Remove ePark1/2/3 prefix if present
            cleaned_source = re.sub(r'^ePark[123]\s+', '', original_source)
            
            if cleaned_source != original_source:
                root.attrib['source'] = cleaned_source
                
                # Write back to file with proper XML formatting
                tree.write(xml_file, encoding='utf-8', xml_declaration=True, pretty_print=True)
                print(f"Updated {xml_file}")
                print(f"  Before: {original_source}")
                print(f"  After:  {cleaned_source}")
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
        if clean_source_attribute(xml_file):
            updated_count += 1
    
    print(f"\nCompleted: Updated {updated_count} out of {len(xml_files)} files")

if __name__ == "__main__":
    main()