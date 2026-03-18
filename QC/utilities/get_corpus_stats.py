import csv
import xml.etree.ElementTree as ET
import os
import argparse
import json
import wave
import re
from pathlib import Path
from collections import defaultdict
from typing import Optional, Tuple
try:
    from mutagen.mp3 import MP3 as MutagenMP3
except ImportError:
    MutagenMP3 = None

def extract_text_from_xml(tree: str, use_standard: bool = False) -> Tuple[str, str, Optional[str]]:
    """
    Extract text from XML file.
    
    Args:
        tree: Parsed XML tree (ET.parse(xml_file))
        use_standard: If True, extract standard text; if False, extract original text
        
    Returns:
        Tuple of (extracted_text, language_code, dialect, en_transl_count, zho_transl_count)
        en_transl_count  – number of <S> elements with a non-empty English <TRANSL>
        zho_transl_count – number of <S> elements with a non-empty Mandarin <TRANSL>
                           (xml:lang="zho" or "zh-Hant")
    """
    XML_LANG = '{http://www.w3.org/XML/1998/namespace}lang'
    ZHO_CODES = {'zho', 'zh-hant', 'zh'}

    try:
        root = tree.getroot()
        
        # Extract metadata from the root TEXT element
        # Handle xml:lang attribute properly - xml namespace is predefined
        language = root.get('{http://www.w3.org/XML/1998/namespace}lang', '').lower()  # ISO 639-3 language code
        dialect = root.get('dialect', '')            # Dialect name if specified
        
        # Extract text from FORM elements marked as original or standard orthography
        # We prioritize sentence-level forms over word-level forms
        texts = []
        kind_of = "standard" if use_standard else "original"
        en_transl_count = 0
        zho_transl_count = 0

        # First, look for sentence-level FORM elements with kindOf="original" or "standard"
        # These contain the complete sentences as they appear in the source
        for sentence in root.findall('.//S'):
            for form in sentence.findall(f'./FORM[@kindOf="{kind_of}"]'):
                if form.text:
                    texts.append(form.text.strip())

            # Count translations by language
            for transl in sentence.findall('TRANSL'):
                lang_code = (transl.get(XML_LANG) or '').lower()
                if transl.text and transl.text.strip():
                    if lang_code == 'en':
                        en_transl_count += 1
                    elif lang_code in ZHO_CODES:
                        zho_transl_count += 1
        
        # Fallback: if no sentence-level forms exist, collect word-level forms
        # This handles cases where only individual words are marked with the specified orthography
        if not texts:
            for word in root.findall('.//W'):
                for form in word.findall(f'./FORM[@kindOf="{kind_of}"]'):
                    if form.text:
                        texts.append(form.text.strip())
        
        # Combine all extracted text snippets into one string for analysis
        combined_text = ' '.join(texts)

        # Clean the text: remove numbers, double quotes, periods, commas, question marks, and exclamation marks
        # Keep letters, apostrophes, hyphens, and other characters that might be linguistically significant
        cleaned_text = re.sub(r'[0-9",!]', ' ', combined_text)

        # Count total number of words in cleaned_text
        word_count = len(cleaned_text.split())
        
        return language, dialect, en_transl_count, zho_transl_count, word_count
        
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        return "", "", None, 0, 0


def get_lang_dialects(tree):
    """
    Extract language and dialect information from the XML tree.
    
    Args:
        tree: Parsed XML tree (ET.parse(xml_file))
    """
    try:
        # Parse the XML file

        root = tree.getroot()
        
        # Extract metadata from the root TEXT element
        # Handle xml:lang attribute properly - xml namespace is predefined
        language = root.get('{http://www.w3.org/XML/1998/namespace}lang', '').lower()  # ISO 639-3 language code
        dialect = root.get('dialect', '')            # Dialect name if specified
        
        return language, dialect
        
    except Exception as e:
        print(f"Error parsing XML file : {e}")
        return "", "", None

