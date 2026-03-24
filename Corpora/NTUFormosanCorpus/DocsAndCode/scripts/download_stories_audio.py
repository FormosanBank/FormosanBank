"""
download_stories_audio.py

Step 2 of 2.  Reads the XML files written by create_xml_stories.py, downloads
the full source audio files referenced in each <AUDIO> element, and extracts
the per-sentence segments to Audio/Stories/<lang>/.

Source audio files are cached in Audio/Stories/<lang>/source/ so they are
only downloaded once even if multiple stories share the same recording.

Run create_xml_stories.py first.
"""

import os
import xml.etree.ElementTree as ET
import requests
from pydub import AudioSegment
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


# ---------------------------------------------------------------------------
# Download / extraction helpers
# ---------------------------------------------------------------------------

def download_source_audio(url, save_path):
    """
    Download a full source audio file to save_path.
    Skips the download if the file already exists.
    Returns True on success, False on failure.
    """
    if os.path.exists(save_path):
        return True
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            print(f"  HTTP {response.status_code} for {url}")
            return False
    except Exception as e:
        print(f"  Download error for {url}: {e}")
        return False


def extract_segment(source_path, start, end, output_path):
    """
    Extract the audio between start and end (seconds) from source_path
    and save as mp3 to output_path.  Skips if output already exists.
    """
    if os.path.exists(output_path):
        return
    try:
        audio   = AudioSegment.from_file(source_path)
        segment = audio[int(start * 1000):int(end * 1000)]
        segment.export(output_path, format="mp3")
    except Exception as e:
        print(f"  Extraction error → {os.path.basename(output_path)}: {e}")


# ---------------------------------------------------------------------------
# Per-XML-file processing
# ---------------------------------------------------------------------------

def process_xml_file(xml_path, lang_audio_dir, source_audio_dir):
    """
    Parse one XML file, download any missing source audio files, then
    extract all per-sentence segments in parallel.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Collect every segment described in the file.
    segments = []
    for s_elem in root.findall('S'):
        audio_elem = s_elem.find('AUDIO')
        if audio_elem is None:
            continue
        seg_file = audio_elem.get('file')
        url      = audio_elem.get('url')
        start    = audio_elem.get('start')
        end      = audio_elem.get('end')
        if not all([seg_file, url, start, end]):
            continue
        source_name = url.split('/')[-1]
        segments.append((
            url,
            os.path.join(source_audio_dir, source_name),
            float(start),
            float(end),
            os.path.join(lang_audio_dir, seg_file),
        ))

    if not segments:
        return

    # Download each unique source file once.
    seen = set()
    for url, source_path, *_ in segments:
        source_name = os.path.basename(source_path)
        if source_name not in seen:
            seen.add(source_name)
            print(f"  Downloading source: {source_name}")
            download_source_audio(url, source_path)

    # Extract all segments in parallel.
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(extract_segment, source_path, start, end, seg_path)
            for _, source_path, start, end, seg_path in segments
        ]
        for future in tqdm(futures,
                           desc=f"  Extracting {os.path.basename(xml_path)}",
                           leave=False):
            future.result()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    curr_dir    = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(curr_dir)
    xml_root    = os.path.join(project_dir, "Final_XML", "Stories")
    audio_root  = os.path.join(project_dir, "Audio",    "Stories")

    if not os.path.isdir(xml_root):
        print(f"XML directory not found: {xml_root}")
        print("Run create_xml_stories.py first.")
        return

    for lang_name in sorted(os.listdir(xml_root)):
        lang_xml_dir = os.path.join(xml_root, lang_name)
        if not os.path.isdir(lang_xml_dir):
            continue

        lang_audio_dir   = os.path.join(audio_root, lang_name)
        source_audio_dir = os.path.join(lang_audio_dir, "source")
        os.makedirs(lang_audio_dir,   exist_ok=True)
        os.makedirs(source_audio_dir, exist_ok=True)

        print(f"Language: {lang_name}")
        for xml_file in sorted(os.listdir(lang_xml_dir)):
            if not xml_file.endswith('.xml'):
                continue
            process_xml_file(
                os.path.join(lang_xml_dir, xml_file),
                lang_audio_dir,
                source_audio_dir,
            )


if __name__ == "__main__":
    main()
