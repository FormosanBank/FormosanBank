import os
import csv
from lxml import etree
from xml.dom import minidom

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
        print(f"mp3_to_wav.csv doesn't exist in {curr_dir}")
        return

    with open(to_remove, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        audios_to_remove = [item for item in reader]

    for item in audios_to_remove:
        path, lang, audio_id = item
        xml_file = os.path.join(path.replace('Final_audio', 'Final_XML'), audio_id.split('_')[0] + ".xml")

        if not os.path.exists(xml_file):
            print(f"XML file does not exist: {xml_file}")
            continue

        tree = etree.parse(xml_file)
        root = tree.getroot()

        audio_element = root.xpath(f".//AUDIO[@file='{audio_id}']")  # Use XPath to find the element
        if audio_element:
            audio_element = audio_element[0]  # XPath returns a list, take the first element
            sentence = audio_element.getparent()

            if sentence is not None:
                sentence.remove(audio_element)  # Remove the AUDIO element

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