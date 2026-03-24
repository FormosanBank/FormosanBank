import xml.etree.ElementTree as ET
import os
import sys
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from mutagen.mp3 import MP3
import wave
import array
import csv
from pathlib import Path
from tqdm import tqdm

"""
The main functionality of this validation test is to check the functionality of audio files associated with a corpus.
The following folder structure is assumed
path/to/corpus/Final_XML/
path/to/corpus/Final_audio/
and the path to Final_audio is the one to be provided as arg for the main
"""


def get_lang(path, file):
    langs = ['Amis', 'Atayal', 'Paiwan', 'Bunun','Puyuma', 'Rukai', 'Tsou', 'Saisiyat', 'Yami',
        'Thao', 'Kavalan', 'Truku', 'Sakizaya','Seediq','Saaroa', 'Kanakanavu', 'Siraya']
    for lang in langs:
        if lang in path or (file.split('.')[0] == lang and file.split('.')[1:] == ['xml']):
            return lang


def get_audio_duration(file_path):
    """Return the duration of an audio file in seconds, or None on failure."""
    try:
        if file_path.endswith('.mp3'):
            audio = MP3(file_path)
            return audio.info.length
        elif file_path.endswith('.wav'):
            with wave.open(file_path, "rb") as wav_file:
                return wav_file.getnframes() / wav_file.getframerate()
    except Exception:
        return None
    return None


def is_silent_wav(file_path, threshold=10):
    """
    Return True if a WAV file appears to be silent.
    Reads all PCM samples and checks whether the RMS amplitude is below
    `threshold` (on a 0-32767 scale for 16-bit audio; the threshold is
    scaled proportionally for 8- and 32-bit files).
    Returns None if the file cannot be read or is not PCM.
    """
    try:
        with wave.open(file_path, "rb") as wf:
            sampwidth = wf.getsampwidth()  # bytes per sample
            nframes = wf.getnframes()
            nchannels = wf.getnchannels()
            if nframes == 0:
                return True
            raw = wf.readframes(nframes)
        # Map sample width to array typecode
        typecode = {1: 'b', 2: 'h', 4: 'i'}.get(sampwidth)
        if typecode is None:
            return None  # unsupported format
        samples = array.array(typecode, raw)
        # Compute RMS
        rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
        # Normalise threshold to the actual bit depth
        max_val = (1 << (sampwidth * 8 - 1)) - 1
        normalised_threshold = threshold * max_val / 32767
        return rms < normalised_threshold
    except Exception:
        return None


def resolve_audio_path(xml_file_path, xml_root, audio_root, audio_filename):
    """
    Resolve the full path of an audio file referenced in an XML element.
    Mirrors the logic from extract_audio_clips.py's resolve_audio_dir:
      XML/Paiwan/Belmira/file.xml  →  Audio/Belmira/<audio_filename>
    Tries the following candidates in order:
      1. audio_root / rel_dir / audio_filename
      2. audio_root / rel_dir (first component stripped) / audio_filename
      3. audio_root / audio_filename
    """
    xml_file = Path(xml_file_path)
    xml_root = Path(xml_root)
    audio_root = Path(audio_root)

    rel_dir = xml_file.parent.relative_to(xml_root)

    candidate = audio_root / rel_dir / audio_filename
    if candidate.is_file():
        return str(candidate)

    parts = rel_dir.parts
    if len(parts) > 1:
        candidate2 = audio_root / Path(*parts[1:]) / audio_filename
        if candidate2.is_file():
            return str(candidate2)

    candidate3 = audio_root / audio_filename
    if candidate3.is_file():
        return str(candidate3)

    return None


def collect_sentence_refs(xml_root):
    """
    Walk all XML files under xml_root and collect audio/text references from
    both <S> (sentence) and <W> (word) elements.
    Returns a list of (xml_file_path, element_id, audio_filename, form_text) tuples.
    Only includes elements that have both an AUDIO child with a 'file' attribute
    and a FORM child with kindOf='original'.
    """
    refs = []
    for root, dirs, files in os.walk(xml_root):
        for file in files:
            if file.endswith('.xml'):
                xml_path = os.path.join(root, file)
                try:
                    tree = ET.parse(xml_path)
                    root_elem = tree.getroot()
                    for elem in root_elem.findall('.//S') + root_elem.findall('.//W'):
                        audio_elem = elem.find('AUDIO')
                        form_elem = elem.find("FORM[@kindOf='original']")
                        if (audio_elem is not None
                                and 'file' in audio_elem.attrib
                                and form_elem is not None):
                            audio_filename = audio_elem.attrib['file']
                            if not audio_filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                                continue
                            form_text = form_elem.text or ''
                            refs.append((xml_path, elem.attrib.get('id', ''), audio_filename, form_text))
                except Exception as e:
                    print(f"Warning: Could not parse {xml_path}: {e}")
    return refs


def collect_text_audio_refs(xml_root):
    """
    Walk all XML files under xml_root and collect audio references from
    <AUDIO> elements that are direct children of the <TEXT> root element.
    Returns a list of (xml_file_path, audio_filename) tuples.
    These elements only require existence and silence checks — no duration
    or words-per-second check is performed for them.
    """
    refs = []
    for root, dirs, files in os.walk(xml_root):
        for file in files:
            if file.endswith('.xml'):
                xml_path = os.path.join(root, file)
                try:
                    tree = ET.parse(xml_path)
                    root_elem = tree.getroot()
                    if root_elem.tag == 'TEXT':
                        for audio_elem in root_elem.findall('AUDIO'):
                            if 'file' in audio_elem.attrib:
                                audio_filename = audio_elem.attrib['file']
                                if not audio_filename.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                                    continue
                                refs.append((xml_path, audio_filename))
                except Exception as e:
                    print(f"Warning: Could not parse {xml_path}: {e}")
    return refs


