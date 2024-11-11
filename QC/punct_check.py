# Description: This script reads in XML files from a directory and analyzes the punctuation used in the <FORM> tags.

from lxml import etree
import os
import re
from collections import defaultdict
import pandas as pd

def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

def analyze_punctuation(text, lang):
    results = defaultdict(int)
    
    # Define patterns for apostrophes, quotes, and punctuation checks
    left_quote = "‘"
    right_quote = "’"
    apostrophe = "'"
    left_double_quote = '“'
    right_double_quote = '”'
    double_quote = '"'
    
    # Count left, right, and apostrophe marks
    results['left_quotes'] += text.count(left_quote)
    results['right_quotes'] += text.count(right_quote)
    results['left_double_quote'] += text.count(left_double_quote)
    results['right_double_quote'] += text.count(right_double_quote)
    results['apostrophes'] += text.count(apostrophe)
    results['double_quote'] += text.count(double_quote)
    
    # Count paired quotation patterns
    paired_single_quotes = re.findall(r'‘([^’]*)’', text)
    results['paired_single_quotes'] += len(paired_single_quotes)
    
    # Print instances where text is between paired single quotes
    #for instance in paired_single_quotes:
    #    print(f"Text between single quotes: {instance}")
    
    paired_double_quotes = re.findall(r'"(.*?)"', text, re.DOTALL)
    results['paired_standard_double_quotes'] += len(paired_double_quotes)

    paired_double_quotes = re.findall(r'“(.*?)”', text, re.DOTALL)
    results['paired_double_quotes'] += len(paired_double_quotes) 
    if lang == "Kavalan" and results['double_quote'] > 0:
        print(text)
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
            temp = [(char, xml_file) for char in form_text if ord(char) > 127]
            non_ascii[lang]['items'] += temp
            non_ascii[lang]['count'] += len(temp)
            for issue_type, count in form_issues.items():
                file_issues[issue_type] += count
    if file_issues['double_quote'] > 0 and lang == "Kavalan":
        print(xml_file)
    return file_issues

def analyze_directory(xml_dir, non_ascii, lang_codes):
    # Group issues by the directory directly above each XML file
    directory_issues = defaultdict(lambda: defaultdict(int))
    
    for root, dirs, files in os.walk(xml_dir):
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
    # Print out the findings for each directory
    for lang, issues in language_issues.items():
        print(f"\nAggregate Report for {structure}: {lang}\n{'-'*40}")
        print(f"Total left quotes (‘): {issues['left_quotes']}")
        print(f"Total right quotes (’): {issues['right_quotes']}")
        print(f"Total left double quotes (“): {issues['left_double_quote']}")
        print(f"Total right double quotes (”): {issues['right_double_quote']}")
        print(f"Total apostrophes ('): {issues['apostrophes']}")
        print(f"Total double quotes (\"): {issues['double_quote']}")
        print(f"Total paired single quotes (‘ and ’): {issues['paired_single_quotes']}")
        print(f"Total paired double quotes (“ and ”): {issues['paired_double_quotes']}")
        print(f"Total paired standard double quotes (\"): {issues['paired_standard_double_quotes']}")
        print("="*50 + "\n")


def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.join(curr_dir, "..")
    corpora_dir = os.path.join(parent_dir, "Corpora")
    
    lang_codes = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}

    directory_issues = defaultdict(lambda: defaultdict(int))
    issues_by_lang = defaultdict(lambda: defaultdict(int))
    non_ascii = defaultdict(lambda: {"count":0, "items":[]})
    # Iterate through each subdirectory and process XML files
    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):  # Ensure it's a directory
            dir_issues = analyze_directory(xml_dir, non_ascii, lang_codes)
            for directory, issues in dir_issues.items():
                for issue_type, count in issues.items():
                    directory_issues[directory][issue_type] += count
                    lang = get_lang(directory, lang_codes)
                    issues_by_lang[lang][issue_type] += count
    for lang in non_ascii:
        print(f"{lang}:")
        print(non_ascii[lang]['count'])
        print("_"*30)
    generate_report(issues_by_lang, "Language")

if __name__ == "__main__":
    main()
