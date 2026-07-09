#!/usr/bin/env python3
"""
Corpus QC test suite for Northern Paiwan reference validation.

Compares a reference corpus to a target corpus using the n-gram statistics
produced by bag_of_sentence_analysis.n_gram_analysis. Supports four predefined
Northern Paiwan scenarios and custom reference/target inputs.

Run from the FormosanBank repository root:

    python QC/orthography/corpus_qc_suite.py
    python QC/orthography/corpus_qc_suite.py --case same_lang_dialect_orthography
    python QC/orthography/corpus_qc_suite.py --ref-corpus path/to/ref.txt --target-corpus path/to/target.txt
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "corpus_qc_results"

DEFAULT_CORPORA_SUBFOLDERS = [
    "ePark/",
    "ILRDF_Dicts/",
    "Paiwan_Stories/",
    "NTUFormosanCorpus/",
]

LANG = "Paiwan"
REFERENCE_DIALECT = "Northern"
REFERENCE_KIND = "standard"
LIMIT = 200


@dataclass(frozen=True)
class CorpusPair:
    """Reference and target text plus metadata for one comparison."""

    case_id: str
    description: str
    reference: str
    target: str
    reference_label: str
    target_label: str
    analysis_lang: str = LANG


def ensure_repo_root() -> None:
    os.chdir(REPO_ROOT)
    if str(SCRIPT_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPT_DIR))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def default_corpora_paths() -> list[str]:
    return [f"Corpora/{name}" for name in DEFAULT_CORPORA_SUBFOLDERS]


def load_dialect_corpus(
    lang: str,
    dialect: str,
    kind_of: str = "standard",
    corpora_paths: list[str] | None = None,
) -> str:
    from orthography_extract import generate_corpus, remove_chinese_characters

    corpora_paths = corpora_paths or default_corpora_paths()
    text = ""
    for path in corpora_paths:
        if not os.path.exists(path):
            continue
        by_dialect = generate_corpus(lang, path, kind_of, by_dialect=True)
        if dialect in by_dialect:
            text += by_dialect[dialect]
    return remove_chinese_characters(text)


def split_sentences(corpus: str) -> list[str]:
    return [sentence for sentence in re.split(r"(?<=[.!?])\s+", corpus) if sentence.strip()]


def partition_corpus(corpus: str, ref_ratio: float = 0.8, seed: int = 0) -> tuple[str, str]:
    sentences = split_sentences(corpus)
    if len(sentences) < 2:
        midpoint = max(1, len(corpus) // 2)
        return corpus[:midpoint], corpus[midpoint:]

    random.seed(seed)
    ref_sentences = random.sample(sentences, math.ceil(ref_ratio * len(sentences)))
    target_sentences = [sentence for sentence in sentences if sentence not in ref_sentences]
    return "".join(ref_sentences), "".join(target_sentences)


def build_northern_paiwan_cases(
    corpora_paths: list[str] | None = None,
    ref_ratio: float = 0.8,
    seed: int = 0,
) -> dict[str, CorpusPair]:
    """
    Build the four Northern Paiwan QC scenarios.

    1. same_lang_dialect_orthography
       Two random partitions of Northern Paiwan standard text.
    2. same_lang_orthography_diff_dialect
       Northern Paiwan standard vs Southern Paiwan standard.
    3. same_lang_dialect_diff_orthography
       Northern Paiwan standard vs Northern Paiwan original spelling.
    4. diff_lang_correct_orthography
       Northern Paiwan standard vs Amis standard (different language).
    """
    northern_standard = load_dialect_corpus(
        LANG, REFERENCE_DIALECT, REFERENCE_KIND, corpora_paths
    )
    if not northern_standard.strip():
        raise ValueError(
            "Could not load Northern Paiwan standard text from the configured corpora."
        )

    ref_partition, target_partition = partition_corpus(
        northern_standard, ref_ratio=ref_ratio, seed=seed
    )
    southern_standard = load_dialect_corpus(
        LANG, "Southern", REFERENCE_KIND, corpora_paths
    )
    northern_original = load_dialect_corpus(
        LANG, REFERENCE_DIALECT, "original", corpora_paths
    )
    amis_standard = load_dialect_corpus(
        "Amis", "Coastal", REFERENCE_KIND, corpora_paths
    )

    if not southern_standard.strip():
        raise ValueError("Could not load Southern Paiwan standard text.")
    if not northern_original.strip():
        raise ValueError("Could not load Northern Paiwan original text.")
    if not amis_standard.strip():
        raise ValueError("Could not load Amis standard text for cross-language comparison.")

    return {
        "same_lang_dialect_orthography": CorpusPair(
            case_id="same_lang_dialect_orthography",
            description=(
                "Same language, dialect, and orthography: two random partitions of "
                "Northern Paiwan standard text."
            ),
            reference=ref_partition,
            target=target_partition,
            reference_label="Northern Paiwan standard (reference partition)",
            target_label="Northern Paiwan standard (target partition)",
        ),
        "same_lang_orthography_diff_dialect": CorpusPair(
            case_id="same_lang_orthography_diff_dialect",
            description=(
                "Same language and orthography, different dialect: Northern vs Southern "
                "Paiwan standard text."
            ),
            reference=northern_standard,
            target=southern_standard,
            reference_label="Northern Paiwan standard",
            target_label="Southern Paiwan standard",
        ),
        # TODO: Find sources to with different orthographies
        # "same_lang_dialect_diff_orthography": CorpusPair(
        #     case_id="same_lang_dialect_diff_orthography",
        #     description=(
        #         "Same language and dialect, different orthography: Northern Paiwan "
        #         "standard vs original spelling."
        #     ),
        #     reference=northern_standard,
        #     target=northern_original,
        #     reference_label="Northern Paiwan standard",
        #     target_label="Northern Paiwan original",
        # ),
        "diff_lang_correct_orthography": CorpusPair(
            case_id="diff_lang_correct_orthography",
            description=(
                "Different language with correct orthography: Northern Paiwan standard "
                "vs Amis standard."
            ),
            reference=northern_standard,
            target=amis_standard,
            reference_label="Northern Paiwan standard",
            target_label="Amis Central standard",
            analysis_lang=LANG,
        ),
    }


def run_comparison(
    pair: CorpusPair,
    *,
    n: int = 2,
    laplace: bool = True,
    output_dir: Path,
    save_plots: bool = False,
    verbose: bool = True,
) -> dict:
    from bag_of_sentence_analysis import n_gram_analysis

    case_output_dir = output_dir / pair.case_id
    stats = n_gram_analysis(
        lang=pair.analysis_lang,
        ref_corpus=pair.reference,
        target_corpus=pair.target,
        logs_dir=str(case_output_dir),
        n=n,
        laplace=laplace,
        save_plots=save_plots,
        verbose=verbose,
        limit=LIMIT,
    )
    compact_statistics = {
        "n": stats.get("n"),
        "mean_next_word_js_distance": stats.get("mean_next_word_js_distance"),
        "mean_interpolated_next_word_js_distance": stats.get("mean_interpolated_next_word_js_distance"),
        "average_interpolated_conditional_probability_proportion": stats.get(
            "average_interpolated_conditional_probability_proportion"
        ),
        "n_gram_statistics": stats.get("n_gram_statistics", {}),
    }
    return {
        "case_id": pair.case_id,
        "description": pair.description,
        "reference_label": pair.reference_label,
        "target_label": pair.target_label,
        "analysis_lang": pair.analysis_lang,
        "reference_char_count": len(pair.reference),
        "target_char_count": len(pair.target),
        "statistics": compact_statistics,
        "analysis_statistics": stats,
    }


def format_stats_row(result: dict) -> dict:
    stats = result.get("analysis_statistics", result.get("statistics", {}))
    n_value = stats.get("n", 2)
    word_metrics = stats.get("n_gram_statistics", {}).get(str(n_value), {}).get("word", {})
    row = {
        "case_id": result["case_id"],
        "jaccard_similarity": word_metrics.get("jaccard_similarity"),
        "overlap_coefficient": word_metrics.get("overlap_coefficient"),
        "cosine_similarity": word_metrics.get("cosine_similarity"),
        "euclidean_distance": word_metrics.get("euclidean_distance"),
        "kl_divergence": word_metrics.get("kl_divergence"),
        "mean_next_word_js_distance": stats.get("mean_next_word_js_distance"),
        "mean_interpolated_next_word_js_distance": stats.get("mean_interpolated_next_word_js_distance"),
        "average_interpolated_conditional_probability_proportion": stats.get(
            "average_interpolated_conditional_probability_proportion"
        ),
        "ref_token_count": stats.get("ref_token_count"),
        "target_token_count": stats.get("target_token_count"),
        "n_gram_statistics": json.dumps(stats.get("n_gram_statistics", {}), ensure_ascii=False),
    }
    return row


def print_summary(results: list[dict]) -> None:
    print("\n=== Corpus QC summary ===")
    rows = [format_stats_row(result) for result in results]
    summary = pd.DataFrame(rows)
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.4f}"))


def save_results(results: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "corpus_qc_results.json"
    csv_path = output_dir / "corpus_qc_summary.csv"

    output_results = []
    for result in results:
        output_result = {
            key: value for key, value in result.items() if key != "analysis_statistics"
        }
        output_results.append(output_result)

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(output_results, handle, indent=2)

    pd.DataFrame([format_stats_row(result) for result in results]).to_csv(
        csv_path, index=False
    )
    print(f"\nWrote detailed results to {json_path}")
    print(f"Wrote summary table to {csv_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Northern Paiwan corpus QC comparisons using bag-of-sentence "
            "n-gram statistics. Optionally run dialect prediction on ePark XML files."
        )
    )
    parser.add_argument(
        "--case",
        choices=[
            "same_lang_dialect_orthography",
            "same_lang_orthography_diff_dialect",
            "same_lang_dialect_diff_orthography",
            "diff_lang_correct_orthography",
            "all",
            "epark_paiwan_dialect_prediction",
        ],
        default="all",
        help="Which predefined Northern Paiwan scenario to run, or 'epark_paiwan_dialect_prediction' for dialect detection.",
    )
    parser.add_argument(
        "--ref-corpus",
        type=Path,
        help="Optional path to a custom reference corpus text file.",
    )
    parser.add_argument(
        "--target-corpus",
        type=Path,
        help="Optional path to a custom target corpus text file.",
    )
    parser.add_argument(
        "--analysis-lang",
        default=LANG,
        help="Language used for orthography-aware tokenization (default: Paiwan).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for JSON/CSV output and optional plots.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=2,
        help="Maximum n-gram length for analysis (default: 2).",
    )
    parser.add_argument(
        "--ref-ratio",
        type=float,
        default=0.8,
        help="Reference partition ratio for the same-corpus case (default: 0.8).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for the same-corpus partition case (default: 0).",
    )
    parser.add_argument(
        "--save-plots",
        action="store_true",
        help="Save comparison plots produced by n_gram_analysis.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-metric console output from n_gram_analysis.",
    )
    return parser.parse_args()


def load_xml_text_by_dialect(xml_path: str, target_dialect: str = None) -> str:
    """Load text from an XML file directory using generate_corpus, extracting target dialect."""
    from orthography_extract import generate_corpus, remove_chinese_characters
    from pathlib import Path
    
    # Get the directory containing the XML file
    xml_dir = str(Path(xml_path).parent)
    
    # Use generate_corpus to extract from this directory
    by_dialect = generate_corpus(LANG, xml_dir, REFERENCE_KIND, by_dialect=True)
    
    # Extract the specified dialect (or reference dialect if not specified)
    dialect_to_extract = target_dialect if target_dialect else REFERENCE_DIALECT
    text = by_dialect.get(dialect_to_extract, "")
    return remove_chinese_characters(text)


def print_confusion_matrix(predictions: list[tuple[str, str]], dialects: list[str]) -> None:
    """
    Print a confusion matrix from (actual_dialect, predicted_dialect) pairs.
    
    Args:
        predictions: List of (actual, predicted) dialect tuples
        dialects: List of dialect names to use as rows/columns
    """
    # Build confusion matrix
    matrix = {actual: {pred: 0 for pred in dialects} for actual in dialects}
    
    for actual, predicted in predictions:
        if actual in matrix and predicted in matrix[actual]:
            matrix[actual][predicted] += 1
    
    # Print header
    print(f"\n{'Actual':>12} | " + " | ".join(f"{d:>12}" for d in dialects))
    print("-" * (15 + len(dialects) * 16))
    
    # Print rows
    for actual in dialects:
        row_vals = [str(matrix[actual][pred]) for pred in dialects]
        print(f"{actual:>12} | " + " | ".join(f"{val:>12}" for val in row_vals))
    
    print()


def get_epark_paiwan_directories_with_all_dialects() -> dict[str, dict[str, str]]:
    """
    Find all directories in ePark/XML that have files for all 4 Paiwan dialects.
    
    Returns:
        Dict mapping directory path to dict of dialect -> file path.
        E.g., {
            'ePark/XML/jiu_jie_jiao_cai_nine_level_materials/Paiwan': {
                'Northern': 'path/to/Northern_Paiwan.xml',
                'Central': 'path/to/Central_Paiwan.xml',
                ...
            }
        }
    """
    from pathlib import Path
    
    epark_root = Path(REPO_ROOT) / "Corpora" / "ePark" / "XML"
    if not epark_root.exists():
        return {}
    
    required_dialects = {"Northern", "Central", "Eastern", "Southern"}
    results = {}
    
    # Walk through all subdirectories
    for item in epark_root.iterdir():
        if not item.is_dir():
            continue
        paiwan_dir = item / "Paiwan"
        if not paiwan_dir.exists():
            continue
        
        # Find all XML files in this Paiwan directory
        dialect_files = {}
        for xml_file in paiwan_dir.glob("*.xml"):
            # Extract dialect from filename (e.g., "Northern_Paiwan.xml" -> "Northern")
            filename = xml_file.stem
            for dialect in required_dialects:
                if dialect in filename:
                    dialect_files[dialect] = str(xml_file)
                    break
        
        # Only include if all 4 dialects are present
        if set(dialect_files.keys()) == required_dialects:
            results[str(paiwan_dir)] = dialect_files
    
    return results


def run_ePark_paiwan_dialect_prediction() -> None:
    """
    For each ePark directory with all 4 Paiwan dialects:
    - For each actual XML file (with known actual dialect)
    - Extract it using its actual dialect
    - Compare against all 4 dialect references
    - Predict the dialect using two methods:
      1. Based on KL divergence (original)
      2. Based on overlap coefficient of top LIMIT n-grams
    """
    from orthography_extract import generate_corpus, remove_chinese_characters
    
    ensure_repo_root()
    
    # Load reference corpora for all 4 dialects using generate_corpus directly
    ref_dialects = {}
    epark_path = "Corpora/ePark"
    by_dialect = generate_corpus(LANG, epark_path, REFERENCE_KIND, by_dialect=True)
    
    for dialect in ["Northern", "Central", "Eastern", "Southern"]:
        ref_text = by_dialect.get(dialect, "")
        ref_dialects[dialect] = remove_chinese_characters(ref_text)
    
    directories = get_epark_paiwan_directories_with_all_dialects()
    
    if not directories:
        print("No ePark directories found with all 4 Paiwan dialects.")
        return
    
    print(f"\nFound {len(directories)} ePark Paiwan directories with all 4 dialects.\n")
    
    all_results = []
    total_correct_kl = 0
    total_correct_overlap = 0
    total_files = 0
    
    kl_predictions = []  # For confusion matrix
    overlap_predictions = []  # For confusion matrix
    
    for dir_path, dialect_files in sorted(directories.items()):
        print(f"\n{'='*80}")
        print(f"Directory: {dir_path}")
        print(f"{'='*80}")
        
        dir_results = {
            "directory": dir_path,
            "file_predictions": {}
        }
        
        # For each actual dialect file in this directory
        for actual_dialect in ["Northern", "Central", "Eastern", "Southern"]:
            xml_path = dialect_files[actual_dialect]
            
            print(f"\n  File: {actual_dialect}_Paiwan.xml (actual dialect: {actual_dialect})")
            
            # Extract this file using its actual dialect
            target_text = load_xml_text_by_dialect(xml_path, target_dialect=actual_dialect)
            
            if not target_text.strip():
                print(f"    Warning: No text found for {actual_dialect}")
                continue
            
            # Compare this extraction against all 4 reference dialects
            kl_divergences = {}
            overlap_coefficients = {}
            
            for ref_dialect in ["Northern", "Central", "Eastern", "Southern"]:
                pair = CorpusPair(
                    case_id=f"{actual_dialect}_vs_{ref_dialect}",
                    description=f"File {actual_dialect} vs {ref_dialect} reference",
                    reference=ref_dialects[ref_dialect],
                    target=target_text,
                    reference_label=f"{ref_dialect} reference",
                    target_label=f"{actual_dialect} file",
                )
                
                result = run_comparison(
                    pair,
                    n=2,
                    output_dir=Path(REPO_ROOT) / "QC" / "corpus_qc_results",
                    save_plots=False,
                    verbose=False,
                )
                
                # Extract metrics from result
                stats = result.get("analysis_statistics", {})
                n_gram_stats = stats.get("n_gram_statistics", {}).get("2", {})
                word_stats = n_gram_stats.get("word", {})
                
                kl_div = word_stats.get("kl_divergence")
                overlap_coef = word_stats.get("overlap_coefficient")
                
                kl_divergences[ref_dialect] = kl_div
                overlap_coefficients[ref_dialect] = overlap_coef
            
            # Prediction 1: Using KL divergence (lower is better, so minimize)
            predicted_dialect_kl = min(kl_divergences, key=lambda d: kl_divergences[d] if kl_divergences[d] is not None else float('inf'))
            min_kl = kl_divergences[predicted_dialect_kl]
            is_correct_kl = (actual_dialect == predicted_dialect_kl)
            
            # Prediction 2: Using overlap coefficient (higher is better, so maximize)
            predicted_dialect_overlap = max(overlap_coefficients, key=lambda d: overlap_coefficients[d] if overlap_coefficients[d] is not None else float('-inf'))
            max_overlap = overlap_coefficients[predicted_dialect_overlap]
            is_correct_overlap = (actual_dialect == predicted_dialect_overlap)
            
            total_files += 1
            if is_correct_kl:
                total_correct_kl += 1
            if is_correct_overlap:
                total_correct_overlap += 1
            
            # Track for confusion matrices
            kl_predictions.append((actual_dialect, predicted_dialect_kl))
            overlap_predictions.append((actual_dialect, predicted_dialect_overlap))
            
            status_kl = "[CORRECT]" if is_correct_kl else "[WRONG]"
            status_overlap = "[CORRECT]" if is_correct_overlap else "[WRONG]"
            
            print(f"    KL Divergence prediction: {predicted_dialect_kl} (KL: {min_kl:.6f}) {status_kl}")
            print(f"    Overlap Coeff prediction: {predicted_dialect_overlap} (overlap: {max_overlap:.6f}) {status_overlap}")
            print(f"      KL divergences: {', '.join(f'{d}={kl_divergences[d]:.6f}' for d in ['Northern', 'Central', 'Eastern', 'Southern'])}")
            print(f"      Overlap coeffs: {', '.join(f'{d}={overlap_coefficients[d]:.6f}' for d in ['Northern', 'Central', 'Eastern', 'Southern'])}")
            
            dir_results["file_predictions"][actual_dialect] = {
                "predicted_dialect_kl": predicted_dialect_kl,
                "predicted_dialect_overlap": predicted_dialect_overlap,
                "min_kl": min_kl,
                "max_overlap": max_overlap,
                "is_correct_kl": is_correct_kl,
                "is_correct_overlap": is_correct_overlap,
                "all_kl_divergences": kl_divergences,
                "all_overlap_coefficients": overlap_coefficients
            }
        
        all_results.append(dir_results)
    
    # Print summary
    print(f"\n\n{'='*80}")
    print("SUMMARY - KL DIVERGENCE METHOD")
    print(f"{'='*80}")
    print(f"Total files tested: {total_files}")
    print(f"Correct predictions: {total_correct_kl}")
    if total_files > 0:
        accuracy_kl = 100.0 * total_correct_kl / total_files
        print(f"Accuracy: {accuracy_kl:.1f}%")
    
    print(f"\n{'='*80}")
    print("SUMMARY - OVERLAP COEFFICIENT METHOD")
    print(f"{'='*80}")
    print(f"Total files tested: {total_files}")
    print(f"Correct predictions: {total_correct_overlap}")
    if total_files > 0:
        accuracy_overlap = 100.0 * total_correct_overlap / total_files
        print(f"Accuracy: {accuracy_overlap:.1f}%")
    
    # Save results to CSV
    output_dir = Path(REPO_ROOT) / "QC" / "corpus_qc_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Flatten results for CSV output
    csv_rows = []
    all_dialects = ["Northern", "Central", "Eastern", "Southern"]
    
    for dir_result in all_results:
        dir_path = dir_result["directory"]
        for actual_dialect, prediction in dir_result["file_predictions"].items():
            row = {
                "directory": dir_path,
                "actual_dialect": actual_dialect,
                "predicted_dialect_kl": prediction["predicted_dialect_kl"],
                "predicted_dialect_overlap": prediction["predicted_dialect_overlap"],
                "correct_kl": prediction["is_correct_kl"],
                "correct_overlap": prediction["is_correct_overlap"],
                "min_kl": prediction["min_kl"],
                "max_overlap": prediction["max_overlap"],
            }
            csv_rows.append(row)
    
    if csv_rows:
        csv_path = output_dir / "ePark_paiwan_dialect_prediction.csv"
        pd.DataFrame(csv_rows).to_csv(csv_path, index=False)
        print(f"\nDetailed results saved to: {csv_path}")
        
        # Print confusion matrices
        print(f"\n{'='*80}")
        print("CONFUSION MATRIX - KL DIVERGENCE METHOD")
        print(f"{'='*80}")
        print_confusion_matrix(kl_predictions, all_dialects)
        
        print(f"\n{'='*80}")
        print("CONFUSION MATRIX - OVERLAP COEFFICIENT METHOD")
        print(f"{'='*80}")
        print_confusion_matrix(overlap_predictions, all_dialects)
        
        # Calculate accuracy by actual dialect
        print(f"\n{'='*80}")
        print("ACCURACY BY DIALECT - KL DIVERGENCE METHOD")
        print(f"{'='*80}")
        for dialect in all_dialects:
            dialect_rows = [r for r in csv_rows if r["actual_dialect"] == dialect]
            if dialect_rows:
                correct = sum(1 for r in dialect_rows if r["correct_kl"])
                total = len(dialect_rows)
                acc = 100.0 * correct / total
                print(f"  {dialect:12s}: {acc:5.1f}% ({correct}/{total})")
        
        print(f"\n{'='*80}")
        print("ACCURACY BY DIALECT - OVERLAP COEFFICIENT METHOD")
        print(f"{'='*80}")
        for dialect in all_dialects:
            dialect_rows = [r for r in csv_rows if r["actual_dialect"] == dialect]
            if dialect_rows:
                correct = sum(1 for r in dialect_rows if r["correct_overlap"])
                total = len(dialect_rows)
                acc = 100.0 * correct / total
                print(f"  {dialect:12s}: {acc:5.1f}% ({correct}/{total})")



def main() -> None:
    args = parse_args()
    ensure_repo_root()

    # Special case: ePark Paiwan dialect prediction
    if args.case == "epark_paiwan_dialect_prediction":
        run_ePark_paiwan_dialect_prediction()
        return

    if args.ref_corpus or args.target_corpus:
        if not args.ref_corpus or not args.target_corpus:
            raise SystemExit(
                "Both --ref-corpus and --target-corpus are required for custom comparisons."
            )
        pair = CorpusPair(
            case_id="custom",
            description="Custom reference and target corpora supplied on the command line.",
            reference=load_text(args.ref_corpus),
            target=load_text(args.target_corpus),
            reference_label=str(args.ref_corpus),
            target_label=str(args.target_corpus),
            analysis_lang=args.analysis_lang,
        )
        cases = [pair]
    else:
        all_cases = build_northern_paiwan_cases(
            ref_ratio=args.ref_ratio,
            seed=args.seed,
        )
        if args.case == "all":
            cases = list(all_cases.values())
        else:
            cases = [all_cases[args.case]]

    results = []
    for pair in cases:
        print(f"\n=== {pair.case_id} ===")
        print(pair.description)
        print(f"Reference: {pair.reference_label}")
        print(f"Target: {pair.target_label}")
        results.append(
            run_comparison(
                pair,
                n=args.n,
                output_dir=args.output_dir,
                save_plots=args.save_plots,
                verbose=not args.quiet,
            )
        )

    print_summary(results)
    save_results(results, args.output_dir)


if __name__ == "__main__":
    main()
