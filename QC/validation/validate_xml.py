from lxml import etree
import os
import pandas as pd
import argparse
import logging
import xml.etree.ElementTree as ET


'''
The validate XML script: 
- Validates the XML file against the xml template DTD file
- Checks if the xml:lang attribute uses an ISO 639-3 code
- Prettifies the XML file by replacing double spaces with tabs
- Parses the XML file and logs any errors that occur
'''

# Generate the name for the log file based on the search method
def get_log_file_name(args):
    if args.search_by == 'by_language':
        log_file_name = f"validation_log_by_language_{args.language.replace(' ', '_')}.txt"
    elif args.search_by == 'by_corpus':
        log_file_name = f"validation_log_by_corpus_{args.corpus.replace(' ', '_')}.txt"
    elif args.search_by == 'by_path':
        base_name = os.path.basename(args.path.strip('/'))
        if base_name:
            log_file_name = f"validation_log_by_path_{base_name.replace(' ', '_')}.txt"
        else:
            log_file_name = "validation_log_by_path.txt"
    else:
        log_file_name = "validation_log.txt"
    return log_file_name

# Get the language being analyzed from the path
def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

# Compare the XML to the DTD
def validate_xml_against_dtd(xml_file, dtd_file):
    try:
        # Parse the DTD file
        dtd = etree.DTD(open(dtd_file))

        # Parse the XML file
        tree = etree.parse(xml_file)

        # Validate the XML against the DTD
        is_valid = dtd.validate(tree)

        if is_valid:
            message = f"{xml_file}: XML is valid against the DTD."
            logging.info(message)
            return True
        else:
            error_message = f"{xml_file}: Validation errors:\n{dtd.error_log.filter_from_errors()}"
            logging.error(error_message)
            return False

    except Exception as e:
        error_message = f"An error occurred while validating {xml_file}: {e}"
        logging.error(error_message)
        return False


def validated_form(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Iterate over all <S> elements
    for s in root.findall('.//S'):
        forms = s.findall('.//FORM')
        if 'kindOf' not in forms[0].attrib or forms[0].attrib.get('kindOf') != 'original':
            return False
        if len(forms) > 1 and forms[1].attrib.get('kindOf') != 'standard':
            return False

    return True

# Ensure that if audio is set to "diarized", at least file attr is set for every Audio tag.
# if audio is set to anything else, check that start and end exist
def validate_audio_attr(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    if "audio" in root.attrib:
        audio_type = root.attrib["audio"]
    else:
        return True
    
    # Iterate over all <Audio> elements
    for audio in root.findall('.//Audio'):
        # If audio is diarized, all audio tages need to have the at least the file attribute
        if audio_type == "diarized" and "file" not in audio.attrib:
            return False
        # if audio isn't diarized, all audio tages need to have a start and end
        elif audio_type != "diarized" and ("start" not in audio.attrib or "end" not in audio.attrib):
            return False

    return True

# Ensure lang code complies with ISO 639-3
def validate_lang_code(xml_file, lang_codes):
    try:
        tree = etree.parse(xml_file)
        root = tree.getroot()
        lang = root.get("{http://www.w3.org/XML/1998/namespace}lang")

        if lang not in lang_codes:
            error_message = f"{xml_file}: xml:lang attribute '{lang}' is not using an ISO 639-3 code."
            logging.error(error_message)
            return False
        else:
            message = f"{xml_file}: xml:lang attribute '{lang}' is using an ISO 639-3 code."
            logging.info(message)
            return True
    except Exception as e:
        error_message = f"An error occurred while checking language code in {xml_file}: {e}"
        logging.error(error_message)
        return False

# Prettify the XML file by replacing double spaces with tabs
def prettify(xml_file):
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_file, parser)

    with open(xml_file, 'w') as f:
        temp_xml = etree.tostring(tree, pretty_print=True, encoding='unicode')
        temp_xml = temp_xml.replace('  ', '\t')
        f.write(temp_xml)

# Get all XML files in the specified path
def get_files(path, to_check, lang):
    if lang:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".xml") and get_lang(os.path.join(root, file), langs) == args.language: # and 'Final_XML' in os.path.join(root, file)
                    to_check.append(os.path.join(root, file))
        return to_check
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"): # and 'Final_XML' in os.path.join(root, file)
                to_check.append(os.path.join(root, file))

