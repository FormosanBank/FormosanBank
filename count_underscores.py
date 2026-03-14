#!/usr/bin/env python3
"""
Script to count underscore characters (_) in XML files from the Corpora directory.
Reads text from <S> elements where kindOf="original" and counts underscores.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

def count_underscores_in_xml(xml_file_path):
    """
    Count underscore characters in a single XML file.
    
    Args:
        xml_file_path (str): Path to the XML file
    
    Returns:
        int: Number of underscore characters found
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        underscore_count = 0
        
        # Find all <S> elements
        for s_element in root.findall('.//S'):
            # Find <FORM> elements with kindOf="original" within this S element
            for form_element in s_element.findall('.//FORM[@kindOf="original"]'):
                if form_element.text:
                    underscore_count += form_element.text.count('_')
        
        return underscore_count
    
    except ET.ParseError as e:
        print(f"Error parsing XML file {xml_file_path}: {e}")
        return 0
    except Exception as e:
        print(f"Error processing file {xml_file_path}: {e}")
        return 0

def main():
    """Main function to process all XML files in the Corpora directory."""
    
    # Define the base Corpora directory
    corpora_dir = Path("/Users/jkhartshorne/Documents/Projects/Formosan/FormosanBank/Corpora")
    
    if not corpora_dir.exists():
        print(f"Corpora directory not found: {corpora_dir}")
        return
    
    total_underscores = 0
    total_files = 0
    results = []
    
    print("Processing XML files in Corpora directory...")
    print("=" * 60)
    
    # Walk through all subdirectories and find XML files
    for xml_file in corpora_dir.rglob("*.xml"):
        file_underscores = count_underscores_in_xml(xml_file)
        total_underscores += file_underscores
        total_files += 1
        
        # Store results for detailed output
        relative_path = xml_file.relative_to(corpora_dir)
        results.append((str(relative_path), file_underscores))
        
        # Print progress every 100 files
        if total_files % 100 == 0:
            print(f"Processed {total_files} files...")
    
    # Sort results by underscore count (descending) for more interesting output
    results.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\nProcessing complete!")
    print("=" * 60)
    print(f"Total XML files processed: {total_files}")
    print(f"Total underscore characters found: {total_underscores}")
    print(f"Average underscores per file: {total_underscores / total_files:.2f}" if total_files > 0 else "No files processed")
    
    print(f"\nTop 10 files with most underscores:")
    print("-" * 60)
    for i, (file_path, count) in enumerate(results[:10]):
        print(f"{i+1:2d}. {file_path}: {count} underscores")
    
    print(f"\nFiles with no underscores: {sum(1 for _, count in results if count == 0)}")
    print(f"Files with underscores: {sum(1 for _, count in results if count > 0)}")
    
    # Optionally write detailed results to a file
    output_file = "underscore_counts.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Underscore Count Results\n")
        f.write("=" * 60 + "\n")
        f.write(f"Total files: {total_files}\n")
        f.write(f"Total underscores: {total_underscores}\n")
        f.write(f"Average per file: {total_underscores / total_files:.2f}\n\n" if total_files > 0 else "No files processed\n\n")
        for file_path, count in results:
            f.write(f"{file_path}: {count}\n")
    
    print(f"\nDetailed results written to: {output_file}")

if __name__ == "__main__":
    main()