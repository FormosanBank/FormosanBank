import copy
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import re
import csv
import sys


'''
def prettify(elem):
    """Return a pretty-printed XML string for the Element using lxml."""
    rough_string = etree.tostring(elem, encoding='utf-8')
    parser = etree.XMLParser(remove_blank_text=True)
    reparsed = etree.fromstring(rough_string, parser)
    return etree.tostring(reparsed, pretty_print=True, encoding='utf-8').decode('utf-8')
'''

def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.

    Args:
        elem (xml.etree.ElementTree.Element): The XML element to pretty-print.

    Returns:
        str: A pretty-printed XML string.
    """
    rough_string = ET.tostring(elem, 'utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string


def get_files(path, language):
    to_check = []
    if language:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".xml") and re.findall(language, os.path.join(root)): # and 'Final_XML' in os.path.join(root, file)
                    to_check.append(os.path.join(root, file))
        return to_check
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"): # and 'Final_XML' in os.path.join(root, file)
                to_check.append(os.path.join(root, file))

    return to_check

def apply_standard(s_element, standard):
    form = s_element.find("FORM[@kindOf='standard']")
    if form.text:
        # Apply each find-replace operation in order
        for original, replacement in standard:
            form.text = form.text.replace(original, replacement)

def _copy_mixed_content(src, dst):
    """Replace dst's text and children with a deep copy of src's.

    Used by create_standard so that mixed-content children — currently
    just <UNCLEAR/> — are preserved when duplicating original → standard.
    A plain `dst.text = src.text` drops UNCLEAR (an element child, not
    text), which would silently strip the "audio is unintelligible"
    marker from the standard tier and trigger V017 (empty FORM) under
    the 2026-06-08 schema.
    """
    for child in list(dst):
        dst.remove(child)
    dst.text = src.text
    for child in src:
        dst.append(copy.deepcopy(child))


def create_standard(element, file_path=None):
    # Find the <FORM> child within each <S> element
    original_form = element.find("FORM[@kindOf='original']")
    standard_form = element.find("FORM[@kindOf='standard']")

    if original_form is None:
        s_id = element.get('id', '<unknown>')
        location = f" in {file_path}" if file_path else ""
        print(
            f"Error: S id={s_id!r}{location} has no original tier (kindOf='original'). "
            f"Cannot create standard tier.",
            file=sys.stderr,
        )
        sys.exit(1)

    if standard_form is not None:
        # Standard form exists, replace its content with original's
        _copy_mixed_content(original_form, standard_form)
        return

    # No standard form exists, create one
    original_form.set("kindOf", "original")

    new_form = ET.Element("FORM")
    new_form.set("kindOf", "standard")
    _copy_mixed_content(original_form, new_form)
    element.insert(1, new_form)

def main(args):
    # Handle copy mode vs normal standardization mode
    if args.copy:
        available_columns = None
        print("Running in copy mode - copying original text to standard form")
    else:
        # Load the TSV file to get available columns
        with open(args.tsv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            available_columns = reader.fieldnames
    
    if args.corpus:
        to_explore = [os.path.join(args.corpora_path, args.corpus)]
    else:
        to_explore = os.listdir(args.corpora_path)
        to_explore = [os.path.join(args.corpora_path, x) for x in to_explore]

    for corpus in to_explore:
        print(f"Processing corpus: {corpus}")
        if ".DS_Store" in corpus:
            continue
        
        # Check if corpus is a file or directory
        if os.path.isfile(corpus) and corpus.endswith('.xml'):
            files = [corpus]
        else:
            files = get_files(corpus, args.language)
            
        if files:
            for file in files:
                try:
                    # Parse the XML file
                    tree = ET.parse(file)
                    root = tree.getroot()
                    
                    if args.copy:
                        # In copy mode, just copy original to standard
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                    else:
                        # Normal standardization mode
                        assert available_columns is not None  # loaded in non-copy branch above
                        # Determine target column
                        target_column = args.target_column
                        if not target_column:
                            # Check if XML has dialect attribute
                            dialect = root.get('dialect')
                            if dialect:
                                if dialect in available_columns:
                                    target_column = dialect
                                    print(f"Using dialect-specific column: {dialect}")
                                else:
                                    print(f"Warning: Dialect '{dialect}' found in file '{file}' but not available in TSV columns: {available_columns}")
                                    if 'standard' in available_columns:
                                        print("Falling back to 'standard' column")
                                        target_column = 'standard'
                                    else:
                                        print(
                                            f"Error: Dialect '{dialect}' from file '{file}' is not in TSV columns "
                                            f"{available_columns}, and no 'standard' column exists to fall back to. "
                                            f"Pass --target_column to pick one explicitly.",
                                            file=sys.stderr,
                                        )
                                        sys.exit(1)
                            elif 'standard' in available_columns:
                                target_column = 'standard'
                            else:
                                print(
                                    f"Error: File '{file}' has no 'dialect' attribute and TSV "
                                    f"{args.tsv_path} has no 'standard' column. Available columns: "
                                    f"{available_columns}. Pass --target_column to pick one explicitly.",
                                    file=sys.stderr,
                                )
                                sys.exit(1)
                        
                        # Load standardization mappings for this target column
                        standard = []
                        with open(args.tsv_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f, delimiter='\t')
                            for row in reader:
                                if target_column in row:
                                    original_value = row.get('original', '').strip()
                                    standard_value = row.get(target_column, '').strip()
                                    # Only include mappings where the original value exists
                                    # Empty standard value means "remove the original character"
                                    if original_value:  # Only process if there's something to replace
                                        standard.append((original_value, standard_value))

                        # Iterate over all <S> elements
                        for element in root.findall('.//FORM/..'):
                            create_standard(element, file_path=file)
                            apply_standard(element, standard)
                        
                    try:
                        xml_string = prettify(root)
                        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
                    except Exception as e:
                        xml_string = ""
                        print(f"Failed to format file: {file}, Error: {e}")

                    with open(file, "w", encoding="utf-8") as xmlfile:
                        xmlfile.write(xml_string)
                        print(f"file: {file} standardized successfully")
                            
                except ET.ParseError:
                    print(f"Error parsing file: {file}")
                except Exception as e:
                    print(f"Unexpected error with file {file}: {e}")
                    
if __name__ == "__main__":
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Standardize the orthography")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--copy', action='store_true', help='copy original text to standard form without any transformations')
    parser.add_argument('--tsv_path', help='path to TSV file with original and standard columns (not required when using --copy)')
    parser.add_argument('--target_column', help='column name to use as target for standardization (default: auto-detect from dialect or use "standard")')
    parser.add_argument('--corpora_path', help='path of the corpora')
    parser.add_argument('--corpus', help='if standardization is desired to be applied to a specific corpus -- optional')
    parser.add_argument('--language', help='if standardization is desired to be applied to a specific language -- optional')
    args = parser.parse_args()

    # Validate required arguments
    if not args.copy and not args.tsv_path:
        parser.error("Either --copy flag or --tsv_path is required.")
    if not args.copy and not os.path.exists(args.tsv_path):
        parser.error(f"The TSV file doesn't exist: {args.tsv_path}")
    if not args.corpora_path:
        parser.error("--corpora_path is required.")
    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered corpora path doesn't exists: {args.corpora_path}")
    if args.corpus:
        if not os.path.exists(os.path.join(args.corpora_path, args.corpus)):
            parser.error(f"The entered corpus doesn't exist: {os.path.join(args.corpora_path, args.corpus)}")
    if args.language and args.language not in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args)