# Main process call subfunctions, log issues, and print summary
def main(args, langs):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    iso6393_3 = pd.read_csv(os.path.join(curr_dir, 'iso-639-3.txt'), sep='\t')
    langs_codes = set(iso6393_3['Id'])
    dtd_file = os.path.join(curr_dir, "xml_template.dtd")
    
    to_check = list()
    path_to_check = None
    lang = None
    
    issues_found = 0
    files_with_issues = []
    
    if args.search_by == "by_language":
        path_to_check = args.corpora_path
        lang = args.language
    elif args.search_by == "by_corpus":
        path_to_check = os.path.join(args.corpora_path, args.corpus)
    elif args.search_by == "by_path":
        path_to_check = args.path

    get_files(path_to_check, to_check, lang)
    for file in to_check:
        if args.verbose:
            logging.info(f"\nChecking {file}...")

        xml_valid = validate_xml_against_dtd(file, dtd_file)
        lang_code_valid = validate_lang_code(file, langs_codes)
        audio_attr_valid = validate_audio_attr(file)
        check_form_valid = validated_form(file)

        if not xml_valid or not lang_code_valid or not audio_attr_valid:
            issues_found += 1
            files_with_issues.append(file)
            if not args.verbose:
                print("-" * 120, "\n")
        if args.verbose:
            logging.info("-" * 120 + "\n")
    
    # Summary of issues
    summary_message = f"\nSummary:\nTotal issues found: {issues_found}"
    if files_with_issues:
        summary_message += "\nFiles with issues:\n" + "\n".join(files_with_issues)
    else:
        summary_message += "\nNo issues found."

    # Print summary to console
    print(summary_message)
    
    # Log summary if verbose mode is on
    if args.verbose:
        logging.info(summary_message)

# Main function to parse arguments and call main process
if __name__ == "__main__":
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Kanakanavu']

    parser = argparse.ArgumentParser(description="Validate XML files.")
    parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('search_by', choices=['by_language', 'by_path', 'by_corpus'],
                        help='Specify the search method: by_language, by_path, or by_corpus')
    parser.add_argument('--language', help='Language code (required for by_language)')
    parser.add_argument('--corpora_path', help='Path to corpora directory (required for by_language and by_corpus)')
    parser.add_argument('--path', help='Path to XML file or directory (required for by_path)')
    parser.add_argument('--corpus', help='Corpus name (required for by_corpus)')
    args = parser.parse_args()

    # Validate required arguments based on 'search_by'
    if args.search_by == 'by_language':
        if not args.language or not args.corpora_path:
            parser.error("For 'by_language', --language and --corpora_path are required.")
        if args.language not in langs:
            parser.error(f"Enter a valid Formosan language from the list: {langs}")
        if not os.path.exists(args.corpora_path):
            parser.error(f"The entered corpora path, {args.corpora_path}, doesn't exist")
    elif args.search_by == 'by_path':
        if not args.path:
            parser.error("For 'by_path', --path is required.")
        if not os.path.exists(args.path):
            parser.error(f"The entered path, {args.path}, doesn't exist")
    elif args.search_by == 'by_corpus':
        if not args.corpus or not args.corpora_path:
            parser.error("For 'by_corpus', --corpus and --corpora_path are required.")
        if not os.path.exists(os.path.join(args.corpora_path, args.corpus)):
            parser.error(f"The entered corpus, {args.corpus}, isn't a valid corpus in the provided corpora path.")

    # Set up logging only if verbose is True
    if args.verbose:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(curr_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file_name = get_log_file_name(args)
        log_file_path = os.path.join(log_dir, log_file_name)

        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # Create file handler which logs debug messages
        fh = logging.FileHandler(log_file_path, mode='w')
        fh.setLevel(logging.DEBUG)

        # Create formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(fh)

        print(f"Verbose mode is on. Detailed logs will be saved in {log_file_path}. Log will include which files have been checked and a detailed record if whether there has been any issues or not. The search mood is indicated by the log file name. A summary of issues can be found the buttom of the log file")

    main(args, langs)
