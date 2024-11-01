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
    
    # Initialize aggregate counts for the file
    file_issues = defaultdict(int)
    
    # Iterate over <S> elements to examine the <FORM> text
    for sentence in root.findall('.//S'):
        form_text = sentence.findtext('FORM')
        if form_text:
            form_issues = analyze_punctuation(form_text)
            # Aggregate results
            for issue_type, count in form_issues.items():
                file_issues[issue_type] += count
    
    return file_issues

def analyze_directory(xml_dir):
    all_issues = {}
    
    # Recursively analyze each XML file in the directory
    for root, dirs, files in os.walk(xml_dir):
        print(f"Analyzing directory: {xml_dir}")  # For debugging
        for file in files:
            if file.endswith(".xml"):
                xml_path = os.path.join(root, file)
                print(f"Processing file: {xml_path}")  # For debugging
                file_issues = analyze_xml_file(xml_path)
                if file_issues:
                    all_issues[xml_path] = file_issues
    
    return all_issues

def generate_report(all_issues):
    # Print out the findings for each file
    for file_path, issues in all_issues.items():
        print(f"\nAnalysis Report for {file_path}:\n{'-'*40}")
        print(f"Total left quotes (‘): {issues['left_quotes']}")
        print(f"Total right quotes (’): {issues['right_quotes']}")
        print(f"Total apostrophes ('): {issues['apostrophes']}")
        print(f"Total paired single quotes (left and right quotes): {issues['paired_single_quotes']}")
        print(f"Total paired double quotes (\"): {issues['paired_double_quotes']}")
        print(f"Total missing spaces after punctuation: {issues['missing_spaces_after_punctuation']}")
        print("\n" + "="*50 + "\n")

def generate_aggregate_report(all_issues):
    # Initialize aggregate totals
    aggregate_totals = defaultdict(int)
    
    # Sum issues across all files
    for issues in all_issues.values():
        for issue_type, count in issues.items():
            aggregate_totals[issue_type] += count
    
    # Print the aggregate report
    print("\nAggregate Report for Entire Corpora:\n" + "-"*40)
    print(f"Total left quotes (‘): {aggregate_totals['left_quotes']}")
    print(f"Total right quotes (’): {aggregate_totals['right_quotes']}")
    print(f"Total apostrophes ('): {aggregate_totals['apostrophes']}")
    print(f"Total paired single quotes (left and right quotes): {aggregate_totals['paired_single_quotes']}")
    print(f"Total paired double quotes (\"): {aggregate_totals['paired_double_quotes']}")
    print(f"Total missing spaces after punctuation: {aggregate_totals['missing_spaces_after_punctuation']}")
    print("="*50 + "\n")

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.join(curr_dir, "..")
    corpora_dir = os.path.join(parent_dir, "Corpora")
    
    all_issues = {}
    
    # Iterate through each subdirectory and process XML files
    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):  # Ensure it's a directory
            issues = analyze_directory(xml_dir)
            if issues:
                all_issues.update(issues)  # Collect issues from all directories
    
    generate_report(all_issues)
    generate_aggregate_report(all_issues)

if __name__ == "__main__":
    main()
