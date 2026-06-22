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


def get_dialects(lang):
    """Get all dialects for a given language from dialects.csv."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        dialects = dialect_csv[dialect_csv['Language'] == lang]['Official'].unique().tolist()
        return dialects
    except Exception as e:
        print(f"Warning: Could not read dialects.csv: {e}")
        return []


def load_target_corpus_from_file(tar_path):
    """Load text from XML file."""
    if tar_path.lower().endswith('.xml'):
        tree = ET.parse(tar_path)
        root = tree.getroot()
        text = []
        for sentence in root.findall('.//S'):
            form = sentence.find("FORM[@kindOf='standard']")
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
    target_corpus = load_target_corpus_from_file(target_file_path)
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

    # Calculate ratio for each dialect
    dialect_ratios = {}
    detailed_results = {}

    for dialect in dialects:
        if verbose:
            print(f"  {dialect}", end="")

        # Generate reference corpus for this dialect
        dialect_corpus = ""
        for path in REF_PATHS:
            corpus = generate_corpus(ref_lang, path, "standard", by_dialect=True)
            if dialect in corpus.keys():
                dialect_corpus += corpus[dialect]

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
        dialect_ratios[dialect] = word_ratio

        detailed_results[dialect] = {
            'word_ov_coeff': word_ov,
            'word_kl_div': word_kl,
            'word_ratio': word_ratio,
            'char_ov_coeff': char_ov,
            'char_kl_div': char_kl,
            'char_ratio': char_ratio,
        }

        if verbose:
            print(f" - kl_div: {word_kl:.6f}")

    # Filter out infinite ratios for prediction
    valid_ratios = {d: r for d, r in dialect_ratios.items() if not np.isinf(r) and r >= 0}
    if not valid_ratios:
        if verbose:
            print(f"Warning: No valid dialect matches found")
        return None, {}, detailed_results

    # Find predicted dialect (minimum ratio)
    predicted_dialect = min(valid_ratios, key=valid_ratios.get)

    # Compute probabilities using softmax on negative ratios
    # Lower ratio = better match, so we use negative ratios
    negative_ratios = np.array([-valid_ratios[d] for d in sorted(valid_ratios.keys())])
    exp_scores = np.exp(negative_ratios - np.max(negative_ratios))  # for numerical stability
    probabilities_array = exp_scores / np.sum(exp_scores)
    
    probabilities_dict = {d: float(p) for d, p in zip(sorted(valid_ratios.keys()), probabilities_array)}

    if verbose:
        print(f"  Predicted: {predicted_dialect} (probability: {probabilities_dict[predicted_dialect]:.6f})")

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


def batch_predict_dialects(corpora_path=CORPORA_PATH, subdirs=None, ref_lang=None, output_csv=None, output_confusion_matrix=None, verbose=VERBOSE):
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
                    if verbose and processed_count % 5 == 0:
                        print(f"\n[Progress] Processed {processed_count} files ({skipped_count} skipped)")

                    if verbose and processed_count % 5 == 1:
                        print(f"  {file_path.name} ({file_lang})", end="", flush=True)
                    elif verbose and processed_count % 5 != 1:
                        print(f", {file_path.name}", end="", flush=True)

                    try:
                        predicted_dialect, probabilities, detailed_results = predict_dialect(
                            str(file_path), file_lang, verbose=False
                        )

                        if predicted_dialect is None:
                            continue

                        # Track for confusion matrix
                        all_predictions.append(predicted_dialect)
                        all_ground_truths.append(ground_truth_dialect)
                        all_dialects.add(predicted_dialect)
                        all_dialects.add(ground_truth_dialect)

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
    if all_predictions and all_ground_truths:
        sorted_dialects = sorted(list(all_dialects))
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

    return results, cm_data




def main(args):
    corpora_path = args.corpora_path
    subdirs = args.subdirs
    ref_lang = args.ref_lang
    output_csv = args.output_csv
    output_confusion_matrix = args.output_confusion_matrix
    verbose = args.verbose

    if verbose:
        print(f"Batch dialect detection with confusion matrix")
        print(f"Corpora path: {corpora_path}")
        print(f"Subdirectories: {subdirs}")
        if ref_lang:
            print(f"Language filter: {ref_lang}")
        print()

    # Run batch prediction
    results, cm_data = batch_predict_dialects(
        corpora_path=corpora_path, 
        subdirs=subdirs, 
        ref_lang=ref_lang,
        output_csv=output_csv, 
        output_confusion_matrix=output_confusion_matrix,
        verbose=verbose
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

            # Calculate average confidence for ground truth dialect
            correct_confidences = []
            incorrect_confidences = []
            for r in results:
                ground_truth = r['ground_truth_dialect']
                prob_key = f'prob_{ground_truth}'
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
                    ground_truth = r['ground_truth_dialect']
                    prob_key = f'prob_{ground_truth}'
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
    parser.add_argument('--ref_dialect', help='reference dialect (informational, for filtering if needed)', required=False, default=None)
    parser.add_argument('--output_csv', help='CSV file to write results to', required=False, default=None)
    parser.add_argument('--output_confusion_matrix', help='path to save confusion matrix plot', required=False, default=None)
    parser.add_argument('--verbose', type=parse_bool, help='verbose output', required=False, default=True)

    args = parser.parse_args()
    main(args)
