import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom

# File paths
English_xml = "../../Intermediate/Paiwan/Presidential_Apology/english.xml"
Paiwan_xml = "../../Intermediate/Paiwan/Presidential_Apology/paiwan.xml"
output_file_path = "../../XML_Final/Paiwan/Presidential_Apology/Paiwan_Presidential_Apology.xml"

# Parse the XML files
paiwan_tree = ET.parse(Paiwan_xml)
paiwan_root = paiwan_tree.getroot()

english_tree = ET.parse(English_xml)
english_root = english_tree.getroot()

# Dictionary to store data by S id
combined_data = {}

# Extract data from the first file (English translation)
for sentence in english_root.findall('S'):
    sid = sentence.get('id')
    translation = sentence.find('TRANSL').text
    combined_data[sid] = {'english': translation}

# Extract data from the second file (Paiwan language)
for sentence in paiwan_root.findall('S'):
    sid = sentence.get('id')
    form = sentence.find('FORM').text
    if sid in combined_data:
        combined_data[sid]['paiwan'] = form
    else:
        combined_data[sid] = {'paiwan': form}

# Create a new XML tree for output
root = ET.Element("TEXT")
root.set("source", "Combined English and Paiwan translations")

# Populate the new XML structure
for sid, data in combined_data.items():
    sentence_element = ET.Element("S", id=sid)

    if 'english' in data:
        english_element = ET.SubElement(sentence_element, "TRANSL", lang="en")
        english_element.text = data['english']

    if 'paiwan' in data:
        paiwan_element = ET.SubElement(sentence_element, "FORM", lang="paiwan")
        paiwan_element.text = data['paiwan']

    root.append(sentence_element)

# Convert the ElementTree to a string
rough_string = ET.tostring(root, encoding="utf-8", method="xml")

# Use minidom to pretty-print the XML with indentation and new lines
dom = minidom.parseString(rough_string)
pretty_xml_as_string = dom.toprettyxml(indent="  ")

# Save the formatted XML to a file
with open(output_file_path, "w", encoding="utf-8") as f:
    f.write(pretty_xml_as_string)

print(f"Combined data saved to {output_file_path}")
