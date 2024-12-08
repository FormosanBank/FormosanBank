import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def read_apologies(path, langs):
    """Read apology texts in multiple languages from text files."""
    to_return = dict()

    # Read apologies in English
    ap = open(os.path.join(path, "English.txt"), "r").read().split("\n")
    for s in ap:
        s = s.strip()  # Remove any extra whitespace
    to_return["English"] = ap

    # Read apologies in Chinese
    ap = open(os.path.join(path, "Chinese.txt"), "r").read().split("\n")
    for s in ap:
        s = s.strip()
    to_return["Chinese"] = ap

    # Read apologies for each specified language
    for lang in langs:
        lang_path = os.path.join(path, lang)
        ap = open(os.path.join(lang_path, lang + ".txt"), "r").read().split("\n")
        for s in ap:
            s = s.strip()
        to_return[lang] = ap

        # Special handling for Kanakanavu language with additional English and Chinese translations
        if lang == "Kanakanavu":
            ap = open(os.path.join(lang_path, lang + "_en.txt"), "r").read().split("\n")
            for s in ap:
                s = s.strip()
            to_return[lang + "_en"] = ap

            ap = open(os.path.join(lang_path, lang + "_zh.txt"), "r").read().split("\n")
            for s in ap:
                s = s.strip()
            to_return[lang + "_zh"] = ap

    return to_return


def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')  # Convert XML element to a string
    reparsed = minidom.parseString(rough_string)  # Reparse for formatting
    return reparsed.toprettyxml(indent="    ")  # Return formatted XML string


def generate_apology_xml(lang, lang_code, apologies, out_path):
    """Generate an XML file with apology texts and translations for a given language."""
    
    # Create the root XML element
    root = Element("TEXT")
    root.set("id", f"PA_{lang}")
    root.set("xml:lang", lang_code)
    root.set("source", f"Presidential apology to indigenous people in {lang}")
    root.set("copyright", "public domain")
    root.set("citation", f"Tsai, I. W. (2016, August 1). President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government [Speech transcript, {lang} translation]. https://indigenous-justice.president.gov.tw/")
    root.set("BibTeX_citation", f"@misc{{PA_{lang}, author = {{Tsai, Ing-Wen}}, title = {{President Tsai Ing-wen's apology to the Indigenous Peoples on behalf of the government}}, year = {{2016}}, month = {{August}}, day = {{1}}, note = {{[Speech transcript, {lang} translation]}}, url = {{https://indigenous-justice.president.gov.tw/}} }}")
 
    print(len(apologies[lang]), lang)  # Print number of apologies for debugging

    # Retrieve apologies and translations based on language
    apology, en, zh = apologies[lang], apologies["English"], apologies["Chinese"]
    if lang == "Kanakanavu":
        en, zh = apologies[lang + "_en"], apologies[lang + "_zh"]

    # Generate XML entries for each apology
    for i in range(len(apology)):
        ap_s, en_s, zh_s = apology[i], en[i], zh[i]

        # Create sentence element
        s_element = SubElement(root, "S")
        s_element.set("id", str(i))

        # Create form (apology text in the target language)
        form_element = SubElement(s_element, "FORM")
        form_element.text = ap_s

        # Create translations in Chinese and English
        transl_element = SubElement(s_element, "TRANSL")
        transl_element.set("xml:lang", "zh")
        transl_element.text = zh_s

        transl_element = SubElement(s_element, "TRANSL")
        transl_element.set("xml:lang", "en")
        transl_element.text = en_s

    # Convert XML structure to a formatted string
    try:
        xml_string = prettify(root)
    except:
        xml_string = ""
        print(lang)  # Log if there’s an issue with XML formatting

    # Write the XML content to a file
    with open(os.path.join(out_path, lang + ".xml"), "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xml_string)


def main():
    """Main function to read apology data and generate XML files."""
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(curr_dir, "Final_XML")

    # Define language codes and list of languages to process
    lang_codes = {
        "Amis": "ami", "Atayal": "tay", "Saisiyat": "xsy", "Thao": "ssf", "Seediq": "trv", "Bunun": "bnn",
        "Paiwan": "pwn", "Rukai": "dru", "Truku": "trv", "Kavalan": "ckv", "Tsou": "tsu", "Kanakanavu": "xnb",
        "Saaroa": "sxr", "Puyuma": "pyu", "Yami": "tao", "Sakizaya": "szy"
    }
    
    langs = [
        "Amis", "Atayal", "Bunun", "Kavalan", "Paiwan", "Puyuma", "Rukai", "Saaroa", "Saisiyat", "Sakizaya", 
        "Seediq", "Thao", "Truku", "Tsou", "Yami", "Kanakanavu"
    ]

    # Read apology texts from files
    apologies_dir = os.path.join(curr_dir, "Apologies")
    apologies = read_apologies(apologies_dir, langs)

    # Generate XML for each language
    for lang in langs:
        generate_apology_xml(lang, lang_codes[lang], apologies, output_path)


if __name__ == "__main__":
    main()