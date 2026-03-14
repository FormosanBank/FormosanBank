#!/usr/bin/env python3
"""
Script to check for mismatches between sentence word count and number of word elements.
Identifies cases like the Yami example where there are extra spurious word entries.
"""

import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import defaultdict

def get_sound_number_from_xml(xml_file_path):
    """
    Extract the sound number from audio URLs in the XML file.
    Returns the number after /sound/ in the URLs, or None if not found.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Find first AUDIO element with a URL
        for audio_elem in root.findall('.//AUDIO'):
            audio_url = audio_elem.get('url')  # Use 'url' not 'src'
            if audio_url and '/sound/' in audio_url:
                # Extract number after /sound/
                import re
                match = re.search(r'/sound/(\d+)/', audio_url)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        print(f"Error extracting sound number from {xml_file_path}: {e}")
        return None

def find_csv_by_sound_number(sound_number):
    """
    Find the CSV file that contains URLs with the given sound number.
    """
    if not sound_number:
        return None
    
    csv_dir = Path('ePark_1/九階教材')
    for csv_file in csv_dir.glob('*.csv'):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if f'/sound/{sound_number}/' in content:
                    return csv_file.name
        except Exception as e:
            continue
    
    return None

def count_words_in_sentence(sentence_text):
    """
    Count words in a sentence by splitting on whitespace and filtering out empty strings.
    """
    if not sentence_text:
        return 0
    # Split on whitespace and filter out empty strings
    words = [word for word in sentence_text.split() if word.strip()]
    return len(words)

def text_matches_without_whitespace(sentence_text, word_elements_text):
    """
    Check if sentence text matches concatenated word elements when whitespace and punctuation are removed.
    """
    def clean_text(text):
        """Remove whitespace and punctuation (?, ., ,) from text."""
        if text is None:
            return ""
        # Remove whitespace first
        cleaned = ''.join(text.split())
        # Remove specific punctuation marks
        cleaned = cleaned.replace('?', '').replace('.', '').replace(',', '').replace('!', '')
        return cleaned
    
    # Clean sentence text
    sentence_cleaned = clean_text(sentence_text)
    
    # Concatenate all word element texts and clean
    word_concat = ''.join(word_text or '' for word_text in word_elements_text)
    word_concat_cleaned = clean_text(word_concat)
    
    return sentence_cleaned == word_concat_cleaned


def analyze_xml_file(file_path):
    """
    Analyze a single XML file for word count mismatches.
    Returns tuple of (missing_audio, segmentation_differences, content_mismatches).
    """
    missing_audio = []
    segmentation_differences = []
    content_mismatches = []
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Get metadata from root element
        text_id = root.get('id', 'unknown')
        lang = root.get('xml:lang', 'unknown')
        source = root.get('source', 'unknown')
        
        # Extract dialect from text_id for labeling
        dialect_identifier = 'unknown'
        if '_' in text_id:
            parts = text_id.split('_')
            dialect_identifier = parts[-1]
        
        # Find CSV file by matching sound URLs
        sound_number = get_sound_number_from_xml(file_path)
        csv_filename = find_csv_by_sound_number(sound_number)
        
        if not csv_filename:
            csv_filename = 'Unknown CSV'
        
        # Find all sentence elements
        for s_element in root.findall('.//S'):
            s_id = s_element.get('id', 'unknown')
            
            # Get the sentence text from FORM element
            form_element = s_element.find('FORM')
            if form_element is None or form_element.text is None:
                continue
                
            sentence_text = form_element.text.strip()
            if not sentence_text:
                continue
                
            # Count words in the sentence
            expected_word_count = count_words_in_sentence(sentence_text)
            
            # Count word elements (W elements) and extract their text
            word_elements = s_element.findall('.//W')
            actual_word_count = len(word_elements)
            w_with_audio_count = 0
            
            # Extract the actual words from W elements
            actual_words = []
            for w_element in word_elements:
                # Get text from the W element itself or from a FORM child
                word_text = None
                if w_element.text and w_element.text.strip():
                    word_text = w_element.text.strip()
                else:
                    # Look for FORM child element
                    form_child = w_element.find('FORM')
                    if form_child is not None and form_child.text:
                        word_text = form_child.text.strip()
                
                if word_text:
                    actual_words.append(word_text)
                else:
                    # Add empty string for None/empty word elements to maintain count
                    actual_words.append("")
                
                # Check if this W element has an AUDIO child with file attribute
                audio_children = w_element.findall('.//AUDIO')
                if audio_children:
                    for audio in audio_children:
                        if audio.get('file'):
                            w_with_audio_count += 1
                            break  # Count each W element only once
            
            # Check all sentences that have word elements
            if actual_word_count > 0:
                # Check if the text content matches when whitespace is removed
                text_matches = text_matches_without_whitespace(sentence_text, actual_words)
                
                # Create mismatch info for any sentence (regardless of word count)
                mismatch = {
                    'file_path': str(file_path),
                    'text_id': text_id,
                    'lang': lang,
                    'source': source,
                    'dialect': dialect_identifier,
                    'csv_filename': csv_filename,
                    's_id': s_id,
                    'sentence_text': sentence_text,
                    'actual_words': actual_words,
                    'expected_words': expected_word_count,
                    'actual_word_elements': actual_word_count,
                    'words_with_audio': w_with_audio_count,
                    'difference': actual_word_count - expected_word_count
                }
                
                # Categorize based on audio files and text matching
                if w_with_audio_count < actual_word_count:
                    # Category 1: Missing audio files for some W elements
                    missing_audio.append(mismatch)
                elif text_matches:
                    # Category 2: All W elements have audio AND text matches (segmentation difference)
                    segmentation_differences.append(mismatch)
                else:
                    # Category 3: All W elements have audio BUT text doesn't match (content mismatch)
                    content_mismatches.append(mismatch)
                
    except ET.ParseError as e:
        print(f"Error parsing {file_path}: {e}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        
    return missing_audio, segmentation_differences, content_mismatches

def find_all_xml_files(directory):
    """
    Find all XML files in the directory and subdirectories.
    """
    xml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(Path(root) / file)
    return xml_files

def main():
    final_xml_dir = Path('./Final_XML')
    
    if not final_xml_dir.exists():
        print(f"Directory {final_xml_dir} does not exist!")
        return
    
    print(f"Analyzing XML files in {final_xml_dir}...")
    
    # Find all XML files
    xml_files = find_all_xml_files(final_xml_dir)
    print(f"Found {len(xml_files)} XML files to analyze")
    
    # Analyze each file
    all_missing_audio = []
    all_segmentation_differences = []
    all_content_mismatches = []
    processed_files = 0
    
    for xml_file in xml_files:
        print(f"Processing: {xml_file.relative_to(final_xml_dir)}")
        missing_audio, segmentation_differences, content_mismatches = analyze_xml_file(xml_file)
        all_missing_audio.extend(missing_audio)
        all_segmentation_differences.extend(segmentation_differences)
        all_content_mismatches.extend(content_mismatches)
        processed_files += 1
        
        if processed_files % 50 == 0:
            print(f"Processed {processed_files}/{len(xml_files)} files...")
    
    print(f"\nAnalysis complete. Processed {processed_files} files.")
    print(f"Found {len(all_missing_audio)} cases with missing audio files.")
    print(f"Found {len(all_segmentation_differences)} segmentation differences (text matches).")
    print(f"Found {len(all_content_mismatches)} content mismatches (text doesn't match).")
    
    # Generate three separate output files
    def write_report(mismatches, filename, title, description):
        """Write a report for a specific category of mismatches."""
        if not mismatches:
            print(f"No {title.lower()} found!")
            return
            
        report_file = Path(filename)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"{title}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"{description}\n\n")
            
            # Calculate audio statistics
            total_word_elements = sum(m['actual_word_elements'] for m in mismatches)
            total_with_audio = sum(m['words_with_audio'] for m in mismatches)
            audio_percentage = (total_with_audio / total_word_elements * 100) if total_word_elements > 0 else 0
            
            f.write(f"Total cases found: {len(mismatches)}\n\n")
            f.write(f"Audio File Statistics:\n")
            f.write(f"  Total word elements: {total_word_elements}\n")
            f.write(f"  Word elements with audio files: {total_with_audio} ({audio_percentage:.1f}%)\n\n")
            
            # Group by source
            by_source = defaultdict(list)
            by_difference = defaultdict(list)
            
            for mismatch in mismatches:
                source_key = f"{mismatch['source']} {mismatch['dialect']} ({mismatch['csv_filename']})"
                by_source[source_key].append(mismatch)
                by_difference[mismatch['difference']].append(mismatch)
            
            f.write("Cases by source:\n")
            for source, cases in sorted(by_source.items()):
                f.write(f"  {source}: {len(cases)} cases\n")
            f.write("\n")
            
            f.write("Cases by difference (actual word elements - expected words):\n")
            for diff, cases in sorted(by_difference.items()):
                f.write(f"  {diff:+d}: {len(cases)} cases\n")
            f.write("\n")
            
            # Detailed listing
            f.write("Detailed Report:\n")
            f.write("-" * 40 + "\n\n")
            
            for i, mismatch in enumerate(mismatches, 1):
                f.write(f"{i}. File: {mismatch['file_path']}\n")
                f.write(f"   Text ID: {mismatch['text_id']}\n")
                f.write(f"   Language: {mismatch['lang']}\n")
                f.write(f"   Source: {mismatch['source']}\n")
                f.write(f"   Dialect: {mismatch['dialect']}\n")
                f.write(f"   CSV File: ePark_1/九階教材/{mismatch['csv_filename']}\n")
                f.write(f"   Sentence ID: {mismatch['s_id']}\n")
                f.write(f"   Sentence: \"{mismatch['sentence_text']}\"\n")
                f.write(f"   Actual words found: {mismatch['actual_words']}\n")
                f.write(f"   Expected words: {mismatch['expected_words']}\n")
                f.write(f"   Actual word elements: {mismatch['actual_word_elements']}\n")
                f.write(f"   Word elements with audio files: {mismatch['words_with_audio']}\n")
                f.write(f"   Difference: {mismatch['difference']:+d}\n")
                f.write("\n")
        
        print(f"{title} report written to: {report_file}")
    
    # Write the three reports
    write_report(
        all_missing_audio,
        './missing_audio_issues.txt',
        'Missing Audio File Issues',
        'Cases where not all <W /> elements have corresponding audio files.'
    )
    
    write_report(
        all_segmentation_differences,
        './segmentation_differences.txt',
        'Word Segmentation Differences',
        'Cases where all <W /> elements have audio files AND the text matches when\npunctuation and whitespace are removed, but word count differs from expected.\nThese are likely different segmentation choices rather than content errors.'
    )
    
    write_report(
        all_content_mismatches,
        './content_mismatches.txt',
        'Content Mismatches',
        'Cases where all <W /> elements have audio files BUT the text content\ndoes not match the sentence text when cleaned. These represent actual\ncontent discrepancies that need investigation.'
    )

if __name__ == "__main__":
    main()