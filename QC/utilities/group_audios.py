import argparse
import os
import xml.etree.ElementTree as ET
import shutil
from tqdm import tqdm

def get_audios(root, file):
    tree = ET.parse(os.path.join(root, file))
    root = tree.getroot()
    if "audio" not in root.attrib or root.attrib["audio"] != "diarized":
        return None
    to_return = list()
    # Iterate over all <AUDIO> elements
    for audio in root.findall('.//AUDIO'):
        audio_file = audio.attrib["file"]
        to_return.append(audio_file)
    return to_return

def main(path):
    """
    The main purpose of this function is to group the audios of every single XML file in a
    seperate folder to easen processing. The assumed structure is that:
    path/to/corpus/Final_XML/xml_file.xml
    path/to/corpus/Final_audio/xml_file/*.mp3
    """
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml") and 'Final_XML' in os.path.join(root, file):
                # print(root, file)
                if not os.path.exists(root.replace("Final_XML", "Final_audio")):
                    continue
                    #raise Exception(f"the directory {root.replace("Final_XML", "Final_audio")} doesn't exist which should contain audio files for {os.path.join(root, file)}")
                audios = get_audios(root, file)
                if audios is None:
                    continue
                tmp_dir = os.path.join(root.replace("Final_XML", "Final_audio"), file.split(".")[0])
                os.makedirs(tmp_dir, exist_ok=True)
                for audio_file in tqdm(audios, total=len(audios), desc=f"processing {os.path.join(root, file)}"):
                    
                    audio_path = os.path.join(root.replace("Final_XML", "Final_audio"), audio_file)
                    if os.path.exists(audio_path):
                        shutil.move(audio_path, os.path.join(tmp_dir, audio_file))
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Group audio files for an XML file.")
    parser.add_argument('--path', help="the Final_XML path which will be explored.")
    args = parser.parse_args()
    if not os.path.exists(args.path):
        parser.error("entered path doesn't exist")
    
    main(args.path)