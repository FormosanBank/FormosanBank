import copy
import os
import xml.etree.ElementTree as ET
import argparse
import re
import csv
import sys
from pathlib import Path
from lxml import etree

# Make the QC package importable so we can reuse the shared dialect inventory
# (the same single-vs-multi-dialect source used by fix_dialects.py and V036).
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from QC.validation._dialect_inventory import ISO_TO_LANGUAGE, is_multi_dialect_language


def prettify(elem):
    """Return a pretty-printed XML string for the Element using lxml."""
    rough_string = ET.tostring(elem, encoding='utf-8')
    parser = etree.XMLParser(remove_blank_text=True)
    reparsed = etree.fromstring(rough_string, parser)
    etree.indent(reparsed, space="    ")
    body = etree.tostring(reparsed, encoding='unicode')
    return f'<?xml version="1.0" ?>\n{body}\n'


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


def get_exploration_targets(corpora_path, corpus=None):
    if corpus:
        return [os.path.join(corpora_path, corpus)]
    if os.path.isfile(corpora_path) and corpora_path.endswith('.xml'):
        return [corpora_path]
    return [os.path.join(corpora_path, x) for x in os.listdir(corpora_path)]

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
    
    to_explore = get_exploration_targets(args.corpora_path, args.corpus)

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
                        # Determine target column, driven by whether the language
                        # actually has multiple dialects (per dialects.csv). Single-dialect
                        # languages follow the convention dialect == the language name
                        # (e.g. dialect="Yami"), so the dialect attribute is NOT a column
                        # selector — we use the sole value column ('standard' or whatever
                        # it is named). Multi-dialect languages select by dialect, falling
                        # back to 'standard'.
                        target_column = args.target_column
                        if not target_column:
                            dialect = root.get('dialect')
                            xlang = (
                                root.get('{http://www.w3.org/XML/1998/namespace}lang')
                                or root.get('xml:lang')
                                or root.get('lang')
                                or ''
                            ).strip()
                            language = ISO_TO_LANGUAGE.get(xlang, xlang)
                            value_columns = [c for c in available_columns if c != 'original']
                            if language and is_multi_dialect_language(language):
                                # Multi-dialect: the dialect attribute selects the column.
                                if dialect and dialect in value_columns:
                                    target_column = dialect
                                    print(f"Using dialect-specific column: {dialect}")
                                elif 'standard' in value_columns:
                                    if dialect and dialect not in ('standard', 'unknown'):
                                        print(f"Warning: Dialect '{dialect}' in file '{file}' not in TSV columns {available_columns}; falling back to 'standard' column")
                                    target_column = 'standard'
                                else:
                                    print(
                                        f"Error: Dialect '{dialect}' from file '{file}' is not in TSV columns "
                                        f"{available_columns}, and no 'standard' column exists to fall back to. "
                                        f"Pass --target_column to pick one explicitly.",
                                        file=sys.stderr,
                                    )
                                    sys.exit(1)
                            else:
                                # Single-dialect language (or unresolved xml:lang): use the
                                # sole value column. A dialect attribute that happens to
                                # match a column is still honored.
                                if dialect and dialect in value_columns:
                                    target_column = dialect
                                    print(f"Using dialect-specific column: {dialect}")
                                elif len(value_columns) == 1:
                                    target_column = value_columns[0]
                                elif 'standard' in value_columns:
                                    target_column = 'standard'
                                else:
                                    print(
                                        f"Error: File '{file}' (language '{language or xlang}') has no unique value "
                                        f"column and no 'standard' column in TSV {args.tsv_path}. Available columns: "
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
        if os.path.isfile(args.corpora_path):
            parser.error("--corpus cannot be used when --corpora_path is a file.")
        if not os.path.exists(os.path.join(args.corpora_path, args.corpus)):
            parser.error(f"The entered corpus doesn't exist: {os.path.join(args.corpora_path, args.corpus)}")
    if args.language and args.language not in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args)
