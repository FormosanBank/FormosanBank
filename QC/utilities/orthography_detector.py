#!/usr/bin/env python3
"""
Orthography Detection for Formosan Bank XML Files

This module provides functionality to determine the most likely orthography
being used in XML files based on the letters found in the original text.
"""

import os
import csv
from pydoc import text
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


def load_orthography_data(orthographies_dir: str) -> Dict[str, Dict[str, Dict[str, Set[str]]]]:
    """
    Load all orthography data from TSV files.
    
    Args:
        orthographies_dir: Path to the Orthographies directory
        
    Returns:
        Dictionary structured as:
        {
            'language': {
                'dialect_name': {
                    'orthography_type': set_of_letters
                }
            }
        }
        For languages with single dialect or IPA column, dialect_name will be 'default'
    """
    # Initialize nested dictionary to store orthography data
    # Structure: language -> dialect -> orthography_type -> set of letters
    orthography_data = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    
    # Discover orthography directories (excluding ConversionTables)
    # ConversionTables contains mapping files, not base orthography definitions
    ortho_dirs = [d for d in os.listdir(orthographies_dir) 
                  if os.path.isdir(os.path.join(orthographies_dir, d)) 
                  and d != 'ConversionTables' 
                  and not d.startswith('.')]  # Skip hidden directories like .DS_Store
    
    # Process each orthography type directory (Church, MinEd, Ortho113, etc.)
    for ortho_type in ortho_dirs:
        ortho_path = os.path.join(orthographies_dir, ortho_type)
        if not os.path.exists(ortho_path):
            continue
            
        for file in os.listdir(ortho_path):
            if file.endswith('.tsv'):
                language = file.replace('.tsv', '')
                tsv_path = os.path.join(ortho_path, file)
                
                try:
                    with open(tsv_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f, delimiter='\t')
                        
                        # Get column names to identify dialect columns
                        fieldnames = reader.fieldnames or []
                        
                        # Extract dialect columns (everything except 'letter')
                        dialect_columns = [col for col in fieldnames if col != 'letter']
                        
                        # If no dialect columns or just 'IPA', treat as single dialect
                        if not dialect_columns or dialect_columns == ['IPA']:
                            dialect_columns = ['default']
                        
                        # Initialize letter sets for each dialect
                        dialect_letters = {dialect: set() for dialect in dialect_columns}
                        
                        # Process each row to extract letters for each dialect
                        for row in reader:
                            # Handle both 'letter' and 'letters' column names
                            letter = row.get('letter', '') or row.get('letters', '') or ''
                            letter = letter.strip() if letter else ''
                            if not letter:
                                continue
                                
                            # For each dialect column, check if this letter is valid
                            for dialect in dialect_columns:
                                if dialect == 'default':
                                    # Single dialect case: always include the letter
                                    dialect_letters[dialect].add(letter)
                                else:
                                    # Multi-dialect case: include if not explicitly 'NA'
                                    # Empty values mean "part of orthography but no IPA"
                                    ipa_value = row.get(dialect, '') or ''
                                    ipa_value = ipa_value.strip() if ipa_value else ''
                                    if ipa_value.upper() != 'NA':  # Include if empty or has any value other than 'NA'
                                        dialect_letters[dialect].add(letter)
                        
                        # Store the dialect-specific letter sets
                        for dialect, letters in dialect_letters.items():
                            if letters:  # Only store non-empty sets
                                orthography_data[language][dialect][ortho_type] = letters
                        
                except Exception as e:
                    print(f"Error reading {tsv_path}: {e}")
                    
    return {k: dict(v) for k, v in orthography_data.items()}


def extract_text_from_xml(xml_file: str, use_standard: bool = False) -> Tuple[str, str, Optional[str]]:
    """
    Extract text from XML file.
    
    Args:
        xml_file: Path to the XML file
        use_standard: If True, extract standard text; if False, extract original text
        
    Returns:
        Tuple of (extracted_text, language_code, dialect)
    """
    try:
        # Parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Extract metadata from the root TEXT element
        # Handle xml:lang attribute properly - xml namespace is predefined
        language = root.get('{http://www.w3.org/XML/1998/namespace}lang', '').lower()  # ISO 639-3 language code
        dialect = root.get('dialect', '')            # Dialect name if specified
        
        # Extract text from FORM elements marked as original or standard orthography
        # We prioritize sentence-level forms over word-level forms
        texts = []
        kind_of = "standard" if use_standard else "original"
        
        # First, look for sentence-level FORM elements with kindOf="original" or "standard"
        # These contain the complete sentences as they appear in the source
        for sentence in root.findall('.//S'):
            for form in sentence.findall(f'./FORM[@kindOf="{kind_of}"]'):
                if form.text:
                    texts.append(form.text.strip())
        
        # Fallback: if no sentence-level forms exist, collect word-level forms
        # This handles cases where only individual words are marked with the specified orthography
        if not texts:
            for word in root.findall('.//W'):
                for form in word.findall(f'./FORM[@kindOf="{kind_of}"]'):
                    if form.text:
                        texts.append(form.text.strip())
        
        # Combine all extracted text snippets into one string for analysis
        combined_text = ' '.join(texts)

        # Clean the text: remove numbers, commas, and exclamation marks
        # Keep letters, apostrophes, hyphens, and other characters that might be linguistically significant
        cleaned_text = re.sub(r'[0-9",!]', ' ', combined_text)
        
        return cleaned_text, language, dialect
        
    except Exception as e:
        print(f"Error parsing XML file {xml_file}: {e}")
        return "", "", None


