import os
import csv
import xml.etree.ElementTree as ET
import argparse
import re

def main(dialects_csv, final_xml_dir):
    # Step 1: Read the dialects.csv file
    dialects_dict = {}
    with open(dialects_csv, mode='r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dialects_dict[row['dialect']] = row['glottocode']

    # Step 2: Iterate through all .xml files in Final_XML and its subdirectories
    for root, dirs, files in os.walk(final_xml_dir):
        for file in files:
            if file.endswith('.xml'):
                file_path = os.path.join(root, file)
                filename_without_ext = os.path.splitext(file)[0]

                # Step 3: Check if the filename is in the dialects_dict
                if filename_without_ext in dialects_dict:
                    glottocode = dialects_dict[filename_without_ext]

                    # Step 4: Parse the XML file
                    tree = ET.parse(file_path)
                    root_element = tree.getroot()

                    # Step 5: Add the glottocode attribute
                    root_element.set('glottocode', glottocode)

                    # Step 6: Check for underscore and add the dialect attribute
                    if '_' in filename_without_ext:
                        dialect = filename_without_ext.split('_')[0]
                        # Add space before capital letter preceded by a lowercase letter
                        dialect = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', dialect)
                        root_element.set('dialect', dialect)

                    # Step 7: Save the modified XML file
                    tree.write(file_path, encoding='utf-8', xml_declaration=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process XML files and add glottocode and dialect attributes.')
    parser.add_argument('--dialects_csv', help='Path to the dialects.csv file')
    parser.add_argument('--final_xml_dir', help='Path to the Final_XML directory')
    args = parser.parse_args()
    if not args.dialects_csv:
        parser.error("--dialects_csv is required.")
    if not args.final_xml_dir:
        parser.error("--final_xml_dir is required.")
    if not os.path.exists(args.final_xml_dir):
        parser.error(f"the path provided for --final_xml_dir, {args.final_xml_dir} doesn't exisit.")
    if not os.path.exists(args.dialects_csv):
        parser.error(f"the path provided for --dialects_csv, {args.dialects_csv} doesn't exisit.")

    main(args.dialects_csv, args.final_xml_dir)