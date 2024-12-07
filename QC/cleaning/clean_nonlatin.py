import os
import re
from lxml import etree
import html

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


def analyze_and_modify_xml_file(xml_file):
    """
    Analyzes and modifies an XML file by cleaning text and handling specific cases in <FORM>.
    """
    tree = etree.parse(xml_file)
    root = tree.getroot()

    for sentence in root.findall('.//S'):
        form_element = sentence.find('FORM')
        if form_element is not None:
            form_text = form_element.text
        cleaned_form_text = remove_nonlatin(form_text, lang="na")
        if cleaned_form_text != form_text:
            form_element.text = cleaned_form_text
            #log 
            with open("nonlatin.log", "a") as f:
                f.write(f"{xml_file}:\n original: {form_text}\n cleaned: {cleaned_form_text}\n\n")
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