def normalize_language_code(lang_code: str) -> str:
    """
    Normalize language codes to match orthography file names.
    
    Args:
        lang_code: ISO 639-3 language code or similar
        
    Returns:
        Normalized language name
    """
    # Mapping from ISO 639-3 language codes to orthography file naming convention
    # The orthography files use capitalized language names (e.g., 'Amis.tsv')
    # while XML files use ISO codes (e.g., 'ami')
    lang_mapping = {
        'ami': 'Amis',
        'tay': 'Atayal',
        'bnn': 'Bunun',
        'ckv': 'Kavalan',
        'pwn': 'Paiwan',
        'pyu': 'Puyuma',
        'dru': 'Rukai',
        'sxr': 'Saaroa',
        'xsy': 'Saisiyat',
        'szy': 'Sakizaya',
        'trv': 'Seediq',
        'ssf': 'Thao',
        'tsu': 'Tsou',
        'tao': 'Yami',
        'xnb': 'Kanakanavu'
    }#Note that since Seediq and Truku both share the code `trv`, we will need to rely on dialect information to distinguish them when analyzing XML files.
    
    # Look up the language code, default to capitalizing the input if not found
    return lang_mapping.get(lang_code.lower(), lang_code.capitalize())


def extract_letters(text: str) -> Tuple[Set[str], Counter]:
    """
    Extract individual letters from text, with frequency counts.
    Multi-letter patterns will be detected per-orthography in calculate_orthography_score.
    
    Args:
        text: Input text
        
    Returns:
        Tuple of (set of unique letters, Counter of letter frequencies)
    """
    
    letters = set()
    letter_counts = Counter()
    # Collect individual characters (excluding spaces)
    for char in text:
        if char != ' ':  # Exclude spaces but include all other remaining characters
            letters.add(char)
            letter_counts[char] += 1
    
    return letters, letter_counts


def calculate_orthography_score(text_letters: Set[str], orthography_letters: Set[str], text_letter_counts: Counter, text: str = None) -> Tuple[float, int, int, float, Set[str], Dict[str, int], int]:
    """
    Calculate how well the text matches an orthography.
    
    Args:
        text_letters: Set of individual letters found in the text  
        orthography_letters: Set of letters defined in the orthography
        text_letter_counts: Counter of individual letter frequencies in text
        text: Original text (needed for multi-letter pattern detection)
        
    Returns:
        Tuple of (match_score, matched_letters, unexpected_letter_types, unexpected_letter_percentage, effective_text_letters, unexpected_tokens, common_letters)
    """
    # Handle edge case: no letters defined in orthography
    if not orthography_letters:
        total_tokens = sum(text_letter_counts.values())
        return 0.0, 0, len(text_letters), 100.0 if total_tokens > 0 else 0.0, text_letters, dict(text_letter_counts), 0
    
    # Identify multi-letter patterns from this specific orthography
    multi_letter_patterns = [letter for letter in orthography_letters if len(letter) > 1]
    
    # Start with individual letters and counts
    effective_text_letters = text_letters.copy()
    effective_letter_counts = text_letter_counts.copy()
    
    # Process multi-letter patterns specific to this orthography
    if text and multi_letter_patterns:        
        for pattern in multi_letter_patterns:
            pattern_count = text.count(pattern)
            if pattern_count > 0:
                # Add the multi-letter pattern
                effective_text_letters.add(pattern)
                effective_letter_counts[pattern] = pattern_count
                
                # Remove individual letters that are part of this pattern to avoid double-counting
                for char in pattern:
                    if char in effective_letter_counts:
                        effective_letter_counts[char] = max(0, effective_letter_counts[char] - pattern_count)
                        if effective_letter_counts[char] == 0:
                            del effective_letter_counts[char]
                            effective_text_letters.discard(char)
    
    # Recalculate matched letters after potential capitalization changes
    matched_letters = len(effective_text_letters & orthography_letters)
    
    # Calculate unexpected letter types and their token frequency
    unexpected_letter_types = effective_text_letters - orthography_letters
    unexpected_token_count = sum(effective_letter_counts[letter] for letter in unexpected_letter_types)
    unexpected_tokens = {letter: effective_letter_counts[letter] for letter in unexpected_letter_types}
    
    # Handle capitalization: if an unexpected letter is uppercase and the orthography 
    # has the lowercase version, treat it as the lowercase letter
    unexpected_to_remove = set()
    for unexpected_letter in list(unexpected_letter_types):
        if unexpected_letter.isupper():
            lowercase_version = unexpected_letter.lower()
            if lowercase_version in orthography_letters:
                # Move the counts from the uppercase to lowercase version
                count = effective_letter_counts.get(unexpected_letter, 0)
                if count > 0:
                    # Add to lowercase version in effective counts
                    if lowercase_version in effective_letter_counts:
                        effective_letter_counts[lowercase_version] += count
                    else:
                        effective_letter_counts[lowercase_version] = count
                    
                    # Add lowercase to effective letters if not already there
                    effective_text_letters.add(lowercase_version)
                    
                    # Remove uppercase version from counts and letters
                    del effective_letter_counts[unexpected_letter]
                    effective_text_letters.discard(unexpected_letter)
                    
                    # Mark for removal from unexpected
                    unexpected_to_remove.add(unexpected_letter)
    
    # Remove handled uppercase letters from unexpected sets
    for letter in unexpected_to_remove:
        unexpected_letter_types.discard(letter)
        if letter in unexpected_tokens:
            del unexpected_tokens[letter]
    
    # Recalculate unexpected counts after handling capitalization
    unexpected_token_count = sum(effective_letter_counts[letter] for letter in unexpected_letter_types)
    
    # Calculate total tokens and unexpected percentage
    total_tokens = sum(effective_letter_counts.values())
    unexpected_percentage = (unexpected_token_count / total_tokens * 100) if total_tokens > 0 else 0.0
    
    # Recalculate matched letters after potential capitalization changes
    matched_letters = len(effective_text_letters & orthography_letters)
    
    # Calculate common letters (letters occurring at least 0.5% of the time)
    # This differs from 'matched_letters' which counts all expected letters that appear at least once
    # Common letters only counts those that appear frequently enough to be considered active in the text
    total_tokens = sum(effective_letter_counts.values())
    common_letters = 0
    if total_tokens > 0:
        threshold = total_tokens * (1 / (len(orthography_letters) ** 1.75))  # 0.5% threshold
        for letter in (effective_text_letters & orthography_letters):
            if effective_letter_counts.get(letter, 0) >= threshold:
                common_letters += 1
    
    # Calculate match percentage based on how much of the orthography is used
    # Combine coverage and cleanliness into a single score, with a small bonus for total number of characters matched
    match_score = ((common_letters / len(orthography_letters)) + (1 - 10 * (unexpected_percentage / 100)))/2 + common_letters/750 
    
    return match_score, matched_letters, len(unexpected_letter_types), unexpected_percentage, effective_text_letters, unexpected_tokens, common_letters


