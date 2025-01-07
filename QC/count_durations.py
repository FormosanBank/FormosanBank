import xml.etree.ElementTree as ET
import os
import argparse
from pydub import AudioSegment
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
from mutagen.wave import WAVE

# Determine the language of the file based on the path
def get_lang(path, langs):
    for lang in langs:
        if lang in path:
            return lang

def process_file(file_path, langs):
    """Process a single file: determine language and duration."""
    try:
        lang = get_lang(file_path, langs)
        # audio = AudioSegment.from_file(file_path)
        # length_in_sec = len(audio) // 1000
        if file_path.endswith('.mp3'):
            audio = MP3(file_path)
            length_in_sec = int(audio.info.length)
        elif file_path.endswith('.wav'):
            audio = WAVE(file_path)
            length_in_sec = int(audio.info.length)
        return (file_path, lang, length_in_sec, None)
    except Exception as e:
        return (file_path, None, None, e)

def count_source(corpus, path, durations_by_lang, langs):
    source_total = 0
    to_process = list()
    for root, dirs, files in os.walk(path):
        for file in files:
            if (file.endswith(".wav") or file.endswith('.mp3')) and 'audio' in os.path.join(root, file):
                file_path = os.path.join(root, file)
                to_process.append(file_path)
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_file, file_path, langs) for file_path in to_process]

        for f in tqdm(as_completed(futures), total=len(to_process), desc=f"processing audio for {corpus}"):
            file_path, lang, length, err = f.result()
            if err is not None:
                print(f"Error reading {file_path}: {err}")
            else:
                source_total += length
                durations_by_lang[lang] += length
                
    return source_total
    
    

def get_durations(corpora_path):
    
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun','Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
        'Thao', 'Kavalan', 'Truku', 'Sakizaya','Seediq','Saaroa', 'Kanakanavu', 'Siraya']

    durations_by_lang = {lang: 0 for lang in langs}
    durations_by_source = dict()
    for source in os.listdir(corpora_path):
        if source.startswith('.'):
            continue
        if source  == 'Siraya_Gospels':
            continue
        durations_by_source[source] = 0
        print(f"\n=====counting in {source}======")
        durations_by_source[source] = count_source(source, os.path.join(corpora_path, source), durations_by_lang, langs)

    return durations_by_lang, durations_by_source
def main(corpora_path):

    durations_by_lang, durations_by_source = get_durations(corpora_path)
    total = sum(durations_by_lang.values())

    print("\n=====durations per language======")
    print(durations_by_lang)
    print("\n=====durations per source======")
    print(durations_by_source)
    print("\n=====durations total-count======")
    print(total)

    # total_seconds = 

    # hours = total_seconds // 3600
    # minutes = (total_seconds % 3600) // 60
    # seconds = total_seconds % 60

    #print(f"Total audio duration: {hours}h {minutes}m {seconds}s")
    
    # with open('current_counts.txt', 'w') as file:
    #     json.dump(token_count, file)
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get durations of audio per corpus and per language.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    args = parser.parse_args()
    main(args.corpora_path)
