import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
import csv
import shutil
from tqdm import tqdm
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import threading

def prettify(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")

def create_root(ePark, dialect, lang):
    root = ET.Element("TEXT")
    root.set("id", f"eP3_{ePark}_{dialect}")
    root.set("xml:lang", lang)
    root.set("source", f"ePark3 {ePark} {dialect}")
    root.set("audio", "diarized")
    root.set("copyright", "CC-BY-NC-SA")
    root.set("citation", "Indigenous Languages Research and Development Foundation. (2020). 族語E樂園. https://web.klokah.tw/")
    root.set("BibTeX_citation", "@misc{ePark, author = {Indigenous Languages Research and Development Foundation}, title = {族語E樂園}, year = {2020}, url = {https://web.klokah.tw/} }")
    return root

def process_match_items(item, types, audio_path, type_id, class_num):
    """
    Processes items of 'match' type, which consist of pairs of sentences and translations.

    Parameters:
        item (Element): The XML item element to process.
        types (dict): A dictionary mapping type IDs to type names.
        audio_path (str): The base path to the audio files.
        type_id (str): The type ID of the item.
        class_num (str): The class number from the item.

    Returns:
        list of tuples: Each tuple contains (sentence, translation, audio_path).
    """
    to_return = list()
    curr = 'A'
    while True:
        sentence, trans = "", ""
        s1, s2 = item.find(f"match{curr}AbA"), item.find(f"match{curr}AbB")
        t1, t2 = item.find(f"match{curr}ChA"), item.find(f"match{curr}ChB")
        if s1 is None or t1 is None:
            break
        sentence = s1.text + " " + s2.text
        trans = t1.text + " " + t2.text
        audio_filename = f"{class_num}_{item.find('matchOrder').text}_{curr}.mp3"
        audio = os.path.join(audio_path, type_id + types[type_id], audio_filename)
        if not os.path.exists(audio):
            audio = None
        to_return.append((sentence, trans, audio))
        curr = chr(ord(curr)+1)
    return to_return

def process_multiple_sentences_single_audio(item, types, audio_path, type_id, class_num):
    """
    Processes items where multiple sentences share a single audio file.

    Parameters:
        item (Element): The XML item element to process.
        types (dict): A dictionary mapping type IDs to type names.
        audio_path (str): The base path to the audio files.
        type_id (str): The type ID of the item.
        class_num (str): The class number from the item.

    Returns:
        list of tuples: Each tuple contains (combined_sentence, combined_translation, audio_path).
    """
    audio_filename = f"{class_num}_{item.find(f'{types[type_id]}Order').text}.mp3"
    audio = os.path.join(audio_path, type_id + types[type_id], audio_filename)
    if not os.path.exists(audio):
        audio = None

    sentence, trans, curr = "", "", 'A'
    while True:
        s = item.find(f"{types[type_id]}{curr}Ab")
        t = item.find(f"{types[type_id]}{curr}Ch")
        if s is None or t is None:
            break

        s_text, t_text = s.text, t.text
        if s_text is None or t_text is None or s_text.isspace():
            break

        sentence += s_text
        trans += t_text
        curr = chr(ord(curr)+1)
    return [(sentence, trans, audio)]

def process_multiple_sentences_multiple_audio(item, types, audio_path, type_id, class_num):
    """
    Processes items where each sentence has its own audio file.

    Parameters:
        item (Element): The XML item element to process.
        types (dict): A dictionary mapping type IDs to type names.
        audio_path (str): The base path to the audio files.
        type_id (str): The type ID of the item.
        class_num (str): The class number from the item.

    Returns:
        list of tuples: Each tuple contains (sentence, translation, audio_path).
    """
    to_return = list()
    curr = 'A'
    while True:
        s = item.find(f"{types[type_id]}{curr}Ab")
        t = item.find(f"{types[type_id]}{curr}Ch")
        if s is None or t is None:
            break
        audio_filename = f"{class_num}_{item.find(f'{types[type_id]}Order').text}_{curr}.mp3"
        audio = os.path.join(audio_path, type_id + types[type_id], audio_filename)
        if not os.path.exists(audio):
            audio = None
        to_return.append((s.text, t.text, audio))
        curr = chr(ord(curr)+1)
    return to_return

def process_single_sentence_item(item, types, audio_path, type_id, class_num):
    """
    Processes items that contain a single sentence and translation.

    Parameters:
        item (Element): The XML item element to process.
        types (dict): A dictionary mapping type IDs to type names.
        audio_path (str): The base path to the audio files.
        type_id (str): The type ID of the item.
        class_num (str): The class number from the item.

    Returns:
        list of tuples: Each tuple contains (sentence, translation, audio_path).
    """
    audio_filename = f"{class_num}_{item.find(f'{types[type_id]}Order').text}.mp3"
    audio = os.path.join(audio_path, type_id + types[type_id], audio_filename)
    if not os.path.exists(audio):
        audio = None
    return [(item.find(f"{types[type_id]}Ab").text,  item.find(f"{types[type_id]}Ch").text, audio)]

def process_item_by_type(ePark, item, types, audio_path):
    """
    Processes an XML item based on its type ID and ePark topic.

    Parameters:
        ePark (str): The ePark topic.
        item (Element): The XML item element to process.
        types (dict): A dictionary mapping type IDs to type names.
        audio_path (str): The base path to the audio files.

    Returns:
        list of tuples: Each tuple contains (sentence, translation, audio_path).
    """
    type_id = item.find("typeId").text
    class_num = item.find("classNo").text

    if ePark == "句型篇國中":
        if type_id in ["1", "3"]:
            return process_single_sentence_item(item, types, audio_path, type_id, class_num)
        elif type_id == "2":
            return process_multiple_sentences_single_audio(item, types, audio_path, type_id, class_num)
        elif type_id in ["4", "5", "9"]:
            return process_multiple_sentences_multiple_audio(item, types, audio_path, type_id, class_num)
        elif type_id == "6":
            return process_match_items(item, types, audio_path, type_id, class_num)
        elif type_id == "10":
            if item.find("pictureTalkAb").text is None:
                return None
            return process_single_sentence_item(item, types, audio_path, type_id, class_num)

    elif ePark == "句型篇高中":
        if type_id in ["1", "3", "7"]:
            return process_single_sentence_item(item, types, audio_path, type_id, class_num)
        elif type_id in ["2", "4"]:
            return process_multiple_sentences_single_audio(item, types, audio_path, type_id, class_num)
        elif type_id in ["5", "8", "9"]:
            return process_multiple_sentences_multiple_audio(item, types, audio_path, type_id, class_num)
        elif type_id == "10":
            if item.find("pictureTalkAb").text is None:
                return None
            return process_single_sentence_item(item, types, audio_path, type_id, class_num)

def process_epark_sentence_patterns(ePark, path, output_path, dialects, lang_codes):
    """
    Processes the ePark '句型篇國中' and '句型篇高中' topics.

    Parameters:
        ePark (str): The ePark topic, either '句型篇國中' or '句型篇高中'.
        path (str): The base path to the data.
        output_path (str): The path where the output XML and audio will be saved.
        dialects (dict): A dictionary mapping indices to dialect names.
        lang_codes (dict): A dictionary mapping language names to ISO codes.
    """
    types = {"1":"word", "2":"sentence", "3":"recognize", "4":"choiceOne", 
             "5":"choiceTwo", "6":"match", "7":"choiceThree", "8":"oralReading", "9":"dialogue", "10":"pictureTalk"}

    xml_path = os.path.join(path, "xml")
    audio_path = os.path.join(path, "sound")
    for idx in tqdm(os.listdir(xml_path), desc= f"Processing {ePark}:"):
        if not idx.isdigit():
            continue

        dialect = dialects[idx if len(idx) > 1 else "0"+idx]
        dialect_path = os.path.join(xml_path, idx)
        lang = dialect.split("_")[-1]
        xml_output = os.path.join(output_path, "ep3_"+ePark, lang)
        audio_output = os.path.join(xml_output, "audio")
        os.makedirs(xml_output, exist_ok=True)
        os.makedirs(audio_output, exist_ok=True)
        
        root = create_root(ePark, dialect, lang_codes[lang])
        
        for file in os.listdir(dialect_path):
            tree = ET.parse(os.path.join(dialect_path, file))
            to_read_root = tree.getroot()
            
            for item in to_read_root.findall('.//item'):
                to_append = process_item_by_type(ePark, item, types, os.path.join(audio_path, idx))
                if to_append:
                    for i, entry in enumerate(to_append):
                        id = item.find("autoId").text if i == 0 else item.find("autoId").text+f"_{i}"
                        form, trans, audio = entry
                        s_element = ET.SubElement(root, "S")
                        s_element.set("id", id)
                        
                        form_element = ET.SubElement(s_element, "FORM")
                        form_element.text = form

                        transl_element = ET.SubElement(s_element, "TRANSL")
                        transl_element.set("xml:lang", "zh")
                        transl_element.text = trans
                        
                        if audio:
                            audio_element = ET.SubElement(s_element, "AUDIO")
                            audio_element.set("file", id + ".mp3")
                            if not os.path.exists(os.path.join(audio_output, id + ".mp3")):
                                try:
                                    shutil.copy(audio, os.path.join(audio_output, id + ".mp3"))
                                except:
                                    print(f"Failed to copy audio: {idx}, {file}")
        try:
            xml_string = prettify(root)
        except Exception as e:
            xml_string = ""
            print(f"Failed to format XML: {dialect}, {ePark}, {idx}, Error: {e}")

        # Before write to path, validate output text for windows paths
        output_path = os.path.join(xml_output, dialect+".xml")
        pattern = r'[<>:"|?*]'
        output_path = re.sub(pattern, '_', output_path)
        output_path = re.sub(r'_+', '_', output_path)
        # Write to file
        with open(output_path, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xml_string)

def download_audio(save_path, url, file_name):
    """
    Downloads an audio file from a URL to a specified path.

    Parameters:
        save_path (str): The directory where the audio file will be saved.
        url (str): The URL to download the audio from.
        file_name (str): The name of the file to save.

    Returns:
        tuple: (success, error_info)
            success (bool): True if download was successful, False otherwise.
            error_info (str): Error information if download failed.
    """
    if os.path.exists(os.path.join(save_path, file_name)):
        return True, None
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(save_path, file_name)
            with open(file_path, 'wb') as audio_file:
                for chunk in response.iter_content(chunk_size=1024):
                    audio_file.write(chunk)
            return True, None
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def process_data_point(data_point, dialects, audio_output_dict, download_url, ePark, failed_audio_entries, s_elements_dict):
    """
    Processes a single data point from the CSV file.

    Parameters:
        data_point (list): The data point to process.
        dialects (dict): A dictionary mapping indices to dialect names.
        audio_output_dict (dict): A dictionary mapping indices to audio output paths.
        download_url (str): The base URL for downloading audio files.
        ePark (str): The ePark topic.
        failed_audio_entries (list): A list to collect entries for which audio download failed.
        s_elements_dict (dict): A dictionary to collect 'S' elements for each index.
    """
    failed_audio_lock = threading.Lock()
    
    idx = data_point[2] if len(data_point[2]) > 1 else '0'+data_point[2]
    dialect = dialects[idx]
    lang = dialect.split("_")[-1]
    audio_output = audio_output_dict[idx]

    s_element = ET.Element("S")
    s_element.set("id", data_point[0])

    form_element = ET.SubElement(s_element, "FORM")
    form_element.text = data_point[3]

    transl_element = ET.SubElement(s_element, "TRANSL")
    transl_element.set("xml:lang", "zh")
    transl_element.text = data_point[4]

    audio_url = f"{download_url}/{data_point[1]}/{data_point[0]}.mp3"
    audio_file = f"{ePark}_{dialect}_{data_point[0]}.mp3"

    success, error_info = download_audio(audio_output, audio_url, audio_file)

    if success:
        audio_element = ET.SubElement(s_element, "AUDIO")
        audio_element.set("file", audio_file)
        audio_element.set("url", audio_url)
    else:
        id = data_point[0]
        error_entry = [audio_url, audio_file, lang, dialect, id, error_info]
        with failed_audio_lock:
            failed_audio_entries.append(error_entry)

    s_elements_dict[idx].append(s_element)

def process_epark_topics_with_csv(ePark, path, output_path, dialects, lang_codes, data_file, download_url):
    """
    Processes ePark topics that have data in CSV files and audio files available via URLs.

    Parameters:
        ePark (str): The ePark topic.
        path (str): The base path to the data.
        output_path (str): The path where the output XML and audio will be saved.
        dialects (dict): A dictionary mapping indices to dialect names.
        lang_codes (dict): A dictionary mapping language names to ISO codes.
        data_file (str): The CSV file containing the data points.
        download_url (str): The base URL for downloading audio files.
    """
    data = {}
    with open(os.path.join(path, data_file), mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for row in reader:
            data[row[0]] = row

    xml_dict = {}
    s_elements_dict = defaultdict(list)
    xml_output_dict = {}
    audio_output_dict = {}
    failed_audio_entries = []
    
    # Initialize XML roots and output paths
    for idx in dialects:
        dialect = dialects[idx]
        lang = dialect.split("_")[-1]

        root = create_root(ePark, dialect, lang_codes[lang])
        xml_dict[idx] = root

        xml_output = os.path.join(output_path, "ep3_"+ePark, lang)
        audio_output = os.path.join(xml_output, "audio")
        os.makedirs(xml_output, exist_ok=True)
        os.makedirs(audio_output, exist_ok=True)

        xml_output_dict[idx] = xml_output
        audio_output_dict[idx] = audio_output

    # Multithreading setup
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(process_data_point, data[entry], dialects, audio_output_dict, download_url, ePark, failed_audio_entries, s_elements_dict) for entry in data]
        for future in tqdm(as_completed(futures), desc= f"Processing {ePark}:", total=len(data)):
            pass
    
    if ePark == "文化篇":
        # Process additional data for '文化篇'
        failed_audio = []
        data_words = {}
        with open(os.path.join(path, "klokah_cuture_word.csv"), mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            for i, row in enumerate(reader):
                data_words[i] = row

        for entry in data_words:
            data_point = data_words[entry]

            idx = data_point[0]
            dialect = dialects[idx if len(idx) > 1 else '0'+idx]
            lang = dialect.split("_")[-1]
            audio_output = audio_output_dict[idx if len(idx) > 1 else '0'+idx]

            id = data_point[0]+"_"+data_point[1]+"_W"+data_point[2]
            s_element = ET.Element("S")
            s_element.set("id", id)

            form_element = ET.SubElement(s_element, "FORM")
            form_element.text = data_point[3]

            transl_element = ET.SubElement(s_element, "TRANSL")
            transl_element.set("xml:lang", "zh")
            transl_element.text = data_point[4]
            
            audio = os.path.join(path, idx, f"{data_point[0]}_{data_point[1]}_V{data_point[2]}.mp3")
            if os.path.exists(audio):
                audio_element = ET.SubElement(s_element, "AUDIO")
                audio_element.set("file", id + ".mp3")
                if not os.path.exists(os.path.join(audio_output, id + ".mp3")):
                    try:
                        shutil.copy(audio, os.path.join(audio_output, id + ".mp3"))
                    except:
                        print(f"Failed to copy audio: {idx}, {id}")
            else:
                failed_audio.append([ePark, audio, lang, dialect, idx, id])
            root = xml_dict[idx if len(idx) > 1 else '0'+idx]
            root.append(s_element)

        with open(os.path.join(output_path, "ep3_"+ePark, "failed_audio_copy.csv"), mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["ePark topic", "audio path", "lang", "dialect", "idx", "id"])
            writer.writerows(failed_audio)
            
    # Append S elements to XML trees
    for idx in xml_dict:
        root = xml_dict[idx]
        for s_element in s_elements_dict[idx]:
            root.append(s_element)

        xml_output = xml_output_dict[idx]
        dialect = dialects[idx]
        try:
            xml_string = prettify(root)
        except Exception as e:
            xml_string = ""
            print(f"Failed to format XML: {ePark}, {dialect}, {idx}, Error: {e}")
        
        if len(root.findall('.//S')) > 0:
            with open(os.path.join(xml_output, dialect+".xml"), "w", encoding="utf-8") as xmlfile:
                xmlfile.write(xml_string)
    
    # Write failed audio entries
    failed_audio_file = os.path.join(output_path, "ep3_"+ePark, "failed_audio_download.csv")
    with open(failed_audio_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["url", "file_name", "lang", "dialect", "id", "error"])
        writer.writerows(failed_audio_entries)

def process_topics4and5_items(item, tag_org, tag_zh, root, path, idx, audio_output, ePark, lang, dialect, failed_audio):
    """
    Processes items for '生活會話篇' and '閱讀書寫篇' topics.

    Parameters:
        item (Element): The XML item element to process.
        tag_org (str): The tag prefix for the original sentences.
        tag_zh (str): The tag prefix for the Chinese translations.
        root (Element): The root XML element to append to.
        path (str): The base path to the data.
        idx (str): The index of the dialect.
        audio_output (str): The path to save audio files.
        ePark (str): The ePark topic.
        lang (str): The language code.
        dialect (str): The dialect name.
        failed_audio (list): A list to collect entries for which audio is missing.
    """
    i = 1
    while True:
        sen, trans = item.find(f"{tag_org}{i}"), item.find(f"{tag_zh}{i}")
        if sen is None or trans is None:
            break

        sen, trans = sen.text, trans.text
        if sen is None or trans is None or sen == "" or sen.isspace():
            break

        if tag_org == "con_AB":
            id = item.find("lessonId").text + f"S_{i}"
        elif tag_org == "word_AB":
            id = item.find("lessonId").text + f"W_{i}"
        elif tag_org == "Ab_":
            id = item.find("lessonNo").text + f"W_{i}"

        s_element = ET.SubElement(root, "S")
        s_element.set("id", id)
        
        form_element = ET.SubElement(s_element, "FORM")
        form_element.text = sen

        transl_element = ET.SubElement(s_element, "TRANSL")
        transl_element.set("xml:lang", "zh")
        transl_element.text = trans

        if tag_org == "con_AB":
            audio = os.path.join(path, idx, "sentence", f"{idx}c{item.find('lessonId').text}s{i}.mp3")
        elif tag_org == "word_AB":
            audio = os.path.join(path, idx, "word", f"{idx}c{item.find('lessonId').text}w{i}.mp3")
        elif tag_org == "Ab_":
            audio = os.path.join(path, idx, "sound", f"{idx}_{item.find('lessonNo').text}_V{i}.mp3")
        
        if os.path.exists(audio):
            audio_element = ET.SubElement(s_element, "AUDIO")
            audio_element.set("file", id + ".mp3")
            if not os.path.exists(os.path.join(audio_output, id + ".mp3")):
                try:
                    shutil.copy(audio, os.path.join(audio_output, id + ".mp3"))
                except:
                    print(f"Failed to copy audio: {idx}, {id}")
        else:
            failed_audio.append([ePark, audio, lang, dialect, idx, id])
        i += 1

def process_epark_conversation_reading(ePark, path, output_path, dialects, lang_codes, xml_file):
    """
    Processes the ePark '生活會話篇' and '閱讀書寫篇' topics.

    Parameters:
        ePark (str): The ePark topic.
        path (str): The base path to the data.
        output_path (str): The path where the output XML and audio will be saved.
        dialects (dict): A dictionary mapping indices to dialect names.
        lang_codes (dict): A dictionary mapping language names to ISO codes.
        xml_file (str): The XML file name to process.
    """
    failed_audio = []
    audio_output_dict = {}
    xml_dict = {}
    xml_output_dict = {}
    s_elements_dict = defaultdict(list)

    for idx in tqdm(os.listdir(path),  desc= f"Processing {ePark}:"):
        if not idx.isdigit():
            continue
        tree = ET.parse(os.path.join(path, idx, xml_file))
        to_read_root = tree.getroot()

        dialect = dialects[idx if len(idx) > 1 else "0"+idx]
        lang = dialect.split("_")[-1]
        xml_output = os.path.join(output_path, "ep3_"+ePark, lang)
        audio_output = os.path.join(xml_output, "audio")
        os.makedirs(xml_output, exist_ok=True)
        os.makedirs(audio_output, exist_ok=True)

        root = create_root(ePark, dialect, lang_codes[lang])        
        xml_dict[idx if len(idx) > 1 else "0"+idx] = root
        audio_output_dict[idx if len(idx) > 1 else "0"+idx] = audio_output
        xml_output_dict[idx if len(idx) > 1 else "0"+idx] = xml_output

        for item in to_read_root.findall('.//lesson'):
            if ePark == "生活會話篇":
                id = item.find("lessonId").text
            elif ePark == "閱讀書寫篇":
                id = item.find("lessonNo").text
            
            s_element = ET.SubElement(root, "S")
            s_element.set("id", id)
            
            form_element = ET.SubElement(s_element, "FORM")
            if ePark == "生活會話篇":
                form_element.text = item.find("lessonAB").text
            elif ePark == "閱讀書寫篇":
                form_element.text = item.find("lessonAb").text

            transl_element = ET.SubElement(s_element, "TRANSL")
            transl_element.set("xml:lang", "zh")
            if ePark == "生活會話篇":
                transl_element.text = item.find("lessonCH").text
            elif ePark == "閱讀書寫篇":
                transl_element.text = item.find("lessonCh").text
           
        if ePark == "生活會話篇":
            for item in to_read_root.findall('.//content'):
                process_topics4and5_items(item, "con_AB", "con_CH", root, path, idx, audio_output, ePark, lang, dialect, failed_audio)
            for item in to_read_root.findall(".//word"):
                process_topics4and5_items(item, "word_AB", "word_CH", root, path, idx, audio_output, ePark, lang, dialect, failed_audio)
        
        elif ePark == "閱讀書寫篇":
            for item in to_read_root.findall('.//vocabulary'):
                process_topics4and5_items(item, "Ab_", "Ch_", root, path, idx, audio_output, ePark, lang, dialect, failed_audio)

    with open(os.path.join(output_path, "ep3_"+ePark, "failed_audio_copy.csv"), mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["ePark topic", "audio path", "lang", "dialect", "idx", "id"])
        writer.writerows(failed_audio)
    
    if ePark == "閱讀書寫篇":
        data = {}
        failed_audio_entries = []

        with open(os.path.join(path, "klokah_reading_sentence.csv"), mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip header row
            for row in reader:
                data[row[0]] = row
                
        with ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(process_data_point, data[entry], dialects, audio_output_dict, "https://web.klokah.tw/text/sound/", ePark, failed_audio_entries, s_elements_dict) for entry in data]
            for future in tqdm(as_completed(futures), desc= f"Processing {ePark}:", total=len(data)):
                pass
        
        failed_audio_file = os.path.join(output_path, "ep3_"+ePark, "failed_audio_download.csv")
        with open(failed_audio_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["url", "file_name", "lang", "dialect", "id", "error"])
            writer.writerows(failed_audio_entries)
        
    for idx in xml_dict:
        root = xml_dict[idx]
        for s_element in s_elements_dict[idx]:
            root.append(s_element)

        xml_output = xml_output_dict[idx]
        dialect = dialects[idx]
        try:
            xml_string = prettify(root)
        except Exception as e:
            xml_string = ""
            print(f"Failed to format XML: {ePark}, {dialect}, {idx}, Error: {e}")

        with open(os.path.join(xml_output, dialect+".xml"), "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xml_string)

def main():
    dialects = dict()
    lang_codes = {"Amis":"ami", "Atayal":"tay", "Saisiyat":"xsy", "Thao":"ssf", "Seediq":"trv", "Bunun":"bnn", 
                  "Paiwan":"pwn", "Rukai":"dru", "Truku":"trv", "Kavalan":"ckv", "Tsou":"tsu", "Kanakanavu":"xnb", 
                  "Saaroa":"sxr", "Puyuma":"pyu", "Yami":"tao", "Sakizaya":"szy"}
    with open("dialects.csv", mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip header row
        for _, row in enumerate(reader):
            dialects[row[0]] = row[1]

    process_epark_sentence_patterns("句型篇國中", "./ePark_3/1.句型篇國中", "./Final_XML", dialects, lang_codes)
    process_epark_sentence_patterns("句型篇高中", "./ePark_3/2.句型篇高中", "./Final_XML", dialects, lang_codes)
    process_epark_topics_with_csv("圖畫故事篇", "./ePark_3/3.圖畫故事篇", "./Final_XML", dialects, lang_codes, "klokah_story_sentence.csv", "https://web.klokah.tw/text/sound/")
    process_epark_conversation_reading("生活會話篇", "./ePark_3/4.生活會話篇", "./Final_XML", dialects, lang_codes, "conversation.xml")
    process_epark_conversation_reading("閱讀書寫篇", "./ePark_3/5.閱讀書寫篇", "./Final_XML", dialects, lang_codes, "reading.xml")
    process_epark_topics_with_csv("文化篇", "./ePark_3/6.文化篇", "./Final_XML", dialects, lang_codes, "klokah_cuture_sentence.csv", "https://web.klokah.tw/text/sound/")
    process_epark_topics_with_csv("情境族語", "./ePark_3/7.情境族語", "./Final_XML", dialects, lang_codes, "klokah_dialogue_sentence.csv", "https://web.klokah.tw/text/sound/")
    process_epark_topics_with_csv("族語短文", "./ePark_3/8.族語短文", "./Final_XML", dialects, lang_codes, "klokah_essay_sentence.csv", "https://web.klokah.tw/text/sound/")
    process_epark_topics_with_csv("繪本平台", "./ePark_3/9.繪本平台", "./Final_XML", dialects, lang_codes, "klokah_PBC_sentence.csv", "https://web.klokah.tw/text/sound/")

if __name__ == "__main__":
    main()
