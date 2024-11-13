from lxml import etree
import os
import re
import argparse
import logging
from collections import defaultdict

# Determine the language of the file based on the path
def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

# Analyze the punctuation to look for common issues
def analyze_punctuation(text, lang):
    results = defaultdict(int)

    # Define patterns for various punctuation issues
    left_quote = "‘"
    right_quote = "’"
    left_double_quote = '“'
    right_double_quote = '”'
    standard_double_quote = '"'
    apostrophe = "'"

    # Count individual punctuation marks
    results['left_quotes'] += text.count(left_quote)
    results['right_quotes'] += text.count(right_quote)
    results['left_double_quote'] += text.count(left_double_quote)
    results['right_double_quote'] += text.count(right_double_quote)
    results['apostrophes'] += text.count(apostrophe)
    results['standard_double_quotes'] += text.count(standard_double_quote)

    # Paired quotation patterns
    results['paired_single_quotes'] += len(re.findall(r'‘([^’]*)’', text))
    results['paired_double_quotes'] += len(re.findall(r'“([^”]*)”', text))
    results['paired_standard_double_quotes'] += len(re.findall(r'"([^"]*)"', text))

    # Detect and count extra spaces
    results['extra_spaces'] += len(re.findall(r' {2,}', text))
    results['multiple_whitespace_issues'] += len(re.findall(r' {2,}', re.sub(r'\s+', ' ', text)))

    # Detect imbalanced parentheses
    open_parens = text.count('(')
    close_parens = text.count(')')
    if open_parens != close_parens:
        results['imbalanced_parentheses'] += abs(open_parens - close_parens)

    # Repeated Punctuation
    results['repeated_punctuation'] += len(re.findall(r'([?!])\1+', text))

    # Mismatched Quotes
    if (text.count('‘') != text.count('’')) or (text.count('“') != text.count('”')):
        results['mismatched_quotes'] += 1

    # Consecutive Dashes
    results['consecutive_dashes'] += len(re.findall(r'--+', text))

    # Non-ASCII Characters
    non_ascii_count = sum(1 for char in text if ord(char) > 127)
    results['non_ascii_characters'] += non_ascii_count

    return results

# Analyze the XML file for punctuation issues
def analyze_xml_file(xml_file, lang_codes, args):
    lang = get_lang(xml_file, lang_codes)
    tree = etree.parse(xml_file)
    root = tree.getroot()

    file_issues = defaultdict(int)

    for sentence in root.findall('.//S'):
        form_text = sentence.findtext('FORM')
        if form_text:
            form_issues = analyze_punctuation(form_text, lang)
            for issue_type, count in form_issues.items():
                file_issues[issue_type] += count

            if args.verbose:
                logging.info(f"Issues found in {xml_file}: {form_issues}")

    return file_issues

# Analyze an entire directory of XML files
def analyze_directory(xml_dir, lang_codes, args):
    directory_issues = defaultdict(lambda: defaultdict(int))

    for root, _, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                xml_path = os.path.join(root, file)
                parent_dir = os.path.dirname(xml_path)
                file_issues = analyze_xml_file(xml_path, lang_codes, args)

                for issue_type, count in file_issues.items():
                    directory_issues[parent_dir][issue_type] += count

    return directory_issues

# Generate an aggregate report of punctuation issues
def generate_report(language_issues, structure):
    for lang, issues in language_issues.items():
        print(f"\nAggregate Report for {structure}: {lang}\n{'-'*40}")
        # Good things that do not need to be zero
        ignored_issues = ['apostrophes', 'standard_double_quotes', 'paired_standard_double_quotes']
        failure_detected = False

        for issue, count in issues.items():
            if count > 0 and issue not in ignored_issues:
                failure_detected = True
                print(f"{issue}: {count}")

        if failure_detected:
            print("FAIL")
        else:
            print("PASS")

        print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Validate punctuation in XML transcriptions.")
    parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('search_by', choices=['by_language', 'by_path', 'by_corpus'],
                        help='Specify the search method: by_language, by_path, or by_corpus')
    parser.add_argument('--language', help='Language code (required for by_language)')
    parser.add_argument('--corpora_path', help='Path to corpora directory (required for by_language and by_corpus)')
    parser.add_argument('--path', help='Path to XML file or directory (required for by_path)')
    parser.add_argument('--corpus', help='Corpus name (required for by_corpus)')
    args = parser.parse_args()

    langs = ["Amis", "Atayal", "Paiwan", "Bunun", "Puyuma", "Rukai", "Tsou", "Saisiyat", "Yami",
             "Thao", "Kavalan", "Truku", "Sakizaya", "Seediq", "Saaroa", "Kanakanavu"]

    if args.verbose:
        curr_dir = os.path.dirname(os.path.abspath(__file__))
        log_dir = os.path.join(curr_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)

        log_file_path = os.path.join(log_dir, f"punctuation_validation_log_{args.search_by}.txt")

        logging.getLogger().handlers.clear()
        logging.basicConfig(filename=log_file_path, level=logging.DEBUG,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        print(f"Verbose mode is on. Logs will be saved in {log_file_path}.")

    lang_codes = {lang: lang.lower() for lang in langs}

    corpora_dir = args.corpora_path if args.search_by != 'by_path' else os.path.dirname(args.path)
    directory_issues = analyze_directory(corpora_dir, lang_codes, args)

    generate_report(directory_issues, "Directory")

if __name__ == "__main__":
    main()
