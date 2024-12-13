import csv
import xml.etree.ElementTree as ET
import os
from xml.dom import minidom

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


def main(output_path):
    for dir in os.listdir(output_path):
        dir = os.path.join(output_path, dir)
        failed_path = os.path.join(dir, "failed_audio.csv")
        if not os.path.exists(failed_path):
            print(f"failed_audio.csv doesn't exist in {dir}")
            continue
        failed_audios = list()

        with open(failed_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            failed_audios = [item for item in reader]
        
        modified = dict()
        for item in failed_audios:
            url,file_name,lang,dialect,id,error = item

            file = os.path.join(dir, lang, dialect + ".xml")
            if file in modified:
                root = modified[file]
            else:
                tree = ET.parse(file)
                root = tree.getroot()
                modified[file] = root

            elm = root.find(f".//S[@id='{id}']")
            if not elm:
                elm = root.find(f".//W[@id='{id}']")
            
            audio_element = elm.find("AUDIO")
            if audio_element is not None:
                elm.remove(audio_element)
            
        for file in modified:
            root = modified[file]
            try:
                xml_string = prettify(root)
                xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
            except Exception as e:
                xml_string = ""
                print(f"Failed to format file: {file}, Error: {e}")

            with open(file, "w", encoding="utf-8") as xmlfile:
                xmlfile.write(xml_string)
                print(f"file: {file} modified successfully")


if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(curr_dir, "Final_XML")

    main(output_path)