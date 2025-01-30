import xml.etree.ElementTree as ET
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
import wave
import csv
import sndhdr
from tqdm import tqdm

"""
The main functionality of this validation test is to check the functionality of audio files associated with a corpus.
The following folder structure is assumed
path/to/corpus/Final_XML/
path/to/corpus/Final_audio/
and the path to Final_audio is the one to be provided as arg for the main
"""


# Determine the language of the file based on the path
def get_lang(path, file):
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun','Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
        'Thao', 'Kavalan', 'Truku', 'Sakizaya','Seediq','Saaroa', 'Kanakanavu', 'Siraya']
    for lang in langs:
        if lang in path or (file.split('.')[0] == lang and file.split('.')[1:] == ['xml']):
            return lang

def process_file(path, file_name, failed_audio):
    """Process a single file"""
    file_path = os.path.join(path, file_name)
    lang = get_lang(path, file_name)
    if file_path.endswith('.mp3'):
        # filetype = sndhdr.what(file_path)
        # if filetype and filetype.filetype == 'wav':
        #     print(file_path)
        try:
            audio = MP3(file_path)
            length_in_sec = audio.info.length
            if audio is None or length_in_sec is None or length_in_sec == 0:
                raise Exception("problem with audio file")
        except Exception as e:
            with open(failed_audio, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([path, lang, file_name])
    elif file_path.endswith('.wav'):
        try:
            with wave.open(file_path, "rb") as wav_file:  # Use correct extension if renamed
                length_in_sec = wav_file.getnframes() / wav_file.getframerate()
                if length_in_sec == 0:
                    raise Exception("problem with audio file")
        except:
            with open(failed_audio, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([path, lang, file_name])
                
    
def main(corpus_audio_path):
    failed_audio = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "non_working_audio.csv")
    
    with open(failed_audio, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["path", "lang", "file_name"])
    
    to_process = list()
    for root, dirs, files in os.walk(corpus_audio_path):
        for file in files:
            if (file.endswith(".wav") or file.endswith('.mp3')) and 'audio' in os.path.join(root, file):
                to_process.append([root, file])
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, path, file, failed_audio) for path, file in to_process]
        for f in tqdm(as_completed(futures), total=len(futures), desc=f"checking {corpus_audio_path}"): 
            f.result()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="validates the functionality of audio files associated with a corpus")
    parser.add_argument('--path', help='the path to the Final_audio folder containing the audio files associated with a corpus')
    args = parser.parse_args()
    main(args.path)