def determine_orthography_with_data(xml_file: str, orthography_data: Dict, ignore_dialect: bool = False, use_standard: bool = False) -> Dict:
    """
    Determine the most likely orthography for an XML file using pre-loaded orthography data.
    
    Args:
        xml_file: Path to the XML file
        orthography_data: Pre-loaded orthography data dictionary
        ignore_dialect: If True, ignore XML dialect tags and test all orthographies
        use_standard: If True, analyze standard text; if False, analyze original text
        
    Returns:
        Dictionary with analysis results
    """
    # Extract text content and metadata from the XML file
    text, language_code, dialect = extract_text_from_xml(xml_file, use_standard)
    
    # If ignore_dialect is True, reset dialect to empty string to force testing all orthographies
    if ignore_dialect:
        dialect = ''
    
    # Use the new core analysis function
    return analyze_text_for_orthography(text, language_code, dialect, orthography_data, xml_file)


def analyze_text_for_orthography(text: str, language_code: str, dialect: str, orthography_data: Dict, file_identifier: str = "unknown") -> Dict:
    """
    Analyze text to determine the most likely orthography using pre-loaded orthography data.
    
    Args:
        text: The text content to analyze
        language_code: ISO language code (e.g., 'tao', 'ami')
        dialect: Dialect name if specified
        orthography_data: Pre-loaded orthography data dictionary
        file_identifier: Identifier for the source (file path, group name, etc.)
        
    Returns:
        Dictionary with analysis results
    """
    # Validation: ensure we have text to analyze
    if not text:
        return {
            'error': 'No text provided for analysis',
            'file': file_identifier
        }
    
    # Convert ISO language code to orthography file naming convention
    normalized_language = normalize_language_code(language_code)
    
    # Analyze the text to identify all letters and letter combinations used
    text_letters, text_letter_counts = extract_letters(text)
    
    # Compare text against all relevant orthographies and score each match
    results = []
    
    # Determine which (language, dialect_name, dialect_data) combinations to test
    test_combinations = []
    
    # Strategy: if we can identify the language, focus on that language's orthographies
    target_language_data = orthography_data.get(normalized_language, {})
    
    if target_language_data:
        # Language identified: determine which dialects to test
        if dialect and dialect in target_language_data:
            # Use dialect information: test the specific dialect orthographies
            test_combinations.append((normalized_language, dialect, target_language_data[dialect]))
            
            # Also test 'default' orthographies (single orthography for all dialects, like Church/MinEd)
            if 'default' in target_language_data:
                test_combinations.append((normalized_language, 'default', target_language_data['default']))
        else:
            # No specific dialect or dialect not found: test all available orthographies for this language
            for dialect_name, dialect_data in target_language_data.items():
                test_combinations.append((normalized_language, dialect_name, dialect_data))
    else:
        # Language not recognized: test against all available orthographies
        # This is a fallback that helps identify the language as well as orthography
        for lang, language_data in orthography_data.items():
            for dialect_name, dialect_data in language_data.items():
                test_combinations.append((lang, dialect_name, dialect_data))
    
    # Single loop to test all determined combinations
    for lang, dialect_name, dialect_data in test_combinations:
        for ortho_type, ortho_letters in dialect_data.items():
            score, matched, unexpected_types, unexpected_pct, effective_text_letters, unexpected_tokens, common_letters = calculate_orthography_score(text_letters, ortho_letters, text_letter_counts, text)
            
            # Calculate missing letters
            missing_letters = sorted(list(ortho_letters - effective_text_letters))
            
            results.append({
                'language': lang,
                'dialect': dialect_name,
                'orthography': ortho_type,
                'score': score,
                'matched_letters': matched,
                'unexpected_letter_types': unexpected_types,
                'unexpected_percentage': unexpected_pct,
                'total_text_letters': len(effective_text_letters),
                'orthography_size': len(ortho_letters),
                'missing_letters': missing_letters,
                'unexpected_tokens': unexpected_tokens,
                'common_letters': common_letters
            })
    
    # Rank results by quality of match
    # Primary sort: highest match score (more letters recognized)
    # Secondary sort: lowest unexpected percentage (fewer foreign/borrowed characters)
    results.sort(key=lambda x: (x['score'], -x['unexpected_percentage']), reverse=True)
    
    # Return comprehensive analysis results
    return {
        # File and language metadata
        'file': file_identifier,                             # Source identifier
        'extracted_language': language_code,                 # ISO 639-3 code
        'normalized_language': normalized_language,          # Language name for orthography lookup
        'dialect': dialect,                                  # Dialect if specified
        
        # Text analysis results
        'text_sample': text[:200] + '...' if len(text) > 200 else text,  # Preview of analyzed text
        'letters_found': sorted(list(text_letters)),         # All unique letters/sequences found
        'letter_frequency': dict(text_letter_counts.most_common()),  # How often each letter appears
        
        # Orthography matching results
        'orthography_analysis': results,                     # All orthography scores, ranked
        'best_match': results[0] if results else None,      # Top-scoring orthography
        
        # Summary statistics
        'total_characters_analyzed': len(text),              # Total text length
        'unique_letters_found': len(text_letters)           # Number of distinct letters
    }


def determine_orthography(xml_file: str, orthographies_dir: str, ignore_dialect: bool = False, use_standard: bool = False) -> Dict:
    """
    Determine the most likely orthography for an XML file.
    
    Args:
        xml_file: Path to the XML file
        orthographies_dir: Path to the Orthographies directory
        ignore_dialect: If True, ignore XML dialect tags and test all orthographies
        use_standard: If True, analyze standard text; if False, analyze original text
        
    Returns:
        Dictionary with analysis results
    """
    # Load orthography data and delegate to optimized function
    orthography_data = load_orthography_data(orthographies_dir)
    return determine_orthography_with_data(xml_file, orthography_data, ignore_dialect=ignore_dialect, use_standard=use_standard)


