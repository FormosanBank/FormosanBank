# CHANGES PUNCTUATION TO MATCH GUIDELINES 

# ALL SINGULAR ‘ and ’ are replaced with ' (apostrophe)
# ALL PAIRED ‘ and ’ are replaced with " (double quotes)


from lxml import etree
import os
import re
from collections import defaultdict

def process_punctuation(text):
    # Define patterns for apostrophes, quotes, and punctuation checks
    left_quote = "‘"
    right_quote = "’"
    apostrophe = "'"
    
    # Replace paired single quotes with double quotes
    text = re.sub(r'‘([^’]*)’', r'"\1"', text)
    
    # Replace any remaining left or right quotes with apostrophes
    text = text.replace(left_quote, apostrophe).replace(right_quote, apostrophe)
    
    return text

def analyze_and_modify_xml_file(xml_file):
    tree = etree.parse(xml_file)
    root = tree.getroot()
    
    modified = False
    
    # Iterate over <S> elements to examine the <FORM> text
    for sentence in root.findall('.//S'):
        form_text = sentence.findtext('FORM')
        if form_text:
            modified_text = process_punctuation(form_text)
            # If changes were made, update the XML
            if modified_text != form_text:
                sentence.find('FORM').text = modified_text
                modified = True
    
    # Write back to the XML file if modifications were made
    if modified:
        tree.write(xml_file, pretty_print=True, encoding="utf-8")

def process_directory(xml_dir):
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