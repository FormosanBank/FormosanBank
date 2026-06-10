"""
download_grammar_audio.py

Step 2 of 2.  Reads the XML files written by create_xml_grammar.py and
downloads each per-sentence audio file referenced in an <AUDIO> element
to Audio/Grammar/<lang>/.

Unlike the stories audio, each grammar sentence has its own individual audio
file at a direct URL — no slicing is needed.

Run create_xml_grammar.py first.
"""

import os
import csv
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Download helper
# ---------------------------------------------------------------------------

def download_file(url, save_path, failed_log):
    """
    Download a single audio file from url to save_path.
    Skips if the file already exists.
    Returns (save_path, True) on success, (save_path, False) on failure.
    """
    if os.path.exists(save_path):
        return save_path, True
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return save_path, True
        else:
            return save_path, False
    except Exception:
        return save_path, False


# ---------------------------------------------------------------------------
# Per-language processing
# ---------------------------------------------------------------------------

def process_language(lang_xml_dir, lang_audio_dir, lang_name):
    """
    Parse all XML files for one language, then download every audio file
    referenced by an <AUDIO> element in parallel.
    """
    os.makedirs(lang_audio_dir, exist_ok=True)

    failed_log = os.path.join(lang_audio_dir, "failed_audio.csv")
    failures   = []

    # Collect all (url, dest_path) pairs from every XML file in this language.
    tasks = []
    for xml_file in sorted(os.listdir(lang_xml_dir)):
        if not xml_file.endswith('.xml'):
            continue
        tree = ET.parse(os.path.join(lang_xml_dir, xml_file))
        for audio_elem in tree.getroot().iter('AUDIO'):
            url  = audio_elem.get('url')
            name = audio_elem.get('file')
            if url and name:
                tasks.append((url, os.path.join(lang_audio_dir, name)))

    if not tasks:
        print(f"  {lang_name}: no audio entries found in XML.")
        return

    # Deduplicate (same file may be referenced multiple times).
    tasks = list({dest: (url, dest) for url, dest in tasks}.values())

    print(f"  {lang_name}: {len(tasks)} audio files to download.")
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_map = {
            executor.submit(download_file, url, dest, failed_log): (url, dest)
            for url, dest in tasks
        }
        for future in tqdm(as_completed(future_map),
                           total=len(future_map),
                           desc=f"  {lang_name}",
                           leave=False):
            dest_path, ok = future.result()
            if not ok:
                url, _ = future_map[future]
                failures.append([url, os.path.basename(dest_path), lang_name])

    if failures:
        with open(failed_log, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(["url", "file", "language"])
            w.writerows(failures)
        print(f"  {lang_name}: {len(failures)} failed — see {failed_log}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    curr_dir    = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(curr_dir)
    xml_root    = os.path.join(project_dir, "Final_XML", "Grammar")
    audio_root  = os.path.join(project_dir, "Audio",    "Grammar")

    if not os.path.isdir(xml_root):
        print(f"XML directory not found: {xml_root}")
        print("Run create_xml_grammar.py first.")
        return

    for lang_name in sorted(os.listdir(xml_root)):
        lang_xml_dir   = os.path.join(xml_root,   lang_name)
        lang_audio_dir = os.path.join(audio_root, lang_name)
        if not os.path.isdir(lang_xml_dir):
            continue
        print(f"Language: {lang_name}")
        process_language(lang_xml_dir, lang_audio_dir, lang_name)


if __name__ == "__main__":
    main()
