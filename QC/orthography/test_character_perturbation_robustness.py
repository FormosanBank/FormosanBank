"""
Comprehensive test suite for character perturbation robustness across Formosan languages.

This script generates a full corpus for each language/dialect combination, samples 1/5 as
a target corpus, and measures the robustness of n-gram statistics (character and word level)
when the most frequent character is swapped with a random character.

Usage:
    python test_character_perturbation_robustness.py [--output-dir OUTPUT_DIR] [--languages LANG1 LANG2 ...] [--sources SOURCE1 SOURCE2 ...]

Example:
    python test_character_perturbation_robustness.py --languages ami tay bnn pwn --output-dir test_results/
    python test_character_perturbation_robustness.py --sources ePark ILRDF_Dicts
"""

import string

from orthography_extract import generate_corpus, extract_orthographic_info, is_dialect, remove_chinese_characters
from orthography_compare import jaccard_similarity, overlap_coefficient, normalize_vector, cosine_similarity, euclidean, kl_divergence
import numpy as np
import random
import re
import math
import argparse
import pandas as pd
import json
import os
from pathlib import Path
from collections import Counter
from datetime import datetime
import logging

# Configure logging
def setup_logging(log_dir):
    """Set up logging to file and console with UTF-8 encoding."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Create handlers with explicit UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    stream_handler = logging.StreamHandler()
    # Set encoding with error handling for Windows console
    stream_handler.stream.reconfigure(encoding='utf-8', errors='replace') if hasattr(stream_handler.stream, 'reconfigure') else None
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            stream_handler
        ]
    )
    return logging.getLogger(__name__)


def get_available_languages():
    """Get all officially recognized languages from dialects.csv."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        return sorted(dialect_csv['Language'].unique())
    except Exception as e:
        logging.error(f"Error reading dialects.csv: {e}")
        return []


def get_available_dialects(language):
    """Get all available dialects for a given language."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        lang_data = dialect_csv[dialect_csv['Language'] == language]
        if lang_data.empty:
            return []
        return sorted(lang_data['Official'].dropna().unique().tolist())
    except Exception as e:
        logging.error(f"Error reading dialects for {language}: {e}")
        return []


def get_language_code_to_name_map():
    """Map 3-letter language codes to full language names from dialects.csv."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        lang_names = sorted(dialect_csv['Language'].unique())
        
        # Explicit mapping for known language codes
        explicit_mapping = {
            'ami': 'Amis',
            'tay': 'Atayal',
            'bnn': 'Bunun',
            'pwn': 'Paiwan',
            'pyu': 'Puyuma',
            'dru': 'Rukai',
            'trv': 'Seediq',
            'tao': 'Yami',
            'kna': 'Kanakanavu',
            'tsou': 'Tsou',
            'sya': 'Saisiyat',
            'ckv': 'Kavalan',
            'xnb': 'Saaroa',
            'ssa': 'Sakizaya',
            'sai': 'Siraya',
            'thk': 'Thao',
        }
        
        return explicit_mapping
    except Exception as e:
        logging.error(f"Error building language code map: {e}")
        return {}


def resolve_language_name(lang_input):
    """
    Resolve language input (either code or full name) to full name from dialects.csv.
    
    Accepts:
    - 3-letter code: "ami" -> "Amis"
    - Full name: "Amis" -> "Amis"
    - Mixed case: "AMI" -> "Amis"
    
    Returns tuple of (full_name, language_code) or (None, None) if not found.
    """
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        lang_names = sorted(dialect_csv['Language'].unique())
        code_to_name = get_language_code_to_name_map()
        
        # Try exact match first (for full names)
        if lang_input in lang_names:
            # Find the code for this name
            code = None
            for c, name in code_to_name.items():
                if name == lang_input:
                    code = c
                    break
            if code:
                return lang_input, code
        
        # Try case-insensitive match for full names
        lang_input_lower = lang_input.lower()
        for name in lang_names:
            if name.lower() == lang_input_lower:
                # Find the code for this name
                code = None
                for c, n in code_to_name.items():
                    if n == name:
                        code = c
                        break
                if code:
                    return name, code
        
        # Try code lookup (3-letter codes)
        code_lower = lang_input.lower()
        if code_lower in code_to_name:
            name = code_to_name[code_lower]
            return name, code_lower
        
        return None, None
    except Exception as e:
        logging.error(f"Error resolving language name: {e}")
        return None, None


def sanitize_for_filename(char):
    """Replace illegal filename characters with safe representations."""
    illegal_chars = {
        '<': 'lt',
        '>': 'gt',
        ':': 'colon',
        '"': 'quote',
        '/': 'slash',
        '\\': 'backslash',
        '|': 'pipe',
        '?': 'question',
        '*': 'asterisk',
    }
    if char in illegal_chars:
        return f"_{illegal_chars[char]}_"
    return char


def char_tokenize(corpus):
    """Tokenize corpus into characters (excluding whitespace)."""
    return [char for char in corpus if not char.isspace()]


def word_tokenize(corpus, lang):
    """Tokenize corpus into words using language-specific orthography."""
    try:
        lang_ortho_table = pd.read_csv(f"Orthographies/Ortho113/{lang}.tsv", sep='\t')
        special_chars = set(str(char) for char in lang_ortho_table['letter'].to_list() 
                           if pd.notna(char))
        regex = r"[\w" + "".join(re.escape(char) for char in special_chars) + r"]+"
        return re.findall(regex, corpus)
    except FileNotFoundError:
        # File doesn't exist - use basic tokenization without warning
        return re.findall(r'\w+', corpus)
    except Exception as e:
        logging.debug(f"Error tokenizing with orthography for {lang}: {e}. Using basic tokenization.")
        return re.findall(r'\w+', corpus)


def compute_ngram_similarity_metrics(tokens, gram_length, laplace=True):
    """
    Compute n-gram similarity metrics for a given token sequence and gram length.
    
    Returns dict with:
        - jaccard_similarity
        - overlap_coefficient
        - cosine_similarity
        - euclidean_distance
        - kl_divergence
        - unique_ngram_count
    """
    def get_ngrams(token_list):
        ngrams = [tuple(token_list[i:i + gram_length]) 
                 for i in range(len(token_list) - gram_length + 1)]
        return Counter(ngrams)
    
    if len(tokens) < gram_length:
        # Return minimal results if insufficient tokens
        return {
            "n": gram_length,
            "jaccard_similarity": 0.0,
            "overlap_coefficient": 0.0,
            "cosine_similarity": 0.0,
            "euclidean_distance": 0.0,
            "kl_divergence": 0.0,
            "unique_ngram_count": len(set(tokens[:gram_length])),
        }
    
    ngrams = get_ngrams(tokens)
    ngrams_set = set(ngrams.elements())
    
    freq_vector = np.array([ngrams[n] + (1 if laplace else 0) for n in ngrams_set], dtype=float)
    freq_vector = normalize_vector(freq_vector)
    
    # For single corpus, compute self-similarity
    cosine_sim = 1.0 if len(freq_vector) > 0 else 0.0
    
    return {
        "n": gram_length,
        "jaccard_similarity": 1.0,  # Self-similarity
        "overlap_coefficient": 1.0,  # Self-similarity
        "cosine_similarity": float(cosine_sim),
        "euclidean_distance": 0.0,
        "kl_divergence": 0.0,
        "unique_ngram_count": len(ngrams_set),
    }


