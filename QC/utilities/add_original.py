import os
import xml.etree.ElementTree as ET
import argparse

def add_kindOf_to_form_elements(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".xml"):
                file_path = os.path.join(root, file)
                tree = ET.parse(file_path)
                root_element = tree.getroot()

                # Iterate over all <FORM> elements and add kindOf="original"
                for form_element in root_element.findall('.//FORM'):
                    form_element.set('kindOf', 'original')

                # Write the changes back to the file
                tree.write(file_path, encoding='utf-8', xml_declaration=True)
                print(f"Updated file: {file_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add kindOf='original' to all <FORM> elements in XML files in a directory.")
    parser.add_argument('--corpora_path', required=True, help='Path to the directory containing XML files')
    args = parser.parse_args()

    if not os.path.isdir(args.corpora_path):
        print(f"The specified path is not a directory: {args.corpora_path}")
        sys.exit(1)

    add_kindOf_to_form_elements(args.corpora_path)