import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import argparse
from lxml import etree


def prettify(elem):
    """Return a pretty-printed XML string for the Element using lxml."""
    rough_string = etree.tostring(elem, encoding='utf-8')
    parser = etree.XMLParser(remove_blank_text=True)
    reparsed = etree.fromstring(rough_string, parser)
    return etree.tostring(reparsed, pretty_print=True, encoding='utf-8').decode('utf-8')

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


# Get the language being analyzed from the path
def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

def get_files(path, to_check, lang):
    if lang:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".xml") and get_lang(os.path.join(root, file), langs) == args.language: # and 'Final_XML' in os.path.join(root, file)
                    to_check.append(os.path.join(root, file))
        return
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml"): # and 'Final_XML' in os.path.join(root, file)
                to_check.append(os.path.join(root, file))

def main(args, curr_dir, langs):
    if args.corpus:
        to_explore = [os.path.join(args.corpora, args.corpus)]
    else:
        to_explore = os.listdir(args.corpora)
        to_explore = [os.path.join(args.corpora, x) for x in to_explore]

    files = list()
    for corpus in to_explore:
        if ".DS_Store" in corpus:
            continue
        
        get_files(corpus, files, args.language)
        for file in files:
            try:
                # Parse the XML file
                tree = ET.parse(file)
                root = tree.getroot()

                # Iterate over all <S> elements
                for s_element in root.findall('.//S'):
                    
                    # Find the <FORM> child within each <S> element
                    form = s_element.find('FORM')
                    text = form.text
                    form.set("kindOf", "original")

                    text = text.replace("u", "o")
                    if text != form.text:
                        new_form = ET.SubElement(s_element, "FORM")
                        new_form.set("kindOf", "standard")
                        new_form.text = text
                   
                tree.write(file, encoding='utf-8', xml_declaration=True)
                print(f"file: {file} standardized successfully")
                try:
                    xml_string = prettify(root)
                except Exception as e:
                    xml_string = ""
                    print(f"Failed to format file: {file}, Error: {e}")

                with open(file, "w", encoding="utf-8") as xmlfile:
                    xmlfile.write(xml_string)
                        
            except ET.ParseError:
                print(f"Error parsing file: {file}")
            except Exception as e:
                print(f"Unexpected error with file {file}: {e}")



  
                    
if __name__ == "__main__":
    
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun', 'Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
             'Thao', 'Kavalan', 'Truku', 'Sakizaya', 'Seediq', 'Saaroa', 'Siraya', 'Kanakanavu']    
    
    parser = argparse.ArgumentParser(description="Standardize the orthography")
    #parser.add_argument('--verbose', action='store_true', help='increase output verbosity')
    parser.add_argument('--corpora', help='path of the corpora')
    parser.add_argument('--corpus', help='if standardization is desired to be applied to a specific corpus -- optional')
    parser.add_argument('--language', help='if standardization is desired to be applied to a specific language -- optional')
    args = parser.parse_args()

    # Validate required arguments
    if not args.corpora:
        parser.error("--corpora is required.")
    if not os.path.exists(args.corpora):
        parser.error(f"The entered corpora path doesn't exists: {args.corpora}")
    if args.corpus:
        if not os.path.exists(os.path.join(args.corpora, args.corpus)):
            parser.error(f"The entered corpus doesn't exist: {os.path.join(args.corpora, args.corpus)}")
    if args.language and args.language not in langs:
        parser.error(f"Enter a valid Formosan language from the list: {langs}")

    main(args, curr_dir, langs)