import csv
import xml.etree.ElementTree as ET
import os
import argparse
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
        en_transl_count  – number of Formosan words (from S FORMs) in sentences with an English <TRANSL>
        zho_transl_count – number of Formosan words (from S FORMs) in sentences with a Mandarin <TRANSL>
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
            sentence_words = 0
            for form in sentence.findall(f'./FORM[@kindOf="{kind_of}"]'):
                if form.text:
                    texts.append(form.text.strip())
                    cleaned = re.sub(r'[0-9",!]', ' ', form.text.strip())
                    sentence_words += len(cleaned.split())

            # Count translated words by language (words in the Formosan S FORM)
            for transl in sentence.findall('TRANSL'):
                lang_code = (transl.get(XML_LANG) or '').lower()
                if transl.text and transl.text.strip():
                    if lang_code == 'en':
                        en_transl_count += sentence_words
                    elif lang_code in ZHO_CODES:
                        zho_transl_count += sentence_words
        
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
      - segmented_words: number of Formosan words (from S FORMs with kindOf="original") in
                         <S> elements that have at least one <M> descendant
      - glossed_words:   number of Formosan words (from S FORMs with kindOf="original") in
                         <S> elements that have at least one <M> descendant with a <TRANSL>
                         child (always <= segmented_words)

    Returns:
        (segmented_words, glossed_words)
    """
    root = tree.getroot()

    segmented_words = 0
    glossed_words = 0
    for s in root.findall('.//S'):
        has_m = s.find('.//M') is not None
        has_glossed_m = s.find('.//M/TRANSL') is not None
        word_count = 0
        for form in s.findall('./FORM[@kindOf="original"]'):
            if form.text:
                cleaned = re.sub(r'[0-9",!]', ' ', form.text.strip())
                word_count += len(cleaned.split())
        if has_m:
            segmented_words += word_count
        if has_glossed_m:
            glossed_words += word_count

    return segmented_words, glossed_words


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
    Given a parsed XML tree and the path of the XML file, count <AUDIO>
    elements and sum up their durations, split into two categories:

      - Transcribed:    <AUDIO> elements that are children of <S> or <W>.
                        These accompany transcribed speech.
      - Untranscribed:  <AUDIO> elements that are direct children of the
                        root <TEXT> element.  These are not transcribed.

    Audio files live under an `Audio` folder that is a sibling of `XML`.
    The relative path of the XML file within `XML` is mirrored under `Audio`.
    For example:
        Corpora/ePark/XML/Amis/text.xml  →  Corpora/ePark/Audio/Amis/<file>

    Args:
        tree:          Parsed XML tree (ET.parse(xml_file_path))
        xml_file_path: Absolute or relative path to the XML file

    Returns:
        (transcribed_count, transcribed_seconds, untranscribed_count, untranscribed_seconds)
        transcribed_count      – number of <AUDIO> elements inside <S> or <W>
        transcribed_seconds    – total duration of transcribed audio in seconds
        untranscribed_count    – number of <AUDIO> elements that are direct children of <TEXT>
        untranscribed_seconds  – total duration of untranscribed audio in seconds
    """
    xml_file = Path(xml_file_path).resolve()

    # Locate the XML root directory by finding the `XML` component in the path
    parts = xml_file.parts
    try:
        xml_idx = next(i for i in reversed(range(len(parts))) if parts[i] == 'XML')
    except StopIteration:
        xml_idx = None

    root = tree.getroot()

    # Untranscribed: <AUDIO> direct children of the root <TEXT> element
    untranscribed_elems = [e for e in root.findall('AUDIO') if 'file' in e.attrib]
    # Transcribed: <AUDIO> elements nested inside <S> or <W>
    transcribed_elems = [e for e in root.findall('.//S/AUDIO') if 'file' in e.attrib]
    transcribed_elems += [e for e in root.findall('.//W/AUDIO') if 'file' in e.attrib]

    if xml_idx is not None:
        corpus_root = Path(*parts[:xml_idx])  # everything before `XML`
        rel = xml_file.relative_to(corpus_root / 'XML')
        audio_base = corpus_root / 'Audio'
    else:
        corpus_root = None
        audio_base = xml_file.parent

    def _sum_duration(elems):
        """Resolve each element's audio file and return the sum of durations."""
        total = 0.0
        for elem in elems:
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
                total += duration
        return total

    transcribed_seconds = _sum_duration(transcribed_elems)
    untranscribed_seconds = _sum_duration(untranscribed_elems)

    return len(transcribed_elems), transcribed_seconds, len(untranscribed_elems), untranscribed_seconds

