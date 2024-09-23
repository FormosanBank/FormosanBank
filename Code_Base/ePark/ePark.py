import csv
from xml.etree.ElementTree import Element, SubElement, tostring, ElementTree
from xml.dom import minidom
import os

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)

    return reparsed.toprettyxml(indent="    ")

def create_xml(input_csv, output_xml, name, lang):
    root = Element("TEXT")
    root.set("xml:lang", lang)
    root.set("source", name)

    with open(input_csv, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for row_id, row in enumerate(reader):
            form_sentence, chinese_translation = row[:2]
            english_translation = ""
            if len(row)>3:
                form_sentence, english_translation, chinese_translation = row[:3]
            s_element = SubElement(root, "S")
            s_element.set("id", str(row_id))
            
            form_element = SubElement(s_element, "FORM")
            form_element.text = form_sentence

            transl_element = SubElement(s_element, "TRANSL")
            transl_element.set("xml:lang", "zh")
            transl_element.text = chinese_translation
            if english_translation!="":
                transl_element = SubElement(s_element, "TRANSL")
                transl_element.set("xml:lang", "en")
                transl_element.text = english_translation


    tree = ElementTree(root)
    try:
        xml_string = prettify(root)
    except:
        xml_string = ""
        input("bug")

    with open(output_xml, "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xml_string)

# Example usage:
for subfold in os.listdir("/mmfs1/data/leferran/data/Formosan/ePark/ePark2/"):
    sub_path = "/mmfs1/data/leferran/data/Formosan/ePark/ePark2/"+subfold+"/"
    for csv_name in os.listdir(sub_path):
        out_path = "./eParkxml/ePark2/{}/".format(subfold)
        if not os.path.isdir(out_path):
            os.mkdir(out_path)
        if ".csv" in csv_name:
            print(subfold,csv_name)
            lang = csv_name.split("-")[-1].replace("csv", "").lower()
            input_csv = sub_path+csv_name
            source = os.path.basename(input_csv).replace(".csv", "")
            output_xml = out_path+"{}.xml".format(source)
            create_xml(input_csv, output_xml, source, lang)
