from lxml import etree
import os
import pandas as pd

def validate_xml_against_dtd(xml_file, dtd_file):
    try:
        # Parse the DTD file
        dtd = etree.DTD(open(dtd_file))

        # Parse the XML file
        tree = etree.parse(xml_file)

        # Validate the XML against the DTD
        is_valid = dtd.validate(tree)

        if is_valid:
            print("XML is valid according to the DTD.")
            return True
        else:
            print("XML is not valid according to the DTD.")
            print(dtd.error_log.filter_from_errors())  # Print validation errors
            return False

    except Exception as e:
        print(f"An error occurred: {e}")


def validate_lang_code(xml_file, lang_codes):

    tree = etree.parse(xml_file)


    root = tree.getroot()
    lang = root.get("{http://www.w3.org/XML/1998/namespace}lang")

    if lang not in lang_codes:
        print("xml:lang attr of TEXT tag isn't using ISO 639-3")
        return False
    else:
        print("xml:lang attr of TEXT tag is using ISO 639-3")
        return True
    
def prettify(xml_file):

    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(xml_file, parser)

    with open(xml_file, 'w') as f:
        temp_xml = etree.tostring(tree, pretty_print=True, encoding='unicode')
        temp_xml = temp_xml.replace('  ', '\t')
        f.write(temp_xml)
    
def main():
    
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    print(curr_dir)
    iso6393_3 = pd.read_csv(os.path.join(curr_dir, 'iso-639-3.txt'), sep='\t')
    langs_codes = set(iso6393_3['Id'])


    xml_file = os.path.join(curr_dir, "temp.xml")
    dtd_file = os.path.join(curr_dir, "xml_template.dtd")
    xml_valid = validate_xml_against_dtd(xml_file, dtd_file)
    lang_code_valid = validate_lang_code(xml_file, langs_codes)
    if xml_valid and lang_code_valid:
        prettify(xml_file)


if __name__ == "__main__":
    main()