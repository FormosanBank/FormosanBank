import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os 

# Get the directory of the currently executing script
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
print("Current Working Directory:", os.getcwd())

# Paths to the input JSON file and output XML file
input_file = "../json/cleaned_amis_chinese_translations.json"
output_file = "../../Final_XML/amis_glosbe.xml"

def create_xml(input_file, output_file):
    # Load the merged JSON data
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Create the root element <TEXT>
    root = ET.Element(
        "TEXT",
        id="Amis",
        citation="Glosbe - An online dictionary (https://glosbe.com/ami/zh or https://glosbe.com/ami/en)",
        copyright="CC-BY-SA 4.0 (Attribution-ShareAlike)",
        **{"xml:lang": "ami"}
    )

    # Iterate over the entries and create XML elements
    for i, entry in enumerate(data, start=1):
        # Create an <S> element for each sentence
        s_element = ET.SubElement(root, "S", id=f"Amis_{i}")

        # Add the <FORM> element for the Formosan sentence
        form_element = ET.SubElement(s_element, "FORM")
        form_element.text = entry["formosan"]

        # Add the Chinese translation if it exists
        if entry.get("chinese"):
            chinese_element = ET.SubElement(s_element, "TRANSL", **{"xml:lang": "zho"})
            chinese_element.text = entry["chinese"]

    # Convert the ElementTree to a string and prettify the XML
    xml_str = ET.tostring(root, encoding="utf-8")
    parsed_xml = minidom.parseString(xml_str)
    pretty_xml_str = parsed_xml.toprettyxml(indent="    ")

    # Save the prettified XML to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pretty_xml_str)

    print(f"XML file created successfully: {output_file}")

if __name__ == "__main__":
    create_xml(input_file, output_file)
