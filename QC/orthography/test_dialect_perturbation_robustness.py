"""
Dialect-focused perturbation robustness test suite.

This script is based on test_character_perturbation_robustness.py, but switches
the focus from language discrimination to dialect discrimination within a
provided language.

Usage:
    python test_dialect_perturbation_robustness.py --language pwn

Example:
    python test_dialect_perturbation_robustness.py \
        --language pwn \
        --output-dir test_results/dialect_perturbation_tests \
        --sources ePark ILRDF_Dicts
"""

import argparse
import json
import logging
import os
import random
import re
import string
from collections import Counter
from datetime import datetime

import numpy as np
import pandas as pd

from orthography_compare import (
    cosine_similarity,
    euclidean,
    jaccard_similarity,
    kl_divergence,
    normalize_vector,
    overlap_coefficient,
)
from orthography_extract import (
    extract_orthographic_info,
    generate_corpus,
    remove_chinese_characters,
)


def setup_logging(log_dir):
    """Set up logging to file and console with UTF-8 encoding."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    stream = getattr(stream_handler, "stream", None)
    if stream is not None:
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[file_handler, stream_handler],
    )
    return logging.getLogger(__name__)


def get_language_code_to_name_map():
    """Map 3-letter language codes to full language names from dialects.csv."""
    return {
        "ami": "Amis",
        "tay": "Atayal",
        "bnn": "Bunun",
        "pwn": "Paiwan",
        "pyu": "Puyuma",
        "dru": "Rukai",
        "trv": "Seediq",
        "tao": "Yami",
        "kna": "Kanakanavu",
        "tsou": "Tsou",
        "sya": "Saisiyat",
        "ckv": "Kavalan",
        "xnb": "Saaroa",
        "ssa": "Sakizaya",
        "sai": "Siraya",
        "thk": "Thao",
    }


def resolve_language_name(lang_input):
    """Resolve language input (code or full name) to (full_name, code)."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        lang_names = sorted(dialect_csv["Language"].unique())
        code_to_name = get_language_code_to_name_map()

        if lang_input in lang_names:
            for code, name in code_to_name.items():
                if name == lang_input:
                    return lang_input, code

        lang_input_lower = lang_input.lower()
        for name in lang_names:
            if name.lower() == lang_input_lower:
                for code, mapped in code_to_name.items():
                    if mapped == name:
                        return name, code

        if lang_input_lower in code_to_name:
            return code_to_name[lang_input_lower], lang_input_lower

        return None, None
    except Exception:
        return None, None


def get_available_dialects(language_full_name):
    """Get available dialects for the specified language."""
    try:
        dialect_csv = pd.read_csv("dialects.csv")
        lang_data = dialect_csv[dialect_csv["Language"] == language_full_name]
        if lang_data.empty:
            return []
        return sorted(lang_data["Official"].dropna().unique().tolist())
    except Exception:
        return []


def char_tokenize(corpus):
    """Tokenize corpus into non-whitespace characters."""
    return [char for char in corpus if not char.isspace()]


def word_tokenize(corpus, lang_code):
    """Tokenize corpus into words using language orthography when available."""
    try:
        lang_ortho_table = pd.read_csv(f"Orthographies/Ortho113/{lang_code}.tsv", sep="\t")
        special_chars = set(str(char) for char in lang_ortho_table["letter"].to_list() if pd.notna(char))
        regex = r"[\w" + "".join(re.escape(char) for char in special_chars) + r"]+"
        return re.findall(regex, corpus)
    except FileNotFoundError:
        return re.findall(r"\w+", corpus)
    except Exception:
        return re.findall(r"\w+", corpus)


