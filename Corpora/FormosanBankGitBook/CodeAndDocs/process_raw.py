import os
import xml.etree.ElementTree as ET
from xml.dom import minidom

LANG_CODES = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}



def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    # print(reparsed.toprettyxml(indent="    "))
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string

def process_file(file_path, lang, file_name, xml_dir):
    
    file_name = file_name.replace(".txt", "")

    # Create the root element of the XML
    root = ET.Element("TEXT")
    root.set("id", f"gitbook_{lang}_{file_name}")
    root.set("xml:lang", LANG_CODES[lang])
    root.set("source", f"translation of FormosanBank gitbook in {lang}")
    root.set("copyright", "CC-BY-NC")
    root.set("citation", "Ruan, X. (2025). Paiwan translation of FormosanBank manual.")
    root.set("BibTeX_citation", "@misc{gitbook_paiwan_transl, author={Ruan, X.}, title={Paiwan Translation of FormosanBank Manual}, year={2025}, note={Translation}}")
    root.set("dialect", "Eastern")

    with open(file_path, 'r') as file:
        data = file.read()
    
    counter = 0
    data = data.split("\n\n")

    for entry in data:
        en, ch, formosan = entry.split("\n")
        s_element = ET.SubElement(root, "S")
        s_element.set("id", str(counter))
            
        # Add the 'FORM' element containing the sentence
        form_element = ET.SubElement(s_element, "FORM")
        form_element.text = formosan
        form_element.set("kindOf", "original")

        # Add the 'TRANSL' element containing the Chinese translation
        transl_element = ET.SubElement(s_element, "TRANSL")
        transl_element.set("xml:lang", "zh")
        transl_element.text = ch
        
        # Add the 'TRANSL' element containing the English translation
        transl_element = ET.SubElement(s_element, "TRANSL")
        transl_element.set("xml:lang", "en")
        transl_element.text = en
        counter += 1
    
    try:
        # Generate the pretty-printed XML string
        xml_string = prettify(root)
    except:
        # If an error occurs during prettifying, print an error message
        xml_string = ""
        print(f"error processing {file_path}")

    # Write the XML string to a file
    with open(os.path.join(xml_dir, file_name+".xml"), "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xml_string)
    



def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))  # Get the current directory
    raw_data_dir = os.path.join(curr_dir, "raw_data")

    xml_dir = os.path.join(curr_dir, "Final_XML")
    os.makedirs(xml_dir, exist_ok=True)

    for lang in os.listdir(raw_data_dir):
        os.makedirs(os.path.join(xml_dir, lang), exist_ok=True)
        lang_dir = os.path.join(raw_data_dir, lang)
        for file in os.listdir(lang_dir):
            if file.startswith("."):
                continue
            file_path = os.path.join(lang_dir, file)
            process_file(file_path, lang, file, os.path.join(xml_dir, lang))


if __name__ == "__main__":
    main()