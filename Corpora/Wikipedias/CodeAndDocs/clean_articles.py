import re
import os
import pickle
import regex
from concurrent.futures import ThreadPoolExecutor, as_completed
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime
from tqdm import tqdm
import chardet
import unicodedata

def detect_encoding(file_path):
    # This function detects the encoding of a file using the chardet library
    # It is called by the read_file_with_detected_encoding function
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    return result['encoding']

def read_file_with_utf8(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        print(f"Warning: Failed to decode {file_path} with UTF-8.")
        encoding = detect_encoding(file_path)
    with open('encoding_detection.log', 'a') as log_file:
        log_file.write(f"File: {file_path}, Encoding: {encoding}\n")
        return(None)

def remove_links(text, file_path):
    """
    This function removes URLs from a given text using a regular expression pattern
    The change is reported in link_removal.log. For each change, the log includes the path to the file,
    the line number, the original line, and the line after removing the URLs.
    """
    # Split the text into lines
    lines = text.split('\n')

    # Define the regular expression pattern
    pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F])|[^\x00-\x7F])+'
    # Find all matches of the pattern in the text
    matches = list(re.finditer(pattern, text))
    
    if not matches:
        return text  # No links to remove

    # Remove the links from the text
    no_links_text = re.sub(pattern, '', text)

    # Log the changes
    with open('link_removal.log', 'a', encoding='utf-8') as log_file:
        for match in matches:
            # Find the line containing the match
            match_start = match.start()
            line_index = next(i for i, line in enumerate(lines) if match_start < len('\n'.join(lines[:i+1])))
            original_line = lines[line_index]
            modified_line = re.sub(pattern, '', original_line)
            log_file.write(f"File: {file_path if file_path else 'N/A'}, Line: {line_index + 1}\n")
            log_file.write(f"Original: {original_line}\n")
            log_file.write(f"Modified: {modified_line}\n")
            log_file.write("\n")

    return no_links_text

def remove_junk(text):
    # Remove junk characters from the text
    text = re.sub(r'編輯原始碼', ' ', text)
    text = re.sub(r'List of current heads of state and government', ' ', text)
    text = re.sub(r'[0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3} --> [0-9]{2}:[0-9]{2}:[0-9]{2},[0-9]{3}', ' ', text) # Remove timestamps
    return text

def remove_after_marker(paragraph, file_path, citations_to_remove):
    """
    This function removes citations from a given text.
    The change is reported in citations_remove.log. For each change, the log includes the path to the file,
    and what was removed.
    """
    markerPositions=[]
    for markerString in citations_to_remove:
        pattern = rf'^\s*{re.escape(markerString.lower())}\s*$'
        matches = re.finditer(pattern, paragraph.lower(), re.MULTILINE)
        first_match = next(matches, None)
        if first_match:
            markerPositions.append(first_match.start())
    #Many articles have junk following a link to the Chinese Wikipedia. This code removes it.
    pattern = r'中文維基'
    matches = re.finditer(pattern, paragraph.lower())
    first_match = next(matches, None)
    if first_match:
        markerPositions.append(first_match.start())
    #Remove whatever was found
    markerPositions=[item for item in markerPositions if item != -1]
    if len(markerPositions) != 0:  # Make sure the marker string is found
        with open('citations_remove.log', 'a', encoding='utf-8') as log_file:
            log_file.write(f"File: {file_path if file_path else 'N/A'}\n")
            log_file.write(f"Trigger: {paragraph[min(markerPositions):min(markerPositions)+15]}\n")
            log_file.write(f"Removed: {paragraph[min(markerPositions):]}\n")
            log_file.write("\n")
        return paragraph[:min(markerPositions)]
    else:
        return paragraph  # If the marker string is not found, return the original paragraph    

