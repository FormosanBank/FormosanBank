import xml.etree.ElementTree as ET
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
import wave
import xml.etree.ElementTree as ET
import os
from xml.dom import minidom
from collections import defaultdict

to_process = defaultdict(list)

def prettify(elem):
    """
    Return a pretty-printed XML string for the Element.

    Args:
        elem (xml.etree.ElementTree.Element): The XML element to pretty-print.

    Returns:
        str: A pretty-printed XML string.
    """
    rough_string = ET.tostring(elem, 'utf-8')  # Convert the Element to a byte string
    reparsed = minidom.parseString(rough_string)  # Parse the byte string using minidom
    return reparsed.toprettyxml(indent="    ")  # Return the pretty-printed XML string


def add_durations():
    
    for file in to_process:
        tree = ET.parse(file)
        root = tree.getroot()

        for s_id, duration in to_process[file]:
            sentence = root.find(f".//S[@id='{s_id}']")
            if sentence is None:
                print(s_id, file)
            audio_element = sentence.find("AUDIO")
            audio_element.set("start", "0")
            audio_element.set("end", str(round(duration, 2)))
              
            
        try:
            xml_string = prettify(root)
            xml_string = '\n'.join([line for line in xml_string.split('\n') if line.strip() != ''])
        except Exception as e:
            xml_string = ""
            print(f"Failed to format file: {file}, Error: {e}")

        with open(file, "w", encoding="utf-8") as xmlfile:
            xmlfile.write(xml_string)
            print(f"file: {file} modified successfully")
        

def process_file(path, file_name):
    """Process a single file"""
    file_path = os.path.join(path, file_name)
    try:
        if file_path.endswith('.mp3'):
            audio = MP3(file_path)
            length_in_sec = audio.info.length
            if audio is None or length_in_sec is None or length_in_sec == 0:
                raise Exception("problem iwth audio file")
            
        elif file_path.endswith('.wav'):
            with wave.open(file_path, "rb") as wav_file:  # Use correct extension if renamed
                length_in_sec = wav_file.getnframes() / wav_file.getframerate()
                if length_in_sec == 0:
                    raise Exception("problem iwth audio file")
    except Exception as e:
        print(e, file_path)
        return
    xml_file = os.path.join(path.replace('Final_audio', 'Final_XML'), file_name.split('_')[0] + ".xml")
    to_process[xml_file].append([file_name.split(".")[0], length_in_sec])

def check_source(path):
    to_process = list()
    for root, dirs, files in os.walk(path):
        for file in files:
            if (file.endswith(".wav") or file.endswith('.mp3')) and 'audio' in os.path.join(root, file):
                to_process.append([root, file])
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, path, file) for path, file in to_process]
        for f in as_completed(futures): f.result()
                
    
def main(corpora_path):
    for source in os.listdir(corpora_path):
        if source.startswith('.'):
            continue
        if os.path.isdir(os.path.join(corpora_path, source)):
            check_source(os.path.join(corpora_path, source))
    add_durations()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get durations of audio per corpus and per language.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    args = parser.parse_args()
    main(args.corpora_path)
