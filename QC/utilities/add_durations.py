import xml.etree.ElementTree as ET
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
import wave
import os
from xml.dom import minidom
from tqdm import tqdm


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


def add_durations(path, xml_file, durations):
    xml_file_path = os.path.join(path, xml_file)
    if not os.path.exists(xml_file_path):
        return
    
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    
    # Find all parent elements that contain AUDIO elements
    for parent in root.findall('.//AUDIO/..'):
        audio = parent.findall('.//AUDIO')[0]
        audio_file = audio.attrib.get("file", "")
        audio_path = xml_file_path.replace("Final_XML", "Final_audio").replace(".xml", "")
        audio_path = os.path.join(audio_path, audio_file)
        
        if audio_path not in durations:
            print(f"Removing AUDIO element for missing duration: {audio_path}")
            parent.remove(audio)  # Remove the AUDIO element
        else:
            audio.set("start", "0")
            audio.set("end", str(round(durations[audio_path], 2)))
    
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)
    print(f"Updated file: {xml_file_path}")
        

def process_file(path, file_name):
    """Process a single file"""
    file_path = os.path.join(path, file_name)
    try:
        if file_path.endswith('.mp3'):
            audio = MP3(file_path)
            length_in_sec = audio.info.length
            if audio is None or length_in_sec is None or length_in_sec == 0:
                raise Exception("problem with audio file")
            
        elif file_path.endswith('.wav'):
            with wave.open(file_path, "rb") as wav_file:  # Use correct extension if renamed
                length_in_sec = wav_file.getnframes() / wav_file.getframerate()
                if length_in_sec == 0:
                    raise Exception("problem with audio file")
    except Exception as e:
        # print(e, file_path)
        return
    return length_in_sec


def main(corpus_path):
    to_process = list()
    for root, dirs, files in os.walk(corpus_path):
        for file in files:
            if (file.endswith(".xml")):
                to_process.append([root, file])
    
    for root, xmlfile in to_process:
        audio_dir = os.path.join(root.replace("Final_XML", "Final_audio"), xmlfile.split('.')[0])
        audio_to_process = list()
        for audio_file in os.listdir(audio_dir):
            if audio_file.endswith(".mp3") or audio_file.endswith(".wav"):
                audio_to_process.append([audio_dir, audio_file])
        
        res = dict()
        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_file, path, file): (path, file) for path, file in audio_to_process}
            for f in tqdm(as_completed(futures), total=len(futures), desc=f"Processing {os.path.join(root, xmlfile)}"): 
                path, file = futures[f]
                tmp = f.result()
                if tmp: res[os.path.join(path, file)] = tmp
        add_durations(root, xmlfile, res)
        # exit()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="add the start and end attribute to AUDIO tags in a corpus with segmented audio")
    parser.add_argument('--path', help='the path to the Final_XML folder containing the xml files associated with a corpus')
    args = parser.parse_args()
    main(args.path)
