#!/usr/bin/env python3
"""
Quick script to add AUDIO elements to the first 86 S elements in Saisiyat XML file.
"""

import xml.etree.ElementTree as ET

def add_audio_elements():
    """Add AUDIO elements to S elements with ids 0-85 in Saisiyat XML file."""
    
    file_path = "Final_XML/sheng_huo_hui_hua_pian_daily_conversation/Saisiyat/Saisiyat.xml"
    
    # Parse the XML file
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Find all S elements
    changes_made = 0
    
    for s_element in root.findall('.//S'):
        s_id = s_element.get('id')
        
        # Check if this is one of the first 86 elements (ids 0-85)
        if s_id and s_id.isdigit():
            s_id_int = int(s_id)
            if 0 <= s_id_int <= 85:
                # Check if AUDIO element already exists
                existing_audio = s_element.find('AUDIO')
                if existing_audio is None:
                    # Create new AUDIO element
                    audio_element = ET.Element('AUDIO')
                    audio_element.set('file', f"sheng_huo_hui_hua_pian_daily_conversation_Saisiyat_{s_id}.mp3")
                    
                    # Add it to the S element
                    s_element.append(audio_element)
                    changes_made += 1
                    print(f"Added AUDIO element to S id={s_id}")
    
    # Save the file
    tree.write(file_path, encoding='utf-8', xml_declaration=True)
    print(f"\nCompleted! Added {changes_made} AUDIO elements to {file_path}")

if __name__ == "__main__":
    add_audio_elements()