def count_glosses(tree):
    """
    Given a parsed XML tree (ET.parse(xml_file)), count:
      - glossed_sentences: number of <S> elements that have at least one <M> descendant
      - transl_proportion: proportion of all <M> elements in the document that have a
                           direct <TRANSL> child (0.0 if there are no <M> elements)

    Returns:
        (glossed_sentences, transl_proportion)
    """
    root = tree.getroot()

    all_morphemes = root.findall('.//M')
    total_m = len(all_morphemes)

    glossed_sentences = sum(
        1 for s in root.findall('.//S')
        if s.find('.//M') is not None
    )

    if total_m == 0:
        transl_proportion = 0.0
    else:
        m_with_transl = sum(1 for m in all_morphemes if m.find('TRANSL') is not None)
        transl_proportion = m_with_transl / total_m

    return glossed_sentences, transl_proportion


def _get_audio_duration(file_path):
    """Return duration in seconds for an mp3 or wav file, or None on failure."""
    try:
        if file_path.endswith('.mp3'):
            if MutagenMP3 is None:
                return None
            return MutagenMP3(file_path).info.length
        elif file_path.endswith('.wav'):
            with wave.open(file_path, 'rb') as wf:
                return wf.getnframes() / wf.getframerate()
    except Exception:
        return None

def count_audio(tree, xml_file_path):
    """
    Given a parsed XML tree and the path of the XML file, count all <AUDIO>
    elements and sum up their durations.

    Audio files live under an `Audio` folder that is a sibling of `XML`.
    The relative path of the XML file within `XML` is mirrored under `Audio`.
    For example:
        Corpora/ePark/XML/Amis/text.xml  →  Corpora/ePark/Audio/Amis/<file>

    Args:
        tree:          Parsed XML tree (ET.parse(xml_file_path))
        xml_file_path: Absolute or relative path to the XML file

    Returns:
        (audio_count, total_seconds)
        audio_count   – number of <AUDIO> elements with a 'file' attribute
        total_seconds – sum of durations in seconds (None-duration files skipped)
    """
    xml_file = Path(xml_file_path).resolve()

    # Locate the XML root directory by finding the `XML` component in the path
    parts = xml_file.parts
    try:
        xml_idx = next(i for i in reversed(range(len(parts))) if parts[i] == 'XML')
    except StopIteration:
        xml_idx = None

    root = tree.getroot()
    audio_elems = [e for e in root.findall('.//AUDIO') if 'file' in e.attrib]
    audio_count = len(audio_elems)
    total_seconds = 0.0

    if xml_idx is not None:
        corpus_root = Path(*parts[:xml_idx])  # everything before `XML`
        rel = xml_file.relative_to(corpus_root / 'XML')
        audio_base = corpus_root / 'Audio'
    else:
        corpus_root = None
        audio_base = xml_file.parent

    for elem in audio_elems:
        audio_filename = elem.attrib['file']
        audio_path_obj = Path(audio_filename)
        # Build alternative filenames with the other common extension
        alt_ext = '.wav' if audio_path_obj.suffix.lower() == '.mp3' else '.mp3'
        alt_filename = audio_path_obj.stem + alt_ext

        # Try candidates in order until one exists on disk
        if corpus_root is not None:
            # Build a list of rel.parent variants, progressively stripping leading components
            # e.g. Paiwan/Sarnix → Sarnix → (empty)
            rel_parts = rel.parent.parts
            rel_variants = [Path(*rel_parts[i:]) for i in range(len(rel_parts))] + [Path('.')]
            candidates = []
            for rel_var in rel_variants:
                for name in (audio_filename, alt_filename):
                    candidates += [
                        audio_base / rel_var / name,                    # direct / stripped mirror
                        audio_base / rel_var / xml_file.stem / name,    # extra lang subfolder
                    ]
            candidates.append(audio_base / audio_filename)   # fully flat fallback
            candidates.append(audio_base / alt_filename)
        else:
            candidates = [audio_base / audio_filename, audio_base / alt_filename]

        audio_path = next((c for c in candidates if c.is_file()), None)
        if audio_path is None:
            continue

        duration = _get_audio_duration(str(audio_path))
        if duration is not None:
            total_seconds += duration

    return audio_count, total_seconds

