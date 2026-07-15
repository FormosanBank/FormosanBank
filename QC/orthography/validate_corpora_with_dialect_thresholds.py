"""
Validate Corpora XML files using per-dialect thresholds for a provided language.

This script is based on validate_corpora_with_thresholds.py, but performs
dialect-focused validation and discrimination within one language.

Usage:
    python validate_corpora_with_dialect_thresholds.py \
        --thresholds-file test_results/dialect_perturbation_tests/dialect_statistical_thresholds.json \
        --language pwn
"""

import argparse
import json
import logging
import math
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import numpy as np
from scipy.optimize import minimize


def setup_logging(log_dir, debug=False):
    """Set up logging to file and console with UTF-8 encoding."""
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"validation_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    stream_handler = logging.StreamHandler()
    stream = getattr(stream_handler, "stream", None)
    if stream is not None:
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except AttributeError:
            pass

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[file_handler, stream_handler],
    )
    return logging.getLogger(__name__)


def extract_standard_text(root):
    """Extract sentence-level standard FORM text from XML root."""
    parts = [
        f.text.strip()
        for s in root.findall(".//S")
        for f in s.findall("./FORM[@kindOf='standard']")
        if f.text and f.text.strip()
    ]
    return " ".join(parts).strip()


def normalize_lang_code(raw_lang):
    """Normalize xml:lang to a primary 3-letter code."""
    lang_code = (raw_lang or "").strip().lower()
    if not lang_code:
        return ""
    if len(lang_code) > 3:
        lang_code = lang_code.split("-")[0]
    return lang_code


def extract_counts(text):
    """Extract char and word n-gram counts."""
    chars = [c for c in text if not c.isspace()]
    char_uni = Counter(chars)
    char_bi = Counter(f"{chars[i]} {chars[i + 1]}" for i in range(len(chars) - 1))
    char_tri = Counter(f"{chars[i]} {chars[i + 1]} {chars[i + 2]}" for i in range(len(chars) - 2))

    words = re.findall(r"\w+", text.casefold())
    word_uni = Counter(words)
    word_bi = Counter(f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1))

    return char_uni, char_bi, char_tri, word_uni, word_bi


def kl_divergence(counts, profile_counts, profile_total, vocab_size, smoothing=1.0):
    """Compute KL(counts || profile) with additive smoothing."""
    n = sum(counts.values())
    if n == 0:
        return 0.0
    denom = profile_total + smoothing * max(vocab_size, 1)
    kl = 0.0
    for item, c in counts.items():
        p = (profile_counts.get(item, 0) + smoothing) / denom
        q = c / n
        if q > 0 and p > 0:
            kl += q * math.log(q / p)
    return kl


def load_language_docs_and_build_dialect_profiles(corpora_path, language_code, logger):
    """Load docs for one language and build aggregated profiles by dialect."""
    docs = {}
    profiles = {}

    xml_files = list(Path(corpora_path).rglob("*.xml"))
    logger.info(f"Found {len(xml_files)} XML files total")

    for xml_file in sorted(xml_files):
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            if root.tag != "TEXT":
                continue

            raw_lang = root.get("{http://www.w3.org/XML/1998/namespace}lang") or root.get("lang")
            lang_code = normalize_lang_code(raw_lang)
            if lang_code != language_code:
                continue

            dialect = root.get("dialect", "default")
            corpus_name = xml_file.stem
            text = extract_standard_text(root)
            if not text:
                continue

            char_uni, char_bi, char_tri, word_uni, word_bi = extract_counts(text)
            docs.setdefault(dialect, []).append(
                {
                    "corpus_name": corpus_name,
                    "language": lang_code,
                    "dialect": dialect,
                    "text": text,
                    "char_uni": char_uni,
                    "char_bi": char_bi,
                    "char_tri": char_tri,
                    "word_uni": word_uni,
                    "word_bi": word_bi,
                }
            )
        except Exception as exc:
            logger.debug(f"Error loading {xml_file}: {exc}")

    for dialect, doc_list in docs.items():
        agg_char_uni = Counter()
        agg_char_bi = Counter()
        agg_char_tri = Counter()
        agg_word_uni = Counter()
        agg_word_bi = Counter()

        for doc in doc_list:
            agg_char_uni.update(doc["char_uni"])
            agg_char_bi.update(doc["char_bi"])
            agg_char_tri.update(doc["char_tri"])
            agg_word_uni.update(doc["word_uni"])
            agg_word_bi.update(doc["word_bi"])

        profiles[dialect] = {
            "char_uni": agg_char_uni,
            "char_bi": agg_char_bi,
            "char_tri": agg_char_tri,
            "word_uni": agg_word_uni,
            "word_bi": agg_word_bi,
            "char_uni_total": sum(agg_char_uni.values()),
            "char_bi_total": sum(agg_char_bi.values()),
            "char_tri_total": sum(agg_char_tri.values()),
            "word_uni_total": sum(agg_word_uni.values()),
            "word_bi_total": sum(agg_word_bi.values()),
            "char_uni_vocab": len(agg_char_uni),
            "char_bi_vocab": len(agg_char_bi),
            "char_tri_vocab": len(agg_char_tri),
            "word_uni_vocab": len(agg_word_uni),
            "word_bi_vocab": len(agg_word_bi),
        }

    total_docs = sum(len(v) for v in docs.values())
    logger.info(f"Loaded {total_docs} documents across {len(docs)} dialects for language {language_code.upper()}")
    return docs, profiles