def compute_reference_target_metrics(ref_tokens, target_tokens, gram_length, laplace=True):
    """
    Compute n-gram similarity metrics between reference and target corpora.
    
    Returns dict with similarity metrics between two token sequences.
    """
    def get_ngrams(token_list):
        ngrams = [tuple(token_list[i:i + gram_length]) 
                 for i in range(len(token_list) - gram_length + 1)]
        return Counter(ngrams)
    
    if len(ref_tokens) < gram_length or len(target_tokens) < gram_length:
        return {
            "n": gram_length,
            "jaccard_similarity": 0.0,
            "overlap_coefficient": 0.0,
            "cosine_similarity": 0.0,
            "euclidean_distance": 0.0,
            "kl_divergence": 0.0,
            "ref_unique_ngram_count": 0,
            "target_unique_ngram_count": 0,
        }
    
    ref_ngrams = get_ngrams(ref_tokens)
    target_ngrams = get_ngrams(target_tokens)
    
    ref_ngrams_set = set(ref_ngrams.elements())
    target_ngrams_set = set(target_ngrams.elements())
    all_ngrams = ref_ngrams_set.union(target_ngrams_set)
    
    if not all_ngrams:
        return {
            "n": gram_length,
            "jaccard_similarity": 0.0,
            "overlap_coefficient": 0.0,
            "cosine_similarity": 0.0,
            "euclidean_distance": 0.0,
            "kl_divergence": 0.0,
            "ref_unique_ngram_count": 0,
            "target_unique_ngram_count": 0,
        }
    
    # Laplace smoothing
    ref_freq_vector = np.array([(ref_ngrams[n] + (1 if laplace else 0)) for n in all_ngrams], dtype=float)
    target_freq_vector = np.array([(target_ngrams[n] + (1 if laplace else 0)) for n in all_ngrams], dtype=float)
    
    ref_freq_vector = normalize_vector(ref_freq_vector)
    target_freq_vector = normalize_vector(target_freq_vector)
    
    jaccard = jaccard_similarity(ref_ngrams_set, target_ngrams_set)
    overlap = overlap_coefficient(ref_ngrams_set, target_ngrams_set)
    cosine = cosine_similarity(np.array([ref_freq_vector]), np.array([target_freq_vector]))[0][0]
    euclidean_dist = euclidean(ref_freq_vector, target_freq_vector)
    kl_div = kl_divergence(ref_freq_vector, target_freq_vector)
    
    return {
        "n": gram_length,
        "jaccard_similarity": float(jaccard),
        "overlap_coefficient": float(overlap),
        "cosine_similarity": float(cosine),
        "euclidean_distance": float(euclidean_dist),
        "kl_divergence": float(kl_div),
        "ref_unique_ngram_count": len(ref_ngrams_set),
        "target_unique_ngram_count": len(target_ngrams_set),
    }


def analyze_corpus_partition(ref_corpus, target_corpus, lang, max_gram_length=3):
    """
    Analyze a reference and target corpus pair at character and word levels
    for gram lengths 1 to max_gram_length.
    
    Returns dict with character and word level metrics for each gram length.
    """
    ref_char_tokens = char_tokenize(ref_corpus)
    target_char_tokens = char_tokenize(target_corpus)
    ref_word_tokens = word_tokenize(ref_corpus, lang)
    target_word_tokens = word_tokenize(target_corpus, lang)
    
    results = {
        "character": {},
        "word": {},
        "token_counts": {
            "ref_char_tokens": len(ref_char_tokens),
            "target_char_tokens": len(target_char_tokens),
            "ref_word_tokens": len(ref_word_tokens),
            "target_word_tokens": len(target_word_tokens),
        }
    }
    
    for gram_length in range(1, max_gram_length + 1):
        results["character"][gram_length] = compute_reference_target_metrics(
            ref_char_tokens, target_char_tokens, gram_length
        )
        results["word"][gram_length] = compute_reference_target_metrics(
            ref_word_tokens, target_word_tokens, gram_length
        )
    
    return results


def compute_metric_deltas(baseline_metrics, perturbed_metrics, max_gram_length=3):
    """
    Compute absolute changes in metrics between baseline and perturbed corpora.
    
    Returns dict with delta values for cosine_similarity and kl_divergence
    at each gram length and level.
    """
    deltas = {
        "character": {},
        "word": {}
    }
    
    metrics_to_track = ["cosine_similarity", "kl_divergence"]
    
    for level in ["character", "word"]:
        for gram_length in range(1, max_gram_length + 1):
            baseline = baseline_metrics[level][gram_length]
            perturbed = perturbed_metrics[level][gram_length]
            
            deltas[level][gram_length] = {}
            for metric in metrics_to_track:
                delta = abs(perturbed[metric] - baseline[metric])
                deltas[level][gram_length][metric] = float(delta)
    
    return deltas


