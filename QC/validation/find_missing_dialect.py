import os
import xml.etree.ElementTree as ET
from pathlib import Path

def find_xmls_missing_dialect(xml_dir):
    missing_dialect = []
    missing_text = []
    for xml_file in Path(xml_dir).glob('*.xml'):
        try:
            tree = ET.parse(xml_file)
            text_elem = tree.getroot()
            if text_elem is not None:
                if 'dialect' not in text_elem.attrib:
                    missing_dialect.append(xml_file.name)
            else:
                missing_text.append(xml_file.name)
        except Exception as e:
            print(f"Error parsing {xml_file}: {e}")
    return missing_dialect, missing_text

if __name__ == "__main__":
    xml_dir = "Corpora/HundredPaiwanStories/XML"
    missing_dialect, missing_text = find_xmls_missing_dialect(xml_dir)
    if missing_dialect:
        print("Files with <TEXT> but missing dialect attribute:")
        for fname in missing_dialect:
            print(f"  {fname}")
    if missing_text:
        print("Files missing <TEXT> element:")
        for fname in missing_text:
            print(f"  {fname}")
    if not missing_dialect and not missing_text:
        print("All files have a <TEXT> element with a dialect attribute.")
