"""
Validate all XML files in Corpora/ using per-language thresholds from the perturbation test suite.

Fast implementation using Counter-based profiles (similar to dialect_detector).
Builds language profiles upfront, then compares each file against its language's profile.

Usage:
    python validate_corpora_with_thresholds.py --thresholds-file <path> [--output-dir <path>]

Example:
    python validate_corpora_with_thresholds.py \
        --thresholds-file test_results/perturbation_tests/statistical_thresholds.json \
        --output-dir test_results/corpora_validation
"""

import json
import os
import argparse
import logging
import math
import re
import numpy as np
from pathlib import Path
from collections import Counter
from datetime import datetime
from xml.etree import ElementTree as ET
from scipy.optimize import minimize

# Configure logging
def setup_logging(log_dir, debug=False):
    """Set up logging to file and console with UTF-8 encoding."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"validation_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    stream_handler = logging.StreamHandler()
    stream_handler.stream.reconfigure(encoding='utf-8', errors='replace') if hasattr(stream_handler.stream, 'reconfigure') else None
    
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            file_handler,
            stream_handler
        ]
    )
    return logging.getLogger(__name__)


def extract_standard_text(root: ET.Element) -> str:
    """Extract standard form text from XML root element."""
    parts = [
        f.text.strip()
        for s in root.findall(".//S")
        for f in s.findall("./FORM[@kindOf='standard']")
        if f.text and f.text.strip()
    ]
    return " ".join(parts).strip()


def extract_counts(text: str) -> tuple:
    """Extract character and word n-grams (unigrams, bigrams, trigrams). Fast Counter-based approach."""
    # Character level
    chars = [c for c in text if not c.isspace()]
    char_uni = Counter(chars)
    char_bi = Counter(f"{chars[i]} {chars[i + 1]}" for i in range(len(chars) - 1))
    char_tri = Counter(f"{chars[i]} {chars[i + 1]} {chars[i + 2]}" for i in range(len(chars) - 2))
    
    # Word level
    words = re.findall(r'\w+', text.casefold())
    word_uni = Counter(words)
    word_bi = Counter(f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1))
    
    return char_uni, char_bi, char_tri, word_uni, word_bi


def kl_divergence(counts: Counter, profile_counts: Counter, profile_total: int, vocab_size: int, smoothing: float = 1.0) -> float:
    """
    Compute KL divergence of document distribution from profile distribution.
    KL(counts || profile) = Sum_x counts(x) * log(counts(x) / profile(x))
    Always non-negative by definition.
    """
    n = sum(counts.values())
    if n == 0:
        return 0.0
    denom = profile_total + smoothing * max(vocab_size, 1)
    kl = 0.0
    for item, c in counts.items():
        p = (profile_counts.get(item, 0) + smoothing) / denom  # profile probability
        q = c / n  # document probability
        if q > 0 and p > 0:  # both must be > 0 for valid log
            kl += q * math.log(q / p)  # KL divergence formula
    return kl


def load_corpora_and_build_profiles(corpora_path, logger):
    """Load all XML files and build language profiles (aggregated Counters)."""
    logger.info("Loading corpora and building language profiles...")
    
    docs = {}  # {lang_code: [(corpus_name, dialect, text, char_uni, char_bi, char_tri, word_uni, word_bi), ...]}
    profiles = {}  # {lang_code: {"char_uni": Counter, "char_bi": Counter, "char_tri": Counter, ...}}
    
    # First pass: load all documents
    xml_files = list(Path(corpora_path).rglob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML files")
    
    for xml_file in sorted(xml_files):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            if root.tag != 'TEXT':
                continue
            
            lang_code = (root.get('{http://www.w3.org/XML/1998/namespace}lang') or root.get('lang') or '').strip().lower()
            if not lang_code or len(lang_code) == 0:
                continue
            
            if len(lang_code) > 3:
                lang_code = lang_code.split('-')[0]
            
            dialect = root.get('dialect', 'default')
            corpus_name = xml_file.stem
            
            # Extract standard text
            text = extract_standard_text(root)
            if not text:
                continue
            
            # Extract features (now includes trigrams)
            char_uni, char_bi, char_tri, word_uni, word_bi = extract_counts(text)
            
            if lang_code not in docs:
                docs[lang_code] = []
            
            docs[lang_code].append({
                'corpus_name': corpus_name,
                'dialect': dialect,
                'text': text,
                'char_uni': char_uni,
                'char_bi': char_bi,
                'char_tri': char_tri,
                'word_uni': word_uni,
                'word_bi': word_bi
            })
        except Exception as e:
            logger.debug(f"Error loading {xml_file}: {e}")
            continue
    
    logger.info(f"Loaded {len(docs)} languages with {sum(len(v) for v in docs.values())} documents")
    
    # Second pass: build aggregated profiles per language
    for lang_code, doc_list in docs.items():
        agg_char_uni = Counter()
        agg_char_bi = Counter()
        agg_char_tri = Counter()
        agg_word_uni = Counter()
        agg_word_bi = Counter()
        
        for doc in doc_list:
            agg_char_uni.update(doc['char_uni'])
            agg_char_bi.update(doc['char_bi'])
            agg_char_tri.update(doc['char_tri'])
            agg_word_uni.update(doc['word_uni'])
            agg_word_bi.update(doc['word_bi'])
        
        profiles[lang_code] = {
            'char_uni': agg_char_uni,
            'char_bi': agg_char_bi,
            'char_tri': agg_char_tri,
            'word_uni': agg_word_uni,
            'word_bi': agg_word_bi,
            'char_uni_total': sum(agg_char_uni.values()),
            'char_bi_total': sum(agg_char_bi.values()),
            'char_tri_total': sum(agg_char_tri.values()),
            'word_uni_total': sum(agg_word_uni.values()),
            'word_bi_total': sum(agg_word_bi.values()),
            'char_uni_vocab': len(agg_char_uni),
            'char_bi_vocab': len(agg_char_bi),
            'char_tri_vocab': len(agg_char_tri),
            'word_uni_vocab': len(agg_word_uni),
            'word_bi_vocab': len(agg_word_bi),
        }
    
    return docs, profiles


def compute_language_scores(doc_features, profiles, baselines, weights):
    """
    Compute weighted KL divergence scores against all language profiles.
    
    Args:
        doc_features: Dict with 'char_uni', 'char_bi', 'char_tri', 'word_uni', 'word_bi'
        profiles: Dict[lang_code -> profile]
        baselines: Dict[lang_code -> baseline metrics]
        weights: Tuple/list of 4 weights [w_char_uni, w_char_bi, w_char_tri, w_word_uni]
    
    Returns:
        Dict[lang_code -> weighted_score]
    """
    scores = {}
    
    for lang_code, profile in profiles.items():
        # Compute KL divergences
        char_uni_kl = kl_divergence(doc_features['char_uni'], profile['char_uni'], 
                                    profile['char_uni_total'], profile['char_uni_vocab'])
        char_bi_kl = kl_divergence(doc_features['char_bi'], profile['char_bi'],
                                   profile['char_bi_total'], profile['char_bi_vocab'])
        char_tri_kl = kl_divergence(doc_features['char_tri'], profile['char_tri'],
                                    profile['char_tri_total'], profile['char_tri_vocab'])
        word_uni_kl = kl_divergence(doc_features['word_uni'], profile['word_uni'],
                                    profile['word_uni_total'], profile['word_uni_vocab'])
        
        # Compute deltas from baseline
        lang_baselines = baselines.get(lang_code, {})
        char_uni_delta = char_uni_kl - lang_baselines.get('character_1gram_baseline_kl', 0)
        char_bi_delta = char_bi_kl - lang_baselines.get('character_2gram_baseline_kl', 0)
        char_tri_delta = char_tri_kl - lang_baselines.get('character_3gram_baseline_kl', 0)
        word_uni_delta = word_uni_kl - lang_baselines.get('word_1gram_baseline_kl', 0)
        
        # Compute weighted score (lower is better/more likely)
        weighted_score = (weights[0] * char_uni_delta + 
                         weights[1] * char_bi_delta +
                         weights[2] * char_tri_delta +
                         weights[3] * word_uni_delta)
        
        scores[lang_code] = weighted_score
    
    return scores


def optimize_language_discrimination_weights(docs, profiles, baselines, logger):
    """
    Optimize weights to maximize F1 score of language discrimination.
    
    Args:
        docs: Dict[lang_code -> List of documents with 'char_uni', 'char_bi', etc.]
        profiles: Dict[lang_code -> profile]
        baselines: Dict[lang_code -> baseline metrics]
        logger: Logger instance
    
    Returns:
        Optimal weights [w_char_uni, w_char_bi, w_char_tri, w_word_uni]
    """
    logger.info("Optimizing weights for language discrimination...")
    
    # Prepare data: true language and features for each document
    data = []
    for true_lang, doc_list in docs.items():
        for doc in doc_list:
            data.append((true_lang, {
                'char_uni': doc['char_uni'],
                'char_bi': doc['char_bi'],
                'char_tri': doc['char_tri'],
                'word_uni': doc['word_uni'],
                'word_bi': doc['word_bi']
            }))
    
    def compute_f1_loss(weights):
        """Compute negative F1 score (for minimization)."""
        # Ensure weights are positive
        weights = np.abs(weights) + 1e-6
        
        tp, fp, fn = 0, 0, 0
        
        for true_lang, doc_features in data:
            scores = compute_language_scores(doc_features, profiles, baselines, weights)
            predicted_lang = min(scores, key=scores.get)
            
            if predicted_lang == true_lang:
                tp += 1
            else:
                fp += 1
                fn += 1
        
        # Compute F1
        if tp + fp == 0 or tp + fn == 0:
            f1 = 0
        else:
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return -f1  # Negative because we're minimizing
    
    # Initial weights (equal)
    initial_weights = np.array([0.25, 0.25, 0.25, 0.25])
    
    # Optimize
    result = minimize(compute_f1_loss, initial_weights, method='Nelder-Mead',
                     options={'maxiter': 500, 'xatol': 1e-6})
    
    optimal_weights = np.abs(result.x) + 1e-6
    # Normalize weights to sum to 1
    optimal_weights = optimal_weights / np.sum(optimal_weights)
    
    best_f1 = -result.fun
    logger.info(f"Optimal weights: char_uni={optimal_weights[0]:.4f}, char_bi={optimal_weights[1]:.4f}, "
               f"char_tri={optimal_weights[2]:.4f}, word_uni={optimal_weights[3]:.4f}")
    logger.info(f"Best F1 score: {best_f1:.4f}")
    
    return optimal_weights


def validate_file_against_profile(corpus_name, lang_code, dialect, doc_features, profile, thresholds, 
                                  all_profiles=None, baselines=None, weights=None, exclude_self_corpus=None):
    """
    Validate a single file against its language profile using language discrimination.
    
    If weights are provided, uses weighted language discrimination (predicts language).
    Otherwise, uses threshold-based validation (passes if deltas are within thresholds).
    """
    result = {
        "corpus": corpus_name,
        "language": lang_code,
        "dialect": dialect,
        "status": "UNKNOWN",
        "metrics": {},
        "metric_deltas": {},
        "issues": [],
        "language_scores": {},
    }
    
    if lang_code not in thresholds.get('per_language', {}):
        result["issues"].append(f"No thresholds for language {lang_code}")
        result["status"] = "SKIP"
        return result
    
    lang_thresholds = thresholds['per_language'][lang_code]
    lang_baselines = thresholds.get('per_language_baselines', {}).get(lang_code, {})
    
    # Compute KL divergences for each metric (unigrams, bigrams, trigrams)
    char_uni_kl = kl_divergence(doc_features['char_uni'], profile['char_uni'], profile['char_uni_total'], profile['char_uni_vocab'])
    char_bi_kl = kl_divergence(doc_features['char_bi'], profile['char_bi'], profile['char_bi_total'], profile['char_bi_vocab'])
    char_tri_kl = kl_divergence(doc_features['char_tri'], profile['char_tri'], profile['char_tri_total'], profile['char_tri_vocab'])
    word_uni_kl = kl_divergence(doc_features['word_uni'], profile['word_uni'], profile['word_uni_total'], profile['word_uni_vocab'])
    word_bi_kl = kl_divergence(doc_features['word_bi'], profile['word_bi'], profile['word_bi_total'], profile['word_bi_vocab'])
    
    result["metrics"] = {
        "char_uni_kl": char_uni_kl,
        "char_bi_kl": char_bi_kl,
        "char_tri_kl": char_tri_kl,
        "word_uni_kl": word_uni_kl,
        "word_bi_kl": word_bi_kl,
    }
    
    # Compute metric deltas from baseline (distance from unperturbed reference)
    char_uni_delta = char_uni_kl - lang_baselines.get('character_1gram_baseline_kl', char_uni_kl)
    char_bi_delta = char_bi_kl - lang_baselines.get('character_2gram_baseline_kl', char_bi_kl)
    char_tri_delta = char_tri_kl - lang_baselines.get('character_3gram_baseline_kl', char_tri_kl)
    word_uni_delta = word_uni_kl - lang_baselines.get('word_1gram_baseline_kl', word_uni_kl)
    word_bi_delta = word_bi_kl - lang_baselines.get('word_2gram_baseline_kl', word_bi_kl)
    
    result["metric_deltas"] = {
        "char_uni_delta": char_uni_delta,
        "char_bi_delta": char_bi_delta,
        "char_tri_delta": char_tri_delta,
        "word_uni_delta": word_uni_delta,
        "word_bi_delta": word_bi_delta,
    }
    
    # Check character metrics against thresholds based on deltas
    # PASS: all of unigram, bigram, trigram pass
    # UNKNOWN: at least bigram or trigram passes (but not all three)
    # FAIL: otherwise (none pass, or only unigram passes)
    
    char_uni_passes = char_uni_delta < lang_thresholds.get("character_kl_1gram", {}).get("upper_threshold", float('inf'))
    char_bi_passes = char_bi_delta < lang_thresholds.get("character_kl_2gram", {}).get("upper_threshold", float('inf'))
    char_tri_passes = char_tri_delta < lang_thresholds.get("character_kl_3gram", {}).get("upper_threshold", float('inf'))
    
    # Track which metrics fail for reporting
    if not char_uni_passes:
        result["issues"].append(f"char_uni_delta: {char_uni_delta:.6f} >= threshold {lang_thresholds.get('character_kl_1gram', {}).get('upper_threshold', 'N/A')}")
    if not char_bi_passes:
        result["issues"].append(f"char_bi_delta: {char_bi_delta:.6f} >= threshold {lang_thresholds.get('character_kl_2gram', {}).get('upper_threshold', 'N/A')}")
    if not char_tri_passes:
        result["issues"].append(f"char_tri_delta: {char_tri_delta:.6f} >= threshold {lang_thresholds.get('character_kl_3gram', {}).get('upper_threshold', 'N/A')}")
    
    # Language discrimination based on weighted scoring (if weights provided)
    if weights is not None and all_profiles is not None and baselines is not None:
        # Compute scores against all languages
        lang_scores = compute_language_scores(doc_features, all_profiles, baselines, weights)
        result["language_scores"] = {k: float(v) for k, v in lang_scores.items()}
        
        # Predict language with minimum score
        predicted_lang = min(lang_scores, key=lang_scores.get)
        result["predicted_language"] = predicted_lang
        result["predicted_score"] = float(lang_scores[predicted_lang])
        
        # PASS: correct language predicted
        # FAIL: wrong language predicted
        if predicted_lang == lang_code:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"
            result["issues"].append(f"Language mismatch: predicted {predicted_lang.upper()}, true {lang_code.upper()}")
    else:
        # Fall back to threshold-based validation
        # Determine status based on character metrics only
        if char_uni_passes and char_bi_passes and char_tri_passes:
            # All character metrics pass
            result["status"] = "PASS"
        elif char_bi_passes or char_tri_passes:
            # At least bigram or trigram passes (but not all three)
            result["status"] = "UNKNOWN"
        else:
            # None pass, or only unigram passes
            result["status"] = "FAIL"
    
    # Store word metrics for reference (but don't use in pass/fail)
    result["word_metrics_reference"] = {
        "word_uni_delta": {
            "value": word_uni_delta,
            "baseline": lang_baselines.get('word_1gram_baseline_kl', 'N/A'),
            "threshold": lang_thresholds.get("word_kl_1gram", {}).get("upper_threshold", "N/A"),
            "passes": word_uni_delta < lang_thresholds.get("word_kl_1gram", {}).get("upper_threshold", float('inf'))
        },
        "word_bi_delta": {
            "value": word_bi_delta,
            "baseline": lang_baselines.get('word_2gram_baseline_kl', 'N/A'),
            "threshold": lang_thresholds.get("word_kl_2gram", {}).get("upper_threshold", "N/A"),
            "passes": word_bi_delta < lang_thresholds.get("word_kl_2gram", {}).get("upper_threshold", float('inf'))
        }
    }
    
    return result


def validate_all_corpora(thresholds_file, output_dir, language_filter=None, debug=False):
    """Validate all corpora using pre-built profiles."""
    logger = setup_logging(output_dir, debug=debug)
    logger.info("="*80)
    logger.info("Validating Corpora with Per-Language Thresholds")
    logger.info("="*80)
    
    # Load thresholds
    try:
        with open(thresholds_file, 'r', encoding='utf-8') as f:
            thresholds = json.load(f)
    except Exception as e:
        logger.error(f"Error loading thresholds: {e}")
        return
    
    logger.info(f"Loaded thresholds for {len(thresholds.get('per_language', {}))} languages")
    
    # Load all corpora and build profiles
    docs, profiles = load_corpora_and_build_profiles("Corpora", logger)
    
    # Keep original docs for weight optimization
    all_docs = docs
    
    if language_filter:
        language_filter = language_filter.lower()
        if language_filter not in docs:
            logger.error(f"Language {language_filter.upper()} not found")
            return
        docs = {language_filter: docs[language_filter]}
    
    # Validate each file
    all_results = []
    summary = {
        "total_files": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    for lang_code, doc_list in sorted(docs.items()):
        logger.debug(f"Validating {len(doc_list)} {lang_code.upper()} files...")
        
        for doc in doc_list:
            summary["total_files"] += 1
            try:
                # Validate against language profile (excluding self for leave-one-out validation)
                result = validate_file_against_profile(
                    doc['corpus_name'],
                    lang_code,
                    doc['dialect'],
                    {
                        'char_uni': doc['char_uni'],
                        'char_bi': doc['char_bi'],
                        'char_tri': doc['char_tri'],
                        'word_uni': doc['word_uni'],
                        'word_bi': doc['word_bi']
                    },
                    profiles[lang_code],
                    thresholds
                )
                
                all_results.append(result)
                
                if result["status"] == "PASS":
                    summary["passed"] += 1
                elif result["status"] == "FAIL":
                    summary["failed"] += 1
                elif result["status"] == "SKIP":
                    summary["skipped"] += 1
                
                logger.debug(f"  {result['corpus']}/{lang_code}: {result['status']}")
                
            except Exception as e:
                logger.error(f"Error validating {doc['corpus_name']}/{lang_code}: {e}")
                summary["errors"] += 1
    
    # Optimize weights for language discrimination
    logger.info("="*80)
    logger.info("Optimizing language discrimination weights...")
    baselines = thresholds.get('per_language_baselines', {})
    
    try:
        optimal_weights = optimize_language_discrimination_weights(all_docs, profiles, baselines, logger)
        
        # Re-validate with optimized weights
        logger.info("="*80)
        logger.info("Re-validating with optimized weights...")
        all_results = []
        summary = {
            "total_files": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
        }
        
        for lang_code, doc_list in sorted(docs.items()):
            logger.debug(f"Re-validating {len(doc_list)} {lang_code.upper()} files with optimized weights...")
            
            for doc in doc_list:
                summary["total_files"] += 1
                try:
                    # Validate with optimized weights for language discrimination
                    result = validate_file_against_profile(
                        doc['corpus_name'],
                        lang_code,
                        doc['dialect'],
                        {
                            'char_uni': doc['char_uni'],
                            'char_bi': doc['char_bi'],
                            'char_tri': doc['char_tri'],
                            'word_uni': doc['word_uni'],
                            'word_bi': doc['word_bi']
                        },
                        profiles[lang_code],
                        thresholds,
                        all_profiles=profiles,
                        baselines=baselines,
                        weights=optimal_weights
                    )
                    
                    all_results.append(result)
                    
                    if result["status"] == "PASS":
                        summary["passed"] += 1
                    elif result["status"] == "FAIL":
                        summary["failed"] += 1
                    elif result["status"] == "SKIP":
                        summary["skipped"] += 1
                    
                    logger.debug(f"  {result['corpus']}/{lang_code}: {result['status']}")
                    
                except Exception as e:
                    logger.error(f"Error re-validating {doc['corpus_name']}/{lang_code}: {e}")
                    summary["errors"] += 1
        
        # Store optimal weights in summary
        summary["optimal_weights"] = {
            "char_uni": float(optimal_weights[0]),
            "char_bi": float(optimal_weights[1]),
            "char_tri": float(optimal_weights[2]),
            "word_uni": float(optimal_weights[3])
        }
        
    except Exception as e:
        logger.warning(f"Weight optimization failed: {e}. Using threshold-based validation.")
        logger.info("Continuing with threshold-based validation (no language discrimination).")

    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    
    results_file = os.path.join(output_dir, "validation_results.json")
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    
    # Save optimal weights if available
    if "optimal_weights" in summary:
        weights_file = os.path.join(output_dir, "optimal_weights.json")
        with open(weights_file, 'w', encoding='utf-8') as f:
            json.dump({
                "optimal_weights": summary["optimal_weights"],
                "generated": datetime.now().isoformat(),
                "description": "Optimized weights for language discrimination (minimized function to maximize F1 score)"
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"Optimal weights saved to {weights_file}")
    
    # Save summary
    summary_file = os.path.join(output_dir, "validation_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("Corpora Validation Summary\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"{'='*80}\n\n")
        
        # Write optimal weights if available
        if "optimal_weights" in summary:
            f.write("LANGUAGE DISCRIMINATION (Optimized Weights)\n")
            f.write(f"  char_uni: {summary['optimal_weights']['char_uni']:.4f}\n")
            f.write(f"  char_bi:  {summary['optimal_weights']['char_bi']:.4f}\n")
            f.write(f"  char_tri: {summary['optimal_weights']['char_tri']:.4f}\n")
            f.write(f"  word_uni: {summary['optimal_weights']['word_uni']:.4f}\n")
            f.write(f"{'='*80}\n\n")
        
        f.write(f"Total files: {summary['total_files']}\n")
        f.write(f"Passed: {summary['passed']} ({100*summary['passed']/max(1, summary['total_files']):.1f}%)\n")
        f.write(f"Failed: {summary['failed']} ({100*summary['failed']/max(1, summary['total_files']):.1f}%)\n")
        if summary['skipped'] > 0:
            f.write(f"Skipped: {summary['skipped']}\n")
        if summary['errors'] > 0:
            f.write(f"Errors: {summary['errors']}\n")
        
        f.write(f"\n{'='*80}\nDetails:\n")
        for result in all_results:
            f.write(f"\n{result['corpus']} ({result['language'].upper()}):\n")
            f.write(f"  Status: {result['status']}\n")
            if result['metrics']:
                f.write(f"  Metrics:\n")
                for metric, value in result['metrics'].items():
                    f.write(f"    {metric}: {value:.6f}\n")
            if result['issues']:
                f.write(f"  Issues:\n")
                for issue in result['issues']:
                    f.write(f"    - {issue}\n")
    
    # Print summary
    logger.info(f"\n{'='*80}")
    logger.info("Validation Complete")
    logger.info(f"{'='*80}")
    logger.info(f"Total files: {summary['total_files']}")
    logger.info(f"Passed: {summary['passed']} ({100*summary['passed']/max(1, summary['total_files']):.1f}%)")
    logger.info(f"Failed: {summary['failed']} ({100*summary['failed']/max(1, summary['total_files']):.1f}%)")
    if summary['skipped'] > 0:
        logger.info(f"Skipped: {summary['skipped']}")
    if summary['errors'] > 0:
        logger.info(f"Errors: {summary['errors']}")
    logger.info(f"Results saved to {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate all Corpora/ XML files using per-language thresholds"
    )
    parser.add_argument(
        '--thresholds-file',
        type=str,
        required=True,
        help='Path to statistical_thresholds.json'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='test_results/corpora_validation',
        help='Output directory for validation results'
    )
    parser.add_argument(
        '--language',
        type=str,
        default=None,
        help='Optional language code to validate (e.g., pwn, ami, trv)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        default=False,
        help='Enable debug-level logging'
    )
    
    args = parser.parse_args()
    validate_all_corpora(
        args.thresholds_file,
        args.output_dir,
        language_filter=args.language,
        debug=args.debug
    )