def compute_reference_target_metrics(ref_tokens, target_tokens, gram_length, laplace=True):
    """Compute n-gram metrics between reference and target token sequences."""

    def get_ngrams(token_list):
        ngrams = [tuple(token_list[i : i + gram_length]) for i in range(len(token_list) - gram_length + 1)]
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

    ref_freq_vector = np.array([(ref_ngrams[n] + (1 if laplace else 0)) for n in all_ngrams], dtype=float)
    target_freq_vector = np.array([(target_ngrams[n] + (1 if laplace else 0)) for n in all_ngrams], dtype=float)

    ref_freq_vector = normalize_vector(ref_freq_vector)
    target_freq_vector = normalize_vector(target_freq_vector)

    return {
        "n": gram_length,
        "jaccard_similarity": float(jaccard_similarity(ref_ngrams_set, target_ngrams_set)),
        "overlap_coefficient": float(overlap_coefficient(ref_ngrams_set, target_ngrams_set)),
        "cosine_similarity": float(cosine_similarity(np.array([ref_freq_vector]), np.array([target_freq_vector]))[0][0]),
        "euclidean_distance": float(euclidean(ref_freq_vector, target_freq_vector)),
        "kl_divergence": float(kl_divergence(ref_freq_vector, target_freq_vector)),
        "ref_unique_ngram_count": len(ref_ngrams_set),
        "target_unique_ngram_count": len(target_ngrams_set),
    }


def analyze_corpus_partition(ref_corpus, target_corpus, lang_code, max_gram_length=3):
    """Analyze reference vs target at character and word levels."""
    ref_char_tokens = char_tokenize(ref_corpus)
    target_char_tokens = char_tokenize(target_corpus)
    ref_word_tokens = word_tokenize(ref_corpus, lang_code)
    target_word_tokens = word_tokenize(target_corpus, lang_code)

    results = {"character": {}, "word": {}}
    for gram_length in range(1, max_gram_length + 1):
        results["character"][gram_length] = compute_reference_target_metrics(
            ref_char_tokens, target_char_tokens, gram_length
        )
        results["word"][gram_length] = compute_reference_target_metrics(
            ref_word_tokens, target_word_tokens, gram_length
        )

    return results


def compute_metric_deltas(baseline_metrics, perturbed_metrics, max_gram_length=3):
    """Compute absolute deltas for cosine similarity and KL divergence."""
    deltas = {"character": {}, "word": {}}
    for level in ["character", "word"]:
        for gram_length in range(1, max_gram_length + 1):
            baseline = baseline_metrics[level][gram_length]
            perturbed = perturbed_metrics[level][gram_length]
            deltas[level][gram_length] = {
                "cosine_similarity": float(abs(perturbed["cosine_similarity"] - baseline["cosine_similarity"])),
                "kl_divergence": float(abs(perturbed["kl_divergence"] - baseline["kl_divergence"])),
            }
    return deltas


def build_dialect_corpus_text(lang_full_name, dialect, sources, logger):
    """Build combined corpus text for one language/dialect from all sources."""
    corpus_text = ""
    sources_found = []
    for source in sources:
        corpus_path = f"Corpora/{source}"
        if not os.path.exists(corpus_path):
            continue
        try:
            corpus = generate_corpus(lang_full_name, corpus_path, "standard", by_dialect=True, phonetic=False)
            if dialect in corpus:
                corpus_text += corpus[dialect]
                sources_found.append(source)
        except Exception as exc:
            logger.warning(f"Error generating corpus from {source}: {exc}")

    return corpus_text, sources_found


def test_dialect(
    lang_full_name,
    lang_code,
    dialect,
    sources,
    output_dir,
    test_ratio=0.2,
    laplace=True,
    num_swaps=5,
):
    """Run perturbation test for a single dialect."""
    logger = logging.getLogger(__name__)
    corpus_text, sources_found = build_dialect_corpus_text(lang_full_name, dialect, sources, logger)

    if not corpus_text:
        logger.error(f"No corpus found for {lang_code}/{dialect}")
        return None

    corpus_text = remove_chinese_characters(corpus_text)
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", corpus_text) if s and s.strip()]

    if len(sentences) < 2:
        logger.warning(f"Insufficient sentences for {lang_code}/{dialect}")
        return None

    rng = random.Random(42)
    num_target = max(1, int(len(sentences) * test_ratio))
    target_indices = set(rng.sample(range(len(sentences)), num_target))

    ref_text = "".join(s for i, s in enumerate(sentences) if i not in target_indices)
    target_text = "".join(s for i, s in enumerate(sentences) if i in target_indices)

    baseline_metrics = analyze_corpus_partition(ref_text, target_text, lang_code)
    target_char_info = extract_orthographic_info(target_text)

    if not target_char_info["character_frequency"]:
        logger.warning(f"No character frequencies for {lang_code}/{dialect}")
        return None

    available_chars = sorted(set(target_char_info["unique_characters"]))
    if not available_chars:
        logger.warning(f"No available characters for {lang_code}/{dialect}")
        return None

    max_freq_char = max(target_char_info["character_frequency"].items(), key=lambda x: x[1])[0]
    max_freq_count = target_char_info["character_frequency"][max_freq_char]

    alternate_chars = [
        ch
        for ch in available_chars
        if ch not in set(string.punctuation) and ch != max_freq_char
    ]
    if not alternate_chars:
        alternate_chars = [ch for ch in available_chars if ch != max_freq_char]
    if not alternate_chars:
        logger.warning(f"No alternate characters for {lang_code}/{dialect}")
        return None

    rng.shuffle(alternate_chars)
    chosen_chars = alternate_chars[: min(num_swaps, len(alternate_chars))]

    all_char_deltas = []
    all_char_perturbations = []
    for idx, random_char in enumerate(chosen_chars, start=1):
        swapped_target_text = target_text.translate(str.maketrans(max_freq_char, random_char))
        perturbed_metrics = analyze_corpus_partition(ref_text, swapped_target_text, lang_code)
        deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
        all_char_deltas.append(deltas)
        all_char_perturbations.append(
            {
                "swap_number": idx,
                "max_frequency_character": max_freq_char,
                "character_frequency": max_freq_count,
                "swapped_with_character": random_char,
                "metric_deltas": deltas,
            }
        )

    words = re.findall(r"\b\w+\b", target_text)
    all_word_deltas = []
    all_word_perturbations = []

    if len(words) < 2:
        all_word_deltas = [delta for delta in all_char_deltas]
    else:
        word_freq = Counter(words)
        max_freq_word = max(word_freq.items(), key=lambda x: x[1])[0]
        max_freq_word_count = word_freq[max_freq_word]
        alternate_words = sorted(set(words) - {max_freq_word})
        rng.shuffle(alternate_words)
        chosen_words = alternate_words[: min(num_swaps, len(alternate_words))]

        if not chosen_words:
            all_word_deltas = [delta for delta in all_char_deltas]
        else:
            for idx, random_word in enumerate(chosen_words, start=1):
                placeholder = f"__PLACEHOLDER_{idx}__"
                swapped_target_text = target_text
                swapped_target_text = re.sub(r"\b" + re.escape(max_freq_word) + r"\b", placeholder, swapped_target_text)
                swapped_target_text = re.sub(r"\b" + re.escape(random_word) + r"\b", max_freq_word, swapped_target_text)
                swapped_target_text = swapped_target_text.replace(placeholder, random_word)

                perturbed_metrics = analyze_corpus_partition(ref_text, swapped_target_text, lang_code)
                deltas = compute_metric_deltas(baseline_metrics, perturbed_metrics)
                all_word_deltas.append(deltas)
                all_word_perturbations.append(
                    {
                        "swap_number": idx,
                        "max_frequency_word": max_freq_word,
                        "word_frequency": max_freq_word_count,
                        "swapped_with_word": random_word,
                        "metric_deltas": deltas,
                    }
                )

    if not all_char_deltas or not all_word_deltas:
        return None

    averaged_char = {"character": {}}
    for gram_length in all_char_deltas[0]["character"].keys():
        averaged_char["character"][gram_length] = {
            "cosine_similarity": float(np.mean([d["character"][gram_length]["cosine_similarity"] for d in all_char_deltas])),
            "kl_divergence": float(np.mean([d["character"][gram_length]["kl_divergence"] for d in all_char_deltas])),
        }

    averaged_word = {"word": {}}
    for gram_length in all_word_deltas[0]["word"].keys():
        averaged_word["word"][gram_length] = {
            "cosine_similarity": float(np.mean([d["word"][gram_length]["cosine_similarity"] for d in all_word_deltas])),
            "kl_divergence": float(np.mean([d["word"][gram_length]["kl_divergence"] for d in all_word_deltas])),
        }

    return {
        "language": lang_code,
        "language_full_name": lang_full_name,
        "dialect": dialect,
        "sources": sources_found,
        "corpus_stats": {
            "total_sentences": len(sentences),
            "reference_sentences": len([s for i, s in enumerate(sentences) if i not in target_indices]),
            "target_sentences": len([s for i, s in enumerate(sentences) if i in target_indices]),
            "test_ratio": test_ratio,
            "total_characters": len(corpus_text),
            "unique_characters": len(target_char_info["unique_characters"]),
        },
        "perturbation": {
            "num_swaps_requested": num_swaps,
            "char_swaps_performed": len(all_char_perturbations),
            "word_swaps_performed": len(all_word_perturbations),
        },
        "baseline_metrics": baseline_metrics,
        "character_perturbations": all_char_perturbations,
        "word_perturbations": all_word_perturbations,
        "metric_deltas_averaged": {**averaged_char, **averaged_word},
        "timestamp": datetime.now().isoformat(),
    }


def compute_dialect_thresholds(all_results, epsilon=0.1):
    """Compute per-dialect thresholds (mean +/- epsilon) for one language."""
    if not all_results:
        return None

    per_dialect_metrics = {}
    per_dialect_baselines = {}

    for result in all_results:
        dialect = result["dialect"]
        per_dialect_metrics.setdefault(
            dialect,
            {
                "character_kl_1gram": [],
                "character_kl_2gram": [],
                "character_kl_3gram": [],
                "word_kl_1gram": [],
                "word_kl_2gram": [],
            },
        )
        per_dialect_baselines.setdefault(
            dialect,
            {
                "character_1gram_baseline_kl": [],
                "character_2gram_baseline_kl": [],
                "character_3gram_baseline_kl": [],
                "word_1gram_baseline_kl": [],
                "word_2gram_baseline_kl": [],
            },
        )

        deltas = result.get("metric_deltas_averaged", {})
        baseline = result.get("baseline_metrics", {})

        for gram in [1, 2, 3]:
            if gram in deltas.get("character", {}):
                per_dialect_metrics[dialect][f"character_kl_{gram}gram"].append(
                    deltas["character"][gram].get("kl_divergence", 0.0)
                )
            if gram in baseline.get("character", {}):
                per_dialect_baselines[dialect][f"character_{gram}gram_baseline_kl"].append(
                    baseline["character"][gram].get("kl_divergence", 0.0)
                )

        for gram in [1, 2]:
            if gram in deltas.get("word", {}):
                per_dialect_metrics[dialect][f"word_kl_{gram}gram"].append(
                    deltas["word"][gram].get("kl_divergence", 0.0)
                )
            if gram in baseline.get("word", {}):
                per_dialect_baselines[dialect][f"word_{gram}gram_baseline_kl"].append(
                    baseline["word"][gram].get("kl_divergence", 0.0)
                )

    eps_minimum = 1e-3
    thresholds = {"epsilon": float(epsilon), "per_dialect": {}, "per_dialect_baselines": {}}

    for dialect, metrics in per_dialect_metrics.items():
        thresholds["per_dialect"][dialect] = {}
        for metric_name, values in metrics.items():
            if not values:
                continue
            mean = float(np.mean(values))
            std = float(np.std(values))
            lower = float(max(eps_minimum, mean - epsilon))
            upper = float(mean + epsilon)
            thresholds["per_dialect"][dialect][metric_name] = {
                "mean": mean,
                "std": std,
                "epsilon": float(epsilon),
                "lower_threshold": lower,
                "upper_threshold": upper,
                "n_samples": len(values),
            }

    for dialect, baselines in per_dialect_baselines.items():
        thresholds["per_dialect_baselines"][dialect] = {}
        for name, values in baselines.items():
            if values:
                thresholds["per_dialect_baselines"][dialect][name] = float(np.mean(values))

    return thresholds


def validate_dialect_integrity(result, thresholds):
    """Validate one dialect result against per-dialect thresholds."""
    dialect = result["dialect"]
    metric_deltas = result.get("metric_deltas_averaged", {})
    threshold_info = thresholds.get("per_dialect", {}).get(dialect, {})

    check = {
        "dialect": dialect,
        "status": "UNKNOWN",
        "message": "",
        "metrics": {},
    }

    if not threshold_info:
        check["status"] = "SKIP"
        check["message"] = f"No thresholds found for dialect {dialect}"
        return check

    pass_all = True
    warn_any = False

    for gram in [1, 2, 3]:
        key = f"character_kl_{gram}gram"
        value = metric_deltas.get("character", {}).get(gram, {}).get("kl_divergence", 0.0)
        upper = threshold_info.get(key, {}).get("upper_threshold", float("inf"))
        lower = threshold_info.get(key, {}).get("lower_threshold", 0.0)
        within_upper = value <= upper
        below_lower = value <= lower

        check["metrics"][key] = {
            "value": float(value),
            "lower_threshold": float(lower),
            "upper_threshold": float(upper),
            "within_upper": bool(within_upper),
        }

        if not within_upper:
            pass_all = False
        if within_upper and not below_lower:
            warn_any = True

    if pass_all and not warn_any:
        check["status"] = "PASS"
        check["message"] = "All character KL deltas are below lower thresholds"
    elif pass_all:
        check["status"] = "WARN"
        check["message"] = "All character KL deltas are within upper bounds"
    else:
        check["status"] = "FAIL"
        check["message"] = "At least one character KL delta exceeded an upper threshold"

    return check


def run_cross_dialect_discrimination(results_by_dialect, thresholds):
    """Check whether other dialects exceed target dialect upper thresholds."""
    checks = []
    dialects = sorted(results_by_dialect.keys())

    for target_dialect in dialects:
        target_thresh = thresholds.get("per_dialect", {}).get(target_dialect, {})
        if not target_thresh:
            continue

        target_upper = target_thresh.get("character_kl_1gram", {}).get("upper_threshold", float("inf"))

        for other_dialect in dialects:
            if other_dialect == target_dialect:
                continue
            other_result = results_by_dialect[other_dialect]
            other_kl = (
                other_result.get("metric_deltas_averaged", {})
                .get("character", {})
                .get(1, {})
                .get("kl_divergence", 0.0)
            )

            if other_kl > target_upper:
                status = "PASS"
                message = f"{other_dialect} exceeds {target_dialect} upper threshold ({other_kl:.6f} > {target_upper:.6f})"
            else:
                status = "FAIL"
                message = f"{other_dialect} does not exceed {target_dialect} upper threshold ({other_kl:.6f} <= {target_upper:.6f})"

            checks.append(
                {
                    "target_dialect": target_dialect,
                    "test_dialect": other_dialect,
                    "status": status,
                    "message": message,
                    "character_kl_1gram": float(other_kl),
                    "target_upper_threshold": float(target_upper),
                }
            )

    return checks


