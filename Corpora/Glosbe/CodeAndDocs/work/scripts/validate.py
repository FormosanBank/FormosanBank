import xml.etree.ElementTree as ET
import os 

# Get the directory of the currently executing script
dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)
print("Current Working Directory:", os.getcwd())

# Path to the XML file
xml_file = "../../xml/amis_glosbe.xml"

def validate_xml(xml_file):
    try:
        # Attempt to parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # If parsing succeeds, print a success message
        print("XML validation successful. The file is well-formed.")

        # Optionally, print the root element to verify
        print(f"Root element: {root.tag}")
    except ET.ParseError as e:
        # Handle XML parsing errors
        print("XML validation failed. The file is not well-formed.")
        print(f"Error: {e}")
    except Exception as e:
        # Handle other potential errors (e.g., file not found)
        print("An unexpected error occurred during XML validation.")
        print(f"Error: {e}")

if __name__ == "__main__":
    validate_xml(xml_file)