def test_language_dialect(lang_full_name, lang_code, dialect, sources, output_dir, test_ratio=0.2, laplace=True, num_swaps=5):
    """
    Run full perturbation test for a single language/dialect combination.
    
    Args:
        lang_full_name: Full language name (e.g., 'Amis') for corpus generation
        lang_code: Language code (e.g., 'ami') for tokenization and results
        dialect: Dialect name
        sources: List of source directories (e.g., ['ePark/', 'ILRDF_Dicts/'])
        output_dir: Directory to save results
        test_ratio: Fraction of corpus to use as target (default 1/5)
        laplace: Whether to use Laplace smoothing
        num_swaps: Number of unique random character swaps to perform (default 5)
    
    Returns:
        Dict with test results containing averaged metrics across all swaps
    """
    logger = logging.getLogger(__name__)
    
    # Generate combined corpus from all sources
    corpus_text = ""
    sources_found = []
    
    for source in sources:
        corpus_path = f"Corpora/{source}"
        if os.path.exists(corpus_path):
            try:
                # Use full language name for corpus generation
                corpus = generate_corpus(lang_full_name, corpus_path, "standard", by_dialect=True, phonetic=False)
                if dialect in corpus.keys():
                    corpus_text += corpus[dialect]
                    sources_found.append(source)
            except Exception as e:
                logger.warning(f"Error generating corpus from {source}: {e}")
    
    if not corpus_text:
        logger.error(f"No corpus found for {lang_code}/{dialect} in sources")
        return None
    
    # Clean and split corpus
    corpus_text = remove_chinese_characters(corpus_text)
    sentences = re.split(r'(?<=[.!?])\s+', corpus_text)
    
    if len(sentences) < 2:
        logger.warning(f"Insufficient sentences for {lang_code}/{dialect}")
        return None
    
    # Split into reference and target
    random.seed(42)  # Deterministic splitting
    num_target = max(1, int(len(sentences) * test_ratio))
    target_indices = set(random.sample(range(len(sentences)), num_target))
    
    ref_sentences = [s for i, s in enumerate(sentences) if i not in target_indices]
    target_sentences = [s for i, s in enumerate(sentences) if i in target_indices]
    
    ref_text = "".join(ref_sentences)
    target_text = "".join(target_sentences)
    
    # Analyze baseline
    logger.info(f"Analyzing baseline for {lang_code}/{dialect}...")
    # Use language code for tokenization
    baseline_metrics = analyze_corpus_partition(ref_text, target_text, lang_code)
    
    # Extract target character frequencies
    target_char_info = extract_orthographic_info(target_text)
    
    if not target_char_info['character_frequency']:
        logger.warning(f"No character frequencies for {lang_code}/{dialect}")
        return None
    
    available_chars = list(set(target_char_info['unique_characters']))
    
    if not available_chars:
        logger.warning(f"No alternate characters available for {lang_code}/{dialect}")
        return None
    
    # Perform character swaps for CHARACTER-level metrics
    # COMMENTED OUT: Original random character swap strategy
    # for swap_idx in range(num_swaps):
    #     # Select a unique random character for this swap
    #     random_char = random.choice(list(set(available_chars).difference(set(string.punctuation))))
    #     other_random_char = random.choice(list(set(available_chars).difference(set(string.punctuation)) - {random_char}))
    #     logger.info(f"  Swap {swap_idx + 1}/{num_swaps}: '{other_random_char}' -> '{random_char}'")
    #     swapped_target_text = target_text.translate(str.maketrans(other_random_char, random_char))
    #     perturbed_metrics = analyze_corpus_partition(ref_text, swapped_target_text, lang_code)
    #     deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
    #     all_char_deltas.append(deltas)
    
    # NEW: Swap max frequency character with random characters
    logger.info(f"Testing max frequency character swaps for character-level metrics...")
    all_char_deltas = []
    all_char_perturbations = []
    
    # Get the character with maximum frequency
    max_freq_char = max(target_char_info['character_frequency'].items(), key=lambda x: x[1])[0]
    max_freq_count = target_char_info['character_frequency'][max_freq_char]
    
    # Get list of alternate characters (excluding punctuation and the max char itself)
    alternate_chars = list(set(available_chars).difference(set(string.punctuation)).difference({max_freq_char}))
    
    if not alternate_chars:
        logger.warning(f"No alternate characters for {lang_code}/{dialect}")
        alternate_chars = list(set(available_chars).difference({max_freq_char}))
    
    for swap_idx in range(min(num_swaps, len(alternate_chars))):
        # Select a random character to replace the max frequency character
        random_char = alternate_chars[swap_idx] if swap_idx < len(alternate_chars) else random.choice(alternate_chars)
        
        logger.info(f"  Swap {swap_idx + 1}: '{max_freq_char}' (freq={max_freq_count}) -> '{random_char}'")
        swapped_target_text = target_text.translate(str.maketrans(max_freq_char, random_char))
        
        # Analyze perturbed corpus
        perturbed_metrics = analyze_corpus_partition(ref_text, swapped_target_text, lang_code)
        
        # Compute deltas for this swap
        deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
        all_char_deltas.append(deltas)
        all_char_perturbations.append({
            "swap_number": swap_idx + 1,
            "max_frequency_character": max_freq_char,
            "character_frequency": max_freq_count,
            "swapped_with_character": random_char,
            "metric_deltas": deltas
        })
    
    # Average the CHARACTER-level deltas across all character swaps
    averaged_char_deltas = {"character": {}}
    for gram_length in all_char_deltas[0]["character"].keys():
        averaged_char_deltas["character"][gram_length] = {}
        for metric in ["cosine_similarity", "kl_divergence"]:
            values = [delta["character"][gram_length][metric] for delta in all_char_deltas]
            averaged_char_deltas["character"][gram_length][metric] = float(np.mean(values))
    
    # Copy other character metrics from first delta (they should be the same for all)
    for gram_length in all_char_deltas[0]["character"].keys():
        for metric in all_char_deltas[0]["character"][gram_length].keys():
            if metric not in ["cosine_similarity", "kl_divergence"]:
                averaged_char_deltas["character"][gram_length][metric] = all_char_deltas[0]["character"][gram_length][metric]
    
    # Perform word swaps for WORD-level metrics
    # COMMENTED OUT: Original random word swap strategy
    # for swap_idx in range(num_swaps):
    #     # Select two random distinct words
    #     idx1, idx2 = random.sample(range(len(words)), min(2, len(words)))
    #     word1, word2 = words[idx1], words[idx2]
    #     logger.info(f"  Swap {swap_idx + 1}/{num_swaps}: '{word1}' <-> '{word2}'")
    #     placeholder = f"__PLACEHOLDER_{swap_idx}__"
    #     swapped_target_text = re.sub(r'\b' + re.escape(word1) + r'\b', placeholder, swapped_target_text)
    #     swapped_target_text = re.sub(r'\b' + re.escape(word2) + r'\b', word1, swapped_target_text)
    #     swapped_target_text = swapped_target_text.replace(placeholder, word2)
    #     perturbed_metrics = analyze_corpus_partition(ref_text, swapped_target_text, lang_code)
    #     deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
    #     all_word_deltas.append(deltas)
    
    # NEW: Swap max frequency word with random words
    logger.info(f"Testing max frequency word swaps for word-level metrics...")
    all_word_deltas = []
    all_word_perturbations = []
    
    # Extract words from target text
    words = re.findall(r'\b\w+\b', target_text)
    if len(words) < 2:
        logger.warning(f"Insufficient words in target text for {lang_code}/{dialect}")
        # Fall back to using word deltas from character swaps if we can't do word swaps
        all_word_deltas = [delta for delta in all_char_deltas]
    else:
        # Compute word frequencies
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get the word with maximum frequency
        max_freq_word = max(word_freq.items(), key=lambda x: x[1])[0]
        max_freq_count = word_freq[max_freq_word]
        
        # Get list of alternate words (excluding the max frequency word)
        alternate_words = list(set(words) - {max_freq_word})
        
        if not alternate_words:
            logger.warning(f"No alternate words for {lang_code}/{dialect}")
            all_word_deltas = [delta for delta in all_char_deltas]
        else:
            for swap_idx in range(min(num_swaps, len(alternate_words))):
                # Select a random word to replace the max frequency word
                random_word = alternate_words[swap_idx] if swap_idx < len(alternate_words) else random.choice(alternate_words)
                
                logger.info(f"  Swap {swap_idx + 1}: '{max_freq_word}' (freq={max_freq_count}) -> '{random_word}'")
                
                # Create word-swapped version of target text
                swapped_target_text = target_text
                placeholder = f"__PLACEHOLDER_{swap_idx}__"
                swapped_target_text = re.sub(r'\b' + re.escape(max_freq_word) + r'\b', placeholder, swapped_target_text)
                swapped_target_text = re.sub(r'\b' + re.escape(random_word) + r'\b', max_freq_word, swapped_target_text)
                swapped_target_text = swapped_target_text.replace(placeholder, random_word)
                
                # Analyze perturbed corpus
                perturbed_metrics = analyze_corpus_partition(ref_text, swapped_target_text, lang_code)
                
                # Compute deltas for this swap
                deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
                all_word_deltas.append(deltas)
                all_word_perturbations.append({
                    "swap_number": swap_idx + 1,
                    "max_frequency_word": max_freq_word,
                    "word_frequency": max_freq_count,
                    "swapped_with_word": random_word,
                    "metric_deltas": deltas
                })
    
    # Average the WORD-level deltas across all word swaps
    averaged_word_deltas = {"word": {}}
    for gram_length in all_word_deltas[0]["word"].keys():
        averaged_word_deltas["word"][gram_length] = {}
        for metric in ["cosine_similarity", "kl_divergence"]:
            values = [delta["word"][gram_length][metric] for delta in all_word_deltas]
            averaged_word_deltas["word"][gram_length][metric] = float(np.mean(values))
    
    # Copy other word metrics from first delta (they should be the same for all)
    for gram_length in all_word_deltas[0]["word"].keys():
        for metric in all_word_deltas[0]["word"][gram_length].keys():
            if metric not in ["cosine_similarity", "kl_divergence"]:
                averaged_word_deltas["word"][gram_length][metric] = all_word_deltas[0]["word"][gram_length][metric]
    
    # Combine character and word deltas
    averaged_deltas = {**averaged_char_deltas, **averaged_word_deltas}
    
    # Compile results
    results = {
        "language": lang_code,
        "dialect": dialect,
        "sources": sources_found,
        "corpus_stats": {
            "total_sentences": len(sentences),
            "reference_sentences": len(ref_sentences),
            "target_sentences": len(target_sentences),
            "test_ratio": test_ratio,
            "total_characters": len(corpus_text),
            "unique_characters": len(target_char_info['unique_characters']),
        },
        "perturbation": {
            "num_swaps": num_swaps,
            "char_swaps_performed": len(all_char_perturbations),
            "word_swaps_performed": len(all_word_perturbations),
        },
        "baseline_metrics": baseline_metrics,
        "character_perturbations": all_char_perturbations,
        "word_perturbations": all_word_perturbations,
        "metric_deltas_averaged": averaged_deltas,
        "timestamp": datetime.now().isoformat(),
    }
    
    return results


def format_results_summary(results):
    """Format test results into a human-readable summary."""
    if not results:
        return "No results to report."
    
    lines = []
    lines.append(f"{'='*80}")
    lines.append(f"Test Results: {results['language'].upper()}/{results['dialect']}")
    lines.append(f"{'='*80}")
    lines.append(f"\nCorpus Statistics:")
    lines.append(f"  Total sentences: {results['corpus_stats']['total_sentences']}")
    lines.append(f"  Reference sentences: {results['corpus_stats']['reference_sentences']}")
    lines.append(f"  Target sentences: {results['corpus_stats']['target_sentences']}")
    lines.append(f"  Total characters: {results['corpus_stats']['total_characters']}")
    lines.append(f"  Unique characters: {results['corpus_stats']['unique_characters']}")
    lines.append(f"\nPerturbation:")
    lines.append(f"  Character swaps performed: {results['perturbation'].get('char_swaps_performed', results['perturbation'].get('num_swaps_performed', 'N/A'))}")
    lines.append(f"  Word swaps performed: {results['perturbation'].get('word_swaps_performed', results['perturbation'].get('num_swaps_performed', 'N/A'))}")
    lines.append(f"\nMetric Changes (Averaged Cosine Similarity & KL Divergence):")
    lines.append(f"  Character Level (from character swaps):")
    
    for gram_length in sorted(results['metric_deltas_averaged']['character'].keys()):
        deltas = results['metric_deltas_averaged']['character'][gram_length]
        lines.append(f"    {gram_length}-gram:")
        lines.append(f"      D Cosine Similarity: {deltas['cosine_similarity']:.6f}")
        lines.append(f"      D KL Divergence: {deltas['kl_divergence']:.6f}")
    
    lines.append(f"\n  Word Level (from word swaps):")
    for gram_length in sorted(results['metric_deltas_averaged']['word'].keys()):
        deltas = results['metric_deltas_averaged']['word'][gram_length]
        lines.append(f"    {gram_length}-gram:")
        lines.append(f"      D Cosine Similarity: {deltas['cosine_similarity']:.6f}")
        lines.append(f"      D KL Divergence: {deltas['kl_divergence']:.6f}")
    
    return "\n".join(lines)