def analyze_xml_files(directory: str, orthographies_dir: str, ignore_dialect: bool = False, use_standard: bool = False, language_filter: str = None) -> List[Dict]:
    """
    Analyze all XML files in a directory.
    
    Args:
        directory: Directory containing XML files
        orthographies_dir: Path to the Orthographies directory
        ignore_dialect: If True, ignore XML dialect tags and test all orthographies
        use_standard: If True, analyze standard text; if False, analyze original text
        
    Returns:
        List of analysis results for each XML file
    """
    results = []
    
    # Load orthography data once for all files (optimization)
    orthography_data = load_orthography_data(orthographies_dir)
    
    # Count files first for progress tracking
    xml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    total_files = len(xml_files)
    if total_files == 0:
        print("No XML files found in directory")
        return results
    
    print(f"Found {total_files} XML files to process...")
    
    # Process files with progress tracking
    for i, xml_path in enumerate(xml_files, 1):
        if i % 100 == 0 or i == total_files:  # Progress every 100 files or at the end
            print(f"Processing file {i}/{total_files}...")
        
        # Extract text and metadata from XML
        text, language_code, dialect = extract_text_from_xml(xml_path, use_standard)
        
        # If language filter is specified, skip files that don't match
        if language_filter and language_code.lower() != language_filter.lower():
            continue
        
        # If ignore_dialect is True, clear dialect to force testing all orthographies
        if ignore_dialect:
            dialect = ''
        
        # Analyze the text using the core analysis function
        result = analyze_text_for_orthography(text, language_code, dialect, orthography_data, xml_path)
        results.append(result)
    
    print(f"Completed analysis of {total_files} files.")
    return results


def summarize_analysis_results(results: List[Dict], ignore_dialect: bool = False) -> Dict:
    """
    Summarize analysis results across multiple files.
    
    Args:
        results: List of analysis results from multiple XML files
        
    Returns:
        Dictionary with aggregated statistics and most common orthography matches
    """
    if not results:
        return {'error': 'No analysis results to summarize'}
    
    # Filter out results with errors
    valid_results = [r for r in results if 'error' not in r]
    error_results = [r for r in results if 'error' in r]
    
    if not valid_results:
        return {
            'error': 'No valid analysis results found',
            'files_with_errors': len(error_results),
            'error_files': [r.get('file', 'unknown') for r in error_results]
        }
    
    # Aggregate statistics
    total_files = len(valid_results)
    total_characters = sum(r.get('total_characters_analyzed', 0) for r in valid_results)
    total_unique_letters = sum(r.get('unique_letters_found', 0) for r in valid_results)
    
    # Count languages and dialects
    languages = Counter()
    dialects = Counter()
    for result in valid_results:
        if result.get('normalized_language'):
            languages[result['normalized_language']] += 1
        if result.get('dialect'):
            dialects[result['dialect']] += 1
    
    # Group files by their XML dialect attribute (source dialect, not orthography dialect)
    # OR when ignore_dialect=True, group by best-matching orthography dialect
    dialect_groups = defaultdict(list)
    for result in valid_results:
        if ignore_dialect:
            # Group by best-matching orthography dialect (what the algorithm thinks fits best)
            best_match = result.get('best_match')
            if best_match:
                group_key = f"{best_match['dialect']}"
            else:
                group_key = 'unmatched'
        else:
            # Group by XML dialect attribute (original metadata)
            group_key = result.get('dialect', 'unspecified')
        
        dialect_groups[group_key].append(result)
    
    # Analyze orthography choices within each dialect group
    dialect_analysis = {}
    overall_orthography_choices = Counter()  # All test results
    overall_best_match_choices = Counter()   # Only best matches
    overall_average_scores = defaultdict(list)
    
    for group_key, files_in_group in dialect_groups.items():
        # Aggregate ALL orthography results for this dialect group (not just best matches)
        all_orthography_scores = defaultdict(list)
        best_match_choices = Counter()
        
        for result in files_in_group:
            # Count best matches for reference
            best_match = result.get('best_match')
            if best_match:
                lang = best_match['language']
                ortho = best_match['orthography']
                dialect_tested = best_match['dialect']
                
                # Create identifier for best match
                if dialect_tested == 'default':
                    best_ortho_id = f"{lang} - {ortho}"
                else:
                    best_ortho_id = f"{lang} ({dialect_tested}) - {ortho}"
                
                best_match_choices[best_ortho_id] += 1
                overall_best_match_choices[best_ortho_id] += 1
            
            # Collect ALL orthography test results for comprehensive analysis
            ortho_analysis = result.get('orthography_analysis', [])
            for match in ortho_analysis:
                lang = match['language']
                ortho = match['orthography']
                dialect_tested = match['dialect']
                score = match['score']
                
                # Create orthography identifier with dialect information
                if dialect_tested == 'default':
                    ortho_id = f"{lang} - {ortho}"
                else:
                    ortho_id = f"{lang} ({dialect_tested}) - {ortho}"
                all_orthography_scores[ortho_id].append(score)
                
                # Also add to overall totals
                if ignore_dialect:
                    # When ignoring dialect, use the group key (best-matching dialect)
                    if dialect_tested == 'default':
                        overall_ortho_id = f"{lang} ({group_key}) - {ortho}"
                    else:
                        overall_ortho_id = f"{lang} ({dialect_tested}) - {ortho}"
                else:
                    # When respecting dialect, show the dialect that was actually tested
                    if dialect_tested == 'default':
                        overall_ortho_id = f"{lang} - {ortho}"
                    else:
                        overall_ortho_id = f"{lang} ({dialect_tested}) - {ortho}"
                overall_orthography_choices[overall_ortho_id] += 1
                overall_average_scores[overall_ortho_id].append(score)
        
        # Calculate averages for all tested orthographies in this dialect group
        group_performance = {}
        for ortho_id, scores in all_orthography_scores.items():
            if scores:
                # Also collect unexpected percentages for this orthography across all files
                unexpected_percentages = []
                matched_counts = []
                total_letter_counts = []
                orthography_size = None  # Will be the same for all instances of this orthography
                
                # Find all results for this orthography to get additional metrics
                for result in files_in_group:
                    ortho_analysis = result.get('orthography_analysis', [])
                    for match in ortho_analysis:
                        # Create the same orthography identifier used in the outer loop
                        match_lang = match['language']
                        match_ortho = match['orthography'] 
                        match_dialect = match['dialect']
                        if match_dialect == 'default':
                            match_ortho_id = f"{match_lang} - {match_ortho}"
                        else:
                            match_ortho_id = f"{match_lang} ({match_dialect}) - {match_ortho}"
                        
                        if match_ortho_id == ortho_id:
                            unexpected_percentages.append(match['unexpected_percentage'])
                            matched_counts.append(match['matched_letters'])
                            total_letter_counts.append(match['total_text_letters'])
                            # Orthography size is constant for all instances of this orthography
                            if orthography_size is None:
                                orthography_size = match['orthography_size']
                
                group_performance[ortho_id] = {
                    'average_score': sum(scores) / len(scores),
                    'min_score': min(scores),
                    'max_score': max(scores),
                    'test_count': len(scores),  # Number of files that tested this orthography
                    'best_match_count': best_match_choices.get(ortho_id, 0),  # Files where this was the top choice
                    'avg_unexpected_percentage': sum(unexpected_percentages) / len(unexpected_percentages) if unexpected_percentages else 0.0,
                    'avg_matched_letters': sum(matched_counts) / len(matched_counts) if matched_counts else 0.0,
                    'orthography_size': orthography_size or 0  # Constant size of this orthography
                }
        
        # Find best orthography for this dialect group 
        # Prioritize orthographies that are actually chosen by files, then by average score
        best_for_group = None
        if group_performance:
            # Sort by: 1) number of files that chose this orthography (descending), 2) average score (descending)
            sorted_orthos = sorted(group_performance.items(), 
                                 key=lambda x: (x[1]['best_match_count'], x[1]['average_score']), 
                                 reverse=True)
            best_ortho_id, best_stats = sorted_orthos[0]
            
            # For the best orthography, find which dialect actually produced the best result
            # by looking at individual file results
            best_dialect_used = None
            for result in files_in_group:
                best_match = result.get('best_match')
                if best_match:
                    # Create the same identifier format
                    match_dialect = best_match['dialect']
                    if match_dialect == 'default':
                        match_ortho_id = f"{best_match['language']} - {best_match['orthography']}"
                    else:
                        match_ortho_id = f"{best_match['language']} ({match_dialect}) - {best_match['orthography']}"
                    
                    if match_ortho_id == best_ortho_id:
                        best_dialect_used = best_match['dialect']
                        break
            
            best_for_group = {
                'orthography': best_ortho_id,
                'dialect_tested': best_dialect_used,
                **best_stats
            }
        
        dialect_analysis[group_key] = {
            'file_count': len(files_in_group),
            'orthography_performance': group_performance,
            'best_match': best_for_group
        }
    