def main(args):
    output_dir = args.output_dir or "test_results/dialect_perturbation_tests"
    os.makedirs(output_dir, exist_ok=True)
    logger = setup_logging(output_dir)

    lang_full_name, lang_code = resolve_language_name(args.language)
    if not lang_full_name or not lang_code:
        logger.error(f"Could not resolve language: {args.language}")
        return

    dialects = args.dialects if args.dialects else get_available_dialects(lang_full_name)
    if not dialects:
        logger.error(f"No dialects found for language {lang_full_name}")
        return

    sources = [s if s.endswith("/") else s + "/" for s in (args.sources or ["ePark/", "ILRDF_Dicts/", "Paiwan_Stories/", "NTUFormosanCorpus/"])]

    logger.info("=" * 80)
    logger.info("Dialect Perturbation Robustness Test Suite")
    logger.info("=" * 80)
    logger.info(f"Language: {lang_full_name} ({lang_code})")
    logger.info(f"Dialects: {dialects}")
    logger.info(f"Sources: {sources}")
    logger.info(f"Number of swaps: {args.num_swaps}")
    logger.info(f"Epsilon: {args.epsilon}")

    all_results = []
    results_by_dialect = {}
    validation_checks = []

    thresholds = None
    if args.load_thresholds:
        try:
            with open(args.load_thresholds, "r", encoding="utf-8") as f:
                thresholds = json.load(f)
            logger.info(f"Loaded thresholds from {args.load_thresholds}")
        except Exception as exc:
            logger.error(f"Failed to load thresholds: {exc}")
            return

    if not thresholds:
        for dialect in dialects:
            logger.info(f"Testing {lang_code}/{dialect}...")
            result = test_dialect(
                lang_full_name,
                lang_code,
                dialect,
                sources,
                output_dir,
                test_ratio=args.test_ratio,
                laplace=True,
                num_swaps=args.num_swaps,
            )
            if result:
                all_results.append(result)
                results_by_dialect[dialect] = result

                result_file = os.path.join(output_dir, f"{lang_code}_{dialect}_results.json")
                with open(result_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
            else:
                logger.warning(f"Failed to produce result for {lang_code}/{dialect}")

        thresholds = compute_dialect_thresholds(all_results, epsilon=args.epsilon)
        if not thresholds:
            logger.error("Could not compute thresholds")
            return

    thresholds["language"] = lang_code
    thresholds["language_full_name"] = lang_full_name

    if not results_by_dialect and all_results:
        results_by_dialect = {r["dialect"]: r for r in all_results}

    for result in all_results:
        validation_checks.append(validate_dialect_integrity(result, thresholds))

    cross_dialect_checks = run_cross_dialect_discrimination(results_by_dialect, thresholds)

    all_results_file = os.path.join(output_dir, "all_results.json")
    with open(all_results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    validation_file = os.path.join(output_dir, "validation_results.json")
    with open(validation_file, "w", encoding="utf-8") as f:
        json.dump(validation_checks, f, indent=2, ensure_ascii=False)

    cross_file = os.path.join(output_dir, "cross_dialect_discrimination.json")
    with open(cross_file, "w", encoding="utf-8") as f:
        json.dump(cross_dialect_checks, f, indent=2, ensure_ascii=False)

    thresholds_file = os.path.join(output_dir, "dialect_statistical_thresholds.json")
    with open(thresholds_file, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2, ensure_ascii=False)

    pass_count = len([c for c in validation_checks if c.get("status") == "PASS"])
    warn_count = len([c for c in validation_checks if c.get("status") == "WARN"])
    fail_count = len([c for c in validation_checks if c.get("status") == "FAIL"])

    discrim_pass = len([c for c in cross_dialect_checks if c.get("status") == "PASS"])
    discrim_fail = len([c for c in cross_dialect_checks if c.get("status") == "FAIL"])

    summary_file = os.path.join(output_dir, "summary_report.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("Dialect Perturbation Robustness Test Suite - Summary Report\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Language: {lang_full_name} ({lang_code})\n")
        f.write(f"{'=' * 80}\n\n")
        f.write(f"Dialects tested: {len(all_results)}\n")
        f.write(f"Validation PASS: {pass_count}\n")
        f.write(f"Validation WARN: {warn_count}\n")
        f.write(f"Validation FAIL: {fail_count}\n\n")
        f.write(f"Cross-dialect discrimination PASS: {discrim_pass}\n")
        f.write(f"Cross-dialect discrimination FAIL: {discrim_fail}\n")

    logger.info("=" * 80)
    logger.info(f"Complete. Results saved to {output_dir}")
    logger.info(f"Dialects tested: {len(all_results)}")
    logger.info(f"Validation PASS/WARN/FAIL: {pass_count}/{warn_count}/{fail_count}")
    logger.info(f"Cross-dialect PASS/FAIL: {discrim_pass}/{discrim_fail}")
    logger.info("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dialect-focused perturbation robustness test suite for a single language"
    )
    parser.add_argument(
        "--language",
        type=str,
        required=True,
        help="Language to test (code or full name, e.g., pwn or Paiwan)",
    )
    parser.add_argument(
        "--dialects",
        type=str,
        nargs="+",
        help="Optional subset of dialects to test (default: all official dialects for the language)",
    )
    parser.add_argument(
        "--sources",
        type=str,
        nargs="+",
        help="Corpus sources (default: ePark ILRDF_Dicts Paiwan_Stories NTUFormosanCorpus)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_results/dialect_perturbation_tests",
        help="Output directory for test results",
    )
    parser.add_argument(
        "--test-ratio",
        type=float,
        default=0.2,
        help="Fraction of corpus to use as target corpus (default: 0.2)",
    )
    parser.add_argument(
        "--num-swaps",
        type=int,
        default=5,
        help="Number of swaps per dialect perturbation test",
    )
    parser.add_argument(
        "--epsilon",
        type=float,
        default=0.1,
        help="Epsilon for per-dialect threshold calculation (mean +/- epsilon)",
    )
    parser.add_argument(
        "--load-thresholds",
        type=str,
        help="Path to pre-computed dialect thresholds JSON file",
    )

    main(parser.parse_args())
