from lxml import etree
import os
import re
from collections import defaultdict
import pandas as pd

def analyze_punctuation(text):
    results = defaultdict(int)
    
    # Define patterns for apostrophes, quotes, and punctuation checks
    left_quote = "‘"
    right_quote = "’"
    apostrophe = "'"
    double_quote = '"'
    
    # Count left, right, and apostrophe marks
    results['left_quotes'] += text.count(left_quote)
    results['right_quotes'] += text.count(right_quote)
    results['apostrophes'] += text.count(apostrophe)
    
    # Count paired quotation patterns
    results['paired_single_quotes'] += len(re.findall(r'‘[^’]*’', text))
    results['paired_double_quotes'] += len(re.findall(r'"[^"]*"', text))
    
    # Check for missing spaces after punctuation
    results['missing_spaces_after_punctuation'] += len(re.findall(r'[.,!?;:](?!\s)', text))
    
    return results

def analyze_xml_file(xml_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()
    
    file_issues = defaultdict(int)
    
    # Iterate over <S> elements to examine the <FORM> text
    for sentence in root.findall('.//S'):
        form_text = sentence.findtext('FORM')
        if form_text:
            form_issues = analyze_punctuation(form_text)
            for issue_type, count in form_issues.items():
                file_issues[issue_type] += count
    
    return file_issues

def analyze_directory(xml_dir):
    # Group issues by the directory directly above each XML file
    directory_issues = defaultdict(lambda: defaultdict(int))
    
    for root, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                xml_path = os.path.join(root, file)
                parent_dir = os.path.dirname(xml_path)
                file_issues = analyze_xml_file(xml_path)
                
                # Aggregate issues at the parent directory level
                for issue_type, count in file_issues.items():
                    directory_issues[parent_dir][issue_type] += count
    
    return directory_issues

def generate_directory_level_report(directory_issues):
    # Print out the findings for each directory
    for directory, issues in directory_issues.items():
        print(f"\nAggregate Report for Directory: {directory}\n{'-'*40}")
        print(f"Total left quotes (‘): {issues['left_quotes']}")
        print(f"Total right quotes (’): {issues['right_quotes']}")
        print(f"Total apostrophes ('): {issues['apostrophes']}")
        print(f"Total paired single quotes (left and right quotes): {issues['paired_single_quotes']}")
        print(f"Total paired double quotes (\"): {issues['paired_double_quotes']}")
        print(f"Total missing spaces after punctuation: {issues['missing_spaces_after_punctuation']}")
        print("="*50 + "\n")

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.join(curr_dir, "..")
    corpora_dir = os.path.join(parent_dir, "Corpora")
    
    directory_issues = defaultdict(lambda: defaultdict(int))
    
    # Iterate through each subdirectory and process XML files
    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):  # Ensure it's a directory
            dir_issues = analyze_directory(xml_dir)
            for directory, issues in dir_issues.items():
                for issue_type, count in issues.items():
                    directory_issues[directory][issue_type] += count
    
    generate_directory_level_report(directory_issues)

if __name__ == "__main__":
    main()
