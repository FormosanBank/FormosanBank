import os
import re
from lxml import etree
import html
import argparse
import unicodedata

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
    pattern = r'[^A-Za-zÀ-ÖØ-öø-ÿʉɨɑɪɾθðŋʃʒʔɔɛæœɑəɯʌʊɜɵɒɲχϕ 0-9.,;:!?`\'\"()\[\]{}<>^]'
    return re.sub(pattern, ' ', text)

def swap_punctuation(text):
    """
    Replaces specific non-ASCII punctuation with their ASCII equivalents.
    """
    # Define the mapping of full-width punctuation to regular punctuation
    # Also convert square brackets to parentheses    
    fullwidth_to_regular = {
        '（': '(',
        '）': ')',
        '：': ':',
        '，': ',',
        '？': '?',
        '。': '.',
        '》': '"',
        '《': '"',
        '」': '"',
        '「': '"',
        '、': ',',
        '】': ')',
        '【': '(',
        ']': ')',
        '[': '(',
        '〔': '(',
        '〕': ')',
        '“': '"',  # Left double quotation mark
        '”': '"',  # Right double quotation mark
        '‘': "'",  # Left single quotation mark
        '’': "'",   # Right single quotation mark
        'ˈ': "'",
        'ʼ': "'",  # Modifier Letter Apostrophe (U+02BC)
        'ʻ': "'",
        '『': '"',
        '』': '"',
        '⌃': '^', # Caret
    }
    
    # Create a regular expression pattern to match any of the full-width punctuation characters
    pattern = re.compile('|'.join(map(re.escape, fullwidth_to_regular.keys())))
    
    # Define a function to replace each match with the corresponding regular punctuation
    def replace(match):
        return fullwidth_to_regular[match.group(0)]
    
    # Use re.sub to replace all full-width punctuation with regular punctuation
    return pattern.sub(replace, text)

def remove_junk_chars(text):
    """
    Replaces specific non-ASCII punctuation with their ASCII equivalents.
    """
    # Define the mapping of full-width punctuation to regular punctuation
    # Also convert square brackets to parentheses    
    to_remove = {
        'ㄇ': ''
    }
    
    # Create a regular expression pattern to match any of the full-width punctuation characters
    pattern = re.compile('|'.join(map(re.escape, to_remove.keys())))
    
    # Define a function to replace each match with the corresponding regular punctuation
    def replace(match):
        return to_remove[match.group(0)]
    
    # Use re.sub to replace all full-width punctuation with regular punctuation
    return pattern.sub(replace, text)


'''
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
'''

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
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    text = remove_junk_chars(text)
    #if lang not in ["zho", "zh"]:  # Apply only for non-Chinese languages
    #    text = remove_nonlatin(text)
    return text

def clean_trans(text, lang):
    """
    Applies a sequence of cleaning functions to the text.
    """
    text = normalize_whitespace(text)
    text = trim_repeated_punctuation(text)
    #if lang not in ["zho", "zh"]:  # Apply only for non-Chinese languages
    #    text = remove_nonlatin(text)
    return text

def analyze_and_modify_xml_file(xml_dir, corpora_dir):
    """
    Analyzes and modifies an XML file by cleaning text and handling specific cases in <FORM>.
    """
    for droot, dirs, files in os.walk(xml_dir):
        for file in files:
            if file.endswith(".xml"):
                print(f"Processing file: {file}")

                xml_file = os.path.join(droot, file)
                # Read the content of the XML file
                with open(xml_file, 'r', encoding='utf-8') as file:
                    content = file.read()

                # Replace all non-breaking spaces with regular spaces
                content = re.sub('\u00A0', ' ', content)

                # Write the modified content back to the XML file
                with open(xml_file, 'w', encoding='utf-8') as file:
                    file.write(content)

                # Silling to re-open the file, but such are the times we live in.
                tree = etree.parse(xml_file)
                root = tree.getroot()
                modified = False

                for sentence in root.findall('.//S'):
                    form_elements = sentence.findall('.//FORM')
                    for form_element in form_elements:
                        if form_element is not None:
                            form_text = form_element.text
                            if form_text is None or form_text == "":
                                continue
                            if form_text != unicodedata.normalize("NFC", form_text):
                                form_element.text = unicodedata.normalize("NFC", form_text)
                                modified = True

                            # Handle specific <FORM> cases
                            if not form_text:  # Remove <S> if <FORM> is empty
                                root.remove(sentence)
                                modified = True
                            elif "456otca" in form_text:  # Remove <S> if text contains 456otca
                                root.remove(sentence)
                                modified = True
                            else:
                                if html.unescape(form_text) != form_text:  # Replace HTML entities
                                    print('HTML entities found')
                                    # log the change
                                    with open(os.path.join(corpora_dir,"html_entities.log"), "a") as f:
                                        f.write(f"{xml_file}:\n")
                                        f.write(f"Original: {form_text}\n")
                                        f.write(f"Modified: {html.unescape(form_text)}\n\n")
                                    form_element.text = html.unescape(form_text)
                                    modified = True
                                cleaned_form_text = clean_text(form_text, lang="na")
                                if cleaned_form_text != form_text:
                                    form_element.text = cleaned_form_text
                                    modified = True

                    # Clean <TRANSL> elements
                    for transl in sentence.findall('TRANSL'):
                        lang = transl.get('{http://www.w3.org/XML/1998/namespace}lang')
                        transl_text = transl.text
                        if transl_text:
                            cleaned_transl_text = clean_trans(transl_text, lang)
                            if cleaned_transl_text != transl_text:
                                transl.text = cleaned_transl_text
                                modified = True

                if modified:
                    tree.write(xml_file, pretty_print=True, encoding="utf-8")
                    print(f"File cleaned: {xml_file}")

def main(args):
    """
    Main function to process XML files in the corpora directory.
    """
    print(f"Processing XML files in directory: {args.corpora_path}")
    # If there are no subdirectories, process the files directly
    subdir = os.listdir(args.corpora_path)
    for subdir in os.listdir(args.corpora_path):
        xml_dir = os.path.join(args.corpora_path, subdir)
        if os.path.isdir(xml_dir):
            analyze_and_modify_xml_file(xml_dir, args.corpora_path)
    analyze_and_modify_xml_file(args.corpora_path, args.corpora_path) #also process the root directory, just in case


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Extract orthographic info")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora_path', help='the path to the corpus')
    args = parser.parse_args()

    if not args.corpora_path:
        parser.error("--corpora_path is required.")    
    if not os.path.exists(os.path.join(args.corpora_path)):
        parser.error(f"The entered path, {args.corpora_path}, doesn't exist")

    main(args)
