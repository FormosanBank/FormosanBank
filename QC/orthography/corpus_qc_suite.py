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
            "n-gram statistics."
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
        ],
        default="all",
        help="Which predefined Northern Paiwan scenario to run.",
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


def main() -> None:
    args = parse_args()
    ensure_repo_root()

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