# Calculate overall average scores
    overall_avg_scores_summary = {}
    for ortho_id, scores in overall_average_scores.items():
        if scores:  # Only process if we have scores
            overall_avg_scores_summary[ortho_id] = {
                'average_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'file_count': len(scores)
            }

    # Find the most successful orthography overall based on best matches
    best_overall = None
    if overall_best_match_choices:
        # Primary criterion: most files that chose this orthography as their best match
        most_common_ortho = overall_best_match_choices.most_common(1)[0][0]
        if most_common_ortho in overall_avg_scores_summary:
            best_overall = {
                'orthography': most_common_ortho,
                'file_count': overall_best_match_choices[most_common_ortho],
                'percentage': (overall_best_match_choices[most_common_ortho] / total_files) * 100,
                **overall_avg_scores_summary[most_common_ortho]
            }
    
    return {
        'summary_statistics': {
            'total_files_analyzed': total_files,
            'files_with_errors': len(error_results),
            'total_characters_analyzed': total_characters,
            'average_characters_per_file': total_characters / total_files if total_files > 0 else 0,
            'total_unique_letters_found': total_unique_letters,
            'average_unique_letters_per_file': total_unique_letters / total_files if total_files > 0 else 0,
        },
        'language_distribution': dict(languages.most_common()),
        'dialect_distribution': dict(dialects.most_common()),
        'dialect_analysis': dialect_analysis,
        'overall_orthography_choices': dict(overall_orthography_choices.most_common()),
        'overall_orthography_performance': overall_avg_scores_summary,
        'best_overall_match': best_overall,
        'error_files': [r.get('file', 'unknown') for r in error_results] if error_results else []
    }


