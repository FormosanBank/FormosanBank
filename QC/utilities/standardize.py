import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
import re


'''
def prettify(elem):
    """Return a pretty-printed XML string for the Element using lxml."""
    rough_string = etree.tostring(elem, encoding='utf-8')
    parser = etree.XMLParser(remove_blank_text=True)
    reparsed = etree.fromstring(rough_string, parser)
    return etree.tostring(reparsed, pretty_print=True, encoding='utf-8').decode('utf-8')
'''

def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.

    Args:
        elem (xml.etree.ElementTree.Element): The XML element to pretty-print.

    Returns:
        str: A pretty-printed XML string.
    """
    rough_string = ET.tostring(elem, 'utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string


def get_files(path, language):
    to_check = []
    if language:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".xml") and re.findall(language, os.path.join(root)): # and 'Final_XML' in os.path.join(root, file)
                    to_check.append(os.path.join(root, file))
        return to_check
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"): # and 'Final_XML' in os.path.join(root, file)
                to_check.append(os.path.join(root, file))

    return to_check


def replace_u_with_o(s_element):
    form = s_element.find("FORM[@kindOf='standard']")
    if form.text:
        form.text = form.text.replace("u", "o")


def create_standard(element):
    # Find the <FORM> child within each <S> element
    tmp = element.find("FORM[@kindOf='standard']")
    if tmp is not None:
        return

    form = element.find('FORM')
    form.set("kindOf", "original")
    
    new_form = ET.Element("FORM")
    new_form.set("kindOf", "standard")
    new_form.text = form.text
    element.insert(1, new_form)

def main(args):
    if args.corpus:
        to_explore = [os.path.join(args.corpora_path, args.corpus)]
    else:
        to_explore = os.listdir(args.corpora_path)
        to_explore = [os.path.join(args.corpora_path, x) for x in to_explore]

    for corpus in to_explore:
        print(f"Processing corpus: {corpus}")
        if ".DS_Store" in corpus:
            continue
        files = get_files(corpus, args.language)
        if files:
            for file in files:
                try:
                    # Parse the XML file
                    tree = ET.parse(file)
                    root = tree.getroot()

                    # Iterate over all <S> elements
                    for element in root.findall('.//FORM/..'):
                        create_standard(element)
                        replace_u_with_o(element)
                        
                    try:
                        xml_string = prettify(root)
                        xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
                    except Exception as e:
                        xml_string = ""
                        print(f"Failed to format file: {file}, Error: {e}")

                    with open(file, "w", encoding="utf-8") as xmlfile:
                        xmlfile.write(xml_string)
                        print(f"file: {file} standardized successfully")
                            
                except ET.ParseError:
                    print(f"Error parsing file: {file}")
                except Exception as e:
                    print(f"Unexpected error with file {file}: {e}")
                    
if __name__ == "__main__":
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Standardize the orthography")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora_path', help='path of the corpora')
    parser.add_argument('--corpus', help='if standardization is desired to be applied to a specific corpus -- optional')
    parser.add_argument('--language', help='if standardization is desired to be applied to a specific language -- optional')
    args = parser.parse_args()

    # Validate required arguments
    if not args.corpora_path:
        parser.error("--corpora_path is required.")
    if not os.path.exists(args.corpora_path):
        parser.error(f"The entered corpora path doesn't exists: {args.corpora_path}")
    if args.corpus:
        if not os.path.exists(os.path.join(args.corpora_path, args.corpus)):
            parser.error(f"The entered corpus doesn't exist: {os.path.join(args.corpora_path, args.corpus)}")
    if args.language and args.language not in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args)