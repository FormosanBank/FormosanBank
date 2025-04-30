import csv
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm 

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = tostring(elem, 'utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    # print(reparsed.toprettyxml(indent="    "))
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string


def download_audio(url, save_path, file_name, lang, dialect , failed_audio):
    """
    Download an audio file from the given URL and save it to the specified path.
    If the download fails, record the failure in 'failed_audio.csv' and append the ID to 'failed_ids'.
    """
    # Determine the path to 'failed_audio.csv' relative to 'save_path'
    try:
        # Send a GET request to the URL with streaming enabled
        response = requests.get(url, stream=True)
        # Check if the request was successful
        if response.status_code == 200:
            # Create the full file path for saving the audio file
            file_path = os.path.join(save_path, file_name)
            # Write the content to the file in chunks
            # with open(file_path, 'wb') as audio_file:
            #     for chunk in response.iter_content(chunk_size=1024):
            #         audio_file.write(chunk)
        else:
            # If the response status is not 200, record the failure
            id = file_name.split(".")[0].split("_")[-1]  # Extract the ID from the file name
            with open(failed_audio, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([url, file_name, lang, dialect, id, response.status_code])
            

    except Exception as e:
        # If an exception occurs, record the failure
        id = file_name.split(".")[0].split("_")[-1]
        with open(failed_audio, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([url, file_name, lang, dialect, id, e])
        

def download_all_audios(audio_urls, save_path, lang, dialect, failed_audio):
    """
    Download all audio files in the 'audio_urls' list concurrently.
    Returns a list of IDs for which the download failed.
    """
    with ThreadPoolExecutor(max_workers=500) as executor:  # Use up to 500 threads for parallel downloading
        # Map each audio URL to a future
        future_to_audio = {executor.submit(download_audio, url, save_path, file_name, lang, dialect, failed_audio): file_name for url, file_name in audio_urls}
        
        # Create a progress bar for tracking downloads
        with tqdm(total=len(audio_urls), desc="Downloading audio files") as pbar:
            for future in as_completed(future_to_audio):
                future.result()  # Wait for the download_audio function to complete
                pbar.update(1)  # Update the progress bar


def create_xml(curr_ePark, out_ePark, file, dialect, lang, lang_code, dir, ePark, failed_audio):
    """
    Create an XML file for the specified dialect and ePark version.
    Reads data from a CSV file, constructs XML elements, downloads associated audio files,
    and writes the resulting XML to a file.
    """
    print(f"in {ePark}, {dialect}, {file}...")
    # Define the output directories for XML and audio files
    xml_output = os.path.join(out_ePark, lang)
    audio_output = os.path.join(xml_output, "audio")
    
    # Create the output directories if they don't exist
    if not os.path.exists(xml_output):
        os.makedirs(xml_output)

    if not os.path.exists(audio_output):
        os.makedirs(audio_output)

    # Create the root element of the XML
    root = Element("TEXT")
    root.set("id", f"eP{ePark[-1]}_{dir}_{dialect}")
    root.set("xml:lang", lang_code)
    root.set("source", ePark + " " + dir + " " + dialect)
    root.set("audio", "diarized")
    root.set("copyright", "CC-BY-NC-SA")
    root.set("citation", "Indigenous Languages Research and Development Foundation. (2020). 族語E樂園. https://web.klokah.tw/")
    root.set("BibTeX_citation", "@misc{ePark, author = {Indigenous Languages Research and Development Foundation}, title = {族語E樂園}, year = {2020}, url = {https://web.klokah.tw/} }")

    audio_urls = list()  # Initialize the list of audio URLs and filenames

    # Open the CSV file containing the data
    with open(os.path.join(curr_ePark, file), mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        last_sent, s_id = None, -1
        for row_id, row in enumerate(reader):
            # Extract data from each row
            audio_url = row[-1]
            if ePark == "ePark1" and 'C' in audio_url.split('/')[-1]:
                form_word, chinese_word = row[:2]
                
                # Create a new 'S' element for each sentence
                word_element = SubElement(last_sent, "W")
                word_element.set("id", f"{s_id}-{row_id}")
                
                # Add the 'FORM' element containing the sentence
                form_element = SubElement(word_element, "FORM")
                form_element.text = form_word

                # Add the 'TRANSL' element containing the Chinese translation
                transl_element = SubElement(word_element, "TRANSL")
                transl_element.set("xml:lang", "zh")
                transl_element.text = chinese_word
                
                # Generate the audio file name and add it to the list for downloading
                audio_file = f"{dir}_{dialect}_{s_id}-{row_id}.{audio_url.split('.')[-1]}"
                audio_urls.append((audio_url, audio_file))
                
                # Add the 'AUDIO' element with the file name and URL
                audio_element = SubElement(word_element, "AUDIO")
                audio_element.set("file", audio_file)
                audio_element.set("url", audio_url)
                continue

            form_sentence, chinese_translation = row[:2]
            english_translation = ""
            
            if len(row)>3:
                # If there is an English translation, extract it
                form_sentence, english_translation, chinese_translation = row[:3]
            # Create a new 'S' element for each sentence
            s_element = SubElement(root, "S")
            s_element.set("id", str(row_id))
            
            # Add the 'FORM' element containing the sentence
            form_element = SubElement(s_element, "FORM")
            form_element.text = form_sentence

            # Add the 'TRANSL' element containing the Chinese translation
            transl_element = SubElement(s_element, "TRANSL")
            transl_element.set("xml:lang", "zh")
            transl_element.text = chinese_translation
            if english_translation!="":
                # If there is an English translation, add another 'TRANSL' element
                transl_element = SubElement(s_element, "TRANSL")
                transl_element.set("xml:lang", "en")
                transl_element.text = english_translation
            
            # Generate the audio file name and add it to the list for downloading
            audio_file = f"{dir}_{dialect}_{str(row_id)}.{audio_url.split('.')[-1]}"
            audio_urls.append((audio_url, audio_file))
            
            # Add the 'AUDIO' element with the file name and URL
            audio_element = SubElement(s_element, "AUDIO")
            audio_element.set("file", audio_file)
            audio_element.set("url", audio_url)
            
            if ePark == "ePark1":
                last_sent = s_element
                s_id = row_id

    print(f"in {ePark}, {dialect}, {file} audios...")
    # Download all audio files and get the list of failed IDs
    download_all_audios(audio_urls, audio_output, lang, dialect, failed_audio)

    try:
        # Generate the pretty-printed XML string
        xml_string = prettify(root)
    except:
        # If an error occurs during prettifying, print an error message
        xml_string = ""
        print(ePark, dir, dialect, lang, file)
    
    # Before write to path, validate output text for windows paths
    pattern = r'[<>:"|?*]'
    dialect = re.sub(pattern, '_', dialect)
    dialect = re.sub(r'_+', '_', dialect)
    output_path = os.path.join(xml_output, dialect+".xml")


    # Write to file
    # Write the XML string to a file
    with open(output_path, "w", encoding="utf-8") as xmlfile:
        xmlfile.write(xml_string)
        
        

def ePark1_2(curr_dir, dialects, lang_codes, ePark_ver):
    """
    Process ePark versions 1 and 2.
    Iterates over directories and files, and creates XML files for each dialect.
    """
    # Define the output directory for the final XML files
    output_dir = os.path.join(curr_dir, "Final_XML")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Iterate over the directories in the ePark version directory
    for dir in os.listdir(os.path.join(curr_dir, ePark_ver)):
        if dir.startswith('.'):
            continue  # Skip hidden directories

        # Define the current and output paths for the ePark version
        curr_ePark = os.path.join(curr_dir, ePark_ver, dir)
        out_ePark = os.path.join(output_dir, f"ep{ePark_ver[-1]}_"+dir)
        

        os.makedirs(out_ePark, exist_ok=True)

        failed = os.path.join(out_ePark, "failed_audio.csv")
        if not os.path.exists(failed):
            with open(failed, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["url", "file_name", "lang", "dialect", "id", "error"])
        # Get the list of files in the current ePark directory
        file_list = os.listdir(curr_ePark)
        file_list.sort()
        for file in file_list:
            idx = file.split(" ")[0]
            if not idx.isdigit():
                continue  # Skip files that do not start with a digit

            # Get the language and language code
            lang = dialects[idx].split("_")[-1]
            lang_code = lang_codes[lang]
            # Create the XML file for the current dialect
            create_xml(curr_ePark, out_ePark, file, dialects[idx], lang, lang_code, dir, "".join(ePark_ver.split("_")), failed)




def main():
    """
    Main function to process the dialects and create the XML files.
    """
    curr_dir = os.path.dirname(os.path.abspath(__file__))  # Get the current directory
    dialects = dict()
    # Define the language codes for each language
    lang_codes = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}
    # Read the dialects from 'dialects.csv'
    with open("dialects.csv", mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for _, row in enumerate(reader):
            dialects[row[0]] = row[1]

    # Process ePark versions 1 and 2
    #ePark1_2(curr_dir, dialects, lang_codes, "ePark_1")
    ePark1_2(curr_dir, dialects, lang_codes, "ePark_2")
    

if __name__ == "__main__":
    main()