def check_audio_existence_and_duration(xml_root, audio_root, duration_log, check_silence=False):
    """
    Phase 1: Verify that every audio file referenced in the XML files exists.
             If any are missing, report them and exit.
             Includes both sentence/word-level <AUDIO> elements and <AUDIO>
             elements that are direct children of <TEXT>.
    Phase 2: For sentence/word-level references, check audio duration and
             words-per-second ratio against <FORM kindOf='original'> text.
             Log any elements where the ratio falls outside expected bounds.
             TEXT-level <AUDIO> elements only undergo existence and silence
             checks — no duration or words-per-second check is performed.
    """
    print(f"Collecting audio references from XMLs in: {xml_root}")
    refs = collect_sentence_refs(xml_root)
    text_refs = collect_text_audio_refs(xml_root)

    if not refs and not text_refs:
        print("No audio references with 'file' attributes found in XML files.")
        return

    # --- Phase 1: existence check ---
    total_count = len(refs) + len(text_refs)
    print(f"Checking existence of {len(refs)} sentence/word and "
          f"{len(text_refs)} TEXT-level audio reference(s)...")
    missing = []
    resolved = []
    for xml_path, sent_id, audio_filename, form_text in refs:
        audio_path = resolve_audio_path(xml_path, xml_root, audio_root, audio_filename)
        if audio_path is None:
            missing.append((xml_path, audio_filename))
        else:
            resolved.append((xml_path, sent_id, audio_filename, audio_path, form_text))

    resolved_text = []
    for xml_path, audio_filename in text_refs:
        audio_path = resolve_audio_path(xml_path, xml_root, audio_root, audio_filename)
        if audio_path is None:
            missing.append((xml_path, audio_filename))
        else:
            resolved_text.append((xml_path, audio_filename, audio_path))

    if missing:
        missing_log = os.path.join(os.path.dirname(duration_log), "missing_audio.csv")
        os.makedirs(os.path.dirname(missing_log), exist_ok=True)
        with open(missing_log, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['xml_file', 'audio_file'])
            for xml_path, audio_filename in missing:
                writer.writerow([xml_path, audio_filename])
        print(f"\nWARNING: {len(missing)} audio file(s) could not be found. "
              f"Logged to: {missing_log}")
        print("Continuing with the files that were found...")
    else:
        print(f"All {total_count} referenced audio files exist.")

    # --- Phase 1b + Phase 2: silence check and words/sec check for sentence/word refs ---
    silent_log = os.path.join(os.path.dirname(duration_log), "silent_audio.csv")
    silent_files = []
    issues = []
    for xml_path, sent_id, audio_filename, audio_path, form_text in tqdm(
        resolved, desc="Checking audio (silence + words/sec)"
    ):
        # Silence check (WAV only)
        if audio_path.endswith('.wav') and check_silence:
            result = is_silent_wav(audio_path)
            if result is True:
                silent_files.append((xml_path, audio_filename))

        # Words/sec check
        duration = get_audio_duration(audio_path)
        if duration is not None and duration > 0:
            word_count = len(form_text.strip().split())
            num_char = len(form_text.strip())
            char_per_sec = num_char / duration
            words_per_sec = word_count / duration
            if (words_per_sec < .1 or char_per_sec > 17) or (word_count < 5 and duration > 10) or (word_count > 12 and duration < 7):
                issues.append((xml_path, audio_filename, round(words_per_sec, 2), round(char_per_sec, 2)))

    # --- Silence check only for TEXT-level refs (no duration/words-per-sec check) ---
    for xml_path, audio_filename, audio_path in tqdm(
        resolved_text, desc="Checking TEXT-level audio (silence only)"
    ):
        if audio_path.endswith('.wav') and check_silence:
            result = is_silent_wav(audio_path)
            if result is True:
                silent_files.append((xml_path, audio_filename))

    os.makedirs(os.path.dirname(duration_log), exist_ok=True)

    with open(silent_log, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['xml_file', 'audio_file'])
        for xml_path, audio_file in silent_files:
            writer.writerow([xml_path, audio_file])
    if silent_files:
        print(f"Silence check: {len(silent_files)} silent WAV file(s) logged to: {silent_log}")
    else:
        print("Silence check: no silent WAV files detected.")

    with open(duration_log, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['xml_file', 'audio_file', 'words_per_sec', 'chars_per_sec'])
        for xml_path, audio_file, issue, issue2 in issues:
            writer.writerow([xml_path, audio_file, issue, issue2])

    print(f"Duration check complete. {len(issues)} potential issue(s) logged to: {duration_log}")

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
                
    
def main(corpus_audio_path, xml_path=None, check_silence=False):
    failed_audio = os.path.join(os.getcwd(), "logs", "non_working_audio.csv")
    os.makedirs(os.path.dirname(failed_audio), exist_ok=True)

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

    if xml_path:
        duration_log = os.path.join(os.getcwd(), "logs", "audio_duration_issues.csv")
        check_audio_existence_and_duration(xml_path, corpus_audio_path, duration_log, check_silence=check_silence)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="validates the functionality of audio files associated with a corpus")
    parser.add_argument('--path', help='the path to the audio folder containing the audio files associated with a corpus')
    parser.add_argument('--xml_path', help='the path to the XML folder; if provided, validates that all referenced audio files exist and checks character-per-second ratios against <FORM kindOf="original"> text')
    parser.add_argument('--check_silence', action='store_true', help='enable silence detection for WAV files (may be slow for large corpora)')
    args = parser.parse_args()
    main(args.path, args.xml_path, check_silence=args.check_silence)
