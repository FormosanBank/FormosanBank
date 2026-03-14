#!/usr/bin/env python3
"""
Script to fix word segmentation in XML files based on possible_word_mismatches.txt.
Fixes cases where:
1. Text content matches (segmentation difference only)
2. Number of audio files matches expected word count from sentence
3. But number of W elements doesn't match

This version focuses on simple, clean changes that are easy to verify with git.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict

def parse_possible_mismatches(file_path):
    """Parse the possible_word_mismatches.txt file to extract mismatch data."""
    mismatches = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by numbered entries
    entries = re.split(r'\n\d+\. File: ', content)[1:]  # Skip the header
    
    for entry in entries:
        lines = entry.strip().split('\n')
        if len(lines) < 10:
            continue
            
        mismatch = {}
        
        # First line is the file path (without "File: " prefix since we split on it)
        mismatch['file_path'] = lines[0].strip()
        
        for line in lines[1:]:
            line = line.strip()
            if line.startswith('Sentence ID: '):
                mismatch['sentence_id'] = line.replace('Sentence ID: ', '').strip()
            elif line.startswith('Sentence: '):
                # Remove quotes and extract sentence
                sentence = line.replace('Sentence: ', '').strip()
                if sentence.startswith('"') and sentence.endswith('"'):
                    sentence = sentence[1:-1]
                mismatch['sentence'] = sentence
            elif line.startswith('Expected words: '):
                mismatch['expected_words'] = int(line.replace('Expected words: ', '').strip())
            elif line.startswith('Actual word elements: '):
                mismatch['actual_word_elements'] = int(line.replace('Actual word elements: ', '').strip())
            elif line.startswith('Word elements with audio files: '):
                mismatch['words_with_audio'] = int(line.replace('Word elements with audio files: ', '').strip())
        
        # Only include entries with all required fields
        required_fields = ['file_path', 'sentence_id', 'sentence', 'expected_words', 'actual_word_elements', 'words_with_audio']
        if all(field in mismatch for field in required_fields):
            mismatches.append(mismatch)
    
    return mismatches

def should_fix_mismatch(mismatch):
    """
    Determine if a mismatch should be fixed.
    Criteria: audio files count matches expected words from sentence
    """
    return mismatch['words_with_audio'] == mismatch['expected_words']

def count_words_in_sentence(sentence_text):
    """Count words in a sentence by splitting on whitespace."""
    if not sentence_text:
        return 0
    words = [word for word in sentence_text.split() if word.strip()]
    return len(words)

def get_sentence_words(sentence_text):
    """Extract words from sentence text."""
    if not sentence_text:
        return []
    return [word for word in sentence_text.split() if word.strip()]

def create_backup(file_path):
    """Create a backup of the original file."""
    backup_path = Path(str(file_path) + '.backup')
    if not backup_path.exists():  # Only create backup if it doesn't exist
        import shutil
        shutil.copy2(file_path, backup_path)
        return backup_path
    return backup_path

def fix_simple_combination_cases(file_path, mismatches):
    """
    Fix simple cases where multiple W elements need to be combined into one.
    Only handles cases where expected_words = 1 for now.
    Uses surgical text replacement to avoid reformatting the entire XML.
    """
    # Create backup first
    backup = create_backup(file_path)
    
    # Read the original content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse the XML for analysis only
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    changes_made = False
    
    for mismatch in mismatches:
        if mismatch['expected_words'] != 1:
            print(f"    Skipping sentence {mismatch['sentence_id']}: complex case ({mismatch['expected_words']} words)")
            continue
            
        sentence_id = mismatch['sentence_id']
        sentence_text = mismatch['sentence']
        
        print(f"    Processing sentence {sentence_id}: '{sentence_text}'")
        
        # Find the S element
        s_element = None
        for s in root.findall('.//S'):
            if s.get('id') == sentence_id:
                s_element = s
                break
        
        if s_element is None:
            print(f"      Warning: Sentence not found")
            continue
        
        # Find W elements
        w_elements = s_element.findall('.//W')
        if len(w_elements) <= 1:
            print(f"      Skipping: already has {len(w_elements)} W element(s)")
            continue
        
        print(f"      Found {len(w_elements)} W elements, combining into 1")
        
        # Get the S element's TRANSL text for updating W element
        s_transl = s_element.find('TRANSL')
        s_transl_text = s_transl.text if s_transl is not None else ""
        
        # Process each W element surgically
        first_w = w_elements[0]
        
        # Update the first W element's FORM and PHON elements
        for form in first_w.findall('.//FORM'):
            old_form_text = form.text
            if old_form_text and old_form_text != sentence_text:
                # Find and replace this specific FORM content
                pattern = f'<FORM([^>]*)>{re.escape(old_form_text)}</FORM>'
                replacement = f'<FORM\\1>{sentence_text}</FORM>'
                content = re.sub(pattern, replacement, content, count=1)
                print(f"        Updated FORM from '{old_form_text}' to '{sentence_text}'")
        
        for phon in first_w.findall('.//PHON'):
            old_phon_text = phon.text
            if old_phon_text and old_phon_text != sentence_text:
                # Find and replace this specific PHON content
                pattern = f'<PHON([^>]*)>{re.escape(old_phon_text)}</PHON>'
                replacement = f'<PHON\\1>{sentence_text}</PHON>'
                content = re.sub(pattern, replacement, content, count=1)
                print(f"        Updated PHON from '{old_phon_text}' to '{sentence_text}'")
        
        # Update TRANSL element if it exists and S element has TRANSL
        if s_transl_text:
            w_transl = first_w.find('TRANSL')
            if w_transl is not None:
                old_transl_text = w_transl.text
                if old_transl_text and old_transl_text != s_transl_text:
                    pattern = f'<TRANSL([^>]*)>{re.escape(old_transl_text)}</TRANSL>'
                    replacement = f'<TRANSL\\1>{s_transl_text}</TRANSL>'
                    content = re.sub(pattern, replacement, content, count=1)
                    print(f"        Updated TRANSL from '{old_transl_text}' to '{s_transl_text}'")
        
        # Remove the extra W elements (all but the first)
        for w in w_elements[1:]:
            w_id = w.get('id')
            if w_id:
                # Find the entire W element block and remove it
                # Match from <W id="..."> to </W>, handling nested elements
                w_pattern = f'\\s*<W[^>]*id="{re.escape(w_id)}"[^>]*>.*?</W>\\s*'
                if re.search(w_pattern, content, re.DOTALL):
                    content = re.sub(w_pattern, '', content, count=1, flags=re.DOTALL)
                    print(f"        Removed W element with id '{w_id}'")
        
        changes_made = True
    
    if changes_made:
        # Write back the surgically modified content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"    Saved changes to {file_path}")
        return True
    else:
        print(f"    No changes made to {file_path}")
        return False

def main():
    possible_mismatches_file = Path('./possible_word_mismatches.txt')
    
    if not possible_mismatches_file.exists():
        print(f"Error: {possible_mismatches_file} not found!")
        print("Please run check_word_count_mismatches.py first to generate the report.")
        return
    
    print("Parsing possible word mismatches...")
    mismatches = parse_possible_mismatches(possible_mismatches_file)
    print(f"Found {len(mismatches)} total possible mismatches")
    
    # Filter for cases we should fix
    fixable_mismatches = []
    for mismatch in mismatches:
        if should_fix_mismatch(mismatch):
            # Verify the expected word count matches actual sentence word count
            sentence_word_count = count_words_in_sentence(mismatch['sentence'])
            if sentence_word_count == mismatch['expected_words']:
                fixable_mismatches.append(mismatch)
    
    print(f"Found {len(fixable_mismatches)} fixable cases (audio count matches expected word count)")
    
    if not fixable_mismatches:
        print("No fixable mismatches found.")
        return
    
    # Group by file for efficiency
    by_file = defaultdict(list)
    for mismatch in fixable_mismatches:
        by_file[mismatch['file_path']].append(mismatch)
    
    print(f"Will process {len(by_file)} files")
    
    # Process each file
    total_fixed = 0
    for file_path, file_mismatches in by_file.items():
        print(f"\nProcessing: {file_path}")
        
        full_path = Path(file_path)
        if not full_path.exists():
            print(f"  Error: File {full_path} not found!")
            continue
        
        # Only handle simple combination cases for now
        simple_cases = [m for m in file_mismatches if m['expected_words'] == 1]
        if simple_cases:
            print(f"  Processing {len(simple_cases)} simple combination cases")
            if fix_simple_combination_cases(full_path, simple_cases):
                total_fixed += len(simple_cases)
        
        complex_cases = [m for m in file_mismatches if m['expected_words'] != 1]
        if complex_cases:
            print(f"  Skipping {len(complex_cases)} complex cases (not implemented yet)")
    
    print(f"\nFixed {total_fixed} sentences")
    print("Use 'git diff' to review the changes made.")
    print("Backups were created with .backup extension")

if __name__ == "__main__":
    main()