def process_xml_file(xml_file_path):
    """Process a single XML file to extract text, language, dialect, glossing stats, and audio stats."""
    try:
        tree = ET.parse(xml_file_path)
        language, dialect, en_transl_count, zho_transl_count, word_count = extract_text_from_xml(tree)
        segmented_words, glossed_words = count_glosses(tree)
        transcribed_count, transcribed_seconds, untranscribed_count, untranscribed_seconds = count_audio(tree, xml_file_path)

        return {
            'language': language,
            'dialect': dialect,
            'word_count': word_count,
            'en_transl_count': en_transl_count,
            'zho_transl_count': zho_transl_count,
            'segmented_words': segmented_words,
            'glossed_words': glossed_words,
            'transcribed_audio_count': transcribed_count,
            'transcribed_audio_seconds': transcribed_seconds,
            'untranscribed_audio_count': untranscribed_count,
            'untranscribed_audio_seconds': untranscribed_seconds,
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
    corpora_dict = defaultdict(lambda: {
        'word_count': 0,
        'segmented_words': 0,
        'glossed_words': 0,
        'transcribed_audio_count': 0,
        'transcribed_audio_seconds': 0.0,
        'untranscribed_audio_count': 0,
        'untranscribed_audio_seconds': 0.0,
        'eng_transl_count': 0,
        'zho_transl_count': 0,
        'file_count': 0,
    })

    for stats in file_stats:
        key = (stats['language'], stats['dialect'])
        corpora_dict[key]['segmented_words'] += stats['segmented_words']
        corpora_dict[key]['glossed_words'] += stats['glossed_words']
        corpora_dict[key]['transcribed_audio_count'] += stats['transcribed_audio_count']
        corpora_dict[key]['transcribed_audio_seconds'] += round(stats['transcribed_audio_seconds'], 0)
        corpora_dict[key]['untranscribed_audio_count'] += stats['untranscribed_audio_count']
        corpora_dict[key]['untranscribed_audio_seconds'] += round(stats['untranscribed_audio_seconds'], 0)
        corpora_dict[key]['eng_transl_count'] += stats['en_transl_count']
        corpora_dict[key]['zho_transl_count'] += stats['zho_transl_count']
        corpora_dict[key]['word_count'] += stats.get('word_count', 0)
        corpora_dict[key]['file_count'] += 1

    # Derive corpus name and repo root from the 'Corpora' component in the path
    parts = Path(corpora_path).resolve().parts
    corpora_idx = next((i for i, p in enumerate(parts) if p == 'Corpora'), None)
    if corpora_idx is not None:
        repo_root = Path(*parts[:corpora_idx])
        corpus_name = parts[corpora_idx + 1] if corpora_idx + 1 < len(parts) else 'unknown'
    else:
        repo_root = Path(corpora_path).resolve()
        corpus_name = repo_root.name

    # Place output in <repo_root>/statistics/
    stats_dir = repo_root / 'statistics'
    stats_dir.mkdir(exist_ok=True)

    # Save as CSV
    csv_path = stats_dir / f'{corpus_name}_corpora_stats.csv'
    fieldnames = ['language', 'dialect', 'segmented_words', 'glossed_words',
                  'transcribed_audio_count', 'transcribed_audio_seconds',
                  'untranscribed_audio_count', 'untranscribed_audio_seconds',
                  'eng_transl_count', 'zho_transl_count', 'word_count', 'file_count']
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for (language, dialect), vals in sorted(corpora_dict.items()):
            writer.writerow({'language': language, 'dialect': dialect, **vals})

    print(f"Corpus statistics saved to {csv_path}")

if __name__ == "__main__":
    # Default Corpora directory is ../../Corpora relative to this script
    script_dir = Path(__file__).resolve().parent
    default_corpora_dir = script_dir / '..' / '..' / 'Corpora'

    parser = argparse.ArgumentParser(description="Count statistics for one or more corpora.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        'corpora_path',
        nargs='?',
        help='Path to a single corpus directory (e.g. Corpora/ePark).',
    )
    group.add_argument(
        '--all',
        action='store_true',
        help=(
            'Run on every corpus found in ../../Corpora (relative to this script), '
            'producing one CSV per corpus in statistics/.'
        ),
    )
    args = parser.parse_args()

    if args.all:
        corpora_dir = default_corpora_dir.resolve()
        corpus_dirs = sorted(
            d for d in corpora_dir.iterdir()
            if d.is_dir() and (d / 'XML').is_dir()
        )
        if not corpus_dirs:
            print(f"No corpus directories with an XML/ subfolder found in {corpora_dir}")
        for corpus_dir in corpus_dirs:
            print(f"Processing {corpus_dir.name} …")
            main(str(corpus_dir))
    else:
        main(args.corpora_path)
