import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import re
import csv
import sys
import string
from pathlib import Path

# Make the QC package importable so we can reuse the shared dialect inventory
# (the same single-vs-multi-dialect source used by fix_dialects.py and V036).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.validation._dialect_inventory import is_multi_dialect_language


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

def apply_phonology_mappings(text, phonology_mappings, conversion_dict):
    """Apply phonology mappings with capitalization handling"""
    result = text
    
    # Apply mappings in the original order from the TSV file
    for letter, ipa_value in phonology_mappings:
        # Apply exact mapping
        if letter in result:
            result = result.replace(letter, ipa_value)
        
        # Handle capitalized version if it exists in text and doesn't have its own mapping
        letter_upper = letter.capitalize() if len(letter) > 1 else letter.upper()
        if letter_upper in result and letter_upper not in conversion_dict:
            result = result.replace(letter_upper, ipa_value)
    
    return result

def main(args):
    # Set up standard orthography path
    standard_path = Path(__file__).parent.parent.parent / 'Orthographies' / 'Ortho113'
    if not os.path.exists(standard_path):
        parser.error(f"The standard orthography files can't be found: {standard_path}")
    
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
                    
                    # Extract language and dialect from TEXT element (which may be the root)
                    text_element = root if root.tag == 'TEXT' else root.find('.//TEXT')
                    if text_element is None:
                        print(f"Warning: No <TEXT> element found in file: {file}")
                        continue
                    
                    # Try different ways to get the language attribute
                    language = (text_element.get('xml:lang', '') or 
                               text_element.get('{http://www.w3.org/XML/1998/namespace}lang', '') or
                               text_element.get('lang', '')).strip()
                    dialect = text_element.get('dialect', '').strip()
                    
                    
                    # Convert xml:lang codes to language names if needed
                    lang_map = {
                        'ami': 'Amis',
                        'tay': 'Atayal',
                        'bnn': 'Bunun',
                        'ckv': 'Kavalan',
                        'pwn': 'Paiwan',
                        'pyu': 'Puyuma',
                        'dru': 'Rukai',
                        'sxr': 'Saaroa',
                        'xsy': 'Saisiyat',
                        'szy': 'Sakizaya',
                        'trv': 'Seediq',
                        'ssf': 'Thao',
                        'tsu': 'Tsou',
                        'tao': 'Yami',
                        'xnb': 'Kanakanavu'
                    }#Note that since Seediq and Truku both share the code `trv`, we will need to rely on dialect information to distinguish them when analyzing XML files.
                    if language in lang_map:
                        language = lang_map[language]
                                        
                    # Check for required language
                    if not language:
                        print(f"Error: Language is blank in file: {file}")
                        sys.exit(1)
                    
                    # Use default dialect if blank
                    if not dialect:
                        dialect = "default"
                    
                    print(f"Processing file: {file} (Language: {language}, Dialect: {dialect})")
                    
                    # Load the TSV file for this language
                    tsv_file_path = standard_path / f"{language}.tsv"
                    if not os.path.exists(tsv_file_path):
                        print(f"Warning: TSV file not found for language {language}: {tsv_file_path}")
                        continue
                    
                    with open(tsv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f, delimiter='\t')
                        available_columns = reader.fieldnames
                    
                    # Pick the TSV column to read IPA from, driven by whether the
                    # language actually has multiple dialects (per dialects.csv).
                    # Single-dialect languages follow the convention dialect == the
                    # language name (e.g. dialect="Yami"), so the dialect attribute is
                    # NOT a column selector — we use the sole value column. Multi-dialect
                    # languages select the column by dialect, falling back to 'default'.
                    value_columns = [c for c in (available_columns or []) if c != 'letter']
                    if is_multi_dialect_language(language):
                        if dialect and dialect != "default" and dialect in value_columns:
                            target_column = dialect
                        elif 'default' in value_columns:
                            if dialect and dialect not in ("default", "unknown"):
                                print(f"Warning: Dialect '{dialect}' not found in TSV columns for {language}; using 'default' column: {available_columns}")
                            target_column = 'default'
                        else:
                            print(f"Error: Dialect '{dialect}' not found and no 'default' column in TSV for multi-dialect {language}: {available_columns}")
                            continue
                    else:
                        # Single-dialect language: use the sole value column, whatever it
                        # is named ('IPA', 'default', ...).
                        if len(value_columns) == 1:
                            target_column = value_columns[0]
                        elif 'IPA' in value_columns:
                            target_column = 'IPA'
                        elif 'default' in value_columns:
                            target_column = 'default'
                        else:
                            print(f"Error: No usable value column in TSV for single-dialect {language}: {available_columns}")
                            continue
                    
                    # Create array of pairs from 'letter' column and target column
                    phonology_mappings = []
                    conversion_dict = {}  # Track all letters and their IPA mappings
                    ipa_characters = set()  # Track all valid IPA output characters
                    with open(tsv_file_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f, delimiter='\t')
                        for row in reader:
                            if 'letter' in row and target_column in row:
                                letter = (row['letter'] or '').strip()
                                target_value = (row[target_column] or '').strip()
                                if letter and target_value != 'NA':  # Include empty values but exclude explicit 'NA'
                                    phonology_mappings.append((letter, target_value))
                                    conversion_dict[letter] = target_value
                                    # Add all characters from the IPA value to the valid set
                                    if target_value:  # Only add characters if there's an actual IPA value
                                        for char in target_value:
                                            ipa_characters.add(char)
                    
                    # Find all <FORM> elements with kindOf="standard"
                    standard_forms = root.findall('.//FORM[@kindOf="standard"]')
                    
                    for form_element in standard_forms:
                        # Check if there's already a sister <PHON> element with kindOf="standard"
                        parent = form_element.getparent() if hasattr(form_element, 'getparent') else None
                        if parent is None:
                            # Find parent using the tree structure
                            for elem in root.iter():
                                if form_element in list(elem):
                                    parent = elem
                                    break
                        
                        if parent is not None:
                            # Check for existing standard PHON element
                            existing_phon = parent.find('PHON[@kindOf="standard"]')
                            if existing_phon is None:
                                # Create new PHON element
                                phon_element = ET.Element("PHON")
                                phon_element.set("kindOf", "standard")
                                
                                # Insert after the FORM element
                                form_index = list(parent).index(form_element)
                                parent.insert(form_index + 1, phon_element)
                                #print(f"  Added standard PHON element")
                            else:
                                phon_element = existing_phon
                            
                            # Process the text from FORM element to create phonological transcription
                            form_text = form_element.text or ""
                            
                            # Apply phonology mappings with capitalization handling
                            processed_text = apply_phonology_mappings(form_text, phonology_mappings, conversion_dict)
                            
                            # Then replace any remaining unknown non-punctuation characters with *
                            # Now check against IPA characters instead of original letters
                            final_text = ""
                            for char in processed_text:
                                if char in ipa_characters or char in string.punctuation or char.isspace():
                                    final_text += char
                                else:
                                    final_text += "*"
                            
                            phon_element.text = final_text
                    
                    # If args.orthography is specified, also process original forms
                    if args.orthography:
                        # Set up custom orthography path
                        custom_ortho_path = Path(__file__).parent.parent.parent / 'Orthographies' / args.orthography
                        custom_tsv_file_path = custom_ortho_path / f"{language}.tsv"
                        
                        if os.path.exists(custom_tsv_file_path):
                            # Load custom orthography mappings
                            with open(custom_tsv_file_path, 'r', encoding='utf-8') as f:
                                reader = csv.DictReader(f, delimiter='\t')
                                custom_available_columns = reader.fieldnames
                            
                            # Determine target column for custom orthography
                            if dialect and dialect != "default":
                                if dialect in custom_available_columns:
                                    custom_target_column = dialect
                                elif 'default' in custom_available_columns:
                                    # Unknown dialect: fall back to the 'default' column
                                    print(f"Warning: Dialect '{dialect}' not found in custom orthography for {language}; using 'default' column")
                                    custom_target_column = 'default'
                                elif 'IPA' in custom_available_columns:
                                    custom_target_column = 'IPA'
                                else:
                                    print(f"Warning: No suitable column found in custom orthography for {dialect}, skipping original forms")
                                    custom_target_column = None
                            else:
                                if 'IPA' in custom_available_columns:
                                    custom_target_column = 'IPA'
                                elif 'default' in custom_available_columns:
                                    custom_target_column = 'default'
                                else:
                                    print(f"Warning: No IPA or default column found in custom orthography, skipping original forms")
                                    custom_target_column = None
                            
                            if custom_target_column:
                                # Create custom phonology mappings
                                custom_phonology_mappings = []
                                custom_conversion_dict = {}
                                custom_ipa_characters = set()
                                with open(custom_tsv_file_path, 'r', encoding='utf-8') as f:
                                    reader = csv.DictReader(f, delimiter='\t')
                                    for row in reader:
                                        if 'letter' in row and custom_target_column in row:
                                            letter = (row['letter'] or '').strip()
                                            target_value = (row[custom_target_column] or '').strip()
                                            if letter and target_value != 'NA':  # Include empty values but exclude explicit 'NA'
                                                custom_phonology_mappings.append((letter, target_value))
                                                custom_conversion_dict[letter] = target_value
                                                if target_value:  # Only add characters if there's an actual IPA value
                                                    for char in target_value:
                                                        custom_ipa_characters.add(char)
                                
                                # Process all <FORM> elements with kindOf="original"
                                original_forms = root.findall('.//FORM[@kindOf="original"]')
                                
                                for form_element in original_forms:
                                    # Check if there's already a sister <PHON> element with kindOf="original"
                                    parent = form_element.getparent() if hasattr(form_element, 'getparent') else None
                                    if parent is None:
                                        # Find parent using the tree structure
                                        for elem in root.iter():
                                            if form_element in list(elem):
                                                parent = elem
                                                break
                                    
                                    if parent is not None:
                                        # Check for existing original PHON element
                                        existing_phon = parent.find('PHON[@kindOf="original"]')
                                        if existing_phon is None:
                                            # Create new PHON element for original
                                            phon_element = ET.Element("PHON")
                                            phon_element.set("kindOf", "original")
                                            
                                            # Insert after the FORM element
                                            form_index = list(parent).index(form_element)
                                            parent.insert(form_index + 1, phon_element)
                                        else:
                                            phon_element = existing_phon
                                        
                                        # Process the text from original FORM element
                                        form_text = form_element.text or ""
                                        
                                        # Apply custom phonology mappings
                                        processed_text = apply_phonology_mappings(form_text, custom_phonology_mappings, custom_conversion_dict)
                                        
                                        # Replace remaining unknown characters
                                        final_text = ""
                                        for char in processed_text:
                                            if char in custom_ipa_characters or char in string.punctuation or char.isspace():
                                                final_text += char
                                            else:
                                                final_text += "*"
                                        
                                        phon_element.text = final_text
                        else:
                            print(f"Warning: Custom orthography TSV file not found: {custom_tsv_file_path}")
                    
                    # Save the modified XML
                    try:
                        xml_string = prettify(root)
                        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
                    except Exception as e:
                        xml_string = ""
                        print(f"Failed to format file: {file}, Error: {e}")

                    with open(file, "w", encoding="utf-8") as xmlfile:
                        xmlfile.write(xml_string)
                        print(f"File: {file} processed successfully")
                            
                except ET.ParseError:
                    print(f"Error parsing file: {file}")
                except Exception as e:
                    print(f"Unexpected error with file {file}: {e}")
                    
if __name__ == "__main__":
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Standardize the orthography")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--orthography', help='if adding phonology for an original, non-standard orthography, specify using the folder name of that orthography. Standard orthography is always processed, if it exists.')
    parser.add_argument('--target_column', help='column name to use as target for standardization (default: auto-detect from dialect or use "standard")')
    parser.add_argument('--corpora_path', help='path of the corpora')
    parser.add_argument('--language', help='if standardization is desired to be applied to a specific language -- optional')
    args = parser.parse_args()
    

    # Validate required arguments
    if args.orthography:
        ortho_path = Path(__file__).parent.parent.parent / 'Orthographies' / args.orthography
        if not os.path.exists(ortho_path):
            parser.error(f"The orthography doesn't exist: {ortho_path}")
    if not args.corpora_path:
        parser.error("--corpora_path is required.")
    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered corpora path doesn't exists: {args.corpora_path}")
    if args.language and args.language not in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args)