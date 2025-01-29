import xml.etree.ElementTree as ET
import os
import argparse
from datetime import timedelta
from collections import defaultdict

# Determine the language of the file based on the path
def get_lang(path, file, langs):
    for lang in langs:
        if lang in path or (file.split('.')[0] == lang and file.split('.')[1:] == ['xml']):
            return lang

# def process_file(path, file, langs):
#     """Process a single file: determine language and duration."""
#     lang = get_lang(path, file, langs)
#     file_path = os.path.join(path, file)
#     # audio = AudioSegment.from_file(file_path)
#     # length_in_sec = len(audio) // 1000
#     if file_path.endswith('.mp3'):
#         try:
#             audio = MP3(file_path)
#             length_in_sec = int(audio.info.length)
#         except Exception as e:
#             return (file_path, None, None, e)
#     elif file_path.endswith('.wav'):
#         try:
#             with wave.open(file_path, "rb") as wav_file:  # Use correct extension if renamed
#                 length_in_sec = wav_file.getnframes() / wav_file.getframerate()
#         except Exception as e:
#             print(file)
#             return (file_path, None, None, e)
#     return (file_path, lang, length_in_sec, None)

# def count_source_diarized(corpus, path, durations_by_lang, langs):
#     source_total = 0
#     to_process = list()
#     for root, dirs, files in os.walk(path):
#         for file in files:
#             if (file.endswith(".wav") or file.endswith('.mp3')) and 'audio' in os.path.join(root, file):
#                 to_process.append([root, file])
    
#     with ThreadPoolExecutor() as executor:
#         futures = [executor.submit(process_file, path, file, langs) for path, file in to_process]

#         for f in tqdm(as_completed(futures), total=len(to_process), desc=f"processing audio for {corpus}"):
#             file_path, lang, length, err = f.result()
#             if err is not None:
#                 print(f"Error reading {file_path}: {err}")
#             else:
#                 source_total += length
#                 durations_by_lang[lang] += length
                
#     return source_total
    

def read_file(file_path):

    duration = 0
    tree = ET.parse(file_path)
    root = tree.getroot()
    if "dialect" in root.attrib:
        dialect = root.attrib['dialect']
    else:
        dialect = None
    # Iterate over all <S> elements
    for audio in root.findall('.//AUDIO'):
        # Find the <FORM> element within the <S> element
        if 'start' not in audio.attrib or 'end' not in audio.attrib:
            raise ValueError("start and end must be set to all audio tags if the audio isn't diarized")
        # print(audio.attrib['end'])
        # print(audio.attrib['start'])
        duration += (float(audio.attrib['end']) - float(audio.attrib['start']))

    return duration, dialect

def count_source(path, durations_by_lang, langs):
    source_total = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".xml") and 'XML' in os.path.join(root, file):
                lang = get_lang(root, file, langs)
                durations_in_file, dialect = read_file(os.path.join(root, file))
                if dialect:
                    durations_by_lang[lang][1][dialect] += durations_in_file
                else:
                    durations_by_lang[lang][1]['Not Specified'] += durations_in_file
                
                durations_by_lang[lang][0] += durations_in_file
                source_total += durations_in_file
    return source_total
    

def get_durations(corpora_path):
    
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun','Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
        'Thao', 'Kavalan', 'Truku', 'Sakizaya','Seediq','Saaroa', 'Kanakanavu', 'Siraya']

    durations_by_lang = {lang: [0, defaultdict(int)] for lang in langs}
    durations_by_source = dict()
    for source in os.listdir(corpora_path):
        if source.startswith('.'):
            continue
        if source  == 'Siraya_Gospels':
            continue
        durations_by_source[source] = 0
        print(f"\n=====counting in {source}======")
        durations_by_source[source] = count_source(os.path.join(corpora_path, source), durations_by_lang, langs)
    
    return durations_by_lang, durations_by_source

def convert_seconds_to_hms(seconds):
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"
    
def main(corpora_path):
    
    durations_by_lang, durations_by_source = get_durations(corpora_path)
    for item in durations_by_lang:
        durations_by_lang[item][0] = round(durations_by_lang[item][0], 2)
        for dialect in durations_by_lang[item][1]:
            durations_by_lang[item][1][dialect] = round(durations_by_lang[item][1][dialect], 2)

    for item in durations_by_source:
        durations_by_source[item] = round(durations_by_source[item], 2)
   
    total = round(sum(durations_by_source.values()), 2)

    print("\n=====durations per language======")
    print(durations_by_lang)
    print("\n=====durations per source======")
    print(durations_by_source)
    print("\n=====durations total-count======")
    print(total, convert_seconds_to_hms(total))
    print("-------------------------------------\n\n")

    for language, (total_duration, dialects) in durations_by_lang.items():
        print(f"{language}:")
        print(f"Total: {convert_seconds_to_hms(total_duration)}")
        for dialect, duration in dialects.items():
            print(f"{dialect} total: {convert_seconds_to_hms(duration)}")
        print("------")

    # new_durations_by_lang, new_durations_by_source = dict(), dict()
    # for item in durations_by_lang:
    #     new_durations_by_lang[item] = convert_seconds_to_hms(durations_by_lang[item])
    # for item in durations_by_source:
    #     new_durations_by_source[item] = convert_seconds_to_hms(durations_by_source[item])
    # new_total = convert_seconds_to_hms(total)

    # print("\n=====durations per language======")
    # print(new_durations_by_lang)
    # print("\n=====durations per source======")
    # print(new_durations_by_source)
    # print("\n=====durations total-count======")
    # print(new_total)

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get durations of audio per corpus and per language.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    # parser.add_argument('--non_diarized', action='store_true', help='use if the corpora isn not diarized')
    args = parser.parse_args()
    main(args.corpora_path)