def analyze_xml_files_combined(directory: str, orthographies_dir: str, ignore_dialect: bool = False, use_standard: bool = False, language_filter: str = None) -> Dict:
    """
    Analyze all XML files in a directory by combining files with same dialect into single datasets.
    
    Args:
        directory: Directory containing XML files
        orthographies_dir: Path to the Orthographies directory
        ignore_dialect: If True, ignore XML dialect tags and test all orthographies
        use_standard: If True, analyze standard text; if False, analyze original text
        language_filter: If specified, only process XML files with this language code
        
    Returns:
        Dictionary with combined analysis results for each dialect group
    """
    # Load orthography data once for all files (optimization)
    orthography_data = load_orthography_data(orthographies_dir)
    
    # Collect all files and group by dialect
    dialect_groups = defaultdict(list)
    error_files = []
    
    # Count files first for progress tracking
    xml_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.xml'):
                xml_files.append(os.path.join(root, file))
    
    total_files = len(xml_files)
    if total_files == 0:
        print("No XML files found in directory")
        return {}
    
    print(f"Found {total_files} XML files to process...")
    
    # Process files with progress tracking
    for i, xml_path in enumerate(xml_files, 1):
        if i % 100 == 0 or i == total_files:  # Progress every 100 files or at the end
            print(f"Processing file {i}/{total_files}...")
        
        try:
            # Extract text and metadata from each file
            text, language_code, dialect = extract_text_from_xml(xml_path, use_standard)
            
            # If language filter is specified, skip files that don't match
            if language_filter and language_code.lower() != language_filter.lower():
                continue
            
            if text:  # Only include files with extractable text
                # Group files by dialect (or 'unspecified' if no dialect)
                group_key = dialect if dialect else 'unspecified'
                dialect_groups[group_key].append({
                    'text': text,
                    'language_code': language_code,
                    'dialect': dialect,
                    'file_path': xml_path
                })
            else:
                error_files.append(xml_path)
        except Exception as e:
            print(f"Error processing {xml_path}: {e}")
            error_files.append(xml_path)
    
    print(f"Completed processing {total_files} files. Found {len(dialect_groups)} dialect groups.")
    
    # Analyze each dialect group as a combined dataset
    results = {}
    for dialect_key, files_in_group in dialect_groups.items():
        print(f"Analyzing combined text for dialect group '{dialect_key}' ({len(files_in_group)} files)...")
        
        # Combine all text from files in this dialect group
        combined_text = ' '.join(f['text'] for f in files_in_group)
        
        # Use the first file's metadata as representative
        representative_file = files_in_group[0]
        language_code = representative_file['language_code']
        dialect = representative_file['dialect']
        
        # If ignore_dialect is True, clear dialect to force testing all orthographies
        if ignore_dialect:
            dialect = ''
        
        # Create group identifier for reporting
        file_list = [f['file_path'] for f in files_in_group]
        group_id = f"Combined {dialect_key} group ({len(files_in_group)} files)"
        
        # Analyze the combined text using the core analysis function
        analysis_result = analyze_text_for_orthography(combined_text, language_code, dialect, orthography_data, group_id)
        
        # Add additional metadata about the group
        analysis_result['files_in_group'] = file_list
        analysis_result['file_count'] = len(files_in_group)
        
        results[dialect_key] = analysis_result
    
    # Add error information to results
    if error_files:
        results['error_info'] = {
            'error_files': error_files,
            'error_count': len(error_files)
        }
    
    return results


def format_unexpected_tokens(unexpected_tokens: Dict[str, int], top_n: int = 10) -> str:
    """
    Format unexpected token counts: list the top_n most-common, then lump the rest as 'other'.
    """
    if not unexpected_tokens:
        return "None"
    sorted_unexpected = sorted(unexpected_tokens.items(), key=lambda x: (-x[1], x[0]))
    top = sorted_unexpected[:top_n]
    rest = sorted_unexpected[top_n:]
    parts = [f"{token}({count})" for token, count in top]
    if rest:
        other_count = sum(count for _, count in rest)
        parts.append(f"other({other_count})")
    return ', '.join(parts)


def display_combined_results(results: Dict) -> None:
    """
    Display results from combined analysis in a readable format.
    """
    print(f"=== Combined Analysis Results ===")
    
    # Calculate total files and errors from the new structure
    total_files = 0
    error_count = 0
    dialect_groups = {}
    
    for key, value in results.items():
        if key == 'error_info':
            error_count = value['error_count']
        else:
            dialect_groups[key] = value
            total_files += value.get('file_count', 0)
    
    print(f"Total files analyzed: {total_files}")
    print(f"Files with errors: {error_count}")
    print(f"Dialect groups found: {len(dialect_groups)}")
    print()
    
    for dialect_key, group_data in dialect_groups.items():
        print(f"=== Dialect Group: {dialect_key} ===")
        print(f"Files combined: {group_data['file_count']}")
        print(f"Combined text length: {group_data['total_characters_analyzed']:,} characters")
        print(f"Unique letters found: {group_data['unique_letters_found']}")
        print(f"Language: {group_data['extracted_language']} -> {group_data['normalized_language']}")
        print()
        
        # Show best match
        if group_data['best_match']:
            best = group_data['best_match']
            dialect_info = f" ({best['dialect']})" if best['dialect'] != 'default' else ""
            print(f"Best orthography: {best['language']}{dialect_info} - {best['orthography']}")
            print(f"  Score: {best['score']:.2%}")
            print(f"  Unexpected tokens: {best['unexpected_percentage']:.1f}%")
            print(f"  Letters matched: {best['matched_letters']}/{best['orthography_size']}")
            print(f"  Common letters: {best.get('common_letters', 0)}")
        
        # Show top 5 orthographies
        print(f"\nTop 7 orthographies for combined {dialect_key} corpus:")
        for i, match in enumerate(group_data['orthography_analysis'][:7]):
            rank = i + 1
            dialect_info = f" ({match['dialect']})" if match['dialect'] != 'default' else ""
            print(f"  {rank}. {match['language']}{dialect_info} - {match['orthography']}")
            print(f"     Score: {match['score']:.2%}")
            print(f"     Unexpected tokens: {match['unexpected_percentage']:.1f}%")
            print(f"     Letters matched: {match['matched_letters']}/{match['orthography_size']}")
            print(f"     Common letters: {match.get('common_letters', 0)}")
            
            # Show missing letters
            missing_letters = match.get('missing_letters', [])
            if missing_letters:
                missing_str = ', '.join(missing_letters)
                print(f"     Missing letters: {missing_str}")
            else:
                print(f"     Missing letters: None")
            
            # Show unexpected tokens
            unexpected_tokens = match.get('unexpected_tokens', {})
            print(f"     Unexpected tokens: {format_unexpected_tokens(unexpected_tokens)}")
        
        print(f"\nFiles included in {dialect_key} group:")
        for file_path in group_data.get('files_in_group', [])[:10]:  # Show first 10 files
            print(f"  - {file_path}")
        if len(group_data.get('files_in_group', [])) > 10:
            print(f"  ... and {len(group_data['files_in_group']) - 10} more files")
        
        print("=" * 60)
        print()