def compute_statistical_thresholds(all_results, epsilon=1e-3):
    """
    Compute per-language thresholds based on mean ± epsilon and standard deviation.
    Computes separate thresholds for each window size:
    - Character: 1-gram, 2-gram, 3-gram
    - Word: 1-gram, 2-gram
    
    Also extracts baseline KL divergence profiles (unperturbed reference metrics).
    
    Args:
        all_results: List of test results
        epsilon: Epsilon value for threshold calculation (default 1e-3)
    
    Returns dict with per-language thresholds per window size, baseline profiles, and global statistics.
    Each language has separate thresholds for:
    - character_kl_1gram, character_kl_2gram, character_kl_3gram
    - word_kl_1gram, word_kl_2gram
    And baseline metrics for reference comparison.
    """
    if not all_results:
        return None
    
    # Group results by language and window size
    lang_metrics = {}
    lang_baselines = {}
    
    for result in all_results:
        lang_code = result['language']
        if lang_code not in lang_metrics:
            lang_metrics[lang_code] = {
                'character_kl_1gram': [],
                'character_kl_2gram': [],
                'character_kl_3gram': [],
                'word_kl_1gram': [],
                'word_kl_2gram': [],
            }
            lang_baselines[lang_code] = {
                'character': {1: [], 2: [], 3: []},
                'word': {1: [], 2: []},
            }
        
        # Use averaged deltas from multiple swaps (KL divergence only)
        # Keep separate by window size
        if 'metric_deltas_averaged' in result:
            deltas = result['metric_deltas_averaged']
            
            # Character: 1-gram, 2-gram, 3-gram
            for gram_length in [1, 2, 3]:
                if gram_length in deltas.get('character', {}):
                    char_kl = deltas['character'][gram_length].get('kl_divergence', 0)
                    key = f'character_kl_{gram_length}gram'
                    lang_metrics[lang_code][key].append(char_kl)
            
            # Word: 1-gram, 2-gram
            for gram_length in [1, 2]:
                if gram_length in deltas.get('word', {}):
                    word_kl = deltas['word'][gram_length].get('kl_divergence', 0)
                    key = f'word_kl_{gram_length}gram'
                    lang_metrics[lang_code][key].append(word_kl)
        
        # Extract baseline metrics (unperturbed reference)
        if 'baseline_metrics' in result:
            baseline = result['baseline_metrics']
            # Extract character baseline KL values
            for gram_length in [1, 2, 3]:
                if gram_length in baseline.get('character', {}):
                    char_baseline_kl = baseline['character'][gram_length].get('kl_divergence', 0)
                    lang_baselines[lang_code]['character'][gram_length].append(char_baseline_kl)
            
            # Extract word baseline KL values
            for gram_length in [1, 2]:
                if gram_length in baseline.get('word', {}):
                    word_baseline_kl = baseline['word'][gram_length].get('kl_divergence', 0)
                    lang_baselines[lang_code]['word'][gram_length].append(word_baseline_kl)
    
    # Compute per-language thresholds
    eps_minimum = 1e-3  # Minimum threshold (KL divergence minimum)
    per_language_thresholds = {}
    per_language_baselines = {}
    global_metrics = {
        'character_kl_1gram': [],
        'character_kl_2gram': [],
        'character_kl_3gram': [],
        'word_kl_1gram': [],
        'word_kl_2gram': [],
    }
    
    for lang_code, metrics in lang_metrics.items():
        per_language_thresholds[lang_code] = {}
        per_language_baselines[lang_code] = {}
        
        for metric_name, values in metrics.items():
            if not values:
                # Skip if no values
                continue
            
            mean = np.mean(values)
            std = np.std(values)
            
            # Thresholds: mean ± epsilon (for per-language)
            # Enforce minimum threshold to prevent negative values
            lower_threshold = max(eps_minimum, mean - epsilon)
            upper_threshold = mean + epsilon
            
            per_language_thresholds[lang_code][metric_name] = {
                'mean': float(mean),
                'std': float(std),
                'epsilon': float(epsilon),
                'lower_threshold': float(lower_threshold),  # Healthy (enforced >= eps_minimum)
                'upper_threshold': float(upper_threshold),  # Anomalous
                'n_samples': len(values),  # Number of samples used
            }
            
            # Aggregate for global stats
            global_metrics[metric_name].extend(values)
    
    # Compute per-language baseline metrics
    for lang_code, baselines in lang_baselines.items():
        per_language_baselines[lang_code] = {}
        
        # Character baselines
        for gram_length in [1, 2, 3]:
            if baselines['character'][gram_length]:
                values = baselines['character'][gram_length]
                mean_baseline = np.mean(values)
                per_language_baselines[lang_code][f'character_{gram_length}gram_baseline_kl'] = float(mean_baseline)
        
        # Word baselines
        for gram_length in [1, 2]:
            if baselines['word'][gram_length]:
                values = baselines['word'][gram_length]
                mean_baseline = np.mean(values)
                per_language_baselines[lang_code][f'word_{gram_length}gram_baseline_kl'] = float(mean_baseline)
    
    # Compute global thresholds (mean ± 1*std across all languages)
    global_thresholds = {}
    for metric_name, values in global_metrics.items():
        if not values:
            continue
        
        mean = np.mean(values)
        std = np.std(values)
        global_thresholds[metric_name] = {
            'mean': float(mean),
            'std': float(std),
            'healthy': float(max(eps_minimum, mean - std)),  # Enforce minimum >= eps_minimum
            'anomalous': float(mean + std),
            'n_samples': len(values),  # Total samples across all languages
        }
    
    return {
        'epsilon': epsilon,
        'per_language': per_language_thresholds,
        'per_language_baselines': per_language_baselines,
        'global': global_thresholds,
        'metrics_included': ['character_kl_1gram', 'character_kl_2gram', 'character_kl_3gram', 'word_kl_1gram', 'word_kl_2gram'],
    }


def evaluate_prediction_efficacy(all_results, validation_results):
    """
    Evaluate how well character and word statistics predict corpus quality.
    
    Returns dict with efficacy metrics showing:
    - Correlation between char/word deltas
    - Consistency across gram levels
    - Predictive power of each metric
    """
    efficacy = {
        'metric_correlations': {},
        'consistency_metrics': {},
        'predictive_power': {},
    }
    
    if not all_results:
        return efficacy
    
    # Extract deltas for correlation analysis (use averaged deltas)
    char_cosine_deltas = []
    char_kl_deltas = []
    word_cosine_deltas = []
    word_kl_deltas = []
    
    for result in all_results:
        char_1gram = result['metric_deltas_averaged']['character'][1]
        word_1gram = result['metric_deltas_averaged']['word'][1]
        
        char_cosine_deltas.append(char_1gram['cosine_similarity'])
        char_kl_deltas.append(char_1gram['kl_divergence'])
        word_cosine_deltas.append(word_1gram['cosine_similarity'])
        word_kl_deltas.append(word_1gram['kl_divergence'])
    
    # Correlation between character and word deltas
    if char_cosine_deltas and word_cosine_deltas:
        corr_cosine = np.corrcoef(char_cosine_deltas, word_cosine_deltas)[0, 1]
        corr_kl = np.corrcoef(char_kl_deltas, word_kl_deltas)[0, 1]
        
        efficacy['metric_correlations']['char_word_cosine'] = float(np.nan_to_num(corr_cosine))
        efficacy['metric_correlations']['char_word_kl'] = float(np.nan_to_num(corr_kl))
    
    # Consistency: check if different gram lengths agree
    for result in all_results:
        # Character level consistency
        char_1gram_cs = result['metric_deltas_averaged']['character'][1]['cosine_similarity']
        char_2gram_cs = result['metric_deltas_averaged']['character'][2]['cosine_similarity']
        char_3gram_cs = result['metric_deltas_averaged']['character'][3]['cosine_similarity']
        
        char_consistency = 1.0 - np.std([char_1gram_cs, char_2gram_cs, char_3gram_cs]) / np.mean([char_1gram_cs, char_2gram_cs, char_3gram_cs])
        
        # Word level consistency
        word_1gram_cs = result['metric_deltas_averaged']['word'][1]['cosine_similarity']
        word_2gram_cs = result['metric_deltas_averaged']['word'][2]['cosine_similarity']
        word_3gram_cs = result['metric_deltas_averaged']['word'][3]['cosine_similarity']
        
        word_consistency = 1.0 - np.std([word_1gram_cs, word_2gram_cs, word_3gram_cs]) / (np.mean([word_1gram_cs, word_2gram_cs, word_3gram_cs]) + 1e-6)
    
    # Predictive power: how well do metrics align with validation status
    passed_char_deltas = []
    warned_char_deltas = []
    failed_char_deltas = []
    
    for result, val in zip(all_results, validation_results):
        char_1gram = result['metric_deltas_averaged']['character'][1]['cosine_similarity']
        
        # Find matching validation result
        for check in val.get('validation_checks', []):
            if 'Character 1-gram' in check.get('name', ''):
                if check['status'] == 'PASS':
                    passed_char_deltas.append(char_1gram)
                elif check['status'] == 'WARN':
                    warned_char_deltas.append(char_1gram)
                elif check['status'] == 'FAIL':
                    failed_char_deltas.append(char_1gram)
    
    if passed_char_deltas and failed_char_deltas:
        # Separation between pass and fail
        mean_pass = np.mean(passed_char_deltas) if passed_char_deltas else 0
        mean_fail = np.mean(failed_char_deltas) if failed_char_deltas else 0
        separation = abs(mean_fail - mean_pass) / (np.std(passed_char_deltas + failed_char_deltas) + 1e-6)
        
        efficacy['predictive_power']['class_separation'] = float(separation)
        efficacy['predictive_power']['pass_mean'] = float(mean_pass)
        efficacy['predictive_power']['fail_mean'] = float(mean_fail)
    
    return efficacy


def validate_xml_corpus_integrity(lang_full_name, lang_code, dialect, sources, logger, output_dir, 
                                 thresholds=None, num_swaps=5):
    """
    Validate that XML files in sources pass robustness tests for the correct language.
    Uses per-language thresholds (mean ± epsilon) computed from corpus distribution.
    
    This test ensures:
    1. XML files for the correct language/dialect have deltas within language-specific norms
    2. Validation against dynamic per-language thresholds instead of fixed arbitrary values
    
    Args:
        lang_full_name: Full language name (e.g., 'Amis') for corpus generation
        lang_code: Language code (e.g., 'ami') for tokenization and results
        dialect: Dialect name
        sources: List of source directories
        logger: Logger instance
        output_dir: Output directory for results
        thresholds: Dict with per-language thresholds from compute_statistical_thresholds()
        num_swaps: Number of random character swaps to perform (default 5)
    
    Returns:
        dict with validation results
    """
    validation_results = {
        "language": lang_code,
        "dialect": dialect,
        "validation_checks": [],
        "corpus_integrity_issues": [],
        "thresholds_used": thresholds or {},
    }
    
    # Use provided thresholds or conservative defaults
    if not thresholds:
        thresholds = {
            'per_language': {
                lang_code: {
                    'character_cosine': {'lower_threshold': 0.2, 'upper_threshold': 0.5},
                    'character_kl': {'lower_threshold': 0.5, 'upper_threshold': 2.0},
                }
            }
        }
    
    # Get per-language thresholds or use global defaults
    lang_thresholds = thresholds.get('per_language', {}).get(lang_code, None)
    
    # Test 1: Check that correct language/dialect has reasonable deltas
    logger.info(f"[VALIDATION] Checking XML integrity for {lang_code}/{dialect} (using {num_swaps} swaps per perturbation)...")
    
    try:
        # Pass both full name and code, with num_swaps parameter
        results = test_language_dialect(lang_full_name, lang_code, dialect, sources, output_dir, 
                                       test_ratio=0.2, laplace=True, num_swaps=num_swaps)
        
        if not results:
            validation_results["corpus_integrity_issues"].append(
                f"Could not generate corpus for {lang_code}/{dialect}"
            )
            return validation_results
        
        # Check character-level 1-gram deltas (most important) - use averaged deltas
        char_1gram_deltas = results['metric_deltas_averaged']['character'][1]
        cosine_delta = char_1gram_deltas['cosine_similarity']
        kl_delta = char_1gram_deltas['kl_divergence']
        
        check_name = f"{lang_code}/{dialect} - Character 1-gram Deltas (avg of {num_swaps} swaps)"
        
        # Get thresholds for this language
        if lang_thresholds:
            char_cosine_thresh = lang_thresholds.get('character_cosine', {})
            char_kl_thresh = lang_thresholds.get('character_kl', {})
            
            cosine_lower = char_cosine_thresh.get('lower_threshold', 0.2)
            cosine_upper = char_cosine_thresh.get('upper_threshold', 0.5)
            kl_lower = char_kl_thresh.get('lower_threshold', 0.5)
            kl_upper = char_kl_thresh.get('upper_threshold', 2.0)
        else:
            # Use global thresholds as fallback
            global_cosine = thresholds.get('global', {}).get('character_cosine', {})
            global_kl = thresholds.get('global', {}).get('character_kl', {})
            cosine_lower = global_cosine.get('healthy', 0.2)
            cosine_upper = global_cosine.get('anomalous', 0.5)
            kl_lower = global_kl.get('healthy', 0.5)
            kl_upper = global_kl.get('anomalous', 2.0)
        
        # Determine status based on per-language epsilon-based thresholds
        if cosine_delta < cosine_lower and kl_delta < kl_lower:
            status = "PASS"
            message = f"Below lower threshold (cosine={cosine_delta:.4f} < {cosine_lower:.4f}, kl={kl_delta:.4f} < {kl_lower:.4f})"
        elif cosine_delta < cosine_upper and kl_delta < kl_upper:
            status = "WARN"
            message = f"Within epsilon bounds (cosine={cosine_delta:.4f}, kl={kl_delta:.4f})"
        else:
            status = "FAIL"
            message = f"Beyond upper threshold (cosine={cosine_delta:.4f} > {cosine_upper:.4f}, kl={kl_delta:.4f} > {kl_upper:.4f})"
        
        validation_results["validation_checks"].append({
            "name": check_name,
            "status": status,
            "message": message,
            "deltas": {
                "cosine_similarity": float(cosine_delta),
                "kl_divergence": float(kl_delta)
            },
            "thresholds": {
                "cosine_lower": float(cosine_lower),
                "cosine_upper": float(cosine_upper),
                "kl_lower": float(kl_lower),
                "kl_upper": float(kl_upper),
            }
        })
        
        log_symbol = "[OK]" if status == "PASS" else "[!]" if status == "WARN" else "[X]"
        logger.info(f"  {log_symbol} {check_name}: {status}")
        
        if status == "FAIL":
            validation_results["corpus_integrity_issues"].append(
                f"{lang_code}/{dialect}: {message}"
            )
        
        # Additional metrics for efficacy evaluation
        word_1gram = results['metric_deltas_averaged']['word'][1]
        validation_results["additional_metrics"] = {
            "word_cosine_delta": float(word_1gram['cosine_similarity']),
            "word_kl_delta": float(word_1gram['kl_divergence']),
            "num_swaps_used": num_swaps,
            "char_word_correlation_potential": True,  # Flag for later analysis
        }
        
    except Exception as e:
        logger.error(f"[VALIDATION] Error during XML corpus integrity check: {e}")
        validation_results["corpus_integrity_issues"].append(str(e))
    
    return validation_results


def validate_cross_language_discrimination(target_lang_full_name, target_lang_code, target_dialect, 
                                           other_languages, lang_code_map, sources, logger, 
                                           output_dir, thresholds=None, num_swaps=5):
    """
    Validate that non-target languages show anomalously high deltas (above thresholds).
    
    This test ensures the thresholds can discriminate the target language from others.
    We apply perturbation logic to each non-target language corpus and verify that
    the resulting metric deltas exceed the upper threshold (indicating wrong language).
    
    Args:
        target_lang_full_name: Target language full name (e.g., 'Amis')
        target_lang_code: Target language code (e.g., 'ami')
        target_dialect: Target dialect
        other_languages: List of non-target language full names
        lang_code_map: Map from full name to language code
        sources: List of source directories
        logger: Logger instance
        output_dir: Output directory
        thresholds: Dict with per-language thresholds
        num_swaps: Number of random character swaps to perform (default 5)
    
    Returns:
        dict with cross-language validation results
    """
    cross_lang_results = {
        "target_language": target_lang_code,
        "target_dialect": target_dialect,
        "discrimination_checks": [],
        "discrimination_issues": [],
    }
    
    if not thresholds:
        thresholds = {
            'character_cosine': {'anomalous': 0.7},
            'character_kl': {'anomalous': 3.0},
        }
    
    logger.info(f"[CROSS-LANG] Testing discrimination for {target_lang_code}/{target_dialect} against other languages...")
    
    # Extract anomalous thresholds
    char_cosine_thresh = thresholds.get('character_cosine', {})
    char_kl_thresh = thresholds.get('character_kl', {})
    cosine_anomalous = char_cosine_thresh.get('anomalous', 0.7)
    kl_anomalous = char_kl_thresh.get('anomalous', 3.0)
    
    # Test each non-target language
    for other_lang_full_name in other_languages:
        other_lang_code = lang_code_map.get(other_lang_full_name)
        if not other_lang_code or other_lang_full_name == target_lang_full_name:
            continue
        
        try:
            # Generate corpus for non-target language
            other_corpus_text = ""
            for source in sources:
                corpus_path = f"Corpora/{source}"
                if os.path.exists(corpus_path):
                    try:
                        corpus = generate_corpus(other_lang_full_name, corpus_path, "standard", 
                                               by_dialect=True, phonetic=False)
                        # Use first available dialect for this language
                        for dialect in corpus.keys():
                            other_corpus_text += corpus[dialect]
                            break
                    except Exception as e:
                        logger.debug(f"Could not generate {other_lang_full_name} from {source}: {e}")
            
            if not other_corpus_text:
                logger.debug(f"No corpus found for {other_lang_code} - skipping discrimination test")
                continue
            
            other_corpus_text = remove_chinese_characters(other_corpus_text)
            
            # Split into reference and target for this non-target language
            sentences = re.split(r'(?<=[.!?])\s+', other_corpus_text)
            if len(sentences) < 2:
                continue
            
            random.seed(0)  # Deterministic splitting
            num_target = max(1, int(len(sentences) * 0.2))
            target_indices = set(random.sample(range(len(sentences)), num_target))
            
            ref_sentences = [s for i, s in enumerate(sentences) if i not in target_indices]
            target_sentences = [s for i, s in enumerate(sentences) if i in target_indices]
            
            ref_text = "".join(ref_sentences)
            target_text = "".join(target_sentences)
            
            # Extract character frequencies and apply perturbation to non-target language
            other_char_info = extract_orthographic_info(target_text)
            if not other_char_info['character_frequency']:
                continue
            
            available_chars = (set(other_char_info['unique_characters'])).difference(string.punctuation)
            
            if not available_chars:
                continue
            
            random_char = random.choice(list(available_chars))
            
            # Apply multiple perturbations to non-target language corpus
            all_perturbation_deltas = []
            for _ in range(num_swaps):
                other_random_char = random.choice(list(available_chars - {random_char}))
                swapped_text = target_text.translate(str.maketrans(other_random_char, random_char))
                
                # Measure baseline and perturbed metrics for non-target language
                baseline_metrics = analyze_corpus_partition(ref_text, target_text, other_lang_code)
                perturbed_metrics = analyze_corpus_partition(ref_text, swapped_text, other_lang_code)
                
                deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
                all_perturbation_deltas.append(deltas)
            
            # Average the deltas across all swaps
            averaged_deltas = {"character": {}, "word": {}}
            for level in ["character", "word"]:
                for gram_length in all_perturbation_deltas[0][level].keys():
                    averaged_deltas[level][gram_length] = {}
                    for metric in ["cosine_similarity", "kl_divergence"]:
                        values = [delta[level][gram_length][metric] for delta in all_perturbation_deltas]
                        averaged_deltas[level][gram_length][metric] = float(np.mean(values))
            
            char_1gram = averaged_deltas['character'][1]
            cosine_delta = char_1gram['cosine_similarity']
            kl_delta = char_1gram['kl_divergence']
            
            # Check thresholds - non-target languages SHOULD exceed upper threshold
            # Expected: FAIL for target language metrics = PASS for discrimination (correctly identified as different)
            if cosine_delta > cosine_upper or kl_delta > kl_upper:
                status = "PASS"  # Correctly identified as different language (metrics exceed thresholds)
                message = f"Correctly identified as non-target (cosine={cosine_delta:.4f} > {cosine_upper:.4f}, kl={kl_delta:.4f} > {kl_upper:.4f})"
            else:
                status = "FAIL"  # Failed to discriminate (metrics within target thresholds)
                message = f"Failed to discriminate (cosine={cosine_delta:.4f} <= {cosine_upper:.4f}, kl={kl_delta:.4f} <= {kl_upper:.4f})"
            
            check_name = f"{target_lang_code}/{target_dialect} vs {other_lang_code} (discrimination test)"
            cross_lang_results["discrimination_checks"].append({
                "name": check_name,
                "status": status,
                "message": message,
                "target_language": target_lang_code,
                "test_language": other_lang_code,
                "deltas": {
                    "cosine_similarity": float(cosine_delta),
                    "kl_divergence": float(kl_delta)
                }
            })
            
            log_symbol = "[OK]" if status == "PASS" else "[X]"
            logger.info(f"  {log_symbol} {check_name}: {status}")
            
            if status == "FAIL":
                cross_lang_results["discrimination_issues"].append(
                    f"Discrimination failed: {target_lang_code} vs {other_lang_code}: {message}"
                )
        
        except Exception as e:
            logger.debug(f"[CROSS-LANG] Error testing {other_lang_code} discrimination: {e}")
    
    return cross_lang_results


def main(args):
    """Main test suite execution."""
    output_dir = args.output_dir or "test_results/perturbation_tests"
    os.makedirs(output_dir, exist_ok=True)
    
    logger = setup_logging(output_dir)
    logger.info("Starting Character Perturbation Robustness Test Suite")
    
    # Check if we should load pre-computed thresholds
    skip_tests = False
    thresholds = None
    if args.load_thresholds:
        logger.info(f"Loading pre-computed thresholds from {args.load_thresholds}")
        try:
            with open(args.load_thresholds, 'r', encoding='utf-8') as f:
                thresholds = json.load(f)
            logger.info("Thresholds loaded successfully. Skipping test recomputation.")
            skip_tests = True
        except Exception as e:
            logger.error(f"Failed to load thresholds: {e}. Will recompute.")
            skip_tests = False
    
    # Determine languages to test
    if args.languages:
        lang_inputs = args.languages
    else:
        lang_inputs = ["ami", "tay", "bnn", "pwn", "pyu", "dru", "trv"]
    
    # Resolve language codes to full names and build mapping
    languages = []  # Full names
    lang_code_map = {}  # Map full name -> code
    
    for lang_input in lang_inputs:
        full_name, code = resolve_language_name(lang_input)
        if full_name and code:
            languages.append(full_name)
            lang_code_map[full_name] = code
        else:
            logger.warning(f"Could not resolve language '{lang_input}' - skipping")
    
    if not languages:
        logger.error("No valid languages found after resolution. Exiting.")
        return
    
    # Determine sources to test
    if args.sources:
        sources = [s if s.endswith('/') else s + '/' for s in args.sources]
    else:
        sources = ["ePark/", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"]
    
    logger.info(f"Testing languages: {languages}")
    logger.info(f"Testing sources: {sources}")
    logger.info(f"Number of swaps per test: {args.num_swaps}")
    logger.info(f"Epsilon for per-language thresholds: {args.epsilon}")
    
    all_results = []
    validation_results = []
    efficacy = {}
    # Note: thresholds may already be loaded if --load-thresholds was provided above
    summary_stats = {
        "total_tests": 0,
        "successful_tests": 0,
        "failed_tests": 0,
        "test_results": [],
        "validation_checks_passed": 0,
        "validation_checks_warned": 0,
        "validation_checks_failed": 0,
    }
    
    # Run tests with multiple swaps (skip if thresholds were loaded)
    num_swaps = args.num_swaps  # Get from command line arguments
    epsilon = args.epsilon  # Get from command line arguments
    
    if skip_tests:
        logger.info(f"\n{'='*80}")
        logger.info("Skipping test suite execution (using pre-loaded thresholds)")
        logger.info(f"{'='*80}\n")
    else:
        logger.info(f"\n{'='*80}")
        logger.info(f"Running robustness tests with {num_swaps} swaps per dialect")
        logger.info(f"{'='*80}\n")
    
    for lang_full_name in languages:
        lang_code = lang_code_map[lang_full_name]
        dialects = get_available_dialects(lang_full_name)
        if not dialects:
            logger.warning(f"No dialects found for language {lang_full_name}")
            continue
        
        if skip_tests:
            # Skip testing phase, continue to validation
            continue
        
        for dialect in dialects:
            logger.info(f"\nTesting {lang_code}/{dialect} with {num_swaps} random character swaps...")
            summary_stats["total_tests"] += 1
            
            try:
                # Pass language full name to test function (for corpus generation)
                # but it will use lang_code internally for tokenization
                results = test_language_dialect(lang_full_name, lang_code, dialect, sources, output_dir, 
                                               num_swaps=num_swaps)
                if results:
                    # Store full language name in results for reference
                    results['language_full_name'] = lang_full_name
                    all_results.append(results)
                    summary_stats["successful_tests"] += 1
                    logger.info(format_results_summary(results))
                    
                    # Save individual result
                    result_file = os.path.join(output_dir, f"{lang_code}_{dialect}_results.json")
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(results, f, indent=2, ensure_ascii=False)
                else:
                    summary_stats["failed_tests"] += 1
                    logger.warning(f"Failed to test {lang_code}/{dialect}")
            except Exception as e:
                summary_stats["failed_tests"] += 1
                logger.error(f"Error testing {lang_code}/{dialect}: {e}", exc_info=True)
    
    # Run XML corpus integrity validation tests with per-language epsilon-based thresholds
    if not skip_tests:
        logger.info(f"\n{'='*80}")
        logger.info("Computing Per-Language Thresholds (mean ± epsilon) for Validation")
        logger.info(f"{'='*80}\n")
        
        # Compute per-language thresholds from all results (using epsilon from command line args)
        thresholds = compute_statistical_thresholds(all_results, epsilon=epsilon)
    else:
        logger.info(f"\n{'='*80}")
        logger.info("Using pre-loaded thresholds (skipped recomputation)")
        logger.info(f"{'='*80}\n")
    
    if thresholds:
        logger.info(f"Per-Language Thresholds (epsilon={epsilon}):")
        for lang_code, lang_thresh in thresholds.get('per_language', {}).items():
            logger.info(f"  {lang_code}:")
            for metric, thresh in lang_thresh.items():
                logger.info(f"    {metric}:")
                logger.info(f"      Mean: {thresh['mean']:.4f}, Std: {thresh['std']:.4f}")
                logger.info(f"      Lower (healthy): {thresh['lower_threshold']:.4f}, Upper (anomalous): {thresh['upper_threshold']:.4f}")
        
        if thresholds.get('global'):
            logger.info(f"\nGlobal Thresholds (fallback, mean ± 1 std):")
            for metric, thresh in thresholds['global'].items():
                logger.info(f"  {metric}:")
                logger.info(f"    Mean: {thresh['mean']:.4f}, Std: {thresh['std']:.4f}")
                logger.info(f"    Healthy: {thresh['healthy']:.4f}, Anomalous: {thresh['anomalous']:.4f}")
    else:
        logger.warning("Could not compute thresholds from results")
    
    logger.info(f"\n{'='*80}")
    logger.info("Running XML Corpus Integrity Validation Tests")
    logger.info(f"{'='*80}\n")
    
    for lang_full_name in languages:
        lang_code = lang_code_map[lang_full_name]
        dialects = get_available_dialects(lang_full_name)
        if not dialects:
            continue
        
        for dialect in dialects:
            try:
                # Pass language full name to validation function, code for file names, thresholds, and num_swaps
                val_result = validate_xml_corpus_integrity(lang_full_name, lang_code, dialect, sources, logger, output_dir, 
                                                           thresholds=thresholds, num_swaps=num_swaps)
                # Store full language name for reference
                val_result['language_full_name'] = lang_full_name
                validation_results.append(val_result)
                
                # Track validation stats
                for check in val_result.get("validation_checks", []):
                    if check["status"] == "PASS":
                        summary_stats["validation_checks_passed"] += 1
                    elif check["status"] == "WARN":
                        summary_stats["validation_checks_warned"] += 1
                    elif check["status"] == "FAIL":
                        summary_stats["validation_checks_failed"] += 1
                
                # Save individual validation result
                val_file = os.path.join(output_dir, f"{lang_code}_{dialect}_validation.json")
                with open(val_file, 'w', encoding='utf-8') as f:
                    json.dump(val_result, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"Error validating {lang_code}/{dialect}: {e}", exc_info=True)
    
    # Run cross-language discrimination tests
    logger.info(f"\n{'='*80}")
    logger.info("Running Cross-Language Discrimination Tests")
    logger.info(f"{'='*80}\n")
    
    cross_language_results = []
    discrimination_passed = 0
    discrimination_failed = 0
    
    for lang_full_name in languages:
        lang_code = lang_code_map[lang_full_name]
        dialects = get_available_dialects(lang_full_name)
        if not dialects:
            continue
        
        # Test first dialect of each language against all other languages
        dialect = dialects[0]
        try:
            other_langs = [l for l in languages if l != lang_full_name]
            cross_result = validate_cross_language_discrimination(
                lang_full_name, lang_code, dialect, other_langs, lang_code_map, 
                sources, logger, output_dir, thresholds=thresholds, num_swaps=num_swaps
            )
            cross_language_results.append(cross_result)
            
            # Track discrimination stats
            for check in cross_result.get("discrimination_checks", []):
                if check["status"] == "PASS":
                    discrimination_passed += 1
                else:
                    discrimination_failed += 1
            
            # Save cross-language results
            cross_file = os.path.join(output_dir, f"{lang_code}_{dialect}_cross_language.json")
            with open(cross_file, 'w', encoding='utf-8') as f:
                json.dump(cross_result, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"Error in cross-language discrimination for {lang_code}: {e}")
    
    # Compute prediction efficacy metrics
    logger.info(f"\n{'='*80}")
    logger.info("Computing Prediction Efficacy Metrics")
    logger.info(f"{'='*80}\n")
    
    efficacy = evaluate_prediction_efficacy(all_results, validation_results)
    
    if efficacy.get('metric_correlations'):
        logger.info("Metric Correlations (character ↔ word deltas):")
        logger.info(f"  Cosine Similarity Correlation: {efficacy['metric_correlations'].get('char_word_cosine', 0):.4f}")
        logger.info(f"  KL Divergence Correlation: {efficacy['metric_correlations'].get('char_word_kl', 0):.4f}")
    
    if efficacy.get('predictive_power'):
        logger.info("\nPredictive Power Analysis:")
        logger.info(f"  Class Separation (PASS vs FAIL): {efficacy['predictive_power'].get('class_separation', 0):.4f}")
        logger.info(f"  PASS Mean Delta: {efficacy['predictive_power'].get('pass_mean', 0):.4f}")
        logger.info(f"  FAIL Mean Delta: {efficacy['predictive_power'].get('fail_mean', 0):.4f}")
    else:
        logger.info("Could not compute predictive power (insufficient validation variety)")
    
    # Save aggregated results and validation
    aggregated_file = os.path.join(output_dir, "all_results.json")
    with open(aggregated_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    
    validation_file = os.path.join(output_dir, "validation_results.json")
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_results, f, indent=2, ensure_ascii=False)
    
    cross_language_file = os.path.join(output_dir, "cross_language_discrimination.json")
    with open(cross_language_file, 'w', encoding='utf-8') as f:
        json.dump(cross_language_results, f, indent=2, ensure_ascii=False)
    
    # Save thresholds and efficacy metrics
    thresholds_file = os.path.join(output_dir, "statistical_thresholds.json")
    with open(thresholds_file, 'w', encoding='utf-8') as f:
        json.dump(thresholds or {}, f, indent=2, ensure_ascii=False)
    
    efficacy_file = os.path.join(output_dir, "prediction_efficacy.json")
    with open(efficacy_file, 'w', encoding='utf-8') as f:
        json.dump(efficacy or {}, f, indent=2, ensure_ascii=False)
    
    # Generate summary report
    summary_file = os.path.join(output_dir, "summary_report.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Character Perturbation Robustness Test Suite - Summary Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"{'='*80}\n\n")
        
        f.write(f"Robustness Test Statistics:\n")
        f.write(f"  Total tests: {summary_stats['total_tests']}\n")
        f.write(f"  Successful: {summary_stats['successful_tests']}\n")
        f.write(f"  Failed: {summary_stats['failed_tests']}\n\n")
        
        # Report per-language thresholds
        if thresholds:
            f.write(f"{'='*80}\n")
            f.write(f"Per-Language Thresholds (mean ± epsilon, epsilon={thresholds.get('epsilon', 0.1)})):\n")
            f.write(f"{'='*80}\n\n")
            
            for lang_code, lang_thresh in thresholds.get('per_language', {}).items():
                f.write(f"{lang_code}:\n")
                for metric_name, thresh in lang_thresh.items():
                    f.write(f"  {metric_name}:\n")
                    f.write(f"    Mean: {thresh['mean']:.6f}\n")
                    f.write(f"    Std Dev: {thresh['std']:.6f}\n")
                    f.write(f"    Lower (healthy): {thresh['lower_threshold']:.6f}\n")
                    f.write(f"    Upper (anomalous): {thresh['upper_threshold']:.6f}\n")
                f.write(f"\n")
            
            if thresholds.get('global'):
                f.write(f"\nGlobal Thresholds (fallback, mean ± 1 std):\n")
                for metric_name, thresh in thresholds['global'].items():
                    f.write(f"  {metric_name}:\n")
                    f.write(f"    Mean: {thresh['mean']:.6f}\n")
                    f.write(f"    Std Dev: {thresh['std']:.6f}\n")
                    f.write(f"    Healthy: {thresh['healthy']:.6f}\n")
                    f.write(f"    Anomalous: {thresh['anomalous']:.6f}\n")
                f.write(f"\n")
        
        # Report efficacy metrics
        if efficacy:
            f.write(f"{'='*80}\n")
            f.write(f"Prediction Efficacy Metrics:\n")
            f.write(f"{'='*80}\n\n")
            
            if efficacy.get('metric_correlations'):
                f.write(f"Character-Word Correlation (indicates joint predictive power):\n")
                f.write(f"  Cosine Similarity: {efficacy['metric_correlations'].get('char_word_cosine', 0):.4f}\n")
                f.write(f"    (1.0 = perfect correlation, 0.0 = no correlation, -1.0 = inverse)\n")
                f.write(f"  KL Divergence: {efficacy['metric_correlations'].get('char_word_kl', 0):.4f}\n\n")
            
            if efficacy.get('predictive_power'):
                f.write(f"Classification Efficacy (how well metrics predict corpus quality):\n")
                f.write(f"  Class Separation: {efficacy['predictive_power'].get('class_separation', 0):.4f}\n")
                f.write(f"    (how many std devs apart PASS and FAIL clusters are)\n")
                f.write(f"  PASS Mean Delta: {efficacy['predictive_power'].get('pass_mean', 0):.4f}\n")
                f.write(f"  FAIL Mean Delta: {efficacy['predictive_power'].get('fail_mean', 0):.4f}\n\n")
        
        f.write(f"XML Corpus Integrity Validation Statistics:\n")
        f.write(f"  Validation checks passed: {summary_stats['validation_checks_passed']}\n")
        f.write(f"  Validation checks warned: {summary_stats['validation_checks_warned']}\n")
        f.write(f"  Validation checks failed: {summary_stats['validation_checks_failed']}\n\n")
        
        # Write validation results
        if validation_results:
            f.write(f"{'='*80}\n")
            f.write(f"XML Corpus Integrity Validation Results:\n")
            f.write(f"{'='*80}\n\n")
            
            for val_result in validation_results:
                f.write(f"{val_result['language'].upper()}/{val_result['dialect']}:\n")
                
                # Validation checks
                if val_result.get("validation_checks"):
                    for check in val_result["validation_checks"]:
                        status_symbol = "[OK]" if check["status"] == "PASS" else \
                                       "[!]" if check["status"] == "WARN" else "[X]"
                        f.write(f"  {status_symbol} {check['name']}: {check['message']}\n")
                        
                        if 'thresholds' in check:
                            thresh = check['thresholds']
                            f.write(f"      Thresholds: cosine [{thresh.get('cosine_lower', 0):.4f}, {thresh.get('cosine_upper', 0):.4f}], ")
                            f.write(f"kl [{thresh.get('kl_lower', 0):.4f}, {thresh.get('kl_upper', 0):.4f}]\n")
                
                # Additional metrics
                if val_result.get("additional_metrics"):
                    metrics = val_result["additional_metrics"]
                    f.write(f"  Word-level deltas (for efficacy analysis):\n")
                    f.write(f"    Cosine: {metrics.get('word_cosine_delta', 0):.6f}\n")
                    f.write(f"    KL: {metrics.get('word_kl_delta', 0):.6f}\n")
                
                # Integrity issues
                if val_result.get("corpus_integrity_issues"):
                    f.write(f"  Issues:\n")
                    for issue in val_result["corpus_integrity_issues"]:
                        f.write(f"    - {issue}\n")
                
                f.write(f"\n")
        
        # Write cross-language discrimination results
        if cross_language_results:
            f.write(f"{'='*80}\n")
            f.write(f"Cross-Language Discrimination Test Results:\n")
            f.write(f"{'='*80}\n\n")
            
            f.write(f"Discrimination Statistics:\n")
            f.write(f"  Discriminations passed (correctly identified non-target languages): {discrimination_passed}\n")
            f.write(f"  Discriminations failed (incorrectly similar to target language): {discrimination_failed}\n\n")
            
            for cross_result in cross_language_results:
                target_lang = cross_result['target_language']
                target_dialect = cross_result['target_dialect']
                f.write(f"{target_lang.upper()}/{target_dialect}:\n")
                
                if cross_result.get("discrimination_checks"):
                    for check in cross_result["discrimination_checks"]:
                        status_symbol = "[OK]" if check["status"] == "PASS" else "[X]"
                        f.write(f"  {status_symbol} {check['name']}: {check['message']}\n")
                
                # Discrimination issues
                if cross_result.get("discrimination_issues"):
                    f.write(f"  Issues:\n")
                    for issue in cross_result["discrimination_issues"]:
                        f.write(f"    - {issue}\n")
                
                f.write(f"\n")
        
        if all_results:
            f.write(f"{'='*80}\n")
            f.write(f"Detailed Robustness Test Results (sampling):\n")
            f.write(f"{'='*80}\n\n")
            
            for results in all_results[:3]:  # Show first 3 for brevity
                f.write(format_results_summary(results))
                f.write(f"\n\n")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Test suite complete. Results saved to {output_dir}")
    logger.info(f"  Total tests: {summary_stats['total_tests']}")
    logger.info(f"  Successful: {summary_stats['successful_tests']}")
    logger.info(f"  Failed: {summary_stats['failed_tests']}")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Character Perturbation Robustness Test Suite for Formosan Languages"
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        help='Output directory for test results (default: test_results/perturbation_tests)'
    )
    parser.add_argument(
        '--languages',
        type=str,
        nargs='+',
        help='Languages to test (default: ami tay bnn pwn pyu dru trv)'
    )
    parser.add_argument(
        '--sources',
        type=str,
        nargs='+',
        help='Corpus sources to use (default: ePark ILRDF_Dicts Paiwan_Stories NTUFormosanCorpus)'
    )
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.2,
        help='Fraction of corpus to use as target corpus (default: 0.2 = 1/5)'
    )
    parser.add_argument(
        '--num-swaps',
        type=int,
        default=5,
        help='Number of unique random character swaps to perform per test (default: 5)'
    )
    parser.add_argument(
        '--epsilon',
        type=float,
        default=0.1,
        help='Epsilon value for per-language threshold calculation (default: 0.1)'
    )
    parser.add_argument(
        '--load-thresholds',
        type=str,
        help='Path to pre-computed thresholds JSON file. If provided, skip recomputation and use these thresholds for validation.'
    )
    
    args = parser.parse_args()
    main(args)