def remove_citation_markers(text, file_path):
    """
    This function removes citation markers (numbers enclosed in square brackets) from a given text.
    The change is reported in citation_removal.log. For each change, the log includes the path to the file,
    the line number, the original line, and the line after removing the citation markers.
    """
    # Split the text into lines
    lines = text.split('\n')

    # Define the regular expression pattern to match citation markers
    pattern = r'\[\d+\]'

    # Find all matches of the pattern in the text
    matches = list(re.finditer(pattern, text))
    
    if not matches:
        return text  # No citation markers to remove

    # Remove the citation markers from the text
    no_citations_text = re.sub(pattern, ' ', text)

    # Log the changes
    with open('citation_marker_removal.log', 'a', encoding='utf-8') as log_file:
        for match in matches:
            # Find the line containing the match
            match_start = match.start()
            line_index = next(i for i, line in enumerate(lines) if match_start < len('\n'.join(lines[:i+1])))
            original_line = lines[line_index]
            modified_line = re.sub(pattern, '', original_line)
            log_file.write(f"File: {file_path if file_path else 'N/A'}, Line: {line_index + 1}\n")
            log_file.write(f"Original: {original_line}\n")
            log_file.write(f"Modified: {modified_line}\n")
            log_file.write("\n")

    return no_citations_text
   
def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    #print(reparsed.toprettyxml(indent="    "))
    return reparsed.toprettyxml(indent="    ")

def create_xml(articles_path, xml_path, lang_code, lang, citations_to_remove):
    today = datetime.today()
    date = datetime.today().strftime("%Y, %B %d")
    month = today.strftime("%B")

    print(f"creating XML of {lang_code}")

    for dir in os.listdir(articles_path):
        if dir.startswith("."):
            continue
        xml_lang_path = os.path.join(xml_path, dir)
        article_lang_path = os.path.join(articles_path, dir)
        if not os.path.exists(xml_lang_path):
            os.makedirs(xml_lang_path)
        for title in os.listdir(article_lang_path):
            if title.startswith("."):
                continue
            article = read_file_with_utf8(os.path.join(article_lang_path, title))
            if article is None:
                continue

            # Clean the page text using various functions
            article = unicodedata.normalize('NFC', article) #first thing is compose unicode characters
            article = remove_after_marker(article, os.path.join(article_lang_path, title), citations_to_remove)
            article = remove_citation_markers(article, os.path.join(article_lang_path)) # Remove citation markers
            article = remove_links(article, article_lang_path)             # Remove URLs
            article = remove_junk(article)   # Remove junk text
            article = re.sub(r'\(\)|\{\}|\[\]', ' ', article)    # Remove empty brackets
            article = re.sub(r'\(\s*\)', '', article)   # Remove empty parentheses
            article = re.sub(r'\s{2,}', ' ', article)   # Replace multiple spaces

            title = title.split(".")[0]
            root = Element("TEXT")
            root.set("id", f"Wiki_{dir}_{title}")
            root.set("xml:lang", lang_code)
            root.set("source", f"{lang} Wikipedia, article: {title}")
            root.set("copyright", "CC BY-SA")
            root.set("citation", f"{title}. ({date}). In Wikipedia [{lang}]. https://{lang_code}.wikipedia.org/wiki/{title}")
            root.set("BibTeX_citation", f"@misc{{Wiki_{lang_code}_{title}, title = {title}, year = {today.year}, month = {month}, day = {today.day}, note = {{In Wikipedia [{lang}]}}, url = {{https://{lang_code}.wikipedia.org/wiki/{title}}} }}")

            s_element = SubElement(root, "S")
            s_element.set("id", "0")

            form_element = SubElement(s_element, "FORM")
            form_element.set("kindOf", "original")
            form_element.text = article

            try:
                xml_string = prettify(root)
            except:
                xml_string = ""
                print(dir, title)

            with open(os.path.join(xml_lang_path, title+".xml"), "w", encoding="utf-8") as xmlfile:
                xmlfile.write(xml_string)
        

def main():
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    lang_codes = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}
    with open("citations_to_remove.pkl", 'rb') as fp:
        citations_to_remove = pickle.load(fp)
    for lang in ["Amis", "Seediq", "Atayal", "Sakizaya", "Paiwan"]:
        print(f"Cleaning and creating XML for {lang}")
        create_xml(os.path.join(curr_dir, "Articles"), os.path.join(curr_dir, "Final_XML"), lang_codes[lang], lang, citations_to_remove)    

if __name__ == "__main__":
    main()