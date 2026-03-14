#!/usr/bin/env python3
"""
Verify that all audio files referenced in XML files exist in Final_audio directory.
"""

import os
from pathlib import Path
from lxml import etree

def verify_audio_files():
    """Check all XML files and verify that referenced audio files exist."""
    
    xml_root = Path("Final_XML")
    audio_root = Path("Final_audio")
    
    missing_files = []
    total_audio_elements = 0
    checked_files = 0
    
    print("Scanning XML files for AUDIO elements...")
    
    # Walk through all XML files
    for xml_file in xml_root.rglob("*.xml"):
        try:
            # Parse the XML file
            tree = etree.parse(str(xml_file))
            
            # Find all AUDIO elements
            audio_elements = tree.xpath("//AUDIO[@file]")
            
            for audio_elem in audio_elements:
                total_audio_elements += 1
                
                # Get the file attribute
                audio_filename = audio_elem.get('file')
                if not audio_filename:
                    continue
                    
                # The audio file should be in Final_audio
                # The path structure should match the XML path structure
                xml_relative_path = xml_file.relative_to(xml_root)
                xml_dir = xml_relative_path.parent  # e.g., section/Language
                
                # Extract dialect from XML filename (without .xml extension)
                xml_filename_stem = xml_file.stem  # e.g., Duda_Seediq
                
                # Construct the expected audio file path: Final_audio/section/Language/Dialect/filename
                expected_audio_path = audio_root / xml_dir / xml_filename_stem / audio_filename
                
                # Check if the file exists - first try the direct path with dialect
                file_exists = expected_audio_path.exists()
                actual_path = expected_audio_path
                
                # If not found, try the single-dialect case where language name is repeated
                # For languages with single dialect: section/Language/Language/filename
                if not file_exists:
                    xml_parts = xml_dir.parts
                    if len(xml_parts) >= 2:  # Should be like ('section', 'Language')
                        language = xml_parts[-1]  # Last part is the language
                        # Check if dialect directory is the same as language
                        if xml_filename_stem == language:
                            # Already tried the right path, no need to try again
                            pass
                        else:
                            # Try: Final_audio/section/Language/Language/filename (single-dialect case)
                            alternative_path = audio_root / xml_dir / language / audio_filename
                            if alternative_path.exists():
                                file_exists = True
                                actual_path = alternative_path
                
                if not file_exists:
                    missing_files.append({
                        'xml_file': str(xml_file),
                        'audio_filename': audio_filename,
                        'expected_path': str(expected_audio_path),
                        'xml_element': etree.tostring(audio_elem, encoding='unicode').strip()
                    })
                else:
                    checked_files += 1
                    
                # Progress indicator
                if total_audio_elements % 1000 == 0:
                    print(f"Checked {total_audio_elements} AUDIO elements...")
                    
        except Exception as e:
            print(f"Error processing {xml_file}: {e}")
            continue
    
    print(f"\nVerification complete!")
    print(f"Total AUDIO elements checked: {total_audio_elements}")
    print(f"Files that exist: {checked_files}")
    print(f"Missing files: {len(missing_files)}")
    
    if missing_files:
        print(f"\n{'='*80}")
        print("MISSING AUDIO FILES:")
        print(f"{'='*80}")
        
        for i, missing in enumerate(missing_files, 1):
            print(f"\n{i}. XML File: {missing['xml_file']}")
            print(f"   Audio filename: {missing['audio_filename']}")
            print(f"   Expected path: {missing['expected_path']}")
            print(f"   XML element: {missing['xml_element']}")
            
        # Save to file for easier review
        with open('missing_audio_files.txt', 'w', encoding='utf-8') as f:
            f.write("Missing Audio Files Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total AUDIO elements checked: {total_audio_elements}\n")
            f.write(f"Files that exist: {checked_files}\n")
            f.write(f"Missing files: {len(missing_files)}\n\n")
            
            for i, missing in enumerate(missing_files, 1):
                f.write(f"{i}. XML File: {missing['xml_file']}\n")
                f.write(f"   Audio filename: {missing['audio_filename']}\n")
                f.write(f"   Expected path: {missing['expected_path']}\n")
                f.write(f"   XML element: {missing['xml_element']}\n\n")
                
        print(f"\nDetailed report saved to: missing_audio_files.txt")
    else:
        print("\n✅ All audio files referenced in XML exist in Final_audio!")
        
    return missing_files

if __name__ == "__main__":
    missing = verify_audio_files()