def process_xml_file(xml_file_path):
    """Process a single XML file to extract text, language, dialect, glossing stats, and audio stats."""
    try:
        tree = ET.parse(xml_file_path)
        language, dialect, en_transl_count, zho_transl_count, word_count = extract_text_from_xml(tree)
        glossed_sentences, transl_proportion = count_glosses(tree)
        audio_count, total_audio_seconds = count_audio(tree, xml_file_path)

        return {
            'language': language,
            'dialect': dialect,
            'word_count': word_count,
            'en_transl_count': en_transl_count,
            'zho_transl_count': zho_transl_count,
            'segmented_sentences': glossed_sentences,
            'glossed_proportion': transl_proportion,
            'audio_count': audio_count,
            'total_audio_seconds': total_audio_seconds
        }

    except Exception as e:
        print(f"Error processing XML file {xml_file_path}: {e}")
        return None

def main(corpora_path):

    if os.path.isdir(os.path.join(corpora_path, 'XML')):
        paths = [os.path.join(corpora_path, 'XML')]
    else:
        paths = [os.path.join(corpora_path, d, 'XML') for d in os.listdir(corpora_path)
                 if os.path.isdir(os.path.join(corpora_path, d, 'XML'))]

    file_stats = []
    for path in paths:
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".xml"):
                    xml_file_path = os.path.join(root, file)
                    stats = process_xml_file(xml_file_path)
                    if stats is not None:
                        file_stats.append(stats)

    # Aggregate stats by language and dialect
    # _file_count is used internally to average glossed_proportion across files
    corpora_dict = defaultdict(lambda: {
        'word_count': 0,
        'segmented_sentences': 0,
        'glossed_proportion': 0.0,
        'audio_count': 0,
        'audio_time': 0.0,
        'eng_transl_count': 0,
        'zho_transl_count': 0,
        'file_count': 0,
    })

    for stats in file_stats:
        key = (stats['language'], stats['dialect'])
        corpora_dict[key]['segmented_sentences'] += stats['segmented_sentences']
        corpora_dict[key]['glossed_proportion'] += stats['glossed_proportion']
        corpora_dict[key]['audio_count'] += stats['audio_count']
        corpora_dict[key]['audio_time'] += round(stats['total_audio_seconds'], 0)
        corpora_dict[key]['eng_transl_count'] += stats['en_transl_count']
        corpora_dict[key]['zho_transl_count'] += stats['zho_transl_count']
        corpora_dict[key]['word_count'] += stats.get('word_count', 0)
        corpora_dict[key]['file_count'] += 1

    # Convert summed glossed_proportion to a per-file average
    for key, vals in corpora_dict.items():
        fc = vals['file_count']
        if fc > 0:
            vals['glossed_proportion'] = round(vals['glossed_proportion'] / fc, 4)

    # Save as CSV
    csv_path = os.path.join(corpora_path, 'corpora_stats.csv')
    fieldnames = ['language', 'dialect', 'segmented_sentences', 'glossed_proportion',
                  'audio_count', 'audio_time', 'eng_transl_count', 'zho_transl_count', 'word_count', 'file_count']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (language, dialect), vals in sorted(corpora_dict.items()):
            writer.writerow({'language': language, 'dialect': dialect, **vals})

    print(f"Corpus statistics saved to {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="count statistics for one or more corpora.")
    parser.add_argument('corpora_path', help='Specify the path of the corpora')
    args = parser.parse_args()
    main(args.corpora_path)
