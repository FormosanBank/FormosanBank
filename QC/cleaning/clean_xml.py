import os
import re
from lxml import etree

'''
def fix_parentheses(text):
    """
    Fixes imbalanced parentheses by removing unmatched ones.
    """
    stack = []
    indices_to_remove = set()
    for i, char in enumerate(text):
        if char == '(':
            stack.append(i)
        elif char == ')':
            if stack:
                stack.pop()
            else:
                indices_to_remove.add(i)
    indices_to_remove.update(stack)
    return ''.join(
        [char for i, char in enumerate(text) if i not in indices_to_remove]
    )
'''

def remove_nonlatin(text):
    """
    Removes characters that are not part of:
    - Latin script (including accented characters)
    - IPA Extensions (e.g., ʉ, ɨ)
    - Digits (0-9)
    - Common punctuation marks, including the caret (^)
    """
    pattern = '[^A-Za-zÀ-ÖØ-öø-ÿʉɨɑɪɾθðŋʃʒʔɔɛæœɑəɯʌʊɜɵɒɲχϕ 0-9.,;:!?`\'\"()\[\]{}<>^]'
    return re.sub(pattern, ' ', text)

def swap_punctuation(input_text):
    """
    Replaces specific non-ASCII punctuation with their ASCII equivalents.
    """
    output_text = ""
    for char in input_text:
        if ord(char) < 127:
            output_text += char
        elif ord(char) in (8217, 8216):  # Single quotes
            output_text += "'"
        elif ord(char) in (8221, 8220):  # Double quotes
            output_text += '"'
        elif ord(char) == 65288:  # Full-width (
            output_text += "("
        elif ord(char) == 65289:  # Full-width )
            output_text += ")"
        elif ord(char) == 65306:  # Full-width :
            output_text += ":"
        elif ord(char) == 12289:  # Ideographic comma
            output_text += ","
        elif ord(char) == 12290:  # Ideographic period
            output_text += "."
        else:
            output_text += char
    return output_text

def process_punctuation(text):
    """
    Cleans and standardizes punctuation in the text.
    """
    text = re.sub(r'‘([^’]*)’', r'"\1"', text)  # Paired single quotes
    text = text.replace("‘", "'").replace("’", "'")  # Single quotes
    text = re.sub(r'“([^”]*)”', r'"\1"', text)  # Paired double quotes
    text = text.replace('“', '"').replace('”', '"')  # Double quotes
    text = text.replace("ˈ", "'")  # Specific mark replacements
    return text

def normalize_whitespace(text):
    """
    Standardizes whitespace in the text.
    """
    text = re.sub(r' {2,}', ' ', text)  # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
    return text

def trim_repeated_punctuation(text):
    """
    Replaces repeated punctuation with single marks.
    """
    text = re.sub(r'([?!])\1+', r'\1', text)  # !! -> !
    text = re.sub(r'--+', '-', text)  # --- -> -
    return text

def clean_text(text, lang):
    """
    Applies a sequence of cleaning functions to the text.
    """
    text = swap_punctuation(text)
    text = process_punctuation(text)
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    if lang not in ["zho", "zh"]:  # Apply only for non-Chinese languages
        text = remove_nonlatin(text)
    return text

def analyze_and_modify_xml_file(xml_file):
    """
    Analyzes and modifies an XML file by cleaning text and handling specific cases in <FORM>.
    """
    tree = etree.parse(xml_file)
    root = tree.getroot()
    modified = False

    for sentence in root.findall('.//S'):
        form_element = sentence.find('FORM')
        
        if form_element is not None:
            form_text = form_element.text

            # Handle specific <FORM> cases
            if not form_text:  # Remove <S> if <FORM> is empty
                root.remove(sentence)
                modified = True
            elif "&rsquo;" in form_text:  # Replace &rsquo;
                form_element.text = form_text.replace("&rsquo;", "’")
                modified = True
            elif "456otca" in form_text:  # Remove <S> if text contains 456otca
                root.remove(sentence)
                modified = True
            else:
                cleaned_form_text = clean_text(form_text, lang="ami")
                if cleaned_form_text != form_text:
                    form_element.text = cleaned_form_text
                    modified = True

        # Clean <TRANSL> elements
        for transl in sentence.findall('TRANSL'):
            lang = transl.get('{http://www.w3.org/XML/1998/namespace}lang')
            transl_text = transl.text
            if transl_text:
                cleaned_transl_text = clean_text(transl_text, lang)
                if cleaned_transl_text != transl_text:
                    transl.text = cleaned_transl_text
                    modified = True

    if modified:
        tree.write(xml_file, pretty_print=True, encoding="utf-8")
        print(f"File cleaned: {xml_file}")

def process_directory(xml_dir):
    """
    Processes all XML files in a directory.
    """
    for root, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                analyze_and_modify_xml_file(os.path.join(root, file))

def main():
    """
    Main function to process XML files in the corpora directory.
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    corpora_dir = os.path.join(curr_dir, "../..", "Corpora")

    for subdir in os.listdir(corpora_dir):
        xml_dir = os.path.join(corpora_dir, subdir)
        if os.path.isdir(xml_dir):
            process_directory(xml_dir)

if __name__ == "__main__":
    main()
