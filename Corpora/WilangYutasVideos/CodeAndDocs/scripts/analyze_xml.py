import os
from lxml import etree
from pathlib import Path

def count_sentences_in_xml(xml_path):
    """Count the number of <S> elements in the XML file."""
    tree = etree.parse(xml_path)
    root = tree.getroot()
    sentences = root.findall(".//S")
    return len(sentences)

def count_sentences_in_all_xml():
    """
    Count all the <S> elements in all XML files in the 'XML' directory.
    """
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    xml_dir = Path("../XML")
    total_sentences = 0
    
    # Recursively search for all XML files
    for xml_file in xml_dir.glob("**/*.xml"):
        sentence_count = count_sentences_in_xml(xml_file)
        total_sentences += sentence_count
        print(f"{xml_file.name}: {sentence_count} sentences")
    
    print(f"\nTotal number of Atayal sentences: {total_sentences}")

if __name__ == "__main__":
    count_sentences_in_all_xml()
