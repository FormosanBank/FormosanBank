from lxml import etree
import os
import re

def process_punctuation(text):
    # Standardize punctuation marks
    text = re.sub(r'‘([^’]*)’', r'"\1"', text)  # Replace paired single quotes with double quotes
    text = text.replace("‘", "'").replace("’", "'")  # Replace remaining single quotes with apostrophes
    text = text.replace("ˈ", "'")  # Replace special mark with apostrophe
    text = text.replace('“', '"').replace('”', '"') #replace left and right double quotes with standard double quotes
    return text

def normalize_whitespace(text):
    # Normalize whitespace by replacing multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def remove_imbalanced_parentheses(text):
    """
    Remove unmatched parentheses from the input string.

    :param s: The input string containing parentheses and other characters.
    :return: A new string with unmatched parentheses removed.
    """
    # Stack to keep track of indices of '(' characters
    stack = []
    # Set to keep track of indices to remove
    indices_to_remove = set()

    # First pass to identify unmatched parentheses
    for i, char in enumerate(text):
        if char == '(':
            # Push the index onto the stack
            stack.append(i)
        elif char == ')':
            if stack:
                # Pop the matching '(' index from the stack
                stack.pop()
            else:
                # Unmatched ')', mark index for removal
                indices_to_remove.add(i)

    # Add any remaining '(' indices in the stack to the removal set
    indices_to_remove.update(stack)

    # Build the result string without the unmatched parentheses
    result = ''.join(
        [char for i, char in enumerate(s) if i not in indices_to_remove]
    )

def clean_text(text, lang):
    # Apply general cleaning functions
    text = process_punctuation(text)
    text = normalize_whitespace(text)
    text = remove_imbalanced_parentheses(text)

    # Additional cleaning for Chinese text
    if lang == "zho":
        text = re.sub(r'\s+', '', text)  # Remove extra spaces in Chinese text

    return text

def analyze_and_modify_xml_file(xml_file):
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
    parent_dir = os.path.join(curr_dir, "..")
    corpora_dir = os.path.join(parent_dir, "Corpora")
    
    # Iterate through each subdirectory and process XML files
    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):  # Ensure it's a directory
            process_directory(xml_dir)

if __name__ == "__main__":
    main()
