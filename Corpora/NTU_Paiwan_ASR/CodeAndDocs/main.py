import json
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import shutil
from tqdm import tqdm

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')  # Convert XML element to string
    reparsed = minidom.parseString(rough_string)  # Parse string for pretty formatting
    return reparsed.toprettyxml(indent="    ")  # Return formatted XML string


def create_root(p, id, audio):
    """Initialize the root XML element for a participant's data."""
    root = ET.Element("TEXT")
    root.set("id", f"Li-May_Pwn{p}_{id}")
    root.set("xml:lang", "pwn")
    root.set("source", f"Li-May Paiwan Data, Participant {p}, file {id}")
    root.set("audio", audio)
    root.set("copyright", "CC-BY")
    root.set("citation", "origianl")
    root.set("BibTeX_citation", "TBD")
    return root


def handle_participant(data_path, name, p_data, output_path):
    """Process each participant's data, creating XML files and copying audio files."""
    for entry in tqdm(p_data, desc=f"processing: {name}"):
        # Extract record, audio, and EAF file details
        record, audio, eaf = entry['wave'], entry['wave'] + ".wav", entry['eaf']
        
        # Check if the EAF file exists; adjust filename if needed
        if not os.path.exists(os.path.join(data_path, eaf)):
            eaf = eaf.replace("_", "")
        
        # Parse the EAF (ELAN Annotation Format) file
        tree = ET.parse(os.path.join(data_path, eaf))
        to_read_root = tree.getroot()

        # Create root XML element for the participant's data
        root = create_root(name, record, audio)

        # Map time slots to start and end times
        time_slots = dict()
        for item in to_read_root.findall('.//TIME_SLOT'):
            time_slots[item.get("TIME_SLOT_ID")] = item.get("TIME_VALUE")[:-3] + '.' + item.get("TIME_VALUE")[-3:]

        # Process each annotation to create XML elements for sentences
        for item in to_read_root.findall('.//ALIGNABLE_ANNOTATION'):
            s, e = time_slots[item.get("TIME_SLOT_REF1")], time_slots[item.get("TIME_SLOT_REF2")]
            form = item.find("ANNOTATION_VALUE").text
            id = item.get("ANNOTATION_ID")
            form = form.replace("\n", "")  # Clean up form text

            # Create XML elements for each sentence entry
            s_element = ET.SubElement(root, "S")
            s_element.set("id", id)

            form_element = ET.SubElement(s_element, "FORM")
            form_element.text = form

            audio_element = ET.SubElement(s_element, "AUDIO")
            audio_element.set("start", s)
            audio_element.set("end", e)
        
        # Update record name to include participant ID
        record += f"_{name}"

        # Convert XML structure to a formatted string
        try:
            xml_string = prettify(root)
        except Exception as e:
            xml_string = ""
            print(f"Failed to format XML: {record}, Error: {e}")

        # Write the XML data to file
        with open(os.path.join(output_path, record + ".xml"), "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xml_string)

        # Copy audio file to output directory
        audio_output = os.path.join(output_path, "audio", record + "." + audio.split('.')[-1])
        if not os.path.exists(audio_output):
            try:
                shutil.copy(os.path.join(data_path, audio), audio_output)
            except Exception as e:
                print(eaf, audio)
                print(f"Failed to copy audio: {os.path.join(data_path, audio)}. Error: {e}")


def main(data_path, output_path):
    """Main function to process JSON data and handle XML/audio for each participant."""
    # Load data for non-spoken entries from JSON file
    with open('non_sp_data.json', 'r') as f:
        desc = json.load(f)
    
    # Process each participant in the JSON data
    for name in desc:
        # Set up directories for participant data
        p_path = os.path.join(data_path, name)
        xml_output_path = os.path.join(output_path, name)
        os.makedirs(output_path, exist_ok=True)
        os.makedirs(os.path.join(xml_output_path, "audio"), exist_ok=True)
        
        # Process and generate XML and audio files for each participant's entries
        handle_participant(p_path, name, desc[name]['enteries'], xml_output_path)


if __name__ == "__main__":
    # Define base directory paths for data and output
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(curr_dir, "Final_XML", "Paiwan")
    os.makedirs(output_path, exist_ok=True)
    
    # Run main function with data and output paths
    main(os.path.join(curr_dir, "Data"), output_path)
