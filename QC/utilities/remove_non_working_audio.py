import os
import csv
from lxml import etree
from xml.dom import minidom

"""
the main use of this utility is to remove the AUDIO tags associated with faulty
audio files that were detected by the validate_audio script. It's assumed that the data
about the faulty audios is listed here non_working_audio.csv in the validation logs.
"""


def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.

    Args:
        elem (etree.Element): The XML element to pretty-print.

    Returns:
        str: A pretty-printed XML string.
    """
    rough_string = etree.tostring(elem, pretty_print=True, encoding='utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    to_remove = os.path.join(curr_dir, "..", "validation", "logs", "non_working_audio.csv")
    audios_to_remove = list()

    if not os.path.exists(to_remove):
        print(f"non_working_audio.csv doesn't exist in {curr_dir}")
        return

    with open(to_remove, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        audios_to_remove = [item for item in reader]

    for item in audios_to_remove:
        path, lang, audio_id = item
        xml_file = path.replace("Final_audio", "Final_XML")+".xml"

        if not os.path.exists(xml_file):
            print(f"XML file does not exist: {xml_file}")
            continue

        tree = etree.parse(xml_file)
        root = tree.getroot()

        audio_element = root.xpath(f".//AUDIO[@file='{audio_id}']")  # Use XPath to find the element
        if audio_element:
            audio_element = audio_element[0]  # XPath returns a list, take the first element
            audio_parent = audio_element.getparent()

            if audio_parent is not None:
                audio_parent.remove(audio_element)  # Remove the AUDIO element

                try:
                    xml_string = prettify(root)
                    xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
                except Exception as e:
                    xml_string = ""
                    print(f"Failed to format file: {xml_file}, Error: {e}")

                with open(xml_file, "w", encoding="utf-8") as xmlfile:
                    xmlfile.write(xml_string)
                    print(f"File: {xml_file} modified successfully")
            else:
                print(f"Parent element not found for AUDIO: {audio_id} in file: {xml_file}")

if __name__ == "__main__":
    main()