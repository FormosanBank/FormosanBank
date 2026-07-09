import argparse
from xml.etree import ElementTree as ET
from orthography_compare import normalize_vector, kl_divergence, overlap_coefficient
from orthography_extract import is_lang, is_dialect, generate_corpus, remove_chinese_characters, parse_bool
from bag_of_sentence_analysis import word_tokenize, char_tokenize
from collections import Counter
import numpy as np
import pandas as pd
import re
import csv
from pathlib import Path
from sklearn.metrics import confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

CORPORA_PATH = "Corpora/"
REF_SUBDIRS = ["ePark", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"]
REF_PATHS = [CORPORA_PATH + subdir for subdir in REF_SUBDIRS]

SEED = 0
np.random.seed(SEED)

LAPLACE = True
N = 2
VERBOSE = True
LIMIT = 100

# Caches for dialect detection (weights, models, reference corpora)
_DIALECT_WEIGHTS_CACHE = {}
_DIALECT_MODELS_CACHE = {}  # {(ref_lang, dialect, mode): (models, tokens)}
_DIALECT_CORPUS_CACHE = {}  # {(ref_lang, dialect): corpus_text}

def get_dialects(lang):
    """Get all dialects for a given language from dialects.csv."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        dialects = dialect_csv[dialect_csv['Language'] == lang]['Official'].unique().tolist()
        return dialects
    except Exception as e:
        print(f"Warning: Could not read dialects.csv: {e}")
        return []


def load_target_corpus_from_file(tar_path, phonetic=False):
    """Load text from XML file."""
    if tar_path.lower().endswith('.xml'):
        tree = ET.parse(tar_path)
        root = tree.getroot()
        text = []
        for sentence in root.findall('.//S'):
            if not phonetic:
                form = sentence.find("FORM[@kindOf='standard']")
                if form is not None and form.text:
                    text.append(form.text)
            else:
                form = sentence.find("PHON[@kindOf='standard']")
                if form is not None and form.text:
                    text.append(form.text)
        return " ".join(text)

    with open(tar_path, 'r', encoding='utf-8') as file_handle:
        return file_handle.read()


def obtain_stats(ref_corpus, target_corpus, ref_lang, n=N, laplace=LAPLACE, verbose=VERBOSE):
    """Calculate similarity metrics between reference and target corpora."""
    def calc_n_gram_prob(counters, n_gram):
        if n != 1:
            return (counters[n - 1][n_gram] + laplace) / (counters[n - 2][n_gram[:n - 1]] + (laplace * len(counters[n - 1])))
        else:
            return (counters[0][n_gram] + laplace) / (counters[0].total() + laplace * len(counters[0]))

    def get_n_grams(tokens):
        counters = []
        for gram_length in range(1, n + 1):
            n_grams = [tuple(tokens[i:i + gram_length]) for i in range(len(tokens) - gram_length + 1)]
            counters.append(Counter(n_grams))
        return counters

    def obtain_n_gram_stats(ref_corpus, target_corpus, mode="word"):
        ref_tokens = word_tokenize(ref_corpus, ref_lang) if mode == "word" else char_tokenize(ref_corpus)
        target_tokens = word_tokenize(target_corpus, ref_lang) if mode == "word" else char_tokenize(target_corpus)

        ref_n_gram_counts = get_n_grams(ref_tokens)
        target_n_gram_counts = get_n_grams(target_tokens)

        ref_n_grams = ref_n_gram_counts[n - 1]
        target_n_grams = target_n_gram_counts[n - 1]

        unique_ref_n_grams = set(ref_n_grams)
        unique_target_n_grams = set(target_n_grams)

        all_unique_n_grams = unique_ref_n_grams.union(unique_target_n_grams)

        ref_freq_vector = np.array([(ref_n_grams[n_gram] + laplace) for n_gram in all_unique_n_grams])
        ref_freq_vector = normalize_vector(ref_freq_vector)

        target_freq_vector = np.array([(target_n_grams[n_gram] + laplace) for n_gram in all_unique_n_grams])
        target_freq_vector = normalize_vector(target_freq_vector)

        ov_coeff = overlap_coefficient(unique_ref_n_grams, unique_target_n_grams)
        kl_div = kl_divergence(ref_freq_vector, target_freq_vector)

        ratio = kl_div / ov_coeff if ov_coeff > 0 else float('inf')

        return ov_coeff, kl_div, ratio

    word_stats = obtain_n_gram_stats(ref_corpus, target_corpus, mode="word")
    char_stats = obtain_n_gram_stats(ref_corpus, target_corpus, mode="char")

    return word_stats, char_stats


def build_ngram_models(corpus, ref_lang, n=N, laplace=LAPLACE, mode="word"):
    """
    Build n-gram probability models for sizes 1 to n.
    
    Args:
        corpus: input text
        ref_lang: language for tokenization
        n: maximum n-gram size
        laplace: Laplace smoothing constant
        mode: "word" for word-level n-grams, otherwise will use character-level n-grams
    
    Returns:
        dict: {gram_size: Counter of n-grams}
    """
    if mode == "word":
        tokens = word_tokenize(corpus, ref_lang)
    else:
        tokens = char_tokenize(corpus)
    
    models = {}
    for gram_size in range(1, n + 1):
        n_grams = [tuple(tokens[i:i + gram_size]) for i in range(len(tokens) - gram_size + 1)]
        models[gram_size] = Counter(n_grams)
    
    return models, tokens


def compute_ngram_probability(models, tokens, gram_size, laplace=LAPLACE):
    """
    Compute probability of token sequence using n-gram model of specified size.
    
    Args:
        models: dict of {gram_size: Counter}
        tokens: sequence of tokens
        gram_size: size of n-grams to use
        laplace: Laplace smoothing constant
    
    Returns:
        float: log probability
    """
    if gram_size < 1 or gram_size > len(models):
        return 0.0
    
    model = models[gram_size]
    log_prob = 0.0
    
    for i in range(len(tokens) - gram_size + 1):
        n_gram = tuple(tokens[i:i + gram_size])
        
        if gram_size == 1:
            # Unigram probability
            total = sum(model.values()) + laplace * len(model)
            prob = (model[n_gram] + laplace) / total
        else:
            # Higher-order n-gram with backoff
            prefix = n_gram[:gram_size - 1]
            prefix_count = sum(count for ngram, count in model.items() if ngram[:gram_size - 1] == prefix)
            if prefix_count == 0:
                # Backoff to lower-order
                prob = 1.0 / (len(model) + laplace)
            else:
                prob = (model[n_gram] + laplace) / (prefix_count + laplace * len(model))
        
        if prob > 0:
            log_prob += np.log(prob)
        else:
            log_prob += np.log(laplace / (sum(model.values()) + laplace * len(model)))
    
    return log_prob


def deleted_interpolation(models, tokens, n=N, laplace=LAPLACE, holdout_size=None):
    """
    Calculate optimal weights for combining n-gram models using deleted interpolation.
    
    Args:
        models: dict of {gram_size: Counter}
        tokens: test sequence tokens
        n: maximum n-gram size
        laplace: Laplace smoothing constant
        holdout_size: number of held-out events (if None, use leave-one-out)
    
    Returns:
        dict: {gram_size: weight} for optimal combination
    """
    if holdout_size is None:
        holdout_size = min(100, len(tokens) // 4)  # Hold out up to 25% or 100 tokens
    
    weights_by_gramsize = {i: [] for i in range(1, n + 1)}
    
    # For each held-out segment
    for holdout_idx in range(min(10, len(tokens) - n)):  # Use up to 10 held-out positions
        start_idx = holdout_idx * (len(tokens) // 10) if len(tokens) > 10 else holdout_idx
        if start_idx + n > len(tokens):
            continue
        
        held_out = tuple(tokens[start_idx:start_idx + n])
        
        # Compute probabilities for each gram size
        probs = {}
        for gram_size in range(1, n + 1):
            model = models.get(gram_size, Counter())
            
            if gram_size == 1:
                total = sum(model.values()) + laplace * len(model)
                probs[gram_size] = (model[held_out[-1:]] + laplace) / total if total > 0 else 1.0 / (len(model) + laplace)
            else:
                prefix = held_out[:gram_size - 1]
                prefix_count = sum(count for ngram, count in model.items() if ngram[:gram_size - 1] == prefix)
                if prefix_count == 0:
                    probs[gram_size] = laplace / (sum(model.values()) + laplace * len(model))
                else:
                    probs[gram_size] = (model[held_out] + laplace) / (prefix_count + laplace * len(model))
            
            weights_by_gramsize[gram_size].append(np.log(max(probs[gram_size], 1e-10)))
    
    # Average weights (in log space) and convert back
    final_weights = {}
    total_weight = 0
    for gram_size in range(1, n + 1):
        if weights_by_gramsize[gram_size]:
            avg_log_weight = np.mean(weights_by_gramsize[gram_size])
            weight = np.exp(avg_log_weight)
        else:
            weight = 1.0 / n
        final_weights[gram_size] = weight
        total_weight += weight
    
    # Normalize weights
    for gram_size in final_weights:
        if total_weight > 0:
            final_weights[gram_size] /= total_weight
    
    return final_weights


def get_or_cache_dialect_corpus(ref_lang, dialect, verbose=VERBOSE):
    """
    Load and cache reference corpus for a dialect.
    
    Args:
        ref_lang: language name
        dialect: dialect name
        verbose: verbose output
    
    Returns:
        str: corpus text (empty string if not found)
    """
    cache_key = (ref_lang, dialect)
    
    # Return cached corpus if available
    if cache_key in _DIALECT_CORPUS_CACHE:
        return _DIALECT_CORPUS_CACHE[cache_key]
    
    # Load reference corpus for this dialect
    dialect_corpus = ""
    for ref_path in REF_PATHS:
        corpus = generate_corpus(ref_lang, ref_path, "standard", by_dialect=True, phonetic=False)
        if dialect in corpus.keys():
            dialect_corpus += corpus[dialect]
    
    dialect_corpus = remove_chinese_characters(dialect_corpus)
    
    # Cache the corpus
    _DIALECT_CORPUS_CACHE[cache_key] = dialect_corpus
    
    return dialect_corpus


def get_or_cache_dialect_models(ref_lang, dialect, mode="word", n=N, laplace=LAPLACE, verbose=VERBOSE):
    """
    Build and cache n-gram models for a dialect.
    
    Args:
        ref_lang: language name
        dialect: dialect name
        mode: "word" or "char"
        n: maximum n-gram size
        laplace: Laplace smoothing constant
        verbose: verbose output
    
    Returns:
        tuple: (models dict, tokens list)
    """
    cache_key = (ref_lang, dialect, mode)
    
    # Return cached models if available
    if cache_key in _DIALECT_MODELS_CACHE:
        return _DIALECT_MODELS_CACHE[cache_key]
    
    # Get dialect corpus (will be cached)
    dialect_corpus = get_or_cache_dialect_corpus(ref_lang, dialect, verbose=verbose)
    
    if not dialect_corpus.strip():
        return {}, []
    
    # Build models from reference corpus
    models, tokens = build_ngram_models(dialect_corpus, ref_lang, n=n, laplace=laplace, mode=mode)
    
    # Cache the models
    _DIALECT_MODELS_CACHE[cache_key] = (models, tokens)
    
    return models, tokens


def compute_and_cache_dialect_weights(ref_lang, dialect, mode="word", n=N, laplace=LAPLACE, verbose=VERBOSE):
    """
    Compute and cache interpolation weights for a dialect using deleted interpolation
    on the reference corpus itself.
    
    Args:
        ref_lang: language name
        dialect: dialect name
        mode: "word" or "char"
        n: maximum n-gram size
        laplace: Laplace smoothing constant
        verbose: verbose output
    
    Returns:
        dict: {gram_size: weight}
    """
    cache_key = (ref_lang, dialect, mode)
    
    # Return cached weights if available
    if cache_key in _DIALECT_WEIGHTS_CACHE:
        return _DIALECT_WEIGHTS_CACHE[cache_key]
    
    # Get models (will be cached)
    models, tokens = get_or_cache_dialect_models(ref_lang, dialect, mode=mode, n=n, laplace=laplace, verbose=verbose)
    
    if not tokens:
        return {1: 1.0}  # Default to unigram if no tokens
    
    # Compute weights using deleted interpolation on the reference corpus itself
    weights = deleted_interpolation(models, tokens, n=n, laplace=laplace)
    
    # Cache the weights
    _DIALECT_WEIGHTS_CACHE[cache_key] = weights

    if verbose:
        print(f"    Cached weights for {dialect} ({mode}): {weights}")
    
    return weights


def pred_inter(target_file_path, ref_lang, n=N, laplace=LAPLACE, verbose=VERBOSE):
    """
    Predict dialect using deleted interpolation of weighted n-gram models.
    
    Uses both character-level and word-level n-grams (sizes 1 to n) with weights
    calculated via deleted interpolation on the reference corpus.
    Weights are computed once per dialect and cached for reuse.
    
    Args:
        target_file_path: path to target XML file
        ref_lang: language name
        n: maximum n-gram size
        laplace: Laplace smoothing constant
        verbose: verbose output
    
    Returns:
        tuple: (predicted_dialect, probabilities_dict, detailed_results)
        - predicted_dialect: dialect with highest probability
        - probabilities_dict: probability for each dialect
        - detailed_results: detailed statistics (log probabilities by gram size and mode)
    """
    # Load target corpus
    target_corpus = load_target_corpus_from_file(target_file_path, phonetic=False)
    target_corpus = remove_chinese_characters(target_corpus)

    if not target_corpus.strip():
        if verbose:
            print(f"Warning: No text found in {target_file_path}")
        return None, {}, {}

    # Get all dialects for this language
    dialects = get_dialects(ref_lang)

    if not dialects:
        if verbose:
            print(f"Warning: No dialects found for language {ref_lang}")
        return None, {}, {}

    # Tokenize target corpus once (for both char and word)
    target_char_tokens = char_tokenize(target_corpus)
    target_word_tokens = word_tokenize(target_corpus, ref_lang)

    # Calculate weighted probability for each dialect
    dialect_scores = {}
    detailed_results = {}

    for dialect in dialects:
        if verbose:
            print(f"  {dialect}", end="")

        # Get cached dialect corpus (or load and cache it)
        dialect_corpus = get_or_cache_dialect_corpus(ref_lang, dialect, verbose=verbose)

        if not dialect_corpus.strip():
            if verbose:
                print(f" - no reference corpus")
            dialect_scores[dialect] = -float('inf')
            detailed_results[dialect] = {
                'char_log_prob': None,
                'word_log_prob': None,
                'weighted_score': -float('inf'),
                'weights': {},
            }
            continue

        # Get cached n-gram models for both character and word levels
        char_models, char_tokens = get_or_cache_dialect_models(ref_lang, dialect, mode="char", n=n, laplace=laplace, verbose=verbose)
        word_models, word_tokens = get_or_cache_dialect_models(ref_lang, dialect, mode="word", n=n, laplace=laplace, verbose=verbose)

        # Get cached weights computed from reference corpus
        char_weights = compute_and_cache_dialect_weights(ref_lang, dialect, mode="char", n=n, laplace=laplace, verbose=verbose)
        word_weights = compute_and_cache_dialect_weights(ref_lang, dialect, mode="word", n=n, laplace=laplace, verbose=verbose)

        # Compute weighted log probabilities for target using cached weights
        char_log_prob = 0.0
        for gram_size in range(1, n + 1):
            if gram_size in char_weights and char_weights[gram_size] > 0:
                prob = compute_ngram_probability(char_models, target_char_tokens, gram_size, laplace=laplace)
                char_log_prob += char_weights[gram_size] * prob

        word_log_prob = 0.0
        for gram_size in range(1, n + 1):
            if gram_size in word_weights and word_weights[gram_size] > 0:
                prob = compute_ngram_probability(word_models, target_word_tokens, gram_size, laplace=laplace)
                word_log_prob += word_weights[gram_size] * prob

        # Normalize by token counts to prevent magnitude explosion
        if len(target_char_tokens) > 0:
            char_log_prob = char_log_prob / len(target_char_tokens)
        if len(target_word_tokens) > 0:
            word_log_prob = word_log_prob / len(target_word_tokens)

        # Combine character and word probabilities equally
        weighted_score = (char_log_prob + word_log_prob) / 2.0

        dialect_scores[dialect] = weighted_score
        detailed_results[dialect] = {
            'char_log_prob': float(char_log_prob),
            'word_log_prob': float(word_log_prob),
            'weighted_score': float(weighted_score),
            'char_weights': {k: float(v) for k, v in char_weights.items()},
            'word_weights': {k: float(v) for k, v in word_weights.items()},
        }

        if verbose:
            print(f" - score: {weighted_score:.6f}")

    # Find predicted dialect (maximum score)
    valid_scores = {d: s for d, s in dialect_scores.items() if not np.isinf(s)}
    if not valid_scores:
        if verbose:
            print(f"Warning: No valid dialect scores found")
        return None, {}, detailed_results

    predicted_dialect = max(valid_scores, key=lambda d: valid_scores[d])

    # Compute probabilities using softmax on scores
    scores_array = np.array([valid_scores[d] for d in sorted(valid_scores.keys())])
    exp_scores = np.exp(scores_array - np.max(scores_array))  # for numerical stability
    probabilities_array = exp_scores / np.sum(exp_scores)
    
    probabilities_dict = {d: float(p) for d, p in zip(sorted(valid_scores.keys()), probabilities_array)}

    if verbose:
        print(f"  Predicted: {predicted_dialect} (probability: {probabilities_dict[predicted_dialect]:.6f})")

    return predicted_dialect, probabilities_dict, detailed_results


def predict_dialect(target_file_path, ref_lang, verbose=VERBOSE):
    """
    Predict the dialect of a target XML file by comparing it to reference corpora.
    
    Returns:
        tuple: (predicted_dialect, probabilities_dict, results_dict)
        - predicted_dialect: the dialect with minimum ratio
        - probabilities_dict: probability for each dialect
        - results_dict: detailed statistics for each dialect
    """
    # Load target corpus
    target_corpus = load_target_corpus_from_file(target_file_path, phonetic=False)
    target_corpus = remove_chinese_characters(target_corpus)

    if not target_corpus.strip():
        if verbose:
            print(f"Warning: No text found in {target_file_path}")
        return None, {}, None, {}

    # Get all dialects for this language
    dialects = get_dialects(ref_lang)

    if not dialects:
        if verbose:
            print(f"Warning: No dialects found for language {ref_lang}")
        return None, {}, None, {}

    # Calculate ratio for each dialect
    dialect_ratios = {}
    detailed_results = {}
    dialect_corpora = {}  # Store corpora for later use

    for dialect in dialects:
        if verbose:
            print(f"  {dialect}", end="")

        # Generate reference corpus for this dialect
        dialect_corpus = ""
        for ref_path in REF_PATHS:
            corpus = generate_corpus(ref_lang, ref_path, "standard", by_dialect=True, phonetic=False)
            if dialect in corpus.keys():
                dialect_corpus += corpus[dialect]

        dialect_corpora[dialect] = dialect_corpus  # Store for later use
        if not dialect_corpus.strip():
            if verbose:
                print(f" - no reference corpus")
            dialect_ratios[dialect] = float('inf')
            detailed_results[dialect] = {
                'word_ov_coeff': None,
                'word_kl_div': None,
                'word_ratio': float('inf'),
                'char_ov_coeff': None,
                'char_kl_div': None,
                'char_ratio': float('inf'),
            }
            continue

        dialect_corpus = remove_chinese_characters(dialect_corpus)

        # Compare target to dialect reference
        word_stats, char_stats = obtain_stats(dialect_corpus, target_corpus, ref_lang, verbose=False)
        word_ov, word_kl, word_ratio = word_stats
        char_ov, char_kl, char_ratio = char_stats

        # Use word-level KL divergence as primary metric
        # dialect_ratios[dialect] = word_kl
        dialect_ratios[dialect] = char_kl

        detailed_results[dialect] = {
            'word_ov_coeff': word_ov,
            'word_kl_div': word_kl,
            'word_ratio': word_ratio,
            'char_ov_coeff': char_ov,
            'char_kl_div': char_kl,
            'char_ratio': char_ratio,
        }

        if verbose:
            print(f" - kl_div: {char_kl:.6f}")

    # # Filter out infinite ratios for prediction
    # valid_ratios = {d: r for d, r in dialect_ratios.items() if not np.isinf(r) and r >= 0}
    # if not valid_ratios:
    #     if verbose:
    #         print(f"Warning: No valid dialect matches found")
    #     return None, {}, None, detailed_results

    # # Find predicted dialect (minimum ratio)
    # predicted_dialect = min(valid_ratios, key=lambda d: valid_ratios[d])
    valid_ratios = {d: r for d, r in dialect_ratios.items() if not np.isinf(r) and r >= 0}
    predicted_dialect = min(valid_ratios, key=lambda d: valid_ratios[d])

    # Compute probabilities using softmax on negative ratios
    # Lower ratio = better match, so we use negative ratios
    negative_ratios = np.array([-valid_ratios[d] for d in sorted(valid_ratios.keys())])
    exp_scores = np.exp(negative_ratios - np.max(negative_ratios))  # for numerical stability
    probabilities_array = exp_scores / np.sum(exp_scores)
    
    probabilities_dict = {d: float(p) for d, p in zip(sorted(valid_ratios.keys()), probabilities_array)}

    if verbose:
        print(f"  Predicted: {predicted_dialect} (probability: {probabilities_dict[predicted_dialect]:.6f})")
    
    # dialect_top_n_grams, top_n_minus_one_grams = get_top_n_gram_diff(dialect_corpora, ref_lang)
    # top_n_gram_pred = pred_from_top_n_grams(target_corpus, dialect_top_n_grams, ref_lang)
    # top_n_minus_one_gram_pred = pred_from_top_n_minus_one_grams(target_corpus, top_n_minus_one_grams, ref_lang)

    return predicted_dialect, probabilities_dict, detailed_results


def _load_iso639_mapping():
    """Load ISO 639-3 code to language name mapping."""
    mapping = {}
    try:
        with open("QC/validation/iso-639-3.txt", 'r', encoding='utf-8') as f:
            f.readline()  # Skip header
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    iso_code = parts[0].strip()
                    lang_name = parts[6].strip()
                    if iso_code and lang_name:
                        mapping[iso_code.lower()] = lang_name
    except Exception:
        pass
    return mapping


# Cache for ISO 639-3 mapping
_ISO639_CACHE = None

def get_iso639_mapping():
    """Get cached ISO 639-3 mapping."""
    global _ISO639_CACHE
    if _ISO639_CACHE is None:
        _ISO639_CACHE = _load_iso639_mapping()
    return _ISO639_CACHE


def extract_language_from_path(file_path):
    """Try to extract language code from file path or XML content."""
    path_parts = Path(file_path).parts
    
    # First, try to find language in path
    for part in path_parts:
        if is_lang(part):
            return part
    
    # Try to extract from XML
    iso_mapping = get_iso639_mapping()
    
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Get xml:lang attribute from root element
        lang_code = root.get('{http://www.w3.org/XML/1998/namespace}lang')
        if lang_code:
            # If it's a language name, return it
            if is_lang(lang_code):
                return lang_code
            # If it's an ISO 639-3 code, try to convert it
            if lang_code.lower() in iso_mapping:
                lang_name = iso_mapping[lang_code.lower()]
                if is_lang(lang_name):
                    return lang_name
        
        # Fallback: check xml:lang in first sentence
        first_sentence = root.find('.//S')
        if first_sentence is not None:
            lang_code = first_sentence.get('{http://www.w3.org/XML/1998/namespace}lang')
            if lang_code:
                if is_lang(lang_code):
                    return lang_code
                if lang_code.lower() in iso_mapping:
                    lang_name = iso_mapping[lang_code.lower()]
                    if is_lang(lang_name):
                        return lang_name
    except Exception:
        pass
    
    # Last resort: try to extract language from filename or directory names
    # Check for patterns like "PaiwanCh2_001" -> "Paiwan"
    for part in path_parts:
        # Remove file extension
        part_clean = part.replace('.xml', '').replace('.txt', '')
        # Split by common delimiters
        for segment in re.split(r'[_\-\d]', part_clean):
            segment = segment.strip()
            if segment and is_lang(segment):
                return segment
    
    return None


def extract_ground_truth_dialect(file_path, ref_lang):
    """
    Extract ground truth dialect from file path or XML content.
    Tries to find dialect in filename, path, or XML attributes.
    """
    file_name = Path(file_path).stem  # filename without extension
    valid_dialects = get_dialects(ref_lang)
    
    # Check if any valid dialect appears in the filename
    for dialect in valid_dialects:
        if dialect.lower() in file_name.lower():
            return dialect
    
    # Try to extract from XML dialect attribute
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        if 'dialect' in root.attrib:
            dialect = root.attrib['dialect']
            if dialect in valid_dialects:
                return dialect
    except Exception:
        pass
    
    return None


def batch_predict_dialects(corpora_path=CORPORA_PATH, subdirs=None, ref_lang=None, output_csv=None, output_confusion_matrix=None, verbose=VERBOSE, max_files=None):
    """
    Predict dialects for all XML files in reference subdirectories.
    Compares predictions against ground truth dialects extracted from files.
    
    Args:
        corpora_path: path to Corpora directory
        subdirs: list of subdirectories to process
        ref_lang: language to process (if None, extracts from each file)
        output_csv: CSV file to write results to
        output_confusion_matrix: path to save confusion matrix plot
        verbose: verbose output
        max_files: maximum number of files to process (for testing)
    
    Returns:
        tuple: (results_list, confusion_matrix_data)
    """
    if subdirs is None:
        subdirs = REF_SUBDIRS

    results = []
    skipped_count = 0
    file_count = 0
    processed_count = 0
    
    # For confusion matrix
    all_predictions = []
    all_ground_truths = []
    all_dialects = set()
    all_n_gram_predictions = []

    for subdir in subdirs:
        full_path = corpora_path + subdir
        if not Path(full_path).exists():
            if verbose:
                print(f"Skipping non-existent path: {full_path}")
            continue

        if verbose:
            print(f"\nProcessing: {full_path}")

        # Walk through all XML files
        for root, dirs, files in Path(full_path).walk():
            for file in files:
                if file.endswith('.xml'):
                    file_count += 1
                    file_path = Path(root) / file
                    
                    # Try to extract language from path or XML
                    file_lang = extract_language_from_path(str(file_path))
                    
                    if not file_lang:
                        skipped_count += 1
                        if verbose and skipped_count <= 3:
                            print(f"  Skipping {file} - could not determine language")
                        elif verbose and skipped_count == 4:
                            print(f"  (skipping files without language detection...)")
                        continue
                    
                    # If ref_lang is specified, only process files of that language
                    if ref_lang and file_lang != ref_lang:
                        continue

                    # Extract ground truth dialect
                    ground_truth_dialect = extract_ground_truth_dialect(str(file_path), file_lang)
                    
                    if not ground_truth_dialect:
                        skipped_count += 1
                        if verbose and skipped_count <= 3:
                            print(f"  Skipping {file} - could not determine ground truth dialect")
                        continue

                    processed_count += 1
                    
                    # Check if we've reached max_files limit
                    if max_files and processed_count > max_files:
                        break
                    
                    if verbose and processed_count % 5 == 0:
                        print(f"\n[Progress] Processed {processed_count} files ({skipped_count} skipped)")

                    if verbose and processed_count % 5 == 1:
                        print(f"  {file_path.name} ({file_lang})", end="", flush=True)
                    elif verbose and processed_count % 5 != 1:
                        print(f", {file_path.name}", end="", flush=True)

                    try:
                        predicted_dialect, probabilities, detailed_results = pred_inter(
                            str(file_path), file_lang, verbose=False
                        )

                        # top_n_gram_dialect = None
                        # if top_n_gram_pred is not None:
                        #     top_n_gram_dialect, top_n_gram_scores = top_n_gram_pred
                        #     if verbose:
                        #         print(f"  Top N-gram prediction: {top_n_gram_dialect} (scores: {top_n_gram_scores})")

                        if predicted_dialect is None:
                            continue

                        # Track for confusion matrix
                        all_predictions.append(predicted_dialect)
                        all_ground_truths.append(ground_truth_dialect)
                        all_dialects.add(predicted_dialect)
                        all_dialects.add(ground_truth_dialect)
                        # all_n_gram_predictions.append(top_n_gram_dialect)

                        result = {
                            'file': file_path.name,
                            'path': str(file_path),
                            'language': file_lang,
                            'ground_truth_dialect': ground_truth_dialect,
                            'predicted_dialect': predicted_dialect,
                            'correct': predicted_dialect == ground_truth_dialect,
                        }
                        
                        # Add probabilities for all dialects
                        for dialect in sorted(probabilities.keys()):
                            result[f'prob_{dialect}'] = probabilities[dialect]
                        
                        results.append(result)

                    except Exception as e:
                        if verbose:
                            print(f" [ERROR: {str(e)[:50]}]", end="", flush=True)
                        continue

    if verbose and processed_count % 5 != 1:
        print()  # newline after batch output

    # Collect all dialect names from probability columns in results
    all_prob_dialects = set()
    for result in results:
        for key in result.keys():
            if key.startswith('prob_'):
                dialect = key.replace('prob_', '')
                all_prob_dialects.add(dialect)

    # Write results to CSV if specified
    if output_csv and results:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['file', 'path', 'language', 'ground_truth_dialect', 'predicted_dialect', 'correct']
            # Add probability columns for all dialects found in results
            for dialect in sorted(all_prob_dialects):
                fieldnames.append(f'prob_{dialect}')
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        if verbose:
            print(f"\nResults written to: {output_path}")

    # Generate confusion matrix
    cm_data = None
    sorted_dialects = sorted(list(all_dialects)) if all_dialects else []
    
    if all_predictions and all_ground_truths and sorted_dialects:
        cm = confusion_matrix(all_ground_truths, all_predictions, labels=sorted_dialects)
        cm_data = {
            'matrix': cm,
            'labels': sorted_dialects,
            'predictions': all_predictions,
            'ground_truths': all_ground_truths,
        }
        
        # Save confusion matrix visualization if path provided
        if output_confusion_matrix:
            output_path = Path(output_confusion_matrix)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            plt.figure(figsize=(12, 10))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                       xticklabels=sorted_dialects, yticklabels=sorted_dialects,
                       cbar_kws={'label': 'Count'})
            plt.title(f'Dialect Prediction Confusion Matrix (n={len(all_predictions)})')
            plt.ylabel('Ground Truth')
            plt.xlabel('Predicted')
            plt.tight_layout()
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            if verbose:
                print(f"Confusion matrix saved to: {output_path}")

    # if all_n_gram_predictions and all_ground_truths and sorted_dialects:
    #     n_gram_cm = confusion_matrix(all_ground_truths, all_n_gram_predictions, labels=sorted_dialects)
    #     n_gram_cm_data = {
    #         'matrix': n_gram_cm,
    #         'labels': sorted_dialects,
    #         'predictions': all_n_gram_predictions,
    #         'ground_truths': all_ground_truths,
    #     }
        
    #     # Save n-gram confusion matrix visualization if path provided
    #     if output_confusion_matrix:
    #         n_gram_output_path = Path(output_confusion_matrix).with_name(f"n_gram_{Path(output_confusion_matrix).name}")
    #         plt.figure(figsize=(12, 10))
    #         sns.heatmap(n_gram_cm, annot=True, fmt='d', cmap='Greens', 
    #                    xticklabels=sorted_dialects, yticklabels=sorted_dialects,
    #                    cbar_kws={'label': 'Count'})
    #         plt.title(f'Top N-gram Dialect Prediction Confusion Matrix (n={len(all_n_gram_predictions)})')
    #         plt.ylabel('Ground Truth')
    #         plt.xlabel('Predicted')
    #         plt.tight_layout()
    #         plt.savefig(n_gram_output_path, dpi=150, bbox_inches='tight')
    #         plt.close()
            
    #         if verbose:
    #             print(f"Top N-gram confusion matrix saved to: {n_gram_output_path}")

    return results, cm_data

def get_top_n_gram_diff(dialect_copora, lang, n=N, limit=LIMIT):
    """
    Get the top n-grams that differentiate dialects based on their frequency.
    
    Args:
        dialect_copora: dict of {dialect: corpus_text}
        n: n-gram size
        limit: number of top n-grams to return
    """
    dialect_n_grams = {}

    for dialect, corpus in dialect_copora.items():
        tokens = word_tokenize(corpus, lang)
        n_grams = [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]
        n_minus_one_grams = [tuple(tokens[i:i + n - 1]) for i in range(len(tokens) - n + 2)] if n > 1 else None
        n_gram_counter = Counter(n_grams)

        total = n_gram_counter.total()
        if total > 0:
            dialect_n_grams[dialect] = Counter({k: v / total for k, v in n_gram_counter.items()})
        else:
            dialect_n_grams[dialect] = Counter()

    dialect_top_n_grams = {}

    for dialect, n_gram_counter in dialect_n_grams.items():
        other_counter = Counter()
        other_total = 0
        for d, c in dialect_n_grams.items():
            if c == n_gram_counter:
                continue
            # Calculate difference in n-gram frequencies
            else:
                other_counter += c
                other_total += sum(c.values())
        if other_total > 0:
            other_counter = Counter({k: v / other_total for k, v in other_counter.items()})
        else:
            other_counter = Counter()
        diff_counter = n_gram_counter - other_counter
        dialect_top_n_grams[dialect] = diff_counter.most_common(limit) 
    
    # Compute top (n-1)-grams with distinctive next-word probability distributions
    top_n_minus_one_grams = {}
    
    if n > 1:
        # Extract tokens for each dialect
        dialect_tokens = {}
        for dialect, corpus in dialect_copora.items():
            dialect_tokens[dialect] = word_tokenize(corpus, lang)
        
        # Extract (n-1)-grams and their continuations for each dialect
        dialect_n_minus_one_continuations = {}  # {dialect: {(n-1)-gram: Counter of next words}}
        all_n_minus_one_grams = set()
        
        for dialect, tokens in dialect_tokens.items():
            n_minus_one_continuations = {}
            for i in range(len(tokens) - n + 1):
                n_minus_one_gram = tuple(tokens[i:i + n - 1])
                next_word = tokens[i + n - 1]
                if n_minus_one_gram not in n_minus_one_continuations:
                    n_minus_one_continuations[n_minus_one_gram] = Counter()
                n_minus_one_continuations[n_minus_one_gram][next_word] += 1
                all_n_minus_one_grams.add(n_minus_one_gram)
            
            dialect_n_minus_one_continuations[dialect] = n_minus_one_continuations
        
        # For each dialect, find (n-1)-grams with distinctive next-word distributions
        for dialect in dialect_copora.keys():
            differences = {}
            
            for n_minus_one_gram in all_n_minus_one_grams:
                # Get next-word distributions for this (n-1)-gram across all dialects
                distributions = {}
                all_words = set()
                
                for d in dialect_copora.keys():
                    if n_minus_one_gram in dialect_n_minus_one_continuations[d]:
                        distributions[d] = dialect_n_minus_one_continuations[d][n_minus_one_gram]
                        all_words.update(distributions[d].keys())
                    else:
                        distributions[d] = Counter()
                
                # Apply Laplace smoothing to all distributions
                smoothed_dists = {}
                for d in dialect_copora.keys():
                    smoothed = Counter()
                    for word in all_words:
                        count = distributions[d].get(word, 0) + LAPLACE
                        smoothed[word] = count
                    total = sum(smoothed.values())
                    if total > 0:
                        smoothed_dists[d] = {word: count / total for word, count in smoothed.items()}
                    else:
                        smoothed_dists[d] = {}
                
                # Compute difference for this dialect's distribution vs others
                if dialect in smoothed_dists and smoothed_dists[dialect]:
                    target_dist = smoothed_dists[dialect]
                    
                    # Compute average distribution of other dialects
                    other_dists = [smoothed_dists[d] for d in dialect_copora.keys() if d != dialect]
                    other_avg = {}
                    if other_dists:
                        for word in all_words:
                            other_avg[word] = np.mean([d.get(word, 0) for d in other_dists])
                    
                    # Use sum of absolute differences as difference measure
                    difference = sum(abs(target_dist.get(w, 0) - other_avg.get(w, 0)) for w in all_words)
                    differences[n_minus_one_gram] = (difference, target_dist)
            
            # Get top limit (n-1)-grams by difference
            sorted_diffs = sorted(differences.items(), key=lambda x: x[1][0], reverse=True)
            top_n_minus_one_grams[dialect] = [(n_minus_one_gram, dist) for n_minus_one_gram, (_, dist) in sorted_diffs[:limit]]
    
    return dialect_top_n_grams, top_n_minus_one_grams

def pred_from_top_n_grams(target_corpus, dialect_top_n_grams, lang, next=False):
    """
    Predict dialect based on the presence of top differentiating n-grams.
    
    Args:
        target_corpus: text of the target corpus
        dialect_top_n_grams: dict of {dialect: list of (n-gram, count)}
        lang: language of the target corpus
    """
    tokens = word_tokenize(target_corpus, lang)
    if not next:
        n_grams = [tuple(tokens[i:i + N]) for i in range(len(tokens) - N + 1)]
    else:
        n_grams = [tuple(tokens[i:i + N - 1]) for i in range(len(tokens) - N + 2)]
    n_gram_set = set(n_grams)

    dialect_scores = {}
    for dialect, top_n_grams in dialect_top_n_grams.items():
        score = sum(count for n_gram, count in top_n_grams if n_gram in n_gram_set)
        dialect_scores[dialect] = score

    # Predict the dialect with the highest score
    predicted_dialect = max(dialect_scores, key=lambda d: dialect_scores[d])
    return predicted_dialect, dialect_scores

def pred_from_top_n_minus_one_grams(target_corpus, dialect_top_n_minus_one_grams, lang):
    """
    Predict dialect based on the presence of top differentiating (n-1)-grams and their next-word distributions.
    
    Args:
        target_corpus: text of the target corpus
        dialect_top_n_minus_one_grams: dict of {dialect: list of (n-1)-gram, next-word distribution)}
        lang: language of the target corpus
    """
    tokens = word_tokenize(target_corpus, lang)
    n_minus_one_grams = [tuple(tokens[i:i + N - 1]) for i in range(len(tokens) - N + 2)]
    
    dialect_scores = {}
    for dialect, top_n_minus_one_grams in dialect_top_n_minus_one_grams.items():
        score = 0
        for n_minus_one_gram, next_word_dist in top_n_minus_one_grams:
            if n_minus_one_gram in n_minus_one_grams:
                # Get the index of the (n-1)-gram in the target tokens
                indices = [i for i in range(len(tokens) - N + 2) if tuple(tokens[i:i + N - 1]) == n_minus_one_gram]
                for idx in indices:
                    if idx + N - 1 < len(tokens):
                        next_word = tokens[idx + N - 1]
                        score += next_word_dist.get(next_word, 0)
        dialect_scores[dialect] = score

    # Predict the dialect with the highest score
    predicted_dialect = max(dialect_scores, key=lambda d: dialect_scores[d])
    return predicted_dialect, dialect_scores

def main(args):
    corpora_path = args.corpora_path
    subdirs = args.subdirs
    ref_lang = args.ref_lang
    output_csv = args.output_csv
    output_confusion_matrix = args.output_confusion_matrix
    verbose = args.verbose
    max_files = args.max_files

    if verbose:
        print(f"Batch dialect detection with confusion matrix")
        print(f"Corpora path: {corpora_path}")
        print(f"Subdirectories: {subdirs}")
        if ref_lang:
            print(f"Language filter: {ref_lang}")
        if max_files:
            print(f"Max files limit: {max_files}")
        print()

    # Run batch prediction
    results, cm_data = batch_predict_dialects(
        corpora_path=corpora_path, 
        subdirs=subdirs, 
        ref_lang=ref_lang,
        output_csv=output_csv, 
        output_confusion_matrix=output_confusion_matrix,
        verbose=verbose,
        max_files=max_files
    )

    if verbose:
        print(f"\n{'='*60}")
        print(f"BATCH PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total files processed: {len(results)}")

        # Summary statistics
        if results:
            # Calculate accuracy
            correct = sum(1 for r in results if r['correct'])
            accuracy = correct / len(results) if results else 0
            print(f"Accuracy: {accuracy:.4f} ({correct}/{len(results)})")

            # Calculate average confidence for predicted dialect (what the model chose)
            correct_confidences = []
            incorrect_confidences = []
            for r in results:
                predicted = r['predicted_dialect']
                prob_key = f'prob_{predicted}'
                if prob_key in r:
                    confidence = r[prob_key]
                    if r['correct']:
                        correct_confidences.append(confidence)
                    else:
                        incorrect_confidences.append(confidence)
            
            if correct_confidences:
                avg_correct_conf = np.mean(correct_confidences)
                print(f"Avg confidence (correct predictions): {avg_correct_conf:.6f}")
            
            if incorrect_confidences:
                avg_incorrect_conf = np.mean(incorrect_confidences)
                print(f"Avg confidence (incorrect predictions): {avg_incorrect_conf:.6f}")

            # Group by language
            by_language = {}
            for r in results:
                lang = r['language']
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(r)

            print(f"\nResults by language:")
            for lang in sorted(by_language.keys()):
                lang_results = by_language[lang]
                lang_correct = sum(1 for r in lang_results if r['correct'])
                lang_accuracy = lang_correct / len(lang_results) if lang_results else 0
                
                # Per-language confidence stats
                lang_correct_confidences = []
                lang_incorrect_confidences = []
                for r in lang_results:
                    predicted = r['predicted_dialect']
                    prob_key = f'prob_{predicted}'
                    if prob_key in r:
                        confidence = r[prob_key]
                        if r['correct']:
                            lang_correct_confidences.append(confidence)
                        else:
                            lang_incorrect_confidences.append(confidence)
                
                print(f"  {lang}: {len(lang_results)} files (accuracy: {lang_accuracy:.4f})", end="")
                
                if lang_correct_confidences:
                    avg_conf = np.mean(lang_correct_confidences)
                    print(f", avg correct conf: {avg_conf:.6f}", end="")
                
                if lang_incorrect_confidences:
                    avg_conf = np.mean(lang_incorrect_confidences)
                    print(f", avg incorrect conf: {avg_conf:.6f}", end="")
                
                print()

        # Print confusion matrix summary
        if cm_data:
            print(f"\n{'='*60}")
            print(f"CONFUSION MATRIX")
            print(f"{'='*60}")
            cm = cm_data['matrix']
            labels = cm_data['labels']
            
            # Create a formatted confusion matrix display
            print("\nPredicted (columns) vs Ground Truth (rows):")
            print("  " + " ".join([f"{l:>8}" for l in labels]))
            for i, label in enumerate(labels):
                print(f"{label:>3} " + " ".join([f"{cm[i][j]:>8}" for j in range(len(labels))]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch detect dialects of XML files with confusion matrix")
    parser.add_argument('--corpora_path', default=CORPORA_PATH, help='path to Corpora directory')
    parser.add_argument('--subdirs', nargs='+', default=REF_SUBDIRS, help='subdirectories to process')
    parser.add_argument('--ref_lang', help='language to process (if None, process all languages)', required=False, default=None)
    parser.add_argument('--output_csv', help='CSV file to write results to', required=False, default=None)
    parser.add_argument('--output_confusion_matrix', help='path to save confusion matrix plot', required=False, default=None)
    parser.add_argument('--verbose', type=parse_bool, help='verbose output', required=False, default=True)
    parser.add_argument('--max_files', type=int, help='max files to process (for testing)', required=False, default=None)

    args = parser.parse_args()
    main(args)