# Example usage and demonstration
if __name__ == "__main__":
    import sys
    import argparse
    
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description='Analyze XML files to determine orthography systems used',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Examples:
  python orthography_detector.py /path/to/file.xml
  python orthography_detector.py /path/to/xml/directory
  python orthography_detector.py /path/to/file.xml --orthographies /custom/orthographies
  python orthography_detector.py /path/to/directory --ignore-dialect
        '''
    )
    
    parser.add_argument('input_path', 
                       help='XML file or directory containing XML files to analyze')
    parser.add_argument('--orthographies', '-o',
                       default=str(Path(__file__).parent.parent.parent / 'Orthographies'),
                       help='Path to orthographies directory (default: ../../Orthographies relative to script)')
    parser.add_argument('--ignore-dialect', '-i',
                       action='store_true',
                       help='Ignore XML dialect tags and test all orthographies equally')
    parser.add_argument('--combine', '-c',
                       action='store_true',
                       help='Combine all files with same dialect into single dataset for analysis')
    parser.add_argument('--use-standard', '-s',
                       action='store_true',
                       help='Analyze standard text instead of original text')
    parser.add_argument('--language', '-l',
                       help='Only process XML files with this specific language (ISO 639-3 code)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if input path exists
    if not os.path.exists(args.input_path):
        print(f"Error: Path '{args.input_path}' does not exist.")
        sys.exit(1)
    
    # Check if orthographies directory exists
    if not os.path.exists(args.orthographies):
        print(f"Error: Orthographies directory '{args.orthographies}' does not exist.")
        sys.exit(1)
    
    # Determine if input is a file or directory
    if os.path.isfile(args.input_path):
        # Single file analysis
        if not args.input_path.endswith('.xml'):
            print(f"Error: '{args.input_path}' is not an XML file.")
            sys.exit(1)
            
        dialect_info = " (ignoring dialect)" if args.ignore_dialect else ""
        print(f"Analyzing single file: {args.input_path}{dialect_info}")
        result = determine_orthography(args.input_path, args.orthographies, ignore_dialect=args.ignore_dialect, use_standard=args.use_standard)
        
        # Display the results in a user-friendly format
        if 'error' in result:
            print(f"Error: {result['error']}")
            sys.exit(1)
            
        print("=== Orthography Analysis ===")
        print(f"File: {result['file']}")
        print(f"Language: {result['extracted_language']} -> {result['normalized_language']}")
        print(f"Dialect: {result['dialect']}")
        print(f"Text sample: {result['text_sample']}")
        print(f"Letters found: {result['letters_found']}")
        print(f"Total unique letters: {result['unique_letters_found']}")
        
        # Show all orthography matches
        print("\n=== All Orthography Matches ===")
        for i, match in enumerate(result['orthography_analysis']):
            dialect_info = f" ({match['dialect']})" if match['dialect'] != 'default' else ""
            print(f"{i+1}. {match['language']}{dialect_info} - {match['orthography']}")
            print(f"   Score: {match['score']:.2%}")
            print(f"   Letters matched: {match['matched_letters']}")
            print(f"   Common letters: {match.get('common_letters', 0)}")
            print(f"   Unexpected letter types: {match['unexpected_letter_types']}")
            print(f"   Unexpected token %: {match['unexpected_percentage']:.1f}%")
            print()
        
        # Highlight the best match
        if result['best_match']:
            best = result['best_match']
            dialect_info = f" ({best['dialect']})" if best['dialect'] != 'default' else ""
            print(f"=== Best Match ===")
            print(f"Orthography: {best['language']}{dialect_info} - {best['orthography']}")
            print(f"Match Score: {best['score']:.2%}")
            
            # Show missing letters and unexpected tokens
            missing_letters = best.get('missing_letters', [])
            if missing_letters:
                print(f"Missing Letters: {', '.join(missing_letters)}")
            else:
                print(f"Missing Letters: None")
            
            unexpected_tokens = best.get('unexpected_tokens', {})
            print(f"Unexpected Tokens: {format_unexpected_tokens(unexpected_tokens)}")
            
    elif os.path.isdir(args.input_path):
        # Directory analysis
        if args.combine:
            # Combined analysis mode
            dialect_info = " (ignoring dialect tags)" if args.ignore_dialect else ""
            print(f"Analyzing directory with combined dialect analysis: {args.input_path}{dialect_info}")
            combined_results = analyze_xml_files_combined(args.input_path, args.orthographies, ignore_dialect=args.ignore_dialect, use_standard=args.use_standard, language_filter=args.language)
            display_combined_results(combined_results)
        else:
            # File-by-file analysis mode (existing behavior)
            dialect_info = " (ignoring dialect tags)" if args.ignore_dialect else ""
            print(f"Analyzing all XML files in directory: {args.input_path}{dialect_info}")
            results = analyze_xml_files(args.input_path, args.orthographies, ignore_dialect=args.ignore_dialect, use_standard=args.use_standard, language_filter=args.language)
        
            if not results:
                print("No XML files found in the specified directory.")
                sys.exit(1)
            
            # Filter out results with errors
            valid_results = [r for r in results if 'error' not in r]
            error_results = [r for r in results if 'error' in r]
        
            if not valid_results:
                print("No valid analysis results found.")
                if error_results:
                    print("Files with errors:")
                    for error_result in error_results:
                        print(f"- {error_result.get('file', 'unknown')}")
                sys.exit(1)
        
            # Display summary statistics
            print("=== Directory Analysis Summary ===")
            print(f"Total files analyzed: {len(valid_results)}")
            print(f"Files with errors: {len(error_results)}")
            total_chars = sum(r.get('total_characters_analyzed', 0) for r in valid_results)
            total_letters = sum(r.get('unique_letters_found', 0) for r in valid_results)
            print(f"Average total characters per file: {total_chars / len(valid_results):.1f}")
            print(f"Average unique letter types per file: {total_letters / len(valid_results):.1f}")
            
            # Collect and aggregate orthography matches across all files
            orthography_aggregates = defaultdict(lambda: {
                'scores': [],
                'matched_letters': [],
                'total_letters': [],
                'unexpected_types': [],
                'unexpected_percentages': [],
                'orthography_sizes': [],
                'files': []
            })
            
            for result in valid_results:
                file_name = result.get('file', 'unknown').split('/')[-1]
                for match in result.get('orthography_analysis', []):
                    # Create orthography identifier
                    language = match['language']
                    dialect = match['dialect']
                    orthography = match['orthography']
                    
                    if dialect == 'default':
                        ortho_id = f"{language} - {orthography}"
                    elif dialect == 'default':
                        continue  # Skip default entries in detailed output
                    else:
                        ortho_id = f"{language} ({dialect}) - {orthography}"
                    
                    # Calculate orthography size from the score and matched letters
                    # Since score = matched_letters / orthography_size, we can derive:
                    # orthography_size = matched_letters / score (when score > 0)
                    if match['score'] > 0:
                        orthography_size = match['matched_letters'] / match['score']
                    else:
                        # Fallback: estimate from the data we have
                        orthography_size = match['matched_letters'] + match['unexpected_letter_types']
                    
                    # Aggregate data for this orthography
                    orthography_aggregates[ortho_id]['scores'].append(match['score'])
                    orthography_aggregates[ortho_id]['matched_letters'].append(match['matched_letters'])
                    orthography_aggregates[ortho_id]['total_letters'].append(match['total_text_letters'])
                    orthography_aggregates[ortho_id]['unexpected_types'].append(match['unexpected_letter_types'])
                    orthography_aggregates[ortho_id]['unexpected_percentages'].append(match['unexpected_percentage'])
                    orthography_aggregates[ortho_id]['orthography_sizes'].append(orthography_size)
                    orthography_aggregates[ortho_id]['files'].append(file_name)
            
            # Calculate aggregate statistics and sort by average score
            aggregated_results = []
            for ortho_id, data in orthography_aggregates.items():
                if not data['scores']:  # Skip empty entries
                    continue
                    
                avg_score = sum(data['scores']) / len(data['scores'])
                min_score = min(data['scores'])
                max_score = max(data['scores'])
                file_count = len(data['scores'])
                avg_matched = sum(data['matched_letters']) / len(data['matched_letters'])
                avg_orthography_size = sum(data['orthography_sizes']) / len(data['orthography_sizes'])
                avg_total = sum(data['total_letters']) / len(data['total_letters'])
                avg_unexpected_types = sum(data['unexpected_types']) / len(data['unexpected_types'])
                avg_unexpected_pct = sum(data['unexpected_percentages']) / len(data['unexpected_percentages'])
                
                aggregated_results.append({
                    'orthography': ortho_id,
                    'avg_score': avg_score,
                    'min_score': min_score,
                    'max_score': max_score,
                    'file_count': file_count,
                    'avg_matched': avg_matched,
                    'avg_orthography_size': avg_orthography_size,
                    'avg_total': avg_total,
                    'avg_unexpected_types': avg_unexpected_types,
                    'avg_unexpected_pct': avg_unexpected_pct
                })
            
            # Generate and show summary using new dialect-based approach
            summary = summarize_analysis_results(results, ignore_dialect=args.ignore_dialect)
            
            # Display results by dialect group  
            if 'dialect_analysis' in summary and summary['dialect_analysis']:
                if args.ignore_dialect:
                    print(f"\n=== Results by Best-Matching Orthography Dialect ===")
                    group_description = "Files grouped by the orthography dialect that performed best (ignoring XML dialect tags)"
                else:
                    print(f"\n=== Results by XML Dialect ===")
                    group_description = "Files grouped by their XML dialect attribute"
                
                print(f"({group_description})")
                
                for group_key, dialect_info in summary['dialect_analysis'].items():
                    if args.ignore_dialect:
                        dialect_label = f"Best-match: {group_key}" if group_key != 'unmatched' else 'No clear best match'
                    else:
                        dialect_label = group_key if group_key != 'unspecified' else 'No dialect specified'
                    print(f"\n--- {dialect_label} ({dialect_info['file_count']} files) ---")
                    
                    if dialect_info['best_match']:
                        best = dialect_info['best_match']
                        if args.ignore_dialect:
                            print(f"Best orthography: {best['orthography']}")
                        else:
                            # Show the dialect that was actually used for the best-matching test
                            best_ortho_parts = best['orthography'].split(' - ')
                            if len(best_ortho_parts) == 2:
                                lang_part, ortho_part = best_ortho_parts
                                print(f"Best orthography: {lang_part} ({best.get('dialect_tested', 'unknown')}) - {ortho_part}")
                            else:
                                print(f"Best orthography: {best['orthography']}")
                        print(f"  Score: {best['average_score']:.2%}")
                        print(f"  Score Range: {best['min_score']:.2%} - {best['max_score']:.2%}")
                        print(f"  Unexpected tokens: {best['avg_unexpected_percentage']:.1f}%")
                        print(f"  Top choice in: {best['best_match_count']} files")
                    
                    # Show top 8 orthographies (or fewer if not enough)
                    performance_items = list(dialect_info['orthography_performance'].items())
                    # Sort by: 1) number of files that chose this orthography (descending), 2) average score (descending)
                    performance_items.sort(key=lambda x: (x[1]['best_match_count'], x[1]['average_score']), reverse=True)
                    
                    top_count = min(8, len(performance_items))
                    print(f"  Top {top_count} orthographies tested:")
                    
                    for i, (ortho_id, perf) in enumerate(performance_items[:top_count]):
                        rank = i + 1
                        print(f"    {rank}. {ortho_id}")
                        print(f"       Score: {perf['average_score']:.2%} (range: {perf['min_score']:.2%} - {perf['max_score']:.2%})")
                        print(f"       Unexpected tokens: {perf['avg_unexpected_percentage']:.1f}%")
                        print(f"       Letters matched: {perf['avg_matched_letters']:.1f}/{perf['orthography_size']}")
                        print(f"       Top choice: {perf['best_match_count']}/{perf['test_count']} files")
            
            # Show overall best match
            if 'best_overall_match' in summary and summary['best_overall_match']:
                best = summary['best_overall_match']
                print(f"\n=== Best Overall Orthography (All Files Combined) ===")
                print(f"Orthography: {best['orthography']}")
                print(f"Used by: {best['file_count']} files ({best['percentage']:.1f}%)")
                print(f"Average Score: {best['average_score']:.2%}")
                print(f"Score Range: {best['min_score']:.2%} - {best['max_score']:.2%}")
            
            if error_results:
                print(f"\n=== Files with Errors ===")
                for error_result in error_results:
                    print(f"- {error_result.get('file', 'unknown')}")
    else:
        print(f"Error: '{args.input_path}' is neither a file nor a directory.")
        sys.exit(1)