import os
import argparse
import xml.etree.ElementTree as ET

def add_dialect_to_xml_files(dialect, path):
    for filename in os.listdir(path):
        if filename.endswith(".xml"):
            file_path = os.path.join(path, filename)
            tree = ET.parse(file_path)
            root = tree.getroot()
            root.set('dialect', dialect)
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            print(f"Updated {filename} with dialect '{dialect}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Add dialect attribute to XML files.')
    parser.add_argument('--dialect', required=True, help='The dialect to add to the XML files.')
    parser.add_argument('--path', required=True, help='The path to the directory containing XML files.')
    
    args = parser.parse_args()
    add_dialect_to_xml_files(args.dialect, args.path)