from lxml import etree
import os
import re
from collections import defaultdict

def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

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
    extra_spaces = len(re.findall(r' {2,}', text))
    results['extra_spaces'] += extra_spaces
    
    # Normalize spaces and count multiple spaces
    normalized_text = re.sub(r'\s+', ' ', text)
    results['multiple_whitespace_issues'] += len(re.findall(r' {2,}', text))

    # Detect imbalanced parentheses
    open_parens = text.count('(')
    close_parens = text.count(')')
    if open_parens != close_parens:
        results['imbalanced_parentheses'] += abs(open_parens - close_parens)
    
    # Unmatched quotes check
    unmatched_left_quotes = max(0, results['left_quotes'] - results['paired_single_quotes'])
    unmatched_right_quotes = max(0, results['right_quotes'] - results['paired_single_quotes'])
    results['unmatched_left_quotes'] += unmatched_left_quotes
    results['unmatched_right_quotes'] += unmatched_right_quotes
    
    return results

def analyze_xml_file(xml_file, non_ascii, lang_codes):
    lang = get_lang(xml_file, lang_codes)
    tree = etree.parse(xml_file)
    root = tree.getroot()
    
    file_issues = defaultdict(int)
    
    # Iterate over <S> elements to examine the <FORM> text
    for sentence in root.findall('.//S'):
        form_text = sentence.findtext('FORM')
        if form_text:
            form_issues = analyze_punctuation(form_text, lang)
            # Accumulate issues per file
            for issue_type, count in form_issues.items():
                file_issues[issue_type] += count
            
            # Count non-ASCII characters
            temp = [(char, xml_file) for char in form_text if ord(char) > 127]
            non_ascii[lang]['items'] += temp
            non_ascii[lang]['count'] += len(temp)
    
    return file_issues

def analyze_directory(xml_dir, non_ascii, lang_codes):
    directory_issues = defaultdict(lambda: defaultdict(int))
    
    for root, _, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                xml_path = os.path.join(root, file)
                parent_dir = os.path.dirname(xml_path)
                file_issues = analyze_xml_file(xml_path, non_ascii, lang_codes)
                
                # Aggregate issues at the parent directory level
                for issue_type, count in file_issues.items():
                    directory_issues[parent_dir][issue_type] += count
    
    return directory_issues

def generate_report(language_issues, structure):
    # Print out the findings for each directory or language
    for lang, issues in language_issues.items():
        print(f"\nAggregate Report for {structure}: {lang}\n{'-'*40}")
        print(f"Total left quotes (‘): {issues['left_quotes']}")
        print(f"Total right quotes (’): {issues['right_quotes']}")
        print(f"Total left double quotes (“): {issues['left_double_quote']}")
        print(f"Total right double quotes (”): {issues['right_double_quote']}")
        print(f"Total apostrophes ('): {issues['apostrophes']}")
        print(f"Total double quotes (\"): {issues['standard_double_quotes']}")
        print(f"Total paired single quotes (‘ and ’): {issues['paired_single_quotes']}")
        print(f"Total paired double quotes (“ and ”): {issues['paired_double_quotes']}")
        print(f"Total paired standard double quotes (\"): {issues['paired_standard_double_quotes']}")
        print(f"Extra spaces found: {issues['extra_spaces']}")
        print(f"Multiple whitespace issues: {issues['multiple_whitespace_issues']}")
        print(f"Imbalanced parentheses: {issues['imbalanced_parentheses']}")
        print(f"Unmatched left quotes: {issues['unmatched_left_quotes']}")
        print(f"Unmatched right quotes: {issues['unmatched_right_quotes']}")
        print("="*50 + "\n")

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.join(curr_dir, "..")
    corpora_dir = os.path.join(parent_dir, "Corpora")
    
    lang_codes = {"Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv", "Bunun": "bnn", 
                  "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv", "Tsou": "tsu", "Kanakanavu": "xnb", 
                  "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao", "Sakizaya": "szy"}

    directory_issues = defaultdict(lambda: defaultdict(int))
    issues_by_lang = defaultdict(lambda: defaultdict(int))
    non_ascii = defaultdict(lambda: {"count": 0, "items": []})
    
    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):
            dir_issues = analyze_directory(xml_dir, non_ascii, lang_codes)
            for directory, issues in dir_issues.items():
                for issue_type, count in issues.items():
                    directory_issues[directory][issue_type] += count
                    lang = get_lang(directory, lang_codes)
                    issues_by_lang[lang][issue_type] += count
    
    for lang in non_ascii:
        print(f"{lang}:")
        print(f"Non-ASCII count: {non_ascii[lang]['count']}")
        print("_" * 30)
    
    generate_report(issues_by_lang, "Language")

if __name__ == "__main__":
    main()