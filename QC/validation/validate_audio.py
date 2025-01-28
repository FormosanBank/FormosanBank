import xml.etree.ElementTree as ET
import os
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
import wave
import csv
import sndhdr


def process_file(path, file, failed_audio):
    """Process a single file"""
    file_path = os.path.join(path, file)
    if file_path.endswith('.mp3'):
        # filetype = sndhdr.what(file_path)
        # if filetype and filetype.filetype == 'wav':
        #     print(file_path)
        try:
            audio = MP3(file_path)
            length_in_sec = int(audio.info.length)
        except Exception as e:
            print(file, e)
            with open(failed_audio, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([file_path])
    elif file_path.endswith('.wav'):
        try:
            with wave.open(file_path, "rb") as wav_file:  # Use correct extension if renamed
                length_in_sec = wav_file.getnframes() / wav_file.getframerate()
        except:
            with open(failed_audio, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([file_path])

def check_source(path, failed_audio):
    to_process = list()
    for root, dirs, files in os.walk(path):
        for file in files:
            if (file.endswith(".wav") or file.endswith('.mp3')) and 'audio' in os.path.join(root, file):
                to_process.append([root, file])
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, path, file, failed_audio) for path, file in to_process]
        for f in as_completed(futures): f.result()
                
    
def main(corpora_path):
    failed_audio = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "non_working_audio.csv")
    
    with open(failed_audio, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["file_name"])
    
    flag = True
    for source in os.listdir(corpora_path):
        if source.startswith('.'):
            continue
        if os.path.isdir(os.path.join(corpora_path, source)):
            flag = False
            check_source(os.path.join(corpora_path, source), failed_audio)
    if flag:
        check_source(corpora_path, failed_audio)
    
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get durations of audio per corpus and per language.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    args = parser.parse_args()
    main(args.corpora_path)
