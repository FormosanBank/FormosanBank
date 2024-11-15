from lxml import etree
import os
import re
from replace_non_ascii import fix_non_ascii_chars

def process_punctuation(text):
    # 1. Replace paired single quotes with double quotes (true quotes)
    text = re.sub(r'‘([^’]*)’', r'"\1"', text)
    
    # 2. Replace any remaining left and right single quotes with apostrophes (punctuation)
    text = text.replace("‘", "'").replace("’", "'")

    # 3. Replace paired double left and right quotes with standard double quotes
    text = re.sub(r'“([^”]*)”', r'"\1"', text)

    # 4. Standardize any remaining double quotes
    text = text.replace('“', '"').replace('”', '"')

    # 5. Handle specific mark replacements (e.g., replace ˈ with apostrophe)
    text = text.replace("ˈ", "'")

    return text

def normalize_whitespace(text):
    # 1. Remove extra spaces
    text = re.sub(r' {2,}', ' ', text)

    # 2. Fix any other multiple whitespace issues (e.g., tabs or newlines)
    text = re.sub(r'\s+', ' ', text).strip()

    return text

def fix_parentheses(text):
    """
    Fix imbalanced parentheses by removing unmatched ones.
    """
    stack = []
    indices_to_remove = set()

    # First pass: Identify unmatched parentheses
    for i, char in enumerate(text):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                indices_to_remove.add(i)

    # Add unmatched '(' indices from the stack
    indices_to_remove.update(stack)

    # Build a new string without the unmatched parentheses
    result = ''.join(
        [char for i, char in enumerate(text) if i not in indices_to_remove]
    )

    return result

def trim_repeated_punctuation(text):
    # 1. Replace repeated punctuation (e.g., !!, ??) with a single mark
    text = re.sub(r'([?!])\1+', r'\1', text)

    # 2. Replace consecutive dashes with a single dash
    text = re.sub(r'--+', '-', text)

    return text

def clean_text(text, lang):
    # Apply general cleaning functions
    text = process_punctuation(text)
    text = normalize_whitespace(text)
    text = fix_parentheses(text)
    text = trim_repeated_punctuation(text)

    # Additional cleaning for Chinese text (remove all extra spaces)
    if lang == "zho":
        text = re.sub(r'\s+', '', text)

    return text

def analyze_and_modify_xml_file(xml_file):
    fix_non_ascii_chars(xml_file)
    tree = etree.parse(xml_file)
    root = tree.getroot()
    modified = False

    # Iterate over <S> elements to clean <FORM> and <TRANSL> text
    for sentence in root.findall('.//S'):
        # Clean <FORM> text (Amis sentence)
        form_text = sentence.findtext('FORM')
        if form_text:
            cleaned_form_text = clean_text(form_text, lang="ami")
            if cleaned_form_text != form_text:
                sentence.find('FORM').text = cleaned_form_text
                modified = True

        # Clean each <TRANSL> element (translations in different languages)
        for transl in sentence.findall('TRANSL'):
            lang = transl.get('{http://www.w3.org/XML/1998/namespace}lang')
            transl_text = transl.text
            if transl_text:
                cleaned_transl_text = clean_text(transl_text, lang)
                if cleaned_transl_text != transl_text:
                    transl.text = cleaned_transl_text
                    modified = True

    # Write back to the XML file if modifications were made
    if modified:
        tree.write(xml_file, pretty_print=True, encoding="utf-8")
        print(f"File cleaned: {xml_file}")

def process_directory(xml_dir):
    # Iterate through the XML directory and process XML files
    for root, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                xml_path = os.path.join(root, file)
                analyze_and_modify_xml_file(xml_path)

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.join(curr_dir, "../..")
    corpora_dir = os.path.join(parent_dir, "Corpora")

    # Iterate through each subdirectory and process XML files
    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):  # Ensure it's a directory
            process_directory(xml_dir)

if __name__ == "__main__":
    main()