def compute_dialect_scores(doc_features, profiles, baselines, weights):
    """Compute weighted dialect scores (lower is more likely)."""
    scores = {}
    for dialect, profile in profiles.items():
        char_uni_kl = kl_divergence(doc_features["char_uni"], profile["char_uni"], profile["char_uni_total"], profile["char_uni_vocab"])
        char_bi_kl = kl_divergence(doc_features["char_bi"], profile["char_bi"], profile["char_bi_total"], profile["char_bi_vocab"])
        char_tri_kl = kl_divergence(doc_features["char_tri"], profile["char_tri"], profile["char_tri_total"], profile["char_tri_vocab"])
        word_uni_kl = kl_divergence(doc_features["word_uni"], profile["word_uni"], profile["word_uni_total"], profile["word_uni_vocab"])

        baseline = baselines.get(dialect, {})
        char_uni_delta = char_uni_kl - baseline.get("character_1gram_baseline_kl", 0.0)
        char_bi_delta = char_bi_kl - baseline.get("character_2gram_baseline_kl", 0.0)
        char_tri_delta = char_tri_kl - baseline.get("character_3gram_baseline_kl", 0.0)
        word_uni_delta = word_uni_kl - baseline.get("word_1gram_baseline_kl", 0.0)

        weighted = (
            weights[0] * char_uni_delta
            + weights[1] * char_bi_delta
            + weights[2] * char_tri_delta
            + weights[3] * word_uni_delta
        )
        scores[dialect] = weighted

    return scores


def optimize_dialect_discrimination_weights(docs, profiles, baselines, logger):
    """Optimize metric weights to maximize dialect prediction F1."""
    logger.info("Optimizing weights for dialect discrimination...")

    data = []
    for true_dialect, doc_list in docs.items():
        for doc in doc_list:
            data.append(
                (
                    true_dialect,
                    {
                        "char_uni": doc["char_uni"],
                        "char_bi": doc["char_bi"],
                        "char_tri": doc["char_tri"],
                        "word_uni": doc["word_uni"],
                        "word_bi": doc["word_bi"],
                    },
                )
            )

    def f1_loss(weights):
        weights = np.abs(weights) + 1e-6
        tp = 0
        fp = 0
        fn = 0

        for true_dialect, doc_features in data:
            scores = compute_dialect_scores(doc_features, profiles, baselines, weights)
            predicted = min(scores.items(), key=lambda item: item[1])[0]
            if predicted == true_dialect:
                tp += 1
            else:
                fp += 1
                fn += 1

        if tp + fp == 0 or tp + fn == 0:
            return 0.0

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        return -f1

    initial = np.random.dirichlet(np.ones(4))
    result = minimize(f1_loss, initial, method="Nelder-Mead", options={"maxiter": 1e4, "xatol": 1e-6})
    optimal = np.abs(result.x) + 1e-6
    optimal = optimal / np.sum(optimal)

    logger.info(
        "Optimal weights: char_uni=%.4f, char_bi=%.4f, char_tri=%.4f, word_uni=%.4f",
        optimal[0],
        optimal[1],
        optimal[2],
        optimal[3],
    )
    logger.info("Best dialect F1: %.4f", -result.fun)
    return optimal


def validate_file_against_dialect_profile(
    doc,
    profile,
    thresholds,
    all_profiles=None,
    baselines=None,
    weights=None,
):
    """Validate one document against dialect profile and optional discrimination."""
    language = doc["language"]
    dialect = doc["dialect"]
    doc_features = {
        "char_uni": doc["char_uni"],
        "char_bi": doc["char_bi"],
        "char_tri": doc["char_tri"],
        "word_uni": doc["word_uni"],
        "word_bi": doc["word_bi"],
    }

    result = {
        "corpus": doc["corpus_name"],
        "language": language,
        "dialect": dialect,
        "status": "UNKNOWN",
        "metrics": {},
        "metric_deltas": {},
        "issues": [],
        "dialect_scores": {},
    }

    dialect_thresholds = thresholds.get("per_dialect", {}).get(dialect, {})
    dialect_baselines = thresholds.get("per_dialect_baselines", {}).get(dialect, {})

    if not dialect_thresholds:
        result["status"] = "SKIP"
        result["issues"].append(f"No thresholds for dialect {dialect}")
        return result

    char_uni_kl = kl_divergence(doc_features["char_uni"], profile["char_uni"], profile["char_uni_total"], profile["char_uni_vocab"])
    char_bi_kl = kl_divergence(doc_features["char_bi"], profile["char_bi"], profile["char_bi_total"], profile["char_bi_vocab"])
    char_tri_kl = kl_divergence(doc_features["char_tri"], profile["char_tri"], profile["char_tri_total"], profile["char_tri_vocab"])
    word_uni_kl = kl_divergence(doc_features["word_uni"], profile["word_uni"], profile["word_uni_total"], profile["word_uni_vocab"])
    word_bi_kl = kl_divergence(doc_features["word_bi"], profile["word_bi"], profile["word_bi_total"], profile["word_bi_vocab"])

    char_uni_delta = char_uni_kl - dialect_baselines.get("character_1gram_baseline_kl", char_uni_kl)
    char_bi_delta = char_bi_kl - dialect_baselines.get("character_2gram_baseline_kl", char_bi_kl)
    char_tri_delta = char_tri_kl - dialect_baselines.get("character_3gram_baseline_kl", char_tri_kl)
    word_uni_delta = word_uni_kl - dialect_baselines.get("word_1gram_baseline_kl", word_uni_kl)
    word_bi_delta = word_bi_kl - dialect_baselines.get("word_2gram_baseline_kl", word_bi_kl)

    result["metrics"] = {
        "char_uni_kl": float(char_uni_kl),
        "char_bi_kl": float(char_bi_kl),
        "char_tri_kl": float(char_tri_kl),
        "word_uni_kl": float(word_uni_kl),
        "word_bi_kl": float(word_bi_kl),
    }
    result["metric_deltas"] = {
        "char_uni_delta": float(char_uni_delta),
        "char_bi_delta": float(char_bi_delta),
        "char_tri_delta": float(char_tri_delta),
        "word_uni_delta": float(word_uni_delta),
        "word_bi_delta": float(word_bi_delta),
    }

    char_uni_passes = char_uni_delta < dialect_thresholds.get("character_kl_1gram", {}).get("upper_threshold", float("inf"))
    char_bi_passes = char_bi_delta < dialect_thresholds.get("character_kl_2gram", {}).get("upper_threshold", float("inf"))
    char_tri_passes = char_tri_delta < dialect_thresholds.get("character_kl_3gram", {}).get("upper_threshold", float("inf"))

    if not char_uni_passes:
        result["issues"].append("char_uni_delta exceeded dialect upper threshold")
    if not char_bi_passes:
        result["issues"].append("char_bi_delta exceeded dialect upper threshold")
    if not char_tri_passes:
        result["issues"].append("char_tri_delta exceeded dialect upper threshold")

    if weights is not None and all_profiles is not None and baselines is not None:
        scores = compute_dialect_scores(doc_features, all_profiles, baselines, weights)
        result["dialect_scores"] = {k: float(v) for k, v in scores.items()}
        predicted_dialect = min(scores.items(), key=lambda item: item[1])[0]
        result["predicted_dialect"] = predicted_dialect
        result["predicted_score"] = float(scores[predicted_dialect])

        if predicted_dialect == dialect:
            result["status"] = "PASS"
        else:
            result["status"] = "FAIL"
            result["issues"].append(f"Dialect mismatch: predicted {predicted_dialect}, true {dialect}")
    else:
        if char_uni_passes and char_bi_passes and char_tri_passes:
            result["status"] = "PASS"
        elif char_bi_passes or char_tri_passes:
            result["status"] = "UNKNOWN"
        else:
            result["status"] = "FAIL"

    return result


def validate_all_corpora(thresholds_file, output_dir, language_filter, dialect_filter=None, debug=False):
    """Validate all corpora for one language using dialect thresholds."""
    logger = setup_logging(output_dir, debug=debug)
    logger.info("=" * 80)
    logger.info("Validating Corpora with Per-Dialect Thresholds")
    logger.info("=" * 80)

    try:
        with open(thresholds_file, "r", encoding="utf-8") as f:
            thresholds = json.load(f)
    except Exception as exc:
        logger.error(f"Error loading thresholds: {exc}")
        return

    threshold_lang = thresholds.get("language")
    if threshold_lang and threshold_lang.lower() != language_filter.lower():
        logger.warning(
            "Threshold language (%s) differs from requested language (%s)",
            threshold_lang,
            language_filter,
        )

    docs, profiles = load_language_docs_and_build_dialect_profiles("Corpora", language_filter.lower(), logger)
    if not docs:
        logger.error(f"No documents found for language {language_filter.upper()}")
        return

    if dialect_filter:
        if dialect_filter not in docs:
            logger.error(f"Dialect {dialect_filter} not found for language {language_filter.upper()}")
            return
        docs = {dialect_filter: docs[dialect_filter]}

    all_docs = docs
    all_results = []
    summary: dict[str, Any] = {"total_files": 0, "passed": 0, "failed": 0, "unknown": 0, "skipped": 0, "errors": 0}

    for dialect, doc_list in sorted(docs.items()):
        for doc in doc_list:
            summary["total_files"] += 1
            try:
                result = validate_file_against_dialect_profile(doc, profiles[dialect], thresholds)
                all_results.append(result)
                status = result["status"]
                if status == "PASS":
                    summary["passed"] += 1
                elif status == "FAIL":
                    summary["failed"] += 1
                elif status == "UNKNOWN":
                    summary["unknown"] += 1
                elif status == "SKIP":
                    summary["skipped"] += 1
            except Exception as exc:
                logger.error(f"Error validating {doc['corpus_name']}/{dialect}: {exc}")
                summary["errors"] += 1

    baselines = thresholds.get("per_dialect_baselines", {})
    try:
        logger.info("=" * 80)
        logger.info("Optimizing dialect discrimination weights...")
        optimal_weights = optimize_dialect_discrimination_weights(all_docs, profiles, baselines, logger)

        all_results = []
        summary = {
            "total_files": 0,
            "passed": 0,
            "failed": 0,
            "unknown": 0,
            "skipped": 0,
            "errors": 0,
        }

        for dialect, doc_list in sorted(docs.items()):
            for doc in doc_list:
                summary["total_files"] += 1
                try:
                    result = validate_file_against_dialect_profile(
                        doc,
                        profiles[dialect],
                        thresholds,
                        all_profiles=profiles,
                        baselines=baselines,
                        weights=optimal_weights,
                    )
                    all_results.append(result)
                    status = result["status"]
                    if status == "PASS":
                        summary["passed"] += 1
                    elif status == "FAIL":
                        summary["failed"] += 1
                    elif status == "UNKNOWN":
                        summary["unknown"] += 1
                    elif status == "SKIP":
                        summary["skipped"] += 1
                except Exception as exc:
                    logger.error(f"Error re-validating {doc['corpus_name']}/{dialect}: {exc}")
                    summary["errors"] += 1

        summary["optimal_weights"] = {
            "char_uni": float(optimal_weights[0]),
            "char_bi": float(optimal_weights[1]),
            "char_tri": float(optimal_weights[2]),
            "word_uni": float(optimal_weights[3]),
        }
    except Exception as exc:
        logger.warning(f"Dialect weight optimization failed: {exc}")

    os.makedirs(output_dir, exist_ok=True)

    results_file = os.path.join(output_dir, "validation_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    if "optimal_weights" in summary:
        weights_file = os.path.join(output_dir, "optimal_dialect_weights.json")
        with open(weights_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "optimal_weights": summary["optimal_weights"],
                    "generated": datetime.now().isoformat(),
                    "description": "Optimized weights for dialect discrimination",
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

    summary_file = os.path.join(output_dir, "validation_summary.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("Corpora Validation Summary (Per-Dialect)\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"Language: {language_filter.upper()}\n")
        f.write(f"{'=' * 80}\n\n")

        if "optimal_weights" in summary:
            f.write("DIALECT DISCRIMINATION (Optimized Weights)\n")
            f.write(f"  char_uni: {summary['optimal_weights']['char_uni']:.4f}\n")
            f.write(f"  char_bi:  {summary['optimal_weights']['char_bi']:.4f}\n")
            f.write(f"  char_tri: {summary['optimal_weights']['char_tri']:.4f}\n")
            f.write(f"  word_uni: {summary['optimal_weights']['word_uni']:.4f}\n")
            f.write(f"{'=' * 80}\n\n")

        f.write(f"Total files: {summary['total_files']}\n")
        f.write(f"Passed: {summary['passed']} ({100 * summary['passed'] / max(1, summary['total_files']):.1f}%)\n")
        f.write(f"Failed: {summary['failed']} ({100 * summary['failed'] / max(1, summary['total_files']):.1f}%)\n")
        if summary["unknown"] > 0:
            f.write(f"Unknown: {summary['unknown']}\n")
        if summary["skipped"] > 0:
            f.write(f"Skipped: {summary['skipped']}\n")
        if summary["errors"] > 0:
            f.write(f"Errors: {summary['errors']}\n")

        f.write(f"\n{'=' * 80}\nDetails:\n")
        for result in all_results:
            f.write(f"\n{result['corpus']} ({result['language'].upper()}/{result['dialect']}):\n")
            f.write(f"  Status: {result['status']}\n")
            for metric, value in result.get("metrics", {}).items():
                f.write(f"  {metric}: {value:.6f}\n")
            if result.get("issues"):
                f.write("  Issues:\n")
                for issue in result["issues"]:
                    f.write(f"    - {issue}\n")

    logger.info("=" * 80)
    logger.info("Validation Complete")
    logger.info(f"Total files: {summary['total_files']}")
    logger.info(f"Passed: {summary['passed']}")
    logger.info(f"Failed: {summary['failed']}")
    if summary["unknown"] > 0:
        logger.info(f"Unknown: {summary['unknown']}")
    if summary["skipped"] > 0:
        logger.info(f"Skipped: {summary['skipped']}")
    if summary["errors"] > 0:
        logger.info(f"Errors: {summary['errors']}")
    logger.info(f"Results saved to {output_dir}")
    logger.info("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate Corpora XML files using per-dialect thresholds"
    )
    parser.add_argument(
        "--thresholds-file",
        type=str,
        required=True,
        help="Path to dialect_statistical_thresholds.json",
    )
    parser.add_argument(
        "--language",
        type=str,
        required=True,
        help="Language code to validate (e.g., pwn, ami, trv)",
    )
    parser.add_argument(
        "--dialect",
        type=str,
        default=None,
        help="Optional dialect filter to validate only one dialect",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="test_results/corpora_dialect_validation",
        help="Output directory for validation results",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="Enable debug logging",
    )

    args = parser.parse_args()
    validate_all_corpora(
        thresholds_file=args.thresholds_file,
        output_dir=args.output_dir,
        language_filter=args.language,
        dialect_filter=args.dialect,
        debug=args.debug,
    )
