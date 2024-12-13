import os
import xml.etree.ElementTree as ET

def add_attributes_to_xml_files(path, citation_value, bibtex_citation_value):
    for root_dir, _, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"):
                file_path = os.path.join(root_dir, file)
                tree = ET.parse(file_path)
                root = tree.getroot()
                root.set('citation', citation_value)
                root.set('BibTeX_citation', bibtex_citation_value)
                tree.write(file_path, encoding='utf-8', xml_declaration=True)
                print(f"Updated {file_path} with citation '{citation_value}' and BibTeX_citation '{bibtex_citation_value}'")

if __name__ == "__main__":
    directory_path = "Final_XML"
    citation = "Le Ferrand, É., Prud'hommeaux, E., Hartshorne, J. K., & Sung, L.-M. (2024). NTU Paiwan ASR Corpus. Electronic Resource."
    bibtex_citation = "@electronic{leferrand2024ntu, author = {Le Ferrand, {\'E}ric and Prud'hommeaux, Emily and Hartshorne, Joshua K. and Sung, Li-May}, year = {2024}, title = {{NTU} {Paiwan} {ASR} Corpus},type = {Electronic Resource}}"
    add_attributes_to_xml_files(directory_path, citation, bibtex